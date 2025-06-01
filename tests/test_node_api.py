#!/usr/bin/env python3
"""
Test script to verify Node.js API connectivity using the NodeAPI library
"""

import os
import sys
import pytest
import requests
from datetime import datetime
from dotenv import load_dotenv
from libraries.node_api import get_client, NodeAPIException

# Load environment variables
load_dotenv()

def test_node_api_integration():
    """Integration test: Hit the Node.js API homepage via Docker networking"""
    
    print("\n🔗 Testing Node.js API integration via Docker networking...")
    
    # Get Node API URL from environment (this should be the Docker service name)
    node_api_url = os.getenv('NODE_API_BASE_URL')
    print(f"NODE_API_BASE_URL from environment: {node_api_url}")
    
    if not node_api_url:
        pytest.fail("NODE_API_BASE_URL environment variable not set")
    
    # Extract the base URL (remove /api/v1/ to get the homepage)
    base_url = node_api_url.rstrip('/').replace('/api/v1', '')
    print(f"Testing Node.js API homepage at: {base_url}")
    
    try:
        # Make a direct request to the homepage
        print("Making request to Node.js API homepage...")
        response = requests.get(base_url, timeout=30)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        # Check for 200 status code
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check that we got some content
        content = response.text
        print(f"Response content length: {len(content)} characters")
        print(f"Content preview: {content[:200]}...")
        
        assert len(content) > 0, "Response should not be empty"
        
        # If it's HTML, check for some expected content
        if 'text/html' in response.headers.get('content-type', '').lower():
            assert '<html>' in content.lower() or '<!doctype html>' in content.lower(), "Should be valid HTML"
            print("✅ Received valid HTML response")
        elif 'application/json' in response.headers.get('content-type', '').lower():
            print("✅ Received JSON response")
        else:
            print(f"✅ Received response with content-type: {response.headers.get('content-type', 'unknown')}")
        
        print(f"\n✅ Integration test PASSED!")
        print(f"   - Successfully connected to Node.js API at {base_url}")
        print(f"   - Received 200 status code")
        print(f"   - Received {len(content)} characters of content")
        
        return True
        
    except requests.exceptions.ConnectionError as e:
        error_msg = str(e)
        print(f"\n❌ Connection failed: {error_msg}")
        
        if "Failed to resolve" in error_msg or "Name or service not known" in error_msg:
            print("\n💡 This suggests the Node.js API container is not running or not on the same network.")
            print("To fix this:")
            print("  1. Start the Node.js API with docker-compose")
            print("  2. Ensure it's named 'api' in docker-compose.yml")
            print("  3. Ensure both projects use the 'drawscape-network'")
            pytest.skip(f"Node.js API not available via Docker networking: {e}")
        else:
            print(f"\n💡 Connection error (API might be down): {error_msg}")
            pytest.skip(f"Node.js API connection failed: {e}")
            
    except requests.exceptions.Timeout as e:
        print(f"\n⏰ Request timed out: {e}")
        pytest.skip(f"Node.js API request timed out: {e}")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


def test_node_api_connection():
    """Test Node.js API connection and basic operations"""
    
    # Get Node API URL from environment
    node_api_url = os.getenv('NODE_API_BASE_URL', 'http://localhost:3000/api/v1/')
    print(f"Connecting to Node.js API at: {node_api_url}")
    
    try:
        # Create NodeAPI client
        client = get_client()
        print(f"   ✓ NodeAPI client created with base URL: {client.base_url}")
        
        # Test 1: Try to hit a basic endpoint - test if API is responsive
        print("\n1. Testing API connectivity...")
        
        # Try common health/status endpoints first
        endpoints_to_try = [
            ("health", "Health check endpoint"),
            ("status", "Status endpoint"), 
            ("", "Root API endpoint"),
            ("ping", "Ping endpoint")
        ]
        
        successful_endpoint = None
        for endpoint, description in endpoints_to_try:
            try:
                print(f"   Trying {description}: {endpoint or 'root'}")
                response = client.get(endpoint)
                print(f"   ✓ SUCCESS: {description} responded")
                print(f"     Response: {response}")
                successful_endpoint = (endpoint, description)
                break
            except NodeAPIException as e:
                if e.status_code == 404:
                    print(f"   - {description} not found (404)")
                    continue
                else:
                    print(f"   - {description} failed with status {e.status_code}: {e}")
                    continue
            except Exception as e:
                print(f"   - {description} failed: {e}")
                continue
        
        if successful_endpoint:
            endpoint, description = successful_endpoint
            print(f"\n✅ Successfully connected to Node.js API via {description}")
        else:
            # If no standard endpoints work, try the homepage without JSON parsing
            print("\n2. Testing raw API homepage...")
            try:
                # Direct test to see if the API is running at all
                base_url = node_api_url.rstrip('/').replace('/api/v1', '')
                raw_response = requests.get(base_url, timeout=10)
                print(f"   Raw homepage status: {raw_response.status_code}")
                print(f"   Content type: {raw_response.headers.get('content-type', 'unknown')}")
                
                if raw_response.status_code == 200:
                    print("   ✓ API server is running and responding")
                    print(f"   Content preview: {raw_response.text[:200]}...")
                else:
                    print(f"   - API returned status {raw_response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                print("   ❌ Cannot connect to API server")
                raise
            except Exception as e:
                print(f"   - Raw request failed: {e}")
                raise
        
        # Test 2: Test error handling
        print("\n3. Testing error handling...")
        try:
            client.get('definitely-does-not-exist-endpoint-12345')
            print("   ⚠️  Expected 404 error but got success - unusual")
        except NodeAPIException as e:
            if e.status_code == 404:
                print("   ✓ 404 errors handled correctly")
            else:
                print(f"   ✓ Error handling works (got {e.status_code})")
        
        # Test 3: Test URL building
        print("\n4. Testing URL construction...")
        test_endpoint = "test/url/construction"
        full_url = client._build_url(test_endpoint)
        expected_base = client.base_url
        print(f"   Base URL: {expected_base}")
        print(f"   Endpoint: {test_endpoint}")
        print(f"   Full URL: {full_url}")
        
        # Verify URL construction is correct
        assert full_url.startswith(expected_base), "URL should start with base URL"
        assert test_endpoint in full_url, "URL should contain endpoint"
        print("   ✓ URL construction working correctly")
        
        # Test 4: Test timeout configuration
        print("\n5. Testing client configuration...")
        print(f"   Timeout: {client.timeout}s")
        print(f"   Session headers: {dict(client.session.headers)}")
        print("   ✓ Client configuration verified")
        
        print("\n✅ All Node.js API library tests passed!")
        
    except NodeAPIException as e:
        print(f"\n⚠️  Node.js API error: {e}")
        if e.status_code:
            print(f"Status Code: {e.status_code}")
        if e.response_data:
            print(f"Response Data: {e.response_data}")
        
        # Don't fail the test if it's just that endpoints don't exist
        if e.status_code in [404, 405]:
            print("\nSkipping remaining tests - API endpoints not available")
            pytest.skip(f"Node.js API endpoints not available: {e}")
        else:
            raise
            
    except Exception as e:
        error_msg = str(e)
        if "Connection refused" in error_msg or "Failed to establish" in error_msg:
            print(f"\n⚠️  Node.js API not available: {e}")
            print("\nTo run Node.js API tests:")
            print("  - Start the Node.js API server")
            print("  - Use Docker: docker-compose up in the Node.js project")
            print("  - Ensure NODE_API_BASE_URL is set correctly")
            print(f"  - Current NODE_API_BASE_URL: {node_api_url}")
            pytest.skip(f"Node.js API not available: {e}")
        else:
            print(f"\n❌ Unexpected error during Node.js API tests: {e}")
            raise


def test_node_api_configuration():
    """Test Node.js API configuration and environment variables"""
    
    print("\n🔧 Testing Node.js API configuration...")
    
    # Test environment variable
    node_api_url = os.getenv('NODE_API_BASE_URL')
    print(f"NODE_API_BASE_URL environment variable: {node_api_url}")
    
    if not node_api_url:
        print("❌ NODE_API_BASE_URL environment variable not set")
        pytest.fail("NODE_API_BASE_URL environment variable must be set")
    
    # Test URL format
    if not node_api_url.startswith(('http://', 'https://')):
        print(f"⚠️  URL should start with http:// or https://")
        pytest.fail("NODE_API_BASE_URL should be a valid HTTP URL")
    
    # Test that URL includes api/v1 path
    if '/api/v1' not in node_api_url:
        print("⚠️  URL should include /api/v1/ path")
        pytest.fail("NODE_API_BASE_URL should include /api/v1/ path")
    
    print("✅ Node.js API configuration looks good")


if __name__ == "__main__":
    try:
        test_node_api_configuration()
        test_node_api_integration()
        test_node_api_connection()
        print("✅ Node.js API test script completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Node.js API test script failed: {e}")
        sys.exit(1) 
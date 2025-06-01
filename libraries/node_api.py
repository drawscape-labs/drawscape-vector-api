"""
Node API Library - Python wrapper for Node.js API endpoints

This library provides a clean interface for making HTTP requests to the Node.js API
from within the Python codebase. It includes generic HTTP methods that can be used
with any API endpoint.

Environment Variables:
    NODE_API_BASE_URL: Base URL for the Node.js API (e.g., http://localhost:3000/api/v1/)
"""

import os
import requests
from typing import Dict, Any, Optional
from urllib.parse import urljoin
import json


class NodeAPIException(Exception):
    """Custom exception for Node API errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class NodeAPI:
    """
    Node API client for making HTTP requests to the Node.js API
    """
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Node API client
        
        Args:
            base_url: Base URL for the API (defaults to NODE_API_BASE_URL env var)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url or os.getenv('NODE_API_BASE_URL')
        if not self.base_url:
            raise ValueError("NODE_API_BASE_URL environment variable must be set or base_url must be provided")
        
        # Ensure base_url ends with a slash for proper URL joining
        if not self.base_url.endswith('/'):
            self.base_url += '/'
            
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint"""
        return urljoin(self.base_url, endpoint.lstrip('/'))
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions for errors
        
        Args:
            response: requests.Response object
            
        Returns:
            Parsed JSON response data
            
        Raises:
            NodeAPIException: For HTTP errors or invalid JSON
        """
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
            except (ValueError, json.JSONDecodeError):
                error_data = {'message': response.text or 'Unknown error'}
            
            raise NodeAPIException(
                f"HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}",
                status_code=response.status_code,
                response_data=error_data
            )
        
        try:
            return response.json()
        except (ValueError, json.JSONDecodeError):
            # If response is not JSON, return the text content
            return {'data': response.text}
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request
        
        Args:
            endpoint: API endpoint (e.g., 'schematic-vectors')
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        url = self._build_url(endpoint)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise NodeAPIException(f"Request failed: {str(e)}")
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
             files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a POST request
        
        Args:
            endpoint: API endpoint
            data: JSON data to send
            files: Files to upload (for multipart requests)
            
        Returns:
            Response data as dictionary
        """
        url = self._build_url(endpoint)
        try:
            if files:
                # For file uploads, don't set Content-Type header (let requests handle it)
                headers = {k: v for k, v in self.session.headers.items() 
                          if k.lower() != 'content-type'}
                response = self.session.post(url, data=data, files=files, 
                                           timeout=self.timeout, headers=headers)
            else:
                response = self.session.post(url, json=data, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise NodeAPIException(f"Request failed: {str(e)}")
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a PUT request
        
        Args:
            endpoint: API endpoint
            data: JSON data to send
            
        Returns:
            Response data as dictionary
        """
        url = self._build_url(endpoint)
        try:
            response = self.session.put(url, json=data, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise NodeAPIException(f"Request failed: {str(e)}")
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a DELETE request
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Response data as dictionary
        """
        url = self._build_url(endpoint)
        try:
            response = self.session.delete(url, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise NodeAPIException(f"Request failed: {str(e)}")


# Convenience function to create a default client
def get_client(base_url: Optional[str] = None, timeout: int = 30) -> NodeAPI:
    """
    Get a NodeAPI client instance
    
    Args:
        base_url: Optional base URL (defaults to NODE_API_BASE_URL env var)
        timeout: Request timeout in seconds
        
    Returns:
        NodeAPI client instance
    """
    return NodeAPI(base_url=base_url, timeout=timeout)


# Example usage and testing functions
if __name__ == "__main__":
    # Example usage - these would normally be called from other parts of the codebase
    
    try:
        # Create client
        client = get_client()
        
        # Example: List all schematic vectors
        vectors = client.get('schematic-vectors')
        print(f"Response: {vectors}")
        
        # Example: Get a specific vector
        # vector = client.get('schematic-vectors/some-uuid-here')
        
        # Example: Update a vector
        # updated = client.post('schematic-vectors/some-uuid-here', 
        #                      data={'optimized': True})
        
    except NodeAPIException as e:
        print(f"API Error: {e}")
        if e.status_code:
            print(f"Status Code: {e.status_code}")
        if e.response_data:
            print(f"Response Data: {e.response_data}")
    except Exception as e:
        print(f"Unexpected error: {e}") 
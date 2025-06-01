#!/usr/bin/env python3
"""
Test script to verify Redis connectivity and basic operations
"""

import os
import sys
import redis
import pytest
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_redis_connection():
    """Test Redis connection and basic operations"""
    
    # Get Redis URL from environment
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    print(f"Connecting to Redis at: {redis_url}")
    
    try:
        # Create Redis client
        # Handle SSL connections (like Heroku Redis) properly
        if redis_url.startswith('rediss://'):
            r = redis.from_url(redis_url, decode_responses=True, ssl_cert_reqs=None)
        else:
            r = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        print("\n1. Testing connection...")
        pong = r.ping()
        print(f"   ✓ Connection successful: {pong}")
        assert pong is True, "Redis ping should return True"
        
        # Test SET operation
        print("\n2. Testing SET operation...")
        test_key = "test:drawscape:timestamp"
        test_value = f"Test at {datetime.now().isoformat()}"
        r.set(test_key, test_value)
        print(f"   ✓ SET {test_key} = {test_value}")
        
        # Test GET operation
        print("\n3. Testing GET operation...")
        retrieved_value = r.get(test_key)
        print(f"   ✓ GET {test_key} = {retrieved_value}")
        
        # Verify values match
        assert test_value == retrieved_value, "SET and GET values should match"
        print("   ✓ Values match!")
            
        # Test LIST operations
        print("\n4. Testing LIST operations...")
        list_key = "test:drawscape:list"
        r.delete(list_key)  # Clean up first
        r.lpush(list_key, "item1", "item2", "item3")
        print(f"   ✓ LPUSH to {list_key}")
        
        list_items = r.lrange(list_key, 0, -1)
        print(f"   ✓ LRANGE {list_key} = {list_items}")
        assert len(list_items) == 3, "List should contain 3 items"
        assert "item1" in list_items, "List should contain item1"
        
        # Test HASH operations
        print("\n5. Testing HASH operations...")
        hash_key = "test:drawscape:svg:metadata"
        r.hset(hash_key, mapping={
            "width": "800",
            "height": "600",
            "created_at": datetime.now().isoformat()
        })
        print(f"   ✓ HSET {hash_key}")
        
        hash_data = r.hgetall(hash_key)
        print(f"   ✓ HGETALL {hash_key} = {hash_data}")
        assert hash_data["width"] == "800", "Hash should contain correct width"
        assert hash_data["height"] == "600", "Hash should contain correct height"
        
        # Test expiration
        print("\n6. Testing key expiration...")
        expire_key = "test:drawscape:expire"
        r.setex(expire_key, 5, "This will expire in 5 seconds")
        ttl = r.ttl(expire_key)
        print(f"   ✓ SETEX {expire_key} with TTL = {ttl} seconds")
        assert ttl > 0, "TTL should be greater than 0"
        
        # Clean up test keys
        print("\n7. Cleaning up test keys...")
        r.delete(test_key, list_key, hash_key, expire_key)
        print("   ✓ Test keys deleted")
        
        # Get Redis info
        print("\n8. Redis server info:")
        info = r.info()
        print(f"   - Redis version: {info['redis_version']}")
        print(f"   - Used memory: {info['used_memory_human']}")
        print(f"   - Connected clients: {info['connected_clients']}")
        print(f"   - Total commands processed: {info['total_commands_processed']}")
        assert "redis_version" in info, "Redis info should contain version"
        
        print("\n✅ All Redis tests passed!")
        
    except redis.ConnectionError as e:
        print(f"\n⚠️  Redis not available: {e}")
        print("\nSkipping Redis tests. To run Redis tests:")
        print("  - Use Docker: docker-compose exec web python -m pytest tests/test_redis.py")
        print("  - Or start Redis locally: redis-server")
        pytest.skip(f"Redis not available: {e}")
    except Exception as e:
        print(f"\n❌ Error during Redis tests: {e}")
        raise


if __name__ == "__main__":
    try:
        test_redis_connection()
        print("✅ Redis test script completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Redis test script failed: {e}")
        sys.exit(1) 
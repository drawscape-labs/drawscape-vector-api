#!/usr/bin/env python3
"""
Main RQ worker bootstrap script with proper SSL handling for Heroku Redis
"""
import os
import sys
from rq import Worker
from redis import Redis


def main():
    """Start RQ worker with proper SSL configuration"""
    # Get Redis URL from environment
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Configure Redis connection with SSL handling for Heroku
    if redis_url.startswith('rediss://'):
        # For SSL Redis connections (like Heroku Redis), skip SSL cert verification
        redis_conn = Redis.from_url(redis_url, ssl_cert_reqs=None)
        print(f"Connecting to Redis with SSL (cert verification disabled): {redis_url[:20]}...")
    else:
        # For non-SSL connections (local development)
        redis_conn = Redis.from_url(redis_url)
        print(f"Connecting to Redis: {redis_url}")
    
    # Test the connection
    try:
        redis_conn.ping()
        print("Redis connection successful!")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        sys.exit(1)
    
    # Create worker and listen to 'background' queue
    worker = Worker(['background'], connection=redis_conn)
    print("Starting RQ worker...")
    worker.work()


if __name__ == '__main__':
    main() 
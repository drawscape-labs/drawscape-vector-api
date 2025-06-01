# Redis Setup for Drawscape Vector API

## Local Development (Docker)

Redis is configured to run in a Docker container for local development.

### Starting Redis
```bash
# Start Redis container
docker-compose up -d redis

# Or start all services
docker-compose up -d
```

### Testing Redis Connection
```bash
# Run the test script
python test_redis.py

# Or test directly with Docker
docker exec drawscape-vector-api-redis-1 redis-cli ping
```

### Redis Configuration
- **Port**: 6379
- **Data Persistence**: Enabled with AOF (Append Only File)
- **Health Check**: Configured to check connectivity every 5 seconds
- **Docker Image**: redis:7-alpine (lightweight Alpine Linux)

## Environment Variables

The following environment variable is used for Redis connection:
```
REDIS_URL=redis://localhost:6379/0  # For local development
REDIS_URL=redis://redis:6379/0      # For Docker Compose
```

## Heroku Deployment

For Heroku deployment, you'll need to add the Redis add-on:

### 1. Add Redis to Heroku
```bash
# Add Heroku Redis (this will automatically set REDIS_URL)
heroku addons:create heroku-redis:mini -a your-app-name

# Or for production use
heroku addons:create heroku-redis:premium-0 -a your-app-name
```

### 2. Verify Redis is Added
```bash
# Check your addons
heroku addons -a your-app-name

# Check Redis URL is set
heroku config:get REDIS_URL -a your-app-name
```

### 3. Environment Variables
Heroku automatically sets `REDIS_URL` when you add the Redis add-on. No manual configuration needed.

### 4. Redis Plans on Heroku
- **mini**: Free tier, 25MB, 20 connections
- **premium-0**: $15/month, 50MB, 40 connections
- **premium-1**: $30/month, 100MB, 80 connections
- **premium-2**: $60/month, 250MB, 200 connections

## Common Redis Operations for SVG/Vector API

```python
import redis
import os

# Connect to Redis
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
r = redis.from_url(redis_url, decode_responses=True)

# Cache an SVG
r.setex('svg:unique_id', 86400, svg_content)  # Cache for 24 hours

# Get cached SVG
svg = r.get('svg:unique_id')

# Store metadata
r.hset('svg:metadata:unique_id', mapping={
    'width': '800',
    'height': '600',
    'created_at': '2025-05-31'
})
```

## Monitoring

### Local Monitoring
```bash
# Watch Redis activity in real-time
docker exec drawscape-vector-api-redis-1 redis-cli monitor

# Check Redis info
docker exec drawscape-vector-api-redis-1 redis-cli info
```

### Heroku Monitoring
```bash
# Connect to Heroku Redis CLI
heroku redis:cli -a your-app-name

# View Redis metrics
heroku redis:info -a your-app-name
``` 
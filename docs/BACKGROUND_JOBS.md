# Background Jobs with RQ (Redis Queue) - Internal Use Only

This document explains how to use the background job processing system in the Drawscape Vector API. Background jobs are used internally within the application and are not exposed through API endpoints.

## Overview

We use RQ (Redis Queue) for background job processing. This allows us to offload time-consuming SVG generation tasks to background workers, keeping the API responsive. Jobs are queued internally from within existing functions and components.

## Local Development Setup

### 1. Using Docker Compose (Recommended)

```bash
# Start all services (web server + worker)
docker-compose up

# Or run in background
docker-compose up -d
```

### 2. Manual Setup

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Flask server
python server.py

# Terminal 3: Start RQ worker
export REDIS_URL=redis://localhost:6379
rq worker --url $REDIS_URL high default low svg-generation
```

## Using Background Jobs in Your Code

### Import the Job Manager

```python
from queues.job_manager import enqueue_svg_generation, get_job_status
```

### Queue a Job from Any Function

```python
def your_function():
    # Queue a background job
    job = enqueue_svg_generation(
        width=200,
        height=200,
        pattern_type='spiral',
        filename='output.svg',
        priority='default'  # 'high', 'default', 'low', or 'svg'
    )
    
    # Store job.id if you need to track progress
    return {"processing": True, "job_id": job.id}
```

### Check Job Status Internally

```python
status = get_job_status(job_id)

if status['status'] == 'finished':
    file_path = status['result']
    # Process the completed file
elif status['status'] == 'failed':
    error = status['error']
    # Handle the error
```

## Creating New Background Tasks

1. Add your task function to `workers/svg_tasks.py`:

```python
def my_new_task(param1, param2):
    """Your background task logic"""
    # Process data
    result = process_something(param1, param2)
    return result
```

2. Create a queue function in `queues/job_manager.py`:

```python
def enqueue_my_task(param1, param2):
    job = default_queue.enqueue(
        'workers.svg_tasks.my_new_task',
        param1=param1,
        param2=param2,
        job_timeout='10m'
    )
    return job
```

3. Use it in your application code:

```python
from queues.job_manager import enqueue_my_task

def some_endpoint():
    # Queue the job internally
    job = enqueue_my_task(data['param1'], data['param2'])
    # Return response without exposing job details
    return {"status": "processing"}
```

## Deployment to Heroku

1. Ensure your `Procfile` includes the worker process:
```
web: gunicorn server:app --bind 0.0.0.0:$PORT
worker: rq worker --url $REDIS_URL high default low svg-generation
```

2. Add Redis addon to your Heroku app:
```bash
heroku addons:create heroku-redis:hobby-dev
```

3. Scale your workers:
```bash
# Start 1 worker dyno
heroku ps:scale worker=1

# Check worker logs
heroku logs --tail --dyno=worker
```

## Monitoring

### Local Development
- RQ Dashboard: Install `pip install rq-dashboard` and run `rq-dashboard`
- Redis CLI: `redis-cli` to inspect queues directly
- Worker logs: `docker-compose logs worker`

### Production (Heroku)
- Worker logs: `heroku logs --tail --dyno=worker`
- Monitor through your application's internal logging

## Available Pattern Types

- `spiral`: Generates a spiral pattern for pen plotting
- `grid`: Generates a grid pattern with customizable spacing

## Best Practices

1. **Timeouts**: Set appropriate job timeouts based on complexity
2. **Priority Queues**: 
   - `high`: User-initiated, time-sensitive tasks
   - `default`: Regular processing
   - `low`: Batch jobs, cleanup tasks
   - `svg-generation`: Dedicated queue for SVG tasks
3. **Error Handling**: Implement fallback to synchronous processing if queues are unavailable
4. **File Storage**: Generated files are saved to `tests/output/generated/`

## Troubleshooting

### Redis Connection Issues
- Check `REDIS_URL` environment variable
- Ensure Redis is running: `redis-cli ping`

### Worker Not Processing Jobs
- Check worker logs for errors
- Verify worker is connected to correct Redis instance
- Ensure worker is listening to correct queue names

### Jobs Stuck in Queue
- Check if workers are running: `docker-compose ps`
- Scale workers if needed: `heroku ps:scale worker=2`

## Example Integration

See `examples/background_job_integration.py` for complete examples of:
- Batch processing with background jobs
- Fallback to synchronous processing
- Priority-based job queuing
- Internal job tracking without exposing implementation details 
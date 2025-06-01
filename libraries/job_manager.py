"""
Job queue manager for background tasks
"""
import os
from rq import Queue
from redis import Redis
from rq.job import Job


# Initialize Redis connection using environment variable
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = Redis.from_url(redis_url)

# Create single background queue
background_queue = Queue('background', connection=redis_conn)


def enqueue_background_job(task_function, *args, **kwargs):
    """
    Queue a background job
    
    Args:
        task_function: The function to execute (as string path like 'workers.svg_tasks.generate_complex_svg')
        *args: Positional arguments to pass to the task function
        **kwargs: Keyword arguments to pass to the task function
                 Special kwargs:
                 - job_timeout: Timeout for the job (default '5m')
    
    Returns:
        Job object with job ID and status
    """
    # Extract job_timeout from kwargs if provided, default to 5 minutes
    job_timeout = kwargs.pop('job_timeout', '5m')
    
    # Enqueue the job
    job = background_queue.enqueue(
        task_function,
        *args,
        **kwargs,
        job_timeout=job_timeout
    )
    
    return job


def get_job_status(job_id):
    """
    Get the status of a job by ID
    
    Args:
        job_id: The job ID to check
        
    Returns:
        Dict with job status information
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        return {
            'id': job.id,
            'status': job.get_status(),
            'result': job.result,
            'error': str(job.exc_info) if job.exc_info else None,
            'created_at': job.created_at,
            'started_at': job.started_at,
            'ended_at': job.ended_at
        }
    except Exception as e:
        return {
            'id': job_id,
            'status': 'not_found',
            'error': str(e)
        }


def cancel_job(job_id):
    """
    Cancel a job by ID
    
    Args:
        job_id: The job ID to cancel
        
    Returns:
        Success status
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.cancel()
        return True
    except Exception:
        return False 
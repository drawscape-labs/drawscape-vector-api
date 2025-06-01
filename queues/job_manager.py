"""
Job queue manager for background SVG generation tasks
"""
import os
from rq import Queue
from redis import Redis
from rq.job import Job


# Initialize Redis connection using environment variable
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = Redis.from_url(redis_url)

# Create queues for different priority levels
high_queue = Queue('high', connection=redis_conn)
default_queue = Queue('default', connection=redis_conn)
low_queue = Queue('low', connection=redis_conn)
svg_queue = Queue('svg-generation', connection=redis_conn)


def enqueue_svg_generation(width, height, pattern_type, filename, priority='default'):
    """
    Queue an SVG generation job
    
    Args:
        width: SVG width in mm
        height: SVG height in mm
        pattern_type: Type of pattern to generate
        filename: Output filename
        priority: Job priority ('high', 'default', 'low')
    
    Returns:
        Job object with job ID and status
    """
    # Select queue based on priority
    queue_map = {
        'high': high_queue,
        'default': default_queue,
        'low': low_queue,
        'svg': svg_queue
    }
    
    queue = queue_map.get(priority, default_queue)
    
    # Enqueue the job
    job = queue.enqueue(
        'workers.svg_tasks.generate_complex_svg',
        width=width,
        height=height,
        pattern_type=pattern_type,
        output_filename=filename,
        job_timeout='5m'  # 5 minute timeout
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
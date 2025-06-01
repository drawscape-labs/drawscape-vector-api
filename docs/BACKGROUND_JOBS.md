# Background Jobs

This document explains how to use the background job processing system in the Drawscape Vector API.

## Overview

We use RQ (Redis Queue) for background job processing. This allows us to offload time-consuming tasks to background workers, keeping the API responsive. Jobs are queued internally from within your application code.

## How It Works

- **Queue**: Single `background` queue handles all job types
- **Worker**: Processes jobs from the queue in the background
- **Tasks**: Located in `workers/` directory (e.g., `workers.svg_tasks.generate_complex_svg`)

## Basic Usage

### Import the Job Manager

```python
from libraries.job_manager import enqueue_background_job, get_job_status
```

### Queue a Background Job

```python
def your_function():
    # Queue any background task
    job = enqueue_background_job(
        'workers.svg_tasks.generate_complex_svg',
        width=200,
        height=200,
        pattern_type='spiral',
        output_filename='output.svg'
    )
    
    # Store job.id if you need to track progress
    return {"processing": True, "job_id": job.id}
```

### Check Job Status

```python
status = get_job_status(job_id)

if status['status'] == 'finished':
    file_path = status['result']
    # Process the completed file
elif status['status'] == 'failed':
    error = status['error']
    # Handle the error
else:
    # Still processing: 'queued', 'started', etc.
    pass
```

## Common Job Examples

### SVG Generation
```python
job = enqueue_background_job(
    'workers.svg_tasks.generate_complex_svg',
    width=210,
    height=297,
    pattern_type='spiral',
    output_filename='complex_spiral.svg'
)
```

### Email Notifications
```python
job = enqueue_background_job(
    'workers.email_tasks.send_notification',
    recipient='user@example.com',
    subject='Your order is ready',
    template='order_complete'
)
```

### Data Processing
```python
job = enqueue_background_job(
    'workers.data_tasks.process_file',
    file_path='/uploads/data.csv',
    format='json',
    job_timeout='15m'
)
```

### Batch Operations
```python
job = enqueue_background_job(
    'workers.file_tasks.process_batch',
    file_list=['file1.csv', 'file2.csv', 'file3.csv'],
    operation='convert_to_json',
    job_timeout='20m'
)
```

## Integration Example

```python
# components/artboard/main.py
from flask import Blueprint, jsonify, request
from libraries.job_manager import enqueue_background_job
from libraries.svg_builder import SVGBuilder

@artboard_bp.route('/create', methods=['POST'])
def create_artboard():
    data = request.get_json()
    
    # Quick response for simple SVGs
    if data.get('complexity') == 'simple':
        svg = SVGBuilder(data['width'], data['height'])
        svg.rect(10, 10, 50, 50)
        return jsonify({"svg": svg.to_string()})
    
    # Background job for complex patterns
    else:
        job = enqueue_background_job(
            'workers.svg_tasks.generate_complex_svg',
            width=data['width'],
            height=data['height'],
            pattern_type=data.get('pattern', 'spiral'),
            output_filename=f"artboard_{data['id']}.svg"
        )
        
        return jsonify({
            "status": "generating",
            "job_id": job.id,
            "message": "Complex pattern queued for generation"
        })
```

## Creating New Background Tasks

1. **Add your task function** to `workers/svg_tasks.py` or create new worker modules:

```python
def generate_postcard_svg(recipient, message, template_name):
    """Generate a postcard with custom message"""
    from libraries.svg_builder import SVGBuilder
    import os
    
    svg = SVGBuilder(210, 148)  # A6 postcard size
    
    # Add template design and message
    if template_name == 'birthday':
        # Add birthday decorations
        pass
    
    svg.hershey_text(105, 74, message, 0.5)
    
    # Save and return path
    filename = f"postcard_{recipient}_{template_name}.svg"
    output_path = os.path.join('output', 'postcards', filename)
    
    with open(output_path, 'w') as f:
        f.write(svg.to_string())
        
    return output_path
```

2. **Queue it** from your application code:

```python
job = enqueue_background_job(
    'workers.svg_tasks.generate_postcard_svg',
    recipient='John Doe',
    message='Happy Birthday!',
    template_name='birthday',
    job_timeout='2m'
)
```

## Function Reference

### `enqueue_background_job(task_function, *args, **kwargs)`

**Parameters:**
- `task_function`: String path to worker function (e.g., `'workers.svg_tasks.generate_complex_svg'`)
- `*args`: Positional arguments to pass to the task function
- `**kwargs`: Keyword arguments to pass to the task function
- `job_timeout`: Optional timeout (default: `'5m'`)

**Returns:** Job object with `.id` property for tracking

### `get_job_status(job_id)`

**Returns:** Dictionary with job information:
```python
{
    'id': 'job-uuid',
    'status': 'finished',  # 'queued', 'started', 'finished', 'failed'
    'result': '/path/to/output.svg',  # Return value from task function
    'error': None,  # Error message if failed
    'created_at': datetime,
    'started_at': datetime,
    'ended_at': datetime
}
```

## Best Practices

- **Use background jobs for**: Complex SVG generation, batch processing, email sending, data export/import
- **Use synchronous processing for**: Simple shapes, quick calculations, user-interactive features
- **Set timeouts**: Use `job_timeout` parameter for long-running tasks
- **Organize tasks**: Group related functions in worker modules (`workers.svg_tasks`, `workers.email_tasks`)
- **Handle errors**: Always check job status and handle failures gracefully 
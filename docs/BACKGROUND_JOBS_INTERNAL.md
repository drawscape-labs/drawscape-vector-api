# Using Background Jobs Internally

Since we're not exposing job endpoints via API, here's how to use background jobs from within your existing code.

## Basic Usage

### 1. Import the job manager

```python
from queues.job_manager import enqueue_svg_generation, get_job_status
```

### 2. Queue a job from any function

```python
def your_existing_function():
    # Do some processing...
    
    # Queue a background SVG generation
    job = enqueue_svg_generation(
        width=200,
        height=200,
        pattern_type='spiral',
        filename='background_spiral.svg',
        priority='default'
    )
    
    # Store job.id if you need to track it
    job_id = job.id
    
    # Continue with other work while SVG generates in background
    return {"status": "processing", "job_id": job_id}
```

## Example Integration

Here's how you might integrate background jobs into an existing blueprint:

```python
# components/artboard/main.py
from flask import Blueprint, jsonify, request
from queues.job_manager import enqueue_svg_generation
from libraries.svg_builder import SVGBuilder

artboard_bp = Blueprint('artboard', __name__, url_prefix='/api/artboard')

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
        job = enqueue_svg_generation(
            width=data['width'],
            height=data['height'],
            pattern_type=data.get('pattern', 'spiral'),
            filename=f"artboard_{data['id']}.svg",
            priority='high' if data.get('urgent') else 'default'
        )
        
        return jsonify({
            "status": "generating",
            "job_id": job.id,
            "message": "Complex pattern queued for generation"
        })
```

## Creating Custom Background Tasks

Add new tasks to `workers/svg_tasks.py`:

```python
def generate_postcard_svg(recipient, message, template_name):
    """Generate a postcard with custom message"""
    svg = SVGBuilder(210, 148)  # A6 postcard size
    
    # Add template design
    if template_name == 'birthday':
        # Add birthday decorations
        pass
    
    # Add message
    svg.hershey_text(105, 74, message, 0.5)
    
    # Save and return path
    filename = f"postcard_{recipient}_{template_name}.svg"
    output_path = os.path.join('output', 'postcards', filename)
    
    with open(output_path, 'w') as f:
        f.write(svg.to_string())
        
    return output_path
```

Then create a queue function in `queues/job_manager.py`:

```python
def enqueue_postcard_generation(recipient, message, template_name):
    """Queue a postcard generation job"""
    job = default_queue.enqueue(
        'workers.svg_tasks.generate_postcard_svg',
        recipient=recipient,
        message=message,
        template_name=template_name,
        job_timeout='2m'
    )
    return job
```

## Checking Job Status Internally

```python
from queues.job_manager import get_job_status

def check_generation_status(job_id):
    status = get_job_status(job_id)
    
    if status['status'] == 'finished':
        # File is ready at status['result']
        return {"ready": True, "path": status['result']}
    elif status['status'] == 'failed':
        # Handle error
        return {"ready": False, "error": status['error']}
    else:
        # Still processing
        return {"ready": False, "status": status['status']}
```

## Best Practices

1. **Use background jobs for**:
   - Complex pattern generation
   - Batch processing multiple SVGs
   - Time-consuming calculations
   - Large file operations

2. **Use synchronous processing for**:
   - Simple shapes and paths
   - Quick calculations
   - User-interactive features

3. **Priority Guidelines**:
   - `high`: User-initiated, time-sensitive tasks
   - `default`: Regular processing
   - `low`: Batch jobs, reports, cleanup tasks

4. **Error Handling**:
   ```python
   try:
       job = enqueue_svg_generation(...)
   except Exception as e:
       # Fallback to synchronous processing
       # or return error to user
       pass
   ``` 
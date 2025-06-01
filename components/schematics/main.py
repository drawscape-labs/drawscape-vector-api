from flask import Blueprint, jsonify
from flask_pydantic import validate
from pydantic import BaseModel, Field
from libraries.job_manager import enqueue_background_job, get_job_status

schematics_bp = Blueprint('schematics', __name__, url_prefix='/schematics')

class SchematicVectorOptimizeParams(BaseModel):
    svg_url: str = Field(
        ..., 
        description="URL to an SVG file on S3 to optimize",
        min_length=1,
        pattern=r"^https?://.*\.svg$"
    )
    schematic_vector_id: str = Field(
        ..., 
        description="String ID for the schematic vector",
        min_length=1,
        max_length=100
    )

@schematics_bp.route('/schematic-vector-optimize', methods=['POST'])
@validate()
def schematic_vector_optimize(body: SchematicVectorOptimizeParams):
    """
    Endpoint for optimizing schematic vectors from SVG files.
    
    Accepts JSON data containing:
        - svg_url: URL to an SVG file on S3 to optimize
        - schematic_vector_id: String ID for the schematic vector
    
    Returns:
        JSON object with the following fields:
            - status: 'success' or 'error'
            - message: Success or error message
            - job_id: Background job ID for tracking progress
            - data: Input parameters for reference
    """
    # Always print the SVG URL when endpoint is hit
    print(f"Processing schematic vector optimization for SVG URL: {body.svg_url}")
    
    # Queue the background job
    job = enqueue_background_job(
        'workers.svg_tasks.schematic_vector_optimize',
        svg_url=body.svg_url,
        schematic_vector_id=body.schematic_vector_id,
        job_timeout='10m'  # 10 minute timeout for optimization
    )
    
    print(f"Background job queued with ID: {job.id}")

    return jsonify({
        'status': 'success',
        'message': 'Schematic vector optimization job queued successfully',
        'job_id': job.id,
        'data': {
            'svg_url': body.svg_url,
            'schematic_vector_id': body.schematic_vector_id
        }
    })
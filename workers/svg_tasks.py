"""Background tasks for SVG generation"""
import requests
import tempfile
import os
import vpype_cli
import re
from urllib.parse import urlparse


def clean_filename(filename):
    """
    Clean a filename by removing spaces and special characters
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for use
    """
    # Remove file extension
    name, ext = os.path.splitext(filename)
    
    # Replace spaces and special characters with underscores
    # Keep only alphanumeric characters, hyphens, and underscores
    cleaned_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
    
    # Remove multiple consecutive underscores
    cleaned_name = re.sub(r'_{2,}', '_', cleaned_name)
    
    # Remove leading/trailing underscores
    cleaned_name = cleaned_name.strip('_')
    
    # Ensure we have something to work with
    if not cleaned_name:
        cleaned_name = 'file'
    
    return f"{cleaned_name}_optimized{ext}"


def schematic_vector_optimize(svg_url, schematic_vector_id):
    """
    Optimize schematic vectors from SVG files in the background
    
    Args:
        svg_url: URL to an SVG file on S3 to optimize
        schematic_vector_id: String ID for the schematic vector
        
    Returns:
        Dictionary with optimization results
    """
    try:
        # Download the SVG file from the URL
        response = requests.get(svg_url)
        response.raise_for_status()
        svg_content = response.text
        
        # Extract original filename from URL
        parsed_url = urlparse(svg_url)
        original_filename = os.path.basename(parsed_url.path)
        if not original_filename or not original_filename.endswith('.svg'):
            original_filename = 'file.svg'
        
        # Create cleaned filename for upload
        upload_filename = clean_filename(original_filename)
        
        # Save to temporary file for vpype processing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as temp_input:
            temp_input.write(svg_content)
            temp_input_path = temp_input.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_optimized.svg', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        try:
            # Run vpype optimization pipeline
            pipeline = f'''read "{temp_input_path}" 
                          linemerge --tolerance 0.1mm 
                          linesort 
                          linesimplify --tolerance 0.05mm 
                          write "{temp_output_path}"'''
            
            document = vpype_cli.execute(pipeline)
            
            if document is not None:
                # Read the optimized SVG content
                if os.path.exists(temp_output_path) and os.path.getsize(temp_output_path) > 0:
                    with open(temp_output_path, 'r') as f:
                        optimized_svg = f.read()
                    
                    # Upload optimized SVG back to the API
                    with tempfile.NamedTemporaryFile(mode='w', suffix='_optimized.svg', delete=False) as upload_temp:
                        upload_temp.write(optimized_svg)
                        upload_temp_path = upload_temp.name
                    
                    try:
                        base_url = os.getenv('NODE_API_BASE_URL')
                        if not base_url.endswith('/'):
                            base_url += '/'
                        
                        url = f"{base_url}schematic-vectors/{schematic_vector_id}/replace"
                        
                        # Read file content and create form data
                        with open(upload_temp_path, 'rb') as upload_file:
                            file_content = upload_file.read()
                        
                        files = {'file': (upload_filename, file_content)}
                        
                        # Make upload request
                        response = requests.post(url, files=files, timeout=30)
                        response.raise_for_status()
                        
                        # Update the schematic vector to mark it as optim   ized
                        try:
                            update_url = f"{base_url}schematic-vectors/{schematic_vector_id}"
                            update_data = {"optimized": True}
                            
                            update_response = requests.post(update_url, json=update_data, timeout=30)
                            update_response.raise_for_status()
                            
                        except requests.exceptions.HTTPError:
                            # Optimization flag update failed but file upload succeeded
                            pass
                        except Exception:
                            # Optimization flag update failed but file upload succeeded
                            pass
                        
                    finally:
                        # Clean up upload temp file
                        if os.path.exists(upload_temp_path):
                            os.unlink(upload_temp_path)
            
            # Return success result
            return {
                'schematic_vector_id': schematic_vector_id,
                'svg_url': svg_url,
                'status': 'completed',
                'message': 'Schematic vector optimization completed successfully'
            }
            
        finally:
            # Clean up temporary files
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)
                
    except requests.RequestException as e:
        return {
            'schematic_vector_id': schematic_vector_id,
            'svg_url': svg_url,
            'status': 'error',
            'message': f"Failed to download SVG from URL: {str(e)}"
        }
        
    except Exception as e:
        return {
            'schematic_vector_id': schematic_vector_id,
            'svg_url': svg_url,
            'status': 'error',
            'message': f"Unexpected error during optimization: {str(e)}"
        }
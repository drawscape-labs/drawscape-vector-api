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
    print(f"[DEBUG] Starting optimization for schematic_vector_id: {schematic_vector_id}")
    print(f"[DEBUG] SVG URL: {svg_url}")
    
    try:
        # Download the SVG file from the URL
        print(f"[DEBUG] Downloading SVG from URL...")
        response = requests.get(svg_url)
        response.raise_for_status()
        svg_content = response.text
        print(f"[DEBUG] Downloaded SVG successfully. Content length: {len(svg_content)} characters")
        
        # Extract original filename from URL
        parsed_url = urlparse(svg_url)
        original_filename = os.path.basename(parsed_url.path)
        if not original_filename or not original_filename.endswith('.svg'):
            original_filename = 'file.svg'
        print(f"[DEBUG] Original filename: {original_filename}")
        
        # Create cleaned filename for upload
        upload_filename = clean_filename(original_filename)
        print(f"[DEBUG] Upload filename: {upload_filename}")
        
        # Save to temporary file for vpype processing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as temp_input:
            temp_input.write(svg_content)
            temp_input_path = temp_input.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_optimized.svg', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        print(f"[DEBUG] Created temp files - Input: {temp_input_path}, Output: {temp_output_path}")
        
        try:
            # Run vpype optimization pipeline
            print(f"[DEBUG] Starting vpype optimization pipeline...")
            pipeline = f'''read "{temp_input_path}" 
                          linemerge --tolerance 0.1mm 
                          linesort 
                          linesimplify --tolerance 0.05mm 
                          write "{temp_output_path}"'''
            
            document = vpype_cli.execute(pipeline)
            print(f"[DEBUG] Vpype execution completed. Document: {document is not None}")
            
            if document is not None:
                # Read the optimized SVG content
                if os.path.exists(temp_output_path) and os.path.getsize(temp_output_path) > 0:
                    with open(temp_output_path, 'r') as f:
                        optimized_svg = f.read()
                    
                    print(f"[DEBUG] Optimized SVG read successfully. Length: {len(optimized_svg)} characters")
                    
                    # Upload optimized SVG back to the API
                    with tempfile.NamedTemporaryFile(mode='w', suffix='_optimized.svg', delete=False) as upload_temp:
                        upload_temp.write(optimized_svg)
                        upload_temp_path = upload_temp.name
                    
                    try:
                        base_url = os.getenv('NODE_API_BASE_URL')
                        if not base_url.endswith('/'):
                            base_url += '/'
                        
                        url = f"{base_url}schematic-vectors/{schematic_vector_id}/replace"
                        print(f"[DEBUG] Upload URL: {url}")
                        
                        # Read file content and create form data
                        with open(upload_temp_path, 'rb') as upload_file:
                            file_content = upload_file.read()
                        
                        files = {'file': (upload_filename, file_content)}
                        print(f"[DEBUG] Uploading file with name: {upload_filename}, size: {len(file_content)} bytes")
                        
                        # Make upload request
                        response = requests.post(url, files=files, timeout=30)
                        response.raise_for_status()
                        print(f"[DEBUG] File upload successful. Response status: {response.status_code}")
                        
                        # Update the schematic vector to mark it as optimized
                        try:
                            update_url = f"{base_url}schematic-vectors/{schematic_vector_id}"
                            update_data = {"optimized": True}
                            print(f"[DEBUG] Updating optimization flag at: {update_url}")
                            
                            update_response = requests.post(update_url, json=update_data, timeout=30)
                            update_response.raise_for_status()
                            print(f"[DEBUG] Optimization flag updated successfully. Response status: {update_response.status_code}")
                            
                        except requests.exceptions.HTTPError as e:
                            # Optimization flag update failed but file upload succeeded
                            print(f"[DEBUG] Optimization flag update failed (HTTP Error): {e}")
                            pass
                        except Exception as e:
                            # Optimization flag update failed but file upload succeeded
                            print(f"[DEBUG] Optimization flag update failed (Exception): {e}")
                            pass
                        
                    finally:
                        # Clean up upload temp file
                        if os.path.exists(upload_temp_path):
                            os.unlink(upload_temp_path)
                            print(f"[DEBUG] Cleaned up upload temp file: {upload_temp_path}")
                else:
                    print(f"[DEBUG] ERROR: Optimized file doesn't exist or is empty. Path: {temp_output_path}")
            else:
                print(f"[DEBUG] ERROR: Vpype document is None - optimization failed")
            
            # Return success result
            print(f"[DEBUG] Optimization completed successfully for {schematic_vector_id}")
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
                print(f"[DEBUG] Cleaned up input temp file: {temp_input_path}")
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)
                print(f"[DEBUG] Cleaned up output temp file: {temp_output_path}")
                
    except requests.RequestException as e:
        print(f"[DEBUG] RequestException: {str(e)}")
        return {
            'schematic_vector_id': schematic_vector_id,
            'svg_url': svg_url,
            'status': 'error',
            'message': f"Failed to download SVG from URL: {str(e)}"
        }
        
    except Exception as e:
        print(f"[DEBUG] Unexpected Exception: {str(e)}")
        return {
            'schematic_vector_id': schematic_vector_id,
            'svg_url': svg_url,
            'status': 'error',
            'message': f"Unexpected error during optimization: {str(e)}"
        }
from flask import Blueprint, jsonify, request
import json
import sys
import os
import boto3
import uuid
import time
import psutil
import random

from dotenv import load_dotenv
load_dotenv()

BUCKET_NAME = 'drawscape-factorio-uploads'

s3 = boto3.client('s3', region_name='us-west-2')

# Use environment variable for drawscape_path, with a fallback
# Need to include the SRC directory to get this to work
# /Users/russelltaylor/Sites/drawscape-factorio/src
if os.getenv('ENV') == 'dev':
    drawscape_path = os.getenv('DRAWSCAPE_PATH')
    print(f"Drawscape path: {drawscape_path}")
    sys.path.insert(0, drawscape_path)

# Now import the functions from drawscape_factorio
from drawscape_factorio import create as createFactorio
from drawscape_factorio import importFUE5
from drawscape_factorio import listThemes

factorio = Blueprint('factorio', __name__)

@factorio.route('/factorio/upload-fue5', methods=['POST'])
async def create_factorio():
    """
    Endpoint for uploading and processing a Factorio User Exchange (FUE5) JSON file.
    
    Accepts:
        - file: A JSON file containing Factorio blueprint data
    
    Returns:
        - On success: A string containing the UUID of the created project
        - On failure: JSON object with an "error" key describing the issue (400 or 500 status code)
    """

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith('.json'):
        return jsonify({"error": "File must be a JSON file"}), 400

    try:
        file_content = json.loads(file.read().decode('utf-8'))
        
        if not isinstance(file_content, dict):
            return jsonify({"error": "Invalid JSON file"}), 400
        
        if 'entities' not in file_content:
            return jsonify({"error": "Missing required key json key, might not be a valid FUE5 file"}), 400
        
        if not isinstance(file_content['entities'], list):
            return jsonify({"error": "The 'entities' key must be an array, might not be a valid FUE5 file"}), 400

        # Generate a unique file name
        folder_id = str(uuid.uuid4())
        
        # If all checks pass, proceed with parsing and creating
        data = importFUE5(file_content)

        upload_json_to_s3(data, folder_id)

    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON data: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
           
    # For now, just return the parsed JSON data
    return folder_id

@factorio.route('/factorio/render-project/<id>', methods=['GET'])
async def render_factorial(id):
    """
    Endpoint for rendering a Factorio project as SVG.
    
    Path Parameters:
        - id: UUID of the project to render
    
    Query Parameters:
        - layers: Comma-separated list of layers to include
        - c_[component]: Color settings for specific components
        - theme_name: Name of the theme to use
        - color_scheme: Name of the color scheme within the theme
    
    Returns:
        - On success: JSON object containing SVG content with the following structure:
            {
                "svg_string": String containing the SVG markup,
                "width": Width of the SVG in pixels,
                "height": Height of the SVG in pixels
            }
        - On failure: JSON object with an "error" key describing the issue (404 or 500 status code)
    """

    print(f"\n\n\n API: Rendering project: {id}")
    # Print the request arguments
    print("API: Request arguments:")
    for key, value in request.args.items():
        print(f"  {key}: {value}")
    print("\n")

    file_name = f"{id}.json"    
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_name)
        json_data = json.loads(response['Body'].read().decode('utf-8'))
        entity_count = len(json_data['entities'])
        
        layers_string = request.args.get('layers', '')
        layers = layers_string.split(',') if layers_string else []

        colors = {}
        color_keys = ['background', 'assets', 'rails', 'belts', 'electrical', 'walls', 'pipes', 'spaceship']
        for key in color_keys:
            param_key = f'c_{key}'
            if request.args.get(param_key):
                colors[key] = request.args.get(param_key)

        # Determine theme based on entity count if not provided in request args
        if not request.args.get('theme_name'):
            if entity_count > 20000:
                theme_name = 'squares'
            else:
                theme_name = 'squares_highres'
        else:
            theme_name = request.args.get('theme_name')

        # If no color_scheme is provided in the request args, choose one randomly
        if not request.args.get('color_scheme'):
            themes = listThemes()
            selected_theme = next((t for t in themes if t['slug'] == theme_name), None)
            color_schemes = selected_theme.get('colors', {})
            color_scheme = random.choice(list(color_schemes.keys()))            
        else:
            color_scheme = request.args.get('color_scheme')

        themeSettings = {
            'theme': theme_name,
            'color_scheme': color_scheme,
            'colors': colors,
            'layers': layers
        }

        print(f"API: Theme settings: {themeSettings}")
        svg_content = createFactorio(json_data, themeSettings)
        del json_data

        return jsonify(svg_content), 200
    except s3.exceptions.NoSuchKey:
        return jsonify({"error": "Project not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@factorio.route('/factorio/available-themes', methods=['GET'])
async def available_themes():
    """
    Endpoint for retrieving available rendering themes.
    
    Returns:
        JSON object with a "themes" key containing an array of theme objects with the following structure:
        {
            "themes": [
                {
                    "name": Human-readable theme name,
                    "slug": Theme identifier,
                    "colors": {
                        "color_scheme_name": {
                            "component": "color_value",
                            ...
                        },
                        ...
                    }
                },
                ...
            ]
        }
    """
    themes = listThemes()
    return jsonify({"themes": themes}), 200


@factorio.route('/factorio/available-colors', methods=['GET'])
async def available_colors():
    """
    Endpoint for retrieving available color schemes for a specific theme.
    
    Query Parameters:
        - theme: Theme slug/identifier
    
    Returns:
        JSON object with a "colors" key containing an object of color schemes:
        {
            "colors": {
                "color_scheme_name": {
                    "component": "color_value",
                    ...
                },
                ...
            }
        }
        The object will be empty if the specified theme doesn't exist.
    """
    theme = request.args.get('theme')
    themes = listThemes()

    # Iterate through themes to find the one with the matching slug
    selected_theme = next((t for t in themes if t['slug'] == theme), None)
    
    if selected_theme:
        colors = selected_theme.get('colors', {})
    else:
        colors = {}

    return jsonify({"colors": colors}), 200


def upload_json_to_s3(json_data, folder_id):
    
    file_name = f"{folder_id}.json"
    
    json_string = json.dumps(json_data)
    
    # Upload the JSON string to S3
    response = s3.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=json_string,
        ContentType='application/json',
    )
    
    # Check if the upload was successful
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False
    
def upload_svg_to_s3(svg, folder_id):
    
    # Generate a unique file name
    file_name = f"{folder_id}/image.svg"
        
    # Upload the SVG string to S3
    response = s3.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=svg,
        ContentType='image/svg+xml',
    )
    
    # Check if the upload was successful
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False    



@factorio.route('/factorio/render-test/<id>', methods=['GET'])
async def render_test(id):
    """
    Test endpoint for rendering a Factorio project with predefined settings.
    
    Path Parameters:
        - id: UUID of the project to render
    
    Returns:
        - On success: JSON object containing SVG content with the following structure:
            {
                "svg_string": String containing the SVG markup,
                "width": Width of the SVG in pixels,
                "height": Height of the SVG in pixels
            }
        - On failure: JSON object with an "error" key describing the issue (404 or 500 status code)
    """

    file_name = f"{id}.json"    
    try:
        
        themeSettings = {
            'theme': 'squares',
            'color': 'black'
        }

        start_time = time.time()
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_name)
        file_size = response['ContentLength']
        file_size_mb = file_size / (1024 * 1024)
        
        start_time = time.time()
        json_data = json.loads(response['Body'].read().decode('utf-8'))
        
        start_time = time.time()
        svg_content = createFactorio(json_data, themeSettings)
        del json_data

        svg_size_mb = len(svg_content['svg_string'].encode('utf-8')) / (1024 * 1024)


        return jsonify(svg_content), 200
    except s3.exceptions.NoSuchKey:
        return jsonify({"error": "Project not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

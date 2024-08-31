from flask import Blueprint, jsonify, request
import json
import sys
import os
import boto3
import uuid

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
from drawscape_factorio import parseFUE5

factorio = Blueprint('factorio', __name__)

@factorio.route('/factorio/upload-fue5', methods=['POST'])
async def create_factorio():

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
        data = parseFUE5(file_content)
        svg = createFactorio(data)

        upload_json_to_s3(file_content, folder_id)        
        upload_svg_to_s3(svg["svg_string"], folder_id)

    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON data: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
           
    # For now, just return the parsed JSON data
    print(f"Uploaded to S3: {folder_id}")
    return folder_id


@factorio.route('/factorio/render-project/<id>', methods=['GET'])
async def render_factorial(id):
    file_name = f"{id}/image.svg"    
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_name)
        svg_content = response['Body'].read().decode('utf-8')
        
        return jsonify({"svg": svg_content}), 200
    except s3.exceptions.NoSuchKey:
        return jsonify({"error": "SVG not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500



def upload_json_to_s3(json_data, folder_id):
    
    file_name = f"{folder_id}/export.json"
    
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
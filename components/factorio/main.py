from flask import Blueprint, jsonify, request
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
def create_factorio():
    # print('data', request.data)
    # print('files', request.files)
    # print('form', request.form)

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
        
        # If all checks pass, proceed with parsing and creating
        data = parseFUE5(file_content)
        svg = createFactorio(data)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON data: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
           
    # For now, just return the parsed JSON data
    return svg["svg_string"]

@factorio.route('/factorio/hello-world', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello World"})
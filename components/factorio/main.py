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

@factorio.route('/factorio/create', methods=['POST'])
def create_factorio():
    if not request.data:
        return jsonify({"error": "No file data in the request"}), 400

    try:
        file_content = json.loads(request.data)
        data = parseFUE5(file_content)
        svg = createFactorio(data)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON data"}), 400
           
    # For now, just return the parsed JSON data
    return svg["svg_string"]
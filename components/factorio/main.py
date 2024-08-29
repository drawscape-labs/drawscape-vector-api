from flask import Blueprint, jsonify, request
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("DRAWSCAPE_PATH")
print(os.getenv('DRAWSCAPE_PATH'))
print("ENV")
print(os.getenv('ENV'))

# Use environment variable for drawscape_path, with a fallback
drawscape_path = os.getenv('DRAWSCAPE_PATH', os.path.expanduser("~/Sites/factorio-cli/src/drawscape_factorio"))
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
       
    
    
    # Process the file content (e.g., pass it to createFactorio)
    # result = createFactorio(file_content)
    
    # For now, just return the parsed JSON data
    return svg["svg_string"]
    return jsonify({
        "result": "Received and parsed JSON data successfully",
        "data": svg
    })
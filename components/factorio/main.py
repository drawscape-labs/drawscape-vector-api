from flask import Blueprint, jsonify, request
import json
import sys
import os
import boto3
import uuid
import time
import psutil
#import subprocess
# import gc
# import tracemalloc

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
    print(f"Uploaded to S3: {folder_id}")
    return folder_id

@factorio.route('/factorio/render-project/<id>', methods=['GET'])
async def render_factorial(id):

    # Start tracking memory allocations
    # tracemalloc.start()

    # Take a snapshot after some memory-intensive operations
    # snapshot1 = tracemalloc.take_snapshot()
    # print(f"API: Memory snapshot 1: {snapshot1}")

    print(f"\n\n\n API: Rendering project: {id}")

    # process = psutil.Process()
    # memory_usage = process.memory_info().rss  # in bytes
    # print(f"--Memory API Start: {memory_usage / 1024 ** 2} MB")    

    file_name = f"{id}.json"    
    try:
        
        themeSettings = {
            'theme': request.args.get('theme_name',),
            'color': request.args.get('color_scheme'),
            'layers': request.args.getlist('show_layers')
        }
        # print(f"API: Theme settings: {themeSettings}")        

        start_time = time.time()
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_name)
        file_size = response['ContentLength']
        file_size_mb = file_size / (1024 * 1024)
        print(f"API: Size of file coming from S3: {file_size_mb:.2f} MB")
        print(f"API: Time to get object from S3: {time.time() - start_time} seconds")
        
        start_time = time.time()
        json_data = json.loads(response['Body'].read().decode('utf-8'))
        print(f"API: Time to load JSON data: {time.time() - start_time} seconds")
        
        start_time = time.time()
        svg_content = createFactorio(json_data, themeSettings)
        del json_data
        print(f"API: Time to create SVG content: {time.time() - start_time} seconds")

        svg_size_mb = len(svg_content['svg_string'].encode('utf-8')) / (1024 * 1024)
        print(f"API: Size of SVG content: {svg_size_mb:.2f} MB")

        # memory_usage = process.memory_info().rss  # in bytes
        # print(f"--Memory API End: {memory_usage / 1024 ** 2} MB")    

        # # Run another memory-heavy operation
        # snapshot2 = tracemalloc.take_snapshot()
        # # Compare snapshots and show the differences
        # top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        # # Get statistics by traceback (to see what's holding memory)
        # stats = snapshot2.statistics('traceback')

        # print(f"Top 10 memory blocks:")
        # for stat in stats[:10]:
        #     print(stat)
        #     # Print the traceback of the allocation
        #     for line in stat.traceback.format():
        #         print(line)

        # print("[ Top 10 memory allocations ]")
        # for stat in top_stats[:10]:
        #     print(stat)

        # tracemalloc.stop()

        return jsonify(svg_content), 200
    except s3.exceptions.NoSuchKey:
        return jsonify({"error": "Project not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@factorio.route('/factorio/available-themes', methods=['GET'])
async def available_themes():
    themes = listThemes()
    return jsonify({"themes": themes}), 200


@factorio.route('/factorio/available-colors', methods=['GET'])
async def available_colors():
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

    print(f"\n\n\n API: Rendering test")
    print(f"virtual_memory: {(psutil.virtual_memory().total - psutil.virtual_memory().available) / (1024 * 1024):.2f} MB")

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
        print(f"API: Size of file coming from S3: {file_size_mb:.2f} MB")
        print(f"API: Time to get object from S3: {time.time() - start_time} seconds")
        
        start_time = time.time()
        json_data = json.loads(response['Body'].read().decode('utf-8'))
        print(f"API: Time to load JSON data: {time.time() - start_time} seconds")
        
        start_time = time.time()
        svg_content = createFactorio(json_data, themeSettings)
        del json_data
        print(f"API: Time to create SVG content: {time.time() - start_time} seconds")

        svg_size_mb = len(svg_content['svg_string'].encode('utf-8')) / (1024 * 1024)
        print(f"API: Size of SVG content: {svg_size_mb:.2f} MB")


        return jsonify(svg_content), 200
    except s3.exceptions.NoSuchKey:
        return jsonify({"error": "Project not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

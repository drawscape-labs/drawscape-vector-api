import os
import json
import requests
import tempfile
from flask import Blueprint, request, jsonify
from datetime import datetime
from HersheyFonts import HersheyFonts
from nextdraw import NextDraw

blueprint_bp = Blueprint('blueprint', __name__, url_prefix='/blueprint')

# Paper sizes in millimeters (width, height)
PAPER_SIZES = {
    'a3': (297, 420),
    'a4': (210, 297),
    'letter': (216, 279),
    'tabloid': (279.4, 431.8)
}

def container(json_data, svg_file_path):
    thefont = HersheyFonts()
    thefont.load_default_font('futural')

    # Default to tabloid size if no size specified
    size = 'tabloid'

    if size in PAPER_SIZES:
        DOCUMENT_WIDTH, DOCUMENT_HEIGHT = PAPER_SIZES[size]
    else:
        print("Cannot find the specified paper size. Defaulting to tabloid size.")
        DOCUMENT_WIDTH, DOCUMENT_HEIGHT = PAPER_SIZES['tabloid']

    if size in ['a3', 'tabloid']:
        # Constants for A3 and Tabloid
        BORDER_INSET = 12
        INTERNAL_PADDING = 8
        
        LEGEND_CELL_HEIGHT = 8
        LEGEND_PADDING = 10
        LEGEND_TEXT_SCALE_FACTOR = 0.13
        
    else:
        # Constants for A4 and Letter
        BORDER_INSET = 8
        INTERNAL_PADDING = 6
        
        LEGEND_CELL_HEIGHT = 6
        LEGEND_PADDING = 8
        LEGEND_TEXT_SCALE_FACTOR = 0.1
        
    # Stroke Widths
    TEXT_STROKE_WIDTH = "0.9"
    LEGEND_STROKE_WIDTH = "0.6"
    
    # Legend Dimensions
    LEGEND_START_X = BORDER_INSET + INTERNAL_PADDING
    LEGEND_START_Y = BORDER_INSET + INTERNAL_PADDING
        
    # Hard code legend details with today's date as the first element
    today_date = datetime.now().strftime("%Y-%m-%d")

    title_text = json_data.get('title', '')
    subtitle_text = json_data.get('subtitle', '')
    combined_title = f"{title_text} - {subtitle_text}" if subtitle_text else title_text
    print(combined_title)

    # Extract order ID and artist name
    order_id = json_data.get('order_id', '')
    artist_name = json_data.get('artist_name', '')

    # Load the SVG file and extract the time estimate
    nd1 = NextDraw()
    nd1.plot_setup(svg_file_path)
    nd1.options.preview = True
    nd1.options.report_time = True
    nd1.options.model = 9  # https://bantam.tools/nd_py/#model
    nd1.options.pen_rate_lower = 10
    nd1.options.pen_rate_upper = 10
    nd1.options.speed_pendown = 30
    nd1.options.speed_penup = 50
    nd1.plot_run()

    time_estimate_seconds = nd1.time_estimate
    hours, remainder = divmod(time_estimate_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        time_estimate = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    else:
        time_estimate = f"{int(minutes)}m {int(seconds)}s"

    # Convert pen travel distance from meters to feet
    distance_pendown_m = nd1.distance_pendown
    distance_pendown_ft = distance_pendown_m * 3.28084

    legend_details = [
        {'name': 'Date', 'detail': today_date},
        {'name': 'Project', 'detail': combined_title},
    ]
    
    # Conditionally add order ID and artist if they exist
    if order_id:
        legend_details.append({'name': 'Order ID', 'detail': order_id})
    if artist_name:
        legend_details.append({'name': 'Artist', 'detail': artist_name})
    
    # Add the remaining standard fields
    legend_details.extend([
        {'name': 'Draw Time', 'detail': f"{time_estimate}"},
        {'name': 'Pen Travel', 'detail': f"{distance_pendown_ft:.1f} ft / {distance_pendown_m:.1f} m"},
        {'name': 'Plotted By', 'detail': 'Drawscape Inc.'},
        {'name': 'Website', 'detail': 'https://drawscape.io'},
    ])
    
    # Start SVG content with XML declaration and dimensions with viewBox
    svg_content = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg_content += f'<svg width="{DOCUMENT_WIDTH}mm" height="{DOCUMENT_HEIGHT}mm" viewBox="0 0 {DOCUMENT_WIDTH} {DOCUMENT_HEIGHT}" xmlns="http://www.w3.org/2000/svg">\n'
        
    # Calculate the width of the widest label name and label detail
    max_name_width = float('-inf')
    max_detail_width = float('-inf')
    for spec in legend_details:
        # Calculate bounding box for name
        min_x, max_x = float('inf'), float('-inf')
        for line in thefont.lines_for_text(spec["name"]):
            for x, y in line:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
        name_width = max_x - min_x
        max_name_width = max(max_name_width, name_width)

        # Calculate bounding box for detail
        min_x, max_x = float('inf'), float('-inf')
        for line in thefont.lines_for_text(spec["detail"]):
            for x, y in line:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
        detail_width = max_x - min_x
        max_detail_width = max(max_detail_width, detail_width)

    # Calculate the legend width based on the widest text with increased padding
    name_column_width = max_name_width * LEGEND_TEXT_SCALE_FACTOR + LEGEND_PADDING
    detail_column_width = max_detail_width * LEGEND_TEXT_SCALE_FACTOR + LEGEND_PADDING
    legend_width = name_column_width + detail_column_width

    # Recalculate legend dimensions
    legend_height = len(legend_details) * LEGEND_CELL_HEIGHT

    # Add 2 column legend outline with labels
    svg_content += f'  <g id="legend" fill="none" stroke="black" stroke-width="{LEGEND_STROKE_WIDTH}">\n'
    svg_content += '    <title>Legend</title>\n'
    svg_content += f'    <rect id="legend-border" x="{LEGEND_START_X}" y="{LEGEND_START_Y}" width="{legend_width}" height="{legend_height}" />\n'
    svg_content += f'    <line id="legend-column-divider" x1="{LEGEND_START_X + name_column_width}" y1="{LEGEND_START_Y}" x2="{LEGEND_START_X + name_column_width}" y2="{LEGEND_START_Y + legend_height}" />\n'
    for i, spec in enumerate(legend_details):
        y = LEGEND_START_Y + i * LEGEND_CELL_HEIGHT
        svg_content += f'    <line id="legend-row-divider-{i}" x1="{LEGEND_START_X}" y1="{y + LEGEND_CELL_HEIGHT}" x2="{LEGEND_START_X + legend_width}" y2="{y + LEGEND_CELL_HEIGHT}" />\n'
        text_y = y + (LEGEND_CELL_HEIGHT / 2)
        svg_content += f'    <g id="legend-label-{i}-name" transform="translate({LEGEND_START_X + 2}, {text_y}) scale({LEGEND_TEXT_SCALE_FACTOR})">\n'
        for line in thefont.lines_for_text(spec["name"]):
            path_data = "M" + " L".join(f"{x},{y}" for x, y in line)
            svg_content += f'      <path d="{path_data}" fill="none" stroke="black" stroke-width="{TEXT_STROKE_WIDTH}" />\n'
        svg_content += '    </g>\n'
        svg_content += f'    <g id="legend-label-{i}-detail" transform="translate({LEGEND_START_X + name_column_width + 2}, {text_y}) scale({LEGEND_TEXT_SCALE_FACTOR})">\n'
        for line in thefont.lines_for_text(spec["detail"]):
            path_data = "M" + " L".join(f"{x},{y}" for x, y in line)
            svg_content += f'      <path d="{path_data}" fill="none" stroke="black" stroke-width="{TEXT_STROKE_WIDTH}" />\n'
        svg_content += '    </g>\n'
    svg_content += '  </g>\n'
    svg_content += '</svg>\n'
    
    return svg_content


@blueprint_bp.route('/generate-label', methods=['POST'])
def generate_label():
    """
    Endpoint for generating a label with project details for a blueprint.
    
    Accepts JSON data containing:
        - project_name: Name of the project to display on the label
        - svg_url: URL to an SVG file to analyze for drawing time and pen travel distance
        - order_id: (Optional) Order ID to display on the label
        - artist_name: (Optional) Artist name to display on the label
    
    Returns:
        JSON object with the following fields:
            - status: 'success' or 'error'
            - svg_string: SVG content string (on success)
            - message: Error message (on error)
        
        The SVG content includes a legend with:
            - Date
            - Project name/title
            - Order ID (if provided)
            - Artist name (if provided)
            - Drawing time estimate
            - Pen travel distance
            - Designer information
            - Website information
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No input data provided.'
        }), 400

    project_name = data.get('project_name')
    svg_url = data.get('svg_url')
    order_id = data.get('order_id')
    artist_name = data.get('artist_name')

    missing_fields = []
    if not project_name:
        missing_fields.append('project_name')
    if not svg_url:
        missing_fields.append('svg_url')
    if missing_fields:
        return jsonify({
            'status': 'error',
            'message': f"Missing field(s): {', '.join(missing_fields)}"
        }), 400

    # Download the SVG file from the provided S3 URL
    try:
        response = requests.get(svg_url)
        if response.status_code != 200:
            return jsonify({'status': 'error', 'message': 'Failed to download SVG from provided URL.'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Exception occurred while downloading SVG: {str(e)}'}), 500

    # Write the downloaded SVG content to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
        tmp.write(response.content)
        temp_svg_path = tmp.name

    # Update the data to include all the project details
    data['title'] = project_name
    data.setdefault('subtitle', '')
    if order_id:
        data['order_id'] = order_id
    if artist_name:
        data['artist_name'] = artist_name

    # Generate the SVG content using the container function
    svg_content = container(data, temp_svg_path)

    # Optionally remove the temporary SVG file
    os.remove(temp_svg_path)

    return jsonify({
        'status': 'success',
        'svg_string': svg_content
    })
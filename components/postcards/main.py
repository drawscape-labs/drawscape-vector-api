from flask import Blueprint, jsonify, Response, request
from flask_pydantic import validate
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, List, Any
from libraries.svg_builder import SVGBuilder

# Blueprint definition
postcards_bp = Blueprint('postcards', __name__, url_prefix='/postcards')

# Constants
POSTCARD_WIDTH = 152.4  # 6 inches in mm
POSTCARD_HEIGHT = 101.6  # 4 inches in mm
ADDRESS_SIZE = 0.15  # Size for all address text
MARGIN = 0  # Margin from the left edge in mm
LINE_SPACING = 6  # Spacing between lines in mm
STAMP_WIDTH = 22.1  # Width of standard US stamp in mm (0.87 inches)
STAMP_HEIGHT = 24.9  # Height of standard US stamp in mm (0.98 inches)
STAMP_MARGIN = 10  # Margin from edges for stamp placement in mm
FROM_MARGIN = 10  # Margin from edges for FROM address in mm

# Sender information
FROM_NAME = "Drawscape"
FROM_ADDRESS = "Truckee, CA"


class PostcardLabelParams(BaseModel):
    """
    Parameters for generating a 6x4 inch postcard label
    """
    name: str = Field("", max_length=100, description="Recipient name (optional)")
    address_line_1: str = Field(..., max_length=100, description="First line of the address")
    address_line_2: str = Field("", max_length=100, description="Second line of the address (optional)")
    city: str = Field(..., max_length=50, description="City name")
    state: str = Field(..., max_length=2, description="State code (2-character)")
    zipcode: str = Field(..., max_length=10, description="ZIP code")
    country: str = Field("", max_length=100, description="Country (optional)")


def add_from_address(svg: SVGBuilder) -> None:
    """
    Adds the sender's address to the postcard
    
    Args:
        svg: SVGBuilder instance
    """
    svg.begin_group({'id': 'from-address'})
    from_x = FROM_MARGIN
    from_y = FROM_MARGIN + LINE_SPACING
    
    # Add FROM name
    svg.hershey_text(from_x, from_y, FROM_NAME, ADDRESS_SIZE, {
        'stroke': 'black',
        'stroke-width': '0.5'
    })
    
    # Add FROM address
    from_y += LINE_SPACING
    svg.hershey_text(from_x, from_y, FROM_ADDRESS, ADDRESS_SIZE, {
        'stroke': 'black',
        'stroke-width': '0.5'
    })
    
    svg.end_group()


def get_address_lines(params: PostcardLabelParams) -> List[str]:
    """
    Extracts all address lines from the parameters
    
    Args:
        params: PostcardLabelParams object
        
    Returns:
        List of address text lines
    """
    text_lines = []
    
    # Add name if provided
    if params.name:
        text_lines.append(params.name)
    
    # Add address lines
    text_lines.append(params.address_line_1)
    
    if params.address_line_2:
        text_lines.append(params.address_line_2)
    
    # Add city, state, zip
    city_state_zip = f"{params.city}, {params.state} {params.zipcode}"
    text_lines.append(city_state_zip)
    
    # Add country if provided
    if params.country:
        text_lines.append(params.country)
    
    return text_lines


def calculate_address_positioning(svg: SVGBuilder, text_lines: List[str]) -> Dict[str, Any]:
    """
    Calculates the positioning and dimensions of address text
    
    Args:
        svg: SVGBuilder instance
        text_lines: List of text lines to render
        
    Returns:
        Dictionary with positioning information
    """
    # Calculate bounding box for each line
    max_width = 0
    max_width_line = ""
    bounding_boxes = []
    
    for line in text_lines:
        bbox = svg.get_hershey_text_bounding_box(line)
        scaled_width = bbox['width'] * ADDRESS_SIZE
        bounding_boxes.append({
            'text': line,
            'width': scaled_width,
            'bbox': bbox
        })
        
        if scaled_width > max_width:
            max_width = scaled_width
            max_width_line = line
    
    # Calculate center position for the address group
    postcard_center_x = POSTCARD_WIDTH / 2
    postcard_center_y = POSTCARD_HEIGHT / 2
    
    # Calculate horizontal centering
    address_x = postcard_center_x - (max_width / 2)
    
    # Calculate vertical centering
    line_count = len(text_lines)
    total_height = line_count * LINE_SPACING
    address_y = postcard_center_y - (total_height / 2) + LINE_SPACING  # Add half line spacing to align properly
    
    return {
        'address_x': address_x,
        'address_y': address_y,
        'bounding_boxes': bounding_boxes,
        'max_width': max_width,
        'max_width_line': max_width_line,
        'line_count': line_count,
        'total_height': total_height
    }


def add_address_to_svg(svg: SVGBuilder, text_lines: List[str], positioning: Dict[str, Any]) -> None:
    """
    Adds the address text to the SVG
    
    Args:
        svg: SVGBuilder instance
        text_lines: List of text lines to render
        positioning: Dictionary with positioning information
    """
    # Create a group for the address
    svg.begin_group({'id': 'address'})
    
    # Starting position - centered horizontally and vertically
    x_pos = positioning['address_x']
    y_pos = positioning['address_y']
    
    # Add each line with information about its bounding box
    for i, line_info in enumerate(positioning['bounding_boxes']):
        svg.hershey_text(x_pos, y_pos, line_info['text'], ADDRESS_SIZE, {
            'stroke': 'black', 
            'stroke-width': '0.5'
        })
        
        # Add a comment with bounding box info (visible in SVG source only)
        svg._add_element(f'<!-- Line {i+1}: "{line_info["text"]}" - Width: {line_info["width"]:.2f}mm -->')
        
        y_pos += LINE_SPACING
    
    # Add a comment about the maximum width line and positioning
    svg._add_element(f'<!-- Maximum width line: "{positioning["max_width_line"]}" - Width: {positioning["max_width"]:.2f}mm -->')
    svg._add_element(f'<!-- Address centered at position: ({positioning["address_x"]:.2f}, {positioning["address_y"]:.2f})mm -->')
    svg._add_element(f'<!-- Line count: {positioning["line_count"]}, Total height: {positioning["total_height"]:.2f}mm -->')
    
    # End the address group
    svg.end_group()


def render_postcard_label(params: PostcardLabelParams) -> str:
    """
    Creates a 6x4 inch (152.4 x 101.6 mm) postcard SVG with address label
    
    Args:
        params: Validated PostcardLabelParams object containing address details
        
    Returns:
        SVG content as a string
    """
    # Create SVG (6x4 inches = 152.4 x 101.6 mm)
    svg = SVGBuilder(POSTCARD_WIDTH, POSTCARD_HEIGHT)
    
    # Add white background
    svg.rect(0, 0, POSTCARD_WIDTH, POSTCARD_HEIGHT, {'fill': 'white', 'stroke': 'none'})
    
    # Add stamp placeholder in top right corner
    stamp_x = POSTCARD_WIDTH - STAMP_WIDTH - STAMP_MARGIN
    stamp_y = STAMP_MARGIN
    svg.rect(stamp_x, stamp_y, STAMP_WIDTH, STAMP_HEIGHT, {
        'stroke': 'black', 
        'stroke-width': '0.5', 
        'stroke-dasharray': '2,1',
        'fill': 'none'
    })
    
    # Add from address
    add_from_address(svg)
    
    # Process address information
    text_lines = get_address_lines(params)
    positioning = calculate_address_positioning(svg, text_lines)
    add_address_to_svg(svg, text_lines, positioning)
    
    return svg.to_string()


@postcards_bp.route('/label', methods=['POST'])
def postcard_label() -> Response:
    """
    Endpoint for postcard label generation
    
    Accepts both JSON data and form data containing address information:
        - name: Recipient name (optional, max 100 chars)
        - address_line_1: First line of the address (required, max 100 chars)
        - address_line_2: Second line of the address (optional, max 100 chars)
        - city: City name (required, max 50 chars)
        - state: State code (required, 2 chars)
        - zipcode: ZIP code (required, max 10 chars)
        - country: Country name (optional, max 100 chars)
    
    Returns:
        SVG content for a 6x4 postcard with the address label
    """
    data = get_request_data()
    
    # If no data, return error
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided. Please send either JSON or form data with the required fields.'
        }), 400
    
    # Validate and process data
    try:
        body = PostcardLabelParams(**data)
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': f'Validation error: {str(e)}'
        }), 400
    
    # Generate SVG for the postcard
    svg_content = render_postcard_label(body)
    
    # Return SVG content with appropriate content type
    return Response(svg_content, mimetype='image/svg+xml')


def get_request_data() -> Dict[str, str]:
    """
    Extracts data from either JSON or form data in the request
    
    Returns:
        Dictionary with request data or empty dict if no data found
    """
    data = {}
    
    # Try to get data from JSON if content type is application/json
    if request.is_json:
        try:
            json_data = request.get_json(silent=True)
            if json_data:
                data = json_data
        except Exception:
            pass
    
    # If no JSON data, try to get data from form
    if not data and request.form:
        data = request.form.to_dict()
    
    return data
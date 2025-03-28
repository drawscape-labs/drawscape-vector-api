from flask import Response
from libraries.svg_builder import SVGBuilder
from components.artboard.helper import svg_test

def render_artboard(title: str):
    """
    Render an artboard as SVG.
    
    Args:
        title: The title to display on the artboard
    """
    # Get the SVG from the helper function
    svg = svg_test(title=title)
    
    # Return the SVG with proper content type
    return Response(svg.to_string(), mimetype='image/svg+xml')

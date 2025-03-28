from flask import Response, request
from libraries.svg_builder import SVGBuilder
from components.artboard.helper import render_test_svg, render_blueprint_svg


def render_blueprint(title="Blueprint", subtitle="", background_color="white", pen_color="black", size="tabloid", orientation="portrait", legend=None):
    """
    Render a blueprint as SVG.
    
    Args:
        title: The title to display on the blueprint
        subtitle: The subtitle to display on the blueprint
        background_color: The background color for the blueprint
        pen_color: The pen color for the blueprint
        size: Paper size ('a3', 'a4', 'letter', 'tabloid')
        orientation: Paper orientation ('portrait' or 'landscape')
        legend: List of legend items with label and content
    """
    # Get the SVG from the helper function
    svg = render_blueprint_svg(
        title=title,
        subtitle=subtitle,
        background_color=background_color,
        pen_color=pen_color,
        size=size,
        orientation=orientation,
        legend=legend or []
    )
    
    # Return the SVG with proper content type
    return Response(svg.to_string(), mimetype='image/svg+xml')



def render_test():
    """
    Render an artboard as SVG.
    
    Args:
        title: The title to display on the artboard
    """
    # Get the SVG from the helper function
    svg = render_test_svg()
    
    # Return the SVG with proper content type
    return Response(svg.to_string(), mimetype='image/svg+xml')

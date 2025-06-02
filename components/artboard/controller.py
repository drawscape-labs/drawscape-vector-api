from flask import Response, request, jsonify
from libraries.svg_builder import SVGBuilder
from components.artboard.helper import render_test_svg, render_blueprint_svg, render_airport_svg
import requests


def render_blueprint(title="Blueprint", subtitle="", paper_color="white", pen_color="black", size="tabloid", orientation="portrait", legend=None, schematic_url=None):
    """
    Render a blueprint as SVG.
    
    Args:
        title: The title to display on the blueprint
        subtitle: The subtitle to display on the blueprint
        paper_color: The paper color for the blueprint
        pen_color: The pen color for the blueprint
        size: Paper size ('a3', 'a4', 'letter', 'tabloid')
        orientation: Paper orientation ('portrait' or 'landscape')
        legend: List of legend items with label and content
        schematic_url: URL to an SVG file to include in the blueprint
    """
    # Download and parse the schematic SVG if URL is provided
    schematic_svg = None
    if schematic_url:
        try:
            response = requests.get(schematic_url)
            response.raise_for_status()
            schematic_svg = response.text
        except requests.RequestException as e:
            print(f"Error downloading schematic SVG: {e}")
            schematic_svg = None
    
    # Get the SVG from the helper function
    svg = render_blueprint_svg(
        title=title,
        subtitle=subtitle,
        paper_color=paper_color,
        pen_color=pen_color,
        size=size,
        orientation=orientation,
        legend=legend or [],
        schematic_svg=schematic_svg
    )
    
    # Return JSON with the SVG string instead of directly returning SVG content
    return jsonify({
        "status": "success",
        "svg_string": svg.to_string()
    })


def render_airport(title="Airport", subtitle="", paper_color="white", pen_color="black", size="tabloid", orientation="portrait", schematic_url=None):
    """
    Render an airport diagram as SVG.
    
    Args:
        title: The title to display on the airport diagram
        subtitle: The subtitle to display on the airport diagram
        paper_color: The paper color for the airport diagram
        pen_color: The pen color for the airport diagram
        size: Paper size ('a3', 'a4', 'letter', 'tabloid')
        orientation: Paper orientation ('portrait' or 'landscape')
        schematic_url: URL to an SVG file to include in the airport diagram
    """
    # Download and parse the schematic SVG if URL is provided
    schematic_svg = None
    if schematic_url:
        try:
            response = requests.get(schematic_url)
            response.raise_for_status()
            schematic_svg = response.text
        except requests.RequestException as e:
            print(f"Error downloading schematic SVG: {e}")
            schematic_svg = None
    
    # Get the SVG from the helper function
    svg = render_airport_svg(
        title=title,
        subtitle=subtitle,
        paper_color=paper_color,
        pen_color=pen_color,
        size=size,
        orientation=orientation,
        schematic_svg=schematic_svg
    )
    
    # Return JSON with the SVG string instead of directly returning SVG content
    return jsonify({
        "status": "success",
        "svg_string": svg.to_string()
    })


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

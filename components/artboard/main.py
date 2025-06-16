from flask import Blueprint
from flask_pydantic import validate
from pydantic import BaseModel, Field
from typing import List, Optional
from components.artboard.controller import render_test, render_blueprint, render_airport

artboard_bp = Blueprint('artboard', __name__, url_prefix='/artboard')

class LegendItem(BaseModel):
    label: str = Field(..., description="Label for the legend item")
    content: str = Field(..., description="Content for the legend item")

class RenderParams(BaseModel):
    render_style: str = Field(..., description="Render style ('blueprint' or 'airport'/'basic')")
    title: str = Field(default="Artboard", description="Title for the diagram")
    subtitle: str = Field(default="", description="Subtitle for the diagram")
    paper_color: str = Field(default="white", description="Paper color for the diagram")
    pen_color: str = Field(default="black", description="Pen color for the diagram")
    size: str = Field(default="tabloid", description="Paper size ('a3', 'a4', 'letter', 'tabloid')")
    orientation: str = Field(default="portrait", description="Paper orientation ('portrait' or 'landscape')")
    legend: Optional[List[LegendItem]] = Field(default=None, description="List of legend items to display (only used for blueprint style)")
    schematic_url: str = Field(default="", description="URL to an SVG file to include in the diagram")

@artboard_bp.route('/render', methods=['POST'])
@validate()
def artboard_render(body: RenderParams):
    """
    Endpoint for rendering diagrams as SVG based on style.
    
    Accepts JSON data including render_style, title, subtitle, colors, size, orientation, and optional legend items.
    
    Style options:
    - 'blueprint': Renders a blueprint-style diagram with optional legend
    - 'airport' or 'basic': Renders an airport-style diagram
    
    Returns:
        JSON object with the following structure:
        {
            "status": "success",
            "svg_string": String containing the SVG markup
        }
        The SVG content varies based on the selected style.
    """
    if body.render_style == "blueprint":
        legend_data = []
        if body.legend:
            legend_data = [{"label": item.label, "content": item.content} for item in body.legend]
        
        return render_blueprint(
            title=body.title,
            subtitle=body.subtitle,
            paper_color=body.paper_color,
            pen_color=body.pen_color,
            size=body.size,
            orientation=body.orientation,
            legend=legend_data,
            schematic_url=body.schematic_url
        )
    elif body.render_style in ["airport", "basic"]:
        return render_airport(
            title=body.title,
            subtitle=body.subtitle,
            paper_color=body.paper_color,
            pen_color=body.pen_color,
            size=body.size,
            orientation=body.orientation,
            schematic_url=body.schematic_url
        )
    else:
        return {"status": "error", "message": f"Invalid style '{body.render_style}'. Use 'blueprint', 'airport', or 'basic'."}

@artboard_bp.route('/render-svg-test', methods=['GET'])
def artboard_render_svg():
    """
    Endpoint for rendering an artboard test SVG.
    
    Returns:
        Response object with SVG content (mimetype='image/svg+xml')
        The SVG content is a sample test SVG containing:
        - Hershey font text samples
        - Basic shapes (rectangles, lines, circles)
        - Nested group elements
        - Standard text elements
    """
    
    return render_test()

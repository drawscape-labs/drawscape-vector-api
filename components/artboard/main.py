from flask import Blueprint
from flask_pydantic import validate
from pydantic import BaseModel, Field
from typing import List
from components.artboard.controller import render_test, render_blueprint

artboard_bp = Blueprint('artboard', __name__, url_prefix='/artboard')

class LegendItem(BaseModel):
    label: str = Field(..., description="Label for the legend item")
    content: str = Field(..., description="Content for the legend item")

class BlueprintTitleParams(BaseModel):
    title: str = Field(default="Blueprint", description="Title for the blueprint")
    subtitle: str = Field(default="", description="Subtitle for the blueprint")
    paper_color: str = Field(default="white", description="Paper color for the blueprint")
    pen_color: str = Field(default="black", description="Pen color for the blueprint")
    size: str = Field(default="tabloid", description="Paper size ('a3', 'a4', 'letter', 'tabloid')")
    orientation: str = Field(default="portrait", description="Paper orientation ('portrait' or 'landscape')")
    legend: List[LegendItem] = Field(default=[], description="List of legend items to display")
    schematic_url: str = Field(default="", description="URL to an SVG file to include in the blueprint")

@artboard_bp.route('/render-blueprint', methods=['POST'])
@validate()
def artboard_render_blueprint(body: BlueprintTitleParams):
    """
    Endpoint for rendering a factorio blueprint as SVG.
    
    Accepts JSON data including title, subtitle, colors, size, orientation, and legend items.
    
    Returns:
        JSON object with the following structure:
        {
            "status": "success",
            "svg_string": String containing the SVG markup
        }
        The SVG content is a blueprint-style diagram with title, subtitle, border, and optional
        schematic content from an external URL.
    """
    # Debug output: Print all parameters
    print("\n--- Render Blueprint Parameters ---")
    for field_name, field_value in body.dict().items():
        if isinstance(field_value, list) and field_name == "legend":
            print(f"{field_name}: {len(field_value)} items")
            for i, item in enumerate(field_value):
                print(f"  Legend Item {i+1}:")
                if hasattr(item, 'dict'):
                    # Item is a Pydantic model
                    for item_field, item_value in item.dict().items():
                        print(f"    {item_field}: {item_value}")
                else:
                    # Item is already a dictionary
                    for item_field, item_value in item.items():
                        print(f"    {item_field}: {item_value}")
        else:
            print(f"{field_name}: {field_value}")
    print("------------------------------------\n")
    
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

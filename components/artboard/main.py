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
    background_color: str = Field(default="white", description="Background color for the blueprint")
    pen_color: str = Field(default="black", description="Pen color for the blueprint")
    size: str = Field(default="tabloid", description="Paper size ('a3', 'a4', 'letter', 'tabloid')")
    orientation: str = Field(default="portrait", description="Paper orientation ('portrait' or 'landscape')")
    legend: List[LegendItem] = Field(default=[], description="List of legend items to display")


@artboard_bp.route('/render-blueprint', methods=['POST'])
@validate()
def artboard_render_blueprint(body: BlueprintTitleParams):
    """
    Endpoint for rendering a factorio blueprint as SVG.
    
    Accepts JSON data including title, subtitle, colors, size, orientation, and legend items.
    """
    legend_data = [{"label": item.label, "content": item.content} for item in body.legend]
    return render_blueprint(
        title=body.title,
        subtitle=body.subtitle,
        background_color=body.background_color,
        pen_color=body.pen_color,
        size=body.size,
        orientation=body.orientation,
        legend=legend_data
    )



@artboard_bp.route('/render-svg-test', methods=['GET'])
def artboard_render_svg():
    """
    Endpoint for rendering an artboard as SVG.
    
    Expects a 'title' parameter in the query string.
    """
    
    return render_test()

from flask import Blueprint
from flask_pydantic import validate
from pydantic import BaseModel, Field
from components.artboard.controller import render_artboard

class ArtboardParams(BaseModel):
    title: str = Field(..., description="Title for the artboard")

artboard_bp = Blueprint('artboard', __name__, url_prefix='/artboard')

@artboard_bp.route('/render-svg', methods=['GET'])
@validate()
def artboard_render_svg(query: ArtboardParams):
    """
    Endpoint for rendering an artboard as SVG.
    
    Validates that a 'title' parameter is provided as a string.
    """
    return render_artboard(title=query.title) 
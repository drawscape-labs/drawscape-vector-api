import pytest
import sys
import os

# Add the parent directory to the path so we can import from libraries
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libraries.svg_builder import SVGBuilder


class TestSVGBuilder:
    """Test suite for the SVGBuilder class"""
    
    def test_svg_creation_with_dimensions(self):
        """Test that we can create an SVG with specified dimensions"""
        svg = SVGBuilder(100, 200)
        
        assert svg.width == 100
        assert svg.height == 200
        assert svg.elements == []
        
    def test_adding_rectangle(self):
        """Test adding a rectangle to the SVG"""
        svg = SVGBuilder(100, 100)
        svg.rect(10, 20, 30, 40, {'fill': 'red', 'stroke': 'black'})
        
        # Check that an element was added
        assert len(svg.elements) == 1
        
        # Check the element contains expected values
        element = svg.elements[0]
        assert 'rect' in element
        assert 'x="10"' in element
        assert 'y="20"' in element
        assert 'width="30"' in element
        assert 'height="40"' in element
        assert 'fill="red"' in element
        assert 'stroke="black"' in element
        
    def test_svg_to_string_output(self):
        """Test the complete SVG output"""
        svg = SVGBuilder(100, 100)
        svg.rect(0, 0, 50, 50, {'fill': 'blue'})
        
        result = svg.to_string()
        
        # Check SVG structure
        assert result.startswith('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
        assert '<svg' in result
        assert 'width="100mm"' in result
        assert 'height="100mm"' in result
        assert 'viewBox="0 0 100 100"' in result
        assert '</svg>' in result
        
        # Check the rectangle is included
        assert '<rect x="0" y="0" width="50" height="50" fill="blue" />' in result
        
    def test_line_element(self):
        """Test adding a line element"""
        svg = SVGBuilder(100, 100)
        svg.line(10, 10, 90, 90, {'stroke': 'black', 'stroke-width': '2'})
        
        assert len(svg.elements) == 1
        element = svg.elements[0]
        assert 'line' in element
        assert 'x1="10"' in element
        assert 'y1="10"' in element
        assert 'x2="90"' in element
        assert 'y2="90"' in element
        
    def test_circle_element(self):
        """Test adding a circle element"""
        svg = SVGBuilder(100, 100)
        svg.circle(50, 50, 25, {'fill': 'none', 'stroke': 'black'})
        
        assert len(svg.elements) == 1
        element = svg.elements[0]
        assert 'circle' in element
        assert 'cx="50"' in element
        assert 'cy="50"' in element
        assert 'r="25"' in element
        
    def test_default_styles(self):
        """Test that default styles are applied to all elements"""
        default_styles = {'stroke': 'black', 'stroke-width': '1', 'fill': 'none'}
        svg = SVGBuilder(100, 100, default_styles)
        
        # Add a rect without any specific styles
        svg.rect(10, 10, 20, 20, {})
        
        element = svg.elements[0]
        assert 'stroke="black"' in element
        assert 'stroke-width="1"' in element
        assert 'fill="none"' in element
        
        # Add a rect with overriding styles
        svg.rect(40, 40, 20, 20, {'fill': 'red'})
        
        element = svg.elements[1]
        assert 'fill="red"' in element  # Override should take precedence
        assert 'stroke="black"' in element  # Default should still apply
        
    def test_text_escaping(self):
        """Test that special characters in text are properly escaped"""
        svg = SVGBuilder(100, 100)
        svg.text(50, 50, 'Test & <special> "chars"', {'font-size': '12'})
        
        element = svg.elements[0]
        assert '&amp;' in element
        assert '&lt;special&gt;' in element
        assert '&quot;chars&quot;' in element
        
    def test_groups(self):
        """Test grouping functionality"""
        svg = SVGBuilder(100, 100)
        
        # Add element outside group
        svg.rect(0, 0, 10, 10)
        
        # Start a group
        svg.begin_group({'transform': 'translate(50,50)'})
        svg.rect(0, 0, 20, 20)
        svg.circle(10, 10, 5)
        svg.end_group()
        
        # Add another element outside group
        svg.line(0, 0, 100, 100)
        
        # Should have 3 elements at root level (rect, group, line)
        assert len(svg.elements) == 3
        
        # Check the group structure in output
        result = svg.to_string()
        assert '<g transform="translate(50,50)">' in result
        assert '</g>' in result 
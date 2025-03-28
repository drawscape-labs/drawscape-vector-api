from libraries.svg_builder import SVGBuilder

def svg_test(title: str):
    """
    Creates a test SVG and returns the SVG object.
    
    Args:
        title: The title to display on the artboard
    """
    # Create a complex SVG with grouped elements using our SVGBuilder
    svg = SVGBuilder(400, 300, {'stroke': 'black', 'stroke-width': '0.5'})
    
    # Add a title for the entire SVG
    svg.title(title)
    
    # Add a background rectangle
    svg.rect(0, 0, 400, 300, {'fill': '#f0f0f0'})

    # Add title using Hershey font (already using 'futural' set during initialization)
    svg.hershey_text(50, 50, title, 0.4, {
        'stroke': '#d23',
        'stroke-width': '0.5',
        'fill': 'none'
    })

    svg.hershey_text_with_bbox(50, 100, "Hershey Fonts", 0.4, {
        'stroke': '#d23',
        'stroke-width': '0.5',
        'fill': 'none'
    })
    
    # Create a translated group for the main content
    svg.begin_group({'transform': 'translate(100,50)', 'id': 'main-content'})
    svg.title("main-content")
    
    # Add shapes to the group
    svg.rect(0, 0, 200, 200, {'fill': 'yellow', 'opacity': '0.8'})
    svg.line(0, 0, 200, 200, {'stroke': 'red', 'stroke-width': '2'})
    svg.line(0, 200, 200, 0, {'stroke': 'blue', 'stroke-width': '2'})
    
    # Create a nested group for circles
    svg.begin_group({'id': 'circles'})
    svg.circle(100, 100, 50, {'fill': 'green', 'opacity': '0.5'})
    svg.circle(60, 60, 20, {'fill': 'purple'})
    svg.circle(140, 140, 20, {'fill': 'orange'})
    svg.end_group()  # End the circles group
    
    # Add text to the main group
    svg.text(100, 230, title, {'font-family': 'Arial', 'font-size': '18px', 'text-anchor': 'middle'})
    
    svg.end_group()  # End the main group
    
    return svg

from libraries.svg_builder import SVGBuilder


# Paper sizes in millimeters (width, height)
PAPER_SIZES = {
    'a3': (297, 420),
    'a4': (210, 297),
    'letter': (216, 279),
    'tabloid': (279.4, 431.8)
}

def render_blueprint_svg(title="Blueprint", subtitle="", size='tabloid', orientation='portrait', paper_color="white", pen_color="black", legend=None, schematic_svg=None):
    """
    Create a blueprint SVG with the correct paper size and border.
    
    Args:
        title: Title to display on the blueprint
        subtitle: Subtitle to display on the blueprint
        size: Paper size ('a3', 'a4', 'letter', 'tabloid')
        orientation: Paper orientation ('portrait' or 'landscape')
        paper_color: Paper color for the blueprint
        pen_color: Pen color for the blueprint
        legend: List of legend items with label and content
        schematic_svg: SVG string to include in the blueprint
        
    Returns:
        SVGBuilder instance with the document and border set up
    """

    # Default to tabloid size if no size specified or if specified size is invalid
    if not size or size not in PAPER_SIZES:
        print(f"Cannot find the specified paper size '{size}'. Defaulting to tabloid size.")
        size = 'tabloid'

    # Document dimensions
    DOCUMENT_WIDTH, DOCUMENT_HEIGHT = PAPER_SIZES[size]
    
    # Swap document width and height if orientation is landscape
    if orientation.lower() == 'landscape':
        DOCUMENT_WIDTH, DOCUMENT_HEIGHT = DOCUMENT_HEIGHT, DOCUMENT_WIDTH
    
    # Border insets based on paper size
    BORDER_STROKE_WIDTH = 1
    BORDER_INSET = 12 if size in ['a3', 'tabloid'] else 8
    BORDER_WIDTH = DOCUMENT_WIDTH - (2 * BORDER_INSET)
    BORDER_HEIGHT = DOCUMENT_HEIGHT - (2 * BORDER_INSET)

    INTERNAL_PADDING = 8 # INTERNAL_PADDING: Standard distance between all content and the border
    HERSHEY_X_OFFSET = 3 # when drawing a hershey text, it is always adding 4 to the x coordinate

    # Constants for title positioning
    TITLE_SCALE_FACTOR = .5
    TITLE_STROKE_WIDTH = 1
    SUBTITLE_SCALE_FACTOR = .3
    SUBTITLE_STROKE_WIDTH = 1
    TITLE_SUBTITLE_SPACING = 4  # Space between title and subtitle

    # Constants for legend positioning
    LEGEND_CELL_HEIGHT = 8 if size in ['a3', 'tabloid'] else 6
    LEGEND_PADDING = 10 if size in ['a3', 'tabloid'] else 8
    LEGEND_TEXT_SCALE_FACTOR = 0.13 if size in ['a3', 'tabloid'] else 0.1
    LEGEND_STROKE_WIDTH = 0.6
    TEXT_STROKE_WIDTH = 3

    # Create SVG builder with document dimensions
    svg = SVGBuilder(DOCUMENT_WIDTH, DOCUMENT_HEIGHT, {'stroke': pen_color, 'stroke-width': '0.5'})
        
    svg.begin_group({'id': 'background'})
    svg.title("background")
    # Add background rectangle
    svg.rect(0, 0, DOCUMENT_WIDTH, DOCUMENT_HEIGHT, {'fill': paper_color, 'stroke': 'none'})
    svg.end_group()
    
    # Add outer border rectangle
    svg.begin_group({'id': 'border'})
    svg.title("border")
        
    svg.rect(
        BORDER_INSET, 
        BORDER_INSET, 
        BORDER_WIDTH, 
        BORDER_HEIGHT, 
        {'fill': 'none', 'stroke': pen_color, 'stroke-width': BORDER_STROKE_WIDTH}
    )
    svg.end_group()

    # Add outer border rectangle
    svg.begin_group({'id': 'titles'})
    svg.title("titles")

    # Add title text using Hershey font
    title_box = svg.get_hershey_text_bounding_box(title)
    title_width = title_box['width']
    title_height = title_box['height']
    
    # Position the title in the top right corner of the border, account for title margin, internal padding, and stroke width
    title_translate_x = DOCUMENT_WIDTH - (title_width * TITLE_SCALE_FACTOR) - HERSHEY_X_OFFSET - INTERNAL_PADDING - BORDER_INSET - BORDER_STROKE_WIDTH
    title_translate_y = ((title_height / 2) * TITLE_SCALE_FACTOR) + BORDER_INSET + INTERNAL_PADDING + (BORDER_STROKE_WIDTH)

    svg.hershey_text(title_translate_x, title_translate_y, title, TITLE_SCALE_FACTOR, {
        'stroke': pen_color,
        'stroke-width': str(TITLE_STROKE_WIDTH)
    })

    # Add subtitle if provided
    if subtitle:
        subtitle_box = svg.get_hershey_text_bounding_box(subtitle)
        subtitle_width = subtitle_box['width']
        subtitle_height = subtitle_box['height']
        
        # Position subtitle below the title
        subtitle_translate_x = DOCUMENT_WIDTH - (subtitle_width * SUBTITLE_SCALE_FACTOR) - HERSHEY_X_OFFSET - INTERNAL_PADDING - BORDER_INSET - BORDER_STROKE_WIDTH
        subtitle_translate_y = title_translate_y + (title_height * TITLE_SCALE_FACTOR) + TITLE_SUBTITLE_SPACING + ((subtitle_height / 2) * SUBTITLE_SCALE_FACTOR)

        svg.hershey_text(subtitle_translate_x, subtitle_translate_y, subtitle, SUBTITLE_SCALE_FACTOR, {
            'stroke': pen_color,
            'stroke-width': str(SUBTITLE_STROKE_WIDTH)
        })

    svg.end_group()

    # Add legend if provided
    if legend:

        svg.begin_group({'id': 'legend'})
        svg.title("legend")

        # Calculate the width of the widest label and content
        max_label_width = 0
        max_content_width = 0
        for item in legend:
            label_box = svg.get_hershey_text_bounding_box(item['label'])
            content_box = svg.get_hershey_text_bounding_box(item['content'])
            max_label_width = max(max_label_width, label_box['width'])
            max_content_width = max(max_content_width, content_box['width'])

        # Calculate legend dimensions
        name_column_width = max_label_width * LEGEND_TEXT_SCALE_FACTOR + LEGEND_PADDING
        detail_column_width = max_content_width * LEGEND_TEXT_SCALE_FACTOR + LEGEND_PADDING
        legend_width = name_column_width + detail_column_width
        legend_height = len(legend) * LEGEND_CELL_HEIGHT

        # Legend starting position
        legend_start_x = BORDER_INSET + INTERNAL_PADDING
        legend_start_y = BORDER_INSET + INTERNAL_PADDING

        # Add legend border
        svg.rect(
            legend_start_x,
            legend_start_y,
            legend_width,
            legend_height,
            {'fill': 'none', 'stroke': pen_color, 'stroke-width': str(LEGEND_STROKE_WIDTH)}
        )

        # Add vertical divider line
        svg.line(
            legend_start_x + name_column_width,
            legend_start_y,
            legend_start_x + name_column_width,
            legend_start_y + legend_height,
            {'stroke': pen_color, 'stroke-width': str(LEGEND_STROKE_WIDTH)}
        )

        # Add legend items
        for i, item in enumerate(legend):
            y = legend_start_y + i * LEGEND_CELL_HEIGHT
            
            # Add horizontal divider line
            if i < len(legend) - 1:
                svg.line(
                    legend_start_x,
                    y + LEGEND_CELL_HEIGHT,
                    legend_start_x + legend_width,
                    y + LEGEND_CELL_HEIGHT,
                    {'stroke': pen_color, 'stroke-width': str(LEGEND_STROKE_WIDTH)}
                )

            # Add label
            label_box = svg.get_hershey_text_bounding_box(item['label'])
            label_y = y + (LEGEND_CELL_HEIGHT / 2) + ((label_box['height'] / 2) * LEGEND_TEXT_SCALE_FACTOR)
            svg.hershey_text(
                legend_start_x + 2,
                label_y - 1,
                item['label'],
                LEGEND_TEXT_SCALE_FACTOR,
                {'stroke': pen_color, 'stroke-width': str(TEXT_STROKE_WIDTH)}
            )

            # Add content
            content_box = svg.get_hershey_text_bounding_box(item['content'])
            content_y = y + (LEGEND_CELL_HEIGHT / 2) + ((content_box['height'] / 2) * LEGEND_TEXT_SCALE_FACTOR)
            svg.hershey_text(
                legend_start_x + name_column_width + 2,
                content_y - 1,
                item['content'],
                LEGEND_TEXT_SCALE_FACTOR,
                {'stroke': pen_color, 'stroke-width': str(TEXT_STROKE_WIDTH)}
            )
        svg.end_group()

    # Add schematic SVG if provided
    if schematic_svg:
        # Calculate the available space for the schematic
        # Leave space for legend at the top and some padding

        # Create a group for the schematic with proper positioning and scaling
        svg.begin_group({ 'id': 'schematic'})
        svg.title("schematic")
        
        # Add the schematic SVG content        
        # svg.calculate_bounding_box(schematic_svg)
        
        svg.add_schematic(schematic_svg, pen_color)
        
        svg.end_group()
    
    return svg



def render_test_svg():
    """
    Creates a test SVG and returns the SVG object.
    
    Args:
        title: The title to display on the artboard
    """
    # Create a complex SVG with grouped elements using our SVGBuilder
    svg = SVGBuilder(400, 300, {'stroke': 'black', 'stroke-width': '0.5'})
    
    # Add a title for the entire SVG
    svg.title("test")
    
    # Add a background rectangle
    svg.rect(0, 0, 400, 300, {'fill': '#f0f0f0'})

    # Add title using Hershey font (already using 'futural' set during initialization)
    svg.hershey_text(50, 50, 'Hershey Fonts', 0.4, {
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
    svg.text(100, 230, 'Non Hershey Text', {'font-family': 'Arial', 'font-size': '18px', 'text-anchor': 'middle'})
    
    svg.end_group()  # End the main group
    
    return svg


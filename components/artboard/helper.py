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

    INTERNAL_PADDING = 10 # INTERNAL_PADDING: Standard distance of 10mm between all content and the edges
    HERSHEY_X_OFFSET = 3 # when drawing a hershey text, it is always adding 4 to the x coordinate

    # Constants for title positioning
    TITLE_SCALE_FACTOR = .45
    TITLE_STROKE_WIDTH = 1
    SUBTITLE_SCALE_FACTOR = .30
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
    
    # Define the reverse direction path for a rectangle in counter-clockwise direction
    # Starting from bottom-right, going counter-clockwise
    path_data = (
        f"M {BORDER_INSET + BORDER_WIDTH} {BORDER_INSET + BORDER_HEIGHT} " +  # Start at bottom-right
        f"L {BORDER_INSET} {BORDER_INSET + BORDER_HEIGHT} " +                 # Bottom edge (right to left)
        f"L {BORDER_INSET} {BORDER_INSET} " +                                 # Left edge (bottom to top)
        f"L {BORDER_INSET + BORDER_WIDTH} {BORDER_INSET} " +                  # Top edge (left to right)
        f"L {BORDER_INSET + BORDER_WIDTH} {BORDER_INSET + BORDER_HEIGHT} " +  # Right edge (top to bottom)
        f"Z"                                                                  # Close path
    )
    
    svg.path(path_data, {
        'fill': 'none', 
        'stroke': pen_color, 
        'stroke-width': BORDER_STROKE_WIDTH,
        'stroke-dasharray': '0'  # Solid line, same as the original border
    })
    
    svg.end_group()

    # Add outer border rectangle
    svg.begin_group({'id': 'titles'})
    svg.title("titles")

    # Add title text using Hershey font
    title_box = svg.get_hershey_text_bounding_box(title)
    title_width = title_box['width']
    title_height = title_box['height']
    
    # Position the title right-aligned and at same top level as legend
    title_translate_x = DOCUMENT_WIDTH - BORDER_INSET - INTERNAL_PADDING - (title_width * TITLE_SCALE_FACTOR) - HERSHEY_X_OFFSET
    # Align with top of legend box
    title_translate_y = BORDER_INSET + INTERNAL_PADDING + ((title_height / 2) * TITLE_SCALE_FACTOR)

    svg.hershey_text(title_translate_x, title_translate_y, title, TITLE_SCALE_FACTOR, {
        'stroke': pen_color,
        'stroke-width': str(TITLE_STROKE_WIDTH)
    })

    # Add subtitle if provided
    if subtitle:
        subtitle_box = svg.get_hershey_text_bounding_box(subtitle)
        subtitle_width = subtitle_box['width']
        subtitle_height = subtitle_box['height']
        
        # Position subtitle right-aligned below the title
        subtitle_translate_x = DOCUMENT_WIDTH - BORDER_INSET - INTERNAL_PADDING - (subtitle_width * SUBTITLE_SCALE_FACTOR) - HERSHEY_X_OFFSET
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
            # Calculate vertical center of the text by considering both min_y and max_y
            label_text_center = (label_box['min_y'] + label_box['max_y']) / 2
            # Position text so its center aligns with the cell center
            label_y = y + (LEGEND_CELL_HEIGHT / 2) - (label_text_center * LEGEND_TEXT_SCALE_FACTOR)
            svg.hershey_text(
                legend_start_x + 2,
                label_y,
                item['label'],
                LEGEND_TEXT_SCALE_FACTOR,
                {'stroke': pen_color, 'stroke-width': str(TEXT_STROKE_WIDTH)}
            )

            # Add content
            content_box = svg.get_hershey_text_bounding_box(item['content'])
            # Calculate vertical center of the text by considering both min_y and max_y
            content_text_center = (content_box['min_y'] + content_box['max_y']) / 2
            # Position text so its center aligns with the cell center
            content_y = y + (LEGEND_CELL_HEIGHT / 2) - (content_text_center * LEGEND_TEXT_SCALE_FACTOR)
            svg.hershey_text(
                legend_start_x + name_column_width + 2,
                content_y,
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


def render_airport_svg(title="Airport", subtitle="", size='tabloid', orientation='portrait', 
                       paper_color="white", pen_color="black", schematic_svg=None):
    """
    Create an airport diagram SVG with responsive layout.
    
    This function creates a clean airport diagram that automatically scales and centers
    content (title, subtitle, and schematic) within the specified paper size.
    
    Args:
        title: Main title text
        subtitle: Optional subtitle text
        size: Paper size ('a3', 'a4', 'letter', 'tabloid')
        orientation: Paper orientation ('portrait' or 'landscape')
        paper_color: Background color
        pen_color: Color for all strokes/text
        schematic_svg: Optional SVG string containing the airport diagram
        
    Returns:
        SVGBuilder instance with the complete airport diagram
    """
    # Import required for regex processing
    import re
    
    # ===== DOCUMENT SETUP =====
    # Validate and set paper size
    if not size or size not in PAPER_SIZES:
        print(f"Cannot find the specified paper size '{size}'. Defaulting to tabloid.")
        size = 'tabloid'

    # Get document dimensions
    doc_width, doc_height = PAPER_SIZES[size]
    
    # Swap dimensions for landscape orientation
    if orientation.lower() == 'landscape':
        doc_width, doc_height = doc_height, doc_width
    
    # ===== LAYOUT CONSTANTS =====
    # Page layout
    PAGE_MARGIN = 15  # mm - margin around the entire page
    MAX_SCALE = 1.5   # Maximum scale factor to prevent overly large content
    
    # Content spacing
    CONTENT_PADDING = 5      # mm - padding inside the content block
    TITLE_SUBTITLE_GAP = 15  # mm - space between title and subtitle
    SUBTITLE_DIAGRAM_GAP = 25  # mm - space between subtitle and diagram
    
    # Text styling
    TITLE_SCALE = 1.2
    TITLE_STROKE_WIDTH = 1.5
    SUBTITLE_SCALE = 0.9
    SUBTITLE_STROKE_WIDTH = 1.2

    # ===== CREATE MAIN SVG =====
    main_svg = SVGBuilder(doc_width, doc_height, {'stroke': pen_color, 'stroke-width': '0.5'})
    
    # Add background
    main_svg.begin_group({'id': 'background'})
    main_svg.title("background")
    main_svg.rect(0, 0, doc_width, doc_height, {'fill': paper_color, 'stroke': 'none'})
    main_svg.end_group()
    
    # ===== CALCULATE CONTENT DIMENSIONS =====
    # Use temporary SVG for text measurements
    temp_svg = SVGBuilder(1000, 1000)
    
    # Measure title
    title_bbox = temp_svg.get_hershey_text_bounding_box(title)
    title_width = title_bbox['width'] * TITLE_SCALE
    title_height = title_bbox['height'] * TITLE_SCALE
    
    # Measure subtitle (if provided)
    subtitle_width = 0
    subtitle_height = 0
    subtitle_bbox = None
    if subtitle:
        subtitle_bbox = temp_svg.get_hershey_text_bounding_box(subtitle)
        subtitle_width = subtitle_bbox['width'] * SUBTITLE_SCALE
        subtitle_height = subtitle_bbox['height'] * SUBTITLE_SCALE
    
    # Measure schematic (if provided)
    schematic_width = 0
    schematic_height = 0
    schematic_bbox = None
    if schematic_svg:
        schematic_bbox = temp_svg.calculate_bounding_box(schematic_svg)
        schematic_width = schematic_bbox['width']
        schematic_height = schematic_bbox['height']
    
    # Find maximum content width
    max_content_width = max(title_width, subtitle_width, schematic_width)
    
    # ===== CALCULATE CONTENT POSITIONS =====
    # Start from top padding
    current_y = CONTENT_PADDING
    
    # Title position (centered horizontally)
    title_x = CONTENT_PADDING + (max_content_width / 2) - (title_width / 2)
    title_y = current_y - (title_bbox['min_y'] * TITLE_SCALE)
    current_y += title_height + TITLE_SUBTITLE_GAP
    
    # Subtitle position (if provided)
    subtitle_x = 0
    subtitle_y = 0
    if subtitle and subtitle_bbox:
        subtitle_x = CONTENT_PADDING + (max_content_width / 2) - (subtitle_width / 2)
        subtitle_y = current_y - (subtitle_bbox['min_y'] * SUBTITLE_SCALE)
        current_y += subtitle_height + SUBTITLE_DIAGRAM_GAP
    else:
        current_y += SUBTITLE_DIAGRAM_GAP
    
    # Schematic position
    schematic_x = CONTENT_PADDING
    schematic_y = current_y
    
    # Total content dimensions
    content_width = max_content_width + (2 * CONTENT_PADDING)
    content_height = current_y + schematic_height + CONTENT_PADDING
    
    # ===== CALCULATE SCALING AND CENTERING =====
    available_width = doc_width - (2 * PAGE_MARGIN)
    available_height = doc_height - (2 * PAGE_MARGIN)
    
    # Calculate scale to fit content within available space
    scale = 1.0
    if content_width > 0 and content_height > 0:
        scale_x = available_width / content_width
        scale_y = available_height / content_height
        scale = min(scale_x, scale_y, MAX_SCALE)
    
    # Calculate centered position
    scaled_width = content_width * scale
    scaled_height = content_height * scale
    x_offset = PAGE_MARGIN + (available_width - scaled_width) / 2
    y_offset = PAGE_MARGIN + (available_height - scaled_height) / 2
    
    # ===== RENDER CONTENT =====
    # Create scaled and positioned content group
    main_svg.begin_group({
        'id': 'content-block',
        'transform': f'translate({x_offset:.2f}, {y_offset:.2f}) scale({scale:.4f})'
    })
    main_svg.title("Scaled content block")
    
    # Add title
    main_svg.hershey_text(
        title_x, title_y, title, TITLE_SCALE,
        {'stroke': pen_color, 'stroke-width': str(TITLE_STROKE_WIDTH)}
    )
    
    # Add subtitle
    if subtitle:
        main_svg.hershey_text(
            subtitle_x, subtitle_y, subtitle, SUBTITLE_SCALE,
            {'stroke': pen_color, 'stroke-width': str(SUBTITLE_STROKE_WIDTH)}
        )
    
    # Add schematic
    if schematic_svg and schematic_bbox:
        # Extract inner content from schematic SVG
        _, schematic_inner_content = main_svg.extract_svg_contents(schematic_svg)
        
        # Position schematic
        main_svg.begin_group({
            'transform': f'translate({schematic_x}, {schematic_y}) translate({-schematic_bbox["min_x"]}, {-schematic_bbox["min_y"]})'
        })
        
        # Process schematic to ensure consistent stroke attributes
        schematic_inner_content = main_svg.process_schematic_strokes(schematic_inner_content, pen_color)
        
        # Add processed content
        main_svg._add_element(schematic_inner_content)
        main_svg.end_group()
    
    # Close content group
    main_svg.end_group()
    
    return main_svg



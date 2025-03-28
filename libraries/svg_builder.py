class SVGBuilder:
    """
    A utility class for programmatically creating SVG elements
    
    This class provides a fluent interface for building SVG documents with various
    shapes and elements. It handles the SVG structure, element creation, and
    attributes formatting.
    
    Example:
        # Create a simple SVG with a red rectangle and blue circle
        svg = SVGBuilder(100, 100)
        svg.rect(10, 10, 40, 40, {'fill': 'red', 'stroke': 'black', 'stroke-width': '2'})
        svg.circle(70, 30, 20, {'fill': 'blue'})
        result = svg.to_string()
        
    Example:
        # Create a grouped set of elements with transformations
        svg = SVGBuilder(200, 200)
        svg.begin_group({'transform': 'translate(50,50)'})
        svg.rect(0, 0, 30, 30, {'fill': 'yellow'})
        svg.text(10, 20, 'Hello', {'font-size': '12px'})
        svg.end_group()
        result = svg.to_string()
    """
    
    def __init__(self, width: float, height: float, default_styles: dict = None, hershey_font_name: str = 'futural'):
        """
        Creates a new SVG builder with specified dimensions
        
        Args:
            width: Width of the SVG canvas in millimeters
            height: Height of the SVG canvas in millimeters
            default_styles: Optional default styles to apply to all elements (e.g., stroke, stroke-width)
            hershey_font_name: Name of the default Hershey font to use (default: 'futural')
        """
        self.elements = []
        self.width = width
        self.height = height
        self.current_group = None
        self.default_styles = default_styles or {}
        
        # Initialize Hershey Fonts support
        try:
            from HersheyFonts import HersheyFonts
            self.hershey_font = HersheyFonts()
            self.set_hershey_font(hershey_font_name)
        except ImportError:
            self.hershey_font = None
            print("Warning: HersheyFonts library not found. hershey_text functions will not work.")
    
    def set_hershey_font(self, font_name: str) -> 'SVGBuilder':
        """
        Set the active Hershey font for subsequent hershey_text calls
        
        Args:
            font_name: Name of the Hershey font to use (e.g., 'futural', 'scriptc', 'gothiceng')
        
        Returns:
            The builder instance for method chaining
            
        Example:
            svg_builder.set_hershey_font('scriptc')
            svg_builder.hershey_text(50, 50, "This is script font")
        """
        if self.hershey_font:
            self.hershey_font.load_default_font(font_name)
        return self
    
    def get_hershey_text_bounding_box(self, text: str) -> dict:
        """
        Calculate the bounding box of the given text using the current Hershey font.
        
        Args:
            text (str): The text to calculate the bounding box for
            
        Returns:
            dict: A dictionary containing the bounding box information:
                - 'min_x': Minimum x-coordinate
                - 'max_x': Maximum x-coordinate
                - 'min_y': Minimum y-coordinate
                - 'max_y': Maximum y-coordinate
                - 'width': Width of the bounding box
                - 'height': Height of the bounding box
                
        Example:
            # Get the bounding box dimensions for text before rendering
            bbox = svg_builder.get_hershey_text_bounding_box("Hello World")
            # Use the dimensions to position or scale the text appropriately
            svg_builder.hershey_text(50, 50, "Hello World", 1.0, {
                'stroke': 'black',
                'stroke-width': str(0.5 * (100 / bbox['width']))  # Scale stroke width based on text size
            })
        """
        if not self.hershey_font:
            print("Warning: HersheyFonts not available. Cannot calculate bounding box.")
            return {
                'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0,
                'width': 0, 'height': 0
            }
        
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        
        for line in self.hershey_font.lines_for_text(text):
            if line:  # Skip empty lines
                for x, y in line:
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
        
        # Handle case where text is empty or contains no renderable characters
        if min_x == float('inf'):
            return {
                'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0,
                'width': 0, 'height': 0
            }
            
        width = max_x - min_x
        height = max_y - min_y
        
        return {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'width': width,
            'height': height
        }
    
    def _format_attrs(self, attrs: dict) -> str:
        """
        Formats object attributes into SVG attribute string
        
        Args:
            attrs: Dictionary containing attribute key-value pairs
        
        Returns:
            Formatted attribute string with leading space if not empty
        """
        # Merge default styles with specific attributes (specific attributes take precedence)
        merged_attrs = {**self.default_styles, **attrs}
        
        attrs_string = ' '.join([f'{key}="{value}"' for key, value in merged_attrs.items()])
        
        return f' {attrs_string}' if attrs_string else ''
    
    def _add_element(self, element: str) -> 'SVGBuilder':
        """
        Helper method to add elements to the current group or root level
        
        Args:
            element: The SVG element to add
            
        Returns:
            The builder instance for method chaining
        """
        if self.current_group:
            self.current_group.add_element(element)
        else:
            self.elements.append(element)
        
        return self
    
    def rect(self, x: float, y: float, width: float, height: float, attrs: dict = None) -> 'SVGBuilder':
        """
        Adds a rectangle element to the SVG
        
        Args:
            x: X-coordinate of the top-left corner
            y: Y-coordinate of the top-left corner
            width: Width of the rectangle
            height: Height of the rectangle
            attrs: Optional attributes for styling and behavior (e.g., fill, stroke)
        
        Returns:
            The builder instance for method chaining
        
        Example:
            # Add a blue rectangle with a border
            svg_builder.rect(10, 10, 50, 30, {
                'fill': 'blue',
                'stroke': '#000',
                'stroke-width': '2'
            })
        """
        attrs = attrs or {}
        element = f'<rect x="{x}" y="{y}" width="{width}" height="{height}"{self._format_attrs(attrs)} />'
        return self._add_element(element)
    
    def title(self, content: str, attrs: dict = None) -> 'SVGBuilder':
        """
        Adds a title element to the SVG - titles provide a tooltip and improve accessibility
        
        Args:
            content: The text content of the title
            attrs: Optional attributes for the title element
        
        Returns:
            The builder instance for method chaining
        
        Example:
            # Add a title to an element for accessibility
            svg_builder.begin_group({'id': 'my-chart'})
            svg_builder.title('Chart showing annual revenue')
            svg_builder.rect(10, 10, 80, 60, {'fill': 'lightblue'})
            svg_builder.end_group()
        """
        attrs = attrs or {}
        element = f'<title{self._format_attrs(attrs)}>{content}</title>'
        return self._add_element(element)
    
    def text(self, x: float, y: float, content: str, attrs: dict = None) -> 'SVGBuilder':
        """
        Adds a text element to the SVG
        
        Args:
            x: X-coordinate of the text position
            y: Y-coordinate of the text position
            content: The text content to display
            attrs: Optional attributes for styling (e.g., font-size, fill)
        
        Returns:
            The builder instance for method chaining
        
        Example:
            # Add black text with a specific font size
            svg_builder.text(25, 40, 'Hello SVG', {
                'font-family': 'Arial',
                'font-size': '16px',
                'text-anchor': 'middle'
            })
        """
        attrs = attrs or {}
        element = f'<text x="{x}" y="{y}"{self._format_attrs(attrs)}>{content}</text>'
        return self._add_element(element)
    
    def hershey_text(self, x: float, y: float, content: str, scale: float = 1.0, attrs: dict = None) -> 'SVGBuilder':
        """
        Adds text using the currently set Hershey font
        
        This method uses the HersheyFonts library to create SVG path elements for single-stroke
        text rendering, ideal for plotters and CNC applications.
        
        Args:
            x: X-coordinate of the text position
            y: Y-coordinate of the text position
            content: The text content to display
            scale: Scaling factor for the text (default: 1.0)
            attrs: Optional attributes for styling (e.g., stroke, stroke-width)
            
        Returns:
            The builder instance for method chaining
            
        Example:
            # Add Hershey font text using the default font
            svg_builder.hershey_text(50, 50, "Hello Hershey", 0.5, {
                'stroke': 'black',
                'stroke-width': '0.5'
            })
            
            # Change font and add more text
            svg_builder.set_hershey_font('scriptc')
            svg_builder.hershey_text(50, 100, "Script Style", 0.4)
        """
        if not self.hershey_font:
            print("Warning: HersheyFonts not available. Text will not be rendered.")
            return self
        
        attrs = attrs or {}
        # Default attributes for Hershey font strokes
        default_hershey_attrs = {'fill': 'none', 'stroke': 'black', 'stroke-width': '1'}
        merged_attrs = {**default_hershey_attrs, **attrs}
        
        # Create a group for the text with a translation transform
        group_attrs = {'transform': f'translate({x},{y}) scale({scale})'}
        
        self.begin_group(group_attrs)
        
        # Add a title element for readability in the SVG code
        self.title(f"{content}")
        
        # Generate SVG paths for each line segment in the text
        for line in self.hershey_font.lines_for_text(content):
            if line:  # Skip empty lines
                # Convert points to SVG path data
                path_data = "M" + " L".join(f"{point[0]},{point[1]}" for point in line)
                # Add the path to the group
                path_element = f'<path d="{path_data}"{self._format_attrs(merged_attrs)} />'
                self._add_element(path_element)
        
        self.end_group()
        return self
    
    def centered_hershey_text(self, x: float, y: float, content: str, scale: float = 1.0, attrs: dict = None) -> 'SVGBuilder':
        """
        Adds text using the currently set Hershey font, centered at the specified coordinates
        
        This method is similar to hershey_text but automatically centers the text
        based on its bounding box.
        
        Args:
            x: X-coordinate of the center position
            y: Y-coordinate of the center position
            content: The text content to display
            scale: Scaling factor for the text (default: 1.0)
            attrs: Optional attributes for styling (e.g., stroke, stroke-width)
            
        Returns:
            The builder instance for method chaining
            
        Example:
            # Add centered Hershey font text
            svg_builder.centered_hershey_text(100, 100, "Centered Text", 0.8, {
                'stroke': 'blue',
                'stroke-width': '0.75'
            })
        """
        if not self.hershey_font:
            print("Warning: HersheyFonts not available. Text will not be rendered.")
            return self
            
        # Calculate the bounding box
        bbox = self.get_hershey_text_bounding_box(content)
        
        # Calculate the centered position
        center_offset_x = (bbox['min_x'] + bbox['max_x']) / 2
        center_offset_y = (bbox['min_y'] + bbox['max_y']) / 2
        
        # Adjust the position to center the text
        centered_x = x - (center_offset_x * scale)
        centered_y = y - (center_offset_y * scale)
        
        # Use the standard hershey_text method with the adjusted position
        return self.hershey_text(centered_x, centered_y, content, scale, attrs)
    
    def hershey_text_with_bbox(self, x: float, y: float, content: str, scale: float = 1.0, 
                               text_attrs: dict = None, bbox_attrs: dict = None) -> 'SVGBuilder':
        """
        Adds text using the currently set Hershey font with a visible bounding box
        
        This method is useful for debugging text positioning and layout.
        
        Args:
            x: X-coordinate of the text position
            y: Y-coordinate of the text position
            content: The text content to display
            scale: Scaling factor for the text (default: 1.0)
            text_attrs: Optional attributes for styling the text
            bbox_attrs: Optional attributes for styling the bounding box rectangle
            
        Returns:
            The builder instance for method chaining
            
        Example:
            # Add Hershey text with a visible bounding box for debugging
            svg_builder.hershey_text_with_bbox(50, 50, "Text with Box", 0.5, 
                {'stroke': 'black', 'stroke-width': '0.5'},
                {'fill': 'none', 'stroke': 'red', 'stroke-width': '0.25', 'stroke-dasharray': '2,1'})
        """
        if not self.hershey_font:
            print("Warning: HersheyFonts not available. Text will not be rendered.")
            return self
            
        # Calculate the bounding box
        bbox = self.get_hershey_text_bounding_box(content)
        
        # Set default styles for the bounding box
        default_bbox_attrs = {
            'fill': 'none', 
            'stroke': 'red', 
            'stroke-width': '0.5', 
            'stroke-dasharray': '2,1',
            'opacity': '0.7'
        }
        merged_bbox_attrs = {**default_bbox_attrs, **(bbox_attrs or {})}
        
        # Start a group for the entire element with text and bounding box
        self.begin_group({'transform': f'translate({x},{y}) scale({scale})'})
        
        # Add the bounding box rectangle
        self.rect(
            bbox['min_x'], 
            bbox['min_y'], 
            bbox['width'], 
            bbox['height'], 
            merged_bbox_attrs
        )
        
        # Add center point marker (optional)
        center_x = (bbox['min_x'] + bbox['max_x']) / 2
        center_y = (bbox['min_y'] + bbox['max_y']) / 2
        self.circle(
            center_x, 
            center_y, 
            0.5, 
            {'fill': 'red', 'stroke': 'none'}
        )
        
        # Generate SVG paths for each line segment in the text
        default_text_attrs = {'fill': 'none', 'stroke': 'black', 'stroke-width': '1'}
        merged_text_attrs = {**default_text_attrs, **(text_attrs or {})}
        
        # Add a title for identification
        self.title(f"{content} (with bounding box)")
        
        # Create the text paths
        for line in self.hershey_font.lines_for_text(content):
            if line:  # Skip empty lines
                path_data = "M" + " L".join(f"{point[0]},{point[1]}" for point in line)
                path_element = f'<path d="{path_data}"{self._format_attrs(merged_text_attrs)} />'
                self._add_element(path_element)
        
        self.end_group()
        return self
    
    def line(self, x1: float, y1: float, x2: float, y2: float, attrs: dict = None) -> 'SVGBuilder':
        """
        Adds a line element to the SVG
        
        Args:
            x1: X-coordinate of the start point
            y1: Y-coordinate of the start point
            x2: X-coordinate of the end point
            y2: Y-coordinate of the end point
            attrs: Optional attributes for styling (e.g., stroke, stroke-width)
        
        Returns:
            The builder instance for method chaining
        
        Example:
            # Add a dashed red line
            svg_builder.line(10, 10, 50, 50, {
                'stroke': 'red',
                'stroke-width': '2',
                'stroke-dasharray': '5,5'
            })
        """
        attrs = attrs or {}
        element = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{self._format_attrs(attrs)} />'
        return self._add_element(element)
    
    def circle(self, cx: float, cy: float, r: float, attrs: dict = None) -> 'SVGBuilder':
        """
        Adds a circle element to the SVG
        
        Args:
            cx: X-coordinate of the center
            cy: Y-coordinate of the center
            r: Radius of the circle
            attrs: Optional attributes for styling (e.g., fill, stroke)
        
        Returns:
            The builder instance for method chaining
        
        Example:
            # Add a green circle with a black border
            svg_builder.circle(50, 50, 25, {
                'fill': 'green',
                'stroke': 'black',
                'stroke-width': '1'
            })
        """
        attrs = attrs or {}
        element = f'<circle cx="{cx}" cy="{cy}" r="{r}"{self._format_attrs(attrs)} />'
        return self._add_element(element)
    
    def ellipse(self, cx: float, cy: float, rx: float, ry: float, attrs: dict = None) -> 'SVGBuilder':
        """
        Adds an ellipse element to the SVG
        
        Args:
            cx: X-coordinate of the center
            cy: Y-coordinate of the center
            rx: Horizontal radius
            ry: Vertical radius
            attrs: Optional attributes for styling (e.g., fill, stroke)
        
        Returns:
            The builder instance for method chaining
        
        Example:
            # Add a green ellipse with a black border
            svg_builder.ellipse(50, 50, 40, 25, {
                'fill': 'green',
                'stroke': 'black',
                'stroke-width': '1'
            })
        """
        attrs = attrs or {}
        element = f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"{self._format_attrs(attrs)} />'
        return self._add_element(element)
    
    def path(self, d: str, attrs: dict = None) -> 'SVGBuilder':
        """
        Adds a path element to the SVG
        
        Args:
            d: The path data string containing path commands (e.g., "M10,10 L90,90")
            attrs: Optional attributes for styling (e.g., fill, stroke)
        
        Returns:
            The builder instance for method chaining
        
        Example:
            # Add a triangle path
            svg_builder.path("M10,10 L50,50 L10,50 Z", {
                'fill': 'yellow',
                'stroke': 'black',
                'stroke-width': '1'
            })
        """
        attrs = attrs or {}
        element = f'<path d="{d}"{self._format_attrs(attrs)} />'
        return self._add_element(element)
    
    def begin_group(self, attrs: dict = None) -> 'SVGBuilder':
        """
        Starts a new group element for organizing and transforming elements together
        
        Args:
            attrs: Optional attributes for the group (e.g., transform, opacity)
        
        Returns:
            The builder instance for method chaining
        
        Example:
            # Create a group with a translation transformation and ID
            svg_builder.begin_group({
                'id': 'chart-container',
                'transform': 'translate(20,20)'
            })
            svg_builder.rect(0, 0, 30, 30, {'fill': 'purple'})
            svg_builder.circle(50, 50, 15, {'fill': 'orange'})
            svg_builder.end_group()
        """
        attrs = attrs or {}
        new_group = Group(attrs, self.current_group)
        
        if self.current_group:
            self.current_group.add_element(new_group)
        else:
            self.elements.append(new_group)
        
        self.current_group = new_group
        return self
    
    def end_group(self) -> 'SVGBuilder':
        """
        Ends the current group and returns to the parent group or root level
        
        Returns:
            The builder instance for method chaining
        """
        if self.current_group and self.current_group.parent:
            self.current_group = self.current_group.parent
        else:
            self.current_group = None
        
        return self
    
    def to_string(self) -> str:
        """
        Generates the complete SVG markup as a string
        
        Returns:
            The SVG document as a string, including XML declaration and SVG root element
        
        Example:
            # Generate the final SVG string to use in HTML or save to a file
            svg_string = SVGBuilder(100, 100)
                .rect(10, 10, 80, 80, {'fill': 'none', 'stroke': 'black'})
                .text(50, 50, 'SVG', {'text-anchor': 'middle'})
                .to_string()
        """
        elements_str = '\n'.join([
            (el if isinstance(el, str) else el.to_string()) 
            for el in self.elements
        ])
        
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}mm" height="{self.height}mm" viewBox="0 0 {self.width} {self.height}">
{elements_str}
</svg>"""


class Group:
    """
    Helper class for managing SVG group elements
    
    Groups allow elements to be organized together and have transformations or
    styles applied to them collectively.
    """
    
    def __init__(self, attrs: dict = None, parent: 'Group' = None):
        """
        Creates a new group element
        
        Args:
            attrs: Attributes to apply to the group
            parent: Optional parent group for nesting
        """
        self.elements = []
        self.attrs = attrs or {}
        self.parent = parent
    
    def add_element(self, element) -> None:
        """
        Adds an element to this group
        
        Args:
            element: The SVG element to add to the group
        """
        self.elements.append(element)
    
    def add_raw_svg(self, svg_content: str) -> None:
        """
        Adds raw SVG content to this group
        
        Args:
            svg_content: Raw SVG content as a string
        """
        self.elements.append(svg_content)
    
    def to_string(self) -> str:
        """
        Generates the string representation of the group with its nested elements
        
        Returns:
            Formatted SVG group markup as a string
        """
        attrs_string = ' '.join([f'{key}="{value}"' for key, value in self.attrs.items()])
        
        open_tag = f'<g {attrs_string}>' if attrs_string else '<g>'
        close_tag = '</g>'
        
        elements_str = '\n'.join([
            '    ' + (el if isinstance(el, str) else el.to_string().replace('\n', '\n    '))
            for el in self.elements
        ])
        
        return f"""  {open_tag}
{elements_str}
  {close_tag}"""

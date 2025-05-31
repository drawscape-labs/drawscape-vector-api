import re

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
            self.hershey_font.render_options['spacing'] = -1.0
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
    
    def _escape_xml(self, text: str) -> str:
        """
        Escapes special characters in XML/SVG text content
        
        Args:
            text: The text to escape
            
        Returns:
            Escaped text safe for XML/SVG
        """
        replacements = [
            ('&', '&amp;'),
            ('<', '&lt;'),
            ('>', '&gt;'),
            ('"', '&quot;'),
            ("'", '&apos;')
        ]
        
        result = str(text)
        for char, replacement in replacements:
            result = result.replace(char, replacement)
        return result
    
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
        safe_content = self._escape_xml(content)
        element = f'<title>{safe_content}</title>'
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
        safe_content = self._escape_xml(content)
        element = f'<text x="{x}" y="{y}"{self._format_attrs(attrs)}>{safe_content}</text>'
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
        self.title(content)
        
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
        self.title(content + " (with bounding box)")
        
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
    
    def calculate_bounding_box(self, svg_content: str) -> dict:
        """
        Calculates the bounding box of an SVG by analyzing its elements.
        Ignores the viewBox, width, and height attributes of the SVG.
        
        Args:
            svg_content: Raw SVG content as a string
            
        Returns:
            dict: A dictionary containing the bounding box information:
                - 'min_x': Minimum x-coordinate
                - 'max_x': Maximum x-coordinate
                - 'min_y': Minimum y-coordinate
                - 'max_y': Maximum y-coordinate
                - 'width': Width of the bounding box
                - 'height': Height of the bounding box
        """
        # Initialize bounding box values
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        # Remove XML declaration if present
        svg_content = re.sub(r'<\?xml[^>]*\?>', '', svg_content)
        
        # Extract the SVG tag and its attributes
        svg_match = re.search(r'<svg([^>]*)>(.*)</svg>', svg_content, re.DOTALL)
        if not svg_match:
            return {
                'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0,
                'width': 0, 'height': 0
            }

        svg_attrs_str = svg_match.group(1)
        inner_content = svg_match.group(2)
        
        # Remove namespace declarations for sodipodi/inkscape
        svg_attrs_str = re.sub(r'\sxmlns:sodipodi="[^"]*"', '', svg_attrs_str)
        svg_attrs_str = re.sub(r'\sxmlns:inkscape="[^"]*"', '', svg_attrs_str)
        
        # Extract width, height, and viewBox using regex
        width_match = re.search(r'width="([^"]+)"', svg_attrs_str)
        height_match = re.search(r'height="([^"]+)"', svg_attrs_str)
        viewbox_match = re.search(r'viewBox="([^"]+)"', svg_attrs_str)
        
        width = width_match.group(1) if width_match else "Not specified"
        height = height_match.group(1) if height_match else "Not specified"
        viewbox = viewbox_match.group(1) if viewbox_match else "Not specified"
        
        # Helper function to update bounding box
        def update_bbox(x, y):
            nonlocal min_x, max_x, min_y, max_y
            if x is not None:
                min_x = min(min_x, float(x))
                max_x = max(max_x, float(x))
            if y is not None:
                min_y = min(min_y, float(y))
                max_y = max(max_y, float(y))
        
        # Helper to parse numeric attributes, stripping units
        def parse_float(value):
            if value is None:
                return None
            try:
                # Strip units like px, mm, etc.
                value = re.sub(r'[a-z%]+$', '', str(value))
                return float(value)
            except (ValueError, TypeError):
                return None
                
        # Helper to parse points for polyline and polygon
        def parse_points(points_str):
            if not points_str:
                return []
                
            # Clean up the points string
            points_str = points_str.strip()
            # Replace commas with spaces for consistent splitting
            points_str = re.sub(r',', ' ', points_str)
            # Normalize whitespace
            points_str = re.sub(r'\s+', ' ', points_str)
            
            # Split into individual coordinates
            coordinates = points_str.split()
            points = []
            
            # Group coordinates into pairs
            for i in range(0, len(coordinates), 2):
                if i + 1 < len(coordinates):
                    try:
                        x = parse_float(coordinates[i])
                        y = parse_float(coordinates[i + 1])
                        if x is not None and y is not None:
                            points.append((x, y))
                    except (ValueError, IndexError):
                        pass
                        
            return points
        
        # Process SVG content using regex for each type of element
        # This approach avoids namespace issues with XML parsing
        
        # Process rect elements
        rect_pattern = r'<rect\s+([^>]*)/?>'
        for match in re.finditer(rect_pattern, inner_content):
            attrs = match.group(1)
            
            # Extract attributes
            x = parse_float(re.search(r'x="([^"]*)"', attrs).group(1) if re.search(r'x="([^"]*)"', attrs) else 0)
            y = parse_float(re.search(r'y="([^"]*)"', attrs).group(1) if re.search(r'y="([^"]*)"', attrs) else 0)
            width = parse_float(re.search(r'width="([^"]*)"', attrs).group(1) if re.search(r'width="([^"]*)"', attrs) else 0)
            height = parse_float(re.search(r'height="([^"]*)"', attrs).group(1) if re.search(r'height="([^"]*)"', attrs) else 0)
            
            if width is not None and height is not None:
                update_bbox(x, y)
                update_bbox(x + width, y + height)
        
        # Process circle elements
        circle_pattern = r'<circle\s+([^>]*)/?>'
        for match in re.finditer(circle_pattern, inner_content):
            attrs = match.group(1)
            
            # Extract attributes
            cx = parse_float(re.search(r'cx="([^"]*)"', attrs).group(1) if re.search(r'cx="([^"]*)"', attrs) else 0)
            cy = parse_float(re.search(r'cy="([^"]*)"', attrs).group(1) if re.search(r'cy="([^"]*)"', attrs) else 0)
            r = parse_float(re.search(r'r="([^"]*)"', attrs).group(1) if re.search(r'r="([^"]*)"', attrs) else 0)
            
            if cx is not None and cy is not None and r is not None:
                update_bbox(cx - r, cy - r)
                update_bbox(cx + r, cy + r)
        
        # Process ellipse elements
        ellipse_pattern = r'<ellipse\s+([^>]*)/?>'
        for match in re.finditer(ellipse_pattern, inner_content):
            attrs = match.group(1)
            
            # Extract attributes
            cx = parse_float(re.search(r'cx="([^"]*)"', attrs).group(1) if re.search(r'cx="([^"]*)"', attrs) else 0)
            cy = parse_float(re.search(r'cy="([^"]*)"', attrs).group(1) if re.search(r'cy="([^"]*)"', attrs) else 0)
            rx = parse_float(re.search(r'rx="([^"]*)"', attrs).group(1) if re.search(r'rx="([^"]*)"', attrs) else 0)
            ry = parse_float(re.search(r'ry="([^"]*)"', attrs).group(1) if re.search(r'ry="([^"]*)"', attrs) else 0)
            
            if cx is not None and cy is not None and rx is not None and ry is not None:
                update_bbox(cx - rx, cy - ry)
                update_bbox(cx + rx, cy + ry)
        
        # Process line elements
        line_pattern = r'<line\s+([^>]*)/?>'
        for match in re.finditer(line_pattern, inner_content):
            attrs = match.group(1)
            
            # Extract attributes
            x1 = parse_float(re.search(r'x1="([^"]*)"', attrs).group(1) if re.search(r'x1="([^"]*)"', attrs) else 0)
            y1 = parse_float(re.search(r'y1="([^"]*)"', attrs).group(1) if re.search(r'y1="([^"]*)"', attrs) else 0)
            x2 = parse_float(re.search(r'x2="([^"]*)"', attrs).group(1) if re.search(r'x2="([^"]*)"', attrs) else 0)
            y2 = parse_float(re.search(r'y2="([^"]*)"', attrs).group(1) if re.search(r'y2="([^"]*)"', attrs) else 0)
            
            update_bbox(x1, y1)
            update_bbox(x2, y2)
            
        # Process polyline elements
        polyline_pattern = r'<polyline\s+([^>]*)/?>'
        for match in re.finditer(polyline_pattern, inner_content):
            attrs = match.group(1)
            
            # Extract points attribute
            points_match = re.search(r'points="([^"]*)"', attrs)
            if points_match:
                points_str = points_match.group(1)
                points = parse_points(points_str)
                for x, y in points:
                    update_bbox(x, y)
        
        # Process polygon elements
        polygon_pattern = r'<polygon\s+([^>]*)/?>'
        for match in re.finditer(polygon_pattern, inner_content):
            attrs = match.group(1)
            
            # Extract points attribute
            points_match = re.search(r'points="([^"]*)"', attrs)
            if points_match:
                points_str = points_match.group(1)
                points = parse_points(points_str)
                for x, y in points:
                    update_bbox(x, y)

        # Process text elements
        text_pattern = r'<text\s+([^>]*)>([^<]*)</text>'
        for match in re.finditer(text_pattern, inner_content):
            attrs = match.group(1)
            text_content = match.group(2)
            
            # Extract attributes
            x = parse_float(re.search(r'x="([^"]*)"', attrs).group(1) if re.search(r'x="([^"]*)"', attrs) else 0)
            y = parse_float(re.search(r'y="([^"]*)"', attrs).group(1) if re.search(r'y="([^"]*)"', attrs) else 0)
            
            # Simple text bounding box approximation
            update_bbox(x, y)
            # Rough estimate of text width based on content length
            if text_content:
                approx_width = len(text_content) * 8  # Very rough approximation
                update_bbox(x + approx_width, y + 10)  # Assuming ~10px height

        # Process path elements
        path_pattern = r'<path\s+([^>]*)/?>'
        for match in re.finditer(path_pattern, inner_content):
            attrs = match.group(1)
            
            # Extract path data
            d_match = re.search(r'd="([^"]*)"', attrs)
            if d_match:
                d = d_match.group(1)
                
                try:
                    # Simplified path parsing
                    # Normalize spaces around commands and commas
                    d = re.sub(r'([MLHVZCSTQAmlhvzcstqa])', r' \1 ', d)
                    d = re.sub(r',', ' ', d)
                    d = re.sub(r'\s+', ' ', d).strip()
                    
                    tokens = d.split()
                    cmd = None
                    x = 0
                    y = 0
                    
                    if len(tokens) == 0:
                        continue
                        
                    # If first token isn't a command, assume an implicit 'M' command
                    if tokens[0] not in 'MLHVZCSTQAmlhvzcstqa':
                        cmd = 'M'
                    
                    i = 0
                    while i < len(tokens):
                        # Safety check for index out of bounds
                        if i >= len(tokens):
                            break
                            
                        token = tokens[i]
                        
                        # Check if token is a command
                        if token in 'MLHVZCSTQAmlhvzcstqa':
                            cmd = token
                            i += 1
                            continue
                        
                        # Process based on current command
                        try:
                            if cmd is not None and cmd in 'Mm' and i + 1 < len(tokens):
                                # moveto: M x y or m dx dy
                                x_val = parse_float(tokens[i])
                                y_val = parse_float(tokens[i + 1])
                                
                                if x_val is not None and y_val is not None:
                                    if cmd == 'm':  # relative
                                        x += x_val
                                        y += y_val
                                    else:  # absolute
                                        x = x_val
                                        y = y_val
                                    
                                    update_bbox(x, y)
                                i += 2
                                
                            elif cmd is not None and cmd in 'Ll' and i + 1 < len(tokens):
                                # lineto: L x y or l dx dy
                                x_val = parse_float(tokens[i])
                                y_val = parse_float(tokens[i + 1])
                                
                                if x_val is not None and y_val is not None:
                                    if cmd == 'l':  # relative
                                        x += x_val
                                        y += y_val
                                    else:  # absolute
                                        x = x_val
                                        y = y_val
                                    
                                    update_bbox(x, y)
                                i += 2
                                
                            elif cmd is not None and cmd in 'Hh':
                                # horizontal lineto: H x or h dx
                                x_val = parse_float(tokens[i])
                                
                                if x_val is not None:
                                    if cmd == 'h':  # relative
                                        x += x_val
                                    else:  # absolute
                                        x = x_val
                                    
                                    update_bbox(x, y)
                                i += 1
                                
                            elif cmd is not None and cmd in 'Vv':
                                # vertical lineto: V y or v dy
                                y_val = parse_float(tokens[i])
                                
                                if y_val is not None:
                                    if cmd == 'v':  # relative
                                        y += y_val
                                    else:  # absolute
                                        y = y_val
                                    
                                    update_bbox(x, y)
                                i += 1
                                
                            elif cmd is not None and cmd in 'Cc' and i + 5 < len(tokens):
                                # curveto: C x1 y1 x2 y2 x y or c dx1 dy1 dx2 dy2 dx dy
                                # Only store the final point for bbox
                                # Control points could extend outside the path
                                x1 = parse_float(tokens[i])
                                y1 = parse_float(tokens[i + 1])
                                x2 = parse_float(tokens[i + 2])
                                y2 = parse_float(tokens[i + 3])
                                x_val = parse_float(tokens[i + 4])
                                y_val = parse_float(tokens[i + 5])
                                
                                if cmd == 'c':  # relative
                                    # Include control points in bounding box
                                    update_bbox(x + x1, y + y1)
                                    update_bbox(x + x2, y + y2)
                                    x += x_val
                                    y += y_val
                                else:  # absolute
                                    # Include control points in bounding box
                                    update_bbox(x1, y1)
                                    update_bbox(x2, y2)
                                    x = x_val
                                    y = y_val
                                    
                                update_bbox(x, y)
                                i += 6
                                
                            elif cmd is not None and cmd in 'Ss' and i + 3 < len(tokens):
                                # shorthand/smooth curveto: S x2 y2 x y or s dx2 dy2 dx dy
                                x2 = parse_float(tokens[i])
                                y2 = parse_float(tokens[i + 1])
                                x_val = parse_float(tokens[i + 2])
                                y_val = parse_float(tokens[i + 3])
                                
                                if cmd == 's':  # relative
                                    update_bbox(x + x2, y + y2)
                                    x += x_val
                                    y += y_val
                                else:  # absolute
                                    update_bbox(x2, y2)
                                    x = x_val
                                    y = y_val
                                    
                                update_bbox(x, y)
                                i += 4
                                
                            elif cmd is not None and cmd in 'Qq' and i + 3 < len(tokens):
                                # quadratic curveto: Q x1 y1 x y or q dx1 dy1 dx dy
                                x1 = parse_float(tokens[i])
                                y1 = parse_float(tokens[i + 1])
                                x_val = parse_float(tokens[i + 2])
                                y_val = parse_float(tokens[i + 3])
                                
                                if cmd == 'q':  # relative
                                    update_bbox(x + x1, y + y1)
                                    x += x_val
                                    y += y_val
                                else:  # absolute
                                    update_bbox(x1, y1)
                                    x = x_val
                                    y = y_val
                                    
                                update_bbox(x, y)
                                i += 4
                                
                            elif cmd is not None and cmd in 'Tt' and i + 1 < len(tokens):
                                # shorthand/smooth quadratic curveto: T x y or t dx dy
                                x_val = parse_float(tokens[i])
                                y_val = parse_float(tokens[i + 1])
                                
                                if cmd == 't':  # relative
                                    x += x_val
                                    y += y_val
                                else:  # absolute
                                    x = x_val
                                    y = y_val
                                    
                                update_bbox(x, y)
                                i += 2
                                
                            elif cmd is not None and cmd in 'Aa' and i + 6 < len(tokens):
                                # elliptical arc: A rx ry x-axis-rotation large-arc-flag sweep-flag x y
                                # or a rx ry x-axis-rotation large-arc-flag sweep-flag dx dy
                                rx = parse_float(tokens[i])
                                ry = parse_float(tokens[i + 1])
                                # Skip rotation and flags
                                x_val = parse_float(tokens[i + 5])
                                y_val = parse_float(tokens[i + 6])
                                
                                if cmd == 'a':  # relative
                                    x += x_val
                                    y += y_val
                                else:  # absolute
                                    x = x_val
                                    y = y_val
                                    
                                update_bbox(x, y)
                                i += 7
                                
                            elif cmd is not None and cmd in 'Zz':
                                # closepath - no coordinates
                                i += 1
                                
                            else:
                                # Skip unknown commands or formats
                                i += 1
                        except (IndexError, ValueError):
                            i += 1
                except Exception:
                    pass

        # Handle cases where no elements were found or parsed
        if min_x == float('inf') or max_x == float('-inf') or min_y == float('inf') or max_y == float('-inf'):
            # If viewBox is specified, use it as fallback
            if viewbox_match:
                try:
                    viewbox_parts = viewbox.split()
                    if len(viewbox_parts) == 4:
                        min_x = float(viewbox_parts[0])
                        min_y = float(viewbox_parts[1])
                        width_val = float(viewbox_parts[2])
                        height_val = float(viewbox_parts[3])
                        max_x = min_x + width_val
                        max_y = min_y + height_val
                    else:
                        min_x = 0
                        max_x = 0
                        min_y = 0
                        max_y = 0
                except:
                    min_x = 0
                    max_x = 0
                    min_y = 0
                    max_y = 0
            else:
                min_x = 0
                max_x = 0
                min_y = 0
                max_y = 0
        
        # Calculate width and height
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

    def extract_svg_contents(self, svg_content: str) -> tuple[str, str]:
        """
        Extracts and cleans up SVG content by removing unnecessary elements and attributes.
        
        This method:
        1. Removes XML declaration
        2. Removes metadata elements
        3. Removes sodipodi:namedview elements
        4. Removes empty defs elements
        5. Removes Inkscape-specific attributes
        6. Removes stroke-related attributes (stroke, stroke-width, etc.)
        7. Extracts the inner content from the SVG tag
        
        Args:
            svg_content: Raw SVG content as a string
            
        Returns:
            tuple[str, str]: A tuple containing:
                - The SVG attributes string
                - The cleaned inner content string
                
        Example:
            svg_attrs, inner_content = svg_builder.extract_svg_contents(raw_svg)
        """
        # Remove XML declaration if present
        svg_content = re.sub(r'<\?xml[^>]*\?>', '', svg_content)
        
        # Extract the SVG tag and its attributes
        svg_match = re.search(r'<svg([^>]*)>(.*)</svg>', svg_content, re.DOTALL)
        if not svg_match:
            return "", ""
            
        svg_attrs_str = svg_match.group(1)
        inner_content = svg_match.group(2)
        
        # Remove namespace declarations for sodipodi/inkscape
        svg_attrs_str = re.sub(r'\sxmlns:sodipodi="[^"]*"', '', svg_attrs_str)
        svg_attrs_str = re.sub(r'\sxmlns:inkscape="[^"]*"', '', svg_attrs_str)
        
        # Remove metadata elements
        inner_content = re.sub(r'<metadata[^>]*>.*?</metadata>', '', inner_content, flags=re.DOTALL)
        
        # Remove sodipodi:namedview elements
        inner_content = re.sub(r'<sodipodi:namedview[^>]*>.*?</sodipodi:namedview>', '', inner_content, flags=re.DOTALL)
        inner_content = re.sub(r'<sodipodi:namedview[^>]*?/>', '', inner_content)
        
        # Remove empty <defs/> elements
        inner_content = re.sub(r'<defs\s*/>', '', inner_content, flags=re.DOTALL)
        
        # Remove Inkscape-specific attributes from all elements
        inner_content = re.sub(r'\sinkscape:[^=]+="[^"]*"', '', inner_content)
        
        # Remove Sodipodi-specific attributes from all elements
        inner_content = re.sub(r'\ssodipodi:[^=]+="[^"]*"', '', inner_content)
        
        # Remove stroke-related attributes
        stroke_attributes = [
            r'\sstroke-width="[^"]*"',
            r'\sstroke="[^"]*"',
            r'\sstroke-opacity="[^"]*"',
            r'\sstroke-dasharray="[^"]*"',
            r'\sstroke-dashoffset="[^"]*"',
            r'\sstroke-linecap="[^"]*"',
            r'\sstroke-linejoin="[^"]*"',
            r'\sstroke-miterlimit="[^"]*"'
        ]
        
        for attr_pattern in stroke_attributes:
            inner_content = re.sub(attr_pattern, '', inner_content)
        
        return svg_attrs_str, inner_content

    def add_schematic(self, svg_content: str, color: str = 'black') -> 'SVGBuilder':
        """
        Adds a schematic SVG to the canvas, scaling it to fit within the available space.
        The available space is defined by:
        - Top boundary: Bottom of the legend box or title/subtitle (whichever is lower)
        - Left/Right boundaries: Border insets
        - Bottom boundary: Border inset
        
        Args:
            svg_content: Raw SVG content as a string
            color: Color to use for strokes (default: 'black')
            
        Returns:
            The builder instance for method chaining
        """
        # --- Constants ---
        border_inset = 10 # mm
        # --- End Constants ---

        # Extract and clean up SVG contents
        svg_attrs, inner_content = self.extract_svg_contents(svg_content)
        
        # Calculate the actual bounding box of the SVG content
        bbox = self.calculate_bounding_box(svg_content)
        
        # Get the parent SVG's content to search for legend and title groups
        parent_svg = self.to_string()
        parent_svg_attrs, parent_inner_content = self.extract_svg_contents(parent_svg)
        
        # Find the upper boundary by checking legend and title groups
        upper_boundary = 0
        
        # Check legend group
        legend_pattern = r'<g[^>]*id="legend"[^>]*>.*?</g>'
        legend_match = re.search(legend_pattern, parent_inner_content, re.DOTALL)
        if legend_match:
            legend_content = legend_match.group(0)
            legend_svg_for_bbox = f"<svg>{legend_content}</svg>"
            legend_bbox = self.calculate_bounding_box(legend_svg_for_bbox)
            if legend_bbox['height'] > 0:
                legend_bottom = legend_bbox['min_y'] + legend_bbox['height']
                upper_boundary = max(upper_boundary, legend_bottom)
            else:
                pass
        else:
            pass

        # Check title group
        title_pattern = r'<g[^>]*id="titles"[^>]*>.*?</g>'
        title_match = re.search(title_pattern, parent_inner_content, re.DOTALL)
        if title_match:
            title_content = title_match.group(0)
            title_svg_for_bbox = f"<svg>{title_content}</svg>"
            title_bbox = self.calculate_bounding_box(title_svg_for_bbox)
            if title_bbox['height'] > 0:
                title_bottom = title_bbox['min_y'] + title_bbox['height']
                upper_boundary = max(upper_boundary, title_bottom)
            else:
                pass
        else:
            pass

        # Calculate available space for the schematic
        available_width = self.width - 2 * border_inset
        available_height = self.height - upper_boundary - border_inset

        # Check for non-positive dimensions or invalid bbox
        if available_width <= 0 or available_height <= 0 or bbox['width'] <= 0 or bbox['height'] <= 0:
             print(f"ERROR: Cannot place schematic. Invalid dimensions.")
             self.text(self.width / 2, self.height / 2, "Error: Cannot place schematic", {'fill': 'red', 'text-anchor': 'middle'})
             return self

        # Calculate the initial scale factor to fit the schematic
        scale_x = available_width / bbox['width']
        scale_y = available_height / bbox['height']
        # Use 80% of the minimum fitting scale
        scale = min(scale_x, scale_y) * 0.85 

        # Calculate the dimensions of the scaled schematic
        scaled_width = bbox['width'] * scale
        scaled_height = bbox['height'] * scale

        # --- Calculate Translation --- 
        # Goal: Center the 80% scaled schematic within the available area.
        
        # Calculate X translation:
        available_x_start = border_inset
        final_schematic_x = available_x_start + (available_width - scaled_width) / 2
        translate_x = final_schematic_x - (bbox['min_x'] * scale)

        # Calculate Y translation:
        available_y_start = upper_boundary # Top of the available space
        final_schematic_y = available_y_start + (available_height - scaled_height) / 2
        translate_y = final_schematic_y - (bbox['min_y'] * scale)
        # --- End Calculate Translation ---

        # Create a group for the schematic with the calculated transform
        group_attrs = {
            'transform': f'translate({translate_x:.2f}, {translate_y:.2f}) scale({scale:.4f})',
            'id': 'schematic-content' # Add an ID for easier selection/debugging
        }

        # Add the schematic in a new group
        self.begin_group(group_attrs)
        
        # Add default stroke attributes to all elements that can have strokes
        elements_with_strokes = [
            ('path', r'<path([^>]*)>'),
            ('rect', r'<rect([^>]*)>'),
            ('circle', r'<circle([^>]*)>'),
            ('ellipse', r'<ellipse([^>]*)>'),
            ('line', r'<line([^>]*)>'),
            ('polyline', r'<polyline([^>]*)>'),
            ('polygon', r'<polygon([^>]*)>')
        ]
        
        # First, remove any style attributes that might override our stroke settings
        for element_name, element_pattern in elements_with_strokes:
            def remove_style_attr(match):
                attrs = match.group(1)
                # Remove style attributes that might contain stroke properties
                attrs = re.sub(r'\sstyle="[^"]*"', '', attrs)
                return f'<{element_name}{attrs}>'
            
            inner_content = re.sub(element_pattern, remove_style_attr, inner_content)

        # Then add our stroke attributes if they don't exist
        for element_name, element_pattern in elements_with_strokes:
            def add_stroke_attrs(match):
                attrs = match.group(1)
                # Check if the element already has a stroke attribute
                if 'stroke=' not in attrs:
                    attrs = f' stroke="{color}" stroke-width="1"{attrs}'
                return f'<{element_name}{attrs}>'
            
            inner_content = re.sub(element_pattern, add_stroke_attrs, inner_content)
        
        # Add the inner content directly without the containing SVG tag
        self._add_element(inner_content)
        self.end_group()
        
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

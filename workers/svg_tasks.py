"""Background tasks for SVG generation"""
import os
from libraries.svg_builder import SVGBuilder


def generate_complex_svg(width, height, pattern_type, output_filename):
    """
    Generate complex SVG patterns in the background
    
    Args:
        width: SVG width in mm
        height: SVG height in mm
        pattern_type: Type of pattern to generate
        output_filename: Filename to save the SVG
        
    Returns:
        Path to the generated SVG file
    """
    svg = SVGBuilder(width, height, {'stroke': 'black', 'fill': 'none'})
    
    if pattern_type == 'spiral':
        # Generate spiral pattern for pen plotter
        import math
        center_x, center_y = width / 2, height / 2
        max_radius = min(width, height) / 2 * 0.9
        
        points = []
        for i in range(0, 1000):
            angle = i * 0.1
            radius = (i / 1000) * max_radius
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append(f"{x},{y}")
        
        svg.path(f"M {points[0]} L {' L '.join(points[1:])}", {'stroke-width': '0.5'})
        
    elif pattern_type == 'grid':
        # Generate grid pattern
        spacing = 10
        for x in range(0, int(width), spacing):
            svg.line(x, 0, x, height, {'stroke-width': '0.3'})
        for y in range(0, int(height), spacing):
            svg.line(0, y, width, y, {'stroke-width': '0.3'})
    
    # Save to output directory (now in tests/output/generated)
    output_dir = os.path.join('tests', 'output', 'generated')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, 'w') as f:
        f.write(svg.to_string())
    
    return output_path


def batch_generate_svgs(job_list):
    """
    Generate multiple SVGs in a batch job
    
    Args:
        job_list: List of dicts with svg parameters
        
    Returns:
        List of generated file paths
    """
    results = []
    for job in job_list:
        path = generate_complex_svg(
            job['width'],
            job['height'], 
            job['pattern_type'],
            job['filename']
        )
        results.append(path)
    
    return results 
import pytest
import sys
import os
import tempfile
import io

# Add the parent directory to the path so we can import from libraries
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVpypeIntegration:
    """Test suite for vpype integration"""

    def test_vpype_import(self):
        """Test that vpype can be imported successfully"""
        try:
            import vpype
            import vpype_cli
            assert True  # If we get here, imports worked
        except ImportError as e:
            pytest.fail(f"Failed to import vpype: {e}")

    def test_vpype_basic_pipeline(self):
        """Test that vpype can execute a basic pipeline programmatically"""
        try:
            import vpype_cli
            
            # Create a simple test SVG
            test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" viewBox="0 0 100 100">
    <path d="M10,10 L90,10 L90,90 L10,90 Z" stroke="black" fill="none" stroke-width="1"/>
    <path d="M20,20 L80,20 L80,80 L20,80 Z" stroke="black" fill="none" stroke-width="1"/>
</svg>'''
            
            # Test basic pipeline execution using temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as temp_input:
                temp_input.write(test_svg)
                temp_input_path = temp_input.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='_output.svg', delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            try:
                # Simple vpype pipeline - read, apply basic optimizations, write
                pipeline = f'read "{temp_input_path}" linemerge linesort write "{temp_output_path}"'
                document = vpype_cli.execute(pipeline)
                
                # Check that we got a document back
                assert document is not None
                
                # Check that output file was created and has content
                assert os.path.exists(temp_output_path)
                assert os.path.getsize(temp_output_path) > 0
                
                # Read the output to verify it's valid SVG
                with open(temp_output_path, 'r') as f:
                    output_content = f.read()
                    assert '<?xml' in output_content
                    assert '<svg' in output_content
                    assert '</svg>' in output_content
                    
            finally:
                # Clean up temp files
                if os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
                    
        except Exception as e:
            pytest.fail(f"vpype pipeline execution failed: {e}")

    def test_vpype_optimization_commands(self):
        """Test specific vpype optimization commands"""
        try:
            import vpype_cli
            
            # Create a test SVG with multiple disconnected paths that could be optimized
            test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" viewBox="0 0 100 100">
    <path d="M10,10 L50,10" stroke="black" fill="none" stroke-width="1"/>
    <path d="M50,10 L90,10" stroke="black" fill="none" stroke-width="1"/>
    <path d="M90,10 L90,50" stroke="black" fill="none" stroke-width="1"/>
    <path d="M90,50 L90,90" stroke="black" fill="none" stroke-width="1"/>
</svg>'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as temp_file:
                temp_file.write(test_svg)
                temp_path = temp_file.name
            
            try:
                # Test pipeline with pen plotter optimizations
                pipeline = f'''read "{temp_path}" 
                            linemerge --tolerance 0.1mm 
                            linesort 
                            linesimplify --tolerance 0.05mm'''
                
                document = vpype_cli.execute(pipeline)
                
                # Verify we got a document back
                assert document is not None
                print(f"✅ vpype optimization pipeline executed successfully!")
                print(f"Document has {len(document.layers)} layers")
                
                # Test that we can access layer information
                if len(document.layers) > 0:
                    layer_id = list(document.layers.keys())[0]
                    layer = document.layers[layer_id]
                    print(f"First layer has {len(layer.lines)} lines")
                    
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            pytest.fail(f"vpype optimization commands failed: {e}")

    def test_vpype_document_api(self):
        """Test working with vpype Document objects directly"""
        try:
            import vpype
            
            # Create a test SVG content
            test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" viewBox="0 0 100 100">
    <rect x="10" y="10" width="80" height="80" stroke="black" fill="none" stroke-width="1"/>
</svg>'''
            
            # Test reading SVG into Document
            svg_io = io.StringIO(test_svg)
            document = vpype.read_multilayer_svg(svg_io, quantization=0.1)
            
            # Verify document structure
            assert document is not None
            assert len(document.layers) > 0
            
            # Test that we can access layers
            layer_ids = list(document.layers.keys())
            assert len(layer_ids) > 0
            
            # Test that layers contain line collections
            first_layer = document.layers[layer_ids[0]]
            assert hasattr(first_layer, 'lines')
            assert len(first_layer.lines) > 0
            
            print(f"✅ vpype Document API working correctly!")
            print(f"Document has {len(document.layers)} layers")
            print(f"First layer has {len(first_layer.lines)} lines")
            
        except Exception as e:
            pytest.fail(f"vpype Document API failed: {e}")

    def test_vpype_svg_output(self):
        """Test converting vpype Document back to SVG"""
        try:
            import vpype
            import vpype_cli
            
            test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="30" stroke="black" fill="none" stroke-width="1"/>
</svg>'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as temp_file:
                temp_file.write(test_svg)
                temp_path = temp_file.name
            
            try:
                # Read SVG and convert back to SVG string via vpype
                pipeline = f'read "{temp_path}"'
                document = vpype_cli.execute(pipeline)
                
                # Convert document back to SVG
                output_io = io.StringIO()
                vpype.write_svg(output_io, document)
                svg_output = output_io.getvalue()
                
                # Verify the output is valid SVG
                assert '<?xml' in svg_output
                assert '<svg' in svg_output
                assert '</svg>' in svg_output
                
                print("✅ vpype SVG output generation working!")
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            pytest.fail(f"vpype SVG output failed: {e}") 
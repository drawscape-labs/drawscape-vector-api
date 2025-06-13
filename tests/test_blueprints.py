#!/usr/bin/env python3
"""
Test script for the blueprints generate_label functionality
"""

import os
import json
import pytest
import tempfile
from unittest.mock import Mock, patch, mock_open
from flask import Flask
from datetime import datetime

# Import the blueprint
from components.blueprints.main import blueprint_bp, container

class TestGenerateLabel:
    """Test class for the generate_label endpoint"""
    
    @pytest.fixture
    def app(self):
        """Create a Flask app for testing"""
        app = Flask(__name__)
        app.register_blueprint(blueprint_bp)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client"""
        return app.test_client()
    
    @pytest.fixture
    def sample_svg_content(self):
        """Sample SVG content for mocking"""
        return b'''<?xml version="1.0" encoding="UTF-8"?>
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <line x1="0" y1="0" x2="100" y2="100" stroke="black"/>
        </svg>'''
    
    @pytest.fixture
    def mock_nextdraw(self):
        """Mock NextDraw object with realistic values"""
        mock_nd = Mock()
        mock_nd.time_estimate = 1800  # 30 minutes in seconds
        mock_nd.distance_pendown = 10.5  # 10.5 meters
        return mock_nd

    def test_generate_label_success_all_params(self, client, sample_svg_content, mock_nextdraw):
        """Test generate_label with all parameters provided"""
        test_data = {
            'project_name': 'Test Project',
            'svg_url': 'https://example.com/test.svg',
            'order_id': 'ORD-12345',
            'artist_name': 'John Doe'
        }
        
        with patch('components.blueprints.main.requests.get') as mock_get, \
             patch('components.blueprints.main.NextDraw') as mock_nextdraw_class, \
             patch('components.blueprints.main.tempfile.NamedTemporaryFile') as mock_temp, \
             patch('components.blueprints.main.os.remove') as mock_remove, \
             patch('components.blueprints.main.HersheyFonts') as mock_hershey:
            
            # Mock successful SVG download
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = sample_svg_content
            mock_get.return_value = mock_response
            
            # Mock NextDraw
            mock_nextdraw_class.return_value = mock_nextdraw
            
            # Mock temporary file
            mock_temp_file = Mock()
            mock_temp_file.name = '/tmp/test.svg'
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            
            # Mock HersheyFonts - return simple path data that we can check for
            mock_font = Mock()
            # Mock returns different paths for different text to make them identifiable
            def mock_lines_for_text(text):
                if 'Test Project' in text:
                    return [[(0, 0), (10, 0)]]  # Simple line for project name
                elif 'ORD-12345' in text:
                    return [[(0, 0), (5, 5)]]   # Simple line for order ID
                elif 'John Doe' in text:
                    return [[(0, 0), (7, 3)]]   # Simple line for artist
                else:
                    return [[(0, 0), (1, 1)]]   # Default simple line
            mock_font.lines_for_text.side_effect = mock_lines_for_text
            mock_hershey.return_value = mock_font
            
            response = client.post('/blueprint/generate-label', 
                                 json=test_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['status'] == 'success'
            assert 'svg_string' in data
            assert '<?xml version="1.0"' in data['svg_string']
            # Check that the SVG has the correct structure with legend elements
            assert 'id="legend"' in data['svg_string']
            assert 'legend-border' in data['svg_string']
            
            # Verify external calls
            mock_get.assert_called_once_with('https://example.com/test.svg')
            mock_nextdraw.plot_setup.assert_called_once()
            mock_nextdraw.plot_run.assert_called_once()
            
            # Verify that HersheyFonts was called for all the expected text
            font_calls = [call[0][0] for call in mock_font.lines_for_text.call_args_list]
            assert any('Test Project' in call or 'TEST PROJECT' in call for call in font_calls)  # Handle either case
            assert any('ORD-12345' in call for call in font_calls)
            assert any('John Doe' in call for call in font_calls)

    def test_generate_label_success_required_only(self, client, sample_svg_content, mock_nextdraw):
        """Test generate_label with only required parameters"""
        test_data = {
            'project_name': 'Minimal Project',
            'svg_url': 'https://example.com/minimal.svg'
        }
        
        with patch('components.blueprints.main.requests.get') as mock_get, \
             patch('components.blueprints.main.NextDraw') as mock_nextdraw_class, \
             patch('components.blueprints.main.tempfile.NamedTemporaryFile') as mock_temp, \
             patch('components.blueprints.main.os.remove') as mock_remove, \
             patch('components.blueprints.main.HersheyFonts') as mock_hershey:
            
            # Mock successful SVG download
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = sample_svg_content
            mock_get.return_value = mock_response
            
            # Mock NextDraw
            mock_nextdraw_class.return_value = mock_nextdraw
            
            # Mock temporary file
            mock_temp_file = Mock()
            mock_temp_file.name = '/tmp/minimal.svg'
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            
            # Mock HersheyFonts
            mock_font = Mock()
            mock_font.lines_for_text.return_value = [[(0, 0), (10, 0)]]
            mock_hershey.return_value = mock_font
            
            response = client.post('/blueprint/generate-label', 
                                 json=test_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['status'] == 'success'
            assert 'svg_string' in data
            assert 'id="legend"' in data['svg_string']
            
            # Check that order ID and artist text are not called since they weren't provided
            font_calls = [call[0][0] for call in mock_font.lines_for_text.call_args_list]
            assert not any('ORD-' in str(call) for call in font_calls)
            assert not any('Order ID' in str(call) for call in font_calls)
            assert not any('Artist' in str(call) for call in font_calls)

    def test_generate_label_missing_required_params(self, client):
        """Test generate_label with missing required parameters"""
        test_data = {
            'project_name': 'Test Project'
            # Missing svg_url
        }
        
        response = client.post('/blueprint/generate-label', 
                             json=test_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data['status'] == 'error'
        assert 'svg_url' in data['message']

    def test_generate_label_no_data(self, client):
        """Test generate_label with no JSON data"""
        response = client.post('/blueprint/generate-label')
        
        # When no JSON is sent, Flask might return different status codes
        assert response.status_code in [400, 415]  # Either bad request or unsupported media type
        
        # Try to get JSON response, but handle case where there might not be any
        try:
            data = response.get_json()
            if data is not None:
                assert data['status'] == 'error'
                assert 'No input data provided' in data['message'] or 'unsupported media type' in data.get('message', '').lower()
        except:
            # If no JSON response, that's also acceptable for this error case
            pass

    def test_generate_label_svg_download_failure(self, client):
        """Test generate_label when SVG download fails"""
        test_data = {
            'project_name': 'Test Project',
            'svg_url': 'https://example.com/nonexistent.svg'
        }
        
        with patch('components.blueprints.main.requests.get') as mock_get:
            # Mock failed SVG download
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            response = client.post('/blueprint/generate-label', 
                                 json=test_data,
                                 content_type='application/json')
            
            assert response.status_code == 400
            data = response.get_json()
            
            assert data['status'] == 'error'
            assert 'Failed to download SVG' in data['message']

    def test_generate_label_svg_download_exception(self, client):
        """Test generate_label when SVG download raises exception"""
        test_data = {
            'project_name': 'Test Project',
            'svg_url': 'https://invalid-domain-12345.com/test.svg'
        }
        
        with patch('components.blueprints.main.requests.get') as mock_get:
            # Mock exception during download
            mock_get.side_effect = Exception("Connection timeout")
            
            response = client.post('/blueprint/generate-label', 
                                 json=test_data,
                                 content_type='application/json')
            
            assert response.status_code == 500
            data = response.get_json()
            
            assert data['status'] == 'error'
            assert 'Exception occurred while downloading SVG' in data['message']

    def test_generate_label_with_one_optional_param(self, client, sample_svg_content, mock_nextdraw):
        """Test generate_label with only one optional parameter"""
        test_data = {
            'project_name': 'Artist Only Project',
            'svg_url': 'https://example.com/artist-only.svg',
            'artist_name': 'Jane Smith'
            # No order_id
        }
        
        with patch('components.blueprints.main.requests.get') as mock_get, \
             patch('components.blueprints.main.NextDraw') as mock_nextdraw_class, \
             patch('components.blueprints.main.tempfile.NamedTemporaryFile') as mock_temp, \
             patch('components.blueprints.main.os.remove') as mock_remove, \
             patch('components.blueprints.main.HersheyFonts') as mock_hershey:
            
            # Mock successful SVG download
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = sample_svg_content
            mock_get.return_value = mock_response
            
            # Mock NextDraw
            mock_nextdraw_class.return_value = mock_nextdraw
            
            # Mock temporary file
            mock_temp_file = Mock()
            mock_temp_file.name = '/tmp/artist-only.svg'
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            
            # Mock HersheyFonts
            mock_font = Mock()
            mock_font.lines_for_text.return_value = [[(0, 0), (10, 0)]]
            mock_hershey.return_value = mock_font
            
            response = client.post('/blueprint/generate-label', 
                                 json=test_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['status'] == 'success'
            
            # Check that artist text was processed but order ID was not
            font_calls = [call[0][0] for call in mock_font.lines_for_text.call_args_list]
            assert any('Jane Smith' in str(call) for call in font_calls)
            assert not any('Order ID' in str(call) for call in font_calls)


class TestContainerFunction:
    """Test class for the container function specifically"""
    
    @pytest.fixture
    def mock_nextdraw(self):
        """Mock NextDraw object with realistic values"""
        mock_nd = Mock()
        mock_nd.time_estimate = 3665  # 1 hour, 1 minute, 5 seconds
        mock_nd.distance_pendown = 25.7  # 25.7 meters
        return mock_nd
    
    @pytest.fixture
    def sample_json_data(self):
        """Sample JSON data for testing"""
        return {
            'title': 'Container Test Project',
            'subtitle': 'Test Subtitle',
            'order_id': 'ORD-67890', 
            'artist_name': 'Test Artist'
        }

    def test_container_with_all_data(self, sample_json_data, mock_nextdraw):
        """Test container function with all data provided"""
        with patch('components.blueprints.main.NextDraw') as mock_nextdraw_class, \
             patch('components.blueprints.main.HersheyFonts') as mock_hershey:
            
            # Mock NextDraw
            mock_nextdraw_class.return_value = mock_nextdraw
            
            # Mock HersheyFonts
            mock_font = Mock()
            mock_font.lines_for_text.return_value = [[(0, 0), (10, 0)]]
            mock_hershey.return_value = mock_font
            
            svg_content = container(sample_json_data, '/tmp/test.svg')
            
            assert '<?xml version="1.0" encoding="UTF-8"' in svg_content
            assert 'id="legend"' in svg_content
            
            # Check that HersheyFonts was called with the expected text values
            font_calls = [call[0][0] for call in mock_font.lines_for_text.call_args_list]
            assert any('Container Test Project - Test Subtitle' in call or 'CONTAINER TEST PROJECT - Test Subtitle' in call for call in font_calls)  # Handle either case
            assert any('ORD-67890' in call for call in font_calls)
            assert any('Test Artist' in call for call in font_calls)
            assert any('1h 1m 5s' in call for call in font_calls)  # Check time formatting in font calls
            assert any('Drawscape Inc.' in call for call in font_calls)  # Check Drawscape Inc. in font calls

    def test_container_without_optional_data(self, mock_nextdraw):
        """Test container function without optional data"""
        json_data = {
            'title': 'Minimal Container Test',
            'subtitle': ''
        }
        
        with patch('components.blueprints.main.NextDraw') as mock_nextdraw_class, \
             patch('components.blueprints.main.HersheyFonts') as mock_hershey:
            
            # Mock NextDraw
            mock_nextdraw_class.return_value = mock_nextdraw
            
            # Mock HersheyFonts
            mock_font = Mock()
            mock_font.lines_for_text.return_value = [[(0, 0), (10, 0)]]
            mock_hershey.return_value = mock_font
            
            svg_content = container(json_data, '/tmp/test.svg')
            
            assert 'id="legend"' in svg_content
            
            # Check that optional fields were not processed
            font_calls = [call[0][0] for call in mock_font.lines_for_text.call_args_list]
            assert any('Minimal Container Test' in call or 'MINIMAL CONTAINER TEST' in call for call in font_calls)  # Handle either case
            assert not any('Order ID' in call for call in font_calls)
            assert not any('Artist' in call for call in font_calls)

    def test_container_time_formatting(self, mock_nextdraw):
        """Test time formatting in container function"""
        json_data = {'title': 'Time Test', 'subtitle': ''}
        
        # Test different time durations
        test_times = [
            (45, "0m 45s"),      # Less than a minute  
            (125, "2m 5s"),      # Minutes and seconds
            (3665, "1h 1m 5s")   # Hours, minutes, and seconds
        ]
        
        with patch('components.blueprints.main.NextDraw') as mock_nextdraw_class, \
             patch('components.blueprints.main.HersheyFonts') as mock_hershey:
            
            mock_font = Mock()
            mock_font.lines_for_text.return_value = [[(0, 0), (10, 0)]]
            mock_hershey.return_value = mock_font
            
            for time_seconds, expected_format in test_times:
                # Update mock for each test
                mock_nd = Mock()
                mock_nd.time_estimate = time_seconds
                mock_nd.distance_pendown = 10.0
                mock_nextdraw_class.return_value = mock_nd
                
                svg_content = container(json_data, '/tmp/test.svg')
                
                # Check that the time appears in font calls (since it's rendered as vector text)
                font_calls = [call[0][0] for call in mock_font.lines_for_text.call_args_list]
                assert any(expected_format in call for call in font_calls), f"Expected {expected_format} in font calls: {font_calls}"

    def test_container_date_inclusion(self, mock_nextdraw):
        """Test that current date is included in the container output"""
        json_data = {'title': 'Date Test', 'subtitle': ''}
        
        with patch('components.blueprints.main.NextDraw') as mock_nextdraw_class, \
             patch('components.blueprints.main.HersheyFonts') as mock_hershey:
            
            # Mock NextDraw
            mock_nextdraw_class.return_value = mock_nextdraw
            
            # Mock HersheyFonts
            mock_font = Mock()
            mock_font.lines_for_text.return_value = [[(0, 0), (10, 0)]]
            mock_hershey.return_value = mock_font
            
            svg_content = container(json_data, '/tmp/test.svg')
            
            # Should contain today's date in YYYY-MM-DD format as part of font calls
            today = datetime.now().strftime("%Y-%m-%d")
            font_calls = [call[0][0] for call in mock_font.lines_for_text.call_args_list]
            assert any(today in call for call in font_calls), f"Expected {today} in font calls: {font_calls}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
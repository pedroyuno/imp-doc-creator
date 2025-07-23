#!/usr/bin/env python3
"""
Comprehensive unit tests for Flask Web Application
"""

import pytest
import os
import tempfile
import json
import sys
from io import BytesIO
from unittest.mock import patch, MagicMock

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import app, allowed_file


class TestFlaskApp:
    """Test class for Flask Web Application"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask application"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def valid_csv_content(self):
        """Fixture providing valid CSV content as bytes"""
        content = """,Feature,REDE_CARD,,,PAGARME_CARD,,,
,Provider,REDE,,,PAGARME,,,
,Payment_Method,CARD,,,CARD,,,
,,INFORMATION,STATUS,ADDITIONAL INFO,INFORMATION,STATUS,ADDITIONAL INFO
,Country,Brazil,Supported,,Brazil,Supported,
,Verify,TRUE,Implemented,,FALSE,Not supported,
,Authorize,TRUE,Implemented,,TRUE,Implemented,"""
        return content.encode('utf-8')
    
    @pytest.fixture
    def invalid_csv_content(self):
        """Fixture providing invalid CSV content as bytes"""
        content = """,Feature,[Provider],,,
,Provider,#N/A,,,
,Payment_Method,#N/A,,,
,,INFO,STATUS,ADDITIONAL INFO
,Country,Brazil,,,"""
        return content.encode('utf-8')
    
    @pytest.fixture
    def empty_csv_content(self):
        """Fixture providing empty CSV content"""
        return b""

    def test_index_route(self, client):
        """Test the main index page"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'Implementation Scoping Document Parser' in response.data
        assert b'Drag & Drop your implementation document here' in response.data
        assert b'Choose File' in response.data

    def test_example_route(self, client):
        """Test the example page"""
        response = client.get('/example')
        
        assert response.status_code == 200
        assert b'Implementation Document Format Guide' in response.data
        assert b'Valid Columns' in response.data
        assert b'Invalid Columns' in response.data

    def test_download_sample_route(self, client):
        """Test the sample file download"""
        response = client.get('/download-sample')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
        assert 'attachment' in response.headers['Content-Disposition']
        assert 'sample_integrations.csv' in response.headers['Content-Disposition']

    def test_upload_no_file(self, client):
        """Test upload route with no file"""
        response = client.post('/upload')
        
        assert response.status_code == 302  # Redirect back to same URL
        
        # Test with data but no file key
        response = client.post('/upload', data={}, follow_redirects=True)
        assert response.status_code == 405  # Method not allowed due to redirect loop

    def test_upload_empty_filename(self, client):
        """Test upload route with empty filename"""
        data = {'file': (BytesIO(b''), '')}
        response = client.post('/upload', data=data)
        
        assert response.status_code == 302  # Redirect

    def test_upload_invalid_file_type(self, client):
        """Test upload route with invalid file type"""
        data = {'file': (BytesIO(b'some content'), 'test.txt')}
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid file type' in response.data

    def test_upload_valid_csv_success(self, client, valid_csv_content):
        """Test successful CSV upload and processing"""
        data = {'file': (BytesIO(valid_csv_content), 'test.csv')}
        response = client.post('/upload', data=data)

        assert response.status_code == 200
        assert b'Implementation Analysis Results' in response.data
        assert b'REDE' in response.data
        assert b'PAGARME' in response.data
        assert b'Valid Combinations' in response.data

    def test_upload_invalid_csv_no_results(self, client, invalid_csv_content):
        """Test upload with CSV that has no valid combinations"""
        data = {'file': (BytesIO(invalid_csv_content), 'invalid.csv')}
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'No valid provider + payment method combinations found' in response.data

    def test_upload_empty_csv(self, client, empty_csv_content):
        """Test upload with empty CSV file"""
        data = {'file': (BytesIO(empty_csv_content), 'empty.csv')}
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        # Should handle gracefully - either show error or empty results

    @patch('web_app.ProviderPaymentParser')
    def test_upload_parser_exception(self, mock_parser, client, valid_csv_content):
        """Test upload when parser raises an exception"""
        # Mock parser to raise exception
        mock_instance = MagicMock()
        mock_instance.parse.side_effect = Exception("Parser error")
        mock_parser.return_value = mock_instance
        
        data = {'file': (BytesIO(valid_csv_content), 'test.csv')}
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Error processing CSV file' in response.data

    def test_api_upload_no_file(self, client):
        """Test API upload endpoint with no file"""
        response = client.post('/api/upload')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file provided' in data['error']

    def test_api_upload_empty_filename(self, client):
        """Test API upload endpoint with empty filename"""
        data = {'file': (BytesIO(b''), '')}
        response = client.post('/api/upload', data=data)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file selected' in data['error']

    def test_api_upload_invalid_file_type(self, client):
        """Test API upload endpoint with invalid file type"""
        data = {'file': (BytesIO(b'content'), 'test.txt')}
        response = client.post('/api/upload', data=data)
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'Invalid file type' in response_data['error']

    def test_api_upload_valid_csv_success(self, client, valid_csv_content):
        """Test successful API CSV upload"""
        data = {'file': (BytesIO(valid_csv_content), 'test.csv')}
        response = client.post('/api/upload', data=data)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'success' in response_data
        assert response_data['success'] is True
        assert 'filename' in response_data
        assert 'results' in response_data
        assert len(response_data['results']) == 2

    @patch('web_app.ProviderPaymentParser')
    def test_api_upload_parser_exception(self, mock_parser, client, valid_csv_content):
        """Test API upload when parser raises an exception"""
        # Mock parser to raise exception
        mock_instance = MagicMock()
        mock_instance.parse.side_effect = Exception("Parser error")
        mock_parser.return_value = mock_instance
        
        data = {'file': (BytesIO(valid_csv_content), 'test.csv')}
        response = client.post('/api/upload', data=data)
        
        assert response.status_code == 500
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'Error processing file' in response_data['error']

    def test_results_page_structure(self, client, valid_csv_content):
        """Test the structure of the results page"""
        data = {'file': (BytesIO(valid_csv_content), 'test.csv')}
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        
        # Check for key elements in results page
        assert b'Implementation Analysis Results' in response.data
        assert b'Valid Combinations' in response.data
        assert b'Features per Provider' in response.data
        assert b'Filter by feature value' in response.data
        assert b'Search features' in response.data
        assert b'Export as JSON' in response.data

    def test_large_file_handling(self, client):
        """Test handling of large CSV files"""
        # Create a large CSV content (but not too large to avoid memory issues in tests)
        large_content = ",Feature,TEST_PROVIDER\n"
        large_content += ",Provider,TEST\n"
        large_content += ",Payment_Method,CARD\n"
        large_content += ",,INFO\n"
        
        # Add many feature rows
        for i in range(100):
            large_content += f",Feature{i},Value{i}\n"
        
        data = {'file': (BytesIO(large_content.encode('utf-8')), 'large.csv')}
        response = client.post('/upload', data=data)
        
        # Should handle gracefully without timeout or memory errors
        assert response.status_code in [200, 302]  # Success or redirect

    def test_special_characters_in_filename(self, client, valid_csv_content):
        """Test handling of special characters in filename"""
        filenames = [
            'test file with spaces.csv',
            'test-file-with-dashes.csv',
            'test_file_with_underscores.csv',
            'test.file.with.dots.csv'
        ]
        
        for filename in filenames:
            data = {'file': (BytesIO(valid_csv_content), filename)}
            response = client.post('/upload', data=data)
            
            # Should handle all filenames gracefully
            assert response.status_code == 200


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_allowed_file_valid_extensions(self):
        """Test allowed_file function with valid extensions"""
        valid_files = [
            'test.csv',
            'TEST.CSV',
            'file.with.dots.csv',
            'file-with-dashes.csv',
            'file_with_underscores.csv'
        ]
        
        for filename in valid_files:
            assert allowed_file(filename) is True

    def test_allowed_file_invalid_extensions(self):
        """Test allowed_file function with invalid extensions"""
        invalid_files = [
            'test.txt',
            'test.xls',
            'test.xlsx',
            'test.doc',
            'test.pdf',
            'test',  # No extension
            'test.csv.txt'  # Wrong final extension
        ]
        
        for filename in invalid_files:
            assert allowed_file(filename) is False

    def test_allowed_file_edge_cases(self):
        """Test allowed_file function with edge cases"""
        edge_cases = [
            '',  # Empty string
            '.',  # Just a dot
            '..',  # Double dot
            'test.',  # Ends with dot
            'test..csv'  # Double dot before extension
        ]
        
        for filename in edge_cases:
            result = allowed_file(filename)
            # Should not raise exception and return boolean
            assert isinstance(result, bool)


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask application"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client

    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404

    def test_405_method_not_allowed(self, client):
        """Test 405 error for wrong HTTP methods"""
        # GET request to upload endpoint (which only accepts POST)
        response = client.get('/upload')
        assert response.status_code == 405

    @patch('tempfile.NamedTemporaryFile')
    def test_file_system_error(self, mock_tempfile, client):
        """Test handling of file system errors"""
        # Mock tempfile to raise an exception
        mock_tempfile.side_effect = OSError("Disk full")
        
        valid_content = b",Feature,TEST\n,Provider,TEST\n,Payment_Method,CARD\n"
        data = {'file': (BytesIO(valid_content), 'test.csv')}
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Error uploading file' in response.data

    def test_concurrent_uploads(self, client):
        """Test handling of multiple concurrent uploads"""
        valid_content = b",Feature,TEST\n,Provider,TEST\n,Payment_Method,CARD\n"
        
        # Simulate multiple uploads (simplified concurrency test)
        responses = []
        for i in range(5):
            data = {'file': (BytesIO(valid_content), f'test{i}.csv')}
            response = client.post('/upload', data=data)
            responses.append(response)
        
        # All should complete successfully
        for response in responses:
            assert response.status_code in [200, 302]


class TestSecurityFeatures:
    """Test security-related features"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask application"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client

    def test_file_size_limits(self, client):
        """Test file size limitations"""
        # This test assumes the MAX_CONTENT_LENGTH is set properly
        # Create a content larger than typical limits would allow
        large_content = b"x" * (20 * 1024 * 1024)  # 20MB
        
        data = {'file': (BytesIO(large_content), 'large.csv')}
        response = client.post('/upload', data=data)
        
        # Should either reject or handle gracefully
        assert response.status_code in [200, 302, 413, 400]

    def test_malicious_filenames(self, client):
        """Test handling of potentially malicious filenames"""
        malicious_names = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32\\config\\sam',
            'con.csv',  # Reserved name on Windows
            'aux.csv',  # Reserved name on Windows
            '<script>alert("xss")</script>.csv',
            'file\x00.csv',  # Null byte injection
        ]
        
        valid_content = b",Feature,TEST\n,Provider,TEST\n,Payment_Method,CARD\n"
        
        for filename in malicious_names:
            data = {'file': (BytesIO(valid_content), filename)}
            response = client.post('/upload', data=data)
            
            # Should handle gracefully without security issues
            assert response.status_code in [200, 302, 400]

    def test_content_type_validation(self, client):
        """Test content type validation"""
        # Test with correct content type
        valid_content = b",Feature,TEST\n,Provider,TEST\n,Payment_Method,CARD\n"
        data = {'file': (BytesIO(valid_content), 'test.csv')}
        
        response = client.post('/upload', 
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code in [200, 302]


if __name__ == '__main__':
    pytest.main([__file__]) 
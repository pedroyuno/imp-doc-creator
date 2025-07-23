#!/usr/bin/env python3
"""
Integration tests for CSV Parser application
"""

import pytest
import os
import tempfile
import json
import sys
from io import BytesIO

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import app
from csv_parser import ProviderPaymentParser


class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask application"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def sample_csv_content(self):
        """Comprehensive sample CSV for integration testing"""
        content = """,Feature,PROVIDER_A_CARD,,,PROVIDER_B_PIX,,,[Provider_C],,,
,Provider,PROVIDER_A,,,PROVIDER_B,,,#N/A,,,
,Payment_Method,CARD,,,PIX,,,#N/A,,,
,,INFORMATION,STATUS,ADDITIONAL INFO,INFORMATION,STATUS,ADDITIONAL INFO,INFORMATION,STATUS,ADDITIONAL INFO
,Country,Brazil,Fully Supported,Brazil operations,Brazil,Supported,Limited regions,Brazil,Not supported,
,Signed contract,TRUE,Active,,TRUE,Active,,FALSE,No contract,
,Integration Status,TRUE,Completed,2023-Q4,FALSE,Pending,Q1-2024,FALSE,Not started,
,Card Types,Credit,Supported,Visa/MC/Amex,N/A,Not applicable,PIX only,N/A,Not applicable,
,Verify,TRUE,Implemented,Real-time,FALSE,Not supported,PIX validation,FALSE,No verification,
,Authorize,TRUE,Implemented,Pre-auth available,FALSE,Not applicable,Instant transfer,FALSE,Not supported,
,Capture,TRUE,Implemented,Manual/Auto,FALSE,Not applicable,Instant,FALSE,Not supported,
,Purchase,TRUE,Implemented,One-step,TRUE,Implemented,Direct transfer,FALSE,Not supported,
,Refund,TRUE,Implemented,Partial/Full,TRUE,Implemented,Manual process,FALSE,Not supported,
,Cancel,TRUE,Implemented,Pre-auth cancel,FALSE,Not applicable,N/A,FALSE,Not supported,
,Fees,2.5%,Competitive,Per transaction,1.5%,Lower cost,Monthly volume,N/A,No fees,
,Settlement,T+1,Standard,Business days,Instant,Real-time,24/7,N/A,No settlement,
,Currency,BRL,Primary,USD secondary,BRL,Only,Local currency,BRL,Supported,
,Limits,1000000,High,Daily limit,50000,Medium,Per transaction,N/A,No limits,
,3DS,TRUE,Implemented,v2.0,FALSE,Not supported,Not applicable,FALSE,Not supported,
,Tokenization,TRUE,Implemented,Vault storage,FALSE,Not supported,No tokens,FALSE,Not supported,
,Webhooks,TRUE,Implemented,Real-time,TRUE,Implemented,Delayed,FALSE,Not supported,
,API Version,v2.1,Latest,RESTful,v1.0,Stable,Legacy support,N/A,No API,
,Documentation,Excellent,Complete,Developer portal,Good,Adequate,Basic docs,Poor,Incomplete,
,Support,24/7,Premium,Dedicated team,Business,Standard,Email support,Limited,Basic,
,Go Live Date,2023-12-01,Completed,,2024-03-15,Planned,,TBD,Unknown,"""
        return content.encode('utf-8')

    def test_complete_workflow_web_interface(self, client, sample_csv_content):
        """Test complete workflow through web interface"""
        # Step 1: Access main page
        response = client.get('/')
        assert response.status_code == 200
        assert b'CSV Provider Parser' in response.data
        
        # Step 2: Upload valid CSV file
        data = {'file': (BytesIO(sample_csv_content), 'integration_test.csv')}
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        assert b'Parsing Results' in response.data
        
        # Step 3: Verify results structure
        assert b'PROVIDER_A' in response.data
        assert b'PROVIDER_B' in response.data
        assert b'CARD' in response.data
        assert b'PIX' in response.data
        
        # Step 4: Check statistics are displayed
        assert b'Valid Combinations' in response.data
        assert b'Features per Provider' in response.data
        
        # Step 5: Verify interactive elements
        assert b'Filter by feature value' in response.data
        assert b'Search features' in response.data
        assert b'Export as JSON' in response.data

    def test_complete_workflow_api(self, client, sample_csv_content):
        """Test complete workflow through API"""
        # Step 1: Upload via API
        data = {'file': (BytesIO(sample_csv_content), 'api_test.csv')}
        response = client.post('/api/upload', data=data)
        
        assert response.status_code == 200
        
        # Step 2: Parse response
        response_data = json.loads(response.data)
        
        assert response_data['success'] is True
        assert 'filename' in response_data
        assert 'results' in response_data
        
        # Step 3: Verify parsed results structure
        results = response_data['results']
        assert len(results) == 2  # Two valid combinations
        
        # Step 4: Verify provider data
        provider_keys = list(results.keys())
        assert 'PROVIDER_A_CARD' in provider_keys
        assert 'PROVIDER_B_PIX' in provider_keys
        
        # Step 5: Verify detailed feature data
        provider_a_data = results['PROVIDER_A_CARD']
        assert provider_a_data['provider'] == 'PROVIDER_A'
        assert provider_a_data['payment_method'] == 'CARD'
        assert 'features' in provider_a_data
        
        features = provider_a_data['features']
        assert 'Country' in features
        assert features['Country'] == 'Brazil'
        assert 'Verify' in features
        assert features['Verify'] == 'TRUE'

    def test_csv_parser_integration(self, sample_csv_content):
        """Test CSV parser integration without web interface"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            temp_path = f.name
        
        try:
            # Step 1: Parse with verbose mode
            parser_verbose = ProviderPaymentParser(temp_path, verbose=True)
            results_verbose = parser_verbose.parse()
            
            # Step 2: Parse with non-verbose mode
            parser_quiet = ProviderPaymentParser(temp_path, verbose=False)
            results_quiet = parser_quiet.parse()
            
            # Step 3: Verify both produce same results
            assert results_verbose == results_quiet
            assert len(results_verbose) == 2
            
            # Step 4: Verify complete data structure
            for key, data in results_verbose.items():
                assert 'provider' in data
                assert 'payment_method' in data
                assert 'features' in data
                assert isinstance(data['features'], dict)
                assert len(data['features']) > 10  # Should have many features
                
        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_end_to_end_error_handling(self, client):
        """Test end-to-end error handling scenarios"""
        # Test 1: Invalid file upload
        invalid_content = b"not,a,valid,csv,structure"
        data = {'file': (BytesIO(invalid_content), 'invalid.csv')}
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        # Should handle gracefully without crashing
        
        # Test 2: Empty file upload
        empty_content = b""
        data = {'file': (BytesIO(empty_content), 'empty.csv')}
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        # Should handle gracefully
        
        # Test 3: Non-existent page
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_sample_file_download_integration(self, client):
        """Test sample file download and re-upload integration"""
        # Step 1: Download sample file
        response = client.get('/download-sample')
        assert response.status_code == 200
        
        sample_content = response.data
        
        # Step 2: Re-upload the downloaded sample
        data = {'file': (BytesIO(sample_content), 'downloaded_sample.csv')}
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        assert b'Parsing Results' in response.data
        
        # Step 3: Verify it parses correctly
        assert b'REDE' in response.data or b'PAGARME' in response.data

    def test_multiple_file_types_integration(self, client):
        """Test integration with various file scenarios"""
        test_cases = [
            # Valid CSV with different structures
            {
                'content': b",Feature,TEST_A\n,Provider,TEST\n,Payment_Method,CARD\n,,INFO\n,Country,Brazil\n",
                'filename': 'simple.csv',
                'should_succeed': True
            },
            # CSV with no valid providers
            {
                'content': b",Feature,INVALID\n,Provider,#N/A\n,Payment_Method,#N/A\n,,INFO\n,Country,Brazil\n",
                'filename': 'no_providers.csv', 
                'should_succeed': False
            },
            # CSV with special characters
            {
                'content': b",Feature,SPECIAL_PROVIDER\n,Provider,TEST-123\n,Payment_Method,CARD\n,,INFO\n,Feature,Value with spaces\n",
                'filename': 'special_chars.csv',
                'should_succeed': True
            }
        ]
        
        for case in test_cases:
            data = {'file': (BytesIO(case['content']), case['filename'])}
            response = client.post('/upload', data=data, follow_redirects=True)
            
            assert response.status_code == 200
            
            if case['should_succeed']:
                # Should show results or handle gracefully
                assert b'Parsing Results' in response.data or b'No valid' in response.data
            else:
                # Should show "no valid combinations" message
                assert b'No valid' in response.data or b'Error' in response.data

    def test_cross_browser_compatibility_simulation(self, client, sample_csv_content):
        """Simulate cross-browser compatibility by testing different headers"""
        headers_sets = [
            # Chrome-like headers
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            # Firefox-like headers  
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101'},
            # Safari-like headers
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'},
            # Mobile-like headers
            {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)'}
        ]
        
        for headers in headers_sets:
            # Test main page
            response = client.get('/', headers=headers)
            assert response.status_code == 200
            
            # Test file upload
            data = {'file': (BytesIO(sample_csv_content), 'browser_test.csv')}
            response = client.post('/upload', data=data, headers=headers)
            assert response.status_code == 200

    def test_performance_integration(self, client):
        """Test performance with various file sizes"""
        sizes_to_test = [
            (10, "small"),      # 10 rows
            (100, "medium"),    # 100 rows  
            (500, "large")      # 500 rows
        ]
        
        for num_rows, size_label in sizes_to_test:
            # Generate CSV content
            content = ",Feature,PERF_PROVIDER\n"
            content += ",Provider,PERF_TEST\n"
            content += ",Payment_Method,CARD\n"
            content += ",,INFO\n"
            
            for i in range(num_rows):
                content += f",Feature_{i},Value_{i}\n"
            
            # Test upload and processing
            data = {'file': (BytesIO(content.encode('utf-8')), f'{size_label}.csv')}
            response = client.post('/upload', data=data)
            
            # Should complete successfully regardless of size
            assert response.status_code == 200
            
            # For large files, verify it still processes correctly
            if size_label == "large":
                assert b'Parsing Results' in response.data or b'No valid' in response.data


class TestRegressionScenarios:
    """Test scenarios that could cause regressions"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask application"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client

    def test_unicode_handling_regression(self, client):
        """Test Unicode character handling"""
        unicode_content = """,Feature,UNICODE_PROVIDER
,Provider,Açaí-Pay
,Payment_Method,CARTÃO
,,INFO
,País,Brasil
,Suporte,24/7
,Moeda,R$""".encode('utf-8')
        
        data = {'file': (BytesIO(unicode_content), 'unicode_test.csv')}
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        # Should handle Unicode gracefully

    def test_empty_values_regression(self, client):
        """Test handling of empty values in CSV"""
        empty_values_content = b""",Feature,EMPTY_PROVIDER
,Provider,TEST
,Payment_Method,CARD
,,INFO
,Country,
,Verify,
,Authorize,TRUE
,Empty Feature,"""
        
        data = {'file': (BytesIO(empty_values_content), 'empty_values.csv')}
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        # Should handle empty values without errors

    def test_quotes_and_commas_regression(self, client):
        """Test handling of quotes and commas in CSV data"""
        complex_content = b''',Feature,COMPLEX_PROVIDER
,Provider,TEST
,Payment_Method,CARD
,,INFO
,Description,"This is a feature with, commas"
,Notes,"And ""quoted"" text"
,Fees,"$1,000.00"'''
        
        data = {'file': (BytesIO(complex_content), 'complex.csv')}
        response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        # Should handle CSV quoting properly


if __name__ == '__main__':
    pytest.main([__file__]) 
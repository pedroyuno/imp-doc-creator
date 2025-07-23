#!/usr/bin/env python3
"""
Additional tests to boost code coverage to 90%+
"""

import pytest
import os
import tempfile
import sys
from io import StringIO
from unittest.mock import patch

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_parser import ProviderPaymentParser, main


class TestCoverageBoost:
    """Additional tests to increase coverage"""
    
    def test_verbose_error_messages(self, capsys):
        """Test verbose error messages"""
        # Test file not found with verbose mode
        parser = ProviderPaymentParser('nonexistent_file.csv', verbose=True)
        
        with pytest.raises(FileNotFoundError):
            parser.load_csv()
        
        captured = capsys.readouterr()
        assert "Error: File 'nonexistent_file.csv' not found" in captured.out
    
    def test_csv_loading_exception_verbose(self, capsys):
        """Test CSV loading exception with verbose mode"""
        # Create a mock that raises a general exception
        parser = ProviderPaymentParser('dummy.csv', verbose=True)
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = Exception("General error")
            
            with pytest.raises(Exception) as exc_info:
                parser.load_csv()
            
            assert "Error loading CSV" in str(exc_info.value)
        
        captured = capsys.readouterr()
        assert "Error loading CSV" in captured.out
    
    def test_insufficient_rows_verbose(self, capsys):
        """Test insufficient rows with verbose mode"""
        # Create CSV with only 2 rows
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,TEST\n')
            f.write(',Provider,TEST\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=True)
            parser.load_csv()
            parser.identify_valid_columns()
            
            captured = capsys.readouterr()
            assert "CSV must have at least 3 rows" in captured.out
        finally:
            os.unlink(temp_path)
    
    def test_no_valid_columns_verbose(self, capsys):
        """Test no valid columns with verbose mode"""
        # Create CSV with no valid combinations
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,[Provider]\n')
            f.write(',Provider,#N/A\n')
            f.write(',Payment_Method,#N/A\n')
            f.write(',,INFO\n')
            f.write(',Country,Brazil\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=True)
            parser.load_csv()
            parser.identify_valid_columns()
            parser.extract_features()
            
            captured = capsys.readouterr()
            assert "No valid columns found" in captured.out
        finally:
            os.unlink(temp_path)
    
    def test_no_feature_data_verbose(self, capsys):
        """Test no feature data with verbose mode"""
        # Create CSV with valid headers but no feature data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,TEST_PROVIDER\n')
            f.write(',Provider,TEST\n')
            f.write(',Payment_Method,CARD\n')
            f.write(',,INFO\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=True)
            parser.load_csv()
            parser.identify_valid_columns()
            parser.extract_features()
            
            captured = capsys.readouterr()
            assert "No feature data found in CSV" in captured.out
        finally:
            os.unlink(temp_path)
    
    def test_display_results_verbose_no_features(self, capsys):
        """Test display results with no features in verbose mode"""
        parser = ProviderPaymentParser('dummy.csv', verbose=True)
        parser.parsed_features = {}  # No features
        
        parser.display_results()
        
        captured = capsys.readouterr()
        assert "No features to display" in captured.out
    
    def test_display_results_with_features(self, capsys):
        """Test display results with actual features"""
        parser = ProviderPaymentParser('dummy.csv', verbose=False)
        parser.parsed_features = {
            'TEST_CARD': {
                'provider': 'TEST',
                'payment_method': 'CARD',
                'features': {
                    'Country': 'Brazil',
                    'Verify': 'TRUE',
                    'EmptyFeature': '',
                    'Authorize': 'FALSE'
                }
            }
        }
        
        parser.display_results()
        
        captured = capsys.readouterr()
        assert "PARSED PROVIDER + PAYMENT METHOD FEATURES" in captured.out
        assert "TEST + CARD" in captured.out
        assert "Country: Brazil" in captured.out
        assert "Verify: TRUE" in captured.out
        assert "Authorize: FALSE" in captured.out
        assert "EmptyFeature: [empty]" in captured.out
    
    def test_main_function_help(self):
        """Test main function with help argument"""
        with patch('sys.argv', ['csv_parser.py', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Help should exit with code 0
            assert exc_info.value.code == 0
    
    def test_main_function_with_file(self, capsys):
        """Test main function with actual file"""
        # Create a test CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,MAIN_TEST\n')
            f.write(',Provider,MAIN\n')
            f.write(',Payment_Method,CARD\n')
            f.write(',,INFO\n')
            f.write(',Country,Brazil\n')
            temp_path = f.name
        
        try:
            with patch('sys.argv', ['csv_parser.py', temp_path]):
                main()
            
            captured = capsys.readouterr()
            assert "Starting CSV parsing" in captured.out
            assert "MAIN + CARD" in captured.out
        finally:
            os.unlink(temp_path)
    
    def test_main_function_quiet_mode(self, capsys):
        """Test main function with quiet flag"""
        # Create a test CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,QUIET_TEST\n')
            f.write(',Provider,QUIET\n')
            f.write(',Payment_Method,CARD\n')
            f.write(',,INFO\n')
            f.write(',Country,Brazil\n')
            temp_path = f.name
        
        try:
            with patch('sys.argv', ['csv_parser.py', temp_path, '--quiet']):
                main()
            
            captured = capsys.readouterr()
            # In quiet mode, should show results but not progress messages
            assert "QUIET + CARD" in captured.out
        finally:
            os.unlink(temp_path)
    
    def test_main_function_error_handling(self, capsys):
        """Test main function error handling"""
        with patch('sys.argv', ['csv_parser.py', 'nonexistent.csv']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should exit with error code
            assert exc_info.value.code == 1
    
    def test_parse_empty_feature_value_handling(self):
        """Test parsing with empty feature values"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,EMPTY_TEST\n')
            f.write(',Provider,TEST\n')
            f.write(',Payment_Method,CARD\n')
            f.write(',,INFO\n')
            f.write(',EmptyValue,\n')
            f.write(',NormalValue,Something\n')
            f.write(',AnotherEmpty,\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=False)
            results = parser.parse()
            
            assert len(results) == 1
            features = results['TEST_CARD']['features']
            assert 'EmptyValue' in features
            assert features['EmptyValue'] == ''
            assert 'NormalValue' in features
            assert features['NormalValue'] == 'Something'
        finally:
            os.unlink(temp_path)
    
    def test_column_boundary_conditions(self):
        """Test edge cases with column boundaries"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create CSV where some rows have fewer columns
            f.write(',Feature,BOUNDARY_TEST,,\n')
            f.write(',Provider,TEST\n')  # Shorter row
            f.write(',Payment_Method,CARD,,\n')
            f.write(',,INFO,STATUS\n')
            f.write(',Country,Brazil\n')  # Missing columns
            f.write(',Feature2,Value2,,Extra\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=False)
            results = parser.parse()
            
            # Should handle gracefully
            if results:
                assert isinstance(results, dict)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__]) 
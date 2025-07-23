#!/usr/bin/env python3
"""
Comprehensive unit tests for CSV Parser functionality
"""

import pytest
import os
import tempfile
import sys
from io import StringIO
from unittest.mock import patch, mock_open

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_parser import ProviderPaymentParser


class TestProviderPaymentParser:
    """Test class for ProviderPaymentParser"""
    
    @pytest.fixture
    def valid_csv_path(self):
        """Fixture providing path to valid test CSV"""
        return os.path.join('tests', 'fixtures', 'valid_csv.csv')
    
    @pytest.fixture
    def invalid_csv_path(self):
        """Fixture providing path to invalid test CSV"""
        return os.path.join('tests', 'fixtures', 'invalid_csv.csv')
    
    @pytest.fixture
    def empty_csv_path(self):
        """Fixture providing path to empty test CSV"""
        return os.path.join('tests', 'fixtures', 'empty_csv.csv')
    
    @pytest.fixture
    def malformed_csv_path(self):
        """Fixture providing path to malformed test CSV"""
        return os.path.join('tests', 'fixtures', 'malformed_csv.csv')
    
    @pytest.fixture
    def temp_csv_file(self):
        """Fixture providing a temporary CSV file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,TEST_PROVIDER,,,\n')
            f.write(',Provider,TEST,,,\n')
            f.write(',Payment_Method,CARD,,,\n')
            f.write(',,INFO,STATUS,ADDITIONAL INFO\n')
            f.write(',Country,Brazil,Supported,\n')
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_parser_initialization_verbose(self):
        """Test parser initialization with verbose mode"""
        parser = ProviderPaymentParser('dummy.csv', verbose=True)
        assert parser.csv_file_path == 'dummy.csv'
        assert parser.verbose is True
        assert parser.data == []
        assert parser.valid_columns == []
        assert parser.parsed_features == {}

    def test_parser_initialization_non_verbose(self):
        """Test parser initialization with non-verbose mode"""
        parser = ProviderPaymentParser('dummy.csv', verbose=False)
        assert parser.csv_file_path == 'dummy.csv'
        assert parser.verbose is False

    def test_load_csv_success(self, valid_csv_path):
        """Test successful CSV loading"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=False)
        parser.load_csv()
        
        assert len(parser.data) > 0
        assert len(parser.data) == 10  # Based on our test fixture

    def test_load_csv_file_not_found(self):
        """Test CSV loading with non-existent file"""
        parser = ProviderPaymentParser('nonexistent.csv', verbose=False)
        
        with pytest.raises(FileNotFoundError):
            parser.load_csv()

    def test_load_csv_verbose_output(self, valid_csv_path, capsys):
        """Test verbose output during CSV loading"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=True)
        parser.load_csv()
        
        captured = capsys.readouterr()
        assert "Successfully loaded CSV" in captured.out

    def test_identify_valid_columns_success(self, valid_csv_path):
        """Test identification of valid columns"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=False)
        parser.load_csv()
        parser.identify_valid_columns()
        
        assert len(parser.valid_columns) == 2
        
        # Check first valid column
        assert parser.valid_columns[0]['provider'] == 'REDE'
        assert parser.valid_columns[0]['payment_method'] == 'CARD'
        assert parser.valid_columns[0]['column_index'] == 2
        
        # Check second valid column
        assert parser.valid_columns[1]['provider'] == 'PAGARME'
        assert parser.valid_columns[1]['payment_method'] == 'CARD'
        assert parser.valid_columns[1]['column_index'] == 5

    def test_identify_valid_columns_no_valid(self, invalid_csv_path):
        """Test identification when no valid columns exist"""
        parser = ProviderPaymentParser(invalid_csv_path, verbose=False)
        parser.load_csv()
        parser.identify_valid_columns()
        
        assert len(parser.valid_columns) == 0

    def test_identify_valid_columns_insufficient_rows(self):
        """Test identification with insufficient rows"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,TEST\n')
            f.write(',Provider,TEST\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=False)
            parser.load_csv()
            parser.identify_valid_columns()
            
            assert len(parser.valid_columns) == 0
        finally:
            os.unlink(temp_path)

    def test_identify_valid_columns_verbose_output(self, valid_csv_path, capsys):
        """Test verbose output during column identification"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=True)
        parser.load_csv()
        parser.identify_valid_columns()
        
        captured = capsys.readouterr()
        assert "Found 2 valid provider + payment method combinations" in captured.out
        assert "REDE" in captured.out
        assert "PAGARME" in captured.out

    def test_extract_features_success(self, valid_csv_path):
        """Test successful feature extraction"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=False)
        parser.load_csv()
        parser.identify_valid_columns()
        parser.extract_features()
        
        assert len(parser.parsed_features) == 2
        
        # Check REDE features
        rede_key = 'REDE_CARD'
        assert rede_key in parser.parsed_features
        assert parser.parsed_features[rede_key]['provider'] == 'REDE'
        assert parser.parsed_features[rede_key]['payment_method'] == 'CARD'
        assert 'features' in parser.parsed_features[rede_key]
        
        # Check that features are extracted
        features = parser.parsed_features[rede_key]['features']
        assert 'Country' in features
        assert features['Country'] == 'Brazil'
        assert 'Verify' in features
        assert features['Verify'] == 'TRUE'

    def test_extract_features_no_valid_columns(self, invalid_csv_path):
        """Test feature extraction with no valid columns"""
        parser = ProviderPaymentParser(invalid_csv_path, verbose=False)
        parser.load_csv()
        parser.identify_valid_columns()
        parser.extract_features()
        
        assert len(parser.parsed_features) == 0

    def test_extract_features_no_feature_data(self):
        """Test feature extraction with no feature data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,TEST_PROVIDER\n')
            f.write(',Provider,TEST\n')
            f.write(',Payment_Method,CARD\n')
            f.write(',,INFO\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=False)
            parser.load_csv()
            parser.identify_valid_columns()
            parser.extract_features()
            
            assert len(parser.parsed_features) == 0
        finally:
            os.unlink(temp_path)

    def test_extract_features_verbose_output(self, valid_csv_path, capsys):
        """Test verbose output during feature extraction"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=True)
        parser.load_csv()
        parser.identify_valid_columns()
        parser.extract_features()
        
        captured = capsys.readouterr()
        assert "Extracted features for 2 valid combinations" in captured.out

    def test_display_results_success(self, valid_csv_path, capsys):
        """Test display results functionality"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=False)
        parser.load_csv()
        parser.identify_valid_columns()
        parser.extract_features()
        parser.display_results()
        
        captured = capsys.readouterr()
        assert "PARSED PROVIDER + PAYMENT METHOD FEATURES" in captured.out
        assert "REDE + CARD" in captured.out
        assert "PAGARME + CARD" in captured.out
        assert "Country: Brazil" in captured.out

    def test_display_results_no_features(self, invalid_csv_path):
        """Test display results with no features"""
        parser = ProviderPaymentParser(invalid_csv_path, verbose=False)
        parser.load_csv()
        parser.identify_valid_columns()
        parser.extract_features()
        
        # Should not raise exception
        parser.display_results()

    def test_export_to_dict(self, valid_csv_path):
        """Test export to dictionary functionality"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=False)
        parser.load_csv()
        parser.identify_valid_columns()
        parser.extract_features()
        
        result = parser.export_to_dict()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert 'REDE_CARD' in result
        assert 'PAGARME_CARD' in result

    def test_parse_method_complete_workflow(self, valid_csv_path):
        """Test the complete parse method workflow"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=False)
        result = parser.parse()
        
        assert isinstance(result, dict)
        assert len(result) == 2
        
        # Verify structure of returned data
        for key, data in result.items():
            assert 'provider' in data
            assert 'payment_method' in data
            assert 'features' in data
            assert isinstance(data['features'], dict)

    def test_parse_method_verbose_output(self, valid_csv_path, capsys):
        """Test verbose output during parse method"""
        parser = ProviderPaymentParser(valid_csv_path, verbose=True)
        result = parser.parse()
        
        captured = capsys.readouterr()
        assert "Starting CSV parsing" in captured.out

    def test_parse_method_with_empty_file(self, empty_csv_path):
        """Test parse method with empty CSV file"""
        parser = ProviderPaymentParser(empty_csv_path, verbose=False)
        result = parser.parse()
        
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_edge_case_missing_column_data(self, temp_csv_file):
        """Test handling of missing column data"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False)
        result = parser.parse()
        
        # Should handle gracefully
        assert isinstance(result, dict)

    def test_edge_case_empty_feature_names(self):
        """Test handling of empty feature names"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,TEST_PROVIDER\n')
            f.write(',Provider,TEST\n')
            f.write(',Payment_Method,CARD\n')
            f.write(',,INFO\n')
            f.write(',Country,Brazil\n')
            f.write(',,\n')  # Empty feature name
            f.write(',Verify,TRUE\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=False)
            result = parser.parse()
            
            # Should skip empty feature names
            if result:
                features = list(result.values())[0]['features']
                assert 'Country' in features
                assert 'Verify' in features
                assert '' not in features  # Empty string should be skipped
        finally:
            os.unlink(temp_path)

    def test_special_characters_in_data(self):
        """Test handling of special characters in CSV data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,SPECIAL_PROVIDER\n')
            f.write(',Provider,TEST-PROVIDER\n')
            f.write(',Payment_Method,CARD\n')
            f.write(',,INFO\n')
            f.write(',Special Feature,Value with "quotes"\n')
            f.write(',Unicode Feature,Cação\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=False)
            result = parser.parse()
            
            if result:
                features = list(result.values())[0]['features']
                assert 'Special Feature' in features
                assert 'Unicode Feature' in features
        finally:
            os.unlink(temp_path)

    def test_filter_header_columns(self):
        """Test filtering of generic header columns"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(',Feature,Provider,,,REAL_PROVIDER\n')
            f.write(',Provider,Provider,,,REAL\n')
            f.write(',Payment_Method,Payment_Method,,,CARD\n')
            f.write(',,INFO,STATUS,ADDITIONAL INFO,INFO\n')
            f.write(',Country,Brazil,,,Brazil\n')
            temp_path = f.name
        
        try:
            parser = ProviderPaymentParser(temp_path, verbose=False)
            parser.load_csv()
            parser.identify_valid_columns()
            
            # Should only find the REAL_PROVIDER column, not the generic "Provider" column
            assert len(parser.valid_columns) == 1
            assert parser.valid_columns[0]['provider'] == 'REAL'
            assert parser.valid_columns[0]['payment_method'] == 'CARD'
        finally:
            os.unlink(temp_path)


class TestCSVParserErrorHandling:
    """Test error handling scenarios"""
    
    def test_file_permission_error(self):
        """Test handling of file permission errors"""
        # Create a mock that raises PermissionError
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")
            
            parser = ProviderPaymentParser('protected.csv', verbose=False)
            
            with pytest.raises(Exception) as exc_info:
                parser.load_csv()
            
            assert "Error loading CSV" in str(exc_info.value)

    def test_csv_read_error(self):
        """Test handling of CSV reading errors"""
        # Test with a file that causes CSV reader issues
        with patch('csv.reader') as mock_reader:
            mock_reader.side_effect = Exception("CSV read error")
            
            parser = ProviderPaymentParser('dummy.csv', verbose=False)
            
            with pytest.raises(Exception):
                parser.load_csv()


if __name__ == '__main__':
    pytest.main([__file__]) 
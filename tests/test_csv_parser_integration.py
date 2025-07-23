#!/usr/bin/env python3
"""
Integration tests for CSV Parser with Rules Manager
"""

import pytest
import os
import tempfile
import json
import sys

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_parser import ProviderPaymentParser


class TestCSVParserRulesIntegration:
    """Test class for CSV Parser + Rules Manager integration"""
    
    @pytest.fixture
    def sample_csv_content(self):
        """Fixture providing sample CSV content"""
        return """,Feature,REDE_CARD,,,PAGARME_CARD,,,
,Provider,REDE,,,PAGARME,,,
,Payment_Method,CARD,,,CARD,,,
,,INFORMATION,STATUS,ADDITIONAL INFO,INFORMATION,STATUS,ADDITIONAL INFO
,Country,Brazil,Supported,,Brazil,Supported,
,Verify,TRUE,Implemented,,FALSE,Not supported,
,Authorize,TRUE,Implemented,,TRUE,Implemented,
,Capture,FALSE,Not available,,TRUE,Implemented,
,Cancel,TRUE,Implemented,,FALSE,Not supported,
,Refund,TRUE,Implemented,,TRUE,Implemented,"""

    @pytest.fixture
    def sample_rules_data(self):
        """Fixture providing sample rules data"""
        return {
            "version": "1.0",
            "rules": {
                "Country": {
                    "feature_name": "Country",
                    "documentation_url": "https://docs.example.com/country",
                    "comment": "Country support for payment processing"
                },
                "Verify": {
                    "feature_name": "Verify",
                    "documentation_url": "https://docs.example.com/verify",
                    "comment": "Payment verification capabilities"
                },
                "Authorize": {
                    "feature_name": "Authorize",
                    "documentation_url": "https://docs.example.com/authorize",
                    "comment": "Payment authorization functionality"
                },
                "UnknownFeature": {
                    "feature_name": "UnknownFeature",
                    "documentation_url": "https://docs.example.com/unknown",
                    "comment": "This feature is not in the CSV"
                }
            }
        }

    @pytest.fixture
    def temp_csv_file(self, sample_csv_content):
        """Fixture providing a temporary CSV file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_rules_file(self, sample_rules_data):
        """Fixture providing a temporary rules file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_rules_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_parser_with_rules_file(self, temp_csv_file, temp_rules_file):
        """Test parser initialization with custom rules file"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        
        # Check that rules manager is initialized
        assert parser.rules_manager is not None
        assert len(parser.rules_manager.rules) == 4
        assert parser.rules_manager.has_rule('Country')
        assert parser.rules_manager.has_rule('Verify')

    def test_parser_without_rules_file(self, temp_csv_file):
        """Test parser with non-existent rules file"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path='nonexistent.json')
        
        # Should still work, just with empty rules
        assert parser.rules_manager is not None
        assert len(parser.rules_manager.rules) == 0

    def test_basic_parsing_with_rules(self, temp_csv_file, temp_rules_file):
        """Test basic CSV parsing with rules integration"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        results = parser.parse()
        
        # Should parse normally
        assert len(results) == 2
        assert 'REDE_CARD' in results
        assert 'PAGARME_CARD' in results
        
        # Check that basic features are parsed
        rede_features = results['REDE_CARD']['features']
        assert 'Country' in rede_features
        assert 'Verify' in rede_features
        assert rede_features['Country'] == 'Brazil'
        assert rede_features['Verify'] == 'TRUE'

    def test_export_enriched_dict(self, temp_csv_file, temp_rules_file):
        """Test export_enriched_dict functionality"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        parser.parse()
        
        enriched_data = parser.export_enriched_dict()
        
        # Check structure
        assert len(enriched_data) == 2
        assert 'REDE_CARD' in enriched_data
        assert 'PAGARME_CARD' in enriched_data
        
        # Check enriched feature data for REDE
        rede_data = enriched_data['REDE_CARD']
        assert rede_data['provider'] == 'REDE'
        assert rede_data['payment_method'] == 'CARD'
        assert 'features' in rede_data
        
        # Check individual enriched features
        country_feature = rede_data['features']['Country']
        assert country_feature['name'] == 'Country'
        assert country_feature['value'] == 'Brazil'
        assert country_feature['has_value'] is True
        assert country_feature['has_rule'] is True
        assert country_feature['documentation_url'] == 'https://docs.example.com/country'
        assert country_feature['comment'] == 'Country support for payment processing'

    def test_enriched_features_with_and_without_rules(self, temp_csv_file, temp_rules_file):
        """Test that some features have rules and some don't"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        parser.parse()
        
        enriched_data = parser.export_enriched_dict()
        rede_features = enriched_data['REDE_CARD']['features']
        
        # Features with rules
        country_feature = rede_features['Country']
        assert country_feature['has_rule'] is True
        assert country_feature['documentation_url'] is not None
        assert country_feature['comment'] is not None
        
        verify_feature = rede_features['Verify']
        assert verify_feature['has_rule'] is True
        
        # Features without rules (like Capture, Cancel, Refund)
        if 'Capture' in rede_features:
            capture_feature = rede_features['Capture']
            assert capture_feature['has_rule'] is False
            assert capture_feature['documentation_url'] is None
            assert capture_feature['comment'] is None

    def test_enriched_empty_values(self, temp_csv_file, temp_rules_file):
        """Test enriched data with empty feature values"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        parser.parse()
        
        enriched_data = parser.export_enriched_dict()
        
        # Find a feature with empty value
        for provider_key, provider_data in enriched_data.items():
            for feature_name, feature_data in provider_data['features'].items():
                if not feature_data['value']:  # Empty value
                    assert feature_data['has_value'] is False
                    # Should still have rule information if rule exists
                    if feature_data['has_rule']:
                        assert feature_data['documentation_url'] is not None
                        assert feature_data['comment'] is not None

    def test_display_results_enriched_mode(self, temp_csv_file, temp_rules_file, capsys):
        """Test display results in enriched mode"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        parser.parse()
        
        # Test enriched display
        parser.display_results(show_enriched=True)
        
        captured = capsys.readouterr()
        assert "PARSED PROVIDER + PAYMENT METHOD FEATURES (with Documentation)" in captured.out
        assert "📚 Documentation:" in captured.out
        assert "💬 Comment:" in captured.out
        assert "https://docs.example.com/country" in captured.out

    def test_display_results_normal_mode(self, temp_csv_file, temp_rules_file, capsys):
        """Test display results in normal mode"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        parser.parse()
        
        # Test normal display
        parser.display_results(show_enriched=False)
        
        captured = capsys.readouterr()
        assert "PARSED PROVIDER + PAYMENT METHOD FEATURES" in captured.out
        assert "(with Documentation)" not in captured.out
        assert "📚 Documentation:" not in captured.out
        assert "💬 Comment:" not in captured.out

    def test_command_line_enriched_flag(self, temp_csv_file, temp_rules_file):
        """Test command line interface with enriched flag"""
        import subprocess
        import sys
        
        # Test with enriched flag
        result = subprocess.run([
            sys.executable, 'csv_parser.py',
            temp_csv_file,
            '--enriched',
            '--rules-file', temp_rules_file,
            '--quiet'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        assert result.returncode == 0
        assert "📚" in result.stdout  # Should show documentation links
        assert "https://docs.example.com" in result.stdout

    def test_command_line_custom_rules_file(self, temp_csv_file, temp_rules_file):
        """Test command line interface with custom rules file"""
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, 'csv_parser.py',
            temp_csv_file,
            '--rules-file', temp_rules_file,
            '--quiet'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        assert result.returncode == 0
        # Should parse successfully even with custom rules file

    def test_rules_manager_integration_with_verbose(self, temp_csv_file, temp_rules_file, capsys):
        """Test rules manager integration with verbose output"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=True, rules_file_path=temp_rules_file)
        parser.parse()
        
        captured = capsys.readouterr()
        assert "Successfully loaded" in captured.out
        assert "feature rules" in captured.out

    def test_enriched_data_completeness(self, temp_csv_file, temp_rules_file):
        """Test that enriched data contains all expected fields"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        parser.parse()
        
        enriched_data = parser.export_enriched_dict()
        
        for provider_key, provider_data in enriched_data.items():
            for feature_name, feature_data in provider_data['features'].items():
                # Check all required enriched fields are present
                required_fields = ['name', 'value', 'has_value', 'documentation_url', 'comment', 'has_rule']
                for field in required_fields:
                    assert field in feature_data, f"Missing field '{field}' in feature '{feature_name}'"

    def test_rules_not_affecting_basic_parsing(self, temp_csv_file, temp_rules_file):
        """Test that rules don't affect basic parsing functionality"""
        # Parse without rules
        parser_no_rules = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path='nonexistent.json')
        results_no_rules = parser_no_rules.parse()
        
        # Parse with rules
        parser_with_rules = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        results_with_rules = parser_with_rules.parse()
        
        # Basic parsing results should be identical
        assert len(results_no_rules) == len(results_with_rules)
        
        for key in results_no_rules:
            assert key in results_with_rules
            assert results_no_rules[key]['provider'] == results_with_rules[key]['provider']
            assert results_no_rules[key]['payment_method'] == results_with_rules[key]['payment_method']
            assert results_no_rules[key]['features'] == results_with_rules[key]['features']

    def test_multiple_providers_enrichment(self, temp_csv_file, temp_rules_file):
        """Test enrichment works correctly for multiple providers"""
        parser = ProviderPaymentParser(temp_csv_file, verbose=False, rules_file_path=temp_rules_file)
        parser.parse()
        
        enriched_data = parser.export_enriched_dict()
        
        # Both providers should have enriched data
        assert 'REDE_CARD' in enriched_data
        assert 'PAGARME_CARD' in enriched_data
        
        # Both should have Country feature with enrichment
        rede_country = enriched_data['REDE_CARD']['features']['Country']
        pagarme_country = enriched_data['PAGARME_CARD']['features']['Country']
        
        assert rede_country['has_rule'] is True
        assert pagarme_country['has_rule'] is True
        assert rede_country['documentation_url'] == pagarme_country['documentation_url']
        assert rede_country['comment'] == pagarme_country['comment']
        
        # But values should be different based on CSV content
        assert rede_country['value'] == 'Brazil'
        assert pagarme_country['value'] == 'Brazil' 
#!/usr/bin/env python3
"""
Comprehensive unit tests for Rules Manager functionality
"""

import pytest
import os
import tempfile
import json
import sys
from unittest.mock import patch, mock_open

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rules_manager import RulesManager, FeatureRule


class TestFeatureRule:
    """Test class for FeatureRule"""
    
    def test_feature_rule_initialization(self):
        """Test FeatureRule initialization"""
        rule = FeatureRule("TestFeature", "https://example.com/docs", "Test comment")
        
        assert rule.feature_name == "TestFeature"
        assert rule.documentation_url == "https://example.com/docs"
        assert rule.comment == "Test comment"
    
    def test_feature_rule_to_dict(self):
        """Test FeatureRule to_dict method"""
        rule = FeatureRule("TestFeature", "https://example.com/docs", "Test comment")
        result = rule.to_dict()
        
        expected = {
            'feature_name': "TestFeature",
            'documentation_url': "https://example.com/docs",
            'comment': "Test comment"
        }
        
        assert result == expected
    
    def test_feature_rule_repr(self):
        """Test FeatureRule string representation"""
        rule = FeatureRule("TestFeature", "https://example.com/docs/very/long/url/that/should/be/truncated", "Very long comment that should be truncated for display")
        repr_str = repr(rule)
        
        assert "TestFeature" in repr_str
        assert "FeatureRule" in repr_str
        assert len(repr_str) < 200  # Should be truncated


class TestRulesManager:
    """Test class for RulesManager"""
    
    @pytest.fixture
    def sample_rules_data(self):
        """Fixture providing sample rules data"""
        return {
            "version": "1.0",
            "description": "Test rules",
            "rules": {
                "Country": {
                    "feature_name": "Country",
                    "documentation_url": "https://docs.example.com/country",
                    "comment": "Country support information"
                },
                "Verify": {
                    "feature_name": "Verify",
                    "documentation_url": "https://docs.example.com/verify",
                    "comment": "Payment verification capability"
                }
            },
            "metadata": {
                "total_rules": 2
            }
        }
    
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
    
    @pytest.fixture
    def invalid_rules_file(self):
        """Fixture providing an invalid rules file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": "json structure"}')  # Missing 'rules' section
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_rules_manager_initialization(self):
        """Test RulesManager initialization"""
        manager = RulesManager('test.json', verbose=False)
        
        assert manager.rules_file_path == 'test.json'
        assert manager.verbose is False
        assert manager.rules == {}
        assert manager.metadata == {}
        assert manager.version == ""
        assert manager.last_loaded is None

    def test_load_rules_success(self, temp_rules_file):
        """Test successful rules loading"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        assert len(manager.rules) == 2
        assert 'Country' in manager.rules
        assert 'Verify' in manager.rules
        assert manager.version == "1.0"
        assert manager.last_loaded is not None
        
        # Check rule content
        country_rule = manager.rules['Country']
        assert country_rule.feature_name == "Country"
        assert country_rule.documentation_url == "https://docs.example.com/country"
        assert country_rule.comment == "Country support information"

    def test_load_rules_file_not_found(self):
        """Test loading rules when file doesn't exist"""
        manager = RulesManager('nonexistent.json', verbose=False)
        manager.load_rules()
        
        assert len(manager.rules) == 0
        assert manager.version == ""

    def test_load_rules_invalid_structure(self, invalid_rules_file):
        """Test loading rules with invalid file structure"""
        manager = RulesManager(invalid_rules_file, verbose=False)
        manager.load_rules()
        
        assert len(manager.rules) == 0

    def test_load_rules_invalid_json(self):
        """Test loading rules with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON syntax
            temp_path = f.name
        
        try:
            manager = RulesManager(temp_path, verbose=False)
            manager.load_rules()
            
            assert len(manager.rules) == 0
        finally:
            os.unlink(temp_path)

    def test_load_rules_verbose_output(self, temp_rules_file, capsys):
        """Test verbose output during rules loading"""
        manager = RulesManager(temp_rules_file, verbose=True)
        manager.load_rules()
        
        captured = capsys.readouterr()
        assert "Successfully loaded 2 feature rules" in captured.out
        assert "Version: 1.0" in captured.out

    def test_get_rule_exists(self, temp_rules_file):
        """Test getting an existing rule"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        rule = manager.get_rule('Country')
        assert rule is not None
        assert rule.feature_name == "Country"
        assert rule.documentation_url == "https://docs.example.com/country"

    def test_get_rule_not_exists(self, temp_rules_file):
        """Test getting a non-existing rule"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        rule = manager.get_rule('NonExistent')
        assert rule is None

    def test_get_documentation_url(self, temp_rules_file):
        """Test getting documentation URL"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        url = manager.get_documentation_url('Country')
        assert url == "https://docs.example.com/country"
        
        url = manager.get_documentation_url('NonExistent')
        assert url is None

    def test_get_comment(self, temp_rules_file):
        """Test getting comment"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        comment = manager.get_comment('Country')
        assert comment == "Country support information"
        
        comment = manager.get_comment('NonExistent')
        assert comment is None

    def test_has_rule(self, temp_rules_file):
        """Test checking if rule exists"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        assert manager.has_rule('Country') is True
        assert manager.has_rule('Verify') is True
        assert manager.has_rule('NonExistent') is False

    def test_get_all_features(self, temp_rules_file):
        """Test getting all feature names"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        features = manager.get_all_features()
        assert len(features) == 2
        assert 'Country' in features
        assert 'Verify' in features

    def test_get_rules_summary(self, temp_rules_file):
        """Test getting rules summary"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        summary = manager.get_rules_summary()
        assert summary['total_rules'] == 2
        assert summary['version'] == "1.0"
        assert summary['last_loaded'] is not None
        assert summary['rules_file'] == temp_rules_file

    def test_enrich_feature_data_with_rule(self, temp_rules_file):
        """Test enriching feature data when rule exists"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        enriched = manager.enrich_feature_data('Country', 'Brazil')
        
        assert enriched['name'] == 'Country'
        assert enriched['value'] == 'Brazil'
        assert enriched['has_value'] is True
        assert enriched['has_rule'] is True
        assert enriched['documentation_url'] == "https://docs.example.com/country"
        assert enriched['comment'] == "Country support information"

    def test_enrich_feature_data_without_rule(self, temp_rules_file):
        """Test enriching feature data when rule doesn't exist"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        enriched = manager.enrich_feature_data('UnknownFeature', 'SomeValue')
        
        assert enriched['name'] == 'UnknownFeature'
        assert enriched['value'] == 'SomeValue'
        assert enriched['has_value'] is True
        assert enriched['has_rule'] is False
        assert enriched['documentation_url'] is None
        assert enriched['comment'] is None

    def test_enrich_feature_data_empty_value(self, temp_rules_file):
        """Test enriching feature data with empty value"""
        manager = RulesManager(temp_rules_file, verbose=False)
        manager.load_rules()
        
        enriched = manager.enrich_feature_data('Country', '')
        
        assert enriched['has_value'] is False
        assert enriched['has_rule'] is True

    def test_reload_rules(self, temp_rules_file, capsys):
        """Test reloading rules"""
        manager = RulesManager(temp_rules_file, verbose=True)
        manager.load_rules()
        
        # Clear captured output
        capsys.readouterr()
        
        # Reload rules
        manager.reload_rules()
        
        captured = capsys.readouterr()
        assert "Reloading feature rules" in captured.out
        assert len(manager.rules) == 2

    def test_validate_rules_file_success(self, temp_rules_file):
        """Test validating a valid rules file"""
        manager = RulesManager(temp_rules_file, verbose=False)
        validation = manager.validate_rules_file()
        
        assert validation['is_valid'] is True
        assert len(validation['errors']) == 0
        assert validation['stats']['total_rules'] == 2
        assert validation['stats']['valid_rules'] == 2
        assert validation['stats']['invalid_rules'] == 0

    def test_validate_rules_file_not_found(self):
        """Test validating a non-existent rules file"""
        manager = RulesManager('nonexistent.json', verbose=False)
        validation = manager.validate_rules_file()
        
        assert validation['is_valid'] is False
        assert len(validation['errors']) > 0
        assert "does not exist" in validation['errors'][0]

    def test_validate_rules_file_invalid_structure(self, invalid_rules_file):
        """Test validating an invalid rules file structure"""
        manager = RulesManager(invalid_rules_file, verbose=False)
        validation = manager.validate_rules_file()
        
        assert validation['is_valid'] is False
        assert len(validation['errors']) > 0
        assert "Missing 'rules' section" in validation['errors'][0]

    def test_validate_rules_file_missing_fields(self):
        """Test validating rules with missing required fields"""
        rules_data = {
            "rules": {
                "InvalidRule": {
                    "feature_name": "InvalidRule",
                    # Missing documentation_url and comment
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(rules_data, f)
            temp_path = f.name
        
        try:
            manager = RulesManager(temp_path, verbose=False)
            validation = manager.validate_rules_file()
            
            assert validation['is_valid'] is False
            assert validation['stats']['invalid_rules'] == 1
            assert validation['stats']['valid_rules'] == 0
        finally:
            os.unlink(temp_path)

    def test_validate_rules_file_empty_fields(self):
        """Test validating rules with empty fields (warnings)"""
        rules_data = {
            "rules": {
                "EmptyRule": {
                    "feature_name": "EmptyRule",
                    "documentation_url": "",  # Empty field
                    "comment": "Valid comment"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(rules_data, f)
            temp_path = f.name
        
        try:
            manager = RulesManager(temp_path, verbose=False)
            validation = manager.validate_rules_file()
            
            # Empty fields generate warnings but still consider the file valid
            assert validation['is_valid'] is True
            assert len(validation['warnings']) > 0
            assert "empty fields" in validation['warnings'][0]
        finally:
            os.unlink(temp_path)

    def test_load_rules_with_invalid_rule_data(self):
        """Test loading rules with some invalid rule data"""
        rules_data = {
            "version": "1.0",
            "rules": {
                "ValidRule": {
                    "feature_name": "ValidRule",
                    "documentation_url": "https://example.com",
                    "comment": "Valid rule"
                },
                "InvalidRule": "not a dictionary",
                "IncompleteRule": {
                    "feature_name": "IncompleteRule"
                    # Missing required fields
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(rules_data, f)
            temp_path = f.name
        
        try:
            manager = RulesManager(temp_path, verbose=False)
            manager.load_rules()
            
            # Should only load the valid rule
            assert len(manager.rules) == 1
            assert 'ValidRule' in manager.rules
            assert 'InvalidRule' not in manager.rules
            assert 'IncompleteRule' not in manager.rules
        finally:
            os.unlink(temp_path)

    def test_load_rules_verbose_warnings(self):
        """Test verbose warnings during rule loading"""
        rules_data = {
            "rules": {
                "ValidRule": {
                    "feature_name": "ValidRule",
                    "documentation_url": "https://example.com",
                    "comment": "Valid rule"
                },
                "InvalidRule": "not a dictionary"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(rules_data, f)
            temp_path = f.name
        
        try:
            manager = RulesManager(temp_path, verbose=True)
            
            with patch('builtins.print') as mock_print:
                manager.load_rules()
                
                # Check that warning was printed
                print_calls = [call.args[0] for call in mock_print.call_args_list]
                warning_printed = any("Skipping invalid rule" in call for call in print_calls)
                assert warning_printed
        finally:
            os.unlink(temp_path) 
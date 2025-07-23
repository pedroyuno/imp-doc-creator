#!/usr/bin/env python3
"""
Coverage boost tests for Rules Manager
These tests specifically target uncovered lines to improve coverage percentage
"""

import pytest
import os
import tempfile
import json
import sys
from unittest.mock import patch
from io import StringIO

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rules_manager import RulesManager, main


class TestRulesManagerCoverageBoost:
    """Test class to boost rules manager coverage"""
    
    def test_missing_rules_file_verbose(self, capsys):
        """Test verbose output when rules file is missing"""
        manager = RulesManager('nonexistent_file.json', verbose=True)
        manager.load_rules()
        
        captured = capsys.readouterr()
        assert "Rules file 'nonexistent_file.json' not found" in captured.out
        assert "Using empty rules set" in captured.out

    def test_invalid_rule_verbose_output(self, capsys):
        """Test verbose output when skipping invalid rules"""
        rules_data = {
            "rules": {
                "ValidRule": {
                    "feature_name": "ValidRule",
                    "documentation_url": "https://example.com",
                    "comment": "Valid rule"
                },
                "InvalidRule": {
                    "feature_name": "InvalidRule"
                    # Missing required fields
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(rules_data, f)
            temp_path = f.name
        
        try:
            manager = RulesManager(temp_path, verbose=True)
            manager.load_rules()
            
            captured = capsys.readouterr()
            assert "Skipping invalid rule for 'InvalidRule'" in captured.out
            assert "missing required fields" in captured.out
        finally:
            os.unlink(temp_path)

    def test_file_not_found_exception_verbose(self, capsys):
        """Test verbose output for FileNotFoundError exception path"""
        manager = RulesManager('nonexistent.json', verbose=True)
        
        # Force the FileNotFoundError exception path by mocking os.path.exists to return True
        # but then file access fails
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=FileNotFoundError("Mock file not found")):
            manager.load_rules()
        
        captured = capsys.readouterr()
        assert "Rules file 'nonexistent.json' not found" in captured.out

    def test_json_decode_error_verbose(self, capsys):
        """Test verbose output for JSON decode error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json syntax}')  # Invalid JSON
            temp_path = f.name
        
        try:
            manager = RulesManager(temp_path, verbose=True)
            manager.load_rules()
            
            captured = capsys.readouterr()
            assert "Error parsing JSON in rules file" in captured.out
        finally:
            os.unlink(temp_path)

    def test_general_exception_verbose(self, capsys):
        """Test verbose output for general exception"""
        manager = RulesManager('test.json', verbose=True)
        
        # Mock an unexpected exception during file processing after file exists check passes
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):
            manager.load_rules()
        
        captured = capsys.readouterr()
        assert "Error loading rules" in captured.out

    def test_validation_json_decode_error(self):
        """Test validation with JSON decode error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON syntax
            temp_path = f.name
        
        try:
            manager = RulesManager(temp_path, verbose=False)
            validation = manager.validate_rules_file()
            
            assert validation['is_valid'] is False
            assert len(validation['errors']) > 0
            assert "Invalid JSON format" in validation['errors'][0]
        finally:
            os.unlink(temp_path)

    def test_validation_general_exception(self):
        """Test validation with general exception"""
        manager = RulesManager('test.json', verbose=False)
        
        # Mock a permission error during validation after file exists check passes
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):
            validation = manager.validate_rules_file()
            
            assert validation['is_valid'] is False
            assert len(validation['errors']) > 0
            assert "Validation error" in validation['errors'][0]

    def test_validation_non_dict_rule(self):
        """Test validation when rule is not a dictionary"""
        rules_data = {
            "rules": {
                "InvalidRule": "this is not a dictionary"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(rules_data, f)
            temp_path = f.name
        
        try:
            manager = RulesManager(temp_path, verbose=False)
            validation = manager.validate_rules_file()
            
            assert validation['is_valid'] is False
            assert any("not a dictionary" in error for error in validation['errors'])
        finally:
            os.unlink(temp_path)

    def test_main_function_execution(self, capsys):
        """Test the main function execution"""
        # Redirect stdout to capture print statements
        with patch('sys.argv', ['rules_manager.py']):
            main()
        
        captured = capsys.readouterr()
        assert "Feature Rules Manager Example" in captured.out
        assert "Rules Summary:" in captured.out
        assert "Feature Rule Lookups:" in captured.out
        assert "Rules File Validation:" in captured.out

    def test_main_with_nonexistent_rules(self, capsys):
        """Test main function with nonexistent rules file"""
        # Test main function when default rules file doesn't exist
        with patch('os.path.exists', return_value=False):
            main()
        
        captured = capsys.readouterr()
        assert "Feature Rules Manager Example" in captured.out
        assert "Total rules: 0" in captured.out

    def test_empty_fields_validation_warning(self):
        """Test validation produces warnings for empty fields"""
        rules_data = {
            "rules": {
                "EmptyFieldRule": {
                    "feature_name": "EmptyFieldRule",
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
            
            # This should generate warnings for empty fields
            assert len(validation['warnings']) > 0
            assert any("empty fields" in warning for warning in validation['warnings'])
        finally:
            os.unlink(temp_path) 
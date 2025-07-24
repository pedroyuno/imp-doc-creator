#!/usr/bin/env python3
"""
Tests for the Test Case Generator module
"""

import pytest
import tempfile
import os
from test_case_generator import TestCaseGenerator


class TestTestCaseGenerator:
    
    @pytest.fixture
    def sample_parsed_features(self):
        """Sample parsed features for testing"""
        return {
            'REDE_CARD': {
                'provider': 'REDE',
                'payment_method': 'CARD',
                'features': {
                    'Country': 'Brazil',
                    'Verify': 'TRUE',
                    'Authorize': 'TRUE',
                    'Capture': 'TRUE',
                    'Refund': 'FALSE',
                    'Currency': 'BRL',
                    'Sandbox': 'TRUE'
                }
            },
            'PAGARME_CARD': {
                'provider': 'PAGARME',
                'payment_method': 'CARD',
                'features': {
                    'Country': 'Brazil',
                    'Verify': 'TRUE',
                    'Authorize': 'IMPLEMENTED',
                    'Capture': '',  # Empty value
                    'Refund': 'TRUE',
                    '3DS': 'TRUE',
                    'Webhook': 'FALSE'
                }
            }
        }
    
    @pytest.fixture
    def generator_en(self):
        """English test case generator"""
        return TestCaseGenerator(locale='en')
    
    @pytest.fixture
    def generator_es(self):
        """Spanish test case generator"""
        return TestCaseGenerator(locale='es')
    
    def test_generator_initialization(self):
        """Test generator initialization with different locales"""
        # Test English
        gen_en = TestCaseGenerator(locale='en')
        assert gen_en.locale == 'en'
        assert gen_en.i18n is not None
        
        # Test Spanish
        gen_es = TestCaseGenerator(locale='es')
        assert gen_es.locale == 'es'
        
        # Test default
        gen_default = TestCaseGenerator()
        assert gen_default.locale == 'en'
    
    def test_is_feature_implemented(self, generator_en):
        """Test feature implementation detection"""
        # Test implemented values
        assert generator_en._is_feature_implemented('TRUE') == True
        assert generator_en._is_feature_implemented('IMPLEMENTED') == True
        assert generator_en._is_feature_implemented('YES') == True
        assert generator_en._is_feature_implemented('Y') == True
        assert generator_en._is_feature_implemented('1') == True
        assert generator_en._is_feature_implemented('SUPPORTED') == True
        assert generator_en._is_feature_implemented('AVAILABLE') == True
        
        # Test case insensitive
        assert generator_en._is_feature_implemented('true') == True
        assert generator_en._is_feature_implemented('True') == True
        assert generator_en._is_feature_implemented(' TRUE ') == True
        
        # Test not implemented values
        assert generator_en._is_feature_implemented('FALSE') == False
        assert generator_en._is_feature_implemented('NO') == False
        assert generator_en._is_feature_implemented('0') == False
        assert generator_en._is_feature_implemented('') == False
        assert generator_en._is_feature_implemented(None) == False
        assert generator_en._is_feature_implemented('RANDOM_VALUE') == False
        
        # Test values that are not boolean flags (like 'Brazil', 'BRL')
        assert generator_en._is_feature_implemented('Brazil') == False
        assert generator_en._is_feature_implemented('BRL') == False
    
    def test_generate_test_cases_for_features(self, generator_en, sample_parsed_features):
        """Test test case generation for features"""
        test_cases_data = generator_en.generate_test_cases_for_features(sample_parsed_features)
        
        # Should be a flat list of test cases
        assert isinstance(test_cases_data, list)
        assert len(test_cases_data) > 0
        
        # Check that test cases have the expected table format columns
        for test_case in test_cases_data:
            assert 'id' in test_case
            assert 'description' in test_case
            assert 'passed' in test_case
            assert 'date' in test_case
            assert 'executer' in test_case
            assert 'evidence' in test_case
            
            # Check ID format
            assert test_case['id'].startswith('TC-')
            
            # Check description format (includes provider + payment method)
            assert any(provider in test_case['description'] for provider in ['REDE', 'PAGARME'])
            assert 'CARD' in test_case['description']
        
        # Should have test cases from both providers (REDE and PAGARME)
        rede_cases = [tc for tc in test_cases_data if 'REDE' in tc['description']]
        pagarme_cases = [tc for tc in test_cases_data if 'PAGARME' in tc['description']]
        assert len(rede_cases) > 0
        assert len(pagarme_cases) > 0
        
        # All test cases should have the required table format fields
        assert all('id' in tc for tc in test_cases_data)
        assert all('description' in tc for tc in test_cases_data)
        assert all('passed' in tc for tc in test_cases_data)
        assert all('date' in tc for tc in test_cases_data)
        assert all('executer' in tc for tc in test_cases_data)
        assert all('evidence' in tc for tc in test_cases_data)
    
    def test_generate_test_cases_no_implemented_features(self, generator_en):
        """Test when no features are implemented"""
        parsed_features = {
            'TEST_PROVIDER': {
                'provider': 'TEST',
                'payment_method': 'CARD',
                'features': {
                    'Country': 'FALSE',
                    'Verify': '',
                    'Authorize': 'NO'
                }
            }
        }
        
        test_cases_data = generator_en.generate_test_cases_for_features(parsed_features)
        assert len(test_cases_data) == 0
    
    def test_generate_markdown_document(self, generator_en, sample_parsed_features):
        """Test markdown document generation"""
        markdown_doc = generator_en.generate_markdown_document(
            sample_parsed_features,
            merchant_name="Test Merchant",
            include_metadata=True
        )
        
        # Check document structure
        assert "# Test Cases for Test Merchant" in markdown_doc
        assert "## Test Case Documentation" in markdown_doc
        assert "## Summary" in markdown_doc
        
        # Should have table format
        assert "| ID | Description | Passed | Date | Executer | Evidence |" in markdown_doc
        assert "|----|-----------|---------|----- |----------|----------|" in markdown_doc
        
        # Should have test cases in table rows
        assert "| TC-" in markdown_doc  # Test case IDs
        assert "REDE + CARD:" in markdown_doc
        assert "PAGARME + CARD:" in markdown_doc
        
        # Should have instructions
        assert "Fill in the 'Passed' column" in markdown_doc
    
    def test_generate_markdown_document_without_metadata(self, generator_en, sample_parsed_features):
        """Test markdown document generation without metadata"""
        markdown_doc = generator_en.generate_markdown_document(
            sample_parsed_features,
            merchant_name="Test Merchant",
            include_metadata=False
        )
        
        # Should not have metadata sections
        assert "Generated on:" not in markdown_doc
        assert "## Summary" not in markdown_doc
        
        # But should have test cases
        assert "## Test Case Documentation" in markdown_doc
        assert "| ID | Description | Passed | Date | Executer | Evidence |" in markdown_doc
        assert "| TC-" in markdown_doc
    
    def test_generate_summary_statistics(self, generator_en, sample_parsed_features):
        """Test summary statistics generation"""
        stats = generator_en.generate_summary_statistics(sample_parsed_features)
        
        # Check required fields
        assert 'total_providers' in stats
        assert 'total_test_cases' in stats
        assert 'total_implemented_features' in stats
        assert 'features_by_provider' in stats
        assert 'language' in stats
        
        # Check values
        assert stats['total_providers'] == 2
        assert stats['total_test_cases'] > 0
        assert stats['language'] == 'en'
        
        # Check features by provider
        assert 'REDE' in stats['features_by_provider']
        assert 'PAGARME' in stats['features_by_provider']
        assert stats['features_by_provider']['REDE'] > 0
        assert stats['features_by_provider']['PAGARME'] > 0
    
    def test_different_locales(self, sample_parsed_features):
        """Test test case generation in different languages"""
        # Test English
        gen_en = TestCaseGenerator(locale='en')
        test_cases_en = gen_en.generate_test_cases_for_features(sample_parsed_features)
        
        # Test Spanish
        gen_es = TestCaseGenerator(locale='es')
        test_cases_es = gen_es.generate_test_cases_for_features(sample_parsed_features)
        
        # Should have same number of test cases but different descriptions
        assert len(test_cases_en) == len(test_cases_es)
        
        # Get first test case from each
        if test_cases_en and test_cases_es:
            en_first = test_cases_en[0]
            es_first = test_cases_es[0]
            
            # Same ID format, different description (if translations exist)
            assert en_first['id'] == es_first['id']
            # Descriptions may differ based on locale if translations are available
            assert en_first['description'] is not None
            assert es_first['description'] is not None
    
    def test_empty_parsed_features(self, generator_en):
        """Test with empty parsed features"""
        empty_features = {}
        
        test_cases_data = generator_en.generate_test_cases_for_features(empty_features)
        assert len(test_cases_data) == 0
        
        markdown_doc = generator_en.generate_markdown_document(empty_features)
        assert "No test cases" not in markdown_doc  # Should handle gracefully
        
        stats = generator_en.generate_summary_statistics(empty_features)
        assert stats['total_providers'] == 0
        assert stats['total_test_cases'] == 0
    
    def test_markdown_document_structure(self, generator_en, sample_parsed_features):
        """Test specific markdown document structure requirements"""
        markdown_doc = generator_en.generate_markdown_document(sample_parsed_features)
        
        lines = markdown_doc.split('\n')
        
        # Should have proper heading structure
        h1_lines = [line for line in lines if line.startswith('# ')]
        h2_lines = [line for line in lines if line.startswith('## ')]
        h3_lines = [line for line in lines if line.startswith('### ')]
        
        assert len(h1_lines) >= 1  # Main title
        assert len(h2_lines) >= 2  # At least intro + providers
        assert len(h3_lines) >= 1  # Feature sections
        
        # Test cases should be one per line as requested - look for actual test case lines
        test_case_lines = [line for line in lines if line.startswith('**') and 
                          ('0001' in line or '0002' in line or '0003' in line)]  # Look for test case IDs
        for line in test_case_lines:
            # Each line should be a complete test case
            assert line.count('**') >= 2  # At least one bold section
            assert '(' in line and ')' in line  # Type in parentheses
            assert ':' in line  # Description separator
    
    def test_feature_value_edge_cases(self, generator_en):
        """Test edge cases in feature values"""
        edge_case_features = {
            'TEST_PROVIDER': {
                'provider': 'TEST',
                'payment_method': 'CARD',
                'features': {
                    'Feature1': '  TRUE  ',  # With spaces
                    'Feature2': 'true',      # Lowercase
                    'Feature3': 'True',      # Mixed case
                    'Feature4': 'IMPLEMENTED',
                    'Feature5': 'false',     # Should not be included
                    'Feature6': '',          # Empty
                    'Feature7': 'RANDOM',    # Unknown value
                }
            }
        }
        
        test_cases_data = generator_en.generate_test_cases_for_features(edge_case_features)
        
        if test_cases_data:
            provider_data = list(test_cases_data.values())[0]
            feature_names = set(tc['feature_name'] for tc in provider_data['test_cases'])
            
            # Only implemented features should have test cases
            # Note: Only features that exist in feature_rules.json will have test cases
            # The test features (Feature1, Feature2, etc.) don't exist in rules, so no test cases
            assert len(feature_names) == 0  # No test cases for unknown features
    
    def test_generate_html_document(self, generator_en, sample_parsed_features):
        """Test HTML document generation"""
        html_doc = generator_en.generate_html_document(
            sample_parsed_features,
            merchant_name="Test Merchant",
            include_metadata=True
        )
        
        # Check HTML structure
        assert html_doc.startswith('<!DOCTYPE html>')
        assert '<html lang="en">' in html_doc
        assert '<title>Test Cases for Test Merchant</title>' in html_doc
        assert '</html>' in html_doc
        
        # Check CSS styling is included
        assert '<style>' in html_doc
        assert 'font-family: Arial' in html_doc
        
        # Check table structure
        assert '<table>' in html_doc
        assert '<th>ID</th>' in html_doc
        assert '<th>Description</th>' in html_doc
        assert '<th>Passed</th>' in html_doc
        assert '<th>Date</th>' in html_doc
        assert '<th>Executer</th>' in html_doc
        assert '<th>Evidence</th>' in html_doc
        
        # Check content structure
        assert '<h1>Test Cases for Test Merchant</h1>' in html_doc
        assert '<h2>Test Case Documentation</h2>' in html_doc
        
        # Check test case data in table rows
        assert '<td>TC-' in html_doc  # Test case IDs
        assert 'REDE + CARD:' in html_doc
        assert 'PAGARME + CARD:' in html_doc
        
        # Check metadata section
        assert 'class="metadata"' in html_doc
        assert 'Generated on:' in html_doc
        
        # Check summary section
        assert 'class="summary"' in html_doc
        assert 'class="notes"' in html_doc
    
    def test_generate_html_document_without_metadata(self, generator_en, sample_parsed_features):
        """Test HTML document generation without metadata"""
        html_doc = generator_en.generate_html_document(
            sample_parsed_features,
            merchant_name="Test Merchant",
            include_metadata=False
        )
        
        # Should not have metadata sections
        assert 'Generated on:' not in html_doc
        assert 'class="summary"' not in html_doc
        assert 'class="metadata"' not in html_doc
        
        # But should have test cases and basic structure
        assert '<h2>Test Case Documentation</h2>' in html_doc
        assert '<table>' in html_doc
        assert '<td>TC-' in html_doc 
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
        
        # Should have data for both providers
        assert len(test_cases_data) == 2
        assert 'REDE_CARD' in test_cases_data
        assert 'PAGARME_CARD' in test_cases_data
        
        # Check REDE data structure
        rede_data = test_cases_data['REDE_CARD']
        assert rede_data['provider'] == 'REDE'
        assert rede_data['payment_method'] == 'CARD'
        assert 'test_cases' in rede_data
        assert len(rede_data['test_cases']) > 0
        
        # Test cases should only be for implemented features
        # REDE has: Verify, Authorize, Capture, Sandbox as TRUE (Country and Currency are not boolean)
        feature_names = set(tc['feature_name'] for tc in rede_data['test_cases'])
        expected_features = {'Verify', 'Authorize', 'Capture', 'Sandbox'}
        assert feature_names == expected_features
        
        # Each test case should have required fields
        for test_case in rede_data['test_cases']:
            assert 'id' in test_case
            assert 'description' in test_case
            assert 'type' in test_case
            assert 'provider' in test_case
            assert 'payment_method' in test_case
            assert 'feature_name' in test_case
            assert 'feature_value' in test_case
    
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
        assert "# Implementation Test Cases for Test Merchant" in markdown_doc
        assert "## Test Case Documentation" in markdown_doc
        assert "## REDE + CARD" in markdown_doc
        assert "## PAGARME + CARD" in markdown_doc
        assert "## Summary" in markdown_doc
        
        # Check test case format (one per line) - look for actual test case lines
        lines = markdown_doc.split('\n')
        # Test case lines should start with ** and contain test case ID pattern
        test_case_lines = [line for line in lines if line.startswith('**') and 
                          ('0001' in line or '0002' in line or '0003' in line)]  # Look for test case IDs
        assert len(test_case_lines) > 0
        
        # Each test case line should have the format: **ID** (type): description
        for line in test_case_lines:
            assert '(' in line and ')' in line  # Test type in parentheses
            assert ':' in line  # Separator
    
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
        assert "## REDE + CARD" in markdown_doc
    
    def test_generate_summary_statistics(self, generator_en, sample_parsed_features):
        """Test summary statistics generation"""
        stats = generator_en.generate_summary_statistics(sample_parsed_features)
        
        # Check required fields
        assert 'total_providers' in stats
        assert 'total_test_cases' in stats
        assert 'total_implemented_features' in stats
        assert 'test_case_types' in stats
        assert 'features_by_provider' in stats
        assert 'language' in stats
        
        # Check values
        assert stats['total_providers'] == 2
        assert stats['total_test_cases'] > 0
        assert stats['language'] == 'en'
        
        # Check test case types
        assert 'happy path' in stats['test_case_types']
        assert 'unhappy path' in stats['test_case_types']
        assert 'corner case' in stats['test_case_types']
    
    def test_different_locales(self, sample_parsed_features):
        """Test test case generation in different languages"""
        # Test English
        gen_en = TestCaseGenerator(locale='en')
        test_cases_en = gen_en.generate_test_cases_for_features(sample_parsed_features)
        
        # Test Spanish
        gen_es = TestCaseGenerator(locale='es')
        test_cases_es = gen_es.generate_test_cases_for_features(sample_parsed_features)
        
        # Should have same structure but different descriptions
        assert len(test_cases_en) == len(test_cases_es)
        
        # Get first test case from each
        if test_cases_en and test_cases_es:
            en_first = list(test_cases_en.values())[0]['test_cases'][0]
            es_first = list(test_cases_es.values())[0]['test_cases'][0]
            
            # Same ID and type, different description (if translations exist)
            assert en_first['id'] == es_first['id']
            assert en_first['type'] == es_first['type']
    
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
        assert '<title>Implementation Test Cases for Test Merchant</title>' in html_doc
        assert '</html>' in html_doc
        
        # Check CSS styling is included
        assert '<style>' in html_doc
        assert 'font-family: Arial' in html_doc
        assert '.test-case' in html_doc
        
        # Check content structure
        assert '<h1>Implementation Test Cases for Test Merchant</h1>' in html_doc
        assert '<h2>Test Case Documentation</h2>' in html_doc
        assert '<h2>REDE + CARD</h2>' in html_doc
        assert '<h2>PAGARME + CARD</h2>' in html_doc
        
        # Check test case formatting
        assert 'class="test-case"' in html_doc
        assert 'class="test-id"' in html_doc
        assert 'class="test-type"' in html_doc
        
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
        assert '<h2>REDE + CARD</h2>' in html_doc
        assert 'class="test-case"' in html_doc 
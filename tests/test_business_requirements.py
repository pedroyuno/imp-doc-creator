#!/usr/bin/env python3
"""
Business Requirements Tests

This module tests business requirements and rules that must be met regardless
of technical implementation details. These tests focus on user expectations
and business logic rather than just code functionality.
"""

import pytest
import os
import sys
import tempfile
from io import BytesIO

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_case_generator import TestCaseGenerator
from csv_parser import ProviderPaymentParser
from i18n_helper import I18nHelper
from web_app import app


class TestMasterRulesBusinessRequirements:
    """Test business requirements related to master rules"""
    
    @pytest.fixture
    def generator_en(self):
        """Create English test case generator"""
        return TestCaseGenerator(locale='en')
    
    @pytest.fixture
    def client(self):
        """Create test client for web app"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client
    
    @pytest.mark.business_requirement
    def test_master_rules_always_included_regardless_of_features(self, generator_en):
        """
        BUSINESS REQUIREMENT: Master rules must appear in ALL generated documents
        regardless of which features are implemented or not implemented.
        """
        test_scenarios = [
            # Scenario 1: No features at all
            {},
            
            # Scenario 2: Features exist but none implemented
            {
                'PROVIDER_TEST': {
                    'provider': 'TEST',
                    'payment_method': 'CARD',
                    'features': {
                        'Feature1': 'FALSE',
                        'Feature2': '',
                        'Feature3': 'NO'
                    }
                }
            },
            
            # Scenario 3: Some features implemented
            {
                'PROVIDER_A': {
                    'provider': 'PROVID_A',
                    'payment_method': 'CARD',
                    'features': {
                        'Verify': 'TRUE',
                        'Authorize': 'FALSE'
                    }
                }
            },
            
            # Scenario 4: All features implemented
            {
                'PROVIDER_B': {
                    'provider': 'PROVIDER_B',
                    'payment_method': 'PIX',
                    'features': {
                        'Verify': 'TRUE',
                        'Purchase': 'IMPLEMENTED',
                        'Refund': 'YES'
                    }
                }
            }
        ]
        
        for i, scenario in enumerate(test_scenarios):
            # Test test case generation
            test_cases = generator_en.generate_test_cases_for_features(scenario)
            
            # Separate master from feature-specific test cases
            master_test_cases = [tc for tc in test_cases if tc['provider'] == 'All Providers']
            feature_test_cases = [tc for tc in test_cases if tc['provider'] != 'All Providers']
            
            # BUSINESS REQUIREMENT: Master test cases must ALWAYS be present
            assert len(master_test_cases) > 0, f"Scenario {i+1}: Master test cases missing"
            assert len(master_test_cases) == 5, f"Scenario {i+1}: Expected 5 master test cases, got {len(master_test_cases)}"
            
            # Verify master test case properties
            for master_case in master_test_cases:
                assert master_case['provider'] == 'All Providers', f"Scenario {i+1}: Invalid master case provider"
                assert master_case['payment_method'] == 'All Payment Methods', f"Scenario {i+1}: Invalid master case payment method"
                assert master_case['id'].startswith('MST'), f"Scenario {i+1}: Master case ID should start with MST"
                assert master_case['description'], f"Scenario {i+1}: Master case missing description"
            
            # Test integration steps generation
            integration_steps = generator_en.generate_integration_steps(scenario)
            
            # BUSINESS REQUIREMENT: Master integration steps must ALWAYS be first
            master_steps = [step for step in integration_steps if step['feature_name'] == 'Master Rules']
            assert len(master_steps) >= 3, f"Scenario {i+1}: Missing master integration steps"
            
            # BUSINESS REQUIREMENT: Master steps must appear FIRST
            if integration_steps:
                first_three_steps = integration_steps[:3]
                assert all(step['feature_name'] == 'Master Rules' for step in first_three_steps), \
                    f"Scenario {i+1}: Master rules must be the first integration steps"
    
    @pytest.mark.business_requirement
    def test_master_rules_content_requirements(self, generator_en):
        """
        BUSINESS REQUIREMENT: Master rules must contain specific essential content
        for security, authentication, and error handling.
        """
        # Test with minimal scenario
        minimal_scenario = {'TEST': {'provider': 'TEST', 'payment_method': 'TEST', 'features': {}}}
        
        # Get master test cases
        test_cases = generator_en.generate_test_cases_for_features(minimal_scenario)
        master_test_cases = [tc for tc in test_cases if tc['provider'] == 'All Providers']
        
        # BUSINESS REQUIREMENT: Must have authentication test case
        auth_cases = [tc for tc in master_test_cases if 'authentication' in tc['description'].lower()]
        assert len(auth_cases) > 0, "Must have authentication test case"
        
        # BUSINESS REQUIREMENT: Must have error handling test case
        error_cases = [tc for tc in master_test_cases if 'invalid' in tc['description'].lower() or 'error' in tc['description'].lower()]
        assert len(error_cases) > 0, "Must have error handling test case"
        
        # BUSINESS REQUIREMENT: Must have security test case
        security_cases = [tc for tc in master_test_cases if 'ssl' in tc['description'].lower() or 'security' in tc['description'].lower()]
        assert len(security_cases) > 0, "Must have security test case"
        
        # Get master integration steps
        integration_steps = generator_en.generate_integration_steps(minimal_scenario)
        master_steps = [step for step in integration_steps if step['feature_name'] == 'Master Rules']
        
        # BUSINESS REQUIREMENT: Must have getting started step
        getting_started = [step for step in master_steps if 'getting-started' in step['documentation_url']]
        assert len(getting_started) > 0, "Must have getting started integration step"
        
        # BUSINESS REQUIREMENT: Must have security step
        security_steps = [step for step in master_steps if 'security' in step['documentation_url']]
        assert len(security_steps) > 0, "Must have security integration step"
        
        # BUSINESS REQUIREMENT: Must have error handling step
        error_steps = [step for step in master_steps if 'error' in step['documentation_url']]
        assert len(error_steps) > 0, "Must have error handling integration step"
    
    @pytest.mark.business_requirement
    def test_document_generation_end_to_end_requirements(self, generator_en):
        """
        BUSINESS REQUIREMENT: All generated documents must contain master rules
        regardless of format (HTML, Markdown, DOCX).
        """
        # Test scenario with some implemented features
        scenario = {
            'TEST_PROVIDER': {
                'provider': 'TEST_PROVIDER',
                'payment_method': 'CARD',
                'features': {
                    'Verify': 'TRUE',
                    'Purchase': 'IMPLEMENTED'
                }
            }
        }
        
        # Test Markdown document generation
        markdown_doc = generator_en.generate_markdown_document(
            scenario, 
            merchant_name="Test Merchant",
            environment='both'
        )
        
        # BUSINESS REQUIREMENT: Markdown must contain master rules
        assert 'Master Rules' in markdown_doc, "Markdown document missing master rules section"
        assert 'MST0001' in markdown_doc, "Markdown document missing master test cases"
        assert 'getting-started' in markdown_doc, "Markdown document missing master integration steps"
        
        # Test HTML document generation
        html_doc = generator_en.generate_html_document(
            scenario,
            merchant_name="Test Merchant",
            environment='both'
        )
        
        # BUSINESS REQUIREMENT: HTML must contain master rules
        assert 'Master Rules' in html_doc, "HTML document missing master rules section"
        assert 'MST0001' in html_doc, "HTML document missing master test cases"
        assert 'All Providers' in html_doc, "HTML document missing master test case provider"
        
        # Test separated environment generation
        env_separated = generator_en.generate_environment_separated_test_cases(scenario)
        
        # BUSINESS REQUIREMENT: Both environments must have master rules
        sandbox_master = [tc for tc in env_separated['sandbox'] if tc['provider'] == 'All Providers']
        production_master = [tc for tc in env_separated['production'] if tc['provider'] == 'All Providers']
        
        assert len(sandbox_master) > 0, "Sandbox environment missing master test cases"
        assert len(production_master) > 0, "Production environment missing master test cases"


class TestBusinessRequirementCoverage:
    """Test that business requirements are properly covered"""
    
    @pytest.fixture
    def i18n_helper(self):
        """Create i18n helper for testing"""
        return I18nHelper()
    
    @pytest.mark.business_requirement
    def test_master_rules_data_integrity(self, i18n_helper):
        """
        BUSINESS REQUIREMENT: Master rules data must be complete and valid
        """
        # BUSINESS REQUIREMENT: Master rules must be loaded
        assert hasattr(i18n_helper, 'master_rules'), "i18n helper missing master_rules attribute"
        assert i18n_helper.master_rules, "Master rules data is empty"
        
        # BUSINESS REQUIREMENT: Master rules must have integration steps
        master_steps = i18n_helper.get_master_integration_steps()
        assert len(master_steps) >= 3, "Master rules must have at least 3 integration steps"
        
        for step in master_steps:
            assert 'documentation_url' in step, "Master integration step missing documentation URL"
            assert 'comment' in step, "Master integration step missing comment"
            assert step['documentation_url'].startswith('https://'), "Master integration step URL must be HTTPS"
            assert len(step['comment']) > 20, "Master integration step comment too short"
        
        # BUSINESS REQUIREMENT: Master rules must have test cases
        master_test_cases = i18n_helper.get_master_test_cases('en')
        assert len(master_test_cases) >= 5, "Master rules must have at least 5 test cases"
        
        for test_case in master_test_cases:
            assert 'id' in test_case, "Master test case missing ID"
            assert 'description' in test_case, "Master test case missing description"
            assert 'type' in test_case, "Master test case missing type"
            assert test_case['id'].startswith('MST'), "Master test case ID must start with MST"
            assert test_case['type'] in ['happy path', 'unhappy path', 'corner case'], "Invalid master test case type"
    
    @pytest.mark.business_requirement  
    def test_web_interface_master_rules_requirement(self, client):
        """
        BUSINESS REQUIREMENT: Web interface must generate documents with master rules
        """
        # Create sample parsed features data (simulating CSV upload result)
        parsed_features = {
            'TEST_PROVIDER_CARD': {
                'provider': 'TEST_PROVIDER',
                'payment_method': 'CARD',
                'features': {
                    'Verify': 'TRUE',
                    'Purchase': 'TRUE'
                }
            }
        }
        
        # Test the API endpoint for test case generation which should include master rules
        test_case_data = {
            'parsed_features': parsed_features,
            'merchant_name': 'Test Merchant',
            'environment': 'both',
            'output_format': 'html',
            'language': 'en'
        }
        
        # Generate test cases via API (this is where master rules should appear)
        response = client.post('/api/generate-test-cases',
                             json=test_case_data,
                             content_type='application/json')
        
        # BUSINESS REQUIREMENT: Test case generation must contain master rules
        assert response.status_code == 200, f"Test case generation failed: {response.status_code}"
        
        # Get the response data
        response_data = response.get_json()
        assert 'document_content' in response_data, "API response missing document_content"
        
        document_content = response_data['document_content']
        
        # Check for master rules in the generated document
        assert 'Master Rules' in document_content or 'MST0001' in document_content or 'All Providers' in document_content, \
            "Generated document missing master rules content"


class TestRequirementTraceability:
    """Test traceability from business requirements to implementation"""
    
    @pytest.mark.business_requirement
    def test_master_rules_requirement_traceability(self):
        """
        Verify that the master rules business requirement is properly implemented
        across all system components.
        """
        # Test 1: i18n_helper loads master rules
        i18n = I18nHelper()
        assert hasattr(i18n, 'master_rules'), "i18n_helper missing master_rules loading"
        assert hasattr(i18n, 'get_master_test_cases'), "i18n_helper missing get_master_test_cases method"
        assert hasattr(i18n, 'get_master_integration_steps'), "i18n_helper missing get_master_integration_steps method"
        
        # Test 2: TestCaseGenerator includes master rules
        generator = TestCaseGenerator()
        
        # Check that generator has access to master rules
        assert hasattr(generator.i18n, 'master_rules'), "TestCaseGenerator missing master rules access"
        
        # Test 3: Integration steps method includes master rules
        empty_features = {}
        steps = generator.generate_integration_steps(empty_features)
        master_steps = [s for s in steps if s['feature_name'] == 'Master Rules']
        assert len(master_steps) > 0, "generate_integration_steps not including master rules"
        
        # Test 4: Test case generation includes master rules  
        test_cases = generator.generate_test_cases_for_features(empty_features)
        master_cases = [tc for tc in test_cases if tc['provider'] == 'All Providers']
        assert len(master_cases) > 0, "generate_test_cases_for_features not including master rules"
        
        # Test 5: Document generation includes master rules
        doc = generator.generate_markdown_document(empty_features)
        assert 'MST' in doc, "Document generation not including master test cases"


if __name__ == "__main__":
    # Run business requirement tests specifically
    pytest.main([__file__, "-v", "-m", "business_requirement"])
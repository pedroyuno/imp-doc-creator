#!/usr/bin/env python3
"""
Tests for Feature Rules Management Web Interface
"""

import pytest
import json
import tempfile
import os
from io import BytesIO
from web_app import app


class TestFeatureRulesManagement:
    """Test the feature rules management web interface"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def temp_rules_file(self):
        """Create a temporary rules file for testing"""
        temp_rules = {
            "version": "2.0",
            "description": "Test rules",
            "last_updated": "2024-01-01",
            "rules": {
                "TestFeature": {
                    "feature_name": "TestFeature",
                    "integration_steps": [
                        {
                            "documentation_url": "https://test.example.com",
                            "comment": "Test feature comment"
                        }
                    ],
                    "testcases": [
                        {
                            "id": "TST0001",
                            "description_key": "testcase.test.basic",
                            "type": "happy path",
                            "environment": "both"
                        }
                    ]
                }
            },
            "metadata": {
                "total_rules": 1,
                "testcase_types": ["happy path", "unhappy path", "corner case"],
                "environments": ["sandbox", "production", "both"]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(temp_rules, f)
            temp_file_path = f.name
        
        # Backup original and replace
        original_path = 'feature_rules.json'
        backup_path = None
        if os.path.exists(original_path):
            backup_path = original_path + '.backup'
            os.rename(original_path, backup_path)
        
        os.rename(temp_file_path, original_path)
        
        yield original_path
        
        # Restore original
        if backup_path and os.path.exists(backup_path):
            os.rename(backup_path, original_path)
        elif os.path.exists(original_path):
            os.remove(original_path)
    
    def test_feature_rules_page(self, client, temp_rules_file):
        """Test the main feature rules page"""
        response = client.get('/feature-rules')
        assert response.status_code == 200
        assert b'Feature Rules Management' in response.data
        assert b'TestFeature' in response.data
    
    def test_edit_feature_rule_page(self, client, temp_rules_file):
        """Test editing a feature rule"""
        response = client.get('/feature-rules/edit/TestFeature')
        assert response.status_code == 200
        assert b'Edit Feature Rule: TestFeature' in response.data
        assert b'https://test.example.com' in response.data
    
    def test_edit_nonexistent_feature_rule(self, client, temp_rules_file):
        """Test editing a non-existent feature rule"""
        response = client.get('/feature-rules/edit/NonExistent')
        assert response.status_code == 302  # Redirect
    
    def test_save_feature_rule(self, client, temp_rules_file):
        """Test saving changes to a feature rule"""
        data = {
            'feature_name': 'TestFeature',
            'documentation_url': 'https://updated.example.com',
            'comment': 'Updated comment'
        }
        response = client.post('/feature-rules/save', data=data)
        assert response.status_code == 302  # Redirect to feature rules page
        
        # Verify the change was saved
        with open(temp_rules_file, 'r') as f:
            rules_data = json.load(f)
        
        assert rules_data['rules']['TestFeature']['integration_steps'][0]['documentation_url'] == 'https://updated.example.com'
        assert rules_data['rules']['TestFeature']['integration_steps'][0]['comment'] == 'Updated comment'
    
    def test_add_feature_rule_page(self, client, temp_rules_file):
        """Test the add feature rule page"""
        response = client.get('/feature-rules/add')
        assert response.status_code == 200
        assert b'Add New Feature Rule' in response.data
    
    def test_add_feature_rule(self, client, temp_rules_file):
        """Test adding a new feature rule"""
        data = {
            'feature_name': 'NewFeature',
            'documentation_url': 'https://new.example.com',
            'comment': 'New feature comment'
        }
        response = client.post('/feature-rules/add', data=data)
        assert response.status_code == 302  # Redirect
        
        # Verify the new rule was added
        with open(temp_rules_file, 'r') as f:
            rules_data = json.load(f)
        
        assert 'NewFeature' in rules_data['rules']
        assert rules_data['rules']['NewFeature']['integration_steps'][0]['documentation_url'] == 'https://new.example.com'
    
    def test_delete_feature_rule(self, client, temp_rules_file):
        """Test deleting a feature rule"""
        response = client.post('/feature-rules/delete/TestFeature')
        assert response.status_code == 302  # Redirect
        
        # Verify the rule was deleted
        with open(temp_rules_file, 'r') as f:
            rules_data = json.load(f)
        
        assert 'TestFeature' not in rules_data['rules']
    
    def test_reorder_feature_rules(self, client, temp_rules_file):
        """Test reordering feature rules"""
        # Add another feature first
        data = {
            'feature_name': 'AnotherFeature',
            'documentation_url': 'https://another.example.com',
            'comment': 'Another feature comment'
        }
        client.post('/feature-rules/add', data=data)
        
        # Test reordering
        new_order = ['AnotherFeature', 'TestFeature']
        response = client.post('/feature-rules/reorder', 
                             json={'order': new_order},
                             content_type='application/json')
        assert response.status_code == 200
        
        # Verify the order was changed
        with open(temp_rules_file, 'r') as f:
            rules_data = json.load(f)
        
        rule_names = list(rules_data['rules'].keys())
        assert rule_names == new_order
    
    def test_manage_testcases_page(self, client, temp_rules_file):
        """Test the test cases management page"""
        response = client.get('/feature-rules/TestFeature/testcases')
        assert response.status_code == 200
        assert b'Test Cases for TestFeature' in response.data
        assert b'TST0001' in response.data
    
    def test_add_testcase_page(self, client, temp_rules_file):
        """Test the add test case page"""
        response = client.get('/feature-rules/TestFeature/testcases/add')
        assert response.status_code == 200
        assert b'Add Test Case to TestFeature' in response.data
    
    def test_add_testcase(self, client, temp_rules_file):
        """Test adding a new test case"""
        data = {
            'testcase_id': 'TST0002',
            'description_key': 'testcase.test.new',
            'testcase_type': 'unhappy path',
            'environment': 'sandbox'
        }
        response = client.post('/feature-rules/TestFeature/testcases/add', data=data)
        assert response.status_code == 302  # Redirect
        
        # Verify the test case was added
        with open(temp_rules_file, 'r') as f:
            rules_data = json.load(f)
        
        testcases = rules_data['rules']['TestFeature']['testcases']
        assert len(testcases) == 2
        assert any(tc['id'] == 'TST0002' for tc in testcases)
    
    def test_edit_testcase_page(self, client, temp_rules_file):
        """Test the edit test case page"""
        response = client.get('/feature-rules/TestFeature/testcases/TST0001/edit')
        assert response.status_code == 200
        assert b'Edit Test Case: TST0001' in response.data
    
    def test_edit_testcase(self, client, temp_rules_file):
        """Test editing a test case"""
        data = {
            'description_key': 'testcase.test.updated',
            'testcase_type': 'corner case',
            'environment': 'production'
        }
        response = client.post('/feature-rules/TestFeature/testcases/TST0001/edit', data=data)
        assert response.status_code == 302  # Redirect
        
        # Verify the test case was updated
        with open(temp_rules_file, 'r') as f:
            rules_data = json.load(f)
        
        testcase = rules_data['rules']['TestFeature']['testcases'][0]
        assert testcase['description_key'] == 'testcase.test.updated'
        assert testcase['type'] == 'corner case'
        assert testcase['environment'] == 'production'
    
    def test_delete_testcase(self, client, temp_rules_file):
        """Test deleting a test case"""
        response = client.post('/feature-rules/TestFeature/testcases/TST0001/delete')
        assert response.status_code == 302  # Redirect
        
        # Verify the test case was deleted
        with open(temp_rules_file, 'r') as f:
            rules_data = json.load(f)
        
        testcases = rules_data['rules']['TestFeature']['testcases']
        assert len(testcases) == 0
    
    def test_error_handling(self, client):
        """Test error handling for various scenarios"""
        # Test accessing rules when file doesn't exist
        if os.path.exists('feature_rules.json'):
            os.rename('feature_rules.json', 'feature_rules.json.tmp')
        
        try:
            response = client.get('/feature-rules')
            assert response.status_code == 302  # Redirect on error
        finally:
            if os.path.exists('feature_rules.json.tmp'):
                os.rename('feature_rules.json.tmp', 'feature_rules.json') 
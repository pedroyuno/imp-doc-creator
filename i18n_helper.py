#!/usr/bin/env python3
"""
Simple i18n helper for test case descriptions
Demonstrates how to load and use translation files with the feature rules
"""

import json
import os
from typing import Dict, Any, Optional

class I18nHelper:
    def __init__(self, default_locale: str = 'en'):
        self.default_locale = default_locale
        self.translations: Dict[str, Dict] = {}
        self.feature_rules: Dict[str, Any] = {}
        
        # Load translations
        self._load_translations()
        
        # Load feature rules
        self._load_feature_rules()
    
    def _load_translations(self):
        """Load all translation files from i18n directory"""
        i18n_dir = os.path.join(os.path.dirname(__file__), 'i18n')
        
        for locale in ['en', 'es', 'pt']:
            file_path = os.path.join(i18n_dir, f'{locale}.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[locale] = json.load(f)
    
    def _load_feature_rules(self):
        """Load feature rules from JSON file"""
        rules_file = os.path.join(os.path.dirname(__file__), 'feature_rules.json')
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.feature_rules = data.get('rules', {})
    
    def get_text(self, key: str, locale: str = None) -> str:
        """
        Get translated text for a given key and locale
        
        Args:
            key: i18n key (e.g., 'testcase.verify.valid_payment_method')
            locale: target locale (e.g., 'es', 'pt', 'en')
        
        Returns:
            Translated text or key if translation not found
        """
        if locale is None:
            locale = self.default_locale
        
        if locale not in self.translations:
            locale = self.default_locale
        
        # Navigate through nested dictionary using dot notation
        keys = key.split('.')
        current = self.translations[locale]
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            # Return the key if translation not found
            return key
    
    def get_test_cases_for_feature(self, feature_name: str, locale: str = None) -> list:
        """
        Get all test cases for a feature with translated descriptions
        
        Args:
            feature_name: Name of the feature (e.g., 'Verify', 'Authorize')
            locale: target locale
            
        Returns:
            List of test cases with translated descriptions
        """
        if feature_name not in self.feature_rules:
            return []
        
        test_cases = []
        feature_data = self.feature_rules[feature_name]
        
        for testcase in feature_data.get('testcases', []):
            translated_case = {
                'id': testcase['id'],
                'description': self.get_text(testcase['description_key'], locale),
                'type': testcase['type']
            }
            test_cases.append(translated_case)
        
        return test_cases
    
    def get_all_test_cases(self, locale: str = None) -> Dict[str, list]:
        """
        Get all test cases for all features with translated descriptions
        
        Args:
            locale: target locale
            
        Returns:
            Dictionary with feature names as keys and test cases as values
        """
        all_test_cases = {}
        
        for feature_name in self.feature_rules.keys():
            all_test_cases[feature_name] = self.get_test_cases_for_feature(feature_name, locale)
        
        return all_test_cases

def main():
    """Example usage of the i18n helper"""
    i18n = I18nHelper()
    
    print("=== Example Usage ===\n")
    
    # Example 1: Get specific test case in different languages
    key = "testcase.verify.valid_payment_method"
    print(f"Key: {key}")
    print(f"English: {i18n.get_text(key, 'en')}")
    print(f"Spanish: {i18n.get_text(key, 'es')}")
    print(f"Portuguese: {i18n.get_text(key, 'pt')}")
    print()
    
    # Example 2: Get all test cases for Verify feature in Spanish
    print("=== Verify Feature Test Cases (Spanish) ===")
    verify_tests = i18n.get_test_cases_for_feature('Verify', 'es')
    for test in verify_tests:
        print(f"ID: {test['id']} | Type: {test['type']} | Description: {test['description']}")
    print()
    
    # Example 3: Get all test cases for Refund feature in Portuguese
    print("=== Refund Feature Test Cases (Portuguese) ===")
    refund_tests = i18n.get_test_cases_for_feature('Refund', 'pt')
    for test in refund_tests:
        print(f"ID: {test['id']} | Type: {test['type']} | Description: {test['description']}")

if __name__ == "__main__":
    main() 
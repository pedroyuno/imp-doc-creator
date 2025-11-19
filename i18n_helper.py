#!/usr/bin/env python3
"""
Simple i18n helper for test case descriptions
Demonstrates how to load and use translation files with the feature rules
"""

import json
import os
from typing import Dict, Any, Optional, List
from rules_manager import RulesManager

class I18nHelper:
    def __init__(self, default_locale: str = 'en', rules_file_paths: Optional[List[str]] = None):
        self.default_locale = default_locale
        self.translations: Dict[str, Dict] = {}
        self.feature_rules: Dict[str, Any] = {}
        self.master_rules: Dict[str, Any] = {}
        self.rules_file_paths = rules_file_paths
        
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
        """Load feature rules from JSON file(s)"""
        # Determine which files to load
        files_to_load = []
        default_file = os.path.join(os.path.dirname(__file__), 'feature_rules.json')
        
        # Always include default file if it exists
        if os.path.exists(default_file):
            files_to_load.append(default_file)
        
        # Add additional files if provided
        if self.rules_file_paths:
            for file_path in self.rules_file_paths:
                if os.path.exists(file_path) and file_path not in files_to_load:
                    files_to_load.append(file_path)
        
        # Load and merge rules from all files
        self.feature_rules = {}
        self.master_rules = {}
        
        for file_path in files_to_load:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Merge feature rules
                    for feature_name, rule_data in data.get('rules', {}).items():
                        if feature_name not in self.feature_rules:
                            # Deep copy the rule data
                            import copy
                            self.feature_rules[feature_name] = copy.deepcopy(rule_data)
                        else:
                            # Merge existing rule
                            existing = self.feature_rules[feature_name]
                            
                            # Merge by_payment_method
                            if 'by_payment_method' in rule_data:
                                if 'by_payment_method' not in existing:
                                    existing['by_payment_method'] = {}
                                
                                for pm_name, pm_data in rule_data['by_payment_method'].items():
                                    if pm_name not in existing['by_payment_method']:
                                        existing['by_payment_method'][pm_name] = copy.deepcopy(pm_data)
                                    else:
                                        # Merge integration_steps
                                        existing_pm = existing['by_payment_method'][pm_name]
                                        if 'integration_steps' in pm_data:
                                            existing_steps = existing_pm.get('integration_steps', [])
                                            new_steps = pm_data.get('integration_steps', [])
                                            # Append new steps that don't already exist
                                            for new_step in new_steps:
                                                step_key = (new_step.get('documentation_url', ''), new_step.get('comment', ''))
                                                if not any((s.get('documentation_url', '') == step_key[0] and 
                                                           s.get('comment', '') == step_key[1]) for s in existing_steps):
                                                    existing_steps.append(new_step)
                                            existing_pm['integration_steps'] = existing_steps
                                        
                                        # Merge testcases
                                        if 'testcases' in pm_data:
                                            existing_tcs = {tc['id']: tc for tc in existing_pm.get('testcases', [])}
                                            for tc in pm_data.get('testcases', []):
                                                if tc['id'] not in existing_tcs:
                                                    existing_pm.setdefault('testcases', []).append(tc)
                            
                            # Merge by_provider (provider-specific steps)
                            if 'by_provider' in rule_data:
                                if 'by_provider' not in existing:
                                    existing['by_provider'] = {}
                                
                                for provider, provider_steps in rule_data['by_provider'].items():
                                    if provider not in existing['by_provider']:
                                        existing['by_provider'][provider] = copy.deepcopy(provider_steps)
                                    else:
                                        # Append new steps
                                        existing['by_provider'][provider].extend(provider_steps)
                    
                    # Merge master rules
                    master = data.get('master', {})
                    if master:
                        # Merge master testcases
                        if 'testcases' in master:
                            existing_tcs = {tc['id']: tc for tc in self.master_rules.get('testcases', [])}
                            for tc in master.get('testcases', []):
                                if tc['id'] not in existing_tcs:
                                    self.master_rules.setdefault('testcases', []).append(tc)
                        
                        # Merge master integration_steps
                        if 'integration_steps' in master:
                            existing_steps = {(s.get('documentation_url', ''), s.get('comment', '')): s 
                                             for s in self.master_rules.get('integration_steps', [])}
                            for step in master.get('integration_steps', []):
                                step_key = (step.get('documentation_url', ''), step.get('comment', ''))
                                if step_key not in existing_steps:
                                    self.master_rules.setdefault('integration_steps', []).append(step)
            except Exception as e:
                # Skip files that can't be loaded
                pass
        
        # Ensure every feature that has universal testcases also includes a by_payment_method key
        try:
            for feature_name, feature_data in self.feature_rules.items():
                if isinstance(feature_data, dict):
                    if 'testcases' in feature_data and 'by_payment_method' not in feature_data:
                        feature_data['by_payment_method'] = {}
        except Exception:
            # Be permissive: if structure isn't as expected, skip enrichment
            pass
    
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
    
    def get_test_cases_for_feature(self, feature_name: str, locale: str = None, payment_method: str = None) -> list:
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
        
        # New structure: by_payment_method with 'universal' section
        by_pm = feature_data.get('by_payment_method', {}) or {}
        universal = by_pm.get('universal', {}) if isinstance(by_pm, dict) else {}
        for testcase in universal.get('testcases', []) or []:
            translated_case = {
                'id': testcase['id'],
                'description': self.get_text(testcase['description_key'], locale),
                'type': testcase['type'],
                'environment': testcase.get('environment', 'both')
            }
            test_cases.append(translated_case)
        
        # Method-specific cases (case-insensitive key match)
        if payment_method and isinstance(by_pm, dict):
            pm_lookup = {str(k).lower(): v for k, v in by_pm.items()}
            pm_block = pm_lookup.get(str(payment_method).lower())
            if isinstance(pm_block, dict):
                for testcase in pm_block.get('testcases', []) or []:
                    translated_case = {
                        'id': testcase['id'],
                        'description': self.get_text(testcase['description_key'], locale),
                        'type': testcase['type'],
                        'environment': testcase.get('environment', 'both')
                    }
                    test_cases.append(translated_case)
        
        # Backward-compat fallback: include top-level testcases if present
        if not test_cases:
            for testcase in feature_data.get('testcases', []) or []:
                translated_case = {
                    'id': testcase['id'],
                    'description': self.get_text(testcase['description_key'], locale),
                    'type': testcase['type'],
                    'environment': testcase.get('environment', 'both')
                }
                test_cases.append(translated_case)
        
        return test_cases

    def get_integration_steps_for_feature(self, feature_name: str, payment_method: str = None, provider: str = None) -> Dict[str, Any]:
        """
        Return integration steps for a feature.
        Returns both universal steps and provider-specific steps.
        If provider is specified, only returns steps for that provider.
        If provider is None, returns all provider-specific steps.
        
        Returns:
            Dictionary with 'universal' and 'provider_specific' keys containing lists of steps
        """
        result = {
            'universal': [],
            'provider_specific': {}
        }
        
        if feature_name not in self.feature_rules:
            return result
        
        feature_data = self.feature_rules[feature_name]
        by_pm = feature_data.get('by_payment_method', {}) or {}
        universal = by_pm.get('universal', {}) if isinstance(by_pm, dict) else {}
        steps = universal.get('integration_steps', []) or []
        
        if not steps:
            # Backward-compat fallback to top-level integration_steps
            steps = feature_data.get('integration_steps', []) or []
        
        result['universal'] = steps
        
        # Get provider-specific steps
        if 'by_provider' in feature_data:
            if provider:
                # Return steps for specific provider only
                provider_steps = feature_data['by_provider'].get(provider, [])
                if provider_steps:
                    result['provider_specific'][provider] = provider_steps
            else:
                # Return all provider-specific steps
                result['provider_specific'] = feature_data['by_provider'].copy()
        
        return result
    
    def get_master_test_cases(self, locale: str = None) -> list:
        """
        Get all master test cases with translated descriptions
        
        Args:
            locale: target locale
            
        Returns:
            List of master test cases with translated descriptions
        """
        test_cases = []
        
        for testcase in self.master_rules.get('testcases', []):
            translated_case = {
                'id': testcase['id'],
                'description': self.get_text(testcase['description_key'], locale),
                'type': testcase['type'],
                'environment': testcase.get('environment', 'both')
            }
            test_cases.append(translated_case)
        
        return test_cases
    
    def get_master_integration_steps(self) -> list:
        """
        Get master integration steps that apply to all conversions
        
        Returns:
            List of master integration steps with documentation URLs and comments
        """
        return self.master_rules.get('integration_steps', [])
    
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
    print()
    
    # Example 4: Get master integration steps and test cases
    print("=== Master Integration Steps ===")
    master_steps = i18n.get_master_integration_steps()
    for i, step in enumerate(master_steps, 1):
        print(f"Step {i}: {step['comment'][:60]}...")
    print()
    
    print("=== Master Test Cases (English) ===")
    master_tests = i18n.get_master_test_cases('en')
    for test in master_tests:
        print(f"ID: {test['id']} | Type: {test['type']} | Description: {test['description']}")


if __name__ == "__main__":
    main() 
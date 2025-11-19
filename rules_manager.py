#!/usr/bin/env python3
"""
Feature Rules Manager

This module manages feature documentation rules for dynamic documentation generation.
It loads rules from JSON files and provides methods to retrieve feature documentation
URLs and comments without requiring code changes.
"""

import json
import os
import glob
from typing import Dict, Any, Optional, List
from datetime import datetime


class FeatureRule:
    """Represents a single feature rule with documentation URL and comment."""
    
    def __init__(self, feature_name: str, documentation_url: str, comment: str, integration_steps: List[Dict[str, str]] = None, provider_specific_steps: Dict[str, List[Dict[str, str]]] = None):
        self.feature_name = feature_name
        self.documentation_url = documentation_url
        self.comment = comment
        self.integration_steps = integration_steps or []
        self.provider_specific_steps = provider_specific_steps or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary format."""
        result = {
            'feature_name': self.feature_name,
            'documentation_url': self.documentation_url,
            'comment': self.comment
        }
        if self.integration_steps:
            result['integration_steps'] = self.integration_steps
        return result
    
    def __repr__(self) -> str:
        return f"FeatureRule('{self.feature_name}', '{self.documentation_url[:50]}...', '{self.comment[:50]}...')"


class RulesManager:
    """Manages feature documentation rules for dynamic documentation generation."""
    
    def __init__(self, rules_file_path: str = 'feature_rules.json', verbose: bool = True, rules_file_paths: Optional[List[str]] = None):
        self.rules_file_path = rules_file_path
        self.rules_file_paths = rules_file_paths or []
        self.verbose = verbose
        self.rules: Dict[str, FeatureRule] = {}
        self.metadata: Dict[str, Any] = {}
        self.version: str = ""
        self.last_loaded: Optional[datetime] = None
        self.loaded_files: List[str] = []
        
    def load_rules(self) -> None:
        """Load rules from JSON file(s)."""
        if self.rules_file_paths:
            # Load multiple files
            self.load_multiple_rules(self.rules_file_paths)
        else:
            # Single file loading (backward compatibility)
            data = self._load_single_rules_file(self.rules_file_path)
            if data:
                # Process single file data
                self.loaded_files = [self.rules_file_path]
                self.version = data.get('version', 'unknown')
                self.metadata = data.get('metadata', {})
                self.rules = {}
                
                # Process rules from single file
                for feature_name, rule_data in data.get('rules', {}).items():
                    if not isinstance(rule_data, dict):
                        if self.verbose:
                            print(f"⚠️  Skipping invalid rule for '{feature_name}': not a dictionary")
                        continue
                    
                    # Extract provider-specific steps if present
                    provider_specific_steps = {}
                    if 'by_provider' in rule_data:
                        provider_specific_steps = rule_data['by_provider']
                    
                    # Get integration steps from by_payment_method.universal or top-level
                    integration_steps = []
                    if 'by_payment_method' in rule_data:
                        universal = rule_data['by_payment_method'].get('universal', {})
                        integration_steps = universal.get('integration_steps', [])
                    elif 'integration_steps' in rule_data:
                        integration_steps = rule_data.get('integration_steps', [])
                    
                    # Get first step for backward compatibility
                    documentation_url = ''
                    comment = ''
                    if integration_steps and isinstance(integration_steps, list) and len(integration_steps) > 0:
                        first_step = integration_steps[0]
                        documentation_url = first_step.get('documentation_url', '')
                        comment = first_step.get('comment', '')
                    elif 'documentation_url' in rule_data:
                        # Legacy format
                        documentation_url = rule_data.get('documentation_url', '')
                        comment = rule_data.get('comment', '')
                        if not integration_steps:
                            integration_steps = [{
                                'documentation_url': documentation_url,
                                'comment': comment
                            }]
                    
                    self.rules[feature_name] = FeatureRule(
                        feature_name=rule_data.get('feature_name', feature_name),
                        documentation_url=documentation_url,
                        comment=comment,
                        integration_steps=integration_steps,
                        provider_specific_steps=provider_specific_steps
                    )
                
                self.last_loaded = datetime.now()
                if self.verbose:
                    print(f"✓ Successfully loaded {len(self.rules)} feature rules from '{self.rules_file_path}'")
                    print(f"  Version: {self.version}")
            else:
                self.rules = {}
                self.loaded_files = []
    
    def _load_single_rules_file(self, file_path: str) -> Dict[str, Any]:
        """Load a single rules file and return its data."""
        try:
            if not os.path.exists(file_path):
                if self.verbose:
                    print(f"⚠️  Rules file '{file_path}' not found.")
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Validate structure
            if 'rules' not in data:
                if self.verbose:
                    print(f"⚠️  Rules file '{file_path}' missing 'rules' section")
                return {}
            
            return data
                
        except FileNotFoundError:
            if self.verbose:
                print(f"✗ Rules file '{file_path}' not found")
            return {}
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"✗ Error parsing JSON in rules file '{file_path}': {e}")
            return {}
        except Exception as e:
            if self.verbose:
                print(f"✗ Error loading rules from '{file_path}': {e}")
            return {}
    
    def load_multiple_rules(self, rules_file_paths: List[str]) -> None:
        """
        Load and merge rules from multiple files.
        Default feature_rules.json is always loaded first as base, then provider-specific files are merged.
        """
        self.rules = {}
        self.loaded_files = []
        all_metadata = []
        
        # Always include default feature_rules.json if it exists
        default_file = 'feature_rules.json'
        if default_file not in rules_file_paths and os.path.exists(default_file):
            rules_file_paths = [default_file] + rules_file_paths
        
        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in rules_file_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        rules_file_paths = unique_paths
        
        # Load each file and merge
        for file_path in rules_file_paths:
            data = self._load_single_rules_file(file_path)
            if not data:
                continue
            
            self.loaded_files.append(file_path)
            
            # Load metadata (use first file's version, merge metadata)
            if not self.version:
                self.version = data.get('version', 'unknown')
            if data.get('metadata'):
                all_metadata.append(data.get('metadata', {}))
            
            # Merge rules
            for feature_name, rule_data in data.get('rules', {}).items():
                if not isinstance(rule_data, dict):
                    if self.verbose:
                        print(f"⚠️  Skipping invalid rule for '{feature_name}': not a dictionary")
                    continue
                
                # Extract provider-specific steps if present
                provider_specific_steps = {}
                if 'by_provider' in rule_data:
                    provider_specific_steps = rule_data['by_provider']
                
                # Get integration steps from by_payment_method.universal or top-level
                integration_steps = []
                if 'by_payment_method' in rule_data:
                    universal = rule_data['by_payment_method'].get('universal', {})
                    integration_steps = universal.get('integration_steps', [])
                elif 'integration_steps' in rule_data:
                    integration_steps = rule_data.get('integration_steps', [])
                
                # Get first step for backward compatibility (documentation_url, comment)
                documentation_url = ''
                comment = ''
                if integration_steps and isinstance(integration_steps, list) and len(integration_steps) > 0:
                    first_step = integration_steps[0]
                    documentation_url = first_step.get('documentation_url', '')
                    comment = first_step.get('comment', '')
                elif 'documentation_url' in rule_data:
                    # Legacy format
                    documentation_url = rule_data.get('documentation_url', '')
                    comment = rule_data.get('comment', '')
                    if not integration_steps:
                        integration_steps = [{
                            'documentation_url': documentation_url,
                            'comment': comment
                        }]
                
                # Merge with existing rule if it exists
                if feature_name in self.rules:
                    existing_rule = self.rules[feature_name]
                    # Merge integration steps (append new ones)
                    merged_steps = existing_rule.integration_steps.copy()
                    for step in integration_steps:
                        if step not in merged_steps:
                            merged_steps.append(step)
                    integration_steps = merged_steps
                    
                    # Merge provider-specific steps
                    merged_provider_steps = existing_rule.provider_specific_steps.copy()
                    for provider, steps in provider_specific_steps.items():
                        if provider in merged_provider_steps:
                            # Append steps for this provider
                            merged_provider_steps[provider].extend(steps)
                        else:
                            merged_provider_steps[provider] = steps.copy()
                    provider_specific_steps = merged_provider_steps
                    
                    # Update URL and comment if not set
                    if not documentation_url:
                        documentation_url = existing_rule.documentation_url
                    if not comment:
                        comment = existing_rule.comment
                
                # Create or update rule
                self.rules[feature_name] = FeatureRule(
                    feature_name=rule_data.get('feature_name', feature_name),
                    documentation_url=documentation_url,
                    comment=comment,
                    integration_steps=integration_steps,
                    provider_specific_steps=provider_specific_steps
                )
        
        # Merge metadata
        if all_metadata:
            self.metadata = {}
            for meta in all_metadata:
                for key, value in meta.items():
                    if key not in self.metadata:
                        self.metadata[key] = value
                    elif isinstance(value, list) and isinstance(self.metadata[key], list):
                        # Merge lists
                        self.metadata[key] = list(set(self.metadata[key] + value))
        
        self.last_loaded = datetime.now()
        
        if self.verbose:
            print(f"✓ Successfully loaded {len(self.rules)} feature rules from {len(self.loaded_files)} file(s)")
            print(f"  Files: {', '.join(self.loaded_files)}")
            print(f"  Version: {self.version}")
    
    @staticmethod
    def get_provider_rules_files(directory: str = '.') -> List[str]:
        """
        Discover available provider-specific rules files matching pattern feature_rules_*.json.
        
        Args:
            directory: Directory to search in (default: current directory)
            
        Returns:
            List of file paths matching the pattern
        """
        pattern = os.path.join(directory, 'feature_rules_*.json')
        files = glob.glob(pattern)
        return sorted(files)
    
    def get_rule(self, feature_name: str) -> Optional[FeatureRule]:
        """Get rule for a specific feature."""
        return self.rules.get(feature_name)
    
    def get_documentation_url(self, feature_name: str) -> Optional[str]:
        """Get documentation URL for a feature."""
        rule = self.get_rule(feature_name)
        return rule.documentation_url if rule else None
    
    def get_comment(self, feature_name: str) -> Optional[str]:
        """Get comment for a feature."""
        rule = self.get_rule(feature_name)
        return rule.comment if rule else None
    
    def has_rule(self, feature_name: str) -> bool:
        """Check if a rule exists for the given feature."""
        return feature_name in self.rules
    
    def get_all_features(self) -> List[str]:
        """Get list of all features that have rules."""
        return list(self.rules.keys())
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """Get summary information about loaded rules."""
        return {
            'total_rules': len(self.rules),
            'version': self.version,
            'last_loaded': self.last_loaded.isoformat() if self.last_loaded else None,
            'rules_file': self.rules_file_path,
            'rules_files': self.loaded_files if self.loaded_files else [self.rules_file_path],
            'metadata': self.metadata
        }
    
    def enrich_feature_data(self, feature_name: str, feature_value: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Enrich feature data with documentation URL and comment from rules.
        
        Args:
            feature_name: Name of the feature
            feature_value: Value of the feature
            provider: Optional provider name to get provider-specific integration steps
        """
        rule = self.get_rule(feature_name)
        
        enriched_data = {
            'name': feature_name,
            'value': feature_value,
            'has_value': bool(feature_value.strip()) if feature_value else False,
            'feature_name': feature_name,
            'feature_value': feature_value,
            'has_rule': rule is not None
        }
        
        if rule:
            # Get universal integration steps
            integration_steps = rule.integration_steps if hasattr(rule, 'integration_steps') else []
            
            # Get provider-specific steps if provider is specified
            provider_steps = []
            if provider and hasattr(rule, 'provider_specific_steps'):
                provider_steps = rule.provider_specific_steps.get(provider, [])
            
            enriched_data.update({
                'documentation_url': rule.documentation_url,
                'comment': rule.comment,
                'integration_steps': integration_steps,
                'provider_specific_steps': provider_steps if provider else {}
            })
            
            if self.verbose:
                print(f"🔗 DEBUG: Feature '{feature_name}' matched with rule -> {rule.documentation_url}")
                if provider and provider_steps:
                    print(f"  Provider-specific steps for {provider}: {len(provider_steps)}")
        else:
            enriched_data.update({
                'documentation_url': None,
                'comment': None,
                'integration_steps': [],
                'provider_specific_steps': {}
            })
            
            if self.verbose:
                print(f"⚠️  DEBUG: Feature '{feature_name}' has no matching rule in feature_rules.json")
        
        return enriched_data
    
    def reload_rules(self) -> None:
        """Reload rules from file (useful for dynamic updates)."""
        if self.verbose:
            print("🔄 Reloading feature rules...")
        self.load_rules()
    
    def validate_rules_file(self) -> Dict[str, Any]:
        """Validate the rules file structure and return validation results."""
        validation_results = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            if not os.path.exists(self.rules_file_path):
                validation_results['errors'].append(f"Rules file '{self.rules_file_path}' does not exist")
                return validation_results
            
            with open(self.rules_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Check top-level structure
            if 'rules' not in data:
                validation_results['errors'].append("Missing 'rules' section")
                return validation_results
            
            # Validate each rule
            valid_rules = 0
            invalid_rules = 0
            
            for feature_name, rule_data in data['rules'].items():
                if not isinstance(rule_data, dict):
                    validation_results['errors'].append(f"Rule '{feature_name}' is not a dictionary")
                    invalid_rules += 1
                    continue
                
                # Check for new format with integration_steps
                if 'integration_steps' in rule_data:
                    integration_steps = rule_data.get('integration_steps', [])
                    if not isinstance(integration_steps, list):
                        validation_results['errors'].append(f"Rule '{feature_name}': integration_steps must be an array")
                        invalid_rules += 1
                        continue
                    
                    if len(integration_steps) == 0:
                        validation_results['errors'].append(f"Rule '{feature_name}': integration_steps array is empty")
                        invalid_rules += 1
                        continue
                    
                    # Validate each integration step
                    for i, step in enumerate(integration_steps):
                        if not isinstance(step, dict):
                            validation_results['errors'].append(f"Rule '{feature_name}': integration_steps[{i}] is not a dictionary")
                            invalid_rules += 1
                            break
                        
                        step_required_fields = ['documentation_url', 'comment']
                        missing_fields = [field for field in step_required_fields if field not in step]
                        if missing_fields:
                            validation_results['errors'].append(f"Rule '{feature_name}': integration_steps[{i}] missing fields: {missing_fields}")
                            invalid_rules += 1
                            break
                        
                        # Check for empty values
                        empty_fields = [field for field in step_required_fields if not step[field].strip()]
                        if empty_fields:
                            validation_results['warnings'].append(f"Rule '{feature_name}': integration_steps[{i}] has empty fields: {empty_fields}")
                    else:
                        # All steps are valid
                        valid_rules += 1
                else:
                    # Legacy format validation
                    required_fields = ['feature_name', 'documentation_url', 'comment']
                    missing_fields = [field for field in required_fields if field not in rule_data]
                    
                    if missing_fields:
                        validation_results['errors'].append(f"Rule '{feature_name}' missing fields: {missing_fields}")
                        invalid_rules += 1
                        continue
                    
                    # Check for empty values
                    empty_fields = [field for field in required_fields if not rule_data[field].strip()]
                    if empty_fields:
                        validation_results['warnings'].append(f"Rule '{feature_name}' has empty fields: {empty_fields}")
                    
                    valid_rules += 1
            
            validation_results['stats'] = {
                'total_rules': len(data['rules']),
                'valid_rules': valid_rules,
                'invalid_rules': invalid_rules,
                'version': data.get('version', 'unknown')
            }
            
            validation_results['is_valid'] = invalid_rules == 0
            
        except json.JSONDecodeError as e:
            validation_results['errors'].append(f"Invalid JSON format: {e}")
        except Exception as e:
            validation_results['errors'].append(f"Validation error: {e}")
        
        return validation_results


def main():
    """Example usage of the RulesManager."""
    print("🔧 Feature Rules Manager Example")
    print("=" * 50)
    
    # Create rules manager
    rules_manager = RulesManager()
    
    # Load rules
    rules_manager.load_rules()
    
    # Show summary
    summary = rules_manager.get_rules_summary()
    print(f"\n📊 Rules Summary:")
    print(f"  Total rules: {summary['total_rules']}")
    print(f"  Version: {summary['version']}")
    print(f"  Last loaded: {summary['last_loaded']}")
    
    # Example feature lookups
    test_features = ['Country', 'Verify', 'NonExistentFeature']
    
    print(f"\n🔍 Feature Rule Lookups:")
    for feature in test_features:
        if rules_manager.has_rule(feature):
            rule = rules_manager.get_rule(feature)
            print(f"  ✓ {feature}:")
            print(f"    URL: {rule.documentation_url}")
            print(f"    Comment: {rule.comment[:100]}...")
            if rule.integration_steps:
                print(f"    Integration Steps: {len(rule.integration_steps)}")
        else:
            print(f"  ✗ {feature}: No rule found")
    
    # Validate rules file
    print(f"\n✅ Rules File Validation:")
    validation = rules_manager.validate_rules_file()
    print(f"  Valid: {validation['is_valid']}")
    if validation['errors']:
        print(f"  Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"  Warnings: {validation['warnings']}")


if __name__ == "__main__":
    main() 
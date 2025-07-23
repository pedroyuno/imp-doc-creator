#!/usr/bin/env python3
"""
Feature Rules Manager

This module manages feature documentation rules for dynamic documentation generation.
It loads rules from JSON files and provides methods to retrieve feature documentation
URLs and comments without requiring code changes.
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime


class FeatureRule:
    """Represents a single feature rule with documentation URL and comment."""
    
    def __init__(self, feature_name: str, documentation_url: str, comment: str):
        self.feature_name = feature_name
        self.documentation_url = documentation_url
        self.comment = comment
    
    def to_dict(self) -> Dict[str, str]:
        """Convert rule to dictionary format."""
        return {
            'feature_name': self.feature_name,
            'documentation_url': self.documentation_url,
            'comment': self.comment
        }
    
    def __repr__(self) -> str:
        return f"FeatureRule('{self.feature_name}', '{self.documentation_url[:50]}...', '{self.comment[:50]}...')"


class RulesManager:
    """Manages feature documentation rules for dynamic documentation generation."""
    
    def __init__(self, rules_file_path: str = 'feature_rules.json', verbose: bool = True):
        self.rules_file_path = rules_file_path
        self.verbose = verbose
        self.rules: Dict[str, FeatureRule] = {}
        self.metadata: Dict[str, Any] = {}
        self.version: str = ""
        self.last_loaded: Optional[datetime] = None
        
    def load_rules(self) -> None:
        """Load rules from JSON file."""
        try:
            if not os.path.exists(self.rules_file_path):
                if self.verbose:
                    print(f"⚠️  Rules file '{self.rules_file_path}' not found. Using empty rules set.")
                self.rules = {}
                return
            
            with open(self.rules_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Validate structure
            if 'rules' not in data:
                raise ValueError("Rules file must contain a 'rules' section")
            
            # Load metadata
            self.version = data.get('version', 'unknown')
            self.metadata = data.get('metadata', {})
            
            # Load rules
            self.rules = {}
            for feature_name, rule_data in data['rules'].items():
                if not isinstance(rule_data, dict):
                    if self.verbose:
                        print(f"⚠️  Skipping invalid rule for '{feature_name}': not a dictionary")
                    continue
                
                # Validate required fields
                required_fields = ['feature_name', 'documentation_url', 'comment']
                if not all(field in rule_data for field in required_fields):
                    if self.verbose:
                        print(f"⚠️  Skipping invalid rule for '{feature_name}': missing required fields")
                    continue
                
                self.rules[feature_name] = FeatureRule(
                    feature_name=rule_data['feature_name'],
                    documentation_url=rule_data['documentation_url'],
                    comment=rule_data['comment']
                )
            
            self.last_loaded = datetime.now()
            
            if self.verbose:
                print(f"✓ Successfully loaded {len(self.rules)} feature rules from '{self.rules_file_path}'")
                print(f"  Version: {self.version}")
                
        except FileNotFoundError:
            if self.verbose:
                print(f"✗ Rules file '{self.rules_file_path}' not found")
            self.rules = {}
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"✗ Error parsing JSON in rules file: {e}")
            self.rules = {}
        except Exception as e:
            if self.verbose:
                print(f"✗ Error loading rules: {e}")
            self.rules = {}
    
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
            'metadata': self.metadata
        }
    
    def enrich_feature_data(self, feature_name: str, feature_value: str) -> Dict[str, Any]:
        """Enrich feature data with documentation URL and comment."""
        enriched_data = {
            'name': feature_name,
            'value': feature_value,
            'has_value': bool(feature_value.strip()) if feature_value else False,
            'documentation_url': None,
            'comment': None,
            'has_rule': False
        }
        
        rule = self.get_rule(feature_name)
        if rule:
            enriched_data.update({
                'documentation_url': rule.documentation_url,
                'comment': rule.comment,
                'has_rule': True
            })
        
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
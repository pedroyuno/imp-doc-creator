#!/usr/bin/env python3
"""
Test Case Generator for Implementation Scope

This module generates merchant-facing test case documents based on parsed 
implementation scope. It creates documents in multiple formats (HTML, Markdown)
for easy import into Google Docs and other documentation platforms.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from i18n_helper import I18nHelper


class TestCaseGenerator:
    def __init__(self, locale: str = 'en'):
        """
        Initialize the test case generator.
        
        Args:
            locale: Language locale for test case descriptions (en, es, pt)
        """
        self.locale = locale
        self.i18n = I18nHelper(default_locale=locale)
        
    def generate_test_cases_for_features(self, parsed_features: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Generate test cases for all implemented features from parsed data.
        
        Args:
            parsed_features: Dictionary of parsed features from CSV parser
            
        Returns:
            Dictionary with provider combinations as keys and test cases as values
        """
        all_test_cases = {}
        
        for provider_key, provider_data in parsed_features.items():
            provider = provider_data['provider']
            payment_method = provider_data['payment_method']
            features = provider_data['features']
            
            # Get test cases for implemented features only
            test_cases = []
            
            for feature_name, feature_value in features.items():
                # Only include test cases for implemented features
                if self._is_feature_implemented(feature_value):
                    feature_test_cases = self.i18n.get_test_cases_for_feature(feature_name, self.locale)
                    
                    # Add provider and payment method context to each test case
                    for test_case in feature_test_cases:
                        test_case_with_context = test_case.copy()
                        test_case_with_context.update({
                            'provider': provider,
                            'payment_method': payment_method,
                            'feature_name': feature_name,
                            'feature_value': feature_value
                        })
                        test_cases.append(test_case_with_context)
            
            if test_cases:  # Only add if there are test cases
                all_test_cases[provider_key] = {
                    'provider': provider,
                    'payment_method': payment_method,
                    'test_cases': test_cases
                }
        
        return all_test_cases
    
    def generate_markdown_document(self, parsed_features: Dict[str, Any], 
                                 merchant_name: str = "Merchant", 
                                 include_metadata: bool = True) -> str:
        """
        Generate a complete markdown document with test cases for merchants.
        
        Args:
            parsed_features: Dictionary of parsed features from CSV parser
            merchant_name: Name of the merchant for document header
            include_metadata: Whether to include document metadata
            
        Returns:
            Complete markdown document as string
        """
        test_cases_data = self.generate_test_cases_for_features(parsed_features)
        
        # Start building the markdown document
        markdown_lines = []
        
        # Document header
        if include_metadata:
            markdown_lines.extend([
                f"# Implementation Test Cases for {merchant_name}",
                "",
                f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Language:** {self.locale.upper()}",
                f"**Total Provider Combinations:** {len(test_cases_data)}",
                "",
                "---",
                ""
            ])
        
        # Introduction
        markdown_lines.extend([
            "## Test Case Documentation",
            "",
            "This document contains test cases for your payment integration implementation.",
            "Each test case should be executed to ensure proper functionality of the implemented features.",
            "Test cases are organized by provider and payment method combinations.",
            "",
            "### Test Case Types",
            "- **Happy Path:** Normal flow test cases",
            "- **Unhappy Path:** Error handling test cases", 
            "- **Corner Case:** Edge case and boundary test cases",
            "",
            "---",
            ""
        ])
        
        # Generate test cases for each provider combination
        for provider_key, provider_info in test_cases_data.items():
            provider = provider_info['provider']
            payment_method = provider_info['payment_method']
            test_cases = provider_info['test_cases']
            
            # Provider section header
            markdown_lines.extend([
                f"## {provider} + {payment_method}",
                "",
                f"**Total Test Cases:** {len(test_cases)}",
                ""
            ])
            
            # Group test cases by feature for better organization
            features_dict = {}
            for test_case in test_cases:
                feature_name = test_case['feature_name']
                if feature_name not in features_dict:
                    features_dict[feature_name] = []
                features_dict[feature_name].append(test_case)
            
            # Generate test cases for each feature
            for feature_name, feature_test_cases in features_dict.items():
                markdown_lines.extend([
                    f"### {feature_name} Feature",
                    ""
                ])
                
                # Add each test case as a single line (as requested)
                for test_case in feature_test_cases:
                    test_line = f"**{test_case['id']}** ({test_case['type']}): {test_case['description']}"
                    markdown_lines.append(test_line)
                
                markdown_lines.append("")  # Empty line after each feature
            
            markdown_lines.append("---")  # Separator between providers
            markdown_lines.append("")
        
        # Summary section
        if include_metadata:
            total_test_cases = sum(len(info['test_cases']) for info in test_cases_data.values())
            markdown_lines.extend([
                "## Summary",
                "",
                f"- **Total Providers:** {len(test_cases_data)}",
                f"- **Total Test Cases:** {total_test_cases}",
                f"- **Document Language:** {self.locale.upper()}",
                "",
                "### Implementation Notes",
                "- Execute all test cases in your test environment before going live",
                "- Document any failures or unexpected behaviors",
                "- Ensure all happy path scenarios work correctly",
                "- Test error handling for unhappy path scenarios",
                "- Validate edge cases and boundary conditions",
                "",
                "---",
                "",
                "*This document was automatically generated from your implementation scope.*"
            ])
        
        return '\n'.join(markdown_lines)
    
    def generate_html_document(self, parsed_features: Dict[str, Any], 
                             merchant_name: str = "Merchant", 
                             include_metadata: bool = True) -> str:
        """
        Generate a complete HTML document with test cases for merchants.
        Google Docs can import HTML files directly while preserving formatting.
        
        Args:
            parsed_features: Dictionary of parsed features from CSV parser
            merchant_name: Name of the merchant for document header
            include_metadata: Whether to include document metadata
            
        Returns:
            Complete HTML document as string
        """
        test_cases_data = self.generate_test_cases_for_features(parsed_features)
        
        # Start building the HTML document
        html_parts = []
        
        # Document start
        html_parts.extend([
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>Implementation Test Cases for {merchant_name}</title>',
            '    <style>',
            '        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }',
            '        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }',
            '        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; margin-top: 30px; }',
            '        h3 { color: #7f8c8d; margin-top: 25px; margin-bottom: 15px; }',
            '        .metadata { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; }',
            '        .test-case { margin: 8px 0; padding: 8px; background-color: #f9f9f9; border-left: 3px solid #27ae60; }',
            '        .test-case.unhappy { border-left-color: #e74c3c; }',
            '        .test-case.corner { border-left-color: #f39c12; }',
            '        .test-id { font-weight: bold; color: #2c3e50; }',
            '        .test-type { font-style: italic; color: #7f8c8d; }',
            '        .summary { background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin-top: 30px; }',
            '        .notes { background-color: #fff3cd; padding: 15px; border: 1px solid #ffeaa7; border-radius: 5px; margin-top: 20px; }',
            '        hr { border: none; border-top: 1px solid #bdc3c7; margin: 25px 0; }',
            '    </style>',
            '</head>',
            '<body>'
        ])
        
        # Document header
        if include_metadata:
            html_parts.extend([
                f'    <h1>Implementation Test Cases for {merchant_name}</h1>',
                '    <div class="metadata">',
                f'        <p><strong>Generated on:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
                f'        <p><strong>Language:</strong> {self.locale.upper()}</p>',
                f'        <p><strong>Total Provider Combinations:</strong> {len(test_cases_data)}</p>',
                '    </div>'
            ])
        else:
            html_parts.append(f'    <h1>Implementation Test Cases for {merchant_name}</h1>')
        
        # Introduction
        html_parts.extend([
            '    <h2>Test Case Documentation</h2>',
            '    <p>This document contains test cases for your payment integration implementation. Each test case should be executed to ensure proper functionality of the implemented features. Test cases are organized by provider and payment method combinations.</p>',
            '    <h3>Test Case Types</h3>',
            '    <ul>',
            '        <li><strong>Happy Path:</strong> Normal flow test cases</li>',
            '        <li><strong>Unhappy Path:</strong> Error handling test cases</li>',
            '        <li><strong>Corner Case:</strong> Edge case and boundary test cases</li>',
            '    </ul>',
            '    <hr>'
        ])
        
        # Generate test cases for each provider combination
        for provider_key, provider_info in test_cases_data.items():
            provider = provider_info['provider']
            payment_method = provider_info['payment_method']
            test_cases = provider_info['test_cases']
            
            # Provider section header
            html_parts.extend([
                f'    <h2>{provider} + {payment_method}</h2>',
                f'    <p><strong>Total Test Cases:</strong> {len(test_cases)}</p>'
            ])
            
            # Group test cases by feature for better organization
            features_dict = {}
            for test_case in test_cases:
                feature_name = test_case['feature_name']
                if feature_name not in features_dict:
                    features_dict[feature_name] = []
                features_dict[feature_name].append(test_case)
            
            # Generate test cases for each feature
            for feature_name, feature_test_cases in features_dict.items():
                html_parts.extend([
                    f'    <h3>{feature_name} Feature</h3>'
                ])
                
                # Add each test case as a formatted div
                for test_case in feature_test_cases:
                    test_type = test_case['type']
                    css_class = 'test-case'
                    if test_type == 'unhappy path':
                        css_class += ' unhappy'
                    elif test_type == 'corner case':
                        css_class += ' corner'
                    
                    html_parts.append(
                        f'    <div class="{css_class}">'
                        f'<span class="test-id">{test_case["id"]}</span> '
                        f'<span class="test-type">({test_case["type"]})</span>: '
                        f'{test_case["description"]}</div>'
                    )
            
            html_parts.append('    <hr>')
        
        # Summary section
        if include_metadata:
            total_test_cases = sum(len(info['test_cases']) for info in test_cases_data.values())
            html_parts.extend([
                '    <div class="summary">',
                '        <h2>Summary</h2>',
                '        <ul>',
                f'            <li><strong>Total Providers:</strong> {len(test_cases_data)}</li>',
                f'            <li><strong>Total Test Cases:</strong> {total_test_cases}</li>',
                f'            <li><strong>Document Language:</strong> {self.locale.upper()}</li>',
                '        </ul>',
                '    </div>',
                '    <div class="notes">',
                '        <h3>Implementation Notes</h3>',
                '        <ul>',
                '            <li>Execute all test cases in your test environment before going live</li>',
                '            <li>Document any failures or unexpected behaviors</li>',
                '            <li>Ensure all happy path scenarios work correctly</li>',
                '            <li>Test error handling for unhappy path scenarios</li>',
                '            <li>Validate edge cases and boundary conditions</li>',
                '        </ul>',
                '    </div>',
                '    <hr>',
                '    <p><em>This document was automatically generated from your implementation scope.</em></p>'
            ])
        
        # Close HTML document
        html_parts.extend([
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def generate_summary_statistics(self, parsed_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary statistics for the test cases.
        
        Args:
            parsed_features: Dictionary of parsed features from CSV parser
            
        Returns:
            Dictionary containing summary statistics
        """
        test_cases_data = self.generate_test_cases_for_features(parsed_features)
        
        total_test_cases = 0
        total_features = 0
        test_case_types = {'happy path': 0, 'unhappy path': 0, 'corner case': 0}
        features_by_provider = {}
        
        for provider_key, provider_info in test_cases_data.items():
            provider = provider_info['provider']
            test_cases = provider_info['test_cases']
            
            total_test_cases += len(test_cases)
            
            # Count unique features per provider
            unique_features = set(tc['feature_name'] for tc in test_cases)
            total_features += len(unique_features)
            features_by_provider[provider] = len(unique_features)
            
            # Count test case types
            for test_case in test_cases:
                test_type = test_case['type']
                if test_type in test_case_types:
                    test_case_types[test_type] += 1
        
        return {
            'total_providers': len(test_cases_data),
            'total_test_cases': total_test_cases,
            'total_implemented_features': total_features,
            'test_case_types': test_case_types,
            'features_by_provider': features_by_provider,
            'language': self.locale
        }
    
    def _is_feature_implemented(self, feature_value: str) -> bool:
        """
        Check if a feature is considered implemented based on its value.
        
        Args:
            feature_value: The value of the feature from CSV
            
        Returns:
            True if feature is implemented, False otherwise
        """
        if not feature_value:
            return False
        
        # Normalize value for comparison
        value = feature_value.strip().upper()
        
        # Consider these values as "implemented"
        implemented_values = ['TRUE', 'IMPLEMENTED', 'YES', 'Y', '1', 'SUPPORTED', 'AVAILABLE']
        
        return value in implemented_values


def main():
    """Example usage of the test case generator"""
    # Example parsed features data (this would normally come from CSV parser)
    example_features = {
        'REDE_CARD': {
            'provider': 'REDE',
            'payment_method': 'CARD',
            'features': {
                'Country': 'Brazil',
                'Verify': 'TRUE',
                'Authorize': 'TRUE',
                'Capture': 'TRUE',
                'Refund': 'TRUE',
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
                'Authorize': 'TRUE',
                'Capture': 'FALSE',
                'Refund': 'TRUE',
                '3DS': 'TRUE',
                'Webhook': 'TRUE'
            }
        }
    }
    
    # Generate test cases in English
    generator = TestCaseGenerator(locale='en')
    
    print("=== Test Case Generation Example ===")
    print()
    
    # Generate markdown document
    markdown_doc = generator.generate_markdown_document(
        example_features, 
        merchant_name="Example Merchant"
    )
    
    print("Generated Markdown Document:")
    print("=" * 50)
    print(markdown_doc)
    print("=" * 50)
    
    # Generate HTML document
    print("\n=== HTML Document Sample ===")
    html_doc = generator.generate_html_document(
        example_features,
        merchant_name="Example Merchant"
    )
    print("HTML document generated (showing first 500 characters):")
    print(html_doc[:500] + "...")
    
    # Generate summary statistics
    stats = generator.generate_summary_statistics(example_features)
    print("\nSummary Statistics:")
    print(f"Total Providers: {stats['total_providers']}")
    print(f"Total Test Cases: {stats['total_test_cases']}")
    print(f"Total Features: {stats['total_implemented_features']}")
    print(f"Test Case Types: {stats['test_case_types']}")


if __name__ == "__main__":
    main() 
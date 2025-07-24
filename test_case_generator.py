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
        
    def generate_test_cases_for_features(self, parsed_features: Dict[str, Any]) -> List[Dict]:
        """
        Generate test cases for all implemented features from parsed data.
        Returns a flat list of test cases for table format.
        
        Args:
            parsed_features: Dictionary of parsed features from CSV parser
            
        Returns:
            List of test cases with table columns: id, description, passed, date, executer, evidence
        """
        all_test_cases = []
        test_case_counter = 1
        
        for provider_key, provider_data in parsed_features.items():
            provider = provider_data['provider']
            payment_method = provider_data['payment_method']
            features = provider_data['features']
            
            # Generate test cases for implemented features only
            for feature_name, feature_value in features.items():
                # Only include test cases for implemented features
                if self._is_feature_implemented(feature_value):
                    feature_test_cases = self.i18n.get_test_cases_for_feature(feature_name, self.locale)
                    
                    # Convert each test case to table format
                    for test_case in feature_test_cases:
                        table_test_case = {
                            'id': f"TC-{test_case_counter:03d}",
                            'description': f"{provider} + {payment_method}: {test_case['description']}",
                            'passed': '',  # Empty field for manual completion
                            'date': '',    # Empty field for manual completion
                            'executer': '',  # Empty field for manual completion
                            'evidence': ''   # Empty field for manual completion
                        }
                        all_test_cases.append(table_test_case)
                        test_case_counter += 1
        
        return all_test_cases
    
    def generate_markdown_document(self, parsed_features: Dict[str, Any], 
                                 merchant_name: str = "Merchant", 
                                 include_metadata: bool = True) -> str:
        """
        Generate a complete markdown document with test cases in table format.
        
        Args:
            parsed_features: Dictionary of parsed features from CSV parser
            merchant_name: Name of the merchant for document header
            include_metadata: Whether to include document metadata
            
        Returns:
            Complete markdown document as string with table format
        """
        test_cases_data = self.generate_test_cases_for_features(parsed_features)
        
        # Start building the markdown document
        markdown_lines = []
        
        # Document header
        if include_metadata:
            markdown_lines.extend([
                f"# Test Cases for {merchant_name}",
                "",
                f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Language:** {self.locale.upper()}",
                f"**Total Test Cases:** {len(test_cases_data)}",
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
            "",
            ""
        ])
        
        # Generate table header
        markdown_lines.extend([
            "| ID | Description | Passed | Date | Executer | Evidence |",
            "|----|-----------|---------|----- |----------|----------|"
        ])
        
        # Generate table rows
        for test_case in test_cases_data:
            row = f"| {test_case['id']} | {test_case['description']} | {test_case['passed']} | {test_case['date']} | {test_case['executer']} | {test_case['evidence']} |"
            markdown_lines.append(row)
        
        # Summary section
        if include_metadata:
            markdown_lines.extend([
                "",
                "---",
                "",
                "## Summary",
                "",
                f"- **Total Test Cases:** {len(test_cases_data)}",
                f"- **Document Language:** {self.locale.upper()}",
                "",
                "### Instructions",
                "- Fill in the 'Passed' column with Yes/No after executing each test case",
                "- Record the execution date in the 'Date' column",
                "- Add the name of the person who executed the test in the 'Executer' column",
                "- Provide evidence (screenshots, logs, etc.) in the 'Evidence' column",
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
        Generate a complete HTML document with test cases in table format.
        Google Docs can import HTML files directly while preserving formatting.
        
        Args:
            parsed_features: Dictionary of parsed features from CSV parser
            merchant_name: Name of the merchant for document header
            include_metadata: Whether to include document metadata
            
        Returns:
            Complete HTML document as string with table format
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
            f'    <title>Test Cases for {merchant_name}</title>',
            '    <style>',
            '        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }',
            '        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }',
            '        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; margin-top: 30px; }',
            '        .metadata { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; }',
            '        table { width: 100%; border-collapse: collapse; margin-top: 20px; }',
            '        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }',
            '        th { background-color: #3498db; color: white; font-weight: bold; }',
            '        tr:nth-child(even) { background-color: #f2f2f2; }',
            '        tr:hover { background-color: #e8f4f8; }',
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
                f'    <h1>Test Cases for {merchant_name}</h1>',
                '    <div class="metadata">',
                f'        <p><strong>Generated on:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
                f'        <p><strong>Language:</strong> {self.locale.upper()}</p>',
                f'        <p><strong>Total Test Cases:</strong> {len(test_cases_data)}</p>',
                '    </div>'
            ])
        else:
            html_parts.append(f'    <h1>Test Cases for {merchant_name}</h1>')
        
        # Introduction
        html_parts.extend([
            '    <h2>Test Case Documentation</h2>',
            '    <p>This document contains test cases for your payment integration implementation. Each test case should be executed to ensure proper functionality of the implemented features.</p>',
            ''
        ])
        
        # Generate table
        html_parts.extend([
            '    <table>',
            '        <thead>',
            '            <tr>',
            '                <th>ID</th>',
            '                <th>Description</th>',
            '                <th>Passed</th>',
            '                <th>Date</th>',
            '                <th>Executer</th>',
            '                <th>Evidence</th>',
            '            </tr>',
            '        </thead>',
            '        <tbody>'
        ])
        
        # Generate table rows
        for test_case in test_cases_data:
            html_parts.append(
                f'            <tr>'
                f'<td>{test_case["id"]}</td>'
                f'<td>{test_case["description"]}</td>'
                f'<td>{test_case["passed"]}</td>'
                f'<td>{test_case["date"]}</td>'
                f'<td>{test_case["executer"]}</td>'
                f'<td>{test_case["evidence"]}</td>'
                f'</tr>'
            )
        
        html_parts.extend([
            '        </tbody>',
            '    </table>'
        ])
        
        # Summary section
        if include_metadata:
            html_parts.extend([
                '    <div class="summary">',
                '        <h2>Summary</h2>',
                '        <ul>',
                f'            <li><strong>Total Test Cases:</strong> {len(test_cases_data)}</li>',
                f'            <li><strong>Document Language:</strong> {self.locale.upper()}</li>',
                '        </ul>',
                '    </div>',
                '    <div class="notes">',
                '        <h3>Instructions</h3>',
                '        <ul>',
                '            <li>Fill in the "Passed" column with Yes/No after executing each test case</li>',
                '            <li>Record the execution date in the "Date" column</li>',
                '            <li>Add the name of the person who executed the test in the "Executer" column</li>',
                '            <li>Provide evidence (screenshots, logs, etc.) in the "Evidence" column</li>',
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
        
        # Count implemented features per provider
        features_by_provider = {}
        total_implemented_features = 0
        
        for provider_key, provider_data in parsed_features.items():
            provider = provider_data['provider']
            implemented_count = 0
            
            for feature_name, feature_value in provider_data['features'].items():
                if self._is_feature_implemented(feature_value):
                    implemented_count += 1
            
            features_by_provider[provider] = implemented_count
            total_implemented_features += implemented_count
        
        return {
            'total_providers': len(parsed_features),
            'total_test_cases': len(test_cases_data),
            'total_implemented_features': total_implemented_features,
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
    print(f"Features by Provider: {stats['features_by_provider']}")


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test Case Generator for Implementation Scope

This module generates merchant-facing test case documents based on parsed 
implementation scope. It creates documents in multiple formats (HTML, Markdown)
for easy import into Google Docs and other documentation platforms.
"""

import os
import json
import secrets
import string
from datetime import datetime
from typing import Dict, List, Any, Optional
from i18n_helper import I18nHelper
from docx import Document
from docx.shared import Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.oxml.shared import OxmlElement, qn


class TestCaseGenerator:
    def __init__(self, locale: str = 'en'):
        """
        Initialize the test case generator.
        
        Args:
            locale: Language locale for test case descriptions (en, es, pt)
        """
        self.locale = locale
        self.i18n = I18nHelper(default_locale=locale)
    
    def _generate_test_case_salt(self, length: int = 6) -> str:
        """
        Generate a random salt for test case IDs.
        
        Args:
            length: Length of the salt string (default: 6)
            
        Returns:
            Random alphanumeric string of specified length
        """
        alphabet = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
        
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
                        # Use original ID from feature_rules.json with random salt
                        original_id = test_case['id']
                        salt = self._generate_test_case_salt()
                        
                        table_test_case = {
                            'id': f"{original_id}.{salt}",
                            'provider': provider,
                            'payment_method': payment_method,
                            'description': test_case['description'],  # Remove provider + payment method from description
                            'passed': '',  # Empty field for manual completion
                            'date': '',    # Empty field for manual completion
                            'executer': '',  # Empty field for manual completion
                            'evidence': ''   # Empty field for manual completion
                        }
                        all_test_cases.append(table_test_case)
        
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
            "| `ID` | Provider | Payment Method | Description | Passed | Date | Executer | Evidence |",
            "|----|----------|----------------|-------------|--------|------|----------|----------|"
        ])
        
        # Generate table rows
        for test_case in test_cases_data:
            row = f"| `{test_case['id']}` | {test_case['provider']} | {test_case['payment_method']} | {test_case['description']} | {test_case['passed']} | {test_case['date']} | {test_case['executer']} | {test_case['evidence']} |"
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
            '        .id-column { font-family: "Courier New", "Monaco", "Lucida Console", monospace; font-size: 14px; }',
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
            '                <th class="id-column">ID</th>',
            '                <th>Provider</th>',
            '                <th>Payment Method</th>',
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
                f'<td class="id-column">{test_case["id"]}</td>'
                f'<td>{test_case["provider"]}</td>'
                f'<td>{test_case["payment_method"]}</td>'
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
    
    def generate_docx_document(self, parsed_features: Dict[str, Any], 
                             merchant_name: str = "Merchant", 
                             include_metadata: bool = True) -> Document:
        """
        Generate a complete DOCX document with test cases in table format.
        DOCX format provides professional styling and is compatible with Microsoft Word.
        
        Args:
            parsed_features: Dictionary of parsed features from CSV parser
            merchant_name: Name of the merchant for document header
            include_metadata: Whether to include document metadata
            
        Returns:
            python-docx Document object ready for saving
        """
        test_cases_data = self.generate_test_cases_for_features(parsed_features)
        
        # Create a new document
        doc = Document()
        
        # Set page orientation to landscape and adjust margins for better table fit
        section = doc.sections[0]
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = Inches(11)    # Standard letter height becomes width in landscape
        section.page_height = Inches(8.5)  # Standard letter width becomes height in landscape
        
        # Set margins for better table fit
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        
        # Document header
        if include_metadata:
            title = doc.add_heading(f'Test Cases for {merchant_name}', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Metadata paragraph
            metadata_para = doc.add_paragraph()
            metadata_para.add_run(f"Generated on: ").bold = True
            metadata_para.add_run(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            metadata_para.add_run(f"Language: ").bold = True
            metadata_para.add_run(f"{self.locale.upper()}\n")
            metadata_para.add_run(f"Total Test Cases: ").bold = True
            metadata_para.add_run(f"{len(test_cases_data)}")
        else:
            title = doc.add_heading(f'Test Cases for {merchant_name}', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add a line break
        doc.add_paragraph()
        
        # Introduction section
        intro_heading = doc.add_heading('Test Case Documentation', level=1)
        intro_para = doc.add_paragraph(
            'This document contains test cases for your payment integration implementation. '
            'Each test case should be executed to ensure proper functionality of the implemented features.'
        )
        
        # Create table with explicit width settings
        table = doc.add_table(rows=1, cols=8)
        table.style = 'Table Grid'
        
        # Set table to use fixed column widths
        table.autofit = False
        table.allow_autofit = False
        
        # Apply column width settings at XML level
        self._set_table_column_widths(table)
        
        # Header row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'ID'
        hdr_cells[1].text = 'Provider'
        hdr_cells[2].text = 'Payment Method'
        hdr_cells[3].text = 'Description'
        hdr_cells[4].text = 'Passed'
        hdr_cells[5].text = 'Date'
        hdr_cells[6].text = 'Executer'
        hdr_cells[7].text = 'Evidence'
        
        # Format header row with styling
        for i, cell in enumerate(hdr_cells):
            # Set background color to blue
            self._set_cell_background_color(cell, "366092")  # Professional blue (hex: 54, 96, 146)
            
            # Make text bold, white, and centered
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)  # White text
                    run.font.size = Inches(0.11)  # Slightly larger font
                    if i == 0:  # ID column header - apply monospace font
                        run.font.name = 'Courier New'
        
        # Add test case rows with alternating colors
        for i, test_case in enumerate(test_cases_data):
            row_cells = table.add_row().cells
            row_cells[0].text = test_case['id']
            row_cells[1].text = test_case['provider']
            row_cells[2].text = test_case['payment_method']
            row_cells[3].text = test_case['description']
            row_cells[4].text = test_case['passed']
            row_cells[5].text = test_case['date']
            row_cells[6].text = test_case['executer']
            row_cells[7].text = test_case['evidence']
            
            # Add alternating row colors (light gray for even rows)
            if i % 2 == 0:
                for cell in row_cells:
                    self._set_cell_background_color(cell, "F8F9FA")  # Light gray
            
            # Apply monospace font to ID column and center align smaller columns
            for j, cell in enumerate(row_cells):
                if j == 0:  # ID column - apply monospace font
                    for paragraph in cell.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        for run in paragraph.runs:
                            run.font.name = 'Courier New'
                elif j in [4, 5]:  # Passed, Date columns
                    for paragraph in cell.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Set column widths optimized for landscape orientation (total ~9.0")
        # Use table-level column width settings for better reliability
        table.columns[0].width = Inches(0.5)   # ID column (smallest)
        table.columns[1].width = Inches(0.8)   # Provider column (small)
        table.columns[2].width = Inches(1.0)   # Payment Method column (small)
        table.columns[3].width = Inches(4.8)   # Description column (LARGEST - main content)
        table.columns[4].width = Inches(0.6)   # Passed column (small)
        table.columns[5].width = Inches(0.7)   # Date column (small)
        table.columns[6].width = Inches(0.8)   # Executer column (small)
        table.columns[7].width = Inches(1.0)   # Evidence column (small)
        
        # Also set individual cell widths as backup
        for row in table.rows:
            row.cells[0].width = Inches(0.5)   # ID
            row.cells[1].width = Inches(0.8)   # Provider
            row.cells[2].width = Inches(1.0)   # Payment Method
            row.cells[3].width = Inches(4.8)   # Description (LARGEST)
            row.cells[4].width = Inches(0.6)   # Passed
            row.cells[5].width = Inches(0.7)   # Date
            row.cells[6].width = Inches(0.8)   # Executer
            row.cells[7].width = Inches(1.0)   # Evidence
        
        # Summary section
        if include_metadata:
            doc.add_page_break()
            summary_heading = doc.add_heading('Summary', level=1)
            
            summary_para = doc.add_paragraph()
            summary_para.add_run("Total Test Cases: ").bold = True
            summary_para.add_run(f"{len(test_cases_data)}\n")
            summary_para.add_run("Document Language: ").bold = True
            summary_para.add_run(f"{self.locale.upper()}")
            
            # Instructions section
            instructions_heading = doc.add_heading('Instructions', level=2)
            instructions = [
                'Fill in the "Passed" column with Yes/No after executing each test case',
                'Record the execution date in the "Date" column',
                'Add the name of the person who executed the test in the "Executer" column',
                'Provide evidence (screenshots, logs, etc.) in the "Evidence" column'
            ]
            
            for instruction in instructions:
                para = doc.add_paragraph(instruction, style='List Bullet')
            
            # Footer note
            doc.add_paragraph()
            footer_para = doc.add_paragraph()
            footer_run = footer_para.add_run(
                'This document was automatically generated from your implementation scope.'
            )
            footer_run.italic = True
        
        return doc
    
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
    
    def _set_cell_background_color(self, cell, color_hex):
        """Set the background color of a table cell.
        
        Args:
            cell: Table cell object
            color_hex: Hex color string (e.g., "366092" for blue)
        """
        # Create shading element using low-level XML manipulation
        shading_elm = OxmlElement('w:shd')
        shading_elm.set(qn('w:fill'), color_hex)
        cell._tc.get_or_add_tcPr().append(shading_elm)
    
    def _set_table_column_widths(self, table):
        """Force table to use specific column widths by setting XML properties."""
        # Define column widths in twips (1 inch = 1440 twips)
        column_widths = [
            720,   # 0.5 inches - ID
            1152,  # 0.8 inches - Provider
            1440,  # 1.0 inches - Payment Method
            6912,  # 4.8 inches - Description (LARGEST)
            864,   # 0.6 inches - Passed
            1008,  # 0.7 inches - Date
            1152,  # 0.8 inches - Executer
            1440   # 1.0 inches - Evidence
        ]
        
        # Set table properties for fixed layout
        tbl = table._tbl
        tbl_pr = tbl.tblPr
        
        # Set table layout to fixed
        tbl_layout = OxmlElement('w:tblLayout')
        tbl_layout.set(qn('w:type'), 'fixed')
        tbl_pr.append(tbl_layout)
        
        # Set column widths
        tbl_grid = tbl.tblGrid
        for i, width in enumerate(column_widths):
            if i < len(tbl_grid.gridCol_lst):
                tbl_grid.gridCol_lst[i].w = width  # Pass as integer, not string
    
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
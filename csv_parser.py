#!/usr/bin/env python3
"""
Implementation Scoping Document Parser

This program parses implementation scoping documents (provided by BDM teams during 
merchant handover) containing provider and payment method information. It extracts 
implementation features only for valid combinations (where provider and payment method
are not "#N/A" or empty). The parsed data is structured for later documentation generation.
"""

import csv
import sys
from typing import Dict, List, Tuple, Any, Optional
import argparse
from rules_manager import RulesManager


class ProviderPaymentParser:
    def __init__(self, csv_file_path: str, verbose: bool = True, rules_file_path: str = 'feature_rules.json', rules_file_paths: Optional[List[str]] = None):
        self.csv_file_path = csv_file_path
        self.verbose = verbose
        self.data = []
        self.valid_columns = []
        self.parsed_features = {}
        # Use multiple files if provided, otherwise use single file (backward compatibility)
        if rules_file_paths:
            self.rules_manager = RulesManager(verbose=verbose, rules_file_paths=rules_file_paths)
        else:
            self.rules_manager = RulesManager(rules_file_path, verbose=verbose)
        self.rules_manager.load_rules()
        
    def load_csv(self) -> None:
        """Load CSV data from file."""
        try:
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                self.data = list(reader)
            if self.verbose:
                print(f"✓ Successfully loaded CSV with {len(self.data)} rows")
        except FileNotFoundError:
            if self.verbose:
                print(f"✗ Error: File '{self.csv_file_path}' not found")
            raise FileNotFoundError(f"File '{self.csv_file_path}' not found")
        except Exception as e:
            if self.verbose:
                print(f"✗ Error loading CSV: {e}")
            raise Exception(f"Error loading CSV: {e}")
    
    def identify_valid_columns(self) -> None:
        """
        Identify valid columns based on provider and payment method.
        Valid columns have:
        - Provider (row 2) that is not "#N/A" and not empty
        - Payment_Method (row 3) that is not "#N/A" and not empty
        """
        if len(self.data) < 3:
            if self.verbose:
                print("✗ Error: CSV must have at least 3 rows (feature names, providers, payment methods)")
            return
        
        provider_row = self.data[1]  # Row with provider names
        payment_method_row = self.data[2]  # Row with payment methods
        
        self.valid_columns = []
        
        for col_idx in range(len(provider_row)):
            if col_idx < len(payment_method_row):
                provider = provider_row[col_idx].strip()
                payment_method = payment_method_row[col_idx].strip()
                
                # Check if this is a valid combination
                # Exclude header columns that contain generic labels
                if (provider and provider != "#N/A" and provider != "Provider" and
                    payment_method and payment_method != "#N/A" and payment_method != "Payment_Method"):
                    
                    self.valid_columns.append({
                        'column_index': col_idx,
                        'provider': provider,
                        'payment_method': payment_method
                    })
        
        if self.verbose:
            print(f"✓ Found {len(self.valid_columns)} valid provider + payment method combinations:")
            for i, col in enumerate(self.valid_columns, 1):
                print(f"  {i}. Provider: {col['provider']}, Payment Method: {col['payment_method']} (Column {col['column_index']})")
    
    def extract_features(self) -> None:
        """Extract all features for valid columns."""
        if not self.valid_columns:
            if self.verbose:
                print("✗ No valid columns found")
            return
        
        self.parsed_features = {}
        found_features = set()  # Track all unique features found
        
        # Start from row 5 (index 4) since rows 0-3 are headers
        feature_start_row = 4
        if len(self.data) <= feature_start_row:
            if self.verbose:
                print("✗ No feature data found in CSV")
            return
        
        if self.verbose:
            print(f"\n🔍 DEBUG: Starting feature extraction from row {feature_start_row + 1}...")
        
        for col_info in self.valid_columns:
            col_idx = col_info['column_index']
            provider = col_info['provider']
            payment_method = col_info['payment_method']
            
            key = f"{provider}_{payment_method}"
            self.parsed_features[key] = {
                'provider': provider,
                'payment_method': payment_method,
                'features': {}
            }
            
            if self.verbose:
                print(f"🔍 DEBUG: Processing {provider}_{payment_method} (column {col_idx})...")
            
            # Extract features starting from row 4
            extracted_count = 0
            for row_idx in range(feature_start_row, len(self.data)):
                row = self.data[row_idx]
                
                if len(row) > 1 and row[1]:  # Feature name exists in column 1
                    feature_name = row[1].strip()
                    if feature_name:  # Skip empty feature names
                        # Get the value for this column (handle missing columns)
                        feature_value = ""
                        if col_idx < len(row):
                            feature_value = row[col_idx].strip()
                        
                        self.parsed_features[key]['features'][feature_name] = feature_value
                        found_features.add(feature_name)
                        extracted_count += 1
                        
                        if self.verbose:
                            # Check if feature has a rule
                            has_rule = self.rules_manager.has_rule(feature_name)
                            rule_indicator = "✓" if has_rule else "✗"
                            print(f"  {rule_indicator} Feature: {feature_name} = '{feature_value}' (Rule: {'Found' if has_rule else 'Missing'})")
            
            if self.verbose:
                print(f"  📊 Extracted {extracted_count} features for {provider}_{payment_method}")
        
        if self.verbose:
            print(f"\n📋 DEBUG: Implementation Scope Parse Summary")
            print(f"✓ Total unique features found: {len(found_features)}")
            print(f"✓ Features with rules: {sum(1 for f in found_features if self.rules_manager.has_rule(f))}")
            print(f"✗ Features without rules: {sum(1 for f in found_features if not self.rules_manager.has_rule(f))}")
            
            # Show features without rules
            missing_rules = [f for f in found_features if not self.rules_manager.has_rule(f)]
            if missing_rules:
                print(f"\n⚠️  Features without rules in feature_rules.json:")
                for feature in sorted(missing_rules):
                    print(f"  - {feature}")
            
            # Show features with rules
            with_rules = [f for f in found_features if self.rules_manager.has_rule(f)]
            if with_rules:
                print(f"\n✅ Features with rules in feature_rules.json:")
                for feature in sorted(with_rules):
                    rule = self.rules_manager.get_rule(feature)
                    print(f"  - {feature} -> {rule.documentation_url}")
            
            print(f"\n✓ Extracted features for {len(self.parsed_features)} valid combinations")
    
    def display_results(self, show_enriched: bool = False) -> None:
        """Display the parsed results in a readable format."""
        if not self.parsed_features:
            if self.verbose:
                print("✗ No features to display")
            return
        
        print("\n" + "="*80)
        if show_enriched:
            print("PARSED PROVIDER + PAYMENT METHOD FEATURES (with Documentation)")
        else:
            print("PARSED PROVIDER + PAYMENT METHOD FEATURES")
        print("="*80)
        
        if show_enriched:
            enriched_data = self.export_enriched_dict()
            for key, data in enriched_data.items():
                print(f"\n📋 {data['provider']} + {data['payment_method']}")
                print("-" * 50)
                
                for feature_name, feature_data in data['features'].items():
                    if feature_data.get('value', feature_data.get('feature_value', '')):  # Only show features with values
                        print(f"  • {feature_data['name']}: {feature_data['value']}")
                        if feature_data['has_rule']:
                            print(f"    📚 Documentation: {feature_data['documentation_url']}")
                            print(f"    💬 Comment: {feature_data['comment']}")
                    else:
                        print(f"  • {feature_data['name']}: [empty]")
                        if feature_data['has_rule']:
                            print(f"    📚 Documentation: {feature_data['documentation_url']}")
        else:
            for key, data in self.parsed_features.items():
                print(f"\n📋 {data['provider']} + {data['payment_method']}")
                print("-" * 50)
                
                for feature_name, feature_value in data['features'].items():
                    if feature_value:  # Only show features with values
                        print(f"  • {feature_name}: {feature_value}")
                    else:
                        print(f"  • {feature_name}: [empty]")
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export parsed data as a dictionary for programmatic use."""
        return self.parsed_features
    
    def export_enriched_dict(self) -> Dict[str, Any]:
        """Export parsed data enriched with documentation URLs and comments."""
        enriched_data = {}
        
        for key, data in self.parsed_features.items():
            enriched_data[key] = {
                'provider': data['provider'],
                'payment_method': data['payment_method'],
                'features': {}
            }
            
            # Enrich each feature with rules data (include provider for provider-specific steps)
            for feature_name, feature_value in data['features'].items():
                enriched_data[key]['features'][feature_name] = self.rules_manager.enrich_feature_data(
                    feature_name, feature_value, provider=data['provider']
                )
        
        return enriched_data
    
    def parse(self) -> Dict[str, Any]:
        """Main parsing method that executes the full pipeline."""
        if self.verbose:
            print("🔄 Starting CSV parsing...")
        self.load_csv()
        self.identify_valid_columns()
        self.extract_features()
        return self.export_to_dict()


def main():
    parser = argparse.ArgumentParser(
        description="Parse CSV files to extract provider + payment method features"
    )
    parser.add_argument(
        "csv_file", 
        help="Path to the CSV file to parse"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output the results, suppress progress messages"
    )
    parser.add_argument(
        "--enriched", "-e",
        action="store_true",
        help="Show enriched results with documentation URLs and comments"
    )
    parser.add_argument(
        "--rules-file", "-r",
        default="feature_rules.json",
        help="Path to the feature rules JSON file"
    )
    
    args = parser.parse_args()
    
    # Create parser instance
    csv_parser = ProviderPaymentParser(args.csv_file, verbose=not args.quiet, rules_file_path=args.rules_file)
    
    # Parse the CSV
    try:
        parsed_data = csv_parser.parse()
        
        if not args.quiet:
            csv_parser.display_results(show_enriched=args.enriched)
        else:
            # In quiet mode, just output the essential results
            if args.enriched:
                enriched_data = csv_parser.export_enriched_dict()
                for key, data in enriched_data.items():
                    print(f"{data['provider']} + {data['payment_method']}:")
                    for feature_name, feature_data in data['features'].items():
                        if feature_data['value']:
                            print(f"  {feature_data['name']}: {feature_data['value']}")
                            if feature_data['has_rule']:
                                print(f"    📚 {feature_data['documentation_url']}")
                    print()
            else:
                for key, data in parsed_data.items():
                    print(f"{data['provider']} + {data['payment_method']}:")
                    for feature, value in data['features'].items():
                        if value:
                            print(f"  {feature}: {value}")
                    print()
        
    except Exception as e:
        print(f"✗ Error during parsing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
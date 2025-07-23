#!/usr/bin/env python3
"""
Example usage of the CSV Parser for Provider Payment Method Features
"""

from csv_parser import ProviderPaymentParser

def main():
    # Example 1: Basic usage
    print("=== Example 1: Basic Usage ===")
    parser = ProviderPaymentParser('sample_integrations.csv')
    
    # Parse the CSV
    results = parser.parse()
    
    # Display results
    parser.display_results()
    
    print("\n" + "="*60)
    print("=== Example 2: Programmatic Access ===")
    
    # Access results programmatically
    for key, data in results.items():
        provider = data['provider']
        payment_method = data['payment_method']
        features = data['features']
        
        print(f"\n🔹 {provider} + {payment_method}")
        print(f"   Total features: {len(features)}")
        
        # Show only features with TRUE/Implemented values
        implemented_features = [
            feature for feature, value in features.items() 
            if value in ['TRUE', 'Implemented']
        ]
        
        print(f"   Implemented features ({len(implemented_features)}):")
        for feature in implemented_features[:5]:  # Show first 5
            print(f"     ✓ {feature}")
        
        if len(implemented_features) > 5:
            print(f"     ... and {len(implemented_features) - 5} more")
    
    print("\n" + "="*60)
    print("=== Example 3: Feature Comparison ===")
    
    # Compare features between providers
    if len(results) >= 2:
        keys = list(results.keys())
        provider1_data = results[keys[0]]
        provider2_data = results[keys[1]]
        
        print(f"\nComparing {provider1_data['provider']} vs {provider2_data['provider']}:")
        
        # Find common features
        common_features = set(provider1_data['features'].keys()) & set(provider2_data['features'].keys())
        
        # Compare values
        differences = []
        for feature in common_features:
            val1 = provider1_data['features'][feature]
            val2 = provider2_data['features'][feature]
            if val1 != val2:
                differences.append((feature, val1, val2))
        
        print(f"   Features with different values: {len(differences)}")
        for feature, val1, val2 in differences[:5]:  # Show first 5 differences
            print(f"     {feature}: {provider1_data['provider']}='{val1}' vs {provider2_data['provider']}='{val2}'")
        
        if len(differences) > 5:
            print(f"     ... and {len(differences) - 5} more differences")

if __name__ == "__main__":
    main() 
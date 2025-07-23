# Feature Rules System Documentation

## Overview

The Feature Rules System allows you to dynamically manage feature documentation URLs and comments without requiring code changes. This system enhances the Implementation Scoping Document Parser by providing rich context and documentation links for each feature extracted from CSV files.

## Key Benefits

- **Dynamic Configuration**: Update documentation URLs and comments without code modifications
- **Rich Documentation**: Provide contextual information and links for each feature
- **Backward Compatibility**: Existing functionality remains unchanged
- **Scalable**: Easily add new features or update existing ones

## System Components

### 1. Rules File (`feature_rules.json`)

A JSON file containing feature documentation rules with the following structure:

```json
{
  "version": "1.0",
  "description": "Feature documentation rules for dynamic documentation generation",
  "last_updated": "2024-01-01",
  "rules": {
    "FeatureName": {
      "feature_name": "FeatureName",
      "documentation_url": "https://docs.company.com/feature",
      "comment": "Detailed description of the feature and its purpose"
    }
  },
  "metadata": {
    "total_rules": 16,
    "categories": ["Payment Processing", "Security & Compliance"],
    "usage_instructions": "Update URLs and comments as needed without code changes"
  }
}
```

### 2. Rules Manager (`rules_manager.py`)

The core class that manages loading, validating, and applying feature rules:

```python
from rules_manager import RulesManager

# Initialize with custom rules file
rules_manager = RulesManager('custom_rules.json')
rules_manager.load_rules()

# Get documentation URL for a feature
url = rules_manager.get_documentation_url('Country')
comment = rules_manager.get_comment('Country')

# Enrich feature data
enriched = rules_manager.enrich_feature_data('Country', 'Brazil')
```

### 3. Enhanced CSV Parser

The CSV parser now integrates with the rules system to provide enriched output:

```python
from csv_parser import ProviderPaymentParser

# Initialize with rules file
parser = ProviderPaymentParser('data.csv', rules_file_path='feature_rules.json')
results = parser.parse()

# Get enriched data with documentation URLs and comments
enriched_data = parser.export_enriched_dict()
```

## Usage Examples

### Command Line Interface

```bash
# Basic parsing with enriched output
python3 csv_parser.py data.csv --enriched

# Use custom rules file
python3 csv_parser.py data.csv --enriched --rules-file custom_rules.json

# Quiet mode with enriched data
python3 csv_parser.py data.csv --enriched --quiet
```

### Web Interface

The web interface automatically displays enriched data with:
- **Documentation Links**: Direct links to feature documentation
- **Contextual Comments**: Detailed explanations of each feature
- **Interactive UI**: Expandable comments and visual indicators

### Programmatic Usage

```python
from csv_parser import ProviderPaymentParser

# Parse with rules
parser = ProviderPaymentParser('implementation_scope.csv')
parser.parse()

# Get enriched data
enriched_data = parser.export_enriched_dict()

for provider_key, provider_data in enriched_data.items():
    print(f"Provider: {provider_data['provider']}")
    
    for feature_name, feature_data in provider_data['features'].items():
        if feature_data['has_rule']:
            print(f"  Feature: {feature_data['name']}")
            print(f"  Value: {feature_data['value']}")
            print(f"  Documentation: {feature_data['documentation_url']}")
            print(f"  Comment: {feature_data['comment']}")
```

## Data Structure

### Enriched Feature Data

Each feature in the enriched output contains:

```python
{
    'name': 'Country',
    'value': 'Brazil',
    'has_value': True,
    'documentation_url': 'https://docs.company.com/integration/country-support',
    'comment': 'Specifies the country where this provider + payment method combination is available.',
    'has_rule': True
}
```

### Field Descriptions

- **name**: The feature name as it appears in the CSV
- **value**: The feature value from the CSV
- **has_value**: Boolean indicating if the feature has a non-empty value
- **documentation_url**: URL to feature documentation (null if no rule exists)
- **comment**: Explanatory comment about the feature (null if no rule exists)
- **has_rule**: Boolean indicating if a rule exists for this feature

## Available Features (Default Rules)

The system comes with pre-configured rules for common payment integration features:

### Payment Processing
- **Country**: Geographic availability
- **Currency**: Supported currencies
- **Recurring**: Subscription payments
- **Installments**: Split payments

### Security & Compliance
- **Verify**: Payment verification
- **3DS**: 3D Secure authentication
- **TokenVault**: Secure token storage
- **Chargeback**: Dispute management

### Customer Experience
- **Authorize**: Payment authorization
- **Capture**: Payment capture
- **Cancel**: Payment cancellation
- **Refund**: Payment refunds
- **PaymentLink**: Shareable payment links

### Development & Testing
- **Sandbox**: Testing environment
- **Webhook**: Real-time notifications
- **Split**: Multi-recipient payments

## Customization

### Adding New Rules

1. Edit `feature_rules.json`
2. Add a new feature entry:

```json
{
  "NewFeature": {
    "feature_name": "NewFeature",
    "documentation_url": "https://docs.company.com/new-feature",
    "comment": "Description of the new feature"
  }
}
```

3. The system automatically picks up the new rule

### Updating Existing Rules

Simply modify the JSON file - no code changes required:

```json
{
  "Country": {
    "feature_name": "Country",
    "documentation_url": "https://updated-docs.company.com/country",
    "comment": "Updated description with new information"
  }
}
```

### Creating Custom Rules Files

You can create multiple rules files for different contexts:

```bash
# Use different rules for different clients
python3 csv_parser.py client_a.csv --rules-file rules_client_a.json
python3 csv_parser.py client_b.csv --rules-file rules_client_b.json
```

## Validation

### Rules File Validation

The system includes built-in validation:

```python
from rules_manager import RulesManager

rules_manager = RulesManager('rules.json')
validation = rules_manager.validate_rules_file()

if validation['is_valid']:
    print("Rules file is valid")
else:
    print("Errors:", validation['errors'])
    print("Warnings:", validation['warnings'])
```

### Required Fields

Each rule must contain:
- `feature_name`: The exact feature name
- `documentation_url`: A valid URL (can be empty but must be present)
- `comment`: Descriptive text (can be empty but must be present)

## Integration with Existing Code

The rules system is designed to be non-intrusive:

1. **Existing functionality remains unchanged**: All current CSV parsing works as before
2. **Optional enhancement**: Rules are only applied when requested
3. **Graceful degradation**: Missing rules files don't break functionality
4. **Backward compatibility**: Old code continues to work without modification

## Performance Considerations

- Rules are loaded once at initialization
- Enrichment is performed on-demand
- Memory usage scales linearly with the number of rules
- File I/O is minimized through caching

## Error Handling

The system handles various error conditions gracefully:

- **Missing rules file**: Continues with empty rules set
- **Invalid JSON**: Logs error and uses empty rules
- **Missing required fields**: Skips invalid rules, continues with valid ones
- **Network issues**: No impact as URLs are only used for display

## Future Extensions

The rules system is designed for extensibility:

- **Multiple rule sources**: Database, API, etc.
- **Rule inheritance**: Base rules with overrides
- **Conditional rules**: Rules based on provider/context
- **Automated validation**: CI/CD integration for rule validation
- **Rule templates**: Standardized rule creation

## Best Practices

1. **Version your rules files** using the version field
2. **Use descriptive comments** that provide real value
3. **Keep URLs current** and test them regularly
4. **Use consistent naming** for feature names
5. **Document your customizations** for team members
6. **Test rules changes** before deploying
7. **Backup rules files** before major changes

## Troubleshooting

### Common Issues

**Rules not loading**:
- Check file path and permissions
- Validate JSON syntax
- Verify required fields are present

**Missing enrichment**:
- Ensure feature names match exactly (case-sensitive)
- Check that rules file is being loaded
- Verify `has_rule` field in output

**Performance issues**:
- Large rules files can impact startup time
- Consider splitting rules files by context
- Use `verbose=False` for production

### Debug Commands

```bash
# Test rules manager standalone
python3 rules_manager.py

# Validate specific rules file
python3 -c "from rules_manager import RulesManager; rm = RulesManager('rules.json'); print(rm.validate_rules_file())"

# Check what rules are loaded
python3 -c "from rules_manager import RulesManager; rm = RulesManager(); rm.load_rules(); print(rm.get_all_features())"
``` 
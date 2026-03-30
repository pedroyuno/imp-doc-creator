# Implementation Scoping Document Parser

This Python program parses implementation scoping documents (provided by BDM teams during merchant handover) containing provider and payment method integration information. It extracts features only for valid combinations where both the provider and payment method are properly defined (not "#N/A" or empty). The parsed data is then used to generate comprehensive test case documentation for merchant validation.

> **Claude Code Skill:** This project is also available as a `/imp-doc-creator` Claude Code skill that generates integration documentation (MD + PDF) directly from the terminal. See the [Confluence documentation](https://yunopayments.atlassian.net/wiki/spaces/IB/pages/1913028632/Implementation+Generator+Document) for usage instructions.

## How it Works

The program analyzes implementation scoping documents (CSV format) with the following structure:
- **Row 1**: Feature column names (e.g., "REDE_CARD", "PAGARME_CARD")
- **Row 2**: Provider names (e.g., "REDE", "PAGARME", "#N/A")
- **Row 3**: Payment methods (e.g., "CARD", "CARD", "#N/A")
- **Row 4+**: Feature names and their corresponding values for each provider+payment method combination

## Valid Columns

A column is considered valid if:
- The provider (row 2) is **not** "#N/A" and **not** empty
- The payment method (row 3) is **not** "#N/A" and **not** empty

## Features

### Core Functionality
- ✅ Automatically identifies valid provider + payment method combinations from BDM handover documents
- ✅ Extracts implementation features for valid combinations
- ✅ **Generates comprehensive test case documentation** for merchant validation
- ✅ **Environment-specific test case generation** (sandbox, production, or separated tables)
- ✅ **Multiple document formats** (HTML, DOCX, Markdown) with professional styling
- ✅ **Multilingual support** (English, Spanish, Portuguese)
- ✅ Handles missing data gracefully
- ✅ Provides both CLI and programmatic interfaces
- ✅ Clean, readable output formatting optimized for documentation generation
- ✅ Error handling for malformed implementation documents

### Test Case Generation
- 📝 **Separated Tables**: Creates distinct sandbox and production test case tables (default)
- 🎯 **Environment Filtering**: Generate test cases for specific environments
- 🎨 **Professional Styling**: Color-coded headers (orange for sandbox, red for production)
- 📋 **Comprehensive Coverage**: Happy path, unhappy path, and corner case scenarios
- 🌍 **Multilingual**: Test case descriptions in English, Spanish, and Portuguese
- 📄 **Multiple Formats**: HTML (Google Docs compatible), DOCX (Word), and Markdown
- 📊 **Summary Statistics**: Detailed test case distribution and coverage metrics
- 🔗 **Integration Documentation**: Links to relevant API documentation for each feature

### Web Interface
- 🖱️ Drag & drop implementation document upload
- 📊 Beautiful implementation results visualization
- 📝 **Interactive test case generation** with environment selection
- 👁️ **Test case preview** before document generation
- 🔍 Filter and search implementation features
- 📥 Export parsed data as JSON for documentation generation
- 📱 Mobile responsive design
- 📖 Interactive document format guide
- 🌐 RESTful API endpoints
- ⚙️ **Interactive Feature Rules Management** with inline editing
- 🌍 **Real-time language switching** (English, Spanish, Portuguese)
- ✏️ **Inline test case description editing** with save/cancel controls
- 🎯 **Payment method-specific test case organization**
- 📁 **Multiple Feature Rules Files**: Create and manage separate feature rules files for different teams/regions (e.g., APAC, EMEA)
- ✏️ **Integration Steps Editing**: Edit documentation URLs and descriptions for integration steps
- 🔄 **Auto-reload Development Server**: Automatic server reload on code changes (no manual restart needed)

### Testing & Quality
- 🧪 **84% code coverage** with comprehensive test suite
- ✅ **184+ comprehensive test cases** (including new API endpoint tests for integration steps and rules files)
- 🔄 Unit, integration, and regression tests
- 🛡️ Security and error handling tests
- 📋 Automated test runner scripts
- 🆕 **API endpoint testing** for feature rules management 

## Usage

### Web Interface (Recommended)

```bash
# Start the web application (handles virtual environment automatically)
./run_web.sh

# Open your browser to: http://localhost:5001
```

**Web Features:**
- 🖱️ Drag & drop document upload (CSV format)
- 📊 Beautiful implementation results visualization
- 📝 **Generate test case documents** with environment selection
- 👁️ **Preview test cases** before downloading
- 🎯 **Environment options**: Separated tables (default), sandbox only, or production only
- 📄 **Multiple formats**: HTML (Google Docs), DOCX (Word), Markdown
- 🌍 **Language support**: English, Spanish, Portuguese
- 🔍 Filter and search implementation features
- 📥 Export parsed data as JSON for documentation generation
- 📱 Mobile responsive design
- 📖 Interactive document format guide
- ⚙️ **Feature Rules Management**: Interactive editing of feature rules and test cases
- ✏️ **Inline Editing**: Edit test case descriptions directly with save/cancel controls
- 🌍 **Real-time Language Switching**: Switch between languages without page reload
- 📁 **Multiple Rules Files**: Create and switch between different feature rules files (e.g., feature_rules_APAC.json)
- 🔗 **Integration Steps Management**: Edit documentation URLs and descriptions for each feature's integration steps
- 🔄 **Auto-reload**: Development server automatically reloads on code changes

### Command Line Interface

```bash
# Basic usage
python csv_parser.py path/to/your/implementation_scoping_document.csv

# Quiet mode (only show results)
python csv_parser.py path/to/your/implementation_scoping_document.csv --quiet
```

### Programmatic Usage

```python
from csv_parser import ProviderPaymentParser
from test_case_generator import TestCaseGenerator

# Create parser instance for implementation scoping document
parser = ProviderPaymentParser('implementation_scoping_document.csv')

# Parse the implementation document and get results
results = parser.parse()

# Display results
parser.display_results()

# Generate test case documentation
generator = TestCaseGenerator(locale='en')

# Generate separated tables (default)
html_doc = generator.generate_html_document(
    results, 
    merchant_name="Your Merchant",
    environment='separated'
)

# Generate environment-specific test cases
sandbox_cases = generator.generate_test_cases_for_features(results, 'sandbox')
production_cases = generator.generate_test_cases_for_features(results, 'production')

# Access parsed data programmatically
for key, data in results.items():
    provider = data['provider']
    payment_method = data['payment_method']
    features = data['features']
    
    print(f"Provider: {provider}, Payment Method: {payment_method}")
    for feature_name, feature_value in features.items():
        print(f"  {feature_name}: {feature_value}")
```

## Testing

### Running Tests

```bash
# Run all tests with coverage report
./run_tests.sh

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests only
pytest -m web                     # Web interface tests
pytest -m api                     # API endpoint tests

# Run specific test files
pytest tests/test_csv_parser.py       # Implementation document parser tests
pytest tests/test_test_case_generator.py  # Test case generator tests
pytest tests/test_web_app.py          # Web application tests
pytest tests/test_integration.py      # End-to-end tests

# Generate detailed coverage report
pytest --cov=. --cov-report=html
# View: open htmlcov/index.html
```

### Test Coverage

Our test suite achieves **84% code coverage** with comprehensive testing:

- **Unit Tests**: Core implementation document parsing and test case generation
- **Web Tests**: Flask routes, document uploads, and API endpoints  
- **Integration Tests**: End-to-end implementation workflows
- **Coverage Boost Tests**: Edge cases and error handling

### Test Categories

| Category | Purpose | Test Count |
|----------|---------|------------|
| **Unit** | Core functionality testing | 50+ |
| **Web** | Web interface testing | 30+ |
| **API** | RESTful API testing | 15+ |
| **Integration** | End-to-end workflows | 15+ |
| **Security** | File upload security | 5+ |
| **Error Handling** | Edge cases & errors | 20+ |
| **Test Case Generation** | Document generation testing | 14+ |
| **Feature Rules** | Feature rules management testing | 22+ |

## Example Output

### CSV Parsing
For a CSV with REDE+CARD and PAGARME+CARD combinations, the program will output:

```
🔄 Starting CSV parsing...
✓ Successfully loaded CSV with 33 rows
✓ Found 2 valid provider + payment method combinations:
  1. Provider: REDE, Payment Method: CARD (Column 2)
  2. Provider: PAGARME, Payment Method: CARD (Column 5)
✓ Extracted features for 2 valid combinations

================================================================================
PARSED PROVIDER + PAYMENT METHOD FEATURES
================================================================================

📋 REDE + CARD
--------------------------------------------------
  • Country: Brazil
  • Verify: TRUE
  • Authorize: TRUE
  • Capture: TRUE
  • Refund: TRUE
  • Currency: BRL
  • Sandbox: TRUE
  ...
```

### Test Case Generation
The system automatically generates comprehensive test case documentation:

- **Separated Tables** (default): Distinct sandbox and production sections
- **Environment-Specific**: Filter by sandbox or production
- **Professional Styling**: Color-coded headers and responsive design
- **Multiple Formats**: HTML, DOCX, and Markdown output
- **Multilingual**: Support for English, Spanish, and Portuguese

## Requirements

- Python 3.6+
- Virtual environment (recommended)
- Flask 2.3.3+ (for web interface)
- python-docx (for DOCX generation)

## Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Run the setup script (creates virtual environment and installs dependencies)
./setup.sh

# Start the web application (automatically activates virtual environment)
./run_web.sh
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python3 -m venv csv_parser_env

# Activate virtual environment
source csv_parser_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start web application (if not using run_web.sh)
python web_app.py

# Or use command line tool
python csv_parser.py your_file.csv
```

### Deactivating Virtual Environment
```bash
deactivate
``` 
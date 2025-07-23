# CSV Parser for Provider Payment Method Features

This Python program parses CSV files containing provider and payment method integration information, extracting features only for valid combinations where both the provider and payment method are properly defined (not "#N/A" or empty).

## How it Works

The program analyzes CSV files with the following structure:
- **Row 1**: Feature column names (e.g., "REDE_CARD", "PAGARME_CARD")
- **Row 2**: Provider names (e.g., "REDE", "PAGARME", "#N/A")
- **Row 3**: Payment methods (e.g., "CARD", "CARD", "#N/A")
- **Row 4+**: Feature names and their corresponding values for each provider+payment method combination

## Valid Columns

A column is considered valid if:
- The provider (row 2) is **not** "#N/A" and **not** empty
- The payment method (row 3) is **not** "#N/A" and **not** empty

## Usage

### Web Interface (Recommended)

```bash
# Start the web application (handles virtual environment automatically)
./run_web.sh

# Open your browser to: http://localhost:5001
```

**Web Features:**
- 🖱️ Drag & drop CSV file upload
- 📊 Beautiful results visualization
- 🔍 Filter and search features
- 📥 Export results as JSON
- 📱 Mobile responsive design
- 📖 Interactive format documentation

### Command Line Interface

```bash
# Basic usage
python csv_parser.py path/to/your/file.csv

# Quiet mode (only show results)
python csv_parser.py path/to/your/file.csv --quiet
```

### Programmatic Usage

```python
from csv_parser import ProviderPaymentParser

# Create parser instance
parser = ProviderPaymentParser('your_file.csv')

# Parse the CSV and get results
results = parser.parse()

# Display results
parser.display_results()

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
pytest tests/test_csv_parser.py    # CSV parser tests
pytest tests/test_web_app.py       # Web application tests
pytest tests/test_integration.py   # End-to-end tests

# Generate detailed coverage report
pytest --cov=csv_parser --cov=web_app --cov-report=html
# View: open htmlcov/index.html
```

### Test Coverage

Our test suite achieves **97% code coverage** with comprehensive testing:

- **Unit Tests**: 27 tests covering core CSV parsing functionality
- **Web Tests**: 28 tests for Flask routes, file uploads, and API endpoints
- **Integration Tests**: 11 tests for end-to-end workflows
- **Coverage Boost Tests**: 13 tests for edge cases and error handling
- **Setup Tests**: 4 tests for environment verification

### Test Categories

| Category | Purpose | Test Count |
|----------|---------|------------|
| **Unit** | Core functionality testing | 27 |
| **Web** | Web interface testing | 28 |
| **API** | RESTful API testing | 8 |
| **Integration** | End-to-end workflows | 11 |
| **Security** | File upload security | 5 |
| **Error Handling** | Edge cases & errors | 15 |

### Coverage Breakdown

- **csv_parser.py**: 99% coverage (116/117 statements)
- **web_app.py**: 95% coverage (86/91 statements)
- **Total**: 97% coverage (202/208 statements)

## Example Output

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
  • Signed contract with provider: TRUE
  • Already integrated with Yuno?: TRUE
  • Experience: SDK Yuno
  • Card Type Accepted: Credit
  • Verify: TRUE
  • Authorize: TRUE
  • Capture: TRUE
  • Purchase: TRUE
  • Refund: TRUE
  • Cancel: TRUE
  • Partial Capture: FALSE
  ...
```

## Requirements

- Python 3.6+
- Virtual environment (recommended)
- Flask 2.3.3+ (for web interface)

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

## Features

### Core Functionality
- ✅ Automatically identifies valid provider + payment method combinations
- ✅ Extracts all features for valid combinations
- ✅ Handles missing data gracefully
- ✅ Provides both CLI and programmatic interfaces
- ✅ Clean, readable output formatting
- ✅ Error handling for malformed CSV files

### Web Interface
- 🖱️ Drag & drop CSV file upload
- 📊 Beautiful results visualization
- 🔍 Filter and search features
- 📥 Export results as JSON
- 📱 Mobile responsive design
- 📖 Interactive format documentation
- 🌐 RESTful API endpoints

### Testing & Quality
- 🧪 **97% code coverage** (exceeds 90% requirement)
- ✅ **81 comprehensive test cases**
- 🔄 Unit, integration, and regression tests
- 🛡️ Security and error handling tests
- 📋 Automated test runner scripts 
#!/bin/bash
# Test runner script for CSV Parser application

echo "🧪 CSV Parser Test Suite"
echo "========================"

# Check if virtual environment exists
if [ ! -d "csv_parser_env" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source csv_parser_env/bin/activate

# Install test dependencies if not already installed
echo "📦 Installing/updating test dependencies..."
pip install -r requirements.txt

# Clear previous coverage data
echo "🧹 Clearing previous coverage data..."
coverage erase 2>/dev/null || true

# Run tests with coverage
echo "🚀 Running test suite..."
echo ""

# Run all tests
pytest

# Check exit code
test_exit_code=$?

echo ""
echo "========================"

if [ $test_exit_code -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "📊 Coverage report generated in htmlcov/index.html"
    echo "📈 To view coverage report, open: htmlcov/index.html"
else
    echo "❌ Some tests failed (exit code: $test_exit_code)"
    echo "📋 Check the output above for details"
fi

echo ""
echo "Test commands you can use:"
echo "  pytest tests/test_csv_parser.py    # Run only CSV parser tests"
echo "  pytest tests/test_web_app.py       # Run only web app tests"
echo "  pytest tests/test_integration.py   # Run only integration tests"
echo "  pytest -k test_upload              # Run tests matching pattern"
echo "  pytest -m unit                     # Run only unit tests"
echo "  pytest -m integration              # Run only integration tests"
echo "  pytest --cov-report=html           # Generate HTML coverage report"

exit $test_exit_code 
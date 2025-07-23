#!/bin/bash
# Run script for CSV Parser Web Application

echo "🚀 Starting CSV Parser Web Application..."

# Check if virtual environment exists
if [ ! -d "csv_parser_env" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source csv_parser_env/bin/activate

# Start the web application
echo "🌐 Starting web server at http://localhost:5001"
echo "📊 Open your browser and go to: http://localhost:5001"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

python web_app.py 
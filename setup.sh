#!/bin/bash
# Setup script for CSV Parser Web Application

echo "🔧 Setting up CSV Parser environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "csv_parser_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv csv_parser_env
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source csv_parser_env/bin/activate

# Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To activate the environment manually, run:"
echo "  source csv_parser_env/bin/activate"
echo ""
echo "To start the web application, run:"
echo "  python web_app.py"
echo ""
echo "To use the command line tool, run:"
echo "  python csv_parser.py your_file.csv" 
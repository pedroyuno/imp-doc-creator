#!/usr/bin/env python3
"""
Test script to verify CSV Parser setup
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import csv
        print("  ✅ csv module")
    except ImportError as e:
        print(f"  ❌ csv module: {e}")
        return False
    
    try:
        from csv_parser import ProviderPaymentParser
        print("  ✅ csv_parser module")
    except ImportError as e:
        print(f"  ❌ csv_parser module: {e}")
        return False
    
    try:
        import flask
        print(f"  ✅ Flask {flask.__version__}")
    except ImportError as e:
        print(f"  ❌ Flask: {e}")
        return False
    
    try:
        from web_app import app
        print("  ✅ web_app module")
    except ImportError as e:
        print(f"  ❌ web_app module: {e}")
        return False

def test_csv_parser():
    """Test the CSV parser with sample data."""
    print("\n📊 Testing CSV parser...")
    
    try:
        from csv_parser import ProviderPaymentParser
        
        if not os.path.exists('sample_integrations.csv'):
            print("  ❌ Sample CSV file not found")
            return False
        
        parser = ProviderPaymentParser('sample_integrations.csv', verbose=False)
        results = parser.parse()
        
        if results:
            print(f"  ✅ Parsed {len(results)} valid combinations")
            for key, data in results.items():
                provider = data['provider']
                payment_method = data['payment_method']
                feature_count = len(data['features'])
                print(f"    • {provider} + {payment_method}: {feature_count} features")
            return True
        else:
            print("  ❌ No results parsed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_flask_app():
    """Test that Flask app can be created."""
    print("\n🌐 Testing Flask app...")
    
    try:
        from web_app import app
        
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("  ✅ Flask app responds correctly")
                return True
            else:
                print(f"  ❌ Flask app returned status code: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'csv_parser.py',
        'web_app.py',
        'requirements.txt',
        'sample_integrations.csv',
        'templates/base.html',
        'templates/index.html',
        'templates/results.html',
        'templates/example.html'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            all_exist = False
    
    return all_exist

def main():
    print("🧪 CSV Parser Setup Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("CSV Parser", test_csv_parser),
        ("Flask App", test_flask_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready to go!")
        print("\nNext steps:")
        print("  1. Run: ./run_web.sh")
        print("  2. Open: http://localhost:5001")
        print("  3. Upload your CSV file")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 
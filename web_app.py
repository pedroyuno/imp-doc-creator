#!/usr/bin/env python3
"""
Web interface for Implementation Scoping Document Parser
Handles BDM handover documents for implementation analysis
"""

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import os
import tempfile
from werkzeug.utils import secure_filename
from csv_parser import ProviderPaymentParser
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with upload form."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        try:
            # Create a temporary file to save the upload
            with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as temp_file:
                file.save(temp_file.name)
                temp_filename = temp_file.name
            
            # Process the CSV file (non-verbose mode for web)
            parser = ProviderPaymentParser(temp_filename, verbose=False)
            
            # Custom parsing to capture any errors
            try:
                results = parser.parse()
                
                # Clean up temporary file
                os.unlink(temp_filename)
                
                if not results:
                    flash('No valid provider + payment method combinations found in the CSV file.')
                    return redirect(url_for('index'))
                
                # Process results for web display
                processed_results = []
                for key, data in results.items():
                    provider_data = {
                        'provider': data['provider'],
                        'payment_method': data['payment_method'],
                        'features': []
                    }
                    
                    for feature_name, feature_value in data['features'].items():
                        provider_data['features'].append({
                            'name': feature_name,
                            'value': feature_value,
                            'has_value': bool(feature_value.strip()) if feature_value else False
                        })
                    
                    processed_results.append(provider_data)
                
                return render_template('results.html', 
                                     results=processed_results,
                                     filename=secure_filename(file.filename))
                
            except Exception as e:
                # Clean up temporary file on error
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                flash(f'Error processing CSV file: {str(e)}')
                return redirect(url_for('index'))
                
        except Exception as e:
            flash(f'Error uploading file: {str(e)}')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload a CSV file.')
        return redirect(url_for('index'))

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint for programmatic access."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only CSV files are allowed.'}), 400
    
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_filename = temp_file.name
        
        # Process the CSV file (non-verbose mode for API)
        parser = ProviderPaymentParser(temp_filename, verbose=False)
        results = parser.parse()
        
        # Clean up temporary file
        os.unlink(temp_filename)
        
        return jsonify({
            'success': True,
            'filename': secure_filename(file.filename),
            'results': results
        })
        
    except Exception as e:
        # Clean up temporary file on error
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.unlink(temp_filename)
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/example')
def example():
    """Show example page with sample data."""
    return render_template('example.html')

@app.route('/download-sample')
def download_sample():
    """Download sample CSV file."""
    from flask import send_file
    return send_file('sample_integrations.csv', 
                     as_attachment=True,
                     download_name='sample_integrations.csv',
                     mimetype='text/csv')

if __name__ == '__main__':
    port = 5001
    print(f"🌐 Starting Implementation Scoping Document Parser on http://localhost:{port}")
    print(f"📋 Open your browser and go to: http://localhost:{port}")
    print("⏹️  Press Ctrl+C to stop the server")
    
    app.run(debug=False, host='0.0.0.0', port=port) 
#!/usr/bin/env python3
"""
Web interface for Implementation Scoping Document Parser
Handles BDM handover documents for implementation analysis
"""

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, session, make_response
import os
import tempfile
from werkzeug.utils import secure_filename
from csv_parser import ProviderPaymentParser
from test_case_generator import TestCaseGenerator
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
                
                # Store the raw results in session for test case generation
                session['parsed_results'] = results
                session['filename'] = secure_filename(file.filename)
                
                # Process results for web display with enriched data
                processed_results = []
                enriched_data = parser.export_enriched_dict()
                
                for key, data in enriched_data.items():
                    provider_data = {
                        'provider': data['provider'],
                        'payment_method': data['payment_method'],
                        'features': []
                    }
                    
                    for feature_name, feature_data in data['features'].items():
                        provider_data['features'].append(feature_data)
                    
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

@app.route('/generate-test-cases')
def generate_test_cases_form():
    """Show form for test case generation options."""
    if 'parsed_results' not in session:
        flash('No parsed results found. Please upload a CSV file first.')
        return redirect(url_for('index'))
    
    return render_template('test_case_options.html', 
                         filename=session.get('filename', 'Unknown'))

@app.route('/generate-test-cases', methods=['POST'])
def generate_test_cases():
    """Generate and download test case document."""
    if 'parsed_results' not in session:
        flash('No parsed results found. Please upload a CSV file first.')
        return redirect(url_for('index'))
    
    # Get form parameters
    merchant_name = request.form.get('merchant_name', 'Merchant')
    language = request.form.get('language', 'en')
    output_format = request.form.get('output_format', 'html')  # Default to HTML
    include_metadata = request.form.get('include_metadata') == 'on'
    
    try:
        # Generate test cases using the stored results
        generator = TestCaseGenerator(locale=language)
        
        if output_format == 'html':
            # Generate HTML document
            document_content = generator.generate_html_document(
                session['parsed_results'],
                merchant_name=merchant_name,
                include_metadata=include_metadata
            )
            content_type = 'text/html'
            file_extension = 'html'
        else:
            # Generate Markdown document
            document_content = generator.generate_markdown_document(
                session['parsed_results'],
                merchant_name=merchant_name,
                include_metadata=include_metadata
            )
            content_type = 'text/markdown'
            file_extension = 'md'
        
        # Create response with document file
        response = make_response(document_content)
        filename = session.get('filename', 'implementation_scope')
        safe_merchant_name = ''.join(c for c in merchant_name if c.isalnum() or c in (' ', '-', '_')).strip()
        download_filename = f"{safe_merchant_name}_test_cases_{language}.{file_extension}".replace(' ', '_')
        
        response.headers['Content-Type'] = content_type
        response.headers['Content-Disposition'] = f'attachment; filename="{download_filename}"'
        
        return response
        
    except Exception as e:
        flash(f'Error generating test cases: {str(e)}')
        return redirect(url_for('generate_test_cases_form'))

@app.route('/api/generate-test-cases', methods=['POST'])
def api_generate_test_cases():
    """API endpoint for test case generation."""
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data or 'parsed_features' not in data:
            return jsonify({'error': 'No parsed features provided'}), 400
        
        parsed_features = data['parsed_features']
        merchant_name = data.get('merchant_name', 'Merchant')
        language = data.get('language', 'en')
        output_format = data.get('output_format', 'html')  # Default to HTML
        include_metadata = data.get('include_metadata', True)
        
        # Generate test cases
        generator = TestCaseGenerator(locale=language)
        
        # Generate document in requested format
        if output_format == 'html':
            document_content = generator.generate_html_document(
                parsed_features,
                merchant_name=merchant_name,
                include_metadata=include_metadata
            )
        else:
            document_content = generator.generate_markdown_document(
                parsed_features,
                merchant_name=merchant_name,
                include_metadata=include_metadata
            )
        
        # Generate statistics
        statistics = generator.generate_summary_statistics(parsed_features)
        
        return jsonify({
            'success': True,
            'document_content': document_content,
            'output_format': output_format,
            'statistics': statistics,
            'language': language,
            'merchant_name': merchant_name
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating test cases: {str(e)}'}), 500

@app.route('/test-case-preview')
def test_case_preview():
    """Preview test cases without downloading."""
    if 'parsed_results' not in session:
        flash('No parsed results found. Please upload a CSV file first.')
        return redirect(url_for('index'))
    
    # Get parameters from query string
    merchant_name = request.args.get('merchant_name', 'Merchant')
    language = request.args.get('language', 'en')
    include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
    
    try:
        # Generate test cases
        generator = TestCaseGenerator(locale=language)
        
        # Get test case data for preview
        test_cases_data = generator.generate_test_cases_for_features(session['parsed_results'])
        statistics = generator.generate_summary_statistics(session['parsed_results'])
        
        return render_template('test_case_preview.html',
                             test_cases_data=test_cases_data,
                             statistics=statistics,
                             merchant_name=merchant_name,
                             language=language,
                             filename=session.get('filename', 'Unknown'))
        
    except Exception as e:
        flash(f'Error generating preview: {str(e)}')
        return redirect(url_for('generate_test_cases_form'))

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
        
        # Return enriched results for API
        enriched_results = parser.export_enriched_dict()
        
        return jsonify({
            'success': True,
            'filename': secure_filename(file.filename),
            'results': results,
            'enriched_results': enriched_results
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
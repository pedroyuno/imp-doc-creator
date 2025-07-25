#!/usr/bin/env python3
"""
Web interface for Implementation Scoping Document Parser
Handles BDM handover documents for implementation analysis
"""

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, session, make_response
import os
import tempfile
from io import BytesIO
from werkzeug.utils import secure_filename
from csv_parser import ProviderPaymentParser
from test_case_generator import TestCaseGenerator
from rules_manager import RulesManager
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

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
    output_format = request.form.get('output_format', 'docx')  # Default to DOCX
    environment = request.form.get('environment', 'separated')  # New environment parameter - default to separated
    include_metadata = request.form.get('include_metadata') == 'on'
    
    try:
        # Generate test cases using the stored results
        generator = TestCaseGenerator(locale=language)
        
        if output_format == 'html':
            # Generate HTML document
            document_content = generator.generate_html_document(
                session['parsed_results'],
                merchant_name=merchant_name,
                include_metadata=include_metadata,
                environment=environment
            )
            content_type = 'text/html'
            file_extension = 'html'
            response = make_response(document_content)
        elif output_format == 'docx':
            # Generate DOCX document
            doc = generator.generate_docx_document(
                session['parsed_results'],
                merchant_name=merchant_name,
                include_metadata=include_metadata,
                environment=environment
            )
            
            # Save document to BytesIO for download
            doc_io = BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)
            
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            file_extension = 'docx'
            response = make_response(doc_io.getvalue())
        else:
            # Generate Markdown document
            document_content = generator.generate_markdown_document(
                session['parsed_results'],
                merchant_name=merchant_name,
                include_metadata=include_metadata,
                environment=environment
            )
            content_type = 'text/markdown'
            file_extension = 'md'
            response = make_response(document_content)
        filename = session.get('filename', 'implementation_scope')
        safe_merchant_name = ''.join(c for c in merchant_name if c.isalnum() or c in (' ', '-', '_')).strip()
        download_filename = f"{safe_merchant_name}_test_cases_{language}_{environment}.{file_extension}".replace(' ', '_')
        
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
        output_format = data.get('output_format', 'docx')  # Default to DOCX
        environment = data.get('environment', 'separated')  # New environment parameter
        include_metadata = data.get('include_metadata', True)
        
        # Generate test cases
        generator = TestCaseGenerator(locale=language)
        
        # Generate document in requested format
        if output_format == 'html':
            document_content = generator.generate_html_document(
                parsed_features,
                merchant_name=merchant_name,
                include_metadata=include_metadata,
                environment=environment
            )
            content_base64 = None
        elif output_format == 'docx':
            # Generate DOCX document
            doc = generator.generate_docx_document(
                parsed_features,
                merchant_name=merchant_name,
                include_metadata=include_metadata,
                environment=environment
            )
            
            # Save document to BytesIO and encode as base64
            doc_io = BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)
            
            import base64
            content_base64 = base64.b64encode(doc_io.getvalue()).decode('utf-8')
            document_content = None  # DOCX content is in base64 format
        else:
            document_content = generator.generate_markdown_document(
                parsed_features,
                merchant_name=merchant_name,
                include_metadata=include_metadata,
                environment=environment
            )
            content_base64 = None
        
        # Generate statistics
        statistics = generator.generate_summary_statistics(parsed_features, environment)
        
        response_data = {
            'success': True,
            'output_format': output_format,
            'statistics': statistics,
            'language': language,
            'merchant_name': merchant_name,
            'environment': environment
        }
        
        # Include appropriate content field based on format
        if output_format == 'docx':
            response_data['document_content_base64'] = content_base64
            response_data['content_type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            response_data['document_content'] = document_content
            response_data['content_type'] = 'text/html' if output_format == 'html' else 'text/markdown'
        
        return jsonify(response_data)
        
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
    environment = request.args.get('environment', 'separated')  # New environment parameter
    include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
    
    try:
        # Generate test cases
        generator = TestCaseGenerator(locale=language)
        
        # Get test case data for preview
        test_cases_data = generator.generate_test_cases_for_features(session['parsed_results'], environment)
        statistics = generator.generate_summary_statistics(session['parsed_results'], environment)
        
        return render_template('test_case_preview.html',
                             test_cases_data=test_cases_data,
                             statistics=statistics,
                             merchant_name=merchant_name,
                             language=language,
                             environment=environment,
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

@app.route('/feature-rules')
def feature_rules():
    """Display feature rules management interface."""
    try:
        rules_manager = RulesManager(verbose=False)
        rules_manager.load_rules()
        
        # Get rules data for display
        rules_data = {}
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        return render_template('feature_rules.html', 
                             rules_data=rules_data,
                             summary=rules_manager.get_rules_summary())
    except Exception as e:
        flash(f'Error loading feature rules: {str(e)}')
        return redirect(url_for('index'))

@app.route('/feature-rules/edit/<feature_name>')
def edit_feature_rule(feature_name):
    """Edit a specific feature rule."""
    try:
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            flash(f'Feature rule "{feature_name}" not found.')
            return redirect(url_for('feature_rules'))
        
        rule = rules_data['rules'][feature_name]
        return render_template('edit_feature_rule.html', 
                             feature_name=feature_name,
                             rule=rule)
    except Exception as e:
        flash(f'Error loading feature rule: {str(e)}')
        return redirect(url_for('feature_rules'))

@app.route('/feature-rules/save', methods=['POST'])
def save_feature_rule():
    """Save changes to a feature rule."""
    try:
        feature_name = request.form.get('feature_name')
        documentation_url = request.form.get('documentation_url', '').strip()
        comment = request.form.get('comment', '').strip()
        
        if not feature_name or not documentation_url or not comment:
            flash('All fields are required.')
            return redirect(url_for('edit_feature_rule', feature_name=feature_name))
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Update the rule
        if feature_name in rules_data.get('rules', {}):
            rules_data['rules'][feature_name]['documentation_url'] = documentation_url
            rules_data['rules'][feature_name]['comment'] = comment
            
            # Handle integration_steps format
            if 'integration_steps' in rules_data['rules'][feature_name]:
                rules_data['rules'][feature_name]['integration_steps'][0]['documentation_url'] = documentation_url
                rules_data['rules'][feature_name]['integration_steps'][0]['comment'] = comment
        
        # Update last_updated timestamp
        from datetime import datetime
        rules_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save back to file
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        flash(f'Successfully updated feature rule for "{feature_name}".')
        return redirect(url_for('feature_rules'))
        
    except Exception as e:
        flash(f'Error saving feature rule: {str(e)}')
        return redirect(url_for('feature_rules'))

@app.route('/feature-rules/add', methods=['GET', 'POST'])
def add_feature_rule():
    """Add a new feature rule."""
    if request.method == 'GET':
        return render_template('add_feature_rule.html')
    
    try:
        feature_name = request.form.get('feature_name', '').strip()
        documentation_url = request.form.get('documentation_url', '').strip()
        comment = request.form.get('comment', '').strip()
        
        if not feature_name or not documentation_url or not comment:
            flash('All fields are required.')
            return render_template('add_feature_rule.html')
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Check if feature already exists
        if feature_name in rules_data.get('rules', {}):
            flash(f'Feature rule "{feature_name}" already exists.')
            return render_template('add_feature_rule.html')
        
        # Create new rule with testcases
        new_rule = {
            "feature_name": feature_name,
            "integration_steps": [
                {
                    "documentation_url": documentation_url,
                    "comment": comment
                }
            ],
            "testcases": [
                {
                    "id": f"{feature_name[:3].upper()}0001",
                    "description_key": f"testcase.{feature_name.lower()}.basic_functionality",
                    "type": "happy path",
                    "environment": "both"
                }
            ]
        }
        
        # Add the new rule
        rules_data['rules'][feature_name] = new_rule
        
        # Update metadata
        from datetime import datetime
        rules_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        rules_data['metadata']['total_rules'] = len(rules_data['rules'])
        
        # Save back to file
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        flash(f'Successfully added new feature rule for "{feature_name}".')
        return redirect(url_for('feature_rules'))
        
    except Exception as e:
        flash(f'Error adding feature rule: {str(e)}')
        return render_template('add_feature_rule.html')

@app.route('/feature-rules/delete/<feature_name>', methods=['POST'])
def delete_feature_rule(feature_name):
    """Delete a feature rule."""
    try:
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            flash(f'Feature rule "{feature_name}" not found.')
            return redirect(url_for('feature_rules'))
        
        # Delete the rule
        del rules_data['rules'][feature_name]
        
        # Update metadata
        from datetime import datetime
        rules_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        rules_data['metadata']['total_rules'] = len(rules_data['rules'])
        
        # Save back to file
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        flash(f'Successfully deleted feature rule for "{feature_name}".')
        return redirect(url_for('feature_rules'))
        
    except Exception as e:
        flash(f'Error deleting feature rule: {str(e)}')
        return redirect(url_for('feature_rules'))

@app.route('/feature-rules/reorder', methods=['POST'])
def reorder_feature_rules():
    """Reorder feature rules based on the new order provided."""
    try:
        new_order = request.json.get('order', [])
        
        if not new_order:
            return jsonify({'error': 'No order provided'}), 400
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Create new ordered rules dictionary
        new_rules = {}
        for feature_name in new_order:
            if feature_name in rules_data['rules']:
                new_rules[feature_name] = rules_data['rules'][feature_name]
        
        # Add any missing rules that weren't in the order (shouldn't happen, but safety)
        for feature_name, rule in rules_data['rules'].items():
            if feature_name not in new_rules:
                new_rules[feature_name] = rule
        
        # Update rules with new order
        rules_data['rules'] = new_rules
        
        # Update timestamp
        from datetime import datetime
        rules_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save back to file
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': 'Rules reordered successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Error reordering rules: {str(e)}'}), 500

@app.route('/feature-rules/<feature_name>/testcases')
def manage_testcases(feature_name):
    """Manage test cases for a specific feature."""
    try:
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            flash(f'Feature rule "{feature_name}" not found.')
            return redirect(url_for('feature_rules'))
        
        rule = rules_data['rules'][feature_name]
        testcases = rule.get('testcases', [])
        
        return render_template('manage_testcases.html', 
                             feature_name=feature_name,
                             testcases=testcases,
                             testcase_types=rules_data['metadata']['testcase_types'],
                             environments=rules_data['metadata']['environments'])
    except Exception as e:
        flash(f'Error loading test cases: {str(e)}')
        return redirect(url_for('feature_rules'))

@app.route('/feature-rules/<feature_name>/testcases/add', methods=['GET', 'POST'])
def add_testcase(feature_name):
    """Add a new test case to a feature."""
    if request.method == 'GET':
        try:
            with open('feature_rules.json', 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            return render_template('add_testcase.html', 
                                 feature_name=feature_name,
                                 testcase_types=rules_data['metadata']['testcase_types'],
                                 environments=rules_data['metadata']['environments'])
        except Exception as e:
            flash(f'Error loading form: {str(e)}')
            return redirect(url_for('manage_testcases', feature_name=feature_name))
    
    try:
        testcase_id = request.form.get('testcase_id', '').strip()
        description_key = request.form.get('description_key', '').strip()
        testcase_type = request.form.get('testcase_type', '').strip()
        environment = request.form.get('environment', '').strip()
        
        if not all([testcase_id, description_key, testcase_type, environment]):
            flash('All fields are required.')
            return redirect(url_for('add_testcase', feature_name=feature_name))
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            flash(f'Feature rule "{feature_name}" not found.')
            return redirect(url_for('feature_rules'))
        
        # Check if testcase ID already exists
        existing_testcases = rules_data['rules'][feature_name].get('testcases', [])
        if any(tc['id'] == testcase_id for tc in existing_testcases):
            flash(f'Test case ID "{testcase_id}" already exists.')
            return redirect(url_for('add_testcase', feature_name=feature_name))
        
        # Create new test case
        new_testcase = {
            'id': testcase_id,
            'description_key': description_key,
            'type': testcase_type,
            'environment': environment
        }
        
        # Add to feature's test cases
        if 'testcases' not in rules_data['rules'][feature_name]:
            rules_data['rules'][feature_name]['testcases'] = []
        
        rules_data['rules'][feature_name]['testcases'].append(new_testcase)
        
        # Update timestamp
        from datetime import datetime
        rules_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save back to file
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        flash(f'Successfully added test case "{testcase_id}".')
        return redirect(url_for('manage_testcases', feature_name=feature_name))
        
    except Exception as e:
        flash(f'Error adding test case: {str(e)}')
        return redirect(url_for('add_testcase', feature_name=feature_name))

@app.route('/feature-rules/<feature_name>/testcases/<testcase_id>/edit', methods=['GET', 'POST'])
def edit_testcase(feature_name, testcase_id):
    """Edit an existing test case."""
    if request.method == 'GET':
        try:
            with open('feature_rules.json', 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            if feature_name not in rules_data.get('rules', {}):
                flash(f'Feature rule "{feature_name}" not found.')
                return redirect(url_for('feature_rules'))
            
            # Find the test case
            testcases = rules_data['rules'][feature_name].get('testcases', [])
            testcase = next((tc for tc in testcases if tc['id'] == testcase_id), None)
            
            if not testcase:
                flash(f'Test case "{testcase_id}" not found.')
                return redirect(url_for('manage_testcases', feature_name=feature_name))
            
            return render_template('edit_testcase.html', 
                                 feature_name=feature_name,
                                 testcase=testcase,
                                 testcase_types=rules_data['metadata']['testcase_types'],
                                 environments=rules_data['metadata']['environments'])
        except Exception as e:
            flash(f'Error loading test case: {str(e)}')
            return redirect(url_for('manage_testcases', feature_name=feature_name))
    
    try:
        description_key = request.form.get('description_key', '').strip()
        testcase_type = request.form.get('testcase_type', '').strip()
        environment = request.form.get('environment', '').strip()
        
        if not all([description_key, testcase_type, environment]):
            flash('All fields are required.')
            return redirect(url_for('edit_testcase', feature_name=feature_name, testcase_id=testcase_id))
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            flash(f'Feature rule "{feature_name}" not found.')
            return redirect(url_for('feature_rules'))
        
        # Find and update the test case
        testcases = rules_data['rules'][feature_name].get('testcases', [])
        for i, testcase in enumerate(testcases):
            if testcase['id'] == testcase_id:
                testcases[i]['description_key'] = description_key
                testcases[i]['type'] = testcase_type
                testcases[i]['environment'] = environment
                break
        else:
            flash(f'Test case "{testcase_id}" not found.')
            return redirect(url_for('manage_testcases', feature_name=feature_name))
        
        # Update timestamp
        from datetime import datetime
        rules_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save back to file
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        flash(f'Successfully updated test case "{testcase_id}".')
        return redirect(url_for('manage_testcases', feature_name=feature_name))
        
    except Exception as e:
        flash(f'Error updating test case: {str(e)}')
        return redirect(url_for('edit_testcase', feature_name=feature_name, testcase_id=testcase_id))

@app.route('/feature-rules/<feature_name>/testcases/<testcase_id>/delete', methods=['POST'])
def delete_testcase(feature_name, testcase_id):
    """Delete a test case."""
    try:
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            flash(f'Feature rule "{feature_name}" not found.')
            return redirect(url_for('feature_rules'))
        
        # Find and remove the test case
        testcases = rules_data['rules'][feature_name].get('testcases', [])
        original_count = len(testcases)
        testcases[:] = [tc for tc in testcases if tc['id'] != testcase_id]
        
        if len(testcases) == original_count:
            flash(f'Test case "{testcase_id}" not found.')
            return redirect(url_for('manage_testcases', feature_name=feature_name))
        
        # Update timestamp
        from datetime import datetime
        rules_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save back to file
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        flash(f'Successfully deleted test case "{testcase_id}".')
        return redirect(url_for('manage_testcases', feature_name=feature_name))
        
    except Exception as e:
        flash(f'Error deleting test case: {str(e)}')
        return redirect(url_for('manage_testcases', feature_name=feature_name))

if __name__ == '__main__':
    port = 5001
    
    print(f"🌐 Starting Implementation Scoping Document Parser on http://localhost:{port}")
    print(f"📋 Open your browser and go to: http://localhost:{port}")
    print("⏹️  Press Ctrl+C to stop the server")
    
    app.run(host='0.0.0.0', port=port, debug=True) 
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
    # Get available rules files
    available_rules_files = RulesManager.get_provider_rules_files()
    # Extract provider names from filenames
    rules_files_info = []
    for file_path in available_rules_files:
        filename = os.path.basename(file_path)
        # Extract provider name from feature_rules_{provider}.json
        if filename.startswith('feature_rules_') and filename.endswith('.json'):
            provider = filename[14:-5]  # Remove 'feature_rules_' prefix and '.json' suffix
            rules_files_info.append({
                'path': file_path,
                'filename': filename,
                'provider': provider
            })
    
    return render_template('index.html', available_rules_files=rules_files_info)

@app.route('/api/rules-files', methods=['GET'])
def api_list_rules_files():
    """List available rules files."""
    try:
        available_rules_files = RulesManager.get_provider_rules_files()
        rules_files_info = []
        for file_path in available_rules_files:
            filename = os.path.basename(file_path)
            if filename.startswith('feature_rules_') and filename.endswith('.json'):
                provider = filename[14:-5]
                rules_files_info.append({
                    'path': file_path,
                    'filename': filename,
                    'provider': provider
                })
        
        return jsonify({
            'success': True,
            'rules_files': rules_files_info
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
            
            # Get selected rules files from form
            selected_rules_files = request.form.getlist('rules_files[]')
            # Validate that selected files exist
            valid_rules_files = []
            for rules_file in selected_rules_files:
                if os.path.exists(rules_file):
                    valid_rules_files.append(rules_file)
                else:
                    flash(f'Warning: Rules file {rules_file} not found, skipping.')
            
            # Store selected rules files in session
            session['selected_rules_files'] = valid_rules_files
            
            # Process the CSV file (non-verbose mode for web)
            if valid_rules_files:
                parser = ProviderPaymentParser(temp_filename, verbose=False, rules_file_paths=valid_rules_files)
            else:
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
        # Get selected rules files from session
        selected_rules_files = session.get('selected_rules_files', [])
        # Generate test cases using the stored results
        generator = TestCaseGenerator(locale=language, rules_file_paths=selected_rules_files if selected_rules_files else None)
        
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
        
        # Get selected rules files from request if provided
        selected_rules_files = data.get('rules_files', [])
        # Generate test cases
        generator = TestCaseGenerator(locale=language, rules_file_paths=selected_rules_files if selected_rules_files else None)
        
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
        # Get selected rules files from session
        selected_rules_files = session.get('selected_rules_files', [])
        # Generate test cases
        generator = TestCaseGenerator(locale=language, rules_file_paths=selected_rules_files if selected_rules_files else None)
        
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
        # Get which rules file to load from query parameter
        rules_file = request.args.get('file', 'feature_rules.json')
        
        # Validate file name to prevent directory traversal
        if not rules_file.endswith('.json') or '/' in rules_file or '..' in rules_file:
            rules_file = 'feature_rules.json'
        
        # Check if file exists
        if not os.path.exists(rules_file):
            flash(f'Rules file "{rules_file}" not found. Loading default.')
            rules_file = 'feature_rules.json'
        
        # Store in session for API calls
        session['current_rules_file'] = rules_file
        
        rules_manager = RulesManager(verbose=False)
        rules_manager.load_rules()
        
        # Get rules data for display
        rules_data = {}
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Extract master rules separately
        master_rules = rules_data.get('master', None)
        
        # Get list of available rules files
        available_rules_files = []
        # Always include default
        if os.path.exists('feature_rules.json'):
            available_rules_files.append({
                'filename': 'feature_rules.json',
                'name': 'Default',
                'path': 'feature_rules.json'
            })
        
        # Get provider-specific files
        provider_files = RulesManager.get_provider_rules_files()
        for file_path in provider_files:
            filename = os.path.basename(file_path)
            if filename.startswith('feature_rules_') and filename.endswith('.json'):
                provider = filename[14:-5]  # Remove 'feature_rules_' prefix and '.json' suffix
                available_rules_files.append({
                    'filename': filename,
                    'name': provider,
                    'path': file_path
                })
        
        return render_template('feature_rules.html', 
                             rules_data=rules_data,
                             master_rules=master_rules,
                             current_rules_file=rules_file,
                             available_rules_files=available_rules_files,
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
        
        # Check if it's a master rule
        is_master_rule = feature_name == 'master'
        
        if is_master_rule:
            if 'master' not in rules_data:
                flash('Master rules not found.')
                return redirect(url_for('feature_rules'))
            rule = rules_data['master']
        else:
            if feature_name not in rules_data.get('rules', {}):
                flash(f'Feature rule "{feature_name}" not found.')
                return redirect(url_for('feature_rules'))
            rule = rules_data['rules'][feature_name]
        
        return render_template('edit_feature_rule.html', 
                             feature_name=feature_name,
                             rule=rule,
                             is_master_rule=is_master_rule)
    except Exception as e:
        flash(f'Error loading feature rule: {str(e)}')
        return redirect(url_for('feature_rules'))

@app.route('/feature-rules/save', methods=['POST'])
def save_feature_rule():
    """Save changes to a feature rule."""
    try:
        feature_name = request.form.get('feature_name')
        
        if not feature_name:
            flash('Feature name is required.')
            return redirect(url_for('feature_rules'))
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Check if it's a master rule
        is_master_rule = feature_name == 'master'
        
        if is_master_rule:
            if 'master' not in rules_data:
                flash('Master rules not found.')
                return redirect(url_for('feature_rules'))
        else:
            if feature_name not in rules_data.get('rules', {}):
                flash(f'Feature rule "{feature_name}" not found.')
                return redirect(url_for('feature_rules'))
        
        # Get all integration steps from form
        integration_steps = []
        step_index = 0
        
        while True:
            doc_url_key = f'documentation_url_{step_index}'
            comment_key = f'comment_{step_index}'
            
            documentation_url = request.form.get(doc_url_key, '').strip()
            comment = request.form.get(comment_key, '').strip()
            
            if not documentation_url and not comment:
                break
                
            if documentation_url and comment:
                integration_steps.append({
                    'documentation_url': documentation_url,
                    'comment': comment
                })
            
            step_index += 1
        
        if not integration_steps:
            flash('At least one integration step is required.')
            return redirect(url_for('edit_feature_rule', feature_name=feature_name))
        
        # Update the rule in the appropriate section
        if is_master_rule:
            rules_data['master']['integration_steps'] = integration_steps
        else:
            rules_data['rules'][feature_name]['integration_steps'] = integration_steps
            
            # Maintain backward compatibility - update old format fields if they exist
            if 'documentation_url' in rules_data['rules'][feature_name]:
                rules_data['rules'][feature_name]['documentation_url'] = integration_steps[0]['documentation_url']
            if 'comment' in rules_data['rules'][feature_name]:
                rules_data['rules'][feature_name]['comment'] = integration_steps[0]['comment']
        
        # Update last_updated timestamp
        from datetime import datetime
        rules_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save back to file
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        rule_type = "master rules" if is_master_rule else f'feature rule for "{feature_name}"'
        flash(f'Successfully updated {rule_type} with {len(integration_steps)} integration step(s).')
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
        
        if not feature_name:
            flash('Feature name is required.')
            return render_template('add_feature_rule.html')
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Check if feature already exists
        if feature_name in rules_data.get('rules', {}):
            flash(f'Feature rule "{feature_name}" already exists.')
            return render_template('add_feature_rule.html')
        
        # Get all integration steps from form
        integration_steps = []
        step_index = 0
        
        while True:
            doc_url_key = f'documentation_url_{step_index}'
            comment_key = f'comment_{step_index}'
            
            documentation_url = request.form.get(doc_url_key, '').strip()
            comment = request.form.get(comment_key, '').strip()
            
            if not documentation_url and not comment:
                break
                
            if documentation_url and comment:
                integration_steps.append({
                    'documentation_url': documentation_url,
                    'comment': comment
                })
            
            step_index += 1
        
        if not integration_steps:
            flash('At least one integration step is required.')
            return render_template('add_feature_rule.html')
        
        # Create new rule with testcases
        new_rule = {
            "feature_name": feature_name,
            "integration_steps": integration_steps,
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
        
        # Save to file
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        flash(f'Successfully added feature rule "{feature_name}" with {len(integration_steps)} integration step(s).')
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

# Helper function to get description text from i18n files
def get_i18n_description(description_key, locale='en'):
    """Get the description text from i18n file."""
    try:
        i18n_file = f'i18n/{locale}.json'
        
        # Load i18n data
        with open(i18n_file, 'r', encoding='utf-8') as f:
            i18n_data = json.load(f)
        
        # Parse the description key (e.g., "testcase.purchase.card.purc001")
        key_parts = description_key.split('.')
        
        # Navigate the nested structure
        current = i18n_data
        for part in key_parts:
            if part in current:
                current = current[part]
            else:
                return None
        
        return current if isinstance(current, str) else None
    except Exception as e:
        print(f"Error reading i18n file: {e}")
        return None

# Helper function to update i18n files
def update_i18n_description(description_key, description_text, locale='en'):
    """Update the i18n file with a new description."""
    try:
        i18n_file = f'i18n/{locale}.json'
        
        # Load current i18n data
        with open(i18n_file, 'r', encoding='utf-8') as f:
            i18n_data = json.load(f)
        
        # Parse the description key (e.g., "testcase.purchase.card.purc001")
        key_parts = description_key.split('.')
        
        # Navigate/create the nested structure
        current = i18n_data
        for part in key_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the final value
        current[key_parts[-1]] = description_text
        
        # Save updated i18n data
        with open(i18n_file, 'w', encoding='utf-8') as f:
            json.dump(i18n_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error updating i18n file: {e}")
        return False

# API endpoints for the new feature rules interface
@app.route('/api/feature-rules/<feature_name>/payment-methods', methods=['POST'])
def api_add_payment_method(feature_name):
    """Add a new payment method to a feature rule."""
    try:
        data = request.get_json()
        payment_method = data.get('payment_method')
        
        if not payment_method:
            return jsonify({'success': False, 'error': 'Payment method name is required'})
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            return jsonify({'success': False, 'error': 'Feature rule not found'})
        
        # Add payment method structure
        if 'by_payment_method' not in rules_data['rules'][feature_name]:
            rules_data['rules'][feature_name]['by_payment_method'] = {}
        
        if payment_method not in rules_data['rules'][feature_name]['by_payment_method']:
            rules_data['rules'][feature_name]['by_payment_method'][payment_method] = {
                'testcases': [],
                'integration_steps': []
            }
        
        # Save updated rules
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/feature-rules/<feature_name>', methods=['PUT'])
def api_update_feature_rule(feature_name):
    """Update a feature rule."""
    try:
        data = request.get_json()
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            return jsonify({'success': False, 'error': 'Feature rule not found'})
        
        # Update feature rule data
        if 'feature_name' in data:
            rules_data['rules'][feature_name]['feature_name'] = data['feature_name']
        
        # Save updated rules
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/testcases', methods=['POST'])
def api_create_testcase():
    """Create a new test case."""
    try:
        data = request.get_json()
        
        # Parse feature and payment method
        # Try to get from explicit fields first, then fallback to parsing id
        feature_name = data.get('feature_name')
        payment_method = data.get('payment_method')
        
        if not feature_name or not payment_method:
            feature_pm = data.get('id', '').split(':')
            if len(feature_pm) == 2:
                feature_name, payment_method = feature_pm
            else:
                return jsonify({'success': False, 'error': 'Missing feature_name or payment_method, and invalid ID format'})
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            return jsonify({'success': False, 'error': 'Feature rule not found'})
        
        # Add test case
        if 'by_payment_method' not in rules_data['rules'][feature_name]:
            rules_data['rules'][feature_name]['by_payment_method'] = {}
        
        if payment_method not in rules_data['rules'][feature_name]['by_payment_method']:
            rules_data['rules'][feature_name]['by_payment_method'][payment_method] = {
                'testcases': [],
                'integration_steps': []
            }
        
        # Generate unique test case ID
        testcase_id = data.get('id', 'TC' + str(len(rules_data['rules'][feature_name]['by_payment_method'][payment_method]['testcases']) + 1).zfill(3))
        
        # Auto-generate description key based on feature, payment method, and test case ID
        description_key = f"testcase.{feature_name.lower()}.{payment_method.lower()}.{testcase_id.lower()}"
        
        new_testcase = {
            'id': testcase_id,
            'description_key': description_key,
            'type': data.get('type', 'happy path'),
            'environment': data.get('environment', 'both')
        }
        
        rules_data['rules'][feature_name]['by_payment_method'][payment_method]['testcases'].append(new_testcase)
        
        # Save updated rules
        with open('feature_rules.json', 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)
        
        # Update i18n files with the description
        description_text = data.get('description', '')
        if description_text:
            # Update all supported locales
            for locale in ['en', 'es', 'pt']:
                update_i18n_description(description_key, description_text, locale)
        
        return jsonify({'success': True, 'testcase_id': testcase_id, 'description_key': description_key})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/testcases/<testcase_id>', methods=['PUT'])
def api_update_testcase(testcase_id):
    """Update an existing test case."""
    try:
        data = request.get_json()
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Find and update test case in regular rules
        for feature_name, rule in rules_data.get('rules', {}).items():
            if 'by_payment_method' in rule:
                for pm_name, pm_config in rule['by_payment_method'].items():
                    for i, testcase in enumerate(pm_config.get('testcases', [])):
                        if testcase['id'] == testcase_id:
                            # Update test case
                            if 'description_key' in data:
                                testcase['description_key'] = data['description_key']
                            if 'type' in data:
                                testcase['type'] = data['type']
                            if 'environment' in data:
                                testcase['environment'] = data['environment']
                            
                            # Save updated rules
                            with open('feature_rules.json', 'w', encoding='utf-8') as f:
                                json.dump(rules_data, f, indent=2, ensure_ascii=False)
                            
                            # Update i18n files if description is provided
                            if 'description' in data and data['description']:
                                description_key = testcase.get('description_key', '')
                                if description_key:
                                    # Update all supported locales
                                    for locale in ['en', 'es', 'pt']:
                                        update_i18n_description(description_key, data['description'], locale)
                            
                            return jsonify({'success': True})
        
        # Check master rules if not found in regular rules
        master_rules = rules_data.get('master', {})
        for i, testcase in enumerate(master_rules.get('testcases', [])):
            if testcase['id'] == testcase_id:
                # Update test case
                if 'description_key' in data:
                    testcase['description_key'] = data['description_key']
                if 'type' in data:
                    testcase['type'] = data['type']
                if 'environment' in data:
                    testcase['environment'] = data['environment']
                
                # Save updated rules
                with open('feature_rules.json', 'w', encoding='utf-8') as f:
                    json.dump(rules_data, f, indent=2, ensure_ascii=False)
                
                # Update i18n files if description is provided
                if 'description' in data and data['description']:
                    description_key = testcase.get('description_key', '')
                    if description_key:
                        # Update all supported locales
                        for locale in ['en', 'es', 'pt']:
                            update_i18n_description(description_key, data['description'], locale)
                
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Test case not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/testcases/<testcase_id>', methods=['DELETE'])
def api_delete_testcase(testcase_id):
    """Delete a test case."""
    try:
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Find and delete test case in regular rules
        for feature_name, rule in rules_data.get('rules', {}).items():
            if 'by_payment_method' in rule:
                for pm_name, pm_config in rule['by_payment_method'].items():
                    for i, testcase in enumerate(pm_config.get('testcases', [])):
                        if testcase['id'] == testcase_id:
                            # Remove test case
                            pm_config['testcases'].pop(i)
                            
                            # Save updated rules
                            with open('feature_rules.json', 'w', encoding='utf-8') as f:
                                json.dump(rules_data, f, indent=2, ensure_ascii=False)
                            
                            return jsonify({'success': True})
        
        # Check master rules if not found in regular rules
        master_rules = rules_data.get('master', {})
        for i, testcase in enumerate(master_rules.get('testcases', [])):
            if testcase['id'] == testcase_id:
                # Remove test case
                master_rules['testcases'].pop(i)
                
                # Save updated rules
                with open('feature_rules.json', 'w', encoding='utf-8') as f:
                    json.dump(rules_data, f, indent=2, ensure_ascii=False)
                
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Test case not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/testcases/<testcase_id>/data', methods=['GET'])
def api_get_testcase_data(testcase_id):
    """Get test case data including description text."""
    try:
        # Get locale from query parameter, default to 'en'
        locale = request.args.get('locale', 'en')
        
        # Load current rules
        with open('feature_rules.json', 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Find test case in regular rules
        for feature_name, rule in rules_data.get('rules', {}).items():
            if 'by_payment_method' in rule:
                for pm_name, pm_config in rule['by_payment_method'].items():
                    for testcase in pm_config.get('testcases', []):
                        if testcase['id'] == testcase_id:
                            # Get description text from i18n using the specified locale
                            description_key = testcase.get('description_key', '')
                            description_text = get_i18n_description(description_key, locale) if description_key else ''
                            
                            return jsonify({
                                'success': True,
                                'testcase': {
                                    'id': testcase['id'],
                                    'description_key': description_key,
                                    'description': description_text,
                                    'type': testcase['type'],
                                    'environment': testcase['environment']
                                }
                            })
        
        # Check master rules if not found in regular rules
        master_rules = rules_data.get('master', {})
        for testcase in master_rules.get('testcases', []):
            if testcase['id'] == testcase_id:
                # Get description text from i18n using the specified locale
                description_key = testcase.get('description_key', '')
                description_text = get_i18n_description(description_key, locale) if description_key else ''
                
                return jsonify({
                    'success': True,
                    'testcase': {
                        'id': testcase['id'],
                        'description_key': description_key,
                        'description': description_text,
                        'type': testcase['type'],
                        'environment': testcase['environment']
                    }
                })
        
        return jsonify({'success': False, 'error': 'Test case not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/feature-rules/<feature_name>/data', methods=['GET'])
def api_get_feature_data(feature_name):
    """Get feature rule data including integration steps."""
    try:
        # Get current rules file
        rules_file = get_current_rules_file()
        
        # Load current rules
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Find feature in regular rules
        if feature_name in rules_data.get('rules', {}):
            feature_rule = rules_data['rules'][feature_name]
            
            # Get the first integration step from the first payment method as default
            default_url = ""
            default_comment = ""
            
            if 'by_payment_method' in feature_rule:
                for pm_name, pm_config in feature_rule['by_payment_method'].items():
                    if 'integration_steps' in pm_config and pm_config['integration_steps']:
                        first_step = pm_config['integration_steps'][0]
                        default_url = first_step.get('documentation_url', '')
                        default_comment = first_step.get('comment', '')
                        break
            
            return jsonify({
                'success': True,
                'feature': {
                    'feature_name': feature_rule.get('feature_name', feature_name),
                    'documentation_url': default_url,
                    'comment': default_comment
                }
            })
        
        # Check master rules if not found in regular rules
        elif feature_name == 'master':
            master_rules = rules_data.get('master', {})
            default_url = ""
            default_comment = ""
            
            if 'integration_steps' in master_rules and master_rules['integration_steps']:
                first_step = master_rules['integration_steps'][0]
                default_url = first_step.get('documentation_url', '')
                default_comment = first_step.get('comment', '')
            
            return jsonify({
                'success': True,
                'feature': {
                    'feature_name': 'Master Rules',
                    'documentation_url': default_url,
                    'comment': default_comment
                }
            })
        
        return jsonify({'success': False, 'error': 'Feature not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/feature-rules/<feature_name>/provider/<provider>/steps', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_provider_steps(feature_name, provider):
    """Handle provider-specific integration steps."""
    try:
        # Get current rules file
        rules_file = get_current_rules_file()
        
        # Load current rules
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            return jsonify({'success': False, 'error': 'Feature rule not found'})
        
        feature_rule = rules_data['rules'][feature_name]
        
        # Initialize by_provider if it doesn't exist
        if 'by_provider' not in feature_rule:
            feature_rule['by_provider'] = {}
        
        if request.method == 'GET':
            # Get provider steps
            provider_steps = feature_rule['by_provider'].get(provider, [])
            return jsonify({
                'success': True,
                'steps': provider_steps
            })
        
        elif request.method == 'POST':
            # Add new provider steps
            data = request.get_json() if request.is_json else {}
            
            # Parse form data if it's a form submission
            if not data:
                form_data = request.form.to_dict()
                provider_name = form_data.get('provider', provider)
                steps = []
                
                # Collect all step fields
                step_index = 0
                while True:
                    url_key = f'provider_step_url_{step_index}'
                    comment_key = f'provider_step_comment_{step_index}'
                    
                    url = form_data.get(url_key, '').strip()
                    comment = form_data.get(comment_key, '').strip()
                    
                    if not url and not comment:
                        break
                    
                    if url and comment:
                        steps.append({
                            'documentation_url': url,
                            'comment': comment
                        })
                    
                    step_index += 1
            else:
                provider_name = data.get('provider', provider)
                steps = data.get('steps', [])
            
            if not steps:
                return jsonify({'success': False, 'error': 'At least one step is required'})
            
            # Add or update provider steps
            feature_rule['by_provider'][provider_name] = steps
            
            # Save updated rules
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': f'Added {len(steps)} step(s) for {provider_name}'})
        
        elif request.method == 'PUT':
            # Update provider steps
            data = request.get_json() if request.is_json else {}
            
            # Parse form data if it's a form submission
            if not data:
                form_data = request.form.to_dict()
                steps = []
                
                # Collect all step fields
                step_index = 0
                while True:
                    url_key = f'provider_step_url_{step_index}'
                    comment_key = f'provider_step_comment_{step_index}'
                    
                    url = form_data.get(url_key, '').strip()
                    comment = form_data.get(comment_key, '').strip()
                    
                    if not url and not comment:
                        break
                    
                    if url and comment:
                        steps.append({
                            'documentation_url': url,
                            'comment': comment
                        })
                    
                    step_index += 1
            else:
                steps = data.get('steps', [])
            
            if not steps:
                return jsonify({'success': False, 'error': 'At least one step is required'})
            
            # Update provider steps
            feature_rule['by_provider'][provider] = steps
            
            # Save updated rules
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': f'Updated {len(steps)} step(s) for {provider}'})
        
        elif request.method == 'DELETE':
            # Delete provider steps
            if provider in feature_rule['by_provider']:
                del feature_rule['by_provider'][provider]
                
                # Save updated rules
                with open(rules_file, 'w', encoding='utf-8') as f:
                    json.dump(rules_data, f, indent=2, ensure_ascii=False)
                
                return jsonify({'success': True, 'message': f'Deleted steps for {provider}'})
            else:
                return jsonify({'success': False, 'error': f'No steps found for {provider}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/feature-rules/<feature_name>/payment-method/<payment_method>/steps', methods=['GET', 'PUT'])
def api_payment_method_steps(feature_name, payment_method):
    """Get or update integration steps for a payment method."""
    try:
        # Get current rules file
        rules_file = get_current_rules_file()
        
        # Load current rules
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if feature_name not in rules_data.get('rules', {}):
            return jsonify({'success': False, 'error': 'Feature rule not found'})
        
        feature_rule = rules_data['rules'][feature_name]
        
        if request.method == 'GET':
            # Get steps from by_payment_method
            steps = []
            if 'by_payment_method' in feature_rule:
                pm_config = feature_rule['by_payment_method'].get(payment_method, {})
                steps = pm_config.get('integration_steps', [])
            
            return jsonify({
                'success': True,
                'steps': steps
            })
        
        elif request.method == 'PUT':
            # Update integration steps
            data = request.get_json() if request.is_json else {}
            
            # Parse form data if it's a form submission
            if not data:
                form_data = request.form.to_dict()
                steps = []
                
                # Collect all step fields
                step_index = 0
                while True:
                    url_key = f'step_url_{step_index}'
                    comment_key = f'step_comment_{step_index}'
                    
                    url = form_data.get(url_key, '').strip()
                    comment = form_data.get(comment_key, '').strip()
                    
                    if not url and not comment:
                        break
                    
                    if url and comment:
                        steps.append({
                            'documentation_url': url,
                            'comment': comment
                        })
                    
                    step_index += 1
            else:
                steps = data.get('steps', [])
            
            if not steps:
                return jsonify({'success': False, 'error': 'At least one step is required'})
            
            # Ensure by_payment_method structure exists
            if 'by_payment_method' not in feature_rule:
                feature_rule['by_payment_method'] = {}
            
            if payment_method not in feature_rule['by_payment_method']:
                feature_rule['by_payment_method'][payment_method] = {
                    'testcases': [],
                    'integration_steps': []
                }
            
            # Update integration steps
            feature_rule['by_payment_method'][payment_method]['integration_steps'] = steps
            
            # Save updated rules
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': f'Updated {len(steps)} integration step(s) for {feature_name} - {payment_method}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/feature-rules/master/steps', methods=['GET', 'PUT'])
def api_master_steps():
    """Handle master integration steps (universal)."""
    try:
        # Get current rules file
        rules_file = get_current_rules_file()
        
        # Load current rules
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if 'master' not in rules_data:
            rules_data['master'] = {}
        
        master_rules = rules_data['master']
        
        if request.method == 'GET':
            # Get master steps
            steps = master_rules.get('integration_steps', [])
            return jsonify({
                'success': True,
                'steps': steps
            })
        
        elif request.method == 'PUT':
            # Update master steps
            data = request.get_json() if request.is_json else {}
            
            # Parse form data if it's a form submission
            if not data:
                form_data = request.form.to_dict()
                steps = []
                
                # Collect all step fields
                step_index = 0
                while True:
                    url_key = f'step_url_{step_index}'
                    comment_key = f'step_comment_{step_index}'
                    
                    url = form_data.get(url_key, '').strip()
                    comment = form_data.get(comment_key, '').strip()
                    
                    if not url and not comment:
                        break
                    
                    if url and comment:
                        steps.append({
                            'documentation_url': url,
                            'comment': comment
                        })
                    
                    step_index += 1
            else:
                steps = data.get('steps', [])
            
            if not steps:
                return jsonify({'success': False, 'error': 'At least one step is required'})
            
            # Update master steps
            master_rules['integration_steps'] = steps
            
            # Save updated rules
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': f'Updated {len(steps)} master step(s)'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/feature-rules-files', methods=['GET', 'POST'])
def api_feature_rules_files():
    """List or create feature rules files."""
    try:
        if request.method == 'GET':
            # List available rules files
            available_rules_files = []
            # Always include default
            if os.path.exists('feature_rules.json'):
                available_rules_files.append({
                    'filename': 'feature_rules.json',
                    'name': 'Default',
                    'path': 'feature_rules.json'
                })
            
            # Get provider-specific files
            provider_files = RulesManager.get_provider_rules_files()
            for file_path in provider_files:
                filename = os.path.basename(file_path)
                if filename.startswith('feature_rules_') and filename.endswith('.json'):
                    provider = filename[14:-5]
                    available_rules_files.append({
                        'filename': filename,
                        'name': provider,
                        'path': file_path
                    })
            
            return jsonify({
                'success': True,
                'rules_files': available_rules_files
            })
        
        elif request.method == 'POST':
            # Create a new feature rules file
            data = request.get_json() if request.is_json else {}
            
            # Get file name from request
            file_name = data.get('name', '').strip()
            if not file_name:
                return jsonify({'success': False, 'error': 'File name is required'})
            
            # Sanitize file name (only alphanumeric, underscore, hyphen)
            import re
            file_name = re.sub(r'[^a-zA-Z0-9_-]', '', file_name)
            if not file_name:
                return jsonify({'success': False, 'error': 'Invalid file name'})
            
            # Create filename
            new_filename = f'feature_rules_{file_name}.json'
            
            # Check if file already exists
            if os.path.exists(new_filename):
                return jsonify({'success': False, 'error': f'File "{new_filename}" already exists'})
            
            # Load default feature_rules.json as template
            template_data = {
                'version': '1.0.0',
                'last_updated': '',
                'metadata': {
                    'total_rules': 0,
                    'categories': [],
                    'testcase_types': ['happy path', 'unhappy path', 'corner case'],
                    'environments': ['both', 'sandbox', 'production'],
                    'i18n': {
                        'supported_locales': ['en', 'es', 'pt']
                    }
                },
                'master': {
                    'integration_steps': [],
                    'testcases': []
                },
                'rules': {}
            }
            
            # If default file exists, use it as template
            if os.path.exists('feature_rules.json'):
                try:
                    with open('feature_rules.json', 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    # Clear rules but keep structure
                    template_data['rules'] = {}
                    template_data['metadata']['total_rules'] = 0
                    template_data['metadata']['categories'] = []
                except:
                    pass  # Use default template
            
            # Add metadata about the file
            from datetime import datetime
            template_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            template_data['metadata']['file_name'] = file_name
            template_data['metadata']['description'] = data.get('description', f'Feature rules for {file_name}')
            
            # Save new file
            with open(new_filename, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'filename': new_filename,
                'path': new_filename,
                'message': f'Successfully created feature rules file: {new_filename}'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Helper function to get current rules file from request
def get_current_rules_file():
    """Get the current rules file from request args, form data, or session."""
    # Try to get from request args first (for GET requests)
    rules_file = request.args.get('rules_file') or request.args.get('file')
    
    # Try to get from form data (for POST requests)
    if not rules_file and request.is_json:
        data = request.get_json() if request.is_json else {}
        rules_file = data.get('rules_file')
    
    # Try to get from form data (for form submissions)
    if not rules_file:
        rules_file = request.form.get('rules_file')
    
    # Fall back to session
    if not rules_file:
        rules_file = session.get('current_rules_file', 'feature_rules.json')
    
    # Validate file name
    if not rules_file.endswith('.json') or '/' in rules_file or '..' in rules_file:
        rules_file = 'feature_rules.json'
    
    # Check if file exists
    if not os.path.exists(rules_file):
        rules_file = 'feature_rules.json'
    
    # Store in session for next request
    session['current_rules_file'] = rules_file
    
    return rules_file

@app.route('/api/feature-rules/master/provider/<provider>/steps', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_master_provider_steps(provider):
    """Handle provider-specific master integration steps."""
    try:
        # Get current rules file
        rules_file = get_current_rules_file()
        
        # Load current rules
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        if 'master' not in rules_data:
            rules_data['master'] = {}
        
        master_rules = rules_data['master']
        
        # Initialize by_provider if it doesn't exist
        if 'by_provider' not in master_rules:
            master_rules['by_provider'] = {}
        
        if request.method == 'GET':
            # Get provider steps
            provider_steps = master_rules['by_provider'].get(provider, [])
            return jsonify({
                'success': True,
                'steps': provider_steps
            })
        
        elif request.method == 'POST':
            # Add new provider steps
            data = request.get_json() if request.is_json else {}
            
            # Parse form data if it's a form submission
            if not data:
                form_data = request.form.to_dict()
                provider_name = form_data.get('provider', provider)
                steps = []
                
                # Collect all step fields
                step_index = 0
                while True:
                    url_key = f'provider_step_url_{step_index}'
                    comment_key = f'provider_step_comment_{step_index}'
                    
                    url = form_data.get(url_key, '').strip()
                    comment = form_data.get(comment_key, '').strip()
                    
                    if not url and not comment:
                        break
                    
                    if url and comment:
                        steps.append({
                            'documentation_url': url,
                            'comment': comment
                        })
                    
                    step_index += 1
            else:
                provider_name = data.get('provider', provider)
                steps = data.get('steps', [])
            
            if not steps:
                return jsonify({'success': False, 'error': 'At least one step is required'})
            
            # Add or update provider steps
            master_rules['by_provider'][provider_name] = steps
            
            # Save updated rules
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': f'Added {len(steps)} master step(s) for {provider_name}'})
        
        elif request.method == 'PUT':
            # Update provider steps
            data = request.get_json() if request.is_json else {}
            
            # Parse form data if it's a form submission
            if not data:
                form_data = request.form.to_dict()
                steps = []
                
                # Collect all step fields
                step_index = 0
                while True:
                    url_key = f'provider_step_url_{step_index}'
                    comment_key = f'provider_step_comment_{step_index}'
                    
                    url = form_data.get(url_key, '').strip()
                    comment = form_data.get(comment_key, '').strip()
                    
                    if not url and not comment:
                        break
                    
                    if url and comment:
                        steps.append({
                            'documentation_url': url,
                            'comment': comment
                        })
                    
                    step_index += 1
            else:
                steps = data.get('steps', [])
            
            if not steps:
                return jsonify({'success': False, 'error': 'At least one step is required'})
            
            # Update provider steps
            master_rules['by_provider'][provider] = steps
            
            # Save updated rules
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': f'Updated {len(steps)} master step(s) for {provider}'})
        
        elif request.method == 'DELETE':
            # Delete provider steps
            if provider in master_rules['by_provider']:
                del master_rules['by_provider'][provider]
                
                # Save updated rules
                with open(rules_file, 'w', encoding='utf-8') as f:
                    json.dump(rules_data, f, indent=2, ensure_ascii=False)
                
                return jsonify({'success': True, 'message': f'Deleted master steps for {provider}'})
            else:
                return jsonify({'success': False, 'error': f'No master steps found for {provider}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = 5001
    
    print(f"🌐 Starting Implementation Scoping Document Parser on http://localhost:{port}")
    print(f"📋 Open your browser and go to: http://localhost:{port}")
    print("⏹️  Press Ctrl+C to stop the server")
    print("🔄 Auto-reload enabled: Changes to Python files and templates will reload automatically")
    print("   (Note: JSON files like feature_rules.json are read on each request, no restart needed)")
    
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True, use_debugger=True) 
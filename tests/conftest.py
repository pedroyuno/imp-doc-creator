#!/usr/bin/env python3
"""
Shared pytest fixtures and configuration
"""

import pytest
import os
import sys
import tempfile
from io import BytesIO

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import app


@pytest.fixture(scope="session")
def flask_app():
    """Create and configure a new app instance for each test session."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'
    return app


@pytest.fixture(scope="function")
def client(flask_app):
    """A test client for the app."""
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client


@pytest.fixture
def sample_csv_bytes():
    """Standard sample CSV content as bytes for testing."""
    content = """,Feature,TEST_PROVIDER,,,ANOTHER_PROVIDER,,,
,Provider,TEST,,,ANOTHER,,,
,Payment_Method,CARD,,,PIX,,,
,,INFORMATION,STATUS,ADDITIONAL INFO,INFORMATION,STATUS,ADDITIONAL INFO
,Country,Brazil,Supported,,Brazil,Supported,
,Verify,TRUE,Implemented,,FALSE,Not supported,
,Authorize,TRUE,Implemented,,TRUE,Implemented,
,Capture,TRUE,Implemented,,FALSE,Not applicable,
,Purchase,TRUE,Implemented,,TRUE,Implemented,
,Refund,TRUE,Implemented,,TRUE,Implemented,"""
    return content.encode('utf-8')


@pytest.fixture
def empty_csv_bytes():
    """Empty CSV content for testing edge cases."""
    return b""


@pytest.fixture
def invalid_csv_bytes():
    """Invalid CSV content with no valid providers."""
    content = """,Feature,[Provider],,,
,Provider,#N/A,,,
,Payment_Method,#N/A,,,
,,INFO,STATUS,ADDITIONAL INFO
,Country,Brazil,,,"""
    return content.encode('utf-8')


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    content = """,Feature,TEMP_PROVIDER
,Provider,TEMP_TEST
,Payment_Method,CARD
,,INFO
,Country,Brazil
,Verify,TRUE
,Features,Multiple"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def uploaded_file_data():
    """Helper fixture to create file upload data."""
    def _create_upload_data(content, filename='test.csv'):
        return {'file': (BytesIO(content), filename)}
    return _create_upload_data


# Test markers for organizing tests
pytest_plugins = []

# Configure test collection
def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and name."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark web tests
        if "web_app" in item.nodeid or "test_web" in item.name:
            item.add_marker(pytest.mark.web)
        
        # Mark API tests
        if "api" in item.name.lower():
            item.add_marker(pytest.mark.api)
        
        # Mark unit tests (everything else)
        if not any(marker.name in ['integration', 'web'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# Coverage configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "web: marks tests as web interface tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    ) 
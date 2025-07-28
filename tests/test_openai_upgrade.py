"""
Test to verify OpenAI upgrade compatibility.

This test verifies that the upgraded openai package is compatible
with the existing codebase and resolves the httpx compatibility issue.
"""
import pytest
import openai
from unittest.mock import patch
import sys
import os

# Add src to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_openai_client_creation():
    """Test that OpenAI client can be created without the proxies error."""
    try:
        # This should not raise TypeError about 'proxies' parameter
        client = openai.AsyncOpenAI(
            api_key="test-key",
            base_url="http://localhost:8080"
        )
        assert client is not None
        assert hasattr(client, 'chat')
    except TypeError as e:
        if "'proxies'" in str(e):
            pytest.fail(f"OpenAI client creation failed with proxies error: {e}")
        else:
            # Re-raise if it's a different TypeError
            raise

def test_openai_version_compatibility():
    """Test that the OpenAI version is >= 1.47.0."""
    from packaging import version
    
    current_version = version.parse(openai.__version__)
    min_version = version.parse("1.47.0")
    
    assert current_version >= min_version, f"OpenAI version {openai.__version__} is less than required 1.47.0"

def test_azure_openai_client_creation():
    """Test that Azure OpenAI client can be created."""
    try:
        # Test Azure OpenAI client creation
        client = openai.AsyncAzureOpenAI(
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
            api_version="2024-02-01"
        )
        assert client is not None
        assert hasattr(client, 'chat')
    except TypeError as e:
        if "'proxies'" in str(e):
            pytest.fail(f"Azure OpenAI client creation failed with proxies error: {e}")
        else:
            # Re-raise if it's a different TypeError
            raise

@patch('openai.AsyncOpenAI')
def test_api_initialization_compatibility(mock_openai):
    """Test that our API initialization code is compatible with new OpenAI version."""
    from api import create_app
    
    # This should not fail during app creation
    app = create_app()
    assert app is not None
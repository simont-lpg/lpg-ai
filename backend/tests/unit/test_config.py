import pytest
from pydantic import ValidationError
from backend.app.config import Settings
import os
import tempfile
from pathlib import Path

def test_valid_settings():
    """Test valid settings configuration."""
    settings = Settings(
        embedding_model="all-MiniLM-L6-v2",
        embedding_dim=384,
        ollama_api_url="http://localhost:11434",
        dev_mode=False
    )
    assert settings.embedding_model == "all-MiniLM-L6-v2"
    assert settings.embedding_dim == 384
    assert str(settings.ollama_api_url).rstrip("/") == "http://localhost:11434"
    assert settings.dev_mode is False

def test_invalid_embedding_dim():
    """Test validation of invalid embedding dimensions."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(embedding_dim=-1)
    assert "Input should be greater than 0" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        Settings(embedding_dim=0)
    assert "Input should be greater than 0" in str(exc_info.value)

def test_invalid_ollama_url():
    """Test validation of invalid Ollama API URLs."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(ollama_api_url="not_a_url")
    assert "Input should be a valid URL" in str(exc_info.value)
    
    with pytest.raises(ValidationError) as exc_info:
        Settings(ollama_api_url="ftp://invalid.com")
    assert "URL scheme should be 'http' or 'https'" in str(exc_info.value)

def test_default_settings():
    """Test default settings values."""
    settings = Settings()
    assert settings.embedding_model == "all-MiniLM-L6-v2"
    assert settings.embedding_dim == 384
    assert str(settings.ollama_api_url).rstrip("/") == "http://127.0.0.1:11434"
    assert settings.collection_name == "documents"
    assert settings.dev_mode is False
    assert str(settings.ollama_api_url) == "http://127.0.0.1:11434/"

def test_settings_from_env():
    """Test settings from environment variables."""
    # Create a temporary .env file
    env_content = """
HAYSTACK_EMBEDDING_MODEL=custom/model
HAYSTACK_EMBEDDING_DIM=512
HAYSTACK_COLLECTION_NAME=custom_collection
HAYSTACK_DEV_MODE=true
HAYSTACK_OLLAMA_API_URL=http://localhost:11434
    """.strip()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_env:
        temp_env.write(env_content)
        temp_env.flush()
        
        try:
            # Create settings with the temporary .env file
            settings = Settings.from_env_file(temp_env.name)
            
            assert settings.embedding_model == "custom/model"
            assert settings.embedding_dim == 512
            assert str(settings.ollama_api_url).rstrip("/") == "http://localhost:11434"
            assert settings.collection_name == "custom_collection"
            assert settings.dev_mode is True
            assert str(settings.ollama_api_url) == "http://localhost:11434/"
        finally:
            # Clean up the temporary file
            os.unlink(temp_env.name)

def test_config_validation():
    """Test configuration validation."""
    # Test invalid embedding dimension
    with pytest.raises(ValidationError):
        Settings(embedding_dim=-1)
    
    # Test invalid URL
    with pytest.raises(ValidationError):
        Settings(ollama_api_url="not-a-url")
    
    # Test invalid model name
    with pytest.raises(ValidationError):
        Settings(embedding_model=123) 
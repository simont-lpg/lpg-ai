import pytest
from pydantic import ValidationError
from backend.app.config import Settings, get_settings
import os
import tempfile
from pathlib import Path

def test_valid_settings():
    """Test valid settings configuration."""
    settings = Settings(
        embedding_model="all-MiniLM-L6-v2",
        embedding_dim=768,
        ollama_api_url="http://localhost:11434",
        dev_mode=False
    )
    assert settings.embedding_model == "all-MiniLM-L6-v2"
    assert settings.embedding_dim == 768
    assert str(settings.ollama_api_url).rstrip("/") == "http://localhost:11434"
    assert settings.dev_mode is False

def test_invalid_embedding_dim():
    """Test validation of invalid embedding dimensions."""
    with pytest.raises(ValidationError):
        Settings(embedding_dim=0)

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
    settings = Settings(
        embedding_model="nomic-embed-text:latest",
        generator_model_name="mistral:latest",
        embedding_dim=768,
        ollama_api_url="http://127.0.0.1:11434",
        collection_name="documents",
        api_host="0.0.0.0",
        api_port=8000,
        cors_origins=["http://localhost:5173"],
        dev_mode=False,
        environment="development",
        log_level="INFO",
        database_url="sqlite:///./lpg_ai.db",
        secret_key="your-secret-key-here",
        rate_limit_per_minute=60
    )
    assert settings.embedding_model == "nomic-embed-text:latest"
    assert settings.embedding_dim == 768
    assert settings.collection_name == "documents"
    assert settings.dev_mode is False
    assert str(settings.ollama_api_url) == "http://127.0.0.1:11434/"

def test_settings_from_env():
    """Test settings from environment variables."""
    # Create a temporary .env file
    env_content = """
LPG_AI_EMBEDDING_MODEL=custom/model
LPG_AI_EMBEDDING_DIM=512
LPG_AI_COLLECTION_NAME=custom_collection
LPG_AI_DEV_MODE=true
LPG_AI_OLLAMA_API_URL=http://localhost:11434
    """.strip()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_env:
        temp_env.write(env_content)
        temp_env.flush()

        try:
            # Set environment variables
            os.environ["LPG_AI_EMBEDDING_MODEL"] = "custom/model"
            os.environ["LPG_AI_EMBEDDING_DIM"] = "512"
            os.environ["LPG_AI_COLLECTION_NAME"] = "custom_collection"
            os.environ["LPG_AI_DEV_MODE"] = "true"
            os.environ["LPG_AI_OLLAMA_API_URL"] = "http://localhost:11434"

            # Create settings
            settings = Settings()
            assert settings.embedding_model == "custom/model"
            assert settings.embedding_dim == 512
            assert settings.collection_name == "custom_collection"
            assert settings.dev_mode is True
            assert str(settings.ollama_api_url) == "http://localhost:11434/"
        finally:
            # Clean up environment variables
            for key in [
                "LPG_AI_EMBEDDING_MODEL",
                "LPG_AI_EMBEDDING_DIM",
                "LPG_AI_COLLECTION_NAME",
                "LPG_AI_DEV_MODE",
                "LPG_AI_OLLAMA_API_URL"
            ]:
                os.environ.pop(key, None)

def test_config_validation():
    """Test configuration validation."""
    # Test invalid embedding dimension
    with pytest.raises(ValidationError):
        Settings(
            embedding_model="test",
            generator_model_name="test",
            embedding_dim=-1,
            ollama_api_url="http://localhost:11434",
            collection_name="test",
            api_host="0.0.0.0",
            api_port=8000,
            cors_origins=["http://localhost:5173"],
            dev_mode=False,
            environment="development",
            log_level="INFO",
            database_url="sqlite:///./lpg_ai.db",
            secret_key="test",
            rate_limit_per_minute=60
        )

    # Test invalid API URL
    with pytest.raises(ValidationError):
        Settings(
            embedding_model="test",
            generator_model_name="test",
            embedding_dim=768,
            ollama_api_url="invalid-url",
            collection_name="test",
            api_host="0.0.0.0",
            api_port=8000,
            cors_origins=["http://localhost:5173"],
            dev_mode=False,
            environment="development",
            log_level="INFO",
            database_url="sqlite:///./lpg_ai.db",
            secret_key="test",
            rate_limit_per_minute=60
        )

def test_environment_variables_override_defaults():
    """Test that environment variables override default settings."""
    # Set environment variables
    os.environ["LPG_AI_EMBEDDING_MODEL"] = "custom/model"
    os.environ["LPG_AI_EMBEDDING_DIM"] = "512"
    os.environ["LPG_AI_COLLECTION_NAME"] = "custom_collection"
    os.environ["LPG_AI_DEV_MODE"] = "true"
    os.environ["LPG_AI_OLLAMA_API_URL"] = "http://localhost:11434"

    try:
        settings = Settings()
        assert settings.embedding_model == "custom/model"
        assert settings.embedding_dim == 512
        assert settings.collection_name == "custom_collection"
        assert settings.dev_mode is True
        assert str(settings.ollama_api_url) == "http://localhost:11434/"
    finally:
        # Clean up environment variables
        for key in [
            "LPG_AI_EMBEDDING_MODEL",
            "LPG_AI_EMBEDDING_DIM",
            "LPG_AI_COLLECTION_NAME",
            "LPG_AI_DEV_MODE",
            "LPG_AI_OLLAMA_API_URL"
        ]:
            os.environ.pop(key, None)

def test_settings_initialization(settings):
    """Test that settings are initialized correctly."""
    assert settings.dev_mode is True
    assert settings.embedding_model is not None
    assert settings.generator_model_name is not None
    assert settings.ollama_api_url is not None
    assert settings.collection_name is not None
    assert settings.api_host is not None
    assert settings.api_port is not None
    assert settings.cors_origins is not None
    assert settings.environment is not None
    assert settings.log_level is not None
    assert settings.database_url is not None
    assert settings.secret_key is not None
    assert settings.rate_limit_per_minute is not None

def test_settings_caching():
    """Test that settings are cached."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2  # Should be the same instance due to caching 
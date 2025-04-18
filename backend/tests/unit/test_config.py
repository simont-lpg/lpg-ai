import os
import pytest
from app.config import Settings

def test_settings_default_values():
    """Test that Settings has correct default values."""
    settings = Settings()
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.chroma_db_path == "data/chroma"
    assert settings.vectorstore_type == "chroma"

def test_settings_from_env():
    """Test that Settings picks up environment variables."""
    os.environ["HAYSTACK_EMBEDDING_MODEL"] = "custom/model"
    os.environ["HAYSTACK_CHROMA_DB_PATH"] = "custom/path"
    os.environ["HAYSTACK_VECTORSTORE_TYPE"] = "custom"
    
    settings = Settings()
    assert settings.embedding_model == "custom/model"
    assert settings.chroma_db_path == "custom/path"
    assert settings.vectorstore_type == "custom"
    
    # Clean up
    del os.environ["HAYSTACK_EMBEDDING_MODEL"]
    del os.environ["HAYSTACK_CHROMA_DB_PATH"]
    del os.environ["HAYSTACK_VECTORSTORE_TYPE"]

def test_config_parsing():
    settings = Settings()
    assert settings.vectorstore_type == "chroma"
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.dev_mode is False 
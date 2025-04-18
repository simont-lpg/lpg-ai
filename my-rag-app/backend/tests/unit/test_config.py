import os
from pathlib import Path

import pytest

from app.config import Settings, settings


def test_settings_defaults():
    """Test that settings have correct default values."""
    assert settings.chroma_persist_dir == Path("chroma_data")
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.dev_mode is False
    assert settings.embedding_model == "sentence-transformers/all-mpnet-base-v2"
    assert settings.embedding_dim == 768


def test_settings_env_override(monkeypatch):
    """Test that environment variables override defaults."""
    monkeypatch.setenv("CHROMA_PERSIST_DIR", "/custom/path")
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("DEV_MODE", "true")
    
    custom_settings = Settings()
    
    assert custom_settings.chroma_persist_dir == Path("/custom/path")
    assert custom_settings.api_host == "127.0.0.1"
    assert custom_settings.api_port == 9000
    assert custom_settings.dev_mode is True


def test_settings_env_file(tmp_path):
    """Test loading settings from .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("""
    CHROMA_PERSIST_DIR=/env/path
    API_HOST=localhost
    API_PORT=8080
    DEV_MODE=true
    """)
    
    custom_settings = Settings(_env_file=env_file)
    
    assert custom_settings.chroma_persist_dir == Path("/env/path")
    assert custom_settings.api_host == "localhost"
    assert custom_settings.api_port == 8080
    assert custom_settings.dev_mode is True 
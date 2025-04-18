from app.vectorstore import get_vectorstore
from app.config import Settings
import pytest
import os

def test_vectorstore_initialization():
    """Test basic vectorstore initialization with default settings."""
    settings = Settings()
    vectorstore = get_vectorstore(settings)
    assert vectorstore is not None
    assert vectorstore._collection is not None
    assert vectorstore._collection.name == "documents"

def test_vectorstore_custom_collection():
    """Test vectorstore initialization with custom collection name."""
    settings = Settings()
    settings.chroma_collection_name = "custom_collection"
    vectorstore = get_vectorstore(settings)
    assert vectorstore._collection.name == "custom_collection"

def test_vectorstore_invalid_path():
    """Test vectorstore initialization with invalid path."""
    settings = Settings()
    settings.chroma_db_path = "/invalid/path/that/does/not/exist"
    with pytest.raises(ValueError, match="Chroma database path does not exist"):
        get_vectorstore(settings)

def test_vectorstore_missing_env():
    """Test vectorstore initialization when required env vars are missing."""
    # Save original env var
    original_path = os.environ.get("HAYSTACK_CHROMA_DB_PATH")
    if original_path:
        del os.environ["HAYSTACK_CHROMA_DB_PATH"]
    
    settings = Settings()
    settings.chroma_db_path = None
    with pytest.raises(ValueError, match="Chroma database path must be set"):
        get_vectorstore(settings)
    
    # Restore original env var
    if original_path:
        os.environ["HAYSTACK_CHROMA_DB_PATH"] = original_path
    # Add more specific assertions based on your vectorstore implementation 
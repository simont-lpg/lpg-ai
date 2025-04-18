import pytest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock
import numpy as np
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import Settings

# Get the absolute path to the project root
root_dir = Path(__file__).parent.parent

# Add the project root to the Python path
sys.path.insert(0, str(root_dir))

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    mock = MagicMock()
    mock.embed_batch.return_value = [np.zeros(384) for _ in range(1)]
    mock.encode.return_value = np.zeros(384)
    return mock

@pytest.fixture
def mock_vectorstore():
    """Mock vectorstore for testing."""
    mock = MagicMock()
    mock.query_by_embedding.return_value = [
        MagicMock(content="test content", metadata={"score": 0.9})
    ]
    return mock

@pytest.fixture
def settings():
    """Test settings."""
    return Settings(dev_mode=True)

@pytest.fixture
def client(mock_embeddings, mock_vectorstore):
    """Test client with mocked dependencies."""
    from backend.app.dependencies import get_embedder, get_document_store
    
    def mock_get_embedder():
        return mock_embeddings
    
    def mock_get_document_store():
        return mock_vectorstore
    
    app.dependency_overrides[get_embedder] = mock_get_embedder
    app.dependency_overrides[get_document_store] = mock_get_document_store
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides = {}

def pytest_configure(config):
    """Register custom marks."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    ) 
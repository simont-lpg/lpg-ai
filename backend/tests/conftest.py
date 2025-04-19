import pytest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock
import numpy as np
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import Settings
from backend.app.schema import DocumentFull
from backend.app.vectorstore import InMemoryDocumentStore
from typing import List

# Get the absolute path to the project root
root_dir = Path(__file__).parent.parent

# Add the project root to the Python path
sys.path.insert(0, str(root_dir))

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def encode(self, text):
            return np.zeros(384)  # Return zero vector
        def embed_batch(self, texts):
            return [np.zeros(384) for _ in texts]  # Return zero vectors
    return MockEmbeddings()

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

@pytest.fixture
def dummy_docs() -> List[DocumentFull]:
    """Create dummy documents for testing."""
    return [
        DocumentFull(id="1", content="A", meta={"namespace": "foo"}),
        DocumentFull(id="2", content="B", meta={"namespace": "foo"}),
        DocumentFull(id="3", content="C", meta={"namespace": "bar"})
    ]

@pytest.fixture
def mock_store(mock_embeddings):
    """Create a mock document store for testing."""
    return InMemoryDocumentStore(
        embedding_dim=384,
        collection_name="test_documents",
        embeddings_model=mock_embeddings
    )

def pytest_configure(config):
    """Register custom marks."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    ) 
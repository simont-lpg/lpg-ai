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
def mock_embeddings(settings):
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def encode(self, text):
            return np.zeros(settings.embedding_dim)  # Return zero vector
        def embed_batch(self, texts):
            return np.zeros((len(texts), settings.embedding_dim))  # Return zero vectors
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
    return Settings(
        embedding_model="all-MiniLM-L6-v2",
        generator_model_name="mistral:latest",
        embedding_dim=768,
        ollama_api_url="http://localhost:11434",
        collection_name="test_collection",
        api_host="0.0.0.0",
        api_port=8000,
        cors_origins=["*"],
        dev_mode=True,
        environment="test",
        log_level="INFO",
        database_url="sqlite:///./test.db",
        secret_key="test_secret",
        rate_limit_per_minute=60,
        default_top_k=5,
        prompt_template="""Based on the following context, please answer the question. If the answer cannot be found in the context, say "I don't know."

Context:
{context}

Question: {query}

Answer:""",
        pipeline_parameters={
            "Retriever": {
                "top_k": 5,
                "score_threshold": 0.7
            },
            "Generator": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
    )

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
def mock_store(mock_embeddings, settings):
    """Create a mock document store for testing."""
    return InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )

def pytest_configure(config):
    """Register custom marks."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )

class MockEmbedder:
    def __init__(self):
        self.embedding_dim = 768

    def embed_documents(self, documents: List[str]) -> List[np.ndarray]:
        return [np.random.rand(self.embedding_dim) for _ in documents]

    def embed_query(self, query: str) -> np.ndarray:
        return np.random.rand(self.embedding_dim) 
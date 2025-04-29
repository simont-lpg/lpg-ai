import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from backend.app.main import app
from backend.app.config import Settings
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.schema import DocumentFull, Query
from backend.app.dependencies import get_document_store, get_embedder
from sentence_transformers import SentenceTransformer
import tempfile
import os
import numpy as np
from unittest.mock import MagicMock

@pytest.fixture
def test_settings(settings):
    """Get test settings."""
    return settings

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def encode(self, text):
            return np.zeros(768)  # Return zero vector
        def embed_batch(self, texts):
            return np.zeros((len(texts), 768))  # Return zero vectors with correct shape
    return MockEmbeddings()

@pytest.fixture
def mock_store(mock_embeddings, test_settings):
    """Create a mock document store for testing."""
    return InMemoryDocumentStore(
        embedding_dim=test_settings.embedding_dim,
        collection_name=test_settings.collection_name,
        embeddings_model=mock_embeddings
    )

@pytest.fixture
def test_app(test_settings, mock_store):
    """Create a test app with overridden dependencies."""
    # Override the document store dependency
    async def override_get_document_store():
        return mock_store
    
    # Override the embedder dependency
    async def override_get_embedder():
        return SentenceTransformer(test_settings.embedding_model)
    
    app.dependency_overrides[get_document_store] = override_get_document_store
    app.dependency_overrides[get_embedder] = override_get_embedder
    return app

@pytest.fixture
def client(mock_embeddings, mock_store):
    """Test client with mocked dependencies."""
    app.dependency_overrides[get_embedder] = lambda: mock_embeddings
    app.dependency_overrides[get_document_store] = lambda: mock_store
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides = {}

@pytest.fixture
def test_document():
    return DocumentFull(
        content="Hello world",
        meta={"namespace": "test_ns", "file_name": "test.txt"},
        id="test1"
    )

def test_end_to_end_query_with_namespace(test_settings, mock_store):
    """Test end-to-end query with namespace filtering."""
    # Add test documents with different namespaces
    docs = [
        DocumentFull(
            content="Test document 1",
            id="1",
            meta={"namespace": "test1"},
            embedding=np.array([0.1] * test_settings.embedding_dim)
        ),
        DocumentFull(
            content="Test document 2",
            id="2",
            meta={"namespace": "test2"},
            embedding=np.array([0.1] * test_settings.embedding_dim)
        )
    ]
    mock_store.write_documents(docs)

    # Verify documents were added
    assert len(mock_store.documents) == 2
    assert len(mock_store.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in mock_store.embeddings)
    assert all(emb.shape[0] == test_settings.embedding_dim for emb in mock_store.embeddings)

    # Test query with namespace filter
    query_embedding = np.array([0.1] * test_settings.embedding_dim)
    results = mock_store.query_by_embedding(
        query_embedding,
        top_k=1,
        filters={"namespace": "test1"}
    )
    assert len(results) == 1
    assert results[0].meta["namespace"] == "test1"

def test_query_end_to_end(client, mock_store):
    """Test the query endpoint with mocked dependencies."""
    # Add test document
    doc = DocumentFull(
        id="1",
        content="Test content",
        meta={"namespace": "test"},
        embedding=[0.1] * 768
    )
    mock_store.write_documents([doc])
    
    # Test query
    response = client.post(
        "/query",
        json={
            "text": "test query",
            "top_k": 5,
            "namespace": "test"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "answers" in data
    assert "documents" in data
    assert len(data["documents"]) == 1
    assert data["documents"][0]["content"] == "Test content"

def test_query_with_namespace(client, mock_store):
    """Test query with namespace filtering."""
    # Add test documents with different namespaces
    docs = [
        DocumentFull(
            id="1",
            content="Test content 1",
            meta={"namespace": "test1"},
            embedding=[0.1] * 768
        ),
        DocumentFull(
            id="2",
            content="Test content 2",
            meta={"namespace": "test2"},
            embedding=[0.1] * 768
        )
    ]
    mock_store.write_documents(docs)
    
    # Test query with namespace filter
    response = client.post(
        "/query",
        json={
            "text": "test query",
            "top_k": 5,
            "namespace": "test1"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 1
    assert data["documents"][0]["meta"]["namespace"] == "test1" 
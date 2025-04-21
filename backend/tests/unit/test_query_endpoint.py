import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from backend.app.main import app
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.schema import DocumentFull
from backend.app.config import Settings
from backend.app.dependencies import get_document_store, get_embedder
from sentence_transformers import SentenceTransformer
from unittest.mock import MagicMock, patch
import numpy as np

@pytest.fixture
def test_document():
    return DocumentFull(
        content="Hello world",
        meta={"namespace": "default", "file_name": "test.txt"},
        id="test1"
    )

@pytest.fixture
def test_settings():
    return Settings(
        embedding_model="all-MiniLM-L6-v2",
        embedding_dim=384,
        collection_name="test_collection"
    )

@pytest.fixture
def mock_embeddings():
    mock = MagicMock()
    mock.encode.return_value = np.random.rand(384).tolist()
    return mock

@pytest.fixture
def mock_store():
    store = MagicMock()
    store.embedding_dim = 384
    store.collection_name = "test_collection"
    store.query_by_embedding.return_value = [
        DocumentFull(
            content="Hello world",
            meta={"namespace": "default", "file_name": "test.txt"},
            id="test1"
        )
    ]
    return store

@pytest.fixture
def test_app(test_settings, mock_store, mock_embeddings):
    """Create a test app with overridden dependencies."""
    # Override the document store dependency
    async def override_get_document_store():
        return mock_store
    
    # Override the embedder dependency
    async def override_get_embedder():
        return mock_embeddings
    
    app.dependency_overrides[get_document_store] = override_get_document_store
    app.dependency_overrides[get_embedder] = override_get_embedder
    return app

@pytest.fixture
def client(test_app):
    return TestClient(test_app)

def test_query_without_namespace(client, mock_store):
    """Test query without namespace falls back to default namespace."""
    # Query without namespace
    response = client.post(
        "/query",
        json={
            "text": "Hello world",
            "top_k": 1
        }
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result["documents"]) == 1
    assert result["documents"][0]["content"] == "Hello world"
    assert result["documents"][0]["meta"]["namespace"] == "default"
    
    # Verify mock was called with correct parameters
    mock_store.query_by_embedding.assert_called_once()
    call_args = mock_store.query_by_embedding.call_args[1]
    assert call_args["filters"] == {"namespace": "default"}
    assert call_args["top_k"] == 1

def test_query_with_explicit_namespace(client, mock_store):
    """Test query with explicit namespace."""
    # Query with explicit namespace
    response = client.post(
        "/query",
        json={
            "text": "Hello world",
            "top_k": 1,
            "namespace": "test_ns"
        }
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result["documents"]) == 1
    assert result["documents"][0]["content"] == "Hello world"
    assert result["documents"][0]["meta"]["namespace"] == "default"
    
    # Verify mock was called with correct parameters
    mock_store.query_by_embedding.assert_called_once()
    call_args = mock_store.query_by_embedding.call_args[1]
    assert call_args["filters"] == {"namespace": "test_ns"}
    assert call_args["top_k"] == 1

def test_query_pipeline_error(client, mock_store):
    """Test query endpoint handles pipeline errors gracefully."""
    # Make the mock store raise an exception
    mock_store.query_by_embedding.side_effect = Exception("Test error")
    
    response = client.post(
        "/query",
        json={
            "text": "Hello world",
            "top_k": 1
        }
    )
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert data["detail"]["error"] == "Pipeline error: Test error"
    assert data["detail"]["documents"] == []
    assert data["detail"]["answers"] == [] 
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from backend.app.main import app
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.schema import DocumentFull, Query
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
def test_settings(settings):
    """Get test settings."""
    return settings

@pytest.fixture
def mock_embeddings():
    mock = MagicMock()
    mock.encode.return_value = np.random.rand(768).tolist()
    return mock

@pytest.fixture
def mock_store():
    store = MagicMock()
    store.embedding_dim = 768
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
def mock_pipeline():
    """Mock pipeline for testing."""
    mock = MagicMock()
    mock.run.return_value = {
        "documents": [MagicMock(content="test content", to_dict=lambda: {"content": "test content"})],
        "answers": ["test answer"]
    }
    return mock

@pytest.fixture
def client(mock_pipeline):
    """Test client with mocked pipeline."""
    with patch('backend.app.main.build_pipeline', return_value=(mock_pipeline, None)):
        with TestClient(app) as client:
            yield client

def test_query_endpoint(client, mock_pipeline):
    """Test the query endpoint."""
    # Setup mock pipeline to return a document
    mock_pipeline.run.return_value = {
        "documents": [MagicMock(content="test content", to_dict=lambda: {"content": "test content"})],
        "answers": ["test answer"]
    }
    
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
    assert data["documents"][0]["content"] == "test content"

def test_query_endpoint_error(client, mock_pipeline):
    """Test error handling in the query endpoint."""
    # Setup mock pipeline to raise an exception
    mock_pipeline.run.side_effect = Exception("Test error")
    
    response = client.post(
        "/query",
        json={
            "text": "test query",
            "top_k": 5
        }
    )
    assert response.status_code == 500
    data = response.json()
    assert "error" in data["detail"]
    assert "documents" in data["detail"]
    assert "answers" in data["detail"]

def test_query_without_namespace(client, mock_pipeline):
    """Test query without namespace falls back to default namespace."""
    # Setup mock pipeline to return a document
    mock_pipeline.run.return_value = {
        "documents": [MagicMock(content="test content", to_dict=lambda: {"content": "test content"})],
        "answers": ["test answer"]
    }
    
    response = client.post(
        "/query",
        json={
            "text": "test query",
            "top_k": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 1
    assert data["documents"][0]["content"] == "test content"

def test_query_with_explicit_namespace(client, mock_pipeline):
    """Test query with explicit namespace."""
    # Setup mock pipeline to return a document
    mock_pipeline.run.return_value = {
        "documents": [MagicMock(content="test content", to_dict=lambda: {"content": "test content"})],
        "answers": ["test answer"]
    }
    
    response = client.post(
        "/query",
        json={
            "text": "test query",
            "top_k": 5,
            "namespace": "test_ns"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 1
    assert data["documents"][0]["content"] == "test content"

def test_query_pipeline_error(client, mock_pipeline):
    """Test query endpoint handles pipeline errors gracefully."""
    # Setup mock pipeline to raise an exception
    mock_pipeline.run.side_effect = Exception("Test error")
    
    response = client.post(
        "/query",
        json={
            "text": "test query",
            "top_k": 5
        }
    )
    assert response.status_code == 500
    data = response.json()
    assert "error" in data["detail"]
    assert "documents" in data["detail"]
    assert "answers" in data["detail"] 
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schema import DocumentFull, Query
from backend.app.config import Settings
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.dependencies import get_document_store, get_embedder, get_settings
import numpy as np
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def encode(self, text):
            return np.zeros(768)  # Return zero vector
        def embed_batch(self, texts):
            return [np.zeros(768) for _ in texts]  # Return zero vectors
    return MockEmbeddings()

@pytest.fixture
def mock_store(mock_embeddings, settings):
    """Create a mock document store for testing."""
    return InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )

@pytest.fixture
def mock_pipeline():
    """Mock pipeline for testing."""
    mock = MagicMock()
    mock.run.return_value = {
        "documents": [MagicMock(
            content="test content",
            id="1",
            meta={"namespace": "test"},
            to_dict=lambda: {
                "content": "test content",
                "id": "1",
                "meta": {"namespace": "test"}
            }
        )],
        "answers": ["test answer"]
    }
    return mock

@pytest.fixture
def client(mock_embeddings, mock_store, mock_pipeline, settings):
    """Test client with mocked dependencies."""
    app.dependency_overrides[get_embedder] = lambda: mock_embeddings
    app.dependency_overrides[get_document_store] = lambda: mock_store
    app.dependency_overrides[get_settings] = lambda: settings
    
    with patch('backend.app.main.build_pipeline', return_value=(mock_pipeline, None)):
        with TestClient(app) as client:
            yield client
    
    app.dependency_overrides = {}

def test_query_integration(client, mock_store, mock_pipeline):
    """Test the query endpoint with mocked dependencies."""
    # Add test document
    doc = DocumentFull(
        id="1",
        content="Test content",
        meta={"namespace": "test"},
        embedding=[0.1] * 768
    )
    mock_store.add_documents([doc])
    
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
    assert data["documents"][0]["content"] == "test content"
    assert data["documents"][0]["id"] == "1"
    assert data["documents"][0]["meta"]["namespace"] == "test"
    assert isinstance(data["answers"], list)
    assert len(data["answers"]) > 0

def test_documents_integration(client, mock_store):
    """Test the documents endpoint with mocked dependencies."""
    # Add test document
    doc = DocumentFull(
        id="1",
        content="Test content",
        meta={"namespace": "test"},
        embedding=[0.1] * 768
    )
    mock_store.add_documents([doc])
    
    # Test get documents
    response = client.get("/documents?namespace=test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "1"
    assert data[0]["meta"]["namespace"] == "test"
    assert "content" not in data[0]  # Content should not be included in metadata response

def test_settings_integration(client, settings):
    """Test the settings endpoint."""
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    assert "embedding_model" in data
    assert "generator_model" in data
    assert data["environment"] == settings.environment
    assert data["embedding_model"] == settings.embedding_model
    assert data["generator_model"] == settings.generator_model_name

def test_document_store_embeddings(client, mock_store, mock_embeddings):
    """Test basic document store operations with embeddings."""
    # Add test documents
    docs = [
        DocumentFull(
            id="1",
            content="Test document 1",
            meta={"namespace": "test"},
            embedding=np.array([0.1] * 768)
        ),
        DocumentFull(
            id="2",
            content="Test document 2",
            meta={"namespace": "test"},
            embedding=np.array([0.1] * 768)
        )
    ]
    mock_store.add_documents(docs)

    # Verify documents were added
    assert len(mock_store.documents) == 2
    assert len(mock_store.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in mock_store.embeddings)
    assert all(emb.shape[0] == 768 for emb in mock_store.embeddings)

def test_upload_document(client, mock_pipeline):
    """Test document upload endpoint."""
    # Create a mock document with fixed ID
    mock_doc = MagicMock()
    mock_doc.id = "1"
    mock_doc.content = "test content"
    mock_doc.meta = {"namespace": "test"}
    mock_doc.to_dict.return_value = {
        "content": "test content",
        "id": "1",
        "meta": {"namespace": "test"}
    }

    # Create a mock document store that preserves IDs
    class MockDocStore:
        def __init__(self):
            self.documents = []

        def write_documents(self, docs):
            self.documents.extend(docs)

        def embed_batch(self, texts):
            return [[0.1] * 768 for _ in texts]

    mock_store = MockDocStore()
    app.dependency_overrides[get_document_store] = lambda: mock_store
    app.dependency_overrides[get_embedder] = lambda: mock_store

    try:
        response = client.post(
            "/ingest",
            files={"files": ("test.txt", mock_doc.content)},
            data={"namespace": "test", "doc_id": "1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) == 1
        assert data["documents"][0]["content"] == "test content"
        assert data["documents"][0]["id"] == "1"
        assert data["documents"][0]["meta"]["namespace"] == "test"
    finally:
        # Clean up the overrides
        app.dependency_overrides.clear()

def test_upload_document_error(client, mock_pipeline):
    """Test document upload error handling."""
    # Setup mock pipeline to raise an exception
    mock_pipeline.run.side_effect = Exception("Test error")
    app.dependency_overrides[get_document_store] = lambda: mock_pipeline

    try:
        response = client.post(
            "/ingest",
            files={"files": ("test.txt", "test content")},
            data={"namespace": "test"}
        )
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["status"] == "error"
        assert data["detail"]["documents"] == []
    finally:
        # Clean up the override
        app.dependency_overrides.clear()

def test_query_document(client, mock_pipeline):
    """Test document query endpoint."""
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

def test_query_document_error(client, mock_pipeline):
    """Test document query error handling."""
    # Setup mock pipeline to raise an exception
    mock_pipeline.run.side_effect = Exception("Test error")
    
    response = client.post(
        "/query",
        json={
            "text": "test query",
            "top_k": 5,
            "namespace": "test"
        }
    )
    assert response.status_code == 500
    data = response.json()
    assert "error" in data["detail"]
    assert "documents" in data["detail"]
    assert "answers" in data["detail"]

def test_settings_endpoint(client):
    """Test settings endpoint."""
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    assert "embedding_model" in data
    assert "generator_model" in data 
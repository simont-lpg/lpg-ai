import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.vectorstore import get_vectorstore
from backend.app.schema import DocumentFull
from backend.app.config import Settings
from unittest.mock import patch, MagicMock
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.dependencies import get_document_store

client = TestClient(app)

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    mock = MagicMock()
    mock.embed_batch.return_value = [[0.1, 0.2, 0.3]]
    mock.encode.return_value = [0.1, 0.2, 0.3]
    return mock

@pytest.fixture
def mock_vectorstore():
    """Mock vectorstore for testing."""
    mock = MagicMock()
    mock.query_by_embedding.return_value = [
        DocumentFull(content="Test document 1", id="1"),
        DocumentFull(content="Test document 2", id="2")
    ]
    return mock

@pytest.fixture
def mock_store():
    # Create a real store instance
    store = InMemoryDocumentStore(
        embedding_dim=384,
        collection_name="test_documents"
    )
    
    # Mock the embeddings model
    store.model = type('MockModel', (), {
        'encode': lambda _, text: [0.1] * 384,
        'embed_batch': lambda _, texts: [[0.1] * 384 for _ in texts]
    })()
    
    return store

@pytest.mark.integration
def test_api_smoke_test(mock_embeddings, mock_vectorstore):
    """End-to-end smoke test of the API endpoints."""
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    with patch('backend.app.vectorstore.SentenceTransformer', return_value=mock_embeddings):
        with patch('backend.app.pipeline.get_vectorstore', return_value=mock_vectorstore):
            # Test query endpoint with valid input
            response = client.post("/query", json={"query": "machine learning", "top_k": 1})
            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            assert len(data["documents"]) == 1
            assert "content" in data["documents"][0]
            
            # Test query endpoint with invalid input
            response = client.post("/query", json={"query": ""})
            assert response.status_code == 422  # Validation error
            
            # Test query endpoint with invalid JSON
            response = client.post("/query", data="invalid json")
            assert response.status_code == 422 

def test_integration_smoke(client, mock_store):
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: mock_store
    
    try:
        # Create test documents
        docs = [
            DocumentFull(id="a", content="A", meta={"namespace":"x"}),
            DocumentFull(id="b", content="B", meta={"namespace":"y"}),
        ]
        
        # Write documents to store
        mock_store.write_documents(docs)
        
        # Test the endpoint
        resp = client.get("/documents")
        assert resp.status_code == 200
        ids = {d["id"] for d in resp.json()}
        assert ids == {"a","b"}
    finally:
        # Clean up
        app.dependency_overrides.clear() 
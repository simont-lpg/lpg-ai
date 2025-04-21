import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schema import DocumentFull
from backend.app.config import Settings
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.dependencies import get_document_store
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    mock = MagicMock()
    mock.encode.return_value = [0.1] * 384
    return mock

@pytest.mark.integration
def test_api_integration(mock_embeddings):
    """End-to-end integration test of the query endpoint."""
    # Create a real in-memory store
    store = InMemoryDocumentStore(
        embedding_dim=384,
        collection_name="test_documents"
    )
    
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: store
    
    try:
        # Add test documents
        docs = [
            DocumentFull(id="1", content="Document about machine learning", meta={"namespace": "default"}),
            DocumentFull(id="2", content="Document about data science", meta={"namespace": "other"})
        ]
        store.write_documents(docs)
        
        # Test query endpoint with mocked embeddings
        with patch('backend.app.pipeline.SentenceTransformer', return_value=mock_embeddings):
            # Test basic query
            response = client.post("/query", json={"text": "machine learning"})
            assert response.status_code == 200
            data = response.json()
            assert len(data["documents"]) == 1
            assert "machine learning" in data["documents"][0]["content"].lower()
            
            # Test namespace filtering
            response = client.post("/query", json={"text": "data", "namespace": "other"})
            assert response.status_code == 200
            data = response.json()
            assert len(data["documents"]) == 1
            assert data["documents"][0]["meta"]["namespace"] == "other"
    
    finally:
        # Clean up
        app.dependency_overrides.clear() 
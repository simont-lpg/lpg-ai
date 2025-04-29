import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schema import DocumentFull
from backend.app.config import Settings
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.dependencies import get_document_store
from unittest.mock import patch, MagicMock
import json
import numpy as np

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_store(settings):
    """Create a mock store instance."""
    mock_model = MagicMock()
    mock_model.embedding_dim = settings.embedding_dim
    # Return zero vectors for any number of documents
    mock_model.embed_batch.side_effect = lambda texts: np.zeros((len(texts), settings.embedding_dim))
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_model
    )
    return store

def test_integration_smoke(client, mock_store):
    """Basic smoke test for document store integration."""
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
        data = resp.json()
        assert len(data) == 2
        ids = {d["id"] for d in data}
        assert ids == {"a", "b"}
    finally:
        # Clean up
        app.dependency_overrides.clear()

def test_delete_documents_integration(client, mock_store):
    """Test document deletion integration."""
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: mock_store
    
    try:
        # Create test documents
        docs = [
            DocumentFull(id="a", content="A", meta={"file_name": "test.txt"}),
            DocumentFull(id="b", content="B", meta={"file_name": "test.txt"}),
            DocumentFull(id="c", content="C", meta={"file_name": "other.txt"}),
        ]
        
        # Write documents to store
        mock_store.write_documents(docs)
        
        # Test deletion
        resp = client.post("/documents/delete", json={"file_name": "test.txt"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 2  # Two documents should be deleted
        assert data["status"] == "success"
        
        # Verify documents are deleted
        resp = client.get("/documents")
        assert resp.status_code == 200
        remaining_docs = resp.json()
        assert len(remaining_docs) == 1
        assert remaining_docs[0]["id"] == "c"
        
        # Test deleting non-existent file
        resp = client.post("/documents/delete", json={"file_name": "nonexistent.txt"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 0  # No documents should be deleted
        assert data["status"] == "success"
    finally:
        # Clean up
        app.dependency_overrides.clear() 
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schema import DocumentFull
from backend.app.config import Settings
from backend.app.dependencies import get_document_store
from unittest.mock import patch, MagicMock
import json
import numpy as np
from backend.tests.utils import MockDocumentStore

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
    store = MockDocumentStore(
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
        mock_store.add(
            documents=["A", "B"],
            metadatas=[{"namespace": "x"}, {"namespace": "y"}],
            ids=["a", "b"]
        )
        
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
        mock_store.add(
            documents=["A", "B", "C"],
            metadatas=[
                {"file_name": "test.txt"},
                {"file_name": "test.txt"},
                {"file_name": "other.txt"}
            ],
            ids=["a", "b", "c"]
        )
        
        # Test deletion
        resp = client.post("/documents/delete", json={"file_name": "test.txt"})
        assert resp.status_code == 200
        
        # Verify documents were deleted
        results = mock_store.get()
        assert len(results["documents"]) == 1
        assert results["documents"][0] == "C"
    finally:
        # Clean up
        app.dependency_overrides.clear() 
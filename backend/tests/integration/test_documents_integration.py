import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schema import DocumentFull
from app.config import Settings
from app.vectorstore import InMemoryDocumentStore
from app.dependencies import get_document_store
from unittest.mock import patch
import json

@pytest.fixture
def client():
    return TestClient(app)

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

def test_delete_documents_integration(client, mock_store):
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
        resp = client.request("DELETE", "/documents", data=json.dumps({"file_name": "test.txt"}), headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["deleted"] == 2  # Should delete 2 documents
        
        # Verify documents are deleted
        resp = client.get("/documents")
        assert resp.status_code == 200
        remaining_docs = resp.json()
        assert len(remaining_docs) == 1
        assert remaining_docs[0]["id"] == "c"
        
        # Test deleting non-existent file
        resp = client.request("DELETE", "/documents", data=json.dumps({"file_name": "nonexistent.txt"}), headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 0
    finally:
        # Clean up
        app.dependency_overrides.clear() 
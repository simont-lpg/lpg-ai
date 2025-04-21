import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from backend.app.main import app
from backend.app.config import Settings
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.schema import DocumentFull
from backend.app.dependencies import get_document_store, get_embedder
from sentence_transformers import SentenceTransformer
import tempfile
import os
import numpy as np

@pytest.fixture
def test_settings():
    return Settings(
        embedding_model="all-MiniLM-L6-v2",
        embedding_dim=384,
        collection_name="test_collection"
    )

@pytest.fixture
def document_store(test_settings):
    """Create a shared document store instance."""
    store = InMemoryDocumentStore(
        embedding_dim=test_settings.embedding_dim,
        collection_name=test_settings.collection_name
    )
    return store

@pytest.fixture
def test_app(test_settings, document_store):
    """Create a test app with overridden dependencies."""
    # Override the document store dependency
    async def override_get_document_store():
        return document_store
    
    # Override the embedder dependency
    async def override_get_embedder():
        return SentenceTransformer(test_settings.embedding_model)
    
    app.dependency_overrides[get_document_store] = override_get_document_store
    app.dependency_overrides[get_embedder] = override_get_embedder
    return app

@pytest.fixture
def client(test_app):
    return TestClient(test_app)

@pytest.fixture
def test_document():
    return DocumentFull(
        content="Hello world",
        meta={"namespace": "test_ns", "file_name": "test.txt"},
        id="test1"
    )

def test_end_to_end_query_with_namespace(client, test_settings, document_store):
    """Test end-to-end query with namespace filtering."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("Hello world")
        temp_file.flush()
        
        try:
            # Ingest the document
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/ingest",
                    files={"files": ("test.txt", f, "text/plain")},
                    data={"namespace": "test_ns"}
                )
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            assert response.json()["namespace"] == "test_ns"
            
            # Verify document was stored
            assert len(document_store.documents) == 1
            assert document_store.documents[0].content == "Hello world"
            assert document_store.documents[0].meta["namespace"] == "test_ns"
            
            # Query with the same namespace
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
            assert result["documents"][0]["meta"]["namespace"] == "test_ns"
            
            # Query with wrong namespace (should return empty)
            response = client.post(
                "/query",
                json={
                    "text": "Hello world",
                    "top_k": 1,
                    "namespace": "wrong_ns"
                }
            )
            assert response.status_code == 200
            result = response.json()
            assert len(result["documents"]) == 0
            
        finally:
            # Clean up
            os.unlink(temp_file.name) 
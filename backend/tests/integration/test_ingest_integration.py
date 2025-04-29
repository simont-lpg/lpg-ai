import tempfile
import os
import pytest
import numpy as np
from fastapi.testclient import TestClient
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.main import app
from backend.app.dependencies import get_document_store
from backend.app.config import Settings
from sentence_transformers import SentenceTransformer
from backend.app.schema import DocumentFull
from unittest.mock import MagicMock

@pytest.fixture
def store(settings):
    """Create a store instance for testing."""
    mock_model = MagicMock()
    mock_model.embedding_dim = settings.embedding_dim
    mock_model.embed_batch.return_value = np.zeros((2, settings.embedding_dim))  # Return zero vectors with correct shape
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_model
    )
    return store

@pytest.fixture
def client(tmp_path, monkeypatch, store):
    # Override the document store dependency
    app.dependency_overrides[get_document_store] = lambda: store
    return TestClient(app)

def make_txt_file(tmp_path, text):
    file = tmp_path / "doc.txt"
    file.write_text(text)
    return file

def test_ingest_and_store(client, store, tmp_path):
    """Test document ingestion and storage."""
    # Create test documents
    docs = [
        DocumentFull(content="Test document 1", id="1", meta={"namespace": "default"}),
        DocumentFull(content="Test document 2", id="2", meta={"namespace": "default"})
    ]

    # Ingest documents
    store.write_documents(docs)

    # Verify ingestion
    assert len(store.documents) == 2
    assert len(store.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in store.embeddings)
    assert all(emb.shape[0] == store.embedding_dim for emb in store.embeddings)

    # Verify document content
    assert store.documents[0].content == "Test document 1"
    assert store.documents[1].content == "Test document 2"
    assert store.documents[0].id == "1"
    assert store.documents[1].id == "2"

    # create a simple text file
    txt = make_txt_file(tmp_path, "This is a test.")
    # call ingest
    resp = client.post(
        "/ingest",
        files=[("files", ("doc.txt", open(txt, "rb"), "text/plain"))],
        data={"namespace":"smoke"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["files_ingested"] == 1
    assert data["total_chunks"] > 0
    
    # now inspect the real store to confirm chunks exist
    docs = store.get_all_documents()
    assert len(docs) > 0
    
    # verify the namespace was set correctly
    for doc in docs:
        if doc.meta.get("file_name") == "doc.txt":
            assert doc.meta.get("namespace") == "smoke"
        else:
            assert doc.meta.get("namespace") == "default"
        assert doc.content is not None
        assert doc.embedding is not None 
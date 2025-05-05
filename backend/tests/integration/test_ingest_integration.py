import tempfile
import os
import pytest
import numpy as np
from fastapi.testclient import TestClient
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.main import app
from backend.app.dependencies import get_document_store, get_embedder
from backend.app.config import Settings
from sentence_transformers import SentenceTransformer
from backend.app.schema import DocumentFull
from unittest.mock import MagicMock

@pytest.fixture
def store(settings):
    """Create a store instance for testing."""
    class MockStore:
        def __init__(self):
            self.embedding_dim = 768
            self.documents = []

        def add_documents(self, documents):
            for doc in documents:
                self.documents.append({
                    "id": doc.id,
                    "content": doc.content,
                    "meta": doc.meta
                })
            return len(documents)

        def get(self, ids=None, where=None):
            if not ids and not where:
                return {
                    "ids": [doc["id"] for doc in self.documents],
                    "documents": [doc["content"] for doc in self.documents],
                    "metadatas": [doc["meta"] for doc in self.documents]
                }

            filtered_docs = []
            for doc in self.documents:
                if ids and doc["id"] not in ids:
                    continue
                if where:
                    match = True
                    for key, value in where.items():
                        if key not in doc["meta"] or doc["meta"][key] != value:
                            match = False
                            break
                    if not match:
                        continue
                filtered_docs.append(doc)

            return {
                "ids": [doc["id"] for doc in filtered_docs],
                "documents": [doc["content"] for doc in filtered_docs],
                "metadatas": [doc["meta"] for doc in filtered_docs]
            }

    return MockStore()

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
    store.add_documents(
        documents=[
            DocumentFull(id="1", content="Test document 1", meta={"namespace": "default"}),
            DocumentFull(id="2", content="Test document 2", meta={"namespace": "default"})
        ]
    )

    # Verify documents were added
    results = store.get()
    assert len(results["documents"]) == 2
    assert results["documents"][0] == "Test document 1"
    assert results["documents"][1] == "Test document 2"
    assert results["metadatas"][0]["namespace"] == "default"
    assert results["metadatas"][1]["namespace"] == "default"

    # Verify ingestion
    results = store.get()
    assert len(results["documents"]) == 2
    assert len(results["metadatas"]) == 2
    assert all(isinstance(meta, dict) for meta in results["metadatas"])

    # Verify document content
    assert results["documents"][0] == "Test document 1"
    assert results["documents"][1] == "Test document 2"
    assert results["ids"][0] == "1"
    assert results["ids"][1] == "2"

    # Create a mock embedder that returns embeddings with the correct dimension
    class MockEmbedder:
        def encode(self, texts, convert_to_numpy=True):
            if isinstance(texts, str):
                return [0.0] * 768
            return [[0.0] * 768 for _ in range(len(texts))]
            
        def encode_queries(self, texts, convert_to_numpy=True):
            if isinstance(texts, str):
                return [0.0] * 768
            return [[0.0] * 768 for _ in range(len(texts))]
            
        def embed_batch(self, texts):
            return [[0.0] * 768 for _ in range(len(texts))]
            
        def embed(self, text):
            return [0.0] * 768

    # Override the embedder dependency
    app.dependency_overrides[get_embedder] = lambda: MockEmbedder()

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
    assert "documents" in data
    assert len(data["documents"]) > 0
    
    # now inspect the real store to confirm chunks exist
    results = store.get()
    assert len(results["documents"]) > 0
    
    # verify the namespace was set correctly
    for doc, meta in zip(results["documents"], results["metadatas"]):
        if meta.get("file_name") == "doc.txt":
            assert meta.get("namespace") == "smoke"
        else:
            assert meta.get("namespace") == "default"
        assert doc is not None 
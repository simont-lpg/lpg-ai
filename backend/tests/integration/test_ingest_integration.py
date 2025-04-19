import tempfile
import os
import pytest
from fastapi.testclient import TestClient
from app.vectorstore import InMemoryDocumentStore
from app.main import app
from app.dependencies import get_document_store
from app.config import Settings
from sentence_transformers import SentenceTransformer

@pytest.fixture
def store():
    settings = Settings()
    model = SentenceTransformer(settings.embedding_model)
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=model
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
        assert doc.meta.get("namespace") == "smoke"
        assert doc.content is not None
        assert doc.embedding is not None 
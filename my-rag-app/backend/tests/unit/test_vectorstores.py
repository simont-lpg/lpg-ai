import pytest
from pathlib import Path

from app.vectorstores import init_document_store
from app.config import settings


def test_init_document_store(tmp_path, monkeypatch):
    """Test document store initialization."""
    # Override the persist directory
    monkeypatch.setattr(settings, "chroma_persist_dir", tmp_path / "test_chroma")
    
    # Initialize the document store
    store = init_document_store()
    
    # Verify the store was created
    assert store is not None
    assert store.persist_directory == str(tmp_path / "test_chroma")
    assert store.embedding_dim == settings.embedding_dim
    assert store.similarity == "cosine"
    assert store.return_embedding is True
    
    # Verify the directory was created
    assert (tmp_path / "test_chroma").exists()


def test_document_store_persistence(tmp_path, monkeypatch):
    """Test that documents persist between store instances."""
    # Override the persist directory
    monkeypatch.setattr(settings, "chroma_persist_dir", tmp_path / "test_chroma")
    
    # Create first store and add a document
    store1 = init_document_store()
    store1.write_documents([{"content": "Test document", "meta": {"source": "test"}}])
    
    # Create second store and verify document exists
    store2 = init_document_store()
    documents = store2.get_all_documents()
    
    assert len(documents) == 1
    assert documents[0].content == "Test document"
    assert documents[0].meta["source"] == "test" 
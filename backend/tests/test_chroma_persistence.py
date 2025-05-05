import pytest
import tempfile
import os
from pathlib import Path
from chromadb import Client, Settings as ChromaSettings
from app.config import Settings
from app.schema import DocumentFull
from app.vectorstore import ChromaDocumentStore
import numpy as np

@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for Chroma."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def test_settings(temp_chroma_dir):
    """Get test settings."""
    return Settings(
        chroma_dir=temp_chroma_dir,
        collection_name="test_collection",
        embedding_model="test_model",
        generator_model_name="test_generator",
        ollama_api_url="http://localhost:11434",
        api_host="localhost",
        api_port=8000,
        cors_origins=["*"],
        dev_mode=True,
        environment="test",
        log_level="INFO",
        secret_key="test_key",
        rate_limit_per_minute=60,
        embedding_dim=1024
    )

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def embed_batch(self, texts):
            return [[0.0] * 1024 for _ in texts]
        def embed(self, text):
            return [0.0] * 1024
    return MockEmbeddings()

@pytest.fixture
def chroma_store(test_settings, mock_embeddings):
    """Create a ChromaDB store instance for testing."""
    return ChromaDocumentStore(
        embedding_dim=test_settings.embedding_dim,
        collection_name=test_settings.collection_name,
        embeddings_model=mock_embeddings,
        persist_directory=test_settings.chroma_dir
    )

def test_chroma_store_initialization(test_settings, mock_embeddings):
    """Test ChromaDB store initialization."""
    store = ChromaDocumentStore(
        embedding_dim=test_settings.embedding_dim,
        collection_name=test_settings.collection_name,
        embeddings_model=mock_embeddings,
        persist_directory=test_settings.chroma_dir
    )
    assert store.embedding_dim == test_settings.embedding_dim
    assert store.collection_name == test_settings.collection_name

def test_chroma_store_add_documents(chroma_store):
    """Test adding documents to ChromaDB store."""
    # Create test documents
    docs = [
        DocumentFull(
            id="test_doc_1",
            content="This is test document 1",
            meta={"source": "test", "file_name": "test1.txt"}
        ),
        DocumentFull(
            id="test_doc_2",
            content="This is test document 2",
            meta={"source": "test", "file_name": "test2.txt"}
        )
    ]
    
    # Add documents
    chroma_store.add_documents(docs)
    
    # Verify documents were added
    results = chroma_store.get()
    assert len(results["documents"]) == 2
    assert results["documents"][0] == "This is test document 1"
    assert results["documents"][1] == "This is test document 2"
    assert results["metadatas"][0]["source"] == "test"
    assert results["metadatas"][1]["source"] == "test"

def test_chroma_store_query_by_embedding(chroma_store):
    """Test querying documents by embedding."""
    # Add test documents
    docs = [
        DocumentFull(
            id="test_doc_1",
            content="This is test document 1",
            meta={"source": "test", "file_name": "test1.txt"}
        ),
        DocumentFull(
            id="test_doc_2",
            content="This is test document 2",
            meta={"source": "test", "file_name": "test2.txt"}
        )
    ]
    chroma_store.add_documents(docs)
    
    # Create a test query embedding
    query_embedding = [0.0] * 1024
    
    # Query documents
    results = chroma_store.query_by_embedding(
        query_embedding,
        top_k=1,
        filters={"source": "test"}
    )
    assert len(results) == 1
    assert results[0].id in ["test_doc_1", "test_doc_2"]
    assert results[0].meta["source"] == "test"

def test_chroma_store_delete_documents(chroma_store):
    """Test deleting documents from ChromaDB store."""
    # Add test documents
    docs = [
        DocumentFull(
            id="test_doc_1",
            content="This is test document 1",
            meta={"source": "test", "file_name": "test1.txt"}
        ),
        DocumentFull(
            id="test_doc_2",
            content="This is test document 2",
            meta={"source": "test", "file_name": "test2.txt"}
        )
    ]
    chroma_store.add_documents(docs)
    
    # Delete one document
    chroma_store.delete_documents(["test_doc_1"])
    
    # Verify document was deleted
    results = chroma_store.get()
    assert len(results["documents"]) == 1
    assert results["documents"][0] == "This is test document 2"

def test_chroma_store_delete_by_file_name(chroma_store):
    """Test deleting documents by file name."""
    # Add test documents
    docs = [
        DocumentFull(
            id="test_doc_1",
            content="This is test document 1",
            meta={"source": "test", "file_name": "test1.txt"}
        ),
        DocumentFull(
            id="test_doc_2",
            content="This is test document 2",
            meta={"source": "test", "file_name": "test2.txt"}
        )
    ]
    chroma_store.add_documents(docs)
    
    # Delete documents by file name
    deleted_count = chroma_store.delete_documents_by_file_name("test1.txt")
    assert deleted_count == 1
    
    # Verify document was deleted
    results = chroma_store.get()
    assert len(results["documents"]) == 1
    assert results["documents"][0] == "This is test document 2"

def test_chroma_store_similarity_search(chroma_store):
    """Test similarity search functionality."""
    # Add test documents
    docs = [
        DocumentFull(
            id="test_doc_1",
            content="This is test document 1",
            meta={"source": "test", "file_name": "test1.txt"}
        ),
        DocumentFull(
            id="test_doc_2",
            content="This is test document 2",
            meta={"source": "test", "file_name": "test2.txt"}
        )
    ]
    chroma_store.add_documents(docs)
    
    # Perform similarity search
    results = chroma_store.similarity_search(
        "test document",
        k=1,
        score_threshold=0.0
    )
    assert len(results) == 1
    assert results[0].id in ["test_doc_1", "test_doc_2"]
    assert results[0].meta["source"] == "test"

def test_chroma_store_persistence(test_settings, mock_embeddings):
    """Test that documents persist across ChromaDB store instances."""
    # Create first store instance
    store1 = ChromaDocumentStore(
        embedding_dim=test_settings.embedding_dim,
        collection_name=test_settings.collection_name,
        embeddings_model=mock_embeddings,
        persist_directory=test_settings.chroma_dir
    )
    
    # Add test document
    doc = DocumentFull(
        id="test_doc_1",
        content="This is a test document",
        meta={"source": "test"}
    )
    store1.add_documents([doc])
    
    # Create second store instance
    store2 = ChromaDocumentStore(
        embedding_dim=test_settings.embedding_dim,
        collection_name=test_settings.collection_name,
        embeddings_model=mock_embeddings,
        persist_directory=test_settings.chroma_dir
    )
    
    # Verify document persists
    results = store2.get()
    assert len(results["documents"]) == 1
    assert results["documents"][0] == "This is a test document"
    assert results["metadatas"][0]["source"] == "test" 
from backend.app.vectorstore import get_vectorstore, InMemoryDocumentStore, OllamaEmbeddings
from backend.app.config import Settings
from backend.app.schema import DocumentFull
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def encode(self, text):
            return np.zeros(384)  # Return zero vector
        def embed_batch(self, texts):
            return [np.zeros(384) for _ in texts]  # Return zero vectors
    return MockEmbeddings()

def test_vectorstore_initialization():
    """Test basic vectorstore initialization."""
    settings = Settings()
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name
    )
    assert store.embedding_dim == settings.embedding_dim
    assert store.collection_name == settings.collection_name
    assert len(store.documents) == 0
    assert len(store.embeddings) == 0

def test_vectorstore_custom_settings():
    """Test vectorstore with custom settings."""
    store = InMemoryDocumentStore(
        embedding_dim=512,
        collection_name="custom"
    )
    assert store.embedding_dim == 512
    assert store.collection_name == "custom"

def test_vectorstore_error_handling():
    """Test vectorstore error handling."""
    settings = Settings()
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=None  # This will cause an error when trying to encode
    )
    
    # Test writing document without a valid embeddings model
    doc = DocumentFull(content="test", id="1")
    with pytest.raises(Exception) as exc_info:
        store.model = None  # Force model to be None
        store.write_documents([doc])
    assert "Failed to process embeddings for document" in str(exc_info.value)

def test_vectorstore_basic_operations(mock_embeddings):
    """Test basic vectorstore operations."""
    settings = Settings()
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    # Test document writing
    docs = [
        DocumentFull(content="Test document 1", id="test1"),
        DocumentFull(content="Test document 2", id="test2")
    ]
    store.write_documents(docs)
    assert len(store.documents) == 2
    assert len(store.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in store.embeddings)
    assert all(emb.shape == (384,) for emb in store.embeddings)
    
    # Test document deletion
    store.delete_documents(["test1"])
    assert len(store.documents) == 1
    assert len(store.embeddings) == 1

def test_vectorstore_ollama_config():
    """Test vectorstore with Ollama configuration."""
    settings = Settings()
    settings.embedding_model_name = "mxbai-embed-large:latest"
    settings.ollama_api_url = "http://localhost:11434"
    
    embedder = OllamaEmbeddings(
        api_url=str(settings.ollama_api_url),
        model_name=settings.embedding_model_name,
        embedding_dim=settings.embedding_dim
    )
    assert embedder.api_url == str(settings.ollama_api_url)
    assert embedder.model_name == settings.embedding_model_name
    assert embedder.embedding_dim == settings.embedding_dim

def test_vectorstore_query_operations(mock_embeddings):
    """Test vectorstore query operations."""
    settings = Settings()
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    # Add test documents
    docs = [
        DocumentFull(content="Test document 1", id="1"),
        DocumentFull(content="Test document 2", id="2")
    ]
    store.write_documents(docs)
    
    # Verify embeddings are created
    assert len(store.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in store.embeddings)
    assert all(emb.shape == (384,) for emb in store.embeddings)
    
    # Test querying with zero vector
    query_embedding = np.zeros(settings.embedding_dim)
    results = store.query_by_embedding(query_embedding, top_k=1)
    assert len(results) == 1
    assert isinstance(results[0], DocumentFull)

def test_vectorstore_write_documents(mock_embeddings):
    """Test writing documents to the vectorstore."""
    settings = Settings()
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    documents = [
        DocumentFull(content="Test document 1"),
        DocumentFull(content="Test document 2")
    ]
    
    store.write_documents(documents)
    assert len(store.documents) == 2
    assert len(store.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in store.embeddings)
    assert all(emb.shape == (384,) for emb in store.embeddings)

def test_vectorstore_delete_documents(mock_embeddings):
    """Test deleting documents from the vectorstore."""
    settings = Settings()
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    # Add test documents
    documents = [
        DocumentFull(content="Test document 1", id="1"),
        DocumentFull(content="Test document 2", id="2")
    ]
    store.write_documents(documents)
    
    # Verify initial state
    assert len(store.documents) == 2
    assert len(store.embeddings) == 2
    
    # Delete one document
    store.delete_documents(["1"])
    assert len(store.documents) == 1
    assert len(store.embeddings) == 1
    assert store.documents[0].id == "2" 
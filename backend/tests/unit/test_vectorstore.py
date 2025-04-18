from backend.app.vectorstore import get_vectorstore, InMemoryDocumentStore, OllamaEmbeddings
from backend.app.config import Settings
from backend.app.schema import Document
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    mock = MagicMock()
    mock.embed_batch.return_value = [np.array([0.1] * 384)]
    mock.encode.return_value = np.array([0.1] * 384)
    return mock

def test_vectorstore_initialization():
    """Test vectorstore initialization with default settings."""
    settings = Settings()
    with patch('backend.app.vectorstore.OllamaEmbeddings') as mock_ollama:
        mock_ollama.return_value = MagicMock()
        mock_ollama.return_value.embed_batch.return_value = [np.array([0.1] * 384)]
        vectorstore = get_vectorstore(settings)
        assert isinstance(vectorstore, InMemoryDocumentStore)
        assert vectorstore.embedding_dim == 384

def test_vectorstore_custom_settings():
    """Test vectorstore initialization with custom settings."""
    settings = Settings(
        collection_name="custom_collection",
        embedding_dim=384,
        embedding_model_name="custom-model"
    )
    with patch('backend.app.vectorstore.OllamaEmbeddings') as mock_ollama:
        mock_ollama.return_value = MagicMock()
        mock_ollama.return_value.embed_batch.return_value = [np.array([0.1] * 384)]
        vectorstore = get_vectorstore(settings)
        assert isinstance(vectorstore, InMemoryDocumentStore)
        assert vectorstore.collection_name == "custom_collection"

def test_vectorstore_error_handling():
    """Test vectorstore error handling for invalid configurations."""
    settings = Settings(
        embedding_model_name="mxbai-embed-large:latest",
        ollama_api_url="http://invalid:11434"
    )
    with patch('backend.app.vectorstore.OllamaEmbeddings', side_effect=Exception("Connection failed")):
        with pytest.raises(Exception, match="Failed to initialize vectorstore"):
            get_vectorstore(settings)

def test_vectorstore_basic_operations(mock_embeddings):
    """Test basic vectorstore operations."""
    settings = Settings()
    vectorstore = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    # Test document writing
    docs = [
        Document(content="Test document 1", id="test1"),
        Document(content="Test document 2", id="test2")
    ]
    vectorstore.write_documents(docs)
    assert len(vectorstore.documents) == 2
    assert len(vectorstore.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in vectorstore.embeddings)
    assert all(emb.shape == (384,) for emb in vectorstore.embeddings)
    
    # Test document deletion
    vectorstore.delete_documents(["test1"])
    assert len(vectorstore.documents) == 1
    assert len(vectorstore.embeddings) == 1

def test_vectorstore_ollama_config():
    """Test vectorstore configuration with Ollama embeddings."""
    settings = Settings(
        embedding_model_name="mxbai-embed-large:latest",
        ollama_api_url="http://localhost:11434"
    )
    with patch('backend.app.vectorstore.OllamaEmbeddings') as mock_ollama:
        mock_ollama.return_value = MagicMock()
        mock_ollama.return_value.embed_batch.return_value = [np.array([0.1] * 384)]
        vectorstore = get_vectorstore(settings)
        assert vectorstore.model is not None
        assert hasattr(vectorstore.model, 'embed_batch')
        # Test the embed_batch method
        result = vectorstore.model.embed_batch(["test1"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], np.ndarray)
        assert result[0].shape == (384,)

def test_vectorstore_query_operations(mock_embeddings):
    """Test vectorstore query operations."""
    settings = Settings()
    vectorstore = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    # Add test documents
    docs = [
        Document(content="Test document 1", id="1"),
        Document(content="Test document 2", id="2")
    ]
    vectorstore.write_documents(docs)
    
    # Verify embeddings are created
    assert len(vectorstore.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in vectorstore.embeddings)
    assert all(emb.shape == (384,) for emb in vectorstore.embeddings)
    
    # Test querying with zero vector
    query_embedding = np.zeros(settings.embedding_dim)
    results = vectorstore.query_by_embedding(query_embedding, top_k=1)
    assert len(results) == 1
    assert isinstance(results[0], Document)

def test_vectorstore_write_documents(mock_embeddings):
    """Test writing documents to the vectorstore."""
    settings = Settings()
    vectorstore = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    documents = [
        Document(content="Test document 1"),
        Document(content="Test document 2")
    ]
    
    vectorstore.write_documents(documents)
    assert len(vectorstore.documents) == 2
    assert len(vectorstore.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in vectorstore.embeddings)
    assert all(emb.shape == (384,) for emb in vectorstore.embeddings)

def test_vectorstore_delete_documents(mock_embeddings):
    """Test deleting documents from the vectorstore."""
    settings = Settings()
    vectorstore = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    # Add test documents
    documents = [
        Document(content="Test document 1", id="1"),
        Document(content="Test document 2", id="2")
    ]
    vectorstore.write_documents(documents)
    
    # Verify initial state
    assert len(vectorstore.documents) == 2
    assert len(vectorstore.embeddings) == 2
    
    # Delete one document
    vectorstore.delete_documents(["1"])
    assert len(vectorstore.documents) == 1
    assert len(vectorstore.embeddings) == 1
    assert vectorstore.documents[0].id == "2" 
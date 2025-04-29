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
            return np.zeros(768)  # Return zero vector
        def embed_batch(self, texts):
            return [np.zeros(768) for _ in texts]  # Return zero vectors
        def embed(self, text):
            return [0.0] * 768  # Return list instead of numpy array
    return MockEmbeddings()

def test_document_store_initialization(settings):
    """Test document store initialization."""
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=None
    )
    assert store.embedding_dim == settings.embedding_dim
    assert store.collection_name == settings.collection_name

def test_document_store_operations(settings, mock_embeddings):
    """Test basic document store operations."""
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    # Test adding documents
    doc = DocumentFull(
        id="1",
        content="Test content",
        meta={"namespace": "test"},
        embedding=[0.1] * settings.embedding_dim
    )
    store.add_documents([doc])
    
    # Test retrieving documents
    retrieved = store.get_all_documents()
    assert len(retrieved) == 1
    assert retrieved[0].id == "1"
    assert retrieved[0].content == "Test content"
    
    # Test filtering by namespace
    filtered = store.get_all_documents(filters={"namespace": "test"})
    assert len(filtered) == 1
    assert filtered[0].meta["namespace"] == "test"

def test_ollama_embeddings(settings):
    """Test Ollama embeddings initialization."""
    embeddings = OllamaEmbeddings(
        api_url=str(settings.ollama_api_url),
        model_name=settings.embedding_model,
        embedding_dim=settings.embedding_dim
    )
    assert embeddings.api_url == str(settings.ollama_api_url)
    assert embeddings.model_name == settings.embedding_model
    assert embeddings.embedding_dim == settings.embedding_dim

def test_vectorstore_initialization():
    """Test basic vectorstore initialization."""
    settings = Settings()
    mock_model = MagicMock()
    mock_model.embedding_dim = settings.embedding_dim
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_model
    )
    assert store.embedding_dim == settings.embedding_dim
    assert store.collection_name == settings.collection_name

def test_vectorstore_custom_settings():
    """Test vectorstore with custom settings."""
    mock_model = MagicMock()
    mock_model.embedding_dim = 512
    store = InMemoryDocumentStore(
        embedding_dim=512,
        collection_name="custom",
        embeddings_model=mock_model
    )
    assert store.embedding_dim == 512
    assert store.collection_name == "custom"

def test_vectorstore_error_handling(settings):
    """Test vectorstore error handling."""
    with pytest.raises(ValueError):
        InMemoryDocumentStore(
            embedding_dim=0,  # Invalid dimension
            collection_name=settings.collection_name,
            embeddings_model=None
        )

def test_vectorstore_basic_operations(mock_embeddings, settings):
    """Test basic vectorstore operations."""
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )

    # Test document writing
    docs = [
        DocumentFull(content="Test document 1", id="test1", meta={"namespace": "default"}),
        DocumentFull(content="Test document 2", id="test2", meta={"namespace": "default"})
    ]
    store.write_documents(docs)
    assert len(store.documents) == 2

def test_vectorstore_query_operations(mock_embeddings, settings):
    """Test vectorstore query operations."""
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )
    
    # Add test documents
    docs = [
        DocumentFull(content="Test document 1", id="1", meta={"namespace": "default"}),
        DocumentFull(content="Test document 2", id="2", meta={"namespace": "default"})
    ]
    store.write_documents(docs)
    
    # Test query
    query_results = store.similarity_search("test", k=1)
    assert len(query_results) == 1
    assert query_results[0].id in ["1", "2"]

def test_vectorstore_write_documents(mock_embeddings):
    """Test writing documents to the vectorstore."""
    settings = Settings()
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )

    documents = [
        DocumentFull(content="Test document 1", id="1", meta={"namespace": "test"}),
        DocumentFull(content="Test document 2", id="2", meta={"namespace": "test"})
    ]
    store.write_documents(documents)
    assert len(store.get_all_documents()) == 2

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
        DocumentFull(content="Test document 1", id="1", meta={"namespace": "test"}),
        DocumentFull(content="Test document 2", id="2", meta={"namespace": "test"})
    ]
    store.write_documents(documents)
    
    # Test deletion
    store.delete_documents(["1"])
    assert len(store.get_all_documents()) == 1
    assert store.get_all_documents()[0].id == "2"

def test_vectorstore_ollama_config():
    """Test vectorstore with Ollama configuration."""
    settings = Settings(
        embedding_model="mxbai-embed-large:latest",
        embedding_dim=768,
        ollama_api_url="http://localhost:11434",
        collection_name="test_documents",
        generator_model_name="mistral-instruct:latest",
        dev_mode=False
    )
    mock_model = MagicMock()
    mock_model.embedding_dim = settings.embedding_dim
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_model
    )
    assert store.embedding_dim == settings.embedding_dim
    assert store.collection_name == settings.collection_name

def test_vectorstore_write_documents(mock_embeddings):
    """Test writing documents to the vectorstore."""
    settings = Settings()
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )

    documents = [
        DocumentFull(content="Test document 1", id="1", meta={"namespace": "test"}),
        DocumentFull(content="Test document 2", id="2", meta={"namespace": "test"})
    ]

    store.write_documents(documents)
    assert len(store.documents) == 2
    assert len(store.embeddings) == 2
    assert all(isinstance(emb, np.ndarray) for emb in store.embeddings)
    assert all(emb.shape == (settings.embedding_dim,) for emb in store.embeddings)

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
        DocumentFull(content="Test document 1", id="1", meta={"namespace": "test"}),
        DocumentFull(content="Test document 2", id="2", meta={"namespace": "test"})
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
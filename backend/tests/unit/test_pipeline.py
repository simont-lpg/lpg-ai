import pytest
from backend.app.pipeline import build_pipeline, Pipeline, Retriever, get_embedder
from backend.app.config import Settings
from backend.app.schema import DocumentFull
from unittest.mock import patch, MagicMock
import numpy as np
from app.pipeline import get_pipeline
from backend.app.vectorstore import InMemoryDocumentStore

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def encode(self, text):
            return np.zeros(384)  # Return zero vector
        def embed_batch(self, texts):
            return [np.zeros(384) for _ in texts]  # Return zero vectors
    return MockEmbeddings()

@pytest.fixture
def mock_store(mock_embeddings):
    """Create a mock document store for testing."""
    return InMemoryDocumentStore(
        embedding_dim=384,
        collection_name="test_documents",
        embeddings_model=mock_embeddings
    )

@patch("backend.app.pipeline.get_embedder")
@patch("backend.app.pipeline.get_vectorstore")
def test_pipeline_query_execution(mock_get_vectorstore, mock_get_embedder, mock_embeddings, mock_store):
    mock_get_embedder.return_value = mock_embeddings
    mock_get_vectorstore.return_value = mock_store
    
    # Create a test document
    test_doc = DocumentFull(content="test content", id="1")
    
    # Set up the mock store to return our test document
    mock_store.query_by_embedding = MagicMock(return_value=[test_doc])
    
    # Create and test pipeline
    pipeline = Pipeline(Retriever(mock_store, Settings()))
    result = pipeline.run("test query")
    
    assert "documents" in result
    assert len(result["documents"]) == 1
    assert result["documents"][0].content == "test content"

@patch("backend.app.pipeline.get_embedder")
@patch("backend.app.pipeline.get_vectorstore")
def test_pipeline_empty_query(mock_get_vectorstore, mock_get_embedder, mock_embeddings, mock_store):
    mock_get_embedder.return_value = mock_embeddings
    mock_get_vectorstore.return_value = mock_store
    
    pipeline = Pipeline(Retriever(mock_store, Settings()))
    with pytest.raises(ValueError, match="Query cannot be empty"):
        pipeline.run("")

@patch("backend.app.pipeline.get_embedder")
@patch("backend.app.pipeline.get_vectorstore")
def test_pipeline_dev_mode(mock_get_vectorstore, mock_get_embedder, mock_embeddings, mock_store):
    mock_get_embedder.return_value = mock_embeddings
    mock_get_vectorstore.return_value = mock_store
    
    # Create a test document
    test_doc = DocumentFull(content="test content", id="1")
    
    # Set up the mock store to return our test document
    mock_store.query_by_embedding = MagicMock(return_value=[test_doc])
    
    pipeline = Pipeline(Retriever(mock_store, Settings()))
    result = pipeline.run("test query")
    
    assert "documents" in result
    assert len(result["documents"]) == 1
    assert result["documents"][0].content == "test content"

def test_pipeline_real_mode_initialization():
    """Test that pipeline in real mode initializes with correct components."""
    settings = Settings()
    with patch('backend.app.pipeline.SentenceTransformer') as mock_st:
        mock_st.return_value = MagicMock()
        pipeline, retriever = build_pipeline(settings=settings, dev=False)
        
        assert hasattr(pipeline, 'retriever')
        assert hasattr(pipeline, 'components')
        assert 'Retriever' in pipeline.components

def test_pipeline_error_handling(mock_embeddings, mock_store):
    """Test pipeline error handling for various failure scenarios."""
    settings = Settings()
    retriever = Retriever(mock_store, settings)
    
    # Test model initialization failure
    with patch('backend.app.pipeline.Retriever.initialize', side_effect=Exception("Model not found")):
        with pytest.raises(Exception) as exc_info:
            build_pipeline(settings=settings, dev=False)
        assert "Failed to build pipeline" in str(exc_info.value)
    
    # Test retrieval failure
    with patch('backend.app.pipeline.SentenceTransformer') as mock_st:
        mock_st.return_value = MagicMock()
        mock_st.return_value.encode.side_effect = Exception("Encoding failed")
        pipeline, _ = build_pipeline(settings=settings, dev=True)  # Use dev mode to avoid actual model loading
        with pytest.raises(Exception) as exc_info:
            pipeline.run(query="test query")
        assert "Pipeline execution failed: Retrieval failed: Encoding failed" in str(exc_info.value)
    
    # Create a new pipeline for the next test
    pipeline, _ = build_pipeline(settings=settings, dev=True)
    
    # Mock retriever to raise an exception
    pipeline.retriever.retrieve = MagicMock(side_effect=Exception("Test error"))
    
    with pytest.raises(Exception, match="Pipeline execution failed: Test error"):
        pipeline.run(query="test query") 
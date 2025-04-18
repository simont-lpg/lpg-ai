import pytest
from backend.app.pipeline import build_pipeline, Pipeline, Retriever, get_embedder
from backend.app.config import Settings
from backend.app.schema import Document
from unittest.mock import patch, MagicMock
import numpy as np
from app.pipeline import get_pipeline

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    mock = MagicMock()
    mock.embed_batch.return_value = [np.zeros(384) for _ in range(1)]
    mock.encode.return_value = np.zeros(384)
    return mock

@pytest.fixture
def mock_vectorstore():
    """Mock vectorstore for testing."""
    mock = MagicMock()
    mock.query_by_embedding.return_value = [
        Document(content="test content", metadata={"score": 0.9})
    ]
    return mock

@pytest.fixture
def settings():
    return Settings(dev_mode=True)

@patch("backend.app.pipeline.get_embedder")
@patch("backend.app.pipeline.get_vectorstore")
def test_pipeline_query_execution(mock_get_vectorstore, mock_get_embedder, mock_embeddings, mock_vectorstore):
    mock_get_embedder.return_value = mock_embeddings
    mock_get_vectorstore.return_value = mock_vectorstore
    mock_vectorstore.query_by_embedding.return_value = [Document(content="test content", metadata={"score": 0.9})]
    
    pipeline = Pipeline(Retriever(mock_vectorstore, Settings()))
    result = pipeline.run("test query")
    
    assert "documents" in result
    assert len(result["documents"]) == 1

@patch("backend.app.pipeline.get_embedder")
@patch("backend.app.pipeline.get_vectorstore")
def test_pipeline_empty_query(mock_get_vectorstore, mock_get_embedder, mock_embeddings, mock_vectorstore):
    mock_get_embedder.return_value = mock_embeddings
    mock_get_vectorstore.return_value = mock_vectorstore
    
    pipeline = Pipeline(Retriever(mock_vectorstore, Settings()))
    with pytest.raises(ValueError, match="Query cannot be empty"):
        pipeline.run("")

@patch("backend.app.pipeline.get_embedder")
@patch("backend.app.pipeline.get_vectorstore")
def test_pipeline_dev_mode(mock_get_vectorstore, mock_get_embedder, settings):
    mock_get_embedder.return_value = MagicMock()
    mock_get_vectorstore.return_value = MagicMock()
    
    pipeline = Pipeline(Retriever(mock_get_vectorstore.return_value, settings))
    result = pipeline.run("test query")
    
    assert "documents" in result
    assert len(result["documents"]) == 0

def test_pipeline_real_mode_initialization():
    """Test that pipeline in real mode initializes with correct components."""
    settings = Settings()
    with patch('backend.app.pipeline.SentenceTransformer') as mock_st:
        mock_st.return_value = MagicMock()
        pipeline, retriever = build_pipeline(settings=settings, dev=False)
        
        assert hasattr(pipeline, 'retriever')
        assert hasattr(pipeline, 'components')
        assert 'retriever' in pipeline.components

def test_pipeline_error_handling():
    """Test pipeline error handling for various failure scenarios."""
    settings = Settings()
    
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
        assert "Encoding failed" in str(exc_info.value) 
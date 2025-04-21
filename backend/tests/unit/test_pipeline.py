import pytest
from backend.app.pipeline import build_pipeline, Pipeline
from backend.app.config import Settings
from backend.app.schema import DocumentFull
from unittest.mock import patch, MagicMock
import numpy as np
from backend.app.vectorstore import InMemoryDocumentStore

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    mock = MagicMock()
    mock.encode.return_value = np.zeros(384)
    mock.embed_batch.return_value = [np.zeros(384)]
    return mock

@pytest.fixture
def mock_store():
    """Create a mock document store for testing."""
    store = MagicMock()
    store.embedding_dim = 384
    store.collection_name = "test_documents"
    return store

def test_pipeline_query_execution(mock_embeddings, mock_store):
    """Test core pipeline functionality with mocked dependencies."""
    # Setup test document
    test_doc = DocumentFull(content="test content", id="1", meta={"namespace": "default"})
    mock_store.query_by_embedding.return_value = [test_doc]
    
    with patch('backend.app.pipeline.SentenceTransformer', return_value=mock_embeddings):
        # Test pipeline in dev mode
        pipeline, _ = build_pipeline(settings=Settings(), document_store=mock_store, dev=True)
        result = pipeline.run("test query")
        
        assert "documents" in result
        assert len(result["documents"]) == 1
        assert result["documents"][0].content == "test content"
        
        # Verify namespace filtering
        result = pipeline.run("test query", params={"Retriever": {"filters": {"namespace": "custom"}}})
        
        # Get the actual call arguments
        call_args = mock_store.query_by_embedding.call_args
        assert call_args is not None
        
        # Check the filters parameter
        assert call_args.kwargs["filters"] == {"namespace": "custom"}
        assert call_args.kwargs["top_k"] == 5

def test_pipeline_error_handling(mock_embeddings, mock_store):
    """Test pipeline error handling for key failure scenarios."""
    settings = Settings()
    
    # Test query execution failure
    mock_store.query_by_embedding.side_effect = Exception("Query failed")
    
    with patch('backend.app.pipeline.SentenceTransformer', return_value=mock_embeddings):
        pipeline, _ = build_pipeline(settings=settings, document_store=mock_store, dev=True)
        with pytest.raises(Exception) as exc_info:
            pipeline.run("test query")
        assert "Pipeline error: Query failed" in str(exc_info.value) 
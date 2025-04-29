import pytest
from backend.app.pipeline import build_pipeline
from backend.app.config import Settings
from backend.app.vectorstore import InMemoryDocumentStore
from unittest.mock import MagicMock
import numpy as np

@pytest.fixture
def mock_store(settings):
    """Create a mock store instance."""
    mock_model = MagicMock()
    mock_model.embedding_dim = settings.embedding_dim
    # Return zero vectors for any number of documents
    mock_model.embed_batch.side_effect = lambda texts: np.zeros((len(texts), settings.embedding_dim))
    store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_model
    )
    return store

def test_pipeline_query_integration(settings, mock_store):
    try:
        # Build pipeline with settings and mock store
        pipeline, _ = build_pipeline(settings=settings, document_store=mock_store, dev=True)
        
        # Test query
        query = "test query"
        result = pipeline.run(query)
        assert result is not None
        assert isinstance(result, dict)
        assert "answers" in result
        assert len(result["answers"]) > 0
        assert isinstance(result["answers"][0], str)
    except Exception as e:
        if "Connection refused" in str(e):
            pytest.skip("Ollama API not available")
        else:
            raise e 
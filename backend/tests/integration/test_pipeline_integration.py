import pytest
import numpy as np
from backend.app.schema import DocumentFull
from backend.app.pipeline import build_pipeline
from backend.app.config import Settings
from backend.app.vectorstore import InMemoryDocumentStore
from unittest.mock import patch, MagicMock

@pytest.mark.integration
def test_pipeline_integration():
    """Test pipeline integration with in-memory store."""
    # Create real document store
    settings = Settings()
    document_store = InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name="test_documents"
    )
    
    # Add test documents
    docs = [
        DocumentFull(id="1", content="Document about machine learning", meta={"namespace": "default"}),
        DocumentFull(id="2", content="Document about data science", meta={"namespace": "other"})
    ]
    document_store.write_documents(docs)
    
    # Mock embeddings model
    mock_embeddings = MagicMock()
    mock_embeddings.encode.return_value = np.zeros(384)
    
    with patch('backend.app.pipeline.SentenceTransformer', return_value=mock_embeddings):
        # Build pipeline
        pipeline, _ = build_pipeline(settings=settings, document_store=document_store, dev=True)
        
        # Test basic query
        result = pipeline.run("machine learning")
        assert len(result["documents"]) == 1
        assert "machine learning" in result["documents"][0].content.lower()
        
        # Test namespace filtering
        result = pipeline.run("data", params={"namespace": "other"})
        assert len(result["documents"]) == 1
        assert result["documents"][0].meta["namespace"] == "other" 
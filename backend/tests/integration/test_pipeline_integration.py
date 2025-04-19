import pytest
import numpy as np
from backend.app.schema import DocumentFull
from backend.app.pipeline import build_pipeline
from backend.app.config import Settings

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def encode(self, text):
            return np.zeros(384)  # Return zero vector
        def embed_batch(self, texts):
            return [np.zeros(384) for _ in texts]  # Return zero vectors
    return MockEmbeddings()

def test_pipeline_integration(mock_embeddings):
    """Test pipeline integration with mock embeddings."""
    settings = Settings()
    pipeline, retriever = build_pipeline(settings=settings, dev=True)
    
    # Add test documents
    docs = [
        DocumentFull(id="1", content="Test document 1"),
        DocumentFull(id="2", content="Test document 2")
    ]
    retriever.document_store.write_documents(docs)
    
    # Test retrieval
    result = pipeline.run(query="test", params={"Retriever": {"top_k": 1}})
    assert len(result["documents"]) == 1
    assert isinstance(result["documents"][0], DocumentFull)
    assert result["documents"][0].content.startswith("Test document") 
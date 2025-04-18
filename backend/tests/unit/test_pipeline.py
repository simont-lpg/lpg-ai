import pytest
from app.pipeline import build_pipeline
from app.config import Settings
from app.schema import Document
from unittest.mock import patch, MagicMock

def test_pipeline_dev_mode():
    """Test that pipeline in dev mode returns expected mock documents."""
    pipeline, _ = build_pipeline(dev=True)
    result = pipeline.run(query="test query")
    
    assert isinstance(result, dict)
    assert "documents" in result
    assert len(result["documents"]) == 2
    assert all(isinstance(doc, Document) for doc in result["documents"])
    assert result["documents"][0].content == "Test document 1"
    assert result["documents"][1].content == "Test document 2"

def test_pipeline_requires_settings():
    """Test that pipeline in non-dev mode requires settings."""
    with pytest.raises(ValueError, match="settings must be provided in non-dev mode"):
        build_pipeline(dev=False)

def test_pipeline_real_mode():
    """Test that pipeline in real mode initializes correctly."""
    settings = Settings()
    pipeline, retriever = build_pipeline(settings=settings, dev=False)
    
    assert pipeline is not None
    assert retriever is not None
    assert retriever.model is not None
    assert retriever.document_store is not None

def test_pipeline_retrieval_empty_store():
    """Test pipeline behavior with empty document store."""
    settings = Settings()
    pipeline, _ = build_pipeline(settings=settings, dev=False)
    
    result = pipeline.run(query="test query")
    assert isinstance(result, dict)
    assert "documents" in result
    assert len(result["documents"]) == 0  # Empty store should return empty list

def test_pipeline_invalid_query():
    """Test pipeline behavior with invalid query input."""
    settings = Settings()
    pipeline, _ = build_pipeline(settings=settings, dev=False)
    
    with pytest.raises(ValueError, match="Query cannot be empty"):
        pipeline.run(query="")

def test_pipeline_model_download_failure():
    """Test pipeline behavior when model download fails."""
    settings = Settings()
    
    with patch('app.pipeline.SentenceTransformer', autospec=True) as mock_model:
        mock_model.side_effect = Exception("Model download failed")
        
        with pytest.raises(Exception, match="Model download failed"):
            build_pipeline(settings=settings, dev=False)

def test_pipeline_retriever_failure():
    """Test pipeline behavior when retriever fails."""
    settings = Settings()
    pipeline, _ = build_pipeline(settings=settings, dev=False)
    
    # Mock the retriever's retrieve method
    with patch.object(pipeline.retriever, 'retrieve') as mock_retrieve:
        mock_retrieve.side_effect = Exception("Retrieval failed")
        
        with pytest.raises(Exception, match="Retrieval failed"):
            pipeline.run(query="test query")

def test_pipeline_with_top_k():
    """Test pipeline respects top_k parameter."""
    settings = Settings()
    pipeline, _ = build_pipeline(settings=settings, dev=False)
    
    result = pipeline.run(query="test query", params={"Retriever": {"top_k": 3}})
    assert isinstance(result, dict)
    assert "documents" in result
    assert len(result["documents"]) <= 3  # Should respect top_k limit 
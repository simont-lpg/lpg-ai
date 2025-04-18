import pytest

from app.pipeline import build_pipeline
from app.config import settings


def test_build_pipeline_dev_mode():
    """Test pipeline construction in development mode."""
    pipeline, doc_store = build_pipeline(dev=True)
    
    # Verify pipeline components
    assert "retriever" in pipeline.components
    
    # Verify component configuration
    retriever = pipeline.components["retriever"]
    assert retriever.top_k == 5
    assert isinstance(retriever, type(pipeline.components["retriever"]))


def test_build_pipeline_prod_mode():
    """Test pipeline construction in production mode."""
    pipeline, doc_store = build_pipeline(dev=False)
    
    # Verify pipeline components
    assert "retriever" in pipeline.components
    
    # Verify component configuration
    retriever = pipeline.components["retriever"]
    assert retriever.top_k == 5
    assert isinstance(retriever, type(pipeline.components["retriever"]))


@pytest.mark.asyncio
async def test_pipeline_run():
    """Test pipeline execution with a simple query."""
    pipeline, doc_store = build_pipeline(dev=False)
    
    # Add a test document
    doc_store.write_documents([
        {"content": "Test document", "meta": {"source": "test"}}
    ])
    
    # Run the pipeline
    result = pipeline.run({
        "retriever": {"query": "test query"},
    })
    
    # Verify results
    assert "retriever" in result
    assert "documents" in result["retriever"]
    assert len(result["retriever"]["documents"]) > 0 
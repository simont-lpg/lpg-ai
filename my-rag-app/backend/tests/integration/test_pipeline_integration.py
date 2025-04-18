import pytest
from pathlib import Path

from app.pipeline import build_pipeline
from app.config import settings


@pytest.fixture
def test_documents():
    """Fixture providing test documents."""
    return [
        {
            "content": "The quick brown fox jumps over the lazy dog.",
            "meta": {"source": "test1", "type": "test"}
        },
        {
            "content": "Python is a popular programming language.",
            "meta": {"source": "test2", "type": "test"}
        },
        {
            "content": "Machine learning is a subset of artificial intelligence.",
            "meta": {"source": "test3", "type": "test"}
        }
    ]


@pytest.fixture
def pipeline_and_store(tmp_path):
    """Fixture providing a configured pipeline with test documents."""
    # Override the persist directory
    settings.chroma_persist_dir = tmp_path / "test_chroma"
    
    # Build and return the pipeline
    pipeline, doc_store = build_pipeline(dev=False)
    return pipeline, doc_store


def test_pipeline_with_documents(pipeline_and_store, test_documents):
    """Test the pipeline with actual documents."""
    pipeline, doc_store = pipeline_and_store
    
    # Add documents to the store
    doc_store.write_documents(test_documents)
    
    # Run a query
    result = pipeline.run({
        "retriever": {"query": "What is Python?"},
    })
    
    # Verify results
    assert "retriever" in result
    documents = result["retriever"]["documents"]
    assert len(documents) > 0
    
    # Verify the most relevant document
    assert "Python" in documents[0].content
    assert documents[0].meta["source"] == "test2"


def test_pipeline_with_multiple_queries(pipeline_and_store, test_documents):
    """Test the pipeline with multiple queries."""
    pipeline, doc_store = pipeline_and_store
    
    # Add documents to the store
    doc_store.write_documents(test_documents)
    
    # Test different queries
    queries = [
        "What is Python?",
        "Tell me about machine learning",
        "What does the fox do?"
    ]
    
    for query in queries:
        result = pipeline.run({
            "retriever": {"query": query},
        })
        
        assert "retriever" in result
        documents = result["retriever"]["documents"]
        assert len(documents) > 0
        assert query.lower() in documents[0].content.lower()


def test_pipeline_persistence(pipeline_and_store, test_documents, tmp_path):
    """Test that the pipeline persists documents between runs."""
    pipeline, doc_store = pipeline_and_store
    
    # Add documents to the store
    doc_store.write_documents(test_documents)
    
    # Create a new pipeline instance
    new_pipeline, new_store = build_pipeline(dev=False)
    
    # Run a query with the new pipeline
    result = new_pipeline.run({
        "retriever": {"query": "What is Python?"},
    })
    
    # Verify the documents are still there
    assert "retriever" in result
    documents = result["retriever"]["documents"]
    assert len(documents) > 0
    assert "Python" in documents[0].content 
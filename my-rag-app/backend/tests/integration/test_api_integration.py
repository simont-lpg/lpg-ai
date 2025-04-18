import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import pipeline, doc_store
from app.config import settings


client = TestClient(app)


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


def test_api_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_query_endpoint(test_documents):
    """Test the query endpoint with actual documents."""
    # Add documents to the store
    doc_store.write_documents(test_documents)
    
    # Test a query
    response = client.post(
        "/query",
        json={"query": "What is Python?"}
    )
    
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 0
    
    # Verify the most relevant result
    assert "Python" in results[0]["content"]
    assert results[0]["meta"]["source"] == "test2"


def test_api_query_with_multiple_queries(test_documents):
    """Test the query endpoint with multiple queries."""
    # Add documents to the store
    doc_store.write_documents(test_documents)
    
    # Test different queries
    queries = [
        "What is Python?",
        "Tell me about machine learning",
        "What does the fox do?"
    ]
    
    for query in queries:
        response = client.post(
            "/query",
            json={"query": query}
        )
        
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) > 0
        assert query.lower() in results[0]["content"].lower()


def test_api_error_handling():
    """Test API error handling."""
    # Test with invalid input
    response = client.post(
        "/query",
        json={"invalid": "input"}
    )
    assert response.status_code == 422
    
    # Test with empty query
    response = client.post(
        "/query",
        json={"query": ""}
    )
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list) 
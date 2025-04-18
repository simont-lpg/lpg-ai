from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_query_endpoint():
    """Test the query endpoint."""
    # First, add some test documents
    response = client.post(
        "/query",
        json={"query": "test query"}
    )
    
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    
    # Verify response structure
    if results:  # If any results were returned
        result = results[0]
        assert "content" in result
        assert "meta" in result
        assert "score" in result


def test_query_endpoint_error_handling():
    """Test error handling in the query endpoint."""
    # Test with invalid input
    response = client.post(
        "/query",
        json={"invalid": "input"}
    )
    assert response.status_code == 422  # Validation error
    
    # Test with empty query
    response = client.post(
        "/query",
        json={"query": ""}
    )
    assert response.status_code == 200  # Should handle empty queries gracefully 
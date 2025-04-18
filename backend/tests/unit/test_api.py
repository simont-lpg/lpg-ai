from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from unittest.mock import patch

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Haystack RAG Service is running"}

def test_query_endpoint_validation():
    """Test query endpoint input validation."""
    # Test missing query
    response = client.post("/query", json={})
    assert response.status_code == 422
    
    # Test invalid top_k
    response = client.post("/query", json={"query": "test", "top_k": -1})
    assert response.status_code == 422
    
    # Test empty query
    response = client.post("/query", json={"query": ""})
    assert response.status_code == 422
    
    # Test non-string query
    response = client.post("/query", json={"query": 123})
    assert response.status_code == 422
    assert "string_type" in response.json()["detail"][0]["type"]

def test_query_endpoint_success():
    """Test successful query returns expected format."""
    response = client.post("/query", json={"query": "test query"})
    assert response.status_code == 200
    data = response.json()
    assert "answers" in data
    assert "documents" in data
    assert isinstance(data["answers"], list)
    assert isinstance(data["documents"], list)
    
    # Test response structure
    if data["documents"]:
        doc = data["documents"][0]
        assert "content" in doc
        assert "id" in doc
        assert "score" in doc

def test_query_endpoint_with_top_k():
    """Test query endpoint respects top_k parameter."""
    response = client.post("/query", json={"query": "test", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) <= 3  # Less than or equal because store might be empty

def test_query_endpoint_pipeline_error():
    """Test query endpoint handles pipeline errors gracefully."""
    with patch('backend.app.main.pipeline') as mock_pipeline:
        mock_pipeline.run.side_effect = Exception("Pipeline error")
        
        response = client.post("/query", json={"query": "test"})
        assert response.status_code == 500
        assert response.json()["detail"]["error"] == "Pipeline error"

def test_query_endpoint_invalid_json():
    """Test query endpoint handles invalid JSON input."""
    response = client.post("/query", data="invalid json")
    assert response.status_code == 422

def test_health_check_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"} 
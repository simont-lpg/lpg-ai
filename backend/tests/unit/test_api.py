from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from unittest.mock import patch, MagicMock
from backend.app.config import Settings
from backend.app.schema import DocumentFull, Response

client = TestClient(app)

@pytest.fixture
def test_settings():
    """Mock settings for testing."""
    return Settings(
        embedding_model="all-MiniLM-L6-v2",
        embedding_dim=384,
        collection_name="test_collection"
    )

def test_root_endpoint():
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Haystack RAG Service is running"}

def test_query_endpoint_validation():
    """Test query endpoint input validation."""
    # Test missing text field
    response = client.post("/query", json={})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "text"]

    # Test invalid top_k
    response = client.post("/query", json={"text": "test", "top_k": -1})
    assert response.status_code == 422
    assert "greater than or equal to 1" in response.json()["detail"][0]["msg"]

    # Test empty query
    response = client.post("/query", json={"text": ""})
    assert response.status_code == 422
    assert "string_too_short" in response.json()["detail"][0]["type"]

    # Test non-string query
    response = client.post("/query", json={"text": 123})
    assert response.status_code == 422
    assert "string_type" in response.json()["detail"][0]["type"]

def test_query_endpoint_success(test_settings):
    """Test query endpoint returns properly formatted results."""
    with patch('backend.app.dependencies.get_document_store') as mock_get_store:
        # Setup mock store
        mock_store = MagicMock()
        mock_store.embedding_dim = 384
        mock_store.collection_name = "test_collection"
        test_doc = DocumentFull(content="Test doc", id="1", meta={"namespace": "default"}, score=0.9)
        mock_store.query_by_embedding.return_value = [test_doc]
        mock_get_store.return_value = mock_store
        
        # Setup mock embeddings
        mock_embeddings = MagicMock()
        mock_embeddings.encode.return_value = [0.1] * 384
        
        # Mock the pipeline and retriever
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [test_doc]
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {"documents": [test_doc], "answers": []}
        
        with patch('backend.app.pipeline.SentenceTransformer', return_value=mock_embeddings), \
             patch('backend.app.pipeline.Retriever', return_value=mock_retriever), \
             patch('backend.app.pipeline.Pipeline', return_value=mock_pipeline):
            # Test basic query
            response = client.post("/query", json={"text": "test"})
            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            assert len(data["documents"]) == 1
            assert data["documents"][0]["content"] == "Test doc"
            assert data["documents"][0]["meta"]["namespace"] == "default"

def test_query_endpoint_pipeline_error(test_settings):
    """Test query endpoint handles pipeline errors gracefully."""
    with patch('backend.app.dependencies.get_document_store') as mock_get_store:
        mock_store = MagicMock()
        mock_store.embedding_dim = 384
        mock_store.collection_name = "test_collection"
        mock_get_store.return_value = mock_store
        
        mock_embeddings = MagicMock()
        mock_embeddings.encode.return_value = [0.1] * 384
        
        # Mock the pipeline and retriever
        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = Exception("Pipeline error")
        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = Exception("Pipeline error")
        
        with patch('backend.app.pipeline.SentenceTransformer', return_value=mock_embeddings), \
             patch('backend.app.pipeline.Retriever', return_value=mock_retriever), \
             patch('backend.app.pipeline.Pipeline', return_value=mock_pipeline):
            response = client.post("/query", json={"text": "test"})
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert data["detail"]["error"] == "Pipeline error"
            assert data["detail"]["documents"] == []
            assert data["detail"]["answers"] == []

def test_query_endpoint_invalid_json():
    """Test query endpoint handles invalid JSON input."""
    response = client.post("/query", data="invalid json")
    assert response.status_code == 422

def test_health_check_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_response_model():
    """Test that the Response model correctly validates input."""
    # Test valid response
    valid_response = {
        "answers": [],
        "documents": [
            {
                "content": "test content",
                "id": "1",
                "meta": {"namespace": "default"}
            }
        ],
        "error": None
    }
    response = Response(**valid_response)
    assert len(response.documents) == 1
    assert response.documents[0]["content"] == "test content"
    assert response.error is None
    
    # Test response with error
    error_response = {
        "answers": [],
        "documents": [],
        "error": "Pipeline error"
    }
    response = Response(**error_response)
    assert len(response.documents) == 0
    assert response.error == "Pipeline error" 
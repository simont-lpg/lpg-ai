from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from unittest.mock import patch, MagicMock
from backend.app.config import Settings
from backend.app.schema import DocumentFull, Response, DeleteDocumentsRequest
from backend.app.dependencies import get_document_store, get_embedder, get_settings

@pytest.fixture
def mock_store():
    """Mock document store for testing."""
    mock = MagicMock()
    mock.get_all_documents.return_value = [
        DocumentFull(id="1", content="test content", meta={"namespace": "test"})
    ]
    mock.delete_documents.return_value = 1
    return mock

@pytest.fixture
def mock_pipeline():
    """Mock pipeline for testing."""
    mock = MagicMock()
    mock.run.return_value = {
        "documents": [MagicMock(
            content="test content",
            id="1",
            meta={"namespace": "test"},
            to_dict=lambda: {
                "content": "test content",
                "id": "1",
                "meta": {"namespace": "test"}
            }
        )],
        "answers": ["test answer"]
    }
    return mock

@pytest.fixture
def client(mock_store, mock_pipeline, settings):
    """Test client with mocked dependencies."""
    app.dependency_overrides[get_document_store] = lambda: mock_store
    app.dependency_overrides[get_settings] = lambda: settings
    
    with patch('backend.app.main.build_pipeline', return_value=(mock_pipeline, None)):
        with TestClient(app) as client:
            yield client
    
    app.dependency_overrides = {}

def test_root_endpoint(client):
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Haystack RAG Service is running"}

def test_query_endpoint_validation(client):
    """Test query endpoint input validation."""
    # Test missing text field
    response = client.post("/query", json={})
    assert response.status_code == 422
    assert "text" in response.json()["detail"][0]["loc"]

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

def test_query_endpoint_success(client, mock_pipeline):
    """Test successful query endpoint."""
    response = client.post(
        "/query",
        json={
            "text": "test query",
            "top_k": 5,
            "namespace": "test"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "answers" in data
    assert "documents" in data
    assert len(data["documents"]) == 1
    assert data["documents"][0]["content"] == "test content"

def test_query_endpoint_pipeline_error(client, mock_pipeline):
    """Test query endpoint with pipeline error."""
    # Setup mock pipeline to raise an exception
    mock_pipeline.run.side_effect = Exception("Test error")

    response = client.post(
        "/query",
        json={
            "text": "test query",
            "top_k": 5,
            "namespace": "test"
        }
    )
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]

def test_query_endpoint_invalid_json(client):
    """Test query endpoint handles invalid JSON input."""
    response = client.post("/query", data="invalid json")
    assert response.status_code == 422

def test_health_check_endpoint(client):
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

def test_get_documents(client, mock_store):
    """Test the get documents endpoint."""
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_documents_with_namespace(client, mock_store):
    """Test the get documents endpoint with namespace filter."""
    response = client.get("/documents?namespace=test")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_delete_documents(client, mock_store):
    """Test the delete documents endpoint."""
    response = client.post(
        "/documents/delete",
        json={"file_name": "test.txt"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data
    assert "status" in data
    assert data["status"] == "success"

def test_settings_endpoint(client, settings):
    """Test the settings endpoint."""
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    assert "embedding_model" in data
    assert "generator_model" in data
    assert data["environment"] == settings.environment
    assert data["embedding_model"] == settings.embedding_model
    assert data["generator_model"] == settings.generator_model_name 
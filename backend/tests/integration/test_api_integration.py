import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schema import DocumentFull
from backend.app.config import Settings
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.dependencies import get_document_store
from unittest.mock import patch, MagicMock
from backend.app.pipeline import build_pipeline
import os

client = TestClient(app)

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    mock = MagicMock()
    mock.encode.return_value = [0.1] * 384
    return mock

@pytest.fixture
def test_settings():
    """Get test settings with Mistral configuration."""
    return Settings(
        embedding_model="all-MiniLM-L6-v2",
        embedding_model_name="all-MiniLM-L6-v2",
        embedding_dim=384,
        ollama_api_url="http://localhost:11434",
        collection_name="test_documents",
        generator_model_name="mistral:latest",
        dev_mode=False
    )

@pytest.mark.integration
def test_api_integration(mock_embeddings):
    """End-to-end integration test of the query endpoint."""
    # Create a real in-memory store
    store = InMemoryDocumentStore(
        embedding_dim=384,
        collection_name="test_documents"
    )
    
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: store
    
    try:
        # Add test documents
        docs = [
            DocumentFull(id="1", content="Document about machine learning", meta={"namespace": "default"}),
            DocumentFull(id="2", content="Document about data science", meta={"namespace": "other"})
        ]
        store.write_documents(docs)
        
        # Test query endpoint with mocked embeddings
        with patch('backend.app.pipeline.SentenceTransformer', return_value=mock_embeddings):
            # Test basic query
            response = client.post("/query", json={"text": "machine learning"})
            assert response.status_code == 200
            data = response.json()
            assert len(data["documents"]) == 1
            assert "machine learning" in data["documents"][0]["content"].lower()
            
            # Test namespace filtering
            response = client.post("/query", json={"text": "data", "namespace": "other"})
            assert response.status_code == 200
            data = response.json()
            assert len(data["documents"]) == 1
            assert data["documents"][0]["meta"]["namespace"] == "other"
    
    finally:
        # Clean up
        app.dependency_overrides.clear()

def test_mistral_instruct_integration(test_settings):
    """Test that Mistral-instruct returns natural language answers."""
    # Create a test document store with some content
    document_store = InMemoryDocumentStore(
        embedding_dim=test_settings.embedding_dim,
        collection_name=test_settings.collection_name
    )
    
    # Add a test document
    test_doc = DocumentFull(
        content="Alice said 'Hello, how are you?' to Bob.",
        meta={"source": "test.txt"},
        id="1"
    )
    document_store.write_documents([test_doc])
    
    # Build pipeline with Mistral-instruct
    pipeline, _ = build_pipeline(test_settings, document_store)
    
    # Test query
    query = "What did Alice say?"
    response = pipeline.run(query=query)
    
    # Verify response
    assert "answers" in response
    assert len(response["answers"]) > 0
    assert isinstance(response["answers"], list)
    assert isinstance(response["answers"][0], str)
    assert len(response["answers"][0]) > 0
    assert "Alice" in response["answers"][0]  # Basic verification of answer content
    
    # Verify documents
    assert "documents" in response
    assert len(response["documents"]) > 0
    assert response["documents"][0].content == test_doc.content 
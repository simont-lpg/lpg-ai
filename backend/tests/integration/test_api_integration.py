import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.vectorstore import get_vectorstore
from app.schema import Document
from app.config import Settings

client = TestClient(app)

@pytest.mark.integration
def test_query_endpoint_integration():
    # Setup
    settings = Settings()
    vectorstore = get_vectorstore(settings)
    
    # Write test documents
    docs = [
        Document(content="Integration test document 1", id="int1"),
        Document(content="Integration test document 2", id="int2")
    ]
    vectorstore.write_documents(docs)
    
    # Test API endpoint
    response = client.post("/query", json={"query": "Integration"})
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert len(data["documents"]) > 0
    
    # Clean up
    vectorstore.delete_documents(["int1", "int2"]) 
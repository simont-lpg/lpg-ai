import pytest
from fastapi.testclient import TestClient
import app.main
from app.schema import DocumentFull
from app.dependencies import get_document_store, get_embedder
import app.dependencies

@pytest.fixture
def client(monkeypatch):
    # Reset global document store
    app.dependencies._document_store = None
    
    # Create test documents
    test_documents = [
        DocumentFull(
            id="1",
            content="content1",
            meta={
                "file_name": "test1.txt",
                "namespace": "default",
                "file_size": 1000
            }
        ),
        DocumentFull(
            id="2",  # Different ID for same file
            content="content2",
            meta={
                "file_name": "test1.txt",
                "namespace": "default",
                "file_size": 1000
            }
        ),
        DocumentFull(
            id="3",
            content="content3",
            meta={
                "file_name": "test2.txt",
                "namespace": "test",
                "file_size": 2000
            }
        )
    ]
    
    # Create a mock document store with test data
    class MockStore:
        def __init__(self):
            self.documents = []
            self.embedding_dim = 768

        def add_documents(self, documents):
            for doc in documents:
                self.documents.append({
                    "id": doc.id,
                    "content": doc.content,
                    "meta": doc.meta
                })
            return len(documents)

        def get(self, ids=None, where=None):
            if not ids and not where:
                return {
                    "ids": [doc["id"] for doc in self.documents],
                    "documents": [doc["content"] for doc in self.documents],
                    "metadatas": [doc["meta"] for doc in self.documents]
                }

            filtered_docs = []
            for doc in self.documents:
                if ids and doc["id"] not in ids:
                    continue
                if where:
                    match = True
                    for key, value in where.items():
                        if key not in doc["meta"] or doc["meta"][key] != value:
                            match = False
                            break
                    if not match:
                        continue
                filtered_docs.append(doc)

            return {
                "ids": [doc["id"] for doc in filtered_docs],
                "documents": [doc["content"] for doc in filtered_docs],
                "metadatas": [doc["meta"] for doc in filtered_docs]
            }
    
    # Create a mock embedder
    class MockEmbedder:
        def encode(self, texts, convert_to_numpy=True):
            return [[0.1] * 768] * len(texts)
    
    # Create and populate mock store
    mock_store = MockStore()
    mock_store.add_documents(test_documents)
    
    # Patch both dependencies
    monkeypatch.setattr(app.dependencies, "_document_store", mock_store)
    monkeypatch.setattr("app.dependencies.get_embedder", lambda: MockEmbedder())
    
    # Create test client
    test_client = TestClient(app.main.app)
    return test_client

def test_get_files_with_size(client):
    """Test that the /files endpoint returns file size in metadata."""
    response = client.get("/files")
    assert response.status_code == 200
    
    data = response.json()
    assert "files" in data
    files = data["files"]
    
    # Verify file sizes are included and correct
    assert len(files) == 2  # Two unique files
    
    # Check first file
    file1 = next(f for f in files if f["filename"] == "test1.txt")
    assert file1["file_size"] == 1000
    assert file1["document_count"] == 2
    
    # Check second file
    file2 = next(f for f in files if f["filename"] == "test2.txt")
    assert file2["file_size"] == 2000
    assert file2["document_count"] == 1 
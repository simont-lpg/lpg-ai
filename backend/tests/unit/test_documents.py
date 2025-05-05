import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schema import DocumentFull
from backend.app.dependencies import get_document_store
from unittest.mock import MagicMock

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def dummy_docs():
    return [
        DocumentFull(id="1", content="A", meta={"namespace": "foo"}),
        DocumentFull(id="2", content="B", meta={"namespace": "foo"}),
        DocumentFull(id="3", content="C", meta={"namespace": "bar"}),
    ]

@pytest.fixture
def dummy_store():
    class DummyStore:
        def __init__(self):
            self.documents = []
            
        def add(self, documents, metadatas, ids):
            for doc, meta, doc_id in zip(documents, metadatas, ids):
                self.documents.append({
                    "id": doc_id,
                    "content": doc,
                    "meta": meta
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
            
        def delete(self, ids=None):
            if ids is None:
                self.documents = []
                return
            
            self.documents = [doc for doc in self.documents if doc["id"] not in ids]
            return len(ids)
    
    return DummyStore()

def test_get_all_and_filtering(client, dummy_docs, dummy_store):
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: dummy_store
    
    try:
        # Add test documents
        dummy_store.add(
            documents=[doc.content for doc in dummy_docs],
            metadatas=[doc.meta for doc in dummy_docs],
            ids=[doc.id for doc in dummy_docs]
        )
        
        # no namespace → all 3
        resp = client.get("/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        
        # namespace=foo → 2
        resp = client.get("/documents?namespace=foo")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(d["meta"]["namespace"] == "foo" for d in data)
        
        # namespace=bar → 1
        resp = client.get("/documents?namespace=bar")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["meta"]["namespace"] == "bar"
    finally:
        app.dependency_overrides.clear()

def test_error_path(client):
    # Create a store that raises an exception
    class ErrorStore:
        def get(self, ids=None, where=None):
            raise Exception("boom")
    
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: ErrorStore()
    
    try:
        # Test the error case
        resp = client.get("/documents")
        assert resp.status_code == 500
        error_data = resp.json()
        assert "detail" in error_data
        assert "error" in error_data["detail"]
        assert error_data["detail"]["error"] == "boom"
    finally:
        app.dependency_overrides.clear()

def test_delete_documents_success(client, dummy_store):
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: dummy_store
    
    try:
        # Add test documents
        dummy_store.add(
            documents=["A", "B", "C"],
            metadatas=[
                {"file_name": "test.txt"},
                {"file_name": "test.txt"},
                {"file_name": "other.txt"}
            ],
            ids=["1", "2", "3"]
        )
        
        # Test successful deletion
        resp = client.post("/documents/delete", json={"file_name": "test.txt"})
        assert resp.status_code == 200
        
        # Verify documents were deleted
        results = dummy_store.get()
        assert len(results["documents"]) == 1
        assert results["documents"][0] == "C"
    finally:
        app.dependency_overrides.clear() 
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schema import DocumentFull
from app.config import Settings
from app.dependencies import get_document_store
from unittest.mock import patch
import json

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def dummy_docs():
    return [
        DocumentFull(id="1", content="A", meta={"namespace": "foo"}),
        DocumentFull(id="2", content="B", meta={"namespace": "foo"}),
        DocumentFull(id="3", content="C", meta={"namespace": "bar"})
    ]

@pytest.fixture
def dummy_store(dummy_docs):
    class DummyStore:
        def __init__(self, docs):
            self._docs = docs
        def get_all_documents(self, filters=None):
            if filters and "namespace" in filters:
                return [d for d in self._docs if d.meta.get("namespace")==filters["namespace"]]
            return self._docs
    return DummyStore(dummy_docs)

def override_get_document_store(store):
    async def _get_document_store():
        return store
    return _get_document_store

def test_get_all_and_filtering(client, dummy_docs, dummy_store):
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: dummy_store
    
    try:
        # no namespace → all 3
        resp = client.get("/documents")
        assert resp.status_code == 200
        assert [d["id"] for d in resp.json()] == ["1","2","3"]
        
        # filter foo → first two only
        resp = client.get("/documents", params={"namespace":"foo"})
        assert resp.status_code == 200
        assert [d["id"] for d in resp.json()] == ["1","2"]
        
        # filter none → empty list
        resp = client.get("/documents", params={"namespace":"none"})
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        # Clean up the override
        app.dependency_overrides.clear()

def test_error_path(client):
    # Create a store that raises an exception
    class ErrorStore:
        def get_all_documents(self, filters=None):
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
        # Clean up the override
        app.dependency_overrides.clear() 

def test_delete_documents_success(client, dummy_store):
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: dummy_store
    
    try:
        # Mock the delete_documents method to return a count
        dummy_store.delete_documents_by_file_name = lambda file_name: 123
    
        # Test successful deletion
        resp = client.post("/documents/delete", json={"file_name": "test.txt"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 123
        assert data["status"] == "success"
    finally:
        # Clean up
        app.dependency_overrides.clear()

def test_delete_documents_missing_file_name(client):
    # Test missing file_name field
    resp = client.post("/documents/delete", json={})
    assert resp.status_code == 422

def test_delete_documents_error(client):
    # Create a store that raises an exception
    class ErrorStore:
        def delete_documents_by_file_name(self, file_name):
            raise Exception("boom")
    
    # Override the dependency
    app.dependency_overrides[get_document_store] = lambda: ErrorStore()
    
    try:
        # Test the error case
        resp = client.post("/documents/delete", json={"file_name": "test.txt"})
        assert resp.status_code == 500
    finally:
        # Clean up
        app.dependency_overrides.clear() 
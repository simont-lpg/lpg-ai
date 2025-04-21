import io
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schema import DocumentFull

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_data_dir():
    return os.path.join(os.path.dirname(__file__), '..', 'data')

def make_file(name, content, media_type):
    return ('files', (name, io.BytesIO(content), media_type))

def test_ingest_no_files(client):
    # Missing files should 422
    resp = client.post("/ingest", files=[])
    assert resp.status_code == 422

def test_ingest_unsupported_type(client):
    # Unsupported extension → success with zero chunks
    files = [ make_file("foo.xyz", b"garbage", "application/octet-stream") ]
    resp = client.post("/ingest", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["files_ingested"] == 0
    assert body["total_chunks"] == 0

def test_ingest_happy_path(client, monkeypatch):
    # stub out actual document store and converter so we can control chunk count
    class DummyStore:
        def write_documents(self, chunks):
            # pretend we saw 3 chunks per file
            self.saved = chunks
    dummy_store = DummyStore()
    # monkey‑patch our DI
    monkeypatch.setattr("app.dependencies.get_document_store", lambda: dummy_store)
    # stub converter to always return exactly 3 chunks for any file
    class MockConverter:
        def run(self, *args, **kwargs):
            return [
                DocumentFull(id="1", content="chunk1", meta={"namespace": "ns"}),
                DocumentFull(id="2", content="chunk2", meta={"namespace": "ns"}),
                DocumentFull(id="3", content="chunk3", meta={"namespace": "ns"})
            ]
    monkeypatch.setattr("app.ingest.SimpleConverter", lambda *args, **kwargs: MockConverter())
    # send two text files
    files = [
        make_file("a.txt", b"hello", "text/plain"),
        make_file("b.txt", b"world", "text/plain")
    ]
    resp = client.post("/ingest", files=files, data={"namespace":"ns"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["namespace"] == "ns"
    assert body["files_ingested"] == 2
    assert body["total_chunks"] == 6  # 3 chunks per file * 2 files 

def test_ingest_large_file(client, monkeypatch, test_data_dir):
    # Create a large test file (simulating Alice in Wonderland)
    large_content = b"Once upon a time..." * 10000  # This creates a ~158KB file
    large_file = make_file("alice.txt", large_content, "text/plain")
    
    # stub out document store
    class DummyStore:
        def write_documents(self, chunks):
            self.saved = chunks
    dummy_store = DummyStore()
    monkeypatch.setattr("app.dependencies.get_document_store", lambda: dummy_store)
    
    # stub converter to handle large content
    class MockConverter:
        def run(self, *args, **kwargs):
            # Simulate chunking of large content
            content = args[0] if args else ""
            chunk_size = 1000  # Simulate reasonable chunk size
            chunks = []
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                chunks.append(DocumentFull(
                    id=f"chunk_{i}",
                    content=chunk,
                    meta={"namespace": "ns"}
                ))
            return chunks
    
    monkeypatch.setattr("app.ingest.SimpleConverter", lambda *args, **kwargs: MockConverter())
    
    # Test ingestion
    resp = client.post("/ingest", files=[large_file], data={"namespace": "ns"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["namespace"] == "ns"
    assert body["files_ingested"] == 1
    assert body["total_chunks"] > 1  # Should have multiple chunks for large file 

def test_ingest_file_size(client, monkeypatch):
    """Test that file size is correctly captured and stored in metadata."""
    # Create a test file with known size
    test_content = b"Hello, world!" * 100  # 1300 bytes
    test_file = make_file("test.txt", test_content, "text/plain")
    
    # Reset global document store
    import app.dependencies
    app.dependencies._document_store = None
    
    # Stub document store
    class DummyStore:
        def __init__(self):
            self.saved = None
            
        def write_documents(self, chunks):
            self.saved = chunks
            return len(chunks)  # Return number of documents written
            
    dummy_store = DummyStore()
    monkeypatch.setattr(app.dependencies, "_document_store", dummy_store)
    
    # Stub embedder
    class MockEmbedder:
        def encode(self, texts, convert_to_numpy=True):
            return [[0.1] * 384] * len(texts)  # Return dummy embeddings
    monkeypatch.setattr("app.dependencies.get_embedder", lambda: MockEmbedder())
    
    # Stub converter
    class MockConverter:
        def run(self, *args, **kwargs):
            return [
                DocumentFull(id="1", content="chunk1", meta={"file_size": len(test_content)}),
                DocumentFull(id="2", content="chunk2", meta={"file_size": len(test_content)})
            ]
    monkeypatch.setattr("app.ingest.SimpleConverter", lambda *args, **kwargs: MockConverter())
    
    # Test ingestion
    resp = client.post("/ingest", files=[test_file])
    assert resp.status_code == 200
    
    # Verify file size was stored in metadata
    assert dummy_store.saved is not None
    saved_docs = dummy_store.saved
    assert len(saved_docs) > 0
    for doc in saved_docs:
        assert doc.meta["file_size"] == len(test_content) 
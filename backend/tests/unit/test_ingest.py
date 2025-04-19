import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schema import DocumentFull

@pytest.fixture
def client():
    return TestClient(app)

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
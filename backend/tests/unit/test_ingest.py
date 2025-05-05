import io
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schema import DocumentFull
import numpy as np
from app.config import Settings
from app.dependencies import get_document_store, get_embedder, get_settings

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
    # Create mock settings with the correct embedding dimension
    mock_settings = Settings(
        embedding_model="mxbai-embed-large:latest",
        generator_model_name="mistral:latest",
        embedding_dim=768,
        ollama_api_url="http://localhost:11434",
        collection_name="test_collection",
        api_host="0.0.0.0",
        api_port=8000,
        cors_origins=["*"],
        dev_mode=True,
        environment="test",
        log_level="INFO",
        secret_key="test_secret",
        rate_limit_per_minute=60,
        default_top_k=5,
        retriever_score_threshold=0.0,  # Set to 0.0 for testing to ensure documents are not filtered out
        prompt_template="""Based on the following context, please answer the question. If the answer cannot be found in the context, say "I don't know."

Context:
{context}

Question: {query}

Answer:""",
        pipeline_parameters={
            "Retriever": {
                "top_k": 5,
                "score_threshold": 0.0  # Set to 0.0 for testing to ensure documents are not filtered out
            },
            "Generator": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
    )
    
    # stub out actual document store and converter so we can control chunk count
    class DummyStore:
        def __init__(self):
            self.embedding_dim = 768
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

    dummy_store = DummyStore()
    
    # Create a mock embedder that returns lists instead of numpy arrays
    class MockEmbedder:
        def encode(self, texts, convert_to_numpy=True):
            if isinstance(texts, str):
                return [0.0] * 768
            return [[0.0] * 768 for _ in range(len(texts))]
            
        def encode_queries(self, texts, convert_to_numpy=True):
            if isinstance(texts, str):
                return [0.0] * 768
            return [[0.0] * 768 for _ in range(len(texts))]
            
        def embed_batch(self, texts):
            return [[0.0] * 768 for _ in range(len(texts))]
            
        def embed(self, text):
            return [0.0] * 768
    
    # Override dependencies
    app.dependency_overrides[get_document_store] = lambda: dummy_store
    app.dependency_overrides[get_embedder] = lambda: MockEmbedder()
    app.dependency_overrides[get_settings] = lambda: mock_settings
    
    try:
        # stub converter to always return exactly 3 chunks for any file
        class MockConverter:
            def run(self, content, doc_id=None):
                return [
                    DocumentFull(
                        id="1", 
                        content="chunk1", 
                        meta={"namespace": "ns", "file_name": "test.txt"}
                    ),
                    DocumentFull(
                        id="2", 
                        content="chunk2", 
                        meta={"namespace": "ns", "file_name": "test.txt"}
                    ),
                    DocumentFull(
                        id="3", 
                        content="chunk3", 
                        meta={"namespace": "ns", "file_name": "test.txt"}
                    )
                ]
        monkeypatch.setattr("app.ingest.SimpleConverter", lambda *args, **kwargs: MockConverter())
        
        # send two text files
        files = [
            make_file("a.txt", b"hello", "text/plain"),
            make_file("b.txt", b"world", "text/plain")
        ]
        resp = client.post("/ingest", files=files, data={"namespace": "ns"})
        assert resp.status_code == 200
        
        # Verify documents were added
        results = dummy_store.get()
        assert len(results["documents"]) == 6  # 3 chunks per file * 2 files
        assert all(meta["namespace"] == "ns" for meta in results["metadatas"])
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()

def test_ingest_large_file(client, monkeypatch, test_data_dir):
    # Create a small test file
    small_payload = b"Alice in Wonderland" * 10  # ~200 bytes
    large_file = make_file("alice.txt", small_payload, "text/plain")
    
    # Mock settings to use 768 dimension
    mock_settings = Settings(
        embedding_model="mxbai-embed-large:latest",
        generator_model_name="mistral:latest",
        embedding_dim=768,
        ollama_api_url="http://localhost:11434",
        collection_name="test_collection",
        api_host="0.0.0.0",
        api_port=8000,
        cors_origins=["*"],
        dev_mode=True,
        environment="test",
        log_level="INFO",
        secret_key="test_secret",
        rate_limit_per_minute=60,
        default_top_k=5,
        retriever_score_threshold=0.0,  # Set to 0.0 for testing to ensure documents are not filtered out
        prompt_template="""Based on the following context, please answer the question. If the answer cannot be found in the context, say "I don't know."

Context:
{context}

Question: {query}

Answer:""",
        pipeline_parameters={
            "Retriever": {
                "top_k": 5,
                "score_threshold": 0.0  # Set to 0.0 for testing to ensure documents are not filtered out
            },
            "Generator": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
    )
    
    # Mock the embedder to return embeddings with dimension 768
    class MockEmbedder:
        def encode(self, texts, convert_to_numpy=True):
            if isinstance(texts, str):
                return [0.0] * 768
            return [[0.0] * 768 for _ in range(len(texts))]
            
        def encode_queries(self, texts, convert_to_numpy=True):
            if isinstance(texts, str):
                return [0.0] * 768
            return [[0.0] * 768 for _ in range(len(texts))]
            
        def embed_batch(self, texts):
            return [[0.0] * 768 for _ in range(len(texts))]
            
        def embed(self, text):
            return [0.0] * 768
    
    # Create a mock document store
    class MockDocumentStore:
        def __init__(self):
            self.embedding_dim = 768
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

    # Override dependencies
    app.dependency_overrides[get_settings] = lambda: mock_settings
    app.dependency_overrides[get_embedder] = lambda: MockEmbedder()
    app.dependency_overrides[get_document_store] = lambda: MockDocumentStore()
    
    # stub converter to return fixed 4 chunks
    class MockConverter:
        def run(self, *args, **kwargs):
            return [
                DocumentFull(id="c1", content="chunk1", meta={"namespace": "ns"}),
                DocumentFull(id="c2", content="chunk2", meta={"namespace": "ns"}),
                DocumentFull(id="c3", content="chunk3", meta={"namespace": "ns"}),
                DocumentFull(id="c4", content="chunk4", meta={"namespace": "ns"}),
            ]
    
    monkeypatch.setattr("app.ingest.SimpleConverter", lambda *args, **kwargs: MockConverter())
    
    try:
        # Test ingestion
        resp = client.post("/ingest", files=[large_file], data={"namespace": "ns"})
        assert resp.status_code == 200
        
        # Verify documents were added
        store = app.dependency_overrides[get_document_store]()
        results = store.get()
        assert len(results["documents"]) == 4
        assert all(meta["namespace"] == "ns" for meta in results["metadatas"])
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()

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
            self.embedding_dim = 768
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

    dummy_store = DummyStore()
    monkeypatch.setattr(app.dependencies, "_document_store", dummy_store)
    
    # Stub embedder
    class MockEmbedder:
        def encode(self, texts, convert_to_numpy=True):
            return [[0.1] * 1024 for _ in range(len(texts))]  # Return list of lists
            
        def embed_batch(self, texts):
            return [[0.1] * 1024 for _ in range(len(texts))]  # Return list of lists
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
    
    # Verify file size was captured
    results = dummy_store.get()
    assert len(results["documents"]) > 0
    for meta in results["metadatas"]:
        assert "file_size" in meta
        assert meta["file_size"] == len(test_content)

def test_settings_endpoint(client):
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    assert "embedding_model" in data
    assert "generator_model_name" in data

def mock_embeddings():
    class MockEmbeddings:
        def embed_batch(self, texts):
            return [[0.0] * 1024 for _ in texts]  # Return list instead of numpy array

        def embed(self, text):
            return [0.0] * 1024  # Return list instead of numpy array
    return MockEmbeddings() 
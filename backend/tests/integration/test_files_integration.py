import pytest
from fastapi.testclient import TestClient
from app.main import app
import io
from app.config import Settings
from app.dependencies import get_document_store, get_embedder, get_settings
from app.schema import DocumentFull

def make_file(name, content, media_type):
    return ('files', (name, io.BytesIO(content), media_type))

@pytest.fixture
def client():
    return TestClient(app)

def test_file_size_integration(client, monkeypatch):
    """Integration test for file size handling."""
    # Create a test file with known size
    test_content = b"Hello, world!" * 100  # 1300 bytes
    test_file = make_file("test.txt", test_content, "text/plain")
    
    # Create mock settings with the correct embedding dimension
    mock_settings = Settings(
        embedding_model="mxbai-embed-large:latest",
        generator_model_name="mistral:latest",
        embedding_dim=1024,
        ollama_api_url="http://localhost:11434",
        collection_name="test_collection",
        api_host="0.0.0.0",
        api_port=8000,
        cors_origins=["*"],
        dev_mode=True,
        environment="test",
        log_level="INFO",
        database_url="sqlite:///./test.db",
        secret_key="test_secret",
        rate_limit_per_minute=60,
        default_top_k=5,
        prompt_template="""Based on the following context, please answer the question. If the answer cannot be found in the context, say "I don't know."

Context:
{context}

Question: {query}

Answer:""",
        pipeline_parameters={
            "Retriever": {
                "top_k": 5,
                "score_threshold": 0.7
            },
            "Generator": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
    )
    
    # Create a mock document store with the correct embedding dimension
    class DummyStore:
        def __init__(self):
            self.embedding_dim = 1024
            self.documents = []  # Add documents attribute
            
        def write_documents(self, chunks):
            for chunk in chunks:
                # Ensure each document has the required metadata
                if not chunk.meta:
                    chunk.meta = {}
                if "file_name" not in chunk.meta:
                    chunk.meta["file_name"] = "test.txt"
                if "namespace" not in chunk.meta:
                    chunk.meta["namespace"] = "default"
                if "file_size" not in chunk.meta:
                    chunk.meta["file_size"] = len(test_content)
                self.documents.append(chunk)
            return len(chunks)
    
    # Create a single instance of DummyStore
    dummy_store = DummyStore()
    
    # Create a mock embedder that returns lists instead of numpy arrays
    class MockEmbedder:
        def encode(self, texts, convert_to_numpy=True):
            return [[0.0] * 1024 for _ in range(len(texts))]  # Return list of lists
            
        def encode_queries(self, texts, convert_to_numpy=True):
            return [[0.0] * 1024 for _ in range(len(texts))]  # Return list of lists
            
        def embed_batch(self, texts):
            return [[0.0] * 1024 for _ in range(len(texts))]  # Return list of lists
            
        def embed(self, text):
            return [0.0] * 1024  # Return list
    
    # Create a mock converter that adds file metadata
    class MockConverter:
        def run(self, content, doc_id=None):
            return [
                DocumentFull(
                    id="1",
                    content="test content",
                    meta={
                        "namespace": "default",
                        "file_name": "test.txt",
                        "file_size": len(test_content)
                    }
                )
            ]
    
    # Override dependencies
    app.dependency_overrides[get_document_store] = lambda: dummy_store  # Use the same instance
    app.dependency_overrides[get_embedder] = lambda: MockEmbedder()
    app.dependency_overrides[get_settings] = lambda: mock_settings
    
    try:
        # Mock the SimpleConverter
        monkeypatch.setattr("app.ingest.SimpleConverter", lambda *args, **kwargs: MockConverter())
        
        # Upload the file
        upload_response = client.post("/ingest", files=[test_file])
        assert upload_response.status_code == 200
        
        # Get the list of files
        files_response = client.get("/files")
        assert files_response.status_code == 200
        
        data = files_response.json()
        print("Files response data:", data)  # Add debug logging
        assert "files" in data
        files = data["files"]
        print("Files list:", files)  # Add debug logging
        
        # Find our test file
        test_file_info = next((f for f in files if f["filename"] == "test.txt"), None)
        assert test_file_info is not None
        assert test_file_info["file_size"] == len(test_content)
    finally:
        # Clean up dependency overrides
        app.dependency_overrides = {} 
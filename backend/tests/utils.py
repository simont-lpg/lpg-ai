from app.config import Settings
from app.schema import Document
from unittest.mock import Mock
import numpy as np
from typing import Optional, List
import pytest
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.schema import DocumentFull

def get_test_settings():
    """Get test settings."""
    return Settings(
        embedding_model="all-MiniLM-L6-v2",
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

class MockDocumentStore:
    """Mock document store for testing."""
    def __init__(self, embedding_dim: int = 1024, collection_name: str = "test_documents", embeddings_model=None):
        self.documents = []
        self.embeddings = []
        self.embedding_dim = embedding_dim
        self._collection_name = collection_name
        self.model = embeddings_model
    
    @property
    def collection_name(self) -> str:
        """Get the collection name."""
        return self._collection_name
    
    def delete_documents(self, document_ids: Optional[List[str]] = None):
        """Delete documents from the store."""
        if document_ids is None:
            self.documents = []
            self.embeddings = []
            return
        
        indices_to_delete = []
        for i, doc in enumerate(self.documents):
            if doc.id in document_ids:
                indices_to_delete.append(i)
        
        for i in sorted(indices_to_delete, reverse=True):
            del self.documents[i]
            del self.embeddings[i]
    
    def write_documents(self, documents: List[Document]):
        """Write documents to store."""
        for doc in documents:
            if isinstance(doc, dict):
                doc = Document(**doc)
            if not doc.id:
                doc.id = str(len(self.documents))
            # Store the document as is
            self.documents.append(doc)
            # Mock embedding as zeros array
            embedding = np.zeros(self.embedding_dim).tolist()
            self.embeddings.append(np.array(embedding))
    
    def get_all_documents(self, filters: Optional[dict] = None) -> List[Document]:
        """Get all documents, optionally filtered."""
        if not filters:
            return self.documents
        
        filtered_docs = []
        for doc in self.documents:
            match = True
            for key, value in filters.items():
                if key not in doc.meta or doc.meta[key] != value:
                    match = False
                    break
            if match:
                filtered_docs.append(doc)
        return filtered_docs
    
    def query_by_embedding(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Document]:
        """Mock query by embedding - returns first top_k documents."""
        if not self.documents:
            return []
        
        result_docs = self.documents[:top_k]
        for doc in result_docs:
            doc.score = 1.0  # Mock perfect similarity score
        return result_docs 

@pytest.fixture
def mock_embeddings(settings):
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def encode(self, text):
            return np.zeros(settings.embedding_dim)  # Return zero vector
        def embed_batch(self, texts):
            return [np.zeros(settings.embedding_dim) for _ in texts]  # Return zero vectors
    return MockEmbeddings()

@pytest.fixture
def mock_store(mock_embeddings, settings):
    """Create a mock document store for testing."""
    return InMemoryDocumentStore(
        embedding_dim=settings.embedding_dim,
        collection_name=settings.collection_name,
        embeddings_model=mock_embeddings
    )

@pytest.fixture
def test_documents(settings):
    """Create test documents."""
    return [
        DocumentFull(
            id="1",
            content="Test content 1",
            meta={"namespace": "test1"},
            embedding=[0.1] * settings.embedding_dim
        ),
        DocumentFull(
            id="2",
            content="Test content 2",
            meta={"namespace": "test2"},
            embedding=[0.1] * settings.embedding_dim
        )
    ]

def test_mock_embeddings(mock_embeddings, settings):
    """Test mock embeddings functionality."""
    embedding = mock_embeddings.encode("test")
    assert len(embedding) == settings.embedding_dim
    assert all(v == 0 for v in embedding)
    
    embeddings = mock_embeddings.embed_batch(["test1", "test2"])
    assert len(embeddings) == 2
    assert all(len(emb) == settings.embedding_dim for emb in embeddings)
    assert all(all(v == 0 for v in emb) for emb in embeddings)

def test_mock_store(mock_store, test_documents):
    """Test mock store functionality."""
    # Test adding documents
    mock_store.add_documents(test_documents)
    assert len(mock_store.documents) == 2
    
    # Test retrieving documents
    documents = mock_store.get_all_documents()
    assert len(documents) == 2
    assert documents[0].id == "1"
    assert documents[1].id == "2"
    
    # Test filtering by namespace
    filtered = mock_store.get_all_documents(filters={"namespace": "test1"})
    assert len(filtered) == 1
    assert filtered[0].namespace == "test1" 
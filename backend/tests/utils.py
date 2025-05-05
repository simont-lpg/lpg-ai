from app.config import Settings
from app.schema import DocumentFull
from unittest.mock import Mock
import numpy as np
from typing import Optional, List
import pytest
from backend.app.vectorstore import InMemoryDocumentStore

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
        secret_key="test_secret",
        rate_limit_per_minute=60,
        default_top_k=5,
        retriever_score_threshold=0.0,
        prompt_template="""Based on the following context, please answer the question. If the answer cannot be found in the context, say "I don't know."

Context:
{context}

Question: {query}

Answer:""",
        pipeline_parameters={
            "Retriever": {
                "top_k": 5,
                "score_threshold": 0.0
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
    
    def delete(self, ids: Optional[List[str]] = None):
        """Delete documents from the store."""
        if ids is None:
            self.documents = []
            self.embeddings = []
            return
        
        indices_to_delete = []
        for i, doc in enumerate(self.documents):
            if doc.id in ids:
                indices_to_delete.append(i)
        
        for i in sorted(indices_to_delete, reverse=True):
            del self.documents[i]
            del self.embeddings[i]
    
    def add(self, documents: List[str], metadatas: List[dict], ids: List[str], embeddings: Optional[List[List[float]]] = None):
        """Add documents to store using Chroma's interface."""
        if embeddings is None:
            embeddings = [np.zeros(self.embedding_dim).tolist() for _ in documents]
            
        for doc, meta, doc_id, embedding in zip(documents, metadatas, ids, embeddings):
            # Store the document
            self.documents.append(DocumentFull(
                id=doc_id,
                content=doc,
                meta=meta
            ))
            # Store the embedding
            self.embeddings.append(np.array(embedding))
    
    def get(self, ids: Optional[List[str]] = None, where: Optional[dict] = None) -> dict:
        """Get documents using Chroma's interface."""
        if not ids and not where:
            return {
                "ids": [doc.id for doc in self.documents],
                "documents": [doc.content for doc in self.documents],
                "metadatas": [doc.meta for doc in self.documents]
            }
        
        filtered_docs = []
        for doc in self.documents:
            if ids and doc.id not in ids:
                continue
            if where:
                match = True
                for key, value in where.items():
                    if key not in doc.meta or doc.meta[key] != value:
                        match = False
                        break
                if not match:
                    continue
            filtered_docs.append(doc)
        
        return {
            "ids": [doc.id for doc in filtered_docs],
            "documents": [doc.content for doc in filtered_docs],
            "metadatas": [doc.meta for doc in filtered_docs]
        }
    
    def query(self, query_embeddings: List[List[float]], n_results: int = 5, where: Optional[dict] = None) -> dict:
        """Mock query by embedding - returns first n_results documents."""
        if not self.documents:
            return {
                "ids": [],
                "documents": [],
                "metadatas": [],
                "distances": []
            }
        
        filtered_docs = []
        for doc in self.documents:
            if where:
                match = True
                for key, value in where.items():
                    if key not in doc.meta or doc.meta[key] != value:
                        match = False
                        break
                if not match:
                    continue
            filtered_docs.append(doc)
        
        result_docs = filtered_docs[:n_results]
        return {
            "ids": [doc.id for doc in result_docs],
            "documents": [doc.content for doc in result_docs],
            "metadatas": [doc.meta for doc in result_docs],
            "distances": [0.0] * len(result_docs)  # Mock perfect similarity score
        }

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
    return MockDocumentStore(
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
    mock_store.add(
        documents=[doc.content for doc in test_documents],
        metadatas=[doc.meta for doc in test_documents],
        ids=[doc.id for doc in test_documents]
    )
    assert len(mock_store.documents) == 2
    
    # Test retrieving documents
    documents = mock_store.get()
    assert len(documents["documents"]) == 2
    assert documents["ids"][0] == "1"
    assert documents["ids"][1] == "2"
    
    # Test filtering by namespace
    filtered = mock_store.get(where={"namespace": "test1"})
    assert len(filtered["documents"]) == 1
    assert filtered["metadatas"][0]["namespace"] == "test1" 
import pytest
from backend.app.pipeline import Pipeline, Retriever, build_pipeline
from backend.app.vectorstore import InMemoryDocumentStore
from backend.app.schema import DocumentFull
import numpy as np
from unittest.mock import MagicMock

@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    class MockEmbeddings:
        def encode(self, text):
            return np.zeros(1024)  # Return zero vector
        def embed_batch(self, texts):
            return [np.zeros(1024) for _ in texts]  # Return zero vectors
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
def test_documents():
    return [
        Document(
            id=f"test-doc-{i}",
            content=f"test content {i}",
            meta={"source": f"test-source-{i}"}
        ) for i in range(3)
    ]

def test_pipeline_initialization(settings, mock_store):
    """Test pipeline initialization."""
    pipeline, retriever = build_pipeline(
        settings=settings,
        document_store=mock_store,
        dev=True
    )
    assert isinstance(pipeline, Pipeline)
    assert isinstance(retriever, Retriever)

def test_pipeline_query(settings, mock_store, monkeypatch):
    """Test pipeline query functionality."""
    # Mock the embedder
    class MockEmbedder:
        def embed_batch(self, texts):
            return [[0.0] * settings.embedding_dim for _ in texts]

        def embed(self, text):
            return [0.0] * settings.embedding_dim

    monkeypatch.setattr("app.dependencies.get_embedder", lambda: MockEmbedder())

    # Add test documents to store
    docs = [
        DocumentFull(content="Test document 1", id="1", meta={"namespace": "test"}),
        DocumentFull(content="Test document 2", id="2", meta={"namespace": "test"})
    ]
    mock_store.write_documents(docs)

    # Create pipeline
    pipeline, _ = build_pipeline(
        settings=settings,
        document_store=mock_store,
        dev=True
    )

    # Test query
    result = pipeline.run("test query")
    expected_prompt = settings.prompt_template.format(
        context="Test document 2\n\nTest document 1",
        query="test query"
    )
    assert result["answers"][0] == f"[DEV] {expected_prompt}"
    assert len(result["documents"]) == 2

def test_retriever_initialization(settings, mock_store):
    """Test retriever initialization."""
    retriever = Retriever(document_store=mock_store)
    retriever.initialize(settings)
    assert retriever.model is not None 
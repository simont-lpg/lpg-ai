import pytest
from app.schema import Document
from app.pipeline import build_pipeline
from pydantic import ConfigDict


# Configure Pydantic to allow arbitrary types
Document.model_config = ConfigDict(arbitrary_types_allowed=True)


@pytest.fixture
def sample_documents():
    """Fixture providing sample documents for testing."""
    return [
        Document(
            content="The quick brown fox jumps over the lazy dog",
            meta={"source": "test1"}
        ),
        Document(
            content="Pack my box with five dozen liquor jugs",
            meta={"source": "test2"}
        )
    ]


def test_pipeline_retrieval(sample_documents):
    """Test that the pipeline can store and retrieve documents."""
    pipeline, doc_store = build_pipeline(dev=True)
    
    # Write documents to store
    doc_store.write_documents(sample_documents)
    
    # Query the pipeline
    result = pipeline.run(
        query="fox",
        params={"Retriever": {"top_k": 10}}
    )
    documents = result["documents"]
    
    # Verify retrieval
    assert len(documents) > 0
    assert any("fox" in doc.content.lower() for doc in documents) 
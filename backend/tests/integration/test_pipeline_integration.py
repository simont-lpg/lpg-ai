import pytest
from app.pipeline import build_pipeline
from app.schema import Document
from app.vectorstore import get_vectorstore
from app.config import Settings

@pytest.mark.integration
def test_pipeline_with_chroma():
    # Initialize components
    settings = Settings()
    vectorstore = get_vectorstore(settings)
    pipeline, _ = build_pipeline(dev=False)
    
    # Create and write sample documents
    docs = [
        Document(content="Sample document 1", id="doc1"),
        Document(content="Sample document 2", id="doc2")
    ]
    vectorstore.write_documents(docs)
    
    # Test pipeline query
    result = pipeline.run(query="Sample")
    assert isinstance(result, dict)
    assert "documents" in result
    assert len(result["documents"]) > 0
    assert all(isinstance(doc, Document) for doc in result["documents"])
    
    # Clean up
    vectorstore.delete_documents(["doc1", "doc2"]) 
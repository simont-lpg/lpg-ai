import pytest
from backend.app.schema import DocumentMetadata, DocumentFull, Query, Response

def test_document_metadata_model():
    """Test DocumentMetadata model."""
    doc = DocumentMetadata(content="test", id="123", meta={"key": "value"})
    assert doc.content == "test"
    assert doc.id == "123"
    assert doc.meta == {"key": "value"}
    
    # Test to_dict method
    doc_dict = doc.to_dict()
    assert doc_dict["content"] == "test"
    assert doc_dict["id"] == "123"
    assert doc_dict["meta"] == {"key": "value"}

def test_document_full_model():
    """Test DocumentFull model."""
    doc = DocumentFull(
        content="test",
        id="123",
        meta={"key": "value"},
        embedding=[0.1, 0.2, 0.3],
        score=0.95
    )
    assert doc.content == "test"
    assert doc.id == "123"
    assert doc.meta == {"key": "value"}
    assert doc.embedding == [0.1, 0.2, 0.3]
    assert doc.score == 0.95
    
    # Test to_dict method
    doc_dict = doc.to_dict()
    assert doc_dict["content"] == "test"
    assert doc_dict["id"] == "123"
    assert doc_dict["meta"] == {"key": "value"}
    assert doc_dict["embedding"] == [0.1, 0.2, 0.3]
    assert doc_dict["score"] == 0.95

def test_query_model():
    """Test Query model."""
    query = Query(text="test query", top_k=10)
    assert query.text == "test query"
    assert query.top_k == 10

def test_response_model():
    """Test Response model."""
    docs = [
        {
            "content": "test1",
            "id": "1",
            "meta": {"namespace": "default"}
        },
        {
            "content": "test2",
            "id": "2",
            "meta": {"namespace": "default"}
        }
    ]
    response = Response(answers=["answer1"], documents=docs)
    assert len(response.documents) == 2
    assert response.documents[0]["content"] == "test1"
    assert response.documents[1]["content"] == "test2" 
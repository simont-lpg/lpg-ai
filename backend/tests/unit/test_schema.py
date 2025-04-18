import pytest
from backend.app.schema import Document, Query, Response

def test_document_model():
    doc = Document(content="Test content", meta={"source": "test"})
    assert doc.content == "Test content"
    assert doc.meta == {"source": "test"}
    assert doc.id is None

def test_query_model():
    query = Query(query="test query", top_k=3)
    assert query.text == "test query"
    assert query.top_k == 3

def test_query_validation():
    with pytest.raises(ValueError):
        Query(query="")

def test_response_model():
    response = Response(
        answers=["answer1", "answer2"],
        documents=[{"content": "doc1"}, {"content": "doc2"}]
    )
    assert len(response.answers) == 2
    assert len(response.documents) == 2 
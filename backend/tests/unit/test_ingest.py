import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import UploadFile
from backend.app.ingest import ingest_documents, SimpleConverter
from backend.app.schema import Document
import tempfile
import os
import io

@pytest.fixture
def test_file_content():
    """Create a temporary test file."""
    content = "This is a test document.\nIt has multiple lines.\nAnd some structure."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_file():
    """Create a mock file for testing."""
    mock = MagicMock(spec=UploadFile)
    mock.filename = "test.txt"
    mock.read = AsyncMock(return_value=b"This is a test document.")
    return mock

@pytest.fixture
def mock_document_store():
    """Create a mock document store."""
    mock = MagicMock()
    mock.write_documents = MagicMock()
    return mock

@pytest.fixture
def mock_embedder():
    """Create a mock embedder."""
    mock = MagicMock()
    mock.embed_batch.return_value = [[0.1] * 384]
    return mock

@pytest.mark.asyncio
async def test_ingest_documents(mock_file, mock_document_store, mock_embedder):
    """Test successful document ingestion."""
    result = await ingest_documents(
        files=[mock_file],
        namespace="test",
        document_store=mock_document_store,
        embedder=mock_embedder
    )
    
    assert result["status"] == "success"
    assert result["namespace"] == "test"
    assert result["files_ingested"] == 1
    assert result["total_chunks"] > 0
    mock_document_store.write_documents.assert_called()

@pytest.mark.asyncio
async def test_ingest_documents_unsupported_file(mock_document_store, mock_embedder):
    """Test ingestion with unsupported file type."""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.unsupported"
    mock_file.read = AsyncMock(return_value=b"content")
    
    result = await ingest_documents(
        files=[mock_file],
        document_store=mock_document_store,
        embedder=mock_embedder
    )
    
    assert result["status"] == "success"
    assert result["files_ingested"] == 0
    assert result["total_chunks"] == 0
    mock_document_store.write_documents.assert_not_called()

@pytest.mark.asyncio
async def test_ingest_documents_error(mock_file, mock_document_store, mock_embedder):
    """Test ingestion error handling."""
    mock_embedder.embed_batch.side_effect = Exception("Embedding failed")
    
    with pytest.raises(Exception) as exc_info:
        await ingest_documents(
            files=[mock_file],
            document_store=mock_document_store,
            embedder=mock_embedder
        )
    assert "Failed to ingest file" in str(exc_info.value)

def test_simple_converter():
    """Test the SimpleConverter with a real file."""
    converter = SimpleConverter()
    content = b"This is a test document.\nIt has multiple lines.\nAnd some structure."
    
    documents = converter.run(content)
    assert len(documents) > 0
    assert all(isinstance(doc, Document) for doc in documents)
    assert all(doc.content for doc in documents)

def test_simple_converter_error():
    """Test SimpleConverter error handling."""
    converter = SimpleConverter()
    with pytest.raises(Exception) as exc_info:
        converter.run(b"")
    assert "Empty file content provided" in str(exc_info.value) 
from pathlib import Path
from typing import Optional

from chroma_haystack import ChromaDocumentStore
from haystack.document_stores.types import DocumentStore

from app.config import settings


def init_document_store() -> DocumentStore:
    """Initialize and return a ChromaDocumentStore instance.
    
    Returns:
        DocumentStore: An initialized ChromaDocumentStore instance.
    """
    # Ensure the persist directory exists
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    
    return ChromaDocumentStore(
        persist_directory=str(settings.chroma_persist_dir),
        embedding_dim=settings.embedding_dim,
        similarity="cosine",
        return_embedding=True,
    )


# Create a global document store instance
document_store = init_document_store() 
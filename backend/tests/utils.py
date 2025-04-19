from app.config import Settings
from app.schema import Document
from unittest.mock import Mock
import numpy as np
from typing import Optional, List

def get_test_settings():
    """Get test settings."""
    return Settings(
        embedding_model="all-MiniLM-L6-v2",
        embedding_model_name="all-MiniLM-L6-v2",
        embedding_dim=384,
        ollama_api_url="http://127.0.0.1:11434",
        collection_name="test_documents"
    )

class MockDocumentStore:
    """Mock document store for testing."""
    def __init__(self, embedding_dim: int = 384, collection_name: str = "test_documents", embeddings_model=None):
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
from typing import List, Optional
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from .config import Settings
from .schema import Document

class InMemoryDocumentStore:
    """Simple in-memory document store with vector similarity search."""
    
    def __init__(self, embedding_dim: int = 384, collection_name: str = "documents"):
        self.documents: List[Document] = []
        self.embeddings: List[np.ndarray] = []
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self._collection = type('Collection', (), {'name': collection_name})()
    
    def write_documents(self, documents: List[Document]):
        """Write documents to the store."""
        for doc in documents:
            if not doc.id:
                doc.id = str(len(self.documents))
            self.documents.append(doc)
            self.embeddings.append(self.model.encode(doc.content))
    
    def delete_documents(self, document_ids: List[str]):
        """Delete documents from the store."""
        indices_to_delete = []
        for i, doc in enumerate(self.documents):
            if doc.id in document_ids:
                indices_to_delete.append(i)
        
        for i in sorted(indices_to_delete, reverse=True):
            del self.documents[i]
            del self.embeddings[i]
    
    def query_by_embedding(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Document]:
        """Find most similar documents by embedding."""
        if not self.documents:
            return []
        
        # Convert embeddings to numpy array for efficient computation
        embeddings_array = np.array(self.embeddings)
        
        # Compute cosine similarity
        similarities = np.dot(embeddings_array, query_embedding) / (
            np.linalg.norm(embeddings_array, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [self.documents[i] for i in top_indices]

def get_vectorstore(settings: Settings) -> InMemoryDocumentStore:
    """Get or create a vector store."""
    if not settings.chroma_db_path:
        raise ValueError("Chroma database path must be set")
    
    if not os.path.exists(settings.chroma_db_path):
        raise ValueError("Chroma database path does not exist")
    
    return InMemoryDocumentStore(
        embedding_dim=384,  # Dimension for all-MiniLM-L6-v2
        collection_name=settings.chroma_collection_name
    ) 
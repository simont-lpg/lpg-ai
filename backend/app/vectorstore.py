from typing import List, Optional, Dict, Any
import numpy as np
import os
import requests
from sentence_transformers import SentenceTransformer
from .config import Settings
from .schema import DocumentFull

class OllamaEmbeddings:
    """Embeddings using Ollama API."""
    
    def __init__(self, api_url: str, model_name: str, embedding_dim: int):
        self.api_url = api_url
        self.model_name = model_name
        self.embedding_dim = embedding_dim
    
    def embed(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        response = requests.post(
            f"{self.api_url}/api/embeddings",
            json={"model": self.model_name, "prompt": text}
        )
        if response.status_code != 200:
            raise Exception(f"Failed to get embedding: {response.text}")
        return response.json()["embedding"][:self.embedding_dim]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts."""
        return [self.embed(text) for text in texts]

class InMemoryDocumentStore:
    """Simple in-memory document store with vector similarity search."""
    
    def __init__(self, embedding_dim: int = 384, collection_name: str = "documents", embeddings_model=None):
        self.documents: List[DocumentFull] = []
        self.embeddings: List[np.ndarray] = []
        self.embedding_dim = embedding_dim
        self._collection_name = collection_name
        if embeddings_model is None:
            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        else:
            self.model = embeddings_model
    
    @property
    def collection_name(self) -> str:
        """Get the collection name."""
        return self._collection_name
    
    def write_documents(self, documents: List[DocumentFull]):
        """Write documents to the store."""
        for doc in documents:
            if not doc.id:
                doc.id = str(len(self.documents))
            self.documents.append(doc)
            try:
                if isinstance(self.model, OllamaEmbeddings):
                    embeddings = self.model.embed_batch([doc.content])[0]
                else:
                    embeddings = self.model.encode(doc.content)
                # Ensure embedding has the correct dimension
                embeddings = np.array(embeddings[:self.embedding_dim])
                self.embeddings.append(embeddings)
            except Exception as e:
                raise Exception(f"Failed to generate embeddings for document: {str(e)}")
    
    def delete_documents(self, document_ids: Optional[List[str]] = None, filters: Optional[dict] = None) -> int:
        """Delete documents from the store.
        
        Args:
            document_ids: Optional list of document IDs to delete
            filters: Optional dictionary of metadata filters
            
        Returns:
            Number of documents deleted
        """
        if document_ids is None and filters is None:
            # Clear all documents
            count = len(self.documents)
            self.documents = []
            self.embeddings = []
            return count
        
        indices_to_delete = []
        
        if document_ids is not None:
            # Delete by document IDs
            for i, doc in enumerate(self.documents):
                if doc.id in document_ids:
                    indices_to_delete.append(i)
        else:
            # Delete by filters
            for i, doc in enumerate(self.documents):
                match = True
                for key, value in filters.items():
                    if key not in doc.meta or doc.meta[key] != value:
                        match = False
                        break
                if match:
                    indices_to_delete.append(i)
        
        # Delete in reverse order to maintain indices
        for i in sorted(indices_to_delete, reverse=True):
            del self.documents[i]
            del self.embeddings[i]
        
        return len(indices_to_delete)
    
    def get_all_documents(self, filters: Optional[dict] = None) -> List[DocumentFull]:
        """Get all documents, optionally filtered by metadata."""
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
    
    def query_by_embedding(self, query_embedding: np.ndarray, top_k: int = 5) -> List[DocumentFull]:
        """Query documents by embedding similarity."""
        if not self.documents:
            return []
        
        # Ensure query embedding has the correct dimension
        query_embedding = np.array(query_embedding[:self.embedding_dim])
        
        # Calculate cosine similarity
        similarities = []
        for embedding in self.embeddings:
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities.append(similarity)
        
        # Get top k documents
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        result_docs = []
        for i in top_indices:
            doc = self.documents[i]
            doc.score = float(similarities[i])  # Convert numpy float to Python float
            result_docs.append(doc)
        return result_docs

def get_vectorstore(settings: Settings) -> InMemoryDocumentStore:
    """Get a vector store instance based on settings."""
    try:
        if settings.embedding_model_name == "mxbai-embed-large:latest":
            model = OllamaEmbeddings(
                api_url=str(settings.ollama_api_url),
                model_name=settings.embedding_model_name,
                embedding_dim=settings.embedding_dim
            )
        else:
            model = SentenceTransformer(settings.embedding_model)
        
        return InMemoryDocumentStore(
            embedding_dim=settings.embedding_dim,
            collection_name=settings.collection_name,
            embeddings_model=model
        )
    except Exception as e:
        raise Exception(f"Failed to initialize vectorstore: {str(e)}") 
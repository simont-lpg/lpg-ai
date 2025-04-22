from typing import List, Optional, Dict, Any
import numpy as np
import os
import requests
from sentence_transformers import SentenceTransformer
from .config import Settings
from .schema import DocumentFull
import logging

class DummyEmbeddings:
    """Dummy embeddings for development."""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
    
    def encode(self, text: str) -> List[float]:
        """Return dummy embeddings."""
        return [0.1] * self.embedding_dim
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Return dummy embeddings for a batch of texts."""
        return [[0.1] * self.embedding_dim for _ in texts]

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
                if doc.embedding is not None:
                    embedding = np.array(doc.embedding)
                else:
                    if isinstance(self.model, OllamaEmbeddings):
                        embedding = self.model.embed_batch([doc.content])[0]
                    else:
                        embedding = self.model.encode(doc.content)
                    embedding = np.array(embedding)
                    doc.embedding = embedding.tolist()
                
                if len(embedding) > self.embedding_dim:
                    embedding = embedding[:self.embedding_dim]
                elif len(embedding) < self.embedding_dim:
                    embedding = np.pad(embedding, (0, self.embedding_dim - len(embedding)))
                
                self.embeddings.append(embedding)
            except Exception as e:
                raise Exception(f"Failed to process embeddings for document: {str(e)}")
    
    def delete_documents(self, document_ids: Optional[List[str]] = None, filters: Optional[dict] = None) -> int:
        """Delete documents from the store."""
        indices_to_delete = []
        
        if document_ids is not None:
            for i, doc in enumerate(self.documents):
                if doc.id in document_ids:
                    indices_to_delete.append(i)
        elif filters is not None:
            for i, doc in enumerate(self.documents):
                match = True
                for key, value in filters.items():
                    if key not in doc.meta or doc.meta[key] != value:
                        match = False
                        break
                if match:
                    indices_to_delete.append(i)
        
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
    
    def query_by_embedding(self, query_embedding: np.ndarray, top_k: int = 5, filters: Optional[dict] = None) -> List[DocumentFull]:
        """Query documents by embedding similarity."""
        if not self.documents:
            return []
        
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        
        query_embedding = np.array(query_embedding[:self.embedding_dim])
        
        # Filter documents by namespace if specified
        filtered_docs = self.documents
        filtered_embeddings = self.embeddings
        
        if filters and "namespace" in filters:
            filtered_docs = []
            filtered_embeddings = []
            for doc, embedding in zip(self.documents, self.embeddings):
                if doc.meta.get("namespace") == filters["namespace"]:
                    filtered_docs.append(doc)
                    filtered_embeddings.append(embedding)
        
        if not filtered_docs:
            return []
        
        similarities = []
        for i, embedding in enumerate(filtered_embeddings):
            query_embedding = np.asarray(query_embedding)
            doc_embedding = np.asarray(embedding)
            
            query_norm = np.linalg.norm(query_embedding)
            doc_norm = np.linalg.norm(doc_embedding)
            
            if query_norm == 0 or doc_norm == 0:
                similarity = 0
            else:
                similarity = np.dot(query_embedding, doc_embedding) / (query_norm * doc_norm)
            
            similarities.append(similarity)
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        result_docs = []
        for i in top_indices:
            doc = filtered_docs[i]
            doc.score = float(similarities[i])
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
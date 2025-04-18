from typing import List, Optional
import numpy as np
import os
import requests
from sentence_transformers import SentenceTransformer
from .config import Settings
from .schema import Document

class OllamaEmbeddings:
    """Ollama-based embeddings implementation."""
    
    def __init__(self, api_url: str, model_name: str, embedding_dim: int = 384):
        self.url = api_url.rstrip("/") + "/api/embed"
        self.model = model_name
        self.embedding_dim = embedding_dim
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts using Ollama."""
        try:
            resp = requests.post(
                self.url,
                json={"model": self.model, "input": texts}
            )
            resp.raise_for_status()
            embeddings = resp.json()["embeddings"]
            # Ensure embeddings have the correct dimension
            return [np.array(emb[:self.embedding_dim]) for emb in embeddings]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get embeddings from Ollama: {str(e)}")

class InMemoryDocumentStore:
    """Simple in-memory document store with vector similarity search."""
    
    def __init__(self, embedding_dim: int = 384, collection_name: str = "documents", embeddings_model=None):
        self.documents: List[Document] = []
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
    
    def write_documents(self, documents: List[Document]):
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
    
    def delete_documents(self, document_ids: List[str]):
        """Delete documents from the store."""
        indices_to_delete = []
        for i, doc in enumerate(self.documents):
            if doc.id in document_ids:
                indices_to_delete.append(i)
        
        # Delete in reverse order to maintain indices
        for i in sorted(indices_to_delete, reverse=True):
            del self.documents[i]
            del self.embeddings[i]
    
    def query_by_embedding(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Document]:
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
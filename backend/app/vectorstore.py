from typing import List, Optional, Dict, Any
import numpy as np
from pydantic import BaseModel
from .schema import DocumentFull
from sentence_transformers import SentenceTransformer
import logging
from .config import Settings

logger = logging.getLogger(__name__)

class OllamaEmbeddings:
    """Wrapper for Ollama embeddings API."""
    
    def __init__(self, api_url: str, model_name: str, embedding_dim: int):
        self.api_url = api_url
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        
    def embed(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        import requests
        try:
            response = requests.post(
                f"{self.api_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Error getting embedding from Ollama: {str(e)}")
            raise
            
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts."""
        return [self.embed(text) for text in texts]

class InMemoryDocumentStore:
    """In-memory document store with vector search capabilities."""
    
    def __init__(
        self,
        embedding_dim: int,
        collection_name: str,
        embeddings_model: Any
    ):
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be greater than 0")
        self.embedding_dim = embedding_dim
        self.collection_name = collection_name
        self.embeddings_model = embeddings_model
        self.documents: List[DocumentFull] = []
        self.embeddings: np.ndarray = np.empty((0, embedding_dim))
        
    def add_documents(self, documents: List[DocumentFull]) -> None:
        """Add documents to the store."""
        if not documents:
            return
            
        # Get embeddings for new documents if not provided
        texts = []
        new_embeddings = []
        for doc in documents:
            if doc.embedding is not None:
                new_embeddings.append(doc.embedding)
            else:
                texts.append(doc.content)
        
        # Generate embeddings for documents without them
        if texts:
            generated_embeddings = self.embeddings_model.embed_batch(texts)
            if isinstance(generated_embeddings, list):
                generated_embeddings = np.array(generated_embeddings)
            new_embeddings.extend(generated_embeddings)
        
        # Ensure embeddings have the correct dimension and convert to numpy array
        if isinstance(new_embeddings, list):
            new_embeddings = np.array(new_embeddings)
        if new_embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {new_embeddings.shape[1]}")
        
        # Add to store
        self.documents.extend(documents)
        self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
    def write_documents(self, documents: List[DocumentFull]) -> None:
        """Write documents to the store (alias for add_documents)."""
        self.add_documents(documents)
        
    def get_all_documents(self, filters: Optional[Dict[str, Any]] = None) -> List[DocumentFull]:
        """Get all documents, optionally filtered."""
        if not filters:
            # Return documents with their embeddings
            for i, doc in enumerate(self.documents):
                doc.embedding = self.embeddings[i].tolist()
            return self.documents
            
        filtered_docs = []
        filtered_indices = []
        for i, doc in enumerate(self.documents):
            match = True
            for key, value in filters.items():
                if key not in doc.meta or doc.meta[key] != value:
                    match = False
                    break
            if match:
                filtered_docs.append(doc)
                filtered_indices.append(i)
        
        # Attach embeddings to filtered documents
        for i, doc in enumerate(filtered_docs):
            doc.embedding = self.embeddings[filtered_indices[i]].tolist()
        return filtered_docs
        
    def query_by_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        settings: Optional[Settings] = None
    ) -> List[DocumentFull]:
        """Query documents by embedding."""
        if not self.documents:
            return []
            
        # Convert query embedding to numpy array if needed
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
            
        # Apply filters first if specified
        if filters:
            filtered_docs = []
            filtered_embeddings = []
            for doc, emb in zip(self.documents, self.embeddings):
                match = True
                for key, value in filters.items():
                    if key not in doc.meta or doc.meta[key] != value:
                        match = False
                        break
                if match:
                    filtered_docs.append(doc)
                    filtered_embeddings.append(emb)
            if not filtered_docs:
                return []
            docs = filtered_docs
            embeddings = np.stack(filtered_embeddings)
        else:
            docs = self.documents
            embeddings = self.embeddings
        
        # Normalize embeddings for cosine similarity
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm
        
        embeddings_norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings_norm[embeddings_norm == 0] = 1  # Avoid division by zero
        embeddings = embeddings / embeddings_norm
        
        # Calculate similarities
        similarities = np.dot(embeddings, query_embedding)
        
        # Get top k results
        top_k = min(top_k, len(docs))
        top_k_indices = np.argsort(similarities)[-top_k:][::-1]
        results = [docs[i] for i in top_k_indices]
        
        # Apply score threshold from settings if available
        if settings is not None and settings.retriever_score_threshold is not None:
            score_threshold = settings.retriever_score_threshold
            results = [
                doc for i, doc in enumerate(results)
                if similarities[top_k_indices[i]] >= score_threshold
            ]
            
            # Add similarity scores to results
            for i, doc in enumerate(results):
                doc.score = float(similarities[top_k_indices[i]])
        
        return results
        
    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents by their IDs."""
        if not document_ids:
            return
            
        # Find indices of documents to delete
        indices_to_delete = [
            i for i, doc in enumerate(self.documents)
            if doc.id in document_ids
        ]
        
        # Remove documents and their embeddings
        for i in sorted(indices_to_delete, reverse=True):
            del self.documents[i]
            self.embeddings = np.delete(self.embeddings, i, axis=0)
            
    def delete_documents_by_file_name(self, file_name: str) -> int:
        """Delete documents by file name.
        
        Args:
            file_name: The name of the file to delete documents for.
            
        Returns:
            int: The number of documents deleted.
        """
        # Find documents with matching file name
        indices_to_delete = [
            i for i, doc in enumerate(self.documents)
            if doc.meta.get("file_name") == file_name
        ]
        
        # Remove documents and their embeddings
        for i in sorted(indices_to_delete, reverse=True):
            if i < len(self.documents):
                del self.documents[i]
                if i < len(self.embeddings):
                    self.embeddings = np.delete(self.embeddings, i, axis=0)
            
        return len(indices_to_delete)
        
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        score_threshold: Optional[float] = None,
        settings: Optional[Settings] = None
    ) -> List[DocumentFull]:
        """Search for similar documents."""
        if not self.documents:
            return []
            
        # Get query embedding
        query_embedding = self.embeddings_model.embed_batch([query])[0]
        
        # Ensure query embedding has the correct dimension
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        if query_embedding.shape[0] != self.embedding_dim:
            raise ValueError(f"Query embedding dimension mismatch: expected {self.embedding_dim}, got {query_embedding.shape[0]}")
        
        # Calculate similarities
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Get top k results
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        results = [self.documents[i] for i in top_k_indices]
        
        # Apply score threshold if specified or from settings
        if score_threshold is None and settings is not None:
            score_threshold = settings.retriever_score_threshold
            
        if score_threshold is not None:
            results = [
                doc for i, doc in enumerate(results)
                if similarities[top_k_indices[i]] >= score_threshold
            ]
            
        return results

def get_vectorstore(settings: Settings) -> InMemoryDocumentStore:
    """Get vectorstore instance based on settings."""
    try:
        from .dependencies import get_embedder
        model = get_embedder(settings)
        return InMemoryDocumentStore(
            embedding_dim=settings.embedding_dim,
            collection_name=settings.collection_name,
            embeddings_model=model
        )
    except Exception as e:
        logger.error(f"Failed to initialize vectorstore: {str(e)}", exc_info=True)
        raise Exception(f"Failed to initialize vectorstore: {str(e)}") 
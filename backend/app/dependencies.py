from typing import Generator, List, Any
from fastapi import Depends
from .config import Settings, get_settings
from .vectorstore import get_vectorstore, OllamaEmbeddings, InMemoryDocumentStore
from .schema import DocumentFull
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache
import logging
from chromadb import Client, Settings as ChromaSettings

logger = logging.getLogger(__name__)

# Global document store instance
_document_store = None
_embedder = None

class Embedder:
    """Wrapper class for embedding models."""
    
    def __init__(self, model):
        self.model = model
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts."""
        if isinstance(self.model, SentenceTransformer):
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        elif isinstance(self.model, OllamaEmbeddings):
            return [self.model.embed(text) for text in texts]
        else:
            raise ValueError(f"Unsupported model type: {type(self.model)}")

@lru_cache()
def get_embedder(settings: Settings = Depends(get_settings)) -> Any:
    """Get embeddings model."""
    global _embedder
    if _embedder is None:
        logger.info(f"Initializing embedder with model: {settings.embedding_model}")
        if settings.dev_mode:
            # Use mock embeddings in dev mode
            class MockEmbeddings:
                def encode(self, text):
                    return np.ones(settings.embedding_dim)  # Return ones vector for high similarity
                def embed_batch(self, texts):
                    return [np.ones(settings.embedding_dim) for _ in texts]  # Return ones vectors for high similarity
            _embedder = MockEmbeddings()
        else:
            # Use Ollama embeddings in production
            logger.info("Using Ollama embeddings")
            _embedder = OllamaEmbeddings(
                api_url=str(settings.ollama_api_url),
                model_name=settings.embedding_model,
                embedding_dim=settings.embedding_dim
            )
    return _embedder

def get_document_store(settings: Settings = Depends(get_settings)) -> InMemoryDocumentStore:
    """Get document store instance."""
    global _document_store
    
    if _document_store is None:
        try:
            _document_store = get_vectorstore(settings)
        except Exception as e:
            raise Exception(f"Failed to initialize document store: {str(e)}")
    
    return _document_store 
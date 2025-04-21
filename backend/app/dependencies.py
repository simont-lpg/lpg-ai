from typing import Generator, List
from fastapi import Depends
from .config import Settings, get_settings
from .vectorstore import get_vectorstore, OllamaEmbeddings, InMemoryDocumentStore
from .schema import DocumentFull
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Global document store instance
_document_store = None

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
def get_embedder(settings: Settings = Depends(get_settings)):
    """Get embedder model based on settings."""
    try:
        logger.info(f"Initializing embedder with model: {settings.embedding_model_name}")
        if settings.embedding_model_name == "mxbai-embed-large:latest":
            logger.info("Using Ollama embeddings")
            return OllamaEmbeddings(
                api_url=str(settings.ollama_api_url),
                model_name=settings.embedding_model_name,
                embedding_dim=settings.embedding_dim
            )
        logger.info(f"Using SentenceTransformer with model: {settings.embedding_model}")
        return SentenceTransformer(settings.embedding_model)
    except Exception as e:
        logger.error(f"Failed to initialize embedder: {str(e)}", exc_info=True)
        raise Exception(f"Failed to initialize embedder: {str(e)}")

def get_document_store(settings: Settings = Depends(get_settings)) -> InMemoryDocumentStore:
    """Get document store instance."""
    global _document_store
    
    if _document_store is None:
        try:
            if settings.embedding_model_name == "mxbai-embed-large:latest":
                model = OllamaEmbeddings(
                    api_url=str(settings.ollama_api_url),
                    model_name=settings.embedding_model_name,
                    embedding_dim=settings.embedding_dim
                )
            else:
                model = SentenceTransformer(settings.embedding_model)
            
            _document_store = InMemoryDocumentStore(
                embedding_dim=settings.embedding_dim,
                collection_name=settings.collection_name,
                embeddings_model=model
            )
        except Exception as e:
            raise Exception(f"Failed to initialize document store: {str(e)}")
    
    return _document_store 
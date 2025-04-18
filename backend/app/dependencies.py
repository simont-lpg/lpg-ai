from typing import Generator, List
from fastapi import Depends
from .config import Settings, get_settings
from .vectorstore import get_vectorstore, OllamaEmbeddings
from .schema import Document
from sentence_transformers import SentenceTransformer
import numpy as np

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

def get_document_store(settings: Settings = Depends(get_settings)):
    """Get document store dependency."""
    store = get_vectorstore(settings)
    return store

def get_embedder(settings: Settings = Depends(get_settings)):
    """Get embedder dependency."""
    if settings.embedding_model_name == "mxbai-embed-large:latest":
        model = OllamaEmbeddings(
            api_url=str(settings.ollama_api_url),
            model_name=settings.embedding_model_name,
            embedding_dim=settings.embedding_dim
        )
    else:
        model = SentenceTransformer(settings.embedding_model)
    return Embedder(model) 
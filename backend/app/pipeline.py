from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from fastapi import Depends
from .config import Settings, get_settings
from .schema import DocumentFull
from .vectorstore import InMemoryDocumentStore, OllamaEmbeddings, get_vectorstore

def get_embedder(settings: Settings = Depends(get_settings)):
    """Get embedder model based on settings."""
    try:
        if settings.embedding_model_name == "mxbai-embed-large:latest":
            return OllamaEmbeddings(
                api_url=str(settings.ollama_api_url),
                model_name=settings.embedding_model_name,
                embedding_dim=settings.embedding_dim
            )
        return SentenceTransformer(settings.embedding_model)
    except Exception as e:
        raise Exception(f"Failed to initialize embedder: {str(e)}")

class Retriever:
    """Document retriever using embeddings and vector similarity search."""
    
    def __init__(self, document_store: InMemoryDocumentStore, settings: Settings):
        self.document_store = document_store
        self.settings = settings
        self.model = None
    
    def initialize(self):
        """Initialize the retriever model."""
        try:
            if self.settings.embedding_model_name == "mxbai-embed-large:latest":
                self.model = OllamaEmbeddings(
                    api_url=str(self.settings.ollama_api_url),
                    model_name=self.settings.embedding_model_name,
                    embedding_dim=self.settings.embedding_dim
                )
            else:
                self.model = SentenceTransformer(self.settings.embedding_model)
        except Exception as e:
            raise Exception(f"Failed to initialize retriever model: {str(e)}")
    
    def retrieve(self, query: str, top_k: int = 5) -> list[DocumentFull]:
        """Retrieve documents for a query."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            if self.model is None:
                self.initialize()
            
            if isinstance(self.model, OllamaEmbeddings):
                query_embedding = self.model.embed_batch([query])[0]
            else:
                query_embedding = self.model.encode(query)
            return self.document_store.query_by_embedding(query_embedding, top_k=top_k)
        except Exception as e:
            raise Exception(f"Retrieval failed: {str(e)}")

class Pipeline:
    """Pipeline for processing RAG queries."""
    
    def __init__(self, retriever: Retriever):
        self.retriever = retriever
        self.components = {"Retriever": retriever}
    
    def run(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the pipeline with the given query and parameters."""
        if not params:
            params = {}
        
        try:
            # Get retriever parameters
            retriever_params = params.get("Retriever", {})
            top_k = retriever_params.get("top_k", 5)
            
            # Retrieve documents
            documents = self.retriever.retrieve(query, top_k=top_k)
            
            return {
                "documents": documents,
                "answers": []  # TODO: Add answer generation
            }
        except ValueError as e:
            # Re-raise ValueError without wrapping
            raise
        except Exception as e:
            raise Exception(f"Pipeline execution failed: {str(e)}")

def build_pipeline(settings: Settings, dev: bool = False) -> tuple[Pipeline, Retriever]:
    """Build a pipeline with the given settings."""
    try:
        if dev:
            # Return a pipeline with a mock retriever
            mock_store = InMemoryDocumentStore(embedding_dim=settings.embedding_dim)
            retriever = Retriever(mock_store, settings)
            return Pipeline(retriever), retriever
        
        # Build real pipeline with a default store
        document_store = InMemoryDocumentStore(
            embedding_dim=settings.embedding_dim,
            collection_name=settings.collection_name
        )
        retriever = Retriever(document_store, settings)
        retriever.initialize()  # Initialize the retriever
        return Pipeline(retriever), retriever
    except Exception as e:
        raise Exception(f"Failed to build pipeline: {str(e)}")

def get_pipeline(settings: Settings = Depends(get_settings)) -> Pipeline:
    """Get pipeline dependency."""
    pipeline, _ = build_pipeline(settings)
    return pipeline 
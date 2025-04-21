from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from fastapi import Depends
from .config import Settings, get_settings
from .schema import DocumentFull
from .vectorstore import InMemoryDocumentStore, OllamaEmbeddings, get_vectorstore
import logging

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
    
    def __init__(self, document_store: InMemoryDocumentStore, model=None):
        self.document_store = document_store
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    def initialize(self):
        """Initialize the retriever if needed."""
        if self.model is None:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def retrieve(self, query: str, top_k: int = 5, filters: Optional[dict] = None) -> list[DocumentFull]:
        """Retrieve documents for a query."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if self.model is None:
            self.initialize()
        
        self.logger.info("=== Starting retrieval ===")
        self.logger.info(f"Query: {query}")
        self.logger.info(f"Filters: {filters}")
        self.logger.info(f"Top k: {top_k}")
        
        # Generate query embedding
        if isinstance(self.model, OllamaEmbeddings):
            query_embedding = self.model.embed_batch([query])[0]
        else:
            query_embedding = self.model.encode(query)
        
        self.logger.info(f"Query embedding shape: {np.array(query_embedding).shape}")
        
        # Convert to numpy array if needed
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        
        # Retrieve documents with filters
        documents = self.document_store.query_by_embedding(query_embedding, top_k=top_k, filters=filters)
        self.logger.info(f"Retrieved {len(documents)} documents")
        
        if documents:
            self.logger.info(f"First document score: {documents[0].score}")
            self.logger.info(f"First document content: {documents[0].content[:100]}...")
        else:
            self.logger.warning("No documents retrieved")
        
        return documents

class Pipeline:
    """Pipeline for processing RAG queries."""
    
    def __init__(self, retriever: Retriever):
        self.retriever = retriever
        self.components = {"Retriever": retriever}
        self.logger = logging.getLogger(__name__)
    
    def run(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the pipeline with the given query and parameters."""
        if not params:
            params = {}
        
        # Get retriever parameters
        retriever_params = params.get("Retriever", {})
        top_k = retriever_params.get("top_k", 5)
        filters = retriever_params.get("filters", None)
        
        try:
            # Retrieve documents with filters
            documents = self.retriever.retrieve(query, top_k=top_k, filters=filters)
            
            self.logger.info(f"Pipeline returned {len(documents)} documents")
            
            return {
                "documents": documents,
                "answers": []  # TODO: Add answer generation
            }
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

def build_pipeline(settings: Settings, document_store: InMemoryDocumentStore, dev: bool = False) -> Tuple[Pipeline, Retriever]:
    """Build a pipeline with the given settings and document store.
    
    Args:
        settings: Application settings
        document_store: Document store instance
        dev: Whether to use development mode (stub embeddings)
        
    Returns:
        Tuple of (Pipeline, Retriever)
        
    Raises:
        RuntimeError: If pipeline initialization fails
    """
    try:
        # Initialize embedder
        if dev:
            # Use stub embeddings in dev mode
            model = type('MockModel', (), {
                'encode': lambda _, text: [0.1] * settings.embedding_dim,
                'embed_batch': lambda _, texts: [[0.1] * settings.embedding_dim for _ in texts]
            })()
        elif settings.embedding_model_name == "mxbai-embed-large:latest":
            model = OllamaEmbeddings(
                api_url=str(settings.ollama_api_url),
                model_name=settings.embedding_model_name,
                embedding_dim=settings.embedding_dim
            )
        else:
            model = SentenceTransformer(settings.embedding_model)
        
        # Create retriever
        retriever = Retriever(document_store=document_store, model=model)
        
        # Create pipeline
        pipeline = Pipeline(retriever=retriever)
        
        return pipeline, retriever
    except Exception as e:
        logger.error(f"Failed to build pipeline: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to build pipeline: {str(e)}")

def get_pipeline(settings: Settings = Depends(get_settings)) -> Pipeline:
    """Get pipeline dependency."""
    pipeline, _ = build_pipeline(settings)
    return pipeline 
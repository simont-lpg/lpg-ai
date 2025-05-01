from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from fastapi import Depends
from .config import Settings, get_settings
from .schema import DocumentFull
from .vectorstore import InMemoryDocumentStore, get_vectorstore
from .dependencies import get_embedder, Embedder
from .generator import OllamaGenerator, DummyGenerator, BaseGenerator
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class Retriever:
    """Document retriever using embeddings and vector similarity search."""
    
    def __init__(self, document_store: InMemoryDocumentStore, model: Optional[Embedder] = None):
        self.document_store = document_store
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    def initialize(self, settings: Settings):
        """Initialize the retriever if needed."""
        if self.model is None:
            self.model = get_embedder(settings)
    
    def retrieve(self, query: str, top_k: int = None, filters: Optional[dict] = None) -> list[DocumentFull]:
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
        query_embedding = self.model.embed_batch([query])[0]
        
        self.logger.info(f"Query embedding shape: {np.array(query_embedding).shape}")
        
        # Convert to numpy array if needed
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
            
        # Resize query embedding if needed
        if query_embedding.shape[0] != self.document_store.embedding_dim:
            self.logger.warning(f"Query embedding dimension ({query_embedding.shape[0]}) does not match document store dimension ({self.document_store.embedding_dim}). Resizing...")
            if query_embedding.shape[0] > self.document_store.embedding_dim:
                query_embedding = query_embedding[:self.document_store.embedding_dim]
            else:
                query_embedding = np.pad(query_embedding, (0, self.document_store.embedding_dim - query_embedding.shape[0]))
        
        # Retrieve documents with filters
        documents = self.document_store.query_by_embedding(query_embedding, top_k=top_k, filters=filters)
        self.logger.info(f"Retrieved {len(documents)} documents")
        
        if documents:
            self.logger.info(f"First document content: {documents[0].content[:100]}...")
        else:
            self.logger.warning("No documents retrieved")
        
        return documents

class Pipeline:
    """Pipeline for processing RAG queries."""
    
    def __init__(self, retriever: Retriever, generator: BaseGenerator, settings: Settings):
        self.retriever = retriever
        self.generator = generator
        self.settings = settings
        self.components = {"Retriever": retriever, "Generator": generator}
        self.logger = logging.getLogger(__name__)
    
    def run(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the pipeline with the given query and parameters."""
        if not params:
            params = {}
        
        # Get retriever parameters with defaults from settings
        retriever_params = {
            **self.settings.pipeline_parameters.get("Retriever", {}),
            **params.get("Retriever", {})
        }
        top_k = retriever_params.get("top_k", self.settings.retriever_top_k)
        filters = retriever_params.get("filters", None)
        
        try:
            # Retrieve documents with filters
            documents = self.retriever.retrieve(query, top_k=top_k, filters=filters)
            
            self.logger.info(f"Pipeline returned {len(documents)} documents")
            
            # Generate answer using the retrieved documents
            if documents:
                # Create a prompt with the retrieved documents
                context = "\n\n".join([doc.content for doc in documents])
                prompt = self.settings.prompt_template.format(
                    context=context,
                    query=query
                )
                
                # Get generator parameters with defaults from settings
                generator_params = {
                    **self.settings.pipeline_parameters.get("Generator", {}),
                    **params.get("Generator", {})
                }
                
                # Generate answer
                answer = self.generator.generate(prompt, **generator_params)
                self.logger.info(f"Generated answer: {answer}")
                
                return {
                    "documents": documents,
                    "answers": [answer]
                }
            else:
                return {
                    "documents": [],
                    "answers": ["I don't know."]
                }
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

def build_pipeline(
    settings: Settings,
    document_store: InMemoryDocumentStore,
    dev: bool = False
) -> Tuple[Pipeline, Retriever]:
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
        # select embedding model
        if dev:
            # Create a dummy embedder for dev/testing
            class DummyEmbedder:
                def __init__(self, dim):
                    self.embedding_dim = dim
                def embed_batch(self, texts):
                    return np.zeros((len(texts), self.embedding_dim))
            embedder = DummyEmbedder(settings.embedding_dim)
        else:
            embedder = get_embedder(settings)
            
        # select generator
        generator = DummyGenerator() if dev else OllamaGenerator(
            api_url=str(settings.ollama_api_url),
            model_name=settings.generator_model_name
        )
        
        # Create retriever
        retriever = Retriever(document_store=document_store, model=embedder)
        
        # Create pipeline
        pipeline = Pipeline(retriever=retriever, generator=generator, settings=settings)
        
        return pipeline, retriever
    except Exception as e:
        logger.error(f"Failed to build pipeline: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to build pipeline: {str(e)}")

def get_pipeline(
    settings: Settings = Depends(get_settings),
    document_store: InMemoryDocumentStore = Depends(get_vectorstore)
) -> Pipeline:
    """Get pipeline dependency."""
    pipeline, _ = build_pipeline(settings, document_store)
    return pipeline 
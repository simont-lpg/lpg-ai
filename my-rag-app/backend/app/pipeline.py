from typing import Tuple

from haystack import Pipeline
from haystack.components.retrievers import InMemoryBM25Retriever
from haystack.document_stores.types import DocumentStore

from app.config import settings
from app.vectorstores import document_store


def build_pipeline(dev: bool = False) -> Tuple[Pipeline, DocumentStore]:
    """Build and return a Haystack pipeline with document store.
    
    Args:
        dev: Whether to run in development mode (uses dummy retriever)
        
    Returns:
        Tuple[Pipeline, DocumentStore]: Configured pipeline and document store
    """
    if dev:
        # Development mode: use dummy retriever that returns first N documents
        pipeline = Pipeline()
        retriever = InMemoryBM25Retriever(
            document_store=document_store,
            top_k=5,
        )
        pipeline.add_component("retriever", retriever)
        
    else:
        # Production mode: full pipeline with placeholders
        pipeline = Pipeline()
        
        # TODO: Add EmbeddingRetriever
        # pipeline.add_component(
        #     "embedder",
        #     SentenceTransformersTextEmbedder(
        #         model=settings.embedding_model,
        #         device="cpu",
        #     )
        # )
        # 
        # pipeline.add_component(
        #     "retriever",
        #     InMemoryEmbeddingRetriever(
        #         document_store=document_store,
        #         top_k=5,
        #     )
        # )
        # 
        # pipeline.add_component(
        #     "reader",
        #     ExtractiveReader(
        #         model="deepset/roberta-base-squad2",
        #         device="cpu",
        #     )
        # )
        # 
        # pipeline.connect("embedder.embedding", "retriever.query_embedding")
        # pipeline.connect("retriever.documents", "reader.documents")
        
        # For now, use the same dummy retriever as dev mode
        retriever = InMemoryBM25Retriever(
            document_store=document_store,
            top_k=5,
        )
        pipeline.add_component("retriever", retriever)
    
    return pipeline, document_store


# Create global instances
pipeline, doc_store = build_pipeline(dev=settings.dev_mode) 
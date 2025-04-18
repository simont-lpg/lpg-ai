from typing import Optional, Tuple, Dict, Any
from sentence_transformers import SentenceTransformer
from .config import Settings
from .vectorstore import get_vectorstore
from .schema import Document

class Pipeline:
    """Simple pipeline that uses sentence transformers for embedding and retrieval."""
    
    def __init__(self, retriever: Any):
        self.retriever = retriever
        self.components = {"retriever": retriever}
    
    def run(self, query: str, params: Optional[Dict] = None, **kwargs) -> Dict:
        """Run the pipeline on a query."""
        if not query:
            raise ValueError("Query cannot be empty")
            
        top_k = params.get("Retriever", {}).get("top_k", 5) if params else 5
        return {"documents": self.retriever.retrieve(query, top_k=top_k)}

class Retriever:
    """Simple retriever that uses sentence transformers."""
    
    def __init__(self, document_store: Any, embedding_model: str):
        self.document_store = document_store
        try:
            self.model = SentenceTransformer(embedding_model)
        except Exception as e:
            raise Exception(f"Model download failed: {str(e)}")
    
    def retrieve(self, query: str, top_k: int = 5) -> list[Document]:
        """Retrieve documents for a query."""
        try:
            query_embedding = self.model.encode(query)
            return self.document_store.query_by_embedding(query_embedding, top_k=top_k)
        except Exception as e:
            raise Exception(f"Retrieval failed: {str(e)}")
    
    def run(self, query: str, top_k: int = 5) -> list[Document]:
        """Alias for retrieve to match the test expectations."""
        return self.retrieve(query, top_k=top_k)

def build_pipeline(settings: Optional[Settings] = None, dev: bool = False) -> Tuple[Pipeline, Retriever]:
    """Build the RAG pipeline.
    
    Args:
        settings: Application settings
        dev: Whether to run in development mode
        
    Returns:
        Tuple of (pipeline, retriever)
    """
    if dev:
        # In dev mode, create a simple pipeline that returns mock documents
        class MockPipeline:
            def run(self, query: str, **kwargs):
                return {
                    "documents": [
                        Document(content="Test document 1", id="test1"),
                        Document(content="Test document 2", id="test2")
                    ]
                }
        
        return MockPipeline(), None
    
    if settings is None:
        raise ValueError("settings must be provided in non-dev mode")
        
    document_store = get_vectorstore(settings)
    retriever = Retriever(document_store, settings.embedding_model)
    pipeline = Pipeline(retriever)
    
    return pipeline, retriever 
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from typing import List, Optional
from .config import Settings
from .pipeline import build_pipeline
from .schema import Query, Response, DocumentMetadata, DocumentFull
from .ingest import ingest_documents
from .dependencies import get_document_store, get_embedder
from pydantic import ConfigDict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Haystack RAG Service")
app.model_config = ConfigDict(arbitrary_types_allowed=True)
settings = Settings()

# Initialize pipeline components
pipeline, retriever = build_pipeline(settings=settings)

@app.get("/")
async def root():
    return {"message": "Haystack RAG Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=Response)
async def query(query: Query, document_store = Depends(get_document_store)):
    """Process a RAG query."""
    try:
        result = pipeline.run(
            query=query.text,
            params={"Retriever": {"top_k": query.top_k}}
        )
        return Response(
            answers=[],  # TODO: Add answer generation
            documents=[doc.to_dict() for doc in result["documents"]]
        )
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/ingest")
async def ingest(
    files: List[UploadFile] = File(...),
    namespace: Optional[str] = Form(None),
    document_store = Depends(get_document_store),
    embedder = Depends(get_embedder)
):
    """Ingest documents into the vector store."""
    try:
        result = await ingest_documents(
            files=files,
            namespace=namespace,
            document_store=document_store,
            embedder=embedder
        )
        return result
    except Exception as e:
        logger.error(f"Error in ingest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.get("/documents", response_model=List[DocumentMetadata])
async def get_documents(
    namespace: Optional[str] = None,
    document_store = Depends(get_document_store)
):
    """Get documents from the document store, optionally filtered by namespace.
    
    Returns a list of documents with metadata only (content, meta, id) in the API documentation,
    but includes full document data (including embeddings and scores) in the actual response.
    """
    try:
        filters = {"namespace": namespace} if namespace else None
        logger.info(f"Getting documents with filters: {filters}")
        logger.info(f"Document store type: {type(document_store)}")
        documents = document_store.get_all_documents(filters=filters)
        logger.info(f"Retrieved {len(documents)} documents")
        # Convert documents to the expected format, preserving all fields
        return [DocumentFull(
            id=doc.id,
            content=doc.content,
            meta=doc.meta,
            embedding=doc.embedding,
            score=doc.score
        ) for doc in documents]
    except Exception as e:
        logger.error(f"Error in get_documents endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) 
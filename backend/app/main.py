from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from .config import Settings, get_settings
from .pipeline import build_pipeline, Pipeline, Retriever
from .schema import Query, Response, DocumentMetadata, DocumentFull, DeleteDocumentsRequest, DeleteDocumentsResponse, FileListResponse
from .ingest import ingest_documents
from .dependencies import get_document_store, get_embedder
from .vectorstore import OllamaEmbeddings
from pydantic import ConfigDict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Haystack RAG Service")
app.model_config = ConfigDict(arbitrary_types_allowed=True)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Default to all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Haystack RAG Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=Response)
async def query(
    query: Query,
    document_store = Depends(get_document_store),
    settings: Settings = Depends(get_settings)
):
    """Process a RAG query."""
    try:
        # Build pipeline with the provided document store
        pipeline, _ = build_pipeline(
            settings=settings, 
            document_store=document_store,
            dev=settings.dev_mode
        )
        
        # Set filters based on namespace
        filters = {"namespace": query.namespace} if query.namespace else {"namespace": "default"}
        
        # Log query details
        logger.info(f"Processing query: {query.text}")
        logger.info(f"Using filters: {filters}")
        logger.info(f"Top k: {query.top_k}")
        
        result = pipeline.run(
            query=query.text,
            params={
                "Retriever": {
                    "top_k": query.top_k,
                    "filters": filters
                }
            }
        )
        
        # Log results
        logger.info(f"Retrieved {len(result['documents'])} documents")
        if result['documents']:
            logger.info(f"First document content: {result['documents'][0].content[:100]}...")
        
        return Response(
            answers=result.get("answers", []),  # Get answers from pipeline result
            documents=[doc.to_dict() for doc in result["documents"]]
        )
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "documents": [],
                "answers": []
            }
        )

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
            namespace=namespace if namespace else "default",
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
    """Get all documents, optionally filtered by namespace."""
    try:
        filters = {"namespace": namespace} if namespace else None
        documents = document_store.get_all_documents(filters=filters)
        return [doc.to_dict() for doc in documents]
    except Exception as e:
        logger.error(f"Error in get_documents endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.delete("/documents", response_model=DeleteDocumentsResponse)
async def delete_documents(
    request: DeleteDocumentsRequest,
    document_store = Depends(get_document_store)
):
    """Delete documents by file name."""
    try:
        deleted = document_store.delete_documents(filters={"file_name": request.file_name})
        return DeleteDocumentsResponse(deleted=deleted)
    except Exception as e:
        logger.error(f"Error in delete_documents endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.get("/files", response_model=FileListResponse)
async def get_files(document_store = Depends(get_document_store)):
    """Get list of files in the document store."""
    try:
        # Group documents by filename and namespace
        file_groups = {}
        for doc in document_store.documents:
            if "file_name" in doc.meta:
                key = (doc.meta["file_name"], doc.meta.get("namespace", "default"))
                if key not in file_groups:
                    file_groups[key] = {
                        "filename": doc.meta["file_name"],
                        "namespace": doc.meta.get("namespace", "default"),
                        "document_count": 0,
                        "id": doc.id,
                        "file_size": doc.meta.get("file_size", 0)
                    }
                file_groups[key]["document_count"] += 1
        
        # Convert to list
        files = list(file_groups.values())
        return FileListResponse(files=files)
    except Exception as e:
        logger.error(f"Error in get_files endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) 
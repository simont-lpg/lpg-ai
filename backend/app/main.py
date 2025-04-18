from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from typing import List, Optional
from .config import Settings
from .pipeline import build_pipeline
from .schema import Query, Response, Document
from .ingest import ingest_documents
from .dependencies import get_document_store, get_embedder

app = FastAPI(title="Haystack RAG Service")
settings = Settings()

# Initialize shared document store
document_store = get_document_store(settings)
pipeline, retriever = build_pipeline(settings=settings, document_store=document_store)

@app.get("/")
async def root():
    return {"message": "Haystack RAG Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=Response)
async def query(query: Query):
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
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/ingest")
async def ingest(
    files: List[UploadFile] = File(...),
    namespace: Optional[str] = Form(None),
    embedder = Depends(get_embedder)
):
    """Ingest documents into the vector store."""
    try:
        return await ingest_documents(files, namespace, document_store, embedder)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) 
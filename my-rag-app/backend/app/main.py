from typing import List

from fastapi import FastAPI, HTTPException
from haystack import Document
from pydantic import BaseModel

from app.config import settings
from app.pipeline import pipeline, doc_store


app = FastAPI(
    title="RAG API",
    description="A RAG (Retrieval-Augmented Generation) API using Haystack and Chroma",
    version="0.1.0",
)


class QueryRequest(BaseModel):
    """Request model for the /query endpoint."""
    query: str


class QueryResponse(BaseModel):
    """Response model for the /query endpoint."""
    content: str
    meta: dict
    score: float | None = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/query", response_model=List[QueryResponse])
async def query(request: QueryRequest) -> List[QueryResponse]:
    """Query the RAG pipeline for relevant documents.
    
    Args:
        request: The query request containing the search query
        
    Returns:
        List[QueryResponse]: List of relevant documents with their metadata
    """
    try:
        # Run the pipeline
        result = pipeline.run(
            {
                "retriever": {"query": request.query},
            }
        )
        
        # Extract and format the results
        documents = result["retriever"]["documents"]
        return [
            QueryResponse(
                content=doc.content,
                meta=doc.meta,
                score=doc.score,
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.dev_mode,
    ) 
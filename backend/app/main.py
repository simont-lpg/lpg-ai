from fastapi import FastAPI, HTTPException
from .config import Settings
from .pipeline import build_pipeline
from .schema import Query, Response

app = FastAPI(title="Haystack RAG Service")
settings = Settings()
pipeline, retriever = build_pipeline(settings=settings)

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
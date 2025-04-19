from pydantic import BaseModel, Field, field_validator, StrictStr, ConfigDict
from typing import Optional, Dict, List, Any

class DocumentMetadata(BaseModel):
    """Lightweight document model for API documentation."""
    content: str
    meta: Dict = {}
    id: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')

    def to_dict(self) -> Dict:
        """Convert document to dictionary."""
        return {
            "content": self.content,
            "meta": self.meta,
            "id": self.id
        }

class DocumentFull(DocumentMetadata):
    """Full document model including embeddings and scores."""
    embedding: Optional[List[float]] = None
    score: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert document to dictionary."""
        return {
            "content": self.content,
            "meta": self.meta,
            "id": self.id,
            "embedding": self.embedding,
            "score": self.score
        }

class Query(BaseModel):
    """Query model for RAG queries."""
    text: StrictStr = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=100)

class Response(BaseModel):
    """Response model for RAG queries."""
    answers: List[str] = []
    documents: List[DocumentMetadata]

class DeleteDocumentsRequest(BaseModel):
    """Request model for deleting documents by file name."""
    file_name: str

class DeleteDocumentsResponse(BaseModel):
    """Response model for document deletion."""
    status: str = "success"
    deleted: int

class FileMetadata(BaseModel):
    """Metadata for a file in the document store."""
    filename: str
    namespace: str = "default"
    document_count: int
    id: str

class FileListResponse(BaseModel):
    """Response model for the /files endpoint."""
    files: List[FileMetadata] 
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
    namespace: Optional[str] = Field(default=None, description="Optional namespace to filter documents")

class Response(BaseModel):
    """Response model for RAG queries."""
    answers: List[str] = Field(default_factory=list)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = Field(default=None, description="Error message if query failed")

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
    file_size: int  # Size in bytes

class FileListResponse(BaseModel):
    """Response model for the /files endpoint."""
    files: List[FileMetadata] 
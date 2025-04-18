from typing import List, Optional
from fastapi import UploadFile, Depends
from unstructured.partition.text import partition_text
from .dependencies import get_document_store, get_embedder
from .schema import Document
import io

class SimpleConverter:
    """A simple converter that uses unstructured to convert files to text."""
    
    def run(self, content: bytes) -> List[Document]:
        """Convert file content to documents."""
        if not content:
            raise Exception("Empty file content provided")
            
        try:
            # Create a file-like object from the content
            file_obj = io.BytesIO(content)
            # Use text partitioner directly for text content
            elements = partition_text(file=file_obj)
            return [Document(content=str(element)) for element in elements]
        except Exception as e:
            raise Exception(f"Failed to convert file content: {str(e)}")

async def ingest_documents(
    files: List[UploadFile],
    namespace: Optional[str] = None,
    document_store = None,
    embedder = None
) -> dict:
    """Ingest documents into the vector store.
    
    Args:
        files: List of uploaded files
        namespace: Optional namespace for the documents
        document_store: Document store instance
        embedder: Embedder instance
        
    Returns:
        dict with ingestion status and counts
    """
    if not document_store or not embedder:
        raise ValueError("Document store and embedder must be provided")
        
    total_chunks = 0
    files_ingested = 0
    
    # Create a single converter instance for all file types
    converter = SimpleConverter()
    
    for file in files:
        try:
            # Skip unsupported file types
            if not file.filename.endswith(('.pdf', '.docx', '.txt')):
                continue
                
            # Read file content
            content = await file.read()
            
            # Convert to document
            documents = converter.run(content)
            
            # Embed chunks
            embeddings = embedder.embed_batch([doc.content for doc in documents])
            
            # Store documents with embeddings
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
                doc.metadata = {"namespace": namespace} if namespace else {}
                document_store.write_documents([doc])
            
            total_chunks += len(documents)
            files_ingested += 1
        except Exception as e:
            raise Exception(f"Failed to ingest file {file.filename}: {str(e)}")
    
    return {
        "status": "success",
        "namespace": namespace,
        "files_ingested": files_ingested,
        "total_chunks": total_chunks
    } 
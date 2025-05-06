from typing import List, Optional
from fastapi import UploadFile, Depends
from unstructured.partition.text import partition_text
from .dependencies import get_document_store, get_embedder
from .schema import DocumentFull
from sentence_transformers import SentenceTransformer
from .progress import get_progress_queue, cleanup_progress_queue
import io
import uuid
import logging
import numpy as np

logger = logging.getLogger(__name__)

class SimpleConverter:
    """A simple converter that uses unstructured to convert files to text."""
    
    def run(self, content: bytes, doc_id: Optional[str] = None) -> List[DocumentFull]:
        """Convert file content to documents."""
        if not content:
            raise Exception("Empty file content provided")
            
        try:
            # Create a file-like object from the content
            file_obj = io.BytesIO(content)
            # Use text partitioner directly for text content
            elements = partition_text(file=file_obj)
            # Use provided ID or generate a new one
            return [DocumentFull(
                id=doc_id or str(uuid.uuid4()), 
                content=str(element),
                meta={}  # Initialize with empty meta dict
            ) for element in elements]
        except Exception as e:
            raise Exception(f"Failed to convert file content: {str(e)}")

async def ingest_documents(
    files: List[UploadFile],
    namespace: Optional[str] = None,
    document_store = None,
    embedder = None,
    doc_id: Optional[str] = None
) -> dict:
    """Ingest documents into the vector store.
    
    Args:
        files: List of uploaded files
        namespace: Optional namespace for the documents
        document_store: Document store instance
        embedder: Embedder instance
        doc_id: Optional document ID to use
        
    Returns:
        dict with ingestion status and upload_id
    """
    if not document_store or not embedder:
        raise ValueError("Document store and embedder must be provided")
        
    # Generate a unique upload ID
    upload_id = str(uuid.uuid4())
    progress_queue = get_progress_queue(upload_id)
    
    try:
        total_chunks = 0
        files_ingested = 0
        all_documents = []
        
        # Create a single converter instance for all file types
        converter = SimpleConverter()
        
        # Report initial progress
        await progress_queue.put(0)
        
        for file in files:
            try:
                # Skip unsupported file types
                if not file.filename.endswith(('.pdf', '.docx', '.txt')):
                    continue
                    
                # Read file content
                content = await file.read()
                file_size = len(content)  # Get file size in bytes
                
                # Convert to document
                documents = converter.run(content, doc_id=doc_id)
                
                # Add namespace and filename to documents
                for doc in documents:
                    doc.meta = {
                        "namespace": namespace if namespace is not None else "default",
                        "file_name": file.filename,
                        "file_size": file_size
                    }
                
                all_documents.extend(documents)
                total_chunks += len(documents)
                files_ingested += 1
            except Exception as e:
                raise Exception(f"Failed to ingest file {file.filename}: {str(e)}")
        
        if all_documents:
            try:
                logger.info(f"Starting embedding generation for {len(all_documents)} documents")
                
                # Verify embedder is initialized
                if embedder is None:
                    raise Exception("Embedder is not initialized")
                
                # Test embedder with a small sample
                test_text = "test"
                try:
                    if isinstance(embedder, SentenceTransformer):
                        test_embedding = embedder.encode(test_text)
                    else:
                        test_embedding = embedder.embed_batch([test_text])[0]
                    logger.info(f"Embedder test successful, embedding dimension: {len(test_embedding)}")
                except Exception as e:
                    logger.error(f"Embedder test failed: {str(e)}", exc_info=True)
                    raise Exception(f"Embedder test failed: {str(e)}")
                
                # Embed all documents at once
                if isinstance(embedder, SentenceTransformer):
                    logger.info("Using SentenceTransformer for embeddings")
                    embeddings = embedder.encode([doc.content for doc in all_documents], convert_to_numpy=True)
                    embeddings = embeddings.tolist()
                else:
                    logger.info("Using custom embedder for batch embeddings")
                    embeddings = embedder.embed_batch([doc.content for doc in all_documents])
                
                logger.info(f"Generated {len(embeddings)} embeddings")
                
                # Add embeddings to documents
                for doc, embedding in zip(all_documents, embeddings):
                    if embedding is None:
                        raise Exception(f"Failed to generate embedding for document {doc.id}")
                    doc.embedding = np.array(embedding) if not isinstance(embedding, np.ndarray) else embedding
                    logger.debug(f"Added embedding to document {doc.id}: {len(embedding) if embedding is not None else 'None'}")
                
                # Write all documents at once
                logger.info("Writing documents to store")
                document_store.add_documents(all_documents)
                logger.info("Successfully wrote documents to store")
                
                # Report completion
                await progress_queue.put(100)
            except Exception as e:
                logger.error(f"Failed to process documents: {str(e)}", exc_info=True)
                raise Exception(f"Failed to process documents: {str(e)}")
        
        return {
            "status": "success",
            "upload_id": upload_id
        }
    except Exception as e:
        # Clean up the progress queue on error
        cleanup_progress_queue(upload_id)
        raise e 
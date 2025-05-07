from typing import List, Optional, Dict, Any
import numpy as np
from pydantic import BaseModel
from .schema import DocumentFull
from sentence_transformers import SentenceTransformer
import logging
from .config import Settings
from chromadb import Client, Settings as ChromaSettings

logger = logging.getLogger(__name__)

class OllamaEmbeddings:
    """Wrapper for Ollama embeddings API."""
    
    def __init__(self, api_url: str, model_name: str, embedding_dim: int):
        self.api_url = api_url
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        
    def embed(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        import requests
        try:
            response = requests.post(
                f"{self.api_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Error getting embedding from Ollama: {str(e)}")
            raise
            
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts."""
        return [self.embed(text) for text in texts]

class InMemoryDocumentStore:
    """In-memory document store with vector search capabilities."""
    
    def __init__(
        self,
        embedding_dim: int,
        collection_name: str,
        embeddings_model: Any
    ):
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be greater than 0")
        self.embedding_dim = embedding_dim
        self.collection_name = collection_name
        self.embeddings_model = embeddings_model
        self.documents: List[DocumentFull] = []
        self.embeddings: np.ndarray = np.empty((0, embedding_dim))
        
    def add_documents(self, documents: List[DocumentFull]) -> None:
        """Add documents to the store."""
        if not documents:
            return
            
        # Get embeddings for new documents if not provided
        texts = []
        new_embeddings = []
        for doc in documents:
            if doc.embedding is not None:
                new_embeddings.append(doc.embedding)
            else:
                texts.append(doc.content)
        
        # Generate embeddings for documents without them
        if texts:
            generated_embeddings = self.embeddings_model.embed_batch(texts)
            if isinstance(generated_embeddings, list):
                generated_embeddings = np.array(generated_embeddings)
            new_embeddings.extend(generated_embeddings)
        
        # Ensure embeddings have the correct dimension and convert to numpy array
        if isinstance(new_embeddings, list):
            new_embeddings = np.array(new_embeddings)
        if new_embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {new_embeddings.shape[1]}")
        
        # Add to store
        self.documents.extend(documents)
        self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
    def write_documents(self, documents: List[DocumentFull]) -> None:
        """Write documents to the store (alias for add_documents)."""
        self.add_documents(documents)
        
    def get_all_documents(self, filters: Optional[Dict[str, Any]] = None) -> List[DocumentFull]:
        """Get all documents, optionally filtered."""
        if not filters:
            # Return documents with their embeddings
            for i, doc in enumerate(self.documents):
                doc.embedding = self.embeddings[i].tolist()
            return self.documents
            
        filtered_docs = []
        filtered_indices = []
        for i, doc in enumerate(self.documents):
            match = True
            for key, value in filters.items():
                if key not in doc.meta or doc.meta[key] != value:
                    match = False
                    break
            if match:
                filtered_docs.append(doc)
                filtered_indices.append(i)
        
        # Attach embeddings to filtered documents
        for i, doc in enumerate(filtered_docs):
            doc.embedding = self.embeddings[filtered_indices[i]].tolist()
        return filtered_docs

    def get(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None) -> Dict[str, List]:
        """Get documents by IDs or filters, matching Chroma's interface."""
        if ids is not None:
            # Filter by IDs
            filtered_docs = []
            filtered_indices = []
            for i, doc in enumerate(self.documents):
                if doc.id in ids:
                    filtered_docs.append(doc)
                    filtered_indices.append(i)
        elif where is not None:
            # Filter by metadata
            filtered_docs = []
            filtered_indices = []
            for i, doc in enumerate(self.documents):
                match = True
                for key, value in where.items():
                    if key not in doc.meta or doc.meta[key] != value:
                        match = False
                        break
                if match:
                    filtered_docs.append(doc)
                    filtered_indices.append(i)
        else:
            # Return all documents
            filtered_docs = self.documents
            filtered_indices = list(range(len(self.documents)))

        # Return in Chroma's format
        return {
            "ids": [doc.id for doc in filtered_docs],
            "metadatas": [doc.meta for doc in filtered_docs],
            "documents": [doc.content for doc in filtered_docs],
            "embeddings": [self.embeddings[i].tolist() for i in filtered_indices]
        }
        
    def query_by_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        settings: Optional[Settings] = None
    ) -> List[DocumentFull]:
        """Query documents by embedding."""
        if not self.documents:
            return []
            
        # Convert query embedding to numpy array if needed
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
            
        # Apply filters first if specified
        if filters:
            filtered_docs = []
            filtered_embeddings = []
            for doc, emb in zip(self.documents, self.embeddings):
                match = True
                for key, value in filters.items():
                    if key not in doc.meta or doc.meta[key] != value:
                        match = False
                        break
                if match:
                    filtered_docs.append(doc)
                    filtered_embeddings.append(emb)
            if not filtered_docs:
                return []
            docs = filtered_docs
            embeddings = np.stack(filtered_embeddings)
        else:
            docs = self.documents
            embeddings = self.embeddings
        
        # Normalize embeddings for cosine similarity
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm
        
        embeddings_norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings_norm[embeddings_norm == 0] = 1  # Avoid division by zero
        embeddings = embeddings / embeddings_norm
        
        # Calculate similarities
        similarities = np.dot(embeddings, query_embedding)
        
        # Get top k results
        top_k = min(top_k, len(docs))
        top_k_indices = np.argsort(similarities)[-top_k:][::-1]
        results = [docs[i] for i in top_k_indices]
        
        # Apply score threshold from settings if available
        if settings is not None and settings.retriever_score_threshold is not None:
            score_threshold = settings.retriever_score_threshold
            results = [
                doc for i, doc in enumerate(results)
                if similarities[top_k_indices[i]] >= score_threshold
            ]
            
            # Add similarity scores to results
            for i, doc in enumerate(results):
                doc.score = float(similarities[top_k_indices[i]])
        
        return results
        
    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents by their IDs."""
        if not document_ids:
            return
            
        # Find indices of documents to delete
        indices_to_delete = [
            i for i, doc in enumerate(self.documents)
            if doc.id in document_ids
        ]
        
        # Remove documents and their embeddings
        for i in sorted(indices_to_delete, reverse=True):
            del self.documents[i]
            self.embeddings = np.delete(self.embeddings, i, axis=0)
            
    def delete_documents_by_file_name(self, file_name: str) -> int:
        """Delete documents by file name.
        
        Args:
            file_name: The name of the file to delete documents for.
            
        Returns:
            int: The number of documents deleted.
        """
        # Find documents with matching file name
        indices_to_delete = [
            i for i, doc in enumerate(self.documents)
            if doc.meta.get("file_name") == file_name
        ]
        
        # Remove documents and their embeddings
        for i in sorted(indices_to_delete, reverse=True):
            if i < len(self.documents):
                del self.documents[i]
                if i < len(self.embeddings):
                    self.embeddings = np.delete(self.embeddings, i, axis=0)
            
        return len(indices_to_delete)
        
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        score_threshold: Optional[float] = None,
        settings: Optional[Settings] = None
    ) -> List[DocumentFull]:
        """Search for similar documents."""
        if not self.documents:
            return []
            
        # Get query embedding
        query_embedding = self.embeddings_model.embed_batch([query])[0]
        
        # Ensure query embedding has the correct dimension
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        if query_embedding.shape[0] != self.embedding_dim:
            raise ValueError(f"Query embedding dimension mismatch: expected {self.embedding_dim}, got {query_embedding.shape[0]}")
        
        # Calculate similarities
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Get top k results
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        results = [self.documents[i] for i in top_k_indices]
        
        # Apply score threshold if specified or from settings
        if score_threshold is None and settings is not None:
            score_threshold = settings.retriever_score_threshold
            
        if score_threshold is not None:
            results = [
                doc for i, doc in enumerate(results)
                if similarities[top_k_indices[i]] >= score_threshold
            ]
            
        return results

class ChromaDocumentStore:
    """ChromaDB-based document store with vector search capabilities."""
    
    def __init__(
        self,
        embedding_dim: int,
        collection_name: str,
        embeddings_model: Any,
        persist_directory: str
    ):
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be greater than 0")
        self.embedding_dim = embedding_dim
        self.collection_name = collection_name
        self.embeddings_model = embeddings_model
        self.persist_directory = persist_directory
        
        # Initialize Chroma client
        try:
            logger.info(f"Initializing ChromaDB with collection '{collection_name}' in directory '{persist_directory}'")
            logger.info(f"Embedding dimension: {embedding_dim}")
            
            self.client = Client(ChromaSettings(
                persist_directory=persist_directory,
                is_persistent=True
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"embedding_dim": embedding_dim}
            )
            
            # Log collection info
            collection_count = self.collection.count()
            logger.info(f"Collection '{collection_name}' initialized with {collection_count} documents")
            
            # Verify collection settings
            collection_metadata = self.collection.metadata
            logger.info(f"Collection metadata: {collection_metadata}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}", exc_info=True)
            raise Exception(f"Failed to initialize ChromaDB: {str(e)}")
    
    def add_documents(self, documents: List[DocumentFull]) -> None:
        """Add documents to the store."""
        if not documents:
            return
            
        # Get embeddings for new documents if not provided
        texts = []
        new_embeddings = []
        for doc in documents:
            if doc.embedding is not None:
                new_embeddings.append(doc.embedding)
            else:
                texts.append(doc.content)
        
        # Generate embeddings for documents without them
        if texts:
            generated_embeddings = self.embeddings_model.embed_batch(texts)
            if isinstance(generated_embeddings, list):
                generated_embeddings = np.array(generated_embeddings)
            new_embeddings.extend(generated_embeddings)
        
        # Ensure embeddings have the correct dimension
        if isinstance(new_embeddings, list):
            new_embeddings = np.array(new_embeddings)
        if new_embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {new_embeddings.shape[1]}")
        
        # Add to ChromaDB in batches
        try:
            logger.info(f"Adding {len(documents)} documents to ChromaDB")
            logger.info(f"First document content preview: {documents[0].content[:100]}...")
            logger.info(f"First embedding shape: {new_embeddings[0].shape}")
            
            # Process in batches of 5000 (slightly below max batch size of 5461)
            batch_size = 5000
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                logger.info(f"Processing batch {i//batch_size + 1} of {(len(documents) + batch_size - 1)//batch_size}")
                
                self.collection.add(
                    documents=[doc.content for doc in documents[i:batch_end]],
                    metadatas=[doc.meta for doc in documents[i:batch_end]],
                    ids=[doc.id for doc in documents[i:batch_end]],
                    embeddings=new_embeddings[i:batch_end].tolist()
                )
            
            logger.info("Successfully added all documents to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {str(e)}", exc_info=True)
            raise Exception(f"Failed to add documents to ChromaDB: {str(e)}")
    
    def get_all_documents(self, filters: Optional[Dict[str, Any]] = None) -> List[DocumentFull]:
        """Get all documents, optionally filtered."""
        try:
            results = self.collection.get(
                where=filters if filters else None,
                include=["documents", "metadatas", "embeddings"]
            )
            
            if not results or not results["ids"]:
                logger.warning("No documents found in collection")
                return []
            
            documents = []
            for i in range(len(results["ids"])):
                doc = DocumentFull(
                    id=results["ids"][i],
                    content=results["documents"][i],
                    meta=results["metadatas"][i]
                )
                # Only set embedding if it exists in results
                if "embeddings" in results and results["embeddings"] is not None and i < len(results["embeddings"]):
                    doc.embedding = results["embeddings"][i]
                documents.append(doc)
            
            logger.info(f"Retrieved {len(documents)} documents from ChromaDB")
            return documents
        except Exception as e:
            logger.error(f"Failed to get documents from ChromaDB: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get documents from ChromaDB: {str(e)}")
    
    def get(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None) -> Dict[str, List]:
        """Get documents by IDs or filters, matching Chroma's interface."""
        try:
            return self.collection.get(
                ids=ids,
                where=where
            )
        except Exception as e:
            logger.error(f"Failed to get documents from ChromaDB: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get documents from ChromaDB: {str(e)}")
    
    def query_by_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        settings: Optional[Settings] = None
    ) -> List[DocumentFull]:
        """Query documents by embedding."""
        try:
            logger.info(f"Querying ChromaDB with top_k={top_k}, filters={filters}")
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results or not results["ids"][0]:
                logger.warning("No documents found in query results")
                return []
            
            documents = []
            distances = results["distances"][0]
            
            # Normalize distances to [0, 1] range
            if distances:
                min_dist = min(distances)
                max_dist = max(distances)
                dist_range = max_dist - min_dist
                if dist_range == 0:
                    # If all distances are the same, give them all the same score
                    normalized_distances = [0.5] * len(distances)
                else:
                    normalized_distances = [(d - min_dist) / dist_range for d in distances]
            else:
                normalized_distances = [0] * len(distances)
            
            for i in range(len(results["ids"][0])):
                doc = DocumentFull(
                    id=results["ids"][0][i],
                    content=results["documents"][0][i],
                    meta=results["metadatas"][0][i]
                )
                if "distances" in results:
                    # Convert normalized distance to similarity score
                    # 1 - normalized_distance gives us a score where:
                    # - 1.0 means most similar (smallest distance)
                    # - 0.0 means least similar (largest distance)
                    doc.score = 1.0 - normalized_distances[i]
                    logger.debug(f"Document {i} distance: {distances[i]}, normalized: {normalized_distances[i]}, score: {doc.score}")
                documents.append(doc)
            
            # Apply score threshold from settings if available
            if settings is not None and settings.retriever_score_threshold is not None:
                original_count = len(documents)
                # Log scores before filtering
                logger.info("Document scores before filtering:")
                for doc in documents:
                    logger.info(f"Document {doc.id}: score={doc.score}")
                
                documents = [
                    doc for doc in documents
                    if doc.score is None or doc.score >= settings.retriever_score_threshold
                ]
                if len(documents) < original_count:
                    logger.info(f"Filtered out {original_count - len(documents)} documents below score threshold {settings.retriever_score_threshold}")
            
            logger.info(f"Retrieved {len(documents)} documents after filtering")
            return documents
        except Exception as e:
            logger.error(f"Failed to query documents from ChromaDB: {str(e)}", exc_info=True)
            raise Exception(f"Failed to query documents from ChromaDB: {str(e)}")
    
    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents by their IDs."""
        if not document_ids:
            return
            
        try:
            self.collection.delete(ids=document_ids)
        except Exception as e:
            logger.error(f"Failed to delete documents from ChromaDB: {str(e)}", exc_info=True)
            raise Exception(f"Failed to delete documents from ChromaDB: {str(e)}")
    
    def delete_documents_by_file_name(self, file_name: str) -> int:
        """Delete documents by file name."""
        try:
            # First get all documents with matching file name
            results = self.collection.get(
                where={"file_name": file_name}
            )
            
            if not results["ids"]:
                return 0
                
            # Delete the documents
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])
        except Exception as e:
            logger.error(f"Failed to delete documents by file name from ChromaDB: {str(e)}", exc_info=True)
            raise Exception(f"Failed to delete documents by file name from ChromaDB: {str(e)}")
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        score_threshold: Optional[float] = None,
        settings: Optional[Settings] = None
    ) -> List[DocumentFull]:
        """Search for similar documents."""
        try:
            # Get query embedding
            query_embedding = self.embeddings_model.embed_batch([query])[0]
            
            # Ensure query embedding has the correct dimension
            if isinstance(query_embedding, list):
                query_embedding = np.array(query_embedding)
            if query_embedding.shape[0] != self.embedding_dim:
                raise ValueError(f"Query embedding dimension mismatch: expected {self.embedding_dim}, got {query_embedding.shape[0]}")
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            documents = []
            for i in range(len(results["ids"][0])):
                doc = DocumentFull(
                    id=results["ids"][0][i],
                    content=results["documents"][0][i],
                    meta=results["metadatas"][0][i]
                )
                if "distances" in results:
                    doc.score = 1.0 - results["distances"][0][i]  # Convert distance to similarity score
                documents.append(doc)
            
            # Apply score threshold if specified or from settings
            if score_threshold is None and settings is not None:
                score_threshold = settings.retriever_score_threshold
                
            if score_threshold is not None:
                documents = [
                    doc for doc in documents
                    if doc.score is None or doc.score >= score_threshold
                ]
            
            return documents
        except Exception as e:
            logger.error(f"Failed to perform similarity search in ChromaDB: {str(e)}", exc_info=True)
            raise Exception(f"Failed to perform similarity search in ChromaDB: {str(e)}")

def get_vectorstore(settings: Settings) -> ChromaDocumentStore:
    """Get vectorstore instance based on settings."""
    try:
        from .dependencies import get_embedder
        model = get_embedder(settings)
        
        # Always use ChromaDB for persistence
        return ChromaDocumentStore(
            embedding_dim=settings.embedding_dim,
            collection_name=settings.collection_name,
            embeddings_model=model,
            persist_directory=settings.chroma_dir
        )
    except Exception as e:
        logger.error(f"Failed to initialize vectorstore: {str(e)}", exc_info=True)
        raise Exception(f"Failed to initialize vectorstore: {str(e)}") 
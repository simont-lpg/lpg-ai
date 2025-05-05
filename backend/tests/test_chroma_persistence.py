import pytest
import tempfile
import os
from pathlib import Path
from chromadb import Client, Settings as ChromaSettings
from app.config import Settings
from app.schema import DocumentFull

def test_chroma_persistence():
    # Create a temporary directory for Chroma
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up test settings
        settings = Settings(
            chroma_dir=temp_dir,
            collection_name="test_collection",
            embedding_model="test_model",
            generator_model_name="test_generator",
            ollama_api_url="http://localhost:11434",
            api_host="localhost",
            api_port=8000,
            cors_origins=["*"],
            dev_mode=True,
            environment="test",
            log_level="INFO",
            secret_key="test_key",
            rate_limit_per_minute=60
        )

        # Initialize Chroma client
        client = Client(ChromaSettings(
            persist_directory=settings.chroma_dir,
            is_persistent=True
        ))
        collection = client.get_or_create_collection(name=settings.collection_name)

        # Create a test document
        test_doc = DocumentFull(
            id="test_doc_1",
            content="This is a test document",
            meta={"source": "test"}
        )

        # Add document to collection
        collection.add(
            documents=[test_doc.content],
            metadatas=[test_doc.meta],
            ids=[test_doc.id]
        )

        # Verify document was added
        results = collection.get(ids=[test_doc.id])
        assert len(results["documents"]) == 1
        assert results["documents"][0] == test_doc.content
        assert results["metadatas"][0] == test_doc.meta

        # Reinitialize client to test persistence
        client = Client(ChromaSettings(
            persist_directory=settings.chroma_dir,
            is_persistent=True
        ))
        collection = client.get_or_create_collection(name=settings.collection_name)

        # Verify document persists after reinitialization
        results = collection.get(ids=[test_doc.id])
        assert len(results["documents"]) == 1
        assert results["documents"][0] == test_doc.content
        assert results["metadatas"][0] == test_doc.meta 
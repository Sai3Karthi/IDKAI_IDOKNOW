"""
Vector Database Manager for storing and retrieving supporting evidence documents.
Uses ChromaDB for vector embeddings and similarity search.
"""

import chromadb
import asyncio
import logging
from typing import List, Dict, Any, Optional
import hashlib
import json
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDBManager:
    """Manages vector database operations for storing supporting evidence."""
    
    def __init__(self, db_path: str = None, db_name: str = "leftist_common_evidence_db"):
        """Initialize the vector database manager."""
        if db_path is None:
            # Default to Module4 directory with custom db name
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', db_name)
        
        self.db_path = db_path
        self.client = None
        self.collections = {}
        
        # Initialize ChromaDB
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize ChromaDB client and setup."""
        try:
            # Create persistent client
            os.makedirs(self.db_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.db_path)
            logger.info(f"Vector database initialized at: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def get_or_create_collection(self, collection_name: str) -> chromadb.Collection:
        """Get or create a collection in the vector database."""
        try:
            if collection_name not in self.collections:
                # Try to get existing collection first
                try:
                    collection = self.client.get_collection(name=collection_name)
                    logger.info(f"Retrieved existing collection: {collection_name}")
                except:
                    # Create new collection if it doesn't exist
                    collection = self.client.create_collection(
                        name=collection_name,
                        metadata={"description": f"Supporting evidence for {collection_name}"}
                    )
                    logger.info(f"Created new collection: {collection_name}")
                
                self.collections[collection_name] = collection
            
            return self.collections[collection_name]
        
        except Exception as e:
            logger.error(f"Error managing collection {collection_name}: {e}")
            raise
    
    async def add_document(self, collection_name: str, document: Dict[str, Any], 
                          document_id: str = None) -> bool:
        """Add a document to the vector database."""
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Generate ID if not provided
            if document_id is None:
                document_id = self._generate_document_id(document)
            
            # Extract content and metadata
            content = document.get('content', '')
            metadata = document.get('metadata', {})
            
            # Ensure metadata values are JSON serializable
            serializable_metadata = self._make_serializable(metadata)
            
            # Add document to collection
            collection.add(
                documents=[content],
                metadatas=[serializable_metadata],
                ids=[document_id]
            )
            
            logger.info(f"Added document {document_id} to collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document to {collection_name}: {e}")
            return False
    
    async def search(self, collection_name: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents in the vector database."""
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Perform similarity search
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'][0] else 0.0,
                        'id': results['ids'][0][i] if results['ids'][0] else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results for query in {collection_name}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching {collection_name}: {e}")
            return []
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()
            
            return {
                "collection_name": collection_name,
                "document_count": count,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {e}")
            return {}
    
    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from the vector database."""
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(ids=[document_id])
            
            logger.info(f"Deleted document {document_id} from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from {collection_name}: {e}")
            return False
    
    async def get_all_collections(self) -> List[str]:
        """Get list of all collections in the database."""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def _generate_document_id(self, document: Dict[str, Any]) -> str:
        """Generate a unique ID for a document."""
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        # Create unique ID based on content and metadata
        id_string = f"{content[:100]}_{metadata.get('source_url', '')}_{metadata.get('claim_text', '')}"
        return hashlib.md5(id_string.encode()).hexdigest()
    
    def _make_serializable(self, obj: Any) -> Any:
        """Make object JSON serializable for ChromaDB metadata."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif obj is None:
            return None
        else:
            # Convert other types to string
            return str(obj)
    
    def close(self):
        """Close the database connection."""
        try:
            if self.client:
                # ChromaDB doesn't require explicit closing
                self.client = None
                self.collections = {}
                logger.info("Vector database connection closed")
        except Exception as e:
            logger.error(f"Error closing vector database: {e}")

# Async context manager for vector database
class AsyncVectorDBManager:
    """Async context manager wrapper for VectorDBManager."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.manager = None
    
    async def __aenter__(self):
        self.manager = VectorDBManager(self.db_path)
        return self.manager
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.manager:
            self.manager.close()
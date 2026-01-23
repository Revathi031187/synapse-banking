"""
ChromaDB Client for Vector Storage and Retrieval
Handles all vector database operations for production deployment
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class ChromaDBClient:
    """Manages ChromaDB collections and operations"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB client with persistence
        
        Args:
            persist_directory: Directory to store ChromaDB data
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding function (sentence-transformers)
        # Using all-MiniLM-L6-v2: Fast, efficient, 384-dimensional embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        logger.info(f"🔥 ChromaDB initialized at {self.persist_directory}")
    
    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None) -> chromadb.Collection:
        """
        Get existing collection or create new one
        
        Args:
            name: Collection name
            metadata: Optional metadata for collection
            
        Returns:
            ChromaDB collection
        """
        try:
            # Prepare metadata - ChromaDB requires non-empty metadata or None
            collection_metadata = None
            if metadata:
                collection_metadata = metadata
            else:
                # Provide default non-empty metadata
                collection_metadata = {"created_at": str(datetime.now()), "type": name}
            
            collection = self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_function,
                metadata=collection_metadata
            )
            logger.info(f"✅ Collection '{name}' ready (count: {collection.count()})")
            return collection
        except Exception as e:
            logger.error(f"❌ Error creating collection '{name}': {e}")
            raise
    
    def delete_collection(self, name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(name)
            logger.info(f"🗑️ Deleted collection: {name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete collection '{name}': {e}")
    
    def reset_database(self):
        """Reset entire database (use with caution!)"""
        self.client.reset()
        logger.warning("🔥 Database reset - all collections deleted")
    
    def list_collections(self) -> List[str]:
        """List all collection names"""
        collections = self.client.list_collections()
        return [col.name for col in collections]
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """
        Add documents to a collection
        
        Args:
            collection_name: Name of collection
            documents: List of text documents to embed
            metadatas: List of metadata dicts
            ids: List of unique IDs
        """
        collection = self.get_or_create_collection(collection_name)
        
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Added {len(documents)} documents to '{collection_name}'")
        except Exception as e:
            logger.error(f"❌ Error adding documents to '{collection_name}': {e}")
            raise
    
    def query_similar(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 10,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict:
        """
        Query for similar documents
        
        Args:
            collection_name: Name of collection
            query_texts: List of query texts
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter
            
        Returns:
            Query results with ids, documents, metadatas, distances
        """
        collection = self.get_or_create_collection(collection_name)
        
        try:
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            return results
        except Exception as e:
            logger.error(f"❌ Error querying '{collection_name}': {e}")
            raise
    
    def get_by_ids(
        self,
        collection_name: str,
        ids: List[str]
    ) -> Dict:
        """
        Get documents by IDs
        
        Args:
            collection_name: Name of collection
            ids: List of document IDs
            
        Returns:
            Documents with metadatas
        """
        collection = self.get_or_create_collection(collection_name)
        
        try:
            results = collection.get(ids=ids)
            return results
        except Exception as e:
            logger.error(f"❌ Error getting documents from '{collection_name}': {e}")
            raise
    
    def get_all(self, collection_name: str) -> Dict:
        """Get all documents from a collection"""
        collection = self.get_or_create_collection(collection_name)
        return collection.get()
    
    def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict]] = None
    ):
        """Update existing documents"""
        collection = self.get_or_create_collection(collection_name)
        
        try:
            collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"✅ Updated {len(ids)} documents in '{collection_name}'")
        except Exception as e:
            logger.error(f"❌ Error updating documents in '{collection_name}': {e}")
            raise
    
    def delete_documents(self, collection_name: str, ids: List[str]):
        """Delete documents by IDs"""
        collection = self.get_or_create_collection(collection_name)
        
        try:
            collection.delete(ids=ids)
            logger.info(f"🗑️ Deleted {len(ids)} documents from '{collection_name}'")
        except Exception as e:
            logger.error(f"❌ Error deleting documents from '{collection_name}': {e}")
            raise
    
    def collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics"""
        collection = self.get_or_create_collection(collection_name)
        return {
            "name": collection_name,
            "count": collection.count(),
            "metadata": collection.metadata
        }


# Singleton instance
_chroma_client = None


def get_chroma_client() -> ChromaDBClient:
    """Get singleton ChromaDB client instance"""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaDBClient()
    return _chroma_client


# Collection names (standardized)
COLLECTIONS = {
    "banking_customers": "banking_customers",
    "banking_personas": "banking_personas",
    "banking_clusters": "banking_clusters",
    "banking_products": "banking_products",
    
    "retail_customers": "retail_customers",
    "retail_personas": "retail_personas",
    "retail_clusters": "retail_clusters",
    "retail_products": "retail_products",
}


logger.info("✨ ChromaDB Client module initialized")


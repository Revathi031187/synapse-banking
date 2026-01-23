"""
ChromaDB utility for Academy Sports - Fast data retrieval
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import pandas as pd
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AcademyChromaDB:
    """Fast ChromaDB client for Academy Sports data"""
    
    def __init__(self, chroma_path: str = "./chroma_db"):
        """Initialize ChromaDB client"""
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info(f"✅ ChromaDB client initialized: {chroma_path}")
    
    def get_customers(self, version='v1', limit=None) -> pd.DataFrame:
        """
        Get customers from ChromaDB - FAST!
        
        Args:
            version: 'v1' or 'v2'
            limit: Number of customers to return (None = all)
        
        Returns:
            DataFrame of customers
        """
        try:
            collection = self.client.get_collection(f'academy_customers_{version}')
            
            # Get all customers
            if limit:
                results = collection.get(limit=limit, include=['metadatas'])
            else:
                results = collection.get(include=['metadatas'])
            
            # Convert to DataFrame
            df = pd.DataFrame(results['metadatas'])
            logger.info(f"✅ Retrieved {len(df)} customers from ChromaDB")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error retrieving customers: {e}")
            return pd.DataFrame()
    
    def get_products(self, version='v1') -> pd.DataFrame:
        """
        Get products from ChromaDB - FAST!
        
        Args:
            version: 'v1' or 'v2'
        
        Returns:
            DataFrame of products
        """
        try:
            collection = self.client.get_collection(f'academy_products_{version}')
            results = collection.get(include=['metadatas'])
            
            df = pd.DataFrame(results['metadatas'])
            logger.info(f"✅ Retrieved {len(df)} products from ChromaDB")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error retrieving products: {e}")
            return pd.DataFrame()
    
    def search_similar_customers(self, query: str, version='v1', n_results=10) -> List[Dict]:
        """
        Find similar customers using vector search - SUPER FAST!
        
        Args:
            query: Search query
            version: 'v1' or 'v2'
            n_results: Number of results
        
        Returns:
            List of similar customers
        """
        try:
            collection = self.client.get_collection(f'academy_customers_{version}')
            
            # Generate query embedding
            query_embedding = self.model.encode([query])[0]
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                include=['metadatas', 'distances']
            )
            
            customers = []
            for i, metadata in enumerate(results['metadatas'][0]):
                customer_data = {**metadata}
                customer_data['similarity_score'] = 1 - results['distances'][0][i]
                customers.append(customer_data)
            
            logger.info(f"✅ Found {len(customers)} similar customers")
            return customers
            
        except Exception as e:
            logger.error(f"❌ Error searching customers: {e}")
            return []
    
    def search_similar_products(self, query: str, version='v1', n_results=10) -> List[Dict]:
        """
        Find similar products using vector search - SUPER FAST!
        
        Args:
            query: Search query (e.g., "lightweight tent for 2 people")
            version: 'v1' or 'v2'
            n_results: Number of results
        
        Returns:
            List of similar products
        """
        try:
            collection = self.client.get_collection(f'academy_products_{version}')
            
            # Generate query embedding
            query_embedding = self.model.encode([query])[0]
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                include=['metadatas', 'distances']
            )
            
            products = []
            for i, metadata in enumerate(results['metadatas'][0]):
                products.append({
                    **metadata,
                    'similarity_score': 1 - results['distances'][0][i]
                })
            
            logger.info(f"✅ Found {len(products)} similar products")
            return products
            
        except Exception as e:
            logger.error(f"❌ Error searching products: {e}")
            return []
    
    def get_customer_by_id(self, customer_id: str, version='v1') -> Optional[Dict]:
        """
        Get specific customer - INSTANT!
        
        Args:
            customer_id: Customer ID
            version: 'v1' or 'v2'
        
        Returns:
            Customer data dict or None
        """
        try:
            collection = self.client.get_collection(f'academy_customers_{version}')
            result = collection.get(ids=[str(customer_id)], include=['metadatas'])
            
            if result['metadatas']:
                return result['metadatas'][0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting customer: {e}")
            return None
    
    def get_persona_definition(self, persona_name: str) -> Optional[Dict]:
        """
        Get persona definition - INSTANT!
        
        Args:
            persona_name: Persona name
        
        Returns:
            Persona data dict or None
        """
        try:
            collection = self.client.get_collection('academy_personas')
            result = collection.get(ids=[persona_name], include=['metadatas', 'documents'])
            
            if result['metadatas']:
                return {
                    'name': persona_name,
                    'description': result['documents'][0],
                    **result['metadatas'][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting persona: {e}")
            return None
    
    def check_collections_exist(self) -> bool:
        """Check if Academy Sports collections exist"""
        try:
            collections = self.client.list_collections()
            collection_names = [c.name for c in collections]
            
            required = [
                'academy_customers_v1',
                'academy_products_v1',
                'academy_personas'
            ]
            
            exists = all(name in collection_names for name in required)
            
            if exists:
                logger.info("✅ All Academy Sports collections exist")
            else:
                logger.warning("⚠️  Some collections missing - run initialization script")
            
            return exists
            
        except Exception as e:
            logger.error(f"❌ Error checking collections: {e}")
            return False


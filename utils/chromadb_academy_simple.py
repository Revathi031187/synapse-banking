"""
Simple ChromaDB initialization without external API dependencies
Uses basic TF-IDF for text similarity (no Together AI needed)
"""

import pandas as pd
import logging
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from utils.chromadb_client import get_chroma_client

logger = logging.getLogger(__name__)


def initialize_chromadb_simple(data_path: str = 'data/preloaded/academy_sports'):
    """
    Initialize ChromaDB with TF-IDF embeddings (no external API needed)
    
    Args:
        data_path: Path to Academy Sports data
        
    Returns:
        Initialization status
    """
    try:
        logger.info("Initializing ChromaDB with TF-IDF embeddings (no API required)...")
        
        data_path = Path(data_path)
        products_df = pd.read_csv(data_path / 'products.csv')
        
        chroma_client = get_chroma_client()
        
        # Check if collection exists
        try:
            existing = chroma_client.client.get_collection('academy_products_semantic')
            logger.info(f"Collection exists with {existing.count()} products")
            if existing.count() > 0:
                return {
                    'status': 'exists',
                    'product_count': existing.count(),
                    'message': 'ChromaDB already initialized'
                }
            chroma_client.client.delete_collection('academy_products_semantic')
        except:
            pass
        
        # Create collection
        collection = chroma_client.client.create_collection('academy_products_semantic')
        
        # Create product descriptions
        descriptions = []
        for _, p in products_df.iterrows():
            desc = f"{p['product_name']} {p['brand']} {p['main_category']}"
            descriptions.append(desc)
        
        # Generate TF-IDF embeddings (768 dimensions to match expected size)
        vectorizer = TfidfVectorizer(max_features=768)
        tfidf_matrix = vectorizer.fit_transform(descriptions)
        embeddings = tfidf_matrix.toarray().tolist()
        
        # Add to ChromaDB
        collection.add(
            ids=products_df['product_id'].tolist(),
            embeddings=embeddings,
            documents=descriptions,
            metadatas=[
                {
                    'product_id': p['product_id'],
                    'product_name': p['product_name'],
                    'brand': p['brand'],
                    'main_category': p['main_category'],
                    'subcategory': p.get('subcategory', 'General'),
                    'price': float(p['price']),
                    'avg_rating': float(p.get('avg_rating', 4.0)),
                    'num_reviews': int(p.get('num_reviews', 10)),
                    'in_stock': bool(p.get('in_stock', True))
                }
                for _, p in products_df.iterrows()
            ]
        )
        
        logger.info(f"✓ Initialized {len(products_df)} products with TF-IDF embeddings")
        
        return {
            'status': 'success',
            'product_count': len(products_df),
            'embedding_type': 'TF-IDF (local, no API)',
            'message': f'Successfully embedded {len(products_df)} products'
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    result = initialize_chromadb_simple()
    print(f"\nStatus: {result['status']}")
    print(f"Products: {result.get('product_count', 0)}")
    print(f"Type: {result.get('embedding_type', 'N/A')}")


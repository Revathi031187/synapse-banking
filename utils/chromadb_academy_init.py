"""
ChromaDB Initialization for Academy Sports Products
Handles embedding and storing products in ChromaDB for semantic search
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List
import time

from utils.chromadb_client import get_chroma_client
from utils.together_ai import TogetherAIService

logger = logging.getLogger(__name__)


class AcademyChromaDBInitializer:
    """
    Initialize and manage ChromaDB collections for Academy Sports
    """
    
    def __init__(self, data_path: str = 'data/preloaded/academy_sports'):
        self.data_path = Path(data_path)
        self.chroma_client = get_chroma_client()
        self.together_ai = TogetherAIService()
        
        logger.info(f"ChromaDB Initializer created for: {data_path}")
    
    def initialize_product_collection(
        self, 
        collection_name: str = 'academy_products_semantic',
        force_recreate: bool = False
    ) -> Dict:
        """
        Initialize product collection with embeddings
        
        Args:
            collection_name: Name of the ChromaDB collection
            force_recreate: If True, delete and recreate existing collection
            
        Returns:
            Dict with initialization status and metrics
        """
        try:
            logger.info(f"Initializing product collection: {collection_name}")
            start_time = time.time()
            
            # Load products
            products_df = pd.read_csv(self.data_path / 'products.csv')
            logger.info(f"Loaded {len(products_df)} products")
            
            # Check if collection exists
            try:
                existing_collection = self.chroma_client.client.get_collection(collection_name)
                if force_recreate:
                    logger.info(f"Deleting existing collection: {collection_name}")
                    self.chroma_client.client.delete_collection(collection_name)
                else:
                    logger.info(f"Collection {collection_name} already exists with {existing_collection.count()} items")
                    return {
                        'status': 'exists',
                        'collection_name': collection_name,
                        'product_count': existing_collection.count(),
                        'message': 'Collection already initialized'
                    }
            except:
                logger.info(f"Collection {collection_name} does not exist, will create")
            
            # Create collection
            collection = self.chroma_client.client.create_collection(
                name=collection_name,
                metadata={"description": "Academy Sports camping products with semantic embeddings"}
            )
            
            # Prepare products for embedding
            products_to_embed = []
            product_ids = []
            product_metadatas = []
            
            for _, product in products_df.iterrows():
                # Create rich text description for embedding
                description = self._create_product_description(product)
                products_to_embed.append(description)
                product_ids.append(product['product_id'])
                
                # Store metadata
                metadata = {
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'brand': product['brand'],
                    'main_category': product['main_category'],
                    'subcategory': product.get('subcategory', 'General'),
                    'price': float(product['price']),
                    'avg_rating': float(product.get('avg_rating', 4.0)),
                    'num_reviews': int(product.get('num_reviews', 10)),
                    'in_stock': bool(product.get('in_stock', True))
                }
                product_metadatas.append(metadata)
            
            # Generate embeddings in batches
            batch_size = 50
            total_embedded = 0
            
            logger.info(f"Starting embedding generation for {len(products_to_embed)} products...")
            
            for i in range(0, len(products_to_embed), batch_size):
                batch_texts = products_to_embed[i:i+batch_size]
                batch_ids = product_ids[i:i+batch_size]
                batch_meta = product_metadatas[i:i+batch_size]
                
                try:
                    # Get embeddings from Together AI (returns numpy array)
                    embeddings_array = self.together_ai.create_embeddings(batch_texts)
                    embeddings_list = embeddings_array.tolist()
                    
                    # Add to ChromaDB
                    collection.add(
                        ids=batch_ids,
                        embeddings=embeddings_list,
                        documents=batch_texts,
                        metadatas=batch_meta
                    )
                    
                    total_embedded += len(batch_ids)
                    logger.info(f"Embedded and stored batch {i//batch_size + 1}: {total_embedded}/{len(products_to_embed)} products")
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error embedding batch {i//batch_size + 1}: {e}")
                    # Continue with next batch
            
            elapsed_time = time.time() - start_time
            
            logger.info(f"✓ Product collection initialized successfully in {elapsed_time:.2f}s")
            logger.info(f"✓ Total products embedded: {total_embedded}/{len(products_to_embed)}")
            
            return {
                'status': 'success',
                'collection_name': collection_name,
                'product_count': total_embedded,
                'elapsed_time': round(elapsed_time, 2),
                'embedding_model': 'togethercomputer/m2-bert-80M-8k-retrieval',
                'message': f'Successfully embedded {total_embedded} products'
            }
            
        except Exception as e:
            logger.error(f"Error initializing product collection: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'collection_name': collection_name
            }
    
    def _create_product_description(self, product: pd.Series) -> str:
        """
        Create rich text description for product embedding
        
        Args:
            product: Product row from DataFrame
            
        Returns:
            Rich text description optimized for semantic search
        """
        # Build comprehensive description
        parts = [
            f"Product: {product['product_name']}",
            f"Brand: {product['brand']}",
            f"Category: {product['main_category']}",
        ]
        
        if 'subcategory' in product and pd.notna(product['subcategory']):
            parts.append(f"Type: {product['subcategory']}")
        
        if 'description' in product and pd.notna(product['description']):
            parts.append(f"Description: {product['description']}")
        
        # Add features if available
        feature_cols = [col for col in product.index if col.startswith('feature_')]
        if feature_cols:
            features = [product[col] for col in feature_cols if pd.notna(product[col])]
            if features:
                parts.append(f"Features: {', '.join(features)}")
        
        # Add price tier for context
        price = product['price']
        if price < 50:
            parts.append("Price tier: Budget-friendly")
        elif price < 150:
            parts.append("Price tier: Mid-range")
        elif price < 300:
            parts.append("Price tier: Premium")
        else:
            parts.append("Price tier: Luxury")
        
        # Add rating context
        if 'avg_rating' in product and pd.notna(product['avg_rating']):
            rating = product['avg_rating']
            if rating >= 4.5:
                parts.append("Highly rated product")
            elif rating >= 4.0:
                parts.append("Well-rated product")
        
        return " | ".join(parts)
    
    def test_semantic_search(
        self, 
        collection_name: str = 'academy_products_semantic',
        test_queries: List[str] = None
    ) -> Dict:
        """
        Test semantic search on product collection
        
        Args:
            collection_name: Name of collection to test
            test_queries: List of test queries (uses defaults if None)
            
        Returns:
            Test results
        """
        if test_queries is None:
            test_queries = [
                "waterproof camping tent",
                "lightweight hiking backpack",
                "warm sleeping bag for winter",
                "portable camping stove"
            ]
        
        try:
            collection = self.chroma_client.client.get_collection(collection_name)
            
            results = {}
            for query in test_queries:
                logger.info(f"Testing query: {query}")
                
                # Get embedding for query (returns numpy array for single text in list)
                query_embedding_array = self.together_ai.create_embeddings([query])
                query_embedding = query_embedding_array[0].tolist()
                
                # Search ChromaDB
                search_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=3,
                    include=['documents', 'metadatas', 'distances']
                )
                
                # Format results
                formatted_results = []
                for i in range(len(search_results['ids'][0])):
                    formatted_results.append({
                        'product_id': search_results['ids'][0][i],
                        'product_name': search_results['metadatas'][0][i]['product_name'],
                        'brand': search_results['metadatas'][0][i]['brand'],
                        'price': search_results['metadatas'][0][i]['price'],
                        'relevance_score': 1 - search_results['distances'][0][i],  # Convert distance to similarity
                        'description': search_results['documents'][0][i][:200] + '...'
                    })
                
                results[query] = formatted_results
                logger.info(f"✓ Found {len(formatted_results)} results for '{query}'")
            
            return {
                'status': 'success',
                'test_queries': test_queries,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error testing semantic search: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


def initialize_academy_chromadb(force_recreate: bool = False) -> Dict:
    """
    Convenience function to initialize Academy ChromaDB collections
    
    Args:
        force_recreate: If True, recreate collections even if they exist
        
    Returns:
        Initialization results
    """
    initializer = AcademyChromaDBInitializer()
    
    # Initialize products
    product_result = initializer.initialize_product_collection(
        force_recreate=force_recreate
    )
    
    # Test search if initialization successful
    test_result = None
    if product_result['status'] in ['success', 'exists']:
        test_result = initializer.test_semantic_search()
    
    return {
        'product_initialization': product_result,
        'search_test': test_result
    }


if __name__ == "__main__":
    print("="*70)
    print("Academy Sports ChromaDB Initializer")
    print("="*70)
    
    # Initialize collections
    results = initialize_academy_chromadb(force_recreate=False)
    
    print("\n✓ Initialization Results:")
    print(f"Products: {results['product_initialization']['status']}")
    
    if results['search_test']:
        print(f"\n✓ Search Test: {results['search_test']['status']}")
        if results['search_test']['status'] == 'success':
            print("\nSample Results:")
            for query, res in list(results['search_test']['results'].items())[:2]:
                print(f"\n  Query: '{query}'")
                for r in res[:2]:
                    print(f"    - {r['product_name']} (${r['price']}) - Relevance: {r['relevance_score']:.2%}")
    
    print("\n" + "="*70)


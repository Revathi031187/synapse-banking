"""
Agent B - Academy Sports Product Recommendations
Professional implementation with ChromaDB semantic search
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from pathlib import Path

from utils.chromadb_client import get_chroma_client
from utils.together_ai import TogetherAIService

logger = logging.getLogger(__name__)


class AgentB_Academy_Recommendations:
    """
    Professional Product Recommendation Engine for Academy Sports
    
    Features:
    1. Similar Products (based on purchase history)
    2. You Might Like (based on micro segment)
    3. Dynamic Search (semantic matching)
    """
    
    def __init__(self, data_path: str = 'data/preloaded/academy_sports'):
        self.data_path = Path(data_path)
        self.customers_df = None
        self.products_df = None
        self.purchases_df = None
        
        # ChromaDB and AI services
        self.chroma_client = get_chroma_client()
        self.together_ai = TogetherAIService()
        self.product_collection = None
        
        logger.info(f"Agent B Recommendations initialized with data path: {data_path}")
    
    def load_data(self) -> bool:
        """Load all required datasets"""
        try:
            self.customers_df = pd.read_csv(self.data_path / 'customers.csv')
            self.products_df = pd.read_csv(self.data_path / 'products.csv')
            self.purchases_df = pd.read_csv(self.data_path / 'purchases.csv')
            
            logger.info(f"✓ Loaded {len(self.customers_df)} customers, {len(self.products_df)} products, {len(self.purchases_df)} purchases")
            
            # Try to load ChromaDB collection
            try:
                self.product_collection = self.chroma_client.client.get_collection('academy_products_semantic')
                logger.info(f"✓ ChromaDB product collection loaded: {self.product_collection.count()} items")
            except Exception as e:
                logger.warning(f"ChromaDB product collection not available: {e}")
                self.product_collection = None
            
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Data files not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def get_customer_price_range(self, customer_id: str) -> Tuple[float, float]:
        """
        Calculate personalized price range for a customer (±50% of avg)
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Tuple of (min_price, max_price)
        """
        customer_purchases = self.purchases_df[self.purchases_df['customer_id'] == customer_id]
        
        if customer_purchases.empty:
            # Default wide range for new customers
            return 20.0, 500.0
        
        avg_price = customer_purchases['price_paid'].mean()
        min_price = max(10.0, avg_price * 0.5)
        max_price = avg_price * 1.5
        
        return min_price, max_price
    
    def filter_and_score_products(
        self, 
        candidate_products: pd.DataFrame,
        customer_id: str,
        exclude_purchased: bool = True,
        reason: str = ""
    ) -> List[Dict]:
        """
        Filter products by price range and score them
        
        Args:
            candidate_products: DataFrame of candidate products
            customer_id: Customer identifier
            exclude_purchased: Whether to exclude already-purchased products
            reason: Recommendation reason
            
        Returns:
            List of top 3 scored products
        """
        if candidate_products.empty:
            return []
        
        # Get price range
        min_price, max_price = self.get_customer_price_range(customer_id)
        
        # Filter by price
        filtered = candidate_products[
            (candidate_products['price'] >= min_price) & 
            (candidate_products['price'] <= max_price)
        ].copy()
        
        # Exclude purchased products
        if exclude_purchased:
            purchased_ids = self.purchases_df[
                self.purchases_df['customer_id'] == customer_id
            ]['product_id'].unique()
            filtered = filtered[~filtered['product_id'].isin(purchased_ids)]
        
        if filtered.empty:
            return []
        
        # Score products
        # Higher rating and moderate price (within range) get better scores
        filtered['rating_score'] = filtered['avg_rating'] / 5.0  # Normalize to 0-1
        filtered['price_score'] = 1 - ((filtered['price'] - min_price) / (max_price - min_price + 1e-6))
        filtered['review_score'] = np.log1p(filtered['num_reviews']) / np.log1p(filtered['num_reviews'].max() + 1)
        
        # Weighted combination
        filtered['final_score'] = (
            filtered['rating_score'] * 0.4 +
            filtered['price_score'] * 0.3 +
            filtered['review_score'] * 0.3
        )
        
        # Get top 3
        top_products = filtered.nlargest(3, 'final_score')
        
        # Format results
        results = []
        for _, product in top_products.iterrows():
            results.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'brand': product['brand'],
                'main_category': product['main_category'],
                'subcategory': product.get('subcategory', 'General'),
                'price': round(float(product['price']), 2),
                'avg_rating': round(float(product['avg_rating']), 1),
                'num_reviews': int(product['num_reviews']),
                'in_stock': bool(product.get('in_stock', True)),
                'recommendation_score': round(float(product['final_score']), 3),
                'reason': reason or f"Matches your preferences (${min_price:.0f}-${max_price:.0f} range)"
            })
        
        return results
    
    def get_similar_products(self, customer_id: str) -> List[Dict]:
        """
        Recommend products similar to customer's purchase history
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of recommended products
        """
        if not self.load_data():
            return []
        
        # Get customer's purchase history
        customer_purchases = self.purchases_df[self.purchases_df['customer_id'] == customer_id]
        
        if customer_purchases.empty:
            logger.info(f"No purchase history for customer {customer_id}")
            return []
        
        # Get purchased products details
        purchased_product_ids = customer_purchases['product_id'].unique()
        purchased_products = self.products_df[self.products_df['product_id'].isin(purchased_product_ids)]
        
        if purchased_products.empty:
            return []
        
        # Find similar products by category, subcategory, and brand
        main_categories = purchased_products['main_category'].unique()
        subcategories = purchased_products['subcategory'].unique() if 'subcategory' in purchased_products.columns else []
        brands = purchased_products['brand'].unique()
        
        # Build candidate pool
        candidates = self.products_df[
            (self.products_df['main_category'].isin(main_categories)) |
            (self.products_df['subcategory'].isin(subcategories) if len(subcategories) > 0 else False) |
            (self.products_df['brand'].isin(brands))
        ]
        
        reason = f"Similar to your {main_categories[0]} purchases"
        
        return self.filter_and_score_products(
            candidates,
            customer_id,
            exclude_purchased=True,
            reason=reason
        )
    
    def get_you_might_like(
        self, 
        customer_id: str, 
        micro_segment_customer_ids: List[str] = None
    ) -> List[Dict]:
        """
        Recommend popular products within customer's micro segment
        
        Args:
            customer_id: Customer identifier
            micro_segment_customer_ids: List of customer IDs in same micro segment
            
        Returns:
            List of recommended products
        """
        if not self.load_data():
            return []
        
        if not micro_segment_customer_ids:
            logger.info(f"No micro segment data for customer {customer_id}")
            return []
        
        # Get popular products in the segment
        segment_purchases = self.purchases_df[
            self.purchases_df['customer_id'].isin(micro_segment_customer_ids)
        ]
        
        if segment_purchases.empty:
            return []
        
        # Count product popularity
        product_popularity = segment_purchases['product_id'].value_counts()
        popular_product_ids = product_popularity.head(20).index  # Top 20
        
        # Get product details
        candidates = self.products_df[self.products_df['product_id'].isin(popular_product_ids)]
        
        reason = "Popular with customers like you"
        
        return self.filter_and_score_products(
            candidates,
            customer_id,
            exclude_purchased=True,
            reason=reason
        )
    
    def get_search_based_recommendations(
        self, 
        customer_id: str, 
        search_term: str
    ) -> List[Dict]:
        """
        Semantic search-based recommendations using ChromaDB
        
        Args:
            customer_id: Customer identifier
            search_term: Customer search query
            
        Returns:
            List of recommended products
        """
        if not self.load_data():
            return []
        
        if not search_term or not search_term.strip():
            return []
        
        # Get price range for filtering
        min_price, max_price = self.get_customer_price_range(customer_id)
        
        # Try ChromaDB semantic search first
        if self.product_collection:
            try:
                # Get query embedding (returns numpy array)
                query_embedding_array = self.together_ai.create_embeddings([search_term])
                query_embedding = query_embedding_array[0].tolist()
                
                # Search with price filter
                results = self.product_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=10,
                    where={
                        "$and": [
                            {"price": {"$gte": min_price}},
                            {"price": {"$lte": max_price}}
                        ]
                    },
                    include=['metadatas', 'distances']
                )
                
                # Format results
                recommendations = []
                for i in range(len(results['ids'][0])):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    relevance = 1 - (distance / 2)  # Convert to 0-1 score
                    
                    recommendations.append({
                        'product_id': metadata['product_id'],
                        'product_name': metadata['product_name'],
                        'brand': metadata['brand'],
                        'main_category': metadata['main_category'],
                        'subcategory': metadata.get('subcategory', 'General'),
                        'price': round(float(metadata['price']), 2),
                        'avg_rating': round(float(metadata['avg_rating']), 1),
                        'num_reviews': int(metadata['num_reviews']),
                        'in_stock': bool(metadata.get('in_stock', True)),
                        'recommendation_score': round(relevance, 3),
                        'reason': f"Matches your search: '{search_term}'"
                    })
                
                logger.info(f"✓ ChromaDB semantic search found {len(recommendations)} results for '{search_term}'")
                return recommendations[:3]
                
            except Exception as e:
                logger.error(f"ChromaDB search failed: {e}, falling back to keyword search")
        
        # Fallback: Keyword-based search
        search_lower = search_term.lower()
        candidates = self.products_df[
            self.products_df['product_name'].str.lower().str.contains(search_lower, na=False) |
            self.products_df['main_category'].str.lower().str.contains(search_lower, na=False) |
            self.products_df['brand'].str.lower().str.contains(search_lower, na=False)
        ]
        
        reason = f"Keyword match: '{search_term}'"
        
        return self.filter_and_score_products(
            candidates,
            customer_id,
            exclude_purchased=False,  # Show all matches for search
            reason=reason
        )
    
    def get_all_recommendations(self, customer_id: str, micro_segment_customer_ids: List[str] = None) -> Dict:
        """
        Get all three types of recommendations for a customer
        
        Args:
            customer_id: Customer identifier
            micro_segment_customer_ids: List of customer IDs in same micro segment
            
        Returns:
            Dictionary with all recommendation types
        """
        return {
            'customer_id': customer_id,
            'similar_products': self.get_similar_products(customer_id),
            'you_might_like': self.get_you_might_like(customer_id, micro_segment_customer_ids),
            'recommendation_metadata': {
                'price_range': self.get_customer_price_range(customer_id),
                'has_chromadb': self.product_collection is not None
            }
        }
    
    def get_new_visitor_recommendations(self) -> Dict:
        """
        Generic recommendations for new visitors without profile
        
        Returns:
            Dictionary with various recommendation types
        """
        if not self.load_data():
            return {}
        
        # Top selling products
        top_selling_ids = self.purchases_df['product_id'].value_counts().head(3).index
        top_selling = self.products_df[self.products_df['product_id'].isin(top_selling_ids)]
        
        # Top rated products
        top_rated = self.products_df.nlargest(3, 'avg_rating')
        
        # Trending (most recent purchases)
        if 'purchase_date' in self.purchases_df.columns:
            self.purchases_df['purchase_date'] = pd.to_datetime(self.purchases_df['purchase_date'])
            recent_purchases = self.purchases_df.nlargest(100, 'purchase_date')
            trending_ids = recent_purchases['product_id'].value_counts().head(3).index
            trending = self.products_df[self.products_df['product_id'].isin(trending_ids)]
        else:
            trending = self.products_df.sample(min(3, len(self.products_df)))
        
        def format_products(df):
            return [
                {
                    'product_id': row['product_id'],
                    'product_name': row['product_name'],
                    'brand': row['brand'],
                    'main_category': row['main_category'],
                    'price': round(float(row['price']), 2),
                    'avg_rating': round(float(row.get('avg_rating', 4.0)), 1),
                    'num_reviews': int(row.get('num_reviews', 10)),
                    'in_stock': bool(row.get('in_stock', True))
                }
                for _, row in df.iterrows()
            ]
        
        return {
            'top_selling': format_products(top_selling),
            'top_rated': format_products(top_rated),
            'trending': format_products(trending)
        }


if __name__ == "__main__":
    print("="*70)
    print("Agent B - Academy Sports Product Recommendations")
    print("="*70)
    print("Professional recommendation engine with ChromaDB semantic search")
    print("="*70)
    
    # Test recommendations
    agent = AgentB_Academy_Recommendations()
    if agent.load_data():
        test_customer = agent.customers_df.iloc[0]['customer_id']
        print(f"\nTesting recommendations for customer: {test_customer}")
        
        recs = agent.get_all_recommendations(test_customer)
        print(f"\n✓ Similar Products: {len(recs['similar_products'])}")
        print(f"✓ You Might Like: {len(recs['you_might_like'])}")
        print(f"✓ ChromaDB Available: {recs['recommendation_metadata']['has_chromadb']}")


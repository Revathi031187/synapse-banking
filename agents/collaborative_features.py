"""
Collaborative Features Module
Adds collaborative filtering signals to enhance ML recommendations
WITHOUT building a full CF system.

These features complement the existing logit model:
- Persona-level popularity
- Customer similarity signals
- Product co-occurrence patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class CollaborativeFeatureEngineer:
    """
    Lightweight collaborative features that enhance existing ML models
    """
    
    def __init__(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        purchases_df: pd.DataFrame
    ):
        self.customers_df = customers_df
        self.products_df = products_df
        self.purchases_df = purchases_df
        
        # Precompute collaborative signals
        self._compute_popularity_scores()
        self._compute_cooccurrence_matrix()
        self._compute_category_affinity()
        
    def _compute_popularity_scores(self):
        """
        Calculate product popularity at different levels:
        - Overall popularity
        - Category-level popularity
        - Persona-level popularity (if persona info available)
        """
        # Overall product purchase frequency
        product_counts = self.purchases_df.groupby('product_id').size()
        total_purchases = len(self.purchases_df)
        
        self.product_popularity = (product_counts / total_purchases).to_dict()
        
        # Category-level popularity (normalized within category)
        product_category = self.products_df.set_index('product_id')['main_category'].to_dict()
        
        purchases_with_category = self.purchases_df.copy()
        purchases_with_category['category'] = purchases_with_category['product_id'].map(product_category)
        
        category_counts = purchases_with_category.groupby(['category', 'product_id']).size().reset_index(name='count')
        category_totals = purchases_with_category.groupby('category').size().to_dict()
        
        category_counts['category_popularity'] = category_counts.apply(
            lambda row: row['count'] / category_totals.get(row['category'], 1),
            axis=1
        )
        
        self.category_popularity = dict(zip(
            category_counts['product_id'],
            category_counts['category_popularity']
        ))
        
        logger.info(f"✅ Computed popularity scores for {len(self.product_popularity)} products")
        
    def _compute_cooccurrence_matrix(self):
        """
        Calculate product co-occurrence:
        "Customers who bought product A also bought product B"
        """
        # Group purchases by customer
        customer_products = self.purchases_df.groupby('customer_id')['product_id'].apply(set).to_dict()
        
        # Count co-occurrences
        cooccurrence = {}
        
        for customer_id, products in customer_products.items():
            products_list = list(products)
            for i, prod_a in enumerate(products_list):
                if prod_a not in cooccurrence:
                    cooccurrence[prod_a] = {}
                    
                for prod_b in products_list[i+1:]:
                    # Bidirectional co-occurrence
                    cooccurrence[prod_a][prod_b] = cooccurrence[prod_a].get(prod_b, 0) + 1
                    
                    if prod_b not in cooccurrence:
                        cooccurrence[prod_b] = {}
                    cooccurrence[prod_b][prod_a] = cooccurrence[prod_b].get(prod_a, 0) + 1
        
        self.cooccurrence_matrix = cooccurrence
        logger.info(f"✅ Computed co-occurrence matrix for {len(cooccurrence)} products")
        
    def _compute_category_affinity(self):
        """
        Calculate customer-category affinity:
        "This customer buys from Hiking Backpacks 60% of the time"
        """
        # Merge purchases with product categories
        purchases_with_cat = self.purchases_df.merge(
            self.products_df[['product_id', 'main_category']],
            on='product_id',
            how='left'
        )
        
        # Count purchases per customer-category
        customer_category_counts = purchases_with_cat.groupby(
            ['customer_id', 'main_category']
        ).size().reset_index(name='count')
        
        # Total purchases per customer
        customer_totals = purchases_with_cat.groupby('customer_id').size().to_dict()
        
        # Calculate affinity (percentage)
        customer_category_counts['affinity'] = customer_category_counts.apply(
            lambda row: row['count'] / customer_totals.get(row['customer_id'], 1),
            axis=1
        )
        
        # Store as nested dict: {customer_id: {category: affinity}}
        self.category_affinity = {}
        for _, row in customer_category_counts.iterrows():
            cid = row['customer_id']
            cat = row['main_category']
            affinity = row['affinity']
            
            if cid not in self.category_affinity:
                self.category_affinity[cid] = {}
            self.category_affinity[cid][cat] = affinity
        
        logger.info(f"✅ Computed category affinity for {len(self.category_affinity)} customers")
    
    def get_collaborative_features(
        self,
        customer_id: str,
        product_id: str,
        customer_purchase_history: List[str] = None
    ) -> Dict[str, float]:
        """
        Extract collaborative features for a single customer-product pair
        
        Returns dict with keys:
        - product_popularity_overall: Global popularity (0-1)
        - product_popularity_in_category: Popularity within category (0-1)
        - customer_category_affinity: How much customer likes this category (0-1)
        - cooccurrence_score: Avg co-occurrence with customer's past purchases (0-1)
        - complementary_score: How often this product is bought with items in same category
        """
        features = {}
        
        # Feature 1: Overall popularity
        features['product_popularity_overall'] = self.product_popularity.get(product_id, 0.0)
        
        # Feature 2: Category-level popularity
        features['product_popularity_in_category'] = self.category_popularity.get(product_id, 0.0)
        
        # Feature 3: Customer-category affinity
        product_category = self.products_df.set_index('product_id').loc[product_id, 'main_category']
        customer_affinities = self.category_affinity.get(customer_id, {})
        features['customer_category_affinity'] = customer_affinities.get(product_category, 0.0)
        
        # Feature 4: Co-occurrence score with customer's purchase history
        if customer_purchase_history:
            cooccurrence_scores = []
            for past_product in customer_purchase_history:
                if past_product in self.cooccurrence_matrix:
                    cooccur_count = self.cooccurrence_matrix[past_product].get(product_id, 0)
                    cooccurrence_scores.append(cooccur_count)
            
            features['cooccurrence_score'] = np.mean(cooccurrence_scores) if cooccurrence_scores else 0.0
        else:
            features['cooccurrence_score'] = 0.0
        
        # Feature 5: Complementary score (co-occurrence with products in same category)
        if product_id in self.cooccurrence_matrix:
            same_category_products = self.products_df[
                self.products_df['main_category'] == product_category
            ]['product_id'].values
            
            complementary_scores = [
                self.cooccurrence_matrix[product_id].get(other_prod, 0)
                for other_prod in same_category_products
                if other_prod != product_id
            ]
            
            features['complementary_score'] = np.mean(complementary_scores) if complementary_scores else 0.0
        else:
            features['complementary_score'] = 0.0
        
        return features
    
    def get_persona_level_features(
        self,
        product_id: str,
        persona_customers: List[str]
    ) -> Dict[str, float]:
        """
        Calculate persona-level collaborative features
        
        "What % of customers in this persona bought this product?"
        "How popular is this product among persona members?"
        """
        features = {}
        
        # Get purchases by persona members
        persona_purchases = self.purchases_df[
            self.purchases_df['customer_id'].isin(persona_customers)
        ]
        
        # Feature 1: Persona purchase rate
        customers_who_bought = persona_purchases[
            persona_purchases['product_id'] == product_id
        ]['customer_id'].nunique()
        
        features['persona_purchase_rate'] = customers_who_bought / max(len(persona_customers), 1)
        
        # Feature 2: Persona-level popularity rank
        persona_product_counts = persona_purchases.groupby('product_id').size()
        product_rank = (
            persona_product_counts.rank(ascending=False, method='min')
            .get(product_id, len(persona_product_counts) + 1)
        )
        features['persona_popularity_rank'] = 1 - (product_rank / max(len(persona_product_counts), 1))
        
        return features


# Example usage in logit_recommendation_model.py
"""
# In _extract_features():

# Initialize collaborative features
collab_engineer = CollaborativeFeatureEngineer(customers_df, products_df, purchases_df)

# Add collaborative features to each customer-product pair
for idx, row in features_df.iterrows():
    cid = row['customer_id']
    pid = row['product_id']
    
    # Get customer's purchase history
    past_purchases = purchases_df[purchases_df['customer_id'] == cid]['product_id'].tolist()
    
    # Extract collaborative features
    collab_features = collab_engineer.get_collaborative_features(cid, pid, past_purchases)
    
    # Add to features_df
    for feat_name, feat_value in collab_features.items():
        features_df.at[idx, feat_name] = feat_value

# Add to feature_cols list:
feature_cols.extend([
    'product_popularity_overall',
    'product_popularity_in_category',
    'customer_category_affinity',
    'cooccurrence_score',
    'complementary_score'
])
"""

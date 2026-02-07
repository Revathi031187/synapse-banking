"""
Agent B Banking Enhanced V2 - Complete Agentic AI Rebuild
Main orchestrator for banking product recommendations

Provides three recommendation types:
1. Persona-Aligned: Based on segment characteristics (PRIMARY)
2. Similar Products: Based on transaction history
3. Segment Popular: Most adopted in customer's segment

Architecture:
- Uses Banking12FactorScorer for all scoring
- Uses BankingPersonaAlignedRecommender for persona-based recs
- Integrates Together AI for on-demand explanations
- Matches Academy Sports proven patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from agents.banking_12_factor_scorer import Banking12FactorScorer
from agents.agent_b_banking_persona_aligned import BankingPersonaAlignedRecommender

logger = logging.getLogger(__name__)


class AgentB_Banking_Enhanced:
    """
    Enhanced Banking Product Recommendation Agent (V2)
    
    Provides three recommendation types:
    1. Persona-Aligned: Based on segment characteristics
    2. Similar Products: Based on transaction history
    3. Segment Popular: Most adopted in customer's segment
    """
    
    def __init__(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
        personas: Dict,
        agent_a = None
    ):
        """
        Initialize Enhanced Recommendation Agent V2
        
        Args:
            customers_df: Customer data with segment assignments
            products_df: Product catalog
            transactions_df: Transaction history
            personas: Persona definitions from Agent A
            agent_a: Agent A instance (optional)
        """
        self.customers_df = customers_df
        self.products_df = products_df
        self.transactions_df = transactions_df
        self.personas = personas
        self.agent_a = agent_a
        
        # Initialize persona-aligned recommender
        self.persona_recommender = BankingPersonaAlignedRecommender(
            customers_df=customers_df,
            products_df=products_df,
            transactions_df=transactions_df,
            personas=personas
        )
        
        # Initialize scorer (used for similar products and segment popular)
        self.scorer = Banking12FactorScorer(
            customers_df=customers_df,
            products_df=products_df,
            transactions_df=transactions_df,
            personas=personas
        )
        
        logger.info("✅ Banking Agent B Enhanced V2 initialized (Agentic AI)")
        logger.info(f"  - Persona-aligned recommendations: ✓")
        logger.info(f"  - Banking 12-factor scoring: ✓")
        logger.info(f"  - Together AI explanations: ✓")
        logger.info(f"  - {len(personas)} personas loaded")
        logger.info(f"  - {len(customers_df)} customers")
        logger.info(f"  - {len(products_df)} products")
    
    def get_recommendations(
        self,
        customer_id: str,
        recommendation_type: str = 'persona_aligned',
        n_recommendations: int = 3
    ) -> Dict:
        """
        Main recommendation method.
        
        Args:
            customer_id: Customer ID
            recommendation_type: 'persona_aligned', 'similar_products', 'segment_popular'
            n_recommendations: Number of recommendations
            
        Returns:
            Dict with recommendations and metadata
        """
        if recommendation_type == 'persona_aligned':
            return self.persona_recommender.get_persona_aligned_recommendations(
                customer_id=customer_id,
                n_recommendations=n_recommendations
            )
        elif recommendation_type == 'similar_products':
            return self._get_similar_products(customer_id, n_recommendations)
        elif recommendation_type == 'segment_popular':
            return self._get_segment_popular(customer_id, n_recommendations)
        else:
            raise ValueError(f"Unknown recommendation type: {recommendation_type}")
    
    def _get_similar_products(self, customer_id: str, n: int) -> Dict:
        """
        Rule-based similar products recommendation.
        Based on transaction history and product categories.
        """
        try:
            # Get customer
            customer = self.customers_df[self.customers_df['customer_id'] == customer_id]
            if len(customer) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'Customer not found',
                    'type': 'similar_products'
                }
            
            customer = customer.iloc[0]
            
            # Get customer's current products
            customer_transactions = self.transactions_df[
                self.transactions_df['customer_id'] == customer_id
            ] if 'product_id' in self.transactions_df.columns else pd.DataFrame()
            
            if len(customer_transactions) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'No transaction history',
                    'type': 'similar_products'
                }
            
            # Get product categories from transactions
            current_product_ids = customer_transactions['product_id'].unique()
            current_products = self.products_df[
                self.products_df['product_id'].isin(current_product_ids)
            ]
            
            # Find complementary products
            complementary = self._find_complementary_products(current_products)
            
            # Remove products customer already has
            complementary = complementary[
                ~complementary['product_id'].isin(current_product_ids)
            ]
            
            if len(complementary) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'No complementary products available',
                    'type': 'similar_products'
                }
            
            # Score and rank using 12-factor scorer
            scored = []
            persona = None
            persona_id = customer.get('cluster', customer.get('macro_segment_id'))
            if persona_id is not None and persona_id in self.personas:
                persona = self.personas[persona_id]
            
            for _, product in complementary.iterrows():
                score_breakdown = self.scorer.score_product(
                    customer=customer.to_dict(),
                    product=product.to_dict(),
                    persona=persona
                )
                scored.append({
                    'product': product,
                    'score': score_breakdown['total_score'],
                    'breakdown': score_breakdown
                })
            
            # Return top N
            scored.sort(key=lambda x: x['score'], reverse=True)
            top_n = scored[:n]
            
            # Format
            formatted = self._format_recommendations(top_n, 'similar_products')
            
            return {
                'customer_id': customer_id,
                'recommendations': formatted,
                'type': 'similar_products',
                'count': len(formatted)
            }
            
        except Exception as e:
            logger.error(f"Error in _get_similar_products: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'customer_id': customer_id,
                'recommendations': [],
                'error': str(e),
                'type': 'similar_products'
            }
    
    def _find_complementary_products(self, current_products: pd.DataFrame) -> pd.DataFrame:
        """Find products that pair well with current products."""
        
        pairing_rules = {
            'Checking': ['Savings', 'Credit_Card', 'Investment', 'Debit_Card'],
            'Savings': ['CD', 'Investment', 'Retirement_IRA', 'Money_Market'],
            'Credit_Card': ['Loan', 'Investment', 'Line_of_Credit'],
            'Loan': ['Insurance', 'Investment', 'Refinance'],
            'Mortgage': ['Home_Equity_Line', 'Insurance', 'Investment', 'Refinance'],
            'Investment': ['Retirement_IRA', 'Wealth_Management', 'CD'],
            'Business_Checking': ['Business_Loan', 'Merchant_Services', 'Payroll'],
            'Agricultural_Loan': ['Crop_Insurance', 'Equipment_Financing', 'Operating_Line']
        }
        
        complementary_categories = set()
        for _, product in current_products.iterrows():
            category = product.get('category', product.get('subcategory', ''))
            if category in pairing_rules:
                complementary_categories.update(pairing_rules[category])
        
        # Filter to complementary products
        if complementary_categories:
            complementary = self.products_df[
                self.products_df['category'].isin(complementary_categories) |
                self.products_df.get('subcategory', pd.Series()).isin(complementary_categories)
            ]
        else:
            # If no rules match, return empty
            complementary = pd.DataFrame(columns=self.products_df.columns)
        
        return complementary
    
    def _get_segment_popular(self, customer_id: str, n: int) -> Dict:
        """
        Get products popular in customer's segment.
        """
        try:
            # Get customer
            customer = self.customers_df[self.customers_df['customer_id'] == customer_id]
            if len(customer) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'Customer not found',
                    'type': 'segment_popular'
                }
            
            customer = customer.iloc[0]
            persona_id = customer.get('cluster', customer.get('macro_segment_id'))
            
            if persona_id is None:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'No segment assignment',
                    'type': 'segment_popular'
                }
            
            # Get customers in same segment
            segment_customers = self.customers_df[
                self.customers_df['cluster'] == persona_id
            ]['customer_id'].values
            
            # Get products popular in this segment
            if 'product_id' not in self.transactions_df.columns:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'No transaction data',
                    'type': 'segment_popular'
                }
            
            segment_transactions = self.transactions_df[
                self.transactions_df['customer_id'].isin(segment_customers)
            ]
            product_popularity = segment_transactions['product_id'].value_counts()
            
            # Get customer's existing products
            customer_products = self.transactions_df[
                self.transactions_df['customer_id'] == customer_id
            ]['product_id'].unique()
            
            # Recommend popular products customer doesn't have
            recommended_product_ids = [
                pid for pid in product_popularity.index 
                if pid not in customer_products
            ][:n * 2]  # Get extra for filtering
            
            # Score these products
            persona = self.personas.get(persona_id, {})
            scored = []
            
            for product_id in recommended_product_ids:
                product = self.products_df[self.products_df['product_id'] == product_id]
                if len(product) > 0:
                    product = product.iloc[0]
                    
                    score_breakdown = self.scorer.score_product(
                        customer=customer.to_dict(),
                        product=product.to_dict(),
                        persona=persona
                    )
                    
                    scored.append({
                        'product': product,
                        'score': score_breakdown['total_score'],
                        'breakdown': score_breakdown,
                        'popularity': int(product_popularity[product_id])
                    })
            
            # Sort by score and take top N
            scored.sort(key=lambda x: x['score'], reverse=True)
            top_n = scored[:n]
            
            # Format
            formatted = self._format_recommendations(top_n, 'segment_popular')
            
            return {
                'customer_id': customer_id,
                'recommendations': formatted,
                'type': 'segment_popular',
                'segment_id': int(persona_id),
                'count': len(formatted)
            }
            
        except Exception as e:
            logger.error(f"Error in _get_segment_popular: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'customer_id': customer_id,
                'recommendations': [],
                'error': str(e),
                'type': 'segment_popular'
            }
    
    def _format_recommendations(
        self,
        recommendations: List[Dict],
        rec_type: str
    ) -> List[Dict]:
        """
        Format recommendations with reasoning
        """
        formatted = []
        
        for item in recommendations:
            product = item['product']
            breakdown = item['breakdown']
            
            # Build reasoning based on type
            if rec_type == 'similar_products':
                pairing_info = breakdown.get('product_pairing', {})
                pairs_with = pairing_info.get('pairs_with', [])
                if pairs_with:
                    reason = f"Complements your existing {', '.join(pairs_with[:2])} products"
                else:
                    reason = "Recommended based on your current banking relationship"
            elif rec_type == 'segment_popular':
                popularity = item.get('popularity', 0)
                reason = f"Popular in your segment ({popularity} customers have this)"
            else:
                reason = "Recommended for your financial profile"
            
            formatted.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'category': product.get('category', 'Unknown'),
                'annual_fee': float(product.get('annual_fee', 0)),
                'min_balance': float(product.get('min_balance', 0)),
                'interest_rate_apy': float(product.get('interest_rate_apy', product.get('interest_rate', 0))),
                'score': item['score'],
                'reasoning': reason,
                'score_breakdown': breakdown,
                'ai_explanation': None  # Generated on-demand
            })
        
        return formatted
    
    def get_all_recommendations(
        self,
        customer_id: str,
        search_term: str = None,
        chromadb_collection = None
    ) -> Dict:
        """
        Get all types of recommendations for a customer
        
        Args:
            customer_id: Customer ID
            search_term: Optional search term (not used in v2)
            chromadb_collection: Optional ChromaDB collection (not used in v2)
            
        Returns:
            Dictionary with all recommendation types
        """
        try:
            # Get customer info
            customer = self.customers_df[self.customers_df['customer_id'] == customer_id]
            if len(customer) == 0:
                return {
                    'error': 'Customer not found',
                    'customer_id': customer_id
                }
            
            customer = customer.iloc[0]
            
            # Get different types of recommendations
            persona_aligned = self.get_recommendations(
                customer_id, 'persona_aligned', n_recommendations=5
            )
            similar = self.get_recommendations(
                customer_id, 'similar_products', n_recommendations=5
            )
            segment = self.get_recommendations(
                customer_id, 'segment_popular', n_recommendations=5
            )
            
            # Use persona-aligned as primary (tailored recommendations)
            tailored = persona_aligned.get('recommendations', [])
            
            # Build result
            result = {
                'customer_id': customer_id,
                'customer_segment': customer.get('customer_segment', 'Personal'),
                'tailored_recommendations': tailored,
                'similar_products': similar.get('recommendations', []),
                'segment_recommendations': segment.get('recommendations', []),
                'customer_info': {
                    'name': customer.get('customer_name', 'Unknown'),
                    'total_deposits': float(customer.get('total_deposits', 0)),
                    'num_products': int(customer.get('num_products', 0)),
                    'credit_score': int(customer.get('credit_score', 700)),
                    'customer_type': customer.get('customer_type', 'Unknown')
                },
                'recommendation_metadata': {
                    'similar_count': len(similar.get('recommendations', [])),
                    'segment_count': len(segment.get('recommendations', [])),
                    'total_count': len(tailored),
                    'scoring_method': 'banking_12_factor',
                    'method': 'persona_aligned'
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in get_all_recommendations: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'error': str(e),
                'customer_id': customer_id,
                'tailored_recommendations': [],
                'similar_products': [],
                'segment_recommendations': []
            }


if __name__ == "__main__":
    logger.info("Agent B Banking Enhanced V2 - Agentic AI Product Recommendations")

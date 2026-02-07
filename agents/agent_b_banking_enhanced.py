"""
Agent B Banking Enhanced - Banking Product Recommendations for Customer Modal
Provides detailed product recommendations for customer insight modals
Adapted from agent_b_academy_enhanced.py for banking domain
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from pathlib import Path
from agents.banking_12_factor_scorer import Banking12FactorScorer

logger = logging.getLogger(__name__)


class AgentB_Banking_Enhanced:
    """
    Enhanced Banking Product Recommendation Agent
    
    Provides personalized banking product recommendations using:
    - Transaction history analysis
    - Segment-based collaborative filtering  
    - Banking 12-Factor scoring
    """
    
    def __init__(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
        micro_segments: Dict = None,
        personas: Dict = None
    ):
        """
        Initialize Enhanced Banking Recommendation Agent
        
        Args:
            customers_df: Customer data with segment assignments
            products_df: Banking product catalog
            transactions_df: Transaction history
            micro_segments: Micro segment assignments (optional)
            personas: Persona definitions from Agent A (optional)
        """
        self.customers_df = customers_df
        self.products_df = products_df
        self.transactions_df = transactions_df
        self.micro_segments = micro_segments or {}
        self.personas = personas or {}
        
        # Initialize Banking 12-Factor Scorer
        try:
            print("\n🔍 [Banking Enhanced Agent] Initializing 12-factor scorer...")
            self.banking_scorer = Banking12FactorScorer(
                customers_df=customers_df,
                products_df=products_df,
                transactions_df=transactions_df,
                personas=personas
            )
            print("✅ [Banking Enhanced Agent] 12-factor scorer initialized!")
            logger.info(f"✅ Initialized Banking 12-Factor Scorer")
        except Exception as e:
            print(f"❌ [Banking Enhanced Agent] Failed to init 12-factor scorer: {e}")
            self.banking_scorer = None
            logger.warning(f"⚠️ Could not initialize Banking 12-factor scorer: {e}")
        
        logger.info(f"Banking Enhanced Recommendation Agent initialized")
        logger.info(f"  - {len(customers_df)} customers")
        logger.info(f"  - {len(products_df)} banking products")
        logger.info(f"  - {len(transactions_df)} transactions")
        logger.info(f"  - {len(personas)} personas")
    
    def get_customer_recommendations(
        self,
        customer_id: str,
        n_recommendations: int = 3
    ) -> Dict:
        """
        Get banking product recommendations for a specific customer
        
        Logic:
        - Analyze customer's financial profile and existing products
        - Find suitable products based on eligibility, financial needs
        - Score using Banking 12-Factor system
        - Return top N products with detailed explanations
        
        Args:
            customer_id: Customer ID
            n_recommendations: Number of recommendations (default 3)
            
        Returns:
            Dictionary with recommendations and detailed scoring
        """
        try:
            # Get customer data
            customer = self.customers_df[
                self.customers_df['customer_id'] == customer_id
            ]
            
            if len(customer) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'Customer not found',
                    'type': 'customer_recommendations'
                }
            
            customer = customer.iloc[0].to_dict()
            
            # Get persona info
            persona_info = {}
            if 'cluster' in customer and customer['cluster'] in self.personas:
                persona_info = self.personas[customer['cluster']]
            
            # Get customer's existing products from transactions
            customer_transactions = self.transactions_df[
                self.transactions_df['customer_id'] == customer_id
            ]
            owned_product_ids = customer_transactions['product_id'].unique()
            
            # Filter eligible products
            candidates = self.products_df.copy()
            
            # 1. Filter by customer segment
            customer_segment = customer.get('customer_segment', 'Personal')
            if 'category' in candidates.columns:
                candidates = candidates[
                    candidates['category'] == customer_segment
                ]
            
            # 2. Filter by credit score eligibility
            customer_credit = customer.get('credit_score', 700)
            if 'min_credit_score' in candidates.columns:
                candidates = candidates[
                    (candidates['min_credit_score'].isna()) |
                    (candidates['min_credit_score'] <= customer_credit + 30)
                ]
            
            # 3. Filter by fee affordability
            customer_deposits = customer.get('total_deposits', 50000)
            max_fee = customer_deposits * 0.015  # 1.5% of deposits
            if 'annual_fee' in candidates.columns:
                candidates = candidates[
                    (candidates['annual_fee'].isna()) |
                    (candidates['annual_fee'] <= max_fee)
                ]
            
            # 4. Exclude already owned products
            candidates = candidates[
                ~candidates['product_id'].isin(owned_product_ids)
            ]
            
            if len(candidates) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'No eligible products available',
                    'type': 'customer_recommendations'
                }
            
            # Score products using Banking 12-Factor
            if self.banking_scorer:
                scored_products = []
                for _, product_row in candidates.iterrows():
                    product = product_row.to_dict()
                    try:
                        detailed = self.banking_scorer.score_product(
                            customer=customer,
                            product=product,
                            persona=persona_info
                        )
                        scored_products.append({
                            'product': product,
                            'score': detailed['total_score'],
                            'detailed_calculation': detailed
                        })
                    except Exception as e:
                        logger.warning(f"Scoring failed for {product.get('product_id')}: {e}")
                        continue
                
                # Sort by score
                scored_products.sort(key=lambda x: x['score'], reverse=True)
                top_products = scored_products[:n_recommendations]
            else:
                # Fallback: simple sorting by interest rate or minimal criteria
                candidates = candidates.copy()
                candidates['simple_score'] = 0.0
                
                # Prefer products with lower fees
                if 'annual_fee' in candidates.columns:
                    candidates['simple_score'] += (100 - candidates['annual_fee'].fillna(0)) / 100
                
                # Prefer products with higher interest rates (for savings/deposits)
                if 'interest_rate_apy' in candidates.columns:
                    candidates['simple_score'] += candidates['interest_rate_apy'].fillna(0) / 5.0
                
                top_candidates = candidates.nlargest(n_recommendations, 'simple_score')
                top_products = [
                    {
                        'product': row.to_dict(),
                        'score': row['simple_score'],
                        'detailed_calculation': {'total_score': row['simple_score']}
                    }
                    for _, row in top_candidates.iterrows()
                ]
            
            # Format recommendations
            recommendations = []
            for item in top_products:
                product = item['product']
                score = item['score']
                detailed_calc = item.get('detailed_calculation', {})
                
                # Build explanation
                explanation_parts = []
                
                # Match level
                match_level = self._get_match_level(score)
                explanation_parts.append(f"{match_level} based on your financial profile")
                
                # Fee affordability
                annual_fee = product.get('annual_fee', 0)
                if annual_fee == 0:
                    explanation_parts.append("No annual fee")
                else:
                    explanation_parts.append(f"${annual_fee:.0f} annual fee fits your budget")
                
                # Interest benefit (for deposit/savings products)
                interest_rate = product.get('interest_rate_apy', product.get('interest_rate', 0))
                if interest_rate > 0:
                    explanation_parts.append(f"{interest_rate:.2f}% APY to grow your savings")
                
                # Credit requirement
                min_credit = product.get('min_credit_score')
                if min_credit:
                    if customer_credit >= min_credit + 50:
                        explanation_parts.append(f"Well above credit requirement ({min_credit})")
                    else:
                        explanation_parts.append(f"Meets credit requirement ({min_credit})")
                
                full_explanation = ". ".join(explanation_parts) + "."
                
                recommendations.append({
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'category': product.get('category', 'Personal'),
                    'subcategory': product.get('subcategory', ''),
                    'annual_fee': float(annual_fee),
                    'min_balance': float(product.get('min_balance', 0)),
                    'interest_rate': float(interest_rate),
                    'min_credit_score': int(min_credit) if min_credit else None,
                    'score': float(score),
                    'match_level': match_level,
                    'reason': full_explanation,
                    'detailed_calculation': detailed_calc,
                    'scoring_method': '12_factor' if self.banking_scorer else 'simple'
                })
            
            return {
                'customer_id': customer_id,
                'recommendations': recommendations,
                'customer_segment': customer_segment,
                'type': 'customer_recommendations',
                'reason': f"Based on your {customer_segment} banking profile"
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Error getting recommendations for {customer_id}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'customer_id': customer_id,
                'recommendations': [],
                'error': str(e),
                'type': 'customer_recommendations'
            }
    
    def get_segment_recommendations(
        self,
        customer_id: str,
        micro_segment_id: Optional[int] = None,
        n_recommendations: int = 3
    ) -> Dict:
        """
        Get recommendations based on micro segment popularity
        
        Logic:
        - Get top products used by others in same micro segment
        - Filter by customer's eligibility
        - Return top N by popularity + suitability
        
        Args:
            customer_id: Customer ID
            micro_segment_id: Micro segment ID (if known)
            n_recommendations: Number of recommendations (default 3)
            
        Returns:
            Dictionary with recommendations and reasoning
        """
        try:
            # Get customer data
            customer = self.customers_df[self.customers_df['customer_id'] == customer_id]
            
            if len(customer) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'Customer not found',
                    'type': 'segment_based'
                }
            
            customer = customer.iloc[0].to_dict()
            
            # Get customers in same segment
            if micro_segment_id is not None and 'micro_segment' in self.customers_df.columns:
                segment_customers = self.customers_df[
                    (self.customers_df['micro_segment'] == micro_segment_id) &
                    (self.customers_df['customer_id'] != customer_id)
                ]['customer_id'].tolist()
                segment_type = "micro"
            else:
                # Fall back to macro segment
                macro_cluster = customer.get('cluster', 0)
                segment_customers = self.customers_df[
                    (self.customers_df['cluster'] == macro_cluster) &
                    (self.customers_df['customer_id'] != customer_id)
                ]['customer_id'].tolist()
                segment_type = "macro"
            
            if len(segment_customers) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'No other customers in segment',
                    'type': 'segment_based'
                }
            
            # Get transactions by segment members
            segment_transactions = self.transactions_df[
                self.transactions_df['customer_id'].isin(segment_customers)
            ]
            
            # Get customer's already owned products
            customer_transactions = self.transactions_df[
                self.transactions_df['customer_id'] == customer_id
            ]
            already_owned = customer_transactions['product_id'].unique()
            
            # Count product popularity in segment
            product_popularity = segment_transactions['product_id'].value_counts()
            
            # Get top popular products
            popular_product_ids = product_popularity.head(20).index.tolist()
            
            # Filter by eligibility
            candidates = self.products_df[
                (self.products_df['product_id'].isin(popular_product_ids)) &
                (~self.products_df['product_id'].isin(already_owned))
            ].copy()
            
            # Apply eligibility filters
            customer_segment = customer.get('customer_segment', 'Personal')
            if 'category' in candidates.columns:
                candidates = candidates[candidates['category'] == customer_segment]
            
            customer_credit = customer.get('credit_score', 700)
            if 'min_credit_score' in candidates.columns:
                candidates = candidates[
                    (candidates['min_credit_score'].isna()) |
                    (candidates['min_credit_score'] <= customer_credit + 30)
                ]
            
            if len(candidates) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'No eligible popular products in segment',
                    'type': 'segment_based'
                }
            
            # Add popularity score
            candidates['popularity'] = candidates['product_id'].map(product_popularity)
            candidates['popularity'] = candidates['popularity'] / candidates['popularity'].max()
            
            # Get top N
            top_products = candidates.nlargest(n_recommendations, 'popularity')
            
            # Format recommendations
            recommendations = []
            for _, product in top_products.iterrows():
                popularity = product.get('popularity', 0)
                
                # Build explanation
                if popularity > 0.7:
                    reason = f"Most popular in your {segment_type} segment"
                elif popularity > 0.4:
                    reason = f"Highly used by customers like you"
                else:
                    reason = f"Popular among similar customers"
                
                recommendations.append({
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'category': product.get('category', 'Personal'),
                    'subcategory': product.get('subcategory', ''),
                    'annual_fee': float(product.get('annual_fee', 0)),
                    'interest_rate': float(product.get('interest_rate_apy', product.get('interest_rate', 0))),
                    'popularity': round(popularity, 2),
                    'reason': reason
                })
            
            return {
                'customer_id': customer_id,
                'recommendations': recommendations,
                'segment_type': segment_type,
                'segment_size': len(segment_customers),
                'type': 'segment_based',
                'reason': f"Popular with other customers in your segment"
            }
            
        except Exception as e:
            logger.error(f"Error getting segment recommendations for {customer_id}: {e}")
            return {
                'customer_id': customer_id,
                'recommendations': [],
                'error': str(e),
                'type': 'segment_based'
            }
    
    def get_all_recommendations(
        self,
        customer_id: str
    ) -> Dict:
        """
        Get all recommendation types for a customer (for modal display)
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary with all recommendation types
        """
        # Get primary customer recommendations
        customer_result = self.get_customer_recommendations(customer_id)
        segment_result = self.get_segment_recommendations(customer_id)
        
        # Extract product lists
        customer_recs = customer_result.get('recommendations', [])
        segment_recs = segment_result.get('recommendations', [])
        
        # Build unified result
        result = {
            'customer_id': customer_id,
            'tailored_recommendations': customer_recs,
            'segment_recommendations': segment_recs,
            'customer_info': {'customer_id': customer_id},
            'recommendation_metadata': {
                'method': 'banking_12_factor',
                'persona_name': None
            }
        }
        
        # Enrich with customer data
        customer = self.customers_df[self.customers_df['customer_id'] == customer_id]
        if not customer.empty:
            customer_data = customer.iloc[0].to_dict()
            result['customer_info'] = customer_data
            
            # Add persona name
            if 'cluster' in customer_data and customer_data['cluster'] in self.personas:
                persona = self.personas[customer_data['cluster']]
                result['recommendation_metadata']['persona_name'] = persona.get('persona_name')
        
        print(f"\n✅ Generated recommendations for customer {customer_id}")
        print(f"   Tailored: {len(customer_recs)} products")
        print(f"   Segment: {len(segment_recs)} products")
        
        return result
    
    def _get_match_level(self, score: float) -> str:
        """Convert score to match level"""
        if score > 0.80:
            return 'Perfect Match'
        elif score > 0.65:
            return 'Great Match'
        elif score > 0.50:
            return 'Good Option'
        else:
            return 'Consider Alternatives'


if __name__ == "__main__":
    print("="*70)
    print("Agent B Banking Enhanced - Product Recommendations")
    print("="*70)
    print("Provides banking product recommendations for customer modals")
    print("Uses Banking 12-Factor scoring for detailed explanations")
    print("="*70)

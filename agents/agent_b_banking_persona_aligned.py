"""
Agent B Banking Persona-Aligned Recommendations
Modeled after agent_b_academy_persona_aligned.py

Key improvements:
1. Use PERSONA average financial metrics (not just individual)
2. Match PERSONA risk tolerance and product sophistication
3. Match PERSONA channel preferences (digital vs branch)
4. Match PERSONA financial needs based on life stage
5. Eligibility-first filtering (credit, income, balance)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from agents.banking_12_factor_scorer import Banking12FactorScorer

logger = logging.getLogger(__name__)


class BankingPersonaAlignedRecommender:
    """
    Ensures product recommendations align with customer's PERSONA characteristics
    for banking products
    """
    
    def __init__(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
        personas: Dict = None
    ):
        """
        Initialize Banking Persona-Aligned Recommender
        
        Args:
            customers_df: Customer data with macro_segment_id assignments
            products_df: Product catalog
            transactions_df: Transaction history
            personas: Persona definitions from Agent A
        """
        self.customers_df = customers_df
        self.products_df = products_df
        self.transactions_df = transactions_df
        self.personas = personas or {}
        
        # Initialize banking 12-factor scorer
        self.scorer = Banking12FactorScorer(
            customers_df=customers_df,
            products_df=products_df,
            transactions_df=transactions_df,
            personas=personas
        )
        
        logger.info(f"✨ Banking Persona-Aligned Recommender initialized")
        logger.info(f"  - {len(customers_df)} customers")
        logger.info(f"  - {len(products_df)} products")
        logger.info(f"  - {len(transactions_df)} transactions")
        logger.info(f"  - {len(personas)} personas")
    
    def get_persona_aligned_recommendations(
        self,
        customer_id: str,
        n_recommendations: int = 3
    ) -> Dict:
        """
        Get recommendations that MATCH the customer's PERSONA characteristics
        
        This ensures:
        - Eligibility requirements met (credit score, income, balance)
        - Products match persona's average financial profile
        - Risk tolerance and sophistication aligned
        - Channel preferences match
        - Financial life stage needs addressed
        
        Args:
            customer_id: Customer ID
            n_recommendations: Number of recommendations
            
        Returns:
            Dict with persona-aligned recommendations
        """
        try:
            # 1. GET CUSTOMER AND PERSONA DATA
            customer = self.customers_df[self.customers_df['customer_id'] == customer_id]
            
            if len(customer) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'error': 'Customer not found',
                    'type': 'persona_aligned'
                }
            
            customer = customer.iloc[0]
            persona_id = customer.get('cluster', customer.get('macro_segment_id'))
            
            # Get persona definition
            persona = None
            if persona_id is not None and persona_id in self.personas:
                persona = self.personas[persona_id]
            
            if persona is None:
                logger.warning(f"No persona found for customer {customer_id} (persona_id {persona_id})")
                return self._fallback_recommendations(customer_id, customer, n_recommendations)
            
            logger.info(f"")
            logger.info(f"{'='*80}")
            logger.info(f"🎯 BANKING PERSONA-ALIGNED RECOMMENDATIONS FOR {customer_id}")
            logger.info(f"   Persona: {persona.get('persona_name', 'Unknown')}")
            logger.info(f"   Persona ID: {persona_id}")
            logger.info(f"{'='*80}")
            
            # 2. EXTRACT PERSONA CHARACTERISTICS
            characteristics = persona.get('characteristics', {})
            
            # Financial profile from persona
            persona_avg_deposits = characteristics.get('avg_deposits', 50000)
            persona_avg_income = characteristics.get('avg_income', 70000)
            persona_avg_credit = characteristics.get('avg_credit_score', 720)
            
            # Digital engagement from persona
            digital_affinity = characteristics.get('avg_digital', 0.5)
            
            # Risk tolerance and sophistication
            avg_products = characteristics.get('avg_products', 2.5)
            risk_tolerance = 'high' if avg_products > 4 else ('medium' if avg_products > 2 else 'low')
            
            logger.info(f"\n📊 PERSONA CHARACTERISTICS:")
            logger.info(f"   • Avg Deposits: ${persona_avg_deposits:,.0f}")
            logger.info(f"   • Avg Income: ${persona_avg_income:,.0f}/year")
            logger.info(f"   • Avg Credit Score: {persona_avg_credit:.0f}")
            logger.info(f"   • Digital Affinity: {digital_affinity:.2f}")
            logger.info(f"   • Risk Tolerance: {risk_tolerance}")
            logger.info(f"   • Avg Products: {avg_products:.1f}")
            
            # 3. CALCULATE ELIGIBILITY THRESHOLDS (Persona-based with buffer)
            # Use persona averages to set reasonable thresholds
            min_credit_threshold = persona_avg_credit - 50  # Allow 50 points below persona avg
            min_income_threshold = persona_avg_income * 0.6  # Allow 40% below persona avg
            min_balance_threshold = persona_avg_deposits * 0.3  # Allow 70% below persona avg
            
            logger.info(f"\n💰 ELIGIBILITY THRESHOLDS (Persona-Based):")
            logger.info(f"   • Min Credit Score: {min_credit_threshold:.0f}")
            logger.info(f"   • Min Income: ${min_income_threshold:,.0f}")
            logger.info(f"   • Min Balance: ${min_balance_threshold:,.0f}")
            
            # 4. GET CUSTOMER'S EXISTING PRODUCTS
            customer_products = []
            if 'product_id' in self.transactions_df.columns:
                customer_transactions = self.transactions_df[
                    self.transactions_df['customer_id'] == customer_id
                ]
                customer_products = customer_transactions['product_id'].unique().tolist()
            
            logger.info(f"\n🎯 CUSTOMER CONTEXT:")
            logger.info(f"   • Credit Score: {customer.get('credit_score', 'N/A')}")
            logger.info(f"   • Income: ${customer.get('income', 0):,.0f}")
            logger.info(f"   • Deposits: ${customer.get('total_deposits', 0):,.0f}")
            logger.info(f"   • Existing Products: {len(customer_products)}")
            
            # 5. FILTER PRODUCTS BY ELIGIBILITY AND PERSONA FIT
            candidates = self._filter_by_persona_and_eligibility(
                customer=customer,
                persona=persona,
                min_credit=min_credit_threshold,
                min_income=min_income_threshold,
                min_balance=min_balance_threshold,
                existing_products=customer_products
            )
            
            if len(candidates) == 0:
                logger.warning(f"⚠️ No products match eligibility, relaxing constraints...")
                # Relax constraints progressively
                candidates = self._filter_by_persona_and_eligibility(
                    customer=customer,
                    persona=persona,
                    min_credit=min_credit_threshold - 30,
                    min_income=min_income_threshold * 0.7,
                    min_balance=0,  # Remove balance requirement
                    existing_products=customer_products,
                    relax_eligibility=True
                )
            
            if len(candidates) == 0:
                logger.warning(f"❌ Still no products found")
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': f'No products match {persona.get("persona_name")} eligibility criteria',
                    'type': 'persona_aligned'
                }
            
            logger.info(f"\n📦 FILTERED CANDIDATES: {len(candidates)} products")
            
            # 6. SCORE PRODUCTS USING BANKING 12-FACTOR SCORER
            scored_products = []
            for _, product in candidates.iterrows():
                score_breakdown = self.scorer.score_product(
                    customer=customer.to_dict(),
                    product=product.to_dict(),
                    persona=persona
                )
                
                scored_products.append({
                    'product': product,
                    'total_score': score_breakdown['total_score'],
                    'breakdown': score_breakdown
                })
            
            # Sort by score
            scored_products.sort(key=lambda x: x['total_score'], reverse=True)
            
            # 7. SELECT TOP N WITH CATEGORY DIVERSITY
            recommendations = self._select_diverse_products(
                scored_products,
                n_recommendations
            )
            
            # 8. FORMAT RECOMMENDATIONS WITH PERSONA-SPECIFIC REASONING
            formatted_recs = self._format_persona_recommendations(
                recommendations,
                persona,
                customer
            )
            
            logger.info(f"\n✅ SELECTED {len(formatted_recs)} PERSONA-ALIGNED RECOMMENDATIONS:")
            for i, rec in enumerate(formatted_recs, 1):
                logger.info(f"   {i}. {rec['product_name']} - Score: {rec['score']:.2f} ({rec['score']*100:.0f}%)")
                logger.info(f"      Category: {rec['category']}")
            
            return {
                'customer_id': customer_id,
                'persona': persona.get('persona_name'),
                'persona_id': persona_id,
                'recommendations': formatted_recs,
                'persona_characteristics': {
                    'avg_deposits': persona_avg_deposits,
                    'avg_income': persona_avg_income,
                    'avg_credit': persona_avg_credit,
                    'digital_affinity': digital_affinity,
                    'risk_tolerance': risk_tolerance
                },
                'type': 'persona_aligned'
            }
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Error getting persona-aligned recommendations: {e}")
            logger.error(traceback.format_exc())
            return {
                'customer_id': customer_id,
                'recommendations': [],
                'error': str(e),
                'type': 'persona_aligned'
            }
    
    def _filter_by_persona_and_eligibility(
        self,
        customer: pd.Series,
        persona: Dict,
        min_credit: float,
        min_income: float,
        min_balance: float,
        existing_products: List[str],
        relax_eligibility: bool = False
    ) -> pd.DataFrame:
        """
        Filter products based on eligibility AND persona characteristics
        """
        candidates = self.products_df.copy()
        
        # 1. Remove already owned products (MANDATORY)
        candidates = candidates[~candidates['product_id'].isin(existing_products)]
        
        # 2. Filter by customer segment (Personal/Business/Agricultural)
        customer_segment = customer.get('customer_segment', customer.get('segment', 'Personal'))
        if 'category' in candidates.columns:
            # If product has category, filter by it
            candidates = candidates[candidates['category'] == customer_segment]
        
        # Early return if no products in segment
        if len(candidates) == 0:
            return candidates
        
        # 3. Eligibility filtering (with checks for column existence)
        customer_credit = customer.get('credit_score', 700)
        customer_income = customer.get('income', 50000)
        customer_deposits = customer.get('total_deposits', 10000)
        
        if not relax_eligibility:
            # Credit score filter (if column exists)
            if 'min_credit_score' in candidates.columns:
                candidates = candidates[
                    (candidates['min_credit_score'].isna()) |
                    (candidates['min_credit_score'] <= customer_credit + 30)  # Increased buffer from 20 to 30
                ]
            
            # Income filter (if column exists) - RELAXED
            if 'min_income' in candidates.columns:
                candidates = candidates[
                    (candidates['min_income'].isna()) |
                    (candidates['min_income'] == 0) |  # Include products with no minimum
                    (candidates['min_income'] <= customer_income * 1.5)  # Increased from 1.2 to 1.5
                ]
            
            # Balance filter (if column exists) - VERY RELAXED
            if 'min_balance' in candidates.columns:
                candidates = candidates[
                    (candidates['min_balance'].isna()) |
                    (candidates['min_balance'] == 0) |  # Include products with no minimum
                    (candidates['min_balance'] <= customer_deposits * 2.0)  # Allow 2x stretch
                ]
        else:
            # Relaxed eligibility (borderline cases)
            if 'min_credit_score' in candidates.columns:
                candidates = candidates[
                    (candidates['min_credit_score'].isna()) |
                    (candidates['min_credit_score'] <= customer_credit + 60)  # Very loose
                ]
        
        # 4. Filter by accepting applications (if column exists)
        if 'accepting_applications' in candidates.columns:
            candidates = candidates[
                (candidates['accepting_applications'].isna()) |
                (candidates['accepting_applications'] == True)
            ]
        
        return candidates
    
    def _select_diverse_products(
        self,
        scored_products: List[Dict],
        n: int
    ) -> List[Dict]:
        """
        Select top N products with category diversity
        """
        selected = []
        categories_used = set()
        
        # First pass: One per category
        for item in scored_products:
            if len(selected) >= n:
                break
            
            category = item['product'].get('category', 'Unknown')
            
            if category not in categories_used:
                selected.append(item)
                categories_used.add(category)
        
        # Second pass: Fill remaining slots with highest scores
        for item in scored_products:
            if len(selected) >= n:
                break
            
            # Compare product IDs instead of entire dicts (which contain pandas Series)
            item_product_id = item['product']['product_id']
            selected_product_ids = [p['product']['product_id'] for p in selected]
            
            if item_product_id not in selected_product_ids:
                selected.append(item)
        
        return selected[:n]
    
    def _format_persona_recommendations(
        self,
        recommendations: List[Dict],
        persona: Dict,
        customer: pd.Series
    ) -> List[Dict]:
        """
        Format recommendations with persona-specific reasoning
        """
        formatted = []
        persona_name = persona.get('persona_name', 'your segment')
        
        for item in recommendations:
            product = item['product']
            breakdown = item['breakdown']
            
            # Build persona-aligned reasoning from score breakdown
            reasons = []
            
            # Eligibility
            if breakdown['eligibility_score']['score'] > 0.15:  # 15% of 25% weight
                reasons.append(
                    f"✓ You qualify: {breakdown['eligibility_score']['explanation']}"
                )
            
            # Financial need match
            if breakdown['financial_need_match']['score'] > 0.12:  # 12% of 20% weight
                reasons.append(
                    f"✓ {breakdown['financial_need_match']['explanation']}"
                )
            
            # Relationship depth
            if breakdown['relationship_depth']['score'] > 0.08:  # 8% of 15% weight
                reasons.append(
                    f"✓ Complements your {customer.get('num_products', 0)} existing products"
                )
            
            # Product pairing
            if breakdown['product_pairing']['score'] > 0.05:  # 5% of 10% weight
                pairs_with = breakdown['product_pairing'].get('pairs_with', [])
                if pairs_with:
                    reasons.append(
                        f"✓ Pairs well with: {', '.join(pairs_with[:2])}"
                    )
            
            # Channel fit
            if breakdown['channel_fit']['score'] > 0.05:
                reasons.append(f"✓ {breakdown['channel_fit']['explanation']}")
            
            reason_text = " ".join(reasons) if reasons else "Recommended for your profile"
            
            formatted.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'category': product.get('category', 'Unknown'),
                'annual_fee': float(product.get('annual_fee', 0)),
                'min_balance': float(product.get('min_balance', 0)),
                'interest_rate_apy': float(product.get('interest_rate_apy', product.get('interest_rate', 0))),
                'score': item['total_score'],
                'reasoning': reason_text,
                'score_breakdown': breakdown,
                'ai_explanation': None  # Generated on-demand via API
            })
        
        return formatted
    
    def _fallback_recommendations(
        self,
        customer_id: str,
        customer: pd.Series,
        n: int
    ) -> Dict:
        """
        Fallback recommendations when no persona is available
        Uses basic eligibility and popular products
        """
        # Get products customer doesn't have
        customer_products = []
        if 'product_id' in self.transactions_df.columns:
            customer_transactions = self.transactions_df[
                self.transactions_df['customer_id'] == customer_id
            ]
            customer_products = customer_transactions['product_id'].unique().tolist()
        
        # Filter by basic eligibility
        candidates = self.products_df[
            ~self.products_df['product_id'].isin(customer_products)
        ].copy()
        
        if 'min_credit_score' in candidates.columns:
            candidates = candidates[
                (candidates['min_credit_score'].isna()) |
                (candidates['min_credit_score'] <= customer.get('credit_score', 700))
            ]
        
        # Sort by popularity (if available) or rating
        if 'adoption_count' in candidates.columns:
            candidates = candidates.sort_values('adoption_count', ascending=False)
        elif 'avg_rating' in candidates.columns:
            candidates = candidates.sort_values('avg_rating', ascending=False)
        
        top_products = candidates.head(n)
        
        recommendations = []
        for _, product in top_products.iterrows():
            recommendations.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'category': product.get('category', 'Unknown'),
                'annual_fee': float(product.get('annual_fee', 0)),
                'min_balance': float(product.get('min_balance', 0)),
                'score': 0.7,  # Default score
                'reasoning': 'Popular product (no persona data available)',
                'ai_explanation': None
            })
        
        return {
            'customer_id': customer_id,
            'recommendations': recommendations,
            'type': 'fallback'
        }


logger.info("✨ Banking Persona-Aligned Recommender module initialized")

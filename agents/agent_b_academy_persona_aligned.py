"""
Agent B Persona-Aligned Recommendations - Academy Sports
ENSURES recommendations match segment/persona characteristics

Key improvements:
1. Use PERSONA average spend (not just individual)
2. Match PERSONA bundle affinity (bundles vs individual items)
3. Match PERSONA expertise level (simple vs technical products)
4. Match PERSONA price sensitivity (strict vs flexible pricing)
5. Match PERSONA category preferences
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PersonaAlignedRecommender:
    """
    Ensures product recommendations align with customer's PERSONA characteristics
    """
    
    def __init__(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        purchases_df: pd.DataFrame,
        personas: Dict = None
    ):
        """
        Initialize Persona-Aligned Recommender
        
        Args:
            customers_df: Customer data with cluster assignments
            products_df: Product catalog
            purchases_df: Purchase history
            personas: Persona definitions from Agent A
        """
        self.customers_df = customers_df
        self.products_df = products_df
        self.purchases_df = purchases_df
        self.personas = personas or {}
        
        logger.info(f"✨ Persona-Aligned Recommender initialized")
        logger.info(f"  - {len(customers_df)} customers")
        logger.info(f"  - {len(products_df)} products")
        logger.info(f"  - {len(purchases_df)} purchases")
        logger.info(f"  - {len(personas)} personas")
    
    
    def get_persona_aligned_recommendations(
        self,
        customer_id: str,
        n_recommendations: int = 3
    ) -> Dict:
        """
        Get recommendations that MATCH the customer's PERSONA characteristics
        
        This ensures:
        - Price matches persona's avg spend range
        - Products match persona's expertise level
        - Bundle preferences align
        - Categories match persona's dominant categories
        
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
            cluster_id = customer.get('cluster', -1)
            
            # Get persona definition
            persona = None
            if cluster_id >= 0 and cluster_id in self.personas:
                persona = self.personas[cluster_id]
            
            if persona is None:
                logger.warning(f"No persona found for customer {customer_id} (cluster {cluster_id})")
                return self._fallback_recommendations(customer_id, customer, n_recommendations)
            
            logger.info(f"")
            logger.info(f"{'='*80}")
            logger.info(f"🎯 PERSONA-ALIGNED RECOMMENDATIONS FOR {customer_id}")
            logger.info(f"   Persona: {persona.get('persona_name', 'Unknown')}")
            logger.info(f"   Cluster: {cluster_id}")
            logger.info(f"{'='*80}")
            
            # 2. EXTRACT PERSONA CHARACTERISTICS
            characteristics = persona.get('characteristics', {})
            
            # Price behavior from persona
            persona_avg_spend = persona.get('revenue_metrics', {}).get('avg_customer_value', 500)
            price_sensitivity = characteristics.get('price_sort_frequency', 0.5)  # 0-1 scale
            
            # Expertise level from persona
            search_specificity = characteristics.get('search_specificity', 3.0)  # 1-5 scale
            expertise_level = self._map_expertise(search_specificity)
            
            # Bundle preference from persona
            bundle_affinity = characteristics.get('bundle_affinity', 0.5)  # 0-1 scale
            prefers_bundles = bundle_affinity > 0.6
            
            # Category preferences from persona
            persona_categories = characteristics.get('top_categories', [])
            
            logger.info(f"\n📊 PERSONA CHARACTERISTICS:")
            logger.info(f"   • Avg Spend: ${persona_avg_spend:.0f}/year")
            logger.info(f"   • Price Sensitivity: {price_sensitivity:.2f} (0=flexible, 1=strict)")
            logger.info(f"   • Search Specificity: {search_specificity:.1f}/5.0 → {expertise_level}")
            logger.info(f"   • Bundle Affinity: {bundle_affinity:.2f} → {'Prefers Bundles' if prefers_bundles else 'Prefers Individual'}")
            logger.info(f"   • Top Categories: {persona_categories[:3]}")
            
            # 3. CALCULATE PERSONA-ALIGNED PRICE RANGE
            price_range = self._calculate_persona_price_range(
                persona_avg_spend,
                price_sensitivity,
                customer.get('avg_order_value', persona_avg_spend / 10)
            )
            
            min_price = price_range['min']
            max_price = price_range['max']
            target_price = price_range['target']
            
            logger.info(f"\n💰 PRICE RANGE (Persona-Aligned):")
            logger.info(f"   • Min: ${min_price:.0f}")
            logger.info(f"   • Target: ${target_price:.0f}")
            logger.info(f"   • Max: ${max_price:.0f}")
            logger.info(f"   • Range width: ${max_price - min_price:.0f}")
            
            # 4. GET CUSTOMER'S PURCHASE HISTORY
            customer_purchases = self.purchases_df[
                self.purchases_df['customer_id'] == customer_id
            ]
            purchased_product_ids = customer_purchases['product_id'].unique()
            
            # Get customer's dominant category
            customer_category = customer.get('dominant_category', None)
            if customer_category is None and len(persona_categories) > 0:
                customer_category = persona_categories[0]
            
            logger.info(f"\n🎯 TARGET CATEGORY: {customer_category}")
            
            # 5. FILTER PRODUCTS BY PERSONA CONSTRAINTS
            candidates = self._filter_by_persona(
                customer_category,
                min_price,
                max_price,
                expertise_level,
                prefers_bundles,
                purchased_product_ids
            )
            
            if len(candidates) == 0:
                logger.warning(f"⚠️ No products match persona constraints, relaxing...")
                # Relax constraints progressively
                candidates = self._filter_by_persona(
                    customer_category,
                    min_price * 0.7,  # Widen price range
                    max_price * 1.3,
                    expertise_level,
                    None,  # Ignore bundle preference
                    purchased_product_ids
                )
            
            if len(candidates) == 0:
                logger.warning(f"❌ Still no products found")
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': f'No products match {persona.get("persona_name")} characteristics',
                    'type': 'persona_aligned'
                }
            
            logger.info(f"\n📦 FILTERED CANDIDATES: {len(candidates)} products")
            
            # 6. SCORE PRODUCTS BASED ON PERSONA ALIGNMENT
            scored_products = self._score_persona_alignment(
                candidates,
                target_price,
                expertise_level,
                prefers_bundles,
                customer_category,
                price_sensitivity
            )
            
            # 7. SELECT TOP N WITH DIVERSITY
            recommendations = self._select_diverse_products(
                scored_products,
                n_recommendations
            )
            
            # 8. FORMAT RECOMMENDATIONS WITH PERSONA-SPECIFIC REASONING
            formatted_recs = self._format_persona_recommendations(
                recommendations,
                persona,
                target_price,
                expertise_level
            )
            
            logger.info(f"\n✅ SELECTED {len(formatted_recs)} PERSONA-ALIGNED RECOMMENDATIONS:")
            for i, rec in enumerate(formatted_recs, 1):
                logger.info(f"   {i}. {rec['product_name']} (${rec['price']:.0f}) - Score: {rec['alignment_score']:.2f}")
                logger.info(f"      Reason: {rec['reason'][:80]}...")
            
            return {
                'customer_id': customer_id,
                'persona': persona.get('persona_name'),
                'persona_cluster': cluster_id,
                'recommendations': formatted_recs,
                'price_range': price_range,
                'persona_characteristics': {
                    'avg_spend': persona_avg_spend,
                    'price_sensitivity': price_sensitivity,
                    'expertise_level': expertise_level,
                    'prefers_bundles': prefers_bundles
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
    
    
    def _calculate_persona_price_range(
        self,
        persona_avg_spend: float,
        price_sensitivity: float,
        customer_avg_order: float
    ) -> Dict:
        """
        Calculate price range based on PERSONA spending patterns
        
        Key logic:
        - High price sensitivity → narrow range around persona avg
        - Low price sensitivity → wider range, can go higher
        - Always consider persona's typical spend
        """
        # Calculate per-purchase budget from annual spend
        # Assume 3-10 purchases per year depending on persona
        persona_price_per_purchase = persona_avg_spend / 5  # Conservative estimate
        
        # Target price is blend of persona avg and customer's historical avg
        target_price = (persona_price_per_purchase * 0.7) + (customer_avg_order * 0.3)
        
        # Width of price range depends on price sensitivity
        if price_sensitivity > 0.7:  # Highly price-sensitive
            # NARROW range, stay close to persona avg
            min_price = max(target_price * 0.7, 15)
            max_price = target_price * 1.2
        elif price_sensitivity > 0.4:  # Moderately price-sensitive
            # MEDIUM range
            min_price = max(target_price * 0.5, 20)
            max_price = target_price * 1.5
        else:  # Low price sensitivity (premium buyers)
            # WIDE range, can go much higher
            min_price = max(target_price * 0.4, 30)
            max_price = target_price * 2.0
        
        return {
            'min': round(min_price, 2),
            'target': round(target_price, 2),
            'max': round(max_price, 2)
        }
    
    
    def _map_expertise(self, search_specificity: float) -> str:
        """
        Map search specificity (1-5) to expertise level
        
        1.0-2.5: Beginner (simple products)
        2.5-3.5: Intermediate (moderate complexity)
        3.5-5.0: Expert (technical products)
        """
        if search_specificity < 2.5:
            return 'beginner'
        elif search_specificity < 3.5:
            return 'intermediate'
        else:
            return 'expert'
    
    
    def _filter_by_persona(
        self,
        category: str,
        min_price: float,
        max_price: float,
        expertise_level: str,
        prefers_bundles: Optional[bool],
        purchased_ids: np.ndarray
    ) -> pd.DataFrame:
        """
        Filter products based on persona characteristics
        """
        # Start with all products
        candidates = self.products_df.copy()
        
        # 1. Category filter (MANDATORY)
        if category:
            candidates = candidates[candidates['main_category'] == category]
        
        # 2. Price filter (MANDATORY)
        candidates = candidates[
            (candidates['price'] >= min_price) &
            (candidates['price'] <= max_price)
        ]
        
        # 3. In stock (MANDATORY)
        if 'in_stock' in candidates.columns:
            candidates = candidates[candidates['in_stock'] == True]
        
        # 4. Not purchased (MANDATORY)
        candidates = candidates[~candidates['product_id'].isin(purchased_ids)]
        
        # 5. Bundle preference (SOFT - if available)
        if prefers_bundles is not None and 'is_bundle' in candidates.columns:
            if prefers_bundles:
                # Prefer bundles but don't exclude individual items
                bundle_products = candidates[candidates['is_bundle'] == True]
                if len(bundle_products) >= 3:
                    candidates = bundle_products
        
        # 6. Expertise level match (SOFT - if available)
        if 'complexity' in candidates.columns:
            if expertise_level == 'beginner':
                # Prefer simple products
                simple_products = candidates[candidates['complexity'].isin(['Simple', 'Easy', 'Beginner'])]
                if len(simple_products) >= 3:
                    candidates = simple_products
            elif expertise_level == 'expert':
                # Prefer technical products
                expert_products = candidates[candidates['complexity'].isin(['Advanced', 'Technical', 'Expert'])]
                if len(expert_products) >= 3:
                    candidates = expert_products
        
        return candidates
    
    
    def _score_persona_alignment(
        self,
        candidates: pd.DataFrame,
        target_price: float,
        expertise_level: str,
        prefers_bundles: bool,
        target_category: str,
        price_sensitivity: float
    ) -> pd.DataFrame:
        """
        Score products based on how well they match persona characteristics
        
        Scoring weights:
        - Price alignment: 35% (how close to target price)
        - Category match: 30%
        - Expertise match: 20%
        - Bundle preference: 10%
        - Rating: 5%
        """
        candidates = candidates.copy()
        candidates['alignment_score'] = 0.0
        
        # 1. PRICE ALIGNMENT (35%) - Most important for persona match
        # Products closer to target price get higher scores
        price_deviation = abs(candidates['price'] - target_price) / target_price
        # Invert so closer = higher score
        candidates['price_score'] = (1 - price_deviation.clip(0, 1)) * 0.35
        candidates['alignment_score'] += candidates['price_score']
        
        # For highly price-sensitive personas, penalize deviations more
        if price_sensitivity > 0.7:
            candidates['alignment_score'] -= price_deviation.clip(0, 0.5) * 0.15
        
        # 2. CATEGORY MATCH (30%)
        if target_category:
            candidates.loc[candidates['main_category'] == target_category, 'alignment_score'] += 0.30
        
        # 3. EXPERTISE MATCH (20%)
        if 'complexity' in candidates.columns:
            if expertise_level == 'beginner':
                candidates.loc[candidates['complexity'].isin(['Simple', 'Easy', 'Beginner']), 'alignment_score'] += 0.20
                # Penalize complex products for beginners
                candidates.loc[candidates['complexity'].isin(['Advanced', 'Technical']), 'alignment_score'] -= 0.10
            elif expertise_level == 'expert':
                candidates.loc[candidates['complexity'].isin(['Advanced', 'Technical', 'Expert']), 'alignment_score'] += 0.20
                # Slight penalty for too simple products
                candidates.loc[candidates['complexity'] == 'Simple', 'alignment_score'] -= 0.05
            else:  # intermediate
                candidates.loc[candidates['complexity'] == 'Moderate', 'alignment_score'] += 0.15
        
        # 4. BUNDLE PREFERENCE (10%)
        if 'is_bundle' in candidates.columns:
            if prefers_bundles:
                candidates.loc[candidates['is_bundle'] == True, 'alignment_score'] += 0.10
            else:
                candidates.loc[candidates['is_bundle'] == False, 'alignment_score'] += 0.05
        
        # 5. PRODUCT RATING (5%)
        if 'avg_rating' in candidates.columns:
            candidates['alignment_score'] += (candidates['avg_rating'] / 5.0) * 0.05
        
        # Ensure non-negative scores
        candidates['alignment_score'] = candidates['alignment_score'].clip(lower=0)
        
        return candidates.sort_values('alignment_score', ascending=False)
    
    
    def _select_diverse_products(
        self,
        scored_products: pd.DataFrame,
        n: int
    ) -> pd.DataFrame:
        """
        Select top N products with diversity (different subcategories/brands)
        """
        selected = []
        used_subcategories = set()
        used_brands = set()
        
        # First pass: high diversity
        for _, product in scored_products.iterrows():
            if len(selected) >= n:
                break
            
            subcat = product.get('subcategory', 'Unknown')
            brand = product.get('brand', 'Unknown')
            
            # Limit 1 per subcategory and 1 per brand in first pass
            if subcat not in used_subcategories and brand not in used_brands:
                selected.append(product)
                used_subcategories.add(subcat)
                used_brands.add(brand)
        
        # Second pass: relax constraints if needed
        if len(selected) < n:
            for _, product in scored_products.iterrows():
                if len(selected) >= n:
                    break
                if product['product_id'] not in [p['product_id'] for p in selected]:
                    selected.append(product)
        
        return pd.DataFrame(selected)
    
    
    def _format_persona_recommendations(
        self,
        products: pd.DataFrame,
        persona: Dict,
        target_price: float,
        expertise_level: str
    ) -> List[Dict]:
        """
        Format recommendations with persona-specific reasoning
        """
        recommendations = []
        persona_name = persona.get('persona_name', 'your segment')
        
        for _, product in products.iterrows():
            # Build persona-aligned reasoning
            reasons = []
            
            # Price alignment
            product_price = product['price']
            price_diff_pct = abs(product_price - target_price) / target_price * 100
            if price_diff_pct < 15:
                reasons.append(f"Perfect price match at ${product_price:.0f} for {persona_name} (avg ${target_price:.0f})")
            elif price_diff_pct < 30:
                reasons.append(f"${product_price:.0f} aligns with {persona_name} spending patterns")
            else:
                if product_price > target_price:
                    reasons.append(f"Premium ${product_price:.0f} option for {persona_name}")
                else:
                    reasons.append(f"Value ${product_price:.0f} choice for {persona_name}")
            
            # Expertise match
            if 'complexity' in product and pd.notna(product['complexity']):
                complexity = product['complexity']
                if expertise_level == 'beginner' and complexity in ['Simple', 'Easy']:
                    reasons.append("Easy to use - perfect for getting started")
                elif expertise_level == 'expert' and complexity in ['Advanced', 'Technical']:
                    reasons.append("Technical features match your expertise")
                elif expertise_level == 'intermediate':
                    reasons.append(f"{complexity} level suits your experience")
            
            # Quality rating
            if 'avg_rating' in product and product['avg_rating'] >= 4.0:
                reasons.append(f"Rated {product['avg_rating']:.1f}/5.0")
            
            # Brand
            if 'brand' in product and pd.notna(product['brand']):
                reasons.append(f"by {product['brand']}")
            
            reason = ". ".join(reasons) + "."
            
            recommendations.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'brand': product.get('brand', 'Unknown'),
                'category': product.get('main_category', 'Unknown'),
                'price': round(float(product['price']), 2),
                'rating': round(float(product.get('avg_rating', 4.0)), 1),
                'alignment_score': round(float(product['alignment_score']), 2),
                'reason': reason,
                'in_stock': bool(product.get('in_stock', True))
            })
        
        return recommendations
    
    
    def _fallback_recommendations(
        self,
        customer_id: str,
        customer: pd.Series,
        n: int
    ) -> Dict:
        """
        Fallback recommendations when no persona is available
        """
        # Use simple logic based on customer's purchase history
        customer_purchases = self.purchases_df[
            self.purchases_df['customer_id'] == customer_id
        ]
        
        if len(customer_purchases) == 0:
            # Return popular products
            popular_products = self.products_df.nlargest(n, 'num_reviews')
            
            recommendations = []
            for _, product in popular_products.iterrows():
                recommendations.append({
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'brand': product.get('brand', 'Unknown'),
                    'category': product.get('main_category', 'Unknown'),
                    'price': round(float(product['price']), 2),
                    'rating': round(float(product.get('avg_rating', 4.0)), 1),
                    'reason': 'Popular product (no persona data available)',
                    'in_stock': bool(product.get('in_stock', True))
                })
            
            return {
                'customer_id': customer_id,
                'recommendations': recommendations,
                'type': 'fallback'
            }
        
        # Use purchase history
        avg_price = customer_purchases['price_paid'].mean()
        purchased_ids = customer_purchases['product_id'].unique()
        
        # Get purchased product categories
        purchased_products = self.products_df[
            self.products_df['product_id'].isin(purchased_ids)
        ]
        top_category = purchased_products['main_category'].mode()[0] if len(purchased_products) > 0 else None
        
        # Find similar products
        candidates = self.products_df[
            (~self.products_df['product_id'].isin(purchased_ids)) &
            (self.products_df['price'] >= avg_price * 0.5) &
            (self.products_df['price'] <= avg_price * 1.5)
        ]
        
        if top_category:
            candidates = candidates[candidates['main_category'] == top_category]
        
        if 'in_stock' in candidates.columns:
            candidates = candidates[candidates['in_stock'] == True]
        
        top_products = candidates.nlargest(n, 'avg_rating')
        
        recommendations = []
        for _, product in top_products.iterrows():
            recommendations.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'brand': product.get('brand', 'Unknown'),
                'category': product.get('main_category', 'Unknown'),
                'price': round(float(product['price']), 2),
                'rating': round(float(product.get('avg_rating', 4.0)), 1),
                'reason': f'Based on your {top_category} purchases (avg ${avg_price:.0f})',
                'in_stock': bool(product.get('in_stock', True))
            })
        
        return {
            'customer_id': customer_id,
            'recommendations': recommendations,
            'type': 'fallback'
        }


logger.info("✨ Persona-Aligned Recommender module initialized")

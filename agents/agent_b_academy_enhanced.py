"""
Agent B Enhanced - Academy Sports Product Recommendations
Provides three types of product recommendations:
1. Similar Products (based on purchase history)
2. You Might Like (based on micro segment)
3. Dynamic Search Matching (semantic search)
4. Persona-Aligned (NEW - matches segment characteristics)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from pathlib import Path
from agents.agent_b_academy_persona_aligned import PersonaAlignedRecommender
from agents.enhanced_12_factor_scorer import Enhanced12FactorScorer

logger = logging.getLogger(__name__)


class AgentB_Academy_Enhanced:
    """
    Enhanced Product Recommendation Agent for Academy Sports
    
    Provides personalized product recommendations using:
    - Purchase history analysis
    - Segment-based collaborative filtering
    - Semantic search with Together AI embeddings
    """
    
    def __init__(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        purchases_df: pd.DataFrame,
        micro_segments: Dict = None,
        personas: Dict = None
    ):
        """
        Initialize Enhanced Recommendation Agent
        
        Args:
            customers_df: Customer data with segment assignments
            products_df: Product catalog
            purchases_df: Purchase history
            micro_segments: Micro segment assignments (optional)
            personas: Persona definitions from Agent A (optional)
        """
        self.customers_df = customers_df
        self.products_df = products_df
        self.purchases_df = purchases_df
        self.micro_segments = micro_segments or {}
        self.personas = personas or {}
        
        # Initialize persona-aligned recommender
        self.persona_recommender = PersonaAlignedRecommender(
            customers_df=customers_df,
            products_df=products_df,
            purchases_df=purchases_df,
            personas=personas
        )
        
        # Initialize Enhanced 12-Factor Scorer
        try:
            print("\n🔍 [Enhanced Agent] Initializing 12-factor scorer...")
            self.enhanced_scorer = Enhanced12FactorScorer(
                customers_df=customers_df,
                products_df=products_df,
                purchases_df=purchases_df,
                personas=personas
            )
            print("✅ [Enhanced Agent] 12-factor scorer initialized!")
            logger.info(f"✅ Initialized Enhanced 12-Factor Scorer")
        except Exception as e:
            print(f"❌ [Enhanced Agent] Failed to init 12-factor scorer: {e}")
            self.enhanced_scorer = None
            logger.warning(f"⚠️ Could not initialize 12-factor scorer: {e}")
        
        logger.info(f"Enhanced Recommendation Agent initialized")
        logger.info(f"  - {len(customers_df)} customers")
        logger.info(f"  - {len(products_df)} products")
        logger.info(f"  - {len(purchases_df)} purchases")
        logger.info(f"  - {len(personas)} personas")
    
    def get_similar_products(
        self,
        customer_id: str,
        n_recommendations: int = 3
    ) -> Dict:
        """
        Get similar products based on customer's purchase history
        
        Logic:
        - Analyze customer's historical purchases
        - Calculate average price range (±50%)
        - Find products in same category/subcategory
        - Score by: category match (40%) + brand match (30%) + rating (30%)
        - Return top N within price range
        
        Args:
            customer_id: Customer ID
            n_recommendations: Number of recommendations (default 3)
            
        Returns:
            Dictionary with recommendations and reasoning
        """
        try:
            # Get customer purchases
            customer_purchases = self.purchases_df[
                self.purchases_df['customer_id'] == customer_id
            ]
            
            if len(customer_purchases) == 0:
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'No purchase history available',
                    'type': 'similar_products'
                }
            
            # Get purchased product details
            purchased_product_ids = customer_purchases['product_id'].unique()
            purchased_products = self.products_df[
                self.products_df['product_id'].isin(purchased_product_ids)
            ]
            
            # Get customer info for better price targeting
            customer_info = self.customers_df[self.customers_df['customer_id'] == customer_id]
            
            # Calculate price range based on customer's actual spending
            avg_price = customer_purchases['price_paid'].mean()
            
            # If customer has LTV/spend data, use that to adjust price range
            if len(customer_info) > 0:
                customer_ltv = customer_info.iloc[0].get('total_spend_12mo', avg_price * 10)
                # Adjust price range based on customer value tier
                # IMPORTANT: Higher tier customers should get premium products
                # CRITICAL: STRICT FIXED price ranges for high-value customers
                if customer_ltv >= 2000:  # Ultra-Premium ($2000+/year) - LUXURY ONLY
                    min_price = 200  # MINIMUM $200 for ultra-premium
                    max_price = 600
                    tier_name = "Ultra-Premium"
                    logger.info(f"💎 ULTRA-PREMIUM customer (${customer_ltv:.0f}/year) - LUXURY range ${min_price}-${max_price}")
                elif customer_ltv >= 1500:  # Platinum tier ($1500-1999/year) - PREMIUM ONLY
                    min_price = 150  # MINIMUM $150 for premium (raised from $100)
                    max_price = 500
                    tier_name = "Platinum"
                    logger.info(f"🏆 PLATINUM customer (${customer_ltv:.0f}/year) - PREMIUM range ${min_price}-${max_price}")
                elif customer_ltv >= 1000:  # Gold tier ($1000-1499/year)
                    min_price = 80   # MINIMUM $80 (raised from $60)
                    max_price = 400
                    tier_name = "Gold"
                    logger.info(f"🥇 GOLD customer (${customer_ltv:.0f}/year) - QUALITY range ${min_price}-${max_price}")
                elif customer_ltv >= 600:  # Silver tier ($600-999/year)
                    min_price = max(avg_price * 0.5, 40)
                    max_price = min(avg_price * 1.3, 250)
                    tier_name = "Silver"
                elif customer_ltv >= 300:  # Bronze tier ($300-599/year)
                    min_price = max(avg_price * 0.4, 20)
                    max_price = min(avg_price * 1.2, 150)
                    tier_name = "Bronze"
                else:  # Entry tier (<$300/year)
                    min_price = 10
                    max_price = min(avg_price * 1.2, 100)
                    tier_name = "Entry"
                
                logger.info(f"💎 Customer tier: {tier_name} (LTV: ${customer_ltv:.0f})")
                logger.info(f"💰 Price range: ${min_price:.0f} - ${max_price:.0f} (avg: ${avg_price:.0f})")
            else:
                min_price = avg_price * 0.5
                max_price = avg_price * 1.5
                tier_name = "Unknown"
            
            # Get customer's preferred categories
            # PRIORITY 1: Use customer's dominant_category from profile (most reliable)
            # PRIORITY 2: Use purchase history
            logger.info(f"🔍 Finding category preference for customer {customer_id}")
            logger.info(f"   Customer info shape: {customer_info.shape if len(customer_info) > 0 else 'None'}")
            logger.info(f"   Purchased products: {len(purchased_products)}")
            
            top_category = None
            
            # Try to get dominant_category from customer profile
            if len(customer_info) > 0 and 'dominant_category' in customer_info.columns:
                customer_dominant_cat = customer_info.iloc[0]['dominant_category']
                logger.info(f"   Customer's dominant_category field: '{customer_dominant_cat}' (type: {type(customer_dominant_cat)})")
                
                # Check if it's a valid category (not NaN, None, Unknown, etc.)
                if pd.notna(customer_dominant_cat) and str(customer_dominant_cat).strip() not in ['Unknown', 'None', '']:
                    top_category = str(customer_dominant_cat).strip()
                    logger.info(f"✅ Using customer's dominant_category from profile: '{top_category}'")
                else:
                    logger.warning(f"⚠️ Customer's dominant_category is invalid: '{customer_dominant_cat}'")
            
            # Fallback to purchase history
            if not top_category and len(purchased_products) > 0:
                mode_category = purchased_products['main_category'].mode()
                if len(mode_category) > 0:
                    top_category = mode_category[0]
                    logger.info(f"✅ Using category from purchase history: '{top_category}'")
            
            # If still no category, return empty
            if not top_category:
                logger.warning(f"❌ Cannot determine product preferences for customer {customer_id}")
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': 'Cannot determine product preferences',
                    'type': 'similar_products'
                }
            
            # Get subcategory and brand preferences (with safety checks for empty mode())
            top_subcategory = None
            if len(purchased_products) > 0 and 'subcategory' in purchased_products.columns:
                mode_subcat = purchased_products['subcategory'].mode()
                if len(mode_subcat) > 0:
                    top_subcategory = mode_subcat[0]
            
            preferred_brand = None
            if len(purchased_products) > 2:
                mode_brand = purchased_products['brand'].mode()
                if len(mode_brand) > 0:
                    preferred_brand = mode_brand[0]
            
            logger.info(f"🎯 Final category for recommendations: '{top_category}'")
            
            # Define premium brands for higher-tier customers
            premium_brands = ['YETI', 'The North Face', 'Big Agnes', 'MSR', 'Patagonia', 'Arc\'teryx']
            
            # Extract customer row as Series for consistent access throughout
            customer_row = customer_info.iloc[0] if len(customer_info) > 0 else pd.Series()
            
            # First, try to find candidates in the same category
            candidates = self.products_df[
                (~self.products_df['product_id'].isin(purchased_product_ids)) &  # Not already purchased
                (self.products_df['main_category'] == top_category) &  # MUST match category
                (self.products_df['price'] >= min_price) &  # Within price range
                (self.products_df['price'] <= max_price) &
                (self.products_df['in_stock'] == True)  # In stock
            ].copy()
            
            # For PREMIUM customers ($1500+), PREFER premium brands but don't fail if unavailable
            if len(customer_info) > 0:
                customer_ltv = customer_row.get('total_spend_12mo', 0)
                
                if customer_ltv >= 1500:  # Platinum/Ultra-Premium - PREFER premium brands
                    premium_candidates = candidates[candidates['brand'].isin(premium_brands)].copy()
                    if len(premium_candidates) >= n_recommendations:
                        logger.info(f"✨ PREMIUM customer (${customer_ltv:.0f}) - showing premium brands: {premium_brands}")
                        candidates = premium_candidates
                    elif len(premium_candidates) > 0:
                        # MIX premium + quality brands to reach n_recommendations
                        logger.info(f"⚠️ Only {len(premium_candidates)} premium products, mixing with quality brands")
                        # Keep premium products + add quality products to reach target
                        quality_brands = ['Kelty', 'Coleman']
                        quality_candidates = candidates[~candidates['brand'].isin(premium_brands) & 
                                                       candidates['brand'].isin(quality_brands)].copy()
                        # Combine: premium first, then quality
                        candidates = pd.concat([premium_candidates, quality_candidates]).head(n_recommendations * 2)
                    # If still < n_recommendations, use ALL candidates (no filtering)
                            
                elif customer_ltv >= 1000:  # Gold - PREFER premium brands
                    premium_candidates = candidates[candidates['brand'].isin(premium_brands)].copy()
                    if len(premium_candidates) >= n_recommendations * 0.7:  # At least 70% premium
                        logger.info(f"✨ GOLD customer (${customer_ltv:.0f}) - prioritizing premium brands")
                        candidates = premium_candidates
                    else:
                        logger.info(f"⚠️ Only {len(premium_candidates)} premium products, including all quality brands")
                        # Keep all candidates for Gold customers (don't filter too strictly)
            
            # If not enough candidates, progressively relax constraints BUT ALWAYS KEEP CATEGORY MATCH!
            if len(candidates) < n_recommendations:
                logger.info(f"⚠️ Only {len(candidates)} candidates with strict filters, relaxing price range...")
                # STEP 1: Relax price range but STRICTLY keep category match
                candidates = self.products_df[
                    (~self.products_df['product_id'].isin(purchased_product_ids)) &
                    (self.products_df['main_category'] == top_category) &  # ✅ MANDATORY category match
                    (self.products_df['in_stock'] == True)
                ].copy()
                logger.info(f"   After relaxing price: {len(candidates)} candidates (category '{top_category}' ONLY)")
            
            # STEP 2: If STILL not enough, try COMPLEMENTARY categories (NOT random categories!)
            # Define complementary product categories (products commonly bought together)
            complementary_categories = {
                'Tents + Screen Houses': ['Sleeping Bags + Airbeds', 'Camping Furniture + Accessories', 'Lighting + Safety'],
                'Sleeping Bags + Airbeds': ['Tents + Screen Houses', 'Camping Furniture + Accessories', 'Sleeping Bags + Airbeds'],
                'Hiking Backpacks': ['Hydration + Water Filtration', 'Trekking Poles + Hiking Accessories', 'Navigation + GPS'],
                'Camping Furniture + Accessories': ['Tents + Screen Houses', 'Coolers + Drinkware', 'Sleeping Bags + Airbeds'],
                'Coolers + Drinkware': ['Camping Furniture + Accessories', 'Tents + Screen Houses'],
                'Camping Cookware + Stoves': ['Coolers + Drinkware', 'Camping Furniture + Accessories'],
                'Hydration + Water Filtration': ['Hiking Backpacks', 'Trekking Poles + Hiking Accessories'],
                'Trekking Poles + Hiking Accessories': ['Hiking Backpacks', 'Hydration + Water Filtration'],
                'Lighting + Safety': ['Tents + Screen Houses', 'Camping Furniture + Accessories'],
                'Navigation + GPS': ['Hiking Backpacks', 'Trekking Poles + Hiking Accessories']
            }
            
            if len(candidates) < n_recommendations:
                logger.info(f"⚠️ Still only {len(candidates)} candidates in '{top_category}', trying COMPLEMENTARY categories...")
                complementary_cats = complementary_categories.get(top_category, [])
                
                if complementary_cats:
                    complementary_candidates = self.products_df[
                        (~self.products_df['product_id'].isin(purchased_product_ids)) &
                        (self.products_df['main_category'].isin(complementary_cats)) &  # ✅ Related categories only
                        (self.products_df['in_stock'] == True)
                    ].copy()
                    
                    if len(complementary_candidates) > 0:
                        # Combine: original category first, then complementary
                        candidates = pd.concat([candidates, complementary_candidates]).drop_duplicates('product_id')
                        logger.info(f"   Added {len(complementary_candidates)} complementary products from: {complementary_cats}")
                    else:
                        logger.info(f"   No complementary products found in: {complementary_cats}")
                else:
                    logger.info(f"   No complementary categories defined for '{top_category}'")
                    
                logger.info(f"   Total candidates after complementary: {len(candidates)}")
            
            # FINAL CHECK: If still no candidates, return empty
            if len(candidates) == 0:
                logger.warning(f"No candidate products found for {customer_id} in category '{top_category}' with price range ${min_price:.0f}-${max_price:.0f}")
                return {
                    'customer_id': customer_id,
                    'recommendations': [],
                    'reason': f'No products available in {top_category} category within ${min_price:.0f}-${max_price:.0f} price range',
                    'type': 'similar_products'
                }
            
            # ✨ ROBUST SCORING - Multiple metrics with HEAVY category weighting
            candidates['score'] = 0.0
            
            # 1. CATEGORY MATCH (50% - DOMINANT factor for accurate recommendations) ⭐⭐⭐⭐⭐
            # Exact category match gets HUGE boost
            candidates.loc[candidates['main_category'] == top_category, 'score'] += 0.40
            # Complementary categories get MUCH LOWER score
            complementary_cats = {
                'Tents + Screen Houses': ['Sleeping Bags + Airbeds', 'Camping Furniture + Accessories'],
                'Sleeping Bags + Airbeds': ['Tents + Screen Houses', 'Camping Furniture + Accessories'],
                'Hiking Backpacks': ['Hydration + Water Filtration', 'Trekking Poles + Hiking Accessories'],
                'Camping Furniture + Accessories': ['Tents + Screen Houses', 'Coolers + Drinkware'],
            }.get(top_category, [])
            candidates.loc[candidates['main_category'].isin(complementary_cats), 'score'] += 0.10  # Only 10% vs 40%!
            
            # Subcategory match (additional 10%)
            if top_subcategory:
                candidates.loc[candidates['subcategory'] == top_subcategory, 'score'] += 0.10
            
            logger.info(f"📊 Category scoring: Exact match=40%, Complementary=10%, Subcategory=10%")
            
            # 2. PRICE APPROPRIATENESS (20% - Match customer's spending tier)
            # Products closer to customer's historical average price get higher scores
            price_deviation = abs(candidates['price'] - avg_price) / avg_price
            candidates['score'] += (1 - price_deviation.clip(0, 1)) * 0.20
            
            # 3. BRAND MATCH & LOYALTY (15% - Consider customer's brand preference)
            if preferred_brand:
                # Check if preferred_brand is premium
                brand_loyalty_score = customer_row.get('brand_loyalty', 0)
                if preferred_brand in premium_brands:
                    # High brand loyalty to premium brand - strongly prefer it
                    candidates.loc[candidates['brand'] == preferred_brand, 'score'] += 0.15
                else:
                    # Non-premium brand or lower loyalty - less weight
                    candidates.loc[candidates['brand'] == preferred_brand, 'score'] += 0.08
            
            # 4. EXPERTISE MATCH (15% - Product complexity matching customer expertise)
            customer_expertise = customer_row.get('search_specificity', 3.0) / 5.0 if len(customer_info) > 0 else 0.6  # 0-1 scale
            if 'complexity' in candidates.columns:
                # Expert customers (>0.7) prefer technical products
                # Beginner customers (<0.4) prefer simple products
                for idx, row in candidates.iterrows():
                    complexity = row.get('complexity', 'Moderate')
                    if customer_expertise > 0.7 and complexity in ['Advanced', 'Technical']:
                        candidates.at[idx, 'score'] += 0.15
                    elif customer_expertise < 0.4 and complexity in ['Simple', 'Easy']:
                        candidates.at[idx, 'score'] += 0.15
                    elif 0.4 <= customer_expertise <= 0.7 and complexity == 'Moderate':
                        candidates.at[idx, 'score'] += 0.10
            
            # 5. CUSTOMER VALUE TIER ALIGNMENT (10% - Premium customers get premium products)
            if tier_name in ["Ultra-Premium", "Platinum"]:
                # Premium customers - boost high-end products
                candidates.loc[candidates['price'] > 150, 'score'] += 0.10
            elif tier_name in ["Bronze", "Entry"]:
                # Budget customers - boost value products
                candidates.loc[candidates['price'] < 80, 'score'] += 0.10
            
            # 6. BUNDLE AFFINITY (5% - If customer likes bundles, prefer bundle-compatible items)
            bundle_affinity = customer_row.get('bundle_affinity', 0)
            if bundle_affinity > 0.15 and 'bundle_compatible' in candidates.columns:
                candidates.loc[candidates['bundle_compatible'] == True, 'score'] += 0.05
            
            # 7. PRODUCT RATING (5% - Quality indicator, but lower weight)
            if 'avg_rating' in candidates.columns:
                candidates['score'] += (candidates['avg_rating'] / 5.0) * 0.05
            
            # 8. PURCHASE RECENCY BOOST (5% - Favor categories bought recently)
            if len(customer_purchases) > 0 and len(purchased_products) > 0:
                # Join purchases with products to get categories
                purchases_with_products = customer_purchases.merge(
                    self.products_df[['product_id', 'main_category']],
                    on='product_id',
                    how='left'
                )
                
                # Sort by purchase date (most recent first)
                if 'purchase_date' in purchases_with_products.columns:
                    purchases_sorted = purchases_with_products.sort_values('purchase_date', ascending=False)
                    recent_categories = purchases_sorted.head(3)['main_category'].dropna().tolist()
                else:
                    recent_categories = purchases_with_products.head(3)['main_category'].dropna().tolist()
                
                # Boost recent categories
                if len(recent_categories) > 0:
                    for cat in set(recent_categories):
                        if pd.notna(cat):
                            candidates.loc[candidates['main_category'] == cat, 'score'] += 0.05 / len(set(recent_categories))
            
            # 10. PURCHASE CO-OCCURRENCE (8% - Products customer bought together)
            # Analyze what products this customer tends to buy together
            if len(customer_purchases) > 1:
                # Find products bought in similar time periods (within 30 days)
                customer_purchases_sorted = customer_purchases.copy()
                if 'purchase_date' in customer_purchases_sorted.columns:
                    customer_purchases_sorted['purchase_date'] = pd.to_datetime(customer_purchases_sorted['purchase_date'])
                    
                    # Find co-purchased categories
                    co_purchased_categories = set()
                    for i, purchase in customer_purchases_sorted.iterrows():
                        date = purchase['purchase_date']
                        # Find other purchases within 30 days
                        nearby_purchases = customer_purchases_sorted[
                            (customer_purchases_sorted['purchase_date'] >= date - pd.Timedelta(days=30)) &
                            (customer_purchases_sorted['purchase_date'] <= date + pd.Timedelta(days=30))
                        ]
                        
                        # Get categories of nearby purchases
                        for pid in nearby_purchases['product_id'].unique():
                            product_cat = self.products_df[self.products_df['product_id'] == pid]['main_category'].values
                            if len(product_cat) > 0:
                                co_purchased_categories.add(product_cat[0])
                    
                    # Boost products in co-purchased categories
                    for cat in co_purchased_categories:
                        if cat != top_category:  # Don't double-boost primary category
                            candidates.loc[candidates['main_category'] == cat, 'score'] += 0.08 / len(co_purchased_categories)
                            logger.info(f"   Co-purchase boost: {cat} (+{0.08/len(co_purchased_categories):.3f})")
            
            # 11. SEGMENT AFFINITY (7% - Popular in customer's segment)
            # Boost products that are popular in this customer's macro segment
            if len(customer_info) > 0 and 'cluster' in customer_row:
                customer_cluster = customer_row.get('cluster', -1)
                if customer_cluster >= 0:
                    # Find other customers in same segment
                    segment_customers = self.customers_df[self.customers_df['cluster'] == customer_cluster]['customer_id'].values
                    # Find products bought by segment members
                    segment_purchases = self.purchases_df[self.purchases_df['customer_id'].isin(segment_customers)]
                    segment_product_counts = segment_purchases['product_id'].value_counts()
                    
                    # Boost popular segment products
                    for product_id, count in segment_product_counts.head(10).items():
                        if product_id in candidates['product_id'].values:
                            # Normalize by segment size
                            popularity_score = min(count / len(segment_customers), 0.07)
                            candidates.loc[candidates['product_id'] == product_id, 'score'] += popularity_score
                            logger.info(f"   Segment affinity: {product_id} (+{popularity_score:.3f}, {count} purchases)")
            
            # 12. INDIVIDUAL VARIETY (5% - Make truly unique per customer)
            # Add deterministic randomization based on customer ID to ensure different customers get different products
            # This ensures customers in same segment with same category get DIFFERENT recommendations
            import hashlib
            customer_hash = int(hashlib.md5(customer_id.encode()).hexdigest(), 16)
            np.random.seed(customer_hash % 10000)  # Deterministic but unique per customer
            candidates['individual_variety'] = np.random.random(len(candidates)) * 0.05  # Reduced from 10% to 5%
            candidates['score'] += candidates['individual_variety']
            
            # 9. POPULARITY AMONG SIMILAR CUSTOMERS (Bonus 5%)
            # If product is highly rated and popular, small boost
            if 'num_reviews' in candidates.columns and 'avg_rating' in candidates.columns:
                popular_mask = (candidates['num_reviews'] > 50) & (candidates['avg_rating'] > 4.0)
                candidates.loc[popular_mask, 'score'] += 0.05
            
            logger.info(f"📊 ENHANCED Scoring breakdown for {len(candidates)} candidates:")
            logger.info(f"   1. Category match: 50% (40% exact + 10% subcategory) ⭐⭐⭐⭐⭐ DOMINANT")
            logger.info(f"   2. Price appropriateness: 20% (match spending tier)")
            logger.info(f"   3. Brand loyalty: 15% (customer's preferred brand)")
            logger.info(f"   4. Expertise match: 15% (technical vs simple)")
            logger.info(f"   5. Value tier alignment: 10% (premium vs budget)")
            logger.info(f"   6. Purchase co-occurrence: 8% (bought together)")
            logger.info(f"   7. Segment affinity: 7% (popular in segment)")
            logger.info(f"   8. Bundle compatibility: 5%")
            logger.info(f"   9. Individual variety: 5% (unique per customer)")
            logger.info(f"  10. Product rating: 5% (quality indicator)")
            logger.info(f"  11. Recency boost: 5% (recent categories)")
            logger.info(f"  12. Popularity: 5% (well-reviewed)")
            logger.info(f"   TOTAL: ~150% (some criteria may not apply)")
            logger.info(f"   🎯 Category match is DOMINANT (50%) to ensure accuracy")
            logger.info(f"   ✨ Complementary categories only if not enough in primary category")
            
            # ✨ DIVERSITY SELECTION: Ensure variety in recommendations (different subcategories, brands)
            # Don't just take top N by score - ensure diversity!
            selected_products = []
            candidates_sorted = candidates.sort_values('score', ascending=False)
            
            selected_subcategories = set()
            selected_brands = set()
            
            # First pass: Select highest-scoring products with diversity constraints
            for _, product in candidates_sorted.iterrows():
                if len(selected_products) >= n_recommendations:
                    break
                    
                subcat = product.get('subcategory', 'Unknown')
                brand = product.get('brand', 'Unknown')
                
                # Allow max 2 products from same subcategory
                subcat_count = sum(1 for p in selected_products if p.get('subcategory') == subcat)
                # Allow max 2 products from same brand
                brand_count = sum(1 for p in selected_products if p.get('brand') == brand)
                
                if subcat_count < 2 and brand_count < 2:
                    selected_products.append(product)
                    selected_subcategories.add(subcat)
                    selected_brands.add(brand)
            
            # Second pass: If we still need more products, relax diversity constraints
            if len(selected_products) < n_recommendations:
                for _, product in candidates_sorted.iterrows():
                    if len(selected_products) >= n_recommendations:
                        break
                    if product['product_id'] not in [p['product_id'] for p in selected_products]:
                        selected_products.append(product)
            
            # Convert back to DataFrame
            top_products = pd.DataFrame(selected_products)
            
            logger.info(f"📦 Found {len(candidates)} candidate products for category '{top_category}'")
            logger.info(f"📦 Selected {len(top_products)} products with diversity:")
            logger.info(f"   - {len(selected_subcategories)} different subcategories")
            logger.info(f"   - {len(selected_brands)} different brands")
            for idx, product in enumerate(selected_products, 1):
                logger.info(f"   {idx}. {product['product_name']} ({product['brand']}) - {product['subcategory']} - Score: {product['score']:.2f}")
            
            # Format recommendations with detailed reasons including price justification
            recommendations = []
            for _, product in top_products.iterrows():
                # BUILD PERSONALIZED "WHY THIS SUITS YOU" EXPLANATION
                explanation = []
                
                # 1. Category match with your history
                product_category = product.get('main_category', 'Unknown')
                if product_category == top_category:
                    explanation.append(f"✓ Perfect match for your {top_category} preference")
                else:
                    explanation.append(f"✓ Complements your {top_category} gear")
                
                # 2. Brand match (if applicable)
                if preferred_brand and product.get('brand') == preferred_brand:
                    explanation.append(f"from your trusted brand {preferred_brand}")
                elif product.get('brand'):
                    explanation.append(f"{product['brand']} quality")
                
                # 3. PERSONALIZED price justification based on YOUR tier and spending
                product_price = product['price']
                if tier_name == "Platinum":
                    explanation.append(f"Premium ${product_price:.0f} matches your ${customer_ltv:.0f}/year investment in top-tier gear")
                elif tier_name == "Gold":
                    explanation.append(f"Quality ${product_price:.0f} aligns with your ${customer_ltv:.0f}/year commitment")
                elif tier_name == "Silver":
                    explanation.append(f"Great value at ${product_price:.0f} for your ${customer_ltv:.0f}/year budget")
                else:
                    explanation.append(f"Affordable ${product_price:.0f} fits your ${customer_ltv:.0f}/year spending")
                
                # 4. Quality rating
                rating = product.get('avg_rating', 4.0)
                num_reviews = product.get('num_reviews', 0)
                if rating >= 4.5 and num_reviews > 50:
                    explanation.append(f"Highly rated {rating:.1f}/5 by {num_reviews} customers")
                elif rating >= 4.0:
                    explanation.append(f"Well-reviewed {rating:.1f}/5")
                
                # Combine into single clear reason
                full_reason = ". ".join(explanation) + "."
                
                recommendations.append({
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'brand': product['brand'],
                    'category': product['main_category'],
                    'price': round(product['price'], 2),
                    'rating': round(rating, 1),
                    'num_reviews': int(num_reviews),
                    'score': round(product['score'], 2),
                    'reason': full_reason,
                    'in_stock': bool(product.get('in_stock', True))
                })
            
            return {
                'customer_id': customer_id,
                'recommendations': recommendations,
                'price_range': {
                    'min': round(min_price, 2),
                    'max': round(max_price, 2),
                    'avg': round(avg_price, 2)
                },
                'preferred_category': top_category,
                'type': 'similar_products',
                'reason': f"Based on your {top_category} purchase history"
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Error getting similar products for {customer_id}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'customer_id': customer_id,
                'recommendations': [],
                'error': str(e),
                'type': 'similar_products'
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
        - Get top products purchased by others in same micro segment
        - Filter by customer's avg price range (±50%)
        - Exclude already purchased products
        - Return top N by popularity + rating
        
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
            
            customer = customer.iloc[0]
            
            # Get customer's price range based on LTV tier
            avg_price = customer['avg_order_value']
            customer_ltv = customer.get('total_spend_12mo', avg_price * 10)
            
            # CRITICAL: STRICT FIXED price ranges matching get_similar_products
            if customer_ltv >= 2000:  # Ultra-Premium - LUXURY ONLY
                min_price = 200
                max_price = 600
                tier_name = "Ultra-Premium"
            elif customer_ltv >= 1500:  # Platinum tier - PREMIUM ONLY
                min_price = 150
                max_price = 500
                tier_name = "Platinum"
            elif customer_ltv >= 1000:  # Gold tier
                min_price = 80
                max_price = 400
                tier_name = "Gold"
            elif customer_ltv >= 600:  # Silver tier
                min_price = max(avg_price * 0.5, 40)
                max_price = min(avg_price * 1.3, 250)
                tier_name = "Silver"
            elif customer_ltv >= 300:  # Bronze tier
                min_price = max(avg_price * 0.4, 20)
                max_price = min(avg_price * 1.2, 150)
                tier_name = "Bronze"
            else:  # Entry tier
                min_price = 10
                max_price = min(avg_price * 1.2, 100)
                tier_name = "Entry"
            
            # Get customers in same segment
            if micro_segment_id is not None and 'micro_segment' in self.customers_df.columns:
                segment_customers = self.customers_df[
                    (self.customers_df['micro_segment'] == micro_segment_id) &
                    (self.customers_df['customer_id'] != customer_id)
                ]['customer_id'].tolist()
                segment_type = "micro"
            else:
                # Fall back to macro segment
                macro_cluster = customer['cluster']
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
            
            # Get purchases by segment members
            segment_purchases = self.purchases_df[
                self.purchases_df['customer_id'].isin(segment_customers)
            ]
            
            # Get customer's already purchased products
            customer_purchases = self.purchases_df[
                self.purchases_df['customer_id'] == customer_id
            ]
            already_purchased = customer_purchases['product_id'].unique()
            
            # Count product popularity in segment
            product_popularity = segment_purchases['product_id'].value_counts()
            
            # Get customer's dominant category preference if available
            customer_category = customer.get('dominant_category', None)
            
            # Get top popular products
            popular_product_ids = product_popularity.head(30).index.tolist()  # Get more candidates
            
            # Filter out already purchased and apply price range
            # PRIORITIZE customer's preferred category
            if customer_category:
                candidates = self.products_df[
                    (self.products_df['product_id'].isin(popular_product_ids)) &
                    (~self.products_df['product_id'].isin(already_purchased)) &
                    (self.products_df['main_category'] == customer_category) &  # Match category
                    (self.products_df['price'] >= min_price) &
                    (self.products_df['price'] <= max_price) &
                    (self.products_df['in_stock'] == True)
                ].copy()
                
                # If not enough in preferred category, get any popular products
                if len(candidates) < n_recommendations:
                    candidates = self.products_df[
                        (self.products_df['product_id'].isin(popular_product_ids)) &
                        (~self.products_df['product_id'].isin(already_purchased)) &
                        (self.products_df['price'] >= min_price) &
                        (self.products_df['price'] <= max_price) &
                        (self.products_df['in_stock'] == True)
                    ].copy()
            else:
                candidates = self.products_df[
                    (self.products_df['product_id'].isin(popular_product_ids)) &
                    (~self.products_df['product_id'].isin(already_purchased)) &
                    (self.products_df['price'] >= min_price) &
                    (self.products_df['price'] <= max_price) &
                    (self.products_df['in_stock'] == True)
                ].copy()
            
            if len(candidates) == 0:
                # Relax price constraint
                candidates = self.products_df[
                    (self.products_df['product_id'].isin(popular_product_ids)) &
                    (~self.products_df['product_id'].isin(already_purchased)) &
                    (self.products_df['in_stock'] == True)
                ].copy()
            
            # Add popularity score
            candidates['popularity'] = candidates['product_id'].map(product_popularity)
            candidates['popularity'] = candidates['popularity'] / candidates['popularity'].max()
            
            # Calculate combined score (70% popularity + 30% rating)
            if 'avg_rating' in candidates.columns:
                candidates['score'] = (
                    candidates['popularity'] * 0.7 +
                    (candidates['avg_rating'] / 5.0) * 0.3
                )
            else:
                candidates['score'] = candidates['popularity']
            
            # Get top N
            top_products = candidates.nlargest(n_recommendations, 'score')
            
            # Determine tier for price justification
            if customer_ltv < 300:
                tier_name = "Bronze"
            elif customer_ltv < 600:
                tier_name = "Silver"
            elif customer_ltv < 1000:
                tier_name = "Gold"
            else:
                tier_name = "Platinum"
            
            # Format recommendations with PERSONALIZED explanations
            recommendations = []
            for _, product in top_products.iterrows():
                # PERSONALIZED "WHY THIS SUITS YOU" based on segment popularity
                explanation = []
                
                # 1. Segment popularity
                popularity = product.get('popularity', 0)
                if popularity > 0.7:
                    explanation.append("Most popular in your customer segment")
                elif popularity > 0.4:
                    explanation.append("Highly favored by customers like you")
                else:
                    explanation.append("Well-liked by similar shoppers")
                
                # 2. PERSONALIZED price match to YOUR spending
                product_price = product['price']
                if tier_name == "Platinum":
                    explanation.append(f"Premium ${product_price:.0f} matches your ${customer_ltv:.0f}/year investment")
                elif tier_name == "Gold":
                    explanation.append(f"Quality ${product_price:.0f} suits your ${customer_ltv:.0f}/year spending")
                elif tier_name == "Silver":
                    explanation.append(f"Good value at ${product_price:.0f} for ${customer_ltv:.0f}/year budget")
                else:
                    explanation.append(f"Affordable ${product_price:.0f} fits ${customer_ltv:.0f}/year range")
                
                # 3. Quality indicator
                rating = product.get('avg_rating', 4.0)
                if rating >= 4.5:
                    explanation.append(f"Excellent {rating:.1f}/5 rating")
                
                full_reason = ". ".join(explanation) + "."
                
                recommendations.append({
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'brand': product['brand'],
                    'category': product['main_category'],
                    'price': round(product['price'], 2),
                    'rating': round(rating, 1),
                    'num_reviews': int(product.get('num_reviews', 0)),
                    'popularity': round(popularity, 2),
                    'reason': full_reason,
                    'in_stock': bool(product.get('in_stock', True))
                })
            
            return {
                'customer_id': customer_id,
                'recommendations': recommendations,
                'segment_type': segment_type,
                'segment_size': len(segment_customers),
                'price_range': {
                    'min': round(min_price, 2),
                    'max': round(max_price, 2),
                    'avg': round(avg_price, 2)
                },
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
    
    def get_search_recommendations(
        self,
        customer_id: str,
        search_term: str,
        chromadb_collection=None,
        n_recommendations: int = 3
    ) -> Dict:
        """
        Get recommendations based on semantic search
        
        Logic:
        - Embed search term using Together AI (if available)
        - Query ChromaDB products collection
        - Filter by customer's price range (±50%)
        - Return top N by similarity score
        
        Args:
            customer_id: Customer ID
            search_term: Search query
            chromadb_collection: ChromaDB collection for products (optional)
            n_recommendations: Number of recommendations (default 3)
            
        Returns:
            Dictionary with recommendations and reasoning
        """
        try:
            # Get customer data for price range
            customer = self.customers_df[self.customers_df['customer_id'] == customer_id]
            
            if len(customer) == 0:
                # No customer data, use general search
                avg_price = self.products_df['price'].median()
            else:
                customer = customer.iloc[0]
                avg_price = customer['avg_order_value']
            
            min_price = avg_price * 0.5
            max_price = avg_price * 1.5
            
            # If ChromaDB collection is available, use semantic search
            if chromadb_collection is not None:
                try:
                    # Query ChromaDB
                    results = chromadb_collection.query(
                        query_texts=[search_term],
                        n_results=20,
                        where={
                            "$and": [
                                {"price": {"$gte": float(min_price)}},
                                {"price": {"$lte": float(max_price)}},
                                {"in_stock": True}
                            ]
                        }
                    )
                    
                    if results and results['ids'] and len(results['ids'][0]) > 0:
                        product_ids = results['ids'][0][:n_recommendations]
                        distances = results['distances'][0][:n_recommendations]
                        
                        # Get product details
                        recommended_products = self.products_df[
                            self.products_df['product_id'].isin(product_ids)
                        ]
                        
                        # Add similarity scores
                        similarity_map = dict(zip(product_ids, [1 - d for d in distances]))
                        
                        recommendations = []
                        for _, product in recommended_products.iterrows():
                            recommendations.append({
                                'product_id': product['product_id'],
                                'product_name': product['product_name'],
                                'brand': product['brand'],
                                'category': product['main_category'],
                                'price': round(product['price'], 2),
                                'rating': round(product.get('avg_rating', 4.0), 1),
                                'num_reviews': int(product.get('num_reviews', 0)),
                                'similarity': round(similarity_map.get(product['product_id'], 0.5), 2),
                                'reason': f"Matches your search for '{search_term}'",
                                'in_stock': bool(product.get('in_stock', True))  # Include in_stock field
                            })
                        
                        return {
                            'customer_id': customer_id,
                            'search_term': search_term,
                            'recommendations': recommendations,
                            'type': 'search_based',
                            'method': 'semantic_search',
                            'price_range': {
                                'min': round(min_price, 2),
                                'max': round(max_price, 2)
                            }
                        }
                
                except Exception as e:
                    logger.warning(f"ChromaDB search failed, falling back to keyword search: {e}")
            
            # Fallback: Simple keyword search
            search_lower = search_term.lower()
            candidates = self.products_df[
                (self.products_df['product_name'].str.lower().str.contains(search_lower, na=False) |
                 self.products_df['main_category'].str.lower().str.contains(search_lower, na=False) |
                 self.products_df['brand'].str.lower().str.contains(search_lower, na=False)) &
                (self.products_df['price'] >= min_price) &
                (self.products_df['price'] <= max_price) &
                (self.products_df['in_stock'] == True)
            ].copy()
            
            if len(candidates) == 0:
                # Relax price constraint
                candidates = self.products_df[
                    (self.products_df['product_name'].str.lower().str.contains(search_lower, na=False) |
                     self.products_df['main_category'].str.lower().str.contains(search_lower, na=False) |
                     self.products_df['brand'].str.lower().str.contains(search_lower, na=False)) &
                    (self.products_df['in_stock'] == True)
                ].copy()
            
            # Score by rating
            if 'avg_rating' in candidates.columns:
                candidates = candidates.nlargest(n_recommendations, 'avg_rating')
            else:
                candidates = candidates.head(n_recommendations)
            
            # Format recommendations
            recommendations = []
            for _, product in candidates.iterrows():
                recommendations.append({
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'brand': product['brand'],
                    'category': product['main_category'],
                    'price': round(product['price'], 2),
                    'rating': round(product.get('avg_rating', 4.0), 1),
                    'num_reviews': int(product.get('num_reviews', 0)),
                    'reason': f"Matches your search for '{search_term}'",
                    'in_stock': bool(product.get('in_stock', True))  # Include in_stock field
                })
            
            return {
                'customer_id': customer_id,
                'search_term': search_term,
                'recommendations': recommendations,
                'type': 'search_based',
                'method': 'keyword_search',
                'price_range': {
                    'min': round(min_price, 2),
                    'max': round(max_price, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting search recommendations: {e}")
            return {
                'customer_id': customer_id,
                'search_term': search_term,
                'recommendations': [],
                'error': str(e),
                'type': 'search_based'
            }
    
    def get_all_recommendations(
        self,
        customer_id: str,
        search_term: Optional[str] = None,
        chromadb_collection=None,
        use_persona_aligned: bool = True
    ) -> Dict:
        """
        Get all three types of recommendations for a customer
        
        Args:
            customer_id: Customer ID
            search_term: Optional search term for dynamic recommendations
            chromadb_collection: ChromaDB collection (optional)
            use_persona_aligned: Use persona-aligned recommendations (default True)
            
        Returns:
            Dictionary with all recommendation types (lists of products)
        """
        # PRIORITY: Use persona-aligned recommendations if available
        if use_persona_aligned and len(self.personas) > 0:
            persona_result = self.persona_recommender.get_persona_aligned_recommendations(customer_id)
            
            if persona_result.get('recommendations'):
                logger.info(f"✅ Using PERSONA-ALIGNED recommendations for {customer_id}")
                similar_result = persona_result
            else:
                logger.info(f"⚠️ Persona-aligned failed, falling back to similar products")
                similar_result = self.get_similar_products(customer_id)
        else:
            logger.info(f"📊 Using standard similar products (no personas available)")
            similar_result = self.get_similar_products(customer_id)
        
        segment_result = self.get_segment_recommendations(customer_id)
        
        # Extract the actual product lists (handle both dict and non-dict responses)
        if isinstance(similar_result, dict):
            similar_products = similar_result.get('recommendations', [])
        else:
            logger.error(f"Invalid similar_result type: {type(similar_result)}, value: {similar_result}")
            similar_products = []
        
        if isinstance(segment_result, dict):
            segment_products = segment_result.get('recommendations', [])
        else:
            logger.error(f"Invalid segment_result type: {type(segment_result)}, value: {segment_result}")
            segment_products = []
        
        # Build result with product lists (not nested dicts)
        result = {
            'customer_id': customer_id,
            # Return product lists that match API expectations
            'tailored_recommendations': similar_products,  # List of products
            'similar_products': similar_products,  # List of products (backward compatibility)
            'segment_recommendations': segment_products,  # List of products
            'you_might_like': segment_products,  # List of products (backward compatibility)
            'customer_info': {'customer_id': customer_id},
            'recommendation_metadata': {
                'method': 'persona_aligned' if (use_persona_aligned and len(self.personas) > 0) else 'enhanced',
                'persona_name': similar_result.get('persona', None) if use_persona_aligned else None
            }
        }
        
        if search_term:
            search_result = self.get_search_recommendations(
                customer_id,
                search_term,
                chromadb_collection
            )
            if isinstance(search_result, dict):
                result['search_results'] = search_result.get('recommendations', [])
            else:
                result['search_results'] = []
        
        # ENRICH RECOMMENDATIONS WITH 12-FACTOR DETAILED CALCULATIONS
        print("\n" + "="*80)
        print("🔍 [Enhanced Agent] ENRICHING CUSTOMER RECOMMENDATIONS WITH 12-FACTOR")
        print("="*80)
        print(f"enhanced_scorer available: {self.enhanced_scorer is not None}")
        print(f"Tailored recommendations: {len(similar_products)}")
        print(f"Segment recommendations: {len(segment_products)}")
        
        if self.enhanced_scorer:
            try:
                # Get customer data
                customer_row = self.customers_df[self.customers_df['customer_id'] == customer_id]
                if not customer_row.empty:
                    customer_info = customer_row.iloc[0].to_dict()
                    print(f"✅ Found customer: {customer_id}")
                    print(f"   AOV: ${customer_info.get('avg_order_value', 0):.2f}")
                    print(f"   Cluster: {customer_info.get('cluster', 'N/A')}")
                    
                    # Get persona info if available
                    persona_info = {}
                    if customer_info.get('cluster') is not None:
                        cluster_id = customer_info['cluster']
                        if cluster_id in self.personas:
                            persona_info = self.personas[cluster_id]
                            print(f"   Persona: {persona_info.get('persona_name', 'N/A')}")
                    
                    # Enrich each recommendation type
                    enriched_count = 0
                    for rec_list_name, rec_list in [('tailored', result['tailored_recommendations']), ('segment', result['segment_recommendations'])]:
                        print(f"\n📦 Enriching {len(rec_list)} {rec_list_name} recommendations...")
                        for idx, rec in enumerate(rec_list):
                            try:
                                # Get product data
                                product_id = rec.get('product_id')
                                product_row = self.products_df[self.products_df['product_id'] == product_id]
                                if not product_row.empty:
                                    product = product_row.iloc[0].to_dict()
                                    
                                    if idx == 0:
                                        print(f"   Product #1: {product.get('product_name', 'unknown')}")
                                    
                                    # Calculate 12-factor score
                                    score_12, detailed_breakdown = self.enhanced_scorer.score_product(
                                        customer=customer_info,
                                        product=product,
                                        persona_info=persona_info
                                    )
                                    
                                    # Add to recommendation
                                    rec['scoring_method'] = '12_factor'
                                    rec['detailed_calculation'] = detailed_breakdown
                                    rec['score'] = score_12
                                    rec['compatibility'] = score_12 * 100
                                    
                                    if idx == 0:
                                        print(f"   ✅ Score: {score_12:.4f} ({score_12*100:.1f}%)")
                                        print(f"   ✅ Breakdown keys: {list(detailed_breakdown.keys())[:5]}...")
                                    
                                    enriched_count += 1
                                else:
                                    print(f"   ⚠️ Product {product_id} not found in products_df")
                                    rec['scoring_method'] = 'enhanced'
                            except Exception as e:
                                print(f"   ❌ Failed to enrich {rec.get('product_id')}: {e}")
                                import traceback
                                traceback.print_exc()
                                rec['scoring_method'] = 'enhanced'
                    
                    print(f"\n✅✅✅ ENRICHED {enriched_count} RECOMMENDATIONS WITH 12-FACTOR DATA ✅✅✅")
                else:
                    print(f"❌ Customer {customer_id} not found in customers_df")
            except Exception as e:
                print(f"❌ Failed to enrich recommendations: {e}")
                import traceback
                traceback.print_exc()
                logger.warning(f"Could not enrich with 12-factor: {e}")
        else:
            print("⚠️ Enhanced scorer not available - skipping enrichment")
        
        print("="*80 + "\n")
        
        return result


if __name__ == "__main__":
    print("="*70)
    print("Agent B Enhanced - Academy Sports Product Recommendations")
    print("="*70)
    print("Provides three types of recommendations:")
    print("1. Similar Products (based on purchase history)")
    print("2. You Might Like (based on segment)")
    print("3. Dynamic Search (semantic matching)")
    print("="*70)


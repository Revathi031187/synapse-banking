"""
Agent B - Academy Sports Product Recommendations
Uses feature-based lift scoring to provide personalized camping gear recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.feature_scorer import FeatureScorer, load_feature_scorer
from agents.enhanced_12_factor_scorer import Enhanced12FactorScorer

logger = logging.getLogger(__name__)


class AgentB_Academy:
    """
    Agent B for Academy Sports: Product Recommendations using Feature-Based Scoring
    
    Recommends camping products based on:
    1. Customer persona (from Agent A)
    2. Product features
    3. Lift factors for persona-feature combinations
    """
    
    def __init__(self, data_path: str = 'data/preloaded/academy_sports', agent_a=None):
        """
        Initialize Agent B
        
        Args:
            data_path: Path to preloaded Academy Sports data
            agent_a: Reference to Agent A for customer persona lookup
        """
        self.data_path = Path(data_path)
        self.products_df = None
        self.feature_scorer = None
        self.personas = {}
        self.agent_a = agent_a
        self.customers_df = None
        self.purchases_df = None
        self.current_dataset_version = None  # Track which dataset is loaded
        
        logger.info(f"Agent B Academy initialized with data path: {data_path}")
    
    def load_data(self, dataset_version='v1'):
        """
        Load product, feature affinity, and customer data
        
        Args:
            dataset_version: 'v1' or 'v2' dataset version
        """
        try:
            # Load products
            if dataset_version == 'v2':
                products_path = self.data_path / 'products_v2.csv'
                feature_affinity_path = self.data_path / 'feature_affinity_v2.csv'
                customers_path = self.data_path / 'customers_v2.csv'
                purchases_path = self.data_path / 'purchases_v2.csv'
            else:
                products_path = self.data_path / 'products.csv'
                feature_affinity_path = self.data_path / 'feature_affinity.csv'
                customers_path = self.data_path / 'customers.csv'
                purchases_path = self.data_path / 'purchases.csv'
            
            self.products_df = pd.read_csv(products_path)
            logger.info(f"✅ Loaded {len(self.products_df)} products from {products_path.name}")
            
            if len(self.products_df) == 0:
                logger.error("❌ Products dataframe is empty!")
                return False
            
            # Load feature scorer
            self.feature_scorer = load_feature_scorer(str(feature_affinity_path))
            logger.info(f"✅ Loaded feature scorer from {feature_affinity_path.name}")
            
            # Load customer and purchase data for customer-specific recommendations
            if customers_path.exists():
                self.customers_df = pd.read_csv(customers_path)
                logger.info(f"✅ Loaded {len(self.customers_df)} customers from {customers_path.name}")
            
            if purchases_path.exists():
                self.purchases_df = pd.read_csv(purchases_path)
                logger.info(f"✅ Loaded {len(self.purchases_df)} purchases from {purchases_path.name}")
            else:
                logger.info("ℹ️  No purchases.csv found (using customer data directly)")
            
            # Initialize Enhanced 12-Factor Scorer
            print("\n" + "="*80)
            print("🔍 INITIALIZING 12-FACTOR SCORER")
            print("="*80)
            print(f"customers_df exists: {self.customers_df is not None}")
            print(f"purchases_df exists: {self.purchases_df is not None}")
            if self.customers_df is not None and self.purchases_df is not None:
                print("✅ Attempting to initialize...")
                try:
                    self.enhanced_scorer = Enhanced12FactorScorer(
                        customers_df=self.customers_df,
                        products_df=self.products_df,
                        purchases_df=self.purchases_df,
                        personas=self.personas
                    )
                    print("✅✅✅ 12-FACTOR SCORER INITIALIZED! ✅✅✅")
                    logger.info(f"✅ Initialized Enhanced 12-Factor Scorer")
                except Exception as e:
                    print(f"❌ INIT FAILED: {e}")
                    import traceback
                    traceback.print_exc()
                    self.enhanced_scorer = None
            else:
                self.enhanced_scorer = None
                print("❌ Cannot initialize - missing data")
                logger.warning("⚠️ Cannot initialize 12-factor scorer (missing customer/purchase data)")
            print("="*80 + "\n")
            
            return True
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def execute(self, params: Dict) -> Dict:
        """
        Execute Agent B: Generate personalized product recommendations
        
        Args:
            params: Dictionary with:
                - customer_id: Optional customer ID (will auto-detect persona)
                - persona: Persona name (required if no customer_id)
                - search_query: Optional search filter
                - category: Optional category filter
                - top_n: Number of recommendations (default: 10)
                - explain: Whether to include explanations (default: True)
                - dataset_version: 'v1' or 'v2' (default: 'v1')
                
        Returns:
            Dictionary with recommendations and insights
        """
        # Load data if not already loaded OR if dataset version changed
        dataset_version = params.get('dataset_version', 'v1')
        if (self.products_df is None or 
            self.feature_scorer is None or 
            self.current_dataset_version != dataset_version):
            logger.info(f"Loading Agent B data for dataset version: {dataset_version}")
            if not self.load_data(dataset_version=dataset_version):
                return {'error': 'Failed to load product/feature data'}
            self.current_dataset_version = dataset_version
        
        # Extract parameters
        customer_id = params.get('customer_id')
        persona = params.get('persona')
        search_query = params.get('search_query', '').lower()
        category = params.get('category')
        top_n = params.get('top_n', 10)
        explain = params.get('explain', True)
        
        # Get customer info if customer_id provided
        customer_info = None
        if customer_id:
            customer_info = self._get_customer_info(customer_id)
            if customer_info:
                # Use customer's actual persona
                if self.agent_a and hasattr(self.agent_a, 'customers_df') and self.agent_a.customers_df is not None:
                    # Get persona from Agent A's clustering results
                    customer_row = self.agent_a.customers_df[self.agent_a.customers_df['customer_id'] == customer_id]
                    if not customer_row.empty and 'cluster' in customer_row.columns:
                        cluster_id = customer_row['cluster'].iloc[0]
                        persona = self._get_persona_from_cluster(cluster_id)
                        logger.info(f"Using persona '{persona}' from Agent A for customer {customer_id}")
                    elif 'true_persona' in customer_row.columns:
                        persona = customer_row['true_persona'].iloc[0]
                        logger.info(f"Using true persona '{persona}' for customer {customer_id}")
                elif customer_info.get('persona'):
                    persona = customer_info['persona']
                    logger.info(f"Using persona '{persona}' from customer data for {customer_id}")
        
        if not persona:
            return {'error': 'Persona is required (or provide customer_id)'}
        
        # Normalize persona name
        persona = self._normalize_persona_name(persona)
        
        # Calculate price range based on customer OR segment/persona
        if customer_info:
            min_price, max_price, tier_name = self._calculate_price_range(customer_info)
        else:
            # NO customer_info = segment-based recommendation
            # Determine price range and tier from PERSONA/SEGMENT NAME
            min_price, max_price, tier_name = self._calculate_segment_price_range(persona)
        
        logger.info(f"💎 {'Customer' if customer_info else 'Segment'} tier: {tier_name} | Price range: ${min_price:.0f} - ${max_price:.0f}")
        
        # Filter products by search, category, AND price range
        filtered_products = self._filter_products(search_query, category, min_price, max_price)
        
        # For PREMIUM segments, filter to ONLY premium brands
        if not customer_info and tier_name in ["Premium", "Ultra-Premium", "Platinum", "Gold"]:
            premium_brands = ['YETI', 'The North Face', 'Big Agnes', 'MSR', 'Patagonia', "Arc'teryx", 'Osprey', 'REI Co-op']
            
            # Convert list to DataFrame for filtering
            if filtered_products:
                df_temp = pd.DataFrame(filtered_products)
                premium_products = df_temp[df_temp['brand'].isin(premium_brands)]
                
                if len(premium_products) > 0:
                    logger.info(f"✨ {tier_name} SEGMENT - filtered to {len(premium_products)} premium brand products")
                    filtered_products = premium_products.to_dict('records')  # Convert back to list
                else:
                    logger.warning(f"⚠️ No premium products found for {tier_name} segment")
        
        if len(filtered_products) == 0:
            logger.warning(f"⚠️ No products found in price range ${min_price:.0f}-${max_price:.0f}. Relaxing constraints...")
            # Fallback: remove price constraints but keep search/category
            filtered_products = self._filter_products(search_query, category, 0, 999999)
        
        if len(filtered_products) == 0:
            return {
                'status': 'no_products',
                'message': 'No products match the search criteria',
                'recommendations': []
            }
        
        # Score and rank products
        recommendations = self._score_and_rank(persona, filtered_products, top_n, explain, customer_info, tier_name)
        
        # Generate insights
        insights = self._generate_insights(persona, recommendations)
        
        # Prepare response
        return {
            'status': 'success',
            'persona': persona,
            'search_query': search_query,
            'category': category,
            'total_products_considered': len(filtered_products),
            'recommendations': recommendations,
            'insights': insights
        }
    
    def _calculate_segment_price_range(self, persona: str) -> tuple:
        """
        Calculate price range based on SEGMENT/PERSONA name
        
        Args:
            persona: Segment/persona name (e.g., "Premium Gear Experts", "Bargain Hunters")
            
        Returns:
            Tuple of (min_price, max_price, tier_name)
        """
        persona_lower = persona.lower()
        
        # PREMIUM/EXPERT SEGMENTS - High price, premium brands
        if any(word in persona_lower for word in ['premium', 'expert', 'specialist', 'affluent', 'luxury', 'elite', 'advanced']):
            return (150, 600, "Premium")  # $150-600 for premium segments
        
        # BUDGET/VALUE SEGMENTS - Low price, value brands
        elif any(word in persona_lower for word in ['bargain', 'budget', 'deal', 'value', 'frugal', 'saver', 'entry', 'casual', 'newcomer']):
            return (10, 100, "Budget")  # $10-100 for budget segments
        
        # ACTIVE/FREQUENT SEGMENTS - Mid to high price
        elif any(word in persona_lower for word in ['active', 'frequent', 'power', 'collector', 'upgrader']):
            return (80, 400, "Gold")  # $80-400 for active segments
        
        # BEGINNER/STARTER SEGMENTS - Low to mid price
        elif any(word in persona_lower for word in ['starter', 'beginner', 'newcomer', 'learning', 'guided']):
            return (20, 150, "Bronze")  # $20-150 for beginners
        
        # MAINSTREAM/BALANCED SEGMENTS - Mid price
        elif any(word in persona_lower for word in ['mainstream', 'balanced', 'regular', 'moderate', 'steady']):
            return (40, 250, "Silver")  # $40-250 for mainstream
        
        # DEFAULT - Broad range
        else:
            logger.warning(f"Unknown segment type '{persona}', using default range")
            return (20, 400, "Unknown")
    
    def _calculate_price_range(self, customer_info: Dict = None) -> tuple:
        """
        Calculate appropriate price range based on customer's LTV tier
        FIXED: Higher minimum prices for premium customers to match spending tier
        
        Args:
            customer_info: Customer information dictionary
            
        Returns:
            Tuple of (min_price, max_price, tier_name)
        """
        if not customer_info:
            # Should not reach here - use _calculate_segment_price_range instead
            logger.warning("No customer info provided to _calculate_price_range")
            return (20, 500, "Unknown")
        
        # Get customer's annual spend (LTV)
        customer_ltv = customer_info.get('total_spend_12mo', customer_info.get('ltv', 0))
        
        # Determine tier and price range - FIXED: Raised minimum prices for premium tiers
        if customer_ltv >= 2000:  # Ultra-Premium tier ($2000+/year) - LUXURY ONLY
            return (200, 600, "Ultra-Premium")  # Minimum $200 for ultra-premium customers
        elif customer_ltv >= 1500:  # Platinum tier ($1500-$1999/year) - PREMIUM ONLY
            return (150, 600, "Platinum")  # Raised from $100 - premium products only
        elif customer_ltv >= 1000:  # Gold tier ($1000-$1499/year)
            return (100, 400, "Gold")  # Raised from $60 - quality products
        elif customer_ltv >= 600:  # Silver tier ($600-999/year)
            return (50, 250, "Silver")  # Raised from $40
        elif customer_ltv >= 300:  # Bronze tier ($300-599/year)
            return (25, 150, "Bronze")  # Raised from $20
        else:  # Entry tier (<$300/year)
            return (10, 100, "Entry")
    
    def _normalize_persona_name(self, persona: str) -> str:
        """
        Normalize persona name to match feature affinity data
        
        Args:
            persona: Input persona name
            
        Returns:
            Normalized persona name
        """
        persona_mapping = {
            'novice': 'Novice',
            'first-time camper': 'Novice',
            'first_time_camper': 'Novice',
            'beginner': 'Novice',
            
            'family': 'Family_Socializer',
            'family socializer': 'Family_Socializer',
            'family_socializer': 'Family_Socializer',
            'occasional camper': 'Family_Socializer',
            
            'pro': 'Seasoned_Pro',
            'seasoned pro': 'Seasoned_Pro',
            'seasoned_pro': 'Seasoned_Pro',
            'expert': 'Seasoned_Pro',
            'professional': 'Seasoned_Pro'
        }
        
        normalized = persona_mapping.get(persona.lower(), persona)
        return normalized
    

    def _create_synthetic_customer_from_persona(self, persona: str, tier_name: str) -> Dict:
        """
        Create a synthetic customer profile from persona characteristics
        
        Args:
            persona: Persona name (e.g., "Premium_Gear_Experts")
            tier_name: Customer tier (e.g., "Premium", "Budget")
            
        Returns:
            Synthetic customer dictionary with all required fields
        """
        persona_lower = persona.lower()
        
        # Determine dominant category
        if 'hiking' in persona_lower or 'trail' in persona_lower or 'backpack' in persona_lower:
            dominant_category = 'Hiking Backpacks'
        elif 'tent' in persona_lower or 'camp' in persona_lower:
            dominant_category = 'Tents + Screen Houses'
        elif 'sleep' in persona_lower:
            dominant_category = 'Sleeping Bags + Airbeds'
        elif 'cook' in persona_lower or 'food' in persona_lower:
            dominant_category = 'Campsite Cooking'
        else:
            dominant_category = 'Hiking Backpacks'
        
        # Determine price tier
        if tier_name == "Premium" or 'premium' in persona_lower or 'expert' in persona_lower or 'specialist' in persona_lower:
            avg_order_value = 320.0
            total_spend = 2400.0
            purchase_frequency = 7.5
            expertise_level = 'expert'
        elif tier_name == "Gold" or 'active' in persona_lower or 'frequent' in persona_lower:
            avg_order_value = 180.0
            total_spend = 1440.0
            purchase_frequency = 8.0
            expertise_level = 'intermediate'
        elif tier_name == "Silver" or 'regular' in persona_lower or 'mainstream' in persona_lower:
            avg_order_value = 120.0
            total_spend = 840.0
            purchase_frequency = 7.0
            expertise_level = 'intermediate'
        elif tier_name == "Budget" or 'budget' in persona_lower or 'deal' in persona_lower or 'value' in persona_lower:
            avg_order_value = 65.0
            total_spend = 390.0
            purchase_frequency = 6.0
            expertise_level = 'beginner'
        else:
            avg_order_value = 150.0
            total_spend = 1050.0
            purchase_frequency = 7.0
            expertise_level = 'intermediate'
        
        # Create synthetic customer
        synthetic_customer = {
            'customer_id': f'synthetic_{persona}',
            'avg_order_value': avg_order_value,
            'total_spend_12mo': total_spend,
            'purchase_frequency': purchase_frequency,
            'dominant_category': dominant_category,
            'expertise_level': expertise_level,
            'persona': persona,
            'tier': tier_name,
            'brand_purchase_history': {},
            'category_purchase_history': {dominant_category: int(purchase_frequency * 0.6)},
            'total_spend': total_spend
        }
        
        # Add brand history based on tier
        if tier_name == "Premium":
            synthetic_customer['brand_purchase_history'] = {
                'Big Agnes': 3, 'YETI': 2, 'The North Face': 2, 'Osprey': 3
            }
        elif tier_name in ["Gold", "Silver"]:
            synthetic_customer['brand_purchase_history'] = {
                'Kelty': 2, 'Coleman': 2, 'REI Co-op': 1
            }
        else:
            synthetic_customer['brand_purchase_history'] = {
                'Coleman': 3, 'Kelty': 1
            }
        
        logger.info(f"✅ Created synthetic customer: AOV=${avg_order_value:.0f}, Category={dominant_category}, Expertise={expertise_level}")
        return synthetic_customer

    
    def _filter_products(self, search_query: str, category: str = None, min_price: float = 0, max_price: float = 999999) -> List[Dict]:
        """
        Filter products based on search query, category, and price range
        
        Args:
            search_query: Search text
            category: Category filter
            min_price: Minimum price
            max_price: Maximum price
            
        Returns:
            List of filtered product dictionaries
        """
        df = self.products_df.copy()
        
        # Filter by price range (CRITICAL for proper tier-based recommendations)
        if min_price > 0 or max_price < 999999:
            df = df[(df['price'] >= min_price) & (df['price'] <= max_price)]
            logger.info(f"💰 After price filter (${min_price:.0f}-${max_price:.0f}): {len(df)} products")
        
        # Filter by category
        if category:
            df = df[df['main_category'].str.contains(category, case=False, na=False)]
        
        # Filter by search query
        if search_query:
            mask = (
                df['product_name'].str.contains(search_query, case=False, na=False) |
                df['brand'].str.contains(search_query, case=False, na=False) |
                df['main_category'].str.contains(search_query, case=False, na=False) |
                df['subcategory'].str.contains(search_query, case=False, na=False)
            )
            df = df[mask]
        
        # Convert to list of dictionaries
        products = df.to_dict('records')
        return products
    
    def _score_and_rank(self, persona: str, products: List[Dict], top_n: int, explain: bool, customer_info: Dict = None, tier_name: str = "Unknown") -> List[Dict]:
        """
        Score products and rank by relevance to persona
        
        Args:
            persona: Persona name
            products: List of product dictionaries
            top_n: Number of top products to return
            explain: Whether to include detailed explanations
            customer_info: Customer information for price justification
            tier_name: Customer tier name (Platinum/Gold/Silver/Bronze)
            
        Returns:
            List of ranked product recommendations
        """
        recommendations = []
        
        # Get customer LTV for price justification
        customer_ltv = 0
        if customer_info:
            customer_ltv = customer_info.get('total_spend_12mo', customer_info.get('ltv', 0))
        
        print(f"\n🔍 Scoring {len(products)} products for {persona}...")
        print(f"   enhanced_scorer: {self.enhanced_scorer is not None}")
        print(f"   customer_info: {customer_info is not None}")
        
        for idx, product in enumerate(products):
            # Try to use Enhanced 12-Factor Scorer if available
            detailed_breakdown = None
            
            if self.enhanced_scorer:
                try:
                    # If no customer_info, create synthetic customer from persona
                    if not customer_info:
                        customer_info = self._create_synthetic_customer_from_persona(persona, tier_name)
                        if idx == 0:
                            print(f"   ✅ Created synthetic customer for {persona}")
                    
                    # Get persona info for segment affinity
                    persona_info = self.personas.get(persona, {}) if isinstance(self.personas, dict) else {}
                    
                    # Use 12-factor scorer
                    score, detailed_breakdown = self.enhanced_scorer.score_product(
                        customer=customer_info,
                        product=product,
                        persona_info=persona_info
                    )
                    
                    if idx == 0:
                        print(f"   ✅✅✅ USED 12-FACTOR SCORER! Score: {score:.4f}")
                    
                    # Generate comprehensive explanation from 12 factors
                    rec_text = f"Comprehensive match score based on 12 factors (see detailed calculation below)"
                    logger.info(f"✅ Used 12-factor scorer for {product.get('product_name', 'unknown')}: {score:.3f}")
                    
                except Exception as e:
                    if idx == 0:
                        print(f"   ❌ 12-factor scorer FAILED: {e}")
                    logger.error(f"❌ 12-factor scorer failed: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to feature scorer
                    score, explanation = self.feature_scorer.score_product(persona, product, explain=True)
                    rec_text = self.feature_scorer.generate_recommendation_text(persona, product, explanation)
            else:
                if idx == 0:
                    print(f"   ⚠️ No enhanced scorer - using feature scorer")
                # Use original feature scorer
                score, explanation = self.feature_scorer.score_product(persona, product, explain=True)
                rec_text = self.feature_scorer.generate_recommendation_text(persona, product, explanation)
            
            # Add price justification to recommendation text
            if explain and customer_ltv > 0:
                price = product.get('price', 0)
                if tier_name == "Platinum":
                    price_justification = f" This ${price:.0f} premium product matches your Platinum tier status (${customer_ltv:.0f}/year spending)."
                elif tier_name == "Gold":
                    price_justification = f" This ${price:.0f} quality product suits your Gold tier preferences (${customer_ltv:.0f}/year)."
                elif tier_name == "Silver":
                    price_justification = f" This ${price:.0f} product fits your Silver tier budget (${customer_ltv:.0f}/year)."
                elif tier_name == "Bronze":
                    price_justification = f" This ${price:.0f} value product matches your budget-conscious approach (${customer_ltv:.0f}/year)."
                else:
                    price_justification = ""
                
                rec_text = rec_text + price_justification if price_justification else rec_text
            
            # Build recommendation object
            recommendation = {
                'product_id': product.get('product_id'),
                'product_name': product.get('product_name'),
                'brand': product.get('brand'),
                'price': product.get('price'),
                'category': product.get('main_category'),
                'subcategory': product.get('subcategory'),
                'score': round(score, 4),
                'compatibility': round(score * 100, 1),  # Convert to percentage for frontend
                'match_level': self._get_match_level(score),
                'recommendation_text': rec_text if explain else None,
                'reason': rec_text if explain else None,  # Alias for compatibility
                'in_stock': product.get('in_stock', True),
                'avg_rating': product.get('avg_rating'),
                'num_reviews': product.get('num_reviews')
            }
            
            # Add detailed explanation if requested
            if explain:
                # If we have 12-factor breakdown, add it
                if detailed_breakdown:
                    recommendation['detailed_calculation'] = detailed_breakdown
                    recommendation['scoring_method'] = '12_factor'
                else:
                    # Legacy feature scorer explanation
                    feature_contributions = explanation.get('feature_contributions', {}) if 'explanation' in locals() else {}
                    recommendation['features'] = {
                        'setup_type': product.get('setup_type'),
                        'complexity': product.get('complexity'),
                        'bundle_compatible': product.get('bundle_compatible'),
                        'weight_class': product.get('weight_class'),
                        'weatherproof': product.get('weatherproof')
                    }
                    recommendation['feature_lifts'] = feature_contributions
                    recommendation['scoring_method'] = 'feature_based'
            
            recommendations.append(recommendation)
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Add RANK EXPLANATIONS - Why #1, #2, #3, etc.
        top_recommendations = recommendations[:top_n]
        
        for rank, rec in enumerate(top_recommendations, 1):
            # Generate rank explanation
            rank_explanation = self._generate_rank_explanation(
                rank=rank,
                product=rec,
                all_products=top_recommendations,
                persona=persona,
                tier_name=tier_name
            )
            
            # Add rank explanation to the recommendation
            rec['rank'] = rank
            rec['rank_explanation'] = rank_explanation
            
            # Update reason to include rank explanation
            if explain and rec.get('reason'):
                rec['reason'] = f"**#{rank} Recommended:** {rank_explanation}\n\n{rec['reason']}"
        
        return top_recommendations
    
    def _generate_rank_explanation(self, rank: int, product: Dict, all_products: List[Dict], persona: str, tier_name: str) -> str:
        """
        Generate explanation for WHY this product is ranked at this position
        
        Args:
            rank: Product rank (1, 2, 3, etc.)
            product: Current product
            all_products: All top products for comparison
            persona: Persona/segment name
            tier_name: Price tier
            
        Returns:
            Clear explanation of why this rank
        """
        score = product['score']
        price = product.get('price', 0)
        brand = product.get('brand', 'Unknown')
        compatibility = product.get('compatibility', 0)
        
        explanations = []
        
        # Rank 1 - THE BEST
        if rank == 1:
            explanations.append(f"Top match with {compatibility:.1f}% compatibility for {persona}")
            
            # Why it's #1
            if score >= 0.9:
                explanations.append("Nearly perfect feature alignment")
            elif score >= 0.8:
                explanations.append("Excellent feature match")
            else:
                explanations.append("Best available option")
            
            # Brand factor for rank 1
            premium_brands = ['YETI', 'The North Face', 'Big Agnes', 'MSR', 'Patagonia']
            if brand in premium_brands:
                explanations.append(f"{brand} premium quality")
            
        # Rank 2 - STRONG ALTERNATIVE
        elif rank == 2:
            explanations.append(f"Strong alternative with {compatibility:.1f}% match")
            
            # Why not #1?
            if len(all_products) > 0:
                top_product = all_products[0]
                score_diff = (top_product['score'] - score) * 100
                
                if score_diff < 5:
                    explanations.append("Nearly as good as top choice")
                elif price < top_product.get('price', price):
                    explanations.append(f"Better value at ${price:.0f} vs ${top_product.get('price', 0):.0f}")
                else:
                    explanations.append("Slightly different feature focus")
        
        # Rank 3 - GOOD OPTION
        elif rank == 3:
            explanations.append(f"Solid option with {compatibility:.1f}% compatibility")
            
            if len(all_products) > 1:
                if price < all_products[0].get('price', price):
                    explanations.append("Most budget-friendly of top picks")
                else:
                    explanations.append("Alternative features worth considering")
        
        # Rank 4-10 - ADDITIONAL OPTIONS
        else:
            explanations.append(f"Good match ({compatibility:.1f}%) worth considering")
            
            # Find something unique about this product
            if price < sum(p.get('price', 0) for p in all_products[:3]) / 3:
                explanations.append("More affordable option")
            else:
                explanations.append("Alternative feature set")
        
        return ". ".join(explanations) + "."
    
    def _get_match_level(self, score: float) -> str:
        """
        Convert score to match level
        
        Args:
            score: Probability score
            
        Returns:
            Match level string
        """
        if score > 0.20:
            return 'Perfect Match'
        elif score > 0.10:
            return 'Great Match'
        elif score > 0.05:
            return 'Good Option'
        else:
            return 'Consider Alternatives'
    
    def _generate_insights(self, persona: str, recommendations: List[Dict]) -> Dict:
        """
        Generate insights about recommendations
        
        Args:
            persona: Persona name
            recommendations: List of recommendations
            
        Returns:
            Dictionary with insights
        """
        if len(recommendations) == 0:
            return {}
        
        # Calculate statistics
        scores = [r['score'] for r in recommendations]
        prices = [r['price'] for r in recommendations if r['price']]
        
        # Count match levels
        match_level_counts = {}
        for rec in recommendations:
            level = rec['match_level']
            match_level_counts[level] = match_level_counts.get(level, 0) + 1
        
        # Top categories
        categories = [r['category'] for r in recommendations]
        category_counts = pd.Series(categories).value_counts().to_dict()
        
        insights = {
            'avg_score': round(np.mean(scores), 4),
            'max_score': round(max(scores), 4),
            'min_score': round(min(scores), 4),
            'avg_price': round(np.mean(prices), 2) if prices else 0,
            'price_range': {
                'min': round(min(prices), 2) if prices else 0,
                'max': round(max(prices), 2) if prices else 0
            },
            'match_level_distribution': match_level_counts,
            'top_categories': category_counts,
            'persona_summary': self._get_persona_summary(persona),
            'recommendation_strategy': self._get_recommendation_strategy(persona)
        }
        
        return insights
    
    def _get_persona_summary(self, persona: str) -> str:
        """Get summary text for persona"""
        summaries = {
            'Novice': 'New to camping, needs simple and reassuring products with instant setup',
            'Family_Socializer': 'Occasional camper who values comfort, space, and reliability for family trips',
            'Seasoned_Pro': 'Expert camper seeking technical, ultralight, and premium gear'
        }
        return summaries.get(persona, 'Unknown persona')
    
    def _get_recommendation_strategy(self, persona: str) -> str:
        """Get recommendation strategy for persona"""
        strategies = {
            'Novice': 'Prioritizing instant setup, bundles, and simple designs. Hiding technical/complex products.',
            'Family_Socializer': 'Balancing comfort and convenience. Showing larger capacity and weather-resistant options.',
            'Seasoned_Pro': 'Focusing on technical features, ultralight gear, and premium brands. Filtering out instant/simple products.'
        }
        return strategies.get(persona, 'Standard ranking by relevance')
    
    def compare_personas(self, product_id: str) -> Dict:
        """
        Compare how different personas would score the same product
        
        Args:
            product_id: Product ID to analyze
            
        Returns:
            Comparison across all personas
        """
        if self.products_df is None or self.feature_scorer is None:
            if not self.load_data():
                return {'error': 'Failed to load data'}
        
        # Find product
        product = self.products_df[self.products_df['product_id'] == product_id].to_dict('records')
        
        if len(product) == 0:
            return {'error': f'Product {product_id} not found'}
        
        product = product[0]
        
        # Score for each persona
        personas = ['Novice', 'Family_Socializer', 'Seasoned_Pro']
        comparisons = []
        
        for persona in personas:
            score, explanation = self.feature_scorer.score_product(persona, product, explain=True)
            rec_text = self.feature_scorer.generate_recommendation_text(persona, product, explanation)
            
            comparisons.append({
                'persona': persona,
                'score': round(score, 4),
                'match_level': self._get_match_level(score),
                'recommendation_text': rec_text,
                'feature_lifts': explanation.get('feature_contributions', {})
            })
        
        return {
            'product': {
                'product_id': product.get('product_id'),
                'product_name': product.get('product_name'),
                'brand': product.get('brand'),
                'price': product.get('price')
            },
            'persona_comparisons': comparisons
        }
    
    def _get_customer_info(self, customer_id: str) -> Dict:
        """
        Get customer information including persona and purchase history
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary with customer information
        """
        if self.customers_df is None:
            return None
        
        customer_row = self.customers_df[self.customers_df['customer_id'] == customer_id]
        
        if customer_row.empty:
            return None
        
        customer_info = customer_row.iloc[0].to_dict()
        
        # Get purchase history if available
        if self.purchases_df is not None and not self.purchases_df.empty:
            customer_purchases = self.purchases_df[self.purchases_df['customer_id'] == customer_id]
            customer_info['purchase_count'] = len(customer_purchases)
            # Handle different column names for total price
            if 'total_price' in customer_purchases.columns:
                customer_info['total_spent'] = customer_purchases['total_price'].sum()
            elif 'price' in customer_purchases.columns:
                customer_info['total_spent'] = customer_purchases['price'].sum()
            else:
                customer_info['total_spent'] = 0
            customer_info['purchased_products'] = customer_purchases['product_id'].tolist() if not customer_purchases.empty else []
        else:
            # Use customer's total_spend_12mo from customers table (Academy Sports)
            customer_info['purchase_count'] = customer_info.get('purchase_frequency', 0)
            customer_info['total_spent'] = customer_info.get('total_spend_12mo', 0)
            customer_info['purchased_products'] = []
        
        # Extract persona from various possible column names
        if 'true_persona' in customer_info:
            customer_info['persona'] = customer_info['true_persona']
        elif 'persona_actual' in customer_info:
            customer_info['persona'] = customer_info['persona_actual']
        elif 'cluster' in customer_info:
            customer_info['persona'] = self._get_persona_from_cluster(customer_info['cluster'])
        
        return customer_info
    
    def _get_persona_from_cluster(self, cluster_id: int) -> str:
        """
        Map cluster ID to persona name
        
        Args:
            cluster_id: Cluster ID (0, 1, or 2)
            
        Returns:
            Persona name
        """
        # Default mapping (may need to be adjusted based on Agent A's clustering)
        cluster_to_persona = {
            0: 'Novice',
            1: 'Family_Socializer',
            2: 'Seasoned_Pro'
        }
        
        # If Agent A is available and has persona mapping, use that
        if self.agent_a and hasattr(self.agent_a, 'personas'):
            # Agent A's personas dict is keyed by cluster_id (integer)
            if cluster_id in self.agent_a.personas:
                persona_data = self.agent_a.personas[cluster_id]
                # Return the short_name from persona data
                return persona_data.get('short_name', 'Novice')
        
        return cluster_to_persona.get(cluster_id, 'Novice')


if __name__ == "__main__":
    # Test Agent B
    print("="*70)
    print("Agent B - Academy Sports Product Recommendations")
    print("="*70)
    
    agent = AgentB_Academy()
    
    # Test 1: Novice persona searching for tent
    print("\n" + "="*70)
    print("Test 1: Novice searching for 'tent'")
    print("="*70)
    result = agent.execute({
        'persona': 'Novice',
        'search_query': 'tent',
        'top_n': 5
    })
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Status: {result['status']}")
        print(f"📊 Products considered: {result['total_products_considered']}")
        print(f"\nTop 5 Recommendations:")
        
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n{i}. {rec['product_name']}")
            print(f"   Score: {rec['score']*100:.2f}% | Match: {rec['match_level']}")
            print(f"   Price: ${rec['price']} | Brand: {rec['brand']}")
            if rec.get('recommendation_text'):
                print(f"   {rec['recommendation_text'][:100]}...")
    
    # Test 2: Seasoned Pro searching for technical gear
    print("\n" + "="*70)
    print("Test 2: Seasoned Pro searching for 'backpack'")
    print("="*70)
    result = agent.execute({
        'persona': 'Seasoned_Pro',
        'search_query': 'backpack',
        'top_n': 5
    })
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Status: {result['status']}")
        print(f"📊 Products considered: {result['total_products_considered']}")
        print(f"\nTop 5 Recommendations:")
        
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n{i}. {rec['product_name']}")
            print(f"   Score: {rec['score']*100:.2f}% | Match: {rec['match_level']}")
            print(f"   Price: ${rec['price']} | Brand: {rec['brand']}")
    
    print("\n" + "="*70)
    print("✅ Agent B Test Complete!")
    print("="*70)

  
  

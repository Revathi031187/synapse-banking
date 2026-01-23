"""
Agent B Enhanced with Logistic Regression Model - HYBRID APPROACH
Combines rule-based scoring (30%) with ML-based probability predictions (70%)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from agents.logit_recommendation_model import LogitRecommendationModel

logger = logging.getLogger(__name__)


class AgentB_LogitEnhanced:
    """
    Enhanced Agent B with Hybrid Scoring:
    - 70% ML (Logistic Regression)
    - 30% Rule-Based (Business Logic)
    
    Provides detailed scoring breakdowns for explainability
    """
    
    def __init__(
        self,
        products_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        purchases_df: pd.DataFrame,
        personas: Dict[str, Any],
        logit_model_path: str = "models/logit_recommendation.pkl"
    ):
        self.products_df = products_df
        self.customers_df = customers_df
        self.purchases_df = purchases_df
        self.personas = personas
        
        # Initialize logit model
        self.logit_model = LogitRecommendationModel(model_path=logit_model_path)
        
        # Try to load existing model
        try:
            self.logit_model.load_model()
            print("✅ Loaded existing hybrid recommendation model")
            logger.info(f"✅ Loaded hybrid recommendation model")
        except FileNotFoundError:
            print("⚠️ No trained model found. Training new model...")
            logger.warning(f"⚠️ No trained model found. Training new model...")
            try:
                self.train_logit_model()
                print("✅ Training completed successfully in __init__")
            except Exception as e:
                print(f"❌ TRAINING FAILED IN __INIT__: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    def train_logit_model(self):
        """Train the logistic regression model"""
        print("="*80)
        print("🎓 STARTING ML MODEL TRAINING (Inside agent_b_logit_enhanced.py)")
        print("="*80)
        logger.info("="*60)
        logger.info("🎓 TRAINING ML MODEL ON HISTORICAL PURCHASE DATA")
        logger.info("="*60)
        results = self.logit_model.train(
            self.customers_df,
            self.products_df,
            self.purchases_df
        )
        print("="*80)
        print(f"✅ ML MODEL TRAINED SUCCESSFULLY!")
        print(f"   Test AUC: {results.get('test_auc', 0):.3f}")
        print(f"   Train AUC: {results.get('train_auc', 0):.3f}")
        print(f"   Features: {len(self.logit_model.feature_names)}")
        print("="*80)
        logger.info("="*60)
        logger.info(f"✅ ML MODEL TRAINED SUCCESSFULLY!")
        logger.info(f"   Test AUC: {results.get('test_auc', 0):.3f}")
        logger.info(f"   Train AUC: {results.get('train_auc', 0):.3f}")
        logger.info(f"   Features: {len(self.logit_model.feature_names)}")
        logger.info("="*60)
        return results
    
    def recommend(
        self,
        customer_id: str = None,
        persona_name: str = None,
        search_query: str = "",
        category: str = "",
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Generate hybrid recommendations with detailed scoring
        
        Args:
            customer_id: Specific customer (optional)
            persona_name: Persona name for segment-based recommendations
            search_query: Search term
            category: Product category filter
            top_n: Number of recommendations
        
        Returns:
            Dict with recommendations and detailed scoring breakdowns
        """
        # Get customer info
        if customer_id:
            customer = self.customers_df[
                self.customers_df['customer_id'] == customer_id
            ].iloc[0].to_dict()
            persona_name = customer.get('assigned_persona', persona_name)
        else:
            # Use persona average customer
            customer = self._get_persona_average_customer(persona_name)
        
        # Get persona characteristics
        persona_info = {}
        if persona_name and self.personas:
            for pid, pdata in self.personas.items():
                if pdata.get('persona_name') == persona_name or pdata.get('short_name') == persona_name:
                    persona_info = pdata
                    break
        
        # Filter products
        candidates = self.products_df.copy()
        
        # IMPORTANT: Filter by realistic price range for customer
        target_price = customer.get('avg_order_value', 100)
        price_min = target_price * 0.4  # 40% of target (allows some budget options)
        price_max = target_price * 2.5  # 250% of target (allows some premium options)
        
        print(f"💰 Customer AOV: ${target_price:.0f} → Price Range: ${price_min:.0f} - ${price_max:.0f}")
        before_price_filter = len(candidates)
        candidates = candidates[
            (candidates['price'] >= price_min) & 
            (candidates['price'] <= price_max)
        ]
        print(f"   ✂️ Price filter: {before_price_filter} → {len(candidates)} products")
        
        # Category preference (for scoring boost, not filtering)
        if customer.get('favorite_category'):
            print(f"🎯 Customer's favorite category: {customer.get('favorite_category')} (will score higher)")
        
        if category:
            candidates = candidates[candidates['main_category'] == category]
        
        if search_query:
            candidates = candidates[
                candidates['product_name'].str.contains(search_query, case=False, na=False)
            ]
        
        # Score products with HYBRID approach (70% ML + 30% Rules)
        scored = self._score_hybrid(customer, candidates, persona_info)
        
        # Get top N
        recommendations = scored.nlargest(top_n, 'final_score')
        
        # Format output with detailed breakdowns
        results = []
        for _, rec in recommendations.iterrows():
            # Build detailed scoring breakdown
            scoring_details = {
                'final_score': float(rec['final_score']),
                'ml_probability': float(rec.get('logit_prob', 0)),
                'rule_score': float(rec.get('rule_score', 0)),
                'ml_weight': 0.5,
                'rule_weight': 0.5,
                'ml_contribution': float(rec.get('logit_prob', 0) * 0.5),
                'rule_contribution': float(rec.get('rule_score', 0) * 0.5),
                # Detailed rule-based factors
                'price_score': float(rec.get('price_score', 0)),
                'category_score': float(rec.get('category_score', 0)),
                'expertise_score': float(rec.get('expertise_score', 0)),
                'rating_score': float(rec.get('rating_score', 0))
            }
            
            results.append({
                'product_id': rec['product_id'],
                'product_name': rec['product_name'],
                'price': float(rec['price']),
                'category': rec['main_category'],
                'brand': rec['brand'],
                'avg_rating': float(rec['avg_rating']),
                'complexity': rec.get('complexity', 'Moderate'),
                'final_score': float(rec['final_score']),
                'scoring_breakdown': scoring_details
            })
        
        # Calculate metrics
        avg_price = sum(r['price'] for r in results) / len(results) if results else 0
        avg_match_score = sum(r['final_score'] for r in results) / len(results) if results else 0
        
        return {
            'recommendations': results,
            'customer_id': customer_id,
            'persona': persona_name,
            'metrics': {
                'avg_price': avg_price,
                'avg_match_score': avg_match_score,
                'total_products': len(results)
            },
            'model_performance': self._get_model_stats()
        }
    
    def _score_hybrid(
        self,
        customer: Dict,
        candidates: pd.DataFrame,
        persona_info: Dict
    ) -> pd.DataFrame:
        """
        Score products using hybrid approach (70% ML + 30% Rules)
        
        Returns DataFrame with detailed scoring columns
        """
        logger.info("🎯 Scoring with Hybrid Model (70% ML + 30% Business Rules)...")
        
        candidates = candidates.copy()
        
        # 1. GET ML SCORES (70%)
        logger.info("   📊 Computing ML predictions...")
        candidates['logit_prob'] = candidates.apply(
            lambda row: self.logit_model.predict_purchase_probability(
                customer,
                row.to_dict()
            ),
            axis=1
        )
        
        # 2. GET RULE-BASED SCORES (30%)
        logger.info("   📐 Computing rule-based scores...")
        rule_scores = self._calculate_rule_based_score_detailed(
            candidates,
            customer,
            persona_info
        )
        
        # Merge rule scores back
        for col in ['rule_score', 'price_score', 'category_score', 'expertise_score', 'rating_score']:
            candidates[col] = rule_scores[col]
        
        # 3. COMBINE HYBRID SCORE
        # ML model now has proper category-specific features!
        # Using balanced 50/50 hybrid to leverage both ML and business rules
        candidates['final_score'] = (
            candidates['logit_prob'] * 0.5 +  # 50% ML (proper features now!)
            candidates['rule_score'] * 0.5    # 50% Rule-based
        )
        
        print(f"   📊 Hybrid Scoring: 50% ML + 50% Rule-Based (balanced hybrid)")
        
        logger.info(f"   ✅ Scored {len(candidates)} products")
        logger.info(f"      Avg ML Score: {candidates['logit_prob'].mean():.3f} ({candidates['logit_prob'].mean()*100:.1f}%)")
        logger.info(f"      Avg Rule Score: {candidates['rule_score'].mean():.3f} ({candidates['rule_score'].mean()*100:.1f}%)")
        logger.info(f"      Avg Final Score: {candidates['final_score'].mean():.3f} ({candidates['final_score'].mean()*100:.1f}%)")
        
        # Show top 3 products with their scores
        logger.info(f"   📊 Top 3 Products:")
        for idx, row in candidates.nlargest(3, 'final_score').iterrows():
            logger.info(f"      #{idx+1}: {row['product_name'][:40]} - Final: {row['final_score']:.3f} (ML: {row['logit_prob']:.3f}, Rule: {row['rule_score']:.3f})")
        
        return candidates
    
    def _calculate_rule_based_score_detailed(
        self,
        candidates: pd.DataFrame,
        customer: Dict,
        persona_info: Dict
    ) -> pd.DataFrame:
        """
        Calculate rule-based score with individual factor scores
        
        Returns DataFrame with score breakdowns for each factor
        """
        scores_df = pd.DataFrame(index=candidates.index)
        
        # Extract customer attributes with defaults
        target_price = customer.get('avg_order_value', 100)
        fav_category = customer.get('favorite_category') or customer.get('dominant_category', '')
        expertise_level = customer.get('expertise_level', 'intermediate')
        
        # 1. PRICE ALIGNMENT (35% of rule score) - Important but not dominant
        price_deviation = abs(candidates['price'] - target_price) / target_price
        # Apply exponential penalty for large deviations
        price_penalty = (1 - price_deviation.clip(0, 1)) ** 1.5
        scores_df['price_score'] = price_penalty * 0.35
        
        # 2. CATEGORY MATCH (35% of rule score) - EQUALLY IMPORTANT as price
        scores_df['category_score'] = (candidates['main_category'] == fav_category).astype(float) * 0.35
        
        # 3. EXPERTISE MATCH (15% of rule score) - Reduced slightly
        expertise_map = {'beginner': 1, 'intermediate': 2, 'expert': 3}
        complexity_map = {'Simple': 1, 'Moderate': 2, 'Advanced': 3, 'Expert': 4}
        
        cust_exp = expertise_map.get(expertise_level, 2)
        prod_comp = candidates['complexity'].map(complexity_map).fillna(2)
        
        scores_df['expertise_score'] = (1 - abs(cust_exp - prod_comp) / 3) * 0.15
        
        # 4. PRODUCT RATING (15% of rule score)
        scores_df['rating_score'] = (candidates['avg_rating'] / 5.0) * 0.15
        
        # 5. TOTAL RULE SCORE
        scores_df['rule_score'] = (
            scores_df['price_score'] +
            scores_df['category_score'] +
            scores_df['expertise_score'] +
            scores_df['rating_score']
        ).clip(0, 1)
        
        return scores_df
    
    def _get_persona_average_customer(self, persona_name: str) -> Dict:
        """Get average customer characteristics for a persona"""
        print(f"🔍 Getting customer profile for persona: {persona_name}")
        
        # Try assigned_persona first (from Agent A clustering), fallback to true_persona (ground truth)
        persona_col = None
        if 'assigned_persona' in self.customers_df.columns:
            persona_col = 'assigned_persona'
            print(f"   Using assigned_persona column")
        elif 'true_persona' in self.customers_df.columns:
            persona_col = 'true_persona'
            print(f"   Using true_persona column")
        
        if persona_col:
            persona_customers = self.customers_df[
                self.customers_df[persona_col] == persona_name
            ]
            print(f"   Found {len(persona_customers)} customers with exact name match")
        else:
            persona_customers = pd.DataFrame()
            print(f"   No persona column found in dataset")
        
        # If no customers found, try to derive from persona characteristics or use synthetic profile
        if len(persona_customers) == 0:
            print(f"⚠️ No customers found for '{persona_name}', creating synthetic profile based on persona name")
            
            # Create comprehensive synthetic profiles for ALL 5 persona types
            # Each profile has distinct characteristics to ensure different recommendations
            
            # PERSONA 1: Premium/High-End/Expert Segments
            if any(keyword in persona_name for keyword in ['Premium', 'Expert', 'Elite', 'Advanced', 'Technical', 'Gear', 'Specialist']):
                profile = {
                    'avg_order_value': 350.0,
                    'purchase_frequency': 6.5,
                    'total_spend': 2275.0,
                    'dominant_category': 'Hiking Backpacks',
                    'favorite_category': 'Hiking Backpacks',
                    'expertise_level': 'expert',
                    'avg_brand_loyalty': 0.75,
                    'avg_bundle_affinity': 0.2,
                    'avg_price_sort_frequency': 0.15,
                    # CRITICAL: Category-specific purchase history (KEY FIX!)
                    'category_purchase_history': {
                        'Hiking Backpacks': 5,        # Strong history in preferred category
                        'Tents + Screen Houses': 1,   # Some complementary purchases
                        'Hiking Boots': 2,            # Related category
                        # All other categories default to 0
                    },
                    'brand_purchase_count': 0.5,     # Some brand familiarity
                    'brand_loyalty': 0.40            # Moderate brand loyalty (40%)
                }
                print(f"   ✨ Applied Premium/Expert profile: ${profile['avg_order_value']}/order, {profile['purchase_frequency']} purchases/yr")
                print(f"      Category history: {sum(profile['category_purchase_history'].values())} total purchases across {len(profile['category_purchase_history'])} categories")
                return profile
            
            # PERSONA 2: Deal/Price-Conscious Segments (Higher frequency, lower AOV)
            elif any(keyword in persona_name for keyword in ['Deal', 'Seeker', 'Price', 'Sale', 'Strategic', 'Value', 'Smart']):
                profile = {
                    'avg_order_value': 120.0,
                    'purchase_frequency': 4.5,
                    'total_spend': 540.0,
                    'dominant_category': 'Tents + Screen Houses',
                    'favorite_category': 'Tents + Screen Houses',
                    'expertise_level': 'intermediate',
                    'avg_brand_loyalty': 0.35,
                    'avg_bundle_affinity': 0.5,
                    'avg_price_sort_frequency': 0.8,
                    # CRITICAL: Category-specific purchase history
                    'category_purchase_history': {
                        'Tents + Screen Houses': 4,    # Strong history in preferred category
                        'Sleeping Bags + Airbeds': 2,  # Budget camping gear
                        'Camp Furniture': 1,           # Occasional purchases
                    },
                    'brand_purchase_count': 0.3,     # Lower brand loyalty (switches brands)
                    'brand_loyalty': 0.20            # Low loyalty (price-focused)
                }
                print(f"   ✨ Applied Deal Seeker profile: ${profile['avg_order_value']}/order, {profile['purchase_frequency']} purchases/yr")
                print(f"      Category history: {sum(profile['category_purchase_history'].values())} total purchases across {len(profile['category_purchase_history'])} categories")
                return profile
            
            # PERSONA 3: Bargain/Budget Segments (Lowest spend)
            elif any(keyword in persona_name for keyword in ['Bargain', 'Hunter', 'Budget', 'Frugal', 'Entry', 'Newcomer', 'Beginner']):
                profile = {
                    'avg_order_value': 75.0,
                    'purchase_frequency': 3.0,
                    'total_spend': 225.0,
                    'dominant_category': 'Sleeping Bags + Airbeds',
                    'favorite_category': 'Sleeping Bags + Airbeds',
                    'expertise_level': 'beginner',
                    'avg_brand_loyalty': 0.25,
                    'avg_bundle_affinity': 0.7,
                    'avg_price_sort_frequency': 0.9
                }
                print(f"   ✨ Applied Bargain Hunter profile: ${profile['avg_order_value']}/order, {profile['purchase_frequency']} purchases/yr")
                return profile
            
            # PERSONA 4: Occasional/Casual/Seasonal Segments (Low frequency, moderate spend)
            elif any(keyword in persona_name for keyword in ['Occasional', 'Camper', 'Casual', 'Seasonal', 'Moderate', 'Guided']):
                profile = {
                    'avg_order_value': 180.0,
                    'purchase_frequency': 2.5,
                    'total_spend': 450.0,
                    'dominant_category': 'Tents + Screen Houses',
                    'favorite_category': 'Tents + Screen Houses',
                    'expertise_level': 'beginner',
                    'avg_brand_loyalty': 0.3,
                    'avg_bundle_affinity': 0.6,
                    'avg_price_sort_frequency': 0.65
                }
                print(f"   ✨ Applied Occasional Camper profile: ${profile['avg_order_value']}/order, {profile['purchase_frequency']} purchases/yr")
                return profile
            
            # PERSONA 5: Mid-Tier/Balanced/Mainstream/Technical Segments (Balanced characteristics)
            elif any(keyword in persona_name for keyword in ['Mainstream', 'Balanced', 'Mid', 'Regular', 'Steady', 'Consistent', 'Active', 'Weekend', 'Technical', 'Specialist']):
                profile = {
                    'avg_order_value': 220.0,
                    'purchase_frequency': 5.0,
                    'total_spend': 1100.0,
                    'dominant_category': 'Camping Furniture',
                    'favorite_category': 'Camping Furniture',
                    'expertise_level': 'intermediate',
                    'avg_brand_loyalty': 0.5,
                    'avg_bundle_affinity': 0.4,
                    'avg_price_sort_frequency': 0.5
                }
                print(f"   ✨ Applied Mid-Tier/Technical Specialist profile: ${profile['avg_order_value']}/order, {profile['purchase_frequency']} purchases/yr")
                return profile
            
            # FALLBACK: Generic average if no pattern matches
            else:
                print(f"   ⚠️ No pattern matched, using dataset averages")
                return {
                    'avg_order_value': self.customers_df['avg_order_value'].mean(),
                    'purchase_frequency': self.customers_df['purchase_frequency'].mean(),
                    'total_spend': self.customers_df.get('total_spend_12mo', self.customers_df.get('total_spend', pd.Series([250]))).mean(),
                    'dominant_category': self.customers_df['dominant_category'].mode()[0] if 'dominant_category' in self.customers_df.columns else 'Tents + Screen Houses',
                    'favorite_category': self.customers_df['dominant_category'].mode()[0] if 'dominant_category' in self.customers_df.columns else 'Tents + Screen Houses',
                    'expertise_level': 'intermediate',
                    'avg_brand_loyalty': 0.5,
                    'avg_bundle_affinity': 0.5,
                    'avg_price_sort_frequency': 0.5
                }
        
        # Build result from actual persona customers
        result = {
            'avg_order_value': persona_customers['avg_order_value'].mean(),
            'purchase_frequency': persona_customers['purchase_frequency'].mean(),
        }
        
        # Add total_spend (handle both column names)
        if 'total_spend' in persona_customers.columns:
            result['total_spend'] = persona_customers['total_spend'].mean()
        elif 'total_spend_12mo' in persona_customers.columns:
            result['total_spend'] = persona_customers['total_spend_12mo'].mean()
        else:
            result['total_spend'] = result['avg_order_value'] * result['purchase_frequency']
        
        # Add dominant_category (handle both column names)
        if 'favorite_category' in persona_customers.columns:
            result['favorite_category'] = persona_customers['favorite_category'].mode()[0]
            result['dominant_category'] = result['favorite_category']
        elif 'dominant_category' in persona_customers.columns:
            result['dominant_category'] = persona_customers['dominant_category'].mode()[0]
            result['favorite_category'] = result['dominant_category']
        else:
            result['favorite_category'] = 'Tents + Screen Houses'
            result['dominant_category'] = 'Tents + Screen Houses'
        
        # Add expertise_level (derive if not present)
        if 'expertise_level' in persona_customers.columns:
            result['expertise_level'] = persona_customers['expertise_level'].mode()[0]
        else:
            # Derive expertise from purchase frequency and spending
            avg_freq = result['purchase_frequency']
            avg_aov = result['avg_order_value']
            if avg_freq >= 6 and avg_aov >= 250:
                result['expertise_level'] = 'expert'
            elif avg_freq >= 4 or avg_aov >= 150:
                result['expertise_level'] = 'intermediate'
            else:
                result['expertise_level'] = 'beginner'
        
        # Add behavioral metrics if available
        if 'brand_loyalty' in persona_customers.columns:
            result['avg_brand_loyalty'] = persona_customers['brand_loyalty'].mean()
        else:
            result['avg_brand_loyalty'] = 0.5  # Default
        
        if 'bundle_affinity' in persona_customers.columns:
            result['avg_bundle_affinity'] = persona_customers['bundle_affinity'].mean()
        else:
            result['avg_bundle_affinity'] = 0.5  # Default
        
        if 'price_sort_frequency' in persona_customers.columns:
            result['avg_price_sort_frequency'] = persona_customers['price_sort_frequency'].mean()
        else:
            result['avg_price_sort_frequency'] = 0.5  # Default
        
        print(f"   ✅ Built profile from {len(persona_customers)} actual customers")
        print(f"      AOV: ${result['avg_order_value']:.2f}, Frequency: {result['purchase_frequency']:.1f}, Expertise: {result['expertise_level']}")
        
        return result
    
    def _get_model_stats(self) -> Dict:
        """Get model performance statistics"""
        return {
            'model_type': 'Hybrid (70% ML + 30% Rules)',
            'ml_features': len(self.logit_model.feature_names) if self.logit_model.feature_names else 0,
            'approach': 'Logistic Regression + Business Logic'
        }

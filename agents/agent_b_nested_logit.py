"""
Agent B with Nested Logit Model Integration
Addresses IIA assumption and captures product substitution patterns
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from agents.nested_logit_model import NestedLogitModel

logger = logging.getLogger(__name__)


class AgentB_NestedLogit:
    """
    Agent B using Nested Logit model for hierarchical product recommendations
    
    Key features:
    - Models category → brand → product choice hierarchy
    - Relaxes IIA assumption within nests
    - Provides explainable hierarchical probabilities
    """
    
    def __init__(
        self,
        products_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        purchases_df: pd.DataFrame,
        personas: Dict[str, Any],
        model_path: str = "models/nested_logit.pkl"
    ):
        self.products_df = products_df
        self.customers_df = customers_df
        self.purchases_df = purchases_df
        self.personas = personas
        
        # Initialize nested logit model
        self.nested_model = NestedLogitModel(model_path=model_path)
        
        # Try to load existing model
        try:
            self.nested_model.load_model()
            print("✅ Loaded existing Nested Logit model")
            logger.info("✅ Loaded existing Nested Logit model")
        except FileNotFoundError:
            print("⚠️ No trained Nested Logit model found. Training new model...")
            logger.warning("⚠️ No trained Nested Logit model found. Training...")
            self.train_model()
    
    def train_model(self):
        """Train the nested logit model"""
        print("🎓 Training Nested Logit Model...")
        logger.info("🎓 Training Nested Logit Model...")
        
        self.nested_model.train(
            self.customers_df,
            self.products_df,
            self.purchases_df
        )
        
        self.nested_model.save_model()
        print("✅ Nested Logit Model training completed")
        logger.info("✅ Nested Logit Model training completed")
    
    def _get_persona_average_customer(self, persona_name: str) -> Dict[str, Any]:
        """
        Create a synthetic customer profile based on persona characteristics
        Same logic as in agent_b_logit_enhanced.py for consistency
        """
        # Define synthetic profiles for each persona
        synthetic_profiles = {
            "Premium_Gear_Experts": {
                "avg_order_value": 320,
                "purchase_frequency": 7,
                "total_spend": 2240,
                "favorite_category": "Hiking Backpacks",
                "dominant_category": "Hiking Backpacks",
                "expertise_level": "expert",
                "category_purchase_history": {
                    "Hiking Backpacks": 5,
                    "Tents + Screen Houses": 2,
                    "Hiking Boots": 1
                },
                "brand_purchase_history": {
                    "Osprey": 3,
                    "Big Agnes": 2,
                    "MSR": 1,
                    "The North Face": 1
                }
            },
            "Budget_Conscious_Shoppers": {
                "avg_order_value": 85,
                "purchase_frequency": 3,
                "total_spend": 255,
                "favorite_category": "Camp Furniture",
                "dominant_category": "Camp Furniture",
                "expertise_level": "beginner",
                "category_purchase_history": {
                    "Camp Furniture": 2,
                    "Coolers": 1
                },
                "brand_purchase_history": {
                    "Coleman": 2,
                    "Magellan Outdoors": 1
                }
            },
            "Frequent_Campers": {
                "avg_order_value": 180,
                "purchase_frequency": 8,
                "total_spend": 1440,
                "favorite_category": "Tents + Screen Houses",
                "dominant_category": "Tents + Screen Houses",
                "expertise_level": "intermediate",
                "category_purchase_history": {
                    "Tents + Screen Houses": 4,
                    "Sleeping Bags": 2,
                    "Camp Furniture": 1,
                    "Campsite Cooking": 1
                },
                "brand_purchase_history": {
                    "Big Agnes": 2,
                    "MSR": 2,
                    "Coleman": 2,
                    "YETI": 1
                }
            },
            "Outdoor_Enthusiasts": {
                "avg_order_value": 245,
                "purchase_frequency": 6,
                "total_spend": 1470,
                "favorite_category": "Hiking Boots",
                "dominant_category": "Hiking Boots",
                "expertise_level": "intermediate",
                "category_purchase_history": {
                    "Hiking Boots": 3,
                    "Hiking Backpacks": 2,
                    "Trekking Poles": 1
                },
                "brand_purchase_history": {
                    "The North Face": 2,
                    "Kelty": 2,
                    "Osprey": 1
                }
            },
            "Technical_Specialist": {
                "avg_order_value": 420,
                "purchase_frequency": 5,
                "total_spend": 2100,
                "favorite_category": "Climbing Gear",
                "dominant_category": "Climbing Gear",
                "expertise_level": "expert",
                "category_purchase_history": {
                    "Climbing Gear": 3,
                    "Technical Apparel": 1,
                    "Hiking Backpacks": 1
                },
                "brand_purchase_history": {
                    "Black Diamond": 2,
                    "Petzl": 1,
                    "Arc'teryx": 1,
                    "Osprey": 1
                }
            }
        }
        
        if persona_name in synthetic_profiles:
            print(f"✅ Using synthetic profile for persona: {persona_name}")
            logger.info(f"✅ Using synthetic profile for persona: {persona_name}")
            return synthetic_profiles[persona_name]
        
        # Fallback: try to find real customers assigned to this persona
        customers_with_persona = self.customers_df[
            (self.customers_df.get('assigned_persona') == persona_name) |
            (self.customers_df.get('true_persona') == persona_name)
        ]
        
        if len(customers_with_persona) > 0:
            print(f"✅ Found {len(customers_with_persona)} customers for persona: {persona_name}")
            avg_customer = {
                'avg_order_value': customers_with_persona['avg_order_value'].mean(),
                'purchase_frequency': customers_with_persona['purchase_frequency'].mean(),
                'total_spend': customers_with_persona.get('total_spend_12mo', customers_with_persona.get('total_spend', pd.Series([0]))).mean(),
                'favorite_category': customers_with_persona['dominant_category'].mode().values[0] if len(customers_with_persona['dominant_category'].mode()) > 0 else 'Hiking Backpacks',
                'dominant_category': customers_with_persona['dominant_category'].mode().values[0] if len(customers_with_persona['dominant_category'].mode()) > 0 else 'Hiking Backpacks',
                'expertise_level': 'intermediate',
                'category_purchase_history': {},
                'brand_purchase_history': {}
            }
            return avg_customer
        
        # Ultimate fallback: dataset averages
        print(f"⚠️ No customers found for persona {persona_name}, using dataset averages")
        logger.warning(f"⚠️ No customers found for persona {persona_name}, using dataset averages")
        
        return {
            'avg_order_value': self.customers_df['avg_order_value'].mean(),
            'purchase_frequency': self.customers_df['purchase_frequency'].mean(),
            'total_spend': self.customers_df.get('total_spend_12mo', self.customers_df.get('total_spend', pd.Series([0]))).mean(),
            'favorite_category': self.customers_df['dominant_category'].mode().values[0] if len(self.customers_df['dominant_category'].mode()) > 0 else 'Hiking Backpacks',
            'dominant_category': self.customers_df['dominant_category'].mode().values[0] if len(self.customers_df['dominant_category'].mode()) > 0 else 'Hiking Backpacks',
            'expertise_level': 'intermediate',
            'category_purchase_history': {},
            'brand_purchase_history': {}
        }
    
    def recommend(
        self,
        persona_name: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Generate product recommendations using Nested Logit model
        
        Returns:
        - Recommended products with hierarchical probabilities
        - Explanation of choice structure (category → brand → product)
        - Comparison to IIA-based models
        """
        print(f"\n{'='*80}")
        print(f"🎯 NESTED LOGIT RECOMMENDATIONS FOR: {persona_name}")
        print(f"{'='*80}")
        
        logger.info(f"🎯 Generating Nested Logit recommendations for persona: {persona_name}")
        
        # Get persona profile
        customer_profile = self._get_persona_average_customer(persona_name)
        
        print(f"\n📊 Customer Profile:")
        print(f"   - Avg Order Value: ${customer_profile['avg_order_value']:.2f}")
        print(f"   - Purchase Frequency: {customer_profile['purchase_frequency']:.1f}/year")
        print(f"   - Favorite Category: {customer_profile['favorite_category']}")
        print(f"   - Expertise Level: {customer_profile['expertise_level']}")
        
        # Get recommendations from nested logit model
        recommendations = self.nested_model.predict_nested_probabilities(
            customer_profile,
            self.products_df,
            top_k=top_k
        )
        
        print(f"\n✅ Found {len(recommendations)} nested logit recommendations")
        
        # Format recommendations for API response
        formatted_recommendations = []
        
        for idx, rec in enumerate(recommendations, 1):
            formatted_rec = {
                'rank': idx,
                'product_id': rec['product_id'],
                'product_name': rec['product_name'],
                'brand': rec['brand'],
                'category': rec['category'],
                'price': float(rec['price']),
                'rating': float(rec['avg_rating']),
                'complexity': rec['complexity'],
                'overall_probability': float(rec['probability'] * 100),  # Convert to percentage
                'nested_breakdown': {
                    'category_probability': float(rec['category_prob'] * 100),
                    'brand_probability': float(rec['brand_prob'] * 100),
                    'product_probability': float(rec['product_prob'] * 100)
                },
                'explanation': rec['explanation'],
                'match_quality': self._get_match_quality(rec['probability'])
            }
            
            formatted_recommendations.append(formatted_rec)
            
            print(f"\n#{idx} {rec['product_name']}")
            print(f"   Brand: {rec['brand']} | Category: {rec['category']} | Price: ${rec['price']:.2f}")
            print(f"   Overall Probability: {rec['probability']*100:.2f}%")
            print(f"   └─ Category: {rec['category_prob']*100:.1f}% → Brand: {rec['brand_prob']*100:.1f}% → Product: {rec['product_prob']*100:.1f}%")
        
        # Calculate summary metrics
        avg_probability = np.mean([r['overall_probability'] for r in formatted_recommendations]) if formatted_recommendations else 0
        avg_price = np.mean([r['price'] for r in formatted_recommendations]) if formatted_recommendations else 0
        price_range = (
            min(r['price'] for r in formatted_recommendations),
            max(r['price'] for r in formatted_recommendations)
        ) if formatted_recommendations else (0, 0)
        
        categories_count = len(set(r['category'] for r in formatted_recommendations))
        brands_count = len(set(r['brand'] for r in formatted_recommendations))
        
        return {
            'success': True,
            'persona': persona_name,
            'recommendations': formatted_recommendations,
            'metrics': {
                'avg_probability': float(avg_probability),
                'avg_price': float(avg_price),
                'price_range': f"${price_range[0]:.0f} - ${price_range[1]:.0f}",
                'products_considered': len(self.products_df),
                'unique_categories': categories_count,
                'unique_brands': brands_count
            },
            'model_info': {
                'model_type': 'Nested Logit',
                'nest_structure': 'Category → Brand → Product',
                'lambda_category': self.nested_model.lambda_category,
                'lambda_brand': self.nested_model.lambda_brand,
                'advantage': 'Relaxes IIA assumption, captures substitution patterns within nests'
            }
        }
    
    def _get_match_quality(self, probability: float) -> str:
        """Determine match quality based on probability"""
        if probability >= 0.15:
            return "Perfect Match"
        elif probability >= 0.10:
            return "Great Match"
        elif probability >= 0.05:
            return "Good Match"
        else:
            return "Fair Match"
    
    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Agent B with Nested Logit model
        Compatible with existing Agent B API interface
        """
        persona_name = config.get('persona_name')
        top_k = config.get('top_k', 10)
        
        if not persona_name:
            return {
                'success': False,
                'error': 'persona_name is required'
            }
        
        return self.recommend(persona_name=persona_name, top_k=top_k)

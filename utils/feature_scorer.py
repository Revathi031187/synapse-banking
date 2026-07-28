"""
Feature-Based Scoring for Academy Sports Personalization
Uses logistic regression with feature lift factors to calculate purchase probability
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class FeatureScorer:
    """
    Calculate personalized product scores using feature-based lift factors
    Based on logistic regression: P = 1 / (1 + e^-(base + lifts))
    """
    
    def __init__(self, feature_affinity_df: pd.DataFrame):
        """
        Initialize with feature affinity data
        
        Args:
            feature_affinity_df: DataFrame with columns [persona, feature, lift_factor, log_lift]
        """
        self.feature_affinity = feature_affinity_df
        self._build_lookup()
        
    def _build_lookup(self):
        """Build fast lookup dictionary for lift factors"""
        self.lift_lookup = {}
        
        for _, row in self.feature_affinity.iterrows():
            persona = row['persona']
            feature = row['feature']
            log_lift = row['log_lift']
            
            if persona not in self.lift_lookup:
                self.lift_lookup[persona] = {}
            
            self.lift_lookup[persona][feature] = log_lift
            
        logger.info(f"Built lift lookup for {len(self.lift_lookup)} personas")
    
    def score_product(self, 
                     persona: str, 
                     product: Dict, 
                     explain: bool = False) -> Tuple[float, Dict]:
        """
        Calculate purchase probability for a persona-product pair
        
        Args:
            persona: Persona name (e.g., "Novice", "Family_Socializer", "Seasoned_Pro")
            product: Product dictionary with features
            explain: Whether to return explanation details
            
        Returns:
            Tuple of (probability, explanation_dict)
        """
        # Base conversion rate (global)
        base_cr = product.get('base_conversion_rate', 0.05)
        base_logit = np.log(base_cr / (1 - base_cr))
        
        # Extract product features and calculate lifts
        lift_sum = 0
        feature_contributions = {}
        
        # Check each product feature
        features_to_check = [
            ('setup_type', product.get('setup_type')),
            ('complexity', product.get('complexity')),
            ('bundle_compatible', product.get('bundle_compatible')),
            ('brand_tier', product.get('brand_tier')),
            ('weight_class', product.get('weight_class')),
            ('weatherproof', product.get('weatherproof')),
            ('capacity', product.get('capacity'))
        ]
        
        for feature_type, feature_value in features_to_check:
            if feature_value and persona in self.lift_lookup:
                # Try exact match first
                if feature_value in self.lift_lookup[persona]:
                    log_lift = self.lift_lookup[persona][feature_value]
                    lift_sum += log_lift
                    
                    if explain:
                        lift_factor = np.exp(log_lift)
                        feature_contributions[feature_value] = {
                            'lift_factor': round(lift_factor, 2),
                            'log_lift': round(log_lift, 4),
                            'boost_percent': round((lift_factor - 1) * 100, 1)
                        }
                
                # Check for special mappings
                elif feature_type == 'brand_tier':
                    # Map brand_tier to feature names
                    brand_mapping = {
                        'budget': 'Budget Brand',
                        'pro_grade': 'Pro-Grade Brand',
                        'premium': 'Premium Brand'
                    }
                    mapped_feature = brand_mapping.get(feature_value)
                    if mapped_feature and mapped_feature in self.lift_lookup[persona]:
                        log_lift = self.lift_lookup[persona][mapped_feature]
                        lift_sum += log_lift
                        
                        if explain:
                            lift_factor = np.exp(log_lift)
                            feature_contributions[mapped_feature] = {
                                'lift_factor': round(lift_factor, 2),
                                'log_lift': round(log_lift, 4),
                                'boost_percent': round((lift_factor - 1) * 100, 1)
                            }
                
                elif feature_type == 'capacity' and feature_value:
                    # Check for 4+ Person capacity
                    try:
                        person_count = int(feature_value.split('-')[0])
                        if person_count >= 4 and '4+ Person Capacity' in self.lift_lookup[persona]:
                            log_lift = self.lift_lookup[persona]['4+ Person Capacity']
                            lift_sum += log_lift
                            
                            if explain:
                                lift_factor = np.exp(log_lift)
                                feature_contributions['4+ Person Capacity'] = {
                                    'lift_factor': round(lift_factor, 2),
                                    'log_lift': round(log_lift, 4),
                                    'boost_percent': round((lift_factor - 1) * 100, 1)
                                }
                    except:
                        pass
        
        # Calculate final probability
        final_logit = base_logit + lift_sum
        probability = 1 / (1 + np.exp(-final_logit))
        probability = min(probability, 0.95)  # Cap at 95%
        
        # Build explanation
        explanation = {
            'probability': round(probability, 4),
            'base_conversion_rate': base_cr,
            'base_logit': round(base_logit, 4),
            'lift_sum': round(lift_sum, 4),
            'final_logit': round(final_logit, 4),
            'feature_contributions': feature_contributions if explain else {}
        }
        
        return probability, explanation
    
    def rank_products(self, 
                      persona: str, 
                      products: List[Dict], 
                      top_n: int = 10) -> List[Dict]:
        """
        Rank products by score for a given persona
        
        Args:
            persona: Persona name
            products: List of product dictionaries
            top_n: Number of top products to return
            
        Returns:
            List of products with scores, sorted by probability descending
        """
        scored_products = []
        
        for product in products:
            probability, explanation = self.score_product(persona, product, explain=True)
            
            scored_product = {
                **product,
                'score': probability,
                'explanation': explanation
            }
            scored_products.append(scored_product)
        
        # Sort by score descending
        scored_products.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_products[:top_n]
    
    def generate_recommendation_text(self, 
                                     persona: str, 
                                     product: Dict, 
                                     explanation: Dict) -> str:
        """
        Generate human-readable recommendation explanation
        
        Args:
            persona: Persona name
            product: Product dictionary
            explanation: Explanation from score_product
            
        Returns:
            Human-readable explanation string
        """
        probability = explanation['probability']
        features = explanation.get('feature_contributions', {})
        
        # Start with match level
        if probability > 0.20:
            text = "🎯 **PERFECT MATCH!** "
        elif probability > 0.10:
            text = "✅ **Great Match!** "
        elif probability > 0.05:
            text = "👍 **Good Option.** "
        else:
            text = "⚠️ **Consider Other Options.** "
        
        # Add positive features
        positive_features = [(k, v) for k, v in features.items() if v['lift_factor'] > 1.0]
        positive_features.sort(key=lambda x: x[1]['lift_factor'], reverse=True)
        
        if positive_features:
            text += "Why this works for you:\n"
            for feature, data in positive_features[:3]:  # Top 3 features
                boost = data['boost_percent']
                if boost > 0:
                    text += f"• **{feature}** (+{boost:.0f}% match)\n"
        
        # Add negative features as warnings
        negative_features = [(k, v) for k, v in features.items() if v['lift_factor'] < 1.0]
        negative_features.sort(key=lambda x: x[1]['lift_factor'])
        
        if negative_features and probability < 0.10:
            text += "\n⚠️ **Note:** This product may not be ideal:\n"
            for feature, data in negative_features[:2]:  # Top 2 concerns
                penalty = abs(data['boost_percent'])
                text += f"• {feature} ({penalty:.0f}% less suitable)\n"
        
        return text
    
    def compare_products(self, 
                        persona: str, 
                        products: List[Dict]) -> pd.DataFrame:
        """
        Create comparison table of products for a persona
        
        Args:
            persona: Persona name
            products: List of product dictionaries
            
        Returns:
            DataFrame with product comparisons
        """
        comparisons = []
        
        for product in products:
            probability, explanation = self.score_product(persona, product, explain=True)
            
            comparison = {
                'product_id': product.get('product_id'),
                'product_name': product.get('product_name'),
                'price': product.get('price'),
                'score': round(probability, 4),
                'base_cr': product.get('base_conversion_rate', 0.05),
                'lift_applied': round(np.exp(explanation['lift_sum']), 2),
                'num_positive_features': len([f for f in explanation.get('feature_contributions', {}).values() if f['lift_factor'] > 1.0]),
                'num_negative_features': len([f for f in explanation.get('feature_contributions', {}).values() if f['lift_factor'] < 1.0])
            }
            comparisons.append(comparison)
        
        df = pd.DataFrame(comparisons)
        df = df.sort_values('score', ascending=False).reset_index(drop=True)
        
        return df


def load_feature_scorer(feature_affinity_path: str = 'data/preloaded/academy_sports/feature_affinity.csv') -> FeatureScorer:
    """
    Convenience function to load feature scorer from CSV
    
    Args:
        feature_affinity_path: Path to feature affinity CSV file
        
    Returns:
        Initialized FeatureScorer
    """
    feature_affinity_df = pd.read_csv(feature_affinity_path)
    return FeatureScorer(feature_affinity_df)


if __name__ == "__main__":
    # Test the scorer
    print("="*70)
    print("Feature Scorer Test")
    print("="*70)
    
    # Load scorer
    scorer = load_feature_scorer()
    
    # Test product (Magellan Instant Cabin - perfect for Novice)
    test_product_novice = {
        'product_id': 'TEST_001',
        'product_name': 'Magellan 4-Person Instant Cabin',
        'price': 149.99,
        'base_conversion_rate': 0.05,
        'setup_type': 'Instant Setup',
        'complexity': 'Simple Design',
        'bundle_compatible': 'Bundle Compatible',
        'brand_tier': 'budget',
        'capacity': '4-Person'
    }
    
    # Test product (MSR Technical Tent - perfect for Pro)
    test_product_pro = {
        'product_id': 'TEST_002',
        'product_name': 'MSR Hubba NX 2-Person',
        'price': 449.99,
        'base_conversion_rate': 0.03,
        'setup_type': 'Traditional Setup',
        'complexity': 'Technical Design',
        'bundle_compatible': 'Standalone Only',
        'brand_tier': 'premium',
        'weight_class': 'Ultralight',
        'capacity': '2-Person'
    }
    
    print("\n" + "="*70)
    print("Test 1: Novice + Instant Cabin (Should be HIGH score)")
    print("="*70)
    prob, exp = scorer.score_product('Novice', test_product_novice, explain=True)
    print(f"Probability: {prob*100:.2f}%")
    print(f"Features contributing:")
    for feature, data in exp['feature_contributions'].items():
        print(f"  - {feature}: {data['lift_factor']:.2f}x ({data['boost_percent']:+.1f}%)")
    
    rec_text = scorer.generate_recommendation_text('Novice', test_product_novice, exp)
    print(f"\nRecommendation:\n{rec_text}")
    
    print("\n" + "="*70)
    print("Test 2: Seasoned_Pro + Instant Cabin (Should be LOW score)")
    print("="*70)
    prob, exp = scorer.score_product('Seasoned_Pro', test_product_novice, explain=True)
    print(f"Probability: {prob*100:.2f}%")
    print(f"Features contributing:")
    for feature, data in exp['feature_contributions'].items():
        print(f"  - {feature}: {data['lift_factor']:.2f}x ({data['boost_percent']:+.1f}%)")
    
    rec_text = scorer.generate_recommendation_text('Seasoned_Pro', test_product_novice, exp)
    print(f"\nRecommendation:\n{rec_text}")
    
    print("\n" + "="*70)
    print("Test 3: Seasoned_Pro + MSR Technical (Should be HIGH score)")
    print("="*70)
    prob, exp = scorer.score_product('Seasoned_Pro', test_product_pro, explain=True)
    print(f"Probability: {prob*100:.2f}%")
    print(f"Features contributing:")
    for feature, data in exp['feature_contributions'].items():
        print(f"  - {feature}: {data['lift_factor']:.2f}x ({data['boost_percent']:+.1f}%)")
    
    rec_text = scorer.generate_recommendation_text('Seasoned_Pro', test_product_pro, exp)
    print(f"\nRecommendation:\n{rec_text}")
    
    print("\n" + "="*70)
    print("✅ Feature Scorer Test Complete!")
    print("="*70)


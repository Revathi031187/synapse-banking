"""
Nested Logit Model for Product Recommendations

Addresses IIA (Independence of Irrelevant Alternatives) assumption by allowing
correlation within product "nests" (groups of similar products).

Hierarchical Structure:
  Level 1: Category Choice (Hiking Backpacks vs Tents vs Boots)
    └─ Level 2: Brand Choice (Osprey vs Big Agnes vs Kelty | Category)
        └─ Level 3: Product Choice (specific SKU | Brand, Category)

This captures realistic substitution patterns:
- Products within the same brand are more substitutable
- Products in the same category are more substitutable than across categories
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from scipy.optimize import minimize
from scipy.special import logsumexp

logger = logging.getLogger(__name__)


class NestedLogitModel:
    """
    Nested Logit Model for hierarchical product recommendations
    
    Key advantages over simple logit:
    - Relaxes IIA assumption within nests
    - Captures product substitution patterns
    - Models hierarchical preferences (category → brand → product)
    """
    
    def __init__(self, model_path: str = "models/nested_logit.pkl"):
        self.model_path = model_path
        self.category_params = {}  # Parameters for category choice
        self.brand_params = {}     # Parameters for brand choice | category
        self.product_params = {}   # Parameters for product choice | brand
        self.lambda_category = 0.7  # Nest correlation parameter (0 < λ ≤ 1)
        self.lambda_brand = 0.8     # Higher λ = less correlation within nest
        
    def _compute_utility_features(
        self,
        customer: Dict[str, Any],
        product: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Compute utility (attractiveness) features for a customer-product pair
        Similar to logit model features but organized for nested structure
        """
        features = {}
        
        # Price utility
        customer_budget = customer.get('avg_order_value', 100)
        product_price = product.get('price', 100)
        
        features['price_deviation'] = abs(product_price - customer_budget) / customer_budget
        features['price_in_budget'] = 1.0 if 0.5 * customer_budget <= product_price <= 2.0 * customer_budget else 0.0
        features['log_price'] = np.log(product_price + 1)
        
        # Category utility
        customer_category = customer.get('favorite_category') or customer.get('dominant_category', '')
        product_category = product.get('main_category', '')
        features['category_match'] = 1.0 if product_category == customer_category else 0.0
        
        # Brand utility
        customer_brand_history = customer.get('brand_purchase_history', {})
        product_brand = product.get('brand', '')
        features['brand_familiarity'] = customer_brand_history.get(product_brand, 0)
        features['brand_loyalty'] = 1.0 if features['brand_familiarity'] > 0 else 0.0
        
        # Quality utility
        features['rating'] = product.get('avg_rating', 3.0)
        features['rating_normalized'] = features['rating'] / 5.0
        
        # Expertise utility
        expertise_map = {'beginner': 1, 'intermediate': 2, 'expert': 3}
        complexity_map = {'Simple': 1, 'Moderate': 2, 'Advanced': 3, 'Expert': 4}
        
        customer_exp = expertise_map.get(customer.get('expertise_level', 'intermediate'), 2)
        product_comp = complexity_map.get(product.get('complexity', 'Moderate'), 2)
        
        features['expertise_match'] = 1.0 - abs(customer_exp - product_comp) / 3.0
        
        return features
    
    def _compute_category_utility(
        self,
        customer: Dict[str, Any],
        category: str,
        category_products: List[Dict[str, Any]]
    ) -> float:
        """
        Compute utility of a category for a customer
        
        U_category = β_category × features + λ_category × log(Σ exp(V_brand/λ_brand))
        
        The log-sum term (inclusive value) captures the expected utility
        from the best brands/products within this category.
        """
        # Base category utility
        customer_category = customer.get('favorite_category') or customer.get('dominant_category', '')
        category_match = 1.0 if category == customer_category else 0.0
        
        # Get category purchase frequency
        category_history = customer.get('category_purchase_history', {})
        category_purchases = category_history.get(category, 0)
        
        base_utility = (
            2.0 * category_match +              # Strong preference for favorite category
            0.5 * np.log1p(category_purchases)   # More purchases = higher utility
        )
        
        # Inclusive value: accounts for the attractiveness of brands within category
        if len(category_products) > 0:
            # Get unique brands in this category
            brands = list(set(p.get('brand', '') for p in category_products))
            brand_utilities = []
            
            for brand in brands:
                brand_products = [p for p in category_products if p.get('brand', '') == brand]
                brand_util = self._compute_brand_utility(customer, brand, brand_products)
                brand_utilities.append(brand_util / self.lambda_brand)
            
            # Inclusive value (log-sum of brand utilities)
            inclusive_value = self.lambda_category * logsumexp(brand_utilities)
        else:
            inclusive_value = 0.0
        
        return base_utility + inclusive_value
    
    def _compute_brand_utility(
        self,
        customer: Dict[str, Any],
        brand: str,
        brand_products: List[Dict[str, Any]]
    ) -> float:
        """
        Compute utility of a brand for a customer (within a category)
        
        U_brand|category = β_brand × features + λ_brand × log(Σ exp(V_product))
        """
        # Base brand utility
        brand_history = customer.get('brand_purchase_history', {})
        brand_purchases = brand_history.get(brand, 0)
        brand_familiarity = min(brand_purchases / 10.0, 1.0)  # Normalize to 0-1
        
        base_utility = (
            1.5 * brand_familiarity +  # Strong loyalty to familiar brands
            0.3 * (1.0 if brand_purchases > 0 else 0.0)  # Bonus for any purchase
        )
        
        # Inclusive value: accounts for the attractiveness of products within brand
        if len(brand_products) > 0:
            product_utilities = []
            
            for product in brand_products:
                product_util = self._compute_product_utility(customer, product)
                product_utilities.append(product_util)
            
            # Inclusive value (log-sum of product utilities)
            inclusive_value = self.lambda_brand * logsumexp(product_utilities)
        else:
            inclusive_value = 0.0
        
        return base_utility + inclusive_value
    
    def _compute_product_utility(
        self,
        customer: Dict[str, Any],
        product: Dict[str, Any]
    ) -> float:
        """
        Compute utility of a specific product (within a brand, category)
        
        U_product|brand,category = β_product × features
        
        Enhanced to add more differentiation between products
        """
        features = self._compute_utility_features(customer, product)
        
        # Enhanced utility function with more granular features
        # This ensures products within same brand are differentiated
        
        # Price utility (more granular)
        price_util = (
            -2.0 * features['price_deviation'] +      # Strong penalty for price mismatch
            3.0 * features['price_in_budget'] +       # Strong reward for budget fit
            -0.5 * features['log_price']              # Slight preference for lower prices
        )
        
        # Quality utility
        quality_util = (
            1.5 * features['rating_normalized'] +     # Product rating matters
            0.5 * (features['rating'] - 4.0)          # Bonus for ratings above 4.0
        )
        
        # Expertise utility
        expertise_util = (
            1.2 * features['expertise_match'] +       # Expertise alignment
            -0.8 * (1.0 - features['expertise_match']) # Penalty for mismatch
        )
        
        # Brand familiarity (minor at product level since brand is already chosen)
        brand_util = 0.3 * features['brand_familiarity']
        
        # Add product-specific noise for differentiation
        # (In production, this would come from actual product attributes)
        product_id_hash = hash(product.get('product_id', '')) % 100 / 100.0
        product_variation = 0.2 * product_id_hash  # Small random component
        
        utility = price_util + quality_util + expertise_util + brand_util + product_variation
        
        return utility
    
    def predict_nested_probabilities(
        self,
        customer: Dict[str, Any],
        products_df: pd.DataFrame,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Predict purchase probabilities using nested logit structure
        
        Returns top K products with:
        - Nested probability decomposition (category prob × brand prob × product prob)
        - Overall probability
        - Explanation of choice at each level
        """
        # Step 1: Group products by category
        categories = products_df['main_category'].unique()
        
        # Compute category-level utilities and probabilities
        category_utilities = {}
        for category in categories:
            category_products = products_df[products_df['main_category'] == category].to_dict('records')
            category_utilities[category] = self._compute_category_utility(
                customer, category, category_products
            )
        
        # Category choice probabilities (multinomial logit at top level)
        category_exp_utils = {cat: np.exp(util) for cat, util in category_utilities.items()}
        total_exp_util = sum(category_exp_utils.values())
        category_probs = {cat: exp_util / total_exp_util for cat, exp_util in category_exp_utils.items()}
        
        logger.info(f"📊 Category probabilities: {category_probs}")
        
        # Step 2: For each category, compute brand probabilities
        all_product_probs = []
        
        for category in categories:
            category_prob = category_probs[category]
            category_products = products_df[products_df['main_category'] == category]
            
            if len(category_products) == 0:
                continue
            
            # Get unique brands in this category
            brands = category_products['brand'].unique()
            
            # Compute brand utilities
            brand_utilities = {}
            for brand in brands:
                brand_products = category_products[category_products['brand'] == brand].to_dict('records')
                brand_utilities[brand] = self._compute_brand_utility(customer, brand, brand_products)
            
            # Brand choice probabilities (conditional on category)
            brand_exp_utils = {b: np.exp(util / self.lambda_brand) for b, util in brand_utilities.items()}
            total_brand_exp = sum(brand_exp_utils.values())
            brand_probs = {b: exp_util / total_brand_exp for b, exp_util in brand_exp_utils.items()}
            
            # Step 3: For each brand, compute product probabilities
            for brand in brands:
                brand_prob = brand_probs[brand]
                brand_products = category_products[category_products['brand'] == brand]
                
                # Compute product utilities
                product_utilities = []
                for _, product in brand_products.iterrows():
                    product_dict = product.to_dict()
                    product_util = self._compute_product_utility(customer, product_dict)
                    product_utilities.append((product_dict, product_util))
                
                # Product choice probabilities (conditional on brand and category)
                product_exp_utils = [np.exp(util) for _, util in product_utilities]
                total_product_exp = sum(product_exp_utils)
                
                for (product_dict, product_util), product_exp_util in zip(product_utilities, product_exp_utils):
                    product_prob = product_exp_util / total_product_exp
                    
                    # Joint probability (multiplicative across levels)
                    joint_prob = category_prob * brand_prob * product_prob
                    
                    all_product_probs.append({
                        'product_id': product_dict['product_id'],
                        'product_name': product_dict['product_name'],
                        'brand': product_dict['brand'],
                        'category': category,
                        'price': product_dict['price'],
                        'avg_rating': product_dict.get('avg_rating', 4.0),
                        'complexity': product_dict.get('complexity', 'Moderate'),
                        'probability': joint_prob,
                        'category_prob': category_prob,
                        'brand_prob': brand_prob,
                        'product_prob': product_prob,
                        'explanation': {
                            'category': f"{category_prob*100:.1f}% chose {category}",
                            'brand': f"{brand_prob*100:.1f}% chose {brand} | {category}",
                            'product': f"{product_prob*100:.1f}% chose this product | {brand}, {category}"
                        }
                    })
        
        # Sort by joint probability and return top K
        all_product_probs.sort(key=lambda x: x['probability'], reverse=True)
        
        return all_product_probs[:top_k]
    
    def train(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        purchases_df: pd.DataFrame
    ):
        """
        Train nested logit parameters using maximum likelihood estimation
        
        Note: For simplicity, we use rule-based parameters initially.
        Full MLE estimation would require optimization (scipy.optimize.minimize)
        """
        logger.info("🎓 Training Nested Logit Model...")
        
        # For now, we use theory-guided parameters rather than MLE
        # In production, you'd estimate these from data using MLE
        
        # Estimate nest correlation parameters from data
        # Higher correlation within nests → lower lambda
        self.lambda_category = 0.7  # Moderate correlation within categories
        self.lambda_brand = 0.8     # Slightly less correlation within brands
        
        logger.info(f"✅ Nested Logit Model initialized with λ_category={self.lambda_category}, λ_brand={self.lambda_brand}")
        logger.info("📝 Using theory-guided parameters (can be estimated via MLE in production)")
        
        return self
    
    def save_model(self):
        """Save model parameters"""
        import joblib
        from pathlib import Path
        
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'lambda_category': self.lambda_category,
            'lambda_brand': self.lambda_brand,
            'category_params': self.category_params,
            'brand_params': self.brand_params,
            'product_params': self.product_params
        }
        
        joblib.dump(model_data, self.model_path)
        logger.info(f"✅ Nested Logit model saved to {self.model_path}")
    
    def load_model(self):
        """Load model parameters"""
        import joblib
        from pathlib import Path
        
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        model_data = joblib.load(self.model_path)
        self.lambda_category = model_data['lambda_category']
        self.lambda_brand = model_data['lambda_brand']
        self.category_params = model_data.get('category_params', {})
        self.brand_params = model_data.get('brand_params', {})
        self.product_params = model_data.get('product_params', {})
        
        logger.info(f"✅ Nested Logit model loaded from {self.model_path}")
  

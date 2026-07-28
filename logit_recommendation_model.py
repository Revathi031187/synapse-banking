"""
Logistic Regression Model for Product Recommendations
Predicts purchase probability based on customer-product features
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
import joblib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LogitRecommendationModel:
    """
    Logistic Regression model for predicting purchase probability
    
    Features Used:
    1. Price Features:
       - Price deviation from customer average
       - Price tier match (budget/mid/premium)
       - Affordability score
    
    2. Category Features:
       - Category exact match (binary)
       - Category parent match
       - Customer's category affinity
    
    3. Behavioral Features:
       - Customer expertise level
       - Product complexity level
       - Bundle preference match
       - Brand loyalty score
    
    4. Historical Features:
       - Customer purchase frequency
       - Product popularity
       - Co-purchase patterns
    """
    
    def __init__(self, model_path: str = "models/logit_recommendation.pkl"):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = Path(model_path)
        self.feature_names = []
        
    def _extract_features(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        purchases_df: pd.DataFrame,
        personas_df: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Extract features for customer-product pairs
        
        Returns DataFrame with columns:
        - customer_id, product_id, purchased (target), feature_1, feature_2, ...
        """
        logger.info("Extracting features for logit model...")
        
        # Create all possible customer-product pairs
        customer_ids = customers_df['customer_id'].unique()
        product_ids = products_df['product_id'].unique()
        
        # For training, we sample to avoid memory issues
        # In production, generate features only for candidate products
        pairs = []
        for cid in customer_ids[:1000]:  # Sample 1000 customers for training
            for pid in product_ids[:50]:  # Sample 50 products
                pairs.append({'customer_id': cid, 'product_id': pid})
        
        features_df = pd.DataFrame(pairs)
        
        # Add target: did customer purchase this product?
        purchases_set = set(zip(purchases_df['customer_id'], purchases_df['product_id']))
        features_df['purchased'] = features_df.apply(
            lambda row: 1 if (row['customer_id'], row['product_id']) in purchases_set else 0,
            axis=1
        )
        
        logger.info(f"Total pairs: {len(features_df)}, Positive rate: {features_df['purchased'].mean():.2%}")
        
        # Merge customer data (using actual column names from Academy Sports data)
        customer_cols = ['customer_id', 'purchase_frequency', 'avg_order_value', 'dominant_category']
        
        # Add total_spend_12mo if it exists (renamed to total_spend for compatibility)
        if 'total_spend_12mo' in customers_df.columns:
            customers_df = customers_df.copy()
            customers_df['total_spend'] = customers_df['total_spend_12mo']
            customer_cols.append('total_spend')
        
        features_df = features_df.merge(
            customers_df[customer_cols],
            on='customer_id',
            how='left'
        )
        
        # Rename dominant_category to favorite_category for consistency
        if 'dominant_category' in features_df.columns:
            features_df['favorite_category'] = features_df['dominant_category']
        
        # Merge product data
        features_df = features_df.merge(
            products_df[['product_id', 'price', 'main_category', 'subcategory', 
                        'avg_rating', 'brand', 'complexity']],
            on='product_id',
            how='left'
        )
        
        # === FEATURE ENGINEERING ===
        
        # 1. PRICE FEATURES (35% importance in rule-based system)
        features_df['price_deviation'] = abs(
            features_df['price'] - features_df['avg_order_value']
        ) / features_df['avg_order_value'].clip(lower=1)
        
        features_df['price_affordability'] = (
            features_df['avg_order_value'] / features_df['price'].clip(lower=1)
        ).clip(0, 3)  # Cap at 3x affordable
        
        features_df['price_in_range'] = (
            (features_df['price'] >= features_df['avg_order_value'] * 0.5) &
            (features_df['price'] <= features_df['avg_order_value'] * 2.0)
        ).astype(int)
        
        # 2. CATEGORY FEATURES (30% importance)
        features_df['category_exact_match'] = (
            features_df['main_category'] == features_df['favorite_category']
        ).astype(int)
        
        # Calculate category purchase frequency
        category_freq = purchases_df.merge(
            products_df[['product_id', 'main_category']], 
            on='product_id'
        ).groupby(['customer_id', 'main_category']).size().reset_index(name='category_purchase_count')
        
        features_df = features_df.merge(
            category_freq,
            left_on=['customer_id', 'main_category'],
            right_on=['customer_id', 'main_category'],
            how='left'
        )
        features_df['category_purchase_count'] = features_df['category_purchase_count'].fillna(0)
        
        # 3. EXPERTISE MATCH FEATURES (20% importance)
        expertise_map = {'beginner': 1, 'intermediate': 2, 'expert': 3}
        complexity_map = {'Simple': 1, 'Moderate': 2, 'Advanced': 3, 'Expert': 4}
        
        # Derive expertise_level if not present (based on purchase frequency and avg spend)
        if 'expertise_level' not in features_df.columns:
            # Infer expertise from purchase behavior
            features_df['expertise_level'] = 'intermediate'  # default
            features_df.loc[features_df['purchase_frequency'] <= 2, 'expertise_level'] = 'beginner'
            features_df.loc[(features_df['purchase_frequency'] >= 5) & 
                          (features_df['avg_order_value'] >= 200), 'expertise_level'] = 'expert'
        
        features_df['customer_expertise_num'] = features_df['expertise_level'].map(expertise_map).fillna(2)
        features_df['product_complexity_num'] = features_df['complexity'].map(complexity_map).fillna(2)
        
        features_df['expertise_match'] = 1 - abs(
            features_df['customer_expertise_num'] - features_df['product_complexity_num']
        ) / 3  # Normalize to 0-1
        
        features_df['expertise_mismatch'] = (
            abs(features_df['customer_expertise_num'] - features_df['product_complexity_num']) > 1
        ).astype(int)
        
        # 4. BRAND LOYALTY FEATURES (15% importance)
        brand_freq = purchases_df.merge(
            products_df[['product_id', 'brand']],
            on='product_id'
        ).groupby(['customer_id', 'brand']).size().reset_index(name='brand_purchase_count')
        
        features_df = features_df.merge(
            brand_freq,
            left_on=['customer_id', 'brand'],
            right_on=['customer_id', 'brand'],
            how='left'
        )
        features_df['brand_purchase_count'] = features_df['brand_purchase_count'].fillna(0)
        features_df['brand_loyalty'] = (features_df['brand_purchase_count'] > 0).astype(int)
        
        # 5. PRODUCT QUALITY FEATURES (5% importance)
        features_df['rating_score'] = features_df['avg_rating'] / 5.0
        
        # 6. BEHAVIORAL FEATURES
        features_df['purchase_frequency_score'] = np.log1p(features_df['purchase_frequency'])
        features_df['customer_spend_tier'] = pd.qcut(
            features_df['total_spend'], 
            q=3, 
            labels=['low', 'mid', 'high'],
            duplicates='drop'
        )
        
        # One-hot encode spend tier
        spend_dummies = pd.get_dummies(features_df['customer_spend_tier'], prefix='spend')
        features_df = pd.concat([features_df, spend_dummies], axis=1)
        
        # 7. INTERACTION FEATURES (capturing non-linear relationships)
        features_df['price_category_interaction'] = (
            features_df['price_deviation'] * features_df['category_exact_match']
        )
        
        features_df['expertise_price_interaction'] = (
            features_df['expertise_match'] * features_df['price_affordability']
        )
        
        # Select final feature columns
        feature_cols = [
            # Price features
            'price_deviation', 'price_affordability', 'price_in_range',
            # Category features
            'category_exact_match', 'category_purchase_count',
            # Expertise features
            'expertise_match', 'expertise_mismatch',
            # Brand features
            'brand_purchase_count', 'brand_loyalty',
            # Quality features
            'rating_score',
            # Behavioral features
            'purchase_frequency_score',
            # Spend tier (one-hot encoded)
            'spend_low', 'spend_mid', 'spend_high',
            # Interaction features
            'price_category_interaction', 'expertise_price_interaction'
        ]
        
        # Handle missing values
        for col in feature_cols:
            if col in features_df.columns:
                features_df[col] = features_df[col].fillna(0)
        
        self.feature_names = feature_cols
        
        return features_df[['customer_id', 'product_id', 'purchased'] + feature_cols]
    
    def train(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        purchases_df: pd.DataFrame,
        test_size: float = 0.2,
        balance_classes: bool = True
    ):
        """
        Train logistic regression model on historical purchase data
        
        Args:
            customers_df: Customer features
            products_df: Product features
            purchases_df: Historical purchases (positive examples)
            test_size: Proportion of data for testing
            balance_classes: Whether to balance positive/negative classes
        """
        logger.info("🚀 Starting logit model training...")
        
        # Extract features
        features_df = self._extract_features(customers_df, products_df, purchases_df)
        
        # Balance classes if needed (since most pairs are not purchased)
        if balance_classes:
            positive = features_df[features_df['purchased'] == 1]
            negative = features_df[features_df['purchased'] == 0].sample(
                n=len(positive) * 3,  # 1:3 ratio (more realistic than 1:1)
                random_state=42
            )
            features_df = pd.concat([positive, negative]).sample(frac=1, random_state=42)
            logger.info(f"Balanced dataset: {len(positive)} positive, {len(negative)} negative")
        
        # Split features and target
        X = features_df[self.feature_names]
        y = features_df['purchased']
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train logistic regression with L2 regularization
        self.model = LogisticRegression(
            penalty='l2',
            C=1.0,  # Inverse regularization strength
            max_iter=1000,
            random_state=42,
            class_weight='balanced'  # Handle any remaining class imbalance
        )
        
        logger.info("Training logistic regression model...")
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_proba = self.model.predict_proba(X_train_scaled)[:, 1]
        test_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        train_auc = roc_auc_score(y_train, train_proba)
        test_auc = roc_auc_score(y_test, test_proba)
        
        logger.info(f"✅ Training complete!")
        logger.info(f"   Train AUC: {train_auc:.4f}")
        logger.info(f"   Test AUC: {test_auc:.4f}")
        
        # Show feature importance (coefficients)
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'coefficient': self.model.coef_[0]
        }).sort_values('coefficient', key=abs, ascending=False)
        
        logger.info("\n📊 Top 10 Most Important Features:")
        for _, row in feature_importance.head(10).iterrows():
            logger.info(f"   {row['feature']}: {row['coefficient']:.4f}")
        
        # Save model
        self.save_model()
        
        return {
            'train_auc': train_auc,
            'test_auc': test_auc,
            'feature_importance': feature_importance.to_dict('records')
        }
    
    def predict_purchase_probability(
        self,
        customer_features: dict,
        product_features: dict
    ) -> float:
        """
        Predict probability that customer will purchase product
        
        Args:
            customer_features: Dict with customer data
            product_features: Dict with product data
        
        Returns:
            Probability (0-1) of purchase
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first or load_model()")
        
        # Build feature vector
        features = self._build_feature_vector(customer_features, product_features)
        
        # Convert to DataFrame with feature names to match training
        import pandas as pd
        features_df = pd.DataFrame([features], columns=self.feature_names)
        
        # Scale and predict
        features_scaled = self.scaler.transform(features_df)
        probability = self.model.predict_proba(features_scaled)[0, 1]
        
        # Debug logging for first few predictions
        if not hasattr(self, '_prediction_count'):
            self._prediction_count = 0
        
        if self._prediction_count < 3:
            logger.info(f"   🔮 Prediction {self._prediction_count + 1}: {product_features.get('product_name', 'Unknown')}")
            logger.info(f"      Customer: AOV=${customer_features.get('avg_order_value')}, Category={customer_features.get('favorite_category')}")
            logger.info(f"      Product: Price=${product_features.get('price')}, Category={product_features.get('main_category')}")
            logger.info(f"      ML Probability: {probability:.4f} ({probability*100:.2f}%)")
        
        self._prediction_count += 1
        
        return float(probability)
    
    def _build_feature_vector(self, customer: dict, product: dict) -> list:
        """Build feature vector for prediction"""
        # This should match the feature engineering in _extract_features
        # Simplified version for single prediction
        
        avg_order = customer.get('avg_order_value', 50)
        price = product.get('price', 50)
        
        features = []
        
        # Price features
        features.append(abs(price - avg_order) / max(avg_order, 1))  # price_deviation
        features.append(min(avg_order / max(price, 1), 3))  # price_affordability
        features.append(1 if 0.5 * avg_order <= price <= 2.0 * avg_order else 0)  # price_in_range
        
        # Category features (use dominant_category if favorite_category not available)
        favorite_cat = customer.get('favorite_category') or customer.get('dominant_category')
        features.append(1 if product.get('main_category') == favorite_cat else 0)
        features.append(customer.get('category_purchase_count', 0))
        
        # Expertise features (derive if not present)
        expertise_map = {'beginner': 1, 'intermediate': 2, 'expert': 3}
        complexity_map = {'Simple': 1, 'Moderate': 2, 'Advanced': 3, 'Expert': 4}
        
        # Derive expertise level from purchase behavior if not present
        # Consistent with agent_b_logit_enhanced.py logic
        cust_expertise_level = customer.get('expertise_level')
        if not cust_expertise_level:
            purchase_freq = customer.get('purchase_frequency', 0)
            avg_order = customer.get('avg_order_value', 0)
            # Aligned criteria for consistent persona profiling
            if purchase_freq >= 6 and avg_order >= 250:
                cust_expertise_level = 'expert'
            elif purchase_freq >= 4 or avg_order >= 150:
                cust_expertise_level = 'intermediate'
            else:
                cust_expertise_level = 'beginner'
        
        cust_exp = expertise_map.get(cust_expertise_level, 2)
        prod_comp = complexity_map.get(product.get('complexity', 'Moderate'), 2)
        
        features.append(1 - abs(cust_exp - prod_comp) / 3)  # expertise_match
        features.append(1 if abs(cust_exp - prod_comp) > 1 else 0)  # expertise_mismatch
        
        # Brand features
        features.append(customer.get('brand_purchase_count', 0))
        features.append(1 if customer.get('brand_purchase_count', 0) > 0 else 0)
        
        # Quality
        features.append(product.get('avg_rating', 4.0) / 5.0)
        
        # Behavioral
        features.append(np.log1p(customer.get('purchase_frequency', 1)))
        
        # Spend tier (one-hot) - need to determine tier
        total_spend = customer.get('total_spend', 0)
        if total_spend < 500:
            features.extend([1, 0, 0])  # low
        elif total_spend < 2000:
            features.extend([0, 1, 0])  # mid
        else:
            features.extend([0, 0, 1])  # high
        
        # Interactions
        features.append(features[0] * features[3])  # price_category_interaction
        features.append(features[5] * features[1])  # expertise_price_interaction
        
        return features
    
    def save_model(self):
        """Save trained model and scaler"""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        
        joblib.dump(model_data, self.model_path)
        logger.info(f"✅ Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        model_data = joblib.load(self.model_path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        
        logger.info(f"✅ Model loaded from {self.model_path}")


# Example usage and training script
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    
    # Load your data
    customers = pd.read_csv('data/preloaded/academy_sports/customers.csv')
    products = pd.read_csv('data/preloaded/academy_sports/products.csv')
    purchases = pd.read_csv('data/preloaded/academy_sports/purchases.csv')
    
    # Train model
    logit_model = LogitRecommendationModel()
    results = logit_model.train(customers, products, purchases)
    
    print("\n🎉 Training Complete!")
    print(f"Test AUC: {results['test_auc']:.4f}")

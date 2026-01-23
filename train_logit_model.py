#!/usr/bin/env python3
"""
Training script for Logistic Regression Recommendation Model
Run this once to train the model, then it can be used in Agent B
"""

import pandas as pd
import logging
from pathlib import Path
from agents.logit_recommendation_model import LogitRecommendationModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Train logistic regression model for product recommendations"""
    
    print("\n" + "="*80)
    print("🎯 LOGISTIC REGRESSION MODEL TRAINING")
    print("Academy Sports Product Recommendations")
    print("="*80 + "\n")
    
    # Check if data files exist
    data_dir = Path('data/preloaded/academy_sports')
    
    required_files = ['customers.csv', 'products.csv', 'purchases.csv']
    missing_files = [f for f in required_files if not (data_dir / f).exists()]
    
    if missing_files:
        logger.error(f"❌ Missing data files: {missing_files}")
        logger.error(f"   Please run data generator first:")
        logger.error(f"   python utils/academy_sports_data_generator_fast.py")
        return
    
    # Load data
    logger.info("📂 Loading training data...")
    customers = pd.read_csv(data_dir / 'customers.csv')
    products = pd.read_csv(data_dir / 'products.csv')
    purchases = pd.read_csv(data_dir / 'purchases.csv')
    
    logger.info(f"   ✓ Customers: {len(customers):,}")
    logger.info(f"   ✓ Products: {len(products):,}")
    logger.info(f"   ✓ Purchases: {len(purchases):,}")
    
    # Initialize model
    model_path = "models/logit_recommendation.pkl"
    logger.info(f"\n🤖 Initializing model (will save to: {model_path})")
    model = LogitRecommendationModel(model_path=model_path)
    
    # Train model
    logger.info("\n🎓 Training model (this may take 1-2 minutes)...")
    results = model.train(
        customers_df=customers,
        products_df=products,
        purchases_df=purchases,
        test_size=0.2,
        balance_classes=True
    )
    
    # Display results
    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE!")
    print("="*80)
    print(f"\n📊 Model Performance:")
    print(f"   • Train AUC: {results['train_auc']:.4f}")
    print(f"   • Test AUC:  {results['test_auc']:.4f}")
    
    if results['test_auc'] >= 0.85:
        print(f"   • Rating: 🌟🌟🌟 Excellent!")
    elif results['test_auc'] >= 0.80:
        print(f"   • Rating: 🌟🌟 Very Good")
    elif results['test_auc'] >= 0.75:
        print(f"   • Rating: 🌟 Good")
    else:
        print(f"   • Rating: ⚠️ Acceptable (consider more data or feature engineering)")
    
    print(f"\n🔑 Top 10 Most Important Features:")
    for i, feat in enumerate(results['feature_importance'][:10], 1):
        coef = feat['coefficient']
        sign = "+" if coef > 0 else ""
        print(f"   {i:2d}. {feat['feature']:30s} {sign}{coef:.4f}")
    
    print(f"\n💾 Model saved to: {model_path}")
    
    # Test prediction
    print(f"\n🧪 Testing prediction capability...")
    test_customer = {
        'avg_order_value': 75.0,
        'purchase_frequency': 8,
        'total_spend': 600.0,
        'expertise_level': 'intermediate',
        'favorite_category': 'Tents',
        'category_purchase_count': 5,
        'brand_purchase_count': 2
    }
    
    test_product = {
        'price': 89.99,
        'main_category': 'Tents',
        'avg_rating': 4.5,
        'complexity': 'Moderate',
        'brand': 'Coleman'
    }
    
    prob = model.predict_purchase_probability(test_customer, test_product)
    print(f"   Sample prediction: {prob:.1%} purchase probability")
    print(f"   (Intermediate customer, $75 avg spend → $90 tent)")
    
    print("\n" + "="*80)
    print("🎉 SUCCESS! Model is ready to use in Agent B")
    print("="*80)
    
    print("\n📖 Next Steps:")
    print("   1. Integrate model into Agent B API (see LOGIT_IMPLEMENTATION_GUIDE.md)")
    print("   2. Test with: curl http://localhost:8002/api/academy/recommendations/logit")
    print("   3. Compare with rule-based scoring")
    print("   4. Set up monthly retraining schedule\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Training interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Training failed: {e}", exc_info=True)
        print("\n💡 Tip: Check that data files exist and are properly formatted")

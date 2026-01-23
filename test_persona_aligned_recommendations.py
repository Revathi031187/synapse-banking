"""
Test Persona-Aligned Recommendations
Verifies that recommendations match segment characteristics
"""

import pandas as pd
import numpy as np
from agents.agent_b_academy_persona_aligned import PersonaAlignedRecommender

# Create sample data
def create_test_data():
    """Create sample customers, products, purchases, and personas"""
    
    # Sample customers
    customers_df = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003'],
        'customer_name': ['John Premium', 'Jane Budget', 'Bob Expert'],
        'cluster': [0, 1, 2],
        'total_spend_12mo': [1200, 300, 800],
        'avg_order_value': [240, 50, 160],
        'dominant_category': ['Hiking Backpacks', 'Tents + Screen Houses', 'Camping Cookware + Stoves'],
        'search_specificity': [4.2, 1.8, 3.5],
        'bundle_affinity': [0.3, 0.8, 0.4],
        'price_sort_frequency': [0.2, 0.9, 0.5]
    })
    
    # Sample products
    products_df = pd.DataFrame({
        'product_id': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006'],
        'product_name': [
            'Osprey Atmos 65L Backpack',
            'Coleman 4-Person Tent',
            'REI Co-op Flash 55 Backpack',
            'Budget Camping Tent',
            'Premium Cooking Set',
            'Basic Cooking Kit'
        ],
        'brand': ['Osprey', 'Coleman', 'REI', 'Ozark Trail', 'MSR', 'Coleman'],
        'main_category': [
            'Hiking Backpacks',
            'Tents + Screen Houses',
            'Hiking Backpacks',
            'Tents + Screen Houses',
            'Camping Cookware + Stoves',
            'Camping Cookware + Stoves'
        ],
        'subcategory': ['Backpacking', 'Family Camping', 'Backpacking', 'Car Camping', 'Backpacking', 'Car Camping'],
        'price': [249, 89, 149, 45, 180, 35],
        'avg_rating': [4.7, 4.2, 4.5, 3.8, 4.6, 4.0],
        'num_reviews': [234, 567, 189, 123, 98, 456],
        'in_stock': [True, True, True, True, True, True],
        'complexity': ['Advanced', 'Simple', 'Moderate', 'Simple', 'Technical', 'Simple']
    })
    
    # Sample purchases
    purchases_df = pd.DataFrame({
        'customer_id': ['C001', 'C001', 'C002', 'C002', 'C003'],
        'product_id': ['P001', 'P003', 'P002', 'P004', 'P005'],
        'price_paid': [249, 149, 89, 45, 180],
        'purchase_date': pd.date_range('2025-01-01', periods=5, freq='30D')
    })
    
    # Sample personas
    personas = {
        0: {  # Premium Outdoor Buyers
            'persona_name': 'Premium Outdoor Buyers',
            'cluster_id': 0,
            'revenue_metrics': {
                'avg_customer_value': 1200
            },
            'characteristics': {
                'search_specificity': 4.2,
                'bundle_affinity': 0.3,
                'price_sort_frequency': 0.2,
                'top_categories': ['Hiking Backpacks', 'Tents + Screen Houses']
            }
        },
        1: {  # Budget Campers
            'persona_name': 'Budget Campers',
            'cluster_id': 1,
            'revenue_metrics': {
                'avg_customer_value': 300
            },
            'characteristics': {
                'search_specificity': 1.8,
                'bundle_affinity': 0.8,
                'price_sort_frequency': 0.9,
                'top_categories': ['Tents + Screen Houses', 'Sleeping Bags + Airbeds']
            }
        },
        2: {  # Intermediate Adventurers
            'persona_name': 'Intermediate Adventurers',
            'cluster_id': 2,
            'revenue_metrics': {
                'avg_customer_value': 800
            },
            'characteristics': {
                'search_specificity': 3.5,
                'bundle_affinity': 0.4,
                'price_sort_frequency': 0.5,
                'top_categories': ['Camping Cookware + Stoves', 'Hiking Backpacks']
            }
        }
    }
    
    return customers_df, products_df, purchases_df, personas


def test_premium_customer():
    """Test recommendations for premium customer"""
    print("\n" + "="*80)
    print("TEST 1: Premium Customer (C001)")
    print("="*80)
    
    customers_df, products_df, purchases_df, personas = create_test_data()
    
    recommender = PersonaAlignedRecommender(
        customers_df=customers_df,
        products_df=products_df,
        purchases_df=purchases_df,
        personas=personas
    )
    
    result = recommender.get_persona_aligned_recommendations('C001', n_recommendations=3)
    
    print(f"\n✅ Customer: {result['customer_id']}")
    print(f"✅ Persona: {result['persona']}")
    print(f"✅ Price Range: ${result['price_range']['min']:.0f} - ${result['price_range']['max']:.0f}")
    print(f"✅ Target Price: ${result['price_range']['target']:.0f}")
    
    print(f"\n📦 Recommendations ({len(result['recommendations'])}):")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"\n   {i}. {rec['product_name']}")
        print(f"      Price: ${rec['price']:.0f}")
        print(f"      Alignment Score: {rec.get('alignment_score', 0):.2f}")
        print(f"      Reason: {rec['reason'][:100]}...")
    
    # Verify price alignment
    prices = [rec['price'] for rec in result['recommendations']]
    target = result['price_range']['target']
    avg_deviation = np.mean([abs(p - target) / target for p in prices])
    
    print(f"\n📊 VALIDATION:")
    print(f"   Avg Price Deviation: {avg_deviation*100:.1f}%")
    print(f"   Expected: <50% for premium customers")
    
    if avg_deviation < 0.5:
        print(f"   ✅ PASS: Prices align with persona!")
    else:
        print(f"   ❌ FAIL: Prices don't match persona")
    
    return avg_deviation < 0.5


def test_budget_customer():
    """Test recommendations for budget customer"""
    print("\n" + "="*80)
    print("TEST 2: Budget Customer (C002)")
    print("="*80)
    
    customers_df, products_df, purchases_df, personas = create_test_data()
    
    recommender = PersonaAlignedRecommender(
        customers_df=customers_df,
        products_df=products_df,
        purchases_df=purchases_df,
        personas=personas
    )
    
    result = recommender.get_persona_aligned_recommendations('C002', n_recommendations=3)
    
    print(f"\n✅ Customer: {result['customer_id']}")
    print(f"✅ Persona: {result['persona']}")
    print(f"✅ Price Range: ${result['price_range']['min']:.0f} - ${result['price_range']['max']:.0f}")
    print(f"✅ Target Price: ${result['price_range']['target']:.0f}")
    
    print(f"\n📦 Recommendations ({len(result['recommendations'])}):")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"\n   {i}. {rec['product_name']}")
        print(f"      Price: ${rec['price']:.0f}")
        print(f"      Alignment Score: {rec.get('alignment_score', 0):.2f}")
    
    # Verify budget constraint
    prices = [rec['price'] for rec in result['recommendations']]
    max_price = result['price_range']['max']
    
    print(f"\n📊 VALIDATION:")
    print(f"   Max Recommended Price: ${max(prices):.0f}")
    print(f"   Budget Limit: ${max_price:.0f}")
    
    if max(prices) <= max_price * 1.1:  # Allow 10% tolerance
        print(f"   ✅ PASS: Within budget!")
    else:
        print(f"   ❌ FAIL: Exceeds budget")
    
    return max(prices) <= max_price * 1.1


def test_expertise_match():
    """Test that expertise levels match"""
    print("\n" + "="*80)
    print("TEST 3: Expertise Matching")
    print("="*80)
    
    customers_df, products_df, purchases_df, personas = create_test_data()
    
    recommender = PersonaAlignedRecommender(
        customers_df=customers_df,
        products_df=products_df,
        purchases_df=purchases_df,
        personas=personas
    )
    
    # Test premium customer (expert)
    result_premium = recommender.get_persona_aligned_recommendations('C001', n_recommendations=3)
    
    # Test budget customer (beginner)
    result_budget = recommender.get_persona_aligned_recommendations('C002', n_recommendations=3)
    
    print(f"\n✅ Premium Customer (Expert - 4.2/5.0):")
    print(f"   Persona Characteristics: {result_premium['persona_characteristics']}")
    
    print(f"\n✅ Budget Customer (Beginner - 1.8/5.0):")
    print(f"   Persona Characteristics: {result_budget['persona_characteristics']}")
    
    print(f"\n📊 VALIDATION:")
    print(f"   Premium should get 'expert' level: {result_premium['persona_characteristics']['expertise_level']}")
    print(f"   Budget should get 'beginner' level: {result_budget['persona_characteristics']['expertise_level']}")
    
    expert_match = result_premium['persona_characteristics']['expertise_level'] == 'expert'
    beginner_match = result_budget['persona_characteristics']['expertise_level'] == 'beginner'
    
    if expert_match and beginner_match:
        print(f"   ✅ PASS: Expertise levels correctly matched!")
    else:
        print(f"   ❌ FAIL: Expertise mismatch")
    
    return expert_match and beginner_match


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 PERSONA-ALIGNED RECOMMENDATIONS TEST SUITE")
    print("="*80)
    
    results = []
    
    try:
        results.append(("Premium Customer Price Alignment", test_premium_customer()))
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        results.append(("Premium Customer Price Alignment", False))
    
    try:
        results.append(("Budget Customer Price Constraint", test_budget_customer()))
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        results.append(("Budget Customer Price Constraint", False))
    
    try:
        results.append(("Expertise Level Matching", test_expertise_match()))
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        results.append(("Expertise Level Matching", False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Persona-aligned recommendations working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")

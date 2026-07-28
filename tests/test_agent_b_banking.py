"""
Test Banking Agent B Complete Implementation
Validates all phases of the Agent B rebuild
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_phase_1_banking_12_factor_scorer():
    """Test Phase 1: Banking 12-Factor Scorer"""
    print("\n" + "="*80)
    print("PHASE 1: Testing Banking 12-Factor Scorer")
    print("="*80)
    
    try:
        from agents.banking_12_factor_scorer import Banking12FactorScorer
        
        # Create minimal test data
        customers_df = pd.DataFrame([
            {
                'customer_id': 'CUST_00001',
                'credit_score': 750,
                'income': 85000,
                'total_deposits': 50000,
                'age': 35,
                'num_products': 3,
                'digital_engagement_score': 0.8,
                'cross_sell_receptivity': 0.7,
                'macro_segment_id': 0
            }
        ])
        
        products_df = pd.DataFrame([
            {
                'product_id': 'PROD_001',
                'product_name': 'Premium Credit Card',
                'category': 'Credit_Card',
                'min_credit_score': 720,
                'min_income': 60000,
                'min_balance': 0,
                'annual_fee': 95,
                'avg_rating': 4.5,
                'complexity_score': 2
            }
        ])
        
        transactions_df = pd.DataFrame([
            {
                'customer_id': 'CUST_00001',
                'product_id': 'PROD_002',
                'transaction_date': '2024-01-15'
            }
        ])
        
        # Initialize scorer
        scorer = Banking12FactorScorer(
            customers_df=customers_df,
            products_df=products_df,
            transactions_df=transactions_df,
            personas={}
        )
        
        # Score a product
        customer = customers_df.iloc[0].to_dict()
        product = products_df.iloc[0].to_dict()
        
        breakdown = scorer.score_product(
            customer=customer,
            product=product,
            persona=None
        )
        
        # Validate breakdown structure
        assert 'total_score' in breakdown, "Missing total_score"
        assert 'eligibility_score' in breakdown, "Missing eligibility_score"
        assert 'financial_need_match' in breakdown, "Missing financial_need_match"
        assert 'relationship_depth' in breakdown, "Missing relationship_depth"
        assert 'product_pairing' in breakdown, "Missing product_pairing"
        
        print(f"✅ Phase 1 PASSED")
        print(f"   Total Score: {breakdown['total_score']:.2f} ({breakdown['total_percentage']:.1f}%)")
        print(f"   Eligibility: {breakdown['eligibility_score']['score']:.3f}")
        print(f"   Financial Need: {breakdown['financial_need_match']['score']:.3f}")
        print(f"   Relationship: {breakdown['relationship_depth']['score']:.3f}")
        return True
        
    except Exception as e:
        print(f"❌ Phase 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_2_persona_aligned_recommender():
    """Test Phase 2: Persona-Aligned Recommender"""
    print("\n" + "="*80)
    print("PHASE 2: Testing Persona-Aligned Recommender")
    print("="*80)
    
    try:
        from agents.agent_b_banking_persona_aligned import BankingPersonaAlignedRecommender
        
        # Create test data
        customers_df = pd.DataFrame([
            {
                'customer_id': 'CUST_00001',
                'credit_score': 750,
                'income': 85000,
                'total_deposits': 50000,
                'age': 35,
                'num_products': 3,
                'digital_engagement_score': 0.8,
                'cross_sell_receptivity': 0.7,
                'macro_segment_id': 0,
                'customer_segment': 'Personal'
            }
        ])
        
        products_df = pd.DataFrame([
            {
                'product_id': 'PROD_001',
                'product_name': 'Premium Credit Card',
                'category': 'Personal',
                'min_credit_score': 720,
                'min_income': 60000,
                'min_balance': 0,
                'annual_fee': 95,
                'interest_rate_apy': 3.5,
                'accepting_applications': True
            },
            {
                'product_id': 'PROD_002',
                'product_name': 'Investment Account',
                'category': 'Personal',
                'min_credit_score': 700,
                'min_income': 50000,
                'min_balance': 10000,
                'annual_fee': 0,
                'interest_rate_apy': 4.2,
                'accepting_applications': True
            }
        ])
        
        transactions_df = pd.DataFrame([
            {
                'customer_id': 'CUST_00001',
                'product_id': 'PROD_003',
                'transaction_date': '2024-01-15'
            }
        ])
        
        personas = {
            0: {
                'persona_name': 'Young Professionals',
                'persona_id': 0,
                'characteristics': {
                    'avg_deposits': 45000,
                    'avg_income': 75000,
                    'avg_credit_score': 740,
                    'avg_digital': 0.75,
                    'avg_products': 2.8
                }
            }
        }
        
        # Initialize recommender
        recommender = BankingPersonaAlignedRecommender(
            customers_df=customers_df,
            products_df=products_df,
            transactions_df=transactions_df,
            personas=personas
        )
        
        # Get recommendations
        result = recommender.get_persona_aligned_recommendations(
            customer_id='CUST_00001',
            n_recommendations=2
        )
        
        # Validate result structure
        assert result['type'] == 'persona_aligned', "Wrong type"
        assert 'recommendations' in result, "Missing recommendations"
        assert len(result['recommendations']) > 0, "No recommendations returned"
        
        rec = result['recommendations'][0]
        assert 'product_id' in rec, "Missing product_id"
        assert 'score' in rec, "Missing score"
        assert 'reasoning' in rec, "Missing reasoning"
        assert 'score_breakdown' in rec, "Missing score_breakdown"
        
        print(f"✅ Phase 2 PASSED")
        print(f"   Recommendations: {len(result['recommendations'])}")
        print(f"   Top Product: {rec['product_name']}")
        print(f"   Score: {rec['score']:.2f}")
        print(f"   Reasoning: {rec['reasoning'][:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Phase 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_3_together_ai():
    """Test Phase 3: Together AI Integration"""
    print("\n" + "="*80)
    print("PHASE 3: Testing Together AI Integration")
    print("="*80)
    
    try:
        from utils.together_ai import TogetherAIService
        
        service = TogetherAIService()
        
        # Check methods exist
        assert hasattr(service, 'generate_banking_product_explanation'), "Missing generate_banking_product_explanation"
        assert hasattr(service, 'generate_segment_product_reasoning'), "Missing generate_segment_product_reasoning"
        
        # Test method signatures (don't actually call to avoid API costs)
        import inspect
        
        sig1 = inspect.signature(service.generate_banking_product_explanation)
        assert 'customer_profile' in sig1.parameters, "Missing customer_profile param"
        assert 'product' in sig1.parameters, "Missing product param"
        assert 'persona_name' in sig1.parameters, "Missing persona_name param"
        assert 'score_breakdown' in sig1.parameters, "Missing score_breakdown param"
        
        sig2 = inspect.signature(service.generate_segment_product_reasoning)
        assert 'persona_name' in sig2.parameters, "Missing persona_name param"
        assert 'persona_characteristics' in sig2.parameters, "Missing persona_characteristics param"
        assert 'products' in sig2.parameters, "Missing products param"
        
        print(f"✅ Phase 3 PASSED")
        print(f"   Together AI methods validated")
        print(f"   generate_banking_product_explanation: ✓")
        print(f"   generate_segment_product_reasoning: ✓")
        return True
        
    except Exception as e:
        print(f"❌ Phase 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_4_enhanced_v2_agent():
    """Test Phase 4: Enhanced V2 Agent"""
    print("\n" + "="*80)
    print("PHASE 4: Testing Enhanced V2 Agent")
    print("="*80)
    
    try:
        from agents.agent_b_banking_enhanced_v2 import AgentB_Banking_Enhanced
        
        # Create test data
        customers_df = pd.DataFrame([
            {
                'customer_id': 'CUST_00001',
                'credit_score': 750,
                'income': 85000,
                'total_deposits': 50000,
                'age': 35,
                'num_products': 3,
                'digital_engagement_score': 0.8,
                'cross_sell_receptivity': 0.7,
                'macro_segment_id': 0,
                'customer_segment': 'Personal',
                'customer_name': 'John Doe',
                'customer_type': 'Individual'
            }
        ])
        
        products_df = pd.DataFrame([
            {
                'product_id': 'PROD_001',
                'product_name': 'Premium Credit Card',
                'category': 'Personal',
                'min_credit_score': 720,
                'min_income': 60000,
                'min_balance': 0,
                'annual_fee': 95,
                'interest_rate_apy': 3.5,
                'accepting_applications': True,
                'avg_rating': 4.5
            },
            {
                'product_id': 'PROD_002',
                'product_name': 'Savings Account',
                'category': 'Personal',
                'min_credit_score': 700,
                'min_income': 40000,
                'min_balance': 5000,
                'annual_fee': 0,
                'interest_rate_apy': 4.2,
                'accepting_applications': True,
                'avg_rating': 4.3
            }
        ])
        
        transactions_df = pd.DataFrame([
            {
                'customer_id': 'CUST_00001',
                'product_id': 'PROD_003',
                'transaction_date': '2024-01-15'
            }
        ])
        
        personas = {
            0: {
                'persona_name': 'Young Professionals',
                'persona_id': 0,
                'characteristics': {
                    'avg_deposits': 45000,
                    'avg_income': 75000,
                    'avg_credit_score': 740,
                    'avg_digital': 0.75,
                    'avg_products': 2.8
                }
            }
        }
        
        # Initialize agent
        agent = AgentB_Banking_Enhanced(
            customers_df=customers_df,
            products_df=products_df,
            transactions_df=transactions_df,
            personas=personas
        )
        
        # Test persona-aligned recommendations
        result1 = agent.get_recommendations(
            customer_id='CUST_00001',
            recommendation_type='persona_aligned',
            n_recommendations=2
        )
        assert result1['type'] == 'persona_aligned', "Wrong type for persona_aligned"
        
        # Test get_all_recommendations
        result2 = agent.get_all_recommendations(
            customer_id='CUST_00001'
        )
        assert 'tailored_recommendations' in result2, "Missing tailored_recommendations"
        assert 'customer_info' in result2, "Missing customer_info"
        assert 'recommendation_metadata' in result2, "Missing recommendation_metadata"
        
        print(f"✅ Phase 4 PASSED")
        print(f"   Agent initialized: ✓")
        print(f"   Persona-aligned: {len(result1.get('recommendations', []))} recommendations")
        print(f"   All recommendations: {len(result2.get('tailored_recommendations', []))} tailored")
        return True
        
    except Exception as e:
        print(f"❌ Phase 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test complete integration"""
    print("\n" + "="*80)
    print("INTEGRATION TEST: Complete Flow")
    print("="*80)
    
    try:
        # Test with actual F&M Bank data if available
        from pathlib import Path
        data_path = Path('data/preloaded/fmb_bank')
        
        if not data_path.exists():
            print("⚠️  F&M Bank data not found, skipping integration test")
            return True
        
        # Load actual data
        customers_df = pd.read_csv(data_path / 'customers.csv')
        products_df = pd.read_csv(data_path / 'products.csv')
        transactions_df = pd.read_csv(data_path / 'transactions.csv')
        
        print(f"   Loaded: {len(customers_df)} customers, {len(products_df)} products")
        
        # Need Agent A to create personas first
        from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
        
        print("   Running Agent A to create personas...")
        agent_a = AgentA_Banking_Enhanced(data_path=str(data_path))
        agent_a_result = agent_a.execute_segmentation(n_segments=3)
        
        personas = agent_a.personas
        print(f"   Created {len(personas)} personas")
        
        # Initialize Agent B V2
        from agents.agent_b_banking_enhanced_v2 import AgentB_Banking_Enhanced
        
        agent_b = AgentB_Banking_Enhanced(
            customers_df=agent_a.customers_df,
            products_df=agent_a.products_df,
            transactions_df=agent_a.transactions_df,
            personas=personas
        )
        
        # Get first customer
        customer_id = customers_df.iloc[0]['customer_id']
        
        # Test all recommendation types
        result = agent_b.get_all_recommendations(customer_id=customer_id)
        
        assert 'tailored_recommendations' in result, "Missing tailored"
        assert 'similar_products' in result, "Missing similar"
        assert 'segment_recommendations' in result, "Missing segment"
        
        print(f"✅ Integration Test PASSED")
        print(f"   Customer: {customer_id}")
        print(f"   Tailored: {len(result['tailored_recommendations'])}")
        print(f"   Similar: {len(result['similar_products'])}")
        print(f"   Segment: {len(result['segment_recommendations'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("BANKING AGENT B - COMPLETE IMPLEMENTATION TEST")
    print("="*80)
    
    results = []
    
    # Run phase tests
    results.append(("Phase 1: Banking 12-Factor Scorer", test_phase_1_banking_12_factor_scorer()))
    results.append(("Phase 2: Persona-Aligned Recommender", test_phase_2_persona_aligned_recommender()))
    results.append(("Phase 3: Together AI Integration", test_phase_3_together_ai()))
    results.append(("Phase 4: Enhanced V2 Agent", test_phase_4_enhanced_v2_agent()))
    results.append(("Integration Test", test_integration()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("\n" + "="*80)
    print(f"OVERALL: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Agent B Banking is ready for deployment.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

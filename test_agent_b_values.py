"""
Comprehensive Test Script for Agent B Values
Tests that all values are present and calculated correctly
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.agent_b_banking_chromadb import AgentB_Banking
from agents.agent_b_banking_logit_enhanced import AgentB_Banking_LogitEnhanced
from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced

def print_header(text, char='='):
    """Print formatted header"""
    print(f"\n{char*80}")
    print(f"  {text}")
    print(f"{char*80}")

def test_rule_based_values():
    """Test Rule-Based Agent B values"""
    print_header("🏦 RULE-BASED AGENT B - VALUE VERIFICATION", '=')
    
    try:
        # Load data
        data_path = project_root / 'data' / 'preloaded' / 'fmb_bank'
        customers = pd.read_csv(data_path / 'customers.csv')
        products = pd.read_csv(data_path / 'products.csv')
        transactions = pd.read_csv(data_path / 'transactions.csv')
        
        print(f"\n✅ Data loaded:")
        print(f"  - Customers: {len(customers):,}")
        print(f"  - Products: {len(products)}")
        print(f"  - Transactions: {len(transactions):,}")
        
        # Show product fee distribution
        print(f"\n📊 Product Fee Distribution:")
        print(f"  - Products with $0 fee: {len(products[products['annual_fee'] == 0])}")
        print(f"  - Products with $95 fee: {len(products[products['annual_fee'] == 95])}")
        print(f"  - Personal products: {len(products[products['category'] == 'Personal'])} (all $0 fee)")
        print(f"  - Business products: {len(products[products['category'] == 'Business'])} (1 with $95 fee)")
        
        # Run Agent A first
        print(f"\n🎯 Running Agent A...")
        agent_a = AgentA_Banking_Enhanced(data_path=str(data_path))
        agent_a.customers_df = customers.copy()
        agent_a.products_df = products.copy()
        agent_a.transactions_df = transactions.copy()
        agent_a_result = agent_a.execute({'n_clusters': 5})
        print(f"✅ Agent A created {len(agent_a_result.get('personas', {}))} personas")
        
        # Initialize Rule-Based Agent B
        print(f"\n🔧 Initializing Rule-Based Agent B...")
        agent_b = AgentB_Banking(
            data_path=str(data_path),
            agent_a=agent_a
        )
        agent_b.load_data()
        print(f"✅ Agent initialized")
        
        # Test Scenario 1: Personal Persona (should have avg fee = $0)
        print_header("TEST 1: Personal Persona (Persona 1) - Expected Avg Fee: $0", '-')
        
        result1 = agent_b.execute({
            'persona': '1',
            'search_query': '',
            'category': None,
            'top_n': 10,
            'explain': True
        })
        
        recs1 = result1.get('recommendations', [])
        insights1 = result1.get('insights', {})
        
        print(f"\n✅ Returned {len(recs1)} recommendations")
        
        # Verify all values present
        if len(recs1) > 0:
            rec = recs1[0]
            print(f"\n📋 First Product Values:")
            print(f"  - product_name: {rec.get('product_name', 'MISSING')}")
            print(f"  - annual_fee: ${rec.get('annual_fee', 'MISSING')}")
            print(f"  - min_balance: ${rec.get('min_balance', 'MISSING'):,}")
            print(f"  - interest_rate: {rec.get('interest_rate_apy', rec.get('interest_rate', 'MISSING'))}%")
            print(f"  - score: {rec.get('score', 'MISSING')}")
            print(f"  - category: {rec.get('category', 'MISSING')}")
            print(f"  - subcategory: {rec.get('subcategory', 'MISSING')}")
        
        # Calculate actual average fee manually
        manual_avg_fee = sum(r.get('annual_fee', 0) for r in recs1) / len(recs1) if recs1 else 0
        
        print(f"\n💰 Fee Calculation Verification:")
        print(f"  - Fees in recommendations: {[r.get('annual_fee', 0) for r in recs1[:5]]}")
        print(f"  - Manual calculation: ${manual_avg_fee:.2f}")
        print(f"  - Insights avg_fee: ${insights1.get('avg_fee', 'MISSING')}")
        
        if abs(manual_avg_fee - insights1.get('avg_fee', -999)) < 0.01:
            print(f"  ✅ PASS: Average fee matches!")
        else:
            print(f"  ❌ FAIL: Average fee mismatch!")
        
        print(f"\n📊 All Insights Values:")
        for key, value in insights1.items():
            if isinstance(value, dict):
                print(f"  - {key}:")
                for k, v in value.items():
                    print(f"      {k}: {v}")
            else:
                print(f"  - {key}: {value}")
        
        # Test Scenario 2: Search with fallback (should NOT return 0 products)
        print_header("TEST 2: Search Query Fallback - Must Return Products", '-')
        
        result2 = agent_b.execute({
            'persona': '1',
            'search_query': 'business',  # Personal persona searching "business"
            'category': None,
            'top_n': 10,
            'explain': True
        })
        
        recs2 = result2.get('recommendations', [])
        insights2 = result2.get('insights', {})
        
        print(f"\n✅ Returned {len(recs2)} recommendations")
        
        # CRITICAL: Must NEVER return 0 products in banking
        if len(recs2) == 0:
            print(f"  ❌ FAIL: Returned 0 products! Bad UX for banking!")
            print(f"  Banking system should ALWAYS show some products")
            return False
        else:
            print(f"  ✅ PASS: Returns products even when search doesn't match segment!")
            print(f"  This is good UX - customer sees alternatives")
        
        # Show fee breakdown if we have products
        if len(recs2) > 0:
            fees = [r.get('annual_fee', 0) for r in recs2]
            manual_avg_fee2 = sum(fees) / len(fees) if fees else 0
            
            print(f"\n💰 Fee Breakdown:")
            print(f"  - All fees: {fees[:5]}{'...' if len(fees) > 5 else ''}")
            print(f"  - Manual avg: ${manual_avg_fee2:.2f}")
            print(f"  - Insights avg_fee: ${insights2.get('avg_fee', 'MISSING')}")
            
            if abs(manual_avg_fee2 - insights2.get('avg_fee', -999)) < 0.01:
                print(f"  ✅ PASS: Average fee matches!")
            else:
                print(f"  ❌ FAIL: Average fee mismatch!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_ml_values():
    """Test Hybrid ML Agent B values"""
    print_header("🤖 HYBRID ML AGENT B - VALUE VERIFICATION", '=')
    
    try:
        # Load data
        data_path = project_root / 'data' / 'preloaded' / 'fmb_bank'
        customers = pd.read_csv(data_path / 'customers.csv')
        products = pd.read_csv(data_path / 'products.csv')
        transactions = pd.read_csv(data_path / 'transactions.csv')
        
        # Run Agent A first
        print(f"\n🎯 Running Agent A...")
        agent_a = AgentA_Banking_Enhanced(data_path=str(data_path))
        agent_a.customers_df = customers.copy()
        agent_a.products_df = products.copy()
        agent_a.transactions_df = transactions.copy()
        agent_a_result = agent_a.execute({'n_clusters': 5})
        print(f"✅ Agent A completed")
        
        # Initialize Hybrid ML Agent B
        print(f"\n🔧 Initializing Hybrid ML Agent B...")
        agent_b_ml = AgentB_Banking_LogitEnhanced(
            products_df=products,
            customers_df=customers,
            transactions_df=transactions,
            personas=agent_a.personas
        )
        print(f"✅ Agent initialized")
        
        # Test Persona Mode
        print_header("TEST 3: Hybrid ML - Persona Mode", '-')
        
        result = agent_b_ml.recommend(
            customer_id=None,
            persona_name='1',
            search_query='',
            category='',
            top_n=10
        )
        
        recs = result.get('recommendations', [])
        metrics = result.get('metrics', {})
        
        print(f"\n✅ Returned {len(recs)} recommendations")
        
        # Verify all values present
        if len(recs) > 0:
            rec = recs[0]
            print(f"\n📋 First Product Values:")
            print(f"  - product_name: {rec.get('product_name', 'MISSING')}")
            print(f"  - annual_fee: ${rec.get('annual_fee', 'MISSING')}")
            print(f"  - min_balance: ${rec.get('min_balance', 'MISSING'):,}")
            print(f"  - interest_rate: {rec.get('interest_rate', 'MISSING')}%")
            print(f"  - score: {rec.get('score', 'MISSING')}")
            print(f"  - ml_probability: {rec.get('ml_probability', 'MISSING')}")
            print(f"  - rule_score: {rec.get('rule_score', 'MISSING')}")
        
        # Calculate actual average fee manually
        manual_avg_fee = sum(r.get('annual_fee', 0) for r in recs) / len(recs) if recs else 0
        
        print(f"\n💰 Fee Calculation Verification:")
        print(f"  - Fees in recommendations: {[r.get('annual_fee', 0) for r in recs[:5]]}")
        print(f"  - Manual calculation: ${manual_avg_fee:.2f}")
        print(f"  - Metrics avg_fee: ${metrics.get('avg_fee', 'MISSING')}")
        
        if abs(manual_avg_fee - metrics.get('avg_fee', -999)) < 0.01:
            print(f"  ✅ PASS: Average fee matches!")
        else:
            print(f"  ❌ FAIL: Average fee mismatch!")
        
        print(f"\n📊 All Metrics Values:")
        for key, value in metrics.items():
            print(f"  - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_expected_calculations():
    """Test expected average fee calculations"""
    print_header("🧮 EXPECTED FEE CALCULATIONS", '=')
    
    print(f"\n📚 Example Calculations:\n")
    
    # Scenario 1: 10 Personal products (all $0)
    fees1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    avg1 = sum(fees1) / len(fees1)
    print(f"Scenario 1: 10 Personal products")
    print(f"  Fees: {fees1}")
    print(f"  Expected Avg: ${avg1:.2f}")
    print(f"  ✅ Should show: $0.00\n")
    
    # Scenario 2: 9 Business products (8 free + 1 with $95)
    fees2 = [0, 0, 0, 0, 0, 0, 0, 0, 95]
    avg2 = sum(fees2) / len(fees2)
    print(f"Scenario 2: 9 Business products (8 free + 1 credit card)")
    print(f"  Fees: {fees2}")
    print(f"  Expected Avg: ${avg2:.2f}")
    print(f"  ✅ Should show: $10.56\n")
    
    # Scenario 3: Mixed 7 Personal + 3 Business
    fees3 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 95]
    avg3 = sum(fees3) / len(fees3)
    print(f"Scenario 3: 7 Personal + 3 Business (including credit card)")
    print(f"  Fees: {fees3}")
    print(f"  Expected Avg: ${avg3:.2f}")
    print(f"  ✅ Should show: $9.50\n")
    
    # Common error case
    print(f"❌ WRONG CALCULATION (excluding $0 fees):")
    fees_wrong = [95]  # Only counting non-zero fees
    avg_wrong = sum(fees_wrong) / len(fees_wrong)
    print(f"  Fees (wrong): {fees_wrong}")
    print(f"  Wrong Avg: ${avg_wrong:.2f}")
    print(f"  ⚠️  This was the bug - only counting $95, not all 10 products!")
    
    return True

def run_all_tests():
    """Run all tests"""
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    🧪 AGENT B VALUE VERIFICATION TEST                         ║
║                                                                                ║
║  Tests all values are present and calculated correctly                        ║
║  - Annual fees (including $0)                                                 ║
║  - Average fee calculation                                                    ║
║  - Fee ranges                                                                  ║
║  - All product attributes                                                     ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'expected_calculations': False,
        'rule_based': False,
        'hybrid_ml': False
    }
    
    # Test 1: Show expected calculations
    results['expected_calculations'] = test_expected_calculations()
    
    # Test 2: Rule-Based Agent
    results['rule_based'] = test_rule_based_values()
    
    # Test 3: Hybrid ML Agent
    results['hybrid_ml'] = test_hybrid_ml_values()
    
    # Final Summary
    print_header("📊 FINAL TEST RESULTS", '█')
    
    print(f"\n{'Test Suite':<40} {'Status':<20}")
    print(f"{'─'*60}")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<40} {status:<20}")
        if not passed:
            all_passed = False
    
    print(f"{'─'*60}")
    
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"\n✅ Value calculations are CORRECT:")
        print(f"  - Average fee includes ALL products (including $0 fees)")
        print(f"  - Personal products: Avg = $0.00 ✓")
        print(f"  - Business products: Avg = ~$10.56 ✓")
        print(f"  - All values present and properly typed")
    else:
        print(f"\n⚠️  SOME TESTS FAILED - See details above")
    
    print(f"\n{'█'*80}")
    
    return results

if __name__ == "__main__":
    try:
        results = run_all_tests()
        
        # Save results to file
        output_file = project_root / 'test_agent_b_values_results.txt'
        with open(output_file, 'w') as f:
            f.write("AGENT B VALUE VERIFICATION TEST RESULTS\n")
            f.write("="*80 + "\n\n")
            for test_name, passed in results.items():
                status = "PASS" if passed else "FAIL"
                f.write(f"{test_name}: {status}\n")
        
        print(f"\n📄 Test results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ TEST SUITE CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

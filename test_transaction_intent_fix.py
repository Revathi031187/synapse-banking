"""
Test script to validate Transaction and Intent Score fixes
"""
import sys
import pandas as pd
from pathlib import Path

print("=" * 80)
print("🧪 TRANSACTION & INTENT SCORE FIX VALIDATION")
print("=" * 80)

# Load data
data_path = Path('data/preloaded/fmb_bank')
customers = pd.read_csv(data_path / 'customers.csv')
transactions = pd.read_csv(data_path / 'transactions.csv')
products = pd.read_csv(data_path / 'products.csv')

print(f"\n📊 DATA LOADED:")
print(f"   Customers: {len(customers):,}")
print(f"   Transactions: {len(transactions):,}")
print(f"   Products: {len(products):,}")

# Test 1: Load Agent A
print(f"\n{'='*80}")
print("TEST 1: Loading Agent A with Enhanced Fix")
print("=" * 80)

try:
    from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
    agent = AgentA_Banking_Enhanced(
        data_path=data_path
    )
    # Load data into agent
    agent.customers_df = customers
    agent.transactions_df = transactions  
    agent.products_df = products
    
    # Create derived columns
    agent._create_derived_columns()
    
    print("✅ Agent A loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Agent A: {e}")
    sys.exit(1)

# Test 2: Run with gamma=0.5
print(f"\n{'='*80}")
print("TEST 2: Running Segmentation with gamma=0.5")
print("=" * 80)

try:
    result_05 = agent.execute({'gamma': 0.5, 'n_clusters': 5})
    
    if 'error' in result_05:
        print(f"❌ Segmentation failed: {result_05['error']}")
        sys.exit(1)
    
    personas_05 = result_05['personas']
    print(f"✅ Created {len(personas_05)} personas")
    
    print(f"\n{'Segment Name':<35} {'Customers':<12} {'Total Txns':<15} {'Avg/Cust':<12} {'Intent':<10}")
    print("-" * 90)
    
    total_customers = 0
    total_txns = 0
    
    for pid, persona in personas_05.items():
        name = persona['persona_name'][:33]
        size = persona['size']
        txns = persona.get('total_transactions', 0)
        avg_txns = persona.get('avg_transactions', 0)
        intent = persona.get('avg_intent_score', 0)
        
        total_customers += size
        total_txns += txns
        
        print(f"{name:<35} {size:<12,} {txns:<15,} {avg_txns:<12.1f} {intent:<10.1%}")
    
    print("-" * 90)
    print(f"{'TOTAL':<35} {total_customers:<12,} {total_txns:<15,} {total_txns/total_customers:<12.1f} {'-':<10}")
    print(f"\n📊 Validation:")
    print(f"   Expected customers: 5,000")
    print(f"   Actual customers:   {total_customers:,} {'✅' if total_customers == 5000 else '❌'}")
    print(f"   Expected transactions: 78,568")
    print(f"   Actual transactions:   {total_txns:,} {'✅' if abs(total_txns - 78568) < 100 else '❌'}")
    
    intent_scores = [p['avg_intent_score'] for p in personas_05.values()]
    intent_range = max(intent_scores) - min(intent_scores)
    print(f"   Intent score range: {min(intent_scores):.1%} - {max(intent_scores):.1%} (range: {intent_range:.1%})")
    
except Exception as e:
    print(f"❌ Segmentation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Run with gamma=0.75
print(f"\n{'='*80}")
print("TEST 3: Running Segmentation with gamma=0.75")
print("=" * 80)

try:
    result_075 = agent.execute({'gamma': 0.75, 'n_clusters': 5})
    
    if 'error' in result_075:
        print(f"❌ Segmentation failed: {result_075['error']}")
        sys.exit(1)
    
    personas_075 = result_075['personas']
    print(f"✅ Created {len(personas_075)} personas")
    
    print(f"\n{'Segment Name':<35} {'Customers':<12} {'Total Txns':<15} {'Avg/Cust':<12} {'Intent':<10}")
    print("-" * 90)
    
    total_customers = 0
    total_txns = 0
    
    for pid, persona in personas_075.items():
        name = persona['persona_name'][:33]
        size = persona['size']
        txns = persona.get('total_transactions', 0)
        avg_txns = persona.get('avg_transactions', 0)
        intent = persona.get('avg_intent_score', 0)
        
        total_customers += size
        total_txns += txns
        
        print(f"{name:<35} {size:<12,} {txns:<15,} {avg_txns:<12.1f} {intent:<10.1%}")
    
    print("-" * 90)
    print(f"{'TOTAL':<35} {total_customers:<12,} {total_txns:<15,} {total_txns/total_customers:<12.1f} {'-':<10}")
    
    intent_scores = [p['avg_intent_score'] for p in personas_075.values()]
    intent_range = max(intent_scores) - min(intent_scores)
    print(f"\n📊 Intent score range: {min(intent_scores):.1%} - {max(intent_scores):.1%} (range: {intent_range:.1%})")
    
except Exception as e:
    print(f"❌ Segmentation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Compare gamma effects
print(f"\n{'='*80}")
print("TEST 4: Gamma Effect on Intent Scores")
print("=" * 80)

print(f"\n{'Segment Name':<35} {'γ=0.5':<12} {'γ=0.75':<12} {'Δ Change':<12} {'Dynamic?':<10}")
print("-" * 85)

all_dynamic = True
for pid in personas_05.keys():
    if pid in personas_075:
        name = personas_05[pid]['persona_name'][:33]
        intent_05 = personas_05[pid]['avg_intent_score']
        intent_075 = personas_075[pid]['avg_intent_score']
        delta = abs(intent_075 - intent_05)
        is_dynamic = "✅" if delta > 0.01 else "❌"
        
        if delta <= 0.01:
            all_dynamic = False
        
        print(f"{name:<35} {intent_05:<12.1%} {intent_075:<12.1%} {delta:<12.1%} {is_dynamic:<10}")

print("-" * 85)
print(f"\n🎯 Result: {'✅ ALL SEGMENTS ARE DYNAMIC!' if all_dynamic else '❌ Some segments are static'}")

# Final Summary
print(f"\n{'='*80}")
print("FINAL SUMMARY")
print("=" * 80)

print(f"\n✅ FIX VALIDATION RESULTS:")
print(f"   1. Transaction totals match data: {'✅ YES' if abs(total_txns - 78568) < 100 else '❌ NO'}")
print(f"   2. Intent scores are dynamic: {'✅ YES' if all_dynamic else '❌ NO'}")
print(f"   3. Wide intent score range: {'✅ YES' if intent_range > 0.20 else '❌ NO'}")
print(f"   4. All customers accounted for: {'✅ YES' if total_customers == 5000 else '❌ NO'}")

if abs(total_txns - 78568) < 100 and all_dynamic and intent_range > 0.20 and total_customers == 5000:
    print(f"\n🎉 ALL TESTS PASSED! System is now DYNAMIC and ROBUST!")
else:
    print(f"\n⚠️  Some tests failed. Review results above.")

print("=" * 80)

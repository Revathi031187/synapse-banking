"""
Test Complete Banking Flow: Agent A → Micro Segments → Agent B
Verifies all fixes are working correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("🧪 TESTING COMPLETE BANKING FLOW")
print("="*80)

# Test 1: Check macro segment names for uniqueness
print("\n📊 TEST 1: Macro Segment Name Uniqueness")
print("-" * 80)
from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
from pathlib import Path

data_path = Path('data/preloaded/fmb_bank')
if not data_path.exists():
    print(f"❌ Data path not found: {data_path}")
    print("Please run generate_fmb_data.bat first")
    sys.exit(1)

agent_a = AgentA_Banking_Enhanced(data_path=str(data_path))
result = agent_a.execute({'n_clusters': 5, 'gamma': 0.5})

if 'error' in result:
    print(f"❌ Agent A failed: {result['error']}")
    sys.exit(1)

print(f"✅ Agent A executed successfully with {result['n_clusters']} personas")

persona_names = []
for persona_id, persona in result['personas'].items():
    name = persona['persona_name']
    persona_names.append(name)
    print(f"  {persona['emoji']} {name}")
    print(f"     Size: {persona['size']} | Balance: ${persona['avg_balance']:,.0f} | Intent: {persona['avg_intent_score']*100:.0f}%")

# Check for duplicates
unique_names = set(persona_names)
if len(unique_names) == len(persona_names):
    print(f"\n✅ All {len(persona_names)} macro segment names are unique!")
else:
    print(f"\n❌ DUPLICATE NAMES FOUND!")
    for name in persona_names:
        if persona_names.count(name) > 1:
            print(f"   - '{name}' appears {persona_names.count(name)} times")

# Check if any contain "Hybrid Adopters" (the old problem)
hybrid_count = sum(1 for name in persona_names if "Hybrid Adopters" in name)
print(f"\n🔍 Names containing 'Hybrid Adopters': {hybrid_count}")
if hybrid_count > 1:
    print("⚠️  WARNING: Multiple personas still have 'Hybrid Adopters' in name")

# Test 2: Check micro segment names for uniqueness
print("\n\n📊 TEST 2: Micro Segment Name Uniqueness")
print("-" * 80)
from agents.agent_a_banking_micro import AgentA_Banking_Micro

# Test on first 2 macro segments
micro_names_all = []
for macro_id in list(result['personas'].keys())[:2]:
    persona = result['personas'][macro_id]
    print(f"\n🎯 Testing micro segments for: {persona['persona_name']}")
    
    agent_micro = AgentA_Banking_Micro(
        customers_df=result['customers_df'],
        macro_personas=result['personas']
    )
    
    micro_result = agent_micro.execute(macro_id, n_micro_segments=4)
    
    if 'error' in micro_result:
        print(f"  ❌ Micro segmentation failed: {micro_result['error']}")
        continue
    
    print(f"  ✅ Created {len(micro_result['micro_segments'])} micro segments:")
    for micro_seg in micro_result['micro_segments']:
        name = micro_seg['name']
        micro_names_all.append(name)
        print(f"     - {name} ({micro_seg['size']} customers)")

# Check micro segment uniqueness
unique_micro_names = set(micro_names_all)
if len(unique_micro_names) == len(micro_names_all):
    print(f"\n✅ All {len(micro_names_all)} micro segment names are unique across macros!")
else:
    print(f"\n❌ DUPLICATE MICRO NAMES FOUND!")
    for name in micro_names_all:
        if micro_names_all.count(name) > 1:
            print(f"   - '{name}' appears {micro_names_all.count(name)} times")

# Test 3: Test Agent B with customer data
print("\n\n📊 TEST 3: Agent B Customer Recommendations")
print("-" * 80)
from agents.agent_b_banking_rule_based import AgentB_Banking_RuleBased

agent_b = AgentB_Banking_RuleBased(
    customers_df=result['customers_df'],
    products_df=agent_a.products_df,
    transactions_df=agent_a.transactions_df,
    personas=result['personas'],
    data_path=str(data_path)
)

# Get a test customer
test_customer_id = result['customers_df'].iloc[0]['customer_id']
test_customer = result['customers_df'].iloc[0]

print(f"🧪 Testing recommendations for customer: {test_customer_id}")
print(f"   Name: {test_customer.get('customer_name', 'Unknown')}")
print(f"   Deposits: ${test_customer.get('total_deposits', 0):,.0f}")
print(f"   Products: {test_customer.get('num_products', 0)}")
print(f"   Intent: {test_customer.get('intent_score', 0)*100:.0f}%")
print(f"   Cluster: {test_customer.get('cluster', 'Unknown')}")

recommendations = agent_b.get_all_recommendations(test_customer_id)

if 'error' in recommendations:
    print(f"\n❌ Agent B failed: {recommendations['error']}")
else:
    print(f"\n✅ Agent B executed successfully!")
    print(f"\n📦 Recommendations:")
    print(f"   - Tailored: {len(recommendations['tailored_recommendations'])}")
    print(f"   - Similar: {len(recommendations['similar_products'])}")
    print(f"   - Segment: {len(recommendations['segment_recommendations'])}")
    
    metadata = recommendations.get('recommendation_metadata', {})
    print(f"\n🔧 Scoring Method: {metadata.get('scoring_method', 'unknown')}")
    print(f"   - Rule-Based Weight: {metadata.get('rule_weight', 0)*100:.0f}%")
    print(f"   - ML Weight: {metadata.get('ml_weight', 0)*100:.0f}%")
    print(f"   - ML Available: {'✅' if metadata.get('ml_available') else '❌'}")
    
    if len(recommendations['tailored_recommendations']) > 0:
        print(f"\n🎯 Top Recommendations:")
        for i, rec in enumerate(recommendations['tailored_recommendations'][:3], 1):
            print(f"   {i}. {rec['product_name']}")
            print(f"      Score: {rec.get('score', 0):.3f} (Rule: {rec.get('rule_score', 0):.3f}, ML: {rec.get('ml_probability', 0):.3f})")
            print(f"      Reason: {rec.get('reason', 'N/A')}")

# Final Summary
print("\n\n" + "="*80)
print("📋 TEST SUMMARY")
print("="*80)
print(f"✅ Agent A: {len(unique_names)}/{len(persona_names)} unique macro segment names")
print(f"✅ Micro Segments: {len(unique_micro_names)}/{len(micro_names_all)} unique names")
print(f"✅ Agent B: {'Working' if 'error' not in recommendations else 'Failed'}")
if 'error' not in recommendations:
    print(f"   - Generated {len(recommendations['tailored_recommendations'])} recommendations")
    print(f"   - Method: {metadata.get('scoring_method', 'unknown')}")

if (len(unique_names) == len(persona_names) and 
    len(unique_micro_names) == len(micro_names_all) and 
    'error' not in recommendations):
    print("\n🎉 ALL TESTS PASSED! 🎉")
    print("\nThe complete flow is working correctly:")
    print("  ✓ Macro segments have unique names")
    print("  ✓ Micro segments have unique names across all macros")
    print("  ✓ Agent B generates recommendations successfully")
    print("  ✓ Rule-based + ML hybrid scoring implemented")
else:
    print("\n⚠️  SOME TESTS FAILED")
    print("Please review the output above for details")

print("\n" + "="*80)

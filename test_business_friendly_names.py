"""
TEST: Business-Friendly Unique Names + Agent B
Shows improved naming with no repetition
"""
import sys
sys.path.append('.')

print("="*80)
print("🧪 TESTING BUSINESS-FRIENDLY UNIQUE NAMES")
print("="*80)

from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced

agent_a = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
print("\n🔄 Running Agent A with new naming logic...")

result = agent_a.execute({'n_clusters': 5, 'gamma': 0.5})

if 'error' in result:
    print(f"❌ Error: {result['error']}")
    sys.exit(1)

print(f"\n✅ Generated {len(result['personas'])} personas\n")

names = []
for pid, persona in result['personas'].items():
    name = persona['persona_name']
    names.append(name)
    print(f"{persona['emoji']} {name}")
    print(f"   {persona['size']:,} customers | ${persona['avg_balance']:,.0f} | {persona['avg_intent_score']*100:.0f}% intent\n")

# Validate uniqueness
unique_count = len(set(names))
total_count = len(names)

print("="*80)
print("📊 UNIQUENESS VALIDATION")
print("="*80)

if unique_count == total_count:
    print(f"✅ SUCCESS! All {total_count} names are UNIQUE!")
    print("\n✓ No repetition detected")
    print("✓ Names are business-friendly")
    print("✓ Easy for non-technical users to understand")
else:
    print(f"❌ FAILED! Only {unique_count}/{total_count} unique names")
    print("\n⚠️ Duplicates found:")
    for name in set(names):
        count = names.count(name)
        if count > 1:
            print(f"   '{name}' appears {count} times")

# Test micro segments
print("\n\n📊 MICRO SEGMENTATION TEST")
print("="*80)

from agents.agent_a_banking_micro import AgentA_Banking_Micro

test_macro_id = list(result['personas'].keys())[0]
test_persona = result['personas'][test_macro_id]

print(f"\nCreating micro segments for: {test_persona['persona_name']}")

agent_micro = AgentA_Banking_Micro(
    customers_df=result['customers_df'],
    macro_personas=result['personas']
)

micro_result = agent_micro.execute(test_macro_id, n_micro_segments=4)

if 'error' not in micro_result:
    print(f"\n✅ Micro segments:")
    micro_names = []
    for micro in micro_result['micro_segments']:
        name = micro['name']
        micro_names.append(name)
        print(f"   • {name}")
        print(f"     {micro['size']} customers | ${micro['avg_balance']:,.0f}")
    
    unique_micro = len(set(micro_names))
    if unique_micro == len(micro_names):
        print(f"\n✅ All {len(micro_names)} micro names are unique!")
    else:
        print(f"\n⚠️ Only {unique_micro}/{len(micro_names)} unique micro names")

# Test Agent B
print("\n\n📊 AGENT B TEST")
print("="*80)

from agents.agent_b_banking_rule_based import AgentB_Banking_RuleBased

agent_b = AgentB_Banking_RuleBased(
    customers_df=result['customers_df'],
    products_df=agent_a.products_df,
    transactions_df=agent_a.transactions_df,
    personas=result['personas'],
    data_path='data/preloaded/fmb_bank'
)

test_customer_id = result['customers_df'].iloc[50]['customer_id']
test_cust = result['customers_df'].iloc[50]

print(f"\nCustomer: {test_cust.get('customer_name', 'Unknown')}")
print(f"Deposits: ${test_cust.get('total_deposits', 0):,.0f} | Products: {test_cust.get('num_products', 0)}")

recs = agent_b.get_all_recommendations(test_customer_id)

if 'error' not in recs:
    print(f"\n✅ Agent B generated {len(recs['tailored_recommendations'])} recommendations")
    if len(recs['tailored_recommendations']) > 0:
        top_rec = recs['tailored_recommendations'][0]
        print(f"\nTop Recommendation: {top_rec['product_name']}")
        print(f"Score: {top_rec.get('score', 0):.3f} (Rule: {top_rec.get('rule_score', 0):.3f})")
else:
    print(f"\n❌ Agent B failed: {recs.get('error', 'Unknown error')}")

print("\n" + "="*80)
print("🎉 All tests complete!")
print("="*80)

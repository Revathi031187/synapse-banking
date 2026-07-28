"""
Quick test to verify segment names are unique
"""
import pandas as pd
from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced

print("=" * 80)
print("Testing Segment Name Uniqueness")
print("=" * 80)

# Load agent
agent = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
agent.load_data('v1')
agent._create_derived_columns()

# Run segmentation
print("\nRunning segmentation with 5 clusters, gamma=0.5...")
result = agent.execute({'n_clusters': 5, 'gamma': 0.5})

if 'error' in result:
    print(f"ERROR: {result['error']}")
    exit(1)

# Check for duplicates
personas = result['personas']
names = [p['persona_name'] for p in personas.values()]

print(f"\n✅ Generated {len(names)} segments:")
for i, name in enumerate(names, 1):
    print(f"   {i}. {name}")

# Check for duplicates
unique_names = set(names)
if len(unique_names) == len(names):
    print(f"\n✅ SUCCESS: All {len(names)} segment names are UNIQUE!")
else:
    duplicates = [name for name in names if names.count(name) > 1]
    print(f"\n❌ FAILURE: Found duplicate names:")
    for dup in set(duplicates):
        print(f"   - '{dup}' appears {names.count(dup)} times")

# Show characteristics
print("\n" + "=" * 80)
print("Segment Characteristics (to verify uniqueness):")
print("=" * 80)

for pid, persona in personas.items():
    chars = persona['characteristics']
    print(f"\n{persona['persona_name']}:")
    print(f"   Deposits: ${chars['avg_deposits']:,.0f}")
    print(f"   Transactions: {persona['avg_transactions']:.1f}")
    print(f"   Digital: {chars['avg_digital_engagement']:.1%}")
    print(f"   Products: {chars['avg_products']:.1f}")
    print(f"   Intent: {persona['avg_intent_score']:.1%}")

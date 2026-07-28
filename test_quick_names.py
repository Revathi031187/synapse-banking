"""Quick test to verify segment names are unique"""
import sys
sys.path.append('.')

print("Testing segment naming...")

from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
from pathlib import Path

agent = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
print("\n✓ Agent A loaded")

print("\n🔄 Running Agent A (this may take 10-15 seconds)...")
result = agent.execute({'n_clusters': 5, 'gamma': 0.5})

if 'error' in result:
    print(f"❌ Error: {result['error']}")
    sys.exit(1)

print(f"\n✅ Generated {len(result['personas'])} personas\n")

names = []
for pid, persona in result['personas'].items():
    name = persona['persona_name']
    names.append(name)
    print(f"{persona['emoji']} {name}")
    print(f"   {persona['size']} customers | ${persona['avg_balance']:,.0f} | {persona['avg_intent_score']*100:.0f}% intent\n")

# Check uniqueness
unique = len(set(names))
total = len(names)

print("="*80)
if unique == total:
    print(f"✅ SUCCESS! All {total} segment names are UNIQUE!")
else:
    print(f"❌ FAILED! Only {unique}/{total} unique names")
    print("\nDuplicates:")
    for name in names:
        if names.count(name) > 1:
            print(f"  - '{name}' appears {names.count(name)} times")

# Check for old problem
hybrid_count = sum(1 for n in names if "Hybrid Adopters" in n)
if hybrid_count > 1:
    print(f"\n⚠️ WARNING: {hybrid_count} segments contain 'Hybrid Adopters'")
elif hybrid_count == 1:
    print(f"\n✓ Only 1 segment has 'Hybrid Adopters' (acceptable)")
else:
    print(f"\n✓ No segments have 'Hybrid Adopters'")

print("="*80)

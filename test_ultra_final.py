"""
Ultra-Final Test - Verify all fixes
"""
import sys
sys.path.append('.')

print("="*80)
print("ULTRA-FINAL TEST - All Fixes Verification")
print("="*80)

from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
import pandas as pd

# Load agent
agent = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
result = agent.execute({'n_clusters': 5, 'gamma': 0.5})

if 'error' in result:
    print(f"❌ Error: {result['error']}")
    sys.exit(1)

# TEST 1: Macro names unique
print("\n✅ MACRO SEGMENTS:")
macro_names = []
for pid, p in result['personas'].items():
    macro_names.append(p['persona_name'])
    print(f"   {p['emoji']} {p['persona_name']}")

unique_macro = len(set(macro_names))
print(f"\n   Unique: {unique_macro}/{len(macro_names)} {'✅' if unique_macro == len(macro_names) else '❌'}")

# TEST 2: Insights unique
print("\n✅ INSIGHTS UNIQUENESS CHECK:")
all_behaviors = []
all_marketing = []
duplicates_found = False

for pid, p in result['personas'].items():
    exp = p.get('segment_explanation', {})
    behaviors = exp.get('key_behaviors', [])
    marketing = exp.get('marketing_recommendations', [])
    
    for b in behaviors:
        if b in all_behaviors:
            print(f"   ❌ Duplicate behavior: {b[:60]}...")
            duplicates_found = True
        all_behaviors.append(b)
    
    for m in marketing:
        if m in all_marketing:
            print(f"   ❌ Duplicate marketing: {m[:60]}...")
            duplicates_found = True
        all_marketing.append(m)

if not duplicates_found:
    print(f"   ✅ All insights are UNIQUE!")
    print(f"      Behaviors: {len(set(all_behaviors))}/{len(all_behaviors)}")
    print(f"      Marketing: {len(set(all_marketing))}/{len(all_marketing)}")
else:
    print(f"   ⚠️  Found {len(all_behaviors) - len(set(all_behaviors))} duplicate behaviors")
    print(f"   ⚠️  Found {len(all_marketing) - len(set(all_marketing))} duplicate marketing")

# TEST 3: Show sample insights
print("\n✅ SAMPLE INSIGHTS (First Segment):")
first_persona = list(result['personas'].values())[0]
exp = first_persona.get('segment_explanation', {})
print(f"\n   Segment: {first_persona['persona_name']}")
print(f"\n   Key Behaviors:")
for b in exp.get('key_behaviors', [])[:2]:
    print(f"     - {b}")
print(f"\n   Marketing:")
for m in exp.get('marketing_recommendations', [])[:2]:
    print(f"     - {m}")

# TEST 4: Micro segments
print("\n\n✅ MICRO SEGMENTS TEST:")
from agents.agent_a_banking_micro import AgentA_Banking_Micro

test_macro_id = list(result['personas'].keys())[0]
agent_micro = AgentA_Banking_Micro(
    customers_df=result['customers_df'],
    macro_personas=result['personas']
)

micro_result = agent_micro.execute(test_macro_id, n_micro_segments=4)

if 'error' not in micro_result:
    print(f"\n   Micro segments:")
    for micro in micro_result['micro_segments']:
        name = micro['name']
        print(f"     • {name}")
        
        # Check format - should be "Description (Tier)" not "Tier Description"
        has_parentheses = '(' in name and ')' in name
        if has_parentheses:
            print(f"       ✅ Tier in parentheses (correct format)")
        else:
            print(f"       ⚠️  No parentheses - check format")

print("\n" + "="*80)
print("🎉 TEST COMPLETE!")
print("="*80)

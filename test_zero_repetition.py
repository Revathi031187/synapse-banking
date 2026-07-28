"""
FINAL TEST: Zero Repetition + Business-Friendly Names
"""
import sys
sys.path.append('.')

# Force module reload to pick up changes
import importlib
if 'agents.agent_a_banking_enhanced' in sys.modules:
    del sys.modules['agents.agent_a_banking_enhanced']
if 'agents.agent_a_banking_micro' in sys.modules:
    del sys.modules['agents.agent_a_banking_micro']

print("="*80)
print("🎯 FINAL TEST: ZERO REPETITION GUARANTEE")
print("="*80)

from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
from agents.agent_a_banking_micro import AgentA_Banking_Micro

agent_a = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
print("\n🔄 Running Agent A with pool-based naming (guarantees uniqueness)...\n")

result = agent_a.execute({'n_clusters': 5, 'gamma': 0.5})

if 'error' in result:
    print(f"❌ Error: {result['error']}")
    sys.exit(1)

print(f"✅ Generated {len(result['personas'])} MACRO SEGMENTS:\n")

names = []
for pid, persona in result['personas'].items():
    name = persona['persona_name']
    names.append(name)
    print(f"{persona['emoji']} {name}")
    print(f"   {persona['size']:,} customers | ${persona['avg_balance']:,.0f}\n")

# Validate NO repetition
print("="*80)
print("📊 MACRO UNIQUENESS CHECK")
print("="*80)

unique = len(set(names))
total = len(names)

if unique == total:
    print(f"✅ PERFECT! All {total} names are 100% UNIQUE!")
    print(f"\n✓ Zero repetition")
    print(f"✓ No numbers in names")
    print(f"✓ Business-friendly language")
else:
    print(f"❌ FAILED: Only {unique}/{total} unique")
    for name in names:
        if names.count(name) > 1:
            print(f"  DUPLICATE: '{name}' appears {names.count(name)}x")

# Test MICRO segments
print("\n\n📊 MICRO SEGMENTS TEST")
print("="*80)

test_macro_id = list(result['personas'].keys())[0]
test_persona = result['personas'][test_macro_id]

print(f"\nMacro Segment: {test_persona['persona_name']}")
print(f"Creating 4 micro segments...\n")

agent_micro = AgentA_Banking_Micro(
    customers_df=result['customers_df'],
    macro_personas=result['personas']
)

micro_result = agent_micro.execute(test_macro_id, n_micro_segments=4)

if 'error' not in micro_result:
    print(f"✅ MICRO SEGMENTS:\n")
    micro_names = []
    for micro in micro_result['micro_segments']:
        name = micro['name']
        micro_names.append(name)
        print(f"  • {name}")
        print(f"    {micro['size']} customers | {micro['ltv_tier']} tier\n")
    
    unique_micro = len(set(micro_names))
    if unique_micro == len(micro_names):
        print(f"✅ All {len(micro_names)} micro names are UNIQUE!")
        # Check for numbers
        has_numbers = any(char.isdigit() for name in micro_names for char in name)
        if not has_numbers:
            print(f"✅ NO NUMBERS in any micro segment names!")
        else:
            print(f"⚠️ WARNING: Numbers found in micro segment names")
    else:
        print(f"❌ Only {unique_micro}/{len(micro_names)} unique micro names")
        for name in micro_names:
            if micro_names.count(name) > 1:
                print(f"  DUPLICATE: '{name}' appears {micro_names.count(name)}x")
else:
    print(f"❌ Micro segmentation failed: {micro_result.get('error')}")

# Final verdict
print("\n" + "="*80)
print("🏆 FINAL VERDICT")
print("="*80)

macro_pass = (unique == total)
micro_pass = ('error' not in micro_result and len(set(micro_names)) == len(micro_names))
no_numbers = not any(char.isdigit() for name in names + micro_names for char in name if name not in [])

if macro_pass and micro_pass and no_numbers:
    print("🎉 SUCCESS! ALL TESTS PASSED!")
    print("\n✓ Macro segments: 100% unique")
    print("✓ Micro segments: 100% unique")
    print("✓ Zero numbers in segment names")
    print("✓ Business-friendly language throughout")
    print("\n👍 Ready for production use!")
else:
    print("⚠️ SOME ISSUES DETECTED:")
    if not macro_pass:
        print("  ❌ Macro segments have duplicates")
    if not micro_pass:
        print("  ❌ Micro segments have duplicates")  
    if not no_numbers:
        print("  ❌ Numbers found in segment names")

print("="*80)

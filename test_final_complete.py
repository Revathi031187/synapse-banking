"""
FINAL COMPREHENSIVE TEST
Tests all requirements:
1. CLV column in data
2. Unique macro segment names
3. Unique micro segment names (no parent prefix)
4. Completely unique insights per segment
5. Agent B working
"""
import sys
sys.path.append('.')

print("="*80)
print("FINAL COMPREHENSIVE TEST")
print("="*80)

# =================================================================
# TEST 1: Verify CLV Column Exists in Data
# =================================================================
print("\n[TEST 1] Checking CLV Column in Data")
print("-"*80)

import pandas as pd
from pathlib import Path

data_path = Path('data/preloaded/fmb_bank')
customers_df = pd.read_csv(data_path / 'customers.csv')

print(f"Loaded {len(customers_df)} customers")
print(f"Total columns: {len(customers_df.columns)}")

if 'customer_lifetime_value' in customers_df.columns:
    print("\n✅ CLV column EXISTS!")
    print(f"   CLV Range: ${customers_df['customer_lifetime_value'].min():,.0f} to ${customers_df['customer_lifetime_value'].max():,.0f}")
    print(f"   Average CLV: ${customers_df['customer_lifetime_value'].mean():,.0f}")
    
    if 'clv_tier' in customers_df.columns:
        print(f"\n   CLV Tier Distribution:")
        for tier in ['Diamond', 'Platinum', 'Gold', 'Silver', 'Bronze']:
            count = len(customers_df[customers_df['clv_tier'] == tier])
            if count > 0:
                print(f"     {tier}: {count:,} customers ({count/len(customers_df)*100:.1f}%)")
else:
    print("\n❌ CLV column MISSING!")
    print("   Running add_clv_to_data.py script...")
    import subprocess
    result = subprocess.run([sys.executable, 'add_clv_to_data.py'], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    # Reload data
    customers_df = pd.read_csv(data_path / 'customers.csv')

# =================================================================
# TEST 2: Macro Segment Names - Uniqueness
# =================================================================
print("\n\n[TEST 2] Macro Segment Names - Uniqueness Test")
print("-"*80)

from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced

agent_a = AgentA_Banking_Enhanced(data_path=str(data_path))
result = agent_a.execute({'n_clusters': 5, 'gamma': 0.5})

if 'error' in result:
    print(f"❌ Error: {result['error']}")
    sys.exit(1)

print(f"\nGenerated {len(result['personas'])} MACRO segments:\n")

macro_names = []
for pid, persona in result['personas'].items():
    name = persona['persona_name']
    macro_names.append(name)
    print(f"{persona['emoji']} {name}")
    print(f"   {persona['size']:,} customers | ${persona['avg_balance']:,.0f}")

# Check uniqueness
unique_macro = len(set(macro_names))
if unique_macro == len(macro_names):
    print(f"\n✅ All {len(macro_names)} macro names are UNIQUE!")
else:
    print(f"\n❌ FAILED! Only {unique_macro}/{len(macro_names)} unique")
    for name in set(macro_names):
        if macro_names.count(name) > 1:
            print(f"   DUPLICATE: '{name}' appears {macro_names.count(name)} times")

# =================================================================
# TEST 3: Micro Segment Names - No Parent Prefix
# =================================================================
print("\n\n[TEST 3] Micro Segment Names - No Parent Prefix Test")
print("-"*80)

from agents.agent_a_banking_micro import AgentA_Banking_Micro

test_macro_id = list(result['personas'].keys())[0]
agent_micro = AgentA_Banking_Micro(
    customers_df=result['customers_df'],
    macro_personas=result['personas']
)

micro_result = agent_micro.execute(test_macro_id, n_micro_segments=4)

if 'error' not in micro_result:
    print(f"\nMicro segments for: {result['personas'][test_macro_id]['persona_name']}\n")
    
    micro_names = []
    has_parent_prefix = []
    
    for micro in micro_result['micro_segments']:
        name = micro['name']
        micro_names.append(name)
        
        # Check if name contains parent keywords (bad!)
        parent_keywords = ['Mass.', 'Elite.', 'Esta.', 'Prem.', 'Grow.', '-']
        if any(kw in name for kw in parent_keywords):
            has_parent_prefix.append(name)
        
        print(f"   {name}")
        print(f"     {micro['size']} customers | {micro['ltv_tier']} tier | ${micro['avg_balance']:,.0f}")
    
    if len(has_parent_prefix) == 0:
        print(f"\n✅ No parent prefix in any micro names!")
    else:
        print(f"\n⚠️  Found {len(has_parent_prefix)} names with parent prefix:")
        for name in has_parent_prefix:
            print(f"     - {name}")
    
    # Check uniqueness
    unique_micro = len(set(micro_names))
    if unique_micro == len(micro_names):
        print(f"✅ All {len(micro_names)} micro names are unique!")
    else:
        print(f"❌ Only {unique_micro}/{len(micro_names)} unique micro names")

# =================================================================
# TEST 4: Insights Uniqueness Test
# =================================================================
print("\n\n[TEST 4] Insights Uniqueness Test")
print("-"*80)

all_behaviors = []
all_marketing = []

print("\nChecking if any segments have identical insights...")

for pid, persona in result['personas'].items():
    explanation = persona.get('segment_explanation', {})
    behaviors = explanation.get('key_behaviors', [])
    marketing = explanation.get('marketing_recommendations', [])
    
    for b in behaviors:
        if b in all_behaviors:
            print(f"⚠️  DUPLICATE BEHAVIOR: '{b[:50]}...'")
        all_behaviors.append(b)
    
    for m in marketing:
        if m in all_marketing:
            print(f"⚠️  DUPLICATE MARKETING: '{m[:50]}...'")
        all_marketing.append(m)

unique_behaviors = len(set(all_behaviors))
unique_marketing = len(set(all_marketing))

if unique_behaviors == len(all_behaviors) and unique_marketing == len(all_marketing):
    print(f"✅ All insights are UNIQUE!")
    print(f"   Behaviors: {unique_behaviors} unique out of {len(all_behaviors)}")
    print(f"   Marketing: {unique_marketing} unique out of {len(all_marketing)}")
else:
    print(f"⚠️  Some insights are duplicated:")
    print(f"   Behaviors: {unique_behaviors}/{len(all_behaviors)} unique")
    print(f"   Marketing: {unique_marketing}/{len(all_marketing)} unique")

# =================================================================
# TEST 5: Agent B Test
# =================================================================
print("\n\n[TEST 5] Agent B Recommendations Test")
print("-"*80)

from agents.agent_b_banking_rule_based import AgentB_Banking_RuleBased

agent_b = AgentB_Banking_RuleBased(
    customers_df=result['customers_df'],
    products_df=agent_a.products_df,
    transactions_df=agent_a.transactions_df,
    personas=result['personas'],
    data_path=str(data_path)
)

test_customer_id = result['customers_df'].iloc[50]['customer_id']
recs = agent_b.get_all_recommendations(test_customer_id)

if 'error' not in recs:
    print(f"✅ Agent B working!")
    print(f"   Generated {len(recs['tailored_recommendations'])} recommendations")
else:
    print(f"❌ Agent B failed: {recs.get('error')}")

# =================================================================
# FINAL SUMMARY
# =================================================================
print("\n\n" + "="*80)
print("FINAL TEST SUMMARY")
print("="*80)

test_results = {
    'CLV in data': 'customer_lifetime_value' in customers_df.columns,
    'Macro names unique': unique_macro == len(macro_names),
    'Micro names no prefix': len(has_parent_prefix) == 0 if 'has_parent_prefix' in locals() else False,
    'Insights unique': unique_behaviors == len(all_behaviors) and unique_marketing == len(all_marketing),
    'Agent B working': 'error' not in recs
}

all_passed = all(test_results.values())

for test_name, passed in test_results.items():
    status = "✅" if passed else "❌"
    print(f"{status} {test_name}")

if all_passed:
    print("\n🎉 ALL TESTS PASSED!")
    print("\nSystem is ready for deployment:")
    print("  ✓ CLV metric added")
    print("  ✓ Unique segment names")
    print("  ✓ Unique insights per segment")
    print("  ✓ Agent B recommendations working")
else:
    print("\n⚠️  SOME TESTS FAILED - Review output above")

print("="*80)

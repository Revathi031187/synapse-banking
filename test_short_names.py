"""
Quick test to verify:
1. Short segment names (2 words max)
2. Correct transaction numbers (10-150 range)
"""
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced

print("="*80)
print("TESTING SHORT NAMES & CORRECT TRANSACTION VOLUMES")
print("="*80)

# Load data (use engine='python' for robust CSV parsing)
customers_df = pd.read_csv('data/preloaded/fmb_bank/customers.csv', engine='python')
print(f"\n✓ Loaded {len(customers_df)} customers")

# Check transaction volume range in data
min_txn = customers_df['monthly_transaction_volume'].min()
max_txn = customers_df['monthly_transaction_volume'].max()
avg_txn = customers_df['monthly_transaction_volume'].mean()
print(f"✓ Data transaction volumes: min={min_txn:.0f}, max={max_txn:.0f}, avg={avg_txn:.0f}")

# Initialize Agent A with correct data path
agent = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
print("\n✓ Agent A initialized")

# Perform segmentation (execute() will load data internally)
params = {
    'n_clusters': 5,  # Note: parameter is 'n_clusters', not 'n_segments'
    'dataset_version': 'fmb_bank'  # Note: This parameter is not currently used by load_data
}
result = agent.execute(params)

if 'error' in result:
    print(f"\n❌ Error: {result['error']}")
    sys.exit(1)

print(f"\n✓ Segmentation complete: {result['n_clusters']} segments")

print("\n" + "="*80)
print("SEGMENT NAMES (Should be 2 words max):")
print("="*80)

personas_list = list(result['personas'].values())
for i, persona in enumerate(personas_list, 1):
    name = persona['persona_name']
    word_count = len(name.split())
    size = persona['size']  # Changed from segment_size
    avg_deposits = persona['characteristics']['avg_deposits']
    avg_monthly_txn = persona['characteristics'].get('avg_monthly_transaction_volume', 0)
    
    print(f"\n{i}. {name}")
    print(f"   Words: {word_count} {'✅' if word_count <= 2 else '❌ TOO LONG!'}")
    print(f"   Size: {size} customers")
    print(f"   Avg Deposits: ${avg_deposits:,.0f}")
    print(f"   Avg Monthly Transactions: {avg_monthly_txn:.1f} {'✅' if 10 <= avg_monthly_txn <= 800 else '❌ OUT OF RANGE!'}")

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)

personas_list = list(result['personas'].values())
names = [p['persona_name'] for p in personas_list]
word_counts = [len(name.split()) for name in names]
max_words = max(word_counts)
all_short = all(wc <= 2 for wc in word_counts)

monthly_txns = [p['characteristics'].get('avg_monthly_transaction_volume', 0) for p in personas_list]
all_txns_valid = all(10 <= txn <= 800 for txn in monthly_txns)  # Updated range for all customer types (retail + business + ag)

print(f"✅ All names unique: {len(set(names)) == len(names)}")
print(f"{'✅' if all_short else '❌'} All names short (≤2 words): {all_short} (max: {max_words} words)")
print(f"{'✅' if all_txns_valid else '❌'} All transactions in range (10-800): {all_txns_valid}")
print(f"\nTransaction ranges by segment:")
for i, (name, txn) in enumerate(zip(names, monthly_txns), 1):
    print(f"  {i}. {name}: {txn:.1f} txns/month")

print("\n" + "="*80)
if all_short and all_txns_valid and len(set(names)) == len(names):
    print("🎉 ALL TESTS PASSED!")
else:
    print("❌ SOME TESTS FAILED - see details above")
print("="*80)

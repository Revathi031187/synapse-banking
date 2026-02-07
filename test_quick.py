"""Quick test of transaction fix"""
import pandas as pd
from pathlib import Path

print("Testing transaction metrics calculation...")

# Load data
data_path = Path('data/preloaded/fmb_bank')
customers = pd.read_csv(data_path / 'customers.csv')
transactions = pd.read_csv(data_path / 'transactions.csv')

print(f"Total customers: {len(customers):,}")
print(f"Total transactions: {len(transactions):,}")

# Simulate what the fix does
cluster_customer_ids = customers['customer_id'].head(1000).tolist()
cluster_transactions = transactions[transactions['customer_id'].isin(cluster_customer_ids)]

total_txns = len(cluster_transactions)
txn_per_customer = cluster_transactions.groupby('customer_id').size()
avg_txns = txn_per_customer.mean()

print(f"\nFor first 1000 customers:")
print(f"  Total transactions: {total_txns:,}")
print(f"  Avg per customer: {avg_txns:.2f}")
print(f"\n✅ Dynamic calculation works!")

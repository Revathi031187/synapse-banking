import pandas as pd

print("=" * 80)
print("TRANSACTION DATA VERIFICATION")
print("=" * 80)

# Load data
customers = pd.read_csv('data/preloaded/fmb_bank/customers.csv')
transactions = pd.read_csv('data/preloaded/fmb_bank/transactions.csv')

print(f"\n📊 DATA OVERVIEW:")
print(f"   Total Customers: {len(customers):,}")
print(f"   Total Transactions: {len(transactions):,}")

# Calculate transaction statistics
txn_per_customer = transactions.groupby('customer_id').size()
print(f"\n📈 TRANSACTION STATISTICS:")
print(f"   Average transactions per customer: {txn_per_customer.mean():.2f}")
print(f"   Median transactions per customer: {txn_per_customer.median():.2f}")
print(f"   Min transactions: {txn_per_customer.min()}")
print(f"   Max transactions: {txn_per_customer.max()}")

# Check monthly_transaction_volume in customers
if 'monthly_transaction_volume' in customers.columns:
    print(f"\n📋 CUSTOMER monthly_transaction_volume COLUMN:")
    print(f"   Average: {customers['monthly_transaction_volume'].mean():.2f}")
    print(f"   Median: {customers['monthly_transaction_volume'].median():.2f}")
    print(f"   Min: {customers['monthly_transaction_volume'].min()}")
    print(f"   Max: {customers['monthly_transaction_volume'].max()}")
else:
    print(f"\n⚠️  monthly_transaction_volume column NOT FOUND in customers.csv")

# Calculate total transaction amounts by customer
txn_amounts = transactions.groupby('customer_id')['amount'].sum()
print(f"\n💰 TRANSACTION AMOUNTS:")
print(f"   Total transaction volume: ${txn_amounts.sum():,.2f}")
print(f"   Average per customer: ${txn_amounts.mean():,.2f}")

# Verify transaction counts match data
actual_txn_counts = transactions.groupby('customer_id').size().to_dict()
sample_customers = customers.head(10)

print(f"\n🔍 SAMPLE VERIFICATION (First 10 customers):")
print(f"   {'Customer ID':<15} {'monthly_txn_vol':<18} {'Actual Txns':<15} {'Match?':<10}")
print(f"   {'-' * 60}")

for _, row in sample_customers.iterrows():
    cust_id = row['customer_id']
    expected = row['monthly_transaction_volume'] if 'monthly_transaction_volume' in row else 0
    actual = actual_txn_counts.get(cust_id, 0)
    match = "✓" if abs(actual - expected) < 5 else "✗"
    print(f"   {cust_id:<15} {expected:<18.0f} {actual:<15} {match:<10}")

print("\n" + "=" * 80)

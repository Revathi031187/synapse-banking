import csv

# Count transactions
with open('data/preloaded/fmb_bank/transactions.csv', 'r', encoding='utf-8') as f:
    tx_count = sum(1 for _ in f) - 1  # Subtract header

# Count customers
with open('data/preloaded/fmb_bank/customers.csv', 'r', encoding='utf-8') as f:
    cust_count = sum(1 for _ in f) - 1  # Subtract header

# Read customer data
with open('data/preloaded/fmb_bank/customers.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    mtv_values = [float(r['monthly_transaction_volume']) for r in rows]

print(f"QUICK DATA CHECK")
print(f"="*60)
print(f"Total transactions: {tx_count:,}")
print(f"Total customers: {cust_count:,}")
print(f"Avg txns per customer: {tx_count / cust_count:.1f}")
print(f"")
print(f"monthly_transaction_volume column:")
print(f"  Min: {min(mtv_values):.0f}")
print(f"  Max: {max(mtv_values):.0f}")
print(f"  Average: {sum(mtv_values)/len(mtv_values):.1f}")
print(f"  Total sum: {sum(mtv_values):,.0f}")
print(f"")
print(f"ANALYSIS:")
print(f"  If column is MONTHLY: {sum(mtv_values):,.0f} txns/month total")
print(f"  If column is TOTAL: {sum(mtv_values):,.0f} txns over lifetime")
print(f"  Actual transactions in file: {tx_count:,}")
print(f"")
print(f"MATCH:")
if abs(sum(mtv_values) - tx_count) < 1000:
    print(f"  ✓ Column represents TOTAL transactions (not monthly)")
    print(f"    Column sum ({sum(mtv_values):,.0f}) ≈ Actual txns ({tx_count:,})")
else:
    print(f"  ✗ Values don't match - needs investigation")
    print(f"    Column sum: {sum(mtv_values):,.0f}")
    print(f"    Actual txns: {tx_count:,}")
    print(f"    Difference: {abs(sum(mtv_values) - tx_count):,.0f}")

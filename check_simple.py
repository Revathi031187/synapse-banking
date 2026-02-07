import csv

with open('data/preloaded/fmb_bank/customers.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    customers = list(reader)

print(f"Total: {len(customers)}")

# Deposits
deposits = [float(c['total_deposits']) for c in customers]
under_100k = sum(1 for d in deposits if d < 100000)
mid = sum(1 for d in deposits if 100000 <= d < 1000000)
over_1m = sum(1 for d in deposits if d >= 1000000)

print(f"\nDeposits:")
print(f"  <100K: {under_100k} ({under_100k/len(customers)*100:.1f}%)")
print(f"  100K-1M: {mid} ({mid/len(customers)*100:.1f}%)")
print(f"  >1M: {over_1m} ({over_1m/len(customers)*100:.1f}%)")

# Check if 80%+ are in same range
if mid/len(customers) > 0.8:
    print(f"\nVERDICT: {mid/len(customers)*100:.1f}% in same deposit range!")
    print(f"This naturally creates 1-2 large 'mainstream' segments.")
    print(f"NORMAL for banking - most customers are similar.")

import pandas as pd
import sys

print("Loading data...", flush=True)
df = pd.read_csv('data/preloaded/fmb_bank/customers.csv')

print(f"\nTotal customers: {len(df):,}", flush=True)

# Check intent score
intent = df['cross_sell_receptivity']
print(f"\nIntent Score:", flush=True)
print(f"  Mean: {intent.mean():.2%}", flush=True)
print(f"  Min: {intent.min():.2%}", flush=True)
print(f"  Max: {intent.max():.2%}", flush=True)

# Check deposit ranges
print(f"\nDeposit Ranges:", flush=True)
print(f"  <$100K: {(df['total_deposits'] < 100000).sum():,} ({(df['total_deposits'] < 100000).sum()/len(df)*100:.1f}%)", flush=True)
print(f"  $100K-$1M: {((df['total_deposits'] >= 100000) & (df['total_deposits'] < 1000000)).sum():,} ({((df['total_deposits'] >= 100000) & (df['total_deposits'] < 1000000)).sum()/len(df)*100:.1f}%)", flush=True)
print(f"  >$1M: {(df['total_deposits'] >= 1000000).sum():,} ({(df['total_deposits'] >= 1000000).sum()/len(df)*100:.1f}%)", flush=True)

# Check homogeneity
from scipy import stats
deposits_z = stats.zscore(df['total_deposits'])
digital_z = stats.zscore(df['digital_engagement_score'])
products_z = stats.zscore(df['num_products'])

average_cust = ((abs(deposits_z) < 1) & (abs(digital_z) < 1) & (abs(products_z) < 1)).sum()
print(f"\nHomogeneity:", flush=True)
print(f"  Customers within 1 std dev: {average_cust:,} ({average_cust/len(df)*100:.1f}%)", flush=True)

if average_cust/len(df) > 0.6:
    print(f"\n✅ VERDICT: Data is homogeneous ({average_cust/len(df)*100:.1f}%)", flush=True)
    print(f"   This explains why 93% fall in 2 segments!", flush=True)
    print(f"   RECOMMENDATION: Use 3-4 clusters instead of 5", flush=True)
else:
    print(f"\n⚠️  VERDICT: Data has variation, check clustering params", flush=True)

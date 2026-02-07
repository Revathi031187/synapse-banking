import pandas as pd

df = pd.read_csv('data/preloaded/fmb_bank/customers.csv')

# Intent score check
intent = df['cross_sell_receptivity']
print(f"Intent Mean: {intent.mean():.2%}")
print(f"Intent Min-Max: {intent.min():.2%} to {intent.max():.2%}")

# Deposit distribution
deposits = df['total_deposits']
under_100k = (deposits < 100000).sum()
mid_range = ((deposits >= 100000) & (deposits < 1000000)).sum()
over_1m = (deposits >= 1000000).sum()

print(f"\nDeposit Distribution:")
print(f"  Under $100K: {under_100k} ({under_100k/len(df)*100:.1f}%)")
print(f"  $100K-$1M: {mid_range} ({mid_range/len(df)*100:.1f}%)")
print(f"  Over $1M: {over_1m} ({over_1m/len(df)*100:.1f}%)")

# Check homogeneity
from scipy.stats import zscore
z_deposits = zscore(df['total_deposits'])
z_digital = zscore(df['digital_engagement_score'])
z_products = zscore(df['num_products'])

average_customers = ((abs(z_deposits) < 1) & (abs(z_digital) < 1) & (abs(z_products) < 1)).sum()

print(f"\nHomogeneity Check:")
print(f"  Average customers (within 1 std dev): {average_customers} ({average_customers/len(df)*100:.1f}%)")

if average_customers/len(df) > 0.6:
    print(f"\n✅ CONFIRMED: Data is homogeneous!")
    print(f"   This explains why 93% fall in 2 segments.")
    print(f"   RECOMMENDATION: Try 3-4 clusters instead of 5")
else:
    print(f"\n⚠️  Data has variation but clustering may need tuning")

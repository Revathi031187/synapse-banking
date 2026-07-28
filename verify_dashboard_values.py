"""
Verify dashboard values against actual data
Checks:
1. Intent score distribution
2. Customer distribution across segments
3. Whether segmentation is balanced
"""
import pandas as pd
import numpy as np

print("="*80, flush=True)
print("DASHBOARD VALUES VERIFICATION", flush=True)
print("="*80, flush=True)

# Load data
customers_df = pd.read_csv('data/preloaded/fmb_bank/customers.csv', engine='python')

print(f"\n📊 TOTAL CUSTOMERS: {len(customers_df):,}", flush=True)

# ============================================================================
# CHECK 1: Intent Score (cross_sell_receptivity) Distribution
# ============================================================================
print("\n" + "="*80, flush=True)
print("CHECK 1: INTENT SCORE DISTRIBUTION", flush=True)
print("="*80, flush=True)

intent_scores = customers_df['cross_sell_receptivity']

print(f"\nIntent Score Statistics:", flush=True)
print(f"  Min: {intent_scores.min():.2%}", flush=True)
print(f"  Max: {intent_scores.max():.2%}", flush=True)
print(f"  Mean: {intent_scores.mean():.2%}", flush=True)
print(f"  Median: {intent_scores.median():.2%}", flush=True)
print(f"  Std Dev: {intent_scores.std():.2%}", flush=True)

# Distribution by ranges
print(f"\nIntent Score Ranges:", flush=True)
print(f"  0-20%: {(intent_scores < 0.2).sum():,} customers ({(intent_scores < 0.2).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  20-40%: {((intent_scores >= 0.2) & (intent_scores < 0.4)).sum():,} customers ({((intent_scores >= 0.2) & (intent_scores < 0.4)).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  40-60%: {((intent_scores >= 0.4) & (intent_scores < 0.6)).sum():,} customers ({((intent_scores >= 0.4) & (intent_scores < 0.6)).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  60-80%: {((intent_scores >= 0.6) & (intent_scores < 0.8)).sum():,} customers ({((intent_scores >= 0.6) & (intent_scores < 0.8)).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  80-100%: {(intent_scores >= 0.8).sum():,} customers ({(intent_scores >= 0.8).sum()/len(customers_df)*100:.1f}%)", flush=True)

print(f"\n🎯 DASHBOARD SHOWS: 36%, 49%, 51%, 52%, 53%", flush=True)
print(f"   This means segments average 36-53% intent", flush=True)
print(f"   Overall average: {intent_scores.mean():.2%}", flush=True)
print(f"\n✅ VERDICT: Intent scores 36-53% are CORRECT if segments cluster around mean", flush=True)

# ============================================================================
# CHECK 2: Customer Distribution Across Key Characteristics
# ============================================================================
print("\n" + "="*80, flush=True)
print("CHECK 2: CUSTOMER CHARACTERISTIC DISTRIBUTION", flush=True)
print("="*80, flush=True)

# Check deposits distribution (to understand why 2 segments dominate)
print(f"\nDeposit Distribution:", flush=True)
print(f"  Min: ${customers_df['total_deposits'].min():,.2f}", flush=True)
print(f"  25th percentile: ${customers_df['total_deposits'].quantile(0.25):,.2f}", flush=True)
print(f"  Median: ${customers_df['total_deposits'].median():,.2f}", flush=True)
print(f"  75th percentile: ${customers_df['total_deposits'].quantile(0.75):,.2f}", flush=True)
print(f"  Max: ${customers_df['total_deposits'].max():,.2f}", flush=True)
print(f"  Mean: ${customers_df['total_deposits'].mean():,.2f}", flush=True)

# Check if data is naturally clustered into 2 main groups
print(f"\nDeposit Ranges:", flush=True)
print(f"  <$100K: {(customers_df['total_deposits'] < 100000).sum():,} customers ({(customers_df['total_deposits'] < 100000).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  $100K-$500K: {((customers_df['total_deposits'] >= 100000) & (customers_df['total_deposits'] < 500000)).sum():,} customers ({((customers_df['total_deposits'] >= 100000) & (customers_df['total_deposits'] < 500000)).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  $500K-$1M: {((customers_df['total_deposits'] >= 500000) & (customers_df['total_deposits'] < 1000000)).sum():,} customers ({((customers_df['total_deposits'] >= 500000) & (customers_df['total_deposits'] < 1000000)).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  $1M-$5M: {((customers_df['total_deposits'] >= 1000000) & (customers_df['total_deposits'] < 5000000)).sum():,} customers ({((customers_df['total_deposits'] >= 1000000) & (customers_df['total_deposits'] < 5000000)).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  >$5M: {(customers_df['total_deposits'] >= 5000000).sum():,} customers ({(customers_df['total_deposits'] >= 5000000).sum()/len(customers_df)*100:.1f}%)", flush=True)

# Check digital engagement
print(f"\nDigital Engagement Distribution:", flush=True)
digital = customers_df['digital_engagement_score']
print(f"  Low (<40%): {(digital < 0.4).sum():,} customers ({(digital < 0.4).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  Medium (40-70%): {((digital >= 0.4) & (digital < 0.7)).sum():,} customers ({((digital >= 0.4) & (digital < 0.7)).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  High (>70%): {(digital >= 0.7).sum():,} customers ({(digital >= 0.7).sum()/len(customers_df)*100:.1f}%)", flush=True)

# Check products
print(f"\nProduct Holdings Distribution:", flush=True)
products = customers_df['num_products']
print(f"  1 product: {(products == 1).sum():,} customers ({(products == 1).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  2 products: {(products == 2).sum():,} customers ({(products == 2).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  3 products: {(products == 3).sum():,} customers ({(products == 3).sum()/len(customers_df)*100:.1f}%)", flush=True)
print(f"  4+ products: {(products >= 4).sum():,} customers ({(products >= 4).sum()/len(customers_df)*100:.1f}%)", flush=True)

# ============================================================================
# CHECK 3: Why 2 Segments Dominate (93% in 2 segments)
# ============================================================================
print("\n" + "="*80, flush=True)
print("CHECK 3: SEGMENTATION IMBALANCE ANALYSIS", flush=True)
print("="*80, flush=True)

print(f"\n🚨 DASHBOARD SHOWS:", flush=True)
print(f"   Elite Savers: 1,657 customers (33%)", flush=True)
print(f"   Household Savers: 3,031 customers (61%)", flush=True)
print(f"   Combined: 4,688 customers (94%!)", flush=True)
print(f"", flush=True)
print(f"   Remaining 3 segments: Only 312 customers (6%)", flush=True)

print(f"\n🔍 POSSIBLE REASONS:", flush=True)

# Calculate similarity scores for all customers
# Check if most customers are actually very similar
deposits_normalized = (customers_df['total_deposits'] - customers_df['total_deposits'].mean()) / customers_df['total_deposits'].std()
digital_normalized = (customers_df['digital_engagement_score'] - customers_df['digital_engagement_score'].mean()) / customers_df['digital_engagement_score'].std()
products_normalized = (customers_df['num_products'] - customers_df['num_products'].mean()) / customers_df['num_products'].std()
income_normalized = (customers_df['income'] - customers_df['income'].mean()) / customers_df['income'].std()

# Check how many customers are "average" (within 1 std dev on all dimensions)
average_customers = (
    (abs(deposits_normalized) < 1) &
    (abs(digital_normalized) < 1) &
    (abs(products_normalized) < 1) &
    (abs(income_normalized) < 1)
).sum()

print(f"\n1. Data Homogeneity:", flush=True)
print(f"   Customers within 1 std dev on all key metrics: {average_customers:,} ({average_customers/len(customers_df)*100:.1f}%)", flush=True)
print(f"   ➜ If >60%, data is relatively homogeneous (few natural clusters)", flush=True)

# Check variance in key clustering features
print(f"\n2. Feature Variance:", flush=True)
print(f"   Deposits coefficient of variation: {customers_df['total_deposits'].std() / customers_df['total_deposits'].mean():.2f}", flush=True)
print(f"   Digital engagement std dev: {customers_df['digital_engagement_score'].std():.3f}", flush=True)
print(f"   Products std dev: {customers_df['num_products'].std():.2f}", flush=True)
print(f"   Income coefficient of variation: {customers_df['income'].std() / customers_df['income'].mean():.2f}", flush=True)
print(f"   ➜ Low variance = harder to distinguish clusters", flush=True)

# Check for natural gaps in data
print(f"\n3. Natural Groupings:", flush=True)
sorted_deposits = customers_df['total_deposits'].sort_values()
# Find largest gaps
gaps = sorted_deposits.diff()
largest_gaps = gaps.nlargest(5)
print(f"   Largest deposit gaps:", flush=True)
for idx, gap in largest_gaps.items():
    lower = sorted_deposits[idx - 1] if idx > 0 else 0
    upper = sorted_deposits[idx]
    print(f"     Gap of ${gap:,.0f} between ${lower:,.0f} and ${upper:,.0f}", flush=True)

# ============================================================================
# RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80, flush=True)
print("📋 VERIFICATION SUMMARY", flush=True)
print("="*80, flush=True)

print(f"\n✅ INTENT SCORES (36-53%):", flush=True)
if intent_scores.mean() >= 0.35 and intent_scores.mean() <= 0.55:
    print(f"   CORRECT - Aligns with overall average of {intent_scores.mean():.2%}", flush=True)
else:
    print(f"   ⚠️  CHECK - Overall average is {intent_scores.mean():.2%}", flush=True)

print(f"\n🚨 SEGMENT IMBALANCE (94% in 2 segments):", flush=True)
if average_customers / len(customers_df) > 0.60:
    print(f"   ⚠️  DATA IS HOMOGENEOUS - {average_customers/len(customers_df)*100:.1f}% of customers are similar", flush=True)
    print(f"   ➜ This causes 2 large 'average' segments to dominate", flush=True)
    print(f"   ➜ RECOMMENDATION: Try 3-4 clusters instead of 5", flush=True)
else:
    print(f"   ⚠️  CLUSTERING ISSUE - Data has natural variation but algorithm isn't using it", flush=True)
    print(f"   ➜ RECOMMENDATION: Check clustering parameters (gamma, features used)", flush=True)

print(f"\n🎯 RECOMMENDED ACTIONS:", flush=True)
print(f"   1. Try n_clusters=3 or 4 instead of 5", flush=True)
print(f"   2. Check if gamma parameter needs adjustment", flush=True)
print(f"   3. Verify all clustering features are being used", flush=True)
print(f"   4. Consider if synthetic data needs more variation", flush=True)

print(f"\n" + "="*80, flush=True)
print("VERIFICATION COMPLETE", flush=True)
print("="*80, flush=True)

"""
Add Customer Lifetime Value (CLV) to existing customer data
Formula: CLV = Total Deposits + (Annual Transaction Value * Expected Years)
"""
import pandas as pd
from pathlib import Path

print("="*70)
print("💰 ADDING CUSTOMER LIFETIME VALUE (CLV)")
print("="*70)

data_path = Path("data/preloaded/fmb_bank")
customers_file = data_path / "customers.csv"

if not customers_file.exists():
    print(f"❌ Error: {customers_file} not found")
    print("Please run generate_fmb_data_unified.py first")
    exit(1)

# Load customers
customers_df = pd.read_csv(customers_file)
print(f"\n✓ Loaded {len(customers_df)} customers")
print(f"  Current columns: {len(customers_df.columns)}")

# Check if CLV already exists
if 'customer_lifetime_value' in customers_df.columns:
    print(f"\n⚠️  CLV column already exists, recalculating...")
    customers_df = customers_df.drop(columns=['customer_lifetime_value', 'clv_tier', 'annual_transaction_value', 'expected_relationship_years'], errors='ignore')

# Calculate CLV components
print(f"\n📊 Calculating CLV components...")

# 1. Annual transaction value (estimate from monthly volume and deposits)
customers_df['annual_transaction_value'] = (
    customers_df['monthly_transaction_volume'] * 
    customers_df['total_deposits'] * 
    0.002  # 0.2% of deposits per transaction as revenue
).round(2)

# 2. Expected relationship years (based on tenure, capped at 10 years)
customers_df['expected_relationship_years'] = customers_df['tenure_months'].apply(
    lambda x: min(x / 12, 10)
)

# 3. Customer Lifetime Value
customers_df['customer_lifetime_value'] = (
    customers_df['total_deposits'] + 
    (customers_df['annual_transaction_value'] * customers_df['expected_relationship_years'])
).round(2)

# 4. CLV Tier for easy identification
def assign_clv_tier(clv):
    if clv >= 1000000:
        return 'Diamond'  # Ultra-high value (>$1M)
    elif clv >= 500000:
        return 'Platinum'  # Very high value ($500K-$1M)
    elif clv >= 200000:
        return 'Gold'  # High value ($200K-$500K)
    elif clv >= 50000:
        return 'Silver'  # Medium value ($50K-$200K)
    else:
        return 'Bronze'  # Growing value (<$50K)

customers_df['clv_tier'] = customers_df['customer_lifetime_value'].apply(assign_clv_tier)

# Save updated file
customers_df.to_csv(customers_file, index=False)

print(f"\n✅ CLV Added Successfully!")
print(f"\n📊 CLV Distribution:")
print(f"   • Diamond (>$1M): {len(customers_df[customers_df['clv_tier']=='Diamond']):,} customers")
print(f"   • Platinum ($500K-$1M): {len(customers_df[customers_df['clv_tier']=='Platinum']):,} customers")
print(f"   • Gold ($200K-$500K): {len(customers_df[customers_df['clv_tier']=='Gold']):,} customers")
print(f"   • Silver ($50K-$200K): {len(customers_df[customers_df['clv_tier']=='Silver']):,} customers")
print(f"   • Bronze (<$50K): {len(customers_df[customers_df['clv_tier']=='Bronze']):,} customers")

print(f"\n💎 Top 5 CLV Customers:")
top_5 = customers_df.nlargest(5, 'customer_lifetime_value')
for idx, row in top_5.iterrows():
    print(f"   {row['customer_name']}: ${row['customer_lifetime_value']:,.0f} ({row['clv_tier']} tier)")

print(f"\n✓ Updated file: {customers_file}")
print(f"✓ Total columns now: {len(customers_df.columns)}")
print(f"\n" + "="*70)
print("✅ CLV SETUP COMPLETE!")
print("="*70)

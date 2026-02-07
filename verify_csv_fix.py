"""Quick verification that CSV parsing fix works"""
import pandas as pd

print("="*70)
print("VERIFYING CSV PARSING FIX")
print("="*70)

# Test with engine='python'
df = pd.read_csv('data/preloaded/fmb_bank/customers.csv', engine='python')

print(f"\n✅ CSV loaded successfully!")
print(f"   Columns: {len(df.columns)}")
print(f"   Rows: {len(df)}")

# Check for monthly_transaction_volume column
if 'monthly_transaction_volume' in df.columns:
    print(f"\n✅ 'monthly_transaction_volume' column exists!")
    print(f"   Min: {df['monthly_transaction_volume'].min():.0f}")
    print(f"   Max: {df['monthly_transaction_volume'].max():.0f}")
    print(f"   Avg: {df['monthly_transaction_volume'].mean():.1f}")
    print(f"\n🎉 CSV parsing fix is WORKING!")
else:
    print(f"\n❌ 'monthly_transaction_volume' column NOT FOUND!")
    print(f"   Available columns: {list(df.columns[:10])}")

print("="*70)

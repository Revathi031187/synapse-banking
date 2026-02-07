"""
Regenerate FMB Bank CSV with proper formatting
Fixes the pandas C engine parsing issue
"""
import pandas as pd
from pathlib import Path

print("="*80)
print("REGENERATING FMB BANK CSV FILES")
print("="*80)

# Read with Python engine (works correctly)
input_dir = Path('data/preloaded/fmb_bank')
customers_path = input_dir / 'customers.csv'

print("\n1. Reading existing data with Python engine...")
df = pd.read_csv(customers_path, engine='python')
print(f"   ✓ Loaded {len(df)} customers with {len(df.columns)} columns")
print(f"   ✓ monthly_transaction_volume exists: {'monthly_transaction_volume' in df.columns}")

if 'monthly_transaction_volume' in df.columns:
    print(f"   ✓ Range: {df['monthly_transaction_volume'].min():.0f} - {df['monthly_transaction_volume'].max():.0f}")

# Save with proper formatting
backup_path = input_dir / 'customers_backup.csv'
print(f"\n2. Creating backup at: {backup_path}")
df.to_csv(backup_path, index=False)

print(f"\n3. Regenerating customers.csv with proper formatting...")
df.to_csv(customers_path, index=False, encoding='utf-8', lineterminator='\n')
print(f"   ✓ Saved {len(df)} customers")

# Verify with default pandas (C engine)
print(f"\n4. Verifying with default pandas parser...")
df_verify = pd.read_csv(customers_path)
print(f"   Columns: {len(df_verify.columns)}")

if len(df_verify.columns) > 40:
    print(f"   ✅ SUCCESS! CSV now reads correctly")
    print(f"   monthly_transaction_volume exists: {'monthly_transaction_volume' in df_verify.columns}")
    if 'monthly_transaction_volume' in df_verify.columns:
        print(f"   Range: {df_verify['monthly_transaction_volume'].min():.0f} - {df_verify['monthly_transaction_volume'].max():.0f}")
        print(f"   Avg: {df_verify['monthly_transaction_volume'].mean():.1f}")
else:
    print(f"   ❌ STILL FAILING - columns: {len(df_verify.columns)}")
    print(f"   This may be a pandas version issue")

# Also fix products and transactions if they exist
for filename in ['products.csv', 'transactions.csv']:
    file_path = input_dir / filename
    if file_path.exists():
        print(f"\n5. Fixing {filename}...")
        df_temp = pd.read_csv(file_path, engine='python')
        df_temp.to_csv(file_path, index=False, encoding='utf-8', lineterminator='\n')
        print(f"   ✓ Fixed {filename}")

print("\n" + "="*80)
print("REGENERATION COMPLETE")
print("="*80)

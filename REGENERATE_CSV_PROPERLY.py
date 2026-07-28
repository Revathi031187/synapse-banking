"""Regenerate CSV file so pandas C engine can read it"""
import pandas as pd
from pathlib import Path

print("="*80)
print("REGENERATING FMB BANK CSV - PROPERLY FORMATTED")
print("="*80)

input_dir = Path('data/preloaded/fmb_bank')
customers_path = input_dir / 'customers.csv'

print("\n1. Reading with Python engine (works)...")
df = pd.read_csv(customers_path, engine='python')
print(f"   ✓ Loaded: {len(df)} rows, {len(df.columns)} columns")

print("\n2. Creating backup...")
backup_path = input_dir / 'customers_OLD_BROKEN.csv'
import shutil
shutil.copy(customers_path, backup_path)
print(f"   ✓ Backup saved: {backup_path}")

print("\n3. Regenerating with proper format...")
# Write with explicit parameters for maximum compatibility
df.to_csv(
    customers_path,
    index=False,
    encoding='utf-8',
    lineterminator='\n',
    sep=',',
    quoting=1  # QUOTE_MINIMAL
)
print(f"   ✓ Regenerated: {customers_path}")

print("\n4. Testing with DEFAULT pandas (C engine)...")
df_test = pd.read_csv(customers_path)  # No engine='python'!
print(f"   Columns: {len(df_test.columns)}")

if len(df_test.columns) > 40:
    print(f"   ✅ SUCCESS! CSV now works with default pandas!")
    print(f"   'monthly_transaction_volume' exists: {'monthly_transaction_volume' in df_test.columns}")
    if 'monthly_transaction_volume' in df_test.columns:
        print(f"   Range: {df_test['monthly_transaction_volume'].min():.0f} - {df_test['monthly_transaction_volume'].max():.0f}")
else:
    print(f"   ❌ STILL BROKEN - only {len(df_test.columns)} columns")

print("\n5. Also fixing transactions and products...")
for filename in ['transactions.csv', 'products.csv']:
    file_path = input_dir / filename
    if file_path.exists():
        df_temp = pd.read_csv(file_path, engine='python')
        df_temp.to_csv(file_path, index=False, encoding='utf-8', lineterminator='\n', sep=',', quoting=1)
        print(f"   ✓ Fixed: {filename}")

print("\n" + "="*80)
print("REGENERATION COMPLETE")
print("="*80)
print("\nNow run: TEST_SHORT_NAMES.bat")

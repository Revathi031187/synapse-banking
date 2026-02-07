"""
Fix CSV Reading Issue - Debug and regenerate if needed
"""
import pandas as pd
import sys

print("="*80)
print("CSV READING DIAGNOSTIC")
print("="*80)

# Try different reading methods
csv_path = 'data/preloaded/fmb_bank/customers.csv'

print("\n1. Default read_csv:")
try:
    df1 = pd.read_csv(csv_path)
    print(f"   Columns: {len(df1.columns)}")
    print(f"   First column name: {df1.columns[0][:100]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. Explicit comma delimiter:")
try:
    df2 = pd.read_csv(csv_path, sep=',')
    print(f"   Columns: {len(df2.columns)}")
    print(f"   First 5 columns: {list(df2.columns[:5])}")
    if len(df2.columns) > 1:
        print(f"   ✓ SUCCESS! 'monthly_transaction_volume' exists: {'monthly_transaction_volume' in df2.columns}")
        print(f"\n   Monthly transaction stats:")
        print(f"   Min: {df2['monthly_transaction_volume'].min():.0f}")
        print(f"   Max: {df2['monthly_transaction_volume'].max():.0f}")
        print(f"   Avg: {df2['monthly_transaction_volume'].mean():.1f}")
except Exception as e:
    print(f"   Error: {e}")

print("\n3. With engine='python':")
try:
    df3 = pd.read_csv(csv_path, sep=',', engine='python')
    print(f"   Columns: {len(df3.columns)}")
    print(f"   First 5 columns: {list(df3.columns[:5])}")
    if len(df3.columns) > 1:
        print(f"   ✓ SUCCESS! 'monthly_transaction_volume' exists: {'monthly_transaction_volume' in df3.columns}")
except Exception as e:
    print(f"   Error: {e}")

print("\n4. Check file encoding:")
try:
    with open(csv_path, 'rb') as f:
        first_bytes = f.read(100)
        print(f"   First bytes: {first_bytes[:80]}")
        print(f"   Contains BOM: {first_bytes.startswith(b'\xef\xbb\xbf')}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)

# Final test
df_final = pd.read_csv(csv_path, sep=',')
if len(df_final.columns) > 40:  # Should have 50 columns
    print("✅ CSV reads correctly with sep=','")
    print(f"   Total columns: {len(df_final.columns)}")
    print(f"   monthly_transaction_volume exists: {'monthly_transaction_volume' in df_final.columns}")
    if 'monthly_transaction_volume' in df_final.columns:
        print(f"   Range: {df_final['monthly_transaction_volume'].min():.0f} - {df_final['monthly_transaction_volume'].max():.0f}")
else:
    print("❌ CSV still not reading correctly")
    print("   Need to regenerate the CSV file")
    sys.exit(1)

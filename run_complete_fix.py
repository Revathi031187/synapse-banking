"""
Complete fix for F&M Bank platform
Regenerates data and verifies all fixes
"""
import subprocess
import pandas as pd
import sys

print("="*80)
print("F&M BANK - COMPLETE FIX")
print("="*80)

# Step 1: Regenerate data
print("\n[1/3] Regenerating F&M Bank data...")
print("-" * 80)
result = subprocess.run([sys.executable, "generate_fmb_data_unified.py"], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"ERROR: {result.stderr}")
    sys.exit(1)

# Step 2: Verify products
print("\n[2/3] Verifying products.csv...")
print("-" * 80)
products = pd.read_csv('data/preloaded/fmb_bank/products.csv')
print(f"Total products: {len(products)}")
print(f"\nTarget segment values:")
print(products['target_segment'].value_counts())

if 'Mass_Market' in products['target_segment'].values or 'Digital_Native' in products['target_segment'].values:
    print("❌ ERROR: Products still have customer types as target_segment!")
    print("   Expected: Personal, Business, Agricultural")
    sys.exit(1)
else:
    print("✅ Products have correct target_segment values!")

# Step 3: Verify customers
print("\n[3/3] Verifying customers.csv...")
print("-" * 80)
customers = pd.read_csv('data/preloaded/fmb_bank/customers.csv')
print(f"Total customers: {len(customers)}")
print(f"\nSegment distribution:")
for seg, count in customers['customer_segment'].value_counts().items():
    pct = (count / len(customers)) * 100
    print(f"  {seg}: {count} ({pct:.1f}%)")

print(f"\nData variance:")
print(f"  Cross-sell receptivity:")
print(f"    Min: {customers['cross_sell_receptivity'].min():.3f}")
print(f"    Max: {customers['cross_sell_receptivity'].max():.3f}")
print(f"    Std: {customers['cross_sell_receptivity'].std():.3f}")
print(f"  Monthly transactions:")
print(f"    Min: {customers['monthly_transaction_volume'].min():.0f}")
print(f"    Max: {customers['monthly_transaction_volume'].max():.0f}")
print(f"    Std: {customers['monthly_transaction_volume'].std():.0f}")

ag_count = len(customers[customers['customer_segment'] == 'Agricultural'])
if ag_count == 0:
    print("\n❌ ERROR: No Agricultural customers!")
    sys.exit(1)
else:
    print(f"\n✅ Agricultural customers present: {ag_count}")

print("\n" + "="*80)
print("✅ ALL DATA FIXES COMPLETE!")
print("="*80)
print("\n🚀 NEXT STEPS:")
print("1. RESTART BACKEND:")
print("   Press Ctrl+C in the terminal running api, then:")
print("   python api/main_unified_chromadb.py")
print("\n2. IN UI:")
print("   - Load Data (should show 5000 customers)")
print("   - Run Agent A (5 personas)")
print("   - Look for 'Generating micro-segments' in terminal logs")
print("   - Test Agent B (should return 3 products)")
print("\n3. VERIFY:")
print("   - Transactions/Intent show DIFFERENT values (not all 50)")
print("   - Micro-segments appear when clicking personas")
print("   - Agent B returns products (not 0)")
print("="*80)

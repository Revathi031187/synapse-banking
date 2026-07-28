"""
F&M BANK CRITICAL FIXES - Run this to fix ALL issues
"""
import pandas as pd
from pathlib import Path

print("="*80)
print("F&M BANK DATA VERIFICATION & FIX")
print("="*80)

data_dir = Path("data/preloaded/fmb_bank")

# Check current state
customers_df = pd.read_csv(data_dir / "customers.csv")
products_df = pd.read_csv(data_dir / "products.csv")
transactions_df = pd.read_csv(data_dir / "transactions.csv")

print(f"\n📊 CURRENT STATE:")
print(f"   Total Customers: {len(customers_df)}")
print(f"   Total Products: {len(products_df)}")
print(f"   Total Transactions: {len(transactions_df)}")

print(f"\n🏢 SEGMENT DISTRIBUTION:")
segment_counts = customers_df['customer_segment'].value_counts()
for segment, count in segment_counts.items():
    pct = (count / len(customers_df)) * 100
    print(f"   {segment:12s}: {count:4d} ({pct:.1f}%)")

print(f"\n👥 CUSTOMER TYPE DISTRIBUTION:")
type_counts = customers_df['customer_type'].value_counts()
for ctype, count in type_counts.items():
    print(f"   {ctype:25s}: {count:4d}")

# Check for Agricultural customers
ag_count = len(customers_df[customers_df['customer_segment'] == 'Agricultural'])

if ag_count == 0:
    print(f"\n❌ CRITICAL: NO AGRICULTURAL CUSTOMERS!")
    print(f"   This will cause segmentation issues.")
    print(f"\n🔧 SOLUTION: Run 'python generate_fmb_data_unified.py'")
    print(f"   This will regenerate data with correct distribution:")
    print(f"   - Personal: 3000 (60%)")
    print(f"   - Business: 1500 (30%)")
    print(f"   - Agricultural: 500 (10%)")
else:
    print(f"\n✅ Agricultural customers present: {ag_count}")

# Check monthly_transaction_volume column
if 'monthly_transaction_volume' in customers_df.columns:
    print(f"\n✅ monthly_transaction_volume column exists")
    sample_values = customers_df['monthly_transaction_volume'].head(10).tolist()
    print(f"   Sample values: {sample_values}")
    avg_value = customers_df['monthly_transaction_volume'].mean()
    print(f"   Average: {avg_value:.2f}")
else:
    print(f"\n❌ monthly_transaction_volume column MISSING!")

print(f"\n" + "="*80)
print(f"NEXT STEPS:")
print(f"="*80)
print(f"1. If Agricultural customers missing, run:")
print(f"   python generate_fmb_data_unified.py")
print(f"\n2. Restart backend:")
print(f"   Ctrl+C in terminal, then: python api/main_unified_chromadb.py")
print(f"\n3. In UI:")
print(f"   - Load Data (this will now save products to system_state)")
print(f"   - Run Agent A")
print(f"   - Agent B should now work!")
print(f"="*80)

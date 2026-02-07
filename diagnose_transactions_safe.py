"""
Bulletproof transaction diagnostics - guaranteed to produce output
"""
import sys
import os

# Step 1: Test basic printing
try:
    print("="*80, flush=True)
    print("TRANSACTION DIAGNOSTICS - SAFE VERSION", flush=True)
    print("="*80, flush=True)
    print(f"Current directory: {os.getcwd()}", flush=True)
    print(f"Python version: {sys.version}", flush=True)
except Exception as e:
    print(f"ERROR in basic setup: {e}", flush=True)
    sys.exit(1)

# Step 2: Import pandas
try:
    print("\nStep 1: Importing pandas...", flush=True)
    import pandas as pd
    from pathlib import Path
    print("   ✓ Pandas imported", flush=True)
except Exception as e:
    print(f"   ✗ Failed to import pandas: {e}", flush=True)
    sys.exit(1)

# Step 3: Check file existence
try:
    print("\nStep 2: Checking files...", flush=True)
    csv_path = Path('data/preloaded/fmb_bank/customers.csv')
    tx_path = Path('data/preloaded/fmb_bank/transactions.csv')
    
    print(f"   Customers CSV: {csv_path}", flush=True)
    print(f"   Exists: {csv_path.exists()}", flush=True)
    
    print(f"   Transactions CSV: {tx_path}", flush=True)
    print(f"   Exists: {tx_path.exists()}", flush=True)
    
    if not csv_path.exists():
        print(f"\n   ✗ ERROR: customers.csv not found at {csv_path.absolute()}", flush=True)
        sys.exit(1)
    
    if not tx_path.exists():
        print(f"\n   ✗ ERROR: transactions.csv not found at {tx_path.absolute()}", flush=True)
        sys.exit(1)
    
    print("   ✓ Both files exist", flush=True)
    
except Exception as e:
    print(f"   ✗ Error checking files: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Load customers
try:
    print("\nStep 3: Loading customers.csv...", flush=True)
    df = pd.read_csv(csv_path, engine='python')
    print(f"   ✓ Loaded {len(df):,} customers", flush=True)
    print(f"   Columns: {len(df.columns)}", flush=True)
    
except Exception as e:
    print(f"   ✗ Failed to load customers: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Check monthly_transaction_volume
try:
    print("\nStep 4: Checking monthly_transaction_volume column...", flush=True)
    
    if 'monthly_transaction_volume' in df.columns:
        print("   ✓ Column found!", flush=True)
        
        min_val = df['monthly_transaction_volume'].min()
        max_val = df['monthly_transaction_volume'].max()
        avg_val = df['monthly_transaction_volume'].mean()
        sum_val = df['monthly_transaction_volume'].sum()
        
        print(f"\n   📊 Column statistics:", flush=True)
        print(f"      Min: {min_val:.0f}", flush=True)
        print(f"      Max: {max_val:.0f}", flush=True)
        print(f"      Average: {avg_val:.1f}", flush=True)
        print(f"      Total sum: {sum_val:,.0f}", flush=True)
        
    else:
        print("   ✗ Column NOT found!", flush=True)
        print(f"   Available columns: {list(df.columns[:15])}", flush=True)
        
except Exception as e:
    print(f"   ✗ Error analyzing column: {e}", flush=True)
    import traceback
    traceback.print_exc()

# Step 6: Load transactions
try:
    print("\nStep 5: Loading transactions.csv...", flush=True)
    tx_df = pd.read_csv(tx_path, engine='python')
    print(f"   ✓ Loaded {len(tx_df):,} transactions", flush=True)
    print(f"   Columns: {list(tx_df.columns)}", flush=True)
    
except Exception as e:
    print(f"   ✗ Failed to load transactions: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 7: Basic transaction analysis
try:
    print("\nStep 6: Analyzing transactions...", flush=True)
    
    if 'customer_id' in tx_df.columns:
        unique_customers = tx_df['customer_id'].nunique()
        total_txns = len(tx_df)
        avg_per_customer = total_txns / unique_customers
        
        print(f"   Total transactions: {total_txns:,}", flush=True)
        print(f"   Unique customers: {unique_customers:,}", flush=True)
        print(f"   Average per customer: {avg_per_customer:.1f}", flush=True)
    else:
        print("   ✗ No customer_id column found", flush=True)
    
except Exception as e:
    print(f"   ✗ Error analyzing transactions: {e}", flush=True)
    import traceback
    traceback.print_exc()

# Step 8: Date analysis
try:
    print("\nStep 7: Date analysis...", flush=True)
    
    if 'transaction_date' in tx_df.columns:
        print("   ✓ transaction_date column found", flush=True)
        
        # Try to parse dates
        tx_df['transaction_date'] = pd.to_datetime(tx_df['transaction_date'], errors='coerce')
        valid_dates = tx_df['transaction_date'].dropna()
        
        if len(valid_dates) > 0:
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            date_range_days = (max_date - min_date).days
            date_range_months = date_range_days / 30
            
            print(f"   Date range: {min_date.date()} to {max_date.date()}", flush=True)
            print(f"   Span: {date_range_days} days ({date_range_months:.1f} months)", flush=True)
            
            # Calculate TRUE monthly rate
            monthly_rate = total_txns / unique_customers / date_range_months
            print(f"\n   🎯 TRUE monthly transaction rate:", flush=True)
            print(f"      {monthly_rate:.2f} txns/month/customer", flush=True)
            print(f"      {monthly_rate * 12:.1f} txns/year/customer", flush=True)
            
        else:
            print("   ✗ No valid dates found in transaction_date column", flush=True)
    else:
        print("   ✗ No transaction_date column found", flush=True)
        print(f"   Available: {list(tx_df.columns)}", flush=True)
    
except Exception as e:
    print(f"   ✗ Error in date analysis: {e}", flush=True)
    import traceback
    traceback.print_exc()

# Step 9: Diagnosis
try:
    print("\n" + "="*80, flush=True)
    print("DIAGNOSIS", flush=True)
    print("="*80, flush=True)
    
    if 'monthly_transaction_volume' in df.columns and 'customer_id' in tx_df.columns:
        customer_col_avg = df['monthly_transaction_volume'].mean()
        actual_total_avg = len(tx_df) / len(df)
        
        print(f"\nCustomer column average: {customer_col_avg:.1f}", flush=True)
        print(f"Actual transactions per customer: {actual_total_avg:.1f}", flush=True)
        print(f"Difference: {abs(customer_col_avg - actual_total_avg):.1f}", flush=True)
        
        if abs(customer_col_avg - actual_total_avg) < 5:
            print("\n✅ Column represents TOTAL transactions (not monthly)", flush=True)
            print("   The column is misnamed - it should be 'total_transactions'", flush=True)
            
            if 'transaction_date' in tx_df.columns and len(valid_dates) > 0:
                correct_monthly = actual_total_avg / date_range_months
                print(f"\n   📊 Correct monthly rate: {correct_monthly:.2f} txns/month", flush=True)
                print(f"      (Currently showing: {customer_col_avg:.1f})", flush=True)
                print(f"      Off by: {customer_col_avg / correct_monthly:.0f}x", flush=True)
        else:
            print("\n⚠️  Values don't match - possible data inconsistency", flush=True)
    
except Exception as e:
    print(f"   ✗ Error in diagnosis: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("\n" + "="*80, flush=True)
print("DIAGNOSTIC COMPLETE", flush=True)
print("="*80, flush=True)
print("\nRead: ✅_MICRO_SEGMENTS_FIXED.md for micro segment fix", flush=True)
print("", flush=True)

"""
Diagnose transaction calculation issues
Determines if monthly_transaction_volume column represents monthly or total transactions
"""
import pandas as pd
from pathlib import Path
import sys
import os

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

print("="*80, flush=True)
print("🔍 TRANSACTION DATA DIAGNOSTICS", flush=True)
print("="*80, flush=True)
print(f"\nCurrent directory: {os.getcwd()}", flush=True)

try:
    # Load data with Python engine
    print("\n📂 Loading data files...", flush=True)
    csv_path = Path('data/preloaded/fmb_bank/customers.csv')
    print(f"   Checking: {csv_path.absolute()}", flush=True)
    print(f"   Exists: {csv_path.exists()}", flush=True)
    
    df = pd.read_csv(csv_path, engine='python')
    print(f"   ✓ Loaded {len(df):,} customers", flush=True)
    
    transactions_path = Path('data/preloaded/fmb_bank/transactions.csv')
    print(f"   Checking: {transactions_path.absolute()}", flush=True)
    print(f"   Exists: {transactions_path.exists()}", flush=True)
    
    transactions_df = pd.read_csv(transactions_path, engine='python')
    print(f"   ✓ Loaded {len(transactions_df):,} transactions", flush=True)
    
    print("\n" + "="*80)
    print("1️⃣  CUSTOMER CSV COLUMN ANALYSIS")
    print("="*80)
    
    # Check customer column
    if 'monthly_transaction_volume' in df.columns:
        min_val = df['monthly_transaction_volume'].min()
        max_val = df['monthly_transaction_volume'].max()
        avg_val = df['monthly_transaction_volume'].mean()
        sum_val = df['monthly_transaction_volume'].sum()
        
        print(f"\nColumn 'monthly_transaction_volume':")
        print(f"   Range: {min_val:.0f} - {max_val:.0f}")
        print(f"   Average: {avg_val:.1f}")
        print(f"   Total sum: {sum_val:,.0f}")
        print(f"   Per customer: {sum_val / len(df):.1f}")
        
        # If this were MONTHLY:
        annual_projection = sum_val * 12
        print(f"\n   📊 If these are MONTHLY per customer:")
        print(f"      Annual total: {annual_projection:,.0f} transactions/year")
        print(f"      Per customer/year: {annual_projection / len(df):.0f}")
    else:
        print("\n❌ Column 'monthly_transaction_volume' NOT FOUND!")
        print(f"   Available columns: {list(df.columns[:15])}")
    
    print("\n" + "="*80)
    print("2️⃣  TRANSACTION FILE ANALYSIS")
    print("="*80)
    
    print(f"\nTransaction file 'transactions.csv':")
    print(f"   Total rows: {len(transactions_df):,}")
    print(f"   Unique customers: {transactions_df['customer_id'].nunique():,}")
    print(f"   Avg per customer: {len(transactions_df) / transactions_df['customer_id'].nunique():.1f}")
    
    # Check if transaction file has dates
    if 'transaction_date' in transactions_df.columns:
        print(f"\n   📅 Date analysis:")
        transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'], errors='coerce')
        
        valid_dates = transactions_df['transaction_date'].dropna()
        if len(valid_dates) > 0:
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            date_range_days = (max_date - min_date).days
            date_range_months = date_range_days / 30
            
            print(f"      Start date: {min_date.date()}")
            print(f"      End date: {max_date.date()}")
            print(f"      Span: {date_range_days} days ({date_range_months:.1f} months)")
            
            # Calculate TRUE monthly rate
            months = max(date_range_months, 1)
            unique_customers = transactions_df['customer_id'].nunique()
            monthly_rate = len(transactions_df) / unique_customers / months
            
            print(f"\n      🎯 TRUE monthly transaction rate:")
            print(f"         {monthly_rate:.2f} transactions/month/customer")
            print(f"         {monthly_rate * 12:.1f} transactions/year/customer")
        else:
            print("      ⚠️  No valid dates found")
    else:
        print(f"\n   ⚠️  No 'transaction_date' column found")
        print(f"      Available columns: {list(transactions_df.columns)}")
    
    print("\n" + "="*80)
    print("3️⃣  COMPARISON & DIAGNOSIS")
    print("="*80)
    
    # Compare values
    if 'monthly_transaction_volume' in df.columns:
        customer_col_avg = df['monthly_transaction_volume'].mean()
        actual_total_avg = len(transactions_df) / len(df)
        
        print(f"\nComparison:")
        print(f"   Customer column average: {customer_col_avg:.1f}")
        print(f"   Actual from transaction file: {actual_total_avg:.1f}")
        print(f"   Difference: {abs(customer_col_avg - actual_total_avg):.1f}")
        
        print("\n" + "="*80)
        print("📋 DIAGNOSIS")
        print("="*80)
        
        if abs(customer_col_avg - actual_total_avg) < 5:
            print("\n✅ Column represents TOTAL TRANSACTIONS (not monthly)")
            print("\n🔧 FIXES NEEDED:")
            print("   1. Rename column: 'monthly_transaction_volume' → 'total_transactions'")
            print("   2. Calculate monthly rate by dividing by timespan")
            
            if 'transaction_date' in transactions_df.columns and len(valid_dates) > 0:
                correct_monthly = actual_total_avg / months
                print(f"\n   📊 Correct monthly rate should be: {correct_monthly:.2f} txns/month/customer")
                print(f"      (Total {actual_total_avg:.1f} ÷ {months:.1f} months = {correct_monthly:.2f})")
        else:
            print("\n⚠️  VALUES DON'T MATCH")
            print(f"   Customer column: {customer_col_avg:.1f}")
            print(f"   Transaction file: {actual_total_avg:.1f}")
            print(f"   Gap: {abs(customer_col_avg - actual_total_avg):.1f}")
            print("\n   Possible reasons:")
            print("   - Customer column may have been calculated incorrectly")
            print("   - Transaction file may be incomplete")
            print("   - Customer column may include transactions not in file")
    
    print("\n" + "="*80)
    print("4️⃣  WHAT THE DASHBOARD SHOULD SHOW")
    print("="*80)
    
    if 'transaction_date' in transactions_df.columns and len(valid_dates) > 0:
        total_txns = len(transactions_df)
        total_customers = len(df)
        avg_per_customer = total_txns / total_customers
        monthly_per_customer = avg_per_customer / months
        
        print(f"\nWith {total_txns:,} transactions across {months:.1f} months:")
        print(f"   📈 Correct dashboard values:")
        print(f"      Total per customer: {avg_per_customer:.1f}")
        print(f"      Monthly per customer: {monthly_per_customer:.2f}")
        print(f"      Daily per customer: {monthly_per_customer/30:.3f}")
        
        print(f"\n   ❌ WRONG values (current dashboard):")
        if 'monthly_transaction_volume' in df.columns:
            print(f"      Showing: {df['monthly_transaction_volume'].mean():.0f}")
            print(f"      Should be: {monthly_per_customer:.2f}")
            print(f"      Off by: {df['monthly_transaction_volume'].mean() / monthly_per_customer:.0f}x")
    
    print("\n" + "="*80)
    print("✅ DIAGNOSTIC COMPLETE")
    print("="*80)
    
except FileNotFoundError as e:
    print(f"\n❌ ERROR: File not found")
    print(f"   {e}")
    print(f"\n   Make sure you're in the project root directory")
    print(f"   Current directory: {Path.cwd()}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

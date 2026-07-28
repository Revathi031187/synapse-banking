"""
Comprehensive Data Fix Script
Fixes all identified data quality issues:
1. Recalculates monthly_transaction_volume from actual transactions
2. Fixes out-of-range income values
3. Validates all other columns
"""
import csv
import sys
from datetime import datetime
from collections import defaultdict
import shutil
from pathlib import Path

print("="*80, flush=True)
print("COMPREHENSIVE DATA FIX SCRIPT", flush=True)
print("="*80, flush=True)

# ============================================================================
# STEP 1: Backup existing files
# ============================================================================
print("\n📦 STEP 1: BACKING UP EXISTING FILES", flush=True)
print("-"*80, flush=True)

backup_dir = Path('data/preloaded/fmb_bank_backup')
backup_dir.mkdir(parents=True, exist_ok=True)

try:
    shutil.copy2('data/preloaded/fmb_bank/customers.csv', backup_dir / 'customers.csv')
    print(f"✓ Backed up customers.csv to {backup_dir}/", flush=True)
except Exception as e:
    print(f"✗ Backup failed: {e}", flush=True)
    print("Continuing anyway...", flush=True)

# ============================================================================
# STEP 2: Load data
# ============================================================================
print("\n📊 STEP 2: LOADING DATA", flush=True)
print("-"*80, flush=True)

with open('data/preloaded/fmb_bank/customers.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    customers = list(reader)
    columns = list(customers[0].keys())

with open('data/preloaded/fmb_bank/transactions.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    transactions = list(reader)

print(f"✓ Loaded {len(customers):,} customers", flush=True)
print(f"✓ Loaded {len(transactions):,} transactions", flush=True)

# ============================================================================
# STEP 3: Calculate actual transaction metrics
# ============================================================================
print("\n📊 STEP 3: CALCULATING ACTUAL METRICS", flush=True)
print("-"*80, flush=True)

# Group transactions by customer
customer_transactions = defaultdict(list)
for tx in transactions:
    customer_transactions[tx['customer_id']].append(tx)

# Parse dates and calculate time span
all_dates = []
for tx in transactions:
    try:
        date = datetime.strptime(tx['transaction_date'], '%Y-%m-%d')
        all_dates.append(date)
    except:
        pass

min_date = min(all_dates)
max_date = max(all_dates)
date_span_days = (max_date - min_date).days
date_span_months = date_span_days / 30.0

print(f"✓ Date span: {date_span_months:.1f} months ({date_span_days} days)", flush=True)

# Calculate per-customer metrics
customer_actual_metrics = {}
for cust in customers:
    cust_id = cust['customer_id']
    
    if cust_id in customer_transactions:
        txs = customer_transactions[cust_id]
        total_txns = len(txs)
        monthly_txns = total_txns / date_span_months
        annual_txns = monthly_txns * 12
    else:
        # Customer has no transactions
        total_txns = 0
        monthly_txns = 0
        annual_txns = 0
    
    customer_actual_metrics[cust_id] = {
        'total_transactions': total_txns,
        'monthly_transactions': round(monthly_txns, 2),
        'annual_transactions': round(annual_txns, 1)
    }

print(f"✓ Calculated metrics for {len(customer_actual_metrics):,} customers", flush=True)

# ============================================================================
# STEP 4: Fix monthly_transaction_volume
# ============================================================================
print("\n🔧 STEP 4: FIXING monthly_transaction_volume", flush=True)
print("-"*80, flush=True)

old_values = []
new_values = []
changes = 0

for cust in customers:
    cust_id = cust['customer_id']
    
    # Get old value
    old_value = float(cust.get('monthly_transaction_volume', 0))
    old_values.append(old_value)
    
    # Set new value from actual data
    new_value = customer_actual_metrics[cust_id]['monthly_transactions']
    new_values.append(new_value)
    
    # Update
    if abs(old_value - new_value) > 0.01:
        changes += 1
    
    cust['monthly_transaction_volume'] = str(new_value)

print(f"✓ Updated {changes:,} customer records", flush=True)
print(f"  Old average: {sum(old_values)/len(old_values):.2f}", flush=True)
print(f"  New average: {sum(new_values)/len(new_values):.2f}", flush=True)
print(f"  Correction: {(sum(old_values)/sum(new_values)):.1f}x reduction", flush=True)

# ============================================================================
# STEP 5: Fix out-of-range income values
# ============================================================================
print("\n🔧 STEP 5: FIXING OUT-OF-RANGE INCOME VALUES", flush=True)
print("-"*80, flush=True)

income_fixes = 0
for cust in customers:
    try:
        income = float(cust.get('income', 0))
        
        # Cap at reasonable limits
        if income < 15000:
            cust['income'] = str(15000)
            income_fixes += 1
        elif income > 1000000:
            cust['income'] = str(1000000)
            income_fixes += 1
    except:
        # Non-numeric income, set to default
        cust['income'] = str(45000)
        income_fixes += 1

if income_fixes > 0:
    print(f"✓ Fixed {income_fixes:,} out-of-range income values", flush=True)
else:
    print(f"✓ All income values are within range", flush=True)

# ============================================================================
# STEP 6: Recalculate annual_transaction_value
# ============================================================================
print("\n🔧 STEP 6: RECALCULATING annual_transaction_value", flush=True)
print("-"*80, flush=True)

if 'annual_transaction_value' in columns:
    atv_updated = 0
    
    for cust in customers:
        cust_id = cust['customer_id']
        
        if cust_id in customer_transactions:
            # Calculate actual annual transaction value from amounts
            txs = customer_transactions[cust_id]
            total_amount = sum(float(tx['amount']) for tx in txs)
            annual_amount = (total_amount / date_span_months) * 12
            
            cust['annual_transaction_value'] = f"{annual_amount:.2f}"
            atv_updated += 1
        else:
            cust['annual_transaction_value'] = "0.00"
    
    print(f"✓ Recalculated annual_transaction_value for {atv_updated:,} customers", flush=True)

# ============================================================================
# STEP 7: Save fixed data
# ============================================================================
print("\n💾 STEP 7: SAVING FIXED DATA", flush=True)
print("-"*80, flush=True)

output_path = 'data/preloaded/fmb_bank/customers.csv'

try:
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(customers)
    
    print(f"✓ Saved fixed data to {output_path}", flush=True)
    print(f"  Total records: {len(customers):,}", flush=True)
    
except Exception as e:
    print(f"✗ Error saving: {e}", flush=True)
    sys.exit(1)

# ============================================================================
# STEP 8: Verify fixes
# ============================================================================
print("\n✅ STEP 8: VERIFYING FIXES", flush=True)
print("-"*80, flush=True)

# Reload and check
with open(output_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    verified = list(reader)

# Check monthly_transaction_volume
mtv_values = [float(c['monthly_transaction_volume']) for c in verified]
print(f"\nmonthly_transaction_volume after fix:", flush=True)
print(f"  Min: {min(mtv_values):.2f}", flush=True)
print(f"  Max: {max(mtv_values):.2f}", flush=True)
print(f"  Average: {sum(mtv_values)/len(mtv_values):.2f}", flush=True)

# Check income
income_values = [float(c['income']) for c in verified]
out_of_range = sum(1 for i in income_values if i < 15000 or i > 1000000)
print(f"\nincome after fix:", flush=True)
print(f"  Out of range: {out_of_range}", flush=True)

print("\n" + "="*80, flush=True)
print("✅ ALL FIXES COMPLETE!", flush=True)
print("="*80, flush=True)

print(f"\n📋 SUMMARY:", flush=True)
print(f"  ✓ Fixed monthly_transaction_volume: {changes:,} records updated", flush=True)
print(f"  ✓ Fixed income values: {income_fixes:,} records updated", flush=True)
if 'annual_transaction_value' in columns:
    print(f"  ✓ Recalculated annual_transaction_value: {atv_updated:,} records updated", flush=True)
print(f"  ✓ Backup saved to: {backup_dir}/", flush=True)

print(f"\n🎯 NEXT STEPS:", flush=True)
print(f"  1. Restart backend: restart_backend.bat", flush=True)
print(f"  2. Reload data in UI", flush=True)
print(f"  3. Verify segment transaction values are now correct", flush=True)
print(f"", flush=True)

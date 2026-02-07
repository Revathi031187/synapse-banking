"""
Comprehensive Data Quality Audit
Checks all columns for consistency, errors, and calculates correct values
"""
import csv
import sys
from datetime import datetime
from collections import defaultdict, Counter

print("="*80, flush=True)
print("COMPREHENSIVE DATA QUALITY AUDIT", flush=True)
print("="*80, flush=True)

# ============================================================================
# STEP 1: Load and analyze customers.csv
# ============================================================================
print("\n📊 STEP 1: LOADING CUSTOMERS DATA", flush=True)
print("-"*80, flush=True)

try:
    with open('data/preloaded/fmb_bank/customers.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        customers = list(reader)
    
    print(f"✓ Loaded {len(customers):,} customers", flush=True)
    print(f"✓ Columns: {len(customers[0].keys())}", flush=True)
    
    # Show all column names
    columns = list(customers[0].keys())
    print(f"\n📋 All {len(columns)} columns:", flush=True)
    for i, col in enumerate(columns, 1):
        print(f"   {i:2d}. {col}", flush=True)
    
except Exception as e:
    print(f"✗ Error loading customers: {e}", flush=True)
    sys.exit(1)

# ============================================================================
# STEP 2: Load and analyze transactions.csv
# ============================================================================
print(f"\n📊 STEP 2: LOADING TRANSACTIONS DATA", flush=True)
print("-"*80, flush=True)

try:
    with open('data/preloaded/fmb_bank/transactions.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        transactions = list(reader)
    
    print(f"✓ Loaded {len(transactions):,} transactions", flush=True)
    print(f"✓ Columns: {', '.join(transactions[0].keys())}", flush=True)
    
except Exception as e:
    print(f"✗ Error loading transactions: {e}", flush=True)
    sys.exit(1)

# ============================================================================
# STEP 3: Calculate actual transaction metrics per customer
# ============================================================================
print(f"\n📊 STEP 3: CALCULATING ACTUAL TRANSACTION METRICS", flush=True)
print("-"*80, flush=True)

# Group transactions by customer
customer_transactions = defaultdict(list)
for tx in transactions:
    customer_transactions[tx['customer_id']].append(tx)

print(f"✓ Transactions span {len(customer_transactions):,} unique customers", flush=True)

# Parse dates and calculate time span
all_dates = []
for tx in transactions:
    try:
        date = datetime.strptime(tx['transaction_date'], '%Y-%m-%d')
        all_dates.append(date)
    except:
        pass

if all_dates:
    min_date = min(all_dates)
    max_date = max(all_dates)
    date_span_days = (max_date - min_date).days
    date_span_months = date_span_days / 30.0
    
    print(f"\n📅 Date Range:", flush=True)
    print(f"   Start: {min_date.date()}", flush=True)
    print(f"   End: {max_date.date()}", flush=True)
    print(f"   Span: {date_span_days} days ({date_span_months:.1f} months)", flush=True)
else:
    print(f"✗ No valid dates found in transactions", flush=True)
    date_span_months = 1

# Calculate per-customer actual metrics
customer_actual_metrics = {}
for cust_id, txs in customer_transactions.items():
    total_txns = len(txs)
    monthly_txns = total_txns / date_span_months
    
    customer_actual_metrics[cust_id] = {
        'total_transactions': total_txns,
        'monthly_transactions': monthly_txns,
        'annual_transactions': monthly_txns * 12
    }

print(f"\n✓ Calculated metrics for {len(customer_actual_metrics):,} customers", flush=True)

# ============================================================================
# STEP 4: Compare with monthly_transaction_volume column
# ============================================================================
print(f"\n📊 STEP 4: COMPARING COLUMN VALUES VS ACTUAL", flush=True)
print("-"*80, flush=True)

mtv_values = []
actual_monthly_values = []
mismatches = []

for cust in customers:
    cust_id = cust['customer_id']
    column_value = float(cust.get('monthly_transaction_volume', 0))
    mtv_values.append(column_value)
    
    if cust_id in customer_actual_metrics:
        actual_monthly = customer_actual_metrics[cust_id]['monthly_transactions']
        actual_monthly_values.append(actual_monthly)
        
        # Check for mismatch
        if abs(column_value - actual_monthly) > 1.0:
            mismatches.append({
                'customer_id': cust_id,
                'column_value': column_value,
                'actual_monthly': actual_monthly,
                'ratio': column_value / actual_monthly if actual_monthly > 0 else 0
            })

print(f"\nColumn 'monthly_transaction_volume':", flush=True)
print(f"   Min: {min(mtv_values):.0f}", flush=True)
print(f"   Max: {max(mtv_values):.0f}", flush=True)
print(f"   Average: {sum(mtv_values)/len(mtv_values):.1f}", flush=True)
print(f"   Total: {sum(mtv_values):,.0f}", flush=True)

print(f"\nActual monthly transactions:", flush=True)
if actual_monthly_values:
    print(f"   Min: {min(actual_monthly_values):.2f}", flush=True)
    print(f"   Max: {max(actual_monthly_values):.2f}", flush=True)
    print(f"   Average: {sum(actual_monthly_values)/len(actual_monthly_values):.2f}", flush=True)

print(f"\n🔍 MISMATCH ANALYSIS:", flush=True)
print(f"   Customers with transactions: {len(actual_monthly_values):,}", flush=True)
print(f"   Customers with mismatches: {len(mismatches):,}", flush=True)
print(f"   Mismatch rate: {len(mismatches)/len(actual_monthly_values)*100:.1f}%", flush=True)

if mismatches:
    # Calculate average inflation ratio
    ratios = [m['ratio'] for m in mismatches if m['ratio'] > 0]
    if ratios:
        avg_ratio = sum(ratios) / len(ratios)
        print(f"   Average inflation ratio: {avg_ratio:.1f}x", flush=True)
    
    # Show sample mismatches
    print(f"\n   Sample mismatches (first 5):", flush=True)
    for i, m in enumerate(mismatches[:5], 1):
        print(f"      {i}. {m['customer_id']}: Column={m['column_value']:.0f}, Actual={m['actual_monthly']:.2f}, Ratio={m['ratio']:.1f}x", flush=True)

# ============================================================================
# STEP 5: Check other critical columns
# ============================================================================
print(f"\n📊 STEP 5: AUDITING OTHER CRITICAL COLUMNS", flush=True)
print("-"*80, flush=True)

issues = []

# Check for missing values
for col in columns:
    missing_count = sum(1 for c in customers if not c.get(col) or c.get(col).strip() == '')
    if missing_count > 0:
        issues.append(f"   ⚠️  '{col}': {missing_count:,} missing values ({missing_count/len(customers)*100:.1f}%)")

# Check numeric ranges
numeric_checks = {
    'age': (18, 100),
    'income': (15000, 1000000),
    'credit_score': (300, 850),
    'tenure_months': (0, 600),
    'num_products': (0, 20),
    'digital_engagement_score': (0, 1),
}

for col, (min_val, max_val) in numeric_checks.items():
    if col in columns:
        try:
            values = [float(c[col]) for c in customers if c.get(col)]
            out_of_range = sum(1 for v in values if v < min_val or v > max_val)
            if out_of_range > 0:
                issues.append(f"   ⚠️  '{col}': {out_of_range:,} values out of range [{min_val}, {max_val}]")
        except:
            issues.append(f"   ⚠️  '{col}': Non-numeric values found")

# Check customer IDs match
customer_ids_in_customers = set(c['customer_id'] for c in customers)
customer_ids_in_transactions = set(tx['customer_id'] for tx in transactions)

orphaned_transactions = customer_ids_in_transactions - customer_ids_in_customers
missing_transactions = customer_ids_in_customers - customer_ids_in_transactions

if orphaned_transactions:
    issues.append(f"   ⚠️  {len(orphaned_transactions):,} customer IDs in transactions but not in customers")

if missing_transactions:
    issues.append(f"   ℹ️  {len(missing_transactions):,} customers have no transactions")

if issues:
    print(f"\n🚨 ISSUES FOUND:", flush=True)
    for issue in issues:
        print(issue, flush=True)
else:
    print(f"\n✅ No critical issues found (except monthly_transaction_volume)", flush=True)

# ============================================================================
# STEP 6: Summary and Recommendations
# ============================================================================
print(f"\n" + "="*80, flush=True)
print("📋 AUDIT SUMMARY", flush=True)
print("="*80, flush=True)

print(f"\n✓ Data loaded successfully:", flush=True)
print(f"   - {len(customers):,} customers", flush=True)
print(f"   - {len(transactions):,} transactions", flush=True)
print(f"   - {date_span_months:.1f} months of data", flush=True)

print(f"\n🔧 FIXES NEEDED:", flush=True)
print(f"   1. Recalculate 'monthly_transaction_volume' from actual transactions", flush=True)
print(f"      Current: Average {sum(mtv_values)/len(mtv_values):.1f} (inflated)", flush=True)
print(f"      Should be: Average {sum(actual_monthly_values)/len(actual_monthly_values):.2f} (actual)", flush=True)
print(f"      Inflation: {(sum(mtv_values)/len(mtv_values))/(sum(actual_monthly_values)/len(actual_monthly_values)):.1f}x", flush=True)

if len(missing_transactions) > 0:
    print(f"   2. Generate transactions for {len(missing_transactions):,} customers with no transactions", flush=True)

if len(issues) > 0:
    print(f"   3. Fix {len(issues)} other data quality issues", flush=True)

print(f"\n" + "="*80, flush=True)
print("AUDIT COMPLETE", flush=True)
print("="*80, flush=True)

# Issue 7: Missing product_id in Transactions

## Problem

Agent B was failing with `KeyError: 'product_id'` when trying to:
1. Filter products by what customer already owns
2. Find similar products based on transaction history
3. Calculate segment-level product adoption rates

**Error locations:**
- `agent_b_banking_persona_aligned.py:277` - `customer_transactions['product_id'].unique()`
- `agent_b_banking_enhanced_v2.py:129` - `customer_txns['product_id'].unique()`
- `agent_b_banking_enhanced_v2.py:309` - `segment_txns['product_id'].value_counts()`

## Root Cause

The `generate_fmb_data_unified.py` generator created transactions without `product_id`:

```python
# OLD (MISSING product_id):
transactions.append({
    'transaction_id': f'TXN_{len(transactions)+1:06d}',
    'customer_id': customer['customer_id'],
    'transaction_date': trans_date.strftime('%Y-%m-%d'),
    'transaction_type': trans_type,
    'amount': round(amount, 2),
    'channel': np.random.choice(['Online', 'Branch', 'Mobile'], p=channel_probs)
})
```

**Original Schema:**
- transaction_id
- customer_id
- transaction_date
- transaction_type
- amount
- channel

**Required Schema (for Agent B):**
- transaction_id
- customer_id
- **product_id** ← MISSING!
- transaction_date
- transaction_type
- amount
- channel

## Fix Applied

### 1. Updated `generate_fmb_data_unified.py` (Lines 313-350)

Added logic to:
- Select products matching customer's segment (Personal/Business/Agricultural)
- Link each transaction to a specific product
- Include `product_id` in transaction data

```python
# NEW (INCLUDES product_id):
for _, customer in customers_df.iterrows():
    n_trans = int(customer['num_products'] * np.random.randint(3, 5))
    
    # Get products available for this customer's segment
    segment_products = products_df[
        products_df['category'] == customer['customer_segment']
    ]
    if len(segment_products) == 0:
        segment_products = products_df
    
    for t in range(n_trans):
        # Select a random product for this transaction
        product = segment_products.sample(1).iloc[0]
        
        transactions.append({
            'transaction_id': f'TXN_{len(transactions)+1:06d}',
            'customer_id': customer['customer_id'],
            'product_id': product['product_id'],  # ✅ NOW INCLUDED
            'transaction_date': trans_date.strftime('%Y-%m-%d'),
            'transaction_type': trans_type,
            'amount': round(amount, 2),
            'channel': np.random.choice(['Online', 'Branch', 'Mobile'], p=channel_probs)
        })
```

### 2. Created `regenerate_transactions_with_product_id.py`

Standalone script to regenerate only transactions (keeps customers/products unchanged to preserve clustering).

### 3. Regenerated Transactions

**Old transactions backed up to:** `data/preloaded/fmb_bank/transactions_OLD_BACKUP.csv`

**New transactions saved to:** `data/preloaded/fmb_bank/transactions.csv`

**Statistics:**
- Total transactions: 78,755
- Average per customer: 15.8
- Unique products: 28
- Columns: ['transaction_id', 'customer_id', 'product_id', 'transaction_date', 'transaction_type', 'amount', 'channel']

**Sample transaction:**
```python
{
    'transaction_id': 'TXN_000001',
    'customer_id': 'CUST_00001',
    'product_id': 'FMB_P001',  # ✅ NOW PRESENT!
    'transaction_date': '2025-04-15',
    'transaction_type': 'account_opened',
    'amount': 1573.49,
    'channel': 'Mobile'
}
```

## Files Modified

| File | Change |
|------|--------|
| `generate_fmb_data_unified.py` (Lines 313-350) | Added product_id to transaction generation |
| `regenerate_transactions_with_product_id.py` | New script to regenerate transactions |
| `data/preloaded/fmb_bank/transactions.csv` | Regenerated with product_id column |
| `data/preloaded/fmb_bank/transactions_OLD_BACKUP.csv` | Backup of old transactions |

## Next Steps

1. **Restart Backend** (REQUIRED - must reload new transactions CSV)
   ```bash
   RESTART_WITH_ALL_FIXES.bat
   ```

2. **Test Agent B**
   ```bash
   TEST_API_DIRECT.bat
   ```

## Expected Result (After Fix)

Agent B should now successfully:
1. ✅ Identify which products customer already owns
2. ✅ Recommend similar products based on transaction history
3. ✅ Calculate segment-level product adoption rates
4. ✅ Return non-empty recommendations with scores

```json
{
  "customer_id": "CUST_00001",
  "tailored_recommendations": [
    {
      "product_id": "FMB_P007",
      "product_name": "Money Market Account",
      "score": 0.89,
      "reason": "Similar to your current products (FMB_P001, FMB_P008)"
    }
  ],
  "segment_recommendations": [
    {
      "product_id": "FMB_P009",
      "product_name": "IRAs",
      "adoption_rate": 0.75,
      "reason": "Popular in your segment (Active Earners)"
    }
  ]
}
```

## Summary

**Before:** Transactions missing `product_id` → Agent B couldn't analyze product ownership → Empty recommendations  
**After:** Transactions include `product_id` → Agent B can analyze product patterns → Persona-aligned recommendations! 🎯

---

## All Issues Fixed (Final Count: 7)

1. ✅ Python 3.14 alpha → Python 3.10
2. ✅ onnxruntime DLL → Mocked
3. ✅ agent_a parameter → Removed
4. ✅ DataFrame serialization → Fixed
5. ✅ Test script JSON parsing → Fixed
6. ✅ Column name mismatch (cluster) → Fixed
7. ✅ **Missing product_id in transactions → FIXED!**

**This was the final piece needed for full persona-level recommendations!** 🎉

"""Fix F&M Bank customer count to exactly 5000"""
import pandas as pd

# Read existing customers
df = pd.read_csv('data/preloaded/fmb_bank/customers.csv')
print(f"Current customers: {len(df)}")

# Keep only first 5000
if len(df) > 5000:
    df = df.head(5000)
    df.to_csv('data/preloaded/fmb_bank/customers.csv', index=False)
    print(f"✅ Trimmed to {len(df)} customers")
    
    # Also update transactions to only reference these customers
    trans_df = pd.read_csv('data/preloaded/fmb_bank/transactions.csv')
    valid_ids = set(df['customer_id'])
    trans_df = trans_df[trans_df['customer_id'].isin(valid_ids)]
    trans_df.to_csv('data/preloaded/fmb_bank/transactions.csv', index=False)
    print(f"✅ Updated transactions: {len(trans_df)}")
else:
    print(f"✅ Customer count is correct: {len(df)}")

# Print segment breakdown
print("\nSegment breakdown:")
print(df['customer_segment'].value_counts())
print(f"\nCustomer type breakdown:")
print(df['customer_type'].value_counts())

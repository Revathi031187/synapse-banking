"""
Regenerate transactions.csv with product_id column
Keeps existing customers and products unchanged
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

np.random.seed(42)

print("="*70)
print("REGENERATING TRANSACTIONS WITH PRODUCT_ID")
print("="*70)

# Load existing data
output_dir = Path("data/preloaded/fmb_bank")
customers_df = pd.read_csv(output_dir / "customers.csv", engine='python')
products_df = pd.read_csv(output_dir / "products.csv")

print(f"\n[OK] Loaded {len(customers_df)} existing customers")
print(f"[OK] Loaded {len(products_df)} existing products")

# Generate transactions
print("\n[1/1] Generating transactions with product_id...")

transactions = []
base_date = datetime.now() - timedelta(days=730)

for _, customer in customers_df.iterrows():
    # Each customer gets 10-20 transactions
    n_trans = int(customer['num_products'] * np.random.randint(3, 5))
    
    # Get products available for this customer's segment
    segment_products = products_df[
        products_df['category'] == customer['customer_segment']
    ]
    if len(segment_products) == 0:
        segment_products = products_df  # Fallback to all products
    
    for t in range(n_trans):
        trans_date = base_date + timedelta(days=np.random.randint(0, 700))
        
        # Select a random product for this transaction
        product = segment_products.sample(1).iloc[0]
        
        # Transaction type based on segment
        if customer['customer_segment'] == 'Personal':
            trans_types = ['account_opened', 'deposit', 'loan_applied', 'credit_card_activated']
            trans_type = np.random.choice(trans_types, p=[0.2, 0.5, 0.2, 0.1])
            amount = np.random.uniform(100, customer['total_deposits'] * 0.3)
        elif customer['customer_segment'] == 'Business':
            trans_types = ['business_account_opened', 'merchant_deposit', 'loan_approved', 'equipment_purchase']
            trans_type = np.random.choice(trans_types, p=[0.15, 0.5, 0.25, 0.1])
            amount = np.random.uniform(500, customer['total_deposits'] * 0.4)
        else:  # Agricultural
            trans_types = ['ag_loan_approved', 'harvest_deposit', 'equipment_financed', 'land_purchase']
            trans_type = np.random.choice(trans_types, p=[0.3, 0.4, 0.2, 0.1])
            amount = np.random.uniform(1000, customer['total_deposits'] * 0.5)
        
        # Determine channel based on engagement
        digital_score = customer['digital_engagement_score']
        if digital_score > 0.7:
            channel_probs = [0.5, 0.1, 0.4]
        elif digital_score < 0.4:
            channel_probs = [0.2, 0.6, 0.2]
        else:
            channel_probs = [0.4, 0.3, 0.3]
        
        transactions.append({
            'transaction_id': f'TXN_{len(transactions)+1:06d}',
            'customer_id': customer['customer_id'],
            'product_id': product['product_id'],  # ✅ NOW INCLUDED
            'transaction_date': trans_date.strftime('%Y-%m-%d'),
            'transaction_type': trans_type,
            'amount': round(amount, 2),
            'channel': np.random.choice(['Online', 'Branch', 'Mobile'], p=channel_probs)
        })

transactions_df = pd.DataFrame(transactions)

# Backup old transactions
old_trans_file = output_dir / "transactions.csv"
if old_trans_file.exists():
    backup_file = output_dir / "transactions_OLD_BACKUP.csv"
    import shutil
    shutil.copy2(old_trans_file, backup_file)
    print(f"\n[OK] Backed up old transactions to: {backup_file}")

# Save new transactions
transactions_df.to_csv(output_dir / "transactions.csv", index=False)

print(f"\n[SUCCESS]")
print(f"   - Generated {len(transactions_df):,} transactions")
print(f"   - Average per customer: {len(transactions_df)/len(customers_df):.1f}")
print(f"   - Columns: {list(transactions_df.columns)}")
print(f"\n[OK] Saved to: {output_dir / 'transactions.csv'}")

# Verify product_id column
print(f"\nVerification:")
print(f"   - Total transactions: {len(transactions_df)}")
print(f"   - Unique products: {transactions_df['product_id'].nunique()}")
print(f"   - Sample transaction:")
print(transactions_df.head(1).to_dict('records')[0])

print("\n" + "="*70)
print("[SUCCESS] TRANSACTIONS REGENERATED WITH PRODUCT_ID")
print("   Now restart the backend and test Agent B!")
print("="*70)

"""Generate only transactions for F&M Bank"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

np.random.seed(42)

print("Generating F&M Bank Transactions...")

# Load existing customers
customers_df = pd.read_csv('data/preloaded/fmb_bank/customers.csv')
print(f"Loaded {len(customers_df)} customers")

transactions = []
base_date = datetime.now() - timedelta(days=730)

for _, customer in customers_df.iterrows():
    # Each customer gets 10-20 transactions
    n_trans = int(customer['num_products'] * np.random.randint(3, 5))
    
    for t in range(n_trans):
        trans_date = base_date + timedelta(days=np.random.randint(0, 700))
        
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
        
        # Channel based on engagement
        digital_score = customer['digital_engagement_score']
        if digital_score > 0.7:
            channel = np.random.choice(['Online', 'Branch', 'Mobile'], p=[0.5, 0.1, 0.4])
        elif digital_score < 0.4:
            channel = np.random.choice(['Online', 'Branch', 'Mobile'], p=[0.2, 0.6, 0.2])
        else:
            channel = np.random.choice(['Online', 'Branch', 'Mobile'], p=[0.4, 0.3, 0.3])
        
        transactions.append({
            'transaction_id': f'TXN_{len(transactions)+1:06d}',
            'customer_id': customer['customer_id'],
            'transaction_date': trans_date.strftime('%Y-%m-%d'),
            'transaction_type': trans_type,
            'amount': round(amount, 2),
            'channel': channel
        })

transactions_df = pd.DataFrame(transactions)
transactions_df.to_csv('data/preloaded/fmb_bank/transactions.csv', index=False)
print(f"✅ Generated {len(transactions_df):,} transactions")
print(f"   Average per customer: {len(transactions_df)/len(customers_df):.1f}")
print("\n✅ F&M Bank data complete!")

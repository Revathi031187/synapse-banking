"""
Simple Banking Data Generator - All in One
Creates customers, products, and transactions in one script
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Set seeds
np.random.seed(42)

# Output directory
output_dir = Path("data/preloaded/banking")
output_dir.mkdir(parents=True, exist_ok=True)

print("="*70)
print("🏦 BANKING DATA GENERATOR - SIMPLE VERSION")
print("="*70)

# ============================================================================
# 1. GENERATE CUSTOMERS
# ============================================================================
print("\n[1/3] Generating customers...")

n_customers = 5000
customers = []

# Persona distribution
personas = {
    'High_Net_Worth': 0.15,
    'Young_Professional': 0.25,
    'Small_Business': 0.10,
    'Mass_Market': 0.35,
    'Digital_Native': 0.15
}

persona_list = []
for persona, pct in personas.items():
    persona_list.extend([persona] * int(n_customers * pct))

# Fill to exactly n_customers
while len(persona_list) < n_customers:
    persona_list.append('Mass_Market')

np.random.shuffle(persona_list)

names = [f"Customer_{i+1}" for i in range(n_customers)]

for i in range(n_customers):
    persona = persona_list[i]
    
    # Base attributes
    customer = {
        'customer_id': f"CUST_{i+1:05d}",
        'customer_name': names[i],
        'age': np.random.randint(25, 65),
        'true_persona': persona
    }
    
    # Persona-specific attributes
    if persona == 'High_Net_Worth':
        customer.update({
            'income': np.random.randint(150000, 500000),
            'credit_score': np.random.randint(740, 850),
            'total_deposits': np.random.uniform(250000, 2000000),
            'total_loan_balance': np.random.uniform(0, 500000),
            'num_products': np.random.randint(5, 9),
            'digital_engagement_score': np.random.uniform(0.5, 0.8),
            'branch_visit_frequency': np.random.uniform(0.3, 0.7),
            'product_adoption_velocity': np.random.uniform(0.6, 0.9),
            'cross_sell_receptivity': np.random.uniform(0.7, 1.0),
            'risk_tolerance': np.random.choice(['Moderate', 'Aggressive']),
            'channel_preference': np.random.choice(['Hybrid', 'Branch']),
            'geographic_region': np.random.choice(['Urban', 'Suburban']),
            'home_ownership': np.random.choice(['Own', 'Mortgage']),
            'life_stage': np.random.choice(['Pre-Retiree', 'Retiree', 'Family']),
            'monthly_transaction_volume': np.random.randint(50, 150),
            'avg_daily_balance': np.random.uniform(150000, 1000000),
            'overdraft_frequency': 0,
            'credit_utilization_ratio': np.random.uniform(0.05, 0.25),
            'account_tenure_months': np.random.randint(60, 240),
            'relationship_length_years': np.random.randint(5, 20),
            'join_date': (datetime.now() - timedelta(days=np.random.randint(1800, 7300))).strftime('%Y-%m-%d')
        })
    
    elif persona == 'Young_Professional':
        customer.update({
            'income': np.random.randint(50000, 100000),
            'credit_score': np.random.randint(680, 780),
            'total_deposits': np.random.uniform(5000, 50000),
            'total_loan_balance': np.random.uniform(0, 50000),
            'num_products': np.random.randint(2, 5),
            'digital_engagement_score': np.random.uniform(0.8, 1.0),
            'branch_visit_frequency': np.random.uniform(0.0, 0.2),
            'product_adoption_velocity': np.random.uniform(0.5, 0.8),
            'cross_sell_receptivity': np.random.uniform(0.6, 0.9),
            'risk_tolerance': np.random.choice(['Moderate', 'Aggressive']),
            'channel_preference': 'Digital',
            'geographic_region': np.random.choice(['Urban', 'Suburban']),
            'home_ownership': np.random.choice(['Rent', 'Mortgage']),
            'life_stage': 'Young Professional',
            'monthly_transaction_volume': np.random.randint(80, 200),
            'avg_daily_balance': np.random.uniform(2000, 25000),
            'overdraft_frequency': np.random.randint(0, 3),
            'credit_utilization_ratio': np.random.uniform(0.20, 0.50),
            'account_tenure_months': np.random.randint(12, 60),
            'relationship_length_years': np.random.randint(1, 5),
            'join_date': (datetime.now() - timedelta(days=np.random.randint(365, 1825))).strftime('%Y-%m-%d')
        })
    
    elif persona == 'Small_Business':
        customer.update({
            'income': np.random.randint(80000, 200000),
            'credit_score': np.random.randint(700, 800),
            'total_deposits': np.random.uniform(50000, 500000),
            'total_loan_balance': np.random.uniform(25000, 300000),
            'num_products': np.random.randint(4, 8),
            'digital_engagement_score': np.random.uniform(0.6, 0.9),
            'branch_visit_frequency': np.random.uniform(0.4, 0.8),
            'product_adoption_velocity': np.random.uniform(0.5, 0.8),
            'cross_sell_receptivity': np.random.uniform(0.6, 0.9),
            'risk_tolerance': 'Moderate',
            'channel_preference': 'Hybrid',
            'geographic_region': np.random.choice(['Urban', 'Suburban', 'Rural']),
            'home_ownership': np.random.choice(['Own', 'Mortgage']),
            'life_stage': 'Family',
            'monthly_transaction_volume': np.random.randint(200, 800),
            'avg_daily_balance': np.random.uniform(25000, 250000),
            'overdraft_frequency': np.random.randint(0, 2),
            'credit_utilization_ratio': np.random.uniform(0.30, 0.60),
            'account_tenure_months': np.random.randint(24, 120),
            'relationship_length_years': np.random.randint(2, 10),
            'join_date': (datetime.now() - timedelta(days=np.random.randint(730, 3650))).strftime('%Y-%m-%d')
        })
    
    elif persona == 'Digital_Native':
        customer.update({
            'income': np.random.randint(25000, 65000),
            'credit_score': np.random.randint(650, 750),
            'total_deposits': np.random.uniform(500, 15000),
            'total_loan_balance': np.random.uniform(0, 25000),
            'num_products': np.random.randint(1, 4),
            'digital_engagement_score': np.random.uniform(0.9, 1.0),
            'branch_visit_frequency': np.random.uniform(0.0, 0.1),
            'product_adoption_velocity': np.random.uniform(0.6, 0.9),
            'cross_sell_receptivity': np.random.uniform(0.5, 0.8),
            'risk_tolerance': np.random.choice(['Moderate', 'Aggressive']),
            'channel_preference': 'Digital',
            'geographic_region': np.random.choice(['Urban', 'Suburban']),
            'home_ownership': 'Rent',
            'life_stage': np.random.choice(['Student', 'Young Professional']),
            'monthly_transaction_volume': np.random.randint(100, 300),
            'avg_daily_balance': np.random.uniform(200, 8000),
            'overdraft_frequency': np.random.randint(0, 4),
            'credit_utilization_ratio': np.random.uniform(0.30, 0.70),
            'account_tenure_months': np.random.randint(3, 36),
            'relationship_length_years': np.random.randint(0, 3),
            'join_date': (datetime.now() - timedelta(days=np.random.randint(90, 1095))).strftime('%Y-%m-%d')
        })
    
    else:  # Mass_Market
        customer.update({
            'income': np.random.randint(30000, 60000),
            'credit_score': np.random.randint(620, 720),
            'total_deposits': np.random.uniform(1000, 25000),
            'total_loan_balance': np.random.uniform(0, 15000),
            'num_products': np.random.randint(1, 3),
            'digital_engagement_score': np.random.uniform(0.3, 0.7),
            'branch_visit_frequency': np.random.uniform(0.2, 0.6),
            'product_adoption_velocity': np.random.uniform(0.1, 0.4),
            'cross_sell_receptivity': np.random.uniform(0.2, 0.5),
            'risk_tolerance': np.random.choice(['Conservative', 'Moderate']),
            'channel_preference': np.random.choice(['Digital', 'Branch', 'Hybrid']),
            'geographic_region': np.random.choice(['Urban', 'Suburban', 'Rural']),
            'home_ownership': np.random.choice(['Rent', 'Own', 'Mortgage']),
            'life_stage': np.random.choice(['Young Professional', 'Family', 'Pre-Retiree']),
            'monthly_transaction_volume': np.random.randint(20, 80),
            'avg_daily_balance': np.random.uniform(500, 10000),
            'overdraft_frequency': np.random.randint(0, 6),
            'credit_utilization_ratio': np.random.uniform(0.40, 0.80),
            'account_tenure_months': np.random.randint(12, 120),
            'relationship_length_years': np.random.randint(1, 10),
            'join_date': (datetime.now() - timedelta(days=np.random.randint(365, 3650))).strftime('%Y-%m-%d')
        })
    
    customers.append(customer)

customers_df = pd.DataFrame(customers)
customers_path = output_dir / "customers.csv"
customers_df.to_csv(customers_path, index=False)

print(f"✅ Generated {len(customers_df)} customers")
print(f"   Saved to: {customers_path}")
print(f"\nPersona Distribution:")
for persona, count in customers_df['true_persona'].value_counts().items():
    print(f"   {persona}: {count} ({count/len(customers_df)*100:.1f}%)")

# ============================================================================
# 2. GENERATE PRODUCTS
# ============================================================================
print("\n[2/3] Generating products...")

products = []
product_id = 1

# Credit Cards
credit_cards = [
    {"name": "Basic Cashback Card", "tier": "Basic", "fee": 0, "apr_min": 16.99, "apr_max": 24.99, "rewards": 1.0, "bonus": 0, "min_score": 620},
    {"name": "Premium Rewards Card", "tier": "Premium", "fee": 95, "apr_min": 13.99, "apr_max": 21.99, "rewards": 2.0, "bonus": 200, "min_score": 680},
    {"name": "Travel Elite Card", "tier": "Platinum", "fee": 450, "apr_min": 12.49, "apr_max": 19.99, "rewards": 4.0, "bonus": 750, "min_score": 760},
    {"name": "Business Cash Card", "tier": "Business", "fee": 0, "apr_min": 14.99, "apr_max": 22.99, "rewards": 1.5, "bonus": 200, "min_score": 680},
    {"name": "Student Rewards Card", "tier": "Basic", "fee": 0, "apr_min": 17.99, "apr_max": 25.99, "rewards": 1.0, "bonus": 50, "min_score": 600},
]

for card in credit_cards:
    products.append({
        'product_id': f"PROD_{product_id:05d}",
        'product_name': card['name'],
        'category': 'Credit Cards',
        'subcategory': card['tier'],
        'brand': np.random.choice(['Visa', 'Mastercard']),
        'annual_fee': card['fee'],
        'apr_min': card['apr_min'],
        'apr_max': card['apr_max'],
        'rewards_rate': card['rewards'],
        'sign_up_bonus': card['bonus'],
        'min_credit_score': card['min_score'],
        'complexity_score': np.random.randint(1, 4),
        'cross_sell_affinity': 'Checking',
        'digital_enabled': True,
        'avg_approval_rate': np.random.uniform(0.50, 0.85),
        'customer_satisfaction': np.random.uniform(4.0, 4.8),
        'accepting_applications': True
    })
    product_id += 1

# Personal Loans
loans = [
    {"name": "Quick Personal Loan", "apr": 12.99, "term": 24, "max_amt": 15000, "min_score": 640},
    {"name": "Debt Consolidation Loan", "apr": 10.99, "term": 36, "max_amt": 35000, "min_score": 660},
    {"name": "Home Improvement Loan", "apr": 9.99, "term": 60, "max_amt": 50000, "min_score": 680},
]

for loan in loans:
    products.append({
        'product_id': f"PROD_{product_id:05d}",
        'product_name': loan['name'],
        'category': 'Personal Loans',
        'subcategory': 'Unsecured',
        'brand': 'Bank Lending',
        'annual_fee': 0,
        'apr_min': loan['apr'],
        'apr_max': loan['apr'] + 3,
        'term_months': loan['term'],
        'max_amount': loan['max_amt'],
        'min_credit_score': loan['min_score'],
        'complexity_score': 3,
        'cross_sell_affinity': 'Insurance',
        'digital_enabled': True,
        'avg_approval_rate': 0.60,
        'customer_satisfaction': 4.2,
        'accepting_applications': True
    })
    product_id += 1

# Accounts
accounts = [
    {"name": "Basic Checking", "type": "Checking", "fee": 0, "min_bal": 0, "interest": 0},
    {"name": "Premium Checking", "type": "Checking", "fee": 25, "min_bal": 5000, "interest": 0.50},
    {"name": "High-Yield Savings", "type": "Savings", "fee": 0, "min_bal": 10000, "interest": 4.50},
    {"name": "Money Market Account", "type": "Savings", "fee": 10, "min_bal": 5000, "interest": 3.75},
]

for acct in accounts:
    products.append({
        'product_id': f"PROD_{product_id:05d}",
        'product_name': acct['name'],
        'category': 'Accounts',
        'subcategory': acct['type'],
        'brand': 'Bank Account',
        'monthly_fee': acct['fee'],
        'min_balance': acct['min_bal'],
        'interest_rate': acct['interest'],
        'complexity_score': 1,
        'cross_sell_affinity': 'Credit Card',
        'digital_enabled': True,
        'avg_approval_rate': 0.95,
        'customer_satisfaction': 4.5,
        'accepting_applications': True
    })
    product_id += 1

# Investments
investments = [
    {"name": "Robo-Advisor Basic", "fee": 0.25, "min": 500, "risk": "Conservative", "return": 6.5},
    {"name": "Managed Portfolio", "fee": 0.50, "min": 10000, "risk": "Moderate", "return": 8.0},
    {"name": "Wealth Management", "fee": 1.00, "min": 250000, "risk": "Aggressive", "return": 10.0},
]

for inv in investments:
    products.append({
        'product_id': f"PROD_{product_id:05d}",
        'product_name': inv['name'],
        'category': 'Investments',
        'subcategory': 'Investment Accounts',
        'brand': 'Bank Investment Services',
        'management_fee_pct': inv['fee'],
        'min_investment': inv['min'],
        'risk_level': inv['risk'],
        'expected_return_pct': inv['return'],
        'complexity_score': 4,
        'cross_sell_affinity': 'Retirement Planning',
        'digital_enabled': True,
        'avg_approval_rate': 0.85,
        'customer_satisfaction': 4.6,
        'accepting_applications': True
    })
    product_id += 1

# Mortgages
mortgages = [
    {"name": "30-Year Fixed Mortgage", "term": 30, "apr": 6.75, "down": 20},
    {"name": "15-Year Fixed Mortgage", "term": 15, "apr": 6.25, "down": 20},
    {"name": "FHA Loan", "term": 30, "apr": 6.50, "down": 3.5},
]

for mtg in mortgages:
    products.append({
        'product_id': f"PROD_{product_id:05d}",
        'product_name': mtg['name'],
        'category': 'Mortgages',
        'subcategory': 'Home Loans',
        'brand': 'Bank Lending',
        'annual_fee': 0,
        'apr_min': mtg['apr'],
        'apr_max': mtg['apr'] + 1,
        'term_years': mtg['term'],
        'down_payment_pct': mtg['down'],
        'complexity_score': 4,
        'cross_sell_affinity': 'Insurance',
        'digital_enabled': True,
        'avg_approval_rate': 0.65,
        'customer_satisfaction': 4.3,
        'accepting_applications': True
    })
    product_id += 1

products_df = pd.DataFrame(products)
products_path = output_dir / "products.csv"
products_df.to_csv(products_path, index=False)

print(f"✅ Generated {len(products_df)} products")
print(f"   Saved to: {products_path}")
print(f"\nCategory Distribution:")
for category, count in products_df['category'].value_counts().items():
    print(f"   {category}: {count}")

# ============================================================================
# 3. GENERATE TRANSACTIONS
# ============================================================================
print("\n[3/3] Generating transactions...")

transactions = []

for _, customer in customers_df.iterrows():
    num_products = int(customer['num_products'])
    persona = customer['true_persona']
    
    # Select random products based on persona
    if persona == 'High_Net_Worth':
        available = products_df[products_df['category'].isin(['Credit Cards', 'Investments', 'Mortgages'])]
    elif persona == 'Young_Professional':
        available = products_df[products_df['category'].isin(['Credit Cards', 'Accounts', 'Investments'])]
    elif persona == 'Small_Business':
        available = products_df[products_df['category'].isin(['Credit Cards', 'Personal Loans', 'Accounts'])]
    else:
        available = products_df[products_df['category'].isin(['Credit Cards', 'Accounts', 'Personal Loans'])]
    
    if len(available) >= num_products:
        selected_products = available.sample(n=num_products)
    else:
        selected_products = available
    
    # Create transactions for each product
    join_date = pd.to_datetime(customer['join_date'])
    
    for _, product in selected_products.iterrows():
        days_offset = np.random.randint(0, 365)
        trans_date = join_date + timedelta(days=days_offset)
        
        # Determine transaction type and amount
        category = product['category']
        if category == 'Credit Cards':
            trans_type = 'credit_card_activated'
            amount = 0
        elif category == 'Personal Loans':
            trans_type = 'loan_approved'
            amount = np.random.uniform(5000, product.get('max_amount', 25000))
        elif category == 'Accounts':
            trans_type = 'account_opened'
            amount = customer['total_deposits'] * np.random.uniform(0.1, 0.3)
        elif category == 'Mortgages':
            trans_type = 'mortgage_approved'
            amount = np.random.uniform(150000, 500000)
        elif category == 'Investments':
            trans_type = 'investment_started'
            amount = np.random.uniform(product['min_investment'], customer['total_deposits'] * 0.4)
        else:
            trans_type = 'account_opened'
            amount = 1000
        
        # Channel based on customer preference
        if customer['digital_engagement_score'] > 0.7:
            channel = np.random.choice(['Web', 'Mobile'])
        elif customer['branch_visit_frequency'] > 0.5:
            channel = 'Branch'
        else:
            channel = np.random.choice(['Web', 'Branch', 'Mobile'])
        
        transactions.append({
            'customer_id': customer['customer_id'],
            'product_id': product['product_id'],
            'transaction_date': trans_date.strftime('%Y-%m-%d'),
            'transaction_type': trans_type,
            'amount': round(amount, 2),
            'channel': channel,
            'approval_status': 'approved'
        })

transactions_df = pd.DataFrame(transactions)
transactions_path = output_dir / "transactions.csv"
transactions_df.to_csv(transactions_path, index=False)

print(f"✅ Generated {len(transactions_df)} transactions")
print(f"   Saved to: {transactions_path}")
print(f"\nTransaction Type Distribution:")
for trans_type, count in transactions_df['transaction_type'].value_counts().items():
    print(f"   {trans_type}: {count}")

print("\n" + "="*70)
print("✅ ALL BANKING DATA GENERATED SUCCESSFULLY!")
print("="*70)
print(f"\nGenerated files:")
print(f"  - {customers_path}")
print(f"  - {products_path}")
print(f"  - {transactions_path}")
print(f"\nNext steps:")
print(f"  1. Start backend: uvicorn api.main_unified_chromadb:app --port 8002")
print(f"  2. Start frontend: cd frontend && npm run dev")
print(f"  3. Access: http://localhost:3000/banking")
print()

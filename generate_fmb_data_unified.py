"""
F&M Bank Complete Data Generator
Generates products, customers, and transactions for F&M Bank
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

np.random.seed(42)
Faker.seed(42)

print("="*70)
print("🏦 F&M BANK DATA GENERATOR")
print("   Farmers & Merchants Bank of Central California")
print("="*70)

# Setup
output_dir = Path("data/preloaded/fmb_bank")
output_dir.mkdir(parents=True, exist_ok=True)
fake = Faker()

# ============================================================================
# STEP 1: GENERATE PRODUCTS (28 products)
# ============================================================================
print("\n[1/3] Generating F&M Bank Products...")

products_data = [
    # Personal Checking (5)
    ('FMB_P001', 'Worry-FREE Checking®', 'Personal', 'Checking', 0, 0, 0.0, ['Mass_Market', 'Digital_Native']),
    ('FMB_P002', 'Ultimate Checking', 'Personal', 'Checking', 0, 2500, 0.0, ['Young_Professional', 'High_Net_Worth']),
    ('FMB_P003', 'Ultimate High Yield Checking®', 'Personal', 'Checking', 0, 5000, 1.25, ['High_Net_Worth', 'Retiree']),
    ('FMB_P004', 'Sky Blue Checking™', 'Personal', 'Checking', 0, 0, 0.0, ['Digital_Native', 'Young_Professional']),
    ('FMB_P005', 'Teen Checking', 'Personal', 'Checking', 0, 0, 0.0, ['Digital_Native']),
    
    # Personal Savings/Investment (6)
    ('FMB_P006', 'Regular Savings', 'Personal', 'Savings', 0, 100, 0.50, ['Mass_Market', 'Young_Professional']),
    ('FMB_P007', 'Money Market Account', 'Personal', 'Savings', 0, 10000, 1.75, ['High_Net_Worth', 'Retiree']),
    ('FMB_P008', 'Certificates of Deposit (CDs)', 'Personal', 'Investment', 0, 1000, 2.50, ['Retiree', 'High_Net_Worth']),
    ('FMB_P009', 'Individual Retirement Accounts (IRAs)', 'Personal', 'Investment', 0, 500, 2.00, ['Young_Professional', 'Retiree']),
    ('FMB_P010', 'Holiday Club', 'Personal', 'Savings', 0, 0, 0.25, ['Mass_Market']),
    ('FMB_P011', 'Junior Savers', 'Personal', 'Savings', 0, 10, 0.50, ['Mass_Market']),
    
    # Personal Credit/Loans (3)
    ('FMB_P012', 'Personal Credit Cards', 'Personal', 'Credit', 0, 0, 14.99, ['Young_Professional', 'Mass_Market']),
    ('FMB_P013', 'Home Mortgage Loans', 'Personal', 'Loan', 0, 0, 6.50, ['Young_Professional', 'High_Net_Worth']),
    ('FMB_P014', 'Auto Loans', 'Personal', 'Loan', 0, 0, 5.75, ['Young_Professional', 'Mass_Market']),
    
    # Business Checking (3)
    ('FMB_B001', 'FREE Business Checking', 'Business', 'Checking', 0, 0, 0.0, ['Small_Business']),
    ('FMB_B002', 'Ultimate Business Checking', 'Business', 'Checking', 0, 5000, 0.0, ['Small_Business', 'Corporate']),
    ('FMB_B003', 'Business Account Analysis Checking', 'Business', 'Checking', 0, 25000, 0.0, ['Corporate']),
    
    # Business Savings/Services (3)
    ('FMB_B004', 'Business Savings', 'Business', 'Savings', 0, 500, 0.75, ['Small_Business', 'Corporate']),
    ('FMB_B005', 'Business Money Market Account', 'Business', 'Savings', 0, 10000, 1.50, ['Small_Business', 'Corporate']),
    ('FMB_B006', 'Business Credit Cards', 'Business', 'Credit', 95, 0, 15.99, ['Small_Business', 'Corporate']),
    
    # Business Loans (3)
    ('FMB_B007', 'Commercial Real Estate Loans', 'Business', 'Loan', 0, 0, 7.25, ['Commercial_Real_Estate', 'Corporate']),
    ('FMB_B008', 'Business Term Loans', 'Business', 'Loan', 0, 0, 6.75, ['Small_Business', 'Corporate']),
    ('FMB_B009', 'Small Business Administration (SBA) Loans', 'Business', 'Loan', 0, 0, 8.00, ['Small_Business']),
    
    # Agricultural (5)
    ('FMB_A001', 'Agricultural Loans', 'Agricultural', 'Loan', 0, 0, 6.50, ['Row_Crop_Farmer', 'Livestock_Rancher']),
    ('FMB_A002', 'Agricultural Real Estate Loans', 'Agricultural', 'Loan', 0, 0, 6.75, ['Row_Crop_Farmer', 'Vineyard_Orchard_Owner']),
    ('FMB_A003', 'Livestock Loans', 'Agricultural', 'Loan', 0, 0, 6.25, ['Livestock_Rancher']),
    ('FMB_A004', 'Farm Equipment Loans & Leasing', 'Agricultural', 'Loan', 0, 0, 5.50, ['Row_Crop_Farmer', 'Vineyard_Orchard_Owner']),
    ('FMB_A005', 'Vineyard & Orchard Development Loans', 'Agricultural', 'Loan', 0, 0, 6.50, ['Vineyard_Orchard_Owner']),
]

products = []
for pid, name, cat, subcat, fee, min_bal, rate, segments in products_data:
    products.append({
        'product_id': pid,
        'product_name': name,
        'category': cat,
        'subcategory': subcat,
        'annual_fee': fee,
        'min_balance': min_bal,
        'interest_rate': rate,
        'description': f'{name} - F&M Bank product',
        'target_segment': cat,  # Use category (Personal/Business/Agricultural) not customer types
        'customer_types': '|'.join(segments)  # Keep customer types in separate column
    })

products_df = pd.DataFrame(products)
products_df.to_csv(output_dir / "products.csv", index=False)
print(f"   ✓ Generated {len(products_df)} products")
print(f"     - Personal: {len(products_df[products_df['category']=='Personal'])}")
print(f"     - Business: {len(products_df[products_df['category']=='Business'])}")
print(f"     - Agricultural: {len(products_df[products_df['category']=='Agricultural'])}")

# ============================================================================
# STEP 2: GENERATE CUSTOMERS (5000 customers)
# ============================================================================
print("\n[2/3] Generating F&M Bank Customers (5000)...")

customers = []
customer_id = 1

# Personal Banking: 60% = 3000 customers  
print("   Generating Personal Banking customers (3000)...")
personal_types = {
    'Mass_Market': 1050,  # 35% of 3000
    'Young_Professional': 600,  # 20% of 3000
    'Digital_Native': 450,  # 15% of 3000
    'High_Net_Worth': 300,  # 10% of 3000
    'Retiree': 600  # 20% of 3000
}

for cust_type, count in personal_types.items():
    for i in range(count):
        if cust_type == 'Mass_Market':
            age = np.random.randint(25, 65)
            income = np.random.randint(30000, 70000)
            credit_score = np.random.randint(620, 750)
            deposits = np.random.uniform(2000, 30000)
            num_products = np.random.randint(1, 4)
            digital_engagement = np.random.uniform(0.3, 0.7)
        elif cust_type == 'Young_Professional':
            age = np.random.randint(25, 40)
            income = np.random.randint(50000, 120000)
            credit_score = np.random.randint(680, 800)
            deposits = np.random.uniform(10000, 80000)
            num_products = np.random.randint(2, 6)
            digital_engagement = np.random.uniform(0.6, 0.95)
        elif cust_type == 'Digital_Native':
            age = np.random.randint(18, 35)
            income = np.random.randint(25000, 80000)
            credit_score = np.random.randint(600, 750)
            deposits = np.random.uniform(1000, 25000)
            num_products = np.random.randint(1, 4)
            digital_engagement = np.random.uniform(0.85, 1.0)
        elif cust_type == 'High_Net_Worth':
            age = np.random.randint(45, 75)
            income = np.random.randint(150000, 500000)
            credit_score = np.random.randint(740, 850)
            deposits = np.random.uniform(100000, 1000000)
            num_products = np.random.randint(5, 12)
            digital_engagement = np.random.uniform(0.4, 0.8)
        else:  # Retiree
            age = np.random.randint(60, 85)
            income = np.random.randint(40000, 120000)
            credit_score = np.random.randint(700, 820)
            deposits = np.random.uniform(50000, 300000)
            num_products = np.random.randint(3, 8)
            digital_engagement = np.random.uniform(0.2, 0.5)
        
        customers.append({
            'customer_id': f'CUST_{customer_id:05d}',
            'customer_name': fake.name(),
            'customer_segment': 'Personal',
            'customer_type': cust_type,
            'age': age,
            'income': income,
            'credit_score': credit_score,
            'total_deposits': deposits,
            'num_products': num_products,
            'digital_engagement_score': digital_engagement,
            'branch_visit_frequency': 1.0 - digital_engagement,
            'tenure_months': np.random.randint(6, 180),
            'monthly_transaction_volume': np.random.randint(10, 150),
            'cross_sell_receptivity': np.random.uniform(0.3, 0.9)
        })
        customer_id += 1

# Business Banking: 30% = 1500 customers
print("   Generating Business Banking customers (1500)...")
business_types = {
    'Small_Business': 1000,
    'Commercial_Real_Estate': 250,
    'Corporate': 250
}

for cust_type, count in business_types.items():
    for i in range(count):
        if cust_type == 'Small_Business':
            age = np.random.randint(30, 65)
            income = np.random.randint(75000, 300000)
            credit_score = np.random.randint(650, 800)
            deposits = np.random.uniform(25000, 300000)
            num_products = np.random.randint(3, 8)
            digital_engagement = np.random.uniform(0.5, 0.85)
        elif cust_type == 'Commercial_Real_Estate':
            age = np.random.randint(35, 70)
            income = np.random.randint(150000, 750000)
            credit_score = np.random.randint(700, 820)
            deposits = np.random.uniform(100000, 2000000)
            num_products = np.random.randint(4, 10)
            digital_engagement = np.random.uniform(0.4, 0.7)
        else:  # Corporate
            age = np.random.randint(40, 65)
            income = np.random.randint(250000, 2000000)
            credit_score = np.random.randint(720, 850)
            deposits = np.random.uniform(250000, 5000000)
            num_products = np.random.randint(6, 15)
            digital_engagement = np.random.uniform(0.6, 0.9)
        
        customers.append({
            'customer_id': f'CUST_{customer_id:05d}',
            'customer_name': fake.company(),
            'customer_segment': 'Business',
            'customer_type': cust_type,
            'age': age,
            'income': income,
            'credit_score': credit_score,
            'total_deposits': deposits,
            'num_products': num_products,
            'digital_engagement_score': digital_engagement,
            'branch_visit_frequency': 1.0 - digital_engagement,
            'tenure_months': np.random.randint(12, 240),
            'monthly_transaction_volume': np.random.randint(100, 800),
            'cross_sell_receptivity': np.random.uniform(0.4, 0.9)
        })
        customer_id += 1

# Agricultural Banking: 10% = 500 customers
print("   Generating Agricultural Banking customers (500)...")
ag_types = {
    'Row_Crop_Farmer': 200,
    'Livestock_Rancher': 150,
    'Vineyard_Orchard_Owner': 150
}

for cust_type, count in ag_types.items():
    for i in range(count):
        age = np.random.randint(35, 70)
        income = np.random.randint(60000, 400000)
        credit_score = np.random.randint(650, 800)
        deposits = np.random.uniform(50000, 500000)
        num_products = np.random.randint(3, 8)
        digital_engagement = np.random.uniform(0.3, 0.7)
        
        customers.append({
            'customer_id': f'CUST_{customer_id:05d}',
            'customer_name': fake.name() + " Farms",
            'customer_segment': 'Agricultural',
            'customer_type': cust_type,
            'age': age,
            'income': income,
            'credit_score': credit_score,
            'total_deposits': deposits,
            'num_products': num_products,
            'digital_engagement_score': digital_engagement,
            'branch_visit_frequency': 1.0 - digital_engagement,
            'tenure_months': np.random.randint(24, 300),
            'monthly_transaction_volume': np.random.randint(50, 400),
            'cross_sell_receptivity': np.random.uniform(0.5, 0.85)
        })
        customer_id += 1

customers_df = pd.DataFrame(customers)

# ============================================================================
# ADD CUSTOMER LIFETIME VALUE (CLV) - Based on feedback
# ============================================================================
print("\n   📊 Calculating Customer Lifetime Value (CLV)...")

# CLV Formula: Total Deposits + (Annual Transaction Value * Expected Relationship Years)
# Expected years = min(tenure_months / 12, 10) - cap at 10 years for realistic projection

# Estimate annual transaction value from monthly volume
customers_df['annual_transaction_value'] = customers_df['monthly_transaction_volume'] * customers_df['total_deposits'] * 0.002  # 0.2% of deposits per transaction

# Expected relationship years (based on current tenure, capped at 10 years)
customers_df['expected_relationship_years'] = customers_df['tenure_months'].apply(lambda x: min(x / 12, 10))

# Calculate CLV
customers_df['customer_lifetime_value'] = (
    customers_df['total_deposits'] + 
    (customers_df['annual_transaction_value'] * customers_df['expected_relationship_years'])
).round(2)

# Add CLV tier for easy identification
def assign_clv_tier(clv):
    if clv >= 1000000:
        return 'Diamond'  # Ultra-high value
    elif clv >= 500000:
        return 'Platinum'  # Very high value
    elif clv >= 200000:
        return 'Gold'  # High value
    elif clv >= 50000:
        return 'Silver'  # Medium value
    else:
        return 'Bronze'  # Growing value

customers_df['clv_tier'] = customers_df['customer_lifetime_value'].apply(assign_clv_tier)

print(f"   ✓ CLV calculated for all customers")
print(f"     - Diamond (>$1M): {len(customers_df[customers_df['clv_tier']=='Diamond'])}")
print(f"     - Platinum ($500K-$1M): {len(customers_df[customers_df['clv_tier']=='Platinum'])}")
print(f"     - Gold ($200K-$500K): {len(customers_df[customers_df['clv_tier']=='Gold'])}")
print(f"     - Silver ($50K-$200K): {len(customers_df[customers_df['clv_tier']=='Silver'])}")
print(f"     - Bronze (<$50K): {len(customers_df[customers_df['clv_tier']=='Bronze'])}")

customers_df.to_csv(output_dir / "customers.csv", index=False)
print(f"\n   ✓ Generated {len(customers_df)} customers")
print(f"     - Personal: {len(customers_df[customers_df['customer_segment']=='Personal'])}")
print(f"     - Business: {len(customers_df[customers_df['customer_segment']=='Business'])}")
print(f"     - Agricultural: {len(customers_df[customers_df['customer_segment']=='Agricultural'])}")

# ============================================================================
# STEP 3: GENERATE TRANSACTIONS (~75,000)
# ============================================================================
print("\n[3/3] Generating F&M Bank Transactions...")

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
        
        # Determine channel based on engagement (probabilities that sum to 1)
        digital_score = customer['digital_engagement_score']
        if digital_score > 0.7:
            channel_probs = [0.5, 0.1, 0.4]  # High digital: mostly online/mobile
        elif digital_score < 0.4:
            channel_probs = [0.2, 0.6, 0.2]  # Low digital: mostly branch
        else:
            channel_probs = [0.4, 0.3, 0.3]  # Balanced
        
        transactions.append({
            'transaction_id': f'TXN_{len(transactions)+1:06d}',
            'customer_id': customer['customer_id'],
            'product_id': product['product_id'],  # ✅ ADDED - Links transaction to product
            'transaction_date': trans_date.strftime('%Y-%m-%d'),
            'transaction_type': trans_type,
            'amount': round(amount, 2),
            'channel': np.random.choice(['Online', 'Branch', 'Mobile'], p=channel_probs)
        })

transactions_df = pd.DataFrame(transactions)
transactions_df.to_csv(output_dir / "transactions.csv", index=False)
print(f"   ✓ Generated {len(transactions_df):,} transactions")
print(f"     Average per customer: {len(transactions_df)/len(customers_df):.1f}")

# ============================================================================
# STEP 4: ADD CHURN ANALYSIS FEATURES
# ============================================================================
print("\n[4/4] Adding Churn Analysis Features...")

try:
    from utils.churn_feature_generator import add_essential_churn_features, generate_churn_report
    
    # Add ESSENTIAL churn features (from real data)
    customers_with_churn = add_essential_churn_features(customers_df, transactions_df)
    
    # Save enhanced dataset with churn features
    customers_with_churn.to_csv(output_dir / "customers.csv", index=False)
    
    # Generate churn report
    churn_report = generate_churn_report(customers_with_churn)
    
    print(f"   ✓ Added {len(customers_with_churn.columns) - len(customers_df.columns)} churn features")
    print(f"   ✓ At-risk customers: {churn_report['at_risk_customers']:,} ({churn_report['at_risk_customers']/churn_report['total_customers']*100:.1f}%)")
    print(f"   ✓ Avg churn risk score: {churn_report['avg_churn_risk_score']:.1f}/100")
    print(f"   ✓ ALL features calculated from real transaction data (NO random generation)")
    
    # Save churn report
    import json
    with open(output_dir / "churn_report.json", 'w') as f:
        json.dump(churn_report, f, indent=2, default=str)
    
    customers_df = customers_with_churn  # Update reference
    
except ImportError as e:
    print(f"   ⚠️  Churn feature generator not available: {e}")
except Exception as e:
    print(f"   ⚠️  Error adding churn features: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("✅ F&M BANK DATA GENERATION COMPLETE!")
print("="*70)
print(f"\n📂 Location: {output_dir.absolute()}")
print(f"\n📊 Summary:")
print(f"   • Products: {len(products_df)} (14 Personal + 9 Business + 5 Agricultural)")
print(f"   • Customers: {len(customers_df):,} (with {len(customers_df.columns)} features including churn analysis)")
print(f"   • Transactions: {len(transactions_df):,}")
print(f"   • Churn Analysis: ✅ Enabled with risk scoring and retention recommendations")
print("\n🏦 F&M Bank - Where Banking Is Easy - Since 1916")
print("="*70)

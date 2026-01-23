"""
Banking Synthetic Data Generator
Generates realistic banking data matching the Ms. X user story scenario
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import os

# Ensure data directory exists
os.makedirs('data/preloaded/banking_nba', exist_ok=True)

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_CUSTOMERS = 100
START_DATE = datetime.now() - timedelta(days=730)  # 2 years of data
CURRENT_DATE = datetime.now()


# ============================================================================
# 1. CUSTOMERS
# ============================================================================
def generate_customers():
    """Generate customer demographic data"""
    print("📊 Generating customers...")
    
    customers = []
    for i in range(NUM_CUSTOMERS):
        customer_id = f"CUST{str(i+1).zfill(6)}"
        
        # Ms. X is customer ID CUST000001
        if i == 0:
            # Ms. X profile
            customer = {
                'customer_id': customer_id,
                'first_name': 'Sarah',
                'last_name': 'Martinez',
                'age': 32,
                'gender': 'Female',
                'income_band': 'High',  # Increased income
                'employment_status': 'Employed',
                'marital_status': 'Single',
                'has_children': False,
                'num_children': 0,
                'household_size': 1,
                'education_level': 'Master',
                'city': 'Austin',
                'state': 'TX',
                'zip_code': '78701',
                'customer_since': (CURRENT_DATE - timedelta(days=4*365)).date(),  # 4 years
                'tenure_months': 48,
                'customer_segment': 'Affluent',
                'risk_score': 15.5,  # Low risk
                'lifetime_value': 45000.00,
                'created_at': CURRENT_DATE - timedelta(days=4*365),
                'updated_at': CURRENT_DATE
            }
        else:
            # Other customers
            age = np.random.choice([25, 30, 35, 40, 45, 50, 55, 60, 65], p=[0.1, 0.15, 0.15, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05])
            tenure_days = np.random.randint(180, 3650)
            
            customer = {
                'customer_id': customer_id,
                'first_name': random.choice(['John', 'Jane', 'Michael', 'Emily', 'David', 'Lisa', 'Robert', 'Maria']),
                'last_name': random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']),
                'age': age,
                'gender': random.choice(['Male', 'Female']),
                'income_band': np.random.choice(['Low', 'Medium', 'High', 'Very High'], p=[0.2, 0.4, 0.3, 0.1]),
                'employment_status': np.random.choice(['Employed', 'Self-Employed', 'Unemployed', 'Retired'], p=[0.7, 0.15, 0.05, 0.1]),
                'marital_status': np.random.choice(['Single', 'Married', 'Divorced', 'Widowed'], p=[0.3, 0.5, 0.15, 0.05]),
                'has_children': random.choice([True, False]),
                'num_children': np.random.choice([0, 1, 2, 3], p=[0.4, 0.3, 0.2, 0.1]),
                'household_size': np.random.randint(1, 6),
                'education_level': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], p=[0.3, 0.4, 0.25, 0.05]),
                'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego']),
                'state': random.choice(['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA']),
                'zip_code': str(np.random.randint(10000, 99999)),
                'customer_since': (CURRENT_DATE - timedelta(days=tenure_days)).date(),
                'tenure_months': tenure_days // 30,
                'customer_segment': np.random.choice(['Mass Market', 'Affluent', 'Student', 'Senior'], p=[0.5, 0.25, 0.15, 0.1]),
                'risk_score': round(np.random.uniform(10, 80), 2),
                'lifetime_value': round(np.random.uniform(5000, 100000), 2),
                'created_at': CURRENT_DATE - timedelta(days=tenure_days),
                'updated_at': CURRENT_DATE
            }
        
        customers.append(customer)
    
    df = pd.DataFrame(customers)
    df.to_csv('data/preloaded/banking_nba/customers.csv', index=False)
    print(f"✅ Generated {len(df)} customers")
    return df


# ============================================================================
# 2. ACCOUNTS
# ============================================================================
def generate_accounts(customers_df):
    """Generate customer accounts"""
    print("📊 Generating accounts...")
    
    accounts = []
    account_counter = 1
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        customer_since = pd.to_datetime(customer['customer_since'])
        
        # Ms. X has checking + credit card
        if customer_id == 'CUST000001':
            # Checking account
            accounts.append({
                'account_id': f"ACC{str(account_counter).zfill(8)}",
                'customer_id': customer_id,
                'account_type': 'Checking',
                'account_status': 'Active',
                'account_opened_date': customer_since.date(),
                'current_balance': 12500.00,
                'available_balance': 12500.00,
                'credit_limit': None,
                'interest_rate': 0.01,
                'minimum_balance': 500.00,
                'monthly_fee': 0.00,
                'account_age_months': 48,
                'last_transaction_date': CURRENT_DATE.date(),
                'transaction_count_30d': 45,
                'created_at': customer_since
            })
            account_counter += 1
            
            # Credit card
            accounts.append({
                'account_id': f"ACC{str(account_counter).zfill(8)}",
                'customer_id': customer_id,
                'account_type': 'Credit Card',
                'account_status': 'Active',
                'account_opened_date': customer_since.date(),
                'current_balance': 2100.00,
                'available_balance': 7900.00,
                'credit_limit': 10000.00,
                'interest_rate': 18.99,
                'minimum_balance': None,
                'monthly_fee': 0.00,
                'account_age_months': 48,
                'last_transaction_date': CURRENT_DATE.date(),
                'transaction_count_30d': 28,
                'created_at': customer_since
            })
            account_counter += 1
        else:
            # Other customers: 1-3 accounts
            num_accounts = np.random.randint(1, 4)
            account_types = np.random.choice(
                ['Checking', 'Savings', 'Credit Card', 'Auto Loan'], 
                size=num_accounts, 
                replace=False
            )
            
            for acc_type in account_types:
                opened_date = customer_since + timedelta(days=np.random.randint(0, 365))
                
                if acc_type == 'Credit Card':
                    credit_limit = np.random.choice([5000, 7500, 10000, 15000, 25000])
                    balance = round(np.random.uniform(0, credit_limit * 0.5), 2)
                    accounts.append({
                        'account_id': f"ACC{str(account_counter).zfill(8)}",
                        'customer_id': customer_id,
                        'account_type': acc_type,
                        'account_status': 'Active',
                        'account_opened_date': opened_date.date(),
                        'current_balance': balance,
                        'available_balance': credit_limit - balance,
                        'credit_limit': credit_limit,
                        'interest_rate': round(np.random.uniform(15.99, 24.99), 2),
                        'minimum_balance': None,
                        'monthly_fee': 0.00,
                        'account_age_months': ((CURRENT_DATE - opened_date).days // 30),
                        'last_transaction_date': (CURRENT_DATE - timedelta(days=np.random.randint(0, 30))).date(),
                        'transaction_count_30d': np.random.randint(10, 50),
                        'created_at': opened_date
                    })
                else:
                    balance = round(np.random.uniform(500, 50000), 2)
                    accounts.append({
                        'account_id': f"ACC{str(account_counter).zfill(8)}",
                        'customer_id': customer_id,
                        'account_type': acc_type,
                        'account_status': 'Active',
                        'account_opened_date': opened_date.date(),
                        'current_balance': balance,
                        'available_balance': balance,
                        'credit_limit': None,
                        'interest_rate': round(np.random.uniform(0.01, 2.5), 2) if acc_type == 'Savings' else None,
                        'minimum_balance': 500.00 if acc_type == 'Checking' else None,
                        'monthly_fee': np.random.choice([0, 5, 10, 15]),
                        'account_age_months': ((CURRENT_DATE - opened_date).days // 30),
                        'last_transaction_date': (CURRENT_DATE - timedelta(days=np.random.randint(0, 30))).date(),
                        'transaction_count_30d': np.random.randint(5, 40),
                        'created_at': opened_date
                    })
                
                account_counter += 1
    
    df = pd.DataFrame(accounts)
    df.to_csv('data/preloaded/banking_nba/accounts.csv', index=False)
    print(f"✅ Generated {len(df)} accounts")
    return df


# ============================================================================
# 3. TRANSACTIONS
# ============================================================================
def generate_transactions(customers_df, accounts_df):
    """Generate transaction history with merchant categories"""
    print("📊 Generating transactions...")
    
    transactions = []
    transaction_counter = 1
    
    # Merchant categories for life event detection
    merchant_categories = {
        'Groceries': ['Whole Foods', 'Trader Joes', 'Kroger', 'Walmart'],
        'Furniture': ['IKEA', 'Ashley Furniture', 'Wayfair', 'West Elm'],
        'Home Improvement': ['Home Depot', 'Lowes', 'Ace Hardware'],
        'Baby Products': ['Buy Buy Baby', 'Target Baby', 'Amazon Baby'],
        'Travel': ['United Airlines', 'Marriott', 'Expedia', 'Airbnb'],
        'Dining': ['Chipotle', 'Starbucks', 'McDonalds', 'Local Restaurant'],
        'Gas': ['Shell', 'Chevron', 'BP', 'Exxon'],
        'Healthcare': ['CVS Pharmacy', 'Walgreens', 'Medical Center'],
        'Entertainment': ['Netflix', 'Spotify', 'AMC Theaters']
    }
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        customer_accounts = accounts_df[accounts_df['customer_id'] == customer_id]
        
        if len(customer_accounts) == 0:
            continue
        
        # Ms. X special scenario: increased furniture and home improvement in last 30 days
        if customer_id == 'CUST000001':
            checking_acc = customer_accounts[customer_accounts['account_type'] == 'Checking'].iloc[0]['account_id']
            
            # Last 60 days: normal transactions
            for day in range(60, 30, -1):
                trans_date = CURRENT_DATE - timedelta(days=day)
                category = np.random.choice(['Groceries', 'Dining', 'Gas', 'Entertainment'])
                merchant = random.choice(merchant_categories[category])
                
                transactions.append({
                    'transaction_id': f"TXN{str(transaction_counter).zfill(10)}",
                    'customer_id': customer_id,
                    'account_id': checking_acc,
                    'transaction_date': trans_date,
                    'transaction_type': 'Debit',
                    'amount': round(np.random.uniform(20, 150), 2),
                    'merchant_name': merchant,
                    'merchant_category': category,
                    'merchant_category_code': str(np.random.randint(5000, 9999)),
                    'transaction_channel': np.random.choice(['In-Store', 'Online', 'Mobile App']),
                    'is_recurring': False,
                    'location_city': 'Austin',
                    'location_state': 'TX',
                    'created_at': trans_date
                })
                transaction_counter += 1
            
            # Last 30 days: LIFE EVENT SIGNALS - Furniture, Home Improvement
            for day in range(30, 0, -1):
                trans_date = CURRENT_DATE - timedelta(days=day)
                
                # 60% chance of furniture/home improvement
                if random.random() < 0.6:
                    category = random.choice(['Furniture', 'Home Improvement'])
                    merchant = random.choice(merchant_categories[category])
                    amount = round(np.random.uniform(200, 1500), 2)  # Higher amounts
                else:
                    category = np.random.choice(['Groceries', 'Dining', 'Gas'])
                    merchant = random.choice(merchant_categories[category])
                    amount = round(np.random.uniform(30, 150), 2)
                
                transactions.append({
                    'transaction_id': f"TXN{str(transaction_counter).zfill(10)}",
                    'customer_id': customer_id,
                    'account_id': checking_acc,
                    'transaction_date': trans_date,
                    'transaction_type': 'Debit',
                    'amount': amount,
                    'merchant_name': merchant,
                    'merchant_category': category,
                    'merchant_category_code': str(np.random.randint(5000, 9999)),
                    'transaction_channel': np.random.choice(['In-Store', 'Online'], p=[0.7, 0.3]),
                    'is_recurring': False,
                    'location_city': 'Austin',
                    'location_state': 'TX',
                    'created_at': trans_date
                })
                transaction_counter += 1
        
        else:
            # Other customers: normal transaction patterns
            num_transactions = np.random.randint(30, 100)
            account_id = customer_accounts.sample(1).iloc[0]['account_id']
            
            for _ in range(num_transactions):
                trans_date = CURRENT_DATE - timedelta(days=np.random.randint(0, 90))
                category = np.random.choice(list(merchant_categories.keys()))
                merchant = random.choice(merchant_categories[category])
                
                transactions.append({
                    'transaction_id': f"TXN{str(transaction_counter).zfill(10)}",
                    'customer_id': customer_id,
                    'account_id': account_id,
                    'transaction_date': trans_date,
                    'transaction_type': np.random.choice(['Debit', 'Credit'], p=[0.85, 0.15]),
                    'amount': round(np.random.uniform(10, 500), 2),
                    'merchant_name': merchant,
                    'merchant_category': category,
                    'merchant_category_code': str(np.random.randint(5000, 9999)),
                    'transaction_channel': np.random.choice(['In-Store', 'Online', 'Mobile App']),
                    'is_recurring': random.choice([True, False]),
                    'location_city': customer['city'],
                    'location_state': customer['state'],
                    'created_at': trans_date
                })
                transaction_counter += 1
    
    df = pd.DataFrame(transactions)
    df.to_csv('data/preloaded/banking_nba/transactions.csv', index=False)
    print(f"✅ Generated {len(df)} transactions")
    return df


# ============================================================================
# 4. DIGITAL_ENGAGEMENT
# ============================================================================
def generate_digital_engagement(customers_df):
    """Generate digital engagement data (app logins, sessions)"""
    print("📊 Generating digital engagement...")
    
    engagements = []
    engagement_counter = 1
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        
        # Ms. X: ELEVATED ENGAGEMENT in last 14 days
        if customer_id == 'CUST000001':
            # Last 60-15 days: moderate engagement (2-3 logins/week)
            for day in range(60, 14, -7):
                for _ in range(np.random.randint(2, 4)):
                    session_date = CURRENT_DATE - timedelta(days=day + np.random.randint(0, 7))
                    
                    engagements.append({
                        'engagement_id': f"ENG{str(engagement_counter).zfill(10)}",
                        'customer_id': customer_id,
                        'session_date': session_date,
                        'channel': 'Mobile App',
                        'session_duration_seconds': np.random.randint(120, 480),
                        'pages_viewed': np.random.randint(3, 8),
                        'features_used': json.dumps(['account_summary', 'transfer', 'bill_pay']),
                        'device_type': 'iOS',
                        'login_method': 'Biometric',
                        'location_city': 'Austin',
                        'location_state': 'TX',
                        'created_at': session_date
                    })
                    engagement_counter += 1
            
            # Last 14 days: ELEVATED ENGAGEMENT (daily, longer sessions)
            for day in range(14, 0, -1):
                session_date = CURRENT_DATE - timedelta(days=day)
                
                # 1-2 logins per day
                for _ in range(np.random.randint(1, 3)):
                    engagements.append({
                        'engagement_id': f"ENG{str(engagement_counter).zfill(10)}",
                        'customer_id': customer_id,
                        'session_date': session_date,
                        'channel': 'Mobile App',
                        'session_duration_seconds': np.random.randint(300, 900),  # Longer sessions
                        'pages_viewed': np.random.randint(8, 15),
                        'features_used': json.dumps(['account_summary', 'mortgage_calculator', 'product_browse', 'transfer']),
                        'device_type': 'iOS',
                        'login_method': 'Biometric',
                        'location_city': 'Austin',
                        'location_state': 'TX',
                        'created_at': session_date
                    })
                    engagement_counter += 1
        
        else:
            # Other customers: varied engagement
            num_sessions = np.random.randint(10, 50)
            
            for _ in range(num_sessions):
                session_date = CURRENT_DATE - timedelta(days=np.random.randint(0, 90))
                
                engagements.append({
                    'engagement_id': f"ENG{str(engagement_counter).zfill(10)}",
                    'customer_id': customer_id,
                    'session_date': session_date,
                    'channel': np.random.choice(['Mobile App', 'Web Banking']),
                    'session_duration_seconds': np.random.randint(60, 600),
                    'pages_viewed': np.random.randint(2, 10),
                    'features_used': json.dumps(random.sample(['account_summary', 'transfer', 'bill_pay', 'product_browse', 'support'], k=np.random.randint(1, 4))),
                    'device_type': np.random.choice(['iOS', 'Android', 'Desktop']),
                    'login_method': np.random.choice(['Biometric', 'Password']),
                    'location_city': customer['city'],
                    'location_state': customer['state'],
                    'created_at': session_date
                })
                engagement_counter += 1
    
    df = pd.DataFrame(engagements)
    df.to_csv('data/preloaded/banking_nba/digital_engagement.csv', index=False)
    print(f"✅ Generated {len(df)} digital engagement records")
    return df


# ============================================================================
# 5. APPLICATIONS
# ============================================================================
def generate_applications(customers_df):
    """Generate product application history"""
    print("📊 Generating applications...")
    
    applications = []
    application_counter = 1
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        
        # Ms. X: TWO ABANDONED MORTGAGE APPLICATIONS
        if customer_id == 'CUST000001':
            # First attempt: 10 days ago
            app_date_1 = CURRENT_DATE - timedelta(days=10)
            applications.append({
                'application_id': f"APP{str(application_counter).zfill(10)}",
                'customer_id': customer_id,
                'product_type': 'Mortgage',
                'application_status': 'Abandoned',
                'started_at': app_date_1,
                'submitted_at': None,
                'completed_at': None,
                'abandoned_at': app_date_1 + timedelta(hours=2),
                'decision': None,
                'denial_reason': None,
                'requested_amount': 350000.00,
                'approved_amount': None,
                'completion_percentage': 45,
                'abandonment_stage': 'Income Verification',
                'channel': 'Mobile App',
                'created_at': app_date_1
            })
            application_counter += 1
            
            # Second attempt: 5 days ago
            app_date_2 = CURRENT_DATE - timedelta(days=5)
            applications.append({
                'application_id': f"APP{str(application_counter).zfill(10)}",
                'customer_id': customer_id,
                'product_type': 'Mortgage',
                'application_status': 'Abandoned',
                'started_at': app_date_2,
                'submitted_at': None,
                'completed_at': None,
                'abandoned_at': app_date_2 + timedelta(hours=3),
                'decision': None,
                'denial_reason': None,
                'requested_amount': 375000.00,
                'approved_amount': None,
                'completion_percentage': 62,
                'abandonment_stage': 'Document Upload',
                'channel': 'Mobile App',
                'created_at': app_date_2
            })
            application_counter += 1
        
        else:
            # Other customers: random applications (20% have applied)
            if random.random() < 0.2:
                num_apps = np.random.randint(1, 3)
                
                for _ in range(num_apps):
                    app_date = CURRENT_DATE - timedelta(days=np.random.randint(30, 365))
                    product_type = np.random.choice(['Credit Card', 'Auto Loan', 'Personal Loan', 'Mortgage'])
                    status = np.random.choice(['Approved', 'Denied', 'Abandoned', 'Under Review'], p=[0.5, 0.2, 0.2, 0.1])
                    
                    applications.append({
                        'application_id': f"APP{str(application_counter).zfill(10)}",
                        'customer_id': customer_id,
                        'product_type': product_type,
                        'application_status': status,
                        'started_at': app_date,
                        'submitted_at': app_date + timedelta(hours=np.random.randint(1, 48)) if status != 'Abandoned' else None,
                        'completed_at': app_date + timedelta(days=np.random.randint(3, 14)) if status == 'Approved' else None,
                        'abandoned_at': app_date + timedelta(hours=np.random.randint(1, 24)) if status == 'Abandoned' else None,
                        'decision': status if status in ['Approved', 'Denied'] else None,
                        'denial_reason': 'Insufficient Income' if status == 'Denied' else None,
                        'requested_amount': round(np.random.uniform(5000, 500000), 2) if product_type != 'Credit Card' else None,
                        'approved_amount': round(np.random.uniform(5000, 400000), 2) if status == 'Approved' else None,
                        'completion_percentage': 100 if status != 'Abandoned' else np.random.randint(20, 80),
                        'abandonment_stage': np.random.choice(['Personal Info', 'Employment', 'Income Verification', 'Document Upload']) if status == 'Abandoned' else None,
                        'channel': np.random.choice(['Mobile App', 'Web', 'Branch']),
                        'created_at': app_date
                    })
                    application_counter += 1
    
    df = pd.DataFrame(applications)
    df.to_csv('data/preloaded/banking_nba/applications.csv', index=False)
    print(f"✅ Generated {len(df)} applications")
    return df


# ============================================================================
# 6. DIRECT_DEPOSITS (continued in next part due to length)
# ============================================================================
def generate_direct_deposits(customers_df, accounts_df):
    """Generate direct deposit (payroll) history"""
    print("📊 Generating direct deposits...")
    
    deposits = []
    deposit_counter = 1
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        checking_accounts = accounts_df[(accounts_df['customer_id'] == customer_id) & (accounts_df['account_type'] == 'Checking')]
        
        if len(checking_accounts) == 0:
            continue
        
        account_id = checking_accounts.iloc[0]['account_id']
        
        # Ms. X: INCREASED PAYROLL in last 2 months (new job signal)
        if customer_id == 'CUST000001':
            # Older deposits: $3500 bi-weekly
            for month_offset in range(12, 2, -1):
                for week in [0, 14]:
                    deposit_date = CURRENT_DATE - timedelta(days=month_offset*30 + week)
                    deposits.append({
                        'deposit_id': f"DEP{str(deposit_counter).zfill(10)}",
                        'customer_id': customer_id,
                        'account_id': account_id,
                        'deposit_date': deposit_date.date(),
                        'amount': round(np.random.uniform(3400, 3600), 2),
                        'deposit_type': 'Payroll',
                        'employer_name': 'Tech Solutions Inc',
                        'frequency': 'Bi-Weekly',
                        'is_recurring': True,
                        'created_at': deposit_date
                    })
                    deposit_counter += 1
            
            # Recent deposits: $4500 bi-weekly (NEW JOB - 30% increase)
            for week in [0, 14, 28, 42]:
                deposit_date = CURRENT_DATE - timedelta(days=60 - week)
                deposits.append({
                    'deposit_id': f"DEP{str(deposit_counter).zfill(10)}",
                    'customer_id': customer_id,
                    'account_id': account_id,
                    'deposit_date': deposit_date.date(),
                    'amount': round(np.random.uniform(4400, 4600), 2),
                    'deposit_type': 'Payroll',
                    'employer_name': 'Enterprise Tech Corp',  # New employer
                    'frequency': 'Bi-Weekly',
                    'is_recurring': True,
                    'created_at': deposit_date
                })
                deposit_counter += 1
        
        else:
            # Other customers: stable payroll
            if customer['employment_status'] == 'Employed':
                num_deposits = np.random.randint(12, 24)
                deposit_amount = np.random.uniform(1500, 6000)
                
                for i in range(num_deposits):
                    deposit_date = CURRENT_DATE - timedelta(days=i*14)
                    deposits.append({
                        'deposit_id': f"DEP{str(deposit_counter).zfill(10)}",
                        'customer_id': customer_id,
                        'account_id': account_id,
                        'deposit_date': deposit_date.date(),
                        'amount': round(deposit_amount + np.random.uniform(-100, 100), 2),
                        'deposit_type': 'Payroll',
                        'employer_name': f"Company {np.random.randint(1, 100)}",
                        'frequency': 'Bi-Weekly',
                        'is_recurring': True,
                        'created_at': deposit_date
                    })
                    deposit_counter += 1
    
    df = pd.DataFrame(deposits)
    df.to_csv('data/preloaded/banking_nba/direct_deposits.csv', index=False)
    print(f"✅ Generated {len(df)} direct deposits")
    return df


# ============================================================================
# 7. PRODUCTS
# ============================================================================
def generate_products():
    """Generate banking product catalog"""
    print("📊 Generating products catalog...")
    
    products = [
        {
            'product_id': 'PROD001',
            'product_name': 'Home Mortgage - Fixed Rate',
            'product_category': 'Loan',
            'product_type': 'Mortgage',
            'description': '30-year fixed rate mortgage for home purchase',
            'min_income_required': 50000.00,
            'min_credit_score': 620,
            'min_tenure_months': 12,
            'max_age': 70,
            'min_age': 21,
            'interest_rate_range': '3.5% - 5.5%',
            'fees_description': 'Origination fee 1%, closing costs vary',
            'eligibility_rules': json.dumps({'debt_to_income_max': 43, 'down_payment_min': 3}),
            'target_segments': json.dumps(['Affluent', 'Mass Market']),
            'cross_sell_priority': 10,
            'is_active': True,
            'created_at': CURRENT_DATE
        },
        {
            'product_id': 'PROD002',
            'product_name': 'Home Insurance',
            'product_category': 'Insurance',
            'product_type': 'Home Insurance',
            'description': 'Comprehensive home insurance coverage',
            'min_income_required': 30000.00,
            'min_credit_score': 500,
            'min_tenure_months': 6,
            'max_age': 80,
            'min_age': 21,
            'interest_rate_range': None,
            'fees_description': 'Annual premium varies by property value',
            'eligibility_rules': json.dumps({'has_mortgage': True}),
            'target_segments': json.dumps(['Affluent', 'Mass Market']),
            'cross_sell_priority': 9,
            'is_active': True,
            'created_at': CURRENT_DATE
        },
        {
            'product_id': 'PROD003',
            'product_name': 'Premium Credit Card',
            'product_category': 'Credit',
            'product_type': 'Credit Card',
            'description': 'Premium rewards credit card with travel benefits',
            'min_income_required': 75000.00,
            'min_credit_score': 700,
            'min_tenure_months': 12,
            'max_age': 75,
            'min_age': 21,
            'interest_rate_range': '15.99% - 24.99%',
            'fees_description': 'Annual fee $95, no foreign transaction fees',
            'eligibility_rules': json.dumps({'max_credit_utilization': 50}),
            'target_segments': json.dumps(['Affluent']),
            'cross_sell_priority': 8,
            'is_active': True,
            'created_at': CURRENT_DATE
        },
        {
            'product_id': 'PROD004',
            'product_name': 'Auto Loan',
            'product_category': 'Loan',
            'product_type': 'Auto Loan',
            'description': 'New and used car financing',
            'min_income_required': 30000.00,
            'min_credit_score': 600,
            'min_tenure_months': 6,
            'max_age': 70,
            'min_age': 18,
            'interest_rate_range': '4.5% - 12.5%',
            'fees_description': 'No origination fee',
            'eligibility_rules': json.dumps({'max_loan_to_value': 120}),
            'target_segments': json.dumps(['Mass Market', 'Affluent']),
            'cross_sell_priority': 7,
            'is_active': True,
            'created_at': CURRENT_DATE
        },
        {
            'product_id': 'PROD005',
            'product_name': 'Personal Loan',
            'product_category': 'Loan',
            'product_type': 'Personal Loan',
            'description': 'Unsecured personal loan for any purpose',
            'min_income_required': 25000.00,
            'min_credit_score': 580,
            'min_tenure_months': 12,
            'max_age': 70,
            'min_age': 21,
            'interest_rate_range': '6.99% - 19.99%',
            'fees_description': 'Origination fee 2-5%',
            'eligibility_rules': json.dumps({'max_debt_to_income': 45}),
            'target_segments': json.dumps(['Mass Market', 'Affluent']),
            'cross_sell_priority': 6,
            'is_active': True,
            'created_at': CURRENT_DATE
        }
    ]
    
    df = pd.DataFrame(products)
    df.to_csv('data/preloaded/banking_nba/products.csv', index=False)
    print(f"✅ Generated {len(df)} products")
    return df


# ============================================================================
# 8. PRODUCT_HOLDINGS
# ============================================================================
def generate_product_holdings(customers_df, products_df, accounts_df):
    """Generate current product holdings"""
    print("📊 Generating product holdings...")
    
    holdings = []
    holding_counter = 1
    
    # Ms. X: Only checking + credit card (no mortgage yet)
    customer = customers_df[customers_df['customer_id'] == 'CUST000001'].iloc[0]
    checking_acc = accounts_df[(accounts_df['customer_id'] == 'CUST000001') & (accounts_df['account_type'] == 'Checking')].iloc[0]
    cc_acc = accounts_df[(accounts_df['customer_id'] == 'CUST000001') & (accounts_df['account_type'] == 'Credit Card')].iloc[0]
    
    # No mortgage product holding for Ms. X - this is key!
    
    # Other customers: assign random product holdings
    for _, customer in customers_df.iterrows():
        if customer['customer_id'] == 'CUST000001':
            continue
        
        customer_accounts = accounts_df[accounts_df['customer_id'] == customer['customer_id']]
        
        for _, account in customer_accounts.iterrows():
            # Match account type to product
            product = None
            if account['account_type'] == 'Credit Card':
                product = products_df[products_df['product_type'] == 'Credit Card'].sample(1).iloc[0]
            elif account['account_type'] == 'Mortgage':
                product = products_df[products_df['product_type'] == 'Mortgage'].sample(1).iloc[0]
            elif account['account_type'] == 'Auto Loan':
                product = products_df[products_df['product_type'] == 'Auto Loan'].sample(1).iloc[0]
            
            if product is not None:
                holdings.append({
                    'holding_id': f"HOLD{str(holding_counter).zfill(8)}",
                    'customer_id': customer['customer_id'],
                    'product_id': product['product_id'],
                    'account_id': account['account_id'],
                    'acquired_date': account['account_opened_date'],
                    'status': 'Active',
                    'usage_frequency': np.random.choice(['High', 'Medium', 'Low']),
                    'satisfaction_score': round(np.random.uniform(3.0, 5.0), 2),
                    'created_at': pd.to_datetime(account['account_opened_date'])
                })
                holding_counter += 1
    
    df = pd.DataFrame(holdings)
    df.to_csv('data/preloaded/banking_nba/product_holdings.csv', index=False)
    print(f"✅ Generated {len(df)} product holdings")
    return df


# ============================================================================
# 9. CREDIT_UTILIZATION
# ============================================================================
def generate_credit_utilization(accounts_df):
    """Generate credit utilization history"""
    print("📊 Generating credit utilization...")
    
    utilization_records = []
    utilization_counter = 1
    
    credit_card_accounts = accounts_df[accounts_df['account_type'] == 'Credit Card']
    
    for _, account in credit_card_accounts.iterrows():
        # Last 6 months of utilization
        for month_offset in range(6):
            report_date = CURRENT_DATE - timedelta(days=month_offset*30)
            credit_limit = account['credit_limit']
            
            # Ms. X: stable moderate utilization (21%)
            if account['customer_id'] == 'CUST000001':
                balance = round(credit_limit * np.random.uniform(0.18, 0.24), 2)
            else:
                balance = round(credit_limit * np.random.uniform(0.05, 0.70), 2)
            
            utilization_records.append({
                'utilization_id': f"UTIL{str(utilization_counter).zfill(10)}",
                'customer_id': account['customer_id'],
                'account_id': account['account_id'],
                'report_date': report_date.date(),
                'credit_limit': credit_limit,
                'current_balance': balance,
                'utilization_percentage': round((balance / credit_limit) * 100, 2),
                'available_credit': credit_limit - balance,
                'payment_status': np.random.choice(['On Time', 'Late', 'Missed'], p=[0.85, 0.10, 0.05]),
                'days_past_due': 0 if np.random.random() > 0.15 else np.random.randint(1, 90),
                'created_at': report_date
            })
            utilization_counter += 1
    
    df = pd.DataFrame(utilization_records)
    df.to_csv('data/preloaded/banking_nba/credit_utilization.csv', index=False)
    print(f"✅ Generated {len(df)} credit utilization records")
    return df


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    print("\n" + "="*80)
    print("🏦 BANKING NBA PLATFORM - SYNTHETIC DATA GENERATOR")
    print("="*80 + "\n")
    
    customers_df = generate_customers()
    accounts_df = generate_accounts(customers_df)
    transactions_df = generate_transactions(customers_df, accounts_df)
    digital_engagement_df = generate_digital_engagement(customers_df)
    applications_df = generate_applications(customers_df)
    direct_deposits_df = generate_direct_deposits(customers_df, accounts_df)
    products_df = generate_products()
    product_holdings_df = generate_product_holdings(customers_df, products_df, accounts_df)
    credit_utilization_df = generate_credit_utilization(accounts_df)
    
    print("\n" + "="*80)
    print("✅ ALL DATA GENERATED SUCCESSFULLY!")
    print("="*80)
    print(f"\n📁 Data saved to: data/preloaded/banking_nba/")
    print(f"\n📊 Summary:")
    print(f"   - Customers: {len(customers_df)}")
    print(f"   - Accounts: {len(accounts_df)}")
    print(f"   - Transactions: {len(transactions_df)}")
    print(f"   - Digital Engagement: {len(digital_engagement_df)}")
    print(f"   - Applications: {len(applications_df)}")
    print(f"   - Direct Deposits: {len(direct_deposits_df)}")
    print(f"   - Products: {len(products_df)}")
    print(f"   - Product Holdings: {len(product_holdings_df)}")
    print(f"   - Credit Utilization: {len(credit_utilization_df)}")
    print("\n🎯 Ms. X (CUST000001) scenario embedded with:")
    print("   ✓ Increased app logins (last 14 days)")
    print("   ✓ Two abandoned mortgage applications")
    print("   ✓ Increased furniture & home improvement spending")
    print("   ✓ Increased payroll deposits (new job)")
    print("\n")


if __name__ == "__main__":
    main()


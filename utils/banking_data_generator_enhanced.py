"""
Enhanced Banking Data Generator for Product Matchmaking
Creates realistic banking data with strong signals for NBA recommendations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

np.random.seed(42)
random.seed(42)


class EnhancedBankingDataGenerator:
    """Generate realistic banking data for product recommendations"""
    
    def __init__(self, n_customers=100):
        self.n_customers = n_customers
        self.start_date = datetime.now() - timedelta(days=365)
        
    def generate_all(self, output_dir="data/preloaded/banking_nba"):
        """Generate all banking tables"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        print("🏦 Generating Enhanced Banking Dataset...")
        
        # Generate base customers
        customers = self.generate_customers()
        customers.to_csv(f"{output_dir}/customers.csv", index=False)
        print(f"✅ Generated {len(customers)} customers")
        
        # Generate products
        products = self.generate_products()
        products.to_csv(f"{output_dir}/products.csv", index=False)
        print(f"✅ Generated {len(products)} products")
        
        # Generate accounts
        accounts = self.generate_accounts(customers)
        accounts.to_csv(f"{output_dir}/accounts.csv", index=False)
        print(f"✅ Generated {len(accounts)} accounts")
        
        # Generate transactions
        transactions = self.generate_transactions(customers, accounts)
        transactions.to_csv(f"{output_dir}/transactions.csv", index=False)
        print(f"✅ Generated {len(transactions)} transactions")
        
        # Generate digital engagement
        engagement = self.generate_digital_engagement(customers)
        engagement.to_csv(f"{output_dir}/digital_engagement.csv", index=False)
        print(f"✅ Generated {len(engagement)} engagement events")
        
        # Generate applications
        applications = self.generate_applications(customers, products)
        applications.to_csv(f"{output_dir}/applications.csv", index=False)
        print(f"✅ Generated {len(applications)} applications")
        
        # Generate direct deposits
        deposits = self.generate_direct_deposits(customers)
        deposits.to_csv(f"{output_dir}/direct_deposits.csv", index=False)
        print(f"✅ Generated {len(deposits)} direct deposits")
        
        # Generate credit utilization
        credit_util = self.generate_credit_utilization(customers)
        credit_util.to_csv(f"{output_dir}/credit_utilization.csv", index=False)
        print(f"✅ Generated {len(credit_util)} credit utilization records")
        
        # Generate product holdings
        holdings = self.generate_product_holdings(customers, products)
        holdings.to_csv(f"{output_dir}/product_holdings.csv", index=False)
        print(f"✅ Generated {len(holdings)} product holdings")
        
        print(f"\n✅ All data saved to {output_dir}/")
        
    def generate_customers(self):
        """Generate customer profiles with realistic segments"""
        customers = []
        
        # Define customer segments for realistic product matching
        segments = [
            {"name": "Young Professionals", "count": 25, "age_range": (25, 35), "income_range": (50000, 80000), "credit_range": (680, 750)},
            {"name": "Established Families", "count": 30, "age_range": (35, 50), "income_range": (80000, 150000), "credit_range": (700, 800)},
            {"name": "Affluent Seniors", "count": 20, "age_range": (50, 70), "income_range": (100000, 250000), "credit_range": (750, 850)},
            {"name": "Entry Level", "count": 15, "age_range": (22, 30), "income_range": (30000, 50000), "credit_range": (620, 700)},
            {"name": "High Net Worth", "count": 10, "age_range": (40, 65), "income_range": (200000, 500000), "credit_range": (780, 850)},
        ]
        
        customer_id = 1
        for segment in segments:
            for _ in range(segment["count"]):
                age = np.random.randint(*segment["age_range"])
                income = np.random.uniform(*segment["income_range"])
                credit_score = np.random.randint(*segment["credit_range"])
                
                # Calculate tenure (longer for older customers)
                tenure_months = int(np.random.uniform(age - 20, age * 1.5))
                tenure_months = max(6, min(tenure_months, 300))
                
                # Life events based on age and profile
                life_events = self._determine_life_events(age, income, segment["name"])
                
                # Intent score based on life events and engagement
                intent_score = self._calculate_intent_score(life_events, age, income)
                
                # Channel preference
                channel = "mobile" if age < 45 else np.random.choice(["mobile", "web", "branch"], p=[0.5, 0.3, 0.2])
                
                # Engagement metrics - more realistic distribution
                # Low engagement: 0-2 logins, Medium: 3-6, High: 7+
                engagement_tier = np.random.choice(['low', 'medium', 'high'], p=[0.3, 0.4, 0.3])
                if engagement_tier == 'low':
                    login_freq = int(np.random.uniform(0, 3))
                elif engagement_tier == 'medium':
                    login_freq = int(np.random.uniform(3, 7))
                else:  # high
                    login_freq = int(np.random.uniform(7, 25))
                
                trans_volume = int(np.random.uniform(10, 50))
                avg_trans_amount = income / 20 + np.random.uniform(50, 500)
                
                customers.append({
                    'customer_id': f'CUST_{customer_id:06d}',
                    'age': age,
                    'income': round(income, 2),
                    'credit_score': credit_score,
                    'tenure_months': tenure_months,
                    'segment': segment["name"],
                    'primary_life_event': life_events[0] if life_events else 'stable',
                    'secondary_life_event': life_events[1] if len(life_events) > 1 else None,
                    'intent_score': round(intent_score, 3),
                    'login_frequency_30d': login_freq,
                    'transaction_volume_30d': trans_volume,
                    'avg_transaction_amount': round(avg_trans_amount, 2),
                    'channel_preference': channel,
                    'estimated_savings': round(income * np.random.uniform(0.1, 0.5), 2),
                    'debt_to_income_ratio': round(np.random.uniform(0.1, 0.4), 3),
                    'risk_category': self._get_risk_category(credit_score),
                    'value_tier': self._get_value_tier(income)
                })
                customer_id += 1
        
        return pd.DataFrame(customers)
    
    def _determine_life_events(self, age, income, segment):
        """Determine realistic life events based on profile"""
        events = []
        
        if 25 <= age <= 35:
            events.extend(np.random.choice(['new_job', 'first_home', 'marriage', 'career_growth'], 2, replace=False))
        elif 35 <= age <= 50:
            events.extend(np.random.choice(['home_purchase', 'child_education', 'investment', 'business_start'], 2, replace=False))
        elif age > 50:
            events.extend(np.random.choice(['retirement_planning', 'wealth_management', 'estate_planning', 'downsizing'], 2, replace=False))
        else:
            events.append('stable')
            
        return events
    
    def _calculate_intent_score(self, life_events, age, income):
        """Calculate purchase intent based on signals"""
        base_score = 0.3
        
        # Life events increase intent
        if 'new_job' in life_events or 'career_growth' in life_events:
            base_score += 0.3
        if 'home_purchase' in life_events or 'first_home' in life_events:
            base_score += 0.4
        if 'retirement_planning' in life_events:
            base_score += 0.2
            
        # Age and income factors
        if 30 <= age <= 45:
            base_score += 0.1
        if income > 100000:
            base_score += 0.1
            
        return min(base_score, 1.0)
    
    def _get_risk_category(self, credit_score):
        """Categorize risk based on credit score"""
        if credit_score >= 750:
            return 'low'
        elif credit_score >= 680:
            return 'medium'
        else:
            return 'high'
    
    def _get_value_tier(self, income):
        """Categorize customer value tier"""
        if income >= 150000:
            return 'platinum'
        elif income >= 80000:
            return 'gold'
        elif income >= 50000:
            return 'silver'
        else:
            return 'bronze'
    
    def generate_products(self):
        """Generate realistic banking products"""
        products = [
            {
                'product_id': 'PROD_001',
                'product_name': 'Premium Rewards Credit Card',
                'product_type': 'credit_card',
                'category': 'lending',
                'annual_fee': 95,
                'interest_rate': 16.99,
                'min_credit_score': 720,
                'min_income': 60000,
                'min_age': 21,
                'max_age': 999,
                'features': '["cashback", "travel_rewards", "insurance"]',
                'target_segment': 'Young Professionals,Established Families',
                'life_event_match': 'new_job,career_growth,travel',
            },
            {
                'product_id': 'PROD_002',
                'product_name': 'First-Time Home Buyer Mortgage',
                'product_type': 'mortgage',
                'category': 'lending',
                'annual_fee': 0,
                'interest_rate': 3.75,
                'min_credit_score': 680,
                'min_income': 50000,
                'min_age': 21,
                'max_age': 65,
                'features': '["low_down_payment", "first_time_buyer", "flexible_terms"]',
                'target_segment': 'Young Professionals,Entry Level',
                'life_event_match': 'first_home,home_purchase,marriage',
            },
            {
                'product_id': 'PROD_003',
                'product_name': 'High-Yield Savings Account',
                'product_type': 'savings',
                'category': 'deposit',
                'annual_fee': 0,
                'interest_rate': 4.5,
                'min_credit_score': 0,
                'min_income': 0,
                'min_age': 18,
                'max_age': 999,
                'features': '["no_fees", "high_interest", "instant_access"]',
                'target_segment': 'All',
                'life_event_match': 'savings,emergency_fund,goal_setting',
            },
            {
                'product_id': 'PROD_004',
                'product_name': 'Retirement Investment Account',
                'product_type': 'investment',
                'category': 'wealth_management',
                'annual_fee': 50,
                'interest_rate': 0,
                'min_credit_score': 0,
                'min_income': 75000,
                'min_age': 40,
                'max_age': 999,
                'features': '["tax_advantaged", "professional_management", "diversified"]',
                'target_segment': 'Established Families,Affluent Seniors,High Net Worth',
                'life_event_match': 'retirement_planning,wealth_management,estate_planning',
            },
            {
                'product_id': 'PROD_005',
                'product_name': 'Small Business Line of Credit',
                'product_type': 'business_loan',
                'category': 'lending',
                'annual_fee': 100,
                'interest_rate': 7.25,
                'min_credit_score': 700,
                'min_income': 80000,
                'min_age': 25,
                'max_age': 70,
                'features': '["flexible_draw", "business_rewards", "financial_tools"]',
                'target_segment': 'Established Families,High Net Worth',
                'life_event_match': 'business_start,career_growth,investment',
            },
        ]
        
        return pd.DataFrame(products)
    
    def generate_accounts(self, customers_df):
        """Generate account data"""
        accounts = []
        account_id = 1
        
        for _, customer in customers_df.iterrows():
            # Most customers have 1-3 accounts
            n_accounts = np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])
            
            for _ in range(n_accounts):
                account_type = np.random.choice(['checking', 'savings', 'credit_card'])
                balance = np.random.uniform(1000, customer['income'] * 0.3)
                
                accounts.append({
                    'account_id': f'ACC_{account_id:08d}',
                    'customer_id': customer['customer_id'],
                    'account_type': account_type,
                    'balance': round(balance, 2),
                    'opened_date': (self.start_date + timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d'),
                    'status': 'active'
                })
                account_id += 1
        
        return pd.DataFrame(accounts)
    
    def generate_transactions(self, customers_df, accounts_df):
        """Generate transaction data"""
        transactions = []
        trans_id = 1
        
        for _, account in accounts_df.iterrows():
            customer = customers_df[customers_df['customer_id'] == account['customer_id']].iloc[0]
            n_trans = int(customer['transaction_volume_30d'])
            
            for _ in range(n_trans):
                amount = np.random.exponential(customer['avg_transaction_amount'])
                trans_type = np.random.choice(['debit', 'credit', 'transfer'], p=[0.6, 0.3, 0.1])
                
                transactions.append({
                    'transaction_id': f'TRANS_{trans_id:010d}',
                    'account_id': account['account_id'],
                    'customer_id': customer['customer_id'],
                    'transaction_date': (datetime.now() - timedelta(days=np.random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S'),
                    'amount': round(amount, 2),
                    'transaction_type': trans_type,
                    'category': np.random.choice(['groceries', 'utilities', 'entertainment', 'shopping', 'dining', 'travel']),
                    'merchant': f'Merchant_{np.random.randint(1, 100)}'
                })
                trans_id += 1
        
        return pd.DataFrame(transactions)
    
    def generate_digital_engagement(self, customers_df):
        """Generate digital engagement events"""
        events = []
        event_id = 1
        
        for _, customer in customers_df.iterrows():
            n_events = int(customer['login_frequency_30d'] * 2)  # Multiple events per session
            
            for _ in range(n_events):
                event_type = np.random.choice([
                    'login', 'view_products', 'mortgage_calculator', 'investment_research',
                    'credit_card_comparison', 'account_summary', 'transfer', 'bill_pay'
                ], p=[0.2, 0.15, 0.1, 0.1, 0.1, 0.15, 0.1, 0.1])
                
                events.append({
                    'event_id': f'EVENT_{event_id:010d}',
                    'customer_id': customer['customer_id'],
                    'event_date': (datetime.now() - timedelta(days=np.random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S'),
                    'event_type': event_type,
                    'channel': customer['channel_preference'],
                    'session_duration_seconds': np.random.randint(60, 1800),
                    'pages_viewed': np.random.randint(1, 20)
                })
                event_id += 1
        
        return pd.DataFrame(events)
    
    def generate_applications(self, customers_df, products_df):
        """Generate product applications"""
        applications = []
        app_id = 1
        
        # 30% of customers have applied for something
        applicants = customers_df.sample(n=int(len(customers_df) * 0.3))
        
        for _, customer in applicants.iterrows():
            # Pick a product based on profile match
            if customer['intent_score'] > 0.6:
                status = np.random.choice(['approved', 'pending', 'review'], p=[0.6, 0.3, 0.1])
            else:
                status = np.random.choice(['approved', 'pending', 'declined'], p=[0.4, 0.3, 0.3])
            
            product = products_df.sample(n=1).iloc[0]
            
            applications.append({
                'application_id': f'APP_{app_id:08d}',
                'customer_id': customer['customer_id'],
                'product_id': product['product_id'],
                'application_date': (datetime.now() - timedelta(days=np.random.randint(0, 90))).strftime('%Y-%m-%d'),
                'status': status,
                'requested_amount': round(np.random.uniform(5000, 500000), 2) if product['product_type'] in ['mortgage', 'business_loan'] else None
            })
            app_id += 1
        
        return pd.DataFrame(applications)
    
    def generate_direct_deposits(self, customers_df):
        """Generate direct deposit records"""
        deposits = []
        deposit_id = 1
        
        # 70% of customers have direct deposit
        dd_customers = customers_df.sample(n=int(len(customers_df) * 0.7))
        
        for _, customer in dd_customers.iterrows():
            # Generate 3 months of deposits
            for month in range(3):
                amount = customer['income'] / 12 * np.random.uniform(0.9, 1.1)
                
                deposits.append({
                    'deposit_id': f'DD_{deposit_id:08d}',
                    'customer_id': customer['customer_id'],
                    'deposit_date': (datetime.now() - timedelta(days=30 * (2 - month) + np.random.randint(0, 5))).strftime('%Y-%m-%d'),
                    'amount': round(amount, 2),
                    'source': 'employer_payroll'
                })
                deposit_id += 1
        
        return pd.DataFrame(deposits)
    
    def generate_credit_utilization(self, customers_df):
        """Generate credit utilization data"""
        utilization = []
        util_id = 1
        
        for _, customer in customers_df.iterrows():
            # Generate 3 months of utilization
            for month in range(3):
                credit_limit = customer['income'] * np.random.uniform(0.3, 1.0)
                utilization_rate = np.random.uniform(0.1, 0.8)
                
                utilization.append({
                    'utilization_id': f'UTIL_{util_id:08d}',
                    'customer_id': customer['customer_id'],
                    'report_date': (datetime.now() - timedelta(days=30 * (2 - month))).strftime('%Y-%m-%d'),
                    'credit_limit': round(credit_limit, 2),
                    'credit_used': round(credit_limit * utilization_rate, 2),
                    'utilization_rate': round(utilization_rate, 3)
                })
                util_id += 1
        
        return pd.DataFrame(utilization)
    
    def generate_product_holdings(self, customers_df, products_df):
        """Generate current product holdings"""
        holdings = []
        holding_id = 1
        
        for _, customer in customers_df.iterrows():
            # Each customer holds 0-2 products
            n_products = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
            
            if n_products > 0:
                held_products = products_df.sample(n=min(n_products, len(products_df)))
                
                for _, product in held_products.iterrows():
                    holdings.append({
                        'holding_id': f'HOLD_{holding_id:08d}',
                        'customer_id': customer['customer_id'],
                        'product_id': product['product_id'],
                        'acquisition_date': (datetime.now() - timedelta(days=np.random.randint(30, 730))).strftime('%Y-%m-%d'),
                        'status': 'active'
                    })
                    holding_id += 1
        
        return pd.DataFrame(holdings)


if __name__ == "__main__":
    generator = EnhancedBankingDataGenerator(n_customers=100)
    generator.generate_all()
    print("\n✅ Enhanced Banking Dataset Generation Complete!")


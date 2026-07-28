"""
Banking Platform - Enhanced Customer Data Generator
Generates 5000 synthetic banking customers with unique segment names and proper explanations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path
from faker import Faker

np.random.seed(42)
random.seed(42)

class BankingDataGenerator5000:
    """Generate 5000 synthetic banking customers with diverse personas"""
    
    def __init__(self):
        self.n_customers = 5000
        self.output_dir = Path("data/preloaded/banking_nba")  # Match backend path
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fake = Faker()
        Faker.seed(42)
        
        # Diverse persona types with unique characteristics
        self.persona_configs = {
            'High_Net_Worth_Investors': {
                'percentage': 0.12,
                'emoji': '💼',
                'description': 'Affluent investors with $500K+ portfolios seeking wealth management',
                'age_range': (45, 70),
                'income_range': (200000, 800000),
                'credit_range': (760, 850),
                'balance_range': (100000, 500000),
                'intent_range': (0.75, 0.95)
            },
            'Young_Professionals': {
                'percentage': 0.22,
                'emoji': '🚀',
                'description': 'Career-focused millennials building wealth with high growth potential',
                'age_range': (25, 40),
                'income_range': (60000, 150000),
                'credit_range': (680, 780),
                'balance_range': (15000, 75000),
                'intent_range': (0.60, 0.85)
            },
            'Small_Business_Owners': {
                'percentage': 0.15,
                'emoji': '🏢',
                'description': 'Entrepreneurs managing both personal and business finances',
                'age_range': (35, 60),
                'income_range': (80000, 300000),
                'credit_range': (700, 820),
                'balance_range': (40000, 200000),
                'intent_range': (0.65, 0.90)
            },
            'Mass_Market_Savers': {
                'percentage': 0.28,
                'emoji': '💰',
                'description': 'Mainstream customers focused on saving and basic banking needs',
                'age_range': (30, 65),
                'income_range': (35000, 75000),
                'credit_range': (620, 720),
                'balance_range': (5000, 35000),
                'intent_range': (0.40, 0.65)
            },
            'Digital_Native_Gen_Z': {
                'percentage': 0.18,
                'emoji': '📱',
                'description': 'Tech-savvy younger customers preferring mobile-first banking',
                'age_range': (18, 30),
                'income_range': (25000, 80000),
                'credit_range': (640, 740),
                'balance_range': (2000, 25000),
                'intent_range': (0.70, 0.95)
            },
            'Near_Retirement_Planners': {
                'percentage': 0.05,
                'emoji': '🏡',
                'description': 'Pre-retirees focused on wealth preservation and income generation',
                'age_range': (55, 68),
                'income_range': (80000, 180000),
                'credit_range': (720, 820),
                'balance_range': (80000, 300000),
                'intent_range': (0.50, 0.75)
            }
        }
        
    def generate_dataset(self):
        """Generate complete banking dataset with all tables"""
        print("="*80)
        print("🏦 BANKING CUSTOMER DATA GENERATOR - 5000 CUSTOMERS")
        print("="*80)
        
        # Generate customers
        customers_df = self._generate_customers()
        
        # Generate products
        products_df = self._generate_products()
        
        # Generate transactions
        transactions_df = self._generate_transactions(customers_df, products_df)
        
        # Print summary
        self._print_summary(customers_df, products_df, transactions_df)
        
        return customers_df, products_df, transactions_df
    
    def _generate_customers(self):
        """Generate 5000 customer profiles"""
        print("\n📊 Generating 5000 customer profiles...")
        
        customers = []
        persona_labels = list(self.persona_configs.keys())
        persona_probs = [config['percentage'] for config in self.persona_configs.values()]
        
        # Assign personas
        persona_assignments = np.random.choice(
            persona_labels,
            size=self.n_customers,
            p=persona_probs
        )
        
        for i, persona_type in enumerate(persona_assignments):
            config = self.persona_configs[persona_type]
            customer_id = f"CUST_{i+1:05d}"
            
            customer = {
                'customer_id': customer_id,
                'customer_name': self.fake.name(),
                'age': np.random.randint(*config['age_range']),
                'income': np.random.randint(*config['income_range']),
                'credit_score': np.random.randint(*config['credit_range']),
                'account_balance': np.random.uniform(*config['balance_range']),
                'account_tenure_months': np.random.randint(6, 240),
                'geographic_region': np.random.choice(['Urban', 'Suburban', 'Rural'], p=[0.5, 0.35, 0.15]),
                'home_ownership': np.random.choice(['Own', 'Mortgage', 'Rent'], p=[0.35, 0.45, 0.20]),
                'employment_status': np.random.choice(['Employed', 'Self-Employed', 'Retired'], p=[0.70, 0.20, 0.10]),
                
                # Behavioral attributes for clustering
                'digital_engagement_score': np.random.uniform(0.3, 1.0),
                'branch_visit_frequency': np.random.uniform(0.1, 0.9),
                'product_adoption_rate': np.random.uniform(0.2, 0.95),
                'transaction_frequency': np.random.randint(5, 150),
                'cross_sell_receptivity': np.random.uniform(0.3, 1.0),
                'risk_tolerance': np.random.uniform(0.2, 0.95),
                'savings_rate': np.random.uniform(0.05, 0.35),
                'investment_interest': np.random.uniform(0.1, 0.95),
                'mobile_app_usage': np.random.uniform(0.2, 1.0),
                'call_center_interaction': np.random.uniform(0.0, 0.7),
                
                # Intent and value
                'intent_score': np.random.uniform(*config['intent_range']),
                'customer_lifetime_value': np.random.uniform(5000, 500000),
                'churn_risk': np.random.uniform(0.05, 0.45),
                
                # Demographics
                'marital_status': np.random.choice(['Single', 'Married', 'Divorced'], p=[0.35, 0.50, 0.15]),
                'dependents': np.random.randint(0, 5),
                'education_level': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], p=[0.25, 0.45, 0.20, 0.10]),
                
                # Persona metadata
                'true_persona': persona_type,  # For validation
                'persona_emoji': config['emoji']
            }
            
            customers.append(customer)
        
        df = pd.DataFrame(customers)
        
        # Save
        output_path = self.output_dir / "customers.csv"
        df.to_csv(output_path, index=False)
        print(f"   ✅ Generated {len(df):,} customers")
        print(f"   📁 Saved to: {output_path}")
        
        return df
    
    def _generate_products(self):
        """Generate banking products catalog"""
        print("\n💳 Generating banking products...")
        
        products = [
            # Checking & Savings
            {'product_id': 'PROD_001', 'product_name': 'Premium Checking', 'category': 'Checking', 'annual_fee': 0, 'min_balance': 5000},
            {'product_id': 'PROD_002', 'product_name': 'Basic Checking', 'category': 'Checking', 'annual_fee': 0, 'min_balance': 0},
            {'product_id': 'PROD_003', 'product_name': 'High-Yield Savings', 'category': 'Savings', 'annual_fee': 0, 'min_balance': 1000},
            {'product_id': 'PROD_004', 'product_name': 'Money Market Account', 'category': 'Savings', 'annual_fee': 0, 'min_balance': 10000},
            
            # Credit Cards
            {'product_id': 'PROD_005', 'product_name': 'Platinum Rewards Card', 'category': 'Credit_Card', 'annual_fee': 95, 'min_balance': 0},
            {'product_id': 'PROD_006', 'product_name': 'Cash Back Card', 'category': 'Credit_Card', 'annual_fee': 0, 'min_balance': 0},
            {'product_id': 'PROD_007', 'product_name': 'Travel Rewards Card', 'category': 'Credit_Card', 'annual_fee': 450, 'min_balance': 0},
            
            # Loans
            {'product_id': 'PROD_008', 'product_name': 'Personal Loan', 'category': 'Loan', 'annual_fee': 0, 'min_balance': 0},
            {'product_id': 'PROD_009', 'product_name': 'Auto Loan', 'category': 'Loan', 'annual_fee': 0, 'min_balance': 0},
            {'product_id': 'PROD_010', 'product_name': 'Mortgage', 'category': 'Mortgage', 'annual_fee': 0, 'min_balance': 0},
            {'product_id': 'PROD_011', 'product_name': 'Home Equity Line', 'category': 'Mortgage', 'annual_fee': 0, 'min_balance': 0},
            
            # Investment Products
            {'product_id': 'PROD_012', 'product_name': 'Brokerage Account', 'category': 'Investment', 'annual_fee': 0, 'min_balance': 5000},
            {'product_id': 'PROD_013', 'product_name': 'Retirement IRA', 'category': 'Investment', 'annual_fee': 0, 'min_balance': 1000},
            {'product_id': 'PROD_014', 'product_name': 'Wealth Management', 'category': 'Investment', 'annual_fee': 500, 'min_balance': 100000},
            
            # Business Products
            {'product_id': 'PROD_015', 'product_name': 'Business Checking', 'category': 'Business', 'annual_fee': 0, 'min_balance': 2500},
            {'product_id': 'PROD_016', 'product_name': 'Business Credit Card', 'category': 'Business', 'annual_fee': 150, 'min_balance': 0},
            {'product_id': 'PROD_017', 'product_name': 'Business Line of Credit', 'category': 'Business', 'annual_fee': 0, 'min_balance': 0},
            
            # CDs & Fixed Income
            {'product_id': 'PROD_018', 'product_name': '12-Month CD', 'category': 'CD', 'annual_fee': 0, 'min_balance': 1000},
            {'product_id': 'PROD_019', 'product_name': '5-Year CD', 'category': 'CD', 'annual_fee': 0, 'min_balance': 5000},
            
            # Insurance
            {'product_id': 'PROD_020', 'product_name': 'Life Insurance', 'category': 'Insurance', 'annual_fee': 600, 'min_balance': 0}
        ]
        
        df = pd.DataFrame(products)
        output_path = self.output_dir / "products.csv"
        df.to_csv(output_path, index=False)
        print(f"   ✅ Generated {len(df)} products")
        print(f"   📁 Saved to: {output_path}")
        
        return df
    
    def _generate_transactions(self, customers_df, products_df):
        """Generate transaction history"""
        print("\n💸 Generating transaction history...")
        
        transactions = []
        base_date = datetime.now() - timedelta(days=365)
        
        # Generate 3-8 transactions per customer
        for _, customer in customers_df.iterrows():
            n_transactions = np.random.randint(3, 9)
            
            for _ in range(n_transactions):
                transaction = {
                    'transaction_id': f"TXN_{len(transactions)+1:07d}",
                    'customer_id': customer['customer_id'],
                    'product_id': np.random.choice(products_df['product_id']),
                    'transaction_date': (base_date + timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d'),
                    'transaction_amount': np.random.uniform(10, 5000),
                    'transaction_type': np.random.choice(['Deposit', 'Withdrawal', 'Transfer', 'Payment'], p=[0.3, 0.2, 0.3, 0.2]),
                    'channel': np.random.choice(['Mobile', 'Web', 'Branch', 'ATM', 'Phone'], p=[0.45, 0.25, 0.15, 0.10, 0.05])
                }
                transactions.append(transaction)
        
        df = pd.DataFrame(transactions)
        output_path = self.output_dir / "transactions.csv"
        df.to_csv(output_path, index=False)
        print(f"   ✅ Generated {len(df):,} transactions")
        print(f"   📁 Saved to: {output_path}")
        
        return df
    
    def _print_summary(self, customers_df, products_df, transactions_df):
        """Print dataset summary"""
        print("\n" + "="*80)
        print("📈 DATASET SUMMARY")
        print("="*80)
        
        print(f"\n👥 CUSTOMERS: {len(customers_df):,}")
        print("\nPersona Distribution:")
        for persona, config in self.persona_configs.items():
            count = len(customers_df[customers_df['true_persona'] == persona])
            pct = (count / len(customers_df)) * 100
            print(f"   {config['emoji']} {persona.replace('_', ' ')}: {count:,} ({pct:.1f}%)")
        
        print(f"\n💳 PRODUCTS: {len(products_df)}")
        print("\nProduct Categories:")
        for category in products_df['category'].unique():
            count = len(products_df[products_df['category'] == category])
            print(f"   • {category}: {count}")
        
        print(f"\n💸 TRANSACTIONS: {len(transactions_df):,}")
        print(f"   • Avg per customer: {len(transactions_df) / len(customers_df):.1f}")
        
        print(f"\n📊 Customer Statistics:")
        print(f"   • Avg Age: {customers_df['age'].mean():.1f} years")
        print(f"   • Avg Income: ${customers_df['income'].mean():,.0f}")
        print(f"   • Avg Balance: ${customers_df['account_balance'].mean():,.0f}")
        print(f"   • Avg Credit Score: {customers_df['credit_score'].mean():.0f}")
        print(f"   • Avg Intent Score: {customers_df['intent_score'].mean():.2f}")
        
        print("\n" + "="*80)
        print("✅ Dataset generation complete!")
        print("="*80)
        print("\n📝 Next Steps:")
        print("   1. Load dataset via Data Loader UI (/banking/data-loader)")
        print("   2. Run Agent A for customer segmentation (/banking/agent-a)")
        print("   3. View macro/micro segments (/banking/macro-dashboard)")
        print("   4. Generate product recommendations (/banking/agent-b)")
        print("\n")

if __name__ == '__main__':
    generator = BankingDataGenerator5000()
    generator.generate_dataset()

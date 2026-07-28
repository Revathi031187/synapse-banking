"""
Banking Platform - Product Catalog Generator
Generates synthetic banking product catalog with detailed attributes
"""

import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

class BankingProductsGenerator:
    """Generate banking product catalog"""
    
    def __init__(self):
        self.output_dir = Path("data/preloaded/banking")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_products(self):
        """Generate all banking products"""
        print("="*70)
        print("💳 BANKING PRODUCTS CATALOG GENERATOR")
        print("="*70)
        
        products = []
        product_id = 1
        
        # 1. Credit Cards (15 products)
        print("\n💳 Generating Credit Cards...")
        products.extend(self._generate_credit_cards(product_id))
        product_id += 15
        
        # 2. Personal Loans (10 products)
        print("💰 Generating Personal Loans...")
        products.extend(self._generate_personal_loans(product_id))
        product_id += 10
        
        # 3. Savings & Checking Accounts (12 products)
        print("🏦 Generating Accounts...")
        products.extend(self._generate_accounts(product_id))
        product_id += 12
        
        # 4. Mortgage & Home Loans (8 products)
        print("🏠 Generating Mortgages...")
        products.extend(self._generate_mortgages(product_id))
        product_id += 8
        
        # 5. Investment Products (10 products)
        print("📈 Generating Investment Products...")
        products.extend(self._generate_investments(product_id))
        product_id += 10
        
        # 6. Business Banking (5 products)
        print("🏢 Generating Business Products...")
        products.extend(self._generate_business_products(product_id))
        
        df = pd.DataFrame(products)
        
        # Save
        output_path = self.output_dir / "products.csv"
        df.to_csv(output_path, index=False)
        
        print(f"\n✅ Generated {len(df)} products")
        print(f"   Saved to: {output_path}")
        
        self._print_summary(df)
        
        return df
    
    def _generate_credit_cards(self, start_id):
        """Generate credit card products"""
        cards = []
        
        card_types = [
            # Basic/Mass Market
            {"name": "Basic Cashback Card", "tier": "basic", "annual_fee": 0, "apr_min": 16.99, "apr_max": 24.99, "rewards_rate": 1.0, "bonus": 0, "min_score": 620},
            {"name": "Student Rewards Card", "tier": "basic", "annual_fee": 0, "apr_min": 17.99, "apr_max": 25.99, "rewards_rate": 1.0, "bonus": 50, "min_score": 600},
            {"name": "Everyday Cash Card", "tier": "basic", "annual_fee": 0, "apr_min": 15.99, "apr_max": 23.99, "rewards_rate": 1.5, "bonus": 100, "min_score": 640},
            
            # Mid-Tier
            {"name": "Premium Cashback Card", "tier": "premium", "annual_fee": 95, "apr_min": 13.99, "apr_max": 21.99, "rewards_rate": 2.0, "bonus": 200, "min_score": 680},
            {"name": "Travel Rewards Card", "tier": "premium", "annual_fee": 95, "apr_min": 14.99, "apr_max": 22.99, "rewards_rate": 2.0, "bonus": 300, "min_score": 700},
            {"name": "Dining & Entertainment Card", "tier": "premium", "annual_fee": 75, "apr_min": 14.49, "apr_max": 22.49, "rewards_rate": 3.0, "bonus": 150, "min_score": 690},
            {"name": "Gas & Grocery Rewards", "tier": "premium", "annual_fee": 0, "apr_min": 15.49, "apr_max": 23.49, "rewards_rate": 3.0, "bonus": 200, "min_score": 680},
            
            # Premium/HNW
            {"name": "Platinum Rewards Card", "tier": "platinum", "annual_fee": 195, "apr_min": 12.99, "apr_max": 20.99, "rewards_rate": 3.0, "bonus": 500, "min_score": 740},
            {"name": "Elite Travel Card", "tier": "platinum", "annual_fee": 450, "apr_min": 12.49, "apr_max": 19.99, "rewards_rate": 4.0, "bonus": 750, "min_score": 760},
            {"name": "Luxury Lifestyle Card", "tier": "platinum", "annual_fee": 550, "apr_min": 11.99, "apr_max": 18.99, "rewards_rate": 5.0, "bonus": 1000, "min_score": 780},
            
            # Business
            {"name": "Small Business Cash Card", "tier": "business", "annual_fee": 0, "apr_min": 14.99, "apr_max": 22.99, "rewards_rate": 1.5, "bonus": 200, "min_score": 680},
            {"name": "Business Travel Rewards", "tier": "business", "annual_fee": 95, "apr_min": 13.99, "apr_max": 21.99, "rewards_rate": 2.0, "bonus": 500, "min_score": 700},
            {"name": "Corporate Elite Card", "tier": "business", "annual_fee": 195, "apr_min": 12.99, "apr_max": 20.99, "rewards_rate": 3.0, "bonus": 750, "min_score": 720},
            
            # Specialty
            {"name": "Balance Transfer Card", "tier": "specialty", "annual_fee": 0, "apr_min": 0, "apr_max": 18.99, "rewards_rate": 0, "bonus": 0, "min_score": 690},
            {"name": "Low APR Card", "tier": "specialty", "annual_fee": 0, "apr_min": 9.99, "apr_max": 16.99, "rewards_rate": 0, "bonus": 0, "min_score": 720},
        ]
        
        for i, card in enumerate(card_types):
            cards.append({
                'product_id': f"PROD_{start_id + i:05d}",
                'product_name': card['name'],
                'category': 'Credit Cards',
                'subcategory': card['tier'].title(),
                'brand': np.random.choice(['Visa', 'Mastercard', 'American Express'], p=[0.5, 0.4, 0.1]),
                'annual_fee': card['annual_fee'],
                'apr_min': card['apr_min'],
                'apr_max': card['apr_max'],
                'rewards_rate': card['rewards_rate'],
                'sign_up_bonus': card['bonus'],
                'min_credit_score': card['min_score'],
                'complexity_score': np.random.randint(1, 4),
                'cross_sell_affinity': np.random.choice(['Checking', 'Savings', 'Investment'], p=[0.5, 0.3, 0.2]),
                'digital_enabled': True,
                'avg_approval_rate': np.random.uniform(0.50, 0.85),
                'customer_satisfaction': np.random.uniform(4.0, 4.8),
                'accepting_applications': np.random.choice([True, False], p=[0.90, 0.10])
            })
        
        return cards
    
    def _generate_personal_loans(self, start_id):
        """Generate personal loan products"""
        loans = []
        
        loan_types = [
            {"name": "Quick Personal Loan", "apr_min": 8.99, "apr_max": 15.99, "term": 24, "max_amount": 15000, "min_score": 640, "origination": 2.0},
            {"name": "Debt Consolidation Loan", "apr_min": 7.99, "apr_max": 14.99, "term": 36, "max_amount": 35000, "min_score": 660, "origination": 3.0},
            {"name": "Home Improvement Loan", "apr_min": 6.99, "apr_max": 12.99, "term": 60, "max_amount": 50000, "min_score": 680, "origination": 2.5},
            {"name": "Medical Expense Loan", "apr_min": 7.49, "apr_max": 13.49, "term": 36, "max_amount": 25000, "min_score": 650, "origination": 1.5},
            {"name": "Wedding Loan", "apr_min": 8.49, "apr_max": 14.49, "term": 24, "max_amount": 20000, "min_score": 660, "origination": 2.0},
            {"name": "Vacation Loan", "apr_min": 9.49, "apr_max": 16.49, "term": 12, "max_amount": 10000, "min_score": 640, "origination": 2.5},
            {"name": "Large Purchase Loan", "apr_min": 7.99, "apr_max": 13.99, "term": 48, "max_amount": 40000, "min_score": 680, "origination": 2.0},
            {"name": "Emergency Cash Loan", "apr_min": 10.99, "apr_max": 18.99, "term": 12, "max_amount": 5000, "min_score": 620, "origination": 3.5},
            {"name": "Premium Personal Loan", "apr_min": 5.99, "apr_max": 10.99, "term": 60, "max_amount": 75000, "min_score": 740, "origination": 1.0},
            {"name": "Flexible Term Loan", "apr_min": 7.49, "apr_max": 13.49, "term": 36, "max_amount": 30000, "min_score": 670, "origination": 2.0},
        ]
        
        for i, loan in enumerate(loan_types):
            loans.append({
                'product_id': f"PROD_{start_id + i:05d}",
                'product_name': loan['name'],
                'category': 'Personal Loans',
                'subcategory': 'Unsecured',
                'brand': 'Bank Lending',
                'annual_fee': 0,
                'apr_min': loan['apr_min'],
                'apr_max': loan['apr_max'],
                'term_months': loan['term'],
                'max_amount': loan['max_amount'],
                'min_credit_score': loan['min_score'],
                'origination_fee_pct': loan['origination'],
                'complexity_score': np.random.randint(2, 4),
                'cross_sell_affinity': np.random.choice(['Checking', 'Credit Card', 'Insurance'], p=[0.5, 0.3, 0.2]),
                'digital_enabled': True,
                'avg_approval_rate': np.random.uniform(0.40, 0.70),
                'customer_satisfaction': np.random.uniform(3.8, 4.6),
                'accepting_applications': True
            })
        
        return loans
    
    def _generate_accounts(self, start_id):
        """Generate checking and savings accounts"""
        accounts = []
        
        account_types = [
            # Checking
            {"name": "Basic Checking", "type": "Checking", "monthly_fee": 0, "min_balance": 0, "interest": 0, "overdraft": 35, "atm_fee": 2.50},
            {"name": "Interest Checking", "type": "Checking", "monthly_fee": 12, "min_balance": 1500, "interest": 0.25, "overdraft": 30, "atm_fee": 0},
            {"name": "Premium Checking", "type": "Checking", "monthly_fee": 25, "min_balance": 5000, "interest": 0.50, "overdraft": 0, "atm_fee": 0},
            {"name": "Student Checking", "type": "Checking", "monthly_fee": 0, "min_balance": 0, "interest": 0.10, "overdraft": 25, "atm_fee": 2.00},
            
            # Savings
            {"name": "Basic Savings", "type": "Savings", "monthly_fee": 5, "min_balance": 100, "interest": 0.50, "overdraft": 0, "atm_fee": 2.50},
            {"name": "High-Yield Savings", "type": "Savings", "monthly_fee": 0, "min_balance": 10000, "interest": 4.50, "overdraft": 0, "atm_fee": 0},
            {"name": "Money Market Account", "type": "Savings", "monthly_fee": 10, "min_balance": 5000, "interest": 3.75, "overdraft": 0, "atm_fee": 0},
            {"name": "Youth Savings", "type": "Savings", "monthly_fee": 0, "min_balance": 25, "interest": 0.75, "overdraft": 0, "atm_fee": 0},
            
            # CDs
            {"name": "6-Month CD", "type": "CD", "monthly_fee": 0, "min_balance": 1000, "interest": 4.00, "overdraft": 0, "atm_fee": 0},
            {"name": "1-Year CD", "type": "CD", "monthly_fee": 0, "min_balance": 1000, "interest": 4.50, "overdraft": 0, "atm_fee": 0},
            {"name": "3-Year CD", "type": "CD", "monthly_fee": 0, "min_balance": 5000, "interest": 4.75, "overdraft": 0, "atm_fee": 0},
            {"name": "5-Year CD", "type": "CD", "monthly_fee": 0, "min_balance": 10000, "interest": 5.00, "overdraft": 0, "atm_fee": 0},
        ]
        
        for i, acct in enumerate(account_types):
            accounts.append({
                'product_id': f"PROD_{start_id + i:05d}",
                'product_name': acct['name'],
                'category': 'Accounts',
                'subcategory': acct['type'],
                'brand': 'Bank Account',
                'monthly_fee': acct['monthly_fee'],
                'min_balance': acct['min_balance'],
                'interest_rate': acct['interest'],
                'overdraft_fee': acct['overdraft'],
                'atm_fee': acct['atm_fee'],
                'complexity_score': np.random.randint(1, 3),
                'cross_sell_affinity': 'Credit Card',
                'digital_enabled': True,
                'avg_approval_rate': 0.95,
                'customer_satisfaction': np.random.uniform(4.0, 4.7),
                'accepting_applications': True
            })
        
        return accounts
    
    def _generate_mortgages(self, start_id):
        """Generate mortgage products"""
        mortgages = []
        
        mortgage_types = [
            {"name": "30-Year Fixed Mortgage", "term": 30, "apr_min": 6.25, "apr_max": 7.50, "down_pct": 20, "closing": 3000},
            {"name": "15-Year Fixed Mortgage", "term": 15, "apr_min": 5.75, "apr_max": 7.00, "down_pct": 20, "closing": 3000},
            {"name": "FHA Loan", "term": 30, "apr_min": 6.00, "apr_max": 7.25, "down_pct": 3.5, "closing": 2500},
            {"name": "VA Loan", "term": 30, "apr_min": 5.75, "apr_max": 7.00, "down_pct": 0, "closing": 2000},
            {"name": "5/1 ARM", "term": 30, "apr_min": 5.50, "apr_max": 6.75, "down_pct": 20, "closing": 3000},
            {"name": "Jumbo Mortgage", "term": 30, "apr_min": 6.50, "apr_max": 7.75, "down_pct": 25, "closing": 5000},
            {"name": "HELOC", "term": 10, "apr_min": 7.00, "apr_max": 9.00, "down_pct": 0, "closing": 500},
            {"name": "Refinance Mortgage", "term": 30, "apr_min": 6.00, "apr_max": 7.25, "down_pct": 0, "closing": 3500},
        ]
        
        for i, mtg in enumerate(mortgage_types):
            mortgages.append({
                'product_id': f"PROD_{start_id + i:05d}",
                'product_name': mtg['name'],
                'category': 'Mortgages',
                'subcategory': 'Home Loans',
                'brand': 'Bank Lending',
                'annual_fee': 0,
                'apr_min': mtg['apr_min'],
                'apr_max': mtg['apr_max'],
                'term_years': mtg['term'],
                'down_payment_pct': mtg['down_pct'],
                'closing_costs': mtg['closing'],
                'min_credit_score': 680,
                'complexity_score': np.random.randint(3, 5),
                'cross_sell_affinity': 'Insurance',
                'digital_enabled': True,
                'avg_approval_rate': np.random.uniform(0.55, 0.75),
                'customer_satisfaction': np.random.uniform(4.1, 4.6),
                'accepting_applications': True
            })
        
        return mortgages
    
    def _generate_investments(self, start_id):
        """Generate investment products"""
        investments = []
        
        investment_types = [
            {"name": "Standard Brokerage Account", "mgmt_fee": 0.00, "min_invest": 0, "risk": "Moderate", "return": 7.5},
            {"name": "Managed Portfolio", "mgmt_fee": 0.50, "min_invest": 10000, "risk": "Moderate", "return": 8.0},
            {"name": "Robo-Advisor Basic", "mgmt_fee": 0.25, "min_invest": 500, "risk": "Conservative", "return": 6.5},
            {"name": "Robo-Advisor Premium", "mgmt_fee": 0.35, "min_invest": 5000, "risk": "Moderate", "return": 8.5},
            {"name": "Traditional IRA", "mgmt_fee": 0.30, "min_invest": 1000, "risk": "Moderate", "return": 7.8},
            {"name": "Roth IRA", "mgmt_fee": 0.30, "min_invest": 1000, "risk": "Moderate", "return": 7.8},
            {"name": "401k Rollover IRA", "mgmt_fee": 0.40, "min_invest": 5000, "risk": "Moderate", "return": 8.2},
            {"name": "Wealth Management", "mgmt_fee": 1.00, "min_invest": 250000, "risk": "Aggressive", "return": 10.0},
            {"name": "Index Fund Portfolio", "mgmt_fee": 0.15, "min_invest": 1000, "risk": "Moderate", "return": 8.0},
            {"name": "ESG Investment Account", "mgmt_fee": 0.45, "min_invest": 5000, "risk": "Moderate", "return": 7.5},
        ]
        
        for i, inv in enumerate(investment_types):
            investments.append({
                'product_id': f"PROD_{start_id + i:05d}",
                'product_name': inv['name'],
                'category': 'Investments',
                'subcategory': 'Investment Accounts',
                'brand': 'Bank Investment Services',
                'management_fee_pct': inv['mgmt_fee'],
                'min_investment': inv['min_invest'],
                'risk_level': inv['risk'],
                'expected_return_pct': inv['return'],
                'complexity_score': np.random.randint(3, 5),
                'cross_sell_affinity': 'Retirement Planning',
                'digital_enabled': True,
                'avg_approval_rate': 0.85,
                'customer_satisfaction': np.random.uniform(4.2, 4.8),
                'accepting_applications': True
            })
        
        return investments
    
    def _generate_business_products(self, start_id):
        """Generate business banking products"""
        business = []
        
        business_types = [
            {"name": "Business Checking", "monthly_fee": 15, "transaction_limit": 200, "rewards": None},
            {"name": "Premium Business Checking", "monthly_fee": 35, "transaction_limit": 500, "rewards": "1% cashback"},
            {"name": "Business Savings", "monthly_fee": 10, "transaction_limit": 6, "rewards": None},
            {"name": "Business Credit Card", "monthly_fee": 0, "transaction_limit": None, "rewards": "2% cashback"},
            {"name": "SBA 7(a) Loan", "monthly_fee": 0, "transaction_limit": None, "rewards": None},
        ]
        
        for i, biz in enumerate(business_types):
            business.append({
                'product_id': f"PROD_{start_id + i:05d}",
                'product_name': biz['name'],
                'category': 'Business Banking',
                'subcategory': 'Business Accounts',
                'brand': 'Business Banking',
                'monthly_fee': biz['monthly_fee'],
                'transaction_limit': biz['transaction_limit'] if biz['transaction_limit'] else 0,
                'rewards_structure': biz['rewards'] if biz['rewards'] else 'None',
                'complexity_score': np.random.randint(2, 4),
                'cross_sell_affinity': 'Merchant Services',
                'digital_enabled': True,
                'avg_approval_rate': np.random.uniform(0.60, 0.80),
                'customer_satisfaction': np.random.uniform(4.0, 4.5),
                'accepting_applications': True
            })
        
        return business
    
    def _print_summary(self, df):
        """Print summary statistics"""
        print("\n" + "="*70)
        print("📊 PRODUCT CATALOG SUMMARY")
        print("="*70)
        
        print(f"\n📦 Product Distribution by Category:")
        category_counts = df['category'].value_counts()
        for category, count in category_counts.items():
            print(f"   {category:20s}: {count:3d} products")
        
        print("\n" + "="*70)


if __name__ == "__main__":
    generator = BankingProductsGenerator()
    products_df = generator.generate_products()
    print("\n✅ Banking products catalog generation complete!")

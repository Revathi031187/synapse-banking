"""
Banking Platform - Customer Data Generator
Generates synthetic banking customer dataset with Databricks-aligned personas
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path
from faker import Faker

np.random.seed(42)
random.seed(42)

class BankingDataGenerator:
    """Generate synthetic banking customer data with behavioral attributes"""
    
    def __init__(self, n_customers=5000):
        self.n_customers = n_customers
        self.output_dir = Path("data/preloaded/banking")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fake = Faker()
        Faker.seed(42)
        
        self.persona_types = {
            'High_Net_Worth': 0.15,      # 15% - Affluent investors
            'Young_Professional': 0.25,  # 25% - Growing careers
            'Small_Business': 0.10,      # 10% - Business owners
            'Mass_Market': 0.35,         # 35% - Mainstream customers
            'Digital_Native': 0.15       # 15% - Gen Z/Millennial digital-first
        }
        
    def generate_customers(self):
        """Generate customer profiles with banking-specific attributes"""
        print("="*70)
        print("🏦 BANKING CUSTOMER DATA GENERATOR")
        print("="*70)
        
        # Determine persona distribution
        persona_labels = list(self.persona_types.keys())
        persona_probs = list(self.persona_types.values())
        
        persona_assignments = np.random.choice(
            persona_labels,
            size=self.n_customers,
            p=persona_probs
        )
        
        customers = []
        base_date = datetime.now() - timedelta(days=730)  # 2 years ago
        
        for i, persona in enumerate(persona_assignments):
            customer_id = f"CUST_{i+1:05d}"
            
            if persona == 'High_Net_Worth':
                customer = self._generate_hnw_customer(customer_id, base_date)
            elif persona == 'Young_Professional':
                customer = self._generate_young_pro_customer(customer_id, base_date)
            elif persona == 'Small_Business':
                customer = self._generate_business_customer(customer_id, base_date)
            elif persona == 'Mass_Market':
                customer = self._generate_mass_market_customer(customer_id, base_date)
            else:  # Digital_Native
                customer = self._generate_digital_native_customer(customer_id, base_date)
            
            customers.append(customer)
        
        df = pd.DataFrame(customers)
        
        # Save
        output_path = self.output_dir / "customers.csv"
        df.to_csv(output_path, index=False)
        
        print(f"\n✅ Generated {len(df)} customers")
        print(f"   Saved to: {output_path}")
        
        # Summary statistics
        self._print_summary(df)
        
        return df
    
    def _generate_hnw_customer(self, customer_id, base_date):
        """High Net Worth customer - affluent, multi-product, investment-focused"""
        return {
            'customer_id': customer_id,
            'customer_name': self.fake.name(),
            'age': np.random.randint(45, 70),
            'income': np.random.randint(150000, 500000),
            'credit_score': np.random.randint(740, 850),
            'account_tenure_months': np.random.randint(60, 240),
            'geographic_region': np.random.choice(['Urban', 'Suburban'], p=[0.6, 0.4]),
            'home_ownership': np.random.choice(['Own', 'Mortgage'], p=[0.7, 0.3]),
            'life_stage': np.random.choice(['Pre-Retiree', 'Retiree', 'Family'], p=[0.4, 0.3, 0.3]),
            
            # Banking Behavior (KEY CLUSTERING VARIABLES)
            'digital_engagement_score': np.random.uniform(0.5, 0.8),
            'branch_visit_frequency': np.random.uniform(0.3, 0.7),
            'product_adoption_velocity': np.random.uniform(0.6, 0.9),
            'cross_sell_receptivity': np.random.uniform(0.7, 1.0),
            'risk_tolerance': np.random.choice(['Moderate', 'Aggressive'], p=[0.6, 0.4]),
            'channel_preference': np.random.choice(['Hybrid', 'Branch'], p=[0.7, 0.3]),
            
            # Financial Metrics
            'total_deposits': np.random.uniform(250000, 2000000),
            'total_loan_balance': np.random.uniform(0, 500000),
            'monthly_transaction_volume': np.random.randint(50, 150),
            'avg_daily_balance': np.random.uniform(150000, 1000000),
            'overdraft_frequency': 0,
            'credit_utilization_ratio': np.random.uniform(0.05, 0.25),
            
            # Derived
            'num_products': np.random.randint(5, 9),
            'relationship_length_years': np.random.randint(5, 20),
            'join_date': (base_date + timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d'),
            'true_persona': 'High_Net_Worth'
        }
    
    def _generate_young_pro_customer(self, customer_id, base_date):
        """Young Professional - digital-first, credit building, growing income"""
        return {
            'customer_id': customer_id,
            'customer_name': self.fake.name(),
            'age': np.random.randint(25, 35),
            'income': np.random.randint(50000, 100000),
            'credit_score': np.random.randint(680, 780),
            'account_tenure_months': np.random.randint(12, 60),
            'geographic_region': np.random.choice(['Urban', 'Suburban'], p=[0.8, 0.2]),
            'home_ownership': np.random.choice(['Rent', 'Mortgage'], p=[0.7, 0.3]),
            'life_stage': 'Young Professional',
            
            # Banking Behavior
            'digital_engagement_score': np.random.uniform(0.8, 1.0),
            'branch_visit_frequency': np.random.uniform(0.0, 0.2),
            'product_adoption_velocity': np.random.uniform(0.5, 0.8),
            'cross_sell_receptivity': np.random.uniform(0.6, 0.9),
            'risk_tolerance': np.random.choice(['Moderate', 'Aggressive'], p=[0.7, 0.3]),
            'channel_preference': np.random.choice(['Digital', 'Hybrid'], p=[0.8, 0.2]),
            
            # Financial Metrics
            'total_deposits': np.random.uniform(5000, 50000),
            'total_loan_balance': np.random.uniform(0, 50000),
            'monthly_transaction_volume': np.random.randint(80, 200),
            'avg_daily_balance': np.random.uniform(2000, 25000),
            'overdraft_frequency': np.random.randint(0, 3),
            'credit_utilization_ratio': np.random.uniform(0.20, 0.50),
            
            # Derived
            'num_products': np.random.randint(2, 5),
            'relationship_length_years': np.random.randint(1, 5),
            'join_date': (base_date + timedelta(days=np.random.randint(365, 730))).strftime('%Y-%m-%d'),
            'true_persona': 'Young_Professional'
        }
    
    def _generate_business_customer(self, customer_id, base_date):
        """Small Business Owner - business accounts, high transaction volume"""
        return {
            'customer_id': customer_id,
            'customer_name': self.fake.name(),
            'age': np.random.randint(35, 60),
            'income': np.random.randint(80000, 200000),
            'credit_score': np.random.randint(700, 800),
            'account_tenure_months': np.random.randint(24, 120),
            'geographic_region': np.random.choice(['Urban', 'Suburban', 'Rural'], p=[0.5, 0.4, 0.1]),
            'home_ownership': np.random.choice(['Own', 'Mortgage'], p=[0.6, 0.4]),
            'life_stage': 'Family',
            
            # Banking Behavior
            'digital_engagement_score': np.random.uniform(0.6, 0.9),
            'branch_visit_frequency': np.random.uniform(0.4, 0.8),
            'product_adoption_velocity': np.random.uniform(0.5, 0.8),
            'cross_sell_receptivity': np.random.uniform(0.6, 0.9),
            'risk_tolerance': 'Moderate',
            'channel_preference': 'Hybrid',
            
            # Financial Metrics
            'total_deposits': np.random.uniform(50000, 500000),
            'total_loan_balance': np.random.uniform(25000, 300000),
            'monthly_transaction_volume': np.random.randint(200, 800),
            'avg_daily_balance': np.random.uniform(25000, 250000),
            'overdraft_frequency': np.random.randint(0, 2),
            'credit_utilization_ratio': np.random.uniform(0.30, 0.60),
            
            # Derived
            'num_products': np.random.randint(4, 8),
            'relationship_length_years': np.random.randint(2, 10),
            'join_date': (base_date + timedelta(days=np.random.randint(180, 550))).strftime('%Y-%m-%d'),
            'true_persona': 'Small_Business'
        }
    
    def _generate_mass_market_customer(self, customer_id, base_date):
        """Mass Market - savings-focused, price-sensitive, basic needs"""
        return {
            'customer_id': customer_id,
            'customer_name': self.fake.name(),
            'age': np.random.randint(25, 65),
            'income': np.random.randint(30000, 60000),
            'credit_score': np.random.randint(620, 720),
            'account_tenure_months': np.random.randint(12, 120),
            'geographic_region': np.random.choice(['Urban', 'Suburban', 'Rural'], p=[0.3, 0.5, 0.2]),
            'home_ownership': np.random.choice(['Rent', 'Own', 'Mortgage'], p=[0.4, 0.3, 0.3]),
            'life_stage': np.random.choice(['Young Professional', 'Family', 'Pre-Retiree'], p=[0.3, 0.5, 0.2]),
            
            # Banking Behavior
            'digital_engagement_score': np.random.uniform(0.3, 0.7),
            'branch_visit_frequency': np.random.uniform(0.2, 0.6),
            'product_adoption_velocity': np.random.uniform(0.1, 0.4),
            'cross_sell_receptivity': np.random.uniform(0.2, 0.5),
            'risk_tolerance': np.random.choice(['Conservative', 'Moderate'], p=[0.7, 0.3]),
            'channel_preference': np.random.choice(['Digital', 'Branch', 'Hybrid'], p=[0.5, 0.3, 0.2]),
            
            # Financial Metrics
            'total_deposits': np.random.uniform(1000, 25000),
            'total_loan_balance': np.random.uniform(0, 15000),
            'monthly_transaction_volume': np.random.randint(20, 80),
            'avg_daily_balance': np.random.uniform(500, 10000),
            'overdraft_frequency': np.random.randint(0, 6),
            'credit_utilization_ratio': np.random.uniform(0.40, 0.80),
            
            # Derived
            'num_products': np.random.randint(1, 3),
            'relationship_length_years': np.random.randint(1, 10),
            'join_date': (base_date + timedelta(days=np.random.randint(0, 730))).strftime('%Y-%m-%d'),
            'true_persona': 'Mass_Market'
        }
    
    def _generate_digital_native_customer(self, customer_id, base_date):
        """Digital Native - Gen Z/Millennial, mobile-first, tech-savvy"""
        return {
            'customer_id': customer_id,
            'customer_name': self.fake.name(),
            'age': np.random.randint(18, 30),
            'income': np.random.randint(25000, 65000),
            'credit_score': np.random.randint(650, 750),
            'account_tenure_months': np.random.randint(3, 36),
            'geographic_region': np.random.choice(['Urban', 'Suburban'], p=[0.7, 0.3]),
            'home_ownership': np.random.choice(['Rent', 'Own'], p=[0.9, 0.1]),
            'life_stage': np.random.choice(['Student', 'Young Professional'], p=[0.3, 0.7]),
            
            # Banking Behavior
            'digital_engagement_score': np.random.uniform(0.9, 1.0),
            'branch_visit_frequency': np.random.uniform(0.0, 0.1),
            'product_adoption_velocity': np.random.uniform(0.6, 0.9),
            'cross_sell_receptivity': np.random.uniform(0.5, 0.8),
            'risk_tolerance': np.random.choice(['Moderate', 'Aggressive'], p=[0.6, 0.4]),
            'channel_preference': 'Digital',
            
            # Financial Metrics
            'total_deposits': np.random.uniform(500, 15000),
            'total_loan_balance': np.random.uniform(0, 25000),
            'monthly_transaction_volume': np.random.randint(100, 300),
            'avg_daily_balance': np.random.uniform(200, 8000),
            'overdraft_frequency': np.random.randint(0, 4),
            'credit_utilization_ratio': np.random.uniform(0.30, 0.70),
            
            # Derived
            'num_products': np.random.randint(1, 4),
            'relationship_length_years': np.random.randint(0, 3),
            'join_date': (base_date + timedelta(days=np.random.randint(365, 730))).strftime('%Y-%m-%d'),
            'true_persona': 'Digital_Native'
        }
    
    def _print_summary(self, df):
        """Print summary statistics"""
        print("\n" + "="*70)
        print("📊 CUSTOMER DATA SUMMARY")
        print("="*70)
        
        print(f"\n🎯 Persona Distribution:")
        persona_counts = df['true_persona'].value_counts()
        for persona, count in persona_counts.items():
            pct = (count / len(df)) * 100
            print(f"   {persona:20s}: {count:5d} ({pct:5.1f}%)")
        
        print(f"\n💰 Financial Metrics:")
        print(f"   Avg Income: ${df['income'].mean():,.0f}")
        print(f"   Avg Credit Score: {df['credit_score'].mean():.0f}")
        print(f"   Avg Deposits: ${df['total_deposits'].mean():,.0f}")
        print(f"   Avg Loan Balance: ${df['total_loan_balance'].mean():,.0f}")
        
        print(f"\n📱 Behavioral Metrics:")
        print(f"   Avg Digital Engagement: {df['digital_engagement_score'].mean():.2f}")
        print(f"   Avg Cross-Sell Receptivity: {df['cross_sell_receptivity'].mean():.2f}")
        print(f"   Avg Products per Customer: {df['num_products'].mean():.1f}")
        
        print("\n" + "="*70)


if __name__ == "__main__":
    generator = BankingDataGenerator(n_customers=5000)
    customers_df = generator.generate_customers()
    print("\n✅ Banking customer data generation complete!")

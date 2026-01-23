"""
Academy Sports - Version 2 Data Generator
Generates DIFFERENT patterns to test model robustness
Same structure, different distributions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path
from faker import Faker

# Different seed for different patterns
np.random.seed(2024)
random.seed(2024)

class AcademyDataGeneratorV2:
    """V2 Generator with different customer behavior patterns"""
    
    def __init__(self, n_customers=5000):
        self.n_customers = n_customers
        self.output_dir = Path("data/preloaded/academy_sports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fake = Faker()
        Faker.seed(2024)  # Different seed for different names
        
        self.camping_categories = {
            'Tents + Screen Houses': ['Instant Tents', 'Dome Tents', 'Cabin Tents', 'Backpacking Tents'],
            'Sleeping Bags + Airbeds': ['Sleeping Bags', 'Sleeping Pads', 'Air Mattresses'],
            'Campsite Cooking': ['Camp Stoves', 'Coolers', 'Camp Cookware'],
            'Flashlights + Lanterns': ['Headlamps', 'Flashlights', 'Lanterns'],
            'Hiking Backpacks': ['Day Packs', 'Multi-Day Packs'],
            'Hiking Boots': ['Hiking Boots', 'Hiking Shoes'],
            'Camp Furniture': ['Folding Chairs', 'Camp Tables']
        }
        
        self.brands = {
            'budget': ['Magellan Outdoors', 'Coleman'],
            'mid_range': ['Coleman', 'Kelty'],
            'premium': ['MSR', 'Big Agnes', 'YETI'],
            'pro_grade': ['MSR', 'YETI', 'The North Face']
        }
        
    def generate_all_data(self):
        """Generate all datasets with V2 patterns"""
        print("="*70)
        print("🏕️  ACADEMY SPORTS DATA GENERATOR V2 (Different Patterns)")
        print("="*70)
        
        print("\n📊 Generating customers with NEW patterns...")
        customers_df = self.generate_customers()
        
        print("\n🏕️  Generating products...")
        products_df = self.generate_products()
        
        print("\n🔍 Generating interactions...")
        interactions_df = self.generate_interactions_fast(customers_df, products_df)
        
        print("\n💳 Generating purchases...")
        purchases_df = self.generate_purchases(customers_df, products_df, interactions_df)
        
        print("\n🎯 Generating feature affinity...")
        feature_affinity_df = self.generate_feature_affinity()
        
        print("\n💾 Saving V2 datasets...")
        self.save_datasets(customers_df, products_df, interactions_df, purchases_df, feature_affinity_df)
        
        self.generate_summary(customers_df, products_df, interactions_df, purchases_df)
        
        return {
            'customers': customers_df,
            'products': products_df,
            'interactions': interactions_df,
            'purchases': purchases_df,
            'feature_affinity': feature_affinity_df
        }
    
    def generate_customers(self):
        """Generate customers with DIFFERENT persona distributions"""
        # V2: More balanced distribution (vs V1 which was Novice-heavy)
        persona_types = np.random.choice(
            ['Novice', 'Family_Socializer', 'Seasoned_Pro'],
            size=self.n_customers,
            p=[0.30, 0.40, 0.30]  # V2: More Family, balanced Novice/Pro
        )
        
        # Generate all names at once (much faster than in loop)
        print("  Generating customer names...")
        customer_names = [self.fake.name() for _ in range(self.n_customers)]
        print("  Names generated!")
        
        customers = []
        base_date = datetime.now() - timedelta(days=365)
        
        for i, persona in enumerate(persona_types):
            customer_id = f"CUST_{i+1:05d}"
            customer_name = customer_names[i]
            
            if persona == 'Novice':
                # V2: Novices have slightly higher income and engagement
                customer = {
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'age': np.random.randint(25, 45),  # Slightly older
                    'income': np.random.randint(45000, 85000),  # Higher income
                    'distance_to_store': np.random.uniform(2, 12),  # Closer to stores
                    'customer_since': (base_date + timedelta(days=np.random.randint(180, 365))).strftime('%Y-%m-%d'),
                    'email_subscriber': np.random.choice([True, False], p=[0.7, 0.3]),  # Higher subscription
                    'loyalty_member': np.random.choice([True, False], p=[0.5, 0.5]),  # Higher loyalty
                    'preferred_contact': np.random.choice(['email', 'sms', 'phone'], p=[0.7, 0.2, 0.1]),
                    'marketing_consent': np.random.choice([True, False], p=[0.75, 0.25]),
                    'persona_actual': persona
                }
                
            elif persona == 'Family_Socializer':
                # V2: Family segment is larger and more engaged
                customer = {
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'age': np.random.randint(32, 52),  # Family age range
                    'income': np.random.randint(65000, 110000),  # Higher family income
                    'distance_to_store': np.random.uniform(4, 18),
                    'customer_since': (base_date + timedelta(days=np.random.randint(90, 300))).strftime('%Y-%m-%d'),
                    'email_subscriber': np.random.choice([True, False], p=[0.85, 0.15]),  # Very high
                    'loyalty_member': np.random.choice([True, False], p=[0.80, 0.20]),  # Very high
                    'preferred_contact': np.random.choice(['email', 'sms', 'phone'], p=[0.8, 0.15, 0.05]),
                    'marketing_consent': np.random.choice([True, False], p=[0.85, 0.15]),
                    'persona_actual': persona
                }
                
            else:  # Seasoned_Pro
                # V2: Pros are less extreme, more varied
                customer = {
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'age': np.random.randint(28, 55),  # Wider age range
                    'income': np.random.randint(70000, 135000),  # More varied income
                    'distance_to_store': np.random.uniform(5, 30),  # Willing to travel
                    'customer_since': (base_date + timedelta(days=np.random.randint(0, 180))).strftime('%Y-%m-%d'),
                    'email_subscriber': True,
                    'loyalty_member': np.random.choice([True, False], p=[0.85, 0.15]),  # Lower than V1
                    'preferred_contact': 'email',
                    'marketing_consent': True,
                    'persona_actual': persona
                }
            
            customers.append(customer)
        
        df = pd.DataFrame(customers)
        print(f"  ✓ Generated {len(df)} customers")
        print(f"    - Novice: {(df['persona_actual']=='Novice').sum()} (30%)")
        print(f"    - Family Socializer: {(df['persona_actual']=='Family_Socializer').sum()} (40%)")
        print(f"    - Seasoned Pro: {(df['persona_actual']=='Seasoned_Pro').sum()} (30%)")
        
        return df
    
    def generate_products(self):
        """Generate product catalog (same as V1)"""
        products = []
        product_id = 1
        
        for category, subcategories in self.camping_categories.items():
            for subcategory in subcategories:
                for brand_tier in ['budget', 'mid_range', 'premium']:
                    brand = np.random.choice(self.brands[brand_tier])
                    
                    if brand_tier == 'budget':
                        price = np.random.uniform(29, 89)
                    elif brand_tier == 'mid_range':
                        price = np.random.uniform(79, 199)
                    else:
                        price = np.random.uniform(189, 499)
                    
                    products.append({
                        'product_id': f"PROD_{product_id:04d}",
                        'product_name': f"{brand} {subcategory}",
                        'category': category,
                        'subcategory': subcategory,
                        'brand': brand,
                        'price': round(price, 2),
                        'brand_tier': brand_tier
                    })
                    product_id += 1
        
        df = pd.DataFrame(products)
        print(f"  ✓ Generated {len(df)} products across {len(self.camping_categories)} categories")
        return df
    
    def generate_interactions_fast(self, customers_df, products_df):
        """Generate interactions with DIFFERENT patterns"""
        interactions = []
        
        for _, customer in customers_df.iterrows():
            persona = customer['persona_actual']
            
            # V2: Different interaction counts
            if persona == 'Novice':
                n_interactions = np.random.randint(5, 18)  # More interactions
            elif persona == 'Family_Socializer':
                n_interactions = np.random.randint(12, 35)  # Even more
            else:  # Seasoned_Pro
                n_interactions = np.random.randint(20, 55)  # Slightly less than V1
            
            # Select products based on persona preference
            if persona == 'Novice':
                # Budget + mid-range
                product_pool = products_df[products_df['brand_tier'].isin(['budget', 'mid_range'])]
            elif persona == 'Family_Socializer':
                # Mid-range heavy
                budget_products = products_df[products_df['brand_tier'] == 'budget'].sample(n=20, replace=True)
                mid_products = products_df[products_df['brand_tier'] == 'mid_range'].sample(n=30, replace=True)
                premium_products = products_df[products_df['brand_tier'] == 'premium'].sample(n=10, replace=True)
                product_pool = pd.concat([budget_products, mid_products, premium_products])
            else:  # Seasoned_Pro
                # Premium + mid-range
                product_pool = products_df[products_df['brand_tier'].isin(['premium', 'mid_range'])]
            
            selected_products = product_pool.sample(n=min(n_interactions, len(product_pool)), replace=True)
            
            for _, product in selected_products.iterrows():
                interaction_date = datetime.now() - timedelta(days=np.random.randint(0, 365))
                
                # V2: Different time spent patterns
                if persona == 'Novice':
                    time_spent = np.random.randint(90, 480)  # More time researching
                elif persona == 'Family_Socializer':
                    time_spent = np.random.randint(180, 600)  # Longer sessions
                else:
                    time_spent = np.random.randint(120, 420)  # Efficient browsing
                
                interactions.append({
                    'interaction_id': f"INT_{len(interactions)+1:06d}",
                    'customer_id': customer['customer_id'],
                    'product_id': product['product_id'],
                    'interaction_type': np.random.choice(['view', 'click', 'add_to_cart'], p=[0.6, 0.3, 0.1]),
                    'interaction_date': interaction_date.strftime('%Y-%m-%d'),
                    'time_spent_seconds': time_spent
                })
        
        df = pd.DataFrame(interactions)
        print(f"  ✓ Generated {len(df)} interactions")
        return df
    
    def generate_purchases(self, customers_df, products_df, interactions_df):
        """Generate purchases with DIFFERENT patterns"""
        purchases = []
        
        for _, customer in customers_df.iterrows():
            persona = customer['persona_actual']
            
            # V2: Different purchase frequencies
            if persona == 'Novice':
                n_purchases = np.random.randint(1, 4)  # More purchases
            elif persona == 'Family_Socializer':
                n_purchases = np.random.randint(3, 8)  # More frequent
            else:  # Seasoned_Pro
                n_purchases = np.random.randint(4, 12)  # Slightly less
            
            customer_interactions = interactions_df[interactions_df['customer_id'] == customer['customer_id']]
            
            if len(customer_interactions) == 0:
                continue
            
            purchase_products = customer_interactions.sample(n=min(n_purchases, len(customer_interactions)), replace=True)
            
            for _, interaction in purchase_products.iterrows():
                product = products_df[products_df['product_id'] == interaction['product_id']].iloc[0]
                
                # V2: Different quantity patterns
                if persona == 'Novice':
                    quantity = np.random.choice([1, 2], p=[0.85, 0.15])  # Mostly single items
                elif persona == 'Family_Socializer':
                    quantity = np.random.choice([1, 2, 3, 4], p=[0.4, 0.35, 0.15, 0.10])  # Family bundles
                else:
                    quantity = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])  # Occasional bulk
                
                purchase_date = datetime.strptime(interaction['interaction_date'], '%Y-%m-%d') + timedelta(days=np.random.randint(0, 7))
                
                # V2: Different discount patterns
                if persona == 'Novice':
                    discount = np.random.uniform(0.05, 0.25)  # More discounts used
                elif persona == 'Family_Socializer':
                    discount = np.random.uniform(0.10, 0.30)  # Deal hunters
                else:
                    discount = np.random.uniform(0, 0.15)  # Less discount-driven
                
                total_price = product['price'] * quantity * (1 - discount)
                
                purchases.append({
                    'purchase_id': f"PUR_{len(purchases)+1:06d}",
                    'customer_id': customer['customer_id'],
                    'product_id': product['product_id'],
                    'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                    'quantity': quantity,
                    'total_price': round(total_price, 2),
                    'discount_applied': round(discount, 2)
                })
        
        df = pd.DataFrame(purchases)
        print(f"  ✓ Generated {len(df)} purchases")
        return df
    
    def generate_feature_affinity(self):
        """Generate feature affinity (same structure as V1)"""
        features = [
            'Waterproof', 'Lightweight', 'Durable', 'Portable',
            'Easy Setup', 'Family Size', 'Professional Grade',
            'Budget Friendly', 'All Season', 'Compact Storage'
        ]
        
        personas = ['Novice', 'Family_Socializer', 'Seasoned_Pro']
        
        affinity_data = []
        
        for persona in personas:
            if persona == 'Novice':
                scores = {
                    'Waterproof': 0.7, 'Lightweight': 0.5, 'Durable': 0.6,
                    'Portable': 0.7, 'Easy Setup': 0.95, 'Family Size': 0.6,
                    'Professional Grade': 0.2, 'Budget Friendly': 0.9,
                    'All Season': 0.4, 'Compact Storage': 0.7
                }
            elif persona == 'Family_Socializer':
                scores = {
                    'Waterproof': 0.8, 'Lightweight': 0.6, 'Durable': 0.85,
                    'Portable': 0.7, 'Easy Setup': 0.9, 'Family Size': 0.95,
                    'Professional Grade': 0.4, 'Budget Friendly': 0.7,
                    'All Season': 0.75, 'Compact Storage': 0.6
                }
            else:  # Seasoned_Pro
                scores = {
                    'Waterproof': 0.95, 'Lightweight': 0.9, 'Durable': 0.95,
                    'Portable': 0.85, 'Easy Setup': 0.6, 'Family Size': 0.3,
                    'Professional Grade': 0.95, 'Budget Friendly': 0.3,
                    'All Season': 0.9, 'Compact Storage': 0.85
                }
            
            for feature, score in scores.items():
                affinity_data.append({
                    'persona': persona,
                    'feature': feature,
                    'affinity_score': score
                })
        
        df = pd.DataFrame(affinity_data)
        print(f"  ✓ Generated {len(df)} feature affinity records")
        return df
    
    def save_datasets(self, customers_df, products_df, interactions_df, purchases_df, feature_affinity_df):
        """Save as V2 versions"""
        customers_df.to_csv(self.output_dir / 'customers_v2.csv', index=False)
        products_df.to_csv(self.output_dir / 'products_v2.csv', index=False)
        interactions_df.to_csv(self.output_dir / 'interactions_v2.csv', index=False)
        purchases_df.to_csv(self.output_dir / 'purchases_v2.csv', index=False)
        feature_affinity_df.to_csv(self.output_dir / 'feature_affinity_v2.csv', index=False)
        
        print(f"  ✓ All V2 datasets saved to: {self.output_dir}")
    
    def generate_summary(self, customers_df, products_df, interactions_df, purchases_df):
        """Generate summary"""
        print("\n" + "="*70)
        print("📊 V2 DATASET SUMMARY")
        print("="*70)
        print(f"👥 Customers:     {len(customers_df):,}")
        print(f"📦 Products:      {len(products_df):,}")
        print(f"🔍 Interactions:  {len(interactions_df):,}")
        print(f"💳 Purchases:     {len(purchases_df):,}")
        print("\n💰 Revenue by Persona (V2):")
        
        revenue_by_persona = purchases_df.merge(customers_df[['customer_id', 'persona_actual']], on='customer_id')
        revenue_summary = revenue_by_persona.groupby('persona_actual')['total_price'].agg(['sum', 'count', 'mean'])
        
        for persona in revenue_summary.index:
            total_rev = revenue_summary.loc[persona, 'sum']
            count = revenue_summary.loc[persona, 'count']
            avg = revenue_summary.loc[persona, 'mean']
            print(f"  {persona:20s}: ${total_rev:>10,.2f} ({count:>4} purchases, avg ${avg:>6.2f})")
        
        print("\n✅ V2 dataset generation complete!")
        print("="*70)

if __name__ == "__main__":
    generator = AcademyDataGeneratorV2(n_customers=5000)
    generator.generate_all_data()


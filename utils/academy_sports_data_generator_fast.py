"""
Academy Sports - FAST Data Generator (For Quick Testing)
Generates smaller datasets quickly for immediate use
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path
from faker import Faker

np.random.seed(42)
random.seed(42)

class FastAcademyDataGenerator:
    """Quick generator for testing"""
    
    def __init__(self, n_customers=5000):
        self.n_customers = n_customers
        self.output_dir = Path("data/preloaded/academy_sports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fake = Faker()
        Faker.seed(42)  # Consistent names for reproducibility
        
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
        """Generate all datasets QUICKLY"""
        print("="*70)
        print("🏕️  FAST ACADEMY SPORTS DATA GENERATOR")
        print("="*70)
        
        # Generate datasets
        print("\n📊 Generating customers...")
        customers_df = self.generate_customers()
        
        print("\n🏕️  Generating products...")
        products_df = self.generate_products()
        
        print("\n🔍 Generating interactions (FAST)...")
        interactions_df = self.generate_interactions_fast(customers_df, products_df)
        
        print("\n💳 Generating purchases...")
        purchases_df = self.generate_purchases(customers_df, products_df, interactions_df)
        
        print("\n🎯 Generating feature affinity...")
        feature_affinity_df = self.generate_feature_affinity()
        
        # Save
        print("\n💾 Saving datasets...")
        self.save_datasets(customers_df, products_df, interactions_df, purchases_df, feature_affinity_df)
        
        # Summary
        self.generate_summary(customers_df, products_df, interactions_df, purchases_df)
        
        return {
            'customers': customers_df,
            'products': products_df,
            'interactions': interactions_df,
            'purchases': purchases_df,
            'feature_affinity': feature_affinity_df
        }
    
    def generate_customers(self):
        """Generate customer profiles"""
        persona_types = np.random.choice(
            ['Novice', 'Family_Socializer', 'Seasoned_Pro'],
            size=self.n_customers,
            p=[0.40, 0.35, 0.25]
        )
        
        customers = []
        base_date = datetime.now() - timedelta(days=365)
        
        for i, persona in enumerate(persona_types):
            customer_id = f"CUST_{i+1:05d}"
            
            if persona == 'Novice':
                customer = {
                    'customer_id': customer_id,
                    'customer_name': self.fake.name(),
                    'age': np.random.randint(22, 40),
                    'income': np.random.randint(35000, 75000),
                    'distance_to_store': np.random.uniform(3, 15),
                    'urbanicity': np.random.choice(['Urban', 'Suburban']),
                    'climate_zone': np.random.choice(['Temperate', 'Hot', 'Cold']),
                    
                    # KEY CLUSTERING VARIABLES
                    'search_specificity': np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1]),
                    'spec_expansion_rate': np.random.uniform(0, 0.2),
                    'bundle_affinity': np.random.uniform(0.7, 1.0),
                    'price_sort_frequency': np.random.uniform(0.7, 1.0),
                    
                    'total_spend_12mo': np.random.uniform(50, 300),
                    'purchase_frequency': np.random.randint(1, 3),
                    'recency_days': np.random.randint(30, 180),
                    'avg_order_value': np.random.uniform(50, 150),
                    'dominant_category': 'Tents + Screen Houses',
                    'brand_loyalty': 'None',
                    'return_rate': np.random.uniform(0.05, 0.20),
                    'channel_preference': np.random.choice(['Web', 'Mobile', 'In-Store']),
                    'join_date': (base_date + timedelta(days=np.random.randint(0, 180))).strftime('%Y-%m-%d'),
                    'true_persona': persona
                }
            
            elif persona == 'Family_Socializer':
                customer = {
                    'customer_id': customer_id,
                    'customer_name': self.fake.name(),
                    'age': np.random.randint(35, 55),
                    'income': np.random.randint(60000, 120000),
                    'distance_to_store': np.random.uniform(5, 25),
                    'urbanicity': np.random.choice(['Suburban', 'Rural']),
                    'climate_zone': np.random.choice(['Temperate', 'Hot', 'Cold']),
                    
                    'search_specificity': np.random.choice([2, 3, 4], p=[0.2, 0.6, 0.2]),
                    'spec_expansion_rate': np.random.uniform(0.2, 0.5),
                    'bundle_affinity': np.random.uniform(0.4, 0.7),
                    'price_sort_frequency': np.random.uniform(0.3, 0.6),
                    
                    'total_spend_12mo': np.random.uniform(300, 1000),
                    'purchase_frequency': np.random.randint(2, 6),
                    'recency_days': np.random.randint(60, 240),
                    'avg_order_value': np.random.uniform(150, 400),
                    'dominant_category': np.random.choice(['Tents + Screen Houses', 'Sleeping Bags + Airbeds', 'Campsite Cooking']),
                    'brand_loyalty': np.random.choice(['Coleman', 'Magellan Outdoors', 'None']),
                    'return_rate': np.random.uniform(0.03, 0.12),
                    'channel_preference': np.random.choice(['Web', 'In-Store']),
                    'join_date': (base_date + timedelta(days=np.random.randint(180, 365))).strftime('%Y-%m-%d'),
                    'true_persona': persona
                }
            
            else:  # Seasoned_Pro
                customer = {
                    'customer_id': customer_id,
                    'customer_name': self.fake.name(),
                    'age': np.random.randint(28, 60),
                    'income': np.random.randint(70000, 150000),
                    'distance_to_store': np.random.uniform(10, 40),
                    'urbanicity': np.random.choice(['Suburban', 'Rural', 'Urban']),
                    'climate_zone': np.random.choice(['Temperate', 'Cold', 'Hot']),
                    
                    'search_specificity': np.random.choice([4, 5], p=[0.4, 0.6]),
                    'spec_expansion_rate': np.random.uniform(0.6, 1.0),
                    'bundle_affinity': np.random.uniform(0, 0.2),
                    'price_sort_frequency': np.random.uniform(0, 0.2),
                    
                    'total_spend_12mo': np.random.uniform(800, 3000),
                    'purchase_frequency': np.random.randint(5, 15),
                    'recency_days': np.random.randint(7, 90),
                    'avg_order_value': np.random.uniform(200, 600),
                    'dominant_category': np.random.choice(['Tents + Screen Houses', 'Hiking Backpacks', 'Sleeping Bags + Airbeds']),
                    'brand_loyalty': np.random.choice(['MSR', 'YETI', 'The North Face', 'Big Agnes']),
                    'return_rate': np.random.uniform(0.01, 0.08),
                    'channel_preference': np.random.choice(['Web', 'In-Store']),
                    'join_date': (base_date + timedelta(days=np.random.randint(365, 1095))).strftime('%Y-%m-%d'),
                    'true_persona': persona
                }
            
            customers.append(customer)
        
        df = pd.DataFrame(customers)
        print(f"   ✅ Generated {len(df)} customers")
        print(f"   📈 Novice: {(persona_types == 'Novice').sum()} ({(persona_types == 'Novice').sum()/len(df)*100:.1f}%)")
        print(f"   📈 Family: {(persona_types == 'Family_Socializer').sum()} ({(persona_types == 'Family_Socializer').sum()/len(df)*100:.1f}%)")
        print(f"   📈 Pro: {(persona_types == 'Seasoned_Pro').sum()} ({(persona_types == 'Seasoned_Pro').sum()/len(df)*100:.1f}%)")
        
        return df
    
    def generate_products(self):
        """Generate camping products"""
        products = []
        product_id = 1
        
        for main_category, subcategories in self.camping_categories.items():
            for subcategory in subcategories:
                n_products = 3  # Fixed 3 per subcategory for speed
                
                for _ in range(n_products):
                    brand_tier = np.random.choice(['budget', 'mid_range', 'premium', 'pro_grade'], p=[0.35, 0.35, 0.20, 0.10])
                    brand = np.random.choice(self.brands[brand_tier])
                    
                    if brand_tier == 'budget':
                        price = np.random.uniform(29.99, 99.99)
                        base_conversion = np.random.uniform(0.04, 0.08)
                    elif brand_tier == 'mid_range':
                        price = np.random.uniform(89.99, 249.99)
                        base_conversion = np.random.uniform(0.03, 0.06)
                    elif brand_tier == 'premium':
                        price = np.random.uniform(199.99, 499.99)
                        base_conversion = np.random.uniform(0.02, 0.05)
                    else:
                        price = np.random.uniform(399.99, 1299.99)
                        base_conversion = np.random.uniform(0.01, 0.04)
                    
                    if 'Tent' in subcategory:
                        capacity = np.random.choice(['2-Person', '4-Person', '6-Person', '8-Person'])
                        product_name = f"{brand} {capacity} {subcategory}"
                    else:
                        capacity = None
                        product_name = f"{brand} {subcategory}"
                    
                    setup_type = np.random.choice(['Instant Setup', 'Traditional Setup', 'Quick Assembly'])
                    complexity = np.random.choice(['Simple Design', 'Moderate Design', 'Technical Design'])
                    bundle = np.random.choice(['Bundle Compatible', 'Standalone Only'])
                    
                    product = {
                        'product_id': f"PROD_{product_id:05d}",
                        'product_name': product_name,
                        'brand': brand,
                        'brand_tier': brand_tier,
                        'main_category': main_category,
                        'subcategory': subcategory,
                        'price': round(price, 2),
                        'base_conversion_rate': round(base_conversion, 4),
                        'setup_type': setup_type,
                        'complexity': complexity,
                        'bundle_compatible': bundle,
                        'capacity': capacity,
                        'weight_class': np.random.choice(['Ultralight', 'Lightweight', 'Standard', 'Heavy-Duty']),
                        'weatherproof': np.random.choice(['Basic', 'Weather Resistant', 'All-Weather', 'Extreme Weather']),
                        'in_stock': np.random.choice([True, False], p=[0.85, 0.15]),
                        'avg_rating': round(np.random.uniform(3.5, 5.0), 1),
                        'num_reviews': np.random.randint(5, 500)
                    }
                    products.append(product)
                    product_id += 1
        
        df = pd.DataFrame(products)
        print(f"   ✅ Generated {len(df)} products across {len(self.camping_categories)} categories")
        
        return df
    
    def generate_interactions_fast(self, customers_df, products_df):
        """Generate interactions using VECTORIZED operations (FAST!)"""
        # Fixed interactions per customer for speed
        interactions_per_persona = {
            'Novice': 10,
            'Family_Socializer': 15,
            'Seasoned_Pro': 20
        }
        
        all_interactions = []
        base_date = datetime.now() - timedelta(days=365)
        
        for persona, n_interactions in interactions_per_persona.items():
            persona_customers = customers_df[customers_df['true_persona'] == persona]
            
            # Vectorized generation
            n_total = len(persona_customers) * n_interactions
            
            customer_ids = np.repeat(persona_customers['customer_id'].values, n_interactions)
            product_ids = np.random.choice(products_df['product_id'].values, size=n_total)
            
            # Timestamps
            days_ago = np.random.randint(0, 365, size=n_total)
            timestamps = [(base_date + timedelta(days=int(d))).strftime('%Y-%m-%d %H:%M:%S') for d in days_ago]
            
            # Persona-specific behaviors
            if persona == 'Novice':
                time_on_page = np.random.randint(30, 180, size=n_total)
                specs_expanded = np.random.random(size=n_total) < 0.1
                bundle_viewed = np.random.random(size=n_total) < 0.8
            elif persona == 'Family_Socializer':
                time_on_page = np.random.randint(60, 240, size=n_total)
                specs_expanded = np.random.random(size=n_total) < 0.35
                bundle_viewed = np.random.random(size=n_total) < 0.5
            else:  # Pro
                time_on_page = np.random.randint(120, 600, size=n_total)
                specs_expanded = np.random.random(size=n_total) < 0.8
                bundle_viewed = np.random.random(size=n_total) < 0.1
            
            # Create DataFrame chunk
            chunk = pd.DataFrame({
                'interaction_id': [f"INT_{np.random.randint(100000, 999999)}" for _ in range(n_total)],
                'customer_id': customer_ids,
                'product_id': product_ids,
                'timestamp': timestamps,
                'interaction_type': 'view',
                'time_on_page_seconds': time_on_page,
                'specs_expanded': specs_expanded,
                'bundle_viewed': bundle_viewed,
                'price_checked': True,
                'reviews_viewed': np.random.choice([True, False], size=n_total)
            })
            
            all_interactions.append(chunk)
        
        df = pd.concat(all_interactions, ignore_index=True)
        print(f"   ✅ Generated {len(df):,} interactions (FAST method)")
        
        return df
    
    def generate_purchases(self, customers_df, products_df, interactions_df):
        """Generate purchases with persona-based conversion"""
        # Merge to get customer and product info
        merged = interactions_df.merge(
            customers_df[['customer_id', 'true_persona', 'bundle_affinity']], 
            on='customer_id'
        ).merge(
            products_df[['product_id', 'price', 'base_conversion_rate', 'setup_type', 'complexity', 'bundle_compatible', 'brand_tier']],
            on='product_id'
        )
        
        # Vectorized conversion probability
        probabilities = np.array([
            self._calc_conversion(row) for _, row in merged.iterrows()
        ])
        
        # Random conversion
        converted = np.random.random(size=len(merged)) < probabilities
        
        purchases_df = merged[converted][['customer_id', 'product_id', 'interaction_id', 'timestamp', 'price']].copy()
        purchases_df['purchase_id'] = [f"PUR_{np.random.randint(100000, 999999)}" for _ in range(len(purchases_df))]
        purchases_df['quantity'] = 1
        purchases_df['price_paid'] = purchases_df['price']
        purchases_df.rename(columns={'timestamp': 'purchase_date'}, inplace=True)
        purchases_df['discount_applied'] = np.random.choice([0, 0.05, 0.10, 0.15], size=len(purchases_df), p=[0.6, 0.2, 0.15, 0.05])
        
        print(f"   ✅ Generated {len(purchases_df):,} purchases")
        
        return purchases_df[['purchase_id', 'customer_id', 'product_id', 'interaction_id', 'purchase_date', 'quantity', 'price_paid', 'discount_applied']]
    
    def _calc_conversion(self, row):
        """Calculate conversion probability"""
        base_logit = np.log(row['base_conversion_rate'] / (1 - row['base_conversion_rate']))
        lift = 0
        
        if row['true_persona'] == 'Novice':
            if row['setup_type'] == 'Instant Setup':
                lift += np.log(3.0)
            if row['complexity'] == 'Simple Design':
                lift += np.log(1.5)
            if row['bundle_compatible'] == 'Bundle Compatible':
                lift += np.log(2.0)
            if row['brand_tier'] == 'budget':
                lift += np.log(1.3)
        
        elif row['true_persona'] == 'Family_Socializer':
            if row['complexity'] in ['Simple Design', 'Moderate Design']:
                lift += np.log(1.3)
        
        else:  # Pro
            if row['complexity'] == 'Technical Design':
                lift += np.log(2.5)
            if row['brand_tier'] in ['premium', 'pro_grade']:
                lift += np.log(1.8)
            if row['setup_type'] == 'Instant Setup':
                lift += np.log(0.2)
            if row['bundle_compatible'] == 'Bundle Compatible':
                lift += np.log(0.1)
        
        final_logit = base_logit + lift
        probability = 1 / (1 + np.exp(-final_logit))
        return min(probability, 0.95)
    
    def generate_feature_affinity(self):
        """Generate feature lift factors"""
        feature_lifts = {
            'Novice': {
                'Instant Setup': 3.0,
                'Simple Design': 1.5,
                'Bundle Compatible': 2.0,
                'Budget Brand': 1.3,
                'Quick Assembly': 2.2,
                'Traditional Setup': 0.5,
                'Technical Design': 0.3,
                'Pro-Grade Brand': 0.4
            },
            'Family_Socializer': {
                '4+ Person Capacity': 2.0,
                'Simple Design': 1.3,
                'Moderate Design': 1.3,
                'Weather Resistant': 1.4,
                'All-Weather': 1.4,
                'Bundle Compatible': 1.2,
                'Ultralight': 0.6,
                'Technical Design': 0.7
            },
            'Seasoned_Pro': {
                'Technical Design': 2.5,
                'Ultralight': 2.0,
                'Lightweight': 2.0,
                'Premium Brand': 1.8,
                'Pro-Grade Brand': 1.8,
                'Extreme Weather': 1.6,
                'Instant Setup': 0.2,
                'Bundle Compatible': 0.1,
                'Simple Design': 0.5
            }
        }
        
        affinities = []
        for persona, features in feature_lifts.items():
            for feature, lift in features.items():
                affinities.append({
                    'persona': persona,
                    'feature': feature,
                    'lift_factor': lift,
                    'log_lift': round(np.log(lift), 4)
                })
        
        df = pd.DataFrame(affinities)
        print(f"   ✅ Generated {len(df)} feature-persona affinity mappings")
        
        return df
    
    def save_datasets(self, customers_df, products_df, interactions_df, purchases_df, feature_affinity_df):
        """Save all datasets"""
        customers_df.to_csv(self.output_dir / 'customers.csv', index=False)
        products_df.to_csv(self.output_dir / 'products.csv', index=False)
        interactions_df.to_csv(self.output_dir / 'interactions.csv', index=False)
        purchases_df.to_csv(self.output_dir / 'purchases.csv', index=False)
        feature_affinity_df.to_csv(self.output_dir / 'feature_affinity.csv', index=False)
        
        print(f"   ✅ Saved all datasets to {self.output_dir}")
    
    def generate_summary(self, customers_df, products_df, interactions_df, purchases_df):
        """Generate summary statistics"""
        print("\n" + "="*70)
        print("📊 DATA GENERATION SUMMARY")
        print("="*70)
        
        print(f"\n👥 Customers: {len(customers_df):,}")
        print(f"   - Novice: {(customers_df['true_persona'] == 'Novice').sum():,}")
        print(f"   - Family: {(customers_df['true_persona'] == 'Family_Socializer').sum():,}")
        print(f"   - Pro: {(customers_df['true_persona'] == 'Seasoned_Pro').sum():,}")
        
        print(f"\n🏕️  Products: {len(products_df):,}")
        print(f"   - Categories: {products_df['main_category'].nunique()}")
        print(f"   - Average Price: ${products_df['price'].mean():.2f}")
        
        print(f"\n🔍 Interactions: {len(interactions_df):,}")
        print(f"   - Per Customer: {len(interactions_df)/len(customers_df):.1f}")
        
        print(f"\n💳 Purchases: {len(purchases_df):,}")
        print(f"   - Overall Conversion: {len(purchases_df)/len(interactions_df)*100:.2f}%")
        print(f"   - Total Revenue: ${purchases_df['price_paid'].sum():,.2f}")
        
        print("\n" + "="*70)
        print("✅ DATA GENERATION COMPLETE!")
        print("="*70)


def main():
    """Main execution"""
    print("\n🚀 Starting FAST data generation...\n")
    generator = FastAcademyDataGenerator(n_customers=5000)
    data = generator.generate_all_data()
    
    print("\n📁 Files created:")
    print("   - data/preloaded/academy_sports/customers.csv")
    print("   - data/preloaded/academy_sports/products.csv")
    print("   - data/preloaded/academy_sports/interactions.csv")
    print("   - data/preloaded/academy_sports/purchases.csv")
    print("   - data/preloaded/academy_sports/feature_affinity.csv")
    
    return data


if __name__ == "__main__":
    main()


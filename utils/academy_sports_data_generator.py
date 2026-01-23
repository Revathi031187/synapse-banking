"""
Academy Sports Camping Personalization - Synthetic Data Generator
Generates realistic customer, product, and interaction data based on:
- Academy Sports actual camping categories
- 3 customer personas (Novice, Family Socializer, Seasoned Pro)
- K-prototypes compatible (numeric + categorical variables)
- Feature-based lift scoring system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

np.random.seed(42)
random.seed(42)

class AcademySportsDataGenerator:
    """Generate realistic Academy Sports camping personalization data"""
    
    def __init__(self, n_customers=5000):
        self.n_customers = n_customers
        self.output_dir = Path("data/preloaded/academy_sports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Academy Sports actual camping categories (from website)
        self.camping_categories = {
            'Tents + Screen Houses': ['Instant Tents', 'Dome Tents', 'Cabin Tents', 'Backpacking Tents', 'Screen Houses'],
            'Sleeping Bags + Airbeds': ['Sleeping Bags', 'Sleeping Pads', 'Air Mattresses', 'Pillows'],
            'Campsite Cooking': ['Camp Stoves', 'Coolers', 'Camp Cookware', 'Water Bottles'],
            'Flashlights + Lanterns': ['Headlamps', 'Flashlights', 'Lanterns', 'Batteries'],
            'Hiking Backpacks': ['Day Packs', 'Multi-Day Packs', 'Hydration Packs'],
            'Hiking Boots': ['Hiking Boots', 'Hiking Shoes', 'Trail Running Shoes'],
            'Camp Furniture': ['Folding Chairs', 'Camp Tables', 'Hammocks', 'Cots']
        }
        
        # Feature types for camping products
        self.product_features = {
            'setup_type': ['Instant Setup', 'Traditional Setup', 'Quick Assembly'],
            'complexity': ['Simple Design', 'Moderate Design', 'Technical Design'],
            'bundle_compatible': ['Bundle Compatible', 'Standalone Only'],
            'capacity': ['1-Person', '2-Person', '4-Person', '6-Person', '8+ Person'],
            'weight_class': ['Ultralight', 'Lightweight', 'Standard', 'Heavy-Duty'],
            'weatherproof': ['Basic', 'Weather Resistant', 'All-Weather', 'Extreme Weather'],
            'brand_tier': ['Budget', 'Mid-Range', 'Premium', 'Pro-Grade']
        }
        
        # Brand mapping (from Academy Sports)
        self.brands = {
            'budget': ['Magellan Outdoors', 'Ozark Trail', 'Coleman'],
            'mid_range': ['Coleman', 'Kelty', 'REI Co-op'],
            'premium': ['MSR', 'Big Agnes', 'YETI'],
            'pro_grade': ['MSR', 'YETI', 'The North Face', 'Arc\'teryx']
        }
        
    def generate_all_data(self):
        """Generate all datasets"""
        print("="*70)
        print("🏕️  ACADEMY SPORTS SYNTHETIC DATA GENERATOR")
        print("="*70)
        
        # Generate datasets
        customers_df = self.generate_customers()
        products_df = self.generate_products()
        interactions_df = self.generate_interactions(customers_df, products_df)
        purchases_df = self.generate_purchases(customers_df, products_df, interactions_df)
        feature_affinity_df = self.generate_feature_affinity()
        
        # Save to CSV
        self.save_datasets(customers_df, products_df, interactions_df, purchases_df, feature_affinity_df)
        
        # Generate summary
        self.generate_summary(customers_df, products_df, interactions_df, purchases_df)
        
        return {
            'customers': customers_df,
            'products': products_df,
            'interactions': interactions_df,
            'purchases': purchases_df,
            'feature_affinity': feature_affinity_df
        }
    
    def generate_customers(self):
        """Generate customer profiles with persona-specific characteristics"""
        print("\n📊 Generating 5,000 customers with 3 distinct personas...")
        
        # Persona distribution: 40% Novice, 35% Family, 25% Pro
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
                customer = self._generate_novice_customer(customer_id, base_date)
            elif persona == 'Family_Socializer':
                customer = self._generate_family_customer(customer_id, base_date)
            else:  # Seasoned_Pro
                customer = self._generate_pro_customer(customer_id, base_date)
            
            customer['true_persona'] = persona  # Ground truth for validation
            customers.append(customer)
        
        df = pd.DataFrame(customers)
        print(f"   ✅ Generated {len(df)} customers")
        print(f"   📈 Novice: {(persona_types == 'Novice').sum()} ({(persona_types == 'Novice').sum()/len(df)*100:.1f}%)")
        print(f"   📈 Family: {(persona_types == 'Family_Socializer').sum()} ({(persona_types == 'Family_Socializer').sum()/len(df)*100:.1f}%)")
        print(f"   📈 Pro: {(persona_types == 'Seasoned_Pro').sum()} ({(persona_types == 'Seasoned_Pro').sum()/len(df)*100:.1f}%)")
        
        return df
    
    def _generate_novice_customer(self, customer_id, base_date):
        """Generate First-Time Camper profile"""
        return {
            'customer_id': customer_id,
            'age': np.random.randint(22, 40),  # Younger, new to camping
            'income': np.random.randint(35000, 75000),  # Price-sensitive
            'distance_to_store': np.random.uniform(3, 15),  # Urban/suburban
            'urbanicity': np.random.choice(['Urban', 'Suburban'], p=[0.6, 0.4]),
            'climate_zone': np.random.choice(['Temperate', 'Hot', 'Cold']),
            
            # Behavioral signals (KEY FOR CLUSTERING)
            'search_specificity': np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1]),  # Generic terms
            'spec_expansion_rate': np.random.uniform(0, 0.2),  # Doesn't expand specs
            'bundle_affinity': np.random.uniform(0.7, 1.0),  # LOVES bundles
            'price_sort_frequency': np.random.uniform(0.7, 1.0),  # Always sorts by price
            
            # Purchase history (limited)
            'total_spend_12mo': np.random.uniform(50, 300),  # Low spend
            'purchase_frequency': np.random.randint(1, 3),  # 1-2 purchases
            'recency_days': np.random.randint(30, 180),
            'avg_order_value': np.random.uniform(50, 150),
            
            # Dominant category
            'dominant_category': 'Tents + Screen Houses',  # Start with tents
            'brand_loyalty': 'None',  # No brand preference
            'primary_return_reason': np.random.choice(['Size/Fit', 'Too Complex', 'Changed Mind']),
            'return_rate': np.random.uniform(0.05, 0.20),  # Higher returns (confusion)
            
            # Channel preference
            'channel_preference': np.random.choice(['Web', 'Mobile', 'In-Store'], p=[0.4, 0.4, 0.2]),
            'join_date': (base_date + timedelta(days=np.random.randint(0, 180))).strftime('%Y-%m-%d')
        }
    
    def _generate_family_customer(self, customer_id, base_date):
        """Generate Occasional Holiday Camper profile"""
        return {
            'customer_id': customer_id,
            'age': np.random.randint(35, 55),  # Family age
            'income': np.random.randint(60000, 120000),  # Comfortable income
            'distance_to_store': np.random.uniform(5, 25),  # Suburban
            'urbanicity': np.random.choice(['Suburban', 'Rural'], p=[0.7, 0.3]),
            'climate_zone': np.random.choice(['Temperate', 'Hot', 'Cold']),
            
            # Behavioral signals
            'search_specificity': np.random.choice([2, 3, 4], p=[0.2, 0.6, 0.2]),  # Moderate specificity
            'spec_expansion_rate': np.random.uniform(0.2, 0.5),  # Some research
            'bundle_affinity': np.random.uniform(0.4, 0.7),  # Likes bundles for convenience
            'price_sort_frequency': np.random.uniform(0.3, 0.6),  # Price matters but not primary
            
            # Purchase history
            'total_spend_12mo': np.random.uniform(300, 1000),  # Moderate spend
            'purchase_frequency': np.random.randint(2, 6),  # 2-5 purchases/year
            'recency_days': np.random.randint(60, 240),
            'avg_order_value': np.random.uniform(150, 400),
            
            # Category preferences
            'dominant_category': np.random.choice([
                'Tents + Screen Houses', 
                'Sleeping Bags + Airbeds',
                'Campsite Cooking'
            ]),
            'brand_loyalty': np.random.choice(['Coleman', 'Magellan Outdoors', 'None']),
            'primary_return_reason': np.random.choice(['Size/Fit', 'Quality', 'Better Price']),
            'return_rate': np.random.uniform(0.03, 0.12),
            
            'channel_preference': np.random.choice(['Web', 'In-Store'], p=[0.6, 0.4]),
            'join_date': (base_date + timedelta(days=np.random.randint(180, 365))).strftime('%Y-%m-%d')
        }
    
    def _generate_pro_customer(self, customer_id, base_date):
        """Generate Seasoned Pro profile"""
        return {
            'customer_id': customer_id,
            'age': np.random.randint(28, 60),  # Wide age range
            'income': np.random.randint(70000, 150000),  # Can afford premium
            'distance_to_store': np.random.uniform(10, 40),  # Will travel for gear
            'urbanicity': np.random.choice(['Suburban', 'Rural', 'Urban'], p=[0.4, 0.4, 0.2]),
            'climate_zone': np.random.choice(['Temperate', 'Cold', 'Hot']),
            
            # Behavioral signals (DISTINCTIVE)
            'search_specificity': np.random.choice([4, 5], p=[0.4, 0.6]),  # Model names/specs
            'spec_expansion_rate': np.random.uniform(0.6, 1.0),  # ALWAYS expands specs
            'bundle_affinity': np.random.uniform(0, 0.2),  # NO interest in bundles
            'price_sort_frequency': np.random.uniform(0, 0.2),  # Doesn't sort by price
            
            # Purchase history (extensive)
            'total_spend_12mo': np.random.uniform(800, 3000),  # High spend
            'purchase_frequency': np.random.randint(5, 15),  # Frequent buyer
            'recency_days': np.random.randint(7, 90),  # Recent
            'avg_order_value': np.random.uniform(200, 600),
            
            # Brand loyalty (STRONG)
            'dominant_category': np.random.choice([
                'Tents + Screen Houses',
                'Hiking Backpacks',
                'Sleeping Bags + Airbeds'
            ]),
            'brand_loyalty': np.random.choice(['MSR', 'YETI', 'The North Face', 'Big Agnes']),
            'primary_return_reason': np.random.choice(['Wrong Spec', 'Quality', 'Warranty']),
            'return_rate': np.random.uniform(0.01, 0.08),  # Low returns (knows what they want)
            
            'channel_preference': np.random.choice(['Web', 'In-Store'], p=[0.7, 0.3]),
            'join_date': (base_date + timedelta(days=np.random.randint(365, 1095))).strftime('%Y-%m-%d')  # Long-term customer
        }
    
    def generate_products(self):
        """Generate camping products with features"""
        print("\n🏕️  Generating camping products...")
        
        products = []
        product_id = 1
        
        # Generate products for each category
        for main_category, subcategories in self.camping_categories.items():
            for subcategory in subcategories:
                # 3-5 products per subcategory
                n_products = np.random.randint(3, 6)
                
                for _ in range(n_products):
                    product = self._generate_product(f"PROD_{product_id:05d}", main_category, subcategory)
                    products.append(product)
                    product_id += 1
        
        df = pd.DataFrame(products)
        print(f"   ✅ Generated {len(df)} products across {len(self.camping_categories)} categories")
        
        return df
    
    def _generate_product(self, product_id, main_category, subcategory):
        """Generate individual product with features"""
        # Determine brand tier
        brand_tier = np.random.choice(['budget', 'mid_range', 'premium', 'pro_grade'], p=[0.35, 0.35, 0.20, 0.10])
        brand = np.random.choice(self.brands[brand_tier])
        
        # Base conversion rate varies by price point
        if brand_tier == 'budget':
            base_conversion = np.random.uniform(0.04, 0.08)
            price = np.random.uniform(29.99, 99.99)
        elif brand_tier == 'mid_range':
            base_conversion = np.random.uniform(0.03, 0.06)
            price = np.random.uniform(89.99, 249.99)
        elif brand_tier == 'premium':
            base_conversion = np.random.uniform(0.02, 0.05)
            price = np.random.uniform(199.99, 499.99)
        else:  # pro_grade
            base_conversion = np.random.uniform(0.01, 0.04)
            price = np.random.uniform(399.99, 1299.99)
        
        # Generate product name
        if 'Tent' in subcategory:
            capacity = np.random.choice(['2-Person', '4-Person', '6-Person', '8-Person'])
            product_name = f"{brand} {capacity} {subcategory}"
        else:
            product_name = f"{brand} {subcategory}"
        
        # Assign features
        setup_type = np.random.choice(list(self.product_features['setup_type']))
        complexity = np.random.choice(list(self.product_features['complexity']))
        bundle = np.random.choice(list(self.product_features['bundle_compatible']))
        
        return {
            'product_id': product_id,
            'product_name': product_name,
            'brand': brand,
            'brand_tier': brand_tier,
            'main_category': main_category,
            'subcategory': subcategory,
            'price': round(price, 2),
            'base_conversion_rate': round(base_conversion, 4),
            
            # Features for lift calculation
            'setup_type': setup_type,
            'complexity': complexity,
            'bundle_compatible': bundle,
            'capacity': np.random.choice(list(self.product_features['capacity'])) if 'Tent' in subcategory or 'Bag' in subcategory else None,
            'weight_class': np.random.choice(list(self.product_features['weight_class'])),
            'weatherproof': np.random.choice(list(self.product_features['weatherproof'])),
            
            # Stock and ratings
            'in_stock': np.random.choice([True, False], p=[0.85, 0.15]),
            'avg_rating': round(np.random.uniform(3.5, 5.0), 1),
            'num_reviews': np.random.randint(5, 500)
        }
    
    def generate_interactions(self, customers_df, products_df):
        """Generate customer-product interactions"""
        print("\n🔍 Generating customer interactions (searches, views, clicks)...")
        
        interactions = []
        base_date = datetime.now() - timedelta(days=365)
        
        for _, customer in customers_df.iterrows():
            # Number of interactions varies by persona
            if customer['true_persona'] == 'Novice':
                n_interactions = np.random.randint(5, 20)
            elif customer['true_persona'] == 'Family_Socializer':
                n_interactions = np.random.randint(10, 30)
            else:  # Pro
                n_interactions = np.random.randint(20, 60)
            
            for _ in range(n_interactions):
                interaction = self._generate_interaction(customer, products_df, base_date)
                interactions.append(interaction)
        
        df = pd.DataFrame(interactions)
        print(f"   ✅ Generated {len(df):,} interactions")
        
        return df
    
    def _generate_interaction(self, customer, products_df, base_date):
        """Generate single interaction event"""
        # Select product based on customer preferences
        if customer['true_persona'] == 'Novice':
            # Prefers budget, instant setup, bundles
            preferred_products = products_df[
                (products_df['brand_tier'].isin(['budget', 'mid_range'])) &
                (products_df['bundle_compatible'] == 'Bundle Compatible')
            ]
        elif customer['true_persona'] == 'Family_Socializer':
            # Prefers mid-range, comfort features
            preferred_products = products_df[
                products_df['brand_tier'].isin(['mid_range', 'premium'])
            ]
        else:  # Pro
            # Prefers premium/pro-grade, technical specs
            preferred_products = products_df[
                (products_df['brand_tier'].isin(['premium', 'pro_grade'])) &
                (products_df['complexity'] == 'Technical Design')
            ]
        
        if len(preferred_products) == 0:
            preferred_products = products_df
        
        product = preferred_products.sample(1).iloc[0]
        
        # Generate search query based on specificity
        search_query = self._generate_search_query(customer, product)
        
        # Interaction timestamp
        days_ago = np.random.randint(0, 365)
        timestamp = (base_date + timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Time on page varies by persona
        if customer['true_persona'] == 'Novice':
            time_on_page = np.random.randint(30, 180)  # Confused, reads a lot
        elif customer['true_persona'] == 'Family_Socializer':
            time_on_page = np.random.randint(60, 240)
        else:
            time_on_page = np.random.randint(120, 600)  # Deep dive into specs
        
        return {
            'interaction_id': f"INT_{np.random.randint(100000, 999999)}",
            'customer_id': customer['customer_id'],
            'product_id': product['product_id'],
            'timestamp': timestamp,
            'interaction_type': 'view',
            'search_query': search_query,
            'time_on_page_seconds': time_on_page,
            'specs_expanded': np.random.random() < customer['spec_expansion_rate'],
            'price_checked': True,
            'reviews_viewed': np.random.choice([True, False]),
            'bundle_viewed': product['bundle_compatible'] == 'Bundle Compatible' and np.random.random() < customer['bundle_affinity']
        }
    
    def _generate_search_query(self, customer, product):
        """Generate realistic search query based on specificity level"""
        specificity = customer['search_specificity']
        
        if specificity == 1:
            # Generic category
            return np.random.choice(['camping tent', 'sleeping bag', 'camping gear', 'outdoor equipment'])
        elif specificity == 2:
            # Product type
            return f"{product['subcategory'].lower()}"
        elif specificity == 3:
            # Attribute
            if product['capacity']:
                return f"{product['capacity']} {product['subcategory'].lower()}"
            return f"{product['weatherproof'].lower()} {product['subcategory'].lower()}"
        elif specificity == 4:
            # Brand
            return f"{product['brand']} {product['subcategory'].lower()}"
        else:  # 5
            # Model name/specs
            return product['product_name'].lower()
    
    def generate_purchases(self, customers_df, products_df, interactions_df):
        """Generate purchase data with persona-based conversion"""
        print("\n💳 Generating purchases...")
        
        purchases = []
        
        # Get interactions that could convert
        for _, interaction in interactions_df.iterrows():
            customer = customers_df[customers_df['customer_id'] == interaction['customer_id']].iloc[0]
            product = products_df[products_df['product_id'] == interaction['product_id']].iloc[0]
            
            # Calculate conversion probability using lift factors
            conversion_prob = self._calculate_conversion_probability(customer, product)
            
            # Did they purchase?
            if np.random.random() < conversion_prob:
                purchase = {
                    'purchase_id': f"PUR_{np.random.randint(100000, 999999)}",
                    'customer_id': customer['customer_id'],
                    'product_id': product['product_id'],
                    'interaction_id': interaction['interaction_id'],
                    'purchase_date': interaction['timestamp'],
                    'quantity': 1,
                    'price_paid': product['price'],
                    'discount_applied': np.random.choice([0, 0.05, 0.10, 0.15], p=[0.6, 0.2, 0.15, 0.05]),
                    'purchased_as_bundle': interaction['bundle_viewed'] and product['bundle_compatible'] == 'Bundle Compatible'
                }
                purchases.append(purchase)
        
        df = pd.DataFrame(purchases)
        print(f"   ✅ Generated {len(df):,} purchases")
        
        return df
    
    def _calculate_conversion_probability(self, customer, product):
        """Calculate conversion probability using logistic regression with lift factors"""
        # Base rate (logit scale)
        base_logit = np.log(product['base_conversion_rate'] / (1 - product['base_conversion_rate']))
        
        # Feature lift based on persona
        lift = 0
        
        if customer['true_persona'] == 'Novice':
            # Boosts for instant setup, simple design, bundles
            if product['setup_type'] == 'Instant Setup':
                lift += np.log(3.0)  # 3x lift
            if product['complexity'] == 'Simple Design':
                lift += np.log(1.5)
            if product['bundle_compatible'] == 'Bundle Compatible':
                lift += np.log(2.0)
            if product['brand_tier'] == 'budget':
                lift += np.log(1.3)
                
        elif customer['true_persona'] == 'Family_Socializer':
            # Moderate preferences
            if 'Person' in str(product['capacity']) and int(product['capacity'].split('-')[0]) >= 4:
                lift += np.log(2.0)  # Likes larger capacity
            if product['complexity'] in ['Simple Design', 'Moderate Design']:
                lift += np.log(1.3)
            if product['weatherproof'] in ['Weather Resistant', 'All-Weather']:
                lift += np.log(1.4)
                
        else:  # Seasoned_Pro
            # Technical preferences
            if product['complexity'] == 'Technical Design':
                lift += np.log(2.5)
            if product['weight_class'] in ['Ultralight', 'Lightweight']:
                lift += np.log(2.0)
            if product['brand_tier'] in ['premium', 'pro_grade']:
                lift += np.log(1.8)
            # Penalties for instant/simple
            if product['setup_type'] == 'Instant Setup':
                lift += np.log(0.2)  # Strong penalty
            if product['bundle_compatible'] == 'Bundle Compatible':
                lift += np.log(0.1)
        
        # Convert to probability
        final_logit = base_logit + lift
        probability = 1 / (1 + np.exp(-final_logit))
        
        return min(probability, 0.95)  # Cap at 95%
    
    def generate_feature_affinity(self):
        """Generate feature lift factors for each persona"""
        print("\n🎯 Generating feature affinity matrix...")
        
        affinities = []
        
        # Based on document: actual lift calculations
        feature_lifts = {
            'Novice': {
                'Instant Setup': 3.0,
                'Simple Design': 1.5,
                'Bundle Compatible': 2.0,
                'Budget Brand': 1.3,
                'Quick Assembly': 2.2,
                'Traditional Setup': 0.5,  # Penalty
                'Technical Design': 0.3,  # Strong penalty
                'Pro-Grade Brand': 0.4
            },
            'Family_Socializer': {
                '4+ Person Capacity': 2.0,
                'Simple Design': 1.3,
                'Moderate Design': 1.3,
                'Weather Resistant': 1.4,
                'All-Weather': 1.4,
                'Bundle Compatible': 1.2,
                'Ultralight': 0.6,  # Penalty (wants comfort)
                'Technical Design': 0.7
            },
            'Seasoned_Pro': {
                'Technical Design': 2.5,
                'Ultralight': 2.0,
                'Lightweight': 2.0,
                'Premium Brand': 1.8,
                'Pro-Grade Brand': 1.8,
                'Extreme Weather': 1.6,
                'Instant Setup': 0.2,  # Strong penalty
                'Bundle Compatible': 0.1,  # Very strong penalty
                'Simple Design': 0.5
            }
        }
        
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
        """Save all datasets to CSV"""
        print("\n💾 Saving datasets...")
        
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
    generator = AcademySportsDataGenerator(n_customers=5000)
    data = generator.generate_all_data()
    
    print("\n📁 Files created:")
    print("   - data/academy_sports/customers.csv")
    print("   - data/academy_sports/products.csv")
    print("   - data/academy_sports/interactions.csv")
    print("   - data/academy_sports/purchases.csv")
    print("   - data/academy_sports/feature_affinity.csv")
    
    return data


if __name__ == "__main__":
    main()


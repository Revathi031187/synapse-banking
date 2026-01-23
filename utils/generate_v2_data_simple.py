"""
Quick V2 data generator without Faker (for Windows performance)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

np.random.seed(2024)
random.seed(2024)

# Simple name generator
FIRST_NAMES = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Barbara',
               'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Christopher', 'Karen',
               'Charles', 'Nancy', 'Daniel', 'Lisa', 'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra',
               'Donald', 'Ashley', 'Steven', 'Kimberly', 'Andrew', 'Emily', 'Paul', 'Donna', 'Joshua', 'Michelle']

LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
              'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
              'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson']

def generate_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

print("="*70)
print("🏕️  ACADEMY SPORTS V2 DATA GENERATOR (Simplified)")
print("="*70)

n_customers = 5000
output_dir = Path("data/preloaded/academy_sports")
output_dir.mkdir(parents=True, exist_ok=True)

# Generate customers with different distribution
print("\n📊 Generating V2 customers...")
persona_types = np.random.choice(
    ['Novice', 'Family_Socializer', 'Seasoned_Pro'],
    size=n_customers,
    p=[0.30, 0.40, 0.30]
)

customers = []
base_date = datetime.now() - timedelta(days=365)

for i, persona in enumerate(persona_types):
    customer_id = f"CUST_{i+1:05d}"
    customer_name = generate_name()
    
    if persona == 'Novice':
        customer = {
            'customer_id': customer_id,
            'customer_name': customer_name,
            'age': np.random.randint(25, 45),
            'income': np.random.randint(45000, 85000),
            'distance_to_store': np.random.uniform(2, 12),
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
            
            'customer_since': (base_date + timedelta(days=np.random.randint(180, 365))).strftime('%Y-%m-%d'),
            'email_subscriber': np.random.choice([True, False], p=[0.7, 0.3]),
            'loyalty_member': np.random.choice([True, False], p=[0.5, 0.5]),
            'preferred_contact': np.random.choice(['email', 'sms', 'phone'], p=[0.7, 0.2, 0.1]),
            'marketing_consent': np.random.choice([True, False], p=[0.75, 0.25]),
            'join_date': (base_date + timedelta(days=np.random.randint(0, 180))).strftime('%Y-%m-%d'),
            'true_persona': persona
        }
    elif persona == 'Family_Socializer':
        customer = {
            'customer_id': customer_id,
            'customer_name': customer_name,
            'age': np.random.randint(32, 52),
            'income': np.random.randint(65000, 110000),
            'distance_to_store': np.random.uniform(4, 18),
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
            
            'customer_since': (base_date + timedelta(days=np.random.randint(90, 300))).strftime('%Y-%m-%d'),
            'email_subscriber': np.random.choice([True, False], p=[0.85, 0.15]),
            'loyalty_member': np.random.choice([True, False], p=[0.80, 0.20]),
            'preferred_contact': np.random.choice(['email', 'sms', 'phone'], p=[0.8, 0.15, 0.05]),
            'marketing_consent': np.random.choice([True, False], p=[0.85, 0.15]),
            'join_date': (base_date + timedelta(days=np.random.randint(180, 365))).strftime('%Y-%m-%d'),
            'true_persona': persona
        }
    else:  # Seasoned_Pro
        customer = {
            'customer_id': customer_id,
            'customer_name': customer_name,
            'age': np.random.randint(28, 55),
            'income': np.random.randint(70000, 135000),
            'distance_to_store': np.random.uniform(5, 30),
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
            
            'customer_since': (base_date + timedelta(days=np.random.randint(0, 180))).strftime('%Y-%m-%d'),
            'email_subscriber': True,
            'loyalty_member': np.random.choice([True, False], p=[0.85, 0.15]),
            'preferred_contact': 'email',
            'marketing_consent': True,
            'join_date': (base_date + timedelta(days=np.random.randint(365, 1095))).strftime('%Y-%m-%d'),
            'true_persona': persona
        }
    
    customers.append(customer)

customers_df = pd.DataFrame(customers)
print(f"  ✓ Generated {len(customers_df)} customers")
print(f"    - Novice: {(customers_df['true_persona']=='Novice').sum()} (30%)")
print(f"    - Family: {(customers_df['true_persona']=='Family_Socializer').sum()} (40%)")
print(f"    - Seasoned Pro: {(customers_df['true_persona']=='Seasoned_Pro').sum()} (30%)")

# Copy products from V1
print("\n📦 Copying products from V1...")
products_df = pd.read_csv(output_dir / 'products.csv')
print(f"  ✓ {len(products_df)} products")

# Generate interactions with different patterns
print("\n🔍 Generating V2 interactions...")
interactions = []

product_ids = products_df['product_id'].tolist()

for idx, row in customers_df.iterrows():
    if idx % 500 == 0:
        print(f"  Processing customer {idx}/{len(customers_df)}...")
    
    customer = row
    persona = customer['true_persona']
    
    if persona == 'Novice':
        n_interactions = np.random.randint(5, 18)
    elif persona == 'Family_Socializer':
        n_interactions = np.random.randint(12, 35)
    else:
        n_interactions = np.random.randint(20, 55)
    
    # Much faster: sample from list instead of DataFrame
    selected_product_ids = np.random.choice(product_ids, size=min(n_interactions, len(product_ids)), replace=True)
    
    for product_id in selected_product_ids:
        interaction_date = datetime.now() - timedelta(days=np.random.randint(0, 365))
        
        if persona == 'Novice':
            time_spent = np.random.randint(90, 480)
        elif persona == 'Family_Socializer':
            time_spent = np.random.randint(180, 600)
        else:
            time_spent = np.random.randint(120, 420)
        
        interactions.append({
            'interaction_id': f"INT_{len(interactions)+1:06d}",
            'customer_id': customer['customer_id'],
            'product_id': product_id,
            'interaction_type': np.random.choice(['view', 'click', 'add_to_cart'], p=[0.6, 0.3, 0.1]),
            'interaction_date': interaction_date.strftime('%Y-%m-%d'),
            'time_spent_seconds': time_spent
        })

interactions_df = pd.DataFrame(interactions)
print(f"  ✓ Generated {len(interactions_df)} interactions")

# Generate purchases
print("\n💳 Generating V2 purchases...")
purchases = []

# Create product price dictionary for faster lookup
product_prices = dict(zip(products_df['product_id'], products_df['price']))

for idx, row in customers_df.iterrows():
    if idx % 500 == 0:
        print(f"  Processing customer {idx}/{len(customers_df)}...")
    
    customer = row
    persona = customer['true_persona']
    
    if persona == 'Novice':
        n_purchases = np.random.randint(1, 4)
    elif persona == 'Family_Socializer':
        n_purchases = np.random.randint(3, 8)
    else:
        n_purchases = np.random.randint(4, 12)
    
    customer_interactions = interactions_df[interactions_df['customer_id'] == customer['customer_id']]
    
    if len(customer_interactions) == 0:
        continue
    
    # Use faster numpy sampling
    n_to_purchase = min(n_purchases, len(customer_interactions))
    selected_indices = np.random.choice(len(customer_interactions), size=n_to_purchase, replace=True)
    
    for sel_idx in selected_indices:
        interaction = customer_interactions.iloc[sel_idx]
        product_id = interaction['product_id']
        product_price = product_prices[product_id]
        
        if persona == 'Novice':
            quantity = np.random.choice([1, 2], p=[0.85, 0.15])
            discount = np.random.uniform(0.05, 0.25)
        elif persona == 'Family_Socializer':
            quantity = np.random.choice([1, 2, 3, 4], p=[0.4, 0.35, 0.15, 0.10])
            discount = np.random.uniform(0.10, 0.30)
        else:
            quantity = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
            discount = np.random.uniform(0, 0.15)
        
        purchase_date = datetime.strptime(interaction['interaction_date'], '%Y-%m-%d') + timedelta(days=np.random.randint(0, 7))
        total_price = product_price * quantity * (1 - discount)
        
        purchases.append({
            'purchase_id': f"PUR_{len(purchases)+1:06d}",
            'customer_id': customer['customer_id'],
            'product_id': product_id,
            'purchase_date': purchase_date.strftime('%Y-%m-%d'),
            'quantity': quantity,
            'total_price': round(total_price, 2),
            'discount_applied': round(discount, 2)
        })

purchases_df = pd.DataFrame(purchases)
print(f"  ✓ Generated {len(purchases_df)} purchases")

# Copy feature affinity
print("\n🎯 Copying feature affinity from V1...")
feature_affinity_df = pd.read_csv(output_dir / 'feature_affinity.csv')
print(f"  ✓ {len(feature_affinity_df)} feature affinity records")

# Save V2 files
print("\n💾 Saving V2 datasets...")
customers_df.to_csv(output_dir / 'customers_v2.csv', index=False)
products_df.to_csv(output_dir / 'products_v2.csv', index=False)
interactions_df.to_csv(output_dir / 'interactions_v2.csv', index=False)
purchases_df.to_csv(output_dir / 'purchases_v2.csv', index=False)
feature_affinity_df.to_csv(output_dir / 'feature_affinity_v2.csv', index=False)
print(f"  ✓ All V2 files saved to: {output_dir}")

# Summary
print("\n" + "="*70)
print("📊 V2 DATASET SUMMARY")
print("="*70)
print(f"👥 Customers:     {len(customers_df):,}")
print(f"📦 Products:      {len(products_df):,}")
print(f"🔍 Interactions:  {len(interactions_df):,}")
print(f"💳 Purchases:     {len(purchases_df):,}")
print("\n💰 Revenue by Persona (V2):")

revenue_by_persona = purchases_df.merge(customers_df[['customer_id', 'true_persona']], on='customer_id')
revenue_summary = revenue_by_persona.groupby('true_persona')['total_price'].agg(['sum', 'count', 'mean'])

for persona in revenue_summary.index:
    total_rev = revenue_summary.loc[persona, 'sum']
    count = revenue_summary.loc[persona, 'count']
    avg = revenue_summary.loc[persona, 'mean']
    print(f"  {persona:20s}: ${total_rev:>10,.2f} ({count:>4} purchases, avg ${avg:>6.2f})")

print("\n✅ V2 dataset generation complete!")
print("="*70)


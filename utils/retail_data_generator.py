"""
Retail/E-commerce Synthetic Data Generator
Generates realistic retail transaction data with purchase patterns
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import os

# Ensure data directory exists
os.makedirs('data/preloaded/retail_nba', exist_ok=True)

# Set random seed
np.random.seed(42)
random.seed(42)

# Configuration
NUM_CUSTOMERS = 150
NUM_PRODUCTS = 200
START_DATE = datetime.now() - timedelta(days=365)
CURRENT_DATE = datetime.now()


# ============================================================================
# 1. PRODUCTS (SKU Catalog)
# ============================================================================
def generate_products():
    """Generate product catalog"""
    print("📦 Generating products...")
    
    categories = {
        'Electronics': ['Smartphones', 'Laptops', 'Headphones', 'Smart Watches', 'Tablets'],
        'Fashion': ['Mens Clothing', 'Womens Clothing', 'Shoes', 'Accessories'],
        'Home': ['Furniture', 'Kitchen', 'Bedding', 'Decor'],
        'Baby': ['Baby Clothes', 'Toys', 'Diapers', 'Strollers', 'Baby Food'],
        'Sports': ['Equipment', 'Apparel', 'Footwear'],
        'Beauty': ['Skincare', 'Makeup', 'Haircare'],
        'Grocery': ['Snacks', 'Beverages', 'Fresh Produce', 'Dairy']
    }
    
    brands = ['Apple', 'Samsung', 'Nike', 'Adidas', 'IKEA', 'Pampers', 'Gerber', 'Sony', 'HP', 'Zara', 'H&M']
    
    products = []
    sku_counter = 1
    
    for category, sub_categories in categories.items():
        for sub_cat in sub_categories:
            num_products_in_subcat = np.random.randint(3, 8)
            
            for i in range(num_products_in_subcat):
                sku_id = f"SKU{str(sku_counter).zfill(6)}"
                
                # Price ranges by category
                if category == 'Electronics':
                    price = round(np.random.uniform(50, 1500), 2)
                elif category == 'Fashion':
                    price = round(np.random.uniform(20, 300), 2)
                elif category == 'Home':
                    price = round(np.random.uniform(30, 800), 2)
                elif category == 'Baby':
                    price = round(np.random.uniform(10, 400), 2)
                else:
                    price = round(np.random.uniform(5, 200), 2)
                
                cost = round(price * np.random.uniform(0.4, 0.7), 2)
                margin = round(((price - cost) / price) * 100, 2)
                
                products.append({
                    'sku_id': sku_id,
                    'product_name': f"{random.choice(brands)} {sub_cat} {i+1}",
                    'category': category,
                    'sub_category': sub_cat,
                    'brand': random.choice(brands),
                    'price': price,
                    'cost': cost,
                    'margin_percentage': margin,
                    'stock_quantity': np.random.randint(50, 500),
                    'is_seasonal': random.choice([True, False]),
                    'season': np.random.choice(['Spring', 'Summer', 'Fall', 'Winter', 'Holiday']) if random.choice([True, False]) else None,
                    'is_active': True,
                    'created_at': START_DATE
                })
                
                sku_counter += 1
                
                if sku_counter > NUM_PRODUCTS:
                    break
            
            if sku_counter > NUM_PRODUCTS:
                break
        
        if sku_counter > NUM_PRODUCTS:
            break
    
    df = pd.DataFrame(products)
    df.to_csv('data/preloaded/retail_nba/products.csv', index=False)
    print(f"✅ Generated {len(df)} products")
    return df


# ============================================================================
# 2. CUSTOMERS
# ============================================================================
def generate_customers():
    """Generate customer profiles"""
    print("👥 Generating customers...")
    
    customers = []
    
    for i in range(NUM_CUSTOMERS):
        customer_id = f"RCUST{str(i+1).zfill(6)}"
        registration_date = START_DATE + timedelta(days=np.random.randint(0, 300))
        days_since = (CURRENT_DATE - registration_date).days
        
        # Customer persona 1: Frequent buyer (20% of customers)
        if i < NUM_CUSTOMERS * 0.2:
            total_orders = np.random.randint(15, 40)
            avg_order_value = round(np.random.uniform(80, 250), 2)
            loyalty_tier = 'Platinum' if total_orders > 30 else 'Gold'
            preferred_channel = 'App'
        # Persona 2: Moderate buyer (50%)
        elif i < NUM_CUSTOMERS * 0.7:
            total_orders = np.random.randint(5, 15)
            avg_order_value = round(np.random.uniform(40, 120), 2)
            loyalty_tier = 'Silver' if total_orders > 10 else 'Bronze'
            preferred_channel = np.random.choice(['Online', 'App', 'Offline'])
        # Persona 3: Occasional buyer (30%)
        else:
            total_orders = np.random.randint(1, 5)
            avg_order_value = round(np.random.uniform(20, 80), 2)
            loyalty_tier = 'Bronze'
            preferred_channel = 'Online'
        
        total_lifetime_spend = round(total_orders * avg_order_value, 2)
        loyalty_points = int(total_lifetime_spend * 10)
        
        customers.append({
            'customer_id': customer_id,
            'first_name': random.choice(['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn']),
            'last_name': random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']),
            'email': f"customer{i+1}@email.com",
            'phone': f"555-{str(np.random.randint(1000, 9999))}",
            'age': np.random.randint(22, 65),
            'gender': random.choice(['Male', 'Female', 'Other']),
            'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
            'state': random.choice(['NY', 'CA', 'IL', 'TX', 'AZ']),
            'zip_code': str(np.random.randint(10000, 99999)),
            'registration_date': registration_date.date(),
            'customer_since_days': days_since,
            'loyalty_tier': loyalty_tier,
            'loyalty_points': loyalty_points,
            'total_lifetime_spend': total_lifetime_spend,
            'total_orders': total_orders,
            'avg_order_value': avg_order_value,
            'preferred_channel': preferred_channel,
            'is_active': True,
            'created_at': registration_date,
            'updated_at': CURRENT_DATE
        })
    
    df = pd.DataFrame(customers)
    df.to_csv('data/preloaded/retail_nba/customers.csv', index=False)
    print(f"✅ Generated {len(df)} customers")
    return df


# ============================================================================
# 3. TRANSACTIONS
# ============================================================================
def generate_transactions(customers_df, products_df):
    """Generate transaction history"""
    print("💳 Generating transactions...")
    
    transactions = []
    transaction_counter = 1
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        num_transactions = customer['total_orders']
        
        for _ in range(num_transactions):
            # Transaction date
            trans_date = pd.to_datetime(customer['registration_date']) + timedelta(
                days=np.random.randint(0, (CURRENT_DATE - pd.to_datetime(customer['registration_date'])).days)
            )
            
            # Number of items in this transaction
            num_items = np.random.randint(1, 6)
            
            # Select products (with some category affinity)
            if np.random.random() < 0.3:  # 30% chance of category-focused shopping
                category = np.random.choice(products_df['category'].unique())
                available_products = products_df[products_df['category'] == category]
            else:
                available_products = products_df
            
            selected_products = available_products.sample(min(num_items, len(available_products)))
            
            total_basket_value = 0
            
            for _, product in selected_products.iterrows():
                quantity = np.random.randint(1, 4)
                unit_price = product['price']
                
                # Apply discount sometimes
                promo_flag = random.random() < 0.25  # 25% of transactions have promo
                if promo_flag:
                    discount = round(unit_price * quantity * np.random.uniform(0.1, 0.3), 2)
                else:
                    discount = 0
                
                item_total = round(unit_price * quantity - discount, 2)
                total_basket_value += item_total
                
                transactions.append({
                    'transaction_id': f"TXN{str(transaction_counter).zfill(10)}",
                    'customer_id': customer_id,
                    'transaction_timestamp': trans_date,
                    'store_id': f"STORE{np.random.randint(1, 10):03d}",
                    'sku_id': product['sku_id'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount_amount': discount,
                    'total_basket_value': item_total,
                    'promo_flag': promo_flag,
                    'channel': customer['preferred_channel'] if random.random() < 0.7 else np.random.choice(['Offline', 'Online', 'App']),
                    'created_at': trans_date
                })
                
                transaction_counter += 1
    
    df = pd.DataFrame(transactions)
    df.to_csv('data/preloaded/retail_nba/transactions.csv', index=False)
    print(f"✅ Generated {len(df)} transactions")
    return df


# ============================================================================
# 4. DIGITAL_BEHAVIORAL_EVENTS (Updated per schema)
# ============================================================================
def generate_digital_behavioral_events(customers_df, products_df):
    """Generate detailed digital behavioral events per provided schema"""
    print("🌐 Generating digital behavioral events...")
    
    events = []
    event_counter = 1
    session_counter = 1
    
    event_types = ['view', 'search', 'add-to-cart', 'wishlist', 'remove-from-cart']
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        
        # Number of sessions = orders * 3
        num_sessions = customer['total_orders'] * 3
        
        for _ in range(num_sessions):
            session_id = f"SESS{str(session_counter).zfill(10)}"
            session_start = pd.to_datetime(customer['registration_date']) + timedelta(
                days=np.random.randint(0, max(1, (CURRENT_DATE - pd.to_datetime(customer['registration_date'])).days))
            )
            
            # Events per session: 5-20
            num_events = np.random.randint(5, 20)
            
            cart_items = []
            
            for i in range(num_events):
                event_time = session_start + timedelta(seconds=i * np.random.randint(10, 120))
                
                # Event type distribution
                if i == 0:
                    event_type = 'view'  # First event is always a view
                elif len(cart_items) > 0 and random.random() < 0.1:
                    event_type = 'remove-from-cart'
                else:
                    event_type = np.random.choice(event_types, p=[0.5, 0.15, 0.2, 0.1, 0.05])
                
                # Select product
                product = products_df.sample(1).iloc[0]
                sku_id = product['sku_id']
                
                # Track cart
                if event_type == 'add-to-cart' and sku_id not in cart_items:
                    cart_items.append(sku_id)
                elif event_type == 'remove-from-cart' and len(cart_items) > 0:
                    cart_items.pop()
                
                # Dwell time (how long they looked at product)
                if event_type in ['view', 'add-to-cart', 'wishlist']:
                    dwell_time = np.random.randint(5, 300)  # 5 sec to 5 min
                else:
                    dwell_time = np.random.randint(1, 30)
                
                # Search query (only for search events)
                search_query = None
                if event_type == 'search':
                    search_queries = [
                        'laptop', 'shoes', 'dress', 'phone', 'headphones',
                        'baby toys', 'furniture', 'kitchen', 'sports equipment',
                        product['category'].lower(), product['brand'].lower()
                    ]
                    search_query = random.choice(search_queries)
                
                # Promo interaction (25% chance on views)
                promo_interaction = random.random() < 0.25 if event_type == 'view' else False
                
                events.append({
                    'event_id': f"EVT{str(event_counter).zfill(12)}",
                    'customer_id': customer_id,
                    'event_type': event_type,
                    'sku_id': sku_id,
                    'timestamp': event_time,
                    'session_id': session_id,
                    'dwell_time_sec': dwell_time,
                    'search_query': search_query,
                    'abandoned_fla': False,  # Will be updated after session ends
                    'promo_interaction_flag': promo_interaction
                })
                
                event_counter += 1
            
            # Determine if cart was abandoned (had items but didn't convert)
            abandoned = len(cart_items) > 0 and random.random() < 0.7  # 70% abandonment rate
            
            # Mark cart abandonment for add-to-cart events in this session
            for event in events:
                if event['session_id'] == session_id and event['event_type'] == 'add-to-cart':
                    event['abandoned_fla'] = abandoned
            
            session_counter += 1
    
    df = pd.DataFrame(events)
    df.to_csv('data/preloaded/retail_nba/digital_behavioral_events.csv', index=False)
    print(f"✅ Generated {len(df)} digital behavioral events")
    return df


# ============================================================================
# 5. CUSTOMER_REVIEWS
# ============================================================================
def generate_reviews(customers_df, products_df, transactions_df):
    """Generate product reviews"""
    print("⭐ Generating customer reviews...")
    
    reviews = []
    review_counter = 1
    
    # 30% of transactions get reviewed
    reviewed_transactions = transactions_df.sample(frac=0.3)
    
    for _, trans in reviewed_transactions.iterrows():
        review_date = pd.to_datetime(trans['transaction_timestamp']) + timedelta(days=np.random.randint(1, 30))
        
        rating = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.05, 0.15, 0.35, 0.4])
        
        review_texts = {
            5: ["Excellent product!", "Highly recommend", "Love it!", "Best purchase ever"],
            4: ["Good quality", "Happy with purchase", "Nice product", "Worth the money"],
            3: ["It's okay", "Average product", "Meets expectations", "Decent"],
            2: ["Not great", "Could be better", "Disappointed", "Below expectations"],
            1: ["Terrible", "Do not buy", "Waste of money", "Very poor quality"]
        }
        
        reviews.append({
            'review_id': f"REV{str(review_counter).zfill(10)}",
            'customer_id': trans['customer_id'],
            'sku_id': trans['sku_id'],
            'rating': rating,
            'review_text': random.choice(review_texts[rating]),
            'review_date': review_date.date(),
            'helpful_votes': np.random.randint(0, 50),
            'created_at': review_date
        })
        
        review_counter += 1
    
    df = pd.DataFrame(reviews)
    df.to_csv('data/preloaded/retail_nba/customer_reviews.csv', index=False)
    print(f"✅ Generated {len(df)} customer reviews")
    return df


# ============================================================================
# 6. BASKET_COMPOSITION
# ============================================================================
def generate_basket_composition(transactions_df):
    """Generate basket-level aggregations"""
    print("🛒 Generating basket composition...")
    
    baskets = []
    basket_counter = 1
    
    # Group transactions by transaction_id
    grouped = transactions_df.groupby(['transaction_id', 'customer_id', 'transaction_timestamp', 'channel'])
    
    for (trans_id, cust_id, trans_time, channel), group in grouped:
        total_items = group['quantity'].sum()
        unique_skus = group['sku_id'].nunique()
        total_value = group['total_basket_value'].sum()
        discount_applied = group['discount_amount'].sum()
        
        skus = group['sku_id'].tolist()
        
        # Get categories (would need to join with products, simplified here)
        categories = ['Mixed']  # Placeholder
        
        baskets.append({
            'basket_id': f"BASK{str(basket_counter).zfill(10)}",
            'transaction_id': trans_id,
            'customer_id': cust_id,
            'transaction_timestamp': trans_time,
            'total_items': int(total_items),
            'unique_skus': int(unique_skus),
            'total_value': round(total_value, 2),
            'discount_applied': round(discount_applied, 2),
            'skus_in_basket': json.dumps(skus),
            'categories_in_basket': json.dumps(categories),
            'channel': channel,
            'created_at': trans_time
        })
        
        basket_counter += 1
    
    df = pd.DataFrame(baskets)
    df.to_csv('data/preloaded/retail_nba/basket_composition.csv', index=False)
    print(f"✅ Generated {len(df)} baskets")
    return df


# ============================================================================
# 7. PROMO_EXPOSURE (Marketing Campaign Exposure)
# ============================================================================
def generate_promo_exposure(customers_df, products_df):
    """Generate promo exposure tracking per provided schema"""
    print("📢 Generating promo exposure data...")
    
    exposures = []
    exposure_counter = 1
    
    # Define campaigns
    campaigns = [
        {'campaign_id': 'CAMP001', 'name': 'Summer Sale 2024', 'promo_type': 'discount'},
        {'campaign_id': 'CAMP002', 'name': 'New Customer Welcome', 'promo_type': 'bundle'},
        {'campaign_id': 'CAMP003', 'name': 'Flash Sale Weekend', 'promo_type': 'discount'},
        {'campaign_id': 'CAMP004', 'name': 'Free Gift with Purchase', 'promo_type': 'free gift'},
        {'campaign_id': 'CAMP005', 'name': 'Loyalty Rewards', 'promo_type': 'discount'},
    ]
    
    channels = ['Email', 'App', 'In-store', 'SMS', 'Web banner']
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        
        # Number of campaigns customer was exposed to: 2-8
        num_exposures = np.random.randint(2, 9)
        
        for _ in range(num_exposures):
            campaign = random.choice(campaigns)
            
            # Select a product to associate
            product = products_df.sample(1).iloc[0]
            
            # Exposure time
            exposure_time = CURRENT_DATE - timedelta(days=np.random.randint(0, 90))
            
            # Promo value
            if campaign['promo_type'] == 'discount':
                promo_value = round(np.random.uniform(5, 50), 2)
            elif campaign['promo_type'] == 'bundle':
                promo_value = round(np.random.uniform(10, 30), 2)
            else:
                promo_value = 0.0
            
            # Channel
            channel = random.choice(channels)
            
            # Redemption (higher for loyal customers)
            if customer['loyalty_tier'] in ['Platinum', 'Gold']:
                redeemed = random.random() < 0.35  # 35% redemption
            elif customer['loyalty_tier'] == 'Silver':
                redeemed = random.random() < 0.20  # 20% redemption
            else:
                redeemed = random.random() < 0.10  # 10% redemption
            
            # Conversion (if redeemed, 60% convert)
            if redeemed:
                converted = random.random() < 0.6
                conversion_txn_id = f"TXN{str(np.random.randint(1, 9999999999)).zfill(10)}" if converted else None
            else:
                converted = False
                conversion_txn_id = None
            
            exposures.append({
                'exposure_id': f"EXP{str(exposure_counter).zfill(10)}",
                'customer_id': customer_id,
                'campaign_id': campaign['campaign_id'],
                'sku_id': product['sku_id'],
                'promo_type': campaign['promo_type'],
                'promo_value': promo_value,
                'channel': channel,
                'exposure_time_stamp': exposure_time,
                'redeemed_flag': redeemed,
                'conversion_txn_id': conversion_txn_id
            })
            
            exposure_counter += 1
    
    df = pd.DataFrame(exposures)
    df.to_csv('data/preloaded/retail_nba/promo_exposure.csv', index=False)
    print(f"✅ Generated {len(df)} promo exposures")
    return df


# ============================================================================
# 8. PRODUCT_AFFINITIES
# ============================================================================
def generate_affinities(transactions_df, products_df):
    """Generate product affinity matrix"""
    print("🔗 Generating product affinities...")
    
    # Simple affinity: products bought in same transaction
    affinities = []
    affinity_counter = 1
    
    # Group by transaction
    grouped = transactions_df.groupby('transaction_id')['sku_id'].apply(list)
    
    # Count co-occurrences
    cooccurrence = {}
    for skus in grouped:
        if len(skus) > 1:
            for i, sku1 in enumerate(skus):
                for sku2 in skus[i+1:]:
                    pair = tuple(sorted([sku1, sku2]))
                    cooccurrence[pair] = cooccurrence.get(pair, 0) + 1
    
    # Convert to affinity records (top 500)
    sorted_pairs = sorted(cooccurrence.items(), key=lambda x: x[1], reverse=True)[:500]
    
    for (sku1, sku2), count in sorted_pairs:
        # Calculate confidence (simplified)
        total_sku1 = len(transactions_df[transactions_df['sku_id'] == sku1])
        confidence = round(count / total_sku1, 2) if total_sku1 > 0 else 0
        
        affinities.append({
            'affinity_id': f"AFF{str(affinity_counter).zfill(8)}",
            'source_sku': sku1,
            'target_sku': sku2,
            'affinity_score': round(min(confidence * 1.5, 1.0), 2),
            'support_count': count,
            'confidence': confidence,
            'created_at': CURRENT_DATE
        })
        
        affinity_counter += 1
    
    df = pd.DataFrame(affinities)
    df.to_csv('data/preloaded/retail_nba/product_affinities.csv', index=False)
    print(f"✅ Generated {len(df)} product affinities")
    return df


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    print("\n" + "="*80)
    print("🛒 RETAIL/E-COMMERCE NBA PLATFORM - SYNTHETIC DATA GENERATOR")
    print("="*80 + "\n")
    
    products_df = generate_products()
    customers_df = generate_customers()
    transactions_df = generate_transactions(customers_df, products_df)
    behavioral_events_df = generate_digital_behavioral_events(customers_df, products_df)
    reviews_df = generate_reviews(customers_df, products_df, transactions_df)
    basket_df = generate_basket_composition(transactions_df)
    promo_exposure_df = generate_promo_exposure(customers_df, products_df)
    affinities_df = generate_affinities(transactions_df, products_df)
    
    print("\n" + "="*80)
    print("✅ ALL RETAIL DATA GENERATED SUCCESSFULLY!")
    print("="*80)
    print(f"\n📁 Data saved to: data/preloaded/retail_nba/")
    print(f"\n📊 Summary:")
    print(f"   - Customers: {len(customers_df)}")
    print(f"   - Products: {len(products_df)}")
    print(f"   - Transactions: {len(transactions_df)}")
    print(f"   - Digital Behavioral Events: {len(behavioral_events_df)}")
    print(f"   - Customer Reviews: {len(reviews_df)}")
    print(f"   - Baskets: {len(basket_df)}")
    print(f"   - Promo Exposure: {len(promo_exposure_df)}")
    print(f"   - Product Affinities: {len(affinities_df)}")
    print("\n")


if __name__ == "__main__":
    main()


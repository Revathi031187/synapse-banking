"""
Enhanced Retail Data Generator for Product Matchmaking
Creates realistic e-commerce data with strong signals for product recommendations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

np.random.seed(42)
random.seed(42)


class EnhancedRetailDataGenerator:
    """Generate realistic retail/e-commerce data for product recommendations"""
    
    def __init__(self, n_customers=150, n_products=130):
        self.n_customers = n_customers
        self.n_products = n_products
        self.start_date = datetime.now() - timedelta(days=365)
        
    def generate_all(self, output_dir="data/preloaded/retail_nba"):
        """Generate all retail tables"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        print("🛒 Generating Enhanced Retail Dataset...")
        
        # Generate customers
        customers = self.generate_customers()
        customers.to_csv(f"{output_dir}/customers.csv", index=False)
        print(f"✅ Generated {len(customers)} customers")
        
        # Generate products
        products = self.generate_products()
        products.to_csv(f"{output_dir}/products.csv", index=False)
        print(f"✅ Generated {len(products)} products")
        
        # Generate transactions
        transactions = self.generate_transactions(customers, products)
        transactions.to_csv(f"{output_dir}/transactions.csv", index=False)
        print(f"✅ Generated {len(transactions)} transactions")
        
        print(f"\n✅ All data saved to {output_dir}/")
        
    def generate_customers(self):
        """Generate customer profiles with realistic shopping segments"""
        customers = []
        
        # Define customer segments
        segments = [
            {"name": "Budget Shoppers", "count": 30, "age_range": (22, 35), "income_range": (30000, 50000), "aov_range": (25, 60)},
            {"name": "Mid-Market", "count": 40, "age_range": (30, 50), "income_range": (50000, 85000), "aov_range": (60, 120)},
            {"name": "Premium Buyers", "count": 35, "age_range": (35, 60), "income_range": (85000, 150000), "aov_range": (120, 250)},
            {"name": "Luxury Shoppers", "count": 25, "age_range": (40, 65), "income_range": (150000, 300000), "aov_range": (250, 500)},
            {"name": "Deal Hunters", "count": 20, "age_range": (25, 55), "income_range": (40000, 80000), "aov_range": (30, 80)},
        ]
        
        customer_id = 1
        for segment in segments:
            for _ in range(segment["count"]):
                age = np.random.randint(*segment["age_range"])
                income = np.random.uniform(*segment["income_range"])
                aov = np.random.uniform(*segment["aov_range"])
                
                # Shopping behavior
                recency_days = int(np.random.exponential(15) + 1)  # Days since last purchase
                frequency_purchases = int(np.random.poisson(8) + 1)  # Purchases in last year
                monetary_total = aov * frequency_purchases * np.random.uniform(0.8, 1.2)
                
                # RFM Scores (1-10 scale)
                recency_score = max(1, min(10, int(10 - (recency_days / 10))))
                frequency_score = max(1, min(10, int(frequency_purchases / 2)))
                monetary_score = max(1, min(10, int(monetary_total / 500)))
                
                # Category preferences
                categories = ['Electronics', 'Fashion', 'Home & Garden', 'Sports', 'Beauty', 'Books', 'Toys']
                preferred_category = np.random.choice(categories)
                
                # Digital engagement
                web_visits = int(np.random.poisson(15) + frequency_purchases)
                app_engagement = np.random.uniform(0.1, 1.0) if age < 50 else np.random.uniform(0.05, 0.6)
                
                # Cart abandonment (higher for price-sensitive segments)
                cart_abandonment_rate = np.random.uniform(0.4, 0.7) if segment["name"] in ["Budget Shoppers", "Deal Hunters"] else np.random.uniform(0.2, 0.4)
                
                # Channel preference
                if age < 35:
                    channel = np.random.choice(['app', 'web', 'mobile_web'], p=[0.5, 0.3, 0.2])
                elif age < 50:
                    channel = np.random.choice(['web', 'app', 'mobile_web'], p=[0.5, 0.3, 0.2])
                else:
                    channel = np.random.choice(['web', 'mobile_web', 'app'], p=[0.6, 0.3, 0.1])
                
                # Intent score (based on recent activity)
                intent_score = self._calculate_intent_score(
                    recency_days, web_visits, frequency_purchases, cart_abandonment_rate
                )
                
                # Promo responsiveness
                promo_response_rate = np.random.uniform(0.3, 0.8) if segment["name"] in ["Budget Shoppers", "Deal Hunters"] else np.random.uniform(0.1, 0.4)
                
                customers.append({
                    'customer_id': f'CUST_{customer_id:06d}',
                    'age': age,
                    'income': round(income, 2),
                    'segment': segment["name"],
                    'recency_days': recency_days,
                    'recency_score': recency_score,
                    'frequency_score': frequency_score,
                    'monetary_score': monetary_score,
                    'rfm_composite': round((recency_score + frequency_score + monetary_score) / 3, 2),
                    'avg_order_value': round(aov, 2),
                    'total_purchases': frequency_purchases,
                    'lifetime_value': round(monetary_total, 2),
                    'avg_basket_size': round(np.random.uniform(2, 8), 1),
                    'preferred_category': preferred_category,
                    'web_visits_30d': web_visits,
                    'app_engagement_score': round(app_engagement, 3),
                    'cart_abandonment_rate': round(cart_abandonment_rate, 3),
                    'promo_response_rate': round(promo_response_rate, 3),
                    'intent_score': round(intent_score, 3),
                    'channel_preference': channel,
                    'customer_since': (self.start_date + timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d'),
                    'loyalty_tier': self._get_loyalty_tier(monetary_total, frequency_purchases)
                })
                customer_id += 1
        
        return pd.DataFrame(customers)
    
    def _calculate_intent_score(self, recency_days, web_visits, frequency, cart_abandonment):
        """Calculate purchase intent score"""
        score = 0.3
        
        # Recent activity
        if recency_days <= 7:
            score += 0.3
        elif recency_days <= 14:
            score += 0.2
        
        # High engagement
        if web_visits > 20:
            score += 0.2
        elif web_visits > 10:
            score += 0.1
        
        # Frequent buyer
        if frequency > 10:
            score += 0.1
        
        # Cart abandonment (indicates interest)
        if cart_abandonment > 0.5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_loyalty_tier(self, ltv, frequency):
        """Determine loyalty tier"""
        if ltv > 2000 and frequency > 15:
            return 'platinum'
        elif ltv > 1000 and frequency > 10:
            return 'gold'
        elif ltv > 500 and frequency > 5:
            return 'silver'
        else:
            return 'bronze'
    
    def generate_products(self):
        """Generate realistic product catalog"""
        products = []
        product_id = 1
        
        # Product categories with realistic items
        product_data = {
            'Electronics': [
                ('Wireless Headphones', 149.99, 4.5, 'Sony'),
                ('Smart Watch', 299.99, 4.3, 'Apple'),
                ('Laptop Computer', 899.99, 4.7, 'Dell'),
                ('Tablet Device', 449.99, 4.4, 'Samsung'),
                ('Wireless Speaker', 79.99, 4.2, 'JBL'),
                ('Gaming Console', 499.99, 4.8, 'Sony'),
                ('Smartphone', 799.99, 4.6, 'Apple'),
                ('Fitness Tracker', 129.99, 4.1, 'Fitbit'),
                ('Wireless Earbuds', 179.99, 4.4, 'Samsung'),
                ('Portable Charger', 39.99, 4.3, 'Anker'),
                ('4K Monitor', 349.99, 4.5, 'LG'),
                ('Webcam HD', 89.99, 4.2, 'Logitech'),
                ('Mechanical Keyboard', 119.99, 4.6, 'Razer'),
                ('Gaming Mouse', 69.99, 4.4, 'Logitech'),
                ('USB-C Hub', 49.99, 4.1, 'Anker'),
            ],
            'Fashion': [
                ('Designer Jeans', 89.99, 4.3, 'Levi\'s'),
                ('Leather Jacket', 299.99, 4.6, 'AllSaints'),
                ('Running Shoes', 119.99, 4.5, 'Nike'),
                ('Casual Sneakers', 79.99, 4.4, 'Adidas'),
                ('Winter Coat', 179.99, 4.5, 'North Face'),
                ('Dress Shirt', 59.99, 4.2, 'Ralph Lauren'),
                ('Yoga Pants', 49.99, 4.3, 'Lululemon'),
                ('Summer Dress', 69.99, 4.4, 'Zara'),
                ('Denim Jacket', 89.99, 4.2, 'Levi\'s'),
                ('Leather Boots', 149.99, 4.5, 'Timberland'),
                ('Wool Sweater', 79.99, 4.3, 'J.Crew'),
                ('Athletic Shorts', 39.99, 4.1, 'Under Armour'),
                ('Formal Suit', 399.99, 4.6, 'Hugo Boss'),
                ('Casual T-Shirt', 29.99, 4.0, 'H&M'),
                ('Silk Scarf', 59.99, 4.4, 'Burberry'),
            ],
            'Home & Garden': [
                ('Coffee Maker', 129.99, 4.6, 'Keurig'),
                ('Vacuum Cleaner', 249.99, 4.5, 'Dyson'),
                ('Air Purifier', 199.99, 4.4, 'Honeywell'),
                ('Bed Sheets Set', 79.99, 4.3, 'Brooklinen'),
                ('Kitchen Mixer', 299.99, 4.7, 'KitchenAid'),
                ('Smart Thermostat', 179.99, 4.5, 'Nest'),
                ('Garden Tool Set', 89.99, 4.2, 'Fiskars'),
                ('Dining Table', 499.99, 4.4, 'IKEA'),
                ('Office Chair', 299.99, 4.6, 'Herman Miller'),
                ('Floor Lamp', 79.99, 4.1, 'Target'),
                ('Cookware Set', 149.99, 4.5, 'All-Clad'),
                ('Bath Towel Set', 59.99, 4.2, 'Parachute'),
                ('Area Rug', 199.99, 4.3, 'Ruggable'),
                ('Wall Art', 89.99, 4.0, 'West Elm'),
                ('Storage Organizer', 49.99, 4.2, 'Container Store'),
            ],
            'Sports': [
                ('Yoga Mat', 39.99, 4.5, 'Manduka'),
                ('Dumbbell Set', 149.99, 4.6, 'Bowflex'),
                ('Tennis Racket', 179.99, 4.4, 'Wilson'),
                ('Golf Clubs Set', 599.99, 4.7, 'Callaway'),
                ('Basketball', 29.99, 4.3, 'Spalding'),
                ('Soccer Ball', 34.99, 4.2, 'Adidas'),
                ('Exercise Bike', 399.99, 4.5, 'Peloton'),
                ('Camping Tent', 199.99, 4.4, 'Coleman'),
                ('Hiking Backpack', 129.99, 4.5, 'Osprey'),
                ('Fishing Rod', 89.99, 4.2, 'Shimano'),
                ('Ski Goggles', 79.99, 4.3, 'Oakley'),
                ('Baseball Glove', 69.99, 4.4, 'Rawlings'),
                ('Surfboard', 449.99, 4.6, 'Channel Islands'),
                ('Boxing Gloves', 59.99, 4.1, 'Everlast'),
                ('Resistance Bands', 24.99, 4.0, 'TRX'),
            ],
            'Beauty': [
                ('Face Cream', 89.99, 4.6, 'La Mer'),
                ('Makeup Palette', 59.99, 4.5, 'Urban Decay'),
                ('Hair Dryer', 129.99, 4.4, 'Dyson'),
                ('Perfume', 99.99, 4.7, 'Chanel'),
                ('Shampoo Set', 49.99, 4.3, 'Olaplex'),
                ('Nail Polish Set', 34.99, 4.2, 'OPI'),
                ('Skincare Set', 79.99, 4.5, 'Drunk Elephant'),
                ('Face Serum', 69.99, 4.6, 'The Ordinary'),
                ('Lipstick Set', 44.99, 4.3, 'MAC'),
                ('Body Lotion', 39.99, 4.2, 'Cetaphil'),
                ('Sunscreen', 29.99, 4.4, 'Neutrogena'),
                ('Eye Cream', 59.99, 4.5, 'Kiehl\'s'),
                ('Facial Cleanser', 34.99, 4.3, 'CeraVe'),
                ('Hair Straightener', 89.99, 4.4, 'GHD'),
                ('Makeup Brushes', 49.99, 4.1, 'Morphe'),
            ],
            'Books': [
                ('Fiction Bestseller', 19.99, 4.6, 'Penguin'),
                ('Self-Help Book', 24.99, 4.5, 'Simon & Schuster'),
                ('Cookbook', 29.99, 4.7, 'Williams Sonoma'),
                ('Business Book', 27.99, 4.4, 'HarperCollins'),
                ('Children\'s Book', 14.99, 4.8, 'Scholastic'),
                ('Mystery Novel', 16.99, 4.3, 'Random House'),
                ('Biography', 22.99, 4.6, 'Knopf'),
                ('Science Book', 31.99, 4.5, 'National Geographic'),
                ('Travel Guide', 19.99, 4.2, 'Lonely Planet'),
                ('Art Book', 39.99, 4.4, 'Taschen'),
                ('History Book', 26.99, 4.3, 'Vintage'),
                ('Poetry Collection', 18.99, 4.1, 'FSG'),
                ('Graphic Novel', 24.99, 4.6, 'DC Comics'),
                ('Textbook', 89.99, 4.0, 'McGraw-Hill'),
                ('Audio Book', 29.99, 4.5, 'Audible'),
            ],
            'Toys': [
                ('LEGO Set', 79.99, 4.8, 'LEGO'),
                ('Board Game', 39.99, 4.6, 'Hasbro'),
                ('Action Figure', 24.99, 4.5, 'Mattel'),
                ('Puzzle', 19.99, 4.4, 'Ravensburger'),
                ('Doll House', 89.99, 4.7, 'KidKraft'),
                ('Remote Control Car', 49.99, 4.5, 'Traxxas'),
                ('Building Blocks', 34.99, 4.6, 'Mega Bloks'),
                ('Educational Toy', 29.99, 4.4, 'LeapFrog'),
                ('Stuffed Animal', 24.99, 4.3, 'Jellycat'),
                ('Play Kitchen', 99.99, 4.6, 'Step2'),
                ('Toy Train Set', 59.99, 4.5, 'Thomas & Friends'),
                ('Science Kit', 44.99, 4.7, 'National Geographic'),
                ('Art Supplies', 29.99, 4.2, 'Crayola'),
                ('Musical Toy', 39.99, 4.3, 'Baby Einstein'),
                ('Outdoor Playset', 199.99, 4.6, 'Little Tikes'),
            ],
        }
        
        for category, items in product_data.items():
            for name, price, rating, brand in items:
                # Generate realistic product attributes
                in_stock = np.random.choice([True, False], p=[0.85, 0.15])
                discount = np.random.choice([0, 10, 15, 20], p=[0.6, 0.2, 0.15, 0.05])
                reviews_count = int(np.random.exponential(200) + 50)
                
                # Tags based on category
                tags = self._generate_product_tags(category, name, price)
                
                products.append({
                    'product_id': f'PROD_{product_id:06d}',
                    'product_name': name,
                    'category': category,
                    'subcategory': self._get_subcategory(category, name),
                    'brand': brand,
                    'price': price,
                    'rating': rating,
                    'reviews_count': reviews_count,
                    'in_stock': in_stock,
                    'discount_percent': discount,
                    'tags': ','.join(tags),
                    'is_featured': np.random.choice([True, False], p=[0.1, 0.9]),
                    'is_new': np.random.choice([True, False], p=[0.15, 0.85]),
                })
                product_id += 1
        
        return pd.DataFrame(products)
    
    def _generate_product_tags(self, category, name, price):
        """Generate relevant tags for products"""
        tags = []
        
        # Price-based tags
        if price > 300:
            tags.append('premium')
        elif price < 50:
            tags.append('budget')
        
        # Category-specific tags
        if category == 'Electronics':
            tags.extend(['tech', 'gadgets'])
        elif category == 'Fashion':
            tags.extend(['clothing', 'style'])
        elif category == 'Home & Garden':
            tags.extend(['home', 'lifestyle'])
        elif category == 'Sports':
            tags.extend(['fitness', 'outdoors'])
        elif category == 'Beauty':
            tags.extend(['cosmetics', 'skincare'])
        elif category == 'Books':
            tags.extend(['reading', 'literature'])
        elif category == 'Toys':
            tags.extend(['kids', 'family'])
        
        # Random additional tags
        additional_tags = ['bestseller', 'trending', 'gift', 'popular', 'recommended']
        tags.append(np.random.choice(additional_tags))
        
        return tags
    
    def _get_subcategory(self, category, name):
        """Get subcategory based on product name"""
        subcategory_map = {
            'Electronics': {'headphones': 'Audio', 'watch': 'Wearables', 'laptop': 'Computers', 
                           'tablet': 'Computers', 'speaker': 'Audio', 'console': 'Gaming',
                           'phone': 'Mobile', 'tracker': 'Wearables', 'earbuds': 'Audio',
                           'charger': 'Accessories', 'monitor': 'Displays', 'webcam': 'Accessories',
                           'keyboard': 'Accessories', 'mouse': 'Accessories', 'hub': 'Accessories'},
            'Fashion': {'jeans': 'Pants', 'jacket': 'Outerwear', 'shoes': 'Footwear',
                       'coat': 'Outerwear', 'shirt': 'Tops', 'pants': 'Bottoms',
                       'dress': 'Dresses', 'boots': 'Footwear', 'sweater': 'Tops',
                       'shorts': 'Bottoms', 'suit': 'Formal', 't-shirt': 'Tops',
                       'scarf': 'Accessories', 'sneakers': 'Footwear'},
            'Home & Garden': {'coffee': 'Kitchen', 'vacuum': 'Appliances', 'purifier': 'Home',
                             'sheets': 'Bedding', 'mixer': 'Kitchen', 'thermostat': 'Smart Home',
                             'tool': 'Garden', 'table': 'Furniture', 'chair': 'Furniture',
                             'lamp': 'Lighting', 'cookware': 'Kitchen', 'towel': 'Bath',
                             'rug': 'Decor', 'art': 'Decor', 'organizer': 'Storage'},
            'Sports': {'yoga': 'Fitness', 'dumbbell': 'Fitness', 'racket': 'Sports',
                      'golf': 'Golf', 'ball': 'Sports', 'bike': 'Fitness',
                      'tent': 'Camping', 'backpack': 'Outdoor', 'rod': 'Fishing',
                      'goggles': 'Accessories', 'glove': 'Sports', 'surfboard': 'Water Sports',
                      'boxing': 'Fitness', 'bands': 'Fitness'},
            'Beauty': {'cream': 'Skincare', 'makeup': 'Cosmetics', 'dryer': 'Hair Care',
                      'perfume': 'Fragrance', 'shampoo': 'Hair Care', 'polish': 'Nails',
                      'serum': 'Skincare', 'lipstick': 'Cosmetics', 'lotion': 'Body Care',
                      'sunscreen': 'Skincare', 'eye cream': 'Skincare', 'cleanser': 'Skincare',
                      'straightener': 'Hair Care', 'brushes': 'Tools'},
            'Books': {'fiction': 'Fiction', 'self-help': 'Self-Help', 'cookbook': 'Cooking',
                     'business': 'Business', 'children': 'Kids', 'mystery': 'Fiction',
                     'biography': 'Non-Fiction', 'science': 'Science', 'travel': 'Travel',
                     'art': 'Art', 'history': 'History', 'poetry': 'Poetry',
                     'graphic': 'Comics', 'textbook': 'Educational', 'audio': 'Audiobooks'},
            'Toys': {'lego': 'Building', 'game': 'Games', 'figure': 'Figures',
                    'puzzle': 'Puzzles', 'house': 'Dolls', 'car': 'Vehicles',
                    'blocks': 'Building', 'educational': 'Learning', 'stuffed': 'Plush',
                    'kitchen': 'Pretend Play', 'train': 'Vehicles', 'kit': 'Science',
                    'art': 'Creative', 'musical': 'Music', 'playset': 'Outdoor'}
        }
        
        name_lower = name.lower()
        for key, subcat in subcategory_map.get(category, {}).items():
            if key in name_lower:
                return subcat
        
        return 'General'
    
    def generate_transactions(self, customers_df, products_df):
        """Generate purchase transactions"""
        transactions = []
        trans_id = 1
        
        for _, customer in customers_df.iterrows():
            n_purchases = int(customer['total_purchases'])
            
            for purchase_num in range(n_purchases):
                # Purchase date
                days_ago = int(np.random.exponential(30) + 1)
                purchase_date = datetime.now() - timedelta(days=days_ago)
                
                # Basket size
                basket_size = max(1, int(np.random.poisson(customer['avg_basket_size'])))
                
                # Select products (prefer customer's preferred category)
                preferred_products = products_df[products_df['category'] == customer['preferred_category']]
                other_products = products_df[products_df['category'] != customer['preferred_category']]
                
                # 60% from preferred category, 40% from others
                n_preferred = int(basket_size * 0.6) + 1
                n_other = basket_size - n_preferred
                
                selected_products = []
                if n_preferred > 0 and len(preferred_products) > 0:
                    selected_products.extend(preferred_products.sample(n=min(n_preferred, len(preferred_products))).to_dict('records'))
                if n_other > 0 and len(other_products) > 0:
                    selected_products.extend(other_products.sample(n=min(n_other, len(other_products))).to_dict('records'))
                
                # Create transaction for each item
                for product in selected_products:
                    quantity = np.random.choice([1, 2, 3], p=[0.7, 0.2, 0.1])
                    unit_price = product['price'] * (1 - product['discount_percent'] / 100)
                    total_amount = unit_price * quantity
                    
                    transactions.append({
                        'transaction_id': f'TRANS_{trans_id:010d}',
                        'customer_id': customer['customer_id'],
                        'product_id': product['product_id'],
                        'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                        'quantity': quantity,
                        'unit_price': round(unit_price, 2),
                        'total_amount': round(total_amount, 2),
                        'channel': customer['channel_preference'],
                        'payment_method': np.random.choice(['credit_card', 'debit_card', 'paypal', 'apple_pay'], p=[0.5, 0.3, 0.15, 0.05])
                    })
                    trans_id += 1
        
        return pd.DataFrame(transactions)


if __name__ == "__main__":
    generator = EnhancedRetailDataGenerator(n_customers=150, n_products=130)
    generator.generate_all()
    print("\n✅ Enhanced Retail Dataset Generation Complete!")


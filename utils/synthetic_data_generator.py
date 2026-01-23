"""Synthetic data generator for the personalization system."""
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
from typing import Tuple, List
import json
from pathlib import Path

fake = Faker()
np.random.seed(42)
Faker.seed(42)


class SyntheticDataGenerator:
    """Generate synthetic customer, product, and transaction data."""
    
    def __init__(self, output_dir: str = "data/synthetic"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Product categories
        self.categories = [
            "Electronics", "Clothing", "Home & Garden", "Sports & Outdoors",
            "Books", "Beauty & Personal Care", "Toys & Games", "Automotive",
            "Health & Wellness", "Food & Beverage"
        ]
        
        # Channels
        self.channels = ["web", "mobile_app", "in_store", "phone", "social_media"]
        
        # Life events
        self.life_events = ["new_job", "relocation", "marriage", "new_home", "new_baby", "none"]
        
        # Customer intents
        self.intents = ["exploring", "ready_to_buy", "comparison_shopping", "abandoned_cart", "loyalty", "dormant"]
    
    def generate_customers(self, n_customers: int = 2000) -> pd.DataFrame:
        """Generate synthetic customer data."""
        print(f"⚡ Generating {n_customers} synthetic customers...")
        
        customers = []
        for i in range(n_customers):
            if i % 500 == 0 and i > 0:
                print(f"   Generated {i:,} customers...")
            customer = {
                "customer_id": f"CUST_{i:06d}",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80),
                "gender": np.random.choice(["M", "F", "Other"], p=[0.48, 0.48, 0.04]),
                "city": fake.city(),
                "state": fake.state(),
                "zipcode": fake.zipcode(),
                "country": "USA",
                "registration_date": fake.date_between(start_date="-5y", end_date="today"),
                "preferred_channel": np.random.choice(self.channels, p=[0.35, 0.30, 0.20, 0.10, 0.05]),
                "life_event": np.random.choice(self.life_events, p=[0.05, 0.05, 0.03, 0.07, 0.05, 0.75]),
                "income_range": np.random.choice(
                    ["<30K", "30K-50K", "50K-75K", "75K-100K", "100K-150K", ">150K"],
                    p=[0.15, 0.20, 0.25, 0.20, 0.12, 0.08]
                ),
                "loyalty_tier": np.random.choice(["Bronze", "Silver", "Gold", "Platinum"], p=[0.50, 0.30, 0.15, 0.05]),
                "is_active": np.random.choice([True, False], p=[0.75, 0.25])
            }
            customers.append(customer)
        
        df = pd.DataFrame(customers)
        df.to_csv(self.output_dir / "customers.csv", index=False)
        print(f"✓ Customers saved to {self.output_dir / 'customers.csv'}")
        return df
    
    def generate_products(self, n_products: int = 100) -> pd.DataFrame:
        """Generate synthetic product catalog."""
        print(f"Generating {n_products} synthetic products...")
        
        products = []
        for i in range(n_products):
            category = np.random.choice(self.categories)
            base_price = np.random.uniform(10, 1000)
            
            product = {
                "product_id": f"PROD_{i:04d}",
                "product_name": f"{fake.word().title()} {fake.word().title()} {category[:-1] if category.endswith('s') else category}",
                "category": category,
                "subcategory": fake.word().title(),
                "brand": fake.company(),
                "base_price": round(base_price, 2),
                "cost": round(base_price * 0.6, 2),
                "margin_pct": 40.0,
                "inventory_count": np.random.randint(0, 500),
                "rating": round(np.random.uniform(3.0, 5.0), 1),
                "num_reviews": np.random.randint(0, 1000),
                "is_featured": np.random.choice([True, False], p=[0.20, 0.80]),
                "is_seasonal": np.random.choice([True, False], p=[0.15, 0.85]),
                "launch_date": fake.date_between(start_date="-3y", end_date="today"),
                "description": fake.text(max_nb_chars=200)
            }
            products.append(product)
        
        df = pd.DataFrame(products)
        df.to_csv(self.output_dir / "products.csv", index=False)
        print(f"✓ Products saved to {self.output_dir / 'products.csv'}")
        return df
    
    def generate_transactions(
        self, 
        customers_df: pd.DataFrame, 
        products_df: pd.DataFrame,
        n_transactions: int = 10000
    ) -> pd.DataFrame:
        """Generate synthetic transaction history."""
        print(f"⚡ Generating {n_transactions} synthetic transactions...")
        
        transactions = []
        customer_ids = customers_df["customer_id"].tolist()
        product_ids = products_df["product_id"].tolist()
        product_prices = dict(zip(products_df["product_id"], products_df["base_price"]))
        
        for i in range(n_transactions):
            if i % 2500 == 0 and i > 0:
                print(f"   Generated {i:,} transactions...")
            customer_id = np.random.choice(customer_ids)
            product_id = np.random.choice(product_ids)
            quantity = np.random.choice([1, 2, 3], p=[0.7, 0.2, 0.1])
            base_price = product_prices[product_id]
            
            # Apply random discount
            discount_pct = np.random.choice([0, 5, 10, 15, 20], p=[0.5, 0.2, 0.15, 0.1, 0.05])
            final_price = base_price * (1 - discount_pct / 100)
            
            transaction = {
                "transaction_id": f"TXN_{i:08d}",
                "customer_id": customer_id,
                "product_id": product_id,
                "transaction_date": fake.date_time_between(start_date="-18M", end_date="now"),
                "quantity": quantity,
                "unit_price": round(base_price, 2),
                "discount_pct": discount_pct,
                "final_price": round(final_price, 2),
                "total_amount": round(final_price * quantity, 2),
                "channel": np.random.choice(self.channels, p=[0.35, 0.30, 0.20, 0.10, 0.05]),
                "payment_method": np.random.choice(["credit_card", "debit_card", "paypal", "apple_pay"], p=[0.45, 0.30, 0.15, 0.10]),
                "is_returned": np.random.choice([True, False], p=[0.05, 0.95]),
                "customer_rating": np.random.choice([3, 4, 5, None], p=[0.1, 0.3, 0.4, 0.2])
            }
            transactions.append(transaction)
        
        df = pd.DataFrame(transactions)
        df = df.sort_values("transaction_date").reset_index(drop=True)
        df.to_csv(self.output_dir / "transactions.csv", index=False)
        print(f"✓ Transactions saved to {self.output_dir / 'transactions.csv'}")
        return df
    
    def generate_behavioral_events(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        n_events: int = 20000
    ) -> pd.DataFrame:
        """Generate synthetic behavioral events (clicks, views, carts)."""
        print(f"⚡ Generating {n_events} synthetic behavioral events...")
        
        events = []
        customer_ids = customers_df["customer_id"].tolist()
        product_ids = products_df["product_id"].tolist()
        event_types = ["page_view", "product_view", "add_to_cart", "remove_from_cart", "search", "filter"]
        
        for i in range(n_events):
            if i % 5000 == 0 and i > 0:
                print(f"   Generated {i:,} events...")
            event = {
                "event_id": f"EVT_{i:08d}",
                "customer_id": np.random.choice(customer_ids),
                "event_type": np.random.choice(event_types, p=[0.30, 0.35, 0.15, 0.05, 0.10, 0.05]),
                "product_id": np.random.choice(product_ids) if np.random.random() > 0.2 else None,
                "timestamp": fake.date_time_between(start_date="-6M", end_date="now"),
                "session_id": f"SESS_{np.random.randint(0, 50000):06d}",
                "device": np.random.choice(["desktop", "mobile", "tablet"], p=[0.45, 0.45, 0.10]),
                "browser": np.random.choice(["Chrome", "Safari", "Firefox", "Edge"], p=[0.50, 0.30, 0.15, 0.05]),
                "duration_seconds": np.random.randint(5, 300) if np.random.random() > 0.3 else None
            }
            events.append(event)
        
        df = pd.DataFrame(events)
        df = df.sort_values("timestamp").reset_index(drop=True)
        df.to_csv(self.output_dir / "behavioral_events.csv", index=False)
        print(f"✓ Behavioral events saved to {self.output_dir / 'behavioral_events.csv'}")
        return df
    
    def generate_all(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate all synthetic data."""
        print("\n" + "="*60)
        print("🎲 SYNTHETIC DATA GENERATION (OPTIMIZED)")
        print("="*60 + "\n")
        
        customers_df = self.generate_customers(n_customers=2000)
        products_df = self.generate_products(n_products=100)
        transactions_df = self.generate_transactions(customers_df, products_df, n_transactions=10000)
        behavioral_df = self.generate_behavioral_events(customers_df, products_df, n_events=20000)
        
        # Generate summary stats
        self._generate_summary_stats(customers_df, products_df, transactions_df, behavioral_df)
        
        print("\n" + "="*60)
        print("✅ SYNTHETIC DATA GENERATION COMPLETE!")
        print("="*60 + "\n")
        
        return customers_df, products_df, transactions_df, behavioral_df
    
    def _generate_summary_stats(self, customers_df, products_df, transactions_df, behavioral_df):
        """Generate and save summary statistics."""
        # Convert value_counts to dict with native Python types
        def counts_to_dict(series):
            return {str(k): int(v) for k, v in series.items()}
        
        stats = {
            "generation_timestamp": datetime.now().isoformat(),
            "customers": {
                "total_count": int(len(customers_df)),
                "active_count": int(customers_df["is_active"].sum()),
                "by_loyalty_tier": counts_to_dict(customers_df["loyalty_tier"].value_counts()),
                "by_preferred_channel": counts_to_dict(customers_df["preferred_channel"].value_counts())
            },
            "products": {
                "total_count": int(len(products_df)),
                "by_category": counts_to_dict(products_df["category"].value_counts()),
                "avg_price": float(products_df["base_price"].mean()),
                "featured_count": int(products_df["is_featured"].sum())
            },
            "transactions": {
                "total_count": int(len(transactions_df)),
                "total_revenue": float(transactions_df["total_amount"].sum()),
                "avg_transaction_value": float(transactions_df["total_amount"].mean()),
                "by_channel": counts_to_dict(transactions_df["channel"].value_counts()),
                "return_rate": float(transactions_df["is_returned"].mean())
            },
            "behavioral_events": {
                "total_count": int(len(behavioral_df)),
                "by_event_type": counts_to_dict(behavioral_df["event_type"].value_counts()),
                "by_device": counts_to_dict(behavioral_df["device"].value_counts())
            }
        }
        
        with open(self.output_dir / "summary_stats.json", "w") as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n📊 Summary Statistics:")
        print(f"   ✓ Customers: {stats['customers']['total_count']:,} ({stats['customers']['active_count']:,} active)")
        print(f"   ✓ Products: {stats['products']['total_count']:,} (Avg price: ${stats['products']['avg_price']:.2f})")
        print(f"   ✓ Transactions: {stats['transactions']['total_count']:,} (Total revenue: ${stats['transactions']['total_revenue']:,.2f})")
        print(f"   ✓ Behavioral Events: {stats['behavioral_events']['total_count']:,}")
        print(f"\n⚡ Generation complete in record time!")


if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    generator.generate_all()


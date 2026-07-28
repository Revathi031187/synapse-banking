"""
Pre-loaded Dataset Generator
Creates realistic datasets for different domains
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import random

from utils.logger import get_logger

logger = get_logger("DatasetGenerator")


class PreloadedDatasetGenerator:
    """Generate realistic pre-loaded datasets for different domains."""
    
    def __init__(self):
        self.output_dir = Path("data/preloaded")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("📦 Pre-loaded Dataset Generator initialized")
    
    def generate_ecommerce_dataset(self, n_customers: int = 1000):
        """Generate e-commerce dataset."""
        logger.info(f"🛍️ Generating e-commerce dataset ({n_customers} customers)...")
        
        # Customers
        customers = []
        for i in range(n_customers):
            customers.append({
                'customer_id': f'CUST_{i:06d}',
                'name': f'Customer {i}',
                'email': f'customer{i}@email.com',
                'age': np.random.randint(18, 75),
                'gender': np.random.choice(['Male', 'Female', 'Other'], p=[0.48, 0.48, 0.04]),
                'income': np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.5, 0.2]),
                'location': np.random.choice(['Urban', 'Suburban', 'Rural'], p=[0.5, 0.3, 0.2]),
                'join_date': (datetime.now() - timedelta(days=np.random.randint(30, 730))).strftime('%Y-%m-%d')
            })
        
        customers_df = pd.DataFrame(customers)
        
        # Products
        categories = ['Electronics', 'Fashion', 'Home & Kitchen', 'Sports', 'Books', 'Beauty', 'Toys', 'Grocery']
        products = []
        product_names = {
            'Electronics': ['Laptop', 'Smartphone', 'Headphones', 'Tablet', 'Smart Watch', 'Camera'],
            'Fashion': ['T-Shirt', 'Jeans', 'Dress', 'Shoes', 'Jacket', 'Accessories'],
            'Home & Kitchen': ['Blender', 'Coffee Maker', 'Cookware Set', 'Vacuum', 'Air Fryer'],
            'Sports': ['Yoga Mat', 'Dumbbells', 'Running Shoes', 'Bike', 'Fitness Tracker'],
            'Books': ['Fiction Novel', 'Self-Help Book', 'Cookbook', 'Biography', 'Textbook'],
            'Beauty': ['Skincare Set', 'Makeup Kit', 'Perfume', 'Hair Care', 'Spa Kit'],
            'Toys': ['Board Game', 'Action Figure', 'Puzzle', 'LEGO Set', 'Doll'],
            'Grocery': ['Organic Snacks', 'Beverages', 'Fresh Produce', 'Dairy Products']
        }
        
        product_id = 0
        for category in categories:
            for product_name in product_names.get(category, []):
                products.append({
                    'product_id': f'PROD_{product_id:04d}',
                    'product_name': product_name,
                    'category': category,
                    'price': np.random.uniform(10, 1000),
                    'description': f'{product_name} in {category} category'
                })
                product_id += 1
        
        products_df = pd.DataFrame(products)
        
        # Transactions
        transactions = []
        trans_id = 0
        for customer in customers:
            # Number of transactions per customer (power law distribution)
            n_trans = min(int(np.random.pareto(0.5) + 1), 50)
            
            for _ in range(n_trans):
                product = products[np.random.randint(0, len(products))]
                trans_date = datetime.strptime(customer['join_date'], '%Y-%m-%d') + timedelta(days=np.random.randint(0, 365))
                
                transactions.append({
                    'transaction_id': f'TRANS_{trans_id:08d}',
                    'customer_id': customer['customer_id'],
                    'product_id': product['product_id'],
                    'total_amount': product['price'] * np.random.uniform(0.8, 1.2),  # Some variance
                    'quantity': np.random.randint(1, 4),
                    'transaction_date': trans_date.strftime('%Y-%m-%d'),
                    'channel': np.random.choice(['Online', 'Mobile App', 'Store'], p=[0.5, 0.3, 0.2])
                })
                trans_id += 1
        
        transactions_df = pd.DataFrame(transactions)
        
        # Save
        output_path = self.output_dir / "ecommerce"
        output_path.mkdir(exist_ok=True)
        
        customers_df.to_csv(output_path / "customers.csv", index=False)
        products_df.to_csv(output_path / "products.csv", index=False)
        transactions_df.to_csv(output_path / "transactions.csv", index=False)
        
        logger.info(f"✅ E-commerce dataset saved to {output_path}")
        logger.info(f"   - {len(customers_df)} customers")
        logger.info(f"   - {len(products_df)} products")
        logger.info(f"   - {len(transactions_df)} transactions")
        
        return {
            'customers': len(customers_df),
            'products': len(products_df),
            'transactions': len(transactions_df)
        }
    
    def generate_sports_academy_dataset(self, n_students: int = 800):
        """Generate sports academy dataset."""
        logger.info(f"⚽ Generating sports academy dataset ({n_students} students)...")
        
        # Students (customers)
        students = []
        for i in range(n_students):
            students.append({
                'customer_id': f'STU_{i:05d}',
                'name': f'Student {i}',
                'email': f'student{i}@academy.com',
                'age': np.random.randint(8, 60),
                'gender': np.random.choice(['Male', 'Female'], p=[0.55, 0.45]),
                'skill_level': np.random.choice(['Beginner', 'Intermediate', 'Advanced'], p=[0.4, 0.4, 0.2]),
                'join_date': (datetime.now() - timedelta(days=np.random.randint(30, 1095))).strftime('%Y-%m-%d'),
                'location': np.random.choice(['North', 'South', 'East', 'West'])
            })
        
        students_df = pd.DataFrame(students)
        
        # Programs (products)
        programs = []
        sports = ['Soccer', 'Basketball', 'Tennis', 'Swimming', 'Martial Arts', 'Yoga', 'Fitness', 'Dance']
        levels = ['Kids', 'Youth', 'Adult', 'Senior']
        
        program_id = 0
        for sport in sports:
            for level in levels:
                programs.append({
                    'product_id': f'PROG_{program_id:04d}',
                    'product_name': f'{sport} - {level} Class',
                    'category': sport,
                    'price': np.random.uniform(50, 300),
                    'description': f'{level} level {sport} training program',
                    'duration_months': np.random.choice([1, 3, 6, 12])
                })
                program_id += 1
        
        programs_df = pd.DataFrame(programs)
        
        # Enrollments (transactions)
        enrollments = []
        enroll_id = 0
        for student in students:
            # Students typically enroll in 1-4 programs
            n_enrollments = np.random.randint(1, 5)
            
            for _ in range(n_enrollments):
                program = programs[np.random.randint(0, len(programs))]
                enroll_date = datetime.strptime(student['join_date'], '%Y-%m-%d') + timedelta(days=np.random.randint(0, 365))
                
                enrollments.append({
                    'transaction_id': f'ENROLL_{enroll_id:08d}',
                    'customer_id': student['customer_id'],
                    'product_id': program['product_id'],
                    'total_amount': program['price'],
                    'quantity': 1,
                    'transaction_date': enroll_date.strftime('%Y-%m-%d'),
                    'channel': np.random.choice(['Website', 'Phone', 'In-Person'], p=[0.5, 0.2, 0.3])
                })
                enroll_id += 1
        
        enrollments_df = pd.DataFrame(enrollments)
        
        # Save
        output_path = self.output_dir / "sports_academy"
        output_path.mkdir(exist_ok=True)
        
        students_df.to_csv(output_path / "customers.csv", index=False)
        programs_df.to_csv(output_path / "products.csv", index=False)
        enrollments_df.to_csv(output_path / "transactions.csv", index=False)
        
        logger.info(f"✅ Sports academy dataset saved to {output_path}")
        logger.info(f"   - {len(students_df)} students")
        logger.info(f"   - {len(programs_df)} programs")
        logger.info(f"   - {len(enrollments_df)} enrollments")
        
        return {
            'customers': len(students_df),
            'products': len(programs_df),
            'transactions': len(enrollments_df)
        }
    
    def generate_banking_dataset(self, n_customers: int = 1200):
        """Generate banking dataset."""
        logger.info(f"🏦 Generating banking dataset ({n_customers} customers)...")
        
        # Customers
        customers = []
        for i in range(n_customers):
            customers.append({
                'customer_id': f'ACC_{i:06d}',
                'name': f'Account Holder {i}',
                'email': f'holder{i}@bank.com',
                'age': np.random.randint(22, 70),
                'gender': np.random.choice(['Male', 'Female'], p=[0.5, 0.5]),
                'income': np.random.choice(['<30K', '30K-60K', '60K-100K', '>100K'], p=[0.2, 0.35, 0.3, 0.15]),
                'account_type': np.random.choice(['Savings', 'Checking', 'Premium'], p=[0.5, 0.4, 0.1]),
                'join_date': (datetime.now() - timedelta(days=np.random.randint(180, 3650))).strftime('%Y-%m-%d')
            })
        
        customers_df = pd.DataFrame(customers)
        
        # Products (banking services)
        products = [
            {'product_id': 'SVC_001', 'product_name': 'Credit Card', 'category': 'Credit', 'price': 0, 'description': 'Standard credit card'},
            {'product_id': 'SVC_002', 'product_name': 'Premium Credit Card', 'category': 'Credit', 'price': 95, 'description': 'Premium rewards card'},
            {'product_id': 'SVC_003', 'product_name': 'Personal Loan', 'category': 'Lending', 'price': 0, 'description': 'Personal loan product'},
            {'product_id': 'SVC_004', 'product_name': 'Home Loan', 'category': 'Lending', 'price': 0, 'description': 'Home mortgage'},
            {'product_id': 'SVC_005', 'product_name': 'Auto Loan', 'category': 'Lending', 'price': 0, 'description': 'Vehicle financing'},
            {'product_id': 'SVC_006', 'product_name': 'Investment Account', 'category': 'Investment', 'price': 0, 'description': 'Investment portfolio'},
            {'product_id': 'SVC_007', 'product_name': 'Fixed Deposit', 'category': 'Savings', 'price': 0, 'description': 'Fixed deposit account'},
            {'product_id': 'SVC_008', 'product_name': 'Insurance Policy', 'category': 'Insurance', 'price': 500, 'description': 'Life insurance'},
            {'product_id': 'SVC_009', 'product_name': 'Debit Card', 'category': 'Cards', 'price': 0, 'description': 'ATM debit card'},
            {'product_id': 'SVC_010', 'product_name': 'Online Banking', 'category': 'Digital', 'price': 0, 'description': 'Digital banking service'}
        ]
        
        products_df = pd.DataFrame(products)
        
        # Transactions (service adoptions/usage)
        transactions = []
        trans_id = 0
        
        for customer in customers:
            # Banking customers have 1-5 products
            n_products = np.random.randint(1, 6)
            selected_products = np.random.choice(products, n_products, replace=False)
            
            for product in selected_products:
                adoption_date = datetime.strptime(customer['join_date'], '%Y-%m-%d') + timedelta(days=np.random.randint(0, 365))
                
                # Transaction amount varies by product
                if product['product_id'] in ['SVC_003', 'SVC_004', 'SVC_005']:  # Loans
                    amount = np.random.uniform(5000, 500000)
                elif product['product_id'] in ['SVC_006', 'SVC_007']:  # Investments
                    amount = np.random.uniform(1000, 100000)
                elif product['product_id'] in ['SVC_002', 'SVC_008']:  # Premium/Insurance
                    amount = product['price']
                else:
                    amount = 0  # Free services
                
                transactions.append({
                    'transaction_id': f'TXN_{trans_id:08d}',
                    'customer_id': customer['customer_id'],
                    'product_id': product['product_id'],
                    'total_amount': amount,
                    'quantity': 1,
                    'transaction_date': adoption_date.strftime('%Y-%m-%d'),
                    'channel': np.random.choice(['Branch', 'Online', 'Mobile App', 'Phone'], p=[0.2, 0.4, 0.3, 0.1])
                })
                trans_id += 1
        
        transactions_df = pd.DataFrame(transactions)
        
        # Save
        output_path = self.output_dir / "banking"
        output_path.mkdir(exist_ok=True)
        
        customers_df.to_csv(output_path / "customers.csv", index=False)
        products_df.to_csv(output_path / "products.csv", index=False)
        transactions_df.to_csv(output_path / "transactions.csv", index=False)
        
        logger.info(f"✅ Banking dataset generated: {len(customers_df)} customers, {len(products_df)} products, {len(transactions_df)} transactions")
        
        return len(customers_df), len(products_df), len(transactions_df)
    
    def generate_all_datasets(self):
        """Generate all pre-loaded datasets."""
        logger.info("="*80)
        logger.info("📦 GENERATING ALL PRE-LOADED DATASETS")
        logger.info("="*80)
        
        results = {}
        
        # E-commerce
        logger.info("\n[1/3] 🛍️ E-commerce Dataset")
        results['ecommerce'] = self.generate_ecommerce_dataset(1000)
        
        # Sports Academy
        logger.info("\n[2/3] ⚽ Sports Academy Dataset")
        results['sports_academy'] = self.generate_sports_academy_dataset(800)
        
        # Banking
        logger.info("\n[3/3] 🏦 Banking Dataset")
        results['banking'] = self.generate_banking_dataset(1200)
        
        logger.info("\n" + "="*80)
        logger.info("✅ ALL DATASETS GENERATED SUCCESSFULLY")
        logger.info("="*80)
        
        return results


# Run if executed directly
if __name__ == "__main__":
    generator = PreloadedDatasetGenerator()
    generator.generate_all_datasets()


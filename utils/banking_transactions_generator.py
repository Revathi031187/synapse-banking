"""
Banking Platform - Transaction History Generator
Generates synthetic transaction history (product adoptions)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

np.random.seed(42)

class BankingTransactionsGenerator:
    """Generate transaction history for banking customers"""
    
    def __init__(self):
        self.output_dir = Path("data/preloaded/banking")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_transactions(self):
        """Generate transaction history"""
        print("="*70)
        print("💰 BANKING TRANSACTIONS GENERATOR")
        print("="*70)
        
        # Load customers and products
        print("\n📊 Loading customers and products...")
        customers_df = pd.read_csv(self.output_dir / "customers.csv")
        products_df = pd.read_csv(self.output_dir / "products.csv")
        
        print(f"   Customers: {len(customers_df)}")
        print(f"   Products: {len(products_df)}")
        
        # Generate transactions
        print("\n💳 Generating transactions...")
        transactions = []
        base_date = datetime.now() - timedelta(days=730)
        
        for _, customer in customers_df.iterrows():
            customer_transactions = self._generate_customer_transactions(
                customer, products_df, base_date
            )
            transactions.extend(customer_transactions)
        
        df = pd.DataFrame(transactions)
        
        # Save
        output_path = self.output_dir / "transactions.csv"
        df.to_csv(output_path, index=False)
        
        print(f"\n✅ Generated {len(df)} transactions")
        print(f"   Saved to: {output_path}")
        
        self._print_summary(df, customers_df)
        
        return df
    
    def _generate_customer_transactions(self, customer, products_df, base_date):
        """Generate transactions for a single customer"""
        transactions = []
        persona = customer['true_persona']
        num_products = int(customer['num_products'])
        
        # Determine which products this customer should have
        if persona == 'High_Net_Worth':
            products = self._select_hnw_products(products_df, num_products)
        elif persona == 'Young_Professional':
            products = self._select_young_pro_products(products_df, num_products)
        elif persona == 'Small_Business':
            products = self._select_business_products(products_df, num_products)
        elif persona == 'Mass_Market':
            products = self._select_mass_market_products(products_df, num_products)
        else:  # Digital_Native
            products = self._select_digital_native_products(products_df, num_products)
        
        # Generate transactions for each product
        join_date = pd.to_datetime(customer['join_date'])
        
        for product in products:
            # When was this product opened/activated?
            days_since_join = np.random.randint(0, min(365, (datetime.now() - join_date).days))
            transaction_date = join_date + timedelta(days=days_since_join)
            
            # Transaction type based on product category
            category = product['category']
            if category == 'Credit Cards':
                transaction_type = 'credit_card_activated'
                amount = 0
            elif category == 'Personal Loans':
                transaction_type = 'loan_approved'
                amount = np.random.uniform(5000, product['max_amount'])
            elif category == 'Accounts':
                transaction_type = 'account_opened'
                amount = np.random.uniform(100, customer['total_deposits'] * 0.3)
            elif category == 'Mortgages':
                transaction_type = 'mortgage_approved'
                amount = np.random.uniform(150000, 750000)
            elif category == 'Investments':
                transaction_type = 'investment_started'
                amount = np.random.uniform(product['min_investment'], customer['total_deposits'] * 0.5)
            else:  # Business Banking
                transaction_type = 'business_account_opened'
                amount = np.random.uniform(5000, 100000)
            
            # Channel based on customer preference
            if customer['digital_engagement_score'] > 0.7:
                channel = np.random.choice(['Web', 'Mobile'], p=[0.4, 0.6])
            elif customer['branch_visit_frequency'] > 0.5:
                channel = np.random.choice(['Branch', 'Web'], p=[0.7, 0.3])
            else:
                channel = np.random.choice(['Web', 'Branch', 'Mobile', 'Call Center'], p=[0.4, 0.3, 0.2, 0.1])
            
            transactions.append({
                'customer_id': customer['customer_id'],
                'product_id': product['product_id'],
                'transaction_date': transaction_date.strftime('%Y-%m-%d'),
                'transaction_type': transaction_type,
                'amount': round(amount, 2),
                'channel': channel,
                'approval_status': 'approved'
            })
        
        return transactions
    
    def _select_hnw_products(self, products_df, num_products):
        """Select products for High Net Worth customers"""
        # HNW customers prefer premium/platinum cards, investments, mortgages
        preferred_products = []
        
        # Always get premium checking
        checking = products_df[
            (products_df['category'] == 'Accounts') & 
            (products_df['product_name'].str.contains('Premium|Interest'))
        ].sample(1)
        preferred_products.append(checking.iloc[0])
        
        # Premium credit cards
        if num_products > 1:
            cards = products_df[
                (products_df['category'] == 'Credit Cards') & 
                (products_df['subcategory'].isin(['Platinum', 'Premium']))
            ].sample(min(2, num_products - 1))
            preferred_products.extend(cards.to_dict('records'))
        
        # Investments
        if num_products > 3:
            investments = products_df[
                products_df['category'] == 'Investments'
            ].sample(min(2, num_products - len(preferred_products)))
            preferred_products.extend(investments.to_dict('records'))
        
        # Fill remaining with mortgages or business banking
        remaining = num_products - len(preferred_products)
        if remaining > 0:
            other = products_df[
                products_df['category'].isin(['Mortgages', 'Business Banking'])
            ].sample(min(remaining, len(products_df)))
            preferred_products.extend(other.to_dict('records'))
        
        return preferred_products[:num_products]
    
    def _select_young_pro_products(self, products_df, num_products):
        """Select products for Young Professionals"""
        preferred_products = []
        
        # Basic/premium checking
        checking = products_df[
            (products_df['category'] == 'Accounts') & 
            (products_df['product_name'].str.contains('Basic|Student|Interest'))
        ].sample(1)
        preferred_products.append(checking.iloc[0])
        
        # Credit cards (basic to premium)
        if num_products > 1:
            cards = products_df[
                (products_df['category'] == 'Credit Cards') & 
                (products_df['subcategory'].isin(['Basic', 'Premium']))
            ].sample(1)
            preferred_products.append(cards.iloc[0])
        
        # Savings or investment
        if num_products > 2:
            savings = products_df[
                (products_df['category'].isin(['Accounts', 'Investments'])) &
                (products_df['product_name'].str.contains('Savings|Robo|IRA'))
            ].sample(1)
            preferred_products.append(savings.iloc[0])
        
        # Personal loan
        if num_products > 3:
            loan = products_df[
                products_df['category'] == 'Personal Loans'
            ].sample(1)
            preferred_products.append(loan.iloc[0])
        
        return preferred_products[:num_products]
    
    def _select_business_products(self, products_df, num_products):
        """Select products for Small Business Owners"""
        preferred_products = []
        
        # Business checking
        biz_checking = products_df[
            products_df['product_name'].str.contains('Business')
        ].sample(1)
        preferred_products.append(biz_checking.iloc[0])
        
        # Business credit card
        if num_products > 1:
            biz_card = products_df[
                (products_df['category'] == 'Credit Cards') & 
                (products_df['subcategory'] == 'Business')
            ].sample(1)
            preferred_products.append(biz_card.iloc[0])
        
        # Personal checking
        if num_products > 2:
            checking = products_df[
                (products_df['category'] == 'Accounts') & 
                (products_df['subcategory'] == 'Checking') &
                (~products_df['product_name'].str.contains('Business'))
            ].sample(1)
            preferred_products.append(checking.iloc[0])
        
        # Loans or mortgages
        remaining = num_products - len(preferred_products)
        if remaining > 0:
            loans = products_df[
                products_df['category'].isin(['Personal Loans', 'Mortgages'])
            ].sample(min(remaining, len(products_df)))
            preferred_products.extend(loans.to_dict('records'))
        
        return preferred_products[:num_products]
    
    def _select_mass_market_products(self, products_df, num_products):
        """Select products for Mass Market customers"""
        preferred_products = []
        
        # Basic checking
        checking = products_df[
            (products_df['category'] == 'Accounts') & 
            (products_df['product_name'].str.contains('Basic'))
        ].sample(1)
        preferred_products.append(checking.iloc[0])
        
        # Basic credit card or savings
        if num_products > 1:
            other = products_df[
                ((products_df['category'] == 'Credit Cards') & (products_df['subcategory'] == 'Basic')) |
                ((products_df['category'] == 'Accounts') & (products_df['subcategory'] == 'Savings'))
            ].sample(1)
            preferred_products.append(other.iloc[0])
        
        # Small loan if more products
        if num_products > 2:
            loan = products_df[
                (products_df['category'] == 'Personal Loans') &
                (products_df['product_name'].str.contains('Quick|Emergency'))
            ].sample(1)
            preferred_products.append(loan.iloc[0])
        
        return preferred_products[:num_products]
    
    def _select_digital_native_products(self, products_df, num_products):
        """Select products for Digital Native customers"""
        preferred_products = []
        
        # Student or basic checking
        checking = products_df[
            (products_df['category'] == 'Accounts') & 
            (products_df['product_name'].str.contains('Student|Basic'))
        ].sample(1)
        preferred_products.append(checking.iloc[0])
        
        # Credit card
        if num_products > 1:
            card = products_df[
                (products_df['category'] == 'Credit Cards') & 
                (products_df['subcategory'].isin(['Basic', 'Premium']))
            ].sample(1)
            preferred_products.append(card.iloc[0])
        
        # Investment or savings
        if num_products > 2:
            invest = products_df[
                ((products_df['category'] == 'Investments') & (products_df['product_name'].str.contains('Robo'))) |
                ((products_df['category'] == 'Accounts') & (products_df['subcategory'] == 'Savings'))
            ].sample(1)
            preferred_products.append(invest.iloc[0])
        
        return preferred_products[:num_products]
    
    def _print_summary(self, df, customers_df):
        """Print summary statistics"""
        print("\n" + "="*70)
        print("📊 TRANSACTION SUMMARY")
        print("="*70)
        
        print(f"\n💳 Transaction Type Distribution:")
        type_counts = df['transaction_type'].value_counts()
        for trans_type, count in type_counts.items():
            print(f"   {trans_type:30s}: {count:5d}")
        
        print(f"\n📱 Channel Distribution:")
        channel_counts = df['channel'].value_counts()
        for channel, count in channel_counts.items():
            pct = (count / len(df)) * 100
            print(f"   {channel:15s}: {count:5d} ({pct:5.1f}%)")
        
        print(f"\n💰 Financial Metrics:")
        print(f"   Total Transaction Volume: ${df['amount'].sum():,.0f}")
        print(f"   Avg Transaction Size: ${df['amount'].mean():,.0f}")
        print(f"   Avg Products per Customer: {len(df) / len(customers_df):.1f}")
        
        print("\n" + "="*70)


if __name__ == "__main__":
    generator = BankingTransactionsGenerator()
    transactions_df = generator.generate_transactions()
    print("\n✅ Banking transactions generation complete!")

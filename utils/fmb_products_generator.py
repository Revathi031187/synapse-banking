"""
F&M Bank Product Catalog Generator
Farmers & Merchants Bank of Central California - Actual Product Lineup
"""

import pandas as pd
from pathlib import Path


class FMBProductsGenerator:
    """Generate F&M Bank's actual product catalog"""
    
    def __init__(self):
        self.output_dir = Path("data/preloaded/fmb_bank")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_products(self):
        """Generate F&M Bank's 28 products across Personal, Business, and Agricultural"""
        print("="*70)
        print("🏦 F&M BANK PRODUCT CATALOG GENERATOR")
        print("="*70)
        
        products = []
        
        # ===== PERSONAL BANKING PRODUCTS (14) =====
        
        # Personal Checking Accounts (5)
        products.extend([
            {
                'product_id': 'FMB_P001',
                'product_name': 'Worry-FREE Checking®',
                'category': 'Personal',
                'subcategory': 'Checking',
                'description': 'Banking is best when it\'s simple — and free',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 0.0,
                'target_segment': ['Mass_Market', 'Digital_Native', 'Young_Professional'],
                'features': 'No monthly fees, Online banking, Debit card, Mobile app',
                'eligibility_min_income': 0,
                'eligibility_min_credit_score': 0,
                'cross_sell_priority': 1
            },
            {
                'product_id': 'FMB_P002',
                'product_name': 'Ultimate Checking',
                'category': 'Personal',
                'subcategory': 'Checking',
                'description': 'Premium checking with enhanced benefits',
                'annual_fee': 0,
                'min_balance': 2500,
                'interest_rate': 0.0,
                'target_segment': ['Young_Professional', 'High_Net_Worth'],
                'features': 'No monthly fees with min balance, Premium debit card, Free checks',
                'eligibility_min_income': 40000,
                'eligibility_min_credit_score': 650,
                'cross_sell_priority': 2
            },
            {
                'product_id': 'FMB_P003',
                'product_name': 'Ultimate High Yield Checking®',
                'category': 'Personal',
                'subcategory': 'Checking',
                'description': 'Earn interest while you bank',
                'annual_fee': 0,
                'min_balance': 5000,
                'interest_rate': 1.25,
                'target_segment': ['High_Net_Worth', 'Retiree'],
                'features': 'High interest rates, Premium benefits, ATM fee rebates',
                'eligibility_min_income': 75000,
                'eligibility_min_credit_score': 700,
                'cross_sell_priority': 3
            },
            {
                'product_id': 'FMB_P004',
                'product_name': 'Sky Blue Checking™',
                'category': 'Personal',
                'subcategory': 'Checking',
                'description': 'Digital-first banking for modern lifestyles',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 0.0,
                'target_segment': ['Digital_Native', 'Young_Professional'],
                'features': 'Mobile-first, Digital statements, Instant notifications, Zero fees',
                'eligibility_min_income': 0,
                'eligibility_min_credit_score': 600,
                'cross_sell_priority': 2
            },
            {
                'product_id': 'FMB_P005',
                'product_name': 'Teen Checking',
                'category': 'Personal',
                'subcategory': 'Checking',
                'description': 'Banking basics for teens with parental oversight',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 0.0,
                'target_segment': ['Digital_Native'],
                'features': 'Parent controls, Financial education, Debit card, Mobile app',
                'eligibility_min_income': 0,
                'eligibility_min_credit_score': 0,
                'cross_sell_priority': 1
            }
        ])
        
        # Personal Savings & Investment (6)
        products.extend([
            {
                'product_id': 'FMB_P006',
                'product_name': 'Regular Savings',
                'category': 'Personal',
                'subcategory': 'Savings',
                'description': 'Build your savings with competitive rates',
                'annual_fee': 0,
                'min_balance': 100,
                'interest_rate': 0.50,
                'target_segment': ['Mass_Market', 'Young_Professional', 'Digital_Native'],
                'features': 'Earn interest, Easy access, FDIC insured',
                'eligibility_min_income': 0,
                'eligibility_min_credit_score': 0,
                'cross_sell_priority': 1
            },
            {
                'product_id': 'FMB_P007',
                'product_name': 'Money Market Account',
                'category': 'Personal',
                'subcategory': 'Savings',
                'description': 'Higher yields for larger balances',
                'annual_fee': 0,
                'min_balance': 10000,
                'interest_rate': 1.75,
                'target_segment': ['High_Net_Worth', 'Retiree'],
                'features': 'Tiered interest rates, Check writing, Limited transactions',
                'eligibility_min_income': 50000,
                'eligibility_min_credit_score': 650,
                'cross_sell_priority': 3
            },
            {
                'product_id': 'FMB_P008',
                'product_name': 'Certificates of Deposit (CDs)',
                'category': 'Personal',
                'subcategory': 'Investment',
                'description': 'Fixed-rate savings with guaranteed returns',
                'annual_fee': 0,
                'min_balance': 1000,
                'interest_rate': 2.50,
                'target_segment': ['Retiree', 'High_Net_Worth', 'Mass_Market'],
                'features': 'Fixed rates, Multiple terms (3mo-5yr), FDIC insured',
                'eligibility_min_income': 0,
                'eligibility_min_credit_score': 0,
                'cross_sell_priority': 2
            },
            {
                'product_id': 'FMB_P009',
                'product_name': 'Individual Retirement Accounts (IRAs)',
                'category': 'Personal',
                'subcategory': 'Investment',
                'description': 'Tax-advantaged retirement savings',
                'annual_fee': 0,
                'min_balance': 500,
                'interest_rate': 2.00,
                'target_segment': ['Young_Professional', 'High_Net_Worth', 'Retiree'],
                'features': 'Traditional & Roth options, Tax benefits, Retirement planning',
                'eligibility_min_income': 20000,
                'eligibility_min_credit_score': 0,
                'cross_sell_priority': 3
            },
            {
                'product_id': 'FMB_P010',
                'product_name': 'Holiday Club',
                'category': 'Personal',
                'subcategory': 'Savings',
                'description': 'Save throughout the year for holiday spending',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 0.25,
                'target_segment': ['Mass_Market', 'Young_Professional'],
                'features': 'Automatic savings, Holiday payout, No fees',
                'eligibility_min_income': 0,
                'eligibility_min_credit_score': 0,
                'cross_sell_priority': 1
            },
            {
                'product_id': 'FMB_P011',
                'product_name': 'Junior Savers',
                'category': 'Personal',
                'subcategory': 'Savings',
                'description': 'Teach kids the value of saving',
                'annual_fee': 0,
                'min_balance': 10,
                'interest_rate': 0.50,
                'target_segment': ['Mass_Market'],
                'features': 'Financial education, Parent oversight, Earn interest',
                'eligibility_min_income': 0,
                'eligibility_min_credit_score': 0,
                'cross_sell_priority': 1
            }
        ])
        
        # Personal Credit & Loans (3)
        products.extend([
            {
                'product_id': 'FMB_P012',
                'product_name': 'Personal Credit Cards',
                'category': 'Personal',
                'subcategory': 'Credit',
                'description': 'Rewards and cashback on everyday purchases',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 14.99,
                'target_segment': ['Young_Professional', 'Mass_Market', 'High_Net_Worth'],
                'features': 'Rewards points, Cashback options, Fraud protection, Mobile payments',
                'eligibility_min_income': 25000,
                'eligibility_min_credit_score': 650,
                'cross_sell_priority': 2
            },
            {
                'product_id': 'FMB_P013',
                'product_name': 'Home Mortgage Loans',
                'category': 'Personal',
                'subcategory': 'Loan',
                'description': 'Finance your home with competitive rates',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 6.50,
                'target_segment': ['Young_Professional', 'High_Net_Worth', 'Mass_Market'],
                'features': 'Fixed & adjustable rates, Local lending decisions, Flexible terms',
                'eligibility_min_income': 50000,
                'eligibility_min_credit_score': 680,
                'cross_sell_priority': 4
            },
            {
                'product_id': 'FMB_P014',
                'product_name': 'Auto Loans',
                'category': 'Personal',
                'subcategory': 'Loan',
                'description': 'New and used vehicle financing',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 5.75,
                'target_segment': ['Young_Professional', 'Mass_Market', 'Digital_Native'],
                'features': 'Quick approval, Competitive rates, New & used vehicles',
                'eligibility_min_income': 30000,
                'eligibility_min_credit_score': 640,
                'cross_sell_priority': 2
            }
        ])
        
        # ===== BUSINESS BANKING PRODUCTS (9) =====
        
        # Business Checking (3)
        products.extend([
            {
                'product_id': 'FMB_B001',
                'product_name': 'FREE Business Checking',
                'category': 'Business',
                'subcategory': 'Checking',
                'description': 'Keep the cost of doing banking low',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 0.0,
                'target_segment': ['Small_Business'],
                'features': 'No monthly fees, 200 free transactions, Online banking',
                'eligibility_min_income': 0,
                'eligibility_min_credit_score': 0,
                'cross_sell_priority': 1
            },
            {
                'product_id': 'FMB_B002',
                'product_name': 'Ultimate Business Checking',
                'category': 'Business',
                'subcategory': 'Checking',
                'description': 'Enhanced features for growing businesses',
                'annual_fee': 0,
                'min_balance': 5000,
                'interest_rate': 0.0,
                'target_segment': ['Small_Business', 'Corporate'],
                'features': 'Unlimited transactions, Remote deposit capture, Business debit cards',
                'eligibility_min_income': 100000,
                'eligibility_min_credit_score': 650,
                'cross_sell_priority': 2
            },
            {
                'product_id': 'FMB_B003',
                'product_name': 'Business Account Analysis Checking',
                'category': 'Business',
                'subcategory': 'Checking',
                'description': 'Comprehensive account management for large businesses',
                'annual_fee': 0,
                'min_balance': 25000,
                'interest_rate': 0.0,
                'target_segment': ['Corporate'],
                'features': 'Earnings credit, Custom reporting, Treasury management',
                'eligibility_min_income': 500000,
                'eligibility_min_credit_score': 700,
                'cross_sell_priority': 3
            }
        ])
        
        # Business Savings & Services (3)
        products.extend([
            {
                'product_id': 'FMB_B004',
                'product_name': 'Business Savings',
                'category': 'Business',
                'subcategory': 'Savings',
                'description': 'Earn interest on business reserves',
                'annual_fee': 0,
                'min_balance': 500,
                'interest_rate': 0.75,
                'target_segment': ['Small_Business', 'Corporate'],
                'features': 'Competitive rates, Easy transfers, FDIC insured',
                'eligibility_min_income': 0,
                'eligibility_min_credit_score': 0,
                'cross_sell_priority': 1
            },
            {
                'product_id': 'FMB_B005',
                'product_name': 'Business Money Market Account',
                'category': 'Business',
                'subcategory': 'Savings',
                'description': 'Higher yields for business cash management',
                'annual_fee': 0,
                'min_balance': 10000,
                'interest_rate': 1.50,
                'target_segment': ['Small_Business', 'Corporate', 'Commercial_Real_Estate'],
                'features': 'Tiered rates, Check writing, Sweep accounts',
                'eligibility_min_income': 150000,
                'eligibility_min_credit_score': 650,
                'cross_sell_priority': 2
            },
            {
                'product_id': 'FMB_B006',
                'product_name': 'Business Credit Cards',
                'category': 'Business',
                'subcategory': 'Credit',
                'description': 'Expense management and rewards for businesses',
                'annual_fee': 95,
                'min_balance': 0,
                'interest_rate': 15.99,
                'target_segment': ['Small_Business', 'Corporate'],
                'features': 'Business rewards, Expense tracking, Employee cards, Fraud protection',
                'eligibility_min_income': 75000,
                'eligibility_min_credit_score': 680,
                'cross_sell_priority': 2
            }
        ])
        
        # Business Loans (3)
        products.extend([
            {
                'product_id': 'FMB_B007',
                'product_name': 'Commercial Real Estate Loans',
                'category': 'Business',
                'subcategory': 'Loan',
                'description': 'Finance commercial property purchases',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 7.25,
                'target_segment': ['Commercial_Real_Estate', 'Corporate'],
                'features': 'Local decisions, Flexible terms, Competitive rates',
                'eligibility_min_income': 250000,
                'eligibility_min_credit_score': 700,
                'cross_sell_priority': 4
            },
            {
                'product_id': 'FMB_B008',
                'product_name': 'Business Term Loans',
                'category': 'Business',
                'subcategory': 'Loan',
                'description': 'Expand your business with term financing',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 6.75,
                'target_segment': ['Small_Business', 'Corporate'],
                'features': 'Fixed & variable rates, Quick approval, Local expertise',
                'eligibility_min_income': 100000,
                'eligibility_min_credit_score': 680,
                'cross_sell_priority': 3
            },
            {
                'product_id': 'FMB_B009',
                'product_name': 'Small Business Administration (SBA) Loans',
                'category': 'Business',
                'subcategory': 'Loan',
                'description': 'Government-backed financing for small businesses',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 8.00,
                'target_segment': ['Small_Business'],
                'features': 'Lower down payments, Longer terms, Preferred lender status',
                'eligibility_min_income': 50000,
                'eligibility_min_credit_score': 650,
                'cross_sell_priority': 3
            }
        ])
        
        # ===== AGRICULTURAL BANKING PRODUCTS (5) =====
        
        products.extend([
            {
                'product_id': 'FMB_A001',
                'product_name': 'Agricultural Loans',
                'category': 'Agricultural',
                'subcategory': 'Loan',
                'description': 'Operating loans for farming operations',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 6.50,
                'target_segment': ['Row_Crop_Farmer', 'Livestock_Rancher'],
                'features': 'Seasonal terms, Ag expertise, Flexible repayment',
                'eligibility_min_income': 75000,
                'eligibility_min_credit_score': 650,
                'cross_sell_priority': 1
            },
            {
                'product_id': 'FMB_A002',
                'product_name': 'Agricultural Real Estate Loans',
                'category': 'Agricultural',
                'subcategory': 'Loan',
                'description': 'Finance the land you need at a rate you can afford',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 6.75,
                'target_segment': ['Row_Crop_Farmer', 'Vineyard_Orchard_Owner', 'Livestock_Rancher'],
                'features': 'Long-term financing, Competitive rates, Farm & ranch expertise',
                'eligibility_min_income': 100000,
                'eligibility_min_credit_score': 680,
                'cross_sell_priority': 4
            },
            {
                'product_id': 'FMB_A003',
                'product_name': 'Livestock Loans',
                'category': 'Agricultural',
                'subcategory': 'Loan',
                'description': 'Finance cattle, dairy, and livestock operations',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 6.25,
                'target_segment': ['Livestock_Rancher'],
                'features': 'Seasonal flexibility, Livestock expertise, Custom terms',
                'eligibility_min_income': 80000,
                'eligibility_min_credit_score': 650,
                'cross_sell_priority': 2
            },
            {
                'product_id': 'FMB_A004',
                'product_name': 'Farm Equipment Loans & Leasing',
                'category': 'Agricultural',
                'subcategory': 'Loan',
                'description': 'Finance tractors, harvesters, and farm equipment',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 5.50,
                'target_segment': ['Row_Crop_Farmer', 'Vineyard_Orchard_Owner', 'Livestock_Rancher'],
                'features': 'Lease or purchase, Competitive rates, Quick approval',
                'eligibility_min_income': 60000,
                'eligibility_min_credit_score': 640,
                'cross_sell_priority': 2
            },
            {
                'product_id': 'FMB_A005',
                'product_name': 'Vineyard & Orchard Development Loans',
                'category': 'Agricultural',
                'subcategory': 'Loan',
                'description': 'Specialized financing for wine and fruit growers',
                'annual_fee': 0,
                'min_balance': 0,
                'interest_rate': 6.50,
                'target_segment': ['Vineyard_Orchard_Owner'],
                'features': 'Development financing, Multi-year terms, Wine country expertise',
                'eligibility_min_income': 90000,
                'eligibility_min_credit_score': 670,
                'cross_sell_priority': 3
            }
        ])
        
        # Create DataFrame
        df = pd.DataFrame(products)
        
        # Save to CSV
        output_path = self.output_dir / "products.csv"
        df.to_csv(output_path, index=False)
        
        print(f"\n✅ Generated {len(df)} F&M Bank products")
        print(f"   Saved to: {output_path}")
        
        # Summary
        self._print_summary(df)
        
        return df
    
    def _print_summary(self, df):
        """Print product catalog summary"""
        print("\n📊 F&M BANK PRODUCT SUMMARY:")
        print(f"   Total Products: {len(df)}")
        print("\nBy Category:")
        for category in df['category'].unique():
            count = len(df[df['category'] == category])
            print(f"   • {category}: {count} products")
            
            # Subcategories
            category_df = df[df['category'] == category]
            for subcat in category_df['subcategory'].unique():
                subcount = len(category_df[category_df['subcategory'] == subcat])
                print(f"     - {subcat}: {subcount}")
        
        print("\n💡 Featured Products:")
        featured = [
            'Worry-FREE Checking®',
            'Ultimate High Yield Checking®',
            'FREE Business Checking',
            'Agricultural Real Estate Loans',
            'SBA Loans'
        ]
        for prod_name in featured:
            if prod_name in df['product_name'].values:
                print(f"   ✓ {prod_name}")


if __name__ == "__main__":
    generator = FMBProductsGenerator()
    products_df = generator.generate_products()
    print("\n" + "="*70)
    print("✅ F&M Bank product catalog generation complete!")
    print("="*70)

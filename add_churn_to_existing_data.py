"""
Add Churn Features to Existing FMB Data
Run this script to add comprehensive churn analysis to your existing customer data
"""
import pandas as pd
from pathlib import Path
from utils.churn_feature_generator import add_essential_churn_features, generate_churn_report

print("=" * 80)
print("🔄 ADDING CHURN ANALYSIS TO FMB BANK DATA")
print("=" * 80)

# Load existing data
data_path = Path('data/preloaded/fmb_bank')
print(f"\n📂 Loading data from: {data_path}")

customers_df = pd.read_csv(data_path / 'customers.csv')
transactions_df = pd.read_csv(data_path / 'transactions.csv')

print(f"   ✓ Loaded {len(customers_df):,} customers")
print(f"   ✓ Loaded {len(transactions_df):,} transactions")

# Add churn features (ESSENTIAL ONLY - from real data)
print(f"\n🎯 Adding ESSENTIAL churn analysis features (from real transaction data)...")
customers_with_churn = add_essential_churn_features(customers_df, transactions_df)

# Generate report
print(f"\n📊 Generating churn report...")
churn_report = generate_churn_report(customers_with_churn)

# Save enhanced data
customers_with_churn.to_csv(data_path / 'customers.csv', index=False)
print(f"\n💾 Saved enhanced customer data with churn features")

# Display report
print(f"\n" + "=" * 80)
print("📈 CHURN ANALYSIS REPORT")
print("=" * 80)
print(f"\n✅ Total Customers: {churn_report['total_customers']:,}")
print(f"⚠️  At-Risk Customers: {churn_report['at_risk_customers']:,} ({churn_report['at_risk_customers']/churn_report['total_customers']*100:.1f}%)")
print(f"❌ Churned Customers: {churn_report['churned_customers']:,} ({churn_report['churned_customers']/churn_report['total_customers']*100:.1f}%)")
print(f"📊 Avg Churn Risk Score: {churn_report['avg_churn_risk_score']:.1f}/100")

print(f"\n🎯 Churn Risk Distribution:")
for category, count in sorted(churn_report['churn_by_category'].items()):
    pct = count / churn_report['total_customers'] * 100
    print(f"   {category:>10}: {count:>5,} customers ({pct:>5.1f}%)")

print(f"\n🛡️  Retention Actions Needed:")
for action, count in sorted(churn_report['retention_actions_needed'].items(), key=lambda x: x[1], reverse=True):
    pct = count / churn_report['total_customers'] * 100
    print(f"   {action:<30}: {count:>5,} customers ({pct:>5.1f}%)")

print(f"\n⚡ Top Churn Indicators:")
for indicator, count in churn_report['top_churn_indicators'].items():
    print(f"   {indicator:<25}: {count:>5,} customers")

# Show high-risk customers sample
print(f"\n🚨 Sample High-Risk Customers (Top 10):")
high_risk = customers_with_churn[customers_with_churn['churn_risk_category'] == 'Critical'].head(10)

if len(high_risk) > 0:
    print(f"\n{'Customer':<12} {'Risk':<6} {'Action':<25} {'Offer':<20}")
    print("-" * 80)
    for _, customer in high_risk.iterrows():
        print(f"{customer['customer_id']:<12} {customer['churn_risk_score']:>5.0f} {customer['recommended_retention_action']:<25} {customer['suggested_retention_offer']:<20}")
else:
    print("   No critical risk customers found (good news!)")

print(f"\n" + "=" * 80)
print("✅ CHURN ANALYSIS COMPLETE!")
print("=" * 80)
print(f"\n📋 New columns added to customers.csv:")
print("   • churn_risk_score (0-100)")
print("   • churn_risk_category (Low/Medium/High/Critical)")
print("   • churn_probability (0-1)")
print("   • churned (0/1)")
print("   • days_since_last_transaction")
print("   • txn_frequency_trend")
print("   • nps_score, csat_score")
print("   • competitor_offer_received")
print("   • recommended_retention_action")
print("   • suggested_retention_offer")
print("   • and 20+ more churn indicators...")
print(f"\n🚀 Ready to use for churn prediction models!")
print("=" * 80)

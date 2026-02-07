# Banking Platform - Implementation Guide

## Overview

This guide documents the complete transformation from Academy Sports camping gear demo to Banking & Financial Services personalization platform.

## Architecture

### Data Layer

**Customer Data** (`data/preloaded/banking/customers.csv`)
- 5,000 synthetic banking customers
- Demographics: age, income, credit_score, geographic_region
- Behavioral: digital_engagement_score, branch_visit_frequency, cross_sell_receptivity
- Financial: total_deposits, loan_balance, monthly_transactions, credit_utilization
- Personas: High Net Worth, Young Professionals, Small Business, Mass Market, Digital Natives

**Product Catalog** (`data/preloaded/banking/products.csv`)
- 60+ banking products across 6 categories
- Credit Cards (15): Basic, Premium, Platinum, Business, Specialty
- Personal Loans (10): Unsecured, debt consolidation, home improvement
- Accounts (12): Checking, Savings, CDs, Money Market
- Mortgages (8): Fixed, ARM, FHA, VA, HELOC, Refinance
- Investments (10): Brokerage, Robo-advisor, IRAs, Wealth management
- Business Banking (5): Business checking, business credit cards, SBA loans

**Transaction History** (`data/preloaded/banking/transactions.csv`)
- Product adoptions (not monetary transactions)
- Transaction types: account_opened, loan_approved, credit_card_activated
- Channels: Branch, Web, Mobile, Call Center

### Agent Layer

#### Agent A: Customer Segmentation (`agents/agent_a_banking_enhanced.py`)

**Clustering Algorithm:** K-Prototypes (mixed numeric/categorical data)

**Key Features:**
- Numeric: digital_engagement, cross_sell_receptivity, deposits, income, credit_score
- Categorical: risk_tolerance, channel_preference, life_stage, geographic_region
- Composite: customer_value_score, digital_adoption, financial_health

**Business Constraints:**
- Minimum segment size: 10% of customers (500+)
- Minimum deposits per customer: $5,000
- Validates segments meet marketing campaign thresholds

**Persona Generation:**
- AI-generated persona names based on cluster characteristics
- Segment descriptions with key differentiators
- Revenue metrics per segment
- Special flags: high_value, digital_first, multi_product, cross_sell_ready

#### Agent B: Product Recommendations (`agents/agent_b_banking_enhanced.py`)

**12-Factor Scoring System** (Adapted for Banking):

1. **Financial Need Match (35%)** - Product category matches customer profile
2. **Eligibility Match (20%)** - Credit score, income requirements met
3. **Relationship Depth (15%)** - Multi-product customers get premium products
4. **Complexity Match (15%)** - Product sophistication matches customer capability
5. **Income Tier Match (10%)** - Product tier aligns with income level
6. **Cross-Sell Affinity (5%)** - Products that pair well together

**Recommendation Types:**
- Similar Products: Based on customer's existing products and profile
- Segment Recommendations: Popular products among similar customers
- All Recommendations: Combined view with customer info

### API Layer

**Core Endpoints:**

```
/api/banking/datasets              GET   - List banking datasets
/api/banking/datasets/load         POST  - Load dataset
/api/banking/status                GET   - System status
/api/banking/agent_a/execute       POST  - Run customer segmentation
/api/banking/agent_a/results       GET   - Get segmentation results
/api/banking/macro-segments        GET   - Get customer segments
/api/banking/agent_a/customers     GET   - List customers (paginated)
/api/banking/agent_a/customer/:id  GET   - Customer details
/api/banking/recommendations/:id/all GET - All recommendations
/api/banking/products              GET   - List all products
```

**Request/Response Examples:**

```json
// POST /api/banking/agent_a/execute
{
  "n_clusters": 5,
  "gamma": 0.5
}

// Response
{
  "success": true,
  "result": {
    "n_clusters": 5,
    "personas": {
      "0": {
        "persona_name": "High Net Worth Investors",
        "short_name": "HNW",
        "size": 750,
        "percentage": 15.0,
        "characteristics": {
          "avg_deposits": 500000,
          "avg_credit_score": 780,
          "avg_products": 6
        }
      }
    }
  }
}
```

### Frontend Layer

**Routes:**
- `/banking` - Dashboard (primary landing)
- `/banking/agent-a` - Customer segmentation UI
- `/banking/agent-b` - Product recommendations UI
- `/banking/customer/:id/recommendations` - Customer detail view

**Components:**
- `BankingDashboard.tsx` - Main dashboard with status cards
- `BankingAgentA.tsx` - Segmentation interface
- `BankingAgentB.tsx` - Recommendation interface

**Styling:**
- Banking theme: Blue (#1e3a8a) and Gold (#fbbf24)
- Tailwind utility classes
- Banking-specific CSS classes (.banking-gradient, .banking-primary, etc.)

## Data Generation

### Customer Generator (`utils/banking_data_generator.py`)

**Persona Distribution:**
- High Net Worth: 15%
- Young Professionals: 25%
- Small Business: 10%
- Mass Market: 35%
- Digital Natives: 15%

**Feature Generation Logic:**

```python
# High Net Worth
income: $150K-$500K
credit_score: 740-850
total_deposits: $250K-$2M
num_products: 5-8
digital_engagement: 0.5-0.8
risk_tolerance: Moderate/Aggressive

# Young Professional
income: $50K-$100K
credit_score: 680-780
total_deposits: $5K-$50K
num_products: 2-4
digital_engagement: 0.8-1.0
risk_tolerance: Moderate/Aggressive

# Mass Market
income: $30K-$60K
credit_score: 620-720
total_deposits: $1K-$25K
num_products: 1-2
digital_engagement: 0.3-0.7
risk_tolerance: Conservative/Moderate
```

### Product Generator (`utils/banking_products_generator.py`)

**Product Attributes:**
- Credit Cards: annual_fee, APR, rewards_rate, sign_up_bonus, min_credit_score
- Loans: APR_range, term_months, max_amount, origination_fee
- Accounts: monthly_fee, min_balance, interest_rate, overdraft_fee
- Mortgages: APR, term_years, down_payment_pct, closing_costs
- Investments: management_fee, min_investment, risk_level, expected_return

### Transaction Generator (`utils/banking_transactions_generator.py`)

**Logic:**
- Assigns products based on customer persona
- HNW: 5-8 products (premium cards, investments, mortgages)
- Young Pro: 2-4 products (checking, credit card, savings)
- Business: 4-8 products (business checking, business card, loans)
- Mass Market: 1-2 products (basic checking, credit card)

**Transaction Channels:**
- Digital customers (digital_engagement > 0.7): Web/Mobile
- Branch customers (branch_visit > 0.5): Branch/Web
- Hybrid: Mix of all channels

## Databricks Alignment

### Use Cases (from Outcome Map)

1. **Prospecting Campaigns**
   - Target high-value segments (HNW, Small Business)
   - Personalized messaging per segment
   - Predicted response rates

2. **Hyper Personalized Banking**
   - Customer-specific product recommendations
   - Real-time eligibility checking
   - Contextual offers

3. **Cross-Sell & Up-Sell**
   - Product bundle recommendations
   - Multi-product discount optimization
   - Relationship depth scoring

4. **Churn Prediction & Segmentation**
   - Identify at-risk segments
   - Proactive retention offers
   - Product switching detection

### Impact Metrics (from Presentation)

- **$40-65M uplift** through higher sales with personalization (10-20% improvement in customer acquisition rate)
- **$50M+ revenue lift** through higher cross-sell rates (20-30% improvement)

### Technical Stack (from Presentation)

- **Unity Catalog**: Governance for sensitive financial data (credit scores, account balances)
- **Lakeflow + MLFlow**: ML model versioning for credit scoring, fraud detection
- **Collaboration**: Secure data sharing across teams (Marketing, Risk, Compliance)

### Personas (from Presentation)

- **Head of Consumer Banking**: P&L owner, revenue growth focus
- **Head of Marketing Strategy**: Campaign ROI, customer lifetime value
- **Head of Customer Experience**: NPS, digital adoption, product usage

## Customization Guide

### Adding New Personas

Edit `agents/agent_a_banking_enhanced.py`:

```python
def _generate_personas(self, numeric_cols, categorical_cols):
    # Add custom persona logic
    if avg_deposits > 1000000 and avg_age > 55:
        persona_name = "Pre-Retirees"
        short_name = "PreRetire"
```

### Adding New Products

Edit `utils/banking_products_generator.py`:

```python
def _generate_crypto_products(self, start_id):
    crypto_products = [
        {
            'product_id': f"PROD_{start_id:05d}",
            'product_name': "Crypto Trading Account",
            'category': 'Investments',
            'subcategory': 'Cryptocurrency',
            # ... more attributes
        }
    ]
    return crypto_products
```

### Adjusting Recommendation Scoring

Edit `agents/agent_b_banking_enhanced.py`:

```python
def _score_product_for_customer(self, customer, product):
    score = 0.0
    
    # Adjust weights
    category_score = self._calculate_category_score(customer, product)
    score += category_score * 0.40  # Increase from 0.35
    
    # Add custom factor
    sustainability_score = self._calculate_sustainability_match(customer, product)
    score += sustainability_score * 0.05
    
    return score
```

## Testing

### Data Validation

```bash
python -c "
import pandas as pd
customers = pd.read_csv('data/preloaded/banking/customers.csv')
print(f'Customers: {len(customers)}')
print(f'Personas: {customers[\"true_persona\"].value_counts()}')
print(f'Avg deposits: ${customers[\"total_deposits\"].mean():,.0f}')
"
```

### API Testing

```bash
# Test status
curl http://localhost:8002/api/banking/status

# Test datasets
curl http://localhost:8002/api/banking/datasets

# Test Agent A
curl -X POST http://localhost:8002/api/banking/agent_a/execute \
  -H "Content-Type: application/json" \
  -d '{"n_clusters": 5, "gamma": 0.5}'
```

### Frontend Testing

1. Navigate to http://localhost:3000/banking
2. Verify dashboard loads with status cards
3. Click "Run Agent A" - should complete in 30-60s
4. Verify 5 personas displayed
5. Click on a customer - should show recommendations

## Performance

### Clustering Performance
- 5,000 customers: 30-60 seconds
- 10,000 customers: 60-120 seconds
- Scales linearly with customer count

### Recommendation Performance
- Per customer: <1 second
- Batch (100 customers): <10 seconds
- Cached after first generation

### Frontend Performance
- Dashboard load: <500ms
- Agent A execution: 30-60s (backend processing)
- Agent B recommendations: <2s per customer
- Segment visualization: <1s

## Deployment

See `BANKING_QUICK_START.md` for deployment instructions.

For production deployment, consider:
- Environment variables for API keys
- Database backend (replace CSV files)
- Caching layer (Redis)
- API rate limiting
- HTTPS/SSL certificates
- Monitoring and logging

## Maintenance

### Regular Updates

- Retrain clustering model monthly (as customer base grows)
- Update product catalog quarterly (new products, discontinued products)
- Refresh transaction data weekly (new adoptions)
- Review recommendation weights quarterly (A/B test results)

### Monitoring

- Track segment stability (churn between segments)
- Monitor recommendation acceptance rate
- Track cross-sell conversion rates
- Monitor API response times

## Troubleshooting

See `BANKING_QUICK_START.md` for common issues and solutions.

## References

- Original Academy Sports implementation: `agents/agent_a_academy_enhanced.py`
- Plan document: `.cursor/plans/academy_to_banking_transform_*.plan.md`
- Databricks outcome map: Provided presentation image

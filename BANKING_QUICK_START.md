# Banking Platform - Quick Start Guide

## Overview

Transform your Academy Sports NBA demo into a Banking & Financial Services personalization platform. This guide will get you up and running in minutes.

## Prerequisites

- Python 3.10+
- Node.js 18+
- All dependencies from `requirements.txt` installed
- Frontend dependencies installed (`cd frontend && npm install`)

## Quick Start (5 Minutes)

### Step 1: Generate Banking Data

Run the data generation script:

```bash
generate_banking_data.bat
```

This creates:
- **5,000 banking customers** with financial profiles
- **60 banking products** (credit cards, loans, accounts, investments, mortgages, business banking)
- **Transaction history** showing product adoptions

**Expected Output:**
```
✅ Generated 5000 customers
   - High Net Worth: 750 customers (15%)
   - Young Professionals: 1,250 customers (25%)
   - Small Business: 500 customers (10%)
   - Mass Market: 1,750 customers (35%)
   - Digital Natives: 750 customers (15%)

✅ Generated 60 products across 6 categories
✅ Generated ~15,000 transactions
```

### Step 2: Start Backend

```bash
uvicorn api.main_unified_chromadb:app --port 8002 --reload
```

**Verify:**
- API running at http://localhost:8002
- API docs at http://localhost:8002/docs
- Check `/api/banking/status` endpoint

### Step 3: Start Frontend

```bash
cd frontend
npm run dev
```

**Verify:**
- Frontend running at http://localhost:3000
- Redirects to `/banking` (now primary demo)

### Step 4: Run the Demo

1. **Navigate to Banking Dashboard**
   - http://localhost:3000/banking
   - Should see 5,000 customers loaded

2. **Run Agent A - Customer Segmentation**
   - Click "Run Agent A - Segmentation"
   - Wait 30-60 seconds for clustering
   - Should see 4-5 banking personas:
     - High Net Worth Investors
     - Young Professionals
     - Small Business Owners
     - Mass Market Savers
     - Digital Natives

3. **View Segments**
   - Explore customer segments
   - View segment characteristics (deposits, credit scores, digital engagement)
   - Click on customers to see detailed profiles

4. **Run Agent B - Product Recommendations**
   - Select a customer
   - View personalized product recommendations
   - See recommendation explanations

## Demo Flow for Databricks Meeting

### Talking Points

1. **Customer Segmentation** (Agent A)
   - "We identify 5 distinct banking customer personas using K-Prototypes clustering"
   - "Segments based on deposits, digital engagement, cross-sell receptivity, risk tolerance"
   - "Business constraints: minimum segment size, minimum deposits per customer"

2. **Product Recommendations** (Agent B)
   - "12-factor scoring system adapted for banking"
   - "Factors: financial need match, eligibility, relationship depth, complexity match"
   - "Personalized recommendations based on credit score, income, deposits, risk profile"

3. **Use Cases** (Reference Databricks outcome map)
   - Prospecting campaigns (target high-value segments)
   - Hyper personalization (customer-specific products)
   - Cross-sell & up-sell (multi-product recommendations)
   - Churn prediction (identify at-risk segments)

4. **Impact** (Reference presentation image)
   - $40-65M uplift through higher sales with personalization
   - $50M+ revenue lift through higher cross-sell rates (20-30% improvement)

### Sample Customer Profiles

**High Net Worth Example:**
- Deposits: $250K-$2M
- Products: 5-8 (checking, premium credit card, investments, mortgage)
- Recommendations: Wealth management, platinum cards, investment products

**Young Professional Example:**
- Age: 25-35, Deposits: $5K-$50K
- Products: 2-4 (basic checking, credit card, savings)
- Recommendations: Cashback cards, auto loans, starter investments

**Small Business Example:**
- Deposits: $50K-$500K, High transaction volume
- Products: 4-8 (business checking, business credit card, loans)
- Recommendations: Business credit line, merchant services, SBA loans

## Troubleshooting

### Data Not Generated

```bash
# Check if files exist
dir data\preloaded\banking\

# If missing, run generator manually
python utils/banking_data_generator.py
python utils/banking_products_generator.py
python utils/banking_transactions_generator.py
```

### Backend Errors

```bash
# Check if kmodes installed
pip install kmodes

# Check if all dependencies installed
pip install -r requirements.txt
```

### Frontend Not Loading

```bash
# Clear cache and rebuild
cd frontend
rm -rf node_modules dist
npm install
npm run dev
```

### Port Conflicts

```bash
# Kill process on port 8002
netstat -ano | findstr :8002
taskkill /PID <pid> /F

# Or use different port
uvicorn api.main_unified_chromadb:app --port 8003
```

## Key API Endpoints

- `GET /api/banking/datasets` - List available datasets
- `POST /api/banking/datasets/load` - Load banking dataset
- `POST /api/banking/agent_a/execute` - Run customer segmentation
- `GET /api/banking/macro-segments` - Get customer segments
- `GET /api/banking/agent_a/customers` - List customers (paginated)
- `GET /api/banking/recommendations/{customer_id}/all` - Get product recommendations

## Next Steps

- Customize persona names in `agents/agent_a_banking_enhanced.py`
- Add more banking products in `utils/banking_products_generator.py`
- Adjust recommendation scoring in `agents/agent_b_banking_enhanced.py`
- Create custom segments for specific use cases

## Demo Preparation Checklist

- [ ] Generate banking data (5,000 customers)
- [ ] Start backend (verify at http://localhost:8002/docs)
- [ ] Start frontend (verify at http://localhost:3000/banking)
- [ ] Run Agent A (verify 5 personas created)
- [ ] Test Agent B (verify recommendations working)
- [ ] Practice demo flow (5-10 minutes end-to-end)
- [ ] Review Databricks outcome map talking points

## Support

For issues or questions:
1. Check API docs: http://localhost:8002/docs
2. Check logs: Terminal output from uvicorn
3. Check browser console: F12 Developer Tools

## Academy Sports Demo

The Academy Sports camping gear demo is still available at:
- http://localhost:3000/academy

Both demos run on the same backend with isolated data.

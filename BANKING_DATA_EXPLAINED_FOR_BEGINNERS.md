# 🏦 Banking & Finance Data Explained for Beginners

## Complete Guide to Understanding Your Dataset

This guide explains all the data tables (customers, products, transactions) in simple terms for someone new to banking and finance.

---

## Part 1: Understanding the CUSTOMERS Table

### 📋 Complete Column List (46 Columns Total)

```
BASIC INFO (6 columns):
customer_id, customer_name, customer_segment, customer_type, age, income

FINANCIAL PROFILE (4 columns):
credit_score, total_deposits, num_products, monthly_transaction_volume

BEHAVIOR & ENGAGEMENT (3 columns):
digital_engagement_score, branch_visit_frequency, tenure_months, cross_sell_receptivity

TRANSACTION ACTIVITY (5 columns):
last_transaction_date, days_since_last_txn, recent_txn_count, previous_txn_count, 
txn_frequency_trend

FINANCIAL HEALTH (4 columns):
balance_trend, deposit_change_3mo_pct, low_balance_flag, products_closed_last_6mo

CUSTOMER SERVICE (3 columns):
complaints_last_year, support_contacts_last_3mo, digital_engagement_decline

COMPETITIVE THREATS (3 columns):
competitor_offer_received, fee_sensitivity_score, external_accounts_linked

LIFE EVENTS & RISK (4 columns):
recent_life_event, age_risk_factor, credit_score_declining, overdrafts_last_3mo

SATISFACTION SCORES (5 columns):
nps_score, nps_category, csat_score, branch_satisfaction, high_overdraft_flag

FINANCIAL STRESS (1 column):
debt_payment_missed

CHURN PREDICTION (6 columns):
churn_risk_score, churn_risk_category, churn_probability, churned, churn_date, 
recommended_retention_action, suggested_retention_offer
```

---

### 📊 Column-by-Column Breakdown

#### 🆔 Basic Customer Information

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **customer_id** | Unique ID for each customer | CUST_00001 | To identify each customer uniquely (like a social security number) |
| **customer_name** | Full name of customer | Allison Hill | Who the customer is |
| **customer_segment** | Type of customer category | Personal, Business, Agricultural | Different customers need different products (e.g., Farmers vs. Companies) |
| **customer_type** | Sub-category within segment | Mass_Market, High_Net_Worth | More specific grouping for targeted offers |
| **age** | Customer's age in years | 63 | Helps determine life-stage needs (Student vs. Retiree) |
| **income** | Yearly income in dollars | $45,795 | Determines product affordability and loan qualification |

---

#### 💰 Financial Profile

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **credit_score** | Credit worthiness (300-850) | 712 (Good) | Determines loan eligibility and interest rates |
| **total_deposits** | Total money in all accounts | $7,136.17 | Measures customer liquidity and wealth |
| **num_products** | Number of products customer has | 1, 2, or 3 | Indicates customer loyalty and "stickiness" |
| **monthly_transaction_volume** | Average transactions per month | 84 | Measures how active the customer is |

---

#### 📱 Behavior & Engagement

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **digital_engagement_score** | Use of online/mobile banking (0-1) | 0.54 (54%) | Shows preference for digital vs. in-person banking |
| **branch_visit_frequency** | Physical branch visits (0-1) | 0.46 (46%) | Indicates demand for face-to-face service |
| **tenure_months** | Duration of relationship | 127 months (10+ years) | Long-term customers are generally more valuable |
| **cross_sell_receptivity** | Likelihood to buy more products (0-1) | 0.58 (58%) | Identifies candidates for new product offers |

---

#### 📊 Transaction Activity Tracking

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **last_transaction_date** | Most recent transaction | 2024-11-28 | How recently customer used account |
| **days_since_last_txn** | Days since last activity | 15 days | Identifies inactive customers (churn risk) |
| **recent_txn_count** | Transactions in last 30 days | 12 | Current activity level |
| **previous_txn_count** | Transactions 30-60 days ago | 18 | Previous activity level for comparison |
| **txn_frequency_trend** | Change in activity | -6 (declining) | Whether customer is becoming less active |

---

#### 💳 Financial Health Indicators

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **balance_trend** | Account balance direction | Declining, Stable, Growing | Financial health trajectory |
| **deposit_change_3mo_pct** | % change in deposits (3 months) | -15% (decreasing) | Warning sign if dropping significantly |
| **low_balance_flag** | Balance below threshold | 1 (Yes) or 0 (No) | Risk of fees or account closure |
| **products_closed_last_6mo** | Products closed recently | 1 | Disengagement signal |

---

#### 📞 Customer Service & Support

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **complaints_last_year** | Number of complaints filed | 2 | Satisfaction issues |
| **support_contacts_last_3mo** | Customer service calls/chats | 5 | High contact = potential problems |
| **digital_engagement_decline** | Drop in online/mobile usage | 1 (Yes) or 0 (No) | Possible dissatisfaction with digital tools |

---

#### ⚠️ Competitive Threats

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **competitor_offer_received** | Got offer from another bank | 1 (Yes) or 0 (No) | At risk of switching banks |
| **fee_sensitivity_score** | How much fees bother them (0-1) | 0.8 (very sensitive) | Price-conscious customers |
| **external_accounts_linked** | Accounts at other banks linked | 2 | Using multiple banks (lower loyalty) |

---

#### 🎯 Life Events & Risk Factors

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **recent_life_event** | Major life change | Job Loss, Marriage, Relocation | Life changes affect banking needs |
| **age_risk_factor** | Age-related churn risk (0-1) | 0.3 | Young adults and very old are higher risk |
| **credit_score_declining** | Credit score dropping | 1 (Yes) or 0 (No) | Financial distress indicator |
| **overdrafts_last_3mo** | Number of overdrafts | 3 | Financial management issues |

---

#### 😊 Customer Satisfaction Scores

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **nps_score** | Net Promoter Score (-100 to 100) | 45 | Would they recommend us? |
| **nps_category** | NPS classification | Promoter, Passive, Detractor | Overall satisfaction level |
| **csat_score** | Customer Satisfaction (1-5) | 4.2 | Recent service experience rating |
| **branch_satisfaction** | Branch service rating (0-1) | 0.85 (85%) | In-person service quality |
| **high_overdraft_flag** | Frequent overdrafts | 1 (Yes) or 0 (No) | Financial stress / fee frustration |

---

#### 💔 Financial Stress

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **debt_payment_missed** | Missed loan/credit payment | 1 (Yes) or 0 (No) | Serious financial distress |

---

#### 🚨 Churn Prediction & Retention

| Column | What It Means | Example Value | Why We Track This |
|--------|---------------|---------------|-------------------|
| **churn_risk_score** | Likelihood to leave (0-100) | 73 | Calculated risk of leaving |
| **churn_risk_category** | Risk level | Low, Medium, High, Critical | Easy classification |
| **churn_probability** | Statistical probability (0-1) | 0.68 (68% chance) | Precise risk estimate |
| **churned** | Already left the bank | 1 (Yes) or 0 (No) | Actual churn status |
| **churn_date** | Date they left | 2024-12-15 | When churn occurred |
| **recommended_retention_action** | What to do | Urgent_Personal_Outreach | Action plan to save customer |
| **suggested_retention_offer** | What to offer | Min_Balance_Waiver | Specific incentive to keep them |

---

### 🎯 Customer Types Explained

#### Personal Segment (Individual Customers)

| Type | Description | Typical Age | Typical Income |
|------|-------------|-------------|----------------|
| **Mass_Market** | Regular everyday customers (most people) | 25-65 | $30K-$70K |
| **Digital_Native** | Younger people comfortable with apps/online | 18-35 | $25K-$60K |
| **Young_Professional** | Building careers, growing income | 25-40 | $50K-$100K |
| **High_Net_Worth** | Rich people with significant assets | 40-70 | $150K+ |
| **Retiree** | Retired people living on savings/pension | 65+ | $30K-$80K |

#### Business Segment (Company Accounts)

| Type | Description | Typical Products |
|------|-------------|------------------|
| **Small_Business** | Small companies, shops, restaurants | Business checking, merchant services |
| **Corporate** | Large companies with many employees | Corporate accounts, payroll, credit lines |

#### Agricultural Segment (Farming Operations)

| Type | Description | Special Needs |
|------|-------------|---------------|
| **Row_Crop_Farmer** | Growing corn, wheat, soybeans | Seasonal loans, equipment financing |
| **Livestock_Rancher** | Raising cattle, pigs, chickens | Operating loans, livestock insurance |
| **Vineyard_Orchard_Owner** | Growing grapes, apples, fruits | Long-term loans, weather insurance |

---

### 📊 Value Ranges in Your Dataset

| Metric | Minimum | Maximum | Average | What It Tells Us |
|--------|---------|---------|---------|------------------|
| **Age** | 27 years | 64 years | ~45 years | Mix of young professionals to pre-retirees |
| **Income** | $30,000/year | $67,000/year | ~$48,000/year | Middle-class customer base |
| **Credit Score** | 623 (Fair) | 749 (Very Good) | ~686 (Good) | Generally creditworthy customers |
| **Total Deposits** | $3,000 | $29,000 | ~$16,000 | Modest to moderate savings |
| **Products** | 1 product | 3 products | ~2 products | Room for cross-selling |
| **Digital Engagement** | 0% (never) | 100% (always) | ~50% | Half digital, half branch |
| **Tenure** | 12 months | 180 months | ~96 months (8 years) | Established relationships |
| **Churn Risk Score** | 0 (safe) | 100 (critical) | ~26 | Average customer is low risk |
| **At-Risk Customers** | - | - | ~594 (12%) | 1 in 8 customers at risk of leaving |

---

### 🚨 Understanding Churn & Retention

#### What is "Churn"?
**Churn** = When a customer leaves your bank and closes their accounts

**Why It Matters:**
- Costs 5-10x more to get new customers than keep existing ones
- Lost revenue from fees, interest, and products
- Negative word-of-mouth hurts reputation

#### How Churn Risk Score Works (0-100):

The system calculates risk by analyzing **real behavior patterns**:

**🟢 Low Risk (0-25)**: Safe customers
- Recent transactions (last 7-14 days)
- Growing or stable balances
- Multiple products
- High satisfaction scores

**🟡 Medium Risk (26-50)**: Watch closely
- Transactions slowing down
- No major issues yet
- May need attention soon

**🟠 High Risk (51-75)**: Intervention needed
- 30+ days since last transaction
- Balance declining
- Complaints or high support contacts
- Only 1 product

**🔴 Critical Risk (76-100)**: Urgent action required
- 60+ days inactive
- Very low balance
- Received competitor offer
- Multiple complaints

#### Retention Actions Explained:

| Action | When Used | What It Means |
|--------|-----------|---------------|
| **Urgent_Personal_Outreach** | Critical risk (75+) | Personal banker calls within 24 hours |
| **Proactive_Offer** | High risk (50-74) | Send special retention offer |
| **Monitor_Closely** | Medium risk (25-49) | Watch for warning signs |
| **Standard_Care** | Low risk (0-24) | Normal service level |

#### Retention Offers Explained:

| Offer | Purpose | Example |
|-------|---------|---------|
| **Min_Balance_Waiver** | Remove fee burden | Waive $2,500 minimum balance requirement for 6 months |
| **Digital_Incentive** | Encourage app usage | $50 bonus for completing 5 mobile transactions |
| **Product_Bundle_Offer** | Increase engagement | Free checking + savings package with bonus interest |
| **Reactivation_Campaign** | Win back inactive customers | "We miss you" offer with account credit |
| **Loyalty_Reward** | Reward good customers | Cash back on transactions or interest rate boost |

#### Real Example - Customer at Risk:

**Customer: John Smith (CUST_00234)**
- **Days since last txn**: 45 days (inactive!)
- **Balance trend**: Declining
- **Recent txn count**: 0 (vs. 12 previously)
- **Complaints**: 1 in last 6 months
- **External accounts**: 2 (using competitors)

**Calculated Churn Risk Score: 68** (High Risk)

**System Recommendation:**
- **Action**: Proactive_Offer
- **Offer**: Min_Balance_Waiver
- **Message**: "John, we value your 8-year relationship. We're waiving fees for 6 months and offering 2% bonus interest on savings."

---

## Part 2: Understanding the PRODUCTS Table

### 📋 Complete Column List

```
product_id, product_name, category, subcategory, annual_fee, 
min_balance, interest_rate, description, target_segment, customer_types
```

---

### 📊 Column-by-Column Breakdown

| Column | What It Means | Example | Why It Matters |
|--------|---------------|---------|----------------|
| **product_id** | Unique product code | FMB_P001 | Internal tracking code |
| **product_name** | Name of the product | Worry-FREE Checking® | What customers see |
| **category** | Main product type | Personal, Business, Agricultural | High-level grouping |
| **subcategory** | Specific product type | Checking, Savings, Loan | Exact product category |
| **annual_fee** | Yearly cost to maintain | $0 or $95 | Revenue from the account |
| **min_balance** | Minimum money needed | $2,500 | Prevents fees or required to open |
| **interest_rate** | % earned on deposits or paid on loans | 0.0% to 5.5% | Earnings (savings) or cost (loans) |
| **description** | What the product does | Basic checking with no fees | Customer-facing explanation |
| **target_segment** | Who it's designed for | Mass_Market, High_Net_Worth | Marketing target |
| **customer_types** | Specific customer types | ['Young_Professional', 'Retiree'] | Ideal customer profiles |

---

### 🏦 Product Categories Explained

#### Personal Banking Products

**Checking Accounts** (For daily transactions)
- Worry-FREE Checking: No fees, no minimum balance
- Ultimate Checking: $2,500 minimum, premium features
- Teen Checking: For young people under 18

**Savings Accounts** (For saving money)
- Regular Savings: 0.50% interest, grow your money
- Money Market: 1.75% interest, higher balance required
- Holiday Club: Save for holidays
- Junior Savers: For kids to learn saving

**Investment Products** (For growing wealth)
- Certificates of Deposit (CDs): 2.50% interest, lock money for 1-5 years
- Individual Retirement Accounts (IRAs): 2.00% interest, save for retirement

**Credit/Loans** (Borrowing money)
- Credit Cards: 15.99% APR, borrow up to credit limit
- Personal Loans: 8.50% APR, borrow lump sum
- Home Equity Line: 5.50% APR, borrow against home value

#### Business Banking Products

**Business Checking**
- Business Checking: For company daily transactions
- Merchant Services: Accept credit card payments

**Business Financing**
- Business Line of Credit: 6.75% APR, flexible borrowing
- Commercial Real Estate Loan: 5.25% APR, buy property
- Equipment Financing: 5.75% APR, buy machinery

**Business Savings**
- Business Savings: 0.75% interest, company emergency fund
- Business Money Market: 2.00% interest, earn more on reserves

#### Agricultural Banking Products

**Farm Operating Loans**
- Operating Line of Credit: 5.50% APR, seasonal farming costs
- Crop Production Loan: 4.75% APR, plant and harvest crops

**Farm Equipment/Land**
- Agricultural Equipment Loan: 5.25% APR, tractors, combines
- Farm Real Estate Loan: 4.50% APR, buy farmland

**Agricultural Savings**
- Farm Savings Account: 1.00% interest, save between harvests

---

### 💰 Understanding Banking Terms

#### Interest Rates
- **Deposit Products** (Savings, CDs): Bank PAYS you interest for keeping money with them
  - Example: 2.50% CD means you earn $250/year on $10,000
- **Loan Products** (Credit Cards, Mortgages): You PAY bank interest for borrowing
  - Example: 15.99% credit card means you pay $159.90/year on $1,000 borrowed

#### Account Features
- **Annual Fee**: Yearly cost to keep account open ($0 means free)
- **Minimum Balance**: Money you must keep in account to avoid fees
- **APR (Annual Percentage Rate)**: Yearly interest rate on loans
- **APY (Annual Percentage Yield)**: Yearly earnings rate on savings

---

## Part 3: Understanding the TRANSACTIONS Table

### 📋 Complete Column List

```
transaction_id, customer_id, transaction_date, transaction_type, amount, channel
```

---

### 📊 Column-by-Column Breakdown

| Column | What It Means | Example | Why We Track This |
|--------|---------------|---------|-------------------|
| **transaction_id** | Unique transaction code | TXN_000001 | Track each individual transaction |
| **customer_id** | Which customer made it | CUST_00001 | Link transaction to customer |
| **transaction_date** | When it happened | 2024-06-15 | Timing of activity |
| **transaction_type** | What kind of transaction | Deposit, Withdrawal, Transfer | Type of banking activity |
| **amount** | Dollar value | $150.00 | How much money moved |
| **channel** | How it was done | Mobile App, ATM, Branch | Customer's preferred method |

---

### 💳 Transaction Types Explained

| Type | What It Means | Example | Frequency |
|------|---------------|---------|-----------|
| **Deposit** | Adding money to account | Paycheck deposit, cash deposit | Very common |
| **Withdrawal** | Taking money out | ATM cash withdrawal, check written | Very common |
| **Transfer** | Moving money between accounts | Savings to checking transfer | Common |
| **Payment** | Paying bills or merchants | Credit card payment, utility bill | Very common |
| **Purchase** | Buying something with card | Debit card at store | Most common |
| **Fee** | Bank charges | Monthly fee, overdraft fee | Occasional |
| **Interest** | Bank paying/charging interest | Interest earned on savings | Monthly |

---

### 📱 Transaction Channels Explained

| Channel | What It Is | Used By | Speed |
|---------|------------|---------|-------|
| **Mobile App** | Banking on smartphone | Digital-savvy customers | Instant |
| **Online** | Website banking | Computer users | Instant |
| **ATM** | Automated Teller Machine | Everyone | Instant |
| **Branch** | Physical bank location | Branch-preferred customers | During hours |
| **Phone** | Call customer service | Less tech-savvy customers | Immediate |

---

### 📊 Transaction Statistics in Your Dataset

| Metric | Value | What It Means |
|--------|-------|---------------|
| **Total Transactions** | 78,568 | Very active customer base |
| **Average per Customer** | ~16 per month | Moderate usage |
| **Most Common Type** | Purchase/Payment | Everyday spending |
| **Most Common Channel** | Mobile App (if digital score > 0.5) | Digital adoption |
| **Date Range** | Past 12 months | Recent activity history |

---

## 🎯 How This Data Works Together

### Example Customer Journey:

**Meet Sarah (CUST_00123)**
- **Profile**: 35 years old, Young Professional
- **Income**: $65,000/year
- **Credit Score**: 720 (Good)
- **Deposits**: $15,000
- **Products**: 2 (Checking + Savings)
- **Digital Score**: 0.85 (85% - loves mobile app)

**Her Banking Activity (Transactions)**:
- **Deposit**: $2,500 salary (every 2 weeks)
- **Payments**: Rent $1,200, utilities $150, credit card $300
- **Purchases**: Groceries, gas, shopping (~$1,000/month)
- **Transfer**: $500 checking → savings (monthly)
- **Channel**: 90% mobile app, 10% ATM

**Cross-Sell Opportunity**:
- Her **cross_sell_receptivity** = 0.72 (72%)
- She's a good candidate for:
  - ✅ Credit Card (rewards for frequent purchases)
  - ✅ IRA (saving for retirement at young age)
  - ✅ Personal Loan (consolidate any debts)

---

## 💡 Key Insights for Segmentation

### Why We Segment Customers:

1. **Different Needs**: Farmers need crop loans, young professionals need mortgages
2. **Different Channels**: Digital natives use apps, retirees prefer branches
3. **Different Profitability**: High net worth customers generate more revenue
4. **Targeted Marketing**: Send relevant offers (don't offer crop loans to city dwellers)

### What Makes a Good Segment:

- **Size**: Enough customers to matter (>100 people)
- **Profitability**: High deposits, multiple products, low maintenance
- **Actionability**: Can design specific products/campaigns for them
- **Measurability**: Can track their behavior and results

---

## 🎯 Churn Features Quick Reference

### Core Churn Indicators (What to Watch):

| Feature | Warning Sign | Action Needed |
|---------|--------------|---------------|
| **days_since_last_txn** | > 30 days | Customer going inactive |
| **txn_frequency_trend** | Negative number | Activity declining |
| **low_balance_flag** | = 1 | Risk of fees causing frustration |
| **products_closed_last_6mo** | > 0 | Disengaging from bank |
| **digital_engagement_decline** | = 1 | App/online issues |
| **competitor_offer_received** | = 1 | About to switch banks |
| **complaints_last_year** | > 2 | Serious dissatisfaction |
| **overdrafts_last_3mo** | > 3 | Financial stress |
| **debt_payment_missed** | = 1 | Critical financial distress |
| **churn_risk_score** | > 50 | Take immediate action |

### How Features Connect to Churn:

```
Inactive Transactions → Low Engagement → Higher Churn Risk
Low Balance → Fee Frustration → Higher Churn Risk  
Competitor Offer → Temptation to Switch → Higher Churn Risk
Complaints → Dissatisfaction → Higher Churn Risk
Single Product → Low Commitment → Higher Churn Risk
```

### Business Impact of Churn Prediction:

**Without Churn Prediction:**
- Customers leave without warning
- No chance to save the relationship
- Lost revenue

**With Churn Prediction:**
- Identify at-risk customers early
- Proactive retention offers
- Save 30-50% of at-risk customers
- Increase customer lifetime value

---

## 📚 Banking & Finance Glossary

| Term | Simple Definition | Example |
|------|-------------------|---------|
| **APR** | Annual Percentage Rate - yearly interest on loans | 15.99% APR on credit card |
| **APY** | Annual Percentage Yield - yearly earnings on savings | 2.50% APY on CD |
| **CD** | Certificate of Deposit - lock money for higher interest | 3-year CD at 3.0% |
| **IRA** | Individual Retirement Account - tax-advantaged retirement savings | Traditional IRA or Roth IRA |
| **Checking** | Account for daily transactions (checks, debit cards) | Everyday spending account |
| **Savings** | Account for storing money and earning interest | Emergency fund account |
| **Credit Score** | 300-850 number showing creditworthiness | 720 = Good credit |
| **Deposit** | Money in your accounts (savings, checking) | $15,000 in total deposits |
| **Loan** | Money borrowed from bank (must pay back with interest) | $20,000 car loan |
| **Mortgage** | Loan to buy a house | 30-year mortgage |
| **Line of Credit** | Approved borrowing limit (use as needed) | $10,000 credit line |
| **Interest** | Fee for borrowing OR earnings for saving | 5% interest |
| **Principal** | Original amount borrowed or deposited | $10,000 principal |
| **Tenure** | How long you've been a customer | 96 months = 8 years |
| **Cross-sell** | Selling additional products to existing customers | Offer credit card to checking customer |
| **Net Worth** | Total assets minus total debts | $100,000 net worth |
| **Liquidity** | How easily you can access your money | Cash is most liquid |

---

## 🎓 Understanding the FMB Bank Context

### About FMB (Farmers & Merchants Bank)

Based on https://www.fmb.com/, this is a **community bank** serving:
- **Rural communities** (farmers, ranchers)
- **Small businesses** (local shops, restaurants)
- **Individual families** (personal banking)

### Their Focus:
- ✅ Strong agricultural lending (farm loans, equipment financing)
- ✅ Personal relationships (branch banking, personal bankers)
- ✅ Community involvement (local decision-making)
- ✅ Digital innovation (mobile app, online banking)

### Your Dataset Reflects:
- **5,000 customers** = Small to medium community bank size
- **78,568 transactions** = Active, engaged customer base
- **28 products** = Comprehensive offering (personal + business + agricultural)
- **3 segments** = Diverse customer mix (Personal, Business, Agricultural)

---

## 🚀 Ready to Use This Data

Now you understand:
- ✅ Every column in customers, products, and transactions
- ✅ What each value means in banking context
- ✅ How customers use different products
- ✅ How transactions show customer behavior
- ✅ Why we segment customers differently

**You're ready to:**
1. Run Agent A to identify customer segments
2. Understand the macro/micro personas
3. Interpret intent scores and recommendations
4. Make data-driven banking decisions!

---

*This guide was created for beginners. All data is from the FMB Bank dataset (5,000 customers, 78,568 transactions).*

-- ============================================================================
-- BANKING PERSONALIZATION PLATFORM - DATA SCHEMA
-- Purpose: Support Agent A (Persona Builder) and Agent B (Product Matchmaker)
-- ============================================================================

-- ============================================================================
-- TABLE 1: CUSTOMERS
-- Core customer demographic and profile data
-- ============================================================================
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INT,
    gender VARCHAR(10),
    income_band VARCHAR(50),  -- 'Low', 'Medium', 'High', 'Very High'
    employment_status VARCHAR(50),  -- 'Employed', 'Self-Employed', 'Unemployed', 'Retired'
    marital_status VARCHAR(20),  -- 'Single', 'Married', 'Divorced', 'Widowed'
    has_children BOOLEAN,
    num_children INT,
    household_size INT,
    education_level VARCHAR(50),  -- 'High School', 'Bachelor', 'Master', 'PhD'
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    customer_since DATE,  -- Tenure calculation
    tenure_months INT,  -- Pre-calculated for convenience
    customer_segment VARCHAR(50),  -- 'Mass Market', 'Affluent', 'Student', 'Senior'
    risk_score DECIMAL(5,2),  -- Credit risk (0-100, lower is better)
    lifetime_value DECIMAL(12,2),  -- Calculated CLV
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- ============================================================================
-- TABLE 2: ACCOUNTS
-- All account types held by customers
-- ============================================================================
CREATE TABLE accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    account_type VARCHAR(50),  -- 'Checking', 'Savings', 'Credit Card', 'Mortgage', 'Auto Loan', 'Personal Loan'
    account_status VARCHAR(20),  -- 'Active', 'Inactive', 'Closed', 'Suspended'
    account_opened_date DATE,
    current_balance DECIMAL(12,2),
    available_balance DECIMAL(12,2),  -- For credit products
    credit_limit DECIMAL(12,2),  -- For credit cards
    interest_rate DECIMAL(5,2),  -- APR for loans/cards
    minimum_balance DECIMAL(12,2),  -- For checking/savings
    monthly_fee DECIMAL(8,2),
    account_age_months INT,
    last_transaction_date DATE,
    transaction_count_30d INT,
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================================================
-- TABLE 3: TRANSACTIONS
-- All debit and credit transactions with merchant category
-- ============================================================================
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    account_id VARCHAR(50),
    transaction_date TIMESTAMP,
    transaction_type VARCHAR(20),  -- 'Debit', 'Credit', 'ATM Withdrawal', 'Transfer'
    amount DECIMAL(12,2),
    merchant_name VARCHAR(200),
    merchant_category VARCHAR(100),  -- MCC codes mapped: 'Groceries', 'Furniture', 'Home Improvement', 'Travel', 'Baby Products', 'Healthcare', etc.
    merchant_category_code VARCHAR(10),  -- Actual MCC code
    transaction_channel VARCHAR(50),  -- 'In-Store', 'Online', 'Mobile App', 'ATM'
    is_recurring BOOLEAN,  -- Subscription or recurring payment
    location_city VARCHAR(100),
    location_state VARCHAR(50),
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- ============================================================================
-- TABLE 4: DIGITAL_ENGAGEMENT
-- Customer digital behavior: logins, sessions, clicks
-- ============================================================================
CREATE TABLE digital_engagement (
    engagement_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    session_date TIMESTAMP,
    channel VARCHAR(50),  -- 'Mobile App', 'Web Banking', 'Tablet App'
    session_duration_seconds INT,
    pages_viewed INT,
    features_used TEXT,  -- JSON array: ['account_summary', 'transfer', 'bill_pay', 'mortgage_calculator']
    device_type VARCHAR(50),  -- 'iOS', 'Android', 'Desktop', 'Tablet'
    login_method VARCHAR(50),  -- 'Biometric', 'Password', 'SSO'
    location_city VARCHAR(100),
    location_state VARCHAR(50),
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================================================
-- TABLE 5: APPLICATIONS
-- Product applications: started, abandoned, completed, approved/denied
-- ============================================================================
CREATE TABLE applications (
    application_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    product_type VARCHAR(100),  -- 'Mortgage', 'Auto Loan', 'Credit Card', 'Personal Loan', 'Home Equity Line'
    application_status VARCHAR(50),  -- 'Started', 'Abandoned', 'Submitted', 'Under Review', 'Approved', 'Denied'
    started_at TIMESTAMP,
    submitted_at TIMESTAMP,
    completed_at TIMESTAMP,
    abandoned_at TIMESTAMP,
    decision VARCHAR(50),  -- 'Approved', 'Denied', 'Pending', NULL
    denial_reason VARCHAR(200),
    requested_amount DECIMAL(12,2),
    approved_amount DECIMAL(12,2),
    completion_percentage INT,  -- 0-100, how far they got before abandoning
    abandonment_stage VARCHAR(100),  -- 'Personal Info', 'Employment', 'Income Verification', 'Document Upload'
    channel VARCHAR(50),  -- 'Mobile App', 'Web', 'Branch'
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================================================
-- TABLE 6: DIRECT_DEPOSITS
-- Payroll and recurring deposit tracking (income signals)
-- ============================================================================
CREATE TABLE direct_deposits (
    deposit_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    account_id VARCHAR(50),
    deposit_date DATE,
    amount DECIMAL(12,2),
    deposit_type VARCHAR(50),  -- 'Payroll', 'Social Security', 'Pension', 'Government Benefit'
    employer_name VARCHAR(200),
    frequency VARCHAR(20),  -- 'Weekly', 'Bi-Weekly', 'Monthly', 'Semi-Monthly'
    is_recurring BOOLEAN,
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- ============================================================================
-- TABLE 7: PRODUCTS
-- Available banking products catalog
-- ============================================================================
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(200),
    product_category VARCHAR(100),  -- 'Deposit', 'Credit', 'Loan', 'Insurance', 'Investment'
    product_type VARCHAR(100),  -- 'Checking', 'Savings', 'Credit Card', 'Mortgage', 'Auto Loan', 'Home Insurance'
    description TEXT,
    min_income_required DECIMAL(12,2),
    min_credit_score INT,
    min_tenure_months INT,  -- Minimum customer tenure required
    max_age INT,
    min_age INT,
    interest_rate_range VARCHAR(50),  -- '3.5% - 5.5%'
    fees_description TEXT,
    eligibility_rules TEXT,  -- JSON: complex rules
    target_segments TEXT,  -- JSON array: ['Affluent', 'Mass Market']
    cross_sell_priority INT,  -- 1-10, higher = more important
    is_active BOOLEAN,
    created_at TIMESTAMP
);

-- ============================================================================
-- TABLE 8: PRODUCT_HOLDINGS
-- Current products held by each customer
-- ============================================================================
CREATE TABLE product_holdings (
    holding_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    product_id VARCHAR(50),
    account_id VARCHAR(50),
    acquired_date DATE,
    status VARCHAR(50),  -- 'Active', 'Inactive', 'Closed'
    usage_frequency VARCHAR(50),  -- 'High', 'Medium', 'Low'
    satisfaction_score DECIMAL(3,2),  -- 0-5 rating
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- ============================================================================
-- TABLE 9: CREDIT_UTILIZATION
-- Credit card utilization tracking over time
-- ============================================================================
CREATE TABLE credit_utilization (
    utilization_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    account_id VARCHAR(50),
    report_date DATE,
    credit_limit DECIMAL(12,2),
    current_balance DECIMAL(12,2),
    utilization_percentage DECIMAL(5,2),  -- 0-100
    available_credit DECIMAL(12,2),
    payment_status VARCHAR(50),  -- 'On Time', 'Late', 'Missed'
    days_past_due INT,
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- ============================================================================
-- TABLE 10: LIFE_EVENT_SIGNALS (Optional - for caching detected signals)
-- Stores detected life events for fast lookup
-- ============================================================================
CREATE TABLE life_event_signals (
    signal_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    signal_type VARCHAR(100),  -- 'Relocation', 'New Job', 'Marriage', 'New Baby', 'Retirement'
    detected_at TIMESTAMP,
    confidence_score DECIMAL(3,2),  -- 0-1
    supporting_evidence TEXT,  -- JSON: what data points led to this inference
    expiry_date TIMESTAMP,  -- Signals age out
    is_active BOOLEAN,
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================================================
-- INDEXES for Performance
-- ============================================================================
CREATE INDEX idx_transactions_customer_date ON transactions(customer_id, transaction_date DESC);
CREATE INDEX idx_transactions_merchant_category ON transactions(merchant_category);
CREATE INDEX idx_digital_engagement_customer_date ON digital_engagement(customer_id, session_date DESC);
CREATE INDEX idx_applications_customer_status ON applications(customer_id, application_status);
CREATE INDEX idx_direct_deposits_customer_date ON direct_deposits(customer_id, deposit_date DESC);
CREATE INDEX idx_accounts_customer_type ON accounts(customer_id, account_type);
CREATE INDEX idx_credit_utilization_customer_date ON credit_utilization(customer_id, report_date DESC);


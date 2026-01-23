-- ============================================================================
-- RETAIL/E-COMMERCE PERSONALIZATION PLATFORM - DATA SCHEMA
-- Purpose: Support Agent A (Persona Builder) and Agent B (Product Matchmaker)
-- Based on: Point-of-Sale & Transaction History
-- ============================================================================

-- ============================================================================
-- TABLE 1: CUSTOMERS
-- Core customer demographic and loyalty data
-- ============================================================================
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    phone VARCHAR(20),
    age INT,
    gender VARCHAR(10),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    registration_date DATE,
    customer_since_days INT,
    loyalty_tier VARCHAR(50),  -- 'Bronze', 'Silver', 'Gold', 'Platinum'
    loyalty_points INT,
    total_lifetime_spend DECIMAL(12,2),
    total_orders INT,
    avg_order_value DECIMAL(10,2),
    preferred_channel VARCHAR(50),  -- 'Offline', 'Online', 'App'
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- ============================================================================
-- TABLE 2: TRANSACTIONS
-- Point-of-Sale and transaction history (from your schema)
-- ============================================================================
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    transaction_timestamp TIMESTAMP,
    store_id VARCHAR(50),
    sku_id VARCHAR(50),
    quantity INT,
    unit_price DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    total_basket_value DECIMAL(12,2),
    promo_flag BOOLEAN,
    channel VARCHAR(50),  -- 'Offline', 'Online', 'App'
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================================================
-- TABLE 3: PRODUCTS (SKU Catalog)
-- Product catalog with categories and attributes
-- ============================================================================
CREATE TABLE products (
    sku_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(200),
    category VARCHAR(100),  -- 'Electronics', 'Fashion', 'Home', 'Baby', 'Sports', etc.
    sub_category VARCHAR(100),
    brand VARCHAR(100),
    price DECIMAL(10,2),
    cost DECIMAL(10,2),
    margin_percentage DECIMAL(5,2),
    stock_quantity INT,
    is_seasonal BOOLEAN,
    season VARCHAR(50),  -- 'Spring', 'Summer', 'Fall', 'Winter', 'Holiday'
    is_active BOOLEAN,
    created_at TIMESTAMP
);

-- ============================================================================
-- TABLE 4: CUSTOMER_SESSIONS
-- Digital browsing behavior
-- ============================================================================
CREATE TABLE customer_sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    session_start TIMESTAMP,
    session_end TIMESTAMP,
    session_duration_seconds INT,
    pages_viewed INT,
    products_viewed TEXT,  -- JSON array of SKU IDs
    products_added_to_cart TEXT,  -- JSON array of SKU IDs
    cart_abandoned BOOLEAN,
    conversion BOOLEAN,
    device_type VARCHAR(50),  -- 'Desktop', 'Mobile', 'Tablet'
    channel VARCHAR(50),  -- 'Web', 'App'
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================================================
-- TABLE 5: CUSTOMER_REVIEWS
-- Product reviews and ratings
-- ============================================================================
CREATE TABLE customer_reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    sku_id VARCHAR(50),
    rating INT,  -- 1-5 stars
    review_text TEXT,
    review_date DATE,
    helpful_votes INT,
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (sku_id) REFERENCES products(sku_id)
);

-- ============================================================================
-- TABLE 6: BASKET_COMPOSITION
-- Detailed basket-level data for affinity analysis
-- ============================================================================
CREATE TABLE basket_composition (
    basket_id VARCHAR(50) PRIMARY KEY,
    transaction_id VARCHAR(50),
    customer_id VARCHAR(50),
    transaction_timestamp TIMESTAMP,
    total_items INT,
    unique_skus INT,
    total_value DECIMAL(12,2),
    discount_applied DECIMAL(10,2),
    skus_in_basket TEXT,  -- JSON array of SKU IDs
    categories_in_basket TEXT,  -- JSON array of categories
    channel VARCHAR(50),
    created_at TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================================================
-- TABLE 7: PROMO_EXPOSURE
-- Marketing campaign exposure and effectiveness tracking
-- ============================================================================
CREATE TABLE promo_exposure (
    exposure_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    campaign_id VARCHAR(50),
    sku_id VARCHAR(50),
    promo_type VARCHAR(50),  -- 'discount', 'bundle', 'free gift'
    promo_value DECIMAL(10,2),
    channel VARCHAR(50),  -- 'Email', 'App', 'In-store', 'SMS', 'Web banner'
    exposure_time_stamp TIMESTAMP,
    redeemed_flag BOOLEAN,
    conversion_txn_id VARCHAR(50),  -- Transaction ID if converted
    created_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (sku_id) REFERENCES products(sku_id)
);

-- ============================================================================
-- TABLE 8: PRODUCT_AFFINITIES
-- Precomputed product-to-product recommendations
-- ============================================================================
CREATE TABLE product_affinities (
    affinity_id VARCHAR(50) PRIMARY KEY,
    source_sku VARCHAR(50),
    target_sku VARCHAR(50),
    affinity_score DECIMAL(5,2),  -- 0-1, higher = stronger affinity
    support_count INT,  -- How many times bought together
    confidence DECIMAL(5,2),  -- Probability of buying target given source
    created_at TIMESTAMP,
    FOREIGN KEY (source_sku) REFERENCES products(sku_id),
    FOREIGN KEY (target_sku) REFERENCES products(sku_id)
);

-- ============================================================================
-- INDEXES for Performance
-- ============================================================================
CREATE INDEX idx_transactions_customer_time ON transactions(customer_id, transaction_timestamp DESC);
CREATE INDEX idx_transactions_sku ON transactions(sku_id);
CREATE INDEX idx_sessions_customer ON customer_sessions(customer_id, session_start DESC);
CREATE INDEX idx_basket_customer ON basket_composition(customer_id, transaction_timestamp DESC);
CREATE INDEX idx_reviews_sku ON customer_reviews(sku_id);
CREATE INDEX idx_affinities_source ON product_affinities(source_sku, affinity_score DESC);
CREATE INDEX idx_promo_exposure_customer ON promo_exposure(customer_id, exposure_time_stamp DESC);
CREATE INDEX idx_promo_exposure_campaign ON promo_exposure(campaign_id, redeemed_flag);


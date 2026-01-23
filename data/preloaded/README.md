# Pre-loaded Datasets

This directory contains pre-generated datasets for testing the personalization platform.

## Available Datasets

### 1. E-commerce 🛍️
**Location:** `ecommerce/`

**Files:**
- `customers.csv` - Customer profiles (1000 records)
- `products.csv` - Product catalog (50+ items)
- `transactions.csv` - Purchase history (~10K transactions)

**Columns:**
- Customers: customer_id, name, email, age, gender, income, location, join_date
- Products: product_id, product_name, category, price, description
- Transactions: transaction_id, customer_id, product_id, total_amount, quantity, transaction_date, channel

---

### 2. Sports Academy ⚽
**Location:** `sports_academy/`

**Files:**
- `customers.csv` - Student profiles (800 records)
- `products.csv` - Program offerings (32 programs)
- `transactions.csv` - Enrollment records (~2K enrollments)

**Columns:**
- Customers: customer_id, name, email, age, gender, skill_level, join_date, location
- Products: product_id, product_name, category, price, description, duration_months
- Transactions: transaction_id, customer_id, product_id, total_amount, quantity, transaction_date, channel

---

### 3. Banking 🏦
**Location:** `banking/`

**Files:**
- `customers.csv` - Account holder profiles (1200 records)
- `products.csv` - Financial services (10 services)
- `transactions.csv` - Service adoptions (~3K transactions)

**Columns:**
- Customers: customer_id, name, email, age, gender, income, account_type, join_date
- Products: product_id, product_name, category, price, description
- Transactions: transaction_id, customer_id, product_id, total_amount, quantity, transaction_date, channel

---

## How to Generate

If datasets don't exist, they will be automatically generated when you:
1. Click "Generate Dataset" in the Data Loader page
2. Or run: `python -c "from utils.dataset_generator import PreloadedDatasetGenerator; PreloadedDatasetGenerator().generate_all_datasets()"`

---

## Custom Data Format

To upload your own data, ensure your CSVs have these required columns:

**customers.csv:**
- `customer_id` (required)
- `name`
- `email`
- Plus any demographic columns (age, gender, etc.)

**products.csv:**
- `product_id` (required)
- `product_name` (required)
- `category` (required)
- `price` (required)
- `description`

**transactions.csv:**
- `transaction_id` (required)
- `customer_id` (required)
- `product_id` (required)
- `total_amount` (required)
- `transaction_date`
- `quantity`

---

**Note:** Datasets are generated with realistic distributions and patterns for demonstration purposes.


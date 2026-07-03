"""
Patch 2 for customers.csv (2026-06-11):
  1. Remap Business/Agricultural customer_segment → Personal
  2. Remap Business/Agricultural customer_type → realistic Personal types
  3. Add products_held column (pipe-separated list of product subcategories
     the customer holds) after num_products
"""

import pandas as pd
import random

random.seed(42)

CUSTOMERS_PATH = "data/preloaded/meridian_bank/customers.csv"

# ── 1. Customer type remapping ────────────────────────────────────────────────
# Business types → income-based personal types
# Agricultural types → mostly Mass_Market / High_Net_Worth by income

BUSINESS_TYPE_MAP = {
    "Small_Business": None,          # resolved by income below
    "Commercial_Real_Estate": "High_Net_Worth",
}
AGRI_TYPE_MAP = {
    "Row_Crop_Farmer": None,         # resolved by income below
    "Livestock_Rancher": None,
    "Vineyard_Orchard_Owner": None,
}

def remap_customer_type(row):
    seg  = row["customer_segment"]
    ctype = row["customer_type"]
    income = row["income"]

    if seg == "Business":
        if ctype == "Commercial_Real_Estate":
            return "High_Net_Worth"
        # Small_Business → tier by income
        if income >= 100000:
            return "High_Net_Worth"
        elif income >= 60000:
            return "Young_Professional"
        else:
            return "Mass_Market"

    if seg == "Agricultural":
        if income >= 90000:
            return "High_Net_Worth"
        elif income >= 50000:
            return "Mass_Market"
        else:
            return "Mass_Market"

    return ctype  # Personal — unchanged


# ── 2. Products held generation ───────────────────────────────────────────────
# products_held uses actual PRODUCT NAMES, not reward benefit labels.
# "Credit Card" is the product; "Cash Back" / "Travel Rewards" are its benefits.

BASE_PRODUCTS     = ["Checking Account"]
SAVINGS_PRODUCTS  = ["Savings Account", "Money Market Account", "12-Month CD", "24-Month CD"]
LOAN_PRODUCTS     = ["Auto Loan", "Personal Loan", "Student Loan", "Home Equity Loan"]
MORTGAGE_PRODUCTS = ["Mortgage", "FHA Mortgage", "Jumbo Mortgage", "Mortgage Refinance"]
INVEST_PRODUCTS   = ["Investment Account", "HSA Account"]

def _candidate_pool(row):
    """Return a pool of actual product names for this customer."""
    income     = row["income"]
    credit     = row["credit_score"]
    life_stage = str(row.get("life_stage", "")).lower()
    owns_home  = row.get("owns_home", 0)
    pool = list(BASE_PRODUCTS)

    # Savings / deposit products
    if income > 50000:
        pool += random.choices(SAVINGS_PRODUCTS, k=2)
    else:
        pool += ["Savings Account"]

    # Credit card — the product is a Credit Card regardless of rewards benefit
    if credit >= 650:
        pool += ["Credit Card"]
    elif credit >= 580:
        pool += ["Secured Credit Card"]

    # Loans
    if "student" in life_stage or ("young" in life_stage and credit >= 640):
        pool += ["Student Loan", "Auto Loan"]
    elif income > 40000:
        pool += random.choices(LOAN_PRODUCTS[:3], k=1)

    # Mortgage
    if owns_home and credit >= 680:
        pool += random.choices(MORTGAGE_PRODUCTS[:2], k=1)
    elif "millennial" in life_stage or "family" in life_stage:
        if credit >= 640 and income > 60000:
            pool += ["Mortgage"]

    # Investments — high income or near retirement
    if income > 80000 or "retire" in life_stage or "senior" in life_stage:
        pool += random.choices(INVEST_PRODUCTS, k=1)

    return list(dict.fromkeys(pool))   # deduplicate preserving order


def generate_products_held(row):
    n = max(1, int(row["num_products"]))
    pool = _candidate_pool(row)
    chosen = pool[:n] if n <= len(pool) else pool
    return "|".join(chosen[:n])


# ── Execute ───────────────────────────────────────────────────────────────────

df = pd.read_csv(CUSTOMERS_PATH)
print(f"Loaded {len(df)} customers, {len(df.columns)} columns")
print(f"Segments before: {df['customer_segment'].value_counts().to_dict()}")

# Step 1: remap customer_type for any remaining Business/Agricultural rows
df["customer_type"] = df.apply(remap_customer_type, axis=1)

# Step 2: remap customer_segment
df["customer_segment"] = df["customer_segment"].replace({
    "Business": "Personal",
    "Agricultural": "Personal",
})
print(f"Segments after:  {df['customer_segment'].value_counts().to_dict()}")

# Step 3: overwrite products_held with corrected product names
df["products_held"] = df.apply(generate_products_held, axis=1)

# Ensure products_held sits right after num_products
cols = list(df.columns)
if "products_held" in cols:
    cols.remove("products_held")
num_idx = cols.index("num_products")
cols.insert(num_idx + 1, "products_held")
df = df[cols]

df.to_csv(CUSTOMERS_PATH, index=False)
print(f"\nSaved customers.csv — {len(df)} rows, {len(df.columns)} columns")
print(f"Sample products_held:\n{df[['customer_id','num_products','products_held']].head(10).to_string(index=False)}")

"""
Patch 3 for customers.csv (2026-06-11):

Customer Profile changes:
  1. customer_segment  → customer_type
  2. customer_type     → DELETE (AI will determine via segmentation)
  3. credit_score_trend → credit_score_trend_p6mo
  4. total_deposits    → total_deposit_value
  5. avg_daily_balance → avg_daily_balance_p30days
  6. owns_home         → DELETE (home_ownership already captures this)

Customer Engagement changes:
  7. competitor_offer_received → DELETE (banks cannot know this)
  8. customer_lifetime_value   → recalculate as realistic 3-year revenue
     Formula: (NIM on deposits + loan margin + product fees + card spend) × 3 yrs
     Tiers: Bronze <$2K | Silver $2K-$6K | Gold $6K-$15K | Platinum >$15K
"""

import pandas as pd
import numpy as np

CUSTOMERS_PATH = "data/preloaded/meridian_bank/customers.csv"

df = pd.read_csv(CUSTOMERS_PATH)
print(f"Loaded {len(df)} customers, {len(df.columns)} columns")

# ── 1. Delete the OLD customer_type BEFORE renaming customer_segment ──────────
# Order matters: drop the old column first, then rename, to avoid collision.
cols_to_drop = [c for c in ["customer_type", "owns_home", "competitor_offer_received"] if c in df.columns]
df.drop(columns=cols_to_drop, inplace=True)
print(f"  Deleted: {cols_to_drop}")

# ── 2. Rename columns ─────────────────────────────────────────────────────────
renames = {
    "customer_segment":   "customer_type",
    "credit_score_trend": "credit_score_trend_p6mo",
    "total_deposits":     "total_deposit_value",
    "avg_daily_balance":  "avg_daily_balance_p30days",
}
df.rename(columns=renames, inplace=True)
print(f"  Renamed: {list(renames.items())}")

# ── 3. Recalculate customer_lifetime_value (3-year realistic bank revenue) ───
# Sources of revenue:
#   NIM    : net interest margin on deposits (2.5% / yr)
#   Loan   : spread on loan balance (3.5% / yr)
#   Fees   : product-count-based fee income (~$60 per product per year)
#   Cards  : interchange on monthly spend (~1.5% of monthly spend × 12)
# Multiplied by 3 years and discounted by churn probability.

def calc_clv_3yr(row):
    balance   = row.get("total_deposit_value", 0) or 0
    loan_bal  = row.get("total_loan_balance", 0) or 0
    n_prods   = row.get("num_products", 1) or 1
    spend_mo  = row.get("monthly_spend_in_primary_cat", 200) or 200
    churn_p   = row.get("churn_probability", 0.1) or 0.1

    nim_annual   = balance   * 0.025          # 2.5% NIM on deposits
    loan_annual  = loan_bal  * 0.035          # 3.5% loan spread
    fee_annual   = n_prods   * 60             # $60 per product/year
    card_annual  = spend_mo  * 12 * 0.015     # 1.5% interchange on annual spend

    annual_rev  = nim_annual + loan_annual + fee_annual + card_annual
    retention   = max(0.1, 1 - churn_p)      # probability customer stays
    clv_3yr     = annual_rev * 3 * retention

    # Add small noise for realism (±5%)
    noise = np.random.uniform(0.95, 1.05)
    return round(clv_3yr * noise, 2)

np.random.seed(42)
df["customer_lifetime_value"] = df.apply(calc_clv_3yr, axis=1)

# ── 4. Recalculate clv_tier with 3-year revenue thresholds ───────────────────
def assign_clv_tier(clv):
    if clv >= 15000:  return "Platinum"
    if clv >= 6000:   return "Gold"
    if clv >= 2000:   return "Silver"
    return "Bronze"

df["clv_tier"] = df["customer_lifetime_value"].apply(assign_clv_tier)

print("\nCLV stats (3-year revenue):")
print(f"  Min:  ${df['customer_lifetime_value'].min():,.0f}")
print(f"  Mean: ${df['customer_lifetime_value'].mean():,.0f}")
print(f"  Max:  ${df['customer_lifetime_value'].max():,.0f}")
print(f"  Tiers: {df['clv_tier'].value_counts().to_dict()}")

# ── 5. Save ───────────────────────────────────────────────────────────────────
df.to_csv(CUSTOMERS_PATH, index=False)
print(f"\nSaved customers.csv — {len(df)} rows, {len(df.columns)} columns")
print(f"Final columns:\n  {list(df.columns)}")

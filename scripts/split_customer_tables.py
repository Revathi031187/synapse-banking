"""
Split customers.csv into two purpose-built tables per Abhay Joshi's direction
(meeting 2026-06-04):

  customer_profile.csv    — Who the customer IS (demographics, finances, preferences)
  customer_engagement.csv — How the customer BEHAVES (interactions, transactions, health)

The original customers.csv is kept intact for backward-compat with existing agents.
Both new files share customer_id as the join key.
"""

import pandas as pd

CUSTOMERS_PATH = "data/preloaded/meridian_bank/customers.csv"
PROFILE_PATH   = "data/preloaded/meridian_bank/customer_profile.csv"
ENGAGEMENT_PATH= "data/preloaded/meridian_bank/customer_engagement.csv"

# ── Column definitions ────────────────────────────────────────────────────────

PROFILE_COLS = [
    # Identity
    "customer_id",
    "customer_name",
    "customer_type",          # renamed from customer_segment
    # Core demographics
    "age",
    "income",
    "credit_score",
    "credit_score_trend_p6mo",  # renamed from credit_score_trend
    "credit_tier",
    # Financial snapshot
    "total_deposit_value",    # renamed from total_deposits
    "num_products",
    "products_held",
    "total_loan_balance",
    "outstanding_debt_total",
    "avg_daily_balance_p30days",  # renamed from avg_daily_balance
    "credit_utilization_ratio",
    # Housing & assets (owns_home removed — home_ownership captures this)
    "home_ownership_type",
    "home_ownership",
    # Employment & demographics
    "employment_type",
    "occupation",
    "life_stage",
    "geographic_region",
    "address_changes_count",
    # Preferences & goals
    "financial_goal",
    "travel_frequency",
    "investment_risk_profile",
    "preferred_loan_term",
    "preferred_rewards_type",
    "preferred_communication_style",
    "risk_tolerance",
    "fee_sensitivity_tier",
    # Banking relationship preferences
    "has_direct_deposit",
    "monthly_direct_deposit_amt",
    "has_competitor_credit_card",
    "primary_spending_category",
    "monthly_spend_in_primary_cat",
]

ENGAGEMENT_COLS = [
    # Join key
    "customer_id",
    # Relationship timeline
    "months_since_relationship_started",
    # Channel behaviour
    "digital_engagement_score",
    "branch_visit_frequency",
    "channel_preference",
    "digital_engagement_decline",
    # Product usage
    "product_adoption_velocity",
    "cross_sell_receptivity",
    "products_closed_last_6mo",
    # Transaction activity
    "monthly_transaction_volume",
    "last_transaction_date",
    "days_since_last_transaction",
    "recent_txn_count",
    "previous_txn_count",
    "txn_frequency_trend",
    "annual_transaction_value",
    # Financial health signals
    "balance_trend",
    "deposit_change_3mo_pct",
    "low_balance_flag",
    "overdrafts_last_3mo",
    "high_overdraft_flag",
    "overdraft_frequency",
    "debt_payment_missed",
    # External signals (competitor_offer_received removed — banks cannot know this)
    "complaints_last_year",
    "support_contacts_last_3mo",
    "external_accounts_linked",
    "recent_life_event",
    "fee_sensitivity_score",
    "age_risk_factor",
    # Satisfaction
    "nps_score",
    "nps_category",
    "csat_score",
    "branch_satisfaction",
    # Credit health
    "credit_score_declining",
    # Churn signals
    "churn_risk_score",
    "churn_risk_category",
    "churn_probability",
    "churned",
    "churn_date",
    "recommended_retention_action",
    "suggested_retention_offer",
    # Lifetime value
    "expected_relationship_years",
    "customer_lifetime_value",
    "clv_tier",
]

# ── Execute split ─────────────────────────────────────────────────────────────

df = pd.read_csv(CUSTOMERS_PATH)
print(f"Loaded {len(df)} customers, {len(df.columns)} columns")

# Only keep columns that actually exist (graceful if some are absent)
profile_cols    = [c for c in PROFILE_COLS    if c in df.columns]
engagement_cols = [c for c in ENGAGEMENT_COLS if c in df.columns]

missing_from_profile    = [c for c in PROFILE_COLS    if c not in df.columns]
missing_from_engagement = [c for c in ENGAGEMENT_COLS if c not in df.columns]
if missing_from_profile:
    print(f"  WARN: columns not found for profile: {missing_from_profile}")
if missing_from_engagement:
    print(f"  WARN: columns not found for engagement: {missing_from_engagement}")

# Check no column is in both tables (except customer_id)
overlap = (set(profile_cols) & set(engagement_cols)) - {"customer_id"}
if overlap:
    print(f"  WARN: columns in both tables: {overlap}")

profile_df    = df[profile_cols].copy()
engagement_df = df[engagement_cols].copy()

profile_df.to_csv(PROFILE_PATH, index=False)
print(f"\nWrote customer_profile.csv    — {len(profile_df)} rows, {len(profile_cols)} columns")

engagement_df.to_csv(ENGAGEMENT_PATH, index=False)
print(f"Wrote customer_engagement.csv — {len(engagement_df)} rows, {len(engagement_cols)} columns")

# Verify the two tables cover all columns (minus any we explicitly excluded)
all_covered = set(profile_cols) | set(engagement_cols)
all_columns = set(df.columns)
uncovered = all_columns - all_covered
if uncovered:
    print(f"\n  NOTE: {len(uncovered)} columns not assigned to either table: {sorted(uncovered)}")
else:
    print("\nAll 80 columns assigned to one of the two tables.")

print("\nSplit complete. customers.csv unchanged (used by agents for full merged view).")

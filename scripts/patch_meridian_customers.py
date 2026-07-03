"""
Patch Meridian Bank customers.csv in-place:
  1. Rename tenure_months -> months_since_relationship_started
  2. Normalize digital_engagement_score + branch_visit_frequency to sum to 1
  3. Add credit_score_trend (Declining / Improving / Stable)
  4. Add occupation
  5. Add address_changes_count (0-3, inversely correlated with tenure)
"""

import random
import pandas as pd

CUSTOMERS_PATH = "data/preloaded/meridian_bank/customers.csv"

df = pd.read_csv(CUSTOMERS_PATH)
print(f"Loaded {len(df)} customers, {len(df.columns)} columns")

# 1. Rename tenure_months -> months_since_relationship_started
if "tenure_months" in df.columns:
    df.rename(columns={"tenure_months": "months_since_relationship_started"}, inplace=True)
    print("Renamed tenure_months -> months_since_relationship_started")
else:
    print("tenure_months not found (may already be renamed)")

tenure_col = "months_since_relationship_started"

# 2. Normalize engagement ratios to sum to 1
total = df["digital_engagement_score"] + df["branch_visit_frequency"]
mask_nonzero = total > 0
df.loc[mask_nonzero, "digital_engagement_score"] = (
    df.loc[mask_nonzero, "digital_engagement_score"] / total[mask_nonzero]
)
df.loc[mask_nonzero, "branch_visit_frequency"] = (
    df.loc[mask_nonzero, "branch_visit_frequency"] / total[mask_nonzero]
)
df.loc[~mask_nonzero, "digital_engagement_score"] = 0.7
df.loc[~mask_nonzero, "branch_visit_frequency"] = 0.3
print("Normalized engagement ratios")

# 3. Add credit_score_trend (skip if already present)
if "credit_score_trend" not in df.columns:
    random.seed(42)
    def get_trend(row):
        if row.get("credit_score_declining", 0) == 1:
            return "Declining"
        return "Improving" if random.random() < 0.4 else "Stable"
    df["credit_score_trend"] = df.apply(get_trend, axis=1)
    print("Added credit_score_trend")
else:
    print("credit_score_trend already present, skipping")

# 4. Add occupation (skip if already present)
if "occupation" not in df.columns:
    OCCUPATION_POOLS = {
        "high": ["Finance", "Technology", "Healthcare", "Manager", "Professional", "Business Owner"],
        "mid":  ["Education", "Government", "Healthcare", "Retail", "Technology", "Manager", "Professional"],
        "low":  ["Retail", "Service", "Education", "Government"],
    }
    random.seed(42)
    def get_occupation(row):
        life_stage = str(row.get("life_stage", "")).lower()
        emp_type   = str(row.get("employment_type", "")).lower()
        age        = row.get("age", 30)
        income     = row.get("annual_income", 0)

        if emp_type == "retired" or life_stage == "retiree":
            return "Retired"
        if life_stage == "student" or (isinstance(age, (int, float)) and age < 22):
            return "Student"

        if income >= 75000:
            pool = OCCUPATION_POOLS["high"]
        elif income >= 35000:
            pool = OCCUPATION_POOLS["mid"]
        else:
            pool = OCCUPATION_POOLS["low"]

        return random.choice(pool)

    df["occupation"] = df.apply(get_occupation, axis=1)
    print("Added occupation")
else:
    print("occupation already present, skipping")

# 5. Add address_changes_count (skip if already present)
if "address_changes_count" not in df.columns:
    random.seed(42)
    def get_address_changes(tenure):
        raw = 3 - (tenure / 60) * 2.5 + random.uniform(-0.5, 0.5)
        return max(0, min(3, round(raw)))
    df["address_changes_count"] = df[tenure_col].apply(get_address_changes)
    print("Added address_changes_count")
else:
    print("address_changes_count already present, skipping")

# Save
df.to_csv(CUSTOMERS_PATH, index=False)
print(f"\nSaved. Final shape: {df.shape}")

# Verification
sample = df[["customer_id", tenure_col, "digital_engagement_score",
             "branch_visit_frequency", "credit_score_trend", "occupation",
             "address_changes_count"]].head(3)
print("\nSample rows:")
print(sample.to_string())

eng_check = (df["digital_engagement_score"] + df["branch_visit_frequency"]).round(6)
assert (eng_check == 1.0).all(), "Engagement ratios do not sum to 1!"
print("\nEngagement ratio check passed (all sum to 1.0)")

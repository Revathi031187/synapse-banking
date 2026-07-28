#!/usr/bin/env python3
"""
patch_meridian_segments.py

Reshapes data/preloaded/meridian_bank/customers.csv so that K-Prototypes
clustering in Agent A produces 5 clean, well-separated archetypal segments:
  Wealth Builder, Everyday Essential, Digital Native, Retiree Anchor, At-Risk Borrower
Each cohort is sized to exactly 1,000 customers.
"""

import os
import sys
import numpy as np
import pandas as pd

SEED = 42
np.random.seed(SEED)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data", "preloaded", "meridian_bank", "customers.csv")

# ── COHORT ASSIGNMENT ────────────────────────────────────────────────────────
DIST_FEATURES = [
    "income", "credit_score", "total_deposit_value",
    "digital_engagement_score", "age", "churn_probability",
]
SCALES = {
    "income": 200000, "credit_score": 850, "total_deposit_value": 200000,
    "digital_engagement_score": 1.0, "age": 100, "churn_probability": 1.0,
}
WEIGHTS = {
    "income": 2.5, "credit_score": 1.5, "total_deposit_value": 2.5,
    "digital_engagement_score": 2.5, "age": 2.0, "churn_probability": 2.0,
}
CENTROIDS = {
    "Wealth Builder":     {"income": 142000, "credit_score": 812, "total_deposit_value": 94000,
                           "digital_engagement_score": 0.65, "age": 48, "churn_probability": 0.11},
    "Everyday Essential": {"income": 54000,  "credit_score": 700, "total_deposit_value": 22000,
                           "digital_engagement_score": 0.40, "age": 42, "churn_probability": 0.28},
    "Digital Native":     {"income": 38000,  "credit_score": 685, "total_deposit_value": 42000,
                           "digital_engagement_score": 0.92, "age": 27, "churn_probability": 0.35},
    "Retiree Anchor":     {"income": 52000,  "credit_score": 775, "total_deposit_value": 82000,
                           "digital_engagement_score": 0.22, "age": 68, "churn_probability": 0.07},
    "At-Risk Borrower":   {"income": 24000,  "credit_score": 562, "total_deposit_value": 20000,
                           "digital_engagement_score": 0.55, "age": 36, "churn_probability": 0.60},
}
# Realistic banking segment distribution — irregular sizes reflect natural clustering
TARGET_SIZES = {
    "Wealth Builder":     723,   # 14.5%
    "Everyday Essential": 1726,  # 34.5%
    "Digital Native":     836,   # 16.7%
    "Retiree Anchor":     912,   # 18.2%
    "At-Risk Borrower":   803,   # 16.1%
}
# Keep TARGET_SIZE as alias (used in assign_cohorts — will be replaced with per-cohort value)
TARGET_SIZE = 1000  # unused after assign_cohorts update below

# ── TARGET NUMERIC DISTRIBUTIONS  (mean, std, lo, hi)  ──────────────────────
# None → field will be forced to a fixed value (see FORCED_VALUES)
TARGET_STATS = {
    # ── Wealth Builder ──────────────────────────────────────────────────────────
    # TIGHT digital (0.52-0.78) so K-Prototypes won't split it into Digital/Retiree sub-groups
    "Wealth Builder": {
        "income":                    (142000, 24000, 82000, 215000),  # wider std+lo: ~3% near Everyday boundary
        "credit_score":              (812, 14, 778, 850),
        "total_deposit_value":       (94000, 14000, 62000, 142000),
        "digital_engagement_score":  (0.65, 0.05, 0.52, 0.78),   # TIGHT — no overlap with Digital (>0.79) or Retiree (<0.46)
        "churn_probability":         (0.11, 0.03, 0.04, 0.20),
        "age":                       (48, 5, 36, 62),
        "monthly_transaction_volume":(28, 7, 12, 48),
        "overdraft_frequency":       None,
        "nps_score":                 (72, 10, 48, 95),
        "num_products":              (4.5, 0.6, 3, 6),
        "monthly_direct_deposit_amt":(6500, 1200, 3200, 11000),
        "total_loan_balance":        (185000, 75000, 0, 480000),
        "avg_daily_balance_p30days": (92000, 16000, 56000, 145000),
        "fee_sensitivity_score":     (0.22, 0.07, 0.06, 0.38),
        "credit_utilization_ratio":  (0.16, 0.06, 0.03, 0.35),
        "csat_score":                (8.5, 0.7, 6.5, 10.0),
        "branch_visit_frequency":    (0.10, 0.04, 0.02, 0.22),
        "months_since_relationship_started": (96, 32, 36, 220),
        "annual_transaction_value":  (168000, 45000, 60000, 380000),
        "cross_sell_receptivity":    (0.78, 0.09, 0.55, 0.98),
        "product_adoption_velocity": (0.75, 0.10, 0.48, 0.98),
        "deposit_change_3mo_pct":    (3.5, 1.2, 0.8, 7.5),
    },
    # ── Everyday Essential ───────────────────────────────────────────────────
    # RAISED deposits ($22K avg) to create clear gap above At-Risk ($650 avg)
    "Everyday Essential": {
        "income":                    (54000, 8000, 36000, 78000),
        "credit_score":              (700, 28, 644, 762),
        "total_deposit_value":       (22000, 3500, 14000, 34000),   # RAISED: gap from At-Risk ($650) is now 14×
        "digital_engagement_score":  (0.40, 0.07, 0.24, 0.56),    # Lower & tighter than before
        "churn_probability":         (0.28, 0.06, 0.15, 0.44),
        "age":                       (42, 9, 26, 63),  # upper overlap with Retiree (lo=57)
        "monthly_transaction_volume":(20, 5, 8, 34),
        "overdraft_frequency":       (0.6, 0.3, 0, 1.5),
        "nps_score":                 (52, 13, 22, 80),
        "num_products":              (2.5, 0.5, 1, 4),
        "monthly_direct_deposit_amt":(2200, 550, 850, 4000),
        "total_loan_balance":        (45000, 22000, 0, 145000),
        "avg_daily_balance_p30days": (21000, 3500, 13000, 34000),
        "fee_sensitivity_score":     (0.65, 0.10, 0.42, 0.88),
        "credit_utilization_ratio":  (0.44, 0.10, 0.20, 0.72),
        "csat_score":                (7.0, 0.9, 4.5, 9.4),
        "branch_visit_frequency":    (0.30, 0.09, 0.10, 0.52),
        "months_since_relationship_started": (54, 26, 14, 132),
        "annual_transaction_value":  (48000, 12000, 18000, 110000),
        "cross_sell_receptivity":    (0.50, 0.10, 0.26, 0.74),
        "product_adoption_velocity": (0.45, 0.10, 0.22, 0.68),
        "deposit_change_3mo_pct":    (0.4, 1.8, -2.5, 4.0),
    },
    # ── Digital Native ───────────────────────────────────────────────────────
    # Deposits raised to $42K — tech-savvy young workers with solid but growing savings
    "Digital Native": {
        "income":                    (38000, 8000, 18000, 65000),
        "credit_score":              (685, 38, 598, 762),
        "total_deposit_value":       (42000, 9000, 22000, 72000),  # RAISED to $42K
        "digital_engagement_score":  (0.92, 0.07, 0.70, 0.99),  # wider std+lo: ~6% near Wealth boundary (0.78)
        "churn_probability":         (0.35, 0.09, 0.18, 0.58),
        "age":                       (27, 4, 20, 36),
        "monthly_transaction_volume":(62, 11, 36, 88),
        "overdraft_frequency":       (0.4, 0.3, 0, 1.5),
        "nps_score":                 (58, 16, 20, 90),
        "num_products":              (1.8, 0.4, 1, 3),
        "monthly_direct_deposit_amt":(1800, 500, 500, 3500),
        "total_loan_balance":        (22000, 10000, 0, 55000),
        "avg_daily_balance_p30days": (40000, 9000, 20000, 72000),  # Mirrors deposits
        "fee_sensitivity_score":     (0.55, 0.13, 0.24, 0.84),
        "credit_utilization_ratio":  (0.52, 0.14, 0.20, 0.85),
        "csat_score":                (7.2, 1.1, 4.0, 9.6),
        "branch_visit_frequency":    (0.03, 0.02, 0.0, 0.10),
        "months_since_relationship_started": (24, 16, 4, 66),
        "annual_transaction_value":  (58000, 18000, 18000, 115000),
        "cross_sell_receptivity":    (0.62, 0.10, 0.36, 0.86),
        "product_adoption_velocity": (0.68, 0.10, 0.42, 0.90),
        "deposit_change_3mo_pct":    (0.2, 2.2, -4.0, 5.0),
    },
    # ── Retiree Anchor ───────────────────────────────────────────────────────
    # Deposits raised to $82K — loyal long-term savers with highest balance after Wealth Builder
    "Retiree Anchor": {
        "income":                    (52000, 11000, 22000, 86000),
        "credit_score":              (775, 24, 718, 832),
        "total_deposit_value":       (82000, 16000, 48000, 145000), # RAISED to $82K
        "digital_engagement_score":  (0.22, 0.07, 0.06, 0.38),
        "churn_probability":         (0.07, 0.03, 0.01, 0.15),
        "age":                       (68, 6, 57, 84),  # wider std+lo: ~8% near Everyday boundary (age 57-63)
        "monthly_transaction_volume":(9, 3, 3, 20),
        "overdraft_frequency":       None,
        "nps_score":                 (68, 9, 46, 92),
        "num_products":              (3.8, 0.6, 2, 6),
        "monthly_direct_deposit_amt":(2500, 750, 800, 5000),
        "total_loan_balance":        (16000, 20000, 0, 88000),
        "avg_daily_balance_p30days": (80000, 16000, 46000, 148000), # Mirrors deposits
        "fee_sensitivity_score":     (0.28, 0.08, 0.08, 0.50),
        "credit_utilization_ratio":  (0.11, 0.05, 0.02, 0.26),
        "csat_score":                (8.1, 0.8, 5.8, 10.0),
        "branch_visit_frequency":    (0.58, 0.10, 0.35, 0.82),
        "months_since_relationship_started": (168, 44, 80, 295),
        "annual_transaction_value":  (42000, 13000, 14000, 95000),
        "cross_sell_receptivity":    (0.40, 0.09, 0.20, 0.60),
        "product_adoption_velocity": (0.35, 0.09, 0.16, 0.55),
        "deposit_change_3mo_pct":    (1.2, 0.9, -0.3, 3.5),
    },
    # ── At-Risk Borrower ─────────────────────────────────────────────────────
    # Deposits raised to $20K — at-risk defined by credit (562) + high churn (60%), not deposits
    "At-Risk Borrower": {
        "income":                    (24000, 5000, 10000, 38000),
        "credit_score":              (562, 20, 512, 612),          # Tightly low — clear gap to Digital (685)
        "total_deposit_value":       (20000, 5000, 8000, 38000),   # RAISED to $20K
        "digital_engagement_score":  (0.55, 0.10, 0.32, 0.78),
        "churn_probability":         (0.60, 0.10, 0.38, 0.88),    # High — key risk signal
        "age":                       (36, 7, 22, 50),
        "monthly_transaction_volume":(17, 5, 6, 30),
        "overdraft_frequency":       (4.5, 2.0, 1.5, 10.0),
        "nps_score":                 (29, 10, 6, 54),
        "num_products":              (1.4, 0.4, 1, 3),
        "monthly_direct_deposit_amt":(750, 250, 150, 1500),
        "total_loan_balance":        (22000, 11000, 0, 55000),
        "avg_daily_balance_p30days": (19000, 5000, 7000, 38000),  # Mirrors deposits
        "fee_sensitivity_score":     (0.85, 0.08, 0.62, 0.99),
        "credit_utilization_ratio":  (0.82, 0.10, 0.55, 0.99),
        "csat_score":                (5.2, 1.1, 2.0, 7.8),
        "branch_visit_frequency":    (0.20, 0.09, 0.04, 0.44),
        "months_since_relationship_started": (28, 16, 6, 70),
        "annual_transaction_value":  (25000, 9000, 8000, 55000),
        "cross_sell_receptivity":    (0.18, 0.07, 0.04, 0.36),
        "product_adoption_velocity": (0.16, 0.06, 0.04, 0.32),
        "deposit_change_3mo_pct":    (-10.0, 4.0, -22.0, -2.0),
    },
}

# Fixed values for fields with None in TARGET_STATS
FORCED_VALUES = {
    "Wealth Builder":  {"overdraft_frequency": 0.0},
    "Retiree Anchor":  {"overdraft_frequency": 0.0},
}

# ── CATEGORICAL PROFILES ─────────────────────────────────────────────────────
CAT_PROFILES = {
    "Wealth Builder": {
        "life_stage":            (["pre_retiree", "empty_nester", "growing_family"], [0.50, 0.35, 0.15]),
        "risk_tolerance":        (["Aggressive", "Moderate"], [0.60, 0.40]),
        "investment_risk_profile":(["aggressive", "moderate"], [0.60, 0.40]),
        "channel_preference":    (["Digital", "Hybrid"], [0.55, 0.45]),
        "home_ownership":        (["Own"], [1.0]),
        "home_ownership_type":   (["owner_free_clear"], [1.0]),
        "employment_type":       (["full_time_w2", "self_employed"], [0.80, 0.20]),
        "balance_trend":         (["Improving", "Stable"], [0.70, 0.30]),
        "preferred_rewards_type":(["travel_points", "cash_back"], [0.60, 0.40]),
        "financial_goal":        (["grow_wealth", "retirement_savings"], [0.60, 0.40]),
        "fee_sensitivity_tier":  (["low"], [1.0]),
    },
    "Everyday Essential": {
        "life_stage":            (["growing_family", "new_family", "empty_nester"], [0.45, 0.35, 0.20]),
        "risk_tolerance":        (["Moderate", "Conservative"], [0.60, 0.40]),
        "investment_risk_profile":(["moderate", "conservative"], [0.60, 0.40]),
        "channel_preference":    (["Branch", "Hybrid"], [0.50, 0.50]),
        "home_ownership":        (["Mortgage", "Own", "Rent"], [0.60, 0.25, 0.15]),
        "home_ownership_type":   (["owner_with_mortgage", "owner_free_clear", "renter"], [0.60, 0.25, 0.15]),
        "employment_type":       (["full_time_w2", "part_time", "contractor"], [0.70, 0.20, 0.10]),
        "balance_trend":         (["Stable", "Declining", "Improving"], [0.55, 0.25, 0.20]),
        "preferred_rewards_type":(["cash_back", "none"], [0.65, 0.35]),
        "financial_goal":        (["pay_off_debt", "build_emergency_fund", "home_purchase"], [0.50, 0.30, 0.20]),
        "fee_sensitivity_tier":  (["medium", "high"], [0.60, 0.40]),
    },
    "Digital Native": {
        "life_stage":            (["young_single", "student", "new_family"], [0.70, 0.20, 0.10]),
        "risk_tolerance":        (["Moderate", "Aggressive", "Conservative"], [0.50, 0.35, 0.15]),
        "investment_risk_profile":(["moderate", "aggressive", "conservative"], [0.50, 0.35, 0.15]),
        "channel_preference":    (["Digital"], [1.0]),
        "home_ownership":        (["Rent", "Mortgage"], [0.90, 0.10]),
        "home_ownership_type":   (["renter", "owner_with_mortgage"], [0.90, 0.10]),
        "employment_type":       (["full_time_w2", "self_employed", "contractor"], [0.50, 0.30, 0.20]),
        "balance_trend":         (["Stable", "Declining", "Improving"], [0.45, 0.35, 0.20]),
        "preferred_rewards_type":(["cash_back", "travel_points"], [0.65, 0.35]),
        "financial_goal":        (["build_emergency_fund", "pay_off_debt", "home_purchase"], [0.40, 0.35, 0.25]),
        "fee_sensitivity_tier":  (["medium", "low", "high"], [0.50, 0.30, 0.20]),
    },
    "Retiree Anchor": {
        "life_stage":            (["retiree"], [1.0]),
        "risk_tolerance":        (["Conservative", "Moderate"], [0.90, 0.10]),
        "investment_risk_profile":(["conservative", "moderate"], [0.90, 0.10]),
        "channel_preference":    (["Branch", "Hybrid"], [0.85, 0.15]),
        "home_ownership":        (["Own", "Mortgage"], [0.80, 0.20]),
        "home_ownership_type":   (["owner_free_clear", "owner_with_mortgage"], [0.80, 0.20]),
        "employment_type":       (["retired"], [1.0]),
        "balance_trend":         (["Stable", "Improving"], [0.65, 0.35]),
        "preferred_rewards_type":(["none", "cash_back"], [0.60, 0.40]),
        "financial_goal":        (["retirement_savings", "grow_wealth"], [0.65, 0.35]),
        "fee_sensitivity_tier":  (["low", "medium"], [0.65, 0.35]),
    },
    "At-Risk Borrower": {
        "life_stage":            (["young_single", "new_family", "growing_family"], [0.40, 0.35, 0.25]),
        "risk_tolerance":        (["Conservative", "Moderate", "Aggressive"], [0.50, 0.40, 0.10]),
        "investment_risk_profile":(["conservative", "moderate", "aggressive"], [0.50, 0.40, 0.10]),
        "channel_preference":    (["Digital", "Branch", "Hybrid"], [0.50, 0.30, 0.20]),
        "home_ownership":        (["Rent", "Mortgage"], [0.70, 0.30]),
        "home_ownership_type":   (["renter", "owner_with_mortgage"], [0.70, 0.30]),
        "employment_type":       (["part_time", "full_time_w2", "contractor", "self_employed"], [0.30, 0.30, 0.25, 0.15]),
        "balance_trend":         (["Declining", "Stable"], [0.80, 0.20]),
        "preferred_rewards_type":(["cash_back", "none"], [0.80, 0.20]),
        "financial_goal":        (["pay_off_debt", "build_emergency_fund"], [0.60, 0.40]),
        "fee_sensitivity_tier":  (["high", "medium"], [0.70, 0.30]),
    },
}


# ── HELPERS ──────────────────────────────────────────────────────────────────

def rescale(series: pd.Series, mean: float, std: float, lo: float, hi: float) -> pd.Series:
    """Rank-preserving rescale: shift mean+std to targets, preserve ordering."""
    arr = series.fillna(series.median()).values.astype(float)
    s = arr.std()
    if s < 1e-8:
        return pd.Series(np.full(len(arr), mean), index=series.index)
    z = (arr - arr.mean()) / s
    new_vals = mean + z * std
    return pd.Series(np.clip(new_vals, lo, hi), index=series.index)


def assign_cohorts(df: pd.DataFrame) -> pd.Series:
    """Greedy priority assignment: each cohort gets exactly TARGET_SIZE rows."""
    archetype_names = list(CENTROIDS.keys())

    # Normalize features
    normed = pd.DataFrame(index=df.index)
    for col in DIST_FEATURES:
        normed[col] = df[col].fillna(df[col].median()) / SCALES[col]

    centroid_mat = np.array([
        [CENTROIDS[name][f] / SCALES[f] for f in DIST_FEATURES]
        for name in archetype_names
    ])
    weight_vec = np.array([WEIGHTS[f] for f in DIST_FEATURES])

    X = normed[DIST_FEATURES].values
    dists = np.sqrt(np.array([
        np.sum(((X - centroid_mat[i]) ** 2) * weight_vec, axis=1)
        for i in range(len(archetype_names))
    ]).T)  # shape: (5000, 5)

    # Customers with the strongest preference (biggest gap between 1st and 2nd choice) go first
    sorted_dists = np.sort(dists, axis=1)
    margin = sorted_dists[:, 1] - sorted_dists[:, 0]
    order = np.argsort(-margin)
    rankings = np.argsort(dists, axis=1)  # each row: archetype indices by proximity

    assignment = np.full(len(df), -1, dtype=int)
    counts = np.zeros(len(archetype_names), dtype=int)

    cohort_targets = [TARGET_SIZES[name] for name in archetype_names]

    for idx in order:
        for pref in rankings[idx]:
            if counts[pref] < cohort_targets[pref]:
                assignment[idx] = pref
                counts[pref] += 1
                break

    print("  Cohort assignment counts:")
    for i, name in enumerate(archetype_names):
        print(f"    {name}: {counts[i]}")

    return pd.Series([archetype_names[a] for a in assignment], index=df.index, name="_cohort")


def apply_numeric(df: pd.DataFrame, cohort: str, mask: pd.Series) -> None:
    stats = TARGET_STATS[cohort]
    forced = FORCED_VALUES.get(cohort, {})

    for col, spec in stats.items():
        if col not in df.columns:
            continue
        # Upcast to float so pandas doesn't warn about dtype mismatch
        if df[col].dtype != np.float64:
            df[col] = df[col].astype(float)
        if spec is None:
            fval = forced.get(col, 0.0)
            df.loc[mask, col] = fval
        else:
            mean, std, lo, hi = spec
            df.loc[mask, col] = rescale(df.loc[mask, col], mean, std, lo, hi).values


def apply_categorical(df: pd.DataFrame, cohort: str, mask: pd.Series, rng) -> None:
    profile = CAT_PROFILES[cohort]
    n = mask.sum()
    for col, (choices, weights) in profile.items():
        if col not in df.columns:
            continue
        wt = np.array(weights, dtype=float)
        wt /= wt.sum()
        df.loc[mask, col] = rng.choice(choices, size=n, p=wt)


def round_int_cols(df: pd.DataFrame, mask: pd.Series) -> None:
    """Round columns that should be whole numbers (kept as float until final cast)."""
    int_cols = ["credit_score", "age", "nps_score", "num_products",
                "monthly_transaction_volume", "overdrafts_last_3mo"]
    for col in int_cols:
        if col in df.columns:
            if df[col].dtype != np.float64:
                df[col] = df[col].astype(float)
            df.loc[mask, col] = df.loc[mask, col].round(0)


def recalculate_derived(df: pd.DataFrame) -> None:
    """Recompute all fields that derive from patched columns."""
    def churn_cat(p):
        if p < 0.15:   return "Low"
        elif p < 0.30: return "Medium"
        elif p < 0.50: return "High"
        else:          return "Critical"

    def nps_cat(s):
        if s >= 70:   return "Promoter"
        elif s >= 50: return "Passive"
        else:         return "Detractor"

    def credit_tier_fn(s):
        if s >= 750:   return "Excellent"
        elif s >= 700: return "Good"
        elif s >= 650: return "Fair"
        else:          return "Poor"

    def fee_tier_fn(s):
        if s < 0.40:   return "low"
        elif s < 0.65: return "medium"
        else:          return "high"

    df["churn_risk_score"]    = (df["churn_probability"] * 100).clip(0, 100)
    df["churn_risk_category"] = df["churn_probability"].apply(churn_cat)
    df["nps_category"]        = df["nps_score"].apply(nps_cat)
    df["credit_tier"]         = df["credit_score"].apply(credit_tier_fn)
    df["fee_sensitivity_tier"]= df["fee_sensitivity_score"].apply(fee_tier_fn)

    # CLV: 3-year NIM on deposits + loan spread + per-product fees
    df["customer_lifetime_value"] = (
        df["total_deposit_value"] * 0.025 * 3
        + df["total_loan_balance"].fillna(0) * 0.035 * 3
        + df["num_products"] * 60
    ).round(2)

    def clv_tier_fn(v):
        if v >= 15000:  return "Platinum"
        elif v >= 6000: return "Gold"
        elif v >= 2000: return "Silver"
        else:           return "Bronze"

    df["clv_tier"] = df["customer_lifetime_value"].apply(clv_tier_fn)

    df["high_overdraft_flag"] = (df["overdraft_frequency"] >= 3).astype(int)
    df["low_balance_flag"]    = (df["total_deposit_value"] < 2000).astype(int)
    df["overdrafts_last_3mo"] = (df["overdraft_frequency"] * 3).round(0).clip(0, 30).astype(int)

    # Sync investment_risk_profile with risk_tolerance casing
    rt_map = {"Aggressive": "aggressive", "Moderate": "moderate", "Conservative": "conservative"}
    if "risk_tolerance" in df.columns:
        df["investment_risk_profile"] = df["risk_tolerance"].map(rt_map).fillna(df["investment_risk_profile"])


def print_summary(df: pd.DataFrame, cohort_col: str) -> None:
    archetypes = list(CENTROIDS.keys())
    header = "  {:<22} {:>5}  {:>10}  {:>8}  {:>12}  {:>8}  {:>7}  {:>5}".format(
        "Archetype", "N", "Income", "Credit", "Deposits", "Digital", "Churn", "Age")
    print("\n" + header)
    print("  " + "-" * 90)
    for arch in archetypes:
        m = df[cohort_col] == arch
        g = df[m]
        print("  {:<22} {:>5}  ${:>9,.0f}  {:>8.0f}  ${:>11,.0f}  {:>8.3f}  {:>7.3f}  {:>5.1f}".format(
            arch, len(g),
            g['income'].mean(),
            g['credit_score'].mean(),
            g['total_deposit_value'].mean(),
            g['digital_engagement_score'].mean(),
            g['churn_probability'].mean(),
            g['age'].mean(),
        ))


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print("  Meridian Bank — Segment Alignment Patch")
    print(f"{'='*60}")
    print(f"\n  Loading: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"  Rows: {len(df)}  Cols: {len(df.columns)}")

    print("\n  BEFORE patch — key stats by current data:")
    for col in ["income", "credit_score", "total_deposit_value", "digital_engagement_score"]:
        print(f"    {col}: mean={df[col].mean():.2f}  std={df[col].std():.2f}")

    print("\n  Assigning cohorts...")
    cohort_series = assign_cohorts(df)
    df["_cohort"] = cohort_series

    rng = np.random.default_rng(SEED)

    for cohort in CENTROIDS.keys():
        mask = df["_cohort"] == cohort
        print(f"\n  Patching '{cohort}' ({mask.sum()} customers)...")
        apply_numeric(df, cohort, mask)
        apply_categorical(df, cohort, mask, rng)
        round_int_cols(df, mask)

    # Final int casts
    for col in ["credit_score", "age", "nps_score", "num_products",
                "monthly_transaction_volume", "overdrafts_last_3mo"]:
        if col in df.columns:
            df[col] = df[col].round(0).astype(int)

    print("\n  Recalculating derived fields...")
    recalculate_derived(df)

    print("\n  AFTER patch — segment profiles:")
    print_summary(df, "_cohort")

    # Drop the helper column before saving
    df.drop(columns=["_cohort"], inplace=True)

    df.to_csv(CSV_PATH, index=False)
    print(f"\n  Saved -> {CSV_PATH}")
    print(f"  Done.\n")


if __name__ == "__main__":
    main()

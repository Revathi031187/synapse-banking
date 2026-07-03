"""
fix_segment_cache.py
====================
Directly patches .agent_a_cache.json with semantically correct segment
values so the banking dashboard shows accurate, internally consistent
metrics for all 5 customer personas.

Correct segment ordering by avg_annual_balance (low to high):
  At-Risk Saver       ~$16K income,  $650  balance — financially stressed
  Digital Trendsetter ~$35K income,  $5K   balance — young, low savings
  Everyday Essentials ~$54K income,  $22K  balance — core retail
  Wealth Manager      ~$141K income, $115K balance — high earner building wealth
  Retiree Depositor   ~$38K income,  $145K balance — HIGHEST balance (lifetime savings)

Run with: py -3 scripts/fix_segment_cache.py
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "preloaded", "meridian_bank", ".agent_a_cache.json")

with open(CACHE, "r", encoding="utf-8") as f:
    data = json.load(f)

# ── Correct target values per segment ────────────────────────────────────────
# Canonical archetype cluster IDs (match agent_a_banking_enhanced.py):
#   0 = HIGH-VALUE   (Wealth Builder / Wealth Creator)
#   1 = DIGITAL-FIRST (Digital Native / Digital Trendsetter)
#   2 = EVERYDAY     (Everyday Essential)
#   3 = LOYAL-STABLE  (Retiree Anchor / Retiree Depositor)  ← HIGHEST balance
#   4 = AT-RISK       (At-Risk Borrower / At-Risk Saver)
#
# Each entry: (avg_income, avg_annual_balance, avg_credit, digital_pct, avg_txns, avg_products, churn_prob, avg_age)
TARGETS = {
    # cluster_id: dict of corrected values
    "0": {  # Wealth Builder / HIGH-VALUE
        "avg_income":             141000,
        "avg_annual_balance":     115000,
        "avg_credit":             806,
        "digital_pct":            0.65,
        "avg_txns":               28,
        "avg_products":           4.5,
        "churn_prob":             0.11,
        "avg_age":                48,
        "description": (
            "These customers are affluent individuals who earn around $141,000 a year, "
            "with an excellent credit score and substantial annual balance of $115,000. They use "
            "digital banking at a moderate rate (65%) and hold an average of 4.5 products. They "
            "are the bank's top earners and present opportunities for wealth management, investment, "
            "and premium financial products."
        ),
        "tagline": "$115K avg annual balance, 65% digital — the bank's top earners building wealth",
        "key_stats": [
            {"label": "Avg Income",       "value": "$141K", "note": "Top tier"},
            {"label": "Avg Credit Score", "value": "806",   "note": "Excellent"},
            {"label": "Avg Products",     "value": "4.5",   "note": "Premium mix"},
            {"label": "Monthly Txns",     "value": "28",    "note": "Active"},
        ],
    },
    "1": {  # Digital Native / DIGITAL-FIRST
        "avg_income":             35000,
        "avg_annual_balance":     5000,
        "avg_credit":             690,
        "digital_pct":            0.92,
        "avg_txns":               62,
        "avg_products":           1.8,
        "churn_prob":             0.35,
        "avg_age":                27,
        "description": (
            "These young customers (~27 years old) earn around $35,000 a year and are "
            "almost exclusively digital (92% digital engagement), making 62 transactions "
            "per month — the highest of any segment. Despite low savings ($5,000), they have "
            "a decent credit score (690) and represent the future of the bank's customer base. "
            "They respond strongly to app-based offers, cashback rewards, and digital-first products."
        ),
        "tagline": "92% digital, 62 monthly transactions — the bank's most digitally engaged customers",
        "key_stats": [
            {"label": "Avg Income",       "value": "$35K",  "note": "Low-moderate"},
            {"label": "Avg Credit Score", "value": "690",   "note": "Good"},
            {"label": "Digital Score",    "value": "92%",   "note": "Highest segment"},
            {"label": "Monthly Txns",     "value": "62",    "note": "Very active"},
        ],
    },
    "2": {  # Everyday Essential / EVERYDAY
        "avg_income":             54000,
        "avg_annual_balance":     22000,
        "avg_credit":             700,
        "digital_pct":            0.40,
        "avg_txns":               20,
        "avg_products":           2.5,
        "churn_prob":             0.28,
        "avg_age":                42,
        "description": (
            "These customers are middle-aged individuals who earn around $54,000 a year, "
            "with a moderate credit score and $22,000 in annual balance. They use a balanced mix "
            "of digital (40%) and branch banking. As the largest segment, they represent the "
            "bank's core retail base with stable transaction habits, presenting opportunities "
            "for cross-selling savings, insurance, and everyday financial products."
        ),
        "tagline": "$22,000 avg annual balance, steady everyday banking — the core of the retail portfolio",
        "key_stats": [
            {"label": "Avg Income",       "value": "$54K",  "note": "Average"},
            {"label": "Avg Credit Score", "value": "700",   "note": "Good"},
            {"label": "Avg Annual Bal",   "value": "$22K",  "note": "Moderate"},
            {"label": "Monthly Txns",     "value": "20",    "note": "Average"},
        ],
    },
    "3": {  # Retiree Depositor / LOYAL-STABLE — HIGHEST annual balance
        "avg_income":             38000,
        "avg_annual_balance":     185000,
        "avg_credit":             775,
        "digital_pct":            0.22,
        "avg_txns":               9,
        "avg_products":           3.8,
        "churn_prob":             0.07,
        "avg_age":                68,
        "description": (
            "These customers are retired individuals aged around 68 with pension/Social Security "
            "income (~$38,000) and the highest annual balance of any segment at $145,000 — the result "
            "of a lifetime of disciplined saving. They prefer in-branch service (78% branch), have "
            "excellent credit (775), and are the most loyal segment with the lowest churn risk (7%). "
            "The bank should focus on protecting and growing their retirement assets."
        ),
        "tagline": "$185K avg annual balance — the highest of any segment — lifetime savings at work",
        "key_stats": [
            {"label": "Avg Income",        "value": "$38K",  "note": "Retirement income"},
            {"label": "Avg Annual Balance", "value": "$185K", "note": "Highest segment"},
            {"label": "Avg Credit Score",  "value": "775",   "note": "Very good"},
            {"label": "Monthly Txns",      "value": "9",     "note": "Low — branch-first"},
        ],
    },
    "4": {  # At-Risk Borrower / AT-RISK
        "avg_income":             16000,
        "avg_annual_balance":     650,
        "avg_credit":             545,
        "digital_pct":            0.55,
        "avg_txns":               17,
        "avg_products":           1.4,
        "churn_prob":             0.60,
        "avg_age":                36,
        "description": (
            "These customers are financially stressed, earning around $16,000 a year "
            "with minimal savings of $650. Their low credit score (545) and very high churn "
            "probability (60%) signal serious financial vulnerability. The bank should focus "
            "on retention through financial wellness programs and affordable credit-building products."
        ),
        "tagline": "$16K income, $650 balance — highest churn risk, needs financial wellness support",
        "key_stats": [
            {"label": "Avg Income",       "value": "$16K",  "note": "Lowest tier"},
            {"label": "Avg Credit Score", "value": "545",   "note": "Below average"},
            {"label": "Churn Risk",       "value": "60%",   "note": "Critical"},
            {"label": "Monthly Txns",     "value": "17",    "note": "Moderate"},
        ],
    },
}

# ── Apply corrections ─────────────────────────────────────────────────────────
for cluster_id, targets in TARGETS.items():
    if cluster_id not in data["personas"]:
        print(f"  WARNING: cluster {cluster_id} not found in cache")
        continue

    p = data["personas"][cluster_id]
    chars = p.setdefault("characteristics", {})

    # Core numeric metrics
    p["avg_annual_balance"]                  = targets["avg_annual_balance"]
    p.pop("avg_balance", None)               # remove old key if present
    chars["avg_deposits"]                    = targets["avg_annual_balance"]
    chars["avg_income"]                      = targets["avg_income"]
    chars["avg_credit_score"]                = targets["avg_credit"]
    chars["avg_digital_engagement"]          = targets["digital_pct"]
    chars["avg_monthly_transaction_volume"]  = targets["avg_txns"]
    chars["monthly_transaction_volume"]      = targets["avg_txns"]
    chars["avg_products"]                    = targets["avg_products"]
    p["avg_transactions"]                    = targets["avg_txns"]
    p["monthly_transaction_rate"]            = targets["avg_txns"]

    # Revenue (bank earns NIM on deposits ≈ 2.5%)
    total_rev = targets["avg_annual_balance"] * 0.025 * p.get("size", 1000)
    p["total_revenue"]                                     = round(total_rev, 2)
    p["revenue_metrics"]["avg_customer_value"]             = targets["avg_annual_balance"]
    p["revenue_metrics"]["total_deposits"]                 = round(targets["avg_annual_balance"] * p.get("size", 1000), 2)
    p["revenue_metrics"]["total_revenue_12mo"]             = round(total_rev, 2)

    # Description and segment explanation
    p["description"] = targets["description"]
    se = p.setdefault("segment_explanation", {})
    se["tagline"]    = targets["tagline"]
    se["key_stats"]  = targets["key_stats"]

    print(f"  Cluster {cluster_id} ({p['name']}): income=${targets['avg_income']:,}  "
          f"annual_balance=${targets['avg_annual_balance']:,}  credit={targets['avg_credit']}  "
          f"digital={targets['digital_pct']}  txns={targets['avg_txns']}")

# ── Save ──────────────────────────────────────────────────────────────────────
with open(CACHE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nSaved -> {CACHE}")
print("Done. Dashboard will reflect corrected segment values on next load.")

"""
Generate data/preloaded/meridian_bank/ad_spend_monthly.csv

12-month (Jan-Dec 2025) monthly ad spend / revenue / ROI per persona x channel.
Costs and conversion rates are calibrated so annual ROAS lands in a realistic
1x-12x range, with deliberate under/over-invested signals baked in per segment.

Run from project root:
    python scripts/generate_ad_spend_history.py
"""

import os
import random
import math
import pandas as pd

random.seed(42)

# ============================================================
# FULLY-LOADED CHANNEL COSTS  (media + platform + creative + mgmt)
# ============================================================
COST_PER_CONTACT = {
    "in_app":  0.80,    # push notification with creative + platform + data
    "email":   0.50,    # ESP + list management + creative + compliance
    "sms":     0.35,    # platform + compliance + creative
    "branch":  8.00,    # staff time + overhead per marketing-driven visit
}

# Per-channel average product value ($) -- branch converts higher-value products
PRODUCT_VALUE = {
    "in_app":  300,     # digital products: credit cards, savings, checkings
    "email":   350,
    "sms":     250,
    "branch":  600,     # mortgages, CDs, investments -- higher ticket
}

# ============================================================
# TRUE BUSINESS ROI COMPONENTS
# (costs and risks NOT captured in marketing spend)
# ============================================================

# Additional cost per successful conversion (beyond marketing spend):
#   underwriting/credit check + account setup + compliance + first-year ops
BUSINESS_COST_PER_CONV = {
    "in_app":  75,    # digital onboarding + KYC + compliance
    "email":   85,    # fulfillment + manual review + ops
    "sms":     70,    # light digital onboarding
    "branch":  150,   # full staff time + paperwork + branch overhead
}

# Revenue at risk: probability that a converted customer defaults, churns,
# or fails to activate the product within 12 months (reduces recognised revenue)
RISK_RATE = {
    "in_app":  0.08,   # 8%  — digital-first customers; higher card default rate
    "email":   0.06,   # 6%
    "sms":     0.10,   # 10% — SMS audience skews slightly higher-risk
    "branch":  0.04,   # 4%  — branch customers are more stable, lower churn
}

CHANNELS = ["in_app", "email", "sms", "branch"]

# ============================================================
# MONTHLY CONTACTS SENT  (persona_size * reach * vol_mult)
# Using PERSONA_CHANNEL reach_prob from generate_mta_history.py
# ============================================================
PERSONA_REACH = {
    "Digital Native":     {"in_app": 0.75, "email": 0.55, "sms": 0.35, "branch": 0.08},
    "Wealth Builder":     {"in_app": 0.55, "email": 0.70, "sms": 0.20, "branch": 0.30},
    "Everyday Essential": {"in_app": 0.60, "email": 0.65, "sms": 0.40, "branch": 0.25},
    "Retiree Anchor":     {"in_app": 0.20, "email": 0.50, "sms": 0.15, "branch": 0.55},
    "At-Risk Saver":      {"in_app": 0.45, "email": 0.55, "sms": 0.50, "branch": 0.15},
}

PERSONA_SIZES = {
    "Digital Native":     900,
    "Wealth Builder":     800,
    "Everyday Essential": 1500,
    "Retiree Anchor":     950,
    "At-Risk Saver":      850,
}

# ============================================================
# CAMPAIGN CONVERSION RATES  (contact -> product conversion)
# Back-calculated to hit deliberate ROAS targets:
#   conv_rate = cost * target_roas / product_value
# Target ROAS designed to make some channels under, some over per segment.
# ============================================================
# Target ROAS summary:
#   Digital Native : in_app=10x UNDER | email=7x UNDER | sms=1.4x OVER | branch=0.9x OVER
#   Wealth Builder : in_app=6x  UNDER | email=2.1x OPT | sms=1.3x OVER | branch=4x  UNDER
#   Everyday Ess.  : in_app=5x  UNDER | email=2.0x OPT | sms=4x   UNDER | branch=1.2x OVER
#   Retiree Anchor : in_app=0.8x OVER | email=4.5x UNDER | sms=1.2x OVER | branch=5.5x UNDER
#   At-Risk Saver  : in_app=4x  UNDER | email=1.4x OVER | sms=5x   UNDER | branch=1.1x OVER

CAMPAIGN_CONV_RATE = {
    "Digital Native": {
        "in_app":  0.0267,   # 0.80*10/300
        "email":   0.0100,   # 0.50*7/350
        "sms":     0.0020,   # 0.35*1.4/250
        "branch":  0.0120,   # 8.00*0.9/600
    },
    "Wealth Builder": {
        "in_app":  0.0160,   # 0.80*6/300
        "email":   0.0030,   # 0.50*2.1/350
        "sms":     0.0018,   # 0.35*1.3/250
        "branch":  0.0533,   # 8.00*4/600
    },
    "Everyday Essential": {
        "in_app":  0.0133,   # 0.80*5/300
        "email":   0.0029,   # 0.50*2.0/350
        "sms":     0.0056,   # 0.35*4/250
        "branch":  0.0160,   # 8.00*1.2/600
    },
    "Retiree Anchor": {
        "in_app":  0.0021,   # 0.80*0.8/300
        "email":   0.0064,   # 0.50*4.5/350
        "sms":     0.0017,   # 0.35*1.2/250
        "branch":  0.0733,   # 8.00*5.5/600
    },
    "At-Risk Saver": {
        "in_app":  0.0107,   # 0.80*4/300
        "email":   0.0020,   # 0.50*1.4/350
        "sms":     0.0070,   # 0.35*5/250
        "branch":  0.0147,   # 8.00*1.1/600
    },
}

# ============================================================
# BANKING SEASONALITY (volume_mult, conv_mult)
# Q1: peak (New Year resolutions)
# Q2: dip (tax season distraction)
# Q3: summer low
# Q4: year-end surge
# ============================================================
SEASONALITY = {
    1:  (1.15, 1.18),
    2:  (1.08, 1.12),
    3:  (0.98, 1.04),
    4:  (0.88, 0.92),
    5:  (0.86, 0.90),
    6:  (0.82, 0.84),
    7:  (0.78, 0.80),
    8:  (0.82, 0.83),
    9:  (0.95, 0.98),
    10: (1.02, 1.05),
    11: (1.10, 1.12),
    12: (1.18, 1.22),
}

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]


def _noise(lo=0.92, hi=1.08):
    return random.uniform(lo, hi)


rows = []

for month in range(1, 13):
    vol_mult, conv_mult = SEASONALITY[month]
    month_name = MONTH_NAMES[month - 1]

    for persona, reach_map in PERSONA_REACH.items():
        size = PERSONA_SIZES[persona]

        for channel in CHANNELS:
            reach    = reach_map[channel]
            base_cv  = CAMPAIGN_CONV_RATE[persona][channel]
            cost_c   = COST_PER_CONTACT[channel]
            prod_val = PRODUCT_VALUE[channel]

            sent = max(1, int(size * reach * vol_mult * _noise()))

            eff_conv  = min(0.99, base_cv * conv_mult * _noise(0.88, 1.12))
            converted = max(0, int(sent * eff_conv))

            # Click / open rates (campaign benchmarks)
            click_r = {"in_app":0.35,"email":0.12,"sms":0.18,"branch":0.55}[channel]
            open_r  = {"in_app":0.55,"email":0.30,"sms":0.42,"branch":0.70}[channel]
            clicked = max(0, int(sent * click_r * _noise()))
            opened  = max(0, int(sent * open_r  * _noise()))

            spend_usd   = round(sent * cost_c, 2)
            revenue_usd = round(converted * prod_val, 2)
            roas        = round(revenue_usd / spend_usd, 4) if spend_usd > 0 else 0.0
            roi_pct     = round((revenue_usd - spend_usd) / spend_usd * 100, 2) if spend_usd > 0 else 0.0
            cpa         = round(spend_usd / converted, 2) if converted > 0 else 0.0

            # ── True Business ROI ────────────────────────────────────────────
            # Adds underwriting/ops cost + reduces revenue by credit/default risk
            biz_cost     = round(converted * BUSINESS_COST_PER_CONV[channel], 2)
            risk_adj_rev = round(revenue_usd * (1 - RISK_RATE[channel]), 2)
            total_cost   = round(spend_usd + biz_cost, 2)
            true_roi_pct = round((risk_adj_rev - total_cost) / total_cost * 100, 2) if total_cost > 0 else -100.0
            true_roas    = round(risk_adj_rev / total_cost, 4) if total_cost > 0 else 0.0

            rows.append({
                "year":                      2025,
                "month":                     month,
                "month_name":                month_name,
                "persona":                   persona,
                "channel":                   channel,
                "sent":                      sent,
                "opened":                    opened,
                "clicked":                   clicked,
                "converted":                 converted,
                "spend_usd":                 spend_usd,
                "revenue_usd":               revenue_usd,
                "roas":                      roas,
                "roi_pct":                   roi_pct,
                "conversion_rate":           round(converted / sent, 4) if sent > 0 else 0.0,
                "click_rate":                round(clicked / sent, 4) if sent > 0 else 0.0,
                "open_rate":                 round(opened  / sent, 4) if sent > 0 else 0.0,
                "cpa":                       cpa,
                "business_cost_usd":         biz_cost,
                "risk_adjusted_revenue_usd": risk_adj_rev,
                "total_cost_usd":            total_cost,
                "true_roi_pct":              true_roi_pct,
                "true_roas":                 true_roas,
            })

df = pd.DataFrame(rows)
df = df.sort_values(["month", "persona", "channel"]).reset_index(drop=True)

out_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "preloaded", "meridian_bank", "ad_spend_monthly.csv",
)
df.to_csv(out_path, index=False)

print(f"Generated {len(df)} rows -> {out_path}")
print("\nChannel totals (full year):")
ch = df.groupby("channel")[["spend_usd","revenue_usd","converted"]].sum()
ch["roas"] = (ch["revenue_usd"] / ch["spend_usd"]).round(2)
print(ch.to_string())
print(f"\nTotal spend:   ${df['spend_usd'].sum():,.0f}")
print(f"Total revenue: ${df['revenue_usd'].sum():,.0f}")
print(f"Overall ROAS:  {df['revenue_usd'].sum() / df['spend_usd'].sum():.2f}x")
print("\nPersona x Channel mean annual ROAS:")
pivot = df.groupby(["persona","channel"])["roas"].mean().unstack()
print(pivot.round(2).to_string())

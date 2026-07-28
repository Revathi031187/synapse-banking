#!/usr/bin/env python3
"""
Generate synthetic A/B experiment data for Meridian Bank offer selection.

Usage:
    python scripts/generate_offer_experiments.py
    python scripts/generate_offer_experiments.py --verify

Produces: data/config/offer_experiments.json

Each experiment simulates a randomized controlled trial where one product is
offered to customers in the same persona segment using different offer variants
plus a holdout group (no offer). Conversion lift is computed via Z-test
(proportions_ztest). Only statistically significant variants (p < 0.05) can
become the winning offer. If no variant is significant, no_offer_recommended=True.
"""
import json
import math
import os
import sys
from collections import defaultdict

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFERS_PATH = os.path.join(ROOT, "data", "config", "product_offers.json")
OUTPUT_PATH = os.path.join(ROOT, "data", "config", "offer_experiments.json")

ALPHA = 0.05       # significance threshold
N_PER_GROUP = 400  # exposures per holdout / per variant

# ── Product name lookup ───────────────────────────────────────────────────────
PRODUCT_NAMES = {
    "MRD_P001": "Meridian Essential Checking",
    "MRD_P002": "Meridian Plus Checking",
    "MRD_P003": "Meridian Prestige Checking",
    "MRD_P004": "Meridian Basic Savings",
    "MRD_P005": "Meridian High-Yield Savings",
    "MRD_P007": "Meridian 12-Month CD",
    "MRD_P009": "Meridian Cash Back Card",
    "MRD_P010": "Meridian Rewards Visa",
    "MRD_P011": "Meridian Platinum Card",
    "MRD_P013": "Meridian Auto Loan",
    "MRD_P014": "Meridian Personal Loan",
    "MRD_P017": "Meridian 30yr Fixed Mortgage",
    "MRD_P019": "Meridian Traditional IRA",
    "MRD_P020": "Meridian Roth IRA",
    "MRD_B001": "Meridian Business Essential Checking",
    "MRD_B004": "Meridian Business Line of Credit",
    "MRD_A001": "Meridian Farm Operating Line",
    "MRD_P006": "Meridian Money Market",
    "MRD_P008": "Meridian 24-Month CD",
    "MRD_P012": "Meridian Credit Builder Card",
    "MRD_P015": "Meridian Home Equity Loan",
    "MRD_P016": "Meridian HELOC",
    "MRD_P018": "Meridian FHA Mortgage",
    "MRD_B002": "Meridian Business Plus Checking",
    "MRD_B003": "Meridian Business Premium Savings",
    "MRD_B005": "Meridian Business Basic Checking",
    "MRD_A002": "Meridian Agricultural Equipment Loan",
    "MRD_A003": "Meridian Agricultural Land Improvement Loan",
}

# ── Experiment definitions ────────────────────────────────────────────────────
# Each entry: (product_id, persona, holdout_rate, variants)
# variants: list of (offer_id, conversion_rate, channel_override)
# Rates near holdout with delta < ~2pp at n=400 → p > 0.05 → NO_OFFER
EXPERIMENT_CONFIGS = [
    # ── Essential Checking (MRD_P001) ─────────────────────────────────────────
    ("MRD_P001", "Digital Native",      0.140, [
        ("MRD_OFF_001", 0.230, "in_app"),
        ("MRD_OFF_002", 0.175, "in_app"),
    ]),
    ("MRD_P001", "Everyday Essential",  0.130, [
        ("MRD_OFF_001", 0.210, "in_app"),
        ("MRD_OFF_002", 0.162, "email"),
    ]),
    ("MRD_P001", "At-Risk Borrower",    0.110, [
        ("MRD_OFF_001", 0.180, "in_app"),
        ("MRD_OFF_002", 0.140, "email"),
    ]),
    # ── Plus Checking (MRD_P002) ──────────────────────────────────────────────
    ("MRD_P002", "Digital Native",      0.140, [
        ("MRD_OFF_003", 0.200, "email"),
        ("MRD_OFF_004", 0.225, "in_app"),
    ]),
    ("MRD_P002", "Everyday Essential",  0.120, [
        ("MRD_OFF_003", 0.175, "email"),
        ("MRD_OFF_004", 0.190, "in_app"),
    ]),
    ("MRD_P002", "Wealth Builder",      0.140, [
        ("MRD_OFF_003", 0.220, "email"),
        ("MRD_OFF_004", 0.250, "in_app"),
    ]),
    # ── Prestige Checking (MRD_P003) ──────────────────────────────────────────
    ("MRD_P003", "Wealth Builder",      0.080, [
        ("MRD_OFF_005", 0.180, "branch"),
        ("MRD_OFF_006", 0.135, "in_app"),
    ]),
    ("MRD_P003", "Digital Native",      0.080, [   # NO_OFFER — poor persona fit
        ("MRD_OFF_005", 0.090, "branch"),
        ("MRD_OFF_006", 0.088, "in_app"),
    ]),
    # ── Basic Savings (MRD_P004) ──────────────────────────────────────────────
    ("MRD_P004", "Everyday Essential",  0.070, [
        ("MRD_OFF_036", 0.130, "in_app"),
        ("MRD_OFF_037", 0.100, "email"),
    ]),
    ("MRD_P004", "Digital Native",      0.070, [
        ("MRD_OFF_036", 0.120, "in_app"),
        ("MRD_OFF_037", 0.095, "email"),
    ]),
    ("MRD_P004", "At-Risk Borrower",    0.060, [   # NO_OFFER — marginal uplift
        ("MRD_OFF_036", 0.065, "in_app"),
        ("MRD_OFF_037", 0.068, "email"),
    ]),
    # ── High-Yield Savings (MRD_P005) ─────────────────────────────────────────
    ("MRD_P005", "Wealth Builder",      0.080, [
        ("MRD_OFF_007", 0.160, "email"),
        ("MRD_OFF_008", 0.120, "in_app"),
    ]),
    ("MRD_P005", "Everyday Essential",  0.070, [
        ("MRD_OFF_007", 0.130, "email"),
        ("MRD_OFF_008", 0.100, "in_app"),
    ]),
    ("MRD_P005", "Retiree Anchor",      0.090, [
        ("MRD_OFF_007", 0.170, "email"),
        ("MRD_OFF_008", 0.130, "in_app"),
    ]),
    # ── 12-Month CD (MRD_P007) ────────────────────────────────────────────────
    ("MRD_P007", "Retiree Anchor",      0.090, [
        ("MRD_OFF_009", 0.160, "email"),
        ("MRD_OFF_010", 0.145, "branch"),
    ]),
    ("MRD_P007", "Wealth Builder",      0.080, [
        ("MRD_OFF_009", 0.150, "email"),
        ("MRD_OFF_010", 0.185, "branch"),
    ]),
    # ── Cash Back Card (MRD_P009) ─────────────────────────────────────────────
    ("MRD_P009", "Digital Native",      0.100, [
        ("MRD_OFF_011", 0.200, "in_app"),
        ("MRD_OFF_012", 0.160, "email"),
        ("MRD_OFF_013", 0.150, "in_app"),
    ]),
    ("MRD_P009", "Everyday Essential",  0.090, [
        ("MRD_OFF_011", 0.170, "in_app"),
        ("MRD_OFF_012", 0.140, "email"),
        ("MRD_OFF_013", 0.130, "in_app"),
    ]),
    ("MRD_P009", "At-Risk Borrower",    0.070, [   # NO_OFFER — marginal uplift
        ("MRD_OFF_011", 0.090, "in_app"),
        ("MRD_OFF_012", 0.082, "email"),
        ("MRD_OFF_013", 0.085, "in_app"),
    ]),
    # ── Rewards Visa (MRD_P010) ───────────────────────────────────────────────
    ("MRD_P010", "Digital Native",      0.100, [
        ("MRD_OFF_014", 0.220, "in_app"),
        ("MRD_OFF_015", 0.180, "in_app"),
        ("MRD_OFF_016", 0.148, "email"),
    ]),
    ("MRD_P010", "Wealth Builder",      0.100, [
        ("MRD_OFF_014", 0.210, "in_app"),
        ("MRD_OFF_015", 0.200, "in_app"),
        ("MRD_OFF_016", 0.168, "email"),
    ]),
    ("MRD_P010", "Everyday Essential",  0.080, [   # NO_OFFER — $95 fee is a barrier
        ("MRD_OFF_014", 0.090, "in_app"),
        ("MRD_OFF_015", 0.094, "in_app"),
        ("MRD_OFF_016", 0.088, "email"),
    ]),
    # ── Platinum Card (MRD_P011) ──────────────────────────────────────────────
    ("MRD_P011", "Wealth Builder",      0.060, [
        ("MRD_OFF_017", 0.160, "in_app"),
        ("MRD_OFF_018", 0.110, "email"),
    ]),
    # ── Auto Loan (MRD_P013) ──────────────────────────────────────────────────
    ("MRD_P013", "Digital Native",      0.070, [
        ("MRD_OFF_019", 0.130, "in_app"),
        ("MRD_OFF_020", 0.118, "email"),
    ]),
    ("MRD_P013", "Everyday Essential",  0.060, [
        ("MRD_OFF_019", 0.110, "in_app"),
        ("MRD_OFF_020", 0.100, "email"),
    ]),
    ("MRD_P013", "At-Risk Borrower",    0.050, [   # NO_OFFER — rate discount minor for this segment
        ("MRD_OFF_019", 0.055, "in_app"),
        ("MRD_OFF_020", 0.058, "email"),
    ]),
    # ── Personal Loan (MRD_P014) ──────────────────────────────────────────────
    ("MRD_P014", "At-Risk Borrower",    0.060, [
        ("MRD_OFF_021", 0.145, "email"),
        ("MRD_OFF_022", 0.110, "in_app"),
    ]),
    ("MRD_P014", "Everyday Essential",  0.060, [
        ("MRD_OFF_021", 0.120, "email"),
        ("MRD_OFF_022", 0.100, "in_app"),
    ]),
    ("MRD_P014", "Retiree Anchor",      0.040, [   # NO_OFFER — retirees rarely take personal loans
        ("MRD_OFF_021", 0.044, "email"),
        ("MRD_OFF_022", 0.043, "in_app"),
    ]),
    # ── Mortgage (MRD_P017) ───────────────────────────────────────────────────
    ("MRD_P017", "Wealth Builder",      0.060, [
        ("MRD_OFF_025", 0.130, "email"),
        ("MRD_OFF_026", 0.110, "branch"),
    ]),
    ("MRD_P017", "Digital Native",      0.050, [
        ("MRD_OFF_025", 0.110, "email"),
        ("MRD_OFF_026", 0.090, "branch"),
    ]),
    ("MRD_P017", "Everyday Essential",  0.050, [
        ("MRD_OFF_025", 0.100, "email"),
        ("MRD_OFF_026", 0.090, "branch"),
    ]),
    ("MRD_P017", "Retiree Anchor",      0.050, [
        ("MRD_OFF_025", 0.104, "email"),
        ("MRD_OFF_026", 0.130, "branch"),  # closing cost credit resonates with retirees
    ]),
    # ── Traditional IRA (MRD_P019) ────────────────────────────────────────────
    ("MRD_P019", "Retiree Anchor",      0.090, [
        ("MRD_OFF_027", 0.170, "email"),
        ("MRD_OFF_028", 0.130, "in_app"),
    ]),
    ("MRD_P019", "Wealth Builder",      0.080, [
        ("MRD_OFF_027", 0.155, "email"),
        ("MRD_OFF_028", 0.120, "in_app"),
    ]),
    # ── Roth IRA (MRD_P020) ───────────────────────────────────────────────────
    ("MRD_P020", "Digital Native",      0.070, [
        ("MRD_OFF_029", 0.150, "in_app"),
        ("MRD_OFF_030", 0.120, "in_app"),
    ]),
    ("MRD_P020", "Wealth Builder",      0.070, [   # NO_OFFER — wealth builder has advisors
        ("MRD_OFF_029", 0.075, "in_app"),
        ("MRD_OFF_030", 0.076, "in_app"),
    ]),
    ("MRD_P020", "Retiree Anchor",      0.050, [   # NO_OFFER — Roth less useful post-retirement
        ("MRD_OFF_029", 0.054, "in_app"),
        ("MRD_OFF_030", 0.053, "in_app"),
    ]),
    # ── Business Checking (MRD_B001) ──────────────────────────────────────────
    ("MRD_B001", "Wealth Builder",      0.090, [
        ("MRD_OFF_031", 0.190, "branch"),
        ("MRD_OFF_032", 0.145, "email"),
    ]),
    # ── Business LOC (MRD_B004) ───────────────────────────────────────────────
    ("MRD_B004", "Wealth Builder",      0.070, [
        ("MRD_OFF_050", 0.140, "email"),
    ]),
    # ── Agricultural LOC (MRD_A001) ───────────────────────────────────────────
    ("MRD_A001", "Everyday Essential",  0.050, [
        ("MRD_OFF_034", 0.110, "branch"),
    ]),
    ("MRD_A001", "At-Risk Borrower",    0.050, [
        ("MRD_OFF_034", 0.100, "branch"),
    ]),
    # ── Money Market (MRD_P006) ───────────────────────────────────────────────
    ("MRD_P006", "Wealth Builder",      0.090, [
        ("MRD_OFF_038", 0.175, "email"),
        ("MRD_OFF_039", 0.205, "email"),
    ]),
    ("MRD_P006", "Retiree Anchor",      0.085, [
        ("MRD_OFF_038", 0.168, "email"),
        ("MRD_OFF_039", 0.140, "branch"),
    ]),
    ("MRD_P006", "Everyday Essential",  0.070, [
        ("MRD_OFF_038", 0.132, "email"),
        ("MRD_OFF_039", 0.108, "in_app"),
    ]),
    # ── 24-Month CD (MRD_P008) ────────────────────────────────────────────────
    ("MRD_P008", "Retiree Anchor",      0.095, [
        ("MRD_OFF_040", 0.182, "email"),
        ("MRD_OFF_041", 0.155, "branch"),
    ]),
    ("MRD_P008", "Wealth Builder",      0.080, [
        ("MRD_OFF_040", 0.162, "email"),
        ("MRD_OFF_041", 0.132, "email"),
    ]),
    ("MRD_P008", "Digital Native",      0.070, [   # NO_OFFER — CD less appealing to digital natives
        ("MRD_OFF_040", 0.075, "in_app"),
        ("MRD_OFF_041", 0.073, "email"),
    ]),
    # ── Credit Builder Card (MRD_P012) ────────────────────────────────────────
    ("MRD_P012", "At-Risk Borrower",    0.080, [
        ("MRD_OFF_042", 0.168, "in_app"),
        ("MRD_OFF_043", 0.148, "email"),
    ]),
    ("MRD_P012", "Everyday Essential",  0.070, [
        ("MRD_OFF_042", 0.148, "in_app"),
        ("MRD_OFF_043", 0.125, "email"),
    ]),
    # ── Home Equity Loan (MRD_P015) ───────────────────────────────────────────
    ("MRD_P015", "Wealth Builder",      0.065, [
        ("MRD_OFF_023", 0.138, "email"),
        ("MRD_OFF_024", 0.118, "branch"),
    ]),
    ("MRD_P015", "Everyday Essential",  0.060, [
        ("MRD_OFF_023", 0.122, "email"),
        ("MRD_OFF_024", 0.098, "branch"),
    ]),
    ("MRD_P015", "Retiree Anchor",      0.055, [   # NO_OFFER — retirees cautious about home equity debt
        ("MRD_OFF_023", 0.060, "email"),
        ("MRD_OFF_024", 0.059, "branch"),
    ]),
    # ── HELOC (MRD_P016) ──────────────────────────────────────────────────────
    ("MRD_P016", "Wealth Builder",      0.070, [
        ("MRD_OFF_044", 0.148, "email"),
        ("MRD_OFF_045", 0.168, "branch"),
    ]),
    ("MRD_P016", "Everyday Essential",  0.065, [
        ("MRD_OFF_044", 0.132, "email"),
        ("MRD_OFF_045", 0.112, "in_app"),
    ]),
    ("MRD_P016", "Digital Native",      0.060, [
        ("MRD_OFF_044", 0.122, "in_app"),
        ("MRD_OFF_045", 0.102, "email"),
    ]),
    # ── FHA Mortgage / First-Time Buyer (MRD_P018) ────────────────────────────
    ("MRD_P018", "Everyday Essential",  0.055, [
        ("MRD_OFF_046", 0.122, "email"),
        ("MRD_OFF_047", 0.098, "branch"),
    ]),
    ("MRD_P018", "Digital Native",      0.050, [
        ("MRD_OFF_046", 0.112, "in_app"),
        ("MRD_OFF_047", 0.088, "email"),
    ]),
    ("MRD_P018", "At-Risk Borrower",    0.045, [
        ("MRD_OFF_046", 0.098, "email"),
        ("MRD_OFF_047", 0.082, "branch"),
    ]),
    ("MRD_P018", "Wealth Builder",      0.050, [   # NO_OFFER — wealth builders use conventional mortgages
        ("MRD_OFF_046", 0.054, "email"),
        ("MRD_OFF_047", 0.052, "branch"),
    ]),
    # ── Business Plus Checking (MRD_B002) ─────────────────────────────────────
    ("MRD_B002", "Wealth Builder",      0.085, [
        ("MRD_OFF_048", 0.172, "branch"),
    ]),
    ("MRD_B002", "Everyday Essential",  0.075, [
        ("MRD_OFF_048", 0.148, "branch"),
    ]),
    # ── Business Premium Savings (MRD_B003) ───────────────────────────────────
    ("MRD_B003", "Wealth Builder",      0.080, [
        ("MRD_OFF_049", 0.162, "email"),
    ]),
    # ── Business Basic Checking (MRD_B005) ────────────────────────────────────
    ("MRD_B005", "Wealth Builder",      0.080, [
        ("MRD_OFF_033", 0.168, "branch"),
    ]),
    ("MRD_B005", "Everyday Essential",  0.070, [
        ("MRD_OFF_033", 0.142, "branch"),
    ]),
    # ── Agricultural Equipment Loan (MRD_A002) ────────────────────────────────
    ("MRD_A002", "Everyday Essential",  0.050, [
        ("MRD_OFF_035", 0.108, "branch"),
    ]),
    # ── Agricultural Land Improvement (MRD_A003) ──────────────────────────────
    ("MRD_A003", "Everyday Essential",  0.050, [
        ("MRD_OFF_051", 0.102, "branch"),
    ]),
]


# ── Z-test (two proportions, one-sided: variant > holdout) ───────────────────

def _ztest_proportions(conv_variant, n_variant, conv_holdout, n_holdout):
    """
    One-sided Z-test: H1 = variant rate > holdout rate.
    Returns (z_stat, p_value).
    Falls back to manual normal approximation if scipy unavailable.
    """
    try:
        from scipy.stats import proportions_ztest  # type: ignore
        z_stat, p_value = proportions_ztest(
            [conv_variant, conv_holdout],
            [n_variant, n_holdout],
            alternative="larger",
        )
        return float(z_stat), float(p_value)
    except ImportError:
        pass

    # Manual fallback: standard z for difference in proportions
    p1 = conv_variant / n_variant if n_variant > 0 else 0
    p2 = conv_holdout / n_holdout if n_holdout > 0 else 0
    p_pool = (conv_variant + conv_holdout) / (n_variant + n_holdout)
    if p_pool <= 0 or p_pool >= 1:
        return 0.0, 1.0
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_variant + 1 / n_holdout))
    if se == 0:
        return 0.0, 1.0
    z_stat = (p1 - p2) / se
    # One-sided p-value from standard normal CDF approximation (Abramowitz & Stegun)
    p_value = _normal_sf(z_stat)
    return z_stat, p_value


def _normal_sf(z):
    """Survival function (1 - CDF) of standard normal — one-sided upper tail."""
    # Abramowitz & Stegun approximation 26.2.17
    t = 1.0 / (1.0 + 0.2316419 * abs(z))
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    cdf = 1.0 - pdf * poly
    return 1.0 - cdf if z >= 0 else cdf


# ── Channel attribution ───────────────────────────────────────────────────────

def _channel_attribution(variants_built, offers_by_id):
    """
    Compute fraction of conversions per channel across all significant variants.
    Winning variant's channel gets majority weight; other channels get residual.
    """
    channel_conv: dict = defaultdict(int)
    total_conv = 0
    for v in variants_built:
        if v["is_significant"]:
            ch = offers_by_id.get(v["offer_id"], {}).get("preferred_channel", "in_app")
            channel_conv[ch] += v["n_converted"]
            total_conv += v["n_converted"]

    if total_conv == 0:
        return {"in_app": 0.25, "email": 0.25, "direct_mail": 0.10, "branch": 0.40}

    # Normalize significant-variant channels
    base: dict = {}
    for ch, cnt in channel_conv.items():
        base[ch] = round(cnt / total_conv, 3)

    # Ensure all four channels appear (minor residual for non-winning channels)
    all_channels = ["in_app", "email", "direct_mail", "branch"]
    residual = 0.05
    total_allocated = sum(base.values())
    for ch in all_channels:
        if ch not in base:
            base[ch] = residual
    # Renormalize
    total_now = sum(base.values())
    return {ch: round(base[ch] / total_now, 3) for ch in all_channels}


# ── Experiment ID builder ─────────────────────────────────────────────────────

def _experiment_id(persona: str, product_id: str) -> str:
    slug = persona.upper().replace(" ", "_").replace("-", "_")
    pid = product_id.replace("_", "")
    return f"EXP_{slug}_{pid}"


# ── Main generation ───────────────────────────────────────────────────────────

def generate(verify: bool = False):
    # Load offers
    with open(OFFERS_PATH, encoding="utf-8") as f:
        all_offers = json.load(f)

    offers_by_id: dict = {o["offer_id"]: o for o in all_offers}

    experiments = []
    no_offer_count = 0

    for product_id, persona, holdout_rate, variant_specs in EXPERIMENT_CONFIGS:
        n_holdout = N_PER_GROUP
        n_conv_holdout = round(holdout_rate * n_holdout)

        # Build variant records
        variants_built = []
        for letter_idx, (offer_id, rate, channel_override) in enumerate(variant_specs):
            offer = offers_by_id.get(offer_id, {})
            variant_label = chr(65 + letter_idx)  # A, B, C ...
            n_v = N_PER_GROUP
            n_conv_v = round(rate * n_v)

            z_stat, p_value = _ztest_proportions(n_conv_v, n_v, n_conv_holdout, n_holdout)
            lift_abs = round(rate - holdout_rate, 4)
            lift_pct = round(lift_abs / holdout_rate * 100, 1) if holdout_rate > 0 else 0.0
            is_sig = bool(p_value < ALPHA and lift_abs > 0)

            variants_built.append({
                "variant_id": variant_label,
                "offer_id": offer_id,
                "offer_name": offer.get("offer_name", offer_id),
                "offer_type": offer.get("offer_type", ""),
                "channel": channel_override or offer.get("preferred_channel", "in_app"),
                "n_exposed": n_v,
                "n_converted": n_conv_v,
                "conversion_rate": round(rate, 4),
                "lift_abs": lift_abs,
                "lift_pct": lift_pct,
                "z_stat": round(z_stat, 4),
                "p_value": round(p_value, 6),
                "is_significant": is_sig,
            })

        # Determine winner: highest significant lift
        sig_variants = [v for v in variants_built if v["is_significant"]]
        if sig_variants:
            winner = max(sig_variants, key=lambda v: v["lift_abs"])
            winning_variant_id = winner["variant_id"]
            winning_offer_id = winner["offer_id"]
            winning_channel = winner["channel"]
            no_offer = False
        else:
            winning_variant_id = None
            winning_offer_id = None
            winning_channel = None
            no_offer = True
            no_offer_count += 1

        channel_attr = _channel_attribution(variants_built, offers_by_id)

        experiment = {
            "experiment_id": _experiment_id(persona, product_id),
            "product_id": product_id,
            "product_name": PRODUCT_NAMES.get(product_id, product_id),
            "persona": persona,
            "experiment_date": "2025-Q1",
            "n_per_group": N_PER_GROUP,
            "total_n": N_PER_GROUP * (1 + len(variant_specs)),
            "holdout": {
                "n_exposed": n_holdout,
                "n_converted": n_conv_holdout,
                "conversion_rate": round(holdout_rate, 4),
            },
            "variants": variants_built,
            "winning_variant_id": winning_variant_id,
            "winning_offer_id": winning_offer_id,
            "winning_channel": winning_channel,
            "no_offer_recommended": no_offer,
            "channel_attribution": channel_attr,
        }
        experiments.append(experiment)

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(experiments, f, indent=2, ensure_ascii=False)

    total = len(experiments)
    winners = total - no_offer_count

    print(f"Generated {total} experiments -> {OUTPUT_PATH}")
    print(f"  With winner:        {winners} ({winners/total*100:.0f}%)")
    print(f"  No offer (no sig.): {no_offer_count} ({no_offer_count/total*100:.0f}%)")

    if verify:
        print("\n=== Verification sample ===")
        for exp in experiments[:5]:
            status = "NO_OFFER" if exp["no_offer_recommended"] else f"winner={exp['winning_offer_id']}"
            best_v = next((v for v in exp["variants"] if v["variant_id"] == exp["winning_variant_id"]), None)
            p_str = f"p={best_v['p_value']:.4f}" if best_v else "-"
            print(f"  {exp['experiment_id']:<45} {status}  {p_str}")

        print("\n=== No-offer experiments ===")
        for exp in experiments:
            if exp["no_offer_recommended"]:
                best_p = min(v["p_value"] for v in exp["variants"])
                print(f"  {exp['experiment_id']:<45} best p={best_p:.4f} (threshold={ALPHA})")

    return experiments


if __name__ == "__main__":
    verify_flag = "--verify" in sys.argv
    generate(verify=verify_flag)

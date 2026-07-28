"""
Generate mta_touchpoint_history.csv — realistic multi-touch channel journey data
for 5000 Meridian Bank customers.

Reads:
  data/preloaded/meridian_bank/customers.csv
  data/preloaded/meridian_bank/products.csv

Writes:
  data/preloaded/meridian_bank/mta_touchpoint_history.csv

Schema:
  journey_id, customer_id, persona, channel, offer_id, product_id,
  timestamp, opened, clicked, converted, position
"""

import os
import random
import csv
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CUSTOMERS_PATH = os.path.join(ROOT, "data", "preloaded", "meridian_bank", "customers.csv")
PRODUCTS_PATH  = os.path.join(ROOT, "data", "preloaded", "meridian_bank", "products.csv")
OUT_PATH       = os.path.join(ROOT, "data", "preloaded", "meridian_bank", "mta_touchpoint_history.csv")

START_DATE = datetime(2025, 1, 1)
END_DATE   = datetime(2025, 6, 30)

CHANNELS = ["in_app", "email", "sms", "direct_mail", "branch"]

# ── Persona inference rules ───────────────────────────────────────────────────

def _infer_persona(row: dict) -> str:
    """
    Persona rules — evaluated in priority order.
    Uses churn_probability (0-1 scale), NOT churn_risk_score (0-100 scale).
    """
    try:
        age      = float(row.get("age", 40) or 40)
        dig      = float(row.get("digital_engagement_score", 0.5) or 0.5)
        clv      = float(row.get("customer_lifetime_value", 3000) or 3000)
        inc      = float(row.get("income", 50000) or 50000)
        churn    = float(row.get("churn_probability", 0.2) or 0.2)   # 0-1 scale
        ch_pref  = str(row.get("channel_preference", "") or "")
    except (ValueError, TypeError):
        return "Everyday Essential"

    # 1. Retiree Anchor — age or explicit branch preference
    if age >= 62 or ch_pref == "Branch":
        return "Retiree Anchor"
    # 2. Digital Native — high engagement, younger
    if dig >= 0.70 and age < 42:
        return "Digital Native"
    # 3. Wealth Builder — high CLV / income, low churn
    if (clv >= 8000 or inc >= 90000) and churn < 0.35:
        return "Wealth Builder"
    # 4. At-Risk Saver — elevated churn probability (0-1 scale)
    if churn >= 0.40:
        return "At-Risk Saver"
    # 5. Everyday Essential — default
    return "Everyday Essential"


# ── Per-persona channel behaviour ────────────────────────────────────────────
# (channel: (reach_prob, open_rate, click_rate, conv_rate))
PERSONA_CHANNEL = {
    "Digital Native": {
        "in_app":      (0.75, 0.72, 0.38, 0.23),
        "email":       (0.55, 0.35, 0.14, 0.09),
        "sms":         (0.35, 0.42, 0.12, 0.06),
        "direct_mail": (0.10, 0.12, 0.04, 0.02),
        "branch":      (0.08, 0.60, 0.25, 0.04),
    },
    "Wealth Builder": {
        "in_app":      (0.55, 0.58, 0.28, 0.16),
        "email":       (0.70, 0.55, 0.27, 0.18),
        "sms":         (0.20, 0.30, 0.08, 0.05),
        "direct_mail": (0.45, 0.38, 0.18, 0.12),
        "branch":      (0.30, 0.65, 0.35, 0.09),
    },
    "Everyday Essential": {
        "in_app":      (0.60, 0.48, 0.22, 0.14),
        "email":       (0.65, 0.44, 0.20, 0.14),
        "sms":         (0.40, 0.38, 0.12, 0.08),
        "direct_mail": (0.30, 0.28, 0.12, 0.10),
        "branch":      (0.25, 0.55, 0.28, 0.11),
    },
    "Retiree Anchor": {
        "in_app":      (0.20, 0.22, 0.08, 0.04),
        "email":       (0.50, 0.35, 0.14, 0.10),
        "sms":         (0.15, 0.20, 0.06, 0.05),
        "direct_mail": (0.60, 0.41, 0.22, 0.15),
        "branch":      (0.55, 0.68, 0.40, 0.21),
    },
    "At-Risk Saver": {
        "in_app":      (0.45, 0.32, 0.12, 0.08),
        "email":       (0.55, 0.30, 0.12, 0.09),
        "sms":         (0.50, 0.38, 0.16, 0.12),
        "direct_mail": (0.20, 0.20, 0.07, 0.06),
        "branch":      (0.15, 0.45, 0.20, 0.07),
    },
}

# ── Channel transition sequences (Markov-inspired, per persona) ───────────────
# Defines which channels tend to follow each other in a multi-touch journey.
CHANNEL_SEQUENCES = {
    "Digital Native":     [["in_app"], ["in_app", "email"], ["in_app", "sms", "in_app"],
                           ["email", "in_app"], ["in_app", "in_app", "in_app"]],
    "Wealth Builder":     [["email"], ["email", "in_app"], ["direct_mail", "email"],
                           ["email", "branch", "email"], ["in_app", "email", "direct_mail"]],
    "Everyday Essential": [["email"], ["in_app", "email"], ["sms", "in_app"],
                           ["email", "email", "in_app"], ["in_app", "sms", "email"]],
    "Retiree Anchor":     [["branch"], ["direct_mail"], ["direct_mail", "branch"],
                           ["email", "branch"], ["direct_mail", "email", "branch"]],
    "At-Risk Saver":      [["sms"], ["email", "sms"], ["sms", "in_app"],
                           ["email", "email", "sms"], ["sms", "sms", "email"]],
}


def _rand_date(start: datetime, end: datetime) -> datetime:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta),
                             hours=random.randint(6, 21),
                             minutes=random.randint(0, 59))


def _journey_for_customer(
    customer_id: str,
    persona: str,
    products: list,
    journey_num: int,
) -> list:
    """Return a list of touchpoint rows for one journey."""
    if not products:
        return []

    product = random.choice(products)
    product_id = product["product_id"]
    offer_id   = f"MRD_OFF_{product_id.replace('MRD_P', '').zfill(3)}_{journey_num}"
    journey_id = f"J_{customer_id}_{journey_num:03d}"

    seq = random.choice(CHANNEL_SEQUENCES.get(persona, [["email"]]))
    ch_stats = PERSONA_CHANNEL.get(persona, PERSONA_CHANNEL["Everyday Essential"])

    start = _rand_date(START_DATE, END_DATE - timedelta(days=14))
    rows = []
    converted_already = False

    for pos, channel in enumerate(seq, start=1):
        stats = ch_stats.get(channel, (0.3, 0.3, 0.1, 0.05))
        _, open_rate, click_rate, conv_rate = stats

        # After first conversion, no more events in this journey
        if converted_already:
            break

        ts = start + timedelta(days=(pos - 1) * random.randint(2, 7),
                               hours=random.randint(0, 12))
        if ts > END_DATE:
            break

        opened    = random.random() < open_rate
        clicked   = (random.random() < click_rate) if opened else False
        converted = (random.random() < conv_rate)  if clicked else False

        if converted:
            converted_already = True

        rows.append({
            "journey_id":  journey_id,
            "customer_id": customer_id,
            "persona":     persona,
            "channel":     channel,
            "offer_id":    offer_id,
            "product_id":  product_id,
            "timestamp":   ts.strftime("%Y-%m-%d %H:%M:%S"),
            "opened":      int(opened),
            "clicked":     int(clicked),
            "converted":   int(converted),
            "position":    pos,
        })

    return rows


def main():
    random.seed(42)

    # Load customers
    with open(CUSTOMERS_PATH, encoding="utf-8") as f:
        customers = list(csv.DictReader(f))

    # Load products (only use Personal / first 20)
    with open(PRODUCTS_PATH, encoding="utf-8") as f:
        products = [r for r in csv.DictReader(f) if r.get("customer_types", "")][:28]

    print(f"Loaded {len(customers)} customers, {len(products)} products.")

    all_rows = []
    for cust in customers:
        customer_id = cust["customer_id"]
        persona     = _infer_persona(cust)

        dig = float(cust.get("digital_engagement_score", 0.5) or 0.5)
        churn = float(cust.get("churn_risk_score", 0.2) or 0.2)
        n_journeys = 1
        if dig >= 0.65:
            n_journeys = random.randint(2, 5)
        elif churn >= 0.35:
            n_journeys = random.randint(3, 6)
        else:
            n_journeys = random.randint(1, 4)

        for j in range(1, n_journeys + 1):
            rows = _journey_for_customer(customer_id, persona, products, j)
            all_rows.extend(rows)

    print(f"Generated {len(all_rows):,} touchpoint rows.")

    fieldnames = [
        "journey_id", "customer_id", "persona", "channel", "offer_id",
        "product_id", "timestamp", "opened", "clicked", "converted", "position",
    ]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Written to {OUT_PATH}")


if __name__ == "__main__":
    main()

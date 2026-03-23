"""
Generate synthetic wishlist.csv and incomplete_applications.csv for F&M Bank Agent D testing.
Run from repo root: python scripts/generate_banking_agent_d_tables.py
"""
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "preloaded" / "fmb_bank"


def main():
    customers = []
    products = []
    with open(DATA / "customers.csv", newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if i >= 800:
                break
            customers.append(row["customer_id"])
    with open(DATA / "products.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            products.append(row["product_id"])
    if not customers or not products:
        print("Need customers.csv and products.csv")
        return

    random.seed(42)
    wish_rows = []
    for _ in range(350):
        wish_rows.append(
            {
                "customer_id": random.choice(customers),
                "product_id": random.choice(products),
                "added_at": f"2025-{random.randint(10,12):02d}-{random.randint(1,28):02d}T12:00:00Z",
            }
        )
    seen_w = set()
    wish_unique = []
    for r in wish_rows:
        k = (r["customer_id"], r["product_id"])
        if k not in seen_w:
            seen_w.add(k)
            wish_unique.append(r)

    inc_rows = []
    for _ in range(180):
        inc_rows.append(
            {
                "customer_id": random.choice(customers),
                "product_id": random.choice(products),
                "abandoned_at": f"2025-{random.randint(11,12):02d}-{random.randint(1,28):02d}T10:00:00Z",
                "session_id": f"sess_{random.randint(10000,99999)}",
            }
        )
    seen_i = set()
    inc_unique = []
    for r in inc_rows:
        k = (r["customer_id"], r["product_id"])
        if k not in seen_i:
            seen_i.add(k)
            inc_unique.append(r)

    with open(DATA / "wishlist.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["customer_id", "product_id", "added_at"])
        w.writeheader()
        w.writerows(wish_unique)
    with open(DATA / "incomplete_applications.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["customer_id", "product_id", "abandoned_at", "session_id"])
        w.writeheader()
        w.writerows(inc_unique)
    print(f"Wrote {len(wish_unique)} wishlist, {len(inc_unique)} incomplete_applications rows.")


if __name__ == "__main__":
    main()

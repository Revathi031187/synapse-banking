"""
Generate JPMorgan Chase synthetic dataset for the personalization platform.
Reads existing FMB Bank customers (5K rows) and:
  1. Adds 8 new JPM-specific columns
  2. Writes enriched customers to data/preloaded/jpm_bank/customers.csv
  3. Generates transactions.csv referencing new JPM product IDs
  4. Copies wishlist.csv, incomplete_applications.csv, and recommendation_impressions.csv
     with updated product IDs
"""

import os
import sys
import random
import csv
from datetime import datetime, timedelta

# ── paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "data", "preloaded", "fmb_bank")
DEST = os.path.join(ROOT, "data", "preloaded", "jpm_bank")
os.makedirs(DEST, exist_ok=True)

random.seed(42)

# ── helpers ──────────────────────────────────────────────────────────────────

def _safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def _safe_int(val, default=0):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def derive_credit_tier(credit_score):
    cs = _safe_int(credit_score)
    if cs >= 750: return "excellent"
    if cs >= 700: return "good"
    if cs >= 650: return "fair"
    return "poor"

def derive_fee_sensitivity_tier(fee_sensitivity_score):
    fss = _safe_float(fee_sensitivity_score)
    if fss >= 0.7: return "high"
    if fss >= 0.4: return "medium"
    return "low"

def derive_preferred_rewards_type(income, digital_engagement_score, age):
    income = _safe_float(income)
    digital = _safe_float(digital_engagement_score)
    age = _safe_int(age)
    # High income + high digital + younger -> travel points
    if income >= 80000 and digital >= 0.6 and age < 55:
        return "travel_points" if random.random() < 0.72 else "cash_back"
    # Moderate income -> cash back
    if income >= 40000:
        return "cash_back" if random.random() < 0.65 else "none"
    return "none" if random.random() < 0.5 else "cash_back"

def derive_has_direct_deposit(tenure_months, income, customer_type):
    tenure = _safe_int(tenure_months)
    income = _safe_float(income)
    # Established customers with stable income likely have direct deposit
    base = 0.55
    if tenure >= 24: base += 0.15
    if income >= 50000: base += 0.10
    if customer_type in ("Young_Professional", "High_Net_Worth"): base += 0.10
    return "True" if random.random() < min(base, 0.92) else "False"

def derive_monthly_direct_deposit_amt(has_direct_deposit, income):
    if has_direct_deposit != "True":
        return 0.0
    # Bi-weekly pay -> roughly income / 26 * 2 per month, slightly noisy
    income = _safe_float(income)
    base = income / 12
    noise = random.uniform(0.88, 1.12)
    return round(base * noise, 2)

def derive_owns_home(age, income, deposits, customer_type):
    age = _safe_int(age)
    income = _safe_float(income)
    deposits = _safe_float(deposits)
    base = 0.25
    if age >= 35: base += 0.25
    if age >= 50: base += 0.15
    if income >= 70000: base += 0.12
    if deposits >= 20000: base += 0.10
    if customer_type in ("High_Net_Worth", "Retiree"): base += 0.15
    return "True" if random.random() < min(base, 0.88) else "False"

def derive_investment_risk_profile(age, deposits, cross_sell_receptivity, customer_type):
    age = _safe_int(age)
    deposits = _safe_float(deposits)
    receptivity = _safe_float(cross_sell_receptivity)
    if age >= 60 or customer_type == "Retiree":
        weights = [0.60, 0.35, 0.05]  # conservative, moderate, aggressive
    elif age >= 45:
        weights = [0.30, 0.50, 0.20]
    else:
        weights = [0.15, 0.45, 0.40]
    if deposits >= 100000:
        weights = [weights[0] - 0.05, weights[1] + 0.02, weights[2] + 0.03]
    if receptivity >= 0.7:
        weights = [weights[0] - 0.05, weights[1], weights[2] + 0.05]
    profiles = ["conservative", "moderate", "aggressive"]
    return random.choices(profiles, weights=weights, k=1)[0]

def derive_preferred_loan_term(age, income, customer_type):
    age = _safe_int(age)
    income = _safe_float(income)
    if income >= 80000 or customer_type == "High_Net_Worth":
        weights = [0.45, 0.40, 0.15]  # short, medium, long
    elif age < 35:
        weights = [0.20, 0.45, 0.35]
    else:
        weights = [0.35, 0.45, 0.20]
    return random.choices(["short", "medium", "long"], weights=weights, k=1)[0]


# ── product ID mapping: old FMB -> new JPM ───────────────────────────────────
# Maps based on product category/type alignment
FMB_TO_JPM = {
    "FMB_P001": "JPM_P005",   # Worry-FREE Checking -> Total Checking
    "FMB_P002": "JPM_P006",   # Ultimate Checking -> Premier Plus Checking
    "FMB_P003": "JPM_P006",   # Ultimate High Yield -> Premier Plus Checking
    "FMB_P004": "JPM_P007",   # Sky Blue Checking -> Secure Banking
    "FMB_P005": "JPM_P007",   # Teen Checking -> Secure Banking
    "FMB_P006": "JPM_P008",   # Regular Savings -> Chase Savings
    "FMB_P007": "JPM_P011",   # Money Market -> CD 12-Month
    "FMB_P008": "JPM_P011",   # CDs -> Chase CD 12-Month
    "FMB_P009": "JPM_P019",   # IRAs -> You Invest IRA
    "FMB_P010": "JPM_P008",   # Holiday Club -> Chase Savings
    "FMB_P011": "JPM_P008",   # Junior Savers -> Chase Savings
    "FMB_P012": "JPM_P001",   # Personal Credit Cards -> Freedom Unlimited
    "FMB_P013": "JPM_P015",   # Home Mortgage -> Fixed 30yr
    "FMB_P014": "JPM_P014",   # Auto Loans -> Auto 60-Month
    "FMB_B001": "JPM_B003",   # FREE Business Checking -> Business Complete Checking
    "FMB_B002": "JPM_B003",   # Ultimate Business Checking -> Business Complete Checking
    "FMB_B003": "JPM_B003",   # Business Analysis Checking -> Business Complete Checking
    "FMB_B004": "JPM_B004",   # Business Savings -> Business Premier Savings
    "FMB_B005": "JPM_B004",   # Business Money Market -> Business Premier Savings
    "FMB_B006": "JPM_B001",   # Business Credit Cards -> Ink Business Preferred
    "FMB_B007": "JPM_A001",   # Commercial Real Estate -> Agri Term Loan (closest)
    "FMB_B008": "JPM_A001",   # Business Term Loans -> Agri Term Loan
    "FMB_B009": "JPM_A001",   # SBA Loans -> Agri Term Loan
    "FMB_A001": "JPM_A001",   # Agricultural Loans -> Agri Term Loan
    "FMB_A002": "JPM_A001",   # Agricultural Real Estate -> Agri Term Loan
    "FMB_A003": "JPM_A001",   # Livestock Loans -> Agri Term Loan
    "FMB_A004": "JPM_A002",   # Farm Equipment -> Agri Equipment Lease
    "FMB_A005": "JPM_A001",   # Vineyard Loans -> Agri Term Loan
}


# ── 1. Enrich customers ──────────────────────────────────────────────────────

def enrich_customers():
    src_path  = os.path.join(SRC, "customers.csv")
    dest_path = os.path.join(DEST, "customers.csv")

    new_cols = [
        "credit_tier", "fee_sensitivity_tier", "preferred_rewards_type",
        "has_direct_deposit", "monthly_direct_deposit_amt",
        "owns_home", "investment_risk_profile", "preferred_loan_term",
    ]

    with open(src_path, "r", newline="", encoding="utf-8") as fin, \
         open(dest_path, "w", newline="", encoding="utf-8") as fout:

        reader = csv.DictReader(fin)
        orig_fields = reader.fieldnames or []
        writer = csv.DictWriter(fout, fieldnames=orig_fields + new_cols)
        writer.writeheader()

        count = 0
        for row in reader:
            cs      = row.get("credit_score", 0)
            fss     = row.get("fee_sensitivity_score", 0.5)
            income  = row.get("income", 0)
            age     = row.get("age", 35)
            digital = row.get("digital_engagement_score", 0.5)
            tenure  = row.get("tenure_months", 12)
            ctype   = row.get("customer_type", "Mass_Market")
            deps    = row.get("total_deposits", 0)
            xsell   = row.get("cross_sell_receptivity", 0.5)

            ct   = derive_credit_tier(cs)
            fst  = derive_fee_sensitivity_tier(fss)
            prt  = derive_preferred_rewards_type(income, digital, age)
            hdd  = derive_has_direct_deposit(tenure, income, ctype)
            mdda = derive_monthly_direct_deposit_amt(hdd, income)
            oh   = derive_owns_home(age, income, deps, ctype)
            irp  = derive_investment_risk_profile(age, deps, xsell, ctype)
            plt  = derive_preferred_loan_term(age, income, ctype)

            row.update({
                "credit_tier": ct,
                "fee_sensitivity_tier": fst,
                "preferred_rewards_type": prt,
                "has_direct_deposit": hdd,
                "monthly_direct_deposit_amt": mdda,
                "owns_home": oh,
                "investment_risk_profile": irp,
                "preferred_loan_term": plt,
            })
            writer.writerow(row)
            count += 1

    print(f"  customers: {count} rows -> {dest_path}")
    return count


# ── 2. Generate transactions ─────────────────────────────────────────────────

# JPM product pool per segment for realistic transaction generation
JPM_PERSONAL_PRODUCTS  = ["JPM_P001", "JPM_P004", "JPM_P005", "JPM_P008", "JPM_P013", "JPM_P014"]
JPM_BUSINESS_PRODUCTS  = ["JPM_B001", "JPM_B002", "JPM_B003", "JPM_B004"]
JPM_AGRI_PRODUCTS      = ["JPM_A001", "JPM_A002"]
JPM_PREMIUM_PRODUCTS   = ["JPM_P002", "JPM_P003", "JPM_P006", "JPM_P018", "JPM_P019", "JPM_P020"]

TRANSACTION_TYPES = ["account_opened", "deposit", "purchase", "transfer", "payment", "withdrawal"]


def generate_transactions():
    # Read customer pool from existing FMB transactions to preserve volume pattern
    src_txn = os.path.join(SRC, "transactions.csv")
    src_cust = os.path.join(DEST, "customers.csv")
    dest_txn = os.path.join(DEST, "transactions.csv")

    # Build customer segment lookup
    cust_segment = {}
    cust_type = {}
    with open(src_cust, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cust_segment[row["customer_id"]] = row.get("customer_segment", "Personal")
            cust_type[row["customer_id"]] = row.get("customer_type", "Mass_Market")

    def pick_product(cust_id):
        seg  = cust_segment.get(cust_id, "Personal")
        ctype = cust_type.get(cust_id, "Mass_Market")
        if seg == "Agricultural":
            pool = JPM_AGRI_PRODUCTS
        elif seg == "Business":
            pool = JPM_BUSINESS_PRODUCTS + (["JPM_B001"] * 2)
        elif ctype in ("High_Net_Worth",):
            pool = JPM_PERSONAL_PRODUCTS + JPM_PREMIUM_PRODUCTS
        else:
            pool = JPM_PERSONAL_PRODUCTS
        return random.choice(pool)

    written = 0
    with open(src_txn, "r", newline="", encoding="utf-8") as fin, \
         open(dest_txn, "w", newline="", encoding="utf-8") as fout:

        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames or [])
        writer.writeheader()

        for row in reader:
            # Map old FMB product ID to JPM product ID
            old_pid = row.get("product_id", "")
            new_pid = FMB_TO_JPM.get(old_pid, pick_product(row.get("customer_id", "")))
            row["product_id"] = new_pid
            writer.writerow(row)
            written += 1

    print(f"  transactions: {written} rows -> {dest_txn}")


# ── 3. Copy/update ancillary files ───────────────────────────────────────────

def copy_ancillary():
    for fname in ("wishlist.csv", "incomplete_applications.csv", "recommendation_impressions.csv"):
        src_f  = os.path.join(SRC, fname)
        dest_f = os.path.join(DEST, fname)
        if not os.path.exists(src_f):
            # Create empty file with correct headers
            headers = {
                "wishlist.csv": "customer_id,product_id,added_date,notes",
                "incomplete_applications.csv": "customer_id,product_id,started_date,last_step",
                "recommendation_impressions.csv": "customer_id,product_id,shown_count,click_count,last_shown_date",
            }
            with open(dest_f, "w", newline="", encoding="utf-8") as fout:
                fout.write(headers.get(fname, "") + "\n")
            print(f"  {fname}: created empty -> {dest_f}")
            continue

        with open(src_f, "r", newline="", encoding="utf-8") as fin, \
             open(dest_f, "w", newline="", encoding="utf-8") as fout:

            reader = csv.DictReader(fin)
            if not reader.fieldnames:
                fout.write(fin.read())
                print(f"  {fname}: copied (no fieldnames) -> {dest_f}")
                continue

            writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
            writer.writeheader()
            count = 0
            for row in reader:
                if "product_id" in row:
                    row["product_id"] = FMB_TO_JPM.get(row["product_id"], row["product_id"])
                writer.writerow(row)
                count += 1
        print(f"  {fname}: {count} rows -> {dest_f}")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating JPMorgan Chase dataset...")
    print(f"  Source : {SRC}")
    print(f"  Dest   : {DEST}")
    print()

    if not os.path.exists(os.path.join(SRC, "customers.csv")):
        print("ERROR: Source customers.csv not found. Run from project root.")
        sys.exit(1)

    print("1. Enriching customers...")
    n = enrich_customers()

    print("2. Generating transactions...")
    generate_transactions()

    print("3. Copying ancillary files...")
    copy_ancillary()

    print()
    print(f"Done. {n} customers written to {DEST}/")
    print("Products CSV was pre-created at data/preloaded/jpm_bank/products.csv")

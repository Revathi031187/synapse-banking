"""
Chatbot end-to-end test.
Tests SQL patterns directly in DuckDB (no server needed),
then calls the full LLM pipeline for key question categories.
Run from project root: python _test_chatbot.py
"""
import os, sys, json, time, traceback
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import duckdb
import pandas as pd

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}[OK]  {RESET} {msg}")
def fail(msg):  print(f"  {RED}[FAIL]{RESET} {msg}")
def warn(msg):  print(f"  {YELLOW}[WARN]{RESET} {msg}")
def info(msg):  print(f"  {CYAN}[-->] {RESET} {msg}")

d = Path("data/preloaded/meridian_bank")
TABLE_FILES = [
    ("customers",           "customers.csv"),
    ("products",            "products.csv"),
    ("transactions",        "transactions.csv"),
    ("customer_profile",    "customer_profile.csv"),
    ("customer_engagement", "customer_engagement.csv"),
    ("mta_touchpoints",     "mta_touchpoint_history.csv"),
    ("ad_spend",            "ad_spend_monthly.csv"),
    ("impressions",         "recommendation_impressions.csv"),
    ("wishlist",            "wishlist.csv"),
    ("incomplete_apps",     "incomplete_applications.csv"),
]

con = duckdb.connect(":memory:")
registered = []
for t, f in TABLE_FILES:
    p = (d / f).as_posix()
    if (d / f).exists():
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_csv_auto('{p}', header=true)")
        registered.append(t)
    else:
        warn(f"File not found, skipping: {f}")

print(f"\n{BOLD}Registered tables: {', '.join(registered)}{RESET}\n")
print(f"{BOLD}{'='*65}{RESET}")
print(f"{BOLD} PART 1 - DuckDB SQL correctness (20 question patterns){RESET}")
print(f"{BOLD}{'='*65}{RESET}\n")

SQL_TESTS = [
    (
        "Churn risk by category",
        "SELECT churn_risk_category, COUNT(*) cnt, ROUND(AVG(churn_probability),3) avg_churn FROM customers GROUP BY churn_risk_category ORDER BY avg_churn DESC",
        3, None
    ),
    (
        "CLV tier breakdown",
        "SELECT clv_tier, COUNT(*) cnt, ROUND(AVG(customer_lifetime_value),0) avg_clv FROM customers GROUP BY clv_tier ORDER BY avg_clv DESC",
        3, None
    ),
    (
        "ROAS by channel (correct aggregation)",
        "SELECT channel, ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0),2) AS roas FROM ad_spend GROUP BY channel ORDER BY roas DESC",
        4, lambda df: df['channel'].nunique() == 4
    ),
    (
        "ROI by channel (AVG aggregation)",
        "SELECT channel, ROUND(AVG(roi_pct),2) AS avg_roi FROM ad_spend GROUP BY channel ORDER BY avg_roi DESC",
        4, lambda df: df['channel'].nunique() == 4
    ),
    (
        "ROAS by channel AND persona",
        "SELECT channel, persona, ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0),2) AS roas FROM ad_spend GROUP BY channel, persona ORDER BY roas DESC LIMIT 20",
        10, None
    ),
    (
        "Monthly spend trend (time series)",
        "SELECT CAST(year AS VARCHAR)||'-'||LPAD(CAST(month AS VARCHAR),2,'0') AS month_key, ROUND(SUM(spend_usd),0) AS total_spend FROM ad_spend GROUP BY year, month, month_key ORDER BY year, month LIMIT 24",
        12, None
    ),
    (
        "Products wishlisted NOT applied (LEFT JOIN + IS NULL)",
        """SELECT p.product_name, COUNT(*) AS wishlist_count
           FROM wishlist w
           JOIN products p ON w.product_id = p.product_id
           LEFT JOIN incomplete_apps i ON w.customer_id=i.customer_id AND w.product_id=i.product_id
           WHERE i.customer_id IS NULL
           GROUP BY p.product_name ORDER BY wishlist_count DESC LIMIT 15""",
        5, lambda df: df['wishlist_count'].sum() > 0
    ),
    (
        "Top 10 most valuable customers",
        "SELECT customer_id, ROUND(customer_lifetime_value,0) AS clv, churn_risk_category FROM customers ORDER BY customer_lifetime_value DESC LIMIT 10",
        10, None
    ),
    (
        "Average income by life stage",
        "SELECT life_stage, ROUND(AVG(income),0) AS avg_income, COUNT(*) AS cnt FROM customers GROUP BY life_stage ORDER BY avg_income DESC",
        3, None
    ),
    (
        "Credit tier distribution",
        "SELECT credit_tier, COUNT(*) AS cnt FROM customers GROUP BY credit_tier ORDER BY cnt DESC",
        3, None
    ),
    (
        "Incomplete applications by product",
        "SELECT p.product_name, COUNT(*) AS incomplete_count FROM incomplete_apps i JOIN products p ON i.product_id=p.product_id GROUP BY p.product_name ORDER BY incomplete_count DESC",
        1, None
    ),
    (
        "High churn + CLV customers",
        "SELECT customer_id, ROUND(churn_probability,3) AS churn_prob, ROUND(customer_lifetime_value,0) AS clv FROM customers WHERE churn_risk_category='High' ORDER BY customer_lifetime_value DESC LIMIT 10",
        5, None
    ),
    (
        "Wishlist count by product category",
        "SELECT p.category, COUNT(*) AS wishlist_count FROM wishlist w JOIN products p ON w.product_id=p.product_id GROUP BY p.category ORDER BY wishlist_count DESC",
        1, None
    ),
    (
        "Channel conversion rate comparison",
        "SELECT channel, ROUND(AVG(conversion_rate),4) AS avg_conversion FROM ad_spend GROUP BY channel ORDER BY avg_conversion DESC",
        4, None
    ),
    (
        "CPA by channel",
        "SELECT channel, ROUND(AVG(cpa),2) AS avg_cpa FROM ad_spend GROUP BY channel ORDER BY avg_cpa ASC",
        4, None
    ),
    (
        "Digital engagement decline by churn risk",
        "SELECT churn_risk_category, COUNT(*) AS cnt FROM customers WHERE digital_engagement_decline=True GROUP BY churn_risk_category ORDER BY cnt DESC",
        1, None
    ),
    (
        "Transaction volume by channel",
        "SELECT channel, COUNT(*) AS txn_count, ROUND(SUM(amount),0) AS total_amount FROM transactions GROUP BY channel ORDER BY total_amount DESC",
        3, None
    ),
    (
        "Product impression click rates",
        "SELECT p.product_name, SUM(click_count) AS total_clicks, SUM(shown_count) AS total_shown FROM impressions i JOIN products p ON i.product_id=p.product_id GROUP BY p.product_name ORDER BY total_clicks DESC LIMIT 10",
        1, None
    ),
    (
        "Competitor offer by churn risk",
        "SELECT churn_risk_category, COUNT(*) AS cnt FROM customers WHERE competitor_offer_received=True GROUP BY churn_risk_category ORDER BY cnt DESC",
        1, None
    ),
    (
        "Multi-table: life stage + category + wishlist",
        """SELECT c.life_stage, p.category, COUNT(*) AS wishlist_count
           FROM wishlist w
           JOIN customers c ON w.customer_id=c.customer_id
           JOIN products p ON w.product_id=p.product_id
           GROUP BY c.life_stage, p.category
           ORDER BY wishlist_count DESC LIMIT 15""",
        5, None
    ),
]

passed = 0
failed = 0

for label, sql, min_rows, check_fn in SQL_TESTS:
    try:
        df = con.execute(sql).df()
        rows = len(df)
        if rows < min_rows:
            fail(f"{label} => only {rows} rows (expected >={min_rows})")
            print(f"       SQL: {sql[:120]}")
            failed += 1
        elif check_fn and not check_fn(df):
            warn(f"{label} => {rows} rows but check failed")
            print(df.head(3).to_string(index=False))
            failed += 1
        else:
            ok(f"{label} => {rows} rows")
            print(f"       {df.head(3).to_string(index=False)}")
        print()
    except Exception as e:
        fail(f"{label} => EXCEPTION: {e}")
        failed += 1
        print()

print(f"\n{BOLD}SQL Tests: {GREEN}{len(SQL_TESTS)-failed}{RESET}/{len(SQL_TESTS)} passed, {RED}{failed}{RESET} failed{RESET}\n")

# ---- PART 2: LLM pipeline test -----------------------------------------------

print(f"\n{BOLD}{'='*65}{RESET}")
print(f"{BOLD} PART 2 - Full LLM pipeline (SQL generation + execution){RESET}")
print(f"{BOLD}{'='*65}{RESET}\n")

try:
    from utils.chat_sql_engine import ask_chatbot
    llm_ok = True
    print(f"  Imported ask_chatbot OK\n")
except Exception as e:
    warn(f"Could not import ask_chatbot: {e}")
    llm_ok = False

LLM_QUESTIONS = [
    ("Channel ROI ranking",         "Which marketing channels have the highest ROI?"),
    ("Churn risk segments",         "Show churn risk breakdown by customer life stage"),
    ("Wishlist gap",                "What products are customers wishlisting but not applying for?"),
    ("Top valuable customers",      "Who are the top 10 most valuable customers?"),
    ("Monthly spend trend",         "Show monthly marketing spend trend across all channels"),
    ("ROAS by channel and persona", "What is the ROAS by marketing channel and persona?"),
    ("Incomplete applications",     "Which products have the most incomplete applications?"),
    ("Life stage income",           "What is the average income per life stage?"),
    ("Digital vs branch",           "Compare digital vs branch transaction volume and amount"),
    ("High churn + high CLV",       "Show customers with high churn risk sorted by highest CLV"),
]

if llm_ok:
    llm_passed = 0
    llm_failed = 0
    llm_warned = 0

    for label, question in LLM_QUESTIONS:
        print(f"  {BOLD}Q: {question}{RESET}")
        t0 = time.time()
        try:
            result = ask_chatbot(question)
            elapsed = time.time() - t0

            sql      = result.get("sql") or ""
            table    = result.get("table")
            chart    = result.get("chart") or {}
            sql_err  = result.get("sql_error")
            narrative= (result.get("narrative") or "")[:120]

            rows = len(table["rows"]) if table else 0
            cols = table["columns"] if table else []

            issues = []
            if not sql:
                issues.append("no SQL generated")
            if sql_err:
                issues.append(f"SQL error: {sql_err[:80]}")
            if rows == 0 and sql and not sql_err:
                issues.append("0 rows returned")

            # Check for missing GROUP BY (duplicate x values). Skip this check when the
            # SQL's own GROUP BY spans 2+ columns — a legitimate cross-tab (e.g.
            # GROUP BY persona, channel) naturally repeats whichever single column the
            # chart picked as x-axis without the data being "ungrouped" at all.
            import re as _re
            _group_by_match = _re.search(r'\bGROUP\s+BY\s+(.+?)(?:\bORDER\s+BY\b|\bLIMIT\b|$)', sql, _re.IGNORECASE | _re.DOTALL)
            _group_by_cols = len(_group_by_match.group(1).split(',')) if _group_by_match else 0
            if table and chart.get("x_col") and chart["x_col"] in cols and _group_by_cols < 2:
                xi = cols.index(chart["x_col"])
                x_vals = [str(r[xi]) for r in table["rows"]]
                uniq = len(set(x_vals))
                if rows > 10 and uniq < rows * 0.6:
                    issues.append(f"BAD AGGREGATION: {uniq} unique x / {rows} rows (missing GROUP BY?)")

            if issues:
                fail(f"{label} ({elapsed:.1f}s) => {'; '.join(issues)}")
                llm_failed += 1
                if sql:
                    print(f"       SQL: {sql[:200]}")
            else:
                ok(f"{label} ({elapsed:.1f}s) => {rows} rows | chart={chart.get('type','?')} x={chart.get('x_col','?')} y={chart.get('y_col','?')}")
                llm_passed += 1

            if narrative:
                info(f"Narrative: {narrative}")
            if table and rows > 0:
                df2 = pd.DataFrame(table["rows"], columns=cols)
                print(f"       {df2.head(3).to_string(index=False)}")

        except Exception as e:
            fail(f"{label} => EXCEPTION: {e}")
            traceback.print_exc()
            llm_failed += 1

        print()

    print(f"\n{BOLD}LLM Tests: {GREEN}{llm_passed}{RESET} passed, {YELLOW}{llm_warned}{RESET} warned, {RED}{llm_failed}{RESET} failed{RESET}")
else:
    warn("Skipping LLM tests")

print(f"\n{BOLD}Done.{RESET}\n")

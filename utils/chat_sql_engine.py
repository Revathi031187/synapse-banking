"""
Advanced Chatbot SQL Engine for Meridian Bank.

Uses DuckDB to query local CSV files directly — no Databricks dependency.
LLM generates DuckDB SQL, we execute it locally, return table + chart config.

DuckDB reads the CSVs as virtual views, so the data is always fresh and
every JOIN across all 10 tables works instantly.
"""

from __future__ import annotations

import os
import re
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

# ── Data path ─────────────────────────────────────────────────────────────────

def _meridian_dir() -> Path:
    root = Path(__file__).parent.parent
    for candidate in (
        root / "data" / "preloaded" / "meridian_bank",
        root / "data" / "preloaded" / "jpm_bank",
        root / "data" / "preloaded" / "fmb_bank",
    ):
        if candidate.is_dir():
            return candidate
    return root / "data" / "preloaded" / "meridian_bank"


# /tmp fallback path for large CSVs excluded from Databricks Apps deployment bundle
_TMP_TXN = Path('/tmp/meridian_bank/transactions.csv')


def _ensure_transactions_csv(local_path: Path) -> Path:
    """Return a valid path to transactions.csv; delegates to large_file_loader."""
    from utils.large_file_loader import ensure_csv
    return ensure_csv(local_path)


def _resolve_csv_path(d: Path, fname: str) -> Path:
    """Return the best available path for a CSV file (checks /tmp fallback after download)."""
    local = d / fname
    if fname == 'transactions.csv' and not local.exists() and _TMP_TXN.exists():
        return _TMP_TXN
    return local


# ── DuckDB connection + view registration ─────────────────────────────────────

# Table-name → CSV-filename mapping (order matters for the schema context)
TABLE_FILES = [
    ("segment_profiles",         "segment_profiles.csv"),
    ("customers",                "customers.csv"),
    ("products",                 "products.csv"),
    ("transactions",             "transactions.csv"),
    ("customer_profile",         "customer_profile.csv"),
    ("customer_engagement",      "customer_engagement.csv"),
    ("mta_touchpoints",          "mta_touchpoint_history.csv"),
    ("ad_spend",                 "ad_spend_monthly.csv"),
    ("impressions",              "recommendation_impressions.csv"),
    ("wishlist",                 "wishlist.csv"),
    ("incomplete_applications",  "incomplete_applications.csv"),
]

_CON: Optional[duckdb.DuckDBPyConnection] = None
_REGISTERED: bool = False
_PERSONAS_REGISTERED: bool = False


def _get_con() -> duckdb.DuckDBPyConnection:
    global _CON, _REGISTERED
    if _CON is None:
        _CON = duckdb.connect(database=":memory:", read_only=False)
    if not _REGISTERED:
        _register_views(_CON)
        _REGISTERED = True
    return _CON


def _register_views(con: duckdb.DuckDBPyConnection) -> None:
    d = _meridian_dir()
    for table, fname in TABLE_FILES:
        p = d / fname
        if fname == 'transactions.csv':
            p = _ensure_transactions_csv(p)
        if p.is_file():
            safe = p.as_posix()
            try:
                con.execute(
                    f"CREATE OR REPLACE VIEW {table} AS "
                    f"SELECT * FROM read_csv_auto('{safe}', header=true, sample_size=-1)"
                )
                logger.debug("Registered view: %s -> %s", table, fname)
            except Exception as e:
                logger.warning("Could not register %s: %s", fname, e)

    # ── Heuristic segment_assignments view ────────────────────────────────────
    # Classifies every customer into one of the 5 Meridian segments using
    # observable customer attributes — available immediately without Agent A.
    # Priority order matches the segment profile characteristics:
    #   1. At-Risk Saver   — lowest credit / lowest income
    #   2. Wealth Accumulator — highest income / excellent credit
    #   3. Digital Trendsetter — very high digital engagement
    #   4. Retiree Depositor — high deposits, moderate income, lower digital
    #   5. Everyday Essential — everyone else (largest segment)
    try:
        con.execute("""
            CREATE OR REPLACE VIEW segment_assignments AS
            SELECT
                customer_id,
                CASE
                    WHEN credit_score < 620
                        THEN 'At-Risk Saver'
                    WHEN income >= 120000
                      OR (income >= 85000 AND credit_score >= 750)
                        THEN 'Wealth Accumulator'
                    WHEN digital_engagement_score >= 0.78
                        THEN 'Digital Trendsetter'
                    WHEN total_deposits >= 80000 AND income < 100000
                        THEN 'Retiree Depositor'
                    ELSE 'Everyday Essential'
                END AS segment_name
            FROM customers
        """)
        logger.debug("Registered heuristic view: segment_assignments")
    except Exception as e:
        logger.warning("Could not register segment_assignments view: %s", e)


def register_persona_results(
    customers_with_clusters: List[Dict],
    personas: Optional[Dict] = None,
) -> None:
    """
    Register Agent A's K-Prototypes output as DuckDB tables so the chatbot
    can answer questions using actual persona names (Wealth Builder, etc.).

    customers_with_clusters: list of customer dicts — each has 'customer_id' and 'cluster'
    personas: dict keyed by cluster_id → {'persona_name': str, ...}

    Creates:
      persona_assignments (customer_id, cluster_id, persona_name)
      persona_stats       (persona_name, customer_count, avg_churn_prob, avg_clv, avg_income,
                           avg_credit_score, avg_digital_engagement, avg_deposits)
    """
    global _PERSONAS_REGISTERED
    if not customers_with_clusters:
        return

    con = _get_con()
    try:
        # Build cluster_id → persona_name lookup
        cluster_to_name: Dict[int, str] = {}
        if personas:
            for cid, pdata in personas.items():
                name = (pdata.get("persona_name") or pdata.get("name") or f"Segment {cid}") if isinstance(pdata, dict) else str(pdata)
                cluster_to_name[int(cid)] = str(name)

        rows = []
        for c in customers_with_clusters:
            cust_id = c.get("customer_id")
            if cust_id is None:
                continue
            # Agent A uses 'cluster' (not 'cluster_id') as the field name
            cid = c.get("cluster") if c.get("cluster") is not None else c.get("cluster_id")
            if cid is None:
                continue
            cid = int(cid)
            pname = cluster_to_name.get(cid) or c.get("persona_name") or f"Segment {cid}"
            rows.append((str(cust_id), cid, pname))

        if not rows:
            return

        df = pd.DataFrame(rows, columns=["customer_id", "cluster_id", "persona_name"])
        con.register("_persona_df", df)
        con.execute("CREATE OR REPLACE TABLE persona_assignments AS SELECT * FROM _persona_df")
        con.unregister("_persona_df")

        # Pre-compute per-persona stats joined with customers
        con.execute("""
            CREATE OR REPLACE TABLE persona_stats AS
            SELECT
                pa.persona_name,
                COUNT(*) AS customer_count,
                ROUND(AVG(c.churn_probability), 3) AS avg_churn_prob,
                ROUND(AVG(c.customer_lifetime_value), 0) AS avg_clv,
                ROUND(AVG(c.income), 0) AS avg_income,
                ROUND(AVG(c.credit_score), 0) AS avg_credit_score,
                ROUND(AVG(c.digital_engagement_score), 3) AS avg_digital_engagement,
                ROUND(AVG(c.total_deposits), 0) AS avg_deposits
            FROM persona_assignments pa
            JOIN customers c ON pa.customer_id = c.customer_id
            GROUP BY pa.persona_name
            ORDER BY customer_count DESC
        """)

        _PERSONAS_REGISTERED = True
        logger.info("Registered %d persona assignments into DuckDB (%d unique personas)",
                    len(rows), df["persona_name"].nunique())
    except Exception as e:
        logger.warning("Could not register persona results: %s", e)


def _columns_for(table: str) -> List[str]:
    try:
        con = _get_con()
        rows = con.execute(f"DESCRIBE {table}").fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


# ── Schema context for the LLM ────────────────────────────────────────────────

def build_schema_context() -> str:
    d = _meridian_dir()
    lines = ["You have access to the following DuckDB tables (loaded from Meridian Bank CSVs):\n"]

    # segment_assignments — always available (heuristic view, no Agent A needed)
    lines.append("VIEW: segment_assignments  ← USE THIS for all customer-level segment queries when Agent A has not run")
    lines.append("  Description: Maps every customer_id to one of the 5 Meridian Bank segments using customer attributes. Always available.")
    lines.append("  Columns: customer_id, segment_name")
    lines.append("  segment_name values: 'Retiree Depositor', 'Wealth Accumulator', 'Everyday Essential', 'Digital Trendsetter', 'At-Risk Saver'")
    lines.append("  JOIN: customers c JOIN segment_assignments sa ON c.customer_id = sa.customer_id")
    lines.append("  JOIN: transactions t JOIN segment_assignments sa ON t.customer_id = sa.customer_id")
    lines.append("")

    # Persona tables (only present after Agent A has run)
    if _PERSONAS_REGISTERED:
        lines.append("TABLE: persona_assignments  ← USE THIS instead of segment_assignments when Agent A has run (more accurate)")
        lines.append("  Description: Customer-to-persona mapping from Agent A K-Prototypes clustering")
        lines.append("  Columns: customer_id, cluster_id, persona_name")
        lines.append("")
        lines.append("TABLE: persona_stats")
        lines.append("  Description: Pre-computed stats per persona — use for segment-level questions")
        lines.append("  Columns: persona_name, customer_count, avg_churn_prob, avg_clv, avg_income, avg_credit_score, avg_digital_engagement, avg_deposits")
        lines.append("")

    descriptions = {
        "segment_profiles":    "Pre-defined Meridian Bank segments — 5 rows, one per segment. Use this for ANY segment-level question (intent score, avg balance, health status, top products). Available BEFORE Agent A runs.",
        "customers":           "Core customer profiles — 5,000 rows, one per customer",
        "products":            "Product catalogue — credit cards, loans, savings, mortgages",
        "transactions":        "Individual transaction ledger — debit/credit/transfer events",
        "customer_profile":    "Extended financial profile per customer — income, debt, assets",
        "customer_engagement": "Digital and channel engagement metrics per customer",
        "mta_touchpoints":     "Multi-touch attribution — marketing interactions across channels",
        "ad_spend":            "Monthly marketing spend and performance by channel and persona",
        "impressions":         "Product recommendation impression and click ledger",
        "wishlist":            "Products customers explicitly saved/wishlisted",
        "incomplete_applications": "Applications started but not completed. Columns: customer_id, product_id, started_date, last_step. last_step values (EXACT — never rename): 'personal_info', 'financial_details', 'review', 'sign', 'document_upload'",
    }

    for table, fname in TABLE_FILES:
        p = _resolve_csv_path(d, fname)
        if not p.is_file():
            continue
        cols = _columns_for(table)
        if not cols:
            try:
                df = pd.read_csv(p, nrows=0)
                cols = df.columns.tolist()
            except Exception:
                continue
        desc = descriptions.get(table, "")
        lines.append(f"TABLE: {table}")
        lines.append(f"  Description: {desc}")
        lines.append(f"  Columns: {', '.join(cols)}")
        lines.append("")

    persona_hint = (
        "  - persona_assignments.customer_id -> customers.customer_id (JOIN to get persona_name per customer)\n"
        "  - persona_stats has one row per persona — use directly for Agent-A-derived segment comparisons\n"
        "  - PREFER persona_name from persona_assignments over segment_assignments when Agent A has run\n"
    ) if _PERSONAS_REGISTERED else (
        "  - Agent A has NOT been run yet — use segment_assignments (always available) for customer-level segment queries\n"
        "  - NEVER use customers.life_stage as a substitute for segment — life_stage values (Family/Student/etc.) are NOT the Meridian segments\n"
    )

    lines.append(
        "JOIN HINTS:\n"
        "  - All tables join via customer_id\n"
        "SEGMENT_ASSIGNMENTS VIEW (always available — no Agent A required):\n"
        "  - segment_assignments maps every customer_id → segment_name (one of 5 Meridian segments)\n"
        "  - segment_name values: 'Retiree Depositor', 'Wealth Accumulator', 'Everyday Essential', 'Digital Trendsetter', 'At-Risk Saver'\n"
        "  - Use segment_assignments for ALL per-customer segment queries (transaction volume by segment, churn by segment, etc.)\n"
        "  - JOIN: customers c JOIN segment_assignments sa ON c.customer_id = sa.customer_id\n"
        "  - JOIN: transactions t JOIN segment_assignments sa ON t.customer_id = sa.customer_id\n"
        "  - EXAMPLE: SELECT sa.segment_name, COUNT(*) AS customers FROM customers c JOIN segment_assignments sa ON c.customer_id = sa.customer_id GROUP BY sa.segment_name\n"
        "  - EXAMPLE: SELECT sa.segment_name, ROUND(SUM(t.amount),0) AS total_volume FROM transactions t JOIN segment_assignments sa ON t.customer_id = sa.customer_id GROUP BY sa.segment_name ORDER BY total_volume DESC\n"
        "SEGMENT_PROFILES TABLE (always available — no Agent A required):\n"
        "  - segment_profiles has 5 rows: Retiree Depositor, Wealth Accumulator, Everyday Essential, Digital Trendsetter, At-Risk Saver\n"
        "  - Columns: segment_name, short_code, customer_count, avg_balance_usd, avg_income_usd, avg_credit_score, digital_adoption_pct, intent_score_pct, health_status, top_product_1, top_product_2, top_product_3, featured_offer, description\n"
        "  - Use segment_profiles for: 'which segment has highest balance', 'compare intent scores', 'which segments are at-risk', 'segment overview', 'top products by segment'\n"
        "  - EXAMPLE: SELECT segment_name, intent_score_pct, health_status FROM segment_profiles ORDER BY intent_score_pct DESC\n"
        "  - EXAMPLE: SELECT segment_name, avg_balance_usd, customer_count FROM segment_profiles ORDER BY avg_balance_usd DESC\n"
        + persona_hint +
        "  - impressions.product_id -> products.product_id\n"
        "  - incomplete_applications.product_id -> products.product_id\n"
        "  - wishlist.product_id -> products.product_id\n"
        "  - transactions has 876K rows — always filter by date or customer_id for performance\n"
        "  - transaction channels: Mobile, Online, Phone, ATM, Branch (5 values — ATM is valid)\n"
        "  - ad_spend channels: email, sms, in_app, branch (4 values — different from transaction channels)\n"
        "  - customers.channel_preference: customer's PREFERRED contact channel (values: Digital, Branch, Hybrid — 3 values). Use for 'preferred communication channel' questions.\n"
        "  - customers.preferred_communication_style: communication style preference (e.g. Formal, Casual, etc.)\n"
        "  - products has NO revenue column — use SUM(transactions.amount) JOIN products ON product_id\n"
        "  - customers.annual_transaction_value: PRE-COMPUTED total annual spend per customer — use this for 'top N by transaction value' queries instead of aggregating the transactions table.\n"
        "  - ad_spend columns: year, month, month_name, channel, persona, spend_usd, revenue_usd, roas, roi_pct, cpa, conversion_rate, click_rate, open_rate, sent, opened, clicked, converted, true_roas, true_roi_pct\n"
        "  - ad_spend has NO date column — it has INTEGER year and month columns. Data covers 2025 only (months 1–12). For 'last N months of ad spend': use WHERE year = 2025 AND month >= (12 - N + 1). NEVER use CURRENT_DATE on ad_spend.\n"
        "  - ad_spend.sent = total contacts/reach for that campaign row (email sent, SMS sent, etc.) — NOT a product impression count. NEVER call it 'impressions'.\n"
        "  - customers.clv_tier values: 'Platinum', 'Gold', 'Silver', 'Bronze' — use these exact strings.\n"
        "  - customers.days_since_last_transaction: PRE-COMPUTED integer, use it directly for dormancy queries. Max value in this dataset is ~48. Use >= 30 for dormancy targeting (yields meaningful cohort). NEVER use >= 90 (returns 0 rows — no customer exceeds 48 days). NEVER compute it from CURRENT_DATE.\n"
        "CRITICAL — DATE REFERENCE RULE (transaction data is STATIC, max date 2025-06-04):\n"
        "  NEVER use CURRENT_DATE, NOW(), TODAY(), or GETDATE() for time-range filters on transactions.\n"
        "  Instead use: (SELECT MAX(CAST(transaction_date AS DATE)) FROM transactions) as the anchor date.\n"
        "  'last 12 months' → WHERE CAST(transaction_date AS DATE) >= (SELECT MAX(CAST(transaction_date AS DATE)) - INTERVAL '365' DAY FROM transactions)\n"
        "  'last 6 months'  → WHERE CAST(transaction_date AS DATE) >= (SELECT MAX(CAST(transaction_date AS DATE)) - INTERVAL '180' DAY FROM transactions)\n"
        "  'last 90 days'   → WHERE CAST(transaction_date AS DATE) >= (SELECT MAX(CAST(transaction_date AS DATE)) - INTERVAL '90'  DAY FROM transactions)\n"
        "  For DORMANCY on customers table use: WHERE c.days_since_last_transaction >= 30  (no date math needed; max value in dataset is ~48 so never use >= 90)\n"
        "PRODUCT COMPATIBILITY (customers table has: credit_score, credit_tier, income):\n"
        "  - products.credit_tier_required: 'any'=all, 'fair'=credit_score>=580, 'good'=credit_score>=670, 'excellent'=credit_score>=740\n"
        "  - always check: c.income >= p.min_income AND c.credit_score >= p.min_credit_score when recommending\n"
    )

    return "\n".join(lines)


# ── SQL generation prompt ─────────────────────────────────────────────────────

_SQL_SYSTEM = """You are an expert DuckDB SQL analyst for Meridian Bank.

Given a natural-language question and conversation history, you generate:
1. A valid DuckDB SELECT query
2. A rich, well-formatted Markdown narrative (100-250 words)
3. A chart configuration (type, x_col, y_col, title)
4. 3 contextual follow-up questions

NARRATIVE REQUIREMENTS — CRITICAL:
Your narrative must be rich, insightful, and formatted in Markdown.

CRITICAL — JSON LINE BREAKS: The "narrative" value in your JSON MUST use \n escape sequences to place each bullet and section header on its own line. Never write the entire narrative as one paragraph. Format example:
"narrative": "**247 customers** (4.9%) have incomplete applications.\n\n- **Meridian Cash Basic** leads with 89 incomplete applications\n- **Elite Rewards Card** has 67 incomplete — mostly Gold tier customers\n- Digital channel drives 61% of all incomplete starts\n\n**Recommendation:** Trigger an in-app nudge within 24 hours of abandonment."

Rules:
- **Open with the key metric in bold**: e.g., "**247 customers** (4.9% of the base) have incomplete applications — a significant missed revenue opportunity."
- Use `**bold**` for ALL numbers, percentages, dollar amounts, and key metrics throughout
- Format ALL monetary values (revenue, spend, income, balance, deposit, cost, amount, budget) as **$X.XK** / **$X.XM** / **$X.XB** — NEVER write raw decimals like 135600.0 or 23824.0. Examples: 135600 → **$135.6K**, 2300000 → **$2.3M**. Non-monetary metrics (ROAS, scores, rates, counts) use bold without $: **5.69 ROAS**, **1,247 customers**, **720 credit score**.
- Use `- bullet points` when listing 3+ data points or breakdowns (e.g., top products, top segments) — EACH bullet on its OWN LINE using \n
- Add "**Recommendation:** ..." ONLY when the answer involves segment strategy, product fit, campaign targeting, customer behaviour, or risk/retention analysis. SKIP the Recommendation entirely for simple factual lookups (e.g. "how many", "list the segments", "what is the definition of", pure count or name queries). When included, place it on its own line preceded by \n\n.
- Use `## Section` headers only when the answer has 2+ clearly distinct parts — each header on its own line
- NEVER start with query descriptions: "The SQL query identifies...", "The query returns...", "The query filters...", "This query retrieves..." — these describe the SQL, not the data. Start with the actual finding (e.g. "**143 Platinum and Gold customers** prefer digital channels but haven't transacted in 30+ days.")
- NEVER write a 1-2 sentence answer — always provide depth, context, and business meaning
- When listing customers, explain WHO they are and WHY it matters for the bank, not just how many
- NEVER describe characteristics generically (e.g. "High average income") without citing the actual numbers from the query result. Always say "avg income of **$67,400**" not just "high income".
- When asked about "top N" personas/segments, ALWAYS name them explicitly in the narrative (e.g. "**Wealth Builder** and **Digital Native**").

DATA GROUNDING — ABSOLUTE RULE (no hallucinations):
Every number, percentage, name, or metric you cite in the narrative MUST come from the SQL SELECT result columns or from earlier messages in the conversation history. NEVER invent supporting details.

CRITICAL GROUNDING RULES:
- Every number in the narrative must equal the exact value in the corresponding table cell. NEVER paraphrase, approximate, or invent a different number.
- Persona names, product names, segment names: copy them EXACTLY as they appear in the result rows. NEVER rename or substitute (e.g. if the table says "Wealth Manager", do NOT say "Wealth Builder").
- NEVER compute or cite a percentage (e.g. "accounts for 73% of revenue") unless your SQL explicitly computes that percentage as a SELECT column. If it is not in the result, do not mention it.
- NEVER describe characteristics of a group (segment, product, customer) using data columns that are NOT in the SQL result. If only subcategory and avg_churn_score are returned, you can ONLY discuss churn scores — not income, credit scores, or customer types.
- If two rows have the same value (e.g. multiple subcategories all show 0.25 churn), say so honestly: "churn risk is nearly uniform across product types (~0.25)." Do NOT invent differentiation that is not in the data.

VIOLATIONS (examples of what NOT to do):
✗ SQL returns: persona_name, avg_clv → Narrative says "Wealth Builder is digitally native with excellent credit scores" (credit_score not in result)
✗ SQL returns: channel, conversion_rate → Narrative adds "especially effective for high-income 45–60 year olds" (no demographic data in result)
✗ sql=null strategy → Narrative says "This approach improves retention by 23%" (no data source)
✗ SQL returns: subcategory, avg_churn_score, customers → Narrative says "Mortgage: 0.23 churn, 215 customers" but table shows 0.25 and 5000 customers (numbers must match exactly)
✗ SQL returns: persona_name = "Wealth Manager" → Narrative says "Wealth Builder segment" (name must be copied exactly)
✗ SQL returns subcategory revenue → Narrative adds "these top 3 account for 73% of total revenue" (percentage not in result)

CORRECT behaviour:
✓ SQL returns: persona_name, avg_clv, avg_credit_score → Narrative says "avg credit score of **742**" (column is in result)
✓ sql=null → Narrative says "Based on the **247** incomplete applications we identified" (cited from conversation history)
✓ If a metric is NOT in the result, say "detailed breakdown unavailable — run a follow-up query" instead of inventing it.
✓ All subcategory churn scores are 0.25 → Narrative says "churn risk is nearly uniform across product types (all ~**0.25**)"

COLUMN COMPLETENESS — "characteristics" / "describe" / "profile" questions:
When the user asks "what are the key characteristics", "describe", "profile", or "compare" ANY group — your SQL MUST SELECT all the columns you will discuss in the narrative. Required columns per entity type:
- Segment/persona profile: segment_name, customer_count, avg_clv, avg_income, avg_credit_score, avg_churn_prob, avg_digital_engagement, avg_deposits
- Customer list: customer_id, customer_name, churn_probability, clv_tier, income, credit_score
- Product profile: product_name, subcategory, avg_rating, min_income, min_credit_score, credit_tier_required
  (use subcategory for grouping — 12 distinct types; category only has 3 values: Personal/Business/Agricultural)
NEVER return 2 columns (e.g., name + avg_clv only) then describe 6 characteristics in the narrative.

SEGMENT CHARACTERISTICS NARRATIVE — BEHAVIORAL INTERPRETATION REQUIRED:
When answering "key characteristics", "describe each segment", or "segment profiles", the narrative MUST go
beyond raw numbers and explain what each metric MEANS for that customer group. Raw numbers alone are NOT an insight.

Interpretation guide (use in narrative alongside the actual values):
- avg_credit_score < 620 → "subprime credit profile — limited product eligibility, elevated default risk"
- avg_credit_score 620–720 → "fair-to-good credit — eligible for standard personal products"
- avg_credit_score > 750 → "excellent credit — qualifies for premium cards and large loans"
- avg_digital_engagement < 0.4 → "branch-first / phone preference — low digital adoption"
- avg_digital_engagement 0.4–0.75 → "hybrid channel — comfortable with digital but still visits branches"
- avg_digital_engagement > 0.75 → "digital-native — prefers mobile/online, rarely visits branch"
- avg_churn_prob > 0.5 → "high retention risk — priority for proactive outreach campaigns"
- avg_churn_prob < 0.3 → "stable and loyal — low immediate churn concern"
- avg_deposits > 100K → "significant wealth on deposit — strong savings/investment orientation"
- avg_deposits < 20K → "low deposit base — transaction-focused, not savings-driven"
- avg_income > 100K → "affluent tier — suitable for wealth management and premium products"
- avg_income < 50K → "mass-market income band — cost-sensitive, fee-waiver eligibility matters"

Example of RIGHT narrative style (never just dump numbers):
WRONG: "Retiree Depositor has an average balance of $102,119, income of $63,119, credit score of 734."
RIGHT: "**Retiree Depositor** (**900 customers**): With an avg balance of **$102K** — nearly **1.6× their avg income of $63K** — this segment is savings-rich and wealth-preservation focused. Their excellent avg credit score of **734** qualifies them for premium deposit products. Low digital engagement (**0.25**) signals a branch-first relationship preference — digital campaigns alone will underperform here."

TEMPORAL LIMITATIONS — columns that do NOT exist in this database:
- "churn_in_next_30_days", "predicted_churn_date", "churn_forecast" → NO such columns
- For future-oriented churn questions: use churn_probability DESC + churn_risk_category='High' as the best available proxy
- For historical churn: filter WHERE churned = TRUE or WHERE churn_date IS NOT NULL
- NEVER claim the data shows "next 30 days" churn — it shows current churn probability only

PRODUCT RATINGS — avg_rating is GLOBAL, not per-segment:
- products.avg_rating is pre-computed across ALL customers — it is identical for all segments
- NEVER say "high-credit customers rate this product 4.6" — every customer sees the same rating
- When asked "which product do X-type customers prefer?" → use COUNT of transactions/impressions/wishlist for that group, NOT avg_rating
- avg_rating can be shown for comparison but must be labelled "overall product rating" not "segment rating"

INTERROGATIVE DATA QUESTIONS — ALWAYS REQUIRE SQL:
"Which", "Who", "What", "Show", "List", "Find", "Rank", "Give me" questions that ask for ranked/highest/lowest/top/bottom data are ALWAYS data retrieval questions. NEVER set sql=null for:
- "Which segment/customer/product has the highest/lowest X?"
- "Who are the top/bottom N customers by X?"
- "What is the average/total X by Y?"
- "Show me the segments/customers/products with..."
These MUST return a SELECT query. The narrative MUST open with the actual winner/answer's name and value.
✗ WRONG: "The segment with the highest churn risk is the one with the highest average churn probability." (circular definition, no data)
✓ CORRECT: "**Retiree Depositor** has the highest churn risk at an average probability of **0.73** across **412** customers."

Q: "Which customer segment has the highest churn risk?" (personas available)
RIGHT: SELECT pa.persona_name, ROUND(AVG(c.churn_probability), 3) AS avg_churn_prob, COUNT(*) AS customers
       FROM customers c JOIN persona_assignments pa ON c.customer_id = pa.customer_id
       GROUP BY pa.persona_name ORDER BY avg_churn_prob DESC

Q: "Which customer segment has the highest churn risk?" (personas NOT available — use segment_assignments)
RIGHT: SELECT sa.segment_name, ROUND(AVG(c.churn_probability), 3) AS avg_churn_prob,
              COUNT(*) AS customers, ROUND(AVG(c.customer_lifetime_value), 0) AS avg_clv
       FROM customers c JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       GROUP BY sa.segment_name ORDER BY avg_churn_prob DESC
chart: {"type": "bar", "x_col": "segment_name", "y_col": "avg_churn_prob", "title": "Churn Risk by Segment"}
— The narrative MUST name the top segment by its exact segment_name and cite the avg_churn_prob and count.
— NEVER use life_stage or churn_risk_category as the grouping column for this query.

HYBRID QUESTIONS — DATA + STRATEGY (ALWAYS generate SQL first):
Some questions combine "which segment / which customers / which product" (data) with "what should I do / campaign / recommend" (strategy).
These ALWAYS require SQL — never set sql=null for hybrid questions.

HYBRID TRIGGERS — generate SQL AND a strategy narrative:
- "which segment should I target for [campaign/offer/retention]"
- "which segment has [low engagement / high churn / low income]"
- "which product should I recommend to [segment / customers]"
- "I want to run a campaign to [X customers] — which segment / product"
- "identify customers / segments for [campaign / outreach / intervention]"
- "what segment should I focus on for [goal]"
- "draft a summary report", "performance summary", "performance insights", "platform health"
- "summary of [today's/this week's/this month's] performance" — use MAX(transaction_date) as reference date
- "report for [team/stakeholders]" when performance metrics can be derived from the data

For hybrid questions, the SQL identifies the data (segments, customers, products), and the narrative combines
the data findings WITH strategy recommendations. NEVER set sql=null when the question asks "which segment",
"which customers", or "which product" — these require actual data from the tables.

HYBRID EXAMPLE:
Q: "I want to run a campaign to low engagement customers to prevent churn, which segment should I identify and which product should I recommend?"
RIGHT:
SELECT sa.segment_name,
       COUNT(*) AS customers,
       ROUND(AVG(c.churn_probability), 3) AS avg_churn_prob,
       ROUND(AVG(c.digital_engagement_score), 3) AS avg_digital_score,
       ROUND(AVG(c.customer_lifetime_value), 0) AS avg_clv,
       ROUND(AVG(c.income), 0) AS avg_income
FROM customers c
JOIN segment_assignments sa ON c.customer_id = sa.customer_id
WHERE c.digital_engagement_score < 0.5
GROUP BY sa.segment_name
ORDER BY avg_churn_prob DESC
chart: {"type": "bar", "x_col": "segment_name", "y_col": "avg_churn_prob", "title": "Churn Risk — Low Engagement Segments"}
— Use segment_assignments (always available). NEVER join persona_assignments for this — it may be empty.
— The narrative MUST name the top segment by its EXACT segment_name from the result.
— Recommend a product by referencing the segment's income and credit_score profile from the result
   (e.g. if avg_income < 50K → suggest Meridian Everyday Checking; if avg_credit_score < 620 → suggest secured card).
— DO NOT invent product names — only reference products that exist in the products table.

Q: "Which segment has the highest churn risk and what product should I cross-sell?"
RIGHT:
SELECT sa.segment_name,
       COUNT(*) AS customers,
       ROUND(AVG(c.churn_probability), 3) AS avg_churn_prob,
       ROUND(AVG(c.credit_score), 0) AS avg_credit_score,
       ROUND(AVG(c.income), 0) AS avg_income,
       ROUND(AVG(c.total_deposits), 0) AS avg_deposits
FROM customers c
JOIN segment_assignments sa ON c.customer_id = sa.customer_id
GROUP BY sa.segment_name
ORDER BY avg_churn_prob DESC
LIMIT 5
chart: {"type": "bar", "x_col": "segment_name", "y_col": "avg_churn_prob", "title": "Churn Risk by Segment"}

Q: "Draft a summary report of today's performance" / "Give me a platform performance summary" / "Summarize recent activity"
Note: the database has static data (no live feed). Use MAX(transaction_date) as reference and report the most recent 90 days.
RIGHT:
SELECT CAST(transaction_date AS DATE) AS txn_date,
       COUNT(*) AS transactions,
       COUNT(DISTINCT customer_id) AS unique_customers,
       ROUND(SUM(amount), 0) AS revenue
FROM transactions
WHERE CAST(transaction_date AS DATE) >= (
    SELECT MAX(CAST(transaction_date AS DATE)) - INTERVAL '30' DAY FROM transactions
)
GROUP BY txn_date
ORDER BY txn_date DESC
LIMIT 30
chart: {"type": "line", "x_col": "txn_date", "y_col": "revenue", "title": "Daily Revenue — Last 30 Days"}
— Open narrative with the most recent date from the result and the total revenue for that period.
— Include total transaction count, unique customers, and avg daily revenue as bolded numbers.
— NEVER say "I need to consider several metrics" or list what TO track — show the actual data.
— If asked for a "report for engineering/platform teams", focus on volume (transaction count, unique customers) over revenue.

Q: "What is the overall platform health?" / "How is the platform performing?"
RIGHT:
SELECT
    (SELECT COUNT(DISTINCT customer_id) FROM customers) AS total_customers,
    (SELECT COUNT(*) FROM incomplete_applications) AS incomplete_applications,
    (SELECT COUNT(*) FROM wishlist) AS wishlist_items,
    (SELECT COUNT(DISTINCT customer_id) FROM transactions
     WHERE CAST(transaction_date AS DATE) >= (SELECT MAX(CAST(transaction_date AS DATE)) - INTERVAL '90' DAY FROM transactions)
    ) AS active_customers_90d,
    (SELECT ROUND(SUM(amount), 0) FROM transactions
     WHERE CAST(transaction_date AS DATE) >= (SELECT MAX(CAST(transaction_date AS DATE)) - INTERVAL '90' DAY FROM transactions)
    ) AS revenue_90d
chart: {"type": "none", "title": "Platform Health Summary"}
— Report each metric as a bolded number. Open with active customers and revenue as the headline KPIs.

STRATEGY & ADVISORY QUESTIONS — SET sql TO null:
ONLY set sql=null when the question is purely HOW to do something with NO identifiable data dimension.
If the question mentions "which segment", "which customers", "which product", "performance", "summary", or any metric to compute → use SQL.

Triggers for sql = null (pure strategy only):
- "How can Meridian Bank...", "How should we...", "How do we improve..."
- "What strategies would you suggest...", "What are the best ways to grow..."
- Follow-up questions after seeing data like "what should we do about this?" or "how can we fix this?"
- "Give me a retention strategy", "Suggest a marketing plan"
- Questions with NO data dimension and NO metric to compute

For strategy questions, write a narrative (200-300 words) that:
1. Opens with the business context and stakes (use numbers from conversation history if available)
2. Uses `## 1. Strategy Name` headers for 3-5 distinct actionable strategies
3. Each strategy has 2-3 specific bullet points with concrete tactics
4. Ends with a bold **Quick Win:** — the single highest-impact action to take in the next 30 days
5. chart.type = "none" (no chart for strategy answers)

Example narrative for "How can Meridian Bank retain high-value customers?":
These **10 Platinum customers** represent **$13.8M in CLV** — their retention is the bank's highest-priority growth lever.

## 1. Dedicated Relationship Management
- Assign each customer a named **Senior Relationship Manager** with quarterly in-person reviews
- Set up **proactive churn alerts**: flag any balance drop >20% or missed payment for immediate outreach

## 2. Premium Product Deepening
- With **$250K+ incomes** and excellent credit, offer **custom wealth management accounts** and **exclusive investment products** not available to standard tiers
- Cross-sell **premium travel rewards cards** — customers with 80+ digital engagement scores respond strongly to digital-first card offers

## 3. Loyalty Recognition
- Launch a **Meridian Platinum Circle** — fee waivers, priority processing, exclusive event invitations
- Celebrate milestones (account anniversaries, balance thresholds) with personal notes from branch managers

**Quick Win:** Call each of these **10 customers** this week — a proactive outreach from a Senior RM before their next billing cycle closes the highest-risk window.

STRATEGY QUESTION GROUNDING RULES:
- Only cite numbers that appeared in earlier conversation messages (e.g., "the **247** incomplete applications we found")
- NEVER cite industry benchmarks, generic statistics, or LLM-estimated percentages (no "23% retention uplift", no "3-5X ROI")
- If you lack grounding data, say: "Run a targeted query to validate this before acting" instead of inventing numbers
- Tactics must be specific to Meridian Bank (use actual product names, channel names from the schema)
- NO hypothetical numbers — every figure cited must come from the data or conversation history

CONTEXT CARRY-FORWARD — follow-up questions referencing prior results:
When the user's question contains "that segment", "that customer", "those customers", "from that segment",
"in that group", "the same segment", or similar anaphoric references, you MUST extract the referenced
entity from the CONVERSATION HISTORY and embed it directly in the SQL.

CONTEXT EXTRACTION RULES:
- "that segment" → find the segment name mentioned in the prior assistant message (e.g. "At-Risk Saver") and
  use it as a literal WHERE filter: WHERE sa.segment_name = 'At-Risk Saver'
  ALWAYS use single quotes. NEVER double quotes. NEVER backslash-escaped quotes.
- "that customer" / "that person" → find the customer_id or name from the prior message
- "from those results" / "in that group" → re-derive the filter logic as a CTE subquery

CONTEXT EXAMPLES:
Q (prior): "Which segment has the lowest number of customers?" → answer mentioned "At-Risk Saver"
Q (follow-up): "Which customer from that segment spent the most?"
RIGHT:
SELECT c.customer_id, c.customer_name,
       ROUND(SUM(t.amount), 0) AS total_spent
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
JOIN segment_assignments sa ON c.customer_id = sa.customer_id
WHERE sa.segment_name = 'At-Risk Saver'
GROUP BY c.customer_id, c.customer_name
ORDER BY total_spent DESC
LIMIT 1
chart: {"type": "none", "title": "Top Spender in At-Risk Saver"}
WRONG: WHERE sa.segment_name = "At-Risk Saver"   ← double quotes = identifier error in DuckDB
WRONG: WHERE sa.segment_name = \"At-Risk Saver\"  ← escaped quotes = parser error

Q (prior): "Which segment has the highest churn?" → answer mentioned "Digital Trendsetter"
Q (follow-up): "What products do customers in that segment hold?"
RIGHT:
SELECT p.product_name, p.subcategory, COUNT(DISTINCT t.customer_id) AS holders
FROM transactions t
JOIN products p ON t.product_id = p.product_id
JOIN segment_assignments sa ON t.customer_id = sa.customer_id
WHERE sa.segment_name = 'Digital Trendsetter'
GROUP BY p.product_name, p.subcategory
ORDER BY holders DESC LIMIT 10
chart: {"type": "bar", "x_col": "product_name", "y_col": "holders", "title": "Products Held by Digital Trendsetter"}

STRING LITERAL RULE FOR CONTEXT QUERIES — ABSOLUTE:
When embedding a segment name, product name, or any string from conversation history into SQL:
  CORRECT: WHERE sa.segment_name = 'At-Risk Saver'
  WRONG:   WHERE sa.segment_name = "At-Risk Saver"
  WRONG:   WHERE sa.segment_name = \"At-Risk Saver\"
Use ONLY single quotes for ALL string literals in SQL.

CONTEXT CARRY-FORWARD — "these customers / those customers / these top N" queries:
When the user says "these customers", "those top N customers", "for these customers", or any phrase that refers
back to a prior result set, you MUST re-derive that same set inside a subquery or CTE — do NOT query the full
customer table. Reconstruct the filter/ordering logic from the conversation history.

Examples:
Q (prior): "Who are the top 10 most valuable customers?"
  → prior SQL used: SELECT customer_id FROM customers ORDER BY customer_lifetime_value DESC LIMIT 10

Q (follow-up): "What are the preferred communication channels for these top 10 customers?"
WRONG: SELECT channel_preference, COUNT(*) FROM customers GROUP BY channel_preference   ← queries ALL customers
RIGHT: WITH top10 AS (
           SELECT customer_id FROM customers ORDER BY customer_lifetime_value DESC LIMIT 10
       )
       SELECT c.channel_preference AS preferred_channel, COUNT(*) AS customer_count
       FROM customers c
       WHERE c.customer_id IN (SELECT customer_id FROM top10)
       GROUP BY c.channel_preference
       ORDER BY customer_count DESC

RULE: The subquery in the CTE must exactly mirror the WHERE / ORDER BY / LIMIT from the prior question's logic.
NEVER drop the LIMIT or change the filter — the user is asking about a specific subset.

STRICT SQL RULES:
- Only SELECT statements. Never DROP/INSERT/UPDATE/DELETE/CREATE/ALTER.
- Table names are exactly as shown in the schema (lowercase, no backticks needed for DuckDB).
- Use ROUND(value, 2) for monetary amounts and rates.
- DuckDB date functions: date_trunc('month', col), strftime(col, '%Y-%m'), year(col), month(col).
- DATE DISPLAY: Always cast date/timestamp columns to DATE to strip the time component:
    CAST(started_date AS DATE) AS started_date  → shows 2025-06-04 not 2025-06-04T00:00:00
  Apply to ALL date columns in SELECT: started_date, completed_date, added_date, transaction_date, etc.
- String concat in DuckDB: col1 || ' ' || col2
STRING LITERALS — CRITICAL (DuckDB parser rule):
- ALWAYS use single quotes for string values: WHERE col = 'value'
- NEVER use double quotes for string values: WHERE col = "value"  ← double quotes = identifier in DuckDB, causes Parser Error
- NEVER use escaped double quotes: WHERE col = \"value\"  ← also invalid, causes syntax error at or near "\"
- CORRECT: WHERE sa.segment_name = 'Wealth Accumulator'
- WRONG:   WHERE sa.segment_name = "Wealth Accumulator"
- WRONG:   WHERE sa.segment_name = \"Wealth Accumulator\"
- This applies to ALL string literals: segment names, channel names, product names, statuses, categories, etc.

AGGREGATION — THE MOST IMPORTANT RULE:
Every comparison question MUST use GROUP BY + an aggregate function (SUM, AVG, COUNT).
Never return raw rows for a comparison or ranking question.

EXAMPLES (follow these exactly):

Q: "Which marketing channels have the highest ROI?"
WRONG: SELECT channel, persona, roi_pct FROM ad_spend ORDER BY roi_pct DESC
RIGHT: SELECT channel, ROUND(AVG(roi_pct), 2) AS avg_roi_pct FROM ad_spend GROUP BY channel ORDER BY avg_roi_pct DESC

Q: "ROAS by channel and persona" / "ROI by marketing persona" / "ROAS by marketing channel and persona"
WRONG: SELECT channel, persona, roas FROM ad_spend ORDER BY roas DESC
WRONG: SELECT pa.persona_name, ... FROM ad_spend JOIN persona_assignments ...  ← NEVER join persona_assignments for ad_spend
WRONG: SELECT p.category, a.channel, ... FROM ad_spend a JOIN products p ON a.product_id = p.product_id ...
       ← ad_spend has NO product_id column. NEVER join ad_spend to products or transactions. It is a standalone table.
RIGHT (by persona only): SELECT persona, ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0),2) AS roas FROM ad_spend GROUP BY persona ORDER BY roas DESC
RIGHT (by channel and persona): SELECT persona, channel, ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0),2) AS roas, ROUND(SUM(spend_usd),0) AS total_spend FROM ad_spend GROUP BY persona, channel ORDER BY roas DESC
— Use ad_spend.persona and ad_spend.channel directly. No JOIN needed or allowed for ad_spend ROAS queries.

Q: "How does transaction volume vary by customer segment over time?" / "transaction volume by segment" / "segment transaction trends"
WRONG: SELECT life_stage, SUM(amount) AS volume FROM transactions t JOIN customers c ON t.customer_id=c.customer_id GROUP BY life_stage
       ← NEVER use life_stage as a segment. life_stage (Family/Student/Professional/Retiree/Pre-Retiree) are NOT the Meridian segments.
RIGHT: SELECT sa.segment_name,
              strftime(t.transaction_date, '%Y-%m') AS month,
              ROUND(SUM(t.amount), 0) AS total_volume
       FROM transactions t
       JOIN segment_assignments sa ON t.customer_id = sa.customer_id
       GROUP BY sa.segment_name, month
       ORDER BY month, sa.segment_name
chart: {"type": "line", "x_col": "month", "y_col": "total_volume", "title": "Transaction Volume by Meridian Segment Over Time"}
— segment_name values in result MUST be: Retiree Depositor, Wealth Accumulator, Everyday Essential, Digital Trendsetter, At-Risk Saver.
— NEVER substitute life_stage, churn_risk_category, or customer_segment for segment_name.

Q: "Transaction volume by segment" / "which segment transacts the most?" (no time breakdown)
RIGHT: SELECT sa.segment_name, ROUND(SUM(t.amount), 0) AS total_volume, COUNT(*) AS transaction_count
       FROM transactions t
       JOIN segment_assignments sa ON t.customer_id = sa.customer_id
       GROUP BY sa.segment_name ORDER BY total_volume DESC
chart: {"type": "bar", "x_col": "segment_name", "y_col": "total_volume", "title": "Transaction Volume by Segment"}

Q: "Show average income per life stage"
WRONG: SELECT life_stage, income FROM customers ORDER BY income DESC
RIGHT: SELECT life_stage, ROUND(AVG(income),0) AS avg_income FROM customers GROUP BY life_stage ORDER BY avg_income DESC

Q: "Monthly spend trend"
WRONG: SELECT month, channel, spend_usd FROM ad_spend ORDER BY month
RIGHT: SELECT CAST(year AS VARCHAR)||'-'||LPAD(CAST(month AS VARCHAR),2,'0') AS month_key, ROUND(SUM(spend_usd),0) AS total_spend FROM ad_spend GROUP BY year, month, month_key ORDER BY year, month LIMIT 24

Q: "Which channel had highest cumulative ROAS?" / "2025 spend and revenue by channel" / "which marketing channel had highest ROAS this year?" / "show total spend, revenue, and ROAS by channel"
RIGHT: SELECT channel,
              ROUND(SUM(spend_usd), 0) AS total_spend,
              ROUND(SUM(revenue_usd), 0) AS total_revenue,
              ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0), 2) AS cumulative_roas
       FROM ad_spend
       WHERE year = 2025
       GROUP BY channel
       ORDER BY cumulative_roas DESC
chart: {"type": "bar", "x_col": "channel", "y_col": "total_spend", "title": "2025 Total Ad Spend by Channel"}
— NEVER add month/month_key to this query. Combining month AND channel produces 48 rows (12 months × 4 channels).
— The narrative LLM only receives the first 10 rows — it will describe January data only and produce wrong answers.
— For "by channel" ROAS / spend / revenue questions: GROUP BY channel only. 4 rows. Always correct.

Q: "What products are customers wishlisting but not applying for?"
WRONG: SELECT ... FROM wishlist w JOIN incomplete_applications i ON w.customer_id=i.customer_id AND w.product_id=i.product_id ...
RIGHT: SELECT p.product_name, p.subcategory, COUNT(*) AS wishlist_count
       FROM wishlist w
       JOIN products p ON w.product_id = p.product_id
       LEFT JOIN incomplete_applications i ON w.customer_id = i.customer_id AND w.product_id = i.product_id
       WHERE i.customer_id IS NULL
       GROUP BY p.product_name, p.subcategory
       ORDER BY wishlist_count DESC LIMIT 15
chart: {"type": "bar", "x_col": "product_name", "y_col": "wishlist_count", "title": "Wishlisted but Not Applied"}
— Do NOT join customers or persona_assignments for this query. Return product-level aggregates only.

Q: "Show customers who wishlisted a product but never applied for it" (customer-level list)
RIGHT: SELECT c.customer_id, c.customer_name, p.product_name, p.subcategory, w.added_date
       FROM wishlist w
       JOIN customers c ON w.customer_id = c.customer_id
       JOIN products p ON w.product_id = p.product_id
       LEFT JOIN incomplete_applications i ON w.customer_id = i.customer_id AND w.product_id = i.product_id
       WHERE i.customer_id IS NULL
       ORDER BY w.added_date DESC LIMIT 50
chart: {"type": "none", "title": "Customers Wishlisted but Not Applied"}
— Do NOT add persona/segment columns to this query. Narrative must only discuss product names and counts visible in the result.

LEFT JOIN RULES — "X but not Y" questions always use LEFT JOIN + WHERE right_table.id IS NULL:
- "customers who wishlisted but never applied" → LEFT JOIN incomplete_applications ... WHERE i.customer_id IS NULL
- "products shown but never clicked" → LEFT JOIN impressions ... WHERE click_count = 0 or IS NULL
- "customers with no transactions" → LEFT JOIN transactions ... WHERE t.customer_id IS NULL
- NEVER use INNER JOIN for "not in" or "but not" patterns — it returns 0 rows when tables don't overlap

Q: "Top products by revenue" / "Which products generate the most revenue?"
WRONG: SELECT product_name, revenue FROM products ORDER BY revenue DESC  (products has NO revenue column)
RIGHT: SELECT p.product_name, ROUND(SUM(t.amount),0) AS revenue
       FROM transactions t JOIN products p ON t.product_id = p.product_id
       GROUP BY p.product_name ORDER BY revenue DESC LIMIT 15

Q: "How does transaction volume vary by product category?" / "transaction volume by product type" / "breakdown by product category"
— products.category has only 3 values (Personal/Business/Agricultural) — use products.subcategory for a meaningful breakdown.
WRONG: SELECT p.category, ROUND(SUM(t.amount),0) AS total_volume
       FROM transactions t JOIN products p ON t.product_id = p.product_id
       GROUP BY p.category
RIGHT: SELECT p.subcategory, ROUND(SUM(t.amount),0) AS total_volume, COUNT(*) AS transaction_count
       FROM transactions t JOIN products p ON t.product_id = p.product_id
       GROUP BY p.subcategory ORDER BY total_volume DESC
chart: {"type": "bar", "x_col": "subcategory", "y_col": "total_volume", "title": "Transaction Volume by Product Type"}
— The narrative MUST use exact subcategory names (Checking, Savings, CD, Credit, Mortgage, etc.) not generic names like "Credit Cards" or "Loans".

Q: "Churn risk by transaction channel"
RIGHT: SELECT t.channel, ROUND(AVG(c.churn_probability)*100, 1) AS avg_churn_score, COUNT(DISTINCT c.customer_id) AS customers
       FROM transactions t JOIN customers c ON t.customer_id = c.customer_id
       GROUP BY t.channel ORDER BY avg_churn_score DESC

TWO KINDS OF CHANNELS — never confuse them:
- MARKETING channels (ad_spend table): email, sms, in_app, branch   ← 4 values, lowercase
- TRANSACTION channels (transactions table): Mobile, Online, Phone, ATM, Branch  ← 5 values, Title Case
- "which channel has highest ROI/ROAS/CPA/spend?" → use ad_spend, GROUP BY channel (4 groups)
- "transaction channel", "how customers transact", "ATM usage" → use transactions, GROUP BY channel (5 groups)
- ATM IS a valid transaction channel — always include it when querying transaction channels
- Do NOT apply ad_spend channel filter to transactions queries or vice versa

CRITICAL — COLUMN BANS:
- NEVER join ad_spend to products, transactions, or customers. ad_spend has NO product_id, customer_id, or foreign key. It is a pre-aggregated marketing table. All breakdowns come from its own columns: persona, channel, month, year.
- NEVER use `customer_segment` for grouping or filtering — it is 'Personal' for ALL 5000 customers and gives 1 useless row.
- NEVER use `customers.life_stage` as a substitute for a segment in "segment" questions. life_stage values (Family, Student, Professional, Retiree, Pre-Retiree) are demographic labels — NOT the Meridian Bank segments. For segment questions always use segment_assignments.segment_name (or persona_assignments.persona_name if Agent A ran).
- NEVER use `products.category` for "product type", "product breakdown", or "by product category" queries — it has only 3 values (Personal, Business, Agricultural) and collapses all retail banking products into one bar. Use `products.subcategory` instead, which has 12+ meaningful types: Checking, Savings, CD, Credit, Auto, Personal Loan, Home Equity, HELOC, Mortgage, Investment, Business Loan, Agricultural Loan.
- products has NO revenue column — compute revenue as SUM(transactions.amount) via JOIN on product_id.
- `customers` table has NO `customer_count` column. NEVER write `c.customer_count` where `c` is an alias for `customers`. Use `COUNT(*) AS customer_count` in a GROUP BY query, OR use `persona_stats.customer_count` (pre-computed) when joining persona_stats directly.

PERSONA_STATS SHORTCUT — use it for segment-level queries to avoid invalid column errors:
When asking for segment characteristics (churn, CLV, income, credit score, digital engagement, deposits):
- If persona_assignments IS registered: `persona_stats` has ALL these columns pre-computed — use it directly.
- CORRECT: SELECT persona_name, customer_count, avg_churn_prob, avg_clv, avg_income, avg_credit_score, avg_digital_engagement, avg_deposits FROM persona_stats ORDER BY avg_churn_prob DESC
- WRONG: SELECT pa.persona_name, c.customer_count, ROUND(AVG(c.churn_probability)...) FROM customers c JOIN persona_assignments pa ... (customer_count is NOT a column in customers)
- Use the JOIN approach ONLY when you need columns not in persona_stats (e.g. churn_date, life_stage, specific transaction data).

SEGMENT PRIORITY — follow this order strictly:
1. If persona_assignments table IS listed in the schema: use persona_name from persona_assignments (the 5 AI-refined segments from Agent A). Always JOIN persona_assignments ON customer_id and GROUP BY pa.persona_name.
2. If persona_assignments is NOT available: use segment_assignments view (ALWAYS available). JOIN segment_assignments sa ON customer_id and GROUP BY sa.segment_name. The 5 segment_name values are: 'Retiree Depositor', 'Wealth Accumulator', 'Everyday Essential', 'Digital Trendsetter', 'At-Risk Saver'.
   - NEVER use customers.life_stage for segment questions. life_stage (Family/Student/Professional/Retiree/Pre-Retiree) are demographic labels, NOT the Meridian Bank segments.
   - NEVER use customers.customer_segment — it contains 'Personal' for all 5000 rows and is useless for segmentation.
3. Use churn_risk_category (High/Medium/Low) ONLY when the question is specifically about churn or risk — not as a generic "segment".
4. Use clv_tier (Bronze/Silver/Gold/Platinum) ONLY when the user explicitly says "CLV tier", "value tier", or "tier". Never use clv_tier as a proxy for "segment" when segment_assignments is available.

Q: "What are the key characteristics of the customer segment with the highest churn risk?" / "describe the highest churn segment"
— persona_assignments IS registered → use persona_stats (has ALL needed columns pre-computed, NO invalid column errors):
RIGHT: SELECT persona_name, customer_count, avg_churn_prob, avg_clv, avg_income,
              avg_credit_score, avg_digital_engagement, avg_deposits
       FROM persona_stats ORDER BY avg_churn_prob DESC LIMIT 1
chart: {"type": "none", "title": "Highest Churn Risk Segment Profile"}
— Narrative: "**{persona_name}** is the highest-risk segment with avg churn probability of **{avg_churn_prob}**, **{customer_count}** customers, avg income **${avg_income}**, avg credit score **{avg_credit_score}**, and avg deposits **${avg_deposits}**."
— If question asks "top N segments" (not just the top 1): remove LIMIT 1 and add a chart.

Q: "What are the key characteristics of the customer segment with the highest churn risk?" (no personas registered)
RIGHT: SELECT churn_risk_category, COUNT(*) AS customer_count,
              ROUND(AVG(churn_probability), 3) AS avg_churn_prob,
              ROUND(AVG(income), 0) AS avg_income,
              ROUND(AVG(credit_score), 0) AS avg_credit_score,
              ROUND(AVG(digital_engagement_score), 3) AS avg_digital_engagement,
              ROUND(AVG(total_deposits), 0) AS avg_deposits
       FROM customers GROUP BY churn_risk_category ORDER BY avg_churn_prob DESC
chart: {"type": "bar", "x_col": "churn_risk_category", "y_col": "avg_churn_prob", "title": "Churn Risk by Category"}

Q: "key characteristics of top N personas by CLV" / "what are the characteristics of the highest CLV personas?" / "top personas profile"
— When the question asks for CHARACTERISTICS or PROFILE of personas, return ALL relevant columns from persona_stats so the narrative can cite real numbers.
RIGHT: SELECT persona_name, customer_count, avg_clv, avg_income, avg_credit_score,
              avg_churn_prob, avg_digital_engagement, avg_deposits
       FROM persona_stats ORDER BY avg_clv DESC LIMIT 2
chart: {"type": "bar", "x_col": "persona_name", "y_col": "avg_clv", "title": "Top 2 Personas by Average CLV"}
— The narrative MUST name the personas explicitly and cite their actual avg_income, avg_credit_score, avg_deposits from the data. NEVER describe characteristics generically without real numbers.

Q: "How do products vary across customer segments?" / "revenue by segment" / "breakdown by segment"
— persona_assignments IS available:
RIGHT: SELECT pa.persona_name, p.product_name, ROUND(SUM(t.amount),0) AS revenue
       FROM transactions t
       JOIN customers c ON t.customer_id = c.customer_id
       JOIN persona_assignments pa ON c.customer_id = pa.customer_id
       JOIN products p ON t.product_id = p.product_id
       GROUP BY pa.persona_name, p.product_name ORDER BY revenue DESC LIMIT 20

Q: "key characteristics of top segments by CLV" — persona_assignments NOT available (use segment_assignments):
WRONG: SELECT life_stage, ROUND(AVG(customer_lifetime_value),0) AS avg_clv FROM customers GROUP BY life_stage LIMIT 2
       ← life_stage is NOT a Meridian segment; use segment_assignments instead
RIGHT: SELECT sa.segment_name,
              COUNT(*) AS customer_count,
              ROUND(AVG(c.customer_lifetime_value),0) AS avg_clv,
              ROUND(AVG(c.income),0) AS avg_income,
              ROUND(AVG(c.credit_score),0) AS avg_credit_score,
              ROUND(AVG(c.digital_engagement_score),3) AS avg_digital_engagement,
              ROUND(AVG(c.churn_probability),3) AS avg_churn_prob
       FROM customers c
       JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       GROUP BY sa.segment_name ORDER BY avg_clv DESC LIMIT 5

Q: "Who are the most likely to churn in the next 30 days?" — NO forward churn column exists:
RIGHT: SELECT c.customer_id, c.customer_name, ROUND(c.churn_probability,3) AS churn_prob,
              c.churn_risk_category, c.clv_tier, ROUND(c.income,0) AS income
       FROM customers c
       WHERE c.churn_risk_category='High'
       ORDER BY c.churn_probability DESC LIMIT 25
— Note: this shows CURRENT churn probability (no "30-day" prediction exists in the data)
chart: {"type": "none", "title": "High Churn Risk Customers"}

Q: "revenue by segment" / "breakdown by segment"
— persona_assignments NOT available (use segment_assignments):
RIGHT: SELECT sa.segment_name, ROUND(SUM(t.amount),0) AS revenue
       FROM transactions t JOIN segment_assignments sa ON t.customer_id = sa.customer_id
       GROUP BY sa.segment_name ORDER BY revenue DESC
— NEVER use c.life_stage as the segment grouping column.

Q: "average churn risk by customer segment" / "churn risk by segment"
WRONG: SELECT customer_segment, AVG(churn_probability) ... GROUP BY customer_segment  ← 1 row, all 'Personal'
WRONG (no personas): SELECT churn_risk_category, ... FROM customers GROUP BY churn_risk_category
       ← this answers "churn risk by risk tier", NOT "churn risk by segment"
RIGHT (personas available): SELECT pa.persona_name, ROUND(AVG(c.churn_probability),3) AS avg_churn_prob, COUNT(*) AS customers,
              ROUND(AVG(c.customer_lifetime_value),0) AS avg_clv
       FROM customers c JOIN persona_assignments pa ON c.customer_id = pa.customer_id
       GROUP BY pa.persona_name ORDER BY avg_churn_prob DESC
RIGHT (no personas — use segment_assignments): SELECT sa.segment_name, ROUND(AVG(c.churn_probability),3) AS avg_churn_prob,
              COUNT(*) AS customers, ROUND(AVG(c.customer_lifetime_value),0) AS avg_clv
       FROM customers c JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       GROUP BY sa.segment_name ORDER BY avg_churn_prob DESC

Q: "How does transaction volume compare across segments?" / "transaction volume by segment"
RIGHT: SELECT sa.segment_name, COUNT(t.transaction_id) AS transaction_count, ROUND(SUM(t.amount),0) AS total_volume
       FROM transactions t JOIN segment_assignments sa ON t.customer_id = sa.customer_id
       GROUP BY sa.segment_name ORDER BY total_volume DESC
— Segment names MUST be: Retiree Depositor, Wealth Accumulator, Everyday Essential, Digital Trendsetter, At-Risk Saver
— NEVER use c.life_stage or GROUP BY life_stage for this question.

NUMBER FORMATTING RULE — VERY IMPORTANT:
Always return RAW numeric values (dollars, counts, scores). NEVER pre-divide by 1000, 1000000, or 1000000000.
The frontend automatically formats: 1500000 → "1.5M", 85000 → "85.0K", 450 → "450"
WRONG: ROUND(SUM(amount)/1000000, 2) AS volume_m  ← renders as "1.5" with no unit (confusing)
RIGHT: ROUND(SUM(amount), 0) AS total_amount       ← frontend renders as "1.5M" (correct)

AD_SPEND PERSONA RULE — CRITICAL:
The `ad_spend` table has its own `persona` column (5 marketing segments: e.g. "At Risk Saver", "Wealth Builder", etc.).
NEVER join persona_assignments with ad_spend. They are separate dimensions.
- ad_spend.persona is a marketing label, NOT the same as persona_assignments.persona_name.
- For any ad_spend query involving persona/segment: use ad_spend.persona directly with GROUP BY.

Q: "ROAS by persona" / "ROI by marketing persona" / "which persona has best ROAS?"
RIGHT: SELECT persona, ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0), 2) AS roas
       FROM ad_spend GROUP BY persona ORDER BY roas DESC
chart: {"type": "bar", "x_col": "persona", "y_col": "roas", "title": "ROAS by Marketing Persona"}

Q: "ROAS by channel and persona" / "ROI by channel and persona" / "How does ROI vary by channel and persona?"
RIGHT: SELECT persona, channel, ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0), 2) AS roas,
              ROUND(SUM(spend_usd), 0) AS total_spend
       FROM ad_spend GROUP BY persona, channel ORDER BY roas DESC
chart: {"type": "bar", "x_col": "persona", "y_col": "roas", "title": "ROAS by Persona and Channel"}
— GROUP BY persona, channel produces up to 20 rows (5 personas × 4 channels). Do NOT drop channel.
— Do NOT join persona_assignments. Do NOT use customer tables.

Q: "How does ROI vary by persona?" / "ROAS by persona only" (no channel breakdown requested)
RIGHT: SELECT persona, ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0), 2) AS roas,
              ROUND(SUM(spend_usd), 0) AS total_spend
       FROM ad_spend GROUP BY persona ORDER BY roas DESC
chart: {"type": "bar", "x_col": "persona", "y_col": "roas", "title": "ROAS by Marketing Persona"}

ROAS / ROI AGGREGATION — NEVER average pre-computed ratios:
- WRONG: AVG(roas), SUM(roas), MIN(roas) — mathematically meaningless; roas is already a ratio
- WRONG: AVG(conversion_rate), AVG(click_rate), AVG(open_rate) without considering row weights
- RIGHT: ROUND(SUM(revenue_usd) / NULLIF(SUM(spend_usd), 0), 2) AS roas
- RIGHT: ROUND(SUM(converted) / NULLIF(SUM(sent), 0), 4) AS conversion_rate
- RIGHT: ROUND(SUM(clicked) / NULLIF(SUM(sent), 0), 4) AS click_rate
Always re-derive rates from the underlying numerator/denominator columns.

CHURN COLUMN CLARIFICATION:
- churn_probability: current point-in-time score (0.0–1.0) — the ONLY available churn predictor
- churn_risk_category: categorical version of churn_probability ('High'/'Medium'/'Low')
- churned: Boolean — TRUE only for customers who have already left
- churn_date: date a customer left — NULL for active customers
- NO "churn_in_30_days", "predicted_churn", or "forward_churn_probability" columns exist
- For "most likely to churn": ORDER BY churn_probability DESC with WHERE churn_risk_category='High'

CUSTOMER TABLE PRIORITY — two tables have overlapping customer columns, NEVER join both:
- customers: the PRIMARY table. Use for churn, CLV, income, credit_score, life_stage, segments, and all customer queries. Column: total_deposits (deposits balance).
- customer_profile: SECONDARY, extended financial detail. Use ONLY when the question specifically asks for debt, assets, or extended loan/spending detail NOT in customers. Column: total_deposit_value (different name — NOT total_deposits).
- NEVER join customers + customer_profile in the same query — they share customer_id and overlap heavily.
- DEFAULT: always use `customers` unless the question cannot be answered from it.

DENORMALIZED COLUMNS (exist in BOTH customers AND customer_engagement — always alias):
- churn_risk_score, churn_risk_category, churn_probability, customer_lifetime_value, clv_tier
- When joining these two tables: always use table alias prefix → c.churn_risk_score NOT churn_risk_score
- Prefer customers table as primary source; avoid joining both tables on the same denormalized column

DIMENSION RULES:
- "by marketing channel" → ad_spend GROUP BY channel (4 values: email, sms, in_app, branch)
- "by transaction channel" → transactions GROUP BY channel (5 values: Mobile, Online, Phone, ATM, Branch)
- "by preferred communication channel" → customers GROUP BY channel_preference (3 values: Digital, Branch, Hybrid)
- "by segment" / "by customer segment" / "by persona" → if persona_assignments is in schema: JOIN persona_assignments GROUP BY persona_name (5 AI segments); else JOIN segment_assignments sa ON customer_id GROUP BY sa.segment_name (5 Meridian Bank segments: Retiree Depositor, Wealth Accumulator, Everyday Essential, Digital Trendsetter, At-Risk Saver). NEVER GROUP BY life_stage for segment questions.
- "by CLV tier" / "by tier" → GROUP BY clv_tier (Bronze/Silver/Gold/Platinum) — only when tier is explicitly mentioned
- "by marketing channel AND persona" (ad_spend only) → SELECT persona, channel, ... FROM ad_spend GROUP BY persona, channel (20 combinations: 5 personas × 4 channels). NEVER drop the channel column. NEVER join persona_assignments for ad_spend queries.
- "trend over time" → GROUP BY year, month ORDER BY year, month
- ad_spend pre-computed columns (roas, roi_pct, cpa) are PER-ROW — always re-derive from SUM(revenue_usd)/NULLIF(SUM(spend_usd),0), NEVER use AVG(roas)
- Target 5–15 rows for chart queries. Use LIMIT 10 for top-N, LIMIT 20 for two-dimension, LIMIT 24 for monthly.

Q: "What are the preferred communication channels for each segment?" / "preferred channel by persona" / "how do segments differ in channel preference?"
— persona_assignments IS available:
RIGHT: WITH ranked AS (
         SELECT pa.persona_name AS segment, c.channel_preference AS preferred_channel,
                COUNT(DISTINCT c.customer_id) AS customer_count,
                ROW_NUMBER() OVER (PARTITION BY pa.persona_name ORDER BY COUNT(DISTINCT c.customer_id) DESC) AS rn
         FROM persona_assignments pa
         JOIN customers c ON pa.customer_id = c.customer_id
         GROUP BY pa.persona_name, c.channel_preference
       )
       SELECT segment, preferred_channel, customer_count FROM ranked WHERE rn = 1 ORDER BY customer_count DESC
chart: {"type": "bar", "x_col": "segment", "y_col": "customer_count", "title": "Preferred Communication Channel per Segment"}
— x_col MUST be "segment" (persona_name), NOT a compound label. Each bar represents one persona; the narrative explains which channel each persona prefers.
— NEVER concatenate persona_name with customer_segment or any other column.

Q: "What are the preferred communication channels for each segment?" / "channel distribution by segment"
— persona_assignments NOT available (use segment_assignments):
RIGHT: SELECT sa.segment_name AS segment, c.channel_preference AS preferred_channel,
              COUNT(DISTINCT c.customer_id) AS customer_count
       FROM customers c
       JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       GROUP BY sa.segment_name, c.channel_preference
       ORDER BY sa.segment_name, customer_count DESC LIMIT 20
chart: {"type": "bar", "x_col": "segment", "y_col": "customer_count", "title": "Preferred Channel by Segment"}
— NEVER use c.life_stage as the segment here.

Q: "What is the overall preferred communication channel?" / "channel preference breakdown" (no segment grouping)
RIGHT: SELECT channel_preference AS preferred_channel, COUNT(DISTINCT customer_id) AS customer_count
       FROM customers GROUP BY channel_preference ORDER BY customer_count DESC
chart: {"type": "bar", "x_col": "preferred_channel", "y_col": "customer_count", "title": "Communication Channel Preferences"}

PRODUCT COMPATIBILITY RULES — always apply when recommending products to specific customers:
Never recommend a product the customer cannot qualify for. Check:
  - income >= p.min_income
  - credit_score >= p.min_credit_score
  - credit_tier_required: 'any'=all, 'fair'=credit_score>=580, 'good'=credit_score>=670, 'excellent'=credit_score>=740

Q: "What products can customer CUST_001 qualify for?" / "Recommend compatible products for this customer"
RIGHT: SELECT p.product_name, p.subcategory, p.avg_rating,
              p.credit_tier_required, p.min_income
       FROM products p CROSS JOIN customers c
       WHERE c.customer_id = 'CUST_001'
         AND c.income >= p.min_income
         AND c.credit_score >= p.min_credit_score
         AND (p.credit_tier_required = 'any'
           OR (p.credit_tier_required = 'fair'      AND c.credit_score >= 580)
           OR (p.credit_tier_required = 'good'      AND c.credit_score >= 670)
           OR (p.credit_tier_required = 'excellent' AND c.credit_score >= 740))
       ORDER BY p.avg_rating DESC LIMIT 10

Q: "Which products are best for high-churn / low-engagement / at-risk customers?" / "Recommend products for at-risk segment"
RIGHT: SELECT p.product_name, p.subcategory,
              COUNT(DISTINCT c.customer_id) AS eligible_customers,
              ROUND(AVG(p.avg_rating), 2) AS avg_rating,
              ROUND(AVG(c.churn_probability), 3) AS avg_churn_prob
       FROM customers c
       JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       CROSS JOIN products p
       WHERE sa.segment_name = 'At-Risk Saver'
         AND c.income >= p.min_income
         AND c.credit_score >= p.min_credit_score
         AND (p.credit_tier_required = 'any'
           OR (p.credit_tier_required = 'fair'      AND c.credit_score >= 580)
           OR (p.credit_tier_required = 'good'      AND c.credit_score >= 670)
           OR (p.credit_tier_required = 'excellent' AND c.credit_score >= 740))
         AND p.category = 'Personal'
       GROUP BY p.product_name, p.subcategory ORDER BY eligible_customers DESC LIMIT 10

Q: "Which products should I recommend to low-engagement customers for a retention campaign?"
RIGHT: SELECT p.product_name, p.subcategory,
              COUNT(DISTINCT c.customer_id) AS eligible_customers,
              ROUND(AVG(p.avg_rating), 2) AS avg_rating
       FROM customers c
       CROSS JOIN products p
       WHERE c.digital_engagement_score < 0.5
         AND c.income >= p.min_income
         AND c.credit_score >= p.min_credit_score
         AND (p.credit_tier_required = 'any'
           OR (p.credit_tier_required = 'fair'      AND c.credit_score >= 580)
           OR (p.credit_tier_required = 'good'      AND c.credit_score >= 670)
           OR (p.credit_tier_required = 'excellent' AND c.credit_score >= 740))
         AND p.category = 'Personal'
         AND p.complexity_score <= 2
       GROUP BY p.product_name, p.subcategory ORDER BY eligible_customers DESC LIMIT 10
— Use complexity_score <= 2 for low-engagement customers (simpler products improve adoption).

SEGMENT → PRODUCT MAPPING (use as narrative context, not SQL logic):
- At-Risk Saver (credit ~568, income ~$35K): Meridian Essential Checking, Meridian Secured Card, Meridian Basic Savings
- Everyday Essential (credit ~708, income ~$73K): Meridian Plus Checking, Meridian Cash Back Card, Meridian Basic Savings
- Digital Trendsetter (credit ~698, income ~$83K, digital 0.91): Meridian Cash Back Card, Meridian Rewards Visa, Meridian High-Yield Savings
- Retiree Depositor (credit ~779, income ~$62K, deposits $184K): Meridian 24-Month CD, Meridian Money Market, Meridian Traditional IRA
- Wealth Accumulator (credit ~808, income ~$195K): Meridian Platinum Card, Meridian Prestige Checking, Meridian HELOC

NEVER use CROSS JOIN without a compatibility WHERE clause — it produces ineligible recommendations.

CUSTOMER LIST QUERIES — USE chart.type = "none":
When the SQL returns individual customer records (one row per customer or transaction), a chart is NOT useful because the x-axis would be customer IDs or names. For these queries, always use chart type "none" so the table view is shown instead.
Triggers for chart type "none":
- "which customers...", "list customers...", "who are the customers...", "show me customers..."
- "which customers started...", "customers who...", "find customers..."
- "show incomplete applications", "show wishlist customers", "which transactions..."
- Any query where x_col would be customer_id, customer_name, or transaction_id

Q: "Top N customers by total transaction value" / "highest spending customers" / "most valuable customers by transactions" / "top 20 customers by transaction value"
— customers.annual_transaction_value is PRE-COMPUTED — use it directly, DO NOT join transactions.
RIGHT: SELECT c.customer_id, c.customer_name,
              COALESCE(sa.segment_name, 'Unassigned') AS segment_name,
              c.clv_tier,
              ROUND(c.annual_transaction_value, 0) AS total_transaction_value
       FROM customers c
       LEFT JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       ORDER BY c.annual_transaction_value DESC
       LIMIT 20
chart: {"type": "none", "x_col": "customer_name", "y_col": "total_transaction_value", "title": "Top 20 Customers by Transaction Value"}
WRONG: SELECT ... FROM customers c JOIN transactions t ON ... GROUP BY ... ORDER BY SUM(t.amount) DESC
— annual_transaction_value (on customers table) already contains the aggregated total — no need for transactions JOIN.
— NEVER use CURRENT_DATE, DATEADD, DATE_SUB, or DATEDIFF — these are unsupported in DuckDB and will crash the query.

Q: "High-value dormant customers" / "CLV customers who haven't transacted recently" / "Platinum/Gold digital customers not active" / "dormant digital re-engagement"
RIGHT: SELECT c.customer_id, c.customer_name, c.clv_tier,
              c.days_since_last_transaction, c.channel_preference,
              COALESCE(sa.segment_name, 'Unassigned') AS segment_name,
              ROUND(c.customer_lifetime_value, 0) AS clv
       FROM customers c
       LEFT JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       WHERE c.clv_tier IN ('Platinum', 'Gold')
         AND c.channel_preference IN ('Digital', 'Hybrid')
         AND c.days_since_last_transaction >= 30
       ORDER BY c.customer_lifetime_value DESC
       LIMIT 25
chart: {"type": "none", "x_col": "customer_name", "y_col": "days_since_last_transaction", "title": "Dormant High-Value Digital Customers"}
— CRITICAL: days_since_last_transaction max value is ~48 in this dataset. NEVER filter >= 90 (zero rows guaranteed).
— Use >= 30 as the dormancy threshold — returns ~145 Platinum/Gold customers with digital channel preference.
— Include BOTH 'Digital' AND 'Hybrid' in channel_preference — both groups prefer digital interactions.
— USE c.days_since_last_transaction for dormancy — NEVER compute from CURRENT_DATE or join transactions.
— clv_tier values: 'Platinum', 'Gold', 'Silver', 'Bronze' — use exact strings with single quotes.

Q: "ad spend by channel and ROAS" / "which marketing channel has the highest ROAS" / "channel performance"
RIGHT: SELECT channel,
              SUM(spend_usd)    AS total_spend,
              SUM(revenue_usd)  AS total_revenue,
              ROUND(SUM(revenue_usd) / NULLIF(SUM(spend_usd), 0), 2) AS roas,
              ROUND(AVG(cpa), 2) AS avg_cpa,
              SUM(sent)          AS total_contacts
       FROM ad_spend
       GROUP BY channel
       ORDER BY roas DESC
chart: {"type": "bar", "x_col": "channel", "y_col": "roas", "title": "ROAS by Marketing Channel"}
— ad_spend has NO customer_id, product_id, or date column. GROUP by channel, persona, month, or year only.
— "impressions" does NOT exist in ad_spend — use sent (contacts reached) instead.
— ad_spend covers 2025 only (year=2025, months 1–12). For "last 6 months": WHERE year = 2025 AND month >= 7

Q: "monthly ad spend trend" / "spend by month" / "monthly channel performance"
RIGHT: SELECT month, month_name, channel, SUM(spend_usd) AS spend, SUM(revenue_usd) AS revenue,
              ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0), 2) AS roas
       FROM ad_spend
       WHERE year = 2025
       GROUP BY month, month_name, channel
       ORDER BY month, channel
chart: {"type": "line", "x_col": "month_name", "y_col": "spend", "title": "Monthly Ad Spend by Channel"}
— ad_spend has INTEGER year and month columns (not a date). Use WHERE year = 2025 to get all 2025 data.
— For "last 6 months" use WHERE year = 2025 AND month >= 7

Q: "Which customers started an application but never completed it?" / "Show incomplete applications"
RIGHT: SELECT c.customer_id, c.customer_name,
              p.product_name, p.subcategory,
              i.started_date,
              c.churn_risk_category, c.clv_tier
       FROM incomplete_applications i
       JOIN customers c ON i.customer_id = c.customer_id
       JOIN products p ON i.product_id = p.product_id
       ORDER BY i.started_date DESC
       LIMIT 50
chart: {"type": "none", "x_col": "customer_name", "y_col": "product_name", "title": "Incomplete Applications"}

Q: "How many customers have incomplete applications by product?" (aggregated version — bar chart ok)
RIGHT: SELECT p.product_name, COUNT(*) AS incomplete_count,
              ROUND(AVG(c.customer_lifetime_value), 0) AS avg_clv
       FROM incomplete_applications i
       JOIN customers c ON i.customer_id = c.customer_id
       JOIN products p ON i.product_id = p.product_id
       GROUP BY p.product_name ORDER BY incomplete_count DESC LIMIT 15
chart: {"type": "bar", "x_col": "product_name", "y_col": "incomplete_count", "title": "Incomplete Applications by Product"}

Q: "What are the most common reasons for incomplete applications?" / "Where do customers abandon?" / "Which step has the most drop-off?"
RIGHT: SELECT last_step, COUNT(*) AS count
       FROM incomplete_applications
       GROUP BY last_step
       ORDER BY count DESC
chart: {"type": "bar", "x_col": "last_step", "y_col": "count", "title": "Application Abandonment by Step"}
— last_step EXACT values: 'personal_info', 'financial_details', 'review', 'sign', 'document_upload'
— NEVER rename these to "Income Verification", "Identity Verification", or any human-readable label not in the data.
— The narrative MUST use the exact last_step string values from the result rows (e.g. "**personal_info** has the most drop-off with **45** abandonments").

Q: "Which segment has the most incomplete applications?" / "Incomplete applications by segment"
RIGHT: SELECT sa.segment_name, COUNT(*) AS incomplete_count
       FROM incomplete_applications i
       JOIN customers c ON i.customer_id = c.customer_id
       JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       GROUP BY sa.segment_name ORDER BY incomplete_count DESC
chart: {"type": "bar", "x_col": "segment_name", "y_col": "incomplete_count", "title": "Incomplete Applications by Segment"}

INDIVIDUAL CUSTOMER LOOKUP — name-based queries (e.g. "George Davis is from which segment?"):
When the user mentions a specific customer name, use LIKE for fuzzy matching then return their segment, profile, or other data.
ALWAYS use LEFT JOIN for both persona_assignments and segment_assignments — NEVER INNER JOIN — so results
appear even before Agent A has been run.
RIGHT: SELECT c.customer_id, c.customer_name,
              COALESCE(pa.persona_name, sa.segment_name) AS segment_name,
              c.income, c.credit_score, c.clv_tier
       FROM customers c
       LEFT JOIN persona_assignments pa ON c.customer_id = pa.customer_id
       LEFT JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       WHERE c.customer_name LIKE '%George%Davis%'
chart: {"type": "none", "title": "Customer Segment Lookup"}
— The narrative MUST use the EXACT segment_name value from the result row. NEVER rename or substitute.
— If the result has 0 rows: report "No customer named X was found in the database."
— If the result has EXACTLY 1 row: answer the question directly using that row's values.
— If the result has 2+ rows: this means MULTIPLE customers share that name. The narrative MUST open with:
   "Found **N customers** named '[name]' in the database. Please clarify which one you mean:"
   Then list EACH customer on its own bullet with their customer_id, segment_name, income, and credit_score.
   End with: "Reply with the customer ID (e.g. **CUST_00123**) to get details for a specific customer."
   Do NOT pick one silently. Do NOT answer the original question until the user disambiguates.

INDIVIDUAL CUSTOMER LOOKUP — ID-based queries (e.g. user replies "CUST_00003" or "tell me about CUST_00003"):
When the user provides a customer ID directly, look up their full profile using that ID.
ALWAYS use LEFT JOIN — NEVER INNER JOIN — so the row is returned even without Agent A data.
RIGHT: SELECT c.customer_id, c.customer_name,
              COALESCE(pa.persona_name, sa.segment_name) AS segment_name,
              c.income, c.credit_score, c.clv_tier,
              ROUND(c.churn_probability, 3) AS churn_probability,
              ROUND(c.customer_lifetime_value, 0) AS clv,
              c.channel_preference, c.digital_engagement_score
       FROM customers c
       LEFT JOIN persona_assignments pa ON c.customer_id = pa.customer_id
       LEFT JOIN segment_assignments sa ON c.customer_id = sa.customer_id
       WHERE c.customer_id = 'CUST_00003'
chart: {"type": "none", "title": "Customer Profile"}
— Always use the exact ID string the user provided (case-sensitive, e.g. 'CUST_00003').
— NEVER use INNER JOIN here — persona_assignments may be empty if Agent A has not been run.

CHART RULES:
- none: Use for customer-listing queries (x-axis would be customer_id or names) — table is more useful
- none: Use when SQL returns exactly 1 row (a single COUNT, SUM, or AVG). ONE bar is meaningless — state the number boldly in the narrative instead. e.g. "**800 customers** are in the At-Risk Saver segment."
- none: Use for strategy/advisory answers (sql=null)
- none: Use for customer profile lookups (single customer, ID-based)
- bar: categorical comparisons (channels, segments, products) — 5–15 groups
- line: time-series (monthly, yearly) — x_col must be a date/month/year column
- area: cumulative trends over time
- pie: ONLY for 5 or fewer categories. Never pie with >5 groups
- If the question cannot be answered with SQL, set sql to null
- Always run SQL for any data question — never just give narrative text

Respond ONLY with a valid JSON object — no markdown fences:
{
  "sql": "SELECT ... or null for strategy/advisory questions",
  "narrative": "**Key metric in bold** — rich Markdown narrative with bullets and a Recommendation at the end.",
  "chart": {"type": "bar|line|pie|area|none", "x_col": "column_name", "y_col": "column_name", "title": "Chart title"},
  "follow_ups": ["question 1", "question 2", "question 3"]
}"""


def _build_prompt(question: str, history: List[Dict], schema: str) -> str:
    history_block = ""
    if history:
        lines = []
        for h in history[-8:]:
            role = "User" if h.get("role") == "user" else "Assistant"
            content = str(h.get("content", ""))[:500]
            lines.append(f"{role}: {content}")
        history_block = "CONVERSATION HISTORY:\n" + "\n".join(lines) + "\n\n"

    return f"""{schema}

{history_block}USER QUESTION: {question}

Generate the SQL, narrative, chart config, and follow-up questions as a JSON object."""


# ── LLM call ──────────────────────────────────────────────────────────────────

def _call_llm(prompt: str) -> str:
    try:
        from utils.claude_client import get_claude_client
        client = get_claude_client()
        if client.is_available():
            return client.generate_text(
                prompt=prompt,
                system=_SQL_SYSTEM,
                max_tokens=2000,
                temperature=0.1,
                agent_name="chatbot",
                call_type="sql_generation",
            )
    except Exception as e:
        logger.warning("ClaudeClient failed: %s, trying TogetherAI", e)

    try:
        from utils.together_ai import together_ai
        return together_ai.generate_text(
            prompt=prompt,
            system_message=_SQL_SYSTEM,
            max_tokens=2000,
            temperature=0.1,
        )
    except Exception as e2:
        logger.error("All LLM calls failed: %s", e2)
        raise RuntimeError(f"No LLM available: {e2}")


# ── Grounded narrative generator (second-stage LLM call) ─────────────────────

_NARRATIVE_SYSTEM = (
    "You are a banking data analyst writing a short narrative (3-5 sentences) about a query result.\n"
    "Rules:\n"
    "1. Open with the single most important finding in **bold** (name + value).\n"
    "2. Use **bold** for EVERY number, name, product, segment, and category you mention.\n"
    "3. ONLY cite values that appear in the provided table rows — NEVER invent, rename, or paraphrase them.\n"
    "   If a column shows 'personal_info', say **personal_info** — do NOT rename it to 'Personal Information'.\n"
    "   If a column shows 'financial_details', say **financial_details** — not 'Financial Verification'.\n"
    "4. NEVER cite a number that is not in the table. NEVER compute percentages unless the table has them.\n"
    "5. Add a '**Recommendation:**' sentence ONLY when the answer involves segment strategy, product fit, campaign targeting, customer behaviour patterns, or risk/retention. OMIT it for simple factual lookups (how many, count, list, name queries).\n"
    "6. No section headers. Use bullet points only if listing 3+ items. Output plain text — NOT JSON.\n"
    "7. Format ALL monetary values (revenue, spend, income, balance, deposit, cost, amount) as **$X.XK** / **$X.XM** / **$X.XB** — NEVER write raw decimals. Examples: 135600.0 → **$135.6K**, 2300000 → **$2.3M**. Non-monetary metrics (ROAS, scores, counts) use bold without $: **5.69 ROAS**, **1,247 customers**.\n"
    "FORBIDDEN phrases — NEVER write these (they signal hallucination and will be rejected):\n"
    "  'the data suggests', 'we can infer', 'it appears that', 'it seems that', 'may indicate',\n"
    "  'could indicate', 'further analysis', 'based on available data', 'the results indicate',\n"
    "  'industry average', 'typical bank', 'generally speaking', 'it is worth noting',\n"
    "  'a significant number', 'many customers', 'most customers' (without citing exact count),\n"
    "  'the query identifies', 'this query returns', 'the query retrieves', 'the query filters',\n"
    "  'are at risk of churn if not re-engaged', 'have a high lifetime value and are'.\n"
    "NEVER describe what the query does — describe what the DATA shows. Do not open with 'The query identifies...' or 'This query returns...' — open with the actual finding: how many customers, who they are, and what their values are.\n"
    "If you cannot find a specific value in the table rows, say 'not available in this result' — do NOT guess."
)


def _table_to_text(table: Dict[str, Any], max_rows: int = 10) -> str:
    columns = table.get("columns", [])
    rows = table.get("rows", [])[:max_rows]
    if not columns or not rows:
        return "(no data)"
    header = " | ".join(columns)
    divider = "-" * max(len(header), 40)
    lines = [header, divider] + [" | ".join(str(v) for v in row) for row in rows]
    extra = len(table.get("rows", [])) - max_rows
    if extra > 0:
        lines.append(f"... and {extra} more rows")
    return "\n".join(lines)


def _generate_grounded_narrative(question: str, table: Dict[str, Any]) -> str:
    """
    Second-stage LLM call: generate a factual narrative from actual query results.
    The table data is passed explicitly so the LLM can only cite real values.
    Called when the first-stage narrative was detected as hollow/hallucinated.
    """
    table_text = _table_to_text(table)
    n_rows = len(table.get("rows", []))
    prompt = (
        f"Question: {question}\n\n"
        f"SQL result ({n_rows} row{'s' if n_rows != 1 else ''}):\n{table_text}\n\n"
        "Write the narrative (3-5 sentences, plain text, no JSON):"
    )
    try:
        from utils.claude_client import get_claude_client
        client = get_claude_client()
        if client.is_available():
            return client.generate_text(
                prompt=prompt,
                system=_NARRATIVE_SYSTEM,
                max_tokens=400,
                temperature=0.1,
                agent_name="chatbot",
                call_type="narrative_grounding",
            ).strip()
    except Exception as e:
        logger.warning("Claude grounded narrative failed: %s, trying TogetherAI", e)

    try:
        from utils.together_ai import together_ai
        return together_ai.generate_text(
            prompt=prompt,
            system_message=_NARRATIVE_SYSTEM,
            max_tokens=400,
            temperature=0.1,
        ).strip()
    except Exception as e2:
        logger.warning("Grounded narrative generation failed: %s", e2)
        return ""


# ── JSON parsing (robust) ─────────────────────────────────────────────────────

def _parse_response(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start < 0 or end <= start:
        return {"narrative": cleaned, "sql": None}
    try:
        return json.loads(cleaned[start:end])
    except json.JSONDecodeError:
        result: Dict[str, Any] = {}
        for field in ("sql", "narrative"):
            m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned, re.DOTALL)
            if m:
                try:
                    result[field] = json.loads('"' + m.group(1) + '"')
                except Exception:
                    result[field] = m.group(1)
        m2 = re.search(r'"follow_ups"\s*:\s*\[([^\]]*)\]', cleaned, re.DOTALL)
        if m2:
            result["follow_ups"] = re.findall(r'"([^"]+)"', m2.group(1))
        return result


# ── SQL safety ────────────────────────────────────────────────────────────────

_UNSAFE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE|MERGE|REPLACE|ATTACH|INSTALL|COPY)\b",
    re.IGNORECASE,
)

def _sanitize_sql(sql: str) -> str:
    """
    Fix common LLM SQL generation mistakes before execution.
    Handles escaped/double-quoted string literals that DuckDB rejects.
    """
    if not sql:
        return sql
    # Step 1: literal backslash-quote sequences (\") → single quote
    sql = sql.replace('\\"', "'")
    # Step 2: double-quoted VALUES after comparison operators → single-quoted
    sql = re.sub(
        r'([=!<>])\s{0,6}"([A-Za-z][A-Za-z0-9 _\-]*)"',
        lambda m: f"{m.group(1)} '{m.group(2)}'",
        sql,
    )
    # Step 3: LIKE "value" → LIKE 'value'
    sql = re.sub(
        r'\bLIKE\s+"([^"]+)"',
        lambda m: f"LIKE '{m.group(1)}'",
        sql, flags=re.IGNORECASE,
    )
    # Step 4: IN ("val1", "val2") → IN ('val1', 'val2')
    sql = re.sub(
        r'\bIN\s*\(([^)]+)\)',
        lambda m: 'IN (' + re.sub(r'"([^"]+)"', lambda n: f"'{n.group(1)}'", m.group(1)) + ')',
        sql, flags=re.IGNORECASE,
    )
    return sql


def _aggressive_sanitize_sql(sql: str) -> str:
    """
    Second-pass sanitizer for SQL that failed with a parser/syntax error.
    Converts ALL remaining double-quoted strings that look like values to single quotes.
    Less conservative than _sanitize_sql — only used on retry.
    """
    if not sql:
        return sql
    sql = _sanitize_sql(sql)
    # Convert any remaining "Text Value" after WHERE/AND/OR/ON clauses
    sql = re.sub(
        r'(?<=\bWHERE\b.{0,120})"([^"]{2,60})"',
        lambda m: f"'{m.group(1)}'",
        sql, flags=re.IGNORECASE | re.DOTALL,
    )
    sql = re.sub(
        r'(?<=\bAND\b.{0,60})"([^"]{2,60})"',
        lambda m: f"'{m.group(1)}'",
        sql, flags=re.IGNORECASE | re.DOTALL,
    )
    sql = re.sub(
        r'(?<=\bOR\b.{0,60})"([^"]{2,60})"',
        lambda m: f"'{m.group(1)}'",
        sql, flags=re.IGNORECASE | re.DOTALL,
    )
    return sql


# ── Domain guardrail ──────────────────────────────────────────────────────────

_OUT_OF_SCOPE_RE = re.compile(
    r'\b(recipe|ingredient|how to cook|how to bake|how to make\b|cuisine|'
    r'\bfood\b|\bdish\b|\bmeal\b|restaurant|menu|calories|nutrition|diet|'
    r'weather|forecast|temperature|climate|'
    r'\bsport\b|football|soccer|cricket|basketball|tennis|baseball|golf|rugby|'
    r'movie|film|\bshow\b|series|episode|\bactor\b|\bactress\b|celebrity|'
    r'singer|musician|\bsong\b|\bmusic\b|album|playlist|'
    r'\bjoke\b|funny|humor|laugh|meme|'
    r'\bpoem\b|poetry|\bessay\b|\bstory\b|fiction|novel|'
    r'translate|translation|\bgrammar\b|'
    r'\bcrypto\b|bitcoin|ethereum|\bnft\b|'
    r'who invented|when was.*born|what country|capital city|'
    r'workout|\bgym\b|exercise|fitness|'
    r'\bhotel\b|\bflight\b|airline|vacation|holiday|tourist|destination)',
    re.IGNORECASE,
)

_IN_SCOPE_RE = re.compile(
    r'\b(customer|segment|product|loan|credit|mortgage|deposit|banking|'
    r'churn|transaction|revenue|clv|income|score|campaign|recommend|'
    r'meridian|synapse|agent|persona|offer|channel|digital|engagement|'
    r'saver|accumulator|trendsetter|at.risk|retiree|depositor|'
    r'portfolio|account|balance|interest|apr|savings|checking|card|'
    r'wealth|analytics|dashboard|incomplete|application|wishlist|'
    r'how many|average|total|top \d|which segment|which product|show me|'
    r'ad.spend|roas|conversion|impression|click|churn.prob|clv.tier)\b',
    re.IGNORECASE,
)

_OUT_OF_SCOPE_REPLY = {
    "success": True,
    "narrative": (
        "I'm **Segment AI**, the intelligence assistant for the **Synapse Finance Platform**. "
        "I'm built specifically to answer questions about Meridian Bank's customer segments, "
        "products, transactions, churn risk, ad spend, and agent pipeline data.\n\n"
        "I can't help with questions outside the Synapse platform scope. Here are some things I can do:\n\n"
        "- *Which segment has the highest churn risk?*\n"
        "- *How many customers are in the At-Risk Saver segment?*\n"
        "- *What products should I recommend to low-engagement customers?*\n"
        "- *Show me incomplete applications by product*\n"
        "- *Which channel has the best ROAS this year?*"
    ),
    "sql": None,
    "table": None,
    "chart": {"type": "none"},
    "follow_ups": [
        "Which segment has the highest churn probability?",
        "What are the key characteristics of each customer segment?",
        "Which products are most popular among Wealth Accumulator customers?",
    ],
    "sql_error": None,
}


def _safe_sql(sql: str) -> bool:
    if not sql:
        return False
    stripped = sql.strip().upper()
    if not (stripped.startswith("SELECT") or stripped.startswith("WITH")):
        return False
    return not _UNSAFE.search(sql)


# ── SQL execution ─────────────────────────────────────────────────────────────

def _exec_sql(sql: str) -> Dict[str, Any]:
    con = _get_con()
    df: pd.DataFrame = con.execute(sql).df()
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("").astype(str)
        else:
            df[col] = df[col].fillna(0)
    columns = df.columns.tolist()
    rows = df.values.tolist()
    clean_rows = []
    for row in rows:
        clean_row = []
        for v in row:
            if isinstance(v, float) and v != v:
                clean_row.append("")
            elif hasattr(v, "item"):
                clean_row.append(v.item())
            else:
                clean_row.append(v)
        clean_rows.append(clean_row)
    return {"columns": columns, "rows": clean_rows}


# ── Auto-aggregation (safety net for ungrouped LLM queries) ──────────────────

def _auto_aggregate(table: Dict[str, Any], llm_chart: Dict) -> Dict[str, Any]:
    """
    Detect when the LLM returned raw per-row data instead of aggregated results,
    and collapse it by the chart's x_col.

    Triggered when:
      - result has >15 rows, AND
      - the chart x_col has duplicate values (ratio unique/total < 0.5), AND
      - the result is not already a time-series (x_col doesn't look like a date/month col)
    """
    columns = table.get("columns") or []
    rows = table.get("rows") or []

    if len(rows) <= 15 or not columns:
        return table

    x_col = llm_chart.get("x_col") or ""
    y_col = llm_chart.get("y_col") or ""

    if x_col not in columns or y_col not in columns:
        return table

    # Don't aggregate time-series columns
    time_keywords = ("month", "year", "date", "week", "quarter", "period", "time")
    if any(kw in x_col.lower() for kw in time_keywords):
        return table

    xi = columns.index(x_col)
    yi = columns.index(y_col)

    x_values = [str(r[xi]) for r in rows]
    unique_x = list(dict.fromkeys(x_values))  # preserve order

    # Only auto-aggregate when there are many duplicates
    if len(unique_x) >= len(rows) * 0.6:
        return table

    logger.info(
        "Auto-aggregating: %d rows → %d unique %s values (duplicate ratio %.2f)",
        len(rows), len(unique_x), x_col, 1 - len(unique_x) / len(rows)
    )

    # Decide: sum for revenue/count/total columns, avg for rates/scores/pct
    sum_keywords = ("revenue", "spend", "amount", "count", "total", "cost", "sales", "profit")
    use_sum = any(kw in y_col.lower() for kw in sum_keywords)

    from collections import defaultdict
    groups: Dict[str, List[float]] = defaultdict(list)
    for r in rows:
        xv = str(r[xi])
        try:
            yv = float(r[yi])
            groups[xv].append(yv)
        except (ValueError, TypeError):
            pass

    agg_rows = []
    for xv in unique_x:
        ys = groups.get(xv, [])
        if not ys:
            continue
        agg_y = sum(ys) if use_sum else sum(ys) / len(ys)
        agg_rows.append([xv, round(agg_y, 2)])

    # Sort descending by aggregated y
    agg_rows.sort(key=lambda r: r[1], reverse=True)

    y_label = f"total_{y_col}" if use_sum else f"avg_{y_col}"
    return {"columns": [x_col, y_label], "rows": agg_rows}


# ── Chart config resolution ───────────────────────────────────────────────────

def _resolve_chart(columns: List[str], rows: List[List], llm_chart: Dict) -> Dict:
    if not columns or not rows:
        return {"type": "none"}

    chart_type = (llm_chart.get("type") or "bar").lower()
    if chart_type == "none":
        return {"type": "none"}
    if chart_type not in ("bar", "line", "pie", "area"):
        chart_type = "bar"

    def is_numeric(ci: int) -> bool:
        sample = [r[ci] for r in rows[:20] if ci < len(r) and r[ci] not in ("", None)]
        if not sample:
            return False
        try:
            [float(v) for v in sample]
            return True
        except (ValueError, TypeError):
            return False

    numeric_cols = [c for i, c in enumerate(columns) if is_numeric(i)]
    label_cols = [c for c in columns if c not in numeric_cols]

    # No numeric columns → nothing meaningful to plot; show table only
    if not numeric_cols:
        return {"type": "none"}

    x_col = llm_chart.get("x_col")
    if x_col not in columns:
        x_col = label_cols[0] if label_cols else columns[0]

    # Suppress chart when x-axis would be individual customer IDs or names (not useful for charting)
    _id_keywords = ("customer_id", "transaction_id", "customer_name")
    if x_col and any(kw in x_col.lower() for kw in _id_keywords):
        return {"type": "none"}
    # Also suppress if the x-axis values look like CUST_##### ID patterns
    if rows and x_col in columns:
        xi = columns.index(x_col)
        sample_vals = [str(r[xi]) for r in rows[:5] if xi < len(r) and r[xi] is not None]
        import re as _re
        if sample_vals and all(_re.match(r'CUST_', v) for v in sample_vals):
            return {"type": "none"}

    y_col = llm_chart.get("y_col")
    if y_col not in columns:
        y_col = numeric_cols[0] if numeric_cols else (columns[1] if len(columns) > 1 else columns[0])

    title = llm_chart.get("title") or "Query Results"

    if chart_type == "pie" and len(rows) > 8:
        chart_type = "bar"

    return {"type": chart_type, "x_col": x_col, "y_col": y_col, "title": title}


# ── Default follow-ups ────────────────────────────────────────────────────────

def _default_follow_ups(q: str) -> List[str]:
    q = q.lower()
    if any(w in q for w in ("churn", "retention", "risk")):
        return [
            "Which products do high-churn customers currently hold?",
            "What is the average CLV of critical-risk customers?",
            "Show churn risk breakdown by customer segment",
        ]
    if any(w in q for w in ("segment", "persona", "cluster", "archetype")):
        return [
            "What is the average income and credit score per segment?",
            "Which segment has the highest product adoption rate?",
            "Show transaction volume by segment for recent activity",
        ]
    if any(w in q for w in ("product", "application", "incomplete", "wishlist")):
        return [
            "Which customer segment holds this product most?",
            "How many customers wishlisted but never applied?",
            "Show incomplete applications grouped by product",
        ]
    if any(w in q for w in ("spend", "roas", "channel", "marketing", "campaign")):
        return [
            "Which channel has the best ROAS by persona?",
            "Show monthly spend trend across all channels",
            "What is the cost-per-acquisition by channel?",
        ]
    if any(w in q for w in ("revenue", "clv", "lifetime", "value")):
        return [
            "Show average CLV by customer segment",
            "Which products generate the most revenue?",
            "What is total expected revenue by churn risk tier?",
        ]
    return [
        "Show this data broken down by customer segment",
        "Which customers are at highest risk of leaving?",
        "What products are driving the most revenue?",
    ]


# ── Main entrypoint ───────────────────────────────────────────────────────────

def ask_chatbot(
    question: str,
    history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Main chatbot entrypoint.

    Returns dict with keys:
      success, narrative, sql, table ({columns, rows}), chart, follow_ups, sql_error
    """
    history = history or []

    # Domain guardrail — reject questions outside Synapse/banking scope before calling LLM
    if _OUT_OF_SCOPE_RE.search(question) and not _IN_SCOPE_RE.search(question):
        logger.info("Segment AI: out-of-scope question blocked: %.80s", question)
        return _OUT_OF_SCOPE_REPLY

    # Agent A detection — warn when segment/persona questions asked without personas registered
    _segment_keywords = ("segment", "persona", "wealth builder", "digital native", "at risk", "cluster")
    _needs_personas = any(kw in question.lower() for kw in _segment_keywords)
    _personas_warning = (
        "\n\n> **Note:** Persona assignments are not yet generated — answering using the **5 Meridian Bank segments** "
        "(heuristic-derived: Retiree Depositor, Wealth Accumulator, Everyday Essential, Digital Trendsetter, At-Risk Saver). "
        "Run **Agent A** for AI-refined segmentation."
    ) if (_needs_personas and not _PERSONAS_REGISTERED) else ""

    schema = build_schema_context()
    prompt = _build_prompt(question, history, schema)

    try:
        raw = _call_llm(prompt)
    except Exception as e:
        logger.exception("LLM unavailable")
        return {
            "success": False,
            "error": f"AI model unavailable: {e}",
            "narrative": "The AI model is currently unavailable. Please check TOGETHER_API_KEY or ANTHROPIC_API_KEY.",
            "sql": None, "table": None, "chart": None, "follow_ups": [],
        }

    parsed = _parse_response(raw)
    sql = (parsed.get("sql") or "").strip()
    narrative = (parsed.get("narrative") or "").strip()
    follow_ups = parsed.get("follow_ups") or []
    llm_chart = parsed.get("chart") or {}

    # Retry when LLM set sql=null for an interrogative data question.
    # Questions starting with Which/Who/What/Show/List/Find are data retrieval, not advisory.
    _INTERROGATIVE = re.compile(r'^\s*(which|who|what|show|list|find|rank|give me)\b', re.IGNORECASE)
    _ADVISORY_WORDS = ('how can', 'how should', 'how do we', 'what strategies', 'what should we do',
                       'what are the best ways', 'how to retain', 'how to grow', 'how to improve')
    _is_advisory = any(t in question.lower() for t in _ADVISORY_WORDS)
    if not sql and _INTERROGATIVE.match(question) and not _is_advisory:
        retry_prompt = _build_prompt(
            question + "\n\n[SYSTEM OVERRIDE: This is a DATA RETRIEVAL question. "
            "You MUST write a SELECT SQL query. Setting sql=null is FORBIDDEN here. "
            "Open the narrative with the actual answer (segment name + exact number).]",
            history, schema,
        )
        try:
            raw2 = _call_llm(retry_prompt)
            parsed2 = _parse_response(raw2)
            if (parsed2.get("sql") or "").strip():
                parsed = parsed2
                sql = parsed2["sql"].strip()
                narrative = (parsed2.get("narrative") or "").strip()
                follow_ups = parsed2.get("follow_ups") or []
                llm_chart = parsed2.get("chart") or {}
                logger.info("Segment AI: interrogative retry succeeded, SQL acquired.")
        except Exception as _retry_exc:
            logger.warning("Interrogative retry failed: %s", _retry_exc)

    # Normalize narrative formatting and number display
    if narrative:
        # Convert literal \n sequences (backslash-n as two chars) the LLM sometimes emits into real newlines
        narrative = narrative.replace('\\n', '\n')
        # Strip stray trailing backslashes left before newlines (e.g. "sentence. \<newline>")
        narrative = re.sub(r'\\ *\n', '\n', narrative)
        narrative = re.sub(r'\\$', '', narrative, flags=re.MULTILINE)
        # Inject newlines before bullets/headers the LLM compacted inline (- or * markers)
        narrative = re.sub(r'([.!?;:])\s+([*-] (?=[A-Z\*`\d]))', r'\1\n\2', narrative)
        narrative = re.sub(r'([^\n])(## )', r'\1\n\2', narrative)
        narrative = re.sub(r'([^\n])(### )', r'\1\n\2', narrative)
        narrative = re.sub(r'([.!?])\s+(\*\*Recommendation)', r'\1\n\n\2', narrative)
        # ── Pass 1: auto-bold bare numbers ≥ 1,000 (not already in ** markers) ──
        _MONEY_KW = re.compile(
            r'\b(revenue|spend(?:ing)?|income|salary|balance|deposit(?:s)?|clv|'
            r'cost(?:s)?|value|amount|budget|lifetime\s+value|roas|return\s+on|'
            r'total\s+spend|total\s+revenue|ad\s+spend|marketing|profit(?:ability)?)\b',
            re.IGNORECASE,
        )

        def _bold_bare(mb: re.Match) -> str:
            raw = mb.group(1).replace(',', '')
            try:
                return f'**{mb.group(1)}**' if abs(float(raw)) >= 1_000 else mb.group(1)
            except ValueError:
                return mb.group(1)

        narrative = re.sub(r'(?<!\*)\b(\d[\d,]*(?:\.\d+)?)\b(?!\*)', _bold_bare, narrative)

        # ── Pass 2: K/M/B formatting + context-aware $ sign for bolded numbers ──
        def _fmt_bold_num(m: re.Match) -> str:
            inner = m.group(1)
            has_dollar = inner.startswith('$')
            raw = inner.lstrip('$').replace(',', '')
            try:
                n = float(raw)
            except ValueError:
                return m.group(0)
            a = abs(n)
            # Add $ when a money-context keyword appears within 100 chars before this number
            if not has_dollar and a >= 100:
                ctx_start = max(0, m.start() - 100)
                if _MONEY_KW.search(narrative[ctx_start:m.start()]):
                    has_dollar = True
            prefix = '$' if has_dollar else ''
            if a >= 1_000_000_000:
                return f'**{prefix}{n/1_000_000_000:.1f}B**'
            if a >= 1_000_000:
                return f'**{prefix}{n/1_000_000:.1f}M**'
            if a >= 1_000:
                return f'**{prefix}{n/1_000:.1f}K**'
            return m.group(0)

        narrative = re.sub(r'\*\*(\$?[\d,]+(?:\.\d+)?)\*\*', _fmt_bold_num, narrative)

    table = None
    chart = None
    sql_error = None

    if sql:
        sql = _sanitize_sql(sql)
        if not _safe_sql(sql):
            sql_error = "Only SELECT queries are permitted."
            sql = None
        else:
            try:
                table = _exec_sql(sql)
                if table and table.get("columns"):
                    rows = table.get("rows", [])
                    if not rows:
                        # Zero rows returned — override narrative so it cannot hallucinate
                        join_count = sql.upper().count("JOIN")
                        if join_count >= 2:
                            narrative = (
                                "The query returned **0 rows**. This usually means one of the joined tables "
                                "has no matching data — for example, `persona_assignments` may not be populated "
                                "(run Agent A first), or there are no records matching the filter conditions.\n\n"
                                "**Recommendation:** Run Agent A to generate persona assignments, then retry this query."
                            )
                        else:
                            narrative = (
                                "The query returned **0 rows** — no records match the specified conditions. "
                                "Try broadening the filter or checking if the data has been loaded."
                            )
                        chart = {"type": "none"}
                    else:
                        # Duplicate-name guard: if all rows share the same customer_name
                        # the narrative was written before SQL ran and is hallucinated.
                        # Override with a disambiguation message so the user can pick the right record.
                        _col_lower = [c.lower() for c in table["columns"]]
                        if "customer_name" in _col_lower and len(rows) >= 2:
                            _name_idx = _col_lower.index("customer_name")
                            _names = {r[_name_idx] for r in rows}
                            if len(_names) == 1:
                                _cname = next(iter(_names))
                                _bullets = []
                                for _r in rows:
                                    _rd = dict(zip(table["columns"], _r))
                                    _cid = _rd.get("customer_id") or _rd.get("CUSTOMER_ID", "?")
                                    _seg = (
                                        _rd.get("segment_name") or _rd.get("persona_name")
                                        or _rd.get("SEGMENT_NAME") or _rd.get("PERSONA_NAME")
                                        or "unknown segment"
                                    )
                                    _inc = _rd.get("income") or _rd.get("INCOME")
                                    _cs  = _rd.get("credit_score") or _rd.get("CREDIT_SCORE")
                                    _inc_str = f", income **${float(_inc):,.0f}**" if _inc is not None else ""
                                    _cs_str  = f", credit score **{_cs}**" if _cs is not None else ""
                                    _bullets.append(f"- **{_cid}**: {_seg}{_inc_str}{_cs_str}")
                                narrative = (
                                    f"Found **{len(rows)} customers** named **{_cname}** in the database. "
                                    "Please clarify which one you mean:\n\n"
                                    + "\n".join(_bullets)
                                    + "\n\nReply with the customer ID (e.g. **CUST_00123**) to get details for a specific customer."
                                )
                                chart = {"type": "none"}

                        # Auto-aggregate if the LLM returned ungrouped rows (safety net)
                        table = _auto_aggregate(table, llm_chart)

                        # Single-row chart suppression — 1 bar is never useful; show as text
                        if len(table.get("rows", [])) == 1:
                            chart = {"type": "none"}
                        else:
                            chart = chart or _resolve_chart(table["columns"], rows, llm_chart)
            except Exception as e:
                _raw_error = str(e)
                logger.warning("SQL execution failed: %s\nSQL: %s", e, sql[:400])

                # Auto-retry with aggressive sanitization on parser/syntax errors
                # (covers escaped-quote issues in context follow-up questions)
                _retried = False
                if any(kw in _raw_error.lower() for kw in ("syntax error", "parser error", "near \"\\")):
                    try:
                        _sql_retry = _aggressive_sanitize_sql(sql)
                        if _sql_retry != sql:
                            logger.info("Segment AI: retrying with aggressive sanitization")
                            table = _exec_sql(_sql_retry)
                            sql = _sql_retry
                            _retried = True
                            if table and table.get("columns"):
                                rows = table.get("rows", [])
                                table = _auto_aggregate(table, llm_chart)
                                if len(table.get("rows", [])) == 1:
                                    chart = {"type": "none"}
                                else:
                                    chart = _resolve_chart(table["columns"], rows, llm_chart)
                    except Exception as _e2:
                        logger.warning("Retry also failed: %s", _e2)
                        _raw_error = str(_e2)

                if not _retried:
                    sql_error = _raw_error
                    # User-friendly fallback — never show raw DuckDB error messages
                    _is_quote_error   = any(kw in _raw_error.lower() for kw in ("syntax error", "parser error", "near"))
                    _is_join_error    = "join" in _raw_error.lower() or "no such column" in _raw_error.lower()
                    _is_schema_error  = any(kw in _raw_error.lower() for kw in (
                        "catalog error", "binder error", "does not exist",
                        "no such table", "dateadd", "date_sub", "datediff",
                        "unknown function", "function.*not.*found", "scalar function",
                    ))
                    if _is_quote_error:
                        narrative = (
                            "I wasn't able to retrieve data for this question — the query contained a formatting issue.\n\n"
                            "**Try rephrasing** with the full segment name, e.g.: "
                            "*\"Which customer in the At-Risk Saver segment spent the most?\"*\n\n"
                            "**Recommendation:** Providing the specific segment or customer ID directly helps me generate an accurate query."
                        )
                    elif _is_join_error:
                        narrative = (
                            "I couldn't find matching data for this question. This may mean **Agent A** hasn't been run yet "
                            "(persona assignments are empty), or the filter conditions returned no matching rows.\n\n"
                            "**Recommendation:** Run **Agent A** to generate persona assignments, then retry."
                        )
                    elif _is_schema_error:
                        narrative = (
                            "The query used a function or column name that isn't supported in this database.\n\n"
                            "**Common causes:** unsupported date functions (`DATEADD`, `DATE_SUB`, `DATEDIFF`), "
                            "or a column name that doesn't exist in the table.\n\n"
                            "**Recommendation:** Try rephrasing — for example: "
                            "*\"Who are the top 20 customers by transaction value?\"*"
                        )
                    else:
                        narrative = (
                            "I wasn't able to answer this question with the available data.\n\n"
                            "**Possible reasons:** the filter conditions matched no records, or the question references "
                            "data that hasn't been loaded yet.\n\n"
                            "**Recommendation:** Try rephrasing, or ask a related question like "
                            "*\"Show me all customers in the At-Risk Saver segment\"* to explore the data first."
                        )
                    chart = {"type": "none"}

    # Detect "hollow" narratives: hallucinated or circular text written before SQL ran.
    # When table data is available, validate the narrative is grounded in real values.
    # If hollow, trigger a second-stage LLM call that passes the actual table rows.
    if narrative and table and table.get("rows"):
        _HOLLOW_RE = re.compile(
            # Circular definitions
            r'is the one with the highest|score between 0 and 1|is a critical metric'
            r'|are determined by their|directly affects customer|improve customer loyalty'
            r'|churn risk is defined as|probability score ranging'
            # Placeholder/advisory language masquerading as narrative
            r'|are likely to be those with|driven by their transaction history'
            r'|the exact product names|can inform the bank'
            r'|are critical for targeted|given the segment.s moderate'
            r'|would need to be analyzed|would require further analysis'
            r'|we would need to look at|it is important to note that'
            r'|analyzing these|to develop targeted'
            # Speculative estimation without data
            r'|can be estimated by|would need to consider|actual profit'
            r'|cost of servicing|revenue generated from their|additional factors such as'
            r'|to determine the actual|profitability.*consider|consider.*profitability'
            r'|cannot be directly calculated|not directly available|would require additional'
            r'|based on general banking|industry average|typical bank'
            # Hedging / inference language (LLM pretending to know without data)
            r'|the data suggests|this suggests|these results suggest|the analysis suggests'
            r'|we can infer|we can observe|we can see that|as we can see'
            r'|it appears that|it seems that|appears to indicate|seems to indicate'
            r'|may indicate|could indicate|might indicate|may suggest|could suggest'
            r'|further investigation|further analysis|deeper analysis|additional analysis'
            r'|a significant number of customers|many customers|most customers'
            r'|generally speaking|in general terms|on average.*customers'
            r'|it is worth noting|it should be noted|note that|notably'
            r'|based on available data|based on the data|based on this data'
            r'|the query result|the sql result|as shown in the query'
            r'|the results indicate|the results show|the table shows'
            r'|according to the data|from the data we can'
            # Query-description masquerading as insight (pre-execution hallucination)
            r'|the query identifies|this query identifies|the query retrieves|the query filters'
            r'|the query returns|this query returns|the query selects|the query finds'
            r'|customers who prefer digital|customers who have not transacted'
            r'|have a high lifetime value and are|lifetime value and are at risk'
            r'|are at risk of churn if not re|if not re-engaged',
            re.IGNORECASE,
        )
        # Hollow patterns are specific enough — flag regardless of bold numbers present
        _is_hollow = bool(_HOLLOW_RE.search(narrative))

        # Also catch narratives that describe what data "would show" without showing it
        _SPECULATIVE_RE = re.compile(
            r'\blikely\b.*\bproduct|\bprobably\b|\bwould be\b.*\bthose\b'
            r'|\bexact\b.*\bnames?\b|\bcorresponding\b.*\bcounts?\b'
            r'|\bmight be\b.*\bthose\b|\bcould be\b.*\bthose\b'
            r'|\bappears to be\b|\bseems to be\b'
            r'|\btypically\b.*\bsegment|\bgenerally\b.*\bcustomer'
            r'|\bwe expect\b|\bwe anticipate\b'
            r'|\bit is likely\b|\bit is possible\b|\bit may be\b',
            re.IGNORECASE,
        )
        if not _is_hollow and _SPECULATIVE_RE.search(narrative):
            _is_hollow = True

        # Unfilled template placeholders: LLM wrote {avg_income} or ${avg_clv} instead of real values
        if not _is_hollow and re.search(r'\$?\{[a-z][a-z_]*\}', narrative):
            _is_hollow = True
            logger.info("Segment AI: unfilled placeholders detected in narrative — triggering grounded replacement.")

        # Category name cross-validation: extract bold non-numeric terms from narrative (e.g. "Income Verification",
        # "Personal Loan") and check that at least one appears in the actual result rows.
        # If NONE of the bolded category names appear in the table, the narrative was hallucinated.
        if not _is_hollow:
            _bold_categories = re.findall(r'\*\*([A-Za-z][A-Za-z ]{3,})\*\*', narrative)
            # Only check when we have 2+ category names (skip numeric-only narratives)
            if len(_bold_categories) >= 2:
                _all_cell_text = ' '.join(
                    str(v).lower()
                    for row in table.get('rows', [])
                    for v in row
                    if v is not None
                ).lower()
                _col_text = ' '.join(c.lower() for c in table.get('columns', []))
                _searchable = _all_cell_text + ' ' + _col_text
                _matches = sum(
                    1 for w in _bold_categories
                    if w.lower() in _searchable
                )
                if _matches == 0:
                    _is_hollow = True
                    logger.info(
                        "Segment AI: bold category names %s not found in table — triggering grounded replacement.",
                        _bold_categories[:4],
                    )

        # Single-row number validation: bold numbers in narrative must match the one result row.
        # Catches "1429 customers" in narrative when table says 766.
        if not _is_hollow:
            _rows = table.get('rows', [])
            if len(_rows) == 1:
                _result_nums = set()
                for _v in _rows[0]:
                    if _v is not None:
                        try:
                            _result_nums.add(str(int(float(str(_v).replace(',', '')))))
                        except (ValueError, TypeError):
                            pass
                _bold_nums = re.findall(r'\*\*([\d,]+)\*\*', narrative)
                if _bold_nums and _result_nums:
                    _num_match = any(bn.replace(',', '') in _result_nums for bn in _bold_nums)
                    if not _num_match:
                        _is_hollow = True
                        logger.info(
                            "Segment AI: narrative numbers %s don't match 1-row result %s — triggering grounded replacement.",
                            _bold_nums[:4], list(_result_nums)[:4],
                        )

        if _is_hollow:
            logger.info("Segment AI: hollow narrative detected — generating grounded replacement.")
            grounded = _generate_grounded_narrative(question, table)
            if grounded:
                narrative = grounded
            else:
                # Grounded LLM call also failed — show a safe static fallback so the user
                # at least sees the table with a neutral header instead of a blank narrative
                _n_rows = len(table.get("rows", []))
                narrative = (
                    f"The query returned **{_n_rows} row{'s' if _n_rows != 1 else ''}**. "
                    "Please review the table below for the full results."
                )

    if not follow_ups:
        follow_ups = _default_follow_ups(question)

    # Append Agent A warning to narrative if applicable
    if _personas_warning and narrative:
        narrative = narrative + _personas_warning

    return {
        "success": True,
        "narrative": narrative,
        "sql": sql,
        "table": table if (table and table.get("columns")) else None,
        "chart": chart,
        "follow_ups": follow_ups[:3],
        "sql_error": sql_error,
        "personas_registered": _PERSONAS_REGISTERED,
    }


# ── Agent A status ───────────────────────────────────────────────────────────

def is_personas_registered() -> bool:
    """Return True if Agent A has been run and persona_assignments is available."""
    return _PERSONAS_REGISTERED


# ── Anomaly detection ─────────────────────────────────────────────────────────

_ANOMALY_QUERIES = [
    {
        "id": "high_value_churn",
        "title": "High-Value Customers at Churn Risk",
        "severity": "critical",
        "description": "Gold/Platinum customers with churn probability > 0.6",
        "sql": """
            SELECT c.customer_name, c.customer_id, c.clv_tier,
                   ROUND(c.churn_probability, 3) AS churn_prob,
                   ROUND(c.customer_lifetime_value, 0) AS clv,
                   ROUND(c.income, 0) AS income
            FROM customers c
            WHERE c.churn_probability > 0.6
              AND c.clv_tier IN ('Gold', 'Platinum')
            ORDER BY c.customer_lifetime_value DESC
            LIMIT 15
        """,
    },
    {
        "id": "wishlist_gap",
        "title": "High-Wishlist Products with Low Conversion",
        "severity": "warning",
        "description": "Products wishlisted 10+ times where buyers are far fewer than wishlisters — indicating interest without purchase",
        "sql": """
            SELECT p.product_name, p.subcategory,
                   COUNT(DISTINCT w.customer_id) AS wishlisted_by,
                   COUNT(DISTINCT t.customer_id) AS actually_purchased,
                   ROUND(
                       CASE WHEN COUNT(DISTINCT w.customer_id) > 0
                            THEN COUNT(DISTINCT t.customer_id) * 100.0 / COUNT(DISTINCT w.customer_id)
                            ELSE 0 END, 1
                   ) AS conversion_pct
            FROM products p
            JOIN wishlist w ON p.product_id = w.product_id
            LEFT JOIN transactions t ON p.product_id = t.product_id
            GROUP BY p.product_name, p.subcategory
            HAVING wishlisted_by >= 10
               AND (actually_purchased = 0 OR actually_purchased < wishlisted_by * 0.5)
            ORDER BY wishlisted_by DESC
            LIMIT 10
        """,
    },
    {
        "id": "txn_volume_spike",
        "title": "Transaction Volume Outliers",
        "severity": "info",
        "description": "Customers whose transaction count is > 2 std deviations above average",
        "sql": """
            WITH vol AS (
                SELECT customer_id, COUNT(*) AS txn_count FROM transactions GROUP BY customer_id
            ),
            stats AS (
                SELECT AVG(txn_count) AS mean_count, STDDEV(txn_count) AS std_count FROM vol
            )
            SELECT c.customer_name, c.customer_id, vol.txn_count,
                   ROUND(stats.mean_count, 1) AS avg_count,
                   ROUND((vol.txn_count - stats.mean_count) / stats.std_count, 2) AS z_score,
                   c.clv_tier, c.churn_risk_category
            FROM vol CROSS JOIN stats
            JOIN customers c ON vol.customer_id = c.customer_id
            WHERE (vol.txn_count - stats.mean_count) / stats.std_count > 2
            ORDER BY z_score DESC
            LIMIT 10
        """,
    },
    {
        "id": "abandoned_applications",
        "title": "Products with High Application Abandonment",
        "severity": "warning",
        "description": "Products with the most incomplete applications",
        "sql": """
            SELECT p.product_name, p.subcategory, COUNT(*) AS abandoned_count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM incomplete_applications), 1) AS pct_of_total
            FROM incomplete_applications i
            JOIN products p ON i.product_id = p.product_id
            GROUP BY p.product_name, p.subcategory
            ORDER BY abandoned_count DESC
            LIMIT 10
        """,
    },
    {
        "id": "roas_outliers",
        "title": "Marketing ROAS Outliers",
        "severity": "info",
        "description": "Channel-persona combos with ROAS more than 1.5σ from average",
        "sql": """
            WITH ch AS (
                SELECT channel, persona,
                       ROUND(SUM(revenue_usd) / NULLIF(SUM(spend_usd), 0), 2) AS roas,
                       ROUND(SUM(spend_usd), 0) AS total_spend
                FROM ad_spend GROUP BY channel, persona
            ),
            stats AS (SELECT AVG(roas) AS mean_roas, STDDEV(roas) AS std_roas FROM ch)
            SELECT ch.channel, ch.persona, ch.roas, ch.total_spend,
                   ROUND((ch.roas - stats.mean_roas) / NULLIF(stats.std_roas, 0), 2) AS z_score
            FROM ch CROSS JOIN stats
            WHERE ABS((ch.roas - stats.mean_roas) / NULLIF(stats.std_roas, 0)) > 1.5
            ORDER BY z_score DESC
            LIMIT 10
        """,
    },
]


def detect_anomalies() -> List[Dict[str, Any]]:
    """
    Run all anomaly detection queries and return structured results.
    Each result contains: id, title, severity, description, columns, rows, count.
    """
    con = _get_con()
    results = []
    for spec in _ANOMALY_QUERIES:
        try:
            rel = con.execute(spec["sql"].strip())
            cols = [d[0] for d in rel.description]
            rows = rel.fetchall()
            results.append({
                "id": spec["id"],
                "title": spec["title"],
                "severity": spec["severity"],
                "description": spec["description"],
                "columns": cols,
                "rows": [list(r) for r in rows],
                "count": len(rows),
            })
        except Exception as e:
            logger.warning("Anomaly query '%s' failed: %s", spec["id"], e)
            results.append({
                "id": spec["id"],
                "title": spec["title"],
                "severity": spec["severity"],
                "description": spec["description"],
                "columns": [],
                "rows": [],
                "count": 0,
                "error": str(e),
            })
    return results


# ── Trend detection ───────────────────────────────────────────────────────────

_TREND_QUERIES = [
    {
        "id": "revenue_mom",
        "title": "Monthly Revenue",
        "unit": "$",
        "sql": """
            WITH max_dt AS (SELECT MAX(CAST(transaction_date AS DATE)) AS mx FROM transactions),
            monthly AS (
                SELECT CAST(year(CAST(transaction_date AS DATE)) AS VARCHAR)
                       || '-' || LPAD(CAST(month(CAST(transaction_date AS DATE)) AS VARCHAR), 2, '0') AS month_key,
                       ROUND(SUM(amount), 0) AS value
                FROM transactions, max_dt
                WHERE CAST(transaction_date AS DATE) >= max_dt.mx - INTERVAL 13 MONTH
                GROUP BY month_key
            )
            SELECT month_key, value FROM monthly ORDER BY month_key
        """,
    },
    {
        "id": "txn_count_mom",
        "title": "Monthly Transaction Count",
        "unit": "",
        "sql": """
            WITH max_dt AS (SELECT MAX(CAST(transaction_date AS DATE)) AS mx FROM transactions),
            monthly AS (
                SELECT CAST(year(CAST(transaction_date AS DATE)) AS VARCHAR)
                       || '-' || LPAD(CAST(month(CAST(transaction_date AS DATE)) AS VARCHAR), 2, '0') AS month_key,
                       COUNT(*) AS value
                FROM transactions, max_dt
                WHERE CAST(transaction_date AS DATE) >= max_dt.mx - INTERVAL 13 MONTH
                GROUP BY month_key
            )
            SELECT month_key, value FROM monthly ORDER BY month_key
        """,
    },
    {
        "id": "ad_spend_mom",
        "title": "Monthly Marketing Spend",
        "unit": "$",
        "sql": """
            SELECT month_key, value FROM (
                SELECT CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR), 2, '0') AS month_key,
                       ROUND(SUM(spend_usd), 0) AS value
                FROM ad_spend
                GROUP BY year, month, month_key ORDER BY month_key DESC LIMIT 13
            ) sub ORDER BY month_key
        """,
    },
    {
        "id": "wishlist_mom",
        "title": "Monthly Wishlist Additions",
        "unit": "",
        "sql": """
            WITH max_dt AS (SELECT MAX(CAST(added_date AS DATE)) AS mx FROM wishlist),
            monthly AS (
                SELECT CAST(year(CAST(added_date AS DATE)) AS VARCHAR)
                       || '-' || LPAD(CAST(month(CAST(added_date AS DATE)) AS VARCHAR), 2, '0') AS month_key,
                       COUNT(*) AS value
                FROM wishlist, max_dt
                WHERE CAST(added_date AS DATE) >= max_dt.mx - INTERVAL 13 MONTH
                GROUP BY month_key
            )
            SELECT month_key, value FROM monthly ORDER BY month_key
        """,
    },
    {
        "id": "incomplete_mom",
        "title": "Monthly Incomplete Applications",
        "unit": "",
        "sql": """
            WITH max_dt AS (SELECT MAX(CAST(started_date AS DATE)) AS mx FROM incomplete_applications),
            monthly AS (
                SELECT CAST(year(CAST(started_date AS DATE)) AS VARCHAR)
                       || '-' || LPAD(CAST(month(CAST(started_date AS DATE)) AS VARCHAR), 2, '0') AS month_key,
                       COUNT(*) AS value
                FROM incomplete_applications, max_dt
                WHERE CAST(started_date AS DATE) >= max_dt.mx - INTERVAL 13 MONTH
                GROUP BY month_key
            )
            SELECT month_key, value FROM monthly ORDER BY month_key
        """,
    },
]


def get_trend_summary() -> List[Dict[str, Any]]:
    """
    Run MoM trend queries. Returns list of trend objects:
      id, title, unit, months (list of {month, value}),
      latest_value, prev_value, pct_change, direction ('up'|'down'|'flat')
    """
    con = _get_con()
    results = []
    for spec in _TREND_QUERIES:
        try:
            rel = con.execute(spec["sql"].strip())
            rows = rel.fetchall()
            months = [{"month": r[0], "value": float(r[1]) if r[1] is not None else 0} for r in rows]
            # Use the second-to-last month as "latest" for MoM comparison
            # because the last month in the dataset is typically partial (incomplete data)
            # Only flag as partial if there are 2+ months and the last value is <50% of the prior month
            last_month_partial = False
            if len(months) >= 2:
                last_val = months[-1]["value"]
                prev_val = months[-2]["value"]
                if prev_val > 0 and last_val < prev_val * 0.5:
                    last_month_partial = True

            latest = months[-1]["value"] if months else 0
            prev = months[-2]["value"] if len(months) >= 2 else None
            # For MoM % change, compare last two complete months (skip if last is partial)
            cmp_latest = months[-2]["value"] if (last_month_partial and len(months) >= 3) else latest
            cmp_prev = months[-3]["value"] if (last_month_partial and len(months) >= 3) else prev
            if cmp_prev and cmp_prev != 0:
                pct_change = round((cmp_latest - cmp_prev) / abs(cmp_prev) * 100, 1)
            else:
                pct_change = None
            direction = "flat"
            if pct_change is not None:
                direction = "up" if pct_change > 1 else ("down" if pct_change < -1 else "flat")
            results.append({
                "id": spec["id"],
                "title": spec["title"],
                "unit": spec["unit"],
                "months": months,
                "latest_value": latest,
                "prev_value": prev,
                "pct_change": pct_change,
                "direction": direction,
                "last_month_partial": last_month_partial,
            })
        except Exception as e:
            logger.warning("Trend query '%s' failed: %s", spec["id"], e)
            results.append({
                "id": spec["id"],
                "title": spec["title"],
                "unit": spec["unit"],
                "months": [],
                "latest_value": 0,
                "prev_value": None,
                "pct_change": None,
                "direction": "flat",
                "error": str(e),
            })
    return results


# ── Product Pulse ─────────────────────────────────────────────────────────────

def get_product_pulse() -> List[Dict[str, Any]]:
    """
    Per-product momentum for the Product Pulse panel.

    Partial-month detection uses TWO signals (either triggers the flag):
      1. days_elapsed < 20  — dataset ends early in the month (e.g. June 4 → 4 days)
      2. cur_vol < 50% of prev_vol — overall transaction volume is abnormally low

    When partial: the last month is still shown in the chart but is excluded from
    momentum comparison and KPI values. The last COMPLETE month is used instead.
    """
    import datetime as _dt
    con = _get_con()
    results: List[Dict[str, Any]] = []
    try:
        # ── Step 0: detect partial last month ────────────────────────────────
        meta = con.execute("""
            WITH max_dt AS (SELECT MAX(CAST(transaction_date AS DATE)) AS mx FROM transactions),
            agg AS (
                SELECT
                    SUM(CASE WHEN CAST(year(CAST(transaction_date AS DATE)) AS VARCHAR)
                                  || '-' || LPAD(CAST(month(CAST(transaction_date AS DATE)) AS VARCHAR), 2, '0')
                                  = CAST(year(mx) AS VARCHAR)
                                  || '-' || LPAD(CAST(month(mx) AS VARCHAR), 2, '0')
                             THEN amount ELSE 0 END) AS cur_vol,
                    SUM(CASE WHEN CAST(transaction_date AS DATE)
                                  >= date_trunc('month', mx) - INTERVAL 1 MONTH
                              AND CAST(transaction_date AS DATE)
                                  <  date_trunc('month', mx)
                             THEN amount ELSE 0 END) AS prev_vol
                FROM transactions, max_dt
            )
            SELECT max_dt.mx, day(max_dt.mx) AS days_elapsed, agg.cur_vol, agg.prev_vol
            FROM max_dt, agg
        """).fetchone()

        max_date, days_elapsed, cur_vol, prev_vol = meta
        last_month_partial = bool(
            days_elapsed < 20
            or (prev_vol and prev_vol > 0 and (cur_vol or 0) < prev_vol * 0.5)
        )

        # Reference month for "new customers" KPI: last complete month
        if last_month_partial:
            first_of_cur = max_date.replace(day=1)
            last_complete_day = first_of_cur - _dt.timedelta(days=1)
            ref_month_str = last_complete_day.strftime('%Y-%m')
        else:
            ref_month_str = max_date.strftime('%Y-%m')

        # ── Step 1: monthly volume + customers per product (last 7 months) ───
        # Fetch 7 so that after dropping the partial last month we still have 6 complete months
        volume_rows = con.execute("""
            WITH max_dt AS (SELECT MAX(CAST(transaction_date AS DATE)) AS mx FROM transactions),
            monthly AS (
                SELECT t.product_id,
                       CAST(year(CAST(t.transaction_date AS DATE)) AS VARCHAR)
                           || '-' || LPAD(CAST(month(CAST(t.transaction_date AS DATE)) AS VARCHAR), 2, '0') AS month_key,
                       COUNT(DISTINCT t.customer_id) AS uniq_customers,
                       ROUND(SUM(t.amount), 0) AS volume
                FROM transactions t, max_dt
                WHERE CAST(t.transaction_date AS DATE) >= max_dt.mx - INTERVAL 7 MONTH
                GROUP BY t.product_id, month_key
            )
            SELECT p.product_name, p.subcategory, m.month_key, m.uniq_customers, m.volume
            FROM monthly m
            JOIN products p ON m.product_id = p.product_id
            ORDER BY p.product_name, m.month_key
        """).fetchall()

        # ── Step 2: new customers for the reference (last complete) month ────
        new_cust_rows = con.execute(f"""
            WITH first_txn AS (
                SELECT customer_id, product_id, MIN(CAST(transaction_date AS DATE)) AS first_date
                FROM transactions GROUP BY customer_id, product_id
            )
            SELECT p.product_name, COUNT(DISTINCT ft.customer_id) AS new_customers
            FROM first_txn ft
            JOIN products p ON ft.product_id = p.product_id
            WHERE CAST(year(ft.first_date) AS VARCHAR)
                  || '-' || LPAD(CAST(month(ft.first_date) AS VARCHAR), 2, '0') = '{ref_month_str}'
            GROUP BY p.product_name
        """).fetchall()

        new_customers_map = {r[0]: int(r[1]) for r in new_cust_rows}

        # ── Step 3: group monthly rows by product ─────────────────────────────
        from collections import defaultdict
        product_map: dict = defaultdict(lambda: {"subcategory": "", "months": []})
        for product_name, subcategory, month_key, uniq, volume in volume_rows:
            product_map[product_name]["subcategory"] = subcategory
            product_map[product_name]["months"].append({
                "month": month_key,
                "customers": int(uniq),
                "volume": float(volume),
            })

        # ── Step 4: compute momentum using only complete months ───────────────
        for product_name, data in product_map.items():
            months = data["months"]   # full list, ascending; may end with a partial month

            # Slice off the partial month for all calculations
            complete = months[:-1] if last_month_partial and len(months) > 1 else months
            nc = len(complete)

            if nc >= 4:
                recent_avg = (complete[-1]["volume"] + complete[-2]["volume"]) / 2
                prior_avg  = (complete[-3]["volume"] + complete[-4]["volume"]) / 2
            elif nc >= 2:
                recent_avg = complete[-1]["volume"]
                prior_avg  = complete[-2]["volume"]
            elif nc == 1:
                recent_avg = complete[0]["volume"]
                prior_avg  = 0
            else:
                recent_avg = 0
                prior_avg  = 0

            if prior_avg > 0:
                pct_change = round((recent_avg - prior_avg) / prior_avg * 100, 1)
                if pct_change > 10:
                    momentum = "Growing"
                elif pct_change < -10:
                    momentum = "Declining"
                else:
                    momentum = "Stable"
            else:
                pct_change = None
                momentum = "Stable"

            # KPI values come from the last COMPLETE month, not the partial one
            kpi_month = complete[-1] if complete else (months[-1] if months else {})

            results.append({
                "product_name": product_name,
                "subcategory": data["subcategory"],
                "new_customers": new_customers_map.get(product_name, 0),
                "this_month_volume": kpi_month.get("volume", 0),
                "this_month_customers": kpi_month.get("customers", 0),
                "kpi_month_label": kpi_month.get("month", ref_month_str),
                "last_month_partial": last_month_partial,
                "momentum": momentum,
                "pct_change": pct_change,
                "months": months,   # full list (chart still shows partial month)
            })

        # Sort: Declining first (most urgent), then Stable, then Growing; within each by volume desc
        _priority = {"Declining": 0, "Stable": 1, "Growing": 2}
        results.sort(key=lambda x: (_priority.get(x["momentum"], 1), -x["this_month_volume"]))
    except Exception as e:
        logger.warning("get_product_pulse failed: %s", e)

    return results


# ── Table list for UI ─────────────────────────────────────────────────────────

def available_tables() -> List[Dict[str, Any]]:
    """Return metadata for all available tables, used by the UI."""
    d = _meridian_dir()
    result = []
    for table, fname in TABLE_FILES:
        p = _resolve_csv_path(d, fname)
        if not p.is_file():
            continue
        cols = _columns_for(table)
        if not cols:
            try:
                df = pd.read_csv(p, nrows=0)
                cols = df.columns.tolist()
            except Exception:
                cols = []
        try:
            row_count = sum(1 for _ in open(p)) - 1
        except Exception:
            row_count = 0
        result.append({
            "table": table,
            "file": fname,
            "columns": len(cols),
            "rows": row_count,
            "col_names": cols[:10],
        })
    return result

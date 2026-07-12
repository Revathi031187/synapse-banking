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
import shutil
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
    """Return a valid path to transactions.csv; downloads from UC Volume when missing."""
    if local_path.exists():
        return local_path
    if _TMP_TXN.exists():
        return _TMP_TXN
    vol_path = os.environ.get(
        'TRANSACTIONS_VOLUME_PATH',
        '/Volumes/dev/banking/meridian_preloaded/transactions.csv',
    )
    try:
        from databricks.sdk import WorkspaceClient  # noqa: PLC0415
        w = WorkspaceClient()
        _TMP_TXN.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading transactions.csv from UC Volume %s ...", vol_path)
        with w.files.download(vol_path) as resp:
            with open(_TMP_TXN, 'wb') as fp:
                shutil.copyfileobj(resp.contents, fp)
        logger.info("Downloaded transactions.csv → %s (%d bytes)",
                    _TMP_TXN, _TMP_TXN.stat().st_size)
        return _TMP_TXN
    except Exception as e:
        logger.warning("Could not download transactions.csv from %s: %s", vol_path, e)
        return local_path  # caller's is_file() check will skip it gracefully


def _resolve_csv_path(d: Path, fname: str) -> Path:
    """Return the best available path for a CSV file (checks /tmp fallback after download)."""
    local = d / fname
    if fname == 'transactions.csv' and not local.exists() and _TMP_TXN.exists():
        return _TMP_TXN
    return local


# ── DuckDB connection + view registration ─────────────────────────────────────

# Table-name → CSV-filename mapping (order matters for the schema context)
TABLE_FILES = [
    ("customers",               "customers.csv"),
    ("products",                "products.csv"),
    ("transactions",            "transactions.csv"),
    ("customer_profile",        "customer_profile.csv"),
    ("customer_engagement",     "customer_engagement.csv"),
    ("mta_touchpoints",         "mta_touchpoint_history.csv"),
    ("ad_spend",                "ad_spend_monthly.csv"),
    ("impressions",             "recommendation_impressions.csv"),
    ("wishlist",                "wishlist.csv"),
    ("incomplete_apps",         "incomplete_applications.csv"),
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

    # Persona tables (only present after Agent A has run)
    if _PERSONAS_REGISTERED:
        lines.append("TABLE: persona_assignments")
        lines.append("  Description: Customer-to-persona mapping from Agent A K-Prototypes clustering")
        lines.append("  Columns: customer_id, cluster_id, persona_name")
        lines.append("")
        lines.append("TABLE: persona_stats")
        lines.append("  Description: Pre-computed stats per persona — use for segment-level questions")
        lines.append("  Columns: persona_name, customer_count, avg_churn_prob, avg_clv, avg_income, avg_credit_score, avg_digital_engagement, avg_deposits")
        lines.append("")

    descriptions = {
        "customers":           "Core customer profiles — 5,000 rows, one per customer",
        "products":            "Product catalogue — credit cards, loans, savings, mortgages",
        "transactions":        "Individual transaction ledger — debit/credit/transfer events",
        "customer_profile":    "Extended financial profile per customer — income, debt, assets",
        "customer_engagement": "Digital and channel engagement metrics per customer",
        "mta_touchpoints":     "Multi-touch attribution — marketing interactions across channels",
        "ad_spend":            "Monthly marketing spend and performance by channel and persona",
        "impressions":         "Product recommendation impression and click ledger",
        "wishlist":            "Products customers explicitly saved/wishlisted",
        "incomplete_apps":     "Applications started but not completed",
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
        "  - persona_stats has one row per persona — use directly for segment comparisons\n"
        "  - PREFER persona_name from persona_assignments over customer_segment for segment questions\n"
    ) if _PERSONAS_REGISTERED else (
        "  - Agent A has NOT been run yet — use churn_risk_category, clv_tier, or life_stage from customers for segmentation\n"
    )

    lines.append(
        "JOIN HINTS:\n"
        "  - All tables join via customer_id\n"
        + persona_hint +
        "  - impressions.product_id -> products.product_id\n"
        "  - incomplete_apps.product_id -> products.product_id\n"
        "  - wishlist.product_id -> products.product_id\n"
        "  - transactions has 876K rows — always filter by date or customer_id for performance\n"
        "  - transaction channels: Mobile, Online, Phone, ATM, Branch (5 values — ATM is valid)\n"
        "  - ad_spend channels: email, sms, in_app, branch (4 values — different from transaction channels)\n"
        "  - products has NO revenue column — use SUM(transactions.amount) JOIN products ON product_id\n"
        "  - ad_spend columns: year, month, channel, persona, spend_usd, revenue_usd, roas, cpa, conversion_rate\n"
        "PRODUCT COMPATIBILITY (customers table has: credit_score, credit_tier, income):\n"
        "  - products.credit_tier_required: 'any'=all, 'fair'=credit_score>=580, 'good'=credit_score>=670, 'excellent'=credit_score>=740\n"
        "  - always check: c.income >= p.min_income AND c.credit_score >= p.min_credit_score when recommending\n"
    )

    return "\n".join(lines)


# ── SQL generation prompt ─────────────────────────────────────────────────────

_SQL_SYSTEM = """You are an expert DuckDB SQL analyst for Meridian Bank.

Given a natural-language question and conversation history, you generate:
1. A valid DuckDB SELECT query
2. A short 2-sentence plain-English narrative answer
3. A chart configuration (type, x_col, y_col, title)
4. 3 contextual follow-up questions

STRICT SQL RULES:
- Only SELECT statements. Never DROP/INSERT/UPDATE/DELETE/CREATE/ALTER.
- Table names are exactly as shown in the schema (lowercase, no backticks needed for DuckDB).
- Use ROUND(value, 2) for monetary amounts and rates.
- DuckDB date functions: date_trunc('month', col), strftime(col, '%Y-%m'), year(col), month(col).
- String concat in DuckDB: col1 || ' ' || col2

AGGREGATION — THE MOST IMPORTANT RULE:
Every comparison question MUST use GROUP BY + an aggregate function (SUM, AVG, COUNT).
Never return raw rows for a comparison or ranking question.

EXAMPLES (follow these exactly):

Q: "Which marketing channels have the highest ROI?"
WRONG: SELECT channel, persona, roi_pct FROM ad_spend ORDER BY roi_pct DESC
RIGHT: SELECT channel, ROUND(AVG(roi_pct), 2) AS avg_roi_pct FROM ad_spend GROUP BY channel ORDER BY avg_roi_pct DESC

Q: "ROAS by channel and persona"
WRONG: SELECT channel, persona, roas FROM ad_spend ORDER BY roas DESC
RIGHT: SELECT channel, persona, ROUND(SUM(revenue_usd)/NULLIF(SUM(spend_usd),0),2) AS roas FROM ad_spend GROUP BY channel, persona ORDER BY roas DESC LIMIT 20

Q: "Show average income per life stage"
WRONG: SELECT life_stage, income FROM customers ORDER BY income DESC
RIGHT: SELECT life_stage, ROUND(AVG(income),0) AS avg_income FROM customers GROUP BY life_stage ORDER BY avg_income DESC

Q: "Monthly spend trend"
WRONG: SELECT month, channel, spend_usd FROM ad_spend ORDER BY month
RIGHT: SELECT CAST(year AS VARCHAR)||'-'||LPAD(CAST(month AS VARCHAR),2,'0') AS month_key, ROUND(SUM(spend_usd),0) AS total_spend FROM ad_spend GROUP BY year, month, month_key ORDER BY year, month LIMIT 24

Q: "What products are customers wishlisting but not applying for?"
WRONG: SELECT ... FROM wishlist w JOIN incomplete_apps i ON w.customer_id=i.customer_id AND w.product_id=i.product_id ...
RIGHT: SELECT p.product_name, COUNT(*) AS wishlist_count
       FROM wishlist w
       JOIN products p ON w.product_id = p.product_id
       LEFT JOIN incomplete_apps i ON w.customer_id = i.customer_id AND w.product_id = i.product_id
       WHERE i.customer_id IS NULL
       GROUP BY p.product_name
       ORDER BY wishlist_count DESC LIMIT 15

LEFT JOIN RULES — "X but not Y" questions always use LEFT JOIN + WHERE right_table.id IS NULL:
- "customers who wishlisted but never applied" → LEFT JOIN incomplete_apps ... WHERE i.customer_id IS NULL
- "products shown but never clicked" → LEFT JOIN impressions ... WHERE click_count = 0 or IS NULL
- "customers with no transactions" → LEFT JOIN transactions ... WHERE t.customer_id IS NULL
- NEVER use INNER JOIN for "not in" or "but not" patterns — it returns 0 rows when tables don't overlap

Q: "Top products by revenue" / "Which products generate the most revenue?"
WRONG: SELECT product_name, revenue FROM products ORDER BY revenue DESC  (products has NO revenue column)
RIGHT: SELECT p.product_name, ROUND(SUM(t.amount),0) AS revenue
       FROM transactions t JOIN products p ON t.product_id = p.product_id
       GROUP BY p.product_name ORDER BY revenue DESC LIMIT 15

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
- NEVER use `customer_segment` for grouping or filtering — it is 'Personal' for ALL 5000 customers and gives 1 useless row.
- When user says "by segment", "by customer segment", "customer group" → use `churn_risk_category` (High/Medium/Low), OR `life_stage` (Student/Young Professional/Family/Retiree/Pre-Retiree), OR `clv_tier` (Bronze/Silver/Gold/Platinum).
- products has NO revenue column — compute revenue as SUM(transactions.amount) via JOIN on product_id.

Q: "average churn risk score by customer segment" / "churn risk by segment"
WRONG: SELECT customer_segment, AVG(churn_risk_score) ... GROUP BY customer_segment  ← 1 row, all 'Personal'
RIGHT: SELECT churn_risk_category, ROUND(AVG(churn_risk_score),2) AS avg_churn_score, COUNT(*) AS customers
       FROM customers GROUP BY churn_risk_category ORDER BY avg_churn_score DESC

Q: "How does transaction volume compare across segments?" / "transaction volume by life stage"
RIGHT: SELECT c.life_stage, COUNT(t.transaction_id) AS transaction_count, ROUND(SUM(t.amount),0) AS total_volume
       FROM transactions t JOIN customers c ON t.customer_id = c.customer_id
       WHERE YEAR(t.transaction_date) = 2025
       GROUP BY c.life_stage ORDER BY total_volume DESC

NUMBER FORMATTING RULE — VERY IMPORTANT:
Always return RAW numeric values (dollars, counts, scores). NEVER pre-divide by 1000, 1000000, or 1000000000.
The frontend automatically formats: 1500000 → "1.5M", 85000 → "85.0K", 450 → "450"
WRONG: ROUND(SUM(amount)/1000000, 2) AS volume_m  ← renders as "1.5" with no unit (confusing)
RIGHT: ROUND(SUM(amount), 0) AS total_amount       ← frontend renders as "1.5M" (correct)

DIMENSION RULES:
- "by marketing channel" → ad_spend GROUP BY channel (4 values: email, sms, in_app, branch)
- "by transaction channel" → transactions GROUP BY channel (5 values: Mobile, Online, Phone, ATM, Branch)
- "by segment" / "by customer segment" → customers GROUP BY churn_risk_category (never customer_segment)
- "by persona/segment" → GROUP BY life_stage or clv_tier (5-6 values)
- "by channel AND persona" → ad_spend GROUP BY channel, persona (≤20 rows, use bar chart)
- "trend over time" → GROUP BY year, month ORDER BY year, month
- ad_spend pre-computed columns (roas, roi_pct, cpa) are PER-ROW — always re-aggregate: SUM(revenue_usd)/NULLIF(SUM(spend_usd),0)
- Target 5–15 rows for chart queries. Use LIMIT 10 for top-N, LIMIT 20 for two-dimension, LIMIT 24 for monthly.

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

Q: "Which products are best for high-churn customers?" / "Recommend products for at-risk customers"
RIGHT: SELECT p.product_name, COUNT(DISTINCT c.customer_id) AS eligible_customers,
              ROUND(AVG(p.avg_rating),2) AS avg_rating
       FROM customers c CROSS JOIN products p
       WHERE c.churn_risk_category = 'High'
         AND c.income >= p.min_income
         AND c.credit_score >= p.min_credit_score
         AND (p.credit_tier_required = 'any'
           OR (p.credit_tier_required = 'fair'      AND c.credit_score >= 580)
           OR (p.credit_tier_required = 'good'      AND c.credit_score >= 670)
           OR (p.credit_tier_required = 'excellent' AND c.credit_score >= 740))
         AND p.category = 'Personal'
       GROUP BY p.product_name ORDER BY eligible_customers DESC LIMIT 10

NEVER use CROSS JOIN without a compatibility WHERE clause — it produces ineligible recommendations.

CHART RULES:
- bar: categorical comparisons (channels, segments, products) — 5–15 groups.
- line: time-series (monthly, yearly) — x_col must be a date/month/year column.
- area: cumulative trends over time.
- pie: ONLY for 5 or fewer categories. Never pie with >5 groups.
- If the question cannot be answered with SQL, set sql to null.
- Always run SQL for any data question — never just give narrative text.

Respond ONLY with a valid JSON object — no markdown fences:
{
  "sql": "SELECT ...",
  "narrative": "2 sentences answering the question directly.",
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
                max_tokens=1200,
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
            max_tokens=1200,
            temperature=0.1,
        )
    except Exception as e2:
        logger.error("All LLM calls failed: %s", e2)
        raise RuntimeError(f"No LLM available: {e2}")


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

    x_col = llm_chart.get("x_col")
    if x_col not in columns:
        x_col = label_cols[0] if label_cols else columns[0]

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

    table = None
    chart = None
    sql_error = None

    if sql:
        if not _safe_sql(sql):
            sql_error = "Only SELECT queries are permitted."
            sql = None
        else:
            try:
                table = _exec_sql(sql)
                if table and table.get("columns"):
                    # Auto-aggregate if the LLM returned ungrouped rows (safety net)
                    table = _auto_aggregate(table, llm_chart)
                    chart = _resolve_chart(table["columns"], table.get("rows", []), llm_chart)
            except Exception as e:
                sql_error = str(e)
                logger.warning("SQL execution failed: %s\nSQL: %s", e, sql[:400])
                if not narrative:
                    narrative = f"Query encountered an error: {sql_error[:200]}"

    if not follow_ups:
        follow_ups = _default_follow_ups(question)

    return {
        "success": True,
        "narrative": narrative,
        "sql": sql,
        "table": table if (table and table.get("columns")) else None,
        "chart": chart,
        "follow_ups": follow_ups[:3],
        "sql_error": sql_error,
    }


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

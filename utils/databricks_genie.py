"""
Databricks Genie + Unity Catalog persona sync helpers.

- Unity Catalog location: resolve once via ``resolve_unity_catalog()`` — ``DOMAIN_CATALOG`` /
  ``DOMAIN_SCHEMA`` first, then ``ACADEMY_CATALOG`` / ``ACADEMY_SCHEMA`` for compatibility.
- Local / non-Databricks: sync returns HTTP-friendly skipped payload (no DATABRICKS_RUNTIME_VERSION).
- Databricks: Spark via ``_get_spark_session()`` (reuse active session or ``getOrCreate()`` so
  Databricks Apps work without a notebook-started session). Delta overwrite uses
  ``option("overwriteSchema", "true")``.
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def is_databricks_runtime() -> bool:
    return bool(os.getenv("DATABRICKS_RUNTIME_VERSION"))


def resolve_unity_catalog() -> Tuple[str, str]:
    """
    Single resolver for catalog + schema (sync, Genie context, status).
    DOMAIN_* wins; ACADEMY_* fallback for older configs.
    """
    catalog = (
        os.getenv("DOMAIN_CATALOG")
        or os.getenv("ACADEMY_CATALOG")
        or "dev"
    ).strip()
    schema = (
        os.getenv("DOMAIN_SCHEMA")
        or os.getenv("ACADEMY_SCHEMA")
        or "banking"
    ).strip()
    return catalog, schema


# Backward-compatible alias
get_domain_catalog_schema = resolve_unity_catalog


def get_customers_table_fqn() -> str:
    catalog, schema = resolve_unity_catalog()
    explicit = os.getenv("DOMAIN_CUSTOMERS_TABLE", "").strip()
    if explicit:
        return explicit
    return f"{catalog}.{schema}.customers"


def genie_env_configured() -> Dict[str, bool]:
    host = bool((os.getenv("DATABRICKS_HOST") or "").strip())
    token = bool((os.getenv("DATABRICKS_TOKEN") or "").strip())
    space = bool((os.getenv("GENIE_SPACE_ID") or "").strip())
    return {
        "databricks_host_set": host,
        "databricks_token_set": token,
        "genie_space_id_set": space,
        "ready_to_ask": host and token and space,
    }


def _persona_cluster_key(personas: Dict[str, Any], cluster: Any) -> Optional[str]:
    if cluster is None:
        return None
    s = str(cluster)
    if s in personas:
        return s
    try:
        n = int(cluster)
        if str(n) in personas:
            return str(n)
    except (TypeError, ValueError):
        pass
    return s if s in personas else None


def _customer_cluster_id(row: Dict[str, Any]) -> Any:
    for key in ("cluster_id", "cluster"):
        if row.get(key) is not None:
            return row.get(key)
    return None


def _normalize_cluster_id(cluster: Any) -> Any:
    if cluster is None:
        return None
    try:
        return int(float(cluster))
    except (TypeError, ValueError):
        return cluster


def build_persona_dataframes(
    personas: Dict[str, Any],
    customers: List[Dict[str, Any]],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    persona_assignments: customer_id, cluster_id, persona_name
    persona_definitions: cluster_id, persona_name, size, total_revenue, avg_spend, percentage
    """
    assignments_rows: List[Dict[str, Any]] = []
    for c in customers:
        cid = c.get("customer_id")
        if cid is None:
            continue
        cluster = _customer_cluster_id(c)
        cluster_norm = _normalize_cluster_id(cluster)
        pk = _persona_cluster_key(personas, cluster_norm) or _persona_cluster_key(personas, cluster)
        meta = personas.get(pk) if pk else None
        if not meta and pk is not None:
            meta = personas.get(cluster) or personas.get(str(cluster))
        pname = ""
        if isinstance(meta, dict):
            pname = meta.get("persona_name") or meta.get("name") or ""
        if not pname:
            pname = c.get("persona_name") or ""
        assignments_rows.append(
            {
                "customer_id": str(cid),
                "cluster_id": cluster_norm if cluster_norm is not None else cluster,
                "persona_name": str(pname),
            }
        )

    definitions_rows: List[Dict[str, Any]] = []
    for key, meta in (personas or {}).items():
        if not isinstance(meta, dict):
            continue
        try:
            cid = int(key)
        except (TypeError, ValueError):
            continue
        rev = meta.get("total_revenue")
        if rev is None and isinstance(meta.get("revenue_metrics"), dict):
            rev = meta["revenue_metrics"].get("total_revenue_12mo") or meta["revenue_metrics"].get(
                "total_deposits"
            )
        avg_spend = meta.get("avg_spend")
        if avg_spend is None:
            avg_spend = meta.get("avg_balance")
        if avg_spend is None and isinstance(meta.get("revenue_metrics"), dict):
            avg_spend = meta["revenue_metrics"].get("avg_customer_value")
        definitions_rows.append(
            {
                "cluster_id": cid,
                "persona_name": meta.get("persona_name") or meta.get("name") or "",
                "size": int(meta.get("size") or 0),
                "total_revenue": float(rev or 0),
                "avg_spend": float(avg_spend or 0),
                "percentage": float(meta.get("percentage") or 0),
            }
        )

    return (
        pd.DataFrame(assignments_rows),
        pd.DataFrame(definitions_rows),
    )


def _get_spark_session() -> Any:
    """
    Prefer an existing session; otherwise create one (Databricks Apps / jobs often have no
    ``getActiveSession()`` until explicitly started).
    """
    try:
        from pyspark.sql import SparkSession
    except ImportError:
        return None
    spark = SparkSession.getActiveSession()
    if spark is not None:
        return spark
    try:
        return SparkSession.builder.appName("persona_sync_uc").getOrCreate()
    except Exception as e:
        logger.warning("Spark getOrCreate failed: %s", e)
        return None


def sync_personas_to_catalog_tables(
    personas: Dict[str, Any],
    customers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Overwrite Delta tables persona_assignments and persona_definitions when running on Databricks with Spark.
    """
    catalog, schema = resolve_unity_catalog()

    if not isinstance(personas, dict) or len(personas) == 0:
        return {
            "success": False,
            "skipped": False,
            "error": "Segmentation results missing or empty: `personas` has no entries. Run Agent A (segmenter) first and ensure results are persisted.",
            "catalog": catalog,
            "schema": schema,
        }
    if not isinstance(customers, list) or len(customers) == 0:
        return {
            "success": False,
            "skipped": False,
            "error": "Segmentation results missing or empty: `customers_with_clusters` is empty. Run Agent A (segmenter) first and ensure results are persisted.",
            "catalog": catalog,
            "schema": schema,
        }

    assignments_df, definitions_df = build_persona_dataframes(personas, customers)

    if len(definitions_df) == 0:
        return {
            "success": False,
            "skipped": False,
            "error": "Could not build persona_definitions from `personas` (no valid cluster definitions). Re-run Agent A.",
            "catalog": catalog,
            "schema": schema,
            "assignments_rows": len(assignments_df),
            "definitions_rows": 0,
        }

    if len(assignments_df) == 0:
        return {
            "success": False,
            "skipped": False,
            "error": "Could not build persona_assignments: no rows with `customer_id` in `customers_with_clusters`. Re-run Agent A or check export shape.",
            "catalog": catalog,
            "schema": schema,
            "assignments_rows": 0,
            "definitions_rows": len(definitions_df),
        }

    if not is_databricks_runtime():
        return {
            "success": False,
            "skipped": True,
            "message": "Not running on Databricks (no DATABRICKS_RUNTIME_VERSION); persona sync skipped. "
            "Run this endpoint from a Databricks notebook/job with Spark, or export CSV locally.",
            "catalog": catalog,
            "schema": schema,
            "assignments_rows": len(assignments_df),
            "definitions_rows": len(definitions_df),
        }

    spark = _get_spark_session()
    if spark is None:
        return {
            "success": False,
            "skipped": True,
            "message": "PySpark/Spark session unavailable; cannot write Delta tables. On Databricks, ensure the app or cluster provides Spark.",
            "catalog": catalog,
            "schema": schema,
            "assignments_rows": len(assignments_df),
            "definitions_rows": len(definitions_df),
        }

    full_assign = f"{catalog}.{schema}.persona_assignments"
    full_def = f"{catalog}.{schema}.persona_definitions"

    spark.createDataFrame(assignments_df).write.format("delta").mode("overwrite").option(
        "overwriteSchema", "true"
    ).saveAsTable(full_assign)
    spark.createDataFrame(definitions_df).write.format("delta").mode("overwrite").option(
        "overwriteSchema", "true"
    ).saveAsTable(full_def)

    logger.info("Synced persona tables: %s, %s", full_assign, full_def)
    return {
        "success": True,
        "skipped": False,
        "message": f"Wrote {full_assign} and {full_def}",
        "persona_assignments_table": full_assign,
        "persona_definitions_table": full_def,
        "assignments_rows": len(assignments_df),
        "definitions_rows": len(definitions_df),
    }


def build_genie_persona_context(
    personas: Dict[str, Any],
    customers: List[Dict[str, Any]],
) -> str:
    catalog, schema = resolve_unity_catalog()
    customers_tbl = get_customers_table_fqn()
    pa = f"{catalog}.{schema}.persona_assignments"
    pd_tbl = f"{catalog}.{schema}.persona_definitions"

    names: List[str] = []
    for _k, meta in sorted((personas or {}).items(), key=lambda x: str(x[0])):
        if isinstance(meta, dict):
            n = meta.get("persona_name") or meta.get("name")
            if n:
                names.append(str(n))
    names = sorted(set(names))

    return (
        f"You are answering questions about our personalization domain in Unity Catalog.\n\n"
        f"For persona or segment questions, join `{customers_tbl}` to `{pa}` ON `customer_id`. "
        f"Use `{pa}.persona_name` and `{pa}.cluster_id` as the source of truth for current segments.\n"
        f"Do NOT use legacy persona or segment columns on the customers table if those exist "
        f"(e.g. stale persona_name or segment_id); prefer `{pa}` only.\n\n"
        f"Summary tables:\n"
        f"- `{pa}` (customer_id, cluster_id, persona_name)\n"
        f"- `{pd_tbl}` (cluster_id, persona_name, size, total_revenue, avg_spend, percentage)\n\n"
        f"Current persona names from the latest segmentation run: {', '.join(names) if names else '(none — run segmentation and sync)'}\n\n"
        f"---\nUser question:\n"
    )


def _genie_message_to_payload(msg: Any) -> Dict[str, Any]:
    """Best-effort extraction of narrative, SQL, and table preview from GenieMessage."""
    out: Dict[str, Any] = {
        "conversation_id": getattr(msg, "conversation_id", None),
        "message_id": getattr(msg, "id", None) or getattr(msg, "message_id", None),
        "narrative": "",
        "sql": None,
        "attachments": [],
        "raw_attachment_types": [],
    }
    attachments = getattr(msg, "attachments", None) or []
    narrative_parts: List[str] = []
    for att in attachments:
        atype = getattr(att, "attachment_type", None) or getattr(att, "type", None)
        out["raw_attachment_types"].append(str(atype))
        ad: Dict[str, Any] = {"type": str(atype)}
        text = getattr(att, "text", None)
        if text:
            ad["text"] = text
            narrative_parts.append(str(text))
        query = getattr(att, "query", None)
        if query is not None:
            sql_str = getattr(query, "query", None) or str(query)
            ad["sql"] = sql_str
            if out["sql"] is None:
                out["sql"] = sql_str
        title = getattr(att, "title", None)
        if title:
            ad["title"] = title
        # Some SDK versions expose statement_response / query_result on attachment
        stmt = getattr(att, "statement_response", None)
        if stmt is not None:
            ad["statement_response"] = str(stmt)[:8000]
        out["attachments"].append(ad)
    out["narrative"] = "\n\n".join(narrative_parts).strip()
    if not out["narrative"]:
        for attr in ("content", "text", "body"):
            v = getattr(msg, attr, None)
            if v:
                out["narrative"] = str(v).strip()
                break
    return out


def ask_genie(question: str, context_prefix: str) -> Dict[str, Any]:
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        return {
            "success": False,
            "error": "databricks-sdk not installed. pip install -r requirements-databricks.txt",
        }

    cfg = genie_env_configured()
    if not cfg["ready_to_ask"]:
        return {
            "success": False,
            "error": "Missing DATABRICKS_HOST, DATABRICKS_TOKEN, or GENIE_SPACE_ID",
            "config": cfg,
        }

    space_id = os.getenv("GENIE_SPACE_ID", "").strip()
    content = (context_prefix or "").strip() + "\n" + (question or "").strip()

    w = WorkspaceClient(
        host=os.getenv("DATABRICKS_HOST", "").strip(),
        token=os.getenv("DATABRICKS_TOKEN", "").strip(),
    )
    msg = w.genie.start_conversation_and_wait(space_id=space_id, content=content)
    payload = _genie_message_to_payload(msg)
    payload["success"] = True
    payload["config"] = cfg
    return payload

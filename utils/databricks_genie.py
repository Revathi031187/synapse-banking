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


def normalize_databricks_host(host: str) -> str:
    h = (host or "").strip().rstrip("/")
    if not h:
        return h
    if not h.startswith(("http://", "https://")):
        h = "https://" + h
    return h


def sanitize_pat_token(token: str) -> str:
    return (token or "").strip().strip('"').strip("'")


_GENIE_SPACE_BAD_FRAGMENTS = (
    "paste",
    "placeholder",
    "your_genie",
    "example",
    "xxxxxxxx",
    "todo",
)


def is_valid_genie_space_id(space_id: str) -> bool:
    """Genie space IDs are hex-like (often 32 chars); reject doc placeholders."""
    s = (space_id or "").strip()
    if not s:
        return False
    low = s.lower()
    if any(frag in low for frag in _GENIE_SPACE_BAD_FRAGMENTS):
        return False
    compact = s.replace("-", "")
    if len(compact) < 16 or len(compact) > 64:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in compact)


def _likely_azure_databricks_host(host: str) -> bool:
    return "azuredatabricks.net" in (host or "").lower()


def _genie_auth_mode_preference() -> str:
    """
    When PAT and OAuth are both in the environment, the Databricks SDK raises
    'more than one authorization method configured' unless auth_type is fixed.

    Set ``DATABRICKS_GENIE_AUTH`` to ``pat`` or ``oauth-m2m`` to choose explicitly.
    If unset: prefer ``oauth-m2m`` when client_id+secret exist (better for Genie on Azure), else PAT.
    """
    raw = (os.getenv("DATABRICKS_GENIE_AUTH") or "").strip().lower()
    if raw in ("pat", "token", "personal-access-token"):
        return "pat"
    if raw in ("oauth", "oauth-m2m", "m2m", "sp", "service-principal"):
        return "oauth-m2m"
    if raw in ("azure", "azure-client-secret", "azure-sp", "entra"):
        return "azure-client-secret"
    return ""


def genie_env_configured() -> Dict[str, Any]:
    host_raw = (os.getenv("DATABRICKS_HOST") or "").strip()
    host = bool(host_raw)
    token = bool(sanitize_pat_token(os.getenv("DATABRICKS_TOKEN") or ""))
    space_raw = (os.getenv("GENIE_SPACE_ID") or "").strip()
    space_nonempty = bool(space_raw)
    space_ok = is_valid_genie_space_id(space_raw)
    oauth_m2m = bool(
        (os.getenv("DATABRICKS_CLIENT_ID") or "").strip()
        and (os.getenv("DATABRICKS_CLIENT_SECRET") or "").strip()
    )
    azure_sp = bool(
        (os.getenv("ARM_CLIENT_ID") or "").strip()
        and (os.getenv("ARM_CLIENT_SECRET") or "").strip()
        and (os.getenv("ARM_TENANT_ID") or "").strip()
    )
    has_auth = oauth_m2m or azure_sp or token
    pref = _genie_auth_mode_preference()
    effective = ""
    if pref == "pat" and token:
        effective = "pat"
    elif pref == "oauth-m2m" and oauth_m2m:
        effective = "oauth-m2m"
    elif pref == "azure-client-secret" and azure_sp:
        effective = "azure-client-secret"
    elif oauth_m2m:
        effective = "oauth-m2m"
    elif azure_sp:
        effective = "azure-client-secret"
    elif token:
        effective = "pat"

    note = ""
    if host and space_ok and token and not (oauth_m2m or azure_sp) and _likely_azure_databricks_host(
        host_raw
    ):
        note = (
            "On Azure Databricks, the Genie Conversation API often rejects personal access tokens. "
            "Prefer OAuth: set DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET (Databricks SP) or "
            "ARM_CLIENT_ID + ARM_CLIENT_SECRET + ARM_TENANT_ID (Azure Entra SP). "
            "See https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api "
            "#configure-azure-databricks-authentication"
        )
    if oauth_m2m and token and not pref:
        extra = (
            "Both PAT and OAuth M2M env vars are set. The Genie client uses OAuth M2M unless you set "
            "DATABRICKS_GENIE_AUTH=pat (force PAT) or DATABRICKS_GENIE_AUTH=oauth-m2m (explicit OAuth)."
        )
        note = f"{note}\n\n{extra}".strip() if note else extra

    ws_id = bool((os.getenv("DATABRICKS_WORKSPACE_ID") or "").strip())
    azure_rid = bool((os.getenv("DATABRICKS_AZURE_RESOURCE_ID") or "").strip())

    return {
        "databricks_host_set": host,
        "databricks_token_set": token,
        "databricks_workspace_id_set": ws_id,
        "databricks_azure_resource_id_set": azure_rid,
        "genie_space_id_set": space_nonempty,
        "genie_space_id_valid": space_ok,
        "databricks_oauth_m2m_set": oauth_m2m,
        "azure_service_principal_set": azure_sp,
        "ready_to_ask": host and space_ok and has_auth,
        "genie_auth_note": note,
        "databricks_genie_auth_preference": pref or None,
        "genie_effective_auth": effective or None,
    }


def _genie_workspace_client_extras() -> Dict[str, Any]:
    """
    Optional SDK kwargs for Genie on Azure workspace URLs.

    The Python SDK only attaches ``X-Databricks-Org-Id`` for UNIFIED hosts; Genie may still need the
    workspace org id on standard ``adb-…azuredatabricks.net`` hosts. When ``DATABRICKS_WORKSPACE_ID``
    is set, we send it on every API request via ``custom_headers``.
    """
    extras: Dict[str, Any] = {}
    wid = (os.getenv("DATABRICKS_WORKSPACE_ID") or "").strip()
    if wid:
        extras["custom_headers"] = {"X-Databricks-Org-Id": wid}
    rid = (os.getenv("DATABRICKS_AZURE_RESOURCE_ID") or "").strip()
    if rid:
        extras["azure_workspace_resource_id"] = rid
    return extras


def build_workspace_client():
    """
    Build a WorkspaceClient for Genie. Always sets ``auth_type`` so PAT + OAuth can coexist in
    ``.env`` without tripping SDK validation.

    Use ``DATABRICKS_GENIE_AUTH=pat`` to force PAT when OAuth vars are also set.

    Uses ``Config(...)`` + ``WorkspaceClient(config=cfg)`` so ``custom_headers`` (e.g.
    ``X-Databricks-Org-Id``) works on older ``databricks-sdk`` releases that do not accept
    ``custom_headers`` on ``WorkspaceClient.__init__``.
    """
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.core import Config

    host = normalize_databricks_host(os.getenv("DATABRICKS_HOST", ""))
    if not host:
        raise ValueError("DATABRICKS_HOST is not set")

    pref = _genie_auth_mode_preference()
    cid = (os.getenv("DATABRICKS_CLIENT_ID") or "").strip()
    csec = (os.getenv("DATABRICKS_CLIENT_SECRET") or "").strip()
    oauth_m2m_ok = bool(cid and csec)

    arm_id = (os.getenv("ARM_CLIENT_ID") or "").strip()
    arm_sec = (os.getenv("ARM_CLIENT_SECRET") or "").strip()
    arm_ten = (os.getenv("ARM_TENANT_ID") or "").strip()
    azure_sp_ok = bool(arm_id and arm_sec and arm_ten)

    token = sanitize_pat_token(os.getenv("DATABRICKS_TOKEN") or "")
    pat_ok = bool(token)

    use_pat = False
    use_m2m = False
    use_azure = False

    if pref == "pat":
        if not pat_ok:
            raise ValueError("DATABRICKS_GENIE_AUTH=pat but DATABRICKS_TOKEN is missing")
        use_pat = True
    elif pref == "oauth-m2m":
        if not oauth_m2m_ok:
            raise ValueError("DATABRICKS_GENIE_AUTH=oauth-m2m but DATABRICKS_CLIENT_ID/SECRET missing")
        use_m2m = True
    elif pref == "azure-client-secret":
        if not azure_sp_ok:
            raise ValueError(
                "DATABRICKS_GENIE_AUTH=azure-client-secret but ARM_CLIENT_ID/ARM_CLIENT_SECRET/ARM_TENANT_ID missing"
            )
        use_azure = True
    else:
        if oauth_m2m_ok:
            use_m2m = True
        elif azure_sp_ok:
            use_azure = True
        elif pat_ok:
            use_pat = True

    ex = _genie_workspace_client_extras()

    if use_azure:
        cfg = Config(
            host=host,
            azure_client_id=arm_id,
            azure_client_secret=arm_sec,
            azure_tenant_id=arm_ten,
            auth_type="azure-client-secret",
            **ex,
        )
    elif use_m2m:
        cfg = Config(
            host=host,
            client_id=cid,
            client_secret=csec,
            auth_type="oauth-m2m",
            **ex,
        )
    elif use_pat:
        cfg = Config(host=host, token=token, auth_type="pat", **ex)
    else:
        raise ValueError(
            "No Databricks credentials: set DATABRICKS_TOKEN or "
            "DATABRICKS_CLIENT_ID+DATABRICKS_CLIENT_SECRET or ARM_CLIENT_ID+ARM_CLIENT_SECRET+ARM_TENANT_ID"
        )

    return WorkspaceClient(config=cfg)


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


def _df_to_values_sql(df: Any, batch_size: int = 500) -> List[str]:
    """Return a list of VALUES(...),(...) SQL strings, one per batch."""
    import math
    rows = df.values.tolist()
    cols = list(df.columns)

    def _esc(v: Any) -> str:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return "NULL"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)):
            return str(v)
        return "'" + str(v).replace("'", "''") + "'"

    batches = []
    for i in range(0, len(rows), batch_size):
        chunk = rows[i : i + batch_size]
        rows_sql = ",\n  ".join(
            "(" + ", ".join(_esc(c) for c in row) + ")" for row in chunk
        )
        batches.append((cols, rows_sql))
    return batches


def _sync_via_sql_warehouse(
    assignments_df: Any,
    definitions_df: Any,
    catalog: str,
    schema: str,
    full_assign: str,
    full_def: str,
) -> Dict[str, Any]:
    """Write persona tables via the Databricks SQL warehouse REST API — works outside Databricks runtime."""
    import httpx, time as _time

    host = (os.getenv("DATABRICKS_HOST") or "").strip().rstrip("/")
    token = (os.getenv("DATABRICKS_TOKEN") or "").strip()
    warehouse_id = (os.getenv("DATABRICKS_SQL_WAREHOUSE_ID") or "").strip()

    if not host or not token or not warehouse_id:
        missing = [k for k, v in [("DATABRICKS_HOST", host), ("DATABRICKS_TOKEN", token), ("DATABRICKS_SQL_WAREHOUSE_ID", warehouse_id)] if not v]
        return {
            "success": False,
            "skipped": False,
            "error": f"Cannot sync: missing env vars {missing}. Set them in .env to sync from outside Databricks.",
            "catalog": catalog,
            "schema": schema,
            "assignments_rows": len(assignments_df),
            "definitions_rows": len(definitions_df),
        }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _exec(statement: str) -> None:
        body = {"warehouse_id": warehouse_id, "statement": statement, "wait_timeout": "50s", "on_wait_timeout": "CONTINUE"}
        with httpx.Client(timeout=120.0) as client:
            r = client.post(f"{host}/api/2.0/sql/statements", headers=headers, json=body)
            if r.status_code >= 400:
                raise RuntimeError(f"SQL API {r.status_code}: {r.text[:1000]}")
            data = r.json()
            sid = data.get("statement_id")
            state = (data.get("status") or {}).get("state")
            for _ in range(120):
                if state in ("SUCCEEDED", "FAILED", "CANCELED"):
                    break
                _time.sleep(1)
                r2 = client.get(f"{host}/api/2.0/sql/statements/{sid}", headers=headers)
                r2.raise_for_status()
                data = r2.json()
                state = (data.get("status") or {}).get("state")
            if state != "SUCCEEDED":
                err = (data.get("status") or {}).get("error") or data
                raise RuntimeError(f"SQL failed ({state}): {err}")

    try:
        # ── persona_assignments ──────────────────────────────────────────
        assign_cols = ", ".join(f"`{c}`" for c in assignments_df.columns)
        _exec(
            f"CREATE OR REPLACE TABLE `{catalog}`.`{schema}`.`persona_assignments` "
            f"({', '.join(f'`{c}` STRING' for c in assignments_df.columns)}) USING DELTA"
        )
        for cols, rows_sql in _df_to_values_sql(assignments_df):
            _exec(f"INSERT INTO `{catalog}`.`{schema}`.`persona_assignments` ({assign_cols}) VALUES\n  {rows_sql}")

        # ── persona_definitions ─────────────────────────────────────────
        def_cols = ", ".join(f"`{c}`" for c in definitions_df.columns)
        col_defs = ", ".join(
            f"`{c}` {'DOUBLE' if definitions_df[c].dtype.kind in ('f', 'i') else 'STRING'}"
            for c in definitions_df.columns
        )
        _exec(
            f"CREATE OR REPLACE TABLE `{catalog}`.`{schema}`.`persona_definitions` "
            f"({col_defs}) USING DELTA"
        )
        for cols, rows_sql in _df_to_values_sql(definitions_df):
            _exec(f"INSERT INTO `{catalog}`.`{schema}`.`persona_definitions` ({def_cols}) VALUES\n  {rows_sql}")

        logger.info("Synced persona tables via SQL warehouse: %s, %s", full_assign, full_def)
        return {
            "success": True,
            "skipped": False,
            "message": f"Wrote {full_assign} ({len(assignments_df)} rows) and {full_def} ({len(definitions_df)} rows) via SQL warehouse",
            "persona_assignments_table": full_assign,
            "persona_definitions_table": full_def,
            "assignments_rows": len(assignments_df),
            "definitions_rows": len(definitions_df),
            "method": "sql_warehouse",
        }
    except Exception as exc:
        logger.exception("SQL warehouse persona sync failed")
        return {
            "success": False,
            "skipped": False,
            "error": str(exc),
            "catalog": catalog,
            "schema": schema,
            "assignments_rows": len(assignments_df),
            "definitions_rows": len(definitions_df),
        }


def sync_personas_to_catalog_tables(
    personas: Dict[str, Any],
    customers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Overwrite Delta tables persona_assignments and persona_definitions.
    Uses Spark when running on Databricks; falls back to SQL warehouse REST API otherwise.
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

    full_assign = f"{catalog}.{schema}.persona_assignments"
    full_def = f"{catalog}.{schema}.persona_definitions"

    # ── Try Spark first (Databricks runtime / job) ──────────────────────────
    if is_databricks_runtime():
        spark = _get_spark_session()
        if spark is not None:
            spark.createDataFrame(assignments_df).write.format("delta").mode("overwrite").option(
                "overwriteSchema", "true"
            ).saveAsTable(full_assign)
            spark.createDataFrame(definitions_df).write.format("delta").mode("overwrite").option(
                "overwriteSchema", "true"
            ).saveAsTable(full_def)
            logger.info("Synced persona tables via Spark: %s, %s", full_assign, full_def)
            return {
                "success": True,
                "skipped": False,
                "message": f"Wrote {full_assign} ({len(assignments_df)} rows) and {full_def} ({len(definitions_df)} rows) via Spark",
                "persona_assignments_table": full_assign,
                "persona_definitions_table": full_def,
                "assignments_rows": len(assignments_df),
                "definitions_rows": len(definitions_df),
                "method": "spark",
            }

    # ── Fallback: SQL warehouse REST API (works locally / Databricks Apps) ──
    return _sync_via_sql_warehouse(assignments_df, definitions_df, catalog, schema, full_assign, full_def)


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


def _extract_table_from_statement_response(stmt: Any) -> Dict[str, Any] | None:
    """Extract columns + rows from a StatementResponse object or dict."""
    if stmt is None:
        return None
    try:
        if isinstance(stmt, dict):
            manifest = stmt.get("manifest") or {}
            schema = manifest.get("schema") or {}
            cols_raw = schema.get("columns") or []
            columns = [c.get("name") or c.get("type_name", f"col_{i}") for i, c in enumerate(cols_raw)]
            result = stmt.get("result") or {}
            rows = result.get("data_array") or []
        else:
            manifest = getattr(stmt, "manifest", None)
            schema = getattr(manifest, "schema", None) if manifest else None
            cols_raw = getattr(schema, "columns", None) or [] if schema else []
            columns = [getattr(c, "name", None) or f"col_{i}" for i, c in enumerate(cols_raw)]
            result = getattr(stmt, "result", None)
            rows = getattr(result, "data_array", None) or [] if result else []
        if not columns and not rows:
            return None
        # Normalize rows to list-of-lists of strings
        norm_rows = []
        for row in rows:
            if isinstance(row, (list, tuple)):
                norm_rows.append([str(v) if v is not None else "" for v in row])
            else:
                norm_rows.append([str(row)])
        return {"columns": columns, "rows": norm_rows}
    except Exception:
        return None


def _genie_message_to_payload(msg: Any) -> Dict[str, Any]:
    """Best-effort extraction of narrative, SQL, and table preview from GenieMessage or API dict."""
    if isinstance(msg, dict):
        return _genie_message_dict_to_payload(msg)
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
            # SDK wraps text in a TextAttachment(content=...) object — extract .content
            text_str = getattr(text, "content", None) or str(text)
            ad["text"] = text_str
            narrative_parts.append(text_str)
        query = getattr(att, "query", None)
        if query is not None:
            sql_str = getattr(query, "query", None) or str(query)
            ad["sql"] = sql_str
            if out["sql"] is None:
                out["sql"] = sql_str
            # Extract tabular result from statement_response on the query object
            stmt = getattr(query, "statement_response", None)
            if stmt is not None:
                table = _extract_table_from_statement_response(stmt)
                if table:
                    ad["table"] = table
                    if out.get("table") is None:
                        out["table"] = table
        title = getattr(att, "title", None)
        if title:
            ad["title"] = title
        # Also check statement_response directly on the attachment
        stmt = getattr(att, "statement_response", None)
        if stmt is not None and not ad.get("table"):
            table = _extract_table_from_statement_response(stmt)
            if table:
                ad["table"] = table
                if out.get("table") is None:
                    out["table"] = table
        out["attachments"].append(ad)
    out["narrative"] = "\n\n".join(narrative_parts).strip()
    if not out["narrative"]:
        for attr in ("content", "text", "body"):
            v = getattr(msg, attr, None)
            if v:
                # May be a TextAttachment object — extract .content if present
                out["narrative"] = (getattr(v, "content", None) or str(v)).strip()
                break
    return out


def _genie_message_dict_to_payload(d: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Genie GET message JSON when the SDK does not wrap it in GenieMessage."""
    out: Dict[str, Any] = {
        "conversation_id": d.get("conversation_id"),
        "message_id": d.get("message_id") or d.get("id"),
        "narrative": "",
        "sql": None,
        "attachments": [],
        "raw_attachment_types": [],
    }
    narrative_parts: List[str] = []
    for att in d.get("attachments") or []:
        if not isinstance(att, dict):
            continue
        atype = att.get("attachment_type") or att.get("type") or "unknown"
        out["raw_attachment_types"].append(str(atype))
        ad: Dict[str, Any] = {"type": str(atype)}
        text = att.get("text")
        if text:
            # Raw API may return {"content": "...", "id": null} — extract content
            text_str = text.get("content") if isinstance(text, dict) else (getattr(text, "content", None) or str(text))
            ad["text"] = text_str
            narrative_parts.append(text_str)
        query = att.get("query")
        if isinstance(query, dict):
            sql_str = query.get("query")
            if sql_str:
                ad["sql"] = sql_str
                if out["sql"] is None:
                    out["sql"] = sql_str
            stmt = query.get("statement_response")
            if stmt is not None:
                table = _extract_table_from_statement_response(stmt)
                if table:
                    ad["table"] = table
                    if out.get("table") is None:
                        out["table"] = table
        elif query is not None:
            ad["sql"] = str(query)
            if out["sql"] is None:
                out["sql"] = str(query)
        if att.get("title"):
            ad["title"] = att["title"]
        out["attachments"].append(ad)
    out["narrative"] = "\n\n".join(narrative_parts).strip()
    if not out["narrative"]:
        for key in ("content", "text", "body"):
            v = d.get(key)
            if v:
                out["narrative"] = str(v).strip()
                break
    return out


def _workspace_api_client(w: Any) -> Any:
    api = getattr(w, "_api_client", None)
    if api is None:
        raise RuntimeError("Databricks WorkspaceClient has no _api_client")
    return api


def _genie_rest_list_spaces(w: Any, page_size: int, page_token: Optional[str]) -> Dict[str, Any]:
    api = _workspace_api_client(w)
    query: Dict[str, Any] = {}
    if page_size:
        query["page_size"] = page_size
    if page_token:
        query["page_token"] = page_token
    headers = {"Accept": "application/json"}
    return api.do("GET", "/api/2.0/genie/spaces", query=query or None, headers=headers)


def _genie_rest_get_space(w: Any, space_id: str) -> Dict[str, Any]:
    api = _workspace_api_client(w)
    headers = {"Accept": "application/json"}
    return api.do("GET", f"/api/2.0/genie/spaces/{space_id}", headers=headers)


def _genie_rest_start_conversation(w: Any, space_id: str, content: str) -> Dict[str, Any]:
    api = _workspace_api_client(w)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    return api.do(
        "POST",
        f"/api/2.0/genie/spaces/{space_id}/start-conversation",
        body={"content": content},
        headers=headers,
    )


def _genie_rest_get_message(w: Any, space_id: str, conversation_id: str, message_id: str) -> Dict[str, Any]:
    api = _workspace_api_client(w)
    headers = {"Accept": "application/json"}
    return api.do(
        "GET",
        f"/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}",
        headers=headers,
    )


def _genie_rest_get_query_result(
    w: Any, space_id: str, conversation_id: str, message_id: str
) -> Dict[str, Any]:
    """Fetch the tabular query result for a completed Genie message."""
    api = _workspace_api_client(w)
    headers = {"Accept": "application/json"}
    return api.do(
        "GET",
        f"/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result",
        headers=headers,
    )


def _genie_rest_wait_message_completed(
    w: Any,
    space_id: str,
    conversation_id: str,
    message_id: str,
    timeout_seconds: float = 1200.0,
) -> Dict[str, Any]:
    import random
    import time

    deadline = time.time() + timeout_seconds
    attempt = 1
    status_message = ""
    while time.time() < deadline:
        res = _genie_rest_get_message(w, space_id, conversation_id, message_id)
        status = str(res.get("status") or "").upper()
        status_message = status or "unknown"
        if status == "COMPLETED":
            return res
        if status == "FAILED":
            raise RuntimeError(f"Genie message FAILED: {res}")
        sleep_s = min(10.0, float(attempt)) + random.random()
        time.sleep(sleep_s)
        attempt += 1
    raise TimeoutError(f"Genie message timed out after {timeout_seconds}s (last status: {status_message})")


_GENIE_SPACE_NOT_FOUND_HINT = (
    "The Genie API cannot resolve this **dataroom** for your **host + credentials**. If Genie → Settings "
    "shows this `space_id`, check: "
    "(1) **Host** — `DATABRICKS_HOST` is the same `https://adb-…azuredatabricks.net` you use in the browser. "
    "(2) **Identity** — **GET /api/banking/genie/spaces** must list this id for the same PAT/SP; if not, grant "
    "that identity Genie/SQL access. "
    "(3) **Workspace org id** — set **`DATABRICKS_WORKSPACE_ID`** to the numeric workspace id (same value as "
    "response header **`x-databricks-org-id`** on a request in the browser DevTools Network tab, or from "
    "admin/workspace metadata). This app sends it as **`X-Databricks-Org-Id`** on Genie calls; the SDK often "
    "omits it on Azure workspace URLs without this. "
    "(4) **Azure resource** — optional **`DATABRICKS_AZURE_RESOURCE_ID`** (full workspace Azure resource id) for SP auth. "
    "(5) Wrong id from export JSON vs Settings. **GET /api/banking/genie/spaces/verify** tests `get_space`."
)


def list_genie_spaces(
    page_size: int = 50,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List Genie spaces visible to the configured credentials in ``DATABRICKS_HOST`` workspace.
    Does not require ``GENIE_SPACE_ID`` to be set.
    """
    try:
        from databricks.sdk import WorkspaceClient  # noqa: F401
    except ImportError:
        return {
            "success": False,
            "error": "databricks-sdk not installed. pip install -r requirements-databricks.txt",
            "spaces": [],
        }

    cfg = genie_env_configured()
    if not cfg.get("databricks_host_set") or not _genie_client_has_credentials():
        return {
            "success": False,
            "error": "Set DATABRICKS_HOST and PAT or OAuth credentials to list Genie spaces (GENIE_SPACE_ID not required).",
            "spaces": [],
            "config": cfg,
        }

    try:
        w = build_workspace_client()
        next_token: Optional[str] = None
        if hasattr(w.genie, "list_spaces"):
            resp = w.genie.list_spaces(page_size=page_size, page_token=page_token)
            rows = [
                {
                    "space_id": s.space_id,
                    "title": s.title,
                    "description": s.description,
                    "warehouse_id": s.warehouse_id,
                }
                for s in (resp.spaces or [])
            ]
            next_token = resp.next_page_token
        else:
            raw = _genie_rest_list_spaces(w, page_size, page_token)
            rows = []
            for s in raw.get("spaces") or []:
                if not isinstance(s, dict):
                    continue
                rows.append(
                    {
                        "space_id": s.get("space_id"),
                        "title": s.get("title"),
                        "description": s.get("description"),
                        "warehouse_id": s.get("warehouse_id"),
                    }
                )
            next_token = raw.get("next_page_token")
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "spaces": [],
            "config": cfg,
        }

    return {
        "success": True,
        "spaces": rows,
        "next_page_token": next_token,
        "config": cfg,
    }


def verify_genie_space(space_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Call Genie ``get_space`` for ``space_id`` or, if omitted, ``GENIE_SPACE_ID`` env.
    Confirms whether the API identity can resolve the space (same check as start-conversation routing).
    """
    try:
        from databricks.sdk import WorkspaceClient  # noqa: F401
    except ImportError:
        return {
            "success": False,
            "error": "databricks-sdk not installed. pip install -r requirements-databricks.txt",
        }

    sid = (space_id or os.getenv("GENIE_SPACE_ID") or "").strip()
    if not sid:
        return {
            "success": False,
            "error": "Pass space_id query param or set GENIE_SPACE_ID",
        }

    cfg = genie_env_configured()
    if not cfg.get("databricks_host_set") or not _genie_client_has_credentials():
        return {
            "success": False,
            "error": "Set DATABRICKS_HOST and PAT or OAuth credentials first.",
            "config": cfg,
        }

    try:
        w = build_workspace_client()
        if hasattr(w.genie, "get_space"):
            sp = w.genie.get_space(sid, include_serialized_space=False)
            return {
                "success": True,
                "space_id": sp.space_id,
                "title": sp.title,
                "description": sp.description,
                "warehouse_id": sp.warehouse_id,
                "config": cfg,
            }
        raw = _genie_rest_get_space(w, sid)
        return {
            "success": True,
            "space_id": raw.get("space_id"),
            "title": raw.get("title"),
            "description": raw.get("description"),
            "warehouse_id": raw.get("warehouse_id"),
            "config": cfg,
        }
    except Exception as e:
        return {
            "success": False,
            "space_id": sid,
            "error": str(e),
            "hint": _GENIE_SPACE_NOT_FOUND_HINT,
            "config": cfg,
        }


def _genie_client_has_credentials() -> bool:
    token = sanitize_pat_token(os.getenv("DATABRICKS_TOKEN") or "")
    m2m = (os.getenv("DATABRICKS_CLIENT_ID") or "").strip() and (
        os.getenv("DATABRICKS_CLIENT_SECRET") or ""
    ).strip()
    az = (
        (os.getenv("ARM_CLIENT_ID") or "").strip()
        and (os.getenv("ARM_CLIENT_SECRET") or "").strip()
        and (os.getenv("ARM_TENANT_ID") or "").strip()
    )
    return bool(token or m2m or az)


def ask_genie(question: str, context_prefix: str) -> Dict[str, Any]:
    try:
        from databricks.sdk.errors.platform import Unauthenticated
    except ImportError:

        class Unauthenticated(Exception):
            pass

    try:
        from databricks.sdk import WorkspaceClient  # noqa: F401
    except ImportError:
        return {
            "success": False,
            "error": "databricks-sdk not installed. pip install -r requirements-databricks.txt",
        }

    cfg = genie_env_configured()
    if not cfg.get("genie_space_id_valid"):
        return {
            "success": False,
            "error": (
                "GENIE_SPACE_ID is missing or still a placeholder. "
                "Use the real space id from Genie space Settings or GET /api/banking/genie/spaces "
                "(or GET /api/2.0/genie/spaces). Do not use ids from inside serialized_space JSON (e.g. 01f… blocks)."
            ),
            "config": cfg,
        }
    if not cfg["ready_to_ask"]:
        return {
            "success": False,
            "error": "Missing DATABRICKS_HOST, credentials (token or OAuth), or valid GENIE_SPACE_ID",
            "config": cfg,
        }

    space_id = os.getenv("GENIE_SPACE_ID", "").strip()
    content = (context_prefix or "").strip() + "\n" + (question or "").strip()

    try:
        w = build_workspace_client()
        genie = w.genie
        if hasattr(genie, "start_conversation_and_wait"):
            msg = genie.start_conversation_and_wait(space_id=space_id, content=content)
        else:
            op = _genie_rest_start_conversation(w, space_id, content)
            conv_id = op.get("conversation_id")
            msg_id = op.get("message_id")
            if not conv_id or not msg_id:
                raise RuntimeError(f"Unexpected Genie start-conversation response: {op}")
            if hasattr(genie, "wait_get_message_genie_completed"):
                msg = genie.wait_get_message_genie_completed(
                    conversation_id=conv_id,
                    message_id=msg_id,
                    space_id=space_id,
                )
            else:
                msg = _genie_rest_wait_message_completed(w, space_id, conv_id, msg_id)
    except Unauthenticated as e:
        hint = (
            "The Genie API rejected this credential type. On Azure Databricks use OAuth: "
            "DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET, or ARM_CLIENT_ID + ARM_CLIENT_SECRET + ARM_TENANT_ID. "
            "See Microsoft Learn: 'Configure Azure Databricks authentication' in the Genie Conversation API article."
        )
        return {
            "success": False,
            "error": str(e),
            "hint": hint,
            "config": cfg,
        }
    except Exception as e:
        err = str(e)
        el = err.lower()
        if "unsupported type" in el or "not sent" in el:
            return {
                "success": False,
                "error": err,
                "hint": cfg.get("genie_auth_note") or (
                    "Try OAuth (service principal) instead of a personal access token for Genie on Azure."
                ),
                "config": cfg,
            }
        if "does not exist" in el or "unable to get space" in el or "datarooms/" in el:
            return {
                "success": False,
                "error": err,
                "hint": _GENIE_SPACE_NOT_FOUND_HINT,
                "config": cfg,
            }
        raise

    payload = _genie_message_to_payload(msg)

    # ── Fetch tabular query result (separate endpoint) ──────────────────────
    # The message/attachment objects never embed row data directly; it lives at
    # .../query-result and must be fetched after the message completes.
    if payload.get("sql") and not payload.get("table"):
        conv_id = payload.get("conversation_id") or (
            getattr(msg, "conversation_id", None) if not isinstance(msg, dict) else msg.get("conversation_id")
        )
        msg_id = payload.get("message_id") or (
            getattr(msg, "id", None) if not isinstance(msg, dict) else (msg.get("id") or msg.get("message_id"))
        )
        if conv_id and msg_id:
            try:
                qr = _genie_rest_get_query_result(w, space_id, conv_id, msg_id)
                # Response shape: {"statement_response": {...}} or direct StatementResponse fields
                stmt = qr.get("statement_response") or qr
                table = _extract_table_from_statement_response(stmt)
                if table and table.get("rows"):
                    payload["table"] = table
            except Exception as qr_exc:
                logger.warning("Could not fetch Genie query-result: %s", qr_exc)

    payload["success"] = True
    payload["config"] = cfg
    return payload

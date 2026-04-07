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
        resp = w.genie.list_spaces(page_size=page_size, page_token=page_token)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "spaces": [],
            "config": cfg,
        }

    rows: List[Dict[str, Any]] = []
    for s in resp.spaces or []:
        rows.append(
            {
                "space_id": s.space_id,
                "title": s.title,
                "description": s.description,
                "warehouse_id": s.warehouse_id,
            }
        )
    return {
        "success": True,
        "spaces": rows,
        "next_page_token": resp.next_page_token,
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
        sp = w.genie.get_space(sid, include_serialized_space=False)
    except Exception as e:
        return {
            "success": False,
            "space_id": sid,
            "error": str(e),
            "hint": _GENIE_SPACE_NOT_FOUND_HINT,
            "config": cfg,
        }

    return {
        "success": True,
        "space_id": sp.space_id,
        "title": sp.title,
        "description": sp.description,
        "warehouse_id": sp.warehouse_id,
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
        msg = w.genie.start_conversation_and_wait(space_id=space_id, content=content)
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
    payload["success"] = True
    payload["config"] = cfg
    return payload

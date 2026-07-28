"""
Push local `data/preloaded/fmb_bank` CSVs to Unity Catalog from the web API (no notebook).

Uses Databricks REST APIs:
  - PUT /api/2.0/fs/files{path}  → Unity Catalog Volume (raw CSV bytes)
  - POST /api/2.0/sql/statements → SQL warehouse (CREATE VOLUME + CREATE OR REPLACE TABLE ... read_files)

Required env:
  DATABRICKS_HOST          Workspace URL (https://...cloud.databricks.com)
  DATABRICKS_TOKEN         PAT with files + SQL warehouse + UC volume write
  DATABRICKS_SQL_WAREHOUSE_ID   e.g. abc123def456

Optional:
  DOMAIN_CATALOG / DOMAIN_SCHEMA (else ACADEMY_* else dev / banking)
  DATABRICKS_UC_VOLUME_NAME     default: fmb_preloaded  (created under catalog.schema if missing)

The PAT often needs scope (or equivalent OAuth permission) for the **files** API preview.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx

from utils.databricks_genie import resolve_unity_catalog

logger = logging.getLogger(__name__)

PRELOADED_FILES = [
    ("customers", "customers.csv"),
    ("products", "products.csv"),
    ("transactions", "transactions.csv"),
]


def _normalize_host(host: str) -> str:
    h = (host or "").strip().rstrip("/")
    if not h:
        return h
    if not h.startswith("http"):
        h = "https://" + h
    return h


def _uc_volume_path(catalog: str, schema: str, volume_name: str, *parts: str) -> str:
    """Absolute UC Files path for API (leading slash)."""
    sub = "/".join(parts)
    return f"/Volumes/{catalog}/{schema}/{volume_name}/{sub}"


def upload_preloaded_env_ok() -> Dict[str, Any]:
    host = bool((os.getenv("DATABRICKS_HOST") or "").strip())
    token = bool((os.getenv("DATABRICKS_TOKEN") or "").strip())
    wh = bool((os.getenv("DATABRICKS_SQL_WAREHOUSE_ID") or "").strip())
    return {
        "databricks_host_set": host,
        "databricks_token_set": token,
        "sql_warehouse_id_set": wh,
        "ready_for_uc_upload": host and token and wh,
    }


def _put_volume_file(host: str, token: str, file_path: str, body: bytes) -> None:
    """PUT raw bytes to UC Files API. file_path must start with /Volumes/..."""
    base = _normalize_host(host)
    url = f"{base}/api/2.0/fs/files{file_path}"
    with httpx.Client(timeout=300.0) as client:
        r = client.put(
            url,
            headers={"Authorization": f"Bearer {token}"},
            content=body,
        )
    if r.status_code not in (200, 201, 204):
        raise RuntimeError(f"Upload failed {r.status_code}: {r.text[:2000]}")


def _execute_sql(host: str, token: str, warehouse_id: str, statement: str) -> Dict[str, Any]:
    base = _normalize_host(host)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "warehouse_id": warehouse_id,
        "statement": statement,
        "wait_timeout": "50s",
        "on_wait_timeout": "CONTINUE",
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(f"{base}/api/2.0/sql/statements", headers=headers, json=body)
        if r.status_code >= 400:
            raise RuntimeError(f"SQL API error {r.status_code}: {r.text[:2000]}")
        data = r.json()
        sid = data.get("statement_id")
        state = (data.get("status") or {}).get("state")
        for _ in range(120):
            if state in ("SUCCEEDED", "FAILED", "CANCELED"):
                break
            time.sleep(1)
            r2 = client.get(f"{base}/api/2.0/sql/statements/{sid}", headers=headers)
            r2.raise_for_status()
            data = r2.json()
            state = (data.get("status") or {}).get("state")
        if state != "SUCCEEDED":
            err = data.get("status", {}).get("error") or data
            raise RuntimeError(f"SQL did not succeed ({state}): {err}")
        return data


def upload_preloaded_fmb_to_uc(project_root: Path) -> Dict[str, Any]:
    """
    Read CSVs from data/preloaded/fmb_bank, upload to a UC Volume, then CREATE OR REPLACE Delta tables.
    """
    env = upload_preloaded_env_ok()
    if not env["ready_for_uc_upload"]:
        return {
            "success": False,
            "error": "Set DATABRICKS_HOST, DATABRICKS_TOKEN, and DATABRICKS_SQL_WAREHOUSE_ID",
            **env,
        }

    host = os.getenv("DATABRICKS_HOST", "").strip()
    token = os.getenv("DATABRICKS_TOKEN", "").strip()
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID", "").strip()
    catalog, schema = resolve_unity_catalog()
    volume_name = (os.getenv("DATABRICKS_UC_VOLUME_NAME") or "fmb_preloaded").strip()

    jpm_dir = project_root / "data" / "preloaded" / "jpm_bank"
    fmb_dir = project_root / "data" / "preloaded" / "fmb_bank"
    fmb_dir = jpm_dir if jpm_dir.is_dir() else fmb_dir
    if not fmb_dir.is_dir():
        return {
            "success": False,
            "error": f"Preloaded folder not found: {fmb_dir}",
            **env,
        }

    run_id = uuid.uuid4().hex[:12]
    steps: List[Dict[str, Any]] = []

    try:
        # Ensure managed volume exists (Unity Catalog)
        vol_sql = f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{schema}`.`{volume_name}`"
        _execute_sql(host, token, warehouse_id, vol_sql)
        steps.append({"step": "create_volume", "ok": True})

        for table_name, csv_name in PRELOADED_FILES:
            src = fmb_dir / csv_name
            if not src.is_file():
                return {
                    "success": False,
                    "error": f"Missing file: {src}",
                    "steps": steps,
                    **env,
                }
            data = src.read_bytes()
            remote_path = _uc_volume_path(catalog, schema, volume_name, "preloaded", run_id, csv_name)
            _put_volume_file(host, token, remote_path, data)
            steps.append({"step": "upload", "table": table_name, "path": remote_path, "bytes": len(data)})

        # Load into Delta tables via read_files (SQL warehouse)
        for table_name, csv_name in PRELOADED_FILES:
            remote_path = _uc_volume_path(catalog, schema, volume_name, "preloaded", run_id, csv_name)
            # Escape single quotes in path for SQL string literal
            path_lit = remote_path.replace("'", "''")
            sql = (
                f"CREATE OR REPLACE TABLE `{catalog}`.`{schema}`.`{table_name}` AS "
                f"SELECT * FROM read_files("
                f"'{path_lit}', "
                f"format => 'csv', "
                f"options => map('header', 'true', 'inferSchema', 'true')"
                f")"
            )
            _execute_sql(host, token, warehouse_id, sql)
            steps.append({"step": "load_table", "table": table_name, "method": "read_files"})

        fqns = [f"{catalog}.{schema}.{t}" for t, _ in PRELOADED_FILES]
        logger.info("UC preload complete: %s", fqns)
        return {
            "success": True,
            "catalog": catalog,
            "schema": schema,
            "volume": volume_name,
            "run_id": run_id,
            "tables": fqns,
            "steps": steps,
            **env,
        }
    except Exception as e:
        logger.exception("UC preload failed")
        return {
            "success": False,
            "error": str(e),
            "steps": steps,
            **env,
        }


def uc_upload_status_extended() -> Dict[str, Any]:
    catalog, schema = resolve_unity_catalog()
    vol = (os.getenv("DATABRICKS_UC_VOLUME_NAME") or "fmb_preloaded").strip()
    out = upload_preloaded_env_ok()
    out.update(
        {
            "catalog": catalog,
            "schema": schema,
            "uc_volume_name": vol,
            "volume_path_example": _uc_volume_path(catalog, schema, vol, "preloaded", "<run_id>", "customers.csv"),
        }
    )
    return out

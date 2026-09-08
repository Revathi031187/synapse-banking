"""
Utility for loading large CSV files that are excluded from Databricks App deployments
(> 10 MB per-file limit).

Access priority for each file:
  1. local_path  — dev Repos path (always wins when present)
  2. /tmp/meridian_bank/<file>  — cached from a previous download this App instance
  3. Direct UC Volume filesystem path (/Volumes/...) — works when the App's service
     principal has been granted READ FILES on the volume (no REST call needed)
  4. Databricks Files REST API  — fallback download via DATABRICKS_HOST + DATABRICKS_TOKEN

For option 4 to work the App's service principal needs:
  GRANT READ FILES ON VOLUME dev.banking.meridian_preloaded
  TO `<app-service-principal>`;
Run that SQL in a Databricks notebook or SQL editor. The service principal name is
visible in the App's settings page under "Permissions".
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable, Optional

# Called with (bytes_so_far, total_bytes_or_None) as a download/copy progresses.
# total is None when the source doesn't report a size (e.g. no Content-Length
# header) — callers should render an indeterminate indicator in that case
# rather than inventing a fake percentage.
ProgressCallback = Callable[[int, Optional[int]], None]

# Importing utils.logger (rather than a bare logging.getLogger) guarantees the
# app's UTF-8-safe console sink is installed before any message below is
# logged — messages here previously used raw print() with unicode arrows
# (→), which crashed with UnicodeEncodeError on Windows' cp1252 console the
# moment this code path actually ran (e.g. a REST-download success/failure),
# silently breaking the whole fallback chain instead of reporting its result.
from utils.logger import get_logger

logger = get_logger("large_file_loader")

_TMP_BASE = Path('/tmp/meridian_bank')
_DEFAULT_VOL_BASE = '/Volumes/dev/banking/meridian_preloaded'

_LARGE_FILES = {
    'transactions.csv': os.environ.get(
        'TRANSACTIONS_VOLUME_PATH',
        f'{_DEFAULT_VOL_BASE}/transactions.csv',
    ),
}

# Fallback source for anyone without READ FILES on the UC Volume above, but
# who DOES have SELECT on the equivalent table (a separate, often easier-to-
# grant permission) — same data, uploaded by scripts/upload_meridian_to_databricks.py
# via `CREATE TABLE ... AS SELECT * FROM read_files(..., header=>true)`, so its
# column names are an exact match for the CSV's header.
_SQL_TABLE_SOURCES = {
    'transactions.csv': {
        'catalog': os.environ.get('DOMAIN_CATALOG', 'dev'),
        'schema': os.environ.get('DOMAIN_SCHEMA', 'banking'),
        'table': 'meridian_transactions',
    },
}
_SQL_EXPORT_BATCH_SIZE = 20_000  # rows per SELECT — comfortably inside inline result
                                 # limits; the one value to tune if a warehouse ever
                                 # needs a smaller batch.


def _sql_exec(host: str, token: str, warehouse_id: str, statement: str, timeout_secs: int = 120) -> dict:
    """
    Execute one SQL statement via the Databricks SQL Statement Execution REST
    API and poll until it finishes. Raises RuntimeError/TimeoutError on
    failure — mirrors the exact pattern already proven in
    scripts/upload_meridian_to_databricks.py::_sql and
    utils/databricks_genie.py::_sync_via_sql_warehouse (ported in rather than
    imported, to keep this module free of a dependency on the scripts folder).
    """
    import requests
    import time as _time

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(
        f"{host}/api/2.0/sql/statements",
        headers=headers,
        json={
            "warehouse_id": warehouse_id,
            "statement": statement,
            "wait_timeout": f"{min(timeout_secs, 50)}s",
            "on_wait_timeout": "CONTINUE",
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    sid = data.get("statement_id")

    deadline = _time.time() + timeout_secs
    while True:
        state = (data.get("status") or {}).get("state", "UNKNOWN")
        if state in ("SUCCEEDED", "FAILED", "CANCELED", "CLOSED"):
            break
        if _time.time() > deadline:
            raise TimeoutError(f"SQL timed out after {timeout_secs}s: {statement[:120]}")
        _time.sleep(2)
        r = requests.get(f"{host}/api/2.0/sql/statements/{sid}", headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()

    if (data.get("status") or {}).get("state") != "SUCCEEDED":
        err = (data.get("status") or {}).get("error", {})
        raise RuntimeError(f"SQL FAILED [{err.get('error_code')}]: {err.get('message', '')}")
    return data


def _download_via_sql_warehouse(
    fname: str,
    tmp_path: Path,
    on_progress: Optional[ProgressCallback],
    on_error: Optional[Callable[[str], None]],
) -> bool:
    """
    Fallback for a user with SELECT on the equivalent Databricks TABLE but no
    READ FILES on the UC Volume (a separate, often easier-to-grant permission).
    Pages through the table in _SQL_EXPORT_BATCH_SIZE-row batches and writes
    a CSV to tmp_path with the same name/shape ensure_csv()'s other paths
    produce — nothing downstream needs to know this method was used.
    """
    import csv as _csv

    source = _SQL_TABLE_SOURCES.get(fname)
    if not source:
        return False  # no table configured for this file — not this method's job

    host = os.environ.get('DATABRICKS_HOST', '').rstrip('/')
    token = os.environ.get('TRANSACTIONS_TOKEN') or os.environ.get('DATABRICKS_TOKEN', '')
    warehouse_id = os.environ.get('DATABRICKS_SQL_WAREHOUSE_ID', '').strip()
    if not host.startswith('http'):
        host = f'https://{host}' if host else host
    fqn = f"{source['catalog']}.{source['schema']}.{source['table']}"

    if not host or not token or not warehouse_id:
        missing = [k for k, v in (
            ('DATABRICKS_HOST', host), ('DATABRICKS_TOKEN', token), ('DATABRICKS_SQL_WAREHOUSE_ID', warehouse_id)
        ) if not v]
        reason = f"Cannot query {fqn}: missing env vars {missing}."
        logger.warning(f"[large_file_loader] {reason}")
        if on_error:
            try:
                on_error(reason)
            except Exception:
                pass
        return False

    try:
        count_result = _sql_exec(host, token, warehouse_id, f"SELECT COUNT(*) FROM {fqn}")
        total_rows = int(count_result["result"]["data_array"][0][0])
        logger.info(f"[large_file_loader] {fqn} has {total_rows:,} rows — exporting via SQL warehouse in "
                    f"batches of {_SQL_EXPORT_BATCH_SIZE:,}")

        _TMP_BASE.mkdir(parents=True, exist_ok=True)
        columns: Optional[list] = None
        rows_written = 0
        with open(tmp_path, 'w', newline='', encoding='utf-8') as fp:
            writer = None
            offset = 0
            while offset < total_rows or (total_rows == 0 and offset == 0):
                batch = _sql_exec(
                    host, token, warehouse_id,
                    f"SELECT * FROM {fqn} LIMIT {_SQL_EXPORT_BATCH_SIZE} OFFSET {offset}",
                    timeout_secs=180,
                )
                if columns is None:
                    cols_raw = ((batch.get("manifest") or {}).get("schema") or {}).get("columns") or []
                    columns = [c.get("name") or f"col_{i}" for i, c in enumerate(cols_raw)]
                    writer = _csv.writer(fp)
                    writer.writerow(columns)
                batch_rows = (batch.get("result") or {}).get("data_array") or []
                for row in batch_rows:
                    writer.writerow(row)
                rows_written += len(batch_rows)
                if on_progress:
                    try:
                        on_progress(rows_written, total_rows or None)
                    except Exception:
                        pass
                if not batch_rows:
                    break  # defensive: stop if a batch unexpectedly comes back empty
                offset += _SQL_EXPORT_BATCH_SIZE

        logger.info(
            f"[large_file_loader] Exported {rows_written:,} rows from {fqn} -> {tmp_path} "
            "via SQL warehouse — successfully loaded"
        )
        return True
    except Exception as exc:
        reason = f"SQL warehouse export of {fqn} failed: {exc}"
        logger.error(f"[large_file_loader] {reason}")
        if on_error:
            try:
                on_error(reason)
            except Exception:
                pass
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return False


def ensure_csv(
    local_path: Path,
    vol_path: str | None = None,
    on_progress: Optional[ProgressCallback] = None,
    on_error: Optional[Callable[[str], None]] = None,
    allow_download: bool = False,
) -> Path:
    """
    Return a valid path to the requested CSV file.

    Priority order:
      1. local_path            (dev Repos — fast, always correct in dev)
      2. /tmp/meridian_bank/   (cached download — persists within an App instance)
      3. Direct /Volumes/ path (UC Volume mounted in the App container — no REST call)
      4. Files REST API        (download via DATABRICKS_HOST + DATABRICKS_TOKEN)
      5. SQL warehouse export  (query the equivalent table instead of the volume)

    Steps 3-5 all reach out to Databricks and only run when allow_download=True
    — the caller must explicitly opt in. This is what the Data Loader's
    dedicated Download button does; every other caller (Agent A/B loading
    their input data, the chat engine, /datasets/load, the startup cache
    restore) calls this with the default False, so a missing file is simply
    reported as unavailable instead of silently kicking off a slow network
    fetch the user never asked for — the download only ever happens when the
    user explicitly clicks Download in the Data Loader.

    Returns local_path on total failure (or when allow_download=False and the
    file isn't already cached); caller's .is_file() will surface the gap.

    on_progress, if given, is called as the file becomes available so a caller
    can drive a live progress indicator. Steps 1-3 are near-instant local disk
    operations — on_progress fires once with (final_size, final_size). Step 4
    is a real network download and fires incrementally as data streams in.

    on_error, if given, is called with a specific, human-readable reason on
    total failure (missing env vars, 403/permissions, or the raw exception
    text) — this is the only way to learn WHY beyond the return value, since
    ensure_csv() always returns a Path and never raises (every caller checks
    .exists() on the result rather than handling an exception).
    """
    def _report_error(reason: str) -> None:
        if on_error:
            try:
                on_error(reason)
            except Exception:
                pass
    def _report_done(p: Path) -> None:
        if not on_progress:
            return
        try:
            size = p.stat().st_size
            on_progress(size, size)
        except Exception:
            pass  # a broken progress callback must never fail the actual file load

    # ── 1. Local dev path ────────────────────────────────────────────────────
    if local_path.exists():
        _report_done(local_path)
        return local_path

    fname = local_path.name
    tmp_path = _TMP_BASE / fname

    # ── 2. Already cached from a previous download this App instance ─────────
    if tmp_path.exists():
        logger.info(f"[large_file_loader] Using cached {fname} from {tmp_path} — successfully loaded")
        _report_done(tmp_path)
        return tmp_path

    if not allow_download:
        # Not present locally or cached, and this caller didn't explicitly ask
        # to fetch it — report "not available" rather than reaching out to
        # Databricks. Not an error: this is the expected, quiet outcome for
        # every caller except the Data Loader's own Download action.
        logger.info(f"[large_file_loader] {fname} not available locally and allow_download=False — skipping fetch")
        return local_path

    # Resolve the UC Volume path for this file
    resolved_vol = vol_path or _LARGE_FILES.get(fname)
    if not resolved_vol:
        reason = f"No UC Volume path configured for {fname}"
        logger.warning(f"[large_file_loader] {reason}")
        _report_error(reason)
        return local_path

    # ── 3. Direct filesystem access (UC Volume mounted in App container) ──────
    # Databricks Apps can read /Volumes/... directly when the App's service
    # principal has been granted READ FILES on the volume — no HTTP call needed.
    vol_direct = Path(resolved_vol)
    if vol_direct.exists():
        try:
            _TMP_BASE.mkdir(parents=True, exist_ok=True)
            shutil.copy2(vol_direct, tmp_path)
            size_mb = tmp_path.stat().st_size / 1_048_576
            logger.info(
                f"[large_file_loader] Copied {fname} from UC Volume -> {tmp_path} "
                f"({size_mb:.1f} MB) — successfully loaded"
            )
            _report_done(tmp_path)
            return tmp_path
        except Exception as exc:
            logger.warning(f"[large_file_loader] Direct volume copy failed: {exc}")
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    # ── 4. Databricks Files REST API download ─────────────────────────────────
    host = os.environ.get('DATABRICKS_HOST', '').rstrip('/')
    # TRANSACTIONS_TOKEN overrides the app service-principal token, which
    # may lack READ VOLUME in older metastores. Set it in App -> Environment.
    token = os.environ.get('TRANSACTIONS_TOKEN') or os.environ.get('DATABRICKS_TOKEN', '')

    if not host or not token:
        reason = (
            f"DATABRICKS_HOST / DATABRICKS_TOKEN not set — cannot download {fname}. "
            f"Place the file at {local_path} or set env vars."
        )
        logger.warning(f"[large_file_loader] {reason}")
        _report_error(reason)
        return local_path

    # Databricks Apps injects DATABRICKS_HOST as a bare hostname (no scheme).
    # urllib.request requires a full URL with https://.
    if not host.startswith('http'):
        host = f'https://{host}'

    try:
        import urllib.request
        _TMP_BASE.mkdir(parents=True, exist_ok=True)
        url = f"{host}/api/2.0/fs/files{resolved_vol}"
        logger.info(f"[large_file_loader] Downloading {fname} from {url} ...")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        chunk_size = 512 * 1024
        with urllib.request.urlopen(req, timeout=300) as resp, open(tmp_path, 'wb') as fp:
            total_str = resp.getheader('Content-Length')
            total = int(total_str) if total_str and total_str.isdigit() else None
            downloaded = 0
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                fp.write(chunk)
                downloaded += len(chunk)
                if on_progress:
                    try:
                        on_progress(downloaded, total)
                    except Exception:
                        pass  # a broken progress callback must never abort the download
        size_mb = tmp_path.stat().st_size / 1_048_576
        logger.info(
            f"[large_file_loader] Downloaded {fname} -> {tmp_path} "
            f"({size_mb:.1f} MB) via Databricks Files REST API — successfully loaded"
        )
        return tmp_path
    except Exception as exc:
        # Never let a download failure (network, auth, or even a logging encoding
        # issue) escape this function — every caller expects ensure_csv() to always
        # return a Path, falling back to local_path on total failure so its own
        # .exists() check can surface the gap, rather than crashing the whole
        # dataset-load/Agent-A/chatbot request that triggered this fallback.
        err_str = str(exc)
        logger.error(f"[large_file_loader] ERROR downloading {fname}: {exc}")
        if '403' in err_str or 'Forbidden' in err_str:
            try:
                catalog, schema, volume = resolved_vol.split('/')[2:5]
                grant_hint = f"GRANT READ FILES ON VOLUME {catalog}.{schema}.{volume} TO `<principal>`;"
            except (IndexError, ValueError):
                grant_hint = "GRANT READ FILES ON VOLUME <catalog>.<schema>.<volume> TO `<principal>`;"
            volume_error_reason = (
                f"403 Forbidden — the token in DATABRICKS_TOKEN/TRANSACTIONS_TOKEN lacks READ FILES "
                f"on the UC Volume {resolved_vol}. Run in Databricks (as a user/admin who can grant "
                f"volume access): {grant_hint} — where <principal> is whichever identity that token "
                f"belongs to (a user email for a personal access token, or the app's service principal "
                f"name if deployed, found under Databricks -> Apps -> <this app> -> Permissions)."
            )
            logger.error(f"[large_file_loader] {volume_error_reason}")
        else:
            volume_error_reason = f"Download failed: {err_str}"
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

        # ── 5. SQL warehouse export (table SELECT permission, not volume file access) ──
        # Tried only after the volume/REST path above has already failed, so
        # this is purely additive — anyone with volume access is unaffected.
        # It reports its own on_error on failure; only fall back to the volume
        # error above when this method isn't even applicable to this file.
        if fname in _SQL_TABLE_SOURCES:
            if _download_via_sql_warehouse(fname, tmp_path, on_progress, on_error):
                return tmp_path
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        else:
            _report_error(volume_error_reason)
        return local_path

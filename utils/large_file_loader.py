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
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_TMP_BASE = Path('/tmp/meridian_bank')
_DEFAULT_VOL_BASE = '/Volumes/dev/banking/meridian_preloaded'

_LARGE_FILES = {
    'transactions.csv': os.environ.get(
        'TRANSACTIONS_VOLUME_PATH',
        f'{_DEFAULT_VOL_BASE}/transactions.csv',
    ),
}


def ensure_csv(local_path: Path, vol_path: str | None = None) -> Path:
    """
    Return a valid path to the requested CSV file.

    Priority order:
      1. local_path            (dev Repos — fast, always correct in dev)
      2. /tmp/meridian_bank/   (cached download — persists within an App instance)
      3. Direct /Volumes/ path (UC Volume mounted in the App container — no REST call)
      4. Files REST API        (download via DATABRICKS_HOST + DATABRICKS_TOKEN)

    Returns local_path on total failure; caller's .is_file() will surface the gap.
    """
    # ── 1. Local dev path ────────────────────────────────────────────────────
    if local_path.exists():
        return local_path

    fname = local_path.name
    tmp_path = _TMP_BASE / fname

    # ── 2. Already cached from a previous download this App instance ─────────
    if tmp_path.exists():
        logger.info("[large_file_loader] Using cached %s from %s", fname, tmp_path)
        return tmp_path

    # Resolve the UC Volume path for this file
    resolved_vol = vol_path or _LARGE_FILES.get(fname)
    if not resolved_vol:
        logger.warning("[large_file_loader] No UC Volume path configured for %s", fname)
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
            print(
                f"[large_file_loader] Copied {fname} from UC Volume → {tmp_path} ({size_mb:.1f} MB)",
                flush=True,
            )
            return tmp_path
        except Exception as exc:
            logger.warning("[large_file_loader] Direct volume copy failed: %s", exc)
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    # ── 4. Databricks Files REST API download ─────────────────────────────────
    host = os.environ.get('DATABRICKS_HOST', '').rstrip('/')
    # TRANSACTIONS_TOKEN overrides the app service-principal token, which
    # may lack READ VOLUME in older metastores. Set it in App → Environment.
    token = os.environ.get('TRANSACTIONS_TOKEN') or os.environ.get('DATABRICKS_TOKEN', '')

    if not host or not token:
        logger.warning(
            "[large_file_loader] DATABRICKS_HOST / DATABRICKS_TOKEN not set — "
            "cannot download %s. Place the file at %s or set env vars.",
            fname, local_path,
        )
        return local_path

    # Databricks Apps injects DATABRICKS_HOST as a bare hostname (no scheme).
    # urllib.request requires a full URL with https://.
    if not host.startswith('http'):
        host = f'https://{host}'

    try:
        import urllib.request
        _TMP_BASE.mkdir(parents=True, exist_ok=True)
        url = f"{host}/api/2.0/fs/files{resolved_vol}"
        print(f"[large_file_loader] Downloading {fname} from {url} ...", flush=True)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=300) as resp, open(tmp_path, 'wb') as fp:
            shutil.copyfileobj(resp, fp)
        size_mb = tmp_path.stat().st_size / 1_048_576
        print(
            f"[large_file_loader] Downloaded {fname} → {tmp_path} ({size_mb:.1f} MB)",
            flush=True,
        )
        return tmp_path
    except Exception as exc:
        err_str = str(exc)
        print(f"[large_file_loader] ERROR downloading {fname}: {exc}", flush=True)
        if '403' in err_str or 'Forbidden' in err_str:
            print(
                "[large_file_loader] 403 Forbidden — the App's service principal lacks "
                "READ FILES on the UC Volume. Fix by running this SQL in Databricks:\n"
                f"  GRANT READ FILES ON VOLUME {resolved_vol.split('/')[2]}.{resolved_vol.split('/')[3]}.{resolved_vol.split('/')[4]}\n"
                "  TO `<your-app-service-principal>`;\n"
                "Find the service principal name in Databricks → Apps → <this app> → Permissions.",
                flush=True,
            )
        logger.error("[large_file_loader] Could not download %s from %s: %s", fname, resolved_vol, exc)
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return local_path

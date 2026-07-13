"""
Utility for loading large CSV files that are excluded from Databricks App deployments
(> 10 MB per-file limit).

Pattern:
  - Local Repos path is checked first (fast, works in dev).
  - /tmp/meridian_bank/ is checked next (persists across requests in same App instance).
  - If neither exists, the file is downloaded from the UC Volume via the Databricks
    Files REST API (DATABRICKS_HOST + DATABRICKS_TOKEN, auto-injected by Databricks Apps).
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

    Priority:
      1. local_path (Repos path — present in dev, absent in Databricks App for large files)
      2. /tmp/meridian_bank/<filename>  (already downloaded this App instance)
      3. Download from UC Volume via Databricks Files API → /tmp/meridian_bank/<filename>

    Returns local_path if download is impossible or fails — caller's is_file() will handle it.
    """
    if local_path.exists():
        return local_path

    fname = local_path.name
    tmp_path = _TMP_BASE / fname

    if tmp_path.exists():
        logger.info("Using cached %s from %s", fname, tmp_path)
        return tmp_path

    # Resolve the UC Volume path for this file
    resolved_vol = vol_path or _LARGE_FILES.get(fname)
    if not resolved_vol:
        logger.warning("No UC Volume path configured for %s — cannot download", fname)
        return local_path

    host = os.environ.get('DATABRICKS_HOST', '').rstrip('/')
    token = os.environ.get('DATABRICKS_TOKEN', '')

    if not host or not token:
        logger.warning(
            "DATABRICKS_HOST / DATABRICKS_TOKEN not set — cannot download %s. "
            "Set these env vars or place the file at %s",
            fname, local_path,
        )
        return local_path

    # Databricks Apps injects DATABRICKS_HOST as bare hostname (no scheme).
    # urllib.request requires a full URL, so add https:// when missing.
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
        print(f"[large_file_loader] Downloaded {fname} → {tmp_path} ({size_mb:.1f} MB)", flush=True)
        return tmp_path
    except Exception as exc:
        print(f"[large_file_loader] ERROR downloading {fname}: {exc}", flush=True)
        logger.error("Could not download %s from %s: %s", fname, resolved_vol, exc)
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return local_path

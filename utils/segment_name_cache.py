"""
Persists generated segment/persona names (Agent A macro personas and their
micro sub-segments) so re-running segmentation within a configurable window
reuses the same name for the same logical segment, instead of asking the LLM
to re-name something that's still the same archetype it was an hour ago.

Keyed by a stable identity (archetype type for macro, (macro_segment_id,
micro_id) for micro)  -  NOT by cluster label or display name, both of which
can vary run to run even when the underlying segment concept hasn't changed.

On-disk (not in-memory-only): this app commonly runs under `uvicorn --reload`,
which restarts the whole process  -  and wipes in-memory state  -  on every
backend file edit, so an in-memory cache alone couldn't honor a real
multi-hour window.
"""
import json
import os
import threading
import time
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# The one value to edit to change how long a generated name stays locked in
# before segmentation is allowed to generate a new one for that same segment.
# Deliberately a plain backend constant  -  not read from any config file, not
# exposed via any endpoint or UI control.
CACHE_TTL_HOURS = 24

_CACHE_PATH = Path(__file__).parent.parent / "data" / ".segment_names_cache.json"
_TMP_CACHE_PATH = Path("/tmp/.segment_names_cache.json")

_lock = threading.Lock()
_cache: Optional[Dict[str, Dict[str, Any]]] = None  # lazy-loaded, in-memory mirror of the file


def _resolve_path() -> Path:
    """Local dev/most deployments: project_root/data/. Databricks Apps bundles
    can be read-only there, so fall back to /tmp  -  same shape as the existing
    Agent A results cache's path resolution."""
    if _CACHE_PATH.parent.is_dir():
        return _CACHE_PATH
    return _TMP_CACHE_PATH


def _load_locked() -> Dict[str, Dict[str, Any]]:
    global _cache
    if _cache is not None:
        return _cache
    path = _resolve_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            _cache = json.load(f)
    except Exception:
        _cache = {}
    return _cache


def _save_locked() -> None:
    path = _resolve_path()
    tmp = path.with_suffix(".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_cache, f, indent=2)
        os.replace(tmp, path)  # atomic  -  safe if the process is killed mid-write
    except Exception as e:
        logger.warning("segment_name_cache: failed to persist %s: %s", path, e)


def get_cached_name(scope: str, key: str) -> Optional[Dict[str, Any]]:
    """Returns {'name','description','source','cached_at'} if a still-fresh
    entry exists for (scope, key), else None. scope e.g. 'banking_macro' /
    'banking_micro'; key e.g. an archetype_type string, or 'macro_id:micro_id'."""
    with _lock:
        cache = _load_locked()
        entry = cache.get(scope, {}).get(key)
        if not entry:
            return None
        age_hours = (time.time() - entry.get("cached_at", 0)) / 3600
        if age_hours >= CACHE_TTL_HOURS:
            return None
        return dict(entry)


def save_name(scope: str, key: str, name: str, description: str, source: str) -> None:
    """Writes/overwrites the (scope, key) entry with cached_at=now() and
    persists the whole cache to disk. Cheap at this call volume (a handful of
    macro names + a couple dozen micro names per segmentation run)."""
    with _lock:
        cache = _load_locked()
        cache.setdefault(scope, {})[key] = {
            "name": name,
            "description": description,
            "source": source,
            "cached_at": time.time(),
        }
        _save_locked()

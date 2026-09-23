"""
Loads config/llm_priority.json  -  lets a human reorder which LLM provider
(and which specific Together AI model) this app tries first, separately for
Agent A/B/C/D generation calls vs. the Segment AI chatbot, without touching
any Python code. Re-read on every call (the file is tiny) so edits apply
immediately  -  no backend restart needed.

Falls back to sane built-in defaults if the file is missing or malformed, so
a broken edit degrades gracefully rather than breaking every LLM call.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "llm_priority.json"

_DEFAULTS: Dict[str, Any] = {
    "agent_functions": {"providers": ["together", "anthropic"]},
    "chatbot": {"providers": ["anthropic", "together"]},
    "together_models": [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3-8B-Instruct-Lite",
    ],
    "anthropic_model": "claude-haiku-4-5-20251001",
}

_VALID_PROVIDERS = {"together", "anthropic"}


def load_llm_priority() -> Dict[str, Any]:
    """Read config/llm_priority.json, shallow-merged over defaults so a
    partially-edited file (e.g. the user only touched "chatbot") doesn't
    lose the other sections."""
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning(f"[llm_priority] {_CONFIG_PATH} not found  -  using built-in defaults")
        return _DEFAULTS
    except Exception as e:
        logger.warning(f"[llm_priority] Could not parse {_CONFIG_PATH} ({e})  -  using built-in defaults")
        return _DEFAULTS

    merged = dict(_DEFAULTS)
    for key in ("agent_functions", "chatbot"):
        if isinstance(data.get(key), dict):
            merged[key] = {**_DEFAULTS[key], **data[key]}
    if isinstance(data.get("together_models"), list) and data["together_models"]:
        merged["together_models"] = data["together_models"]
    if isinstance(data.get("anthropic_model"), str) and data["anthropic_model"].strip():
        merged["anthropic_model"] = data["anthropic_model"].strip()
    return merged


def get_provider_order(scope: str) -> List[str]:
    """scope: 'chatbot' or 'agent_functions'. Returns an ordered, validated
    provider list  -  never empty, never containing an unrecognized provider."""
    cfg = load_llm_priority()
    section = cfg.get(scope) or _DEFAULTS.get(scope, {})
    order = section.get("providers") or _DEFAULTS[scope]["providers"]
    cleaned = [p for p in order if p in _VALID_PROVIDERS]
    if not cleaned:
        logger.warning(f"[llm_priority] '{scope}.providers' has no valid entries  -  using default order")
        return list(_DEFAULTS[scope]["providers"])
    return cleaned


def get_together_models() -> List[str]:
    cfg = load_llm_priority()
    models = cfg.get("together_models") or _DEFAULTS["together_models"]
    return list(models)


def get_anthropic_model() -> str:
    cfg = load_llm_priority()
    return cfg.get("anthropic_model") or _DEFAULTS["anthropic_model"]

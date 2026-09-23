"""
Cross-module LLM token-usage tracking (Together AI + Anthropic/Claude).

Two things live here:

1. A thread-local accumulator scoped to one logical unit of work (e.g. one
   chatbot question-to-reply round trip, which may fan out into several LLM
   calls across retries/grounding passes). reset_scope()/get_scope_usage()
   let a caller wrap a block of work and read back the total afterwards,
   without threading a counter through every intermediate LLM call site.

2. log_llm_call()  -  a single structured console-log line emitted for every
   LLM invocation, Together AI and Anthropic/Claude alike, so token spend
   (and thus $ cost) can be audited from the server console alone. This
   NEVER logs prompt/response content  -  metadata and metrics only.
"""
import json
import logging
import threading
from datetime import datetime, timezone

logger = logging.getLogger("token_tracker")

_local = threading.local()


def reset_scope() -> None:
    """Start a fresh accumulation scope  -  call at the top of one logical request
    (e.g. one chatbot question) before any LLM calls it may trigger."""
    _local.usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "calls": 0}


def get_scope_usage() -> dict:
    """Tokens accumulated in the current scope since the last reset_scope()."""
    if not hasattr(_local, "usage"):
        reset_scope()
    return dict(_local.usage)


def _record_scope(prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
    if not hasattr(_local, "usage"):
        reset_scope()
    u = _local.usage
    u["prompt_tokens"] += int(prompt_tokens or 0)
    u["completion_tokens"] += int(completion_tokens or 0)
    u["total_tokens"] += int(total_tokens or 0)
    u["calls"] += 1


def log_llm_call(
    provider: str,
    agent: str,
    call_type: str,
    duration_ms: int,
    success: bool,
    model: str = "",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    fallback_used: bool = False,
    note: str = "",
) -> None:
    """
    Log one LLM API call's metadata/metrics to the console  -  provider, model,
    duration, and token counts (never the prompt or response content)  -  and
    add its tokens to the current accumulation scope (see reset_scope above).
    """
    total_tokens = total_tokens or (prompt_tokens + completion_tokens)
    _record_scope(prompt_tokens, completion_tokens, total_tokens)
    payload = {
        "type": "llm_call",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "agent": agent,
        "call_type": call_type,
        "model": model,
        "duration_ms": duration_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "success": success,
        "fallback_used": fallback_used,
    }
    if note:
        payload["note"] = note
    logger.info(json.dumps(payload))

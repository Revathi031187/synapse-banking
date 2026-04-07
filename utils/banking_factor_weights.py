"""
Banking Agent B — 12-factor weight defaults, validation, and AI/heuristic persona weights.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _scorer_weights():
    from agents.banking_12_factor_scorer import Banking12FactorScorer

    return Banking12FactorScorer.WEIGHTS


def factor_keys() -> List[str]:
    return list(_scorer_weights().keys())


def default_weights_percent() -> Dict[str, float]:
    return {k: round(v * 100, 2) for k, v in _scorer_weights().items()}


FACTOR_LABELS: Dict[str, str] = {
    "eligibility_score": "Eligibility (credit, income, balance)",
    "financial_need_match": "Financial need match",
    "relationship_depth": "Relationship depth & loyalty",
    "product_value": "Product value (fees, APY, min balance)",
    "product_pairing": "Cross-sell / product pairing",
    "channel_fit": "Channel fit (digital vs branch)",
    "complexity_match": "Complexity vs customer sophistication",
    "intent_score": "Cross-sell intent / receptivity",
    "segment_affinity": "Segment affinity (peer behavior)",
    "transaction_pattern": "Transaction pattern fit",
    "product_rating": "Product rating / quality",
    "popularity": "Popularity in segment",
}


def validate_weights_percent(weights: Dict[str, Any]) -> Tuple[bool, str, float]:
    keys = factor_keys()
    if not weights:
        return False, "No weights provided", 0.0
    total = sum(float(weights.get(k, 0) or 0) for k in keys)
    if abs(total - 100.0) > 1.5:
        return False, f"Weights must sum to 100% (currently {total:.1f}%)", total
    return True, "", total


def _normalize_to_100(pct: Dict[str, float]) -> Dict[str, float]:
    keys = factor_keys()
    raw = {k: max(0.0, float(pct.get(k, 0))) for k in keys}
    s = sum(raw.values())
    if s <= 0:
        return default_weights_percent()
    out = {k: round(100.0 * raw[k] / s, 2) for k in keys}
    diff = round(100.0 - sum(out.values()), 2)
    out[keys[0]] = round(out[keys[0]] + diff, 2)
    return out


def build_customer_feature_summary(customer_context: Optional[Dict[str, Any]]) -> str:
    """Stable, compact summary for LLM prompts and cache keys."""
    if not customer_context or not isinstance(customer_context, dict):
        return ""
    metrics = customer_context.get("metrics") or {}
    if not isinstance(metrics, dict):
        metrics = {}
    parts: List[str] = []
    cid = customer_context.get("customer_id")
    if cid is not None:
        parts.append(f"customer_id={cid}")
    if customer_context.get("cluster_id") is not None:
        parts.append(f"cluster_id={customer_context.get('cluster_id')}")
    pn = customer_context.get("persona")
    if pn is not None and str(pn).strip():
        parts.append(f"persona={str(pn).strip()}")
    for k in (
        "credit_score",
        "income",
        "num_products",
        "total_deposits",
        "digital_engagement",
        "cross_sell_receptivity",
    ):
        if k in metrics and metrics.get(k) is not None:
            try:
                parts.append(f"{k}={float(metrics[k]):.4g}")
            except (TypeError, ValueError):
                parts.append(f"{k}={metrics[k]}")
    return "; ".join(parts)


def ai_weights_cache_fingerprint(
    persona_id: Optional[int],
    customer_id: Optional[str],
    customer_context: Optional[Dict[str, Any]],
) -> str:
    """Deterministic short key for caching AI weight + rationale responses."""
    parts: List[str] = []
    if persona_id is not None:
        parts.append(f"pid:{int(persona_id)}")
    if customer_id:
        parts.append(f"cid:{str(customer_id).strip()}")
    summary = build_customer_feature_summary(customer_context)
    parts.append(f"feat:{summary}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:40]


def heuristic_rationales_from_customer_data(
    keys: List[str],
    weights_percent: Dict[str, float],
    persona_name: str,
    customer_context: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    """
    When the LLM path is unavailable, still attach short data-grounded copy so Agent B
    shows per-factor explanations before Submit (persona + customer feature summary).
    """
    summary = build_customer_feature_summary(customer_context).strip()
    if not summary:
        summary = (
            "persona-only context — select Customer mode and a customer for row-level metrics "
            "(deposits, credit, engagement) in these explanations."
        )
    raw: Dict[str, str] = {}
    for k in keys:
        label = FACTOR_LABELS.get(k, k)
        raw[k] = (
            f"Heuristic allocation for “{persona_name}”. "
            f"Data snapshot: {summary}. "
            f"This factor reflects {label.lower()} — adjust the slider if underwriting or channel fit should weigh differently."
        )[:450]
    return _finalize_rationales_for_weights(keys, weights_percent, raw)


def heuristic_weights_for_persona(persona_name: str) -> Dict[str, float]:
    """Persona-tuned weights when LLM is unavailable."""
    w = {k: float(v) for k, v in _scorer_weights().items()}
    n = (persona_name or "").lower()

    def move(fr: str, to: str, amt: float) -> None:
        if w[fr] <= amt:
            return
        w[fr] -= amt
        w[to] += amt

    if any(x in n for x in ("digital", "young", "millennial", "native", "professional")):
        move("relationship_depth", "channel_fit", 0.04)
        move("transaction_pattern", "product_value", 0.03)
        move("segment_affinity", "complexity_match", 0.02)
    elif any(x in n for x in ("traditional", "loyal", "established", "saver", "household")):
        move("channel_fit", "relationship_depth", 0.05)
        move("intent_score", "product_value", 0.04)
    elif any(x in n for x in ("wealth", "investor", "affluent", "platinum")):
        move("intent_score", "product_value", 0.05)
        move("transaction_pattern", "eligibility_score", 0.03)
    elif "business" in n or "commercial" in n or "agricultural" in n or "farm" in n:
        move("product_rating", "financial_need_match", 0.05)
        move("popularity", "product_pairing", 0.04)
    return _normalize_to_100({k: w[k] * 100 for k in w})


def _parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
    if not text or len(text) < 10:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _extract_weights_and_rationales(
    data: Dict[str, Any], keys: List[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Support nested {weights, rationales} or legacy flat factor keys only."""
    if not data:
        return None, None
    w_block = data.get("weights")
    r_block = data.get("rationales")
    if isinstance(w_block, dict):
        return w_block, r_block if isinstance(r_block, dict) else {}
    # Legacy: all factor keys at top level
    if any(k in data for k in keys):
        return data, {}
    return None, None


def _merge_rationales(keys: List[str], raw: Any) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not isinstance(raw, dict):
        raw = {}
    for k in keys:
        t = raw.get(k)
        out[k] = (str(t).strip() if t is not None else "")[:500]
    return out


def _finalize_rationales_for_weights(
    keys: List[str],
    weights_percent: Dict[str, float],
    raw_rationales: Dict[str, str],
) -> Dict[str, str]:
    """
    Prefix each rationale with the **final normalized %** and factor label so copy matches sliders.
    If the model already opened with ~the same %, keep the original text.
    """
    out: Dict[str, str] = {}
    for k in keys:
        p = round(float(weights_percent.get(k, 0) or 0), 2)
        label = FACTOR_LABELS.get(k, k)
        t = (raw_rationales.get(k) or "").strip()
        if not t:
            out[k] = f"{p}% of total score on “{label}” (no rationale returned)."
            continue
        m = re.match(r"^(\d{1,2}(?:\.\d+)?)\s*%", t)
        if m:
            try:
                stated = float(m.group(1))
                if abs(stated - p) <= 2.0:
                    out[k] = t[:500]
                    continue
            except ValueError:
                pass
        rest = t
        if rest.lower().startswith("because "):
            rest = rest[8:].strip()
        out[k] = f"{p}% → “{label}”: {rest}"[:500]
    return out


def ai_recommended_weights_for_persona(
    persona_name: str,
    persona_description: str = "",
    customer_context: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, float], str, str, Dict[str, str]]:
    """
    Returns (weights_percent, source, note, factor_rationales).
    source is 'llm' or 'heuristic'.
    factor_rationales maps factor_key -> short explanation (empty for heuristic path).
    """
    keys = factor_keys()
    key_list = ", ".join(keys)
    desc = (persona_description or "")[:800]
    summary = build_customer_feature_summary(customer_context)
    summary_block = (
        f"\nCustomer data (cite ONLY these fields; if a field is absent, say unknown — do not invent):\n{summary}\n"
        if summary
        else "\n(No per-customer row: use persona name + description only.)\n"
    )
    labels_lines = "\n".join(f'  - "{k}": {FACTOR_LABELS.get(k, k)}' for k in keys)

    try:
        from utils.together_ai import together_ai

        prompt = f"""You calibrate weights for a 12-factor banking recommendation scorer (100 points total across factors).

Persona / segment name: {persona_name}
Segment description: {desc}{summary_block}

Factor keys and what they measure:
{labels_lines}

Return ONLY valid JSON:
{{
  "weights": {{
    {", ".join(f'"{k}": <integer>' for k in keys)}
  }},
  "rationales": {{
    {", ".join(f'"{k}": "<text>"' for k in keys)}
  }}
}}

Hard rules for "weights":
- Non-negative integers only; the sum of all twelve MUST be exactly 100.

Hard rules for "rationales" (max 280 characters each):
1. First clause MUST give the same integer weight as in "weights" for that key (e.g. "19 points go to …" or "We assign 14 of 100 points because …").
2. Second clause MUST explain why that **share of the 100 points** is justified **for this customer/persona** using 1–2 concrete numbers or facts from the data line above (credit_score, income, num_products, deposits, digital_engagement, cross_sell_receptivity, cluster_id, persona name). Explain the **trade-off**: why this factor earns more or fewer points than a minor factor (e.g. eligibility vs popularity).
3. Do NOT invent segment nicknames, job titles, or "leader/builder" labels unless they appear verbatim in the segment description.
4. Do NOT mention the customer_id more than once in a single rationale.
5. Make each factor’s wording distinct — no copy-paste across keys.
6. If the model must down-weight a factor (low points), say explicitly it is a weaker signal for this profile."""

        raw = together_ai.generate_text(
            prompt,
            system_message=(
                "You output only compact JSON. No markdown code fences. No commentary outside JSON. "
                "Rationales must justify the numeric weight allocation using only provided data."
            ),
            max_tokens=1600,
            temperature=0.0,
        )
        if raw and "Error generating" not in raw[:80]:
            data = _parse_llm_json(raw)
            if data:
                w_block, r_block = _extract_weights_and_rationales(data, keys)
                if w_block:
                    pct: Dict[str, float] = {}
                    for k in keys:
                        v = w_block.get(k)
                        if v is None:
                            pct[k] = _scorer_weights()[k] * 100
                        else:
                            pct[k] = max(0, int(round(float(v))))
                    if sum(pct.values()) > 0:
                        pct = _normalize_to_100(pct)
                        rationales = _merge_rationales(keys, r_block)
                        rationales = _finalize_rationales_for_weights(keys, pct, rationales)
                        return (
                            pct,
                            "llm",
                            "AI-suggested starting weights for this selection. Review and edit before Submit.",
                            rationales,
                        )

    except Exception as e:
        logger.warning("LLM factor weights failed: %s", e)

    h = heuristic_weights_for_persona(persona_name)
    rats = heuristic_rationales_from_customer_data(keys, h, persona_name, customer_context)
    return (
        h,
        "heuristic",
        "Persona + customer data template (AI model unavailable). Review per-factor explanations below, then Submit.",
        rats,
    )

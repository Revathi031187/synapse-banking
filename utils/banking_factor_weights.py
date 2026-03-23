"""
Banking Agent B — 12-factor weight defaults, validation, and AI/heuristic persona weights.
"""

from __future__ import annotations

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


def ai_recommended_weights_for_persona(
    persona_name: str,
    persona_description: str = "",
) -> Tuple[Dict[str, float], str, str]:
    """
    Returns (weights_percent, source, note).
    source is 'llm' or 'heuristic'.
    """
    keys = factor_keys()
    key_list = ", ".join(keys)
    desc = (persona_description or "")[:800]

    try:
        from utils.together_ai import together_ai

        prompt = f"""You are a banking personalization expert. For this customer segment, assign importance (integers only) to each scoring factor. All values MUST sum to exactly 100.

Factors (keys): {key_list}

Persona: {persona_name}
Description: {desc}

Return ONLY valid JSON, one object with exactly those keys and integer values summing to 100. Example shape: {{"eligibility_score": 20, "financial_need_match": 18, ...}}"""

        raw = together_ai.generate_text(
            prompt,
            system_message="You output only compact JSON. No markdown, no explanation outside JSON.",
            max_tokens=500,
            temperature=0.35,
        )
        if raw and "Error generating" not in raw[:80]:
            data = _parse_llm_json(raw)
            if data:
                pct = {}
                for k in keys:
                    v = data.get(k)
                    if v is None:
                        pct[k] = _scorer_weights()[k] * 100
                    else:
                        pct[k] = max(0, int(round(float(v))))
                if sum(pct.values()) > 0:
                    pct = _normalize_to_100(pct)
                    return pct, "llm", "Weights suggested by AI for this persona (Together). You can edit before Submit."

    except Exception as e:
        logger.warning("LLM factor weights failed: %s", e)

    h = heuristic_weights_for_persona(persona_name)
    return (
        h,
        "heuristic",
        "Persona-based template (AI model unavailable). Adjust sliders and Submit.",
    )

"""Unit tests for banking 12-factor weight helpers (determinism, normalization, cache)."""

import pytest

from utils.banking_factor_weights import (
    _normalize_to_100,
    _finalize_rationales_for_weights,
    ai_weights_cache_fingerprint,
    build_customer_feature_summary,
    factor_keys,
    heuristic_weights_for_persona,
    ai_recommended_weights_for_persona,
)
from utils import banking_factor_weights as bfw


def test_normalize_to_100_sums_to_100():
    keys = factor_keys()
    raw = {k: (10.0 if i == 0 else 5.0) for i, k in enumerate(keys)}
    out = _normalize_to_100(raw)
    total = round(sum(out.values()), 2)
    assert abs(total - 100.0) < 0.02
    assert len(out) == len(keys)


def test_build_customer_feature_summary_stable():
    ctx = {
        "customer_id": "C1",
        "cluster_id": 2,
        "metrics": {
            "credit_score": 712.0,
            "income": 85000.0,
            "num_products": 3,
            "digital_engagement": 0.72,
        },
    }
    a = build_customer_feature_summary(ctx)
    b = build_customer_feature_summary(ctx)
    assert a == b
    assert "credit_score" in a
    assert "712" in a


def test_ai_weights_cache_fingerprint_deterministic():
    ctx = {"customer_id": "CUST_1", "cluster_id": 0, "metrics": {"credit_score": 700}}
    fp1 = ai_weights_cache_fingerprint(0, "CUST_1", ctx)
    fp2 = ai_weights_cache_fingerprint(0, "CUST_1", ctx)
    assert fp1 == fp2
    assert len(fp1) == 40


def test_ai_weights_cache_changes_with_customer():
    ctx = {"metrics": {"credit_score": 700}}
    a = ai_weights_cache_fingerprint(0, "A", ctx)
    b = ai_weights_cache_fingerprint(0, "B", ctx)
    assert a != b


def test_extract_weights_nested_and_legacy():
    keys = factor_keys()
    nested = {
        "weights": {k: 8 for k in keys},
        "rationales": {k: f"why {k}" for k in keys},
    }
    w1, r1 = bfw._extract_weights_and_rationales(nested, keys)
    assert w1 is not None
    assert r1 == nested["rationales"]

    legacy = {k: 7 for k in keys}
    w2, r2 = bfw._extract_weights_and_rationales(legacy, keys)
    assert w2 == legacy
    assert r2 == {}


def test_heuristic_fallback_four_tuple(monkeypatch):
    """When LLM is unavailable, heuristic returns four-tuple with empty rationales."""

    class FakeTogether:
        def generate_text(self, *args, **kwargs):
            return "Error generating description"

    monkeypatch.setattr("utils.together_ai.together_ai", FakeTogether())
    w, src, note, rats = ai_recommended_weights_for_persona("Steady Savers", "Test description", None)
    assert src == "heuristic"
    assert set(rats.keys()) == set(factor_keys())
    assert abs(sum(w.values()) - 100.0) < 1.6
    for k in factor_keys():
        assert k in w


def test_merge_rationales_fills_keys():
    keys = factor_keys()
    raw = {"eligibility_score": "only one"}
    out = bfw._merge_rationales(keys, raw)
    assert out["eligibility_score"] == "only one"
    assert out["popularity"] == ""


def test_finalize_rationales_prefixes_weight():
    keys = factor_keys()
    pct = {k: round(100.0 / len(keys), 2) for k in keys}
    diff = round(100.0 - sum(pct.values()), 2)
    first = keys[0]
    pct[first] = round(pct[first] + diff, 2)
    raw = {k: "High fit for this profile." for k in keys}
    out = _finalize_rationales_for_weights(keys, pct, raw)
    assert "→" in out[first]
    assert "%" in out[first]

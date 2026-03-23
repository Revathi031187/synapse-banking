"""Unit tests for Agent D Banking orchestration."""

import pytest
import pandas as pd

from agents.agent_d_banking import AgentD_Banking, _empty_ledger


@pytest.fixture
def products_df():
    return pd.DataFrame(
        [
            {"product_id": "FMB_P001", "product_name": "Checking A", "category": "Personal"},
            {"product_id": "FMB_P012", "product_name": "Credit Card", "category": "Personal"},
            {"product_id": "FMB_P013", "product_name": "Mortgage", "category": "Personal"},
        ]
    )


@pytest.fixture
def all_recs():
    return {
        "tailored_recommendations": [
            {"product_id": "FMB_P001", "product_name": "Checking A", "score": 0.9, "category": "Personal"},
            {"product_id": "FMB_P012", "product_name": "Credit Card", "score": 0.85, "category": "Personal"},
        ],
        "similar_products": [
            {"product_id": "FMB_P013", "product_name": "Mortgage", "score": 0.7, "category": "Personal"},
        ],
        "segment_recommendations": [],
    }


@pytest.fixture
def agent_c():
    return {
        "offer": {
            "product_id": "FMB_P012",
            "product_name": "Credit Card",
            "category": "Personal",
            "score": 0.88,
            "reasoning": "Best commercial fit",
        },
        "reason": "Segment + eligibility",
    }


def test_abandoned_and_saved_prioritized(products_df, all_recs, agent_c):
    d = AgentD_Banking(deprioritize_min_shows=99)
    ledger = _empty_ledger()
    out = d.orchestrate(
        customer_id="C1",
        ledger=ledger,
        saved_goals=["FMB_P001"],
        incomplete_applications=["FMB_P013"],
        clicked_product_ids=[],
        products_df=products_df,
        all_recs=all_recs,
        agent_c_result=agent_c,
    )
    live = out["live_recommendations"]
    slots = [r.get("supervisor_slot") for r in live[:4]]
    assert "incomplete_application" in slots[0] or slots[0] == "incomplete_application"
    assert any(s == "saved_goal" for s in slots[:3])
    assert out["next_visit_directives"]["priority_pin_product_id"] == "FMB_P013"


def test_clicked_product_pins_for_agent_b(products_df, all_recs, agent_c):
    """Customer click on a recommendation becomes #1 pin for next Agent B (over incomplete/saved)."""
    d = AgentD_Banking(deprioritize_min_shows=99)
    ledger = _empty_ledger()
    out = d.orchestrate(
        customer_id="C1",
        ledger=ledger,
        saved_goals=["FMB_P001"],
        incomplete_applications=["FMB_P013"],
        clicked_product_ids=["FMB_P012"],
        products_df=products_df,
        all_recs=all_recs,
        agent_c_result=agent_c,
    )
    assert out["next_visit_directives"]["priority_pin_product_id"] == "FMB_P012"
    assert out["next_visit_directives"]["focus_source"] == "clicked_recommendation"


def test_deprioritize_after_repeated_shows(products_df, all_recs, agent_c):
    d = AgentD_Banking(deprioritize_min_shows=3)
    ledger = _empty_ledger()
    for _ in range(3):
        d.orchestrate(
            customer_id="C2",
            ledger=ledger,
            saved_goals=[],
            incomplete_applications=[],
            clicked_product_ids=[],
            products_df=products_df,
            all_recs=all_recs,
            agent_c_result=agent_c,
        )
    dep = ledger["last_directives"].get("deprioritize_product_ids") or []
    assert len(dep) > 0


def test_apply_directives_boost_and_pin():
    recs = [
        {"product_id": "A", "score": 0.5},
        {"product_id": "B", "score": 0.9},
    ]
    out = AgentD_Banking.apply_directives_to_recommendations(
        recs,
        {
            "boost_product_ids": ["A"],
            "deprioritize_product_ids": [],
            "priority_pin_product_id": "A",
        },
    )
    assert out[0]["product_id"] == "A"
    assert float(out[0]["score"]) > 0.5

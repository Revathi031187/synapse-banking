import pytest

from agents.agent_d_banking_next_best import (
    excluded_until_click,
    execute_next_best_banking,
    mark_impression_clicked,
)


def test_excluded_until_click():
    rows = [
        {"customer_id": "C1", "product_id": "P1", "recommended_at": "t", "clicked_at": ""},
        {"customer_id": "C1", "product_id": "P2", "recommended_at": "t", "clicked_at": "2025-01-01"},
    ]
    assert excluded_until_click(rows, "C1") == {"P1"}


def test_mark_click_clears_exclusion():
    rows = [
        {"customer_id": "C1", "product_id": "P1", "recommended_at": "t", "clicked_at": ""},
    ]
    assert mark_impression_clicked(rows, "C1", "P1")
    assert excluded_until_click(rows, "C1") == set()


def test_execute_next_best_orders_c_before_b():
    all_recs = {
        "tailored_recommendations": [
            {"product_id": "B1", "product_name": "B Product", "score": 0.99, "category": "Personal"},
        ],
        "similar_products": [],
        "segment_recommendations": [],
    }
    c = {"offer": {"product_id": "C1", "product_name": "C Offer", "category": "Personal"}}
    recs, meta = execute_next_best_banking(
        "CUST_X",
        5,
        None,
        all_recs,
        c,
        [],
        [],
        [],
        "",
    )
    assert recs[0]["product_id"] == "C1"
    assert "agent_c" in meta["sources_used"]

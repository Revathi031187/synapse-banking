"""
Banking Agent D — real-time next-best-product engine.
Wishlist + incomplete applications + Agent B + Agent C, with recommendation_impressions
exclusion (no repeat until click). Banking analog of Academy Agent D.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

from agents.agent_d_banking import _pid, _get_product_from_catalog, _merge_b_lists

MAX_PER_CATEGORY_NEXT = 3


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def excluded_until_click(impression_rows: List[Dict[str, Any]], customer_id: str) -> Set[str]:
    """Product IDs shown but not yet clicked for this customer."""
    cid = _pid(customer_id)
    out: Set[str] = set()
    for row in impression_rows or []:
        if _pid(row.get("customer_id")) != cid:
            continue
        pid = _pid(row.get("product_id"))
        if not pid:
            continue
        clicked = row.get("clicked_at")
        if clicked is None or (isinstance(clicked, float) and str(clicked) == "nan"):
            out.add(pid)
        elif isinstance(clicked, str) and str(clicked).strip() in ("", "nan", "None"):
            out.add(pid)
    return out


def wishlist_product_ids(wishlist_rows: List[Dict], customer_id: str) -> List[str]:
    cid = _pid(customer_id)
    seen = []
    for row in wishlist_rows or []:
        if _pid(row.get("customer_id")) != cid:
            continue
        pid = _pid(row.get("product_id"))
        if pid and pid not in seen:
            seen.append(pid)
    return seen


def incomplete_application_ids(abandoned_rows: List[Dict], customer_id: str) -> List[str]:
    cid = _pid(customer_id)
    seen = []
    for row in abandoned_rows or []:
        if _pid(row.get("customer_id")) != cid:
            continue
        pid = _pid(row.get("product_id"))
        if pid and pid not in seen:
            seen.append(pid)
    return seen


def execute_next_best_banking(
    customer_id: str,
    top_n: int,
    products_df: Any,
    all_recs: Optional[Dict[str, Any]],
    agent_c_result: Optional[Dict[str, Any]],
    wishlist_rows: List[Dict],
    incomplete_rows: List[Dict],
    impression_rows: List[Dict],
    persona_name: str = "",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Build ranked next-best list; append new impression rows (caller persists CSV).

    Returns (recommendations, meta) where meta has sources_used, excluded_count, new_impression_rows.
    """
    cid = _pid(customer_id)
    excluded = excluded_until_click(impression_rows, cid)
    excluded_count = len(excluded)

    b_ranked: List[Dict[str, Any]] = _merge_b_lists(all_recs or {}) if all_recs else []
    b_by_id = {_pid(r.get("product_id")): r for r in b_ranked}

    offer = (agent_c_result or {}).get("offer") if agent_c_result else None
    c_pid = _pid(offer.get("product_id")) if offer else ""

    wl = wishlist_product_ids(wishlist_rows, cid)
    inc = incomplete_application_ids(incomplete_rows, cid)

    sources_used: Set[str] = set()
    candidates: List[Tuple[int, float, str, str, Dict[str, Any]]] = []
    # tuple: (tier_lower_is_better, score, reason_code, reason_text, product_dict)

    def add_tier(tier: int, pid: str, reason: str, reason_detail: str, base_rec: Optional[Dict] = None):
        pid = _pid(pid)
        if not pid or pid in excluded:
            return
        rec = base_rec or b_by_id.get(pid) or _get_product_from_catalog(products_df, pid)
        if not rec:
            rec = {
                "product_id": pid,
                "product_name": f"Product {pid}",
                "category": "Banking",
                "score": 0.5,
            }
        else:
            rec = dict(rec)
        rec["recommendation_reason"] = reason_detail
        rec["reason_code"] = reason
        sc = float(rec.get("score") or 0.5)
        candidates.append((tier, -sc, reason, reason_detail, rec))

    # Tier 0: Agent C primary
    if c_pid:
        add_tier(0, c_pid, "agent_c_offer", "From your current best offer (Agent C).", b_by_id.get(c_pid))
        sources_used.add("agent_c")

    # Tier 1: Incomplete applications (recovery)
    for pid in inc:
        add_tier(1, pid, "incomplete_application", "You started this application — pick up where you left off.")
        sources_used.add("incomplete_application")

    # Tier 2: Wishlist / saved goals
    for pid in wl:
        add_tier(2, pid, "wishlist", "From your saved goals / watchlist.")
        sources_used.add("wishlist")

    # Tier 3: Agent B by score
    for r in b_ranked:
        pid = _pid(r.get("product_id"))
        if not pid or pid == c_pid:
            continue
        src = (r.get("d_source") or "persona") if isinstance(r, dict) else "persona"
        if src in ("tailored", "persona"):
            msg = "Strong match for your profile (Agent B)."
        elif src == "similar":
            msg = "Similar to products that fit you (Agent B)."
        else:
            msg = "Popular with customers like you (Agent B)."
        add_tier(3, pid, "agent_b", msg, r)
        sources_used.add("agent_b")

    # Sort: tier, then score desc
    candidates.sort(key=lambda x: (x[0], x[1]))

    used_cat: Dict[str, int] = {}
    used_pid: Set[str] = set()
    out: List[Dict[str, Any]] = []
    for _, _, _, _, rec in candidates:
        pid = _pid(rec.get("product_id"))
        if pid in used_pid:
            continue
        cat = str(rec.get("category") or "General").split("/")[0][:40]
        if used_cat.get(cat, 0) >= MAX_PER_CATEGORY_NEXT:
            continue
        used_pid.add(pid)
        used_cat[cat] = used_cat.get(cat, 0) + 1
        out.append(rec)
        if len(out) >= top_n:
            break

    # Cold-start fill from catalog if still short
    if len(out) < top_n and products_df is not None:
        try:
            for _, row in products_df.iterrows():
                pid = _pid(row.get("product_id"))
                if not pid or pid in excluded or pid in used_pid:
                    continue
                cat = str(row.get("category") or "General")[:40]
                if used_cat.get(cat, 0) >= MAX_PER_CATEGORY_NEXT:
                    continue
                used_pid.add(pid)
                used_cat[cat] = used_cat.get(cat, 0) + 1
                out.append(
                    {
                        "product_id": pid,
                        "product_name": row.get("product_name"),
                        "category": row.get("category"),
                        "score": 0.35,
                        "recommendation_reason": "Suggested from our catalog for your segment.",
                        "reason_code": "catalog_fill",
                    }
                )
                sources_used.add("catalog_fallback")
                if len(out) >= top_n:
                    break
        except Exception as e:
            logger.warning("catalog fill: %s", e)

    new_impressions = [
        {
            "customer_id": cid,
            "product_id": _pid(r.get("product_id")),
            "recommended_at": _now_iso(),
            "clicked_at": "",
        }
        for r in out
    ]

    meta = {
        "sources_used": sorted(sources_used),
        "excluded_count": excluded_count,
        "no_repeat_message": (
            "Products we showed you before — until you tap or open them — stay hidden so we don’t keep "
            "pushing the same offer. Click a product below to engage; then it can appear again in future runs."
        ),
        "new_impression_rows": new_impressions,
        "persona_name": persona_name or "",
    }
    return out, meta


def apply_impression_rows(impression_rows: List[Dict], new_rows: List[Dict]) -> None:
    for row in new_rows:
        impression_rows.append(
            {
                "customer_id": _pid(row.get("customer_id")),
                "product_id": _pid(row.get("product_id")),
                "recommended_at": row.get("recommended_at") or _now_iso(),
                "clicked_at": row.get("clicked_at") if row.get("clicked_at") else "",
            }
        )


def mark_impression_clicked(impression_rows: List[Dict], customer_id: str, product_id: str) -> bool:
    """Set clicked_at on all unclicked rows for (customer, product). Returns True if any updated."""
    cid, pid = _pid(customer_id), _pid(product_id)
    when = _now_iso()
    updated = False
    for row in impression_rows:
        if _pid(row.get("customer_id")) != cid or _pid(row.get("product_id")) != pid:
            continue
        ca = row.get("clicked_at")
        empty = ca is None or (isinstance(ca, str) and not str(ca).strip())
        if empty:
            row["clicked_at"] = when
            updated = True
    return updated

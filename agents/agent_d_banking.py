"""
Agent D Banking — Behavioral supervisor / session orchestration.
Connects saved goals, incomplete applications, and impression/click history to:
- This visit's prioritized product stack (after Agent B + Agent C signals)
- Impression logging for next-run deprioritization
- next_visit_directives contract for Agent B (boost, deprioritize, priority pin)
"""

from __future__ import annotations

import json
import logging
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

try:
    from utils.claude_client import get_claude_client
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    get_claude_client = None

# Shown at least this many times with zero clicks → deprioritize on next B run
DEPRIORITIZE_MIN_SHOWS = 3
MAX_PER_CATEGORY = 3
MAX_LIVE_STACK = 12
MAX_ABANDONED_SLOTS = 2
MAX_SAVED_SLOTS = 2


def _pid(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _safe_float(v: Any, default: float = 0.0) -> float:
    """Convert v to float, returning default on None / NaN / inf / error."""
    import math
    try:
        f = float(v)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return default


def _empty_ledger() -> Dict[str, Any]:
    return {
        "impressions": {},  # product_id -> {"shown": int, "clicked": int}
        "last_session_product_ids": [],
        "last_directives": {},
    }


def _get_product_from_catalog(products_df, product_id: str) -> Optional[Dict[str, Any]]:
    if products_df is None or not product_id:
        return None
    try:
        row = products_df[products_df["product_id"].astype(str) == str(product_id)]
        if len(row) == 0:
            return None
        r = row.iloc[0].to_dict()  # convert Series → plain dict (avoids numpy scalar leakage)
        sub = r.get("subcategory")
        sub_s = "" if sub is None or str(sub).strip().lower() == "nan" else str(sub).strip()
        return {
            "product_id": _pid(r.get("product_id")),
            "product_name": str(r.get("product_name") or "Banking product"),
            "category": str(r.get("category") or r.get("subcategory") or "Banking"),
            "subcategory": sub_s,
            "annual_fee": _safe_float(r.get("annual_fee"), 0.0),
            "min_balance": _safe_float(r.get("min_balance"), 0.0),
            "interest_rate_apy": _safe_float(
                r.get("interest_rate_apy") or r.get("interest_rate"), 0.0
            ),
            "score": 0.55,
            "reasoning": "From your saved goals or application activity.",
        }
    except Exception as e:
        logger.warning("catalog lookup %s: %s", product_id, e)
        return None


def _merge_b_lists(all_recs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Single deduped list from tailored, similar, segment; keep best score per product_id."""
    seen: Dict[str, Dict[str, Any]] = {}
    for key in ("tailored_recommendations", "similar_products", "segment_recommendations"):
        for rec in all_recs.get(key) or []:
            pid = _pid(rec.get("product_id"))
            if not pid:
                continue
            s = float(rec.get("score") or 0)
            if pid not in seen or s > float(seen[pid].get("score") or 0):
                c = dict(rec)
                c["d_source"] = key.replace("_recommendations", "").replace("products", "similar")
                seen[pid] = c
    return sorted(seen.values(), key=lambda x: float(x.get("score") or 0), reverse=True)


class AgentD_Banking:
    """
    Banking behavioral supervisor: wishlist → abandoned app → Agent C → Agent B → fill,
    with category caps and impression-aware steering for the next Agent B run.
    """

    def __init__(self, deprioritize_min_shows: int = DEPRIORITIZE_MIN_SHOWS):
        self.deprioritize_min_shows = deprioritize_min_shows

    def _deprioritize_set(self, ledger: Dict[str, Any]) -> Set[str]:
        out: Set[str] = set()
        for pid, meta in (ledger.get("impressions") or {}).items():
            shown = int(meta.get("shown") or 0)
            clicked = int(meta.get("clicked") or 0)
            if shown >= self.deprioritize_min_shows and clicked == 0:
                out.add(_pid(pid))
        return out

    def _apply_ledger_updates(
        self,
        ledger: Dict[str, Any],
        live_product_ids: List[str],
        clicked_product_ids: List[str],
    ) -> None:
        imp = ledger.setdefault("impressions", {})
        for pid in live_product_ids:
            p = _pid(pid)
            if not p:
                continue
            entry = imp.setdefault(p, {"shown": 0, "clicked": 0})
            entry["shown"] = int(entry.get("shown") or 0) + 1
        for pid in clicked_product_ids:
            p = _pid(pid)
            if not p:
                continue
            entry = imp.setdefault(p, {"shown": 0, "clicked": 0})
            entry["clicked"] = int(entry.get("clicked") or 0) + 1
        ledger["last_session_product_ids"] = [_pid(x) for x in live_product_ids if _pid(x)]

    def orchestrate(
        self,
        customer_id: str,
        ledger: Dict[str, Any],
        saved_goals: List[str],
        incomplete_applications: List[str],
        clicked_product_ids: List[str],
        products_df: Any,
        all_recs: Dict[str, Any],
        agent_c_result: Dict[str, Any],
        persona_name: str = "",
    ) -> Dict[str, Any]:
        """
        Build live stack, update ledger (impressions + clicks), emit next_visit_directives and narrative.

        Args:
            persona_name: Display label for segment (e.g. from Agent A).
        """
        if not isinstance(ledger, dict):
            ledger = _empty_ledger()
        ledger.setdefault("impressions", {})

        deprioritize = self._deprioritize_set(ledger)
        b_ranked = _merge_b_lists(all_recs or {})
        b_by_id = {_pid(r.get("product_id")): r for r in b_ranked}

        def enrich(pid: str, slot_reason: str) -> Optional[Dict[str, Any]]:
            pid = _pid(pid)
            if not pid:
                return None
            if pid in b_by_id:
                r = deepcopy(b_by_id[pid])
                r["supervisor_slot"] = slot_reason
                return r
            cat = _get_product_from_catalog(products_df, pid)
            if cat:
                cat = deepcopy(cat)
                cat["supervisor_slot"] = slot_reason
                return cat
            return {
                "product_id": pid,
                "product_name": f"Product {pid}",
                "category": "Banking",
                "score": 0.5,
                "supervisor_slot": slot_reason,
            }

        live: List[Dict[str, Any]] = []
        used: Set[str] = set()
        cat_count: Dict[str, int] = {}

        def category_of(rec: Dict[str, Any]) -> str:
            return str(rec.get("category") or "General").split("/")[0][:40]

        def can_add(rec: Dict[str, Any]) -> bool:
            pid = _pid(rec.get("product_id"))
            if pid in used:
                return False
            cat = category_of(rec)
            if cat_count.get(cat, 0) >= MAX_PER_CATEGORY:
                return False
            return True

        def push(rec: Dict[str, Any], force: bool = False) -> bool:
            if len(live) >= MAX_LIVE_STACK:
                return False
            if not force and not can_add(rec):
                return False
            pid = _pid(rec.get("product_id"))
            used.add(pid)
            cat_count[category_of(rec)] = cat_count.get(category_of(rec), 0) + 1
            live.append(rec)
            return True

        # 1) Incomplete applications (highest priority)
        for pid in incomplete_applications[:MAX_ABANDONED_SLOTS + 2]:
            r = enrich(pid, "incomplete_application")
            if r and _pid(r.get("product_id")) not in used:
                push(r, force=True)

        # 2) Saved goals / watchlist
        for pid in saved_goals[:MAX_SAVED_SLOTS + 2]:
            r = enrich(pid, "saved_goal")
            if r and _pid(r.get("product_id")) not in used:
                push(r, force=True)

        # 3) Agent C primary offer
        offer = (agent_c_result or {}).get("offer")
        # Extract offer card details from offer_intelligence
        _offer_intel = (agent_c_result or {}).get("offer_intelligence") or {}
        _sel_offer = _offer_intel.get("selected_offer") or {}
        if offer and offer.get("product_id"):
            pid = _pid(offer["product_id"])
            if pid not in used:
                crec = {
                    "product_id": pid,
                    "product_name": offer.get("product_name"),
                    "category": offer.get("category") or "Banking",
                    "score": float(offer.get("score") or 0.9),
                    "reasoning": offer.get("reasoning") or (agent_c_result or {}).get("reason"),
                    "annual_fee": offer.get("annual_fee"),
                    "min_balance": offer.get("min_balance"),
                    "interest_rate_apy": offer.get("interest_rate_apy"),
                    "supervisor_slot": "agent_c_primary",
                }
                push(crec, force=True)

        # 4) Agent B picks (skip heavy deprioritize unless we need fill)
        for rec in b_ranked:
            pid = _pid(rec.get("product_id"))
            if pid in used:
                continue
            if pid in deprioritize:
                continue
            r = deepcopy(rec)
            r["supervisor_slot"] = "agent_b"
            if push(r):
                pass

        # 5) Deprioritized B items as low-priority fill
        for rec in b_ranked:
            pid = _pid(rec.get("product_id"))
            if pid in used:
                continue
            if pid not in deprioritize:
                continue
            r = deepcopy(rec)
            r["supervisor_slot"] = "agent_b_deprioritized"
            r["supervisor_note"] = "Shown often with no engagement; surfaced lower."
            if push(r):
                pass

        # 6) Similar category fill from B tail
        for rec in b_ranked:
            if len(live) >= MAX_LIVE_STACK:
                break
            pid = _pid(rec.get("product_id"))
            if pid in used:
                continue
            r = deepcopy(rec)
            r["supervisor_slot"] = "agent_b_fill"
            push(r)

        live_pids = [_pid(r.get("product_id")) for r in live if _pid(r.get("product_id"))]
        self._apply_ledger_updates(ledger, live_pids, clicked_product_ids)

        # Next visit: recompute deprioritize after this session's impressions
        deprioritize_next = self._deprioritize_set(ledger)
        boost_ids = list(
            dict.fromkeys(
                [_pid(x) for x in incomplete_applications]
                + [_pid(x) for x in saved_goals]
                + [_pid(x) for x in clicked_product_ids]
            )
        )
        boost_ids = [x for x in boost_ids if x]

        focus_source = None
        priority_pin = None
        # Clicked recommendation wins #1 for Agent B (most recent click last in list)
        if clicked_product_ids:
            priority_pin = _pid(clicked_product_ids[-1])
            focus_source = "clicked_recommendation"
        elif incomplete_applications:
            priority_pin = _pid(incomplete_applications[0])
            focus_source = "incomplete_application"
        elif saved_goals:
            priority_pin = _pid(saved_goals[0])
            focus_source = "saved_goal"
        elif offer and offer.get("product_id"):
            priority_pin = _pid(offer["product_id"])
            focus_source = "agent_c_primary"
        elif b_ranked:
            priority_pin = _pid(b_ranked[0].get("product_id"))
            focus_source = "agent_b_top_fallback"

        deprioritize_list = sorted(deprioritize_next)

        offer_reason = ""
        if offer:
            offer_reason = str(offer.get("reasoning") or offer.get("reason") or "").strip()

        # Build offer card snapshot to surface in Recommender when the pinned product is shown.
        # Requires only a product_id — offer experiment fields are optional so the card still
        # renders even when no named offer experiment is active for this customer.
        _pinned_offer_card = None
        if offer and offer.get("product_id"):
            _pinned_offer_card = {
                "product_id": _pid(offer["product_id"]),
                "product_name": offer.get("product_name") or "",
                "offer_name": _sel_offer.get("offer_name") or offer.get("offer_name") or "",
                "offer_type": _sel_offer.get("offer_type") or offer.get("offer_type") or "",
                "headline_value": _sel_offer.get("headline_value") or offer.get("headline_value") or "",
                "content_benefit_1": _sel_offer.get("content_benefit_1") or "",
                "content_benefit_2": _sel_offer.get("content_benefit_2") or "",
                "content_benefit_3": _sel_offer.get("content_benefit_3") or "",
                "days_remaining": _sel_offer.get("days_remaining"),
                "terms_summary": _sel_offer.get("terms_summary") or offer.get("terms_summary") or "",
            }

        directives = {
            "boost_product_ids": boost_ids,
            "deprioritize_product_ids": deprioritize_list,
            "priority_pin_product_id": priority_pin,
            "focus_source": focus_source,
            "focus_offer_reasoning": offer_reason[:500] if offer_reason else "",
            "supervisor_story_hint": self._story_hint(
                incomplete_applications, saved_goals, clicked_product_ids, offer
            ),
            "pinned_offer_card": _pinned_offer_card,
        }
        ledger["last_directives"] = directives

        narrative = self._build_narrative(
            customer_id=customer_id,
            live=live,
            agent_c=agent_c_result,
            incomplete_applications=incomplete_applications,
            saved_goals=saved_goals,
            clicked_product_ids=clicked_product_ids,
            directives=directives,
        )

        def _card(r: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "product_id": _pid(r.get("product_id")),
                "product_name": r.get("product_name") or r.get("product_id"),
                "category": r.get("category") or "Banking",
                "score": round(float(r.get("score") or 0), 4),
            }

        agent_b_top_three = [_card(r) for r in b_ranked[:3]]

        def _signal_products(ids: List[str]) -> List[Dict[str, str]]:
            out = []
            for pid in ids[:5]:
                p = _pid(pid)
                if not p:
                    continue
                r = b_by_id.get(p) or _get_product_from_catalog(products_df, p)
                name = (r.get("product_name") if r else None) or p
                out.append({"product_id": p, "product_name": str(name)})
            return out

        focus_product = None
        if priority_pin:
            fr = enrich(priority_pin, "focus")
            if fr:
                focus_product = {
                    "product_id": _pid(fr.get("product_id")),
                    "product_name": fr.get("product_name"),
                    "category": fr.get("category"),
                    "focus_source": focus_source,
                }
            if focus_source == "agent_c_primary" and offer:
                focus_product = {
                    "product_id": _pid(offer.get("product_id")),
                    "product_name": offer.get("product_name"),
                    "category": offer.get("category"),
                    "focus_source": focus_source,
                    "reasoning": offer.get("reasoning"),
                }

        sup_text, sup_detail = self._supervisor_banking_copy(
            focus_source, focus_product, offer, persona_name or "this segment"
        )

        return {
            "customer_id": customer_id,
            "persona_name": (persona_name or "").strip() or "Unknown segment",
            "live_recommendations": live,
            "agent_c_snapshot": {
                "primary_product_id": _pid((offer or {}).get("product_id")),
                "primary_product_name": (offer or {}).get("product_name"),
            },
            "supervisor_view": {
                "agent_b_product_recommendations": agent_b_top_three,
                "agent_b_note": (
                    "Agent B ranks banking products by persona fit, eligibility, and 12-factor match — "
                    "not by campaign or offer strategy."
                ),
                # Fall back to top Agent B product if Agent C didn't select an offer
                # (common for persona mode when the auto-selected customer has no eligible products)
                "agent_c_primary_offer": (
                    lambda _src, _from_c: {
                        "product_id": _pid(_src.get("product_id")),
                        "product_name": _src.get("product_name"),
                        "category": _src.get("category"),
                        "reasoning": (_src.get("reasoning") or (
                            "Top-ranked product for this segment by 12-factor scoring."
                            if not _from_c else ""
                        ))[:300],
                        "status": "Offer ready" if _from_c else "Segment recommendation",
                        "offer_name": _sel_offer.get("offer_name") or "",
                        "offer_type": _sel_offer.get("offer_type") or "",
                        "headline_value": _sel_offer.get("headline_value") or "",
                        "content_benefit_1": _sel_offer.get("content_benefit_1") or "",
                        "content_benefit_2": _sel_offer.get("content_benefit_2") or "",
                        "content_benefit_3": _sel_offer.get("content_benefit_3") or "",
                        "days_remaining": _sel_offer.get("days_remaining"),
                        "terms_summary": _sel_offer.get("terms_summary") or "",
                    } if _src else None
                )(
                    offer if (offer and offer.get("product_id")) else (b_ranked[0] if b_ranked else None),
                    bool(offer and offer.get("product_id")),
                ),
                "agent_c_note": (
                    "Agent C picks the one best commercial offer (retention, strategy, eligibility) — "
                    "often different from B’s #1 ranked product."
                ),
                "digital_journey_signals": {
                    "has_incomplete_application": len(incomplete_applications) > 0,
                    "incomplete_applications": _signal_products(incomplete_applications),
                    "saved_goals_watchlist": _signal_products(saved_goals),
                    "digital_engagement": _signal_products(clicked_product_ids),
                },
                "focus_product": focus_product,
                "supervisor_headline": sup_text,
                "supervisor_detail": sup_detail,
                "why_b_and_c_differ": (
                    "**Why the lists differ:** Agent B optimizes for **relationship fit** (segment, credit, "
                    "deposits, product history). Agent C optimizes for **business outcome** (one best offer). "
                    "**Agent D** decides what Agent B should **lead with next** — an **incomplete application** "
                    "beats everything; otherwise align with **Agent C’s primary** so mobile, branch, and email "
                    "stay consistent."
                ),
                "next_step_hint": (
                    "Open **Agent B** → Customer mode → same customer → enable **Apply Agent D supervisor directives** "
                    "→ Run recommendations. The **focus product** is pinned #1."
                ),
            },
            "supervisor_narrative": narrative,
            "next_visit_directives": directives,
            "impressions_recorded": live_pids,
            "meta": {
                "max_per_category": MAX_PER_CATEGORY,
                "deprioritize_threshold_shows": self.deprioritize_min_shows,
            },
        }

    def _supervisor_banking_copy(
        self,
        focus_source: Optional[str],
        focus_product: Optional[Dict],
        offer: Any,
        persona_label: str,
    ) -> Tuple[str, str]:
        """Headline + paragraph for supervisor instruction card. Tries Claude first, falls back to templates."""
        fn = (focus_product or {}).get("product_name") or "selected product"
        churn_category = (offer or {}).get("churn_category") if isinstance(offer, dict) else ""

        # Try Claude LLM for dynamic supervisor copy
        if CLAUDE_AVAILABLE and get_claude_client:
            try:
                claude = get_claude_client()
                if claude.is_available():
                    llm_result = claude.generate_supervisor_copy(
                        focus_source=focus_source or "standard",
                        product_name=fn,
                        persona_label=persona_label,
                        churn_category=churn_category or "",
                    )
                    if llm_result.get("headline") and llm_result.get("detail"):
                        return llm_result["headline"], llm_result["detail"]
            except Exception as e:
                logger.warning(f"Claude supervisor copy failed, using template: {e}")

        # Template fallback
        if focus_source == "incomplete_application":
            return (
                f"Recovery priority: incomplete application — {fn}",
                (
                    f"**Supervisor (Agent D) -> Agent B:** On the **next session or outbound campaign**, lead with "
                    f"**{fn}**. The customer started but did not finish this application — recovery takes priority "
                    f"over generic **{persona_label}** product rankings. Pin this product **#1** and pair with "
                    f"branch or digital completion messaging."
                ),
            )
        if focus_source == "saved_goal":
            return (
                f"Reinforce saved goal: {fn}",
                (
                    f"**Supervisor -> Agent B:** The customer saved **{fn}** (watchlist / goal). On the next visit, "
                    f"surface it **first** to respect stated intent while keeping eligibility checks in Agent B."
                ),
            )
        if focus_source == "digital_engagement":
            return (
                f"Double down on engagement: {fn}",
                (
                    f"**Supervisor -> Agent B:** The customer recently engaged with **{fn}**. Boost and pin it **#1** "
                    f"next time instead of repeating ignored recommendations."
                ),
            )
        if focus_source == "agent_c_primary" and offer:
            return (
                f"Align with offer engine: {fn}",
                (
                    f"No **incomplete application** on file for this session. **Supervisor instructs Agent B:** on the "
                    f"**next visit or campaign**, lead with **{fn}** (Agent C primary) so recommendations match the "
                    f"**commercial offer** — consistent across app, branch, and email."
                ),
            )
        if focus_source == "agent_b_top_fallback":
            return (
                f"Lead with segment fit: {fn}",
                (
                    f"No Agent C primary offer and no recovery signals. **Supervisor -> Agent B:** pin **{fn}** (#1 "
                    f"segment-ranked product) until offer engine or journey signals update."
                ),
            )
        return (
            "Supervisor routing",
            "**Supervisor -> Agent B:** Use standard persona rankings; add engagement signals when available.",
        )

    def _story_hint(
        self,
        abandoned: List[str],
        saved: List[str],
        clicked: List[str],
        offer: Any,
    ) -> str:
        parts = []
        if abandoned:
            parts.append(f"Recovery focus on incomplete application(s): {', '.join(map(_pid, abandoned[:3]))}.")
        if saved:
            parts.append(f"Reinforce saved goals: {', '.join(map(_pid, saved[:3]))}.")
        if clicked:
            parts.append(f"Customer engaged with: {', '.join(map(_pid, clicked[:5]))}.")
        if offer and offer.get("product_name"):
            parts.append(f"Commercial anchor: {offer.get('product_name')}.")
        return " ".join(parts) if parts else "Standard persona-aligned sequencing for next Agent B run."

    def _build_narrative(
        self,
        customer_id: str,
        live: List[Dict[str, Any]],
        agent_c: Dict[str, Any],
        incomplete_applications: List[str],
        saved_goals: List[str],
        clicked_product_ids: List[str],
        directives: Dict[str, Any],
    ) -> str:
        lines = [
            f"**Supervisor summary (Customer {customer_id})**",
            "",
            "**This session stack** — ordered by behavioral priority, then Agent C, then Agent B (ignored SKUs demoted):",
        ]
        for i, rec in enumerate(live[:10], 1):
            slot = rec.get("supervisor_slot", "")
            name = rec.get("product_name") or rec.get("product_id")
            lines.append(f"{i}. [{slot}] {name} (`{rec.get('product_id')}`)")
        if len(live) > 10:
            lines.append(f"… and {len(live) - 10} more.")

        lines.append("")
        lines.append("**Signals used**")
        if incomplete_applications:
            lines.append(f"- Incomplete applications (abandoned funnel): {', '.join(map(_pid, incomplete_applications))}")
        else:
            lines.append("- No incomplete-application products flagged this session.")
        if saved_goals:
            lines.append(f"- Saved goals / watchlist: {', '.join(map(_pid, saved_goals))}")
        else:
            lines.append("- No saved-goal products flagged.")
        if clicked_product_ids:
            lines.append(f"- Engaged (clicked) this session: {', '.join(map(_pid, clicked_product_ids))}")
        else:
            lines.append("- No click engagement reported this session.")

        oc = (agent_c or {}).get("offer")
        if oc:
            lines.append(f"- Agent C primary offer: **{oc.get('product_name')}** — {(agent_c or {}).get('reason', '')[:120]}")

        lines.append("")
        lines.append("**Next visit → Agent B**")
        d = directives
        if d.get("priority_pin_product_id"):
            src = d.get("focus_source") or ""
            if src == "clicked_recommendation":
                lines.append(
                    f"- **Pin #1 next Agent B run:** `{d['priority_pin_product_id']}` (customer clicked this recommendation)."
                )
            else:
                lines.append(
                    f"- **Pin #1 next run:** product `{d['priority_pin_product_id']}` "
                    f"(journey / offer story)."
                )
        if d.get("boost_product_ids"):
            lines.append(f"- **Boost scores:** {', '.join(d['boost_product_ids'][:8])}")
        if d.get("deprioritize_product_ids"):
            lines.append(
                f"- **Deprioritize (shown ≥{self.deprioritize_min_shows}×, never clicked):** "
                f"{', '.join(d['deprioritize_product_ids'][:8])}"
            )
        else:
            lines.append("- No SKUs in deprioritize band yet.")

        return "\n".join(lines)

    @staticmethod
    def _clip_txt(s: str, max_len: int) -> str:
        t = (s or "").strip()
        if len(t) <= max_len:
            return t
        return t[: max_len - 1].rstrip() + "…"

    @staticmethod
    def _money_rough(v: Any) -> Optional[str]:
        try:
            x = float(v)
            if x <= 0:
                return None
            if x >= 1_000_000:
                return f"${x/1_000_000:.1f}M"
            if x >= 1_000:
                return f"${x:,.0f}"
            return f"${x:.0f}"
        except (TypeError, ValueError):
            return None

    @staticmethod
    def build_supervisor_pin_story(
        directives: Optional[Dict[str, Any]],
        product_label: str,
        pinned_rec: Optional[Dict[str, Any]] = None,
        catalog_row: Optional[Dict[str, Any]] = None,
        customer_context: Optional[Dict[str, Any]] = None,
        persona_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Customer-centric supervisor narrative + structured UI payload (not agent-internals jargon).
        """
        label = (product_label or "").strip() or "this product"
        d = directives or {}
        src = (d.get("focus_source") or "").strip()
        offer_snip = AgentD_Banking._clip_txt(str(d.get("focus_offer_reasoning") or ""), 320)

        cx = customer_context or {}
        persona_disp = (
            (persona_name or "").strip()
            or str(cx.get("persona") or "").strip()
            or "this customer’s segment"
        )
        deposits_s = AgentD_Banking._money_rough(cx.get("total_deposits"))
        income_s = AgentD_Banking._money_rough(cx.get("income"))
        credit = cx.get("credit_score")
        n_prod = cx.get("num_products")
        txn_n = cx.get("transaction_count")
        tenure = cx.get("tenure_months")

        pr = pinned_rec or {}
        cr = catalog_row or {}
        sub = str(pr.get("subcategory") or cr.get("subcategory") or "").strip() or "Banking"
        apy_raw = pr.get("interest_rate_apy", pr.get("interest_rate", cr.get("interest_rate_apy", cr.get("interest_rate", 0))))
        try:
            apy_f = float(apy_raw) if apy_raw is not None and str(apy_raw).strip() != "" else 0.0
        except (TypeError, ValueError):
            apy_f = 0.0
        score = _safe_float(pr.get("score"), 0.0)
        compat = pr.get("compatibility")
        if compat is None:
            compat = round(score * 100, 1)
        else:
            compat = _safe_float(compat, round(score * 100, 1))

        baseline_pct: Optional[float] = None
        pre_raw = pr.get("_pre_supervisor_score")
        if pre_raw is not None:
            try:
                baseline_pct = round(float(pre_raw) * 100, 1)
            except (TypeError, ValueError):
                baseline_pct = None
        dc = pr.get("detailed_calculation") or {}
        if baseline_pct is None and isinstance(dc, dict):
            ts = dc.get("total_score")
            if ts is not None:
                try:
                    baseline_pct = round(float(ts) * 100, 1)
                except (TypeError, ValueError):
                    pass
        need_x = (dc.get("financial_need_match") or {}).get("explanation") if isinstance(dc.get("financial_need_match"), dict) else ""
        elig_x = (dc.get("eligibility_score") or {}).get("explanation") if isinstance(dc.get("eligibility_score"), dict) else ""
        fit_bits: List[str] = []
        if elig_x:
            fit_bits.append(AgentD_Banking._clip_txt(str(elig_x), 200))
        if need_x:
            fit_bits.append(AgentD_Banking._clip_txt(str(need_x), 200))

        profile_bits: List[str] = []
        if deposits_s:
            profile_bits.append(f"deposit relationship near {deposits_s}")
        if income_s:
            profile_bits.append(f"stated income around {income_s}")
        if credit is not None and str(credit).strip() != "":
            try:
                profile_bits.append(f"credit score near {int(float(credit))}")
            except (TypeError, ValueError):
                profile_bits.append("credit profile on file")
        if n_prod is not None and str(n_prod).strip() != "":
            profile_bits.append(f"{int(float(n_prod))} banked products today")
        if txn_n is not None:
            profile_bits.append(f"{int(txn_n)} recorded transactions in the feed")
        if tenure is not None and str(tenure).strip() != "":
            try:
                profile_bits.append(f"~{int(float(tenure))} months with the bank")
            except (TypeError, ValueError):
                pass
        profile_clause = ", ".join(profile_bits[:4]) if profile_bits else "the balances, products, and digital signals we already hold"

        bullets: List[str] = []
        sub_l = sub.lower()
        if "loan" in sub_l or "mortgage" in label.lower() or "mortgage" in sub_l:
            if apy_f > 0:
                bullets.append(f"Competitive pricing context at {apy_f:.2f}% for this category")
            bullets.append("Structured payments that fit long-term housing or refinance goals")
        elif sub == "Checking":
            bullets.append("Everyday liquidity and cash-flow management")
            if apy_f > 0:
                bullets.append(f"Earns {apy_f:.2f}% on balances where applicable")
        elif sub == "Savings":
            bullets.append("Builds reserves with clearer yield visibility")
        elif sub == "Credit":
            bullets.append("Revolving capacity for planned or unexpected spend")
        else:
            bullets.append(f"{label} matches how {persona_disp} customers typically expand the relationship")

        highlights: List[Dict[str, str]] = []
        # After supervisor boost, displayed score can hit 100% — show pre-adjustment fit only (honest chip).
        if baseline_pct is not None and baseline_pct > 0:
            highlights.append(
                {"label": "Baseline model fit", "value": f"{min(baseline_pct, 99.9):.1f}%"},
            )
        if apy_f > 0:
            highlights.append({"label": "Featured rate", "value": f"{apy_f:.2f}%"})
        if deposits_s:
            highlights.append({"label": "Deposits", "value": deposits_s})

        if src == "clicked_recommendation":
            headline = f"We’re leading with {label} because they engaged with it"
            p1 = (
                f"They recently clicked or opened {label} in the recommendation journey — that is the strongest "
                f"real-time intent signal in the data we have for this session."
            )
            p2 = (
                f"For someone in the **{persona_disp}** profile, acting on that signal avoids pitching a different "
                f"product they did not choose and keeps the conversation credible."
            )
            p3 = (
                f"Against their profile ({profile_clause}), {label} remains eligible and on-strategy — "
                f"the pin simply aligns the ranked list with what they already showed interest in."
            )
            if fit_bits:
                p4 = f"Model detail: {' '.join(fit_bits[:2])}"
            else:
                p4 = (
                    f"Use the factor breakdown below to show how fees, minimums, and need-match still support {label} "
                    f"even if it was not the highest raw score before the pin."
                )
            retention = (
                "Retention: honoring a self-selected product reduces friction, protects trust, and gives bankers a "
                "clear story for follow-up instead of resetting to a generic top pick."
            )
        elif src == "incomplete_application":
            headline = f"Finish-line priority: {label}"
            p1 = f"They started {label} but did not complete it — recovery beats cold cross-sell for conversion and experience."
            p2 = f"As **{persona_disp}**, nudging completion (docs, rate lock, or next step) is often the fastest win."
            p3 = f"Given {profile_clause}, leading with this SKU signals you remember where they left off."
            p4 = fit_bits[0] if fit_bits else f"{label} still fits standard eligibility checks for their tier."
            retention = "Retention: abandoned applications are a leading churn signal; closing the loop materially improves win-back odds."
        elif src == "saved_goal":
            headline = f"They marked {label} as a goal"
            p1 = f"{label} is on their saved goals or watchlist — stated intent without a fresh click still deserves airtime."
            p2 = f"For **{persona_disp}**, surfacing the goal first respects what they told the bank they care about."
            p3 = f"With {profile_clause}, this is a disciplined way to deepen share-of-wallet without guessing."
            p4 = fit_bits[0] if fit_bits else f"Twelve-factor scoring still shows how {label} fits their needs — see below."
            retention = "Retention: acknowledging saved goals reinforces that the bank listens, which lifts engagement on the next visit or outbound."
        elif src == "agent_c_primary":
            headline = f"Strategic lead offer: {label}"
            if offer_snip:
                p1 = f"For **{persona_disp}**, the bank’s primary offer story is: {offer_snip}"
            else:
                p1 = (
                    f"For **{persona_disp}**, {label} is the single coordinated offer the bank wants to lead with — "
                    f"balancing growth, risk, and eligibility for this customer."
                )
            p2 = (
                f"Using their live profile ({profile_clause}), this product is positioned to deepen the relationship "
                f"without stretching past what the data supports."
            )
            p3 = (
                f"Showing {label} first keeps mobile, branch, and outbound messaging aligned so the customer is not "
                f"told one story in the app and another at the desk."
            )
            p4 = fit_bits[0] if fit_bits else (
                f"{label} as a **{sub}** product maps to how similar customers expand — use the rate and benefits "
                f"below to personalize the conversation."
            )
            retention = (
                "Retention: a consistent ‘hero’ offer reduces confusion, supports pricing discipline, and makes it "
                "easier to defend why this product—not another—deserves the first conversation."
            )
        elif src == "agent_b_top_fallback":
            headline = f"Segment-fit lead: {label}"
            p1 = f"No stronger journey signal fired, so {label} — the best raw segment match — is the supervisory default."
            p2 = f"For **{persona_disp}**, that means leading with the strongest model score while we wait for clicks, goals, or offers."
            p3 = f"Profile context: {profile_clause}."
            p4 = fit_bits[0] if fit_bits else f"Expand with the 12-factor narrative below to explain why the score landed where it did."
            retention = "Retention: even a score-led pin gives a coherent opening; pair it with discovery questions so the next-best products still feel relevant."
        else:
            headline = f"Supervisor priority: {label}"
            p1 = f"The bank marked {label} as the #1 focus for this run for **{persona_disp}**."
            p2 = f"Customer context: {profile_clause}."
            p3 = f"Use product economics (rate, fees, minimums) in the card to explain tangible value."
            p4 = fit_bits[0] if fit_bits else "See the scored factors below for evidence-backed talking points."
            retention = "Retention: a deliberate lead product reduces random cross-sell and helps teams prepare one strong narrative."

        paragraphs = [p1, p2, p3, p4]

        return {
            "headline": headline,
            "subhead": f"Personalized for {persona_disp} using customer + product data on file.",
            "paragraphs": paragraphs,
            "bullets": bullets[:4],
            "highlights": highlights[:4],
            "retention": retention,
            "focus_source": src or "supervisor",
        }

    @staticmethod
    def enrich_pin_story_with_llm(
        story: Dict[str, Any],
        product_label: str,
        customer_context: Optional[Dict[str, Any]],
        persona_name: Optional[str],
        directives: Optional[Dict[str, Any]],
    ) -> None:
        """
        Optional Together AI pass: clearer RM-facing copy. Uses TOGETHER_API_KEY from env.
        Set BANKING_PIN_STORY_LLM=0 to skip (faster / offline).
        """
        if os.getenv("BANKING_PIN_STORY_LLM", "1").strip().lower() in ("0", "false", "no", "off"):
            return
        try:
            from utils.together_ai import together_ai

            key = getattr(together_ai, "api_key", None) or ""
            if len(str(key).strip()) < 8:
                return
        except Exception:
            return

        cx = customer_context or {}
        facts = {
            "persona": persona_name or cx.get("persona"),
            "customer_name": cx.get("customer_name"),
            "deposits": cx.get("total_deposits"),
            "income": cx.get("income"),
            "credit_score": cx.get("credit_score"),
            "num_products": cx.get("num_products"),
            "tenure_months": cx.get("tenure_months"),
            "transaction_count": cx.get("transaction_count"),
            "focus_source": (directives or {}).get("focus_source"),
            "offer_note": AgentD_Banking._clip_txt(str((directives or {}).get("focus_offer_reasoning") or ""), 450),
            "product": product_label,
            "draft_paragraphs": story.get("paragraphs") or [],
            "retention_hint": story.get("retention"),
            "product_bullets": story.get("bullets") or [],
        }
        payload = json.dumps(facts, default=str)[:8000]

        prompt = f"""You are a senior retail-banking coach. Rewrite the storyline into EXACTLY four short paragraphs for a relationship manager.

Rules:
- Use ONLY facts in CUSTOMER_FACTS_JSON. Do not invent dollar amounts, credit scores, or rates not present there.
- No internal jargon: do not say "Agent C", "Agent D", "12-factor", "orchestrate", or "supervisor engine".
- Paragraph 1: why this product fits THIS customer’s situation (money, relationship, segment).
- Paragraph 2: concrete product value using facts (rate/APY/type if present in bullets or offer_note).
- Paragraph 3: consistency across channels / trust.
- Paragraph 4: retention — why opening with this product helps keep or grow the relationship.

CUSTOMER_FACTS_JSON:
{payload}

Output exactly four lines, each starting with P1:, P2:, P3:, P4:
P1: ...
P2: ...
P3: ...
P4: ...
"""

        try:
            raw = together_ai.generate_text(
                prompt,
                system_message="You write concise banker-facing coaching copy. Follow the P1–P4 format exactly.",
                max_tokens=560,
                temperature=0.35,
                agent_name="agent_d",
                call_type="pin_story",
            )
        except Exception as e:
            logger.debug("pin story LLM skipped: %s", e)
            return

        if not raw or str(raw).strip().startswith("Error"):
            return

        paras: List[str] = []
        for line in str(raw).splitlines():
            s = line.strip()
            if len(paras) >= 4:
                break
            up = s[:3].upper()
            if up == "P1:":
                paras.append(s[3:].strip())
            elif up == "P2:":
                paras.append(s[3:].strip())
            elif up == "P3:":
                paras.append(s[3:].strip())
            elif up == "P4:":
                paras.append(s[3:].strip())
        if len(paras) >= 3:
            story["paragraphs"] = paras[:4]
            story["llm_polished"] = True

    @staticmethod
    def priority_pin_reason_text(
        directives: Optional[Dict[str, Any]],
        products_df: Any = None,
    ) -> str:
        """Plain-text pin summary for directives API (no customer row)."""
        pin = _pid((directives or {}).get("priority_pin_product_id") or "")
        if not pin:
            return ""
        cat0 = _get_product_from_catalog(products_df, pin)
        plab = (cat0.get("product_name") if cat0 else None) or pin
        story = AgentD_Banking.build_supervisor_pin_story(
            directives, str(plab), None, cat0, None, None
        )
        return "\n\n".join(story.get("paragraphs") or [])

    @staticmethod
    def apply_directives_to_recommendations(
        recommendations: List[Dict[str, Any]],
        directives: Optional[Dict[str, Any]],
        products_df: Any = None,
        customer_context: Optional[Dict[str, Any]] = None,
        persona_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Re-rank Agent B list using supervisor directives (for Agent B execute)."""
        if not directives or not recommendations:
            return recommendations
        boost = set(map(_pid, directives.get("boost_product_ids") or []))
        dep = set(map(_pid, directives.get("deprioritize_product_ids") or []))
        pin = _pid(directives.get("priority_pin_product_id") or "")
        cat_for_pin = _get_product_from_catalog(products_df, pin) if pin else None
        plab = (cat_for_pin.get("product_name") if cat_for_pin else None) or pin

        out = []
        for r in recommendations:
            c = deepcopy(r)
            try:
                c["_pre_supervisor_score"] = float(r.get("score") or 0)
            except (TypeError, ValueError):
                c["_pre_supervisor_score"] = 0.0
            pid = _pid(c.get("product_id"))
            base = float(c.get("score") or 0.5)
            if pid in boost:
                base = min(1.0, base + 0.12)
            if pid in dep:
                base = max(0.05, base * 0.55)
            c["score"] = base
            c["supervisor_adjusted"] = True
            out.append(c)
        out.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
        if pin:
            pinned = [x for x in out if _pid(x.get("product_id")) == pin]
            rest = [x for x in out if _pid(x.get("product_id")) != pin]

            def _attach_pin_fields(target: Dict[str, Any], cat_row: Optional[Dict[str, Any]]) -> None:
                story = AgentD_Banking.build_supervisor_pin_story(
                    directives,
                    str(target.get("product_name") or plab),
                    pinned_rec=target,
                    catalog_row=cat_row or cat_for_pin,
                    customer_context=customer_context,
                    persona_name=persona_name,
                )
                AgentD_Banking.enrich_pin_story_with_llm(
                    story,
                    str(target.get("product_name") or plab),
                    customer_context,
                    persona_name,
                    directives,
                )
                target["priority_pin_story"] = story
                target["priority_pin_reason"] = "\n\n".join(story.get("paragraphs") or [])

            if not pinned:
                # Supervisor-clicked product may not be in B's filtered top-N — still force #1
                cat = _get_product_from_catalog(products_df, pin)

                def _fnum(v: Any, default: float = 0.0) -> float:
                    if v is None or v == "":
                        return default
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return default

                stub_pre = 0.58
                if cat:
                    try:
                        stub_pre = float(cat.get("score") or 0.58)
                    except (TypeError, ValueError):
                        stub_pre = 0.58
                stub = {
                    "product_id": pin,
                    "product_name": (cat.get("product_name") if cat else None) or pin,
                    "category": (cat.get("category") if cat else None) or "Banking",
                    "subcategory": (cat.get("subcategory") if cat else None) or "",
                    "score": 1.0,
                    "compatibility": 100.0,
                    "_pre_supervisor_score": stub_pre,
                    "match_level": "Perfect Match",
                    "in_stock": True,
                    "supervisor_pinned": True,
                    "reasoning": "Pinned #1 by Agent D supervisor directives for this customer.",
                    "recommendation_text": "Pinned by Agent D supervisor for this customer.",
                    "annual_fee": _fnum(cat.get("annual_fee")) if cat else 0.0,
                    "min_balance": _fnum(cat.get("min_balance")) if cat else 0.0,
                    "interest_rate": _fnum(cat.get("interest_rate_apy")) if cat else 0.0,
                    "interest_rate_apy": _fnum(cat.get("interest_rate_apy")) if cat else 0.0,
                    "avg_rating": 4.5,
                    "description": "",
                    "scoring_method": "supervisor_pin",
                }
                _attach_pin_fields(stub, cat)
                out = [stub] + rest
            else:
                for p in pinned:
                    p["supervisor_pinned"] = True
                    _attach_pin_fields(p, cat_for_pin)
                out = pinned + rest
        return out

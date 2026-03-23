"""
Agent D Banking — Behavioral supervisor / session orchestration.
Connects saved goals, incomplete applications, and impression/click history to:
- This visit's prioritized product stack (after Agent B + Agent C signals)
- Impression logging for next-run deprioritization
- next_visit_directives contract for Agent B (boost, deprioritize, priority pin)
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

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
        r = row.iloc[0]
        return {
            "product_id": _pid(r.get("product_id")),
            "product_name": r.get("product_name") or "Banking product",
            "category": r.get("category") or r.get("subcategory") or "Banking",
            "annual_fee": r.get("annual_fee"),
            "min_balance": r.get("min_balance"),
            "interest_rate_apy": r.get("interest_rate_apy") or r.get("interest_rate"),
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

        directives = {
            "boost_product_ids": boost_ids,
            "deprioritize_product_ids": deprioritize_list,
            "priority_pin_product_id": priority_pin,
            "focus_source": focus_source,
            "supervisor_story_hint": self._story_hint(
                incomplete_applications, saved_goals, clicked_product_ids, offer
            ),
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
                "agent_c_primary_offer": (
                    {
                        "product_id": _pid(offer.get("product_id")),
                        "product_name": offer.get("product_name"),
                        "category": offer.get("category"),
                        "reasoning": (offer.get("reasoning") or "")[:240],
                        "status": "Offer ready",
                    }
                    if offer and offer.get("product_id")
                    else None
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
        """Headline + paragraph for supervisor instruction card (banking)."""
        fn = (focus_product or {}).get("product_name") or "selected product"
        if focus_source == "incomplete_application":
            return (
                f"Recovery priority: incomplete application — {fn}",
                (
                    f"**Supervisor (Agent D) → Agent B:** On the **next session or outbound campaign**, lead with "
                    f"**{fn}**. The customer started but did not finish this application — recovery takes priority "
                    f"over generic **{persona_label}** product rankings. Pin this product **#1** and pair with "
                    f"branch or digital completion messaging."
                ),
            )
        if focus_source == "saved_goal":
            return (
                f"Reinforce saved goal: {fn}",
                (
                    f"**Supervisor → Agent B:** The customer saved **{fn}** (watchlist / goal). On the next visit, "
                    f"surface it **first** to respect stated intent while keeping eligibility checks in Agent B."
                ),
            )
        if focus_source == "digital_engagement":
            return (
                f"Double down on engagement: {fn}",
                (
                    f"**Supervisor → Agent B:** The customer recently engaged with **{fn}**. Boost and pin it **#1** "
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
                    f"No Agent C primary offer and no recovery signals. **Supervisor → Agent B:** pin **{fn}** (#1 "
                    f"segment-ranked product) until offer engine or journey signals update."
                ),
            )
        return (
            "Supervisor routing",
            "**Supervisor → Agent B:** Use standard persona rankings; add engagement signals when available.",
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
    def apply_directives_to_recommendations(
        recommendations: List[Dict[str, Any]],
        directives: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Re-rank Agent B list using supervisor directives (for Agent B execute)."""
        if not directives or not recommendations:
            return recommendations
        boost = set(map(_pid, directives.get("boost_product_ids") or []))
        dep = set(map(_pid, directives.get("deprioritize_product_ids") or []))
        pin = _pid(directives.get("priority_pin_product_id") or "")

        out = []
        for r in recommendations:
            c = deepcopy(r)
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
            if not pinned:
                # Supervisor-clicked product may not be in B's filtered top-N — still force #1
                stub = {
                    "product_id": pin,
                    "product_name": pin,
                    "category": "Banking",
                    "subcategory": "",
                    "score": 1.0,
                    "compatibility": 100.0,
                    "match_level": "Perfect Match",
                    "in_stock": True,
                    "supervisor_pinned": True,
                    "reasoning": "Pinned #1 by Agent D (customer clicked this recommendation).",
                    "recommendation_text": "Pinned by Agent D supervisor for this customer.",
                    "annual_fee": 0.0,
                    "min_balance": 0.0,
                    "interest_rate": 0.0,
                    "interest_rate_apy": 0.0,
                    "avg_rating": 4.5,
                    "description": "",
                    "scoring_method": "supervisor_pin",
                }
                out = [stub] + rest
            else:
                for p in pinned:
                    p["supervisor_pinned"] = True
                out = pinned + rest
        return out

"""
Agent C Banking - One Best Offer with Explainability
Hyper-personalized 1:1 offer for each customer with clear reasoning and cross-channel actionability.
CMO-critical: one best offer, how/why AI got there, why our approach is better.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def _load_exclusions(config_path: Optional[Path] = None) -> Dict[str, List[str]]:
    """Load product exclusions: product_id -> list of persona names to exclude for."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "data" / "config" / "product_exclusions.json"
    if not config_path.exists():
        return {}
    try:
        import json
        with open(config_path) as f:
            data = json.load(f)
        return data.get("exclusions", {}) or {}
    except Exception as e:
        logger.warning(f"Could not load exclusions: {e}")
        return {}


class AgentC_Banking:
    """
    Banking Agent C: One Best Offer per customer with explainability and cross-channel payload.
    Uses Agent A (segment/persona) and Agent B (recommendations); picks single best offer;
    applies exclusions; returns reason and why-our-AI narrative.
    """

    def __init__(self, exclusions_config_path: Optional[Path] = None):
        self.exclusions_map = _load_exclusions(exclusions_config_path)

    def get_one_best_offer(
        self,
        customer_id: str,
        customer_details: Dict,
        all_recommendations: Dict,
        churn_risk_score: Optional[float] = None,
        churn_category: Optional[str] = None,
        fallback_products: Optional[List[Dict]] = None,
        agent_b_reference_recs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Select the single best offer for this customer and build explainability.
        If no candidates from recommendations, uses fallback_products when provided.

        agent_b_reference_recs: Raw rows from rule-based Agent B execute (same order as UI #1–#3).
        When set, B vs C comparison uses execute #1 vs Agent C pick — otherwise raw merge rank vs churn-boosted pick.
        """
        persona_name = (customer_details.get("persona") or "Unknown").strip()
        metrics = customer_details.get("metrics") or {}
        digital = float(metrics.get("digital_engagement", 0.5))
        tailored = all_recommendations.get("tailored_recommendations") or []
        similar = all_recommendations.get("similar_products") or []
        segment = all_recommendations.get("segment_recommendations") or []

        # Merge and dedupe by product_id; keep best score per product
        seen = {}
        for rec in tailored:
            pid = rec.get("product_id")
            if pid and pid not in seen:
                rec_copy = dict(rec)
                rec_copy["source"] = "persona_aligned"
                seen[pid] = rec_copy
        for rec in similar:
            pid = rec.get("product_id")
            if pid and (pid not in seen or rec.get("score", 0) > seen[pid].get("score", 0)):
                rec_copy = dict(rec)
                rec_copy["source"] = "similar_products"
                seen[pid] = rec_copy
        for rec in segment:
            pid = rec.get("product_id")
            if not pid:
                continue
            rec_copy = dict(rec)
            rec_copy["source"] = "segment_popular"
            # Segment rows from Enhanced often only have popularity — map so merge can beat execute
            try:
                sc = float(rec_copy.get("score") or 0)
            except (TypeError, ValueError):
                sc = 0.0
            if sc <= 0:
                pop = float(rec_copy.get("popularity") or 0)
                rec_copy["score"] = round(min(0.94, max(0.18, pop * 0.75 + 0.18)), 4)
            if pid not in seen or float(rec_copy.get("score") or 0) > float(seen[pid].get("score") or 0):
                seen[pid] = rec_copy

        # Apply exclusions
        excluded_product_ids = set()
        for product_id, excluded_personas in self.exclusions_map.items():
            if isinstance(excluded_personas, list) and persona_name in excluded_personas:
                excluded_product_ids.add(str(product_id))
        candidates = [r for r in seen.values() if str(r.get("product_id") or "") not in excluded_product_ids]

        # Fallback when no candidates: use first fallback product if provided
        if not candidates and fallback_products:
            for p in fallback_products:
                pid = p.get("product_id")
                if pid and str(pid) not in excluded_product_ids:
                    candidates = [{
                        "product_id": pid,
                        "product_name": p.get("product_name", "Banking product"),
                        "category": p.get("category", "Banking"),
                        "score": 0.65,
                        "reasoning": "Segment-safe option when eligibility filters were strict.",
                        "source": "fallback",
                        "annual_fee": p.get("annual_fee"),
                        "min_balance": p.get("min_balance"),
                        "interest_rate_apy": p.get("interest_rate_apy"),
                    }]
                    break

        if not candidates:
            channels, best_channel, best_channel_reason = self._compute_channels(
                persona_name, digital, churn_category, metrics
            )
            return {
                "customer_id": customer_id,
                "offer": None,
                "score": 0,
                "reason": "No eligible recommendations after exclusions. For high churn risk, prioritize retention outreach (call or branch).",
                "explainability": {
                    "why_this_offer": "No product passed eligibility for this customer. Recommend manual review or outbound retention contact.",
                    "why_our_ai": "Our AI applies credit, income, and balance rules so offers are actionable. When none pass, a relationship manager or branch follow-up is the best next step.",
                },
                "channels": channels,
                "best_channel": best_channel,
                "best_channel_reason": best_channel_reason,
                "persona": persona_name,
                "churn_risk_score": churn_risk_score,
                "churn_category": churn_category,
            }

        # Raw Agent B ordering (same candidate pool, no churn boost) — for B vs C comparison
        retention_categories = {
            "Savings",
            "CD",
            "Retirement_IRA",
            "Wealth_Management",
            "Investment",
            "Money_Market",
            "Regular Savings",
            "Certificates of Deposit",
        }
        b_ranked = sorted(
            [dict(r) for r in candidates],
            key=lambda x: float(x.get("score") or 0),
            reverse=True,
        )

        # Agent C: multi-signal boost (segment / similar) so one-best-offer can diverge from rule-based B #1
        AGENT_C_CROSS_SIGNAL_BOOST = 0.05

        # Agent C: apply retention boost on copies, then re-rank
        boosted: List[Dict[str, Any]] = []
        for c in candidates:
            cc = dict(c)
            base = float(cc.get("score") or 0)
            src = (cc.get("source") or "").strip()
            if src in ("segment_popular", "similar_products"):
                base += AGENT_C_CROSS_SIGNAL_BOOST
            if churn_risk_score is not None and churn_category in ("High", "Critical"):
                cat = cc.get("category") or ""
                if any(rc in cat for rc in retention_categories):
                    base += 0.12
            cc["score"] = base
            boosted.append(cc)
        boosted.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
        best = boosted[0]

        # Agent B reference: prefer rule-based execute order (matches Agent B UI); else merged-pool raw rank
        if agent_b_reference_recs and len(agent_b_reference_recs) > 0:
            ref_rows = agent_b_reference_recs[:3]
            agent_b_top_products = [
                {
                    "product_id": r.get("product_id"),
                    "product_name": r.get("product_name") or str(r.get("product_id") or ""),
                    "score": float(r.get("score") or 0),
                }
                for r in ref_rows
            ]
            b0 = agent_b_reference_recs[0]
            b_top_id = str(b0.get("product_id") or "")
            b_line = ", ".join(
                f"{(x.get('product_name') or x.get('product_id'))!s} ({float(x.get('score') or 0)*100:.0f}%)"
                for x in agent_b_reference_recs[:3]
            )
        else:
            b_top_id = str(b_ranked[0].get("product_id") or "") if b_ranked else ""
            b_line = ", ".join(
                f"{(x.get('product_name') or x.get('product_id'))!s} ({float(x.get('score') or 0)*100:.0f}%)"
                for x in b_ranked[:3]
            )
            agent_b_top_products = [
                {
                    "product_id": r.get("product_id"),
                    "product_name": r.get("product_name") or str(r.get("product_id") or ""),
                    "score": float(r.get("score") or 0),
                }
                for r in b_ranked[:3]
            ]

        c_pick_id = str(best.get("product_id") or "")
        recommendations_differ = bool(b_top_id and c_pick_id and b_top_id != c_pick_id)
        agent_c_vs_agent_b: Optional[Dict[str, Any]] = None
        if recommendations_differ:
            if agent_b_reference_recs and len(agent_b_reference_recs) > 0:
                b0 = agent_b_reference_recs[0]
            else:
                b0 = b_ranked[0]
            b_name = (b0.get("product_name") or b_top_id or "Agent B top pick").strip()
            c_name = (best.get("product_name") or c_pick_id or "this offer").strip()
            b_score = float(b0.get("score") or 0)
            c_score = float(best.get("score") or 0)
            template = self._template_b_vs_c(
                persona_name, churn_category, b_name, b_score, c_name, c_score
            )
            llm_text = self._llm_b_vs_c_explanation(
                persona_name=persona_name,
                churn_category=churn_category or "",
                agent_b_top_name=b_name,
                agent_b_top_score=b_score,
                agent_c_name=c_name,
                agent_c_score=c_score,
                agent_b_products_line=b_line,
            )
            if llm_text:
                agent_c_vs_agent_b = {
                    "recommendations_differ": True,
                    "explanation": llm_text,
                    "explanation_source": "llm",
                }
            else:
                agent_c_vs_agent_b = {
                    "recommendations_differ": True,
                    "explanation": template,
                    "explanation_source": "template",
                }
        else:
            agent_c_vs_agent_b = {
                "recommendations_differ": False,
                "explanation": None,
                "explanation_source": None,
            }

        reason = best.get("reasoning") or "Best fit for your segment and profile."
        score_val = float(best.get("score") or 0)
        source = best.get("source") or "persona_aligned"
        category = best.get("category") or "Banking"

        # Polished, structured explainability
        why_parts = [
            f"• This offer has the highest propensity score ({score_val*100:.0f}%) for your segment ({persona_name}).",
            f"• It matches your profile: deposits, digital engagement, and product depth.",
            f"• Source: {source.replace('_', ' ')}.",
        ]
        if churn_category in ("High", "Critical") and category:
            why_parts.insert(1, f"• As a {churn_category} churn-risk customer, retention-oriented products (e.g. savings, CD) were prioritized.")
        why_this_offer = "\n".join(why_parts)

        why_our_ai = (
            "• Our AI combines segment fit (persona), behavior (similar and popular products), and eligibility (credit, income, balance) in one score.\n"
            "• Rule-based systems often use a single signal; we use multiple signals so the one best offer is both relevant and actionable.\n"
            "• This reduces wasted touches and improves conversion."
        )

        channels, best_channel, best_channel_reason = self._compute_channels(
            persona_name, digital, churn_category, metrics
        )

        return {
            "customer_id": customer_id,
            "offer": {
                "product_id": best.get("product_id"),
                "product_name": best.get("product_name"),
                "category": category,
                "score": score_val,
                "reasoning": reason,
                "annual_fee": best.get("annual_fee"),
                "min_balance": best.get("min_balance"),
                "interest_rate_apy": best.get("interest_rate_apy"),
            },
            "score": score_val,
            "reason": reason,
            "explainability": {
                "why_this_offer": why_this_offer,
                "why_our_ai": why_our_ai,
            },
            "channels": channels,
            "best_channel": best_channel,
            "best_channel_reason": best_channel_reason,
            "persona": persona_name,
            "churn_risk_score": churn_risk_score,
            "churn_category": churn_category,
            "agent_b_top_products": agent_b_top_products,
            "agent_c_vs_agent_b": agent_c_vs_agent_b,
        }

    def _template_b_vs_c(
        self,
        persona_name: str,
        churn_category: Optional[str],
        agent_b_top_name: str,
        agent_b_top_score: float,
        agent_c_name: str,
        agent_c_score: float,
    ) -> str:
        """Fallback copy when LLM is unavailable."""
        churn_bit = ""
        if churn_category in ("High", "Critical"):
            churn_bit = (
                f" With {churn_category} churn risk, Agent C prioritizes retention-oriented offers so outreach "
                f"leads with a product that protects the relationship—not only the highest raw fit score."
            )
        return (
            f'Agent B\'s top match-ranked product is "{agent_b_top_name}" ({agent_b_top_score*100:.0f}% fit). '
            f'Agent C selects "{agent_c_name}" ({agent_c_score*100:.0f}% after retention rules) as the one best offer '
            f"for segment {persona_name}.{churn_bit} "
            f'Use "{agent_c_name}" as the primary campaign SKU to maximize retention and deepen share-of-wallet; '
            f'"{agent_b_top_name}" remains a strong alternative for follow-up if the customer declines.'
        )

    def _llm_b_vs_c_explanation(
        self,
        persona_name: str,
        churn_category: str,
        agent_b_top_name: str,
        agent_b_top_score: float,
        agent_c_name: str,
        agent_c_score: float,
        agent_b_products_line: str,
    ) -> str:
        try:
            import os

            if not (os.getenv("TOGETHER_API_KEY") or "").strip():
                return ""
            from utils.together_ai import together_ai

            raw = together_ai.generate_agent_b_vs_c_explanation(
                persona_name=persona_name,
                churn_category=churn_category,
                agent_b_top_name=agent_b_top_name,
                agent_b_top_score=agent_b_top_score,
                agent_c_name=agent_c_name,
                agent_c_score=agent_c_score,
                agent_b_products_line=agent_b_products_line,
            )
            if not raw or "Error generating" in raw:
                return ""
            return raw.strip()
        except Exception as e:
            logger.warning(f"agent_b vs agent_c LLM explanation failed: {e}")
            return ""

    def _compute_channels(
        self,
        persona_name: str,
        digital: float,
        churn_category: Optional[str],
        metrics: Dict,
    ):
        """Compute channel order and best channel with reason so they vary by segment and risk."""
        persona_lower = (persona_name or "").lower()
        is_traditional = "traditional" in persona_lower or "branch" in persona_lower
        is_high_churn = churn_category in ("High", "Critical")

        if is_high_churn:
            channels = [
                {"channel": "outbound_call", "priority": 1, "label": "Outbound call"},
                {"channel": "branch", "priority": 2, "label": "Branch"},
                {"channel": "email", "priority": 3, "label": "Email"},
            ]
            best_channel = "outbound_call"
            best_channel_reason = f"High churn risk ({churn_category}); personal outreach converts best."
        elif is_traditional:
            channels = [
                {"channel": "branch", "priority": 1, "label": "Branch"},
                {"channel": "direct_mail", "priority": 2, "label": "Direct mail"},
                {"channel": "email", "priority": 3, "label": "Email"},
            ]
            best_channel = "branch"
            pct = int((1 - digital) * 100)
            best_channel_reason = f"Segment prefers branch ({pct}% non-digital); in-person works best."
        elif digital >= 0.65:
            channels = [
                {"channel": "in_app", "priority": 1, "label": "In-app"},
                {"channel": "email", "priority": 2, "label": "Email"},
                {"channel": "web", "priority": 3, "label": "Web"},
            ]
            best_channel = "in_app"
            pct = int(digital * 100)
            best_channel_reason = f"High digital engagement ({pct}%); in-app reaches them where they are."
        elif digital >= 0.4:
            channels = [
                {"channel": "email", "priority": 1, "label": "Email"},
                {"channel": "web", "priority": 2, "label": "Web"},
                {"channel": "branch", "priority": 3, "label": "Branch"},
            ]
            best_channel = "email"
            pct = int(digital * 100)
            best_channel_reason = f"Mixed channel user ({pct}% digital); email has highest open rates."
        else:
            channels = [
                {"channel": "branch", "priority": 1, "label": "Branch"},
                {"channel": "email", "priority": 2, "label": "Email"},
                {"channel": "direct_mail", "priority": 3, "label": "Direct mail"},
            ]
            best_channel = "branch"
            best_channel_reason = "Lower digital usage; branch or direct mail performs better."

        return channels, best_channel, best_channel_reason

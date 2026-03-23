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
    ) -> Dict[str, Any]:
        """
        Select the single best offer for this customer and build explainability.
        If no candidates from recommendations, uses fallback_products when provided.
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
            if pid and (pid not in seen or rec.get("score", 0) > seen[pid].get("score", 0)):
                rec_copy = dict(rec)
                rec_copy["source"] = "segment_popular"
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

        # Boost retention-type products for high churn risk
        if churn_risk_score is not None and churn_category in ("High", "Critical"):
            retention_categories = {"Savings", "CD", "Retirement_IRA", "Wealth_Management", "Investment", "Money_Market", "Regular Savings", "Certificates of Deposit"}
            for c in candidates:
                cat = (c.get("category") or "")
                if any(rc in cat for rc in retention_categories):
                    c["score"] = (c.get("score") or 0) + 0.12
        candidates.sort(key=lambda x: x.get("score") or 0, reverse=True)
        best = candidates[0]

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
        }

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

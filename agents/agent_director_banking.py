"""
DirectorAgent — interprets behavioral signals from a customer's current session
and decides what product to recommend on their next visit.

This is distinct from Agent D's impression ledger (which tracks shown/clicked
counts over time). The Director reads *intent signals* — time on page, form
fills, high-value clicks — and derives an affinity score per product. The
product with the highest affinity becomes the next-visit pin directive.

Signal weights reflect intent strength:
    form_fill             1.00  — customer started applying (strongest signal)
    time_on_page_long     0.70  — >90 seconds = serious consideration
    click_apply           0.60  — explicit apply intent
    click_learn_more      0.35  — exploration, not yet committed
    time_on_page_medium   0.25  — 30–90 seconds, soft interest
    page_view             0.10  — weakest, merely visible
"""
import os
from typing import Optional

# ── Signal configuration ──────────────────────────────────────────────────────

SIGNAL_WEIGHTS: dict = {
    "form_fill":            1.00,
    "time_on_page_long":    0.70,
    "click_apply":          0.60,
    "click_learn_more":     0.35,
    "time_on_page_medium":  0.25,
    "page_view":            0.10,
}

# Signals whose presence implies a recurring intent (cap at 1.0 regardless)
CAPPING_SIGNALS = {"form_fill", "click_apply"}

# Minimum affinity score to generate a pin directive (filter noise)
MIN_AFFINITY_TO_PIN = 0.30

# ── Product name helper ────────────────────────────────────────────────────────

_PRODUCT_NAMES: dict = {
    "MRD_P001": "Meridian Essential Checking",
    "MRD_P002": "Meridian Plus Checking",
    "MRD_P003": "Meridian Prestige Checking",
    "MRD_P004": "Meridian Basic Savings",
    "MRD_P005": "Meridian High-Yield Savings",
    "MRD_P006": "Meridian Money Market",
    "MRD_P007": "Meridian 12-Month CD",
    "MRD_P008": "Meridian 24-Month CD",
    "MRD_P009": "Meridian Cash Back Card",
    "MRD_P010": "Meridian Rewards Visa",
    "MRD_P011": "Meridian Platinum Card",
    "MRD_P012": "Meridian Secured Card",
    "MRD_P013": "Meridian Auto Loan",
    "MRD_P014": "Meridian Personal Loan",
    "MRD_P015": "Meridian Home Equity Loan",
    "MRD_P016": "Meridian HELOC",
    "MRD_P017": "Meridian 30yr Fixed Mortgage",
    "MRD_P018": "Meridian FHA Mortgage",
    "MRD_P019": "Meridian Traditional IRA",
    "MRD_P020": "Meridian Roth IRA",
    "MRD_B001": "Meridian Business Essential Checking",
    "MRD_B002": "Meridian Business Plus Checking",
    "MRD_B003": "Meridian Business Savings",
    "MRD_B004": "Meridian Business Line of Credit",
    "MRD_B005": "Meridian Business Rewards Card",
    "MRD_A001": "Meridian Farm Operating Line",
    "MRD_A002": "Meridian Equipment Term Loan",
    "MRD_A003": "Meridian Land Improvement Loan",
}


class DirectorAgent:
    """
    Analyzes session behavioral signals and generates next-visit directives.

    Usage
    -----
    director = DirectorAgent()
    result = director.analyze_session(
        customer_id="MRD_C0001",
        behavioral_signals=[
            {"product_id": "MRD_P010", "signal_type": "time_on_page_long"},
            {"product_id": "MRD_P010", "signal_type": "form_fill"},
            {"product_id": "MRD_P009", "signal_type": "click_learn_more"},
        ],
        current_recommended_product_id="MRD_P009",
        experiment_channel="in_app",
    )
    """

    def __init__(self):
        self.signal_weights = SIGNAL_WEIGHTS

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze_session(
        self,
        customer_id: str,
        behavioral_signals: list,
        current_recommended_product_id: Optional[str] = None,
        experiment_channel: Optional[str] = None,
    ) -> dict:
        """
        Compute per-product affinity from behavioral signals and build
        next-visit directives.

        Parameters
        ----------
        behavioral_signals : list of {"product_id": str, "signal_type": str}
        current_recommended_product_id : the product Agent C served this visit
        experiment_channel : channel from winning experiment (if any)

        Returns
        -------
        {
            "affinity_analysis": {
                "top_product_id": str | None,
                "top_product_name": str,
                "affinity_score": float,
                "signal_summary": str,
                "signal_breakdown": {product_id: score},
                "signals_received": int,
            },
            "next_visit_directives": {
                "priority_pin_product_id": str | None,
                "priority_pin_reason": str,
                "boost_product_ids": list,
                "deprioritize_product_ids": list,
                "focus_source": str,
                "affinity_score": float,
                "recommended_channel": str | None,
            },
            "diverges_from_current": bool,
            "divergence_explanation": str,
        }
        """
        if not behavioral_signals:
            return self._empty_result(current_recommended_product_id)

        scores, signal_counts = self._accumulate_scores(behavioral_signals)

        if not scores:
            return self._empty_result(current_recommended_product_id)

        top_product = max(scores, key=lambda p: scores[p])
        top_score = round(min(scores[top_product], 1.0), 4)
        top_name = _PRODUCT_NAMES.get(top_product, top_product)

        signal_summary = self._build_signal_summary(signal_counts, top_product)

        # Normalize all scores to [0, 1]
        breakdown = {
            pid: round(min(s, 1.0), 4) for pid, s in sorted(scores.items(), key=lambda x: -x[1])
        }

        # Determine recommended channel
        rec_channel = self._pick_channel(top_product, experiment_channel, signal_counts.get(top_product, {}))

        # Build directives
        should_pin = top_score >= MIN_AFFINITY_TO_PIN
        pin_product = top_product if should_pin else None
        boost_ids = [
            pid for pid, s in breakdown.items()
            if pid != top_product and s >= 0.20
        ]

        pin_reason = ""
        if pin_product:
            sig_list = [s for s, c in signal_counts.get(top_product, {}).items() if c > 0]
            sig_friendly = [s.replace("_", " ") for s in sig_list]
            pin_reason = (
                f"Customer showed {', '.join(sig_friendly[:3])} intent signal"
                f"{'s' if len(sig_friendly) > 1 else ''} during this session"
            )

        diverges = bool(
            current_recommended_product_id
            and pin_product
            and pin_product != current_recommended_product_id
        )
        divergence_explanation = ""
        if diverges:
            curr_name = _PRODUCT_NAMES.get(current_recommended_product_id, current_recommended_product_id)
            divergence_explanation = (
                f"Director identified {top_name} intent despite {curr_name} being served"
            )

        return {
            "affinity_analysis": {
                "top_product_id": top_product if should_pin else None,
                "top_product_name": top_name,
                "affinity_score": top_score,
                "signal_summary": signal_summary,
                "signal_breakdown": breakdown,
                "signals_received": len(behavioral_signals),
            },
            "next_visit_directives": {
                "priority_pin_product_id": pin_product,
                "priority_pin_reason": pin_reason,
                "boost_product_ids": boost_ids[:3],
                "deprioritize_product_ids": [],
                "focus_source": "director_behavioral_analysis",
                "affinity_score": top_score,
                "recommended_channel": rec_channel,
            },
            "diverges_from_current": diverges,
            "divergence_explanation": divergence_explanation,
        }

    def derive_signals_from_ledger(self, impressions: list) -> list:
        """
        Auto-derive behavioral signals from Agent D's impression ledger rows.

        Used by the "Live / Auto" tab in the frontend — no manual input needed.

        Parameters
        ----------
        impressions : list of dicts from recommendation_impressions.csv rows
            Each row: {product_id, shown_count, click_count, ...}

        Returns
        -------
        list of {"product_id": str, "signal_type": str}
        """
        signals = []
        for row in impressions:
            pid = row.get("product_id") or row.get("recommended_product_id", "")
            if not pid:
                continue
            shown = int(row.get("shown_count", 0) or 0)
            clicks = int(row.get("click_count", 0) or 0)
            app_started = bool(row.get("application_started", False))
            app_completed = bool(row.get("application_completed", False))

            if app_completed:
                signals.append({"product_id": pid, "signal_type": "form_fill"})
            elif app_started:
                signals.append({"product_id": pid, "signal_type": "click_apply"})
            elif clicks >= 2:
                signals.append({"product_id": pid, "signal_type": "click_learn_more"})
            elif shown >= 3 and clicks == 0:
                # Shown 3+ times with no click = mild negative; skip
                pass
            elif shown >= 1:
                signals.append({"product_id": pid, "signal_type": "page_view"})

        return signals

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _accumulate_scores(self, behavioral_signals: list) -> tuple:
        """
        Accumulate weighted scores per product_id.
        Returns (scores dict, signal_counts dict).
        signal_counts: {product_id: {signal_type: count}}
        """
        scores: dict = {}
        signal_counts: dict = {}

        for sig in behavioral_signals:
            pid = sig.get("product_id", "").strip()
            stype = sig.get("signal_type", "").strip().lower()
            if not pid or stype not in self.signal_weights:
                continue

            weight = self.signal_weights[stype]
            scores[pid] = scores.get(pid, 0.0) + weight
            if pid not in signal_counts:
                signal_counts[pid] = {}
            signal_counts[pid][stype] = signal_counts[pid].get(stype, 0) + 1

        return scores, signal_counts

    def _build_signal_summary(self, signal_counts: dict, top_product: str) -> str:
        """Build a human-readable one-liner describing the strongest signals."""
        counts = signal_counts.get(top_product, {})
        parts = []

        # Rank signals by weight descending
        for stype in sorted(counts, key=lambda s: -self.signal_weights.get(s, 0)):
            cnt = counts[stype]
            label = stype.replace("_", " ")
            parts.append(f"{cnt}x {label}" if cnt > 1 else label)
            if len(parts) >= 3:
                break

        if not parts:
            return "behavioral interest detected"
        return " + ".join(parts) + " detected"

    def _pick_channel(
        self, product_id: str, experiment_channel: Optional[str], signal_counts: dict
    ) -> Optional[str]:
        """
        Pick recommended channel.
        Priority: experiment_channel > inferred from signals > product default.
        """
        if experiment_channel:
            return experiment_channel

        # Infer from signal pattern: form_fill / click_apply = in_app
        high_intent = {"form_fill", "click_apply"}
        if any(s in signal_counts for s in high_intent):
            return "in_app"

        return None

    def _empty_result(self, current_product: Optional[str]) -> dict:
        return {
            "affinity_analysis": {
                "top_product_id": None,
                "top_product_name": "",
                "affinity_score": 0.0,
                "signal_summary": "No behavioral signals provided",
                "signal_breakdown": {},
                "signals_received": 0,
            },
            "next_visit_directives": {
                "priority_pin_product_id": None,
                "priority_pin_reason": "",
                "boost_product_ids": [],
                "deprioritize_product_ids": [],
                "focus_source": "director_behavioral_analysis",
                "affinity_score": 0.0,
                "recommended_channel": None,
            },
            "diverges_from_current": False,
            "divergence_explanation": "",
        }

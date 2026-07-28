"""
MTAEngine — Markov chain Multi-Touch Attribution engine.

Uses mta_touchpoint_history.csv (journey_id, customer_id, persona, channel,
offer_id, product_id, timestamp, opened, clicked, converted, position).

Key public methods:
  compute_markov_attribution(persona, product_id) -> {channel: weight}
  get_customer_channel_fatigue(customer_id)       -> {channel: {sent, opened, clicked, is_fatigued}}
  get_persona_channel_stats(persona)              -> {channel: {conversion_rate, open_rate, ...}}
  get_all_personas_heatmap()                      -> {persona: {channel: stats}}
  get_customer_journey(customer_id, last_n_days)  -> list[dict]
  generate_channel_insight(...)                   -> dict
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    import pandas as pd  # only used for type hints

from utils.banking_constants import (
    CHANNELS,
    CHANNEL_LABELS,
    MTA_JOURNEY_CHANNELS,
    PERSONAS,
    MTA_FALLBACK_ATTRIBUTION,
    MTA_FALLBACK_ATTRIBUTION_DEFAULT,
    FATIGUE_CONSECUTIVE_THRESHOLD,
    FATIGUE_TOTAL_SENDS_MIN,
    MTA_MIN_PERSONAL_SENDS,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MTA_HISTORY_PATH = os.path.join(
    _ROOT, "data", "preloaded", "meridian_bank", "mta_touchpoint_history.csv"
)


class MTAEngine:
    def __init__(self, history_path: str = MTA_HISTORY_PATH):
        self._path = history_path
        self._df: Optional[pd.DataFrame] = None
        self._markov_cache: Dict[Tuple, Dict[str, float]] = {}
        self._heatmap_cache: Optional[Dict] = None
        self._persona_stats_cache: Dict[str, Dict] = {}

    # ── Lazy data loader ──────────────────────────────────────────────────────

    def _data(self):  # returns pd.DataFrame
        if self._df is None:
            import pandas as pd  # deferred — avoids segfault on Python 3.14 alpha at import time
            try:
                self._df = pd.read_csv(self._path, parse_dates=["timestamp"])
            except FileNotFoundError:
                logger.warning(
                    "[MTA] History file not found: %s — using empty DataFrame. "
                    "Run scripts/generate_mta_history.py to create it.", self._path
                )
                self._df = pd.DataFrame(columns=[
                    "journey_id", "customer_id", "persona", "channel",
                    "offer_id", "product_id", "timestamp",
                    "opened", "clicked", "converted", "position",
                ])
        return self._df

    # ── Core: Markov chain attribution (empirical removal-effect method) ──────

    def compute_markov_attribution(
        self,
        persona: Optional[str] = None,
        product_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Empirical removal-effect Markov attribution:

        For each channel C:
          1. Base conv rate = converted journeys / total journeys
          2. Remove journeys that contain C, recompute conv rate
          3. Removal effect[C] = (base - without_C) / base
          4. Attribution[C] = RE[C] / sum(RE)

        This matches the Databricks solution accelerator approach and avoids
        matrix inversion.
        """
        cache_key = (
            (persona or "").lower().strip(),
            (product_id or "").lower().strip(),
        )
        if cache_key in self._markov_cache:
            return self._markov_cache[cache_key]

        df = self._data()
        subset = df.copy()
        if persona:
            subset = subset[subset["persona"].str.lower().str.strip() == persona.lower().strip()]
        if product_id:
            subset = subset[subset["product_id"] == product_id]

        if len(subset) < 30:
            result = self._fallback_attribution(persona)
            self._markov_cache[cache_key] = result
            return result

        # Build journey-level summary: did this journey convert?
        journey_summary = (
            subset.groupby("journey_id")
            .agg(
                converted=("converted", "max"),
                channels=("channel", lambda x: set(x.tolist())),
            )
            .reset_index()
        )

        total = len(journey_summary)
        base_conv = journey_summary["converted"].mean()

        if base_conv <= 0 or total < 20:
            result = self._fallback_attribution(persona)
            self._markov_cache[cache_key] = result
            return result

        removal_effects: Dict[str, float] = {}
        for ch in CHANNELS:
            # outbound_call and web have no journey data in the CSV — skip Markov
            # computation for them; their weight comes from the fallback defaults.
            if ch not in MTA_JOURNEY_CHANNELS:
                removal_effects[ch] = 0.0
                continue
            # Journeys that never touched channel C
            without_c = journey_summary[
                journey_summary["channels"].apply(lambda s: ch not in s)
            ]
            if len(without_c) < 5:
                removal_effects[ch] = 0.01
                continue
            conv_without = without_c["converted"].mean()
            re = (base_conv - conv_without) / base_conv
            removal_effects[ch] = max(0.0, re)

        total_re = sum(removal_effects.values())
        if total_re <= 0:
            result = self._fallback_attribution(persona)
        else:
            result = {ch: round(re / total_re, 4) for ch, re in removal_effects.items()}
            for ch in CHANNELS:
                result.setdefault(ch, 0.0)

        self._markov_cache[cache_key] = result
        return result

    def _fallback_attribution(self, persona: Optional[str]) -> Dict[str, float]:
        """Persona-informed fallback when not enough journey data.
        Weights sourced from banking_constants.MTA_FALLBACK_ATTRIBUTION."""
        key = (persona or "").strip()
        for p in PERSONAS:
            if p.lower() == key.lower():
                return dict(MTA_FALLBACK_ATTRIBUTION[p])
        return dict(MTA_FALLBACK_ATTRIBUTION_DEFAULT)

    # ── Channel fatigue ───────────────────────────────────────────────────────

    def get_customer_channel_fatigue(self, customer_id: str) -> Dict[str, Dict]:
        """
        Per customer, per channel:
          - total sends, opens, clicks
          - is_fatigued = True if last THRESHOLD sends all had opened==0
                         AND total sends >= THRESHOLD
        """
        df = self._data()
        cust_df = df[df["customer_id"].astype(str) == str(customer_id)].sort_values("timestamp")
        result: Dict[str, Dict] = {}

        for ch in CHANNELS:
            ch_df = cust_df[cust_df["channel"] == ch]
            sent      = len(ch_df)
            opened    = int(ch_df["opened"].sum())
            clicked   = int(ch_df["clicked"].sum())
            converted = int(ch_df["converted"].sum())

            # Count actual consecutive no-opens from the tail of sends
            consecutive_no_open = 0
            if sent > 0:
                for val in reversed(ch_df["opened"].tolist()):
                    if val == 0:
                        consecutive_no_open += 1
                    else:
                        break

            # Fatigued = enough sends AND last N were all unopened
            # Deliberately NOT requiring total opens == 0: a customer who opened
            # once long ago but ignored the last 3+ sends is still fatigued.
            is_fatigued = bool(
                sent >= FATIGUE_TOTAL_SENDS_MIN
                and consecutive_no_open >= FATIGUE_CONSECUTIVE_THRESHOLD
            )

            ts_max = ch_df["timestamp"].max() if sent > 0 else None
            last_sent = str(ts_max)[:10] if (ts_max is not None and str(ts_max) != "NaT") else None

            result[ch] = {
                "sent":                sent,
                "opened":              opened,
                "clicked":             clicked,
                "converted":           converted,
                "is_fatigued":         is_fatigued,
                "consecutive_no_open": consecutive_no_open,
                "open_rate":           round(opened / sent, 3) if sent > 0 else 0.0,
                "click_rate":          round(clicked / sent, 3) if sent > 0 else 0.0,
                "last_sent":           last_sent,
            }

        return result

    # ── Persona channel stats ─────────────────────────────────────────────────

    def get_persona_channel_stats(self, persona: str) -> Dict[str, Dict]:
        if persona in self._persona_stats_cache:
            return self._persona_stats_cache[persona]

        df = self._data()
        subset = df[df["persona"].str.lower().str.strip() == persona.lower().strip()]
        total_customers = max(subset["customer_id"].nunique(), 1)

        result: Dict[str, Dict] = {}
        for ch in CHANNELS:
            ch_df = subset[subset["channel"] == ch]
            sent      = len(ch_df)
            opened    = int(ch_df["opened"].sum())
            clicked   = int(ch_df["clicked"].sum())
            converted = int(ch_df["converted"].sum())
            reach_n   = ch_df["customer_id"].nunique()

            result[ch] = {
                "sent":            sent,
                "opened":          opened,
                "clicked":         clicked,
                "converted":       converted,
                "open_rate":       round(opened / sent, 3) if sent > 0 else 0.0,
                "click_rate":      round(clicked / sent, 3) if sent > 0 else 0.0,
                "conversion_rate": round(converted / sent, 3) if sent > 0 else 0.0,
                "reach_pct":       round(reach_n / total_customers, 3),
                "sample_size":     sent,
            }

        self._persona_stats_cache[persona] = result
        return result

    def get_all_personas_heatmap(self) -> Dict[str, Dict]:
        if self._heatmap_cache:
            return self._heatmap_cache
        df = self._data()
        if df.empty:
            empty_stats = {ch: {"sent": 0, "opened": 0, "clicked": 0, "converted": 0,
                                "open_rate": 0.0, "click_rate": 0.0,
                                "conversion_rate": 0.0, "reach_pct": 0.0, "sample_size": 0}
                           for ch in CHANNELS}
            result = {p: dict(empty_stats) for p in PERSONAS}
        else:
            result = {p: self.get_persona_channel_stats(p) for p in PERSONAS}
        self._heatmap_cache = result
        return result

    # ── Customer journey ──────────────────────────────────────────────────────

    def get_customer_journey(
        self, customer_id: str, last_n_days: int = 60
    ) -> List[Dict]:
        import pandas as pd
        df = self._data()
        cust_df = df[df["customer_id"].astype(str) == str(customer_id)].sort_values("timestamp")

        if last_n_days > 0 and len(cust_df) > 0:
            ts_max = cust_df["timestamp"].max()
            cutoff = ts_max - pd.Timedelta(days=last_n_days)
            cust_df = cust_df[cust_df["timestamp"] >= cutoff]

        rows = []
        for _, r in cust_df.iterrows():
            rows.append({
                "journey_id": str(r["journey_id"]),
                "channel":    str(r["channel"]),
                "offer_id":   str(r["offer_id"]),
                "product_id": str(r["product_id"]),
                "timestamp":  str(r["timestamp"])[:16],
                "opened":     bool(r["opened"]),
                "clicked":    bool(r["clicked"]),
                "converted":  bool(r["converted"]),
                "position":   int(r["position"]),
            })
        return rows

    # ── Two-tier channel recommendation ──────────────────────────────────────

    MIN_PERSONAL_SENDS = MTA_MIN_PERSONAL_SENDS  # from banking_constants

    def get_customer_channel_recommendation(
        self,
        customer_id: str,
        persona: Optional[str] = None,
    ) -> Dict:
        """
        Two-tier channel selection:
          Tier 1 (personal): customer has >= MIN_PERSONAL_SENDS total sends →
              score each non-fatigued channel by personal click/open rate.
              clicks weighted 3× vs opens (clicks = stronger intent).
          Tier 2 (segment): insufficient personal data →
              fall back to persona-level Markov attribution.

        Returns:
          {
            "recommended_channel": str,
            "signal_source": "personal" | "segment" | "segment_fallback",
            "confidence": "high" | "medium" | "low",
            "total_personal_sends": int,
            "reason": str,
            "personal_scores": {ch: score},
          }
        """
        df = self._data()
        cust_df = df[df["customer_id"].astype(str) == str(customer_id)]
        total_sends = len(cust_df)
        fatigue = self.get_customer_channel_fatigue(customer_id)

        if total_sends < self.MIN_PERSONAL_SENDS:
            # ── Tier 2: segment signal ───────────────────────────────────────
            segment_attr = self.compute_markov_attribution(persona=persona)
            best = max(
                (ch for ch in CHANNELS if not fatigue.get(ch, {}).get("is_fatigued", False)),
                key=lambda ch: segment_attr.get(ch, 0),
                default=CHANNELS[0],
            )
            return {
                "recommended_channel": best,
                "signal_source": "segment",
                "confidence": "low" if total_sends == 0 else "medium",
                "total_personal_sends": total_sends,
                "reason": (
                    f"Only {total_sends} personal send{'s' if total_sends != 1 else ''} recorded — "
                    f"insufficient individual history. Using {persona or 'segment'}-level Markov "
                    f"attribution ({round(segment_attr.get(best, 0) * 100)}% for {CHANNEL_LABELS.get(best, best)}) "
                    "as the primary signal."
                ),
                "personal_scores": {},
            }

        # ── Tier 1: personal engagement signal ──────────────────────────────
        personal_scores: Dict[str, float] = {}
        for ch in CHANNELS:
            if fatigue.get(ch, {}).get("is_fatigued", False):
                continue
            ch_df = cust_df[cust_df["channel"] == ch]
            if len(ch_df) == 0:
                continue
            sends  = len(ch_df)
            opens  = int(ch_df["opened"].sum())
            clicks = int(ch_df["clicked"].sum())
            # Clicks = 3× weight (intent), opens = 1× (awareness)
            score = (clicks / sends) * 3.0 + (opens / sends) * 1.0
            if score > 0:
                personal_scores[ch] = round(score, 4)

        if not personal_scores:
            # All channels with data are fatigued — segment fallback
            segment_attr = self.compute_markov_attribution(persona=persona)
            best = max(
                (ch for ch in CHANNELS if not fatigue.get(ch, {}).get("is_fatigued", False)),
                key=lambda ch: segment_attr.get(ch, 0),
                default=CHANNELS[0],
            )
            return {
                "recommended_channel": best,
                "signal_source": "segment_fallback",
                "confidence": "low",
                "total_personal_sends": total_sends,
                "reason": (
                    "All channels with personal engagement data are fatigued. "
                    f"Using segment attribution for {CHANNEL_LABELS.get(best, best)}."
                ),
                "personal_scores": {},
            }

        best_personal = max(personal_scores, key=lambda ch: personal_scores[ch])
        score = personal_scores[best_personal]
        confidence = "high" if score >= 0.5 else "medium" if score >= 0.15 else "low"

        return {
            "recommended_channel": best_personal,
            "signal_source": "personal",
            "confidence": confidence,
            "total_personal_sends": total_sends,
            "reason": (
                f"Personal engagement across {total_sends} sends: "
                f"{CHANNEL_LABELS.get(best_personal, best_personal)} leads with "
                f"score {score:.2f} (clicks×3 + opens×1 / sends). "
                "Individual behaviour overrides segment-level Markov attribution."
            ),
            "personal_scores": personal_scores,
        }

    # ── AI insight ────────────────────────────────────────────────────────────

    def generate_channel_insight(
        self,
        customer_id: str,
        best_channel: str,
        mta_attribution: Dict[str, float],
        fatigue: Dict[str, Dict],
        persona_stats: Dict[str, Dict],
        persona_name: str,
        experiment_id: Optional[str] = None,
        p_value: Optional[float] = None,
        digital_score: Optional[float] = None,
    ) -> Dict:
        """Pure template-based channel explanation."""
        ch_label = CHANNEL_LABELS.get(best_channel, best_channel.replace("_", " ").title())
        reason_lines = []
        suppressed = [ch for ch, info in fatigue.items() if info.get("is_fatigued")]

        best_pct = round(mta_attribution.get(best_channel, 0) * 100)

        # Headline: ratio vs second best channel
        ranked = sorted(mta_attribution.items(), key=lambda x: -x[1])
        second = next(((ch, v) for ch, v in ranked if ch != best_channel and v > 0), None)
        if second:
            second_label = CHANNEL_LABELS.get(second[0], second[0])
            second_pct   = round(second[1] * 100)
            ratio = round(best_pct / max(second_pct, 1), 1)
            headline = (
                f"{ch_label} delivers {ratio}× more conversions than "
                f"{second_label} for {persona_name} segment"
            )
        else:
            headline = f"{ch_label} is the top-performing channel for {persona_name} customers"

        # Markov attribution fact
        if best_pct > 0:
            reason_lines.append({
                "type": "positive",
                "text": (
                    f"Persona {persona_name}: {ch_label} yields {best_pct}% of "
                    "segment conversions (Markov attribution)"
                ),
            })

        # Digital engagement
        if digital_score is not None:
            if digital_score >= 0.65 and best_channel in ("in_app", "sms"):
                reason_lines.append({
                    "type": "positive",
                    "text": f"Digital engagement score {digital_score:.2f} — confirms digital-first behavior",
                })
            elif digital_score < 0.35 and best_channel in ("branch", "direct_mail"):
                reason_lines.append({
                    "type": "positive",
                    "text": f"Low digital engagement ({digital_score:.2f}) — branch or mail preferred",
                })

        # Fatigue warnings
        for ch in suppressed:
            f_info = fatigue[ch]
            ch_l = CHANNEL_LABELS.get(ch, ch)
            reason_lines.append({
                "type": "warning",
                "text": (
                    f"{ch_l}: fatigued — {f_info['sent']} sends, "
                    f"{f_info['opened']} opens (suppressed)"
                ),
            })

        # Experiment fact
        if experiment_id and p_value is not None:
            sig = "statistically significant" if p_value < 0.05 else "not yet significant"
            p_str = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.4f}"
            reason_lines.append({
                "type": "positive" if p_value < 0.05 else "neutral",
                "text": f"Experiment {experiment_id}: {sig} ({p_str})",
            })

        # Persona conversion rate
        p_ch = persona_stats.get(best_channel, {})
        p_conv = round(p_ch.get("conversion_rate", 0) * 100, 1)
        if p_conv > 0:
            reason_lines.append({
                "type": "positive",
                "text": (
                    f"{ch_label} conversion rate for {persona_name}: {p_conv}% "
                    f"({p_ch.get('sample_size', 0):,} historical sends)"
                ),
            })

        # Top alternative
        top_alternative = None
        for ch, _ in ranked:
            if ch != best_channel and not fatigue.get(ch, {}).get("is_fatigued"):
                top_alternative = ch
                break

        return {
            "headline":            headline,
            "reason_lines":        reason_lines,
            "suppressed_channels": suppressed,
            "top_alternative":     top_alternative,
            "best_channel_pct":    best_pct,
            "persona_conv_rate":   p_conv,
        }


# ── Module-level singleton ────────────────────────────────────────────────────

_MTA_ENGINE: Optional[MTAEngine] = None


def get_mta_engine(history_path: str = MTA_HISTORY_PATH) -> MTAEngine:
    global _MTA_ENGINE
    if _MTA_ENGINE is None:
        _MTA_ENGINE = MTAEngine(history_path)
    return _MTA_ENGINE

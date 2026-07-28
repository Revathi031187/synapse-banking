"""
ConversionLiftEngine — looks up pre-computed A/B experiment results for a
given (product_id, persona) pair and returns the winning offer with its
statistical metadata.

Experiment data is loaded once from data/config/offer_experiments.json.
Lookup is O(1) via a two-level dict: {product_id: {persona_lower: record}}.

Cross-persona fallback: if no exact persona match, returns any experiment for
the same product that has a winner (useful when a customer's persona slightly
diverges from the trained set).
"""
import json
import math
import os
from typing import Optional

# ── Default path ──────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_EXPERIMENTS_PATH = os.path.join(_ROOT, "data", "config", "offer_experiments.json")


class ConversionLiftEngine:

    def __init__(self, experiments_path: Optional[str] = None):
        path = experiments_path or _DEFAULT_EXPERIMENTS_PATH
        self._experiments_raw = self._load(path)
        # Primary index: product_id -> persona_lower -> experiment_record
        self._index: dict = {}
        # Secondary index: product_id -> [list of experiments with winners]
        self._product_index: dict = {}
        self._build_index()

    # ── Loading & indexing ────────────────────────────────────────────────────

    def _load(self, path: str) -> list:
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _build_index(self):
        for exp in self._experiments_raw:
            pid = exp.get("product_id", "")
            persona = exp.get("persona", "").lower().strip()
            if pid not in self._index:
                self._index[pid] = {}
                self._product_index[pid] = []
            self._index[pid][persona] = exp
            if not exp.get("no_offer_recommended", True):
                self._product_index[pid].append(exp)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_best_offer(self, product_id: str, persona: str) -> dict:
        """
        Return the winning offer for a (product_id, persona) pair.

        Returns
        -------
        On hit:
            {
                "found": True,
                "offer_id": str,
                "offer_name": str,
                "offer_type": str,
                "channel": str,
                "lift_abs": float,
                "lift_pct": float,
                "p_value": float,
                "z_stat": float,
                "holdout_conversion_rate": float,
                "winning_conversion_rate": float,
                "no_offer_recommended": bool,
                "experiment_id": str,
                "all_variants": list,
                "channel_attribution": dict,
                "persona_match": "exact" | "cross_persona",
            }
        No match:
            {"found": False}
        """
        persona_key = persona.lower().strip()
        product_exps = self._index.get(product_id, {})

        # 1. Exact (product, persona) match
        exp = product_exps.get(persona_key)
        match_type = "exact"

        # 2. Cross-persona fallback: pick any winner for this product
        if exp is None:
            fallback_list = self._product_index.get(product_id, [])
            if fallback_list:
                exp = fallback_list[0]
                match_type = "cross_persona"

        if exp is None:
            return {"found": False}

        holdout_rate = exp["holdout"]["conversion_rate"]

        if exp.get("no_offer_recommended", True):
            return {
                "found": True,
                "no_offer_recommended": True,
                "experiment_id": exp["experiment_id"],
                "holdout_conversion_rate": holdout_rate,
                "all_variants": exp.get("variants", []),
                "channel_attribution": exp.get("channel_attribution", {}),
                "persona_match": match_type,
            }

        winning_id = exp["winning_variant_id"]
        winning_v = next(
            (v for v in exp["variants"] if v["variant_id"] == winning_id), None
        )
        if winning_v is None:
            return {"found": False}

        return {
            "found": True,
            "no_offer_recommended": False,
            "offer_id": exp["winning_offer_id"],
            "offer_name": winning_v.get("offer_name", ""),
            "offer_type": winning_v.get("offer_type", ""),
            "channel": exp.get("winning_channel", "in_app"),
            "lift_abs": winning_v.get("lift_abs", 0.0),
            "lift_pct": winning_v.get("lift_pct", 0.0),
            "p_value": winning_v.get("p_value", 1.0),
            "z_stat": winning_v.get("z_stat", 0.0),
            "holdout_conversion_rate": holdout_rate,
            "winning_conversion_rate": winning_v.get("conversion_rate", 0.0),
            "experiment_id": exp["experiment_id"],
            "all_variants": exp.get("variants", []),
            "channel_attribution": exp.get("channel_attribution", {}),
            "persona_match": match_type,
        }

    def recompute_significance(
        self,
        n_variant: int,
        conv_variant: int,
        n_holdout: int,
        conv_holdout: int,
        alpha: float = 0.05,
    ) -> dict:
        """
        Live Z-test on two raw count inputs.  Useful for UI demo sliders.

        Returns {"z_stat": float, "p_value": float, "is_significant": bool,
                 "lift_abs": float, "lift_pct": float}
        """
        try:
            from scipy.stats import proportions_ztest  # type: ignore
            z_stat, p_value = proportions_ztest(
                [conv_variant, conv_holdout],
                [n_variant, n_holdout],
                alternative="larger",
            )
            z_stat = float(z_stat)
            p_value = float(p_value)
        except ImportError:
            z_stat, p_value = self._manual_ztest(
                n_variant, conv_variant, n_holdout, conv_holdout
            )

        p1 = conv_variant / n_variant if n_variant > 0 else 0.0
        p2 = conv_holdout / n_holdout if n_holdout > 0 else 0.0
        lift_abs = round(p1 - p2, 4)
        lift_pct = round(lift_abs / p2 * 100, 1) if p2 > 0 else 0.0

        return {
            "z_stat": round(z_stat, 4),
            "p_value": round(p_value, 6),
            "is_significant": bool(p_value < alpha and lift_abs > 0),
            "lift_abs": lift_abs,
            "lift_pct": lift_pct,
        }

    def list_products(self) -> list:
        """Return all product_ids that have at least one experiment record."""
        return sorted(self._index.keys())

    def list_personas_for_product(self, product_id: str) -> list:
        """Return known persona names for a product."""
        return [exp["persona"] for exp in self._experiments_raw if exp.get("product_id") == product_id]

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _manual_ztest(n1, x1, n2, x2):
        p1 = x1 / n1 if n1 > 0 else 0
        p2 = x2 / n2 if n2 > 0 else 0
        p_pool = (x1 + x2) / (n1 + n2) if (n1 + n2) > 0 else 0
        if p_pool <= 0 or p_pool >= 1:
            return 0.0, 1.0
        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        if se == 0:
            return 0.0, 1.0
        z = (p1 - p2) / se
        p_value = ConversionLiftEngine._normal_sf(z)
        return z, p_value

    @staticmethod
    def _normal_sf(z):
        t = 1.0 / (1.0 + 0.2316419 * abs(z))
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
        cdf = 1.0 - pdf * poly
        return 1.0 - cdf if z >= 0 else cdf

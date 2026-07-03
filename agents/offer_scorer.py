"""
OfferScorer — scores each product offer against a customer profile.

Used by Agent C after the best product is selected: loads all active offers
for that product, runs this scorer, and returns the best-fit offer plus
runner-ups.
"""

import json
import logging
import os
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

TODAY = datetime.today()

_offer_logger = logging.getLogger(__name__)


# ── offer registry loader ─────────────────────────────────────────────────────

def load_offers_registry(config_path: Optional[str] = None) -> Dict[str, List[Dict]]:
    """
    Returns {product_id: [offer_dict, ...]} for all active offers.
    Defaults to data/config/product_offers.json relative to project root.
    """
    if config_path is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(root, "data", "config", "product_offers.json")

    if not os.path.exists(config_path):
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        offers = json.load(f)

    registry: Dict[str, List[Dict]] = {}
    for offer in offers:
        pid = offer.get("product_id", "")
        registry.setdefault(pid, []).append(offer)
    return registry


# ── helpers ───────────────────────────────────────────────────────────────────

def _sf(val, default: float = 0.0) -> float:
    try:
        return float(val) if val not in (None, "", "None") else default
    except (ValueError, TypeError):
        return default

def _si(val, default: int = 0) -> int:
    try:
        return int(float(val)) if val not in (None, "", "None") else default
    except (ValueError, TypeError):
        return default

def _sb(val) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes")

def _days_remaining(offer_end_date) -> Optional[int]:
    if not offer_end_date or offer_end_date in (None, "None", ""):
        return None
    try:
        end = datetime.strptime(str(offer_end_date), "%Y-%m-%d")
        delta = (end - TODAY).days
        return max(0, delta)
    except (ValueError, TypeError):
        return None

def _normalize(val: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (val - lo) / (hi - lo)))


# ── main scorer ───────────────────────────────────────────────────────────────

class OfferScorer:
    """
    Scores a single offer against a customer profile.

    Default factor weights (sum = 1.0):
      monetary_value_relevance  : 0.30
      spending_behavior_match   : 0.25
      life_stage_fit            : 0.20
      digital_engagement_fit    : 0.15
      urgency_retention_signal  : 0.10

    When a persona is provided, PERSONA_WEIGHT_OVERRIDES and PERSONA_TAG_MAP
    adjust both weights and the guaranteed lifestyle-tag set for that segment.
    """

    WEIGHTS = {
        "monetary_value_relevance":  0.30,
        "spending_behavior_match":   0.25,
        "life_stage_fit":            0.20,
        "digital_engagement_fit":    0.15,
        "urgency_retention_signal":  0.10,
    }

    # Per-persona weight overrides — must sum to 1.0
    PERSONA_WEIGHT_OVERRIDES: Dict[str, Dict[str, float]] = {
        "digital native": {
            "monetary_value_relevance":  0.20,
            "spending_behavior_match":   0.25,
            "life_stage_fit":            0.15,
            "digital_engagement_fit":    0.30,  # digital channel fit is the primary signal
            "urgency_retention_signal":  0.10,
        },
        "wealth builder": {
            "monetary_value_relevance":  0.40,  # ROI/value of the offer matters most
            "spending_behavior_match":   0.30,
            "life_stage_fit":            0.15,
            "digital_engagement_fit":    0.10,
            "urgency_retention_signal":  0.05,
        },
        "everyday essential": {
            "monetary_value_relevance":  0.25,
            "spending_behavior_match":   0.35,  # spending pattern alignment is key
            "life_stage_fit":            0.25,  # family life stage matters
            "digital_engagement_fit":    0.10,
            "urgency_retention_signal":  0.05,
        },
        "retiree anchor": {
            "monetary_value_relevance":  0.25,
            "spending_behavior_match":   0.20,
            "life_stage_fit":            0.35,  # life stage is the dominant signal
            "digital_engagement_fit":    0.05,
            "urgency_retention_signal":  0.15,  # CD expiry / retention urgency matters
        },
        "at-risk saver": {
            "monetary_value_relevance":  0.20,
            "spending_behavior_match":   0.20,
            "life_stage_fit":            0.15,
            "digital_engagement_fit":    0.10,
            "urgency_retention_signal":  0.35,  # retention is the priority signal
        },
    }

    # Guaranteed lifestyle tags injected per persona — augment customer-derived tags
    PERSONA_TAG_MAP: Dict[str, set] = {
        "digital native":     {"early_career", "digital_shopper", "safety_first"},
        "wealth builder":     {"wealth_builder", "high_earner", "retirement_saver"},
        "everyday essential": {"family", "safety_first", "commuter"},
        "retiree anchor":     {"retirement_focused", "retirement_saver"},
        "at-risk saver":      {"debt_reducer", "safety_first"},
    }

    TRAVEL_FREQ_SCORE = {
        "none": 0.05,
        "domestic_occasional": 0.45,
        "domestic_frequent": 0.75,
        "international_occasional": 0.85,
        "international_frequent": 1.0,
    }

    def __init__(self, offers_registry: Optional[Dict[str, List[Dict]]] = None):
        self.registry = offers_registry or load_offers_registry()

    # ── public API ────────────────────────────────────────────────────────────

    def get_offers_for_product(self, product_id: str) -> List[Dict]:
        return list(self.registry.get(product_id, []))

    def passes_eligibility(
        self,
        offer: Dict,
        customer: Dict,
        churn_category: Optional[str] = None,
        owned_subcategories: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        Hard eligibility check. Returns (passes: bool, reason: str).
        Any False short-circuits the offer from scoring.
        """
        tenure = _si(customer.get("months_since_relationship_started") or customer.get("tenure_months", 0))
        credit_tier = str(customer.get("credit_tier", "fair")).lower()
        cs = _si(customer.get("credit_score", 600))
        home_type = str(customer.get("home_ownership_type", "renter")).lower()

        # new_customer_only — use 12 months as the practical cutoff so recent joiners
        # still see new-customer offers (3-month window was too aggressive for this dataset)
        if _sb(offer.get("new_customer_only", False)) and tenure > 12:
            return False, "new_customer_only: customer tenure > 12 months"

        # existing_customer_only
        if _sb(offer.get("existing_customer_only", False)) and tenure < 1:
            return False, "existing_customer_only: customer tenure < 1 month"

        # min_tenure
        min_ten = _si(offer.get("min_tenure_months", 0))
        if tenure < min_ten:
            return False, f"min_tenure_months: {tenure} < {min_ten}"

        # excluded_credit_tiers
        excl_tiers = offer.get("excluded_credit_tiers")
        if excl_tiers:
            for et in str(excl_tiers).split(","):
                if et.strip().lower() == credit_tier:
                    return False, f"excluded_credit_tier: {credit_tier}"

        # min_credit_score_override
        cs_override = _si(offer.get("min_credit_score_override", 0))
        if cs_override > 0 and cs < cs_override:
            return False, f"min_credit_score_override: {cs} < {cs_override}"

        # required_existing_products (subcategory check)
        req_prods = offer.get("required_existing_products")
        if req_prods and owned_subcategories is not None:
            req_lower = str(req_prods).lower()
            owned_lower = [s.lower() for s in owned_subcategories]
            if req_lower not in owned_lower:
                return False, f"required_existing_products: '{req_prods}' not in customer's owned subcategories"

        # excluded_if_holds_subcategory
        excl_sub = offer.get("excluded_if_holds_subcategory")
        if excl_sub and owned_subcategories is not None:
            if str(excl_sub).lower() in [s.lower() for s in owned_subcategories]:
                return False, f"excluded_if_holds_subcategory: customer already holds '{excl_sub}'"

        # requires_homeowner
        if _sb(offer.get("requires_homeowner", False)):
            if home_type == "renter":
                return False, "requires_homeowner: customer is a renter"

        # min_deposits_required
        min_deps = _sf(offer.get("min_deposits_required", 0))
        if min_deps > 0:
            deps = _sf(customer.get("total_deposits", 0))
            if deps < min_deps:
                return False, f"min_deposits_required: {deps:.0f} < {min_deps:.0f}"

        # churn_only
        if _sb(offer.get("churn_only", False)):
            if churn_category not in ("High", "Critical"):
                return False, "churn_only: customer is not High/Critical churn"

        return True, ""

    def score(
        self,
        offer: Dict,
        customer: Dict,
        churn_risk_score: float = 0.0,
        churn_category: Optional[str] = None,
        persona: Optional[str] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Returns (final_score: float, breakdown: dict).
        final_score is in [0.0, 1.0].
        persona: when provided, applies PERSONA_WEIGHT_OVERRIDES and injects guaranteed tags.
        """
        breakdown: Dict[str, Any] = {}

        f1 = self._factor_monetary_value(offer, customer)
        f2 = self._factor_spending_behavior(offer, customer)
        f3 = self._factor_life_stage(offer, customer)
        f4 = self._factor_digital_engagement(offer, customer)
        f5 = self._factor_urgency_retention(offer, customer, churn_risk_score, churn_category)

        w = self._persona_weights(persona)
        composite = (
            f1 * w["monetary_value_relevance"] +
            f2 * w["spending_behavior_match"] +
            f3 * w["life_stage_fit"] +
            f4 * w["digital_engagement_fit"] +
            f5 * w["urgency_retention_signal"]
        )
        # slight tiebreak on bank-assigned base_offer_score
        base = _sf(offer.get("base_offer_score", 0.7))
        final = composite * 0.92 + base * 0.08

        # revenue-priority micro-boost for high-margin offer types
        REVENUE_PRIORITY = {
            "balance_transfer_promo": 0.03,
            "cashback_boost":         0.02,
            "cd_rate_bump":           0.02,
            "signup_bonus":           0.01,
            "loyalty_reward":         0.01,
        }
        final += REVENUE_PRIORITY.get(str(offer.get("offer_type", "")).lower(), 0.0)
        final = max(0.0, min(1.0, final))

        breakdown = {
            "monetary_value_relevance": {
                "score": round(f1, 4),
                "weight": w["monetary_value_relevance"],
                "explanation": self._explain_monetary(offer, customer, f1),
                "calculation": self._calc_monetary(offer, customer),
            },
            "spending_behavior_match": {
                "score": round(f2, 4),
                "weight": w["spending_behavior_match"],
                "explanation": self._explain_spending(offer, customer, f2),
                "calculation": self._calc_spending(offer, customer),
            },
            "life_stage_fit": {
                "score": round(f3, 4),
                "weight": w["life_stage_fit"],
                "explanation": self._explain_life_stage(offer, customer, f3),
                "calculation": self._calc_life_stage(offer, customer),
            },
            "digital_engagement_fit": {
                "score": round(f4, 4),
                "weight": w["digital_engagement_fit"],
                "explanation": self._explain_digital(offer, customer, f4),
                "calculation": self._calc_digital(offer, customer),
            },
            "urgency_retention_signal": {
                "score": round(f5, 4),
                "weight": w["urgency_retention_signal"],
                "explanation": self._explain_urgency(offer, churn_category, f5),
                "calculation": self._calc_urgency(offer, customer, churn_risk_score, churn_category),
            },
        }
        return round(final, 4), breakdown

    def _build_fallback_result(self, product_id: str, customer: Dict) -> Dict[str, Any]:
        """Lifestyle-matched generic offer — returned when no product-specific offers are registered or all are blocked."""
        tags = self._derive_customer_lifestyle_tags(customer)

        if 'frequent_traveler' in tags or 'international_traveler' in tags:
            hero = "Travel more, earn more with every purchase"
            how  = "Use this product regularly to build travel rewards. Link your Meridian checking for the best perks."
            b1, b2, b3 = "Earn points on every transaction", "Redeem for flights, hotels, and upgrades", "No blackout dates on redemptions"
            offer_type = "cashback_boost"
        elif 'debt_reducer' in tags:
            hero = "Cut interest costs — pay smarter"
            how  = "Set up automatic payments from your Meridian checking to lock in a rate discount and pay down debt faster."
            b1, b2, b3 = "Rate reduction with auto-pay enrollment", "Debt-payoff tracker in the Meridian app", "No prepayment penalty — pay off early"
            offer_type = "rate_discount"
        elif 'retirement_focused' in tags or 'retirement_saver' in tags:
            hero = "Your retirement goals, our priority"
            how  = "Regular contributions and account bundling unlock preferred rates and waived annual fees."
            b1, b2, b3 = "Tax-advantaged growth potential", "Dedicated retirement planning support", "Fee waiver with linked checking account"
            offer_type = "fee_waiver"
        elif 'homebuyer' in tags or 'home_improvement' in tags:
            hero = "Your path to homeownership starts here"
            how  = "Apply today for a personalized rate quote and connect with a Meridian home loan specialist."
            b1, b2, b3 = "Competitive rates for qualified buyers", "60-day rate lock guarantee", "Fast pre-approval — decision in minutes"
            offer_type = "rate_discount"
        elif 'wealth_builder' in tags or 'high_earner' in tags:
            hero = "Premium banking for premium results"
            how  = "Maintain your Meridian relationship to unlock exclusive rates and dedicated banker access."
            b1, b2, b3 = "Premium deposit and loan rates", "Dedicated relationship banker", "Exclusive wealth management referrals"
            offer_type = "loyalty_reward"
        elif 'early_career' in tags or 'digital_shopper' in tags:
            hero = "Start strong — zero fees, max rewards"
            how  = "Set up direct deposit to activate your new member welcome benefits immediately."
            b1, b2, b3 = "No monthly fee with direct deposit", "Instant mobile account management", "Free credit score monitoring"
            offer_type = "fee_waiver"
        elif 'family' in tags:
            hero = "Family banking — simplified"
            how  = "Bundle family accounts to unlock shared savings benefits and simplify your household finances."
            b1, b2, b3 = "Linked family accounts in one app", "Joint savings booster rate", "Free family debit cards"
            offer_type = "fee_waiver"
        elif 'business_owner' in tags:
            hero = "Power your business with Meridian"
            how  = "Open a business banking relationship to qualify for preferred rates and dedicated small business support."
            b1, b2, b3 = "Dedicated small business banker", "Preferred rates on business loans", "Free online ACH and wire transfers"
            offer_type = "loyalty_reward"
        elif 'agricultural' in tags:
            hero = "Ag banking built for your season"
            how  = "Speak with our agricultural lending team about flexible seasonal payment structures."
            b1, b2, b3 = "Seasonal interest-only payment options", "Lines of credit up to $2M", "48-hour credit decisions"
            offer_type = "rate_discount"
        else:
            hero = "Exclusive Meridian member benefit — active now"
            how  = "Maintain your account in good standing to enjoy ongoing member benefits and preferred pricing."
            b1, b2, b3 = "Preferred rates and terms", "Priority customer service access", "Digital banking with advanced security"
            offer_type = "loyalty_reward"

        return {
            "available": True,
            "is_fallback": True,
            "selected_offer": {
                "offer_id": f"GEN_{product_id}",
                "offer_type": offer_type,
                "offer_name": "Meridian Member Benefit",
                "headline_value": hero,
                "terms_summary": hero,
                "content_hero_stat": hero,
                "content_how_to_earn": how,
                "content_benefit_1": b1,
                "content_benefit_2": b2,
                "content_benefit_3": b3,
                "preferred_channel": "in_app",
                "is_evergreen": True,
                "offer_end_date": None,
                "days_remaining": None,
                "is_fallback": True,
            },
            "offer_score": 0.60,
            "offer_score_breakdown": {},
            "runner_up_offers": [],
            "secondary_offer": None,
            "offers_considered": 0,
            "offers_blocked_by_eligibility": 0,
        }

    def select_best_offer(
        self,
        product_id: str,
        customer: Dict,
        churn_risk_score: float = 0.0,
        churn_category: Optional[str] = None,
        owned_subcategories: Optional[List[str]] = None,
        persona: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns dict with:
          available, selected_offer, offer_score, offer_score_breakdown,
          runner_up_offers, offers_considered, offers_blocked_by_eligibility

        persona: when provided, injects guaranteed lifestyle tags and applies
                 persona-specific factor weights before scoring.
        """
        # Augment customer with persona-guaranteed tags (Layer 1)
        scored_customer = self._persona_augmented_customer(customer, persona) if persona else customer

        _cust_id   = customer.get("customer_id", "?")
        _cust_tags = self._derive_customer_lifestyle_tags(scored_customer)

        candidates = self.get_offers_for_product(product_id)
        if not candidates:
            _offer_logger.info(
                f"[OFFER-INTEL] cust={_cust_id} | product={product_id} | "
                f"NO OFFERS DEFINED — fallback"
            )
            return self._build_fallback_result(product_id, scored_customer)

        eligible = []
        blocked_reasons = []
        for offer in candidates:
            ok, reason = self.passes_eligibility(
                offer, scored_customer, churn_category, owned_subcategories
            )
            if ok:
                # Layer 2: persona weight overrides applied inside score()
                score, breakdown = self.score(offer, scored_customer, churn_risk_score, churn_category, persona)
                eligible.append((score, breakdown, offer))
            else:
                blocked_reasons.append((offer.get("offer_id"), reason))

        blocked = len(blocked_reasons)

        if not eligible:
            _offer_logger.info(
                f"[OFFER-INTEL] cust={_cust_id} | product={product_id} | "
                f"total={len(candidates)} | eligible=0 | blocked={blocked} — all offers blocked"
            )
            for _oid, _why in blocked_reasons:
                _offer_logger.info(f"[OFFER-INTEL]   🚫 {_oid} blocked: {_why}")
            result = self._build_fallback_result(product_id, scored_customer)
            result["offers_considered"] = len(candidates)
            result["offers_blocked_by_eligibility"] = blocked
            return result

        eligible.sort(key=lambda x: x[0], reverse=True)

        best_score, best_breakdown, best_offer = eligible[0]
        runner_ups = []
        for sc, _, o in eligible[1:3]:
            runner_ups.append({
                "offer_id": o.get("offer_id"),
                "offer_name": o.get("offer_name"),
                "offer_score": sc,
                "reason_not_selected": self._runner_up_reason(o, best_offer, sc, best_score),
            })

        # ── offer selection logging ───────────────────────────────────────────
        _offer_logger.info(
            f"[OFFER-INTEL] cust={_cust_id} | product={product_id} | "
            f"total={len(candidates)} | eligible={len(eligible)} | blocked={blocked}"
        )
        if _cust_tags:
            _offer_logger.info(f"[OFFER-INTEL]   🏷️  customer_tags: {sorted(_cust_tags)}")
        else:
            _offer_logger.info(f"[OFFER-INTEL]   🏷️  customer_tags: (none derived)")
        for _sc, _bd, _o in eligible:
            _spend_exp = (_bd.get("spending_behavior_match") or {}).get("explanation", "")
            _offer_logger.info(
                f"[OFFER-INTEL]   📊 {_o.get('offer_id')} "
                f"'{_o.get('offer_name')}' → {_sc:.4f} | {_spend_exp}"
            )
        _offer_logger.info(
            f"[OFFER-INTEL]   🏆 SELECTED: {best_offer.get('offer_id')} "
            f"'{best_offer.get('offer_name')}' ({best_score:.4f})"
        )
        for _ru in runner_ups:
            _offer_logger.info(
                f"[OFFER-INTEL]   🥈 runner-up: {_ru.get('offer_id')} "
                f"'{_ru.get('offer_name')}' ({_ru.get('offer_score', 0):.4f})"
            )
        # ─────────────────────────────────────────────────────────────────────

        # secondary offer: best offer of a DIFFERENT type (for "Also Consider" display)
        primary_type = best_offer.get("offer_type", "")
        secondary_entry = next(
            (entry for entry in eligible[1:] if entry[2].get("offer_type", "") != primary_type),
            eligible[1] if len(eligible) > 1 else None,
        )
        secondary_offer_payload = None
        if secondary_entry:
            sec_score, _, sec_offer = secondary_entry
            secondary_offer_payload = {
                "offer_id": sec_offer.get("offer_id"),
                "offer_type": sec_offer.get("offer_type"),
                "offer_name": sec_offer.get("offer_name"),
                "headline_value": sec_offer.get("headline_value"),
                "offer_score": sec_score,
                "content_hero_stat": sec_offer.get("content_hero_stat"),
            }

        # Persona scoring metadata: which path was used and what tags were active
        persona_key = persona.lower().strip() if persona else None
        persona_scoring = {
            "persona": persona,
            "weights_used": "persona_override" if (persona_key and persona_key in self.PERSONA_WEIGHT_OVERRIDES) else "default",
            "active_weights": self._persona_weights(persona),
            "guaranteed_tags": sorted(self.PERSONA_TAG_MAP.get(persona_key, set())) if persona_key else [],
            "derived_tags": sorted(_cust_tags),
        } if persona else None

        return {
            "available": True,
            "secondary_offer": secondary_offer_payload,
            "selected_offer": {
                "offer_id": best_offer.get("offer_id"),
                "offer_type": best_offer.get("offer_type"),
                "offer_name": best_offer.get("offer_name"),
                "headline_value": best_offer.get("headline_value"),
                "terms_summary": self._build_terms_summary(best_offer),
                "value_amount": best_offer.get("value_amount"),
                "value_currency": best_offer.get("value_currency"),
                "content_hero_stat": best_offer.get("content_hero_stat"),
                "content_how_to_earn": best_offer.get("content_how_to_earn"),
                "content_benefit_1": best_offer.get("content_benefit_1"),
                "content_benefit_2": best_offer.get("content_benefit_2"),
                "content_benefit_3": best_offer.get("content_benefit_3"),
                "preferred_channel": best_offer.get("preferred_channel"),
                "is_evergreen": best_offer.get("is_evergreen"),
                "offer_end_date": best_offer.get("offer_end_date"),
                "days_remaining": _days_remaining(best_offer.get("offer_end_date")),
            },
            "offer_score": best_score,
            "offer_score_breakdown": best_breakdown,
            "runner_up_offers": runner_ups,
            "offers_considered": len(candidates),
            "offers_blocked_by_eligibility": blocked,
            "persona_scoring": persona_scoring,
            "selection_method": "formula_score",
        }

    # ── persona helpers ───────────────────────────────────────────────────────

    def _persona_augmented_customer(self, customer: Dict, persona: str) -> Dict:
        """Return a shallow customer copy with persona-guaranteed lifestyle tags injected."""
        guaranteed = self.PERSONA_TAG_MAP.get(persona.lower().strip(), set())
        if not guaranteed:
            return customer
        augmented = dict(customer)
        augmented["_persona_guaranteed_tags"] = guaranteed
        return augmented

    def _persona_weights(self, persona: Optional[str]) -> Dict[str, float]:
        """Return weight dict for the persona, falling back to class defaults."""
        if persona:
            key = persona.lower().strip()
            if key in self.PERSONA_WEIGHT_OVERRIDES:
                return self.PERSONA_WEIGHT_OVERRIDES[key]
        return self.WEIGHTS

    # ── customer lifestyle tag derivation ────────────────────────────────────

    @staticmethod
    def _derive_customer_lifestyle_tags(customer: Dict) -> set:
        tags = set()
        # Persona-guaranteed tags (injected by _persona_augmented_customer)
        guaranteed = customer.get("_persona_guaranteed_tags")
        if guaranteed:
            tags.update(guaranteed)

        # travel_frequency
        travel = str(customer.get('travel_frequency', 'none') or 'none').lower()
        if travel in ('domestic_frequent', 'international_occasional', 'international_frequent'):
            tags.add('frequent_traveler')
        if travel in ('international_occasional', 'international_frequent'):
            tags.add('international_traveler')

        # primary_spending_category
        prim_cat = str(customer.get('primary_spending_category', '') or '').lower()
        if prim_cat == 'groceries':      tags.add('grocery_spender')
        if prim_cat == 'dining':         tags.add('dining_enthusiast')
        if prim_cat in ('gas', 'fuel'):  tags.add('commuter')
        if prim_cat == 'travel':         tags.add('frequent_traveler')
        if prim_cat in ('online_retail', 'online retail', 'shopping'):
            tags.add('digital_shopper')

        # life_stage — handles CSV values (Title Case / spaces / dashes) and snake_case variants
        life_stage = str(customer.get('life_stage', '') or '').lower().replace('-', '_').replace(' ', '_')
        if life_stage in ('student', 'young_single', 'young_professional'):
            tags.add('early_career')
        if life_stage in ('family', 'new_family', 'growing_family'):
            tags.add('family')
        if life_stage == 'pre_retiree':
            tags.add('retirement_focused')
            tags.add('retirement_saver')
        if life_stage == 'retiree':
            tags.add('retirement_focused')

        # financial_goal — handles CSV values (debt_payoff, wealth_growth, etc.)
        goal = str(customer.get('financial_goal', '') or '').lower().replace(' ', '_')
        if goal in ('pay_off_debt', 'debt_payoff', 'debt_reduction'):
            tags.add('debt_reducer')
        if goal in ('home_purchase', 'buy_home'):
            tags.add('homebuyer')
        if goal in ('retirement_savings', 'retirement_planning'):
            tags.add('retirement_saver')
        if goal in ('grow_wealth', 'wealth_growth', 'investment'):
            tags.add('wealth_builder')
        if goal in ('build_emergency_fund', 'emergency_fund', 'savings_growth'):
            tags.add('safety_first')
        if goal in ('wealth_preservation', 'estate_planning'):
            tags.add('wealth_builder')
            tags.add('safety_first')

        # income / deposit threshold
        if _sf(customer.get('income', 0)) > 150000 or _sf(customer.get('total_deposits', 0)) > 100000:
            tags.add('high_earner')

        # segment
        segment = str(customer.get('segment', '') or '').lower()
        if segment == 'business':     tags.add('business_owner')
        if segment == 'agricultural': tags.add('agricultural')

        return tags

    # ── factor 1: monetary value relevance ───────────────────────────────────

    def _factor_monetary_value(self, offer: Dict, customer: Dict) -> float:
        offer_type = str(offer.get("offer_type", "")).lower()
        income     = _sf(customer.get("income", 40000))
        monthly_spend = _sf(customer.get("monthly_spend_in_primary_cat", 300))
        out_debt   = _sf(customer.get("outstanding_debt_total", 0))
        fee_sens   = str(customer.get("fee_sensitivity_tier", "medium")).lower()
        deposits   = _sf(customer.get("total_deposits", 0))

        if offer_type == "signup_bonus":
            value = _sf(offer.get("value_amount", 0))
            spend_req = _sf(offer.get("spend_requirement", 500))
            # spend attainability: can customer realistically hit the spend threshold?
            monthly_txn_proxy = max(monthly_spend, income / 24)
            window_days = _sf(offer.get("spend_window_days", 90))
            projected_spend = monthly_txn_proxy * (window_days / 30)
            attainability = min(1.0, projected_spend / max(spend_req, 1))
            # value as % of annual income
            value_ratio = min(1.0, value / max(income * 0.003, 50))
            return min(1.0, (value_ratio * 0.6 + attainability * 0.4))

        elif offer_type in ("intro_apr", "balance_transfer_promo"):
            # most useful for customers with outstanding debt
            if out_debt > 0:
                duration = _sf(offer.get("rate_duration_months", 12))
                # estimated savings vs 22% typical card APR
                savings = out_debt * 0.22 * (duration / 12)
                return min(1.0, savings / max(income * 0.02, 200))
            # or fee-sensitive customers looking to finance a purchase
            if fee_sens == "high":
                return 0.65
            return 0.40

        elif offer_type == "cashback_boost":
            cashback_cat = str(offer.get("cashback_category", "")).lower()
            prim_cat = str(customer.get("primary_spending_category", "")).lower()
            cashback_pct = _sf(offer.get("cashback_pct", 3.0))
            base_pct     = 1.5  # assumed base rate
            duration_mo  = _sf(offer.get("rate_duration_months", 6))
            extra_rate   = (cashback_pct - base_pct) / 100
            if cashback_cat and cashback_cat == prim_cat:
                projected_extra = monthly_spend * extra_rate * duration_mo
                return min(1.0, projected_extra / max(income * 0.004, 30) + 0.35)
            else:
                return 0.30

        elif offer_type in ("cd_rate_bump", "rate_discount", "intro_rate_boost"):
            bump = _sf(offer.get("value_amount", 0.15))
            # more valuable for savers with larger deposits
            dep_factor = _normalize(deposits, 500, 50000)
            return min(1.0, 0.40 + dep_factor * 0.50 + bump * 0.40)

        elif offer_type == "fee_waiver":
            annual_fee = _sf(offer.get("value_amount", 50))
            # highly valuable for fee-sensitive customers
            if fee_sens == "high":
                return min(1.0, 0.50 + annual_fee / 500)
            if fee_sens == "medium":
                return min(1.0, 0.35 + annual_fee / 600)
            return min(1.0, 0.20 + annual_fee / 800)

        elif offer_type == "loyalty_reward":
            # tenure-sensitive; more valuable for long-tenured customers
            tenure = _si(customer.get("months_since_relationship_started") or customer.get("tenure_months", 0))
            return _normalize(tenure, 6, 60) * 0.75 + 0.15

        elif offer_type == "referral_bonus":
            digital = _sf(customer.get("digital_engagement_score", 0.5))
            return 0.25 + digital * 0.45

        # generic
        return 0.45

    # ── factor 2: spending behavior match ────────────────────────────────────

    def _factor_spending_behavior(self, offer: Dict, customer: Dict) -> float:
        offer_type   = str(offer.get("offer_type", "")).lower()
        cashback_cat = str(offer.get("cashback_category") or "").lower()
        prim_cat     = str(customer.get("primary_spending_category", "")).lower()
        travel_freq  = str(customer.get("travel_frequency", "none")).lower()
        xsell        = _sf(customer.get("cross_sell_receptivity", 0.5))

        # Lifestyle tag matching — primary behavioral signal when tags are declared on the offer
        offer_tags = offer.get('lifestyle_tags')
        if offer_tags:
            customer_tags = self._derive_customer_lifestyle_tags(customer)
            if customer_tags:
                matches = len(set(offer_tags) & customer_tags)
                if matches > 0:
                    match_ratio = matches / len(offer_tags)
                    return min(1.0, 0.65 + match_ratio * 0.25 + xsell * 0.10)
                else:
                    return max(0.05, 0.25 - len(offer_tags) * 0.03)

        # cashback or points on specific category
        if cashback_cat:
            if cashback_cat == prim_cat:
                return min(1.0, 0.75 + xsell * 0.25)
            # partial match: e.g. "groceries" vs "dining" both food-related
            partial_pairs = {("groceries","dining"),("dining","groceries"),
                             ("travel","gas"),("gas","travel"),
                             ("online_retail","dining"),("online_retail","groceries")}
            if (cashback_cat, prim_cat) in partial_pairs:
                return 0.50 + xsell * 0.20
            return 0.20

        # travel-themed offers (signup bonus for travel card, companion ticket)
        if offer_type in ("signup_bonus","cashback_boost") and "travel" in str(offer.get("offer_name","")).lower():
            return self.TRAVEL_FREQ_SCORE.get(travel_freq, 0.3)

        # financial goal alignment (highest-conversion signal)
        goal = str(customer.get("financial_goal", "")).lower()
        goal_offer_alignment = {
            "pay_off_debt":         ("balance_transfer_promo", "rate_discount", "intro_apr"),
            "home_purchase":        ("rate_lock", "fee_waiver", "rate_discount"),
            "retirement_savings":   ("cd_rate_bump", "rate_bump", "loyalty_reward"),
            "grow_wealth":          ("signup_bonus", "fee_waiver", "loyalty_reward"),
            "build_emergency_fund": ("intro_rate_boost", "rate_boost", "cd_rate_bump"),
        }
        aligned_types = goal_offer_alignment.get(goal, ())
        if aligned_types:
            if offer_type in aligned_types:
                return min(1.0, 0.40 + xsell * 0.25 + 0.15)
            # penalise acquisition offers pushed at a debt-focused customer
            if offer_type == "signup_bonus" and goal == "pay_off_debt":
                return max(0.0, 0.40 + xsell * 0.25 - 0.10)

        # generic offer — moderate baseline boosted by cross-sell receptivity
        return 0.40 + xsell * 0.25

    # ── factor 3: life stage fit ──────────────────────────────────────────────

    def _factor_life_stage(self, offer: Dict, customer: Dict) -> float:
        offer_type = str(offer.get("offer_type", "")).lower()
        age = _si(customer.get("age", 40))
        life_stage = str(customer.get("life_stage", "")).lower()

        base = _sf(offer.get("scoring_weights", {}).get("life_stage_boost", 0.3))

        # age-bracket multipliers
        if 18 <= age <= 30:
            if offer_type in ("signup_bonus", "intro_apr", "cashback_boost"):
                mult = 1.25
            elif offer_type in ("cd_rate_bump", "loyalty_reward"):
                mult = 0.60
            else:
                mult = 0.85
        elif 31 <= age <= 50:
            if offer_type in ("cashback_boost", "balance_transfer_promo", "signup_bonus"):
                mult = 1.15
            elif offer_type == "fee_waiver":
                mult = 1.10
            else:
                mult = 0.90
        elif 51 <= age <= 65:
            if offer_type in ("cd_rate_bump", "loyalty_reward", "fee_waiver"):
                mult = 1.20
            elif offer_type in ("signup_bonus", "cashback_boost"):
                mult = 0.85
            else:
                mult = 1.0
        else:  # 65+
            if offer_type in ("fee_waiver", "loyalty_reward", "cd_rate_bump"):
                mult = 1.25
            elif offer_type in ("intro_apr", "balance_transfer_promo"):
                mult = 0.75
            else:
                mult = 0.90

        # life stage fine-tuning
        if life_stage in ("student", "young_single") and offer_type == "intro_apr":
            mult *= 1.10
        if life_stage in ("new_family", "growing_family") and offer_type in ("cashback_boost","signup_bonus"):
            mult *= 1.10
        if life_stage in ("pre_retiree", "retiree") and offer_type == "cd_rate_bump":
            mult *= 1.15

        return min(1.0, max(0.05, base * mult + 0.20))

    # ── factor 4: digital engagement fit ─────────────────────────────────────

    def _factor_digital_engagement(self, offer: Dict, customer: Dict) -> float:
        digital = _sf(customer.get("digital_engagement_score", 0.5))
        w_boost = _sf(offer.get("scoring_weights", {}).get("digital_boost", 0.3))
        offer_complexity = _si(offer.get("offer_complexity", 1))

        if digital >= 0.65:
            # digital customers benefit more from complex, app-centric offers
            digital_score = w_boost * (0.5 + digital * 0.5)
        elif digital < 0.35:
            # branch-oriented customers prefer simple, low-complexity offers
            simplicity_bonus = 1.0 - (offer_complexity - 1) / 3.0
            digital_score = simplicity_bonus * 0.7 + (1 - w_boost) * 0.3
        else:
            # mid-range — blend
            digital_score = w_boost * digital + (1 - w_boost) * (1 - digital) * 0.5

        return min(1.0, max(0.05, digital_score))

    # ── factor 5: urgency and retention ──────────────────────────────────────

    def _factor_urgency_retention(
        self, offer: Dict, customer: Dict,
        churn_risk_score: float, churn_category: Optional[str]
    ) -> float:
        offer_type = str(offer.get("offer_type", "")).lower()
        is_evergreen = _sb(offer.get("is_evergreen", True))
        days_left = _days_remaining(offer.get("offer_end_date"))

        # retention-oriented offers for at-risk customers
        retention_types = ("loyalty_reward", "fee_waiver", "cd_rate_bump", "balance_transfer_promo")
        if churn_category in ("High", "Critical"):
            if offer_type in retention_types:
                retention_boost = 0.15 * (churn_risk_score / 100)
            else:
                retention_boost = -0.10  # acquisition offers less relevant for churning customer
        else:
            retention_boost = 0.0

        # urgency from time-limited offers
        if not is_evergreen and days_left is not None:
            if days_left <= 7:
                urgency = 1.0
            elif days_left <= 14:
                urgency = 0.90
            elif days_left <= 30:
                urgency = 0.78
            elif days_left <= 60:
                urgency = 0.65
            else:
                urgency = 0.55
        else:
            urgency = 0.55  # evergreen, no urgency premium

        return min(1.0, max(0.0, urgency + retention_boost))

    # ── calculation detail helpers (for UI explainability) ───────────────────

    def _calc_monetary(self, offer: Dict, customer: Dict) -> Dict:
        offer_type    = str(offer.get("offer_type", "")).lower()
        income        = _sf(customer.get("income", 40000))
        monthly_spend = _sf(customer.get("monthly_spend_in_primary_cat", 300))
        out_debt      = _sf(customer.get("outstanding_debt_total", 0))
        fee_sens      = str(customer.get("fee_sensitivity_tier", "medium")).lower()
        deposits      = _sf(customer.get("total_deposits", 0))

        if offer_type == "signup_bonus":
            value     = _sf(offer.get("value_amount", 0))
            spend_req = _sf(offer.get("spend_requirement", 500))
            proxy     = max(monthly_spend, income / 24)
            wdays     = _sf(offer.get("spend_window_days", 90))
            proj      = proxy * (wdays / 30)
            att       = min(1.0, proj / max(spend_req, 1))
            vrat      = min(1.0, value / max(income * 0.003, 50))
            sc        = round(min(1.0, vrat * 0.6 + att * 0.4), 2)
            return {
                "inputs": {
                    "Bonus value": f"${value:,.0f}",
                    "Annual income": f"${income:,.0f}",
                    "Monthly spend proxy": f"${proxy:,.0f}",
                    "Spend requirement": f"${spend_req:,.0f} in {int(wdays)} days",
                },
                "formula": "score = value_ratio × 0.60 + attainability × 0.40",
                "steps": [
                    f"Projected spend in {int(wdays)}d = ${proxy:,.0f} × ({int(wdays)}/30) = ${proj:,.0f}",
                    f"Attainability = min(1.0, ${proj:,.0f} ÷ ${spend_req:,.0f}) = {att:.2f}",
                    f"Value ratio = min(1.0, ${value:,.0f} ÷ max(${income*0.003:,.0f}, $50)) = {vrat:.2f}",
                    f"Score = {vrat:.2f}×0.60 + {att:.2f}×0.40 = {sc}",
                ],
            }
        elif offer_type in ("intro_apr", "balance_transfer_promo"):
            if out_debt > 0:
                dur    = _sf(offer.get("rate_duration_months", 12))
                savs   = out_debt * 0.22 * (dur / 12)
                denom  = max(income * 0.02, 200)
                sc     = round(min(1.0, savs / denom), 2)
                return {
                    "inputs": {
                        "Outstanding debt": f"${out_debt:,.0f}",
                        "Intro period": f"{int(dur)} months",
                        "Assumed market APR": "22%",
                        "Annual income": f"${income:,.0f}",
                    },
                    "formula": "savings = debt × 22% × (months/12)   score = savings ÷ max(income×2%, $200)",
                    "steps": [
                        f"Interest savings = ${out_debt:,.0f} × 0.22 × ({int(dur)}/12) = ${savs:,.0f}",
                        f"Score denom = max(${income*0.02:,.0f}, $200) = ${denom:,.0f}",
                        f"Score = min(1.0, ${savs:,.0f} ÷ ${denom:,.0f}) = {sc}",
                    ],
                }
            sc = 0.65 if fee_sens == "high" else 0.40
            return {
                "inputs": {"Outstanding debt": "$0", "Fee sensitivity tier": fee_sens},
                "formula": "No debt → fee_sensitivity fallback",
                "steps": [
                    "No outstanding debt — interest-savings path skipped",
                    f"Fee sensitivity '{fee_sens}' → score = {sc}",
                ],
            }
        elif offer_type == "cashback_boost":
            cb_cat  = str(offer.get("cashback_category", "")).lower()
            pc      = str(customer.get("primary_spending_category", "")).lower()
            cb_pct  = _sf(offer.get("cashback_pct", 3.0))
            base_r  = 1.5
            dur_mo  = _sf(offer.get("rate_duration_months", 6))
            xrate   = (cb_pct - base_r) / 100
            if cb_cat and cb_cat == pc:
                proj    = monthly_spend * xrate * dur_mo
                denom   = max(income * 0.004, 30)
                sc      = round(min(1.0, proj / denom + 0.35), 2)
                return {
                    "inputs": {
                        "Cashback rate": f"{cb_pct}%",
                        "Base rate": f"{base_r}%",
                        "Boost period": f"{int(dur_mo)} months",
                        "Monthly spend (primary cat)": f"${monthly_spend:,.0f}",
                        "Category match": f"'{cb_cat}' = '{pc}'",
                    },
                    "formula": "extra = (cb% − 1.5%)/100 × spend × months   score = extra÷denom + 0.35",
                    "steps": [
                        f"Extra rate = ({cb_pct}% − {base_r}%) / 100 = {xrate:.4f}",
                        f"Projected extra = ${monthly_spend:,.0f} × {xrate:.4f} × {int(dur_mo)} = ${proj:,.2f}",
                        f"Score = min(1.0, ${proj:,.2f} ÷ ${denom:,.2f} + 0.35) = {sc}",
                    ],
                }
            return {
                "inputs": {
                    "Offer cashback category": cb_cat or "general",
                    "Customer primary category": pc,
                    "Match": "No",
                },
                "formula": "No category match → 0.30",
                "steps": [
                    f"Offer category '{cb_cat}' ≠ customer's '{pc}'",
                    "Score = 0.30 (category mismatch fallback)",
                ],
            }
        elif offer_type in ("cd_rate_bump", "rate_discount", "intro_rate_boost"):
            bump   = _sf(offer.get("value_amount", 0.15))
            dpf    = _normalize(deposits, 500, 50000)
            sc     = round(min(1.0, 0.40 + dpf * 0.50 + bump * 0.40), 2)
            label  = "APY boost" if offer_type == "intro_rate_boost" else "Rate bump"
            return {
                "inputs": {
                    "Total deposits": f"${deposits:,.0f}",
                    label: f"{bump:.2f}%",
                    "Deposit range": "$500 – $50,000",
                },
                "formula": "score = 0.40 + normalize(deposits)×0.50 + rate_boost×0.40",
                "steps": [
                    f"Deposit factor = normalize(${deposits:,.0f}, $500, $50K) = {dpf:.2f}",
                    f"Score = 0.40 + {dpf:.2f}×0.50 + {bump:.2f}×0.40 = {sc}",
                ],
            }
        elif offer_type == "fee_waiver":
            afee = _sf(offer.get("value_amount", 50))
            if fee_sens == "high":   bv, div = 0.50, 500
            elif fee_sens == "medium": bv, div = 0.35, 600
            else:                    bv, div = 0.20, 800
            sc = round(min(1.0, bv + afee / div), 2)
            return {
                "inputs": {
                    "Annual fee waived": f"${afee:,.0f}",
                    "Fee sensitivity tier": fee_sens,
                },
                "formula": f"score = base + annual_fee ÷ {div}",
                "steps": [
                    f"Fee sensitivity '{fee_sens}' → base = {bv}, divisor = {div}",
                    f"Score = min(1.0, {bv} + ${afee:,.0f} ÷ {div}) = {sc}",
                ],
            }
        elif offer_type == "loyalty_reward":
            ten = _si(customer.get("months_since_relationship_started") or customer.get("tenure_months", 0))
            tf  = _normalize(ten, 6, 60)
            sc  = round(tf * 0.75 + 0.15, 2)
            return {
                "inputs": {
                    "Tenure": f"{ten} months",
                    "Tenure range": "6 – 60 months",
                },
                "formula": "score = normalize(tenure, 6, 60) × 0.75 + 0.15",
                "steps": [
                    f"Tenure factor = normalize({ten}, 6, 60) = {tf:.2f}",
                    f"Score = {tf:.2f} × 0.75 + 0.15 = {sc}",
                ],
            }
        elif offer_type == "referral_bonus":
            dig = _sf(customer.get("digital_engagement_score", 0.5))
            sc  = round(0.25 + dig * 0.45, 2)
            return {
                "inputs": {"Digital engagement score": f"{dig:.2f}"},
                "formula": "score = 0.25 + digital × 0.45",
                "steps": [f"Score = 0.25 + {dig:.2f} × 0.45 = {sc}"],
            }
        return {
            "inputs": {"offer_type": offer_type},
            "formula": "Generic → 0.45",
            "steps": ["Unrecognized offer type → score = 0.45"],
        }

    def _calc_spending(self, offer: Dict, customer: Dict) -> Dict:
        offer_type   = str(offer.get("offer_type", "")).lower()
        cashback_cat = str(offer.get("cashback_category") or "").lower()
        prim_cat     = str(customer.get("primary_spending_category", "")).lower()
        xsell        = _sf(customer.get("cross_sell_receptivity", 0.5))

        offer_tags = offer.get("lifestyle_tags")
        if offer_tags:
            ctags = self._derive_customer_lifestyle_tags(customer)
            if ctags:
                matched = sorted(set(offer_tags) & ctags)
                nm = len(matched)
                if nm > 0:
                    mrat = nm / len(offer_tags)
                    sc   = round(min(1.0, 0.65 + mrat * 0.25 + xsell * 0.10), 2)
                    return {
                        "inputs": {
                            "Offer lifestyle tags": ", ".join(offer_tags),
                            "Customer tags": ", ".join(sorted(ctags)),
                            "Matched tags": ", ".join(matched),
                            "Cross-sell receptivity": f"{xsell:.2f}",
                        },
                        "formula": "score = 0.65 + (matches÷offer_tags)×0.25 + xsell×0.10",
                        "steps": [
                            f"Matched {nm} of {len(offer_tags)} tags: [{', '.join(matched)}]",
                            f"Match ratio = {nm}/{len(offer_tags)} = {mrat:.2f}",
                            f"Score = 0.65 + {mrat:.2f}×0.25 + {xsell:.2f}×0.10 = {sc}",
                        ],
                    }
                pen = round(max(0.05, 0.25 - len(offer_tags) * 0.03), 2)
                return {
                    "inputs": {
                        "Offer lifestyle tags": ", ".join(offer_tags),
                        "Customer tags": ", ".join(sorted(ctags)) if ctags else "none derived",
                        "Overlap": "None",
                    },
                    "formula": "No match → score = max(0.05, 0.25 − n_tags×0.03)",
                    "steps": [
                        "No overlap between offer lifestyle tags and customer profile",
                        f"Penalty = max(0.05, 0.25 − {len(offer_tags)}×0.03) = {pen}",
                    ],
                }
            return {
                "inputs": {"Offer lifestyle tags": ", ".join(offer_tags), "Customer tags": "none derived"},
                "formula": "Lifestyle tags present but no customer tags derived",
                "steps": ["Could not derive customer lifestyle tags — generic fallback"],
            }

        if cashback_cat:
            if cashback_cat == prim_cat:
                sc = round(min(1.0, 0.75 + xsell * 0.25), 2)
                return {
                    "inputs": {
                        "Cashback category": cashback_cat,
                        "Customer primary category": prim_cat,
                        "Match": "Exact",
                        "Cross-sell receptivity": f"{xsell:.2f}",
                    },
                    "formula": "Exact match: score = 0.75 + xsell×0.25",
                    "steps": [
                        f"Category match: '{cashback_cat}' = '{prim_cat}'",
                        f"Score = 0.75 + {xsell:.2f}×0.25 = {sc}",
                    ],
                }
            partial_pairs = {("groceries","dining"),("dining","groceries"),
                             ("travel","gas"),("gas","travel"),
                             ("online_retail","dining"),("online_retail","groceries")}
            if (cashback_cat, prim_cat) in partial_pairs:
                sc = round(0.50 + xsell * 0.20, 2)
                return {
                    "inputs": {
                        "Cashback category": cashback_cat,
                        "Customer primary category": prim_cat,
                        "Match": "Partial (related categories)",
                        "Cross-sell receptivity": f"{xsell:.2f}",
                    },
                    "formula": "Partial match: score = 0.50 + xsell×0.20",
                    "steps": [
                        f"Partial match: '{cashback_cat}' and '{prim_cat}' are related",
                        f"Score = 0.50 + {xsell:.2f}×0.20 = {sc}",
                    ],
                }
            return {
                "inputs": {
                    "Cashback category": cashback_cat,
                    "Customer primary category": prim_cat,
                    "Match": "None",
                },
                "formula": "No cashback category match → 0.20",
                "steps": [
                    f"No match: offer '{cashback_cat}' ≠ customer's '{prim_cat}'",
                    "Score = 0.20",
                ],
            }

        goal = str(customer.get("financial_goal", "")).lower()
        goal_offer_alignment = {
            "pay_off_debt":         ("balance_transfer_promo", "rate_discount", "intro_apr"),
            "home_purchase":        ("rate_lock", "fee_waiver", "rate_discount"),
            "retirement_savings":   ("cd_rate_bump", "rate_bump", "loyalty_reward"),
            "grow_wealth":          ("signup_bonus", "fee_waiver", "loyalty_reward"),
            "build_emergency_fund": ("intro_rate_boost", "rate_boost", "cd_rate_bump"),
        }
        aligned = goal_offer_alignment.get(goal, ())
        if aligned and offer_type in aligned:
            sc = round(min(1.0, 0.40 + xsell * 0.25 + 0.15), 2)
            return {
                "inputs": {
                    "Financial goal": goal,
                    "Offer type": offer_type,
                    "Aligned types": ", ".join(aligned),
                    "Cross-sell receptivity": f"{xsell:.2f}",
                },
                "formula": "Goal-aligned: score = 0.40 + xsell×0.25 + 0.15",
                "steps": [
                    f"Financial goal '{goal}' aligns with '{offer_type}'",
                    f"Score = 0.40 + {xsell:.2f}×0.25 + 0.15 = {sc}",
                ],
            }

        sc = round(0.40 + xsell * 0.25, 2)
        return {
            "inputs": {
                "Primary spend category": prim_cat or "not specified",
                "Cross-sell receptivity": f"{xsell:.2f}",
            },
            "formula": "Generic baseline: score = 0.40 + xsell×0.25",
            "steps": [
                "No lifestyle tags, cashback category, or goal alignment found",
                f"Score = 0.40 + {xsell:.2f}×0.25 = {sc}",
            ],
        }

    def _calc_life_stage(self, offer: Dict, customer: Dict) -> Dict:
        offer_type = str(offer.get("offer_type", "")).lower()
        age        = _si(customer.get("age", 40))
        life_stage = str(customer.get("life_stage", "")).lower()
        base       = _sf(offer.get("scoring_weights", {}).get("life_stage_boost", 0.3))

        if 18 <= age <= 30:
            ab = "18–30"
            if offer_type in ("signup_bonus", "intro_apr", "cashback_boost"): mult = 1.25
            elif offer_type in ("cd_rate_bump", "loyalty_reward"): mult = 0.60
            else: mult = 0.85
        elif 31 <= age <= 50:
            ab = "31–50"
            if offer_type in ("cashback_boost", "balance_transfer_promo", "signup_bonus"): mult = 1.15
            elif offer_type == "fee_waiver": mult = 1.10
            else: mult = 0.90
        elif 51 <= age <= 65:
            ab = "51–65"
            if offer_type in ("cd_rate_bump", "loyalty_reward", "fee_waiver"): mult = 1.20
            elif offer_type in ("signup_bonus", "cashback_boost"): mult = 0.85
            else: mult = 1.0
        else:
            ab = "65+"
            if offer_type in ("fee_waiver", "loyalty_reward", "cd_rate_bump"): mult = 1.25
            elif offer_type in ("intro_apr", "balance_transfer_promo"): mult = 0.75
            else: mult = 0.90

        base_mult  = mult
        adj_notes: List[str] = []
        if life_stage in ("student", "young_single") and offer_type == "intro_apr":
            mult *= 1.10
            adj_notes.append(f"Life stage '{life_stage}' + intro_apr → ×1.10")
        if life_stage in ("new_family", "growing_family") and offer_type in ("cashback_boost", "signup_bonus"):
            mult *= 1.10
            adj_notes.append(f"Life stage '{life_stage}' + {offer_type} → ×1.10")
        if life_stage in ("pre_retiree", "retiree") and offer_type == "cd_rate_bump":
            mult *= 1.15
            adj_notes.append(f"Life stage '{life_stage}' + cd_rate_bump → ×1.15")

        sc = round(min(1.0, max(0.05, base * mult + 0.20)), 2)
        steps = [
            f"Age {age} → bracket {ab} → base multiplier for '{offer_type}' = {base_mult:.2f}",
            f"Config life_stage_boost = {base:.2f}",
        ]
        if adj_notes:
            steps.extend(adj_notes)
            steps.append(f"Adjusted multiplier = {mult:.2f}")
        steps.append(f"Score = min(1.0, max(0.05, {base:.2f} × {mult:.2f} + 0.20)) = {sc}")

        return {
            "inputs": {
                "Age": age,
                "Life stage": life_stage or "not specified",
                "Offer type": offer_type,
                "Config life_stage_boost": base,
            },
            "formula": "score = min(1.0, max(0.05, life_stage_boost × age_mult + 0.20))",
            "steps": steps,
        }

    def _calc_digital(self, offer: Dict, customer: Dict) -> Dict:
        digital    = _sf(customer.get("digital_engagement_score", 0.5))
        w_boost    = _sf(offer.get("scoring_weights", {}).get("digital_boost", 0.3))
        complexity = _si(offer.get("offer_complexity", 1))

        if digital >= 0.65:
            raw    = w_boost * (0.5 + digital * 0.5)
            path   = "High digital (app-centric)"
            formula = "score = digital_boost × (0.5 + engagement×0.5)"
            steps  = [
                f"Digital engagement {digital:.2f} ≥ 0.65 → high-digital path",
                f"Score = {w_boost:.2f} × (0.5 + {digital:.2f}×0.5) = {raw:.2f}",
            ]
        elif digital < 0.35:
            simp   = 1.0 - (complexity - 1) / 3.0
            raw    = simp * 0.7 + (1 - w_boost) * 0.3
            path   = "Low digital (branch-oriented)"
            formula = "score = simplicity×0.7 + (1−digital_boost)×0.3"
            steps  = [
                f"Digital engagement {digital:.2f} < 0.35 → branch-oriented path",
                f"Simplicity bonus = 1.0 − ({complexity}−1)/3.0 = {simp:.2f}",
                f"Score = {simp:.2f}×0.70 + {(1-w_boost):.2f}×0.30 = {raw:.2f}",
            ]
        else:
            raw    = w_boost * digital + (1 - w_boost) * (1 - digital) * 0.5
            path   = "Mid digital (blended)"
            formula = "score = digital_boost×engagement + (1−boost)×(1−engagement)×0.5"
            steps  = [
                f"Digital engagement {digital:.2f} → mid-range blended path",
                f"Score = {w_boost:.2f}×{digital:.2f} + {(1-w_boost):.2f}×{(1-digital):.2f}×0.50 = {raw:.2f}",
            ]

        sc = round(min(1.0, max(0.05, raw)), 2)
        steps.append(f"Final = min(1.0, max(0.05, {raw:.2f})) = {sc}")

        return {
            "inputs": {
                "Digital engagement score": f"{digital:.2f}",
                "Offer digital_boost weight": f"{w_boost:.2f}",
                "Offer complexity": complexity,
                "Path": path,
            },
            "formula": formula,
            "steps": steps,
        }

    def _calc_urgency(
        self, offer: Dict, customer: Dict,
        churn_risk_score: float, churn_category: Optional[str],
    ) -> Dict:
        offer_type   = str(offer.get("offer_type", "")).lower()
        is_evergreen = _sb(offer.get("is_evergreen", True))
        days_left    = _days_remaining(offer.get("offer_end_date"))
        end_date     = offer.get("offer_end_date")

        retention_types = ("loyalty_reward", "fee_waiver", "cd_rate_bump", "balance_transfer_promo")
        if churn_category in ("High", "Critical"):
            if offer_type in retention_types:
                rb   = round(0.15 * (churn_risk_score / 100), 3)
                bnote = f"Retention offer for {churn_category} churn → +{rb:.3f}"
            else:
                rb   = -0.10
                bnote = f"Acquisition offer for {churn_category}-churn customer → −0.10 penalty"
        else:
            rb    = 0.0
            bnote = f"Churn: {churn_category or 'Low/None'} — no retention adjustment"

        if not is_evergreen and days_left is not None:
            if days_left <= 7:    urg, tier = 1.00, "Critical (≤7d)"
            elif days_left <= 14: urg, tier = 0.90, "Very High (≤14d)"
            elif days_left <= 30: urg, tier = 0.78, "High (≤30d)"
            elif days_left <= 60: urg, tier = 0.65, "Medium (≤60d)"
            else:                 urg, tier = 0.55, "Low (>60d)"
        else:
            urg, tier = 0.55, "None — evergreen"

        sc = round(min(1.0, max(0.0, urg + rb)), 2)
        return {
            "inputs": {
                "Offer end date": str(end_date) if end_date else "N/A (evergreen)",
                "Days remaining": days_left if days_left is not None else "N/A",
                "Is evergreen": is_evergreen,
                "Churn category": churn_category or "Low/None",
                "Churn risk score": f"{churn_risk_score:.1f}",
            },
            "formula": "score = urgency_tier_score + retention_boost",
            "steps": [
                f"Urgency tier: {tier} → {urg:.2f}",
                bnote,
                f"Score = min(1.0, max(0.0, {urg:.2f} + {rb:.2f})) = {sc}",
            ],
        }

    # ── explanation helpers ───────────────────────────────────────────────────

    def _explain_monetary(self, offer, customer, score) -> str:
        offer_type = str(offer.get("offer_type", "")).lower()
        if offer_type == "signup_bonus":
            val = offer.get("value_amount", 0)
            return f"${val} bonus vs customer income — spend attainability factored in (score {score:.0%})"
        if offer_type in ("intro_apr","balance_transfer_promo"):
            debt = _sf(customer.get("outstanding_debt_total", 0))
            return f"Interest savings on ${debt:,.0f} outstanding debt over intro period (score {score:.0%})"
        if offer_type == "cashback_boost":
            cat = offer.get("cashback_category","purchases")
            ms  = _sf(customer.get("monthly_spend_in_primary_cat", 300))
            return f"Extra cashback on {cat} vs ${ms:.0f}/mo primary spend (score {score:.0%})"
        if offer_type in ("cd_rate_bump", "rate_discount", "intro_rate_boost"):
            return f"Rate/APY improvement relative to deposit base (score {score:.0%})"
        if offer_type == "fee_waiver":
            return f"Fee eliminated for {customer.get('fee_sensitivity_tier','medium')}-sensitivity customer (score {score:.0%})"
        return f"Offer value relevance to customer profile (score {score:.0%})"

    def _explain_spending(self, offer, customer, score) -> str:
        offer_tags = offer.get('lifestyle_tags') or []
        if offer_tags:
            customer_tags = self._derive_customer_lifestyle_tags(customer)
            matched = sorted(set(offer_tags) & customer_tags)
            if matched:
                return f"Lifestyle match: customer profile ({', '.join(matched)}) aligns with offer's target audience"
            else:
                return f"Lifestyle mismatch: offer targets {offer_tags} — no overlap with customer profile"
        cat = offer.get("cashback_category") or "general"
        prim = customer.get("primary_spending_category","unknown")
        if str(cat).lower() == str(prim).lower():
            return f"Offer category '{cat}' matches customer's primary spending category '{prim}'"
        if cat != "general":
            return f"Offer targets '{cat}' but customer primarily spends on '{prim}'"
        travel = customer.get("travel_frequency","none")
        return f"Cross-sell receptivity and travel frequency ({travel}) factored in (score {score:.0%})"

    def _explain_life_stage(self, offer, customer, score) -> str:
        age = customer.get("age", 40)
        ls  = customer.get("life_stage", "unknown")
        ot  = offer.get("offer_type","")
        return f"Age {age} ({ls} stage) — {ot} offer fit for this life stage (score {score:.0%})"

    def _explain_digital(self, offer, customer, score) -> str:
        dig = _sf(customer.get("digital_engagement_score", 0.5))
        cpx = offer.get("offer_complexity", 1)
        return (f"Digital engagement {dig:.0%} vs offer complexity {cpx}/4 — "
                f"channel alignment {'strong' if score > 0.7 else 'moderate' if score > 0.4 else 'limited'}")

    def _explain_urgency(self, offer, churn_category, score) -> str:
        days = _days_remaining(offer.get("offer_end_date"))
        if churn_category in ("High","Critical"):
            return f"Retention boost applied for {churn_category} churn risk customer"
        if days is not None and days <= 30:
            return f"Time-limited offer — {days} days remaining creates urgency"
        if _sb(offer.get("is_evergreen", False)):
            return "Evergreen offer — no urgency premium, standard baseline score"
        return f"Offer timing relevance (score {score:.0%})"

    @staticmethod
    def _build_terms_summary(offer: Dict) -> str:
        parts = []
        val    = offer.get("value_amount")
        vtype  = str(offer.get("value_currency", "USD")).lower()
        spend  = offer.get("spend_requirement")
        window = offer.get("spend_window_days")
        dur    = offer.get("rate_duration_months")
        rate   = offer.get("rate_pct")
        cat    = offer.get("cashback_category")
        pct    = offer.get("cashback_pct")

        if val is not None and vtype == "usd" and val > 0:
            parts.append(f"${val:,.0f} bonus")
        if spend:
            parts.append(f"after ${spend:,.0f} spend")
        if window:
            parts.append(f"in {window} days")
        if rate == 0.0 and dur:
            parts.append(f"0% APR for {dur} months")
        elif rate and rate > 0 and dur:
            parts.append(f"{rate}% rate for {dur} months")
        elif rate and rate > 0:
            parts.append(f"{rate}% rate")
        if pct and cat:
            parts.append(f"{pct}% cash back on {cat}")
        elif pct:
            parts.append(f"{pct}% cash back")
        if val and vtype == "pct_apr_reduction":
            parts.append(f"{val}% rate reduction")
        if val and vtype == "months":
            parts.append(f"{val} months")

        return " ".join(parts) if parts else str(offer.get("headline_value", ""))

    @staticmethod
    def _runner_up_reason(runner_offer: Dict, winner_offer: Dict, runner_score: float, winner_score: float) -> str:
        gap = winner_score - runner_score
        r_type = runner_offer.get("offer_type","")
        w_type = winner_offer.get("offer_type","")
        if gap > 0.15:
            return f"Score gap {gap:.0%} — '{w_type}' offer better fit for this customer's profile"
        if r_type != w_type:
            return f"'{w_type}' offer (score {winner_score:.0%}) ranked higher than '{r_type}' (score {runner_score:.0%}) for this profile"
        return f"Similar offer type but lower overall score ({runner_score:.0%} vs {winner_score:.0%})"

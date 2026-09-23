"""
Agent C Banking - One Best Offer with Explainability + Offer Intelligence Layer
Hyper-personalized 1:1 offer for each customer with clear reasoning and cross-channel actionability.
CMO-critical: one best offer, how/why AI got there, why our approach is better.

Offer Intelligence (new): after the best product is selected, Agent C loads all active
marketing offers for that product, scores them against the customer profile via OfferScorer,
picks the single best offer, and generates personalized flyer/email/push content via Together AI.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from utils.banking_constants import DIGITAL_HIGH, DIGITAL_MED, DIGITAL_LOW
except ImportError:
    DIGITAL_HIGH, DIGITAL_MED, DIGITAL_LOW = 0.65, 0.40, 0.20

try:
    from utils.claude_client import get_claude_client
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    get_claude_client = None

from agents.agent_d_banking import AgentD_Banking

try:
    from agents.offer_scorer import OfferScorer, load_offers_registry
    OFFER_SCORER_AVAILABLE = True
except ImportError:
    try:
        from offer_scorer import OfferScorer, load_offers_registry
        OFFER_SCORER_AVAILABLE = True
    except ImportError:
        OFFER_SCORER_AVAILABLE = False
        OfferScorer = None  # type: ignore
        load_offers_registry = None  # type: ignore

try:
    from agents.conversion_lift_engine import ConversionLiftEngine
    LIFT_ENGINE_AVAILABLE = True
except ImportError:
    try:
        from conversion_lift_engine import ConversionLiftEngine
        LIFT_ENGINE_AVAILABLE = True
    except ImportError:
        LIFT_ENGINE_AVAILABLE = False
        ConversionLiftEngine = None  # type: ignore

try:
    from utils.mta_engine import get_mta_engine as _get_mta_engine
    MTA_AVAILABLE = True
except ImportError:
    MTA_AVAILABLE = False
    _get_mta_engine = None  # type: ignore

logger = logging.getLogger(__name__)


# ── financial goal hint (no LLM) ─────────────────────────────────────────────

def _derive_financial_goal_hint(metrics: Dict) -> str:
    age = int(float(metrics.get("age", 40) or 40))
    home_type = str(metrics.get("home_ownership_type", "") or "").lower()
    income = float(metrics.get("income", 40000) or 40000)
    life_event = str(metrics.get("recent_life_event", "") or "").lower()
    financial_goal = str(metrics.get("financial_goal", "") or "").lower()

    # explicit goal from customer data takes priority
    goal_map = {
        "build_emergency_fund": "building an emergency fund",
        "pay_off_debt": "paying off debt",
        "home_purchase": "homeownership planning",
        "retirement_savings": "retirement savings",
        "grow_wealth": "growing wealth",
    }
    if financial_goal in goal_map:
        return goal_map[financial_goal]

    # infer from signals
    if life_event in ("job_change", "promotion"):
        return "career growth and income management"
    if home_type == "renter" and income > 60000 and age < 45:
        return "homeownership planning"
    if age >= 58:
        return "retirement readiness and wealth preservation"
    if age < 28:
        return "building credit and early savings"
    return "growing savings and financial security"


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

    def __init__(
        self,
        exclusions_config_path: Optional[Path] = None,
        offers_config_path: Optional[str] = None,
    ):
        self.exclusions_map = _load_exclusions(exclusions_config_path)

        # Offer Intelligence Layer
        if OFFER_SCORER_AVAILABLE:
            registry = load_offers_registry(offers_config_path)
            self.offer_scorer: Optional[OfferScorer] = OfferScorer(registry)
            # Flat offer lookup: offer_id -> offer_dict (used by experiment path)
            self.offers_by_id: Dict[str, Dict] = {
                o["offer_id"]: o
                for offers_list in registry.values()
                for o in offers_list
            }
        else:
            self.offer_scorer = None
            self.offers_by_id = {}

        # Experiment-driven offer path (primary; OfferScorer is fallback)
        if LIFT_ENGINE_AVAILABLE:
            self.lift_engine: Optional[ConversionLiftEngine] = ConversionLiftEngine()
        else:
            self.lift_engine = None

    def _check_compliance_rules(self, candidate: Dict, customer_details: Dict) -> bool:
        """
        Fast Python compliance check  -  no LLM.
        Returns True if the offer is eligible, False if it must be skipped.
        """
        metrics = customer_details.get('metrics') or {}
        credit_score = float(metrics.get('credit_score', 0) or 0)
        income = float(metrics.get('income', 0) or 0)
        annual_fee = float(candidate.get('annual_fee', 0) or 0)
        monthly_fee = float(candidate.get('monthly_fee', 0) or 0)
        fee_sensitivity_tier = str(metrics.get('fee_sensitivity_tier', 'medium')).lower()
        churned = str(metrics.get('churned', '0'))
        credit_tier_required = str(candidate.get('credit_tier_required', 'any')).lower()
        customer_credit_tier = str(metrics.get('credit_tier', '')).lower()

        # Block churned customers from cross-sell (only retention products allowed)
        if churned in ('1', 'true') and str(candidate.get('category', '')).lower() in ('credit card', 'loan', 'investment'):
            return False

        # Block if product requires excellent credit and customer doesn't have it
        if credit_tier_required == 'excellent' and customer_credit_tier not in ('excellent', ''):
            return False

        # Block if total annual cost exceeds 1% of customer income (extreme fee burden)
        total_annual_cost = annual_fee + (monthly_fee * 12)
        if income > 0 and total_annual_cost > income * 0.01 and fee_sensitivity_tier == 'high':
            return False

        # Debt guard: don't push high-APR rewards/premium credit cards at heavily-indebted,
        # fee-sensitive customers  -  only balance-transfer and secured cards are appropriate
        outstanding_debt = float(metrics.get('outstanding_debt_total', 0) or 0)
        category_val = str(candidate.get('category', '')).lower()
        subcategory_val = str(candidate.get('subcategory', '')).lower()
        if outstanding_debt > 20000 and category_val == 'credit card' and fee_sensitivity_tier == 'high':
            product_name_lower = str(candidate.get('product_name', '')).lower()
            if 'balance transfer' not in product_name_lower and subcategory_val != 'secured':
                return False

        return True

    def get_one_best_offer(
        self,
        customer_id: str,
        customer_details: Dict,
        all_recommendations: Dict,
        churn_risk_score: Optional[float] = None,
        churn_category: Optional[str] = None,
        fallback_products: Optional[List[Dict]] = None,
        agent_b_reference_recs: Optional[List[Dict[str, Any]]] = None,
        transactions_df=None,
        supervisor_directives: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Select the single best offer for this customer and build explainability.
        If no candidates from recommendations, uses fallback_products when provided.

        agent_b_reference_recs: Raw rows from rule-based Agent B execute (same order as UI #1–#3).
        When set, B vs C comparison uses execute #1 vs Agent C pick  -  otherwise raw merge rank vs churn-boosted pick.

        supervisor_directives: Agent D's last_directives for this customer (same dict Agent B's
        execute() already respects). When it carries a priority_pin_product_id, that product is
        forced to be THE offer here too  -  reusing AgentD_Banking.apply_directives_to_recommendations,
        the exact same pin-forcing logic Agent B uses, so pin behavior stays identical between tabs.
        """
        import time as _time
        _offer_start = _time.monotonic()
        logger.info(
            f"[Agent C] get_one_best_offer: customer={customer_id}, persona={customer_details.get('persona')}, "
            f"churn_category={churn_category}, agent_b_candidates={len(agent_b_reference_recs) if agent_b_reference_recs else 0}"
        )
        persona_name = (customer_details.get("persona") or "Unknown").strip()
        metrics = customer_details.get("metrics") or {}
        digital = float(metrics.get("digital_engagement", 0.5))

        # Shared exclusion set
        excluded_product_ids = set()
        for product_id, excluded_personas in self.exclusions_map.items():
            if isinstance(excluded_personas, list) and persona_name in excluded_personas:
                excluded_product_ids.add(str(product_id))

        retention_categories = {"Certificate of Deposit", "Investment", "Bank Account"}
        selected_from_agent_b = False
        agent_b_product_rank = None

        # ── Primary path: use Agent B's ordered product list ─────────────────
        # Agent C's job is OFFER SELECTION, not product reselection  -  the best
        # offer must always be Agent B's #1 product (same list, same order),
        # for both per-customer and per-cluster calls. Life event / churn signals
        # are surfaced in the "why this offer" narrative below, but must NOT
        # re-rank the pool here  -  that was previously letting a boosted #2/#3
        # win over Agent B's actual #1, which is exactly the Recommender-vs-
        # Offer (and, downstream, Director) disconnect this pathway must avoid.
        # Exclusions/compliance are the only reason to skip past #1  -  a real
        # eligibility block, not a preference reordering.
        #
        # Agent B's own execute() (rule-based agent_b_banking_chromadb.py) applies
        # any Agent D supervisor directives (boost/deprioritize/pin from the
        # customer's ledger) via this exact same AgentD_Banking helper whenever
        # the Recommender tab is loaded with use_agent_d_directives  -  so Agent C
        # must apply them here too, in the same order, or a lingering boost/pin
        # from an earlier click/goal/Director run makes Recommender show one
        # product while Offer, having never looked at the ledger, shows another.
        best = None
        if agent_b_reference_recs and len(agent_b_reference_recs) > 0:
            primary_pool = [dict(r) for r in agent_b_reference_recs]
            if supervisor_directives:
                primary_pool = AgentD_Banking.apply_directives_to_recommendations(
                    primary_pool, supervisor_directives, customer_context=customer_details, persona_name=persona_name,
                )
            for rank, candidate in enumerate(primary_pool):
                pid = str(candidate.get("product_id") or "")
                if pid in excluded_product_ids:
                    continue
                if not self._check_compliance_rules(candidate, customer_details):
                    continue
                best = candidate
                agent_b_product_rank = rank + 1
                selected_from_agent_b = True
                break

        # ── Fallback: merged pool from all recommendation sources ─────────────
        # Used when Agent B list is unavailable or all products failed compliance.
        if best is None:
            tailored = all_recommendations.get("tailored_recommendations") or []
            similar = all_recommendations.get("similar_products") or []
            segment = all_recommendations.get("segment_recommendations") or []
            seen: Dict[str, Any] = {}
            for rec in tailored:
                pid = rec.get("product_id")
                if pid and pid not in seen:
                    rc = dict(rec); rc["source"] = "persona_aligned"; seen[pid] = rc
            for rec in similar:
                pid = rec.get("product_id")
                if pid and (pid not in seen or rec.get("score", 0) > seen[pid].get("score", 0)):
                    rc = dict(rec); rc["source"] = "similar_products"; seen[pid] = rc
            for rec in segment:
                pid = rec.get("product_id")
                if not pid:
                    continue
                rc = dict(rec); rc["source"] = "segment_popular"
                raw_score = rc.get("score")
                if raw_score is None:
                    pop = float(rc.get("popularity") or 0)
                    rc["score"] = round(min(0.94, max(0.18, pop * 0.75 + 0.18)), 4)
                if pid not in seen or float(rc.get("score") or 0) > float(seen[pid].get("score") or 0):
                    seen[pid] = rc
            candidates = [r for r in seen.values() if str(r.get("product_id") or "") not in excluded_product_ids]
            candidates = [c for c in candidates if self._check_compliance_rules(c, customer_details)]
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
            if candidates:
                AGENT_C_CROSS_SIGNAL_BOOST = 0.05
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
                boosted = self._apply_life_event_boost(boosted, customer_details)
                boosted.sort(key=lambda x: (-float(x.get("score") or 0), str(x.get("product_id") or "")))
                best = boosted[0]

        # ── Director pin override ──────────────────────────────────────────
        # Forces the same product Agent B would show as #1 for this customer,
        # reusing its exact pin-forcing/stub-synthesis logic so a pin can win
        # even when nothing else was eligible (best is still None here).
        if supervisor_directives and supervisor_directives.get('priority_pin_product_id'):
            pin_pool = list(agent_b_reference_recs) if agent_b_reference_recs else ([best] if best is not None else [])
            forced = AgentD_Banking.apply_directives_to_recommendations(
                pin_pool, supervisor_directives, customer_context=customer_details, persona_name=persona_name,
            )
            if forced:
                best = forced[0]
                selected_from_agent_b = False
                agent_b_product_rank = None

        if best is None:
            channels, best_channel, best_channel_reason = self._compute_channels(
                persona_name, digital, churn_category, metrics
            )
            _offer_ms = int((_time.monotonic() - _offer_start) * 1000)
            logger.info(
                f"[Agent C] No eligible offer for customer={customer_id} after exclusions/compliance "
                f"(duration={_offer_ms}ms)  -  falling back to manual review / retention outreach"
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
                "selected_from_agent_b": False,
                "agent_b_product_rank": None,
            }

        # Raw Agent B reference ranking  -  for Recommender vs Best Offer comparison panel
        b_ranked = sorted(
            [dict(r) for r in (agent_b_reference_recs or [best])],
            key=lambda x: float(x.get("score") or 0),
            reverse=True,
        )

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
        product_name = best.get("product_name") or best.get("product_id") or "this product"

        # Try Claude for LLM-generated explainability bullets (now includes full customer context)
        why_this_offer = None
        if CLAUDE_AVAILABLE and get_claude_client:
            try:
                claude = get_claude_client()
                if claude.is_available():
                    bullets = claude.generate_why_this_offer(
                        product_name=product_name,
                        persona_name=persona_name,
                        score=score_val,
                        churn_category=churn_category or "",
                        customer_context=metrics,
                    )
                    if bullets:
                        why_this_offer = "\n".join(f"• {b}" for b in bullets)
            except Exception:
                pass

        # Fallback: rule-based template
        if not why_this_offer:
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

        # ── Credit Personalization ────────────────────────────────────────────
        credit_personalization = self._generate_credit_personalization(best, customer_details)

        # ── Offer Intelligence Layer ──────────────────────────────────────────
        offer_intel_result = self._run_offer_intelligence(
            best_product=best,
            customer_details=customer_details,
            churn_risk_score=churn_risk_score or 0.0,
            churn_category=churn_category,
            persona_name=persona_name,
            best_channel=best_channel,
            transactions_df=transactions_df,
        )

        # ── Multi-Touch Attribution enrichment ───────────────────────────────
        mta_attribution: Dict[str, float] = {}
        channel_fatigue: Dict[str, Any] = {}
        persona_channel_stats: Dict[str, Any] = {}
        mta_ai_insight: Dict[str, Any] = {}
        if MTA_AVAILABLE and _get_mta_engine is not None:
            try:
                _mta = _get_mta_engine()
                product_id_for_mta = str(best.get("product_id") or "")
                mta_attribution    = _mta.compute_markov_attribution(
                    persona=persona_name, product_id=product_id_for_mta
                )
                channel_fatigue    = _mta.get_customer_channel_fatigue(customer_id)
                persona_channel_stats = _mta.get_persona_channel_stats(persona_name)
                _exp_data          = (
                    (offer_intel_result.get("offer_intelligence") or {})
                    .get("experiment_data") or {}
                )
                dig_score = float(metrics.get("digital_engagement_score", 0) or 0)
                mta_ai_insight = _mta.generate_channel_insight(
                    customer_id=customer_id,
                    best_channel=best_channel,
                    mta_attribution=mta_attribution,
                    fatigue=channel_fatigue,
                    persona_stats=persona_channel_stats,
                    persona_name=persona_name,
                    experiment_id=_exp_data.get("experiment_id"),
                    p_value=_exp_data.get("p_value"),
                    digital_score=dig_score,
                )
                # Annotate each channel entry with its fatigue status
                for ch_entry in channels:
                    ch_entry["is_fatigued"] = channel_fatigue.get(
                        ch_entry.get("channel", ""), {}
                    ).get("is_fatigued", False)
            except Exception as _mta_err:
                logger.warning("MTA enrichment failed: %s", _mta_err)

        # ── MTA Two-Tier Channel Override (personal signal > segment signal) ────
        # If customer has >= 3 sends with any engagement, use their personal
        # click/open rates to select the channel  -  not segment-level Markov.
        # Segment attribution is only the fallback when personal data is thin.
        mta_channel_recommendation: Dict[str, Any] = {}
        if MTA_AVAILABLE and _get_mta_engine is not None:
            try:
                _mta = _get_mta_engine()
                mta_channel_recommendation = _mta.get_customer_channel_recommendation(
                    customer_id, persona=persona_name
                )
                if (
                    mta_channel_recommendation.get("signal_source") == "personal"
                    and mta_channel_recommendation.get("recommended_channel")
                    and mta_channel_recommendation["recommended_channel"] != best_channel
                ):
                    override_ch = mta_channel_recommendation["recommended_channel"]
                    best_channel = override_ch
                    best_channel_reason = mta_channel_recommendation.get(
                        "reason", best_channel_reason
                    )
                    # Move overridden channel to front of priority list
                    channels.sort(
                        key=lambda c: (0 if c.get("channel") == override_ch else 1)
                    )
                    # Always regenerate AI insight to match the new best_channel,
                    # using whatever partial data is available (both may be partial).
                    if True:
                        _exp_data_rec = (
                            (offer_intel_result.get("offer_intelligence") or {})
                            .get("experiment_data") or {}
                        )
                        _dig_score_rec = float(
                            metrics.get("digital_engagement_score", 0) or 0
                        )
                        try:
                            mta_ai_insight = _mta.generate_channel_insight(
                                customer_id=customer_id,
                                best_channel=best_channel,
                                mta_attribution=mta_attribution,
                                fatigue=channel_fatigue,
                                persona_stats=persona_channel_stats,
                                persona_name=persona_name,
                                experiment_id=_exp_data_rec.get("experiment_id"),
                                p_value=_exp_data_rec.get("p_value"),
                                digital_score=_dig_score_rec,
                            )
                        except Exception:
                            pass
            except Exception as _mta_rec_err:
                logger.warning("MTA channel recommendation failed: %s", _mta_rec_err)

        # ── Agentic Customer Analysis (full LLM deep-dive using all 52+ fields) ──
        customer_analysis: Dict[str, Any] = {}
        try:
            api_key = os.getenv("TOGETHER_API_KEY", "").strip()
            if api_key:
                from utils.together_ai import together_ai as _tai
                _selected_offer = (
                    (offer_intel_result.get("offer_intelligence") or {}).get("selected_offer")
                )
                customer_analysis = _tai.generate_complete_customer_analysis(
                    customer=metrics,
                    recommended_product=best,
                    selected_offer=_selected_offer,
                    persona_name=persona_name,
                    churn_category=churn_category or "",
                )
        except Exception as _e:
            logger.warning("Agentic analysis failed: %s", _e)

        _offer_ms = int((_time.monotonic() - _offer_start) * 1000)
        logger.info(
            f"[Agent C] Best offer selected for customer={customer_id}: product={best.get('product_id')} "
            f"({product_name}), score={score_val:.3f}, source={source}, "
            f"selected_from_agent_b={selected_from_agent_b} (duration={_offer_ms}ms)"
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
                "supervisor_pinned": bool(best.get("supervisor_pinned")),
                "priority_pin_reason": best.get("priority_pin_reason"),
            },
            "supervisor_pinned": bool(best.get("supervisor_pinned")),
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
            # Offer Intelligence
            "offer_intelligence": offer_intel_result.get("offer_intelligence", {"available": False}),
            "personalized_communication": offer_intel_result.get("personalized_communication"),
            # Credit Personalization
            "credit_personalization": credit_personalization,
            # Agentic Analysis  -  LLM deep-dive across all 52+ customer signals
            "customer_analysis": customer_analysis if customer_analysis else None,
            # Provenance  -  did Agent C anchor on Agent B's product choice?
            "selected_from_agent_b": selected_from_agent_b,
            "agent_b_product_rank": agent_b_product_rank,
            # Multi-Touch Attribution
            "mta_attribution": mta_attribution,
            "channel_fatigue": channel_fatigue,
            "persona_channel_stats": persona_channel_stats,
            "mta_ai_insight": mta_ai_insight,
            "mta_channel_recommendation": mta_channel_recommendation,
        }

    # ── Credit Personalization Methods ───────────────────────────────────────

    def _generate_credit_personalization(
        self,
        best_product: Dict,
        customer_details: Dict,
    ) -> Optional[Dict[str, Any]]:
        """
        Compute product-specific personalized offer data for credit cards and loans.
        Shows the customer their personal rate, projected rewards value, and approval confidence.
        Returns None for non-credit/loan products.
        """
        subcategory = str(best_product.get("subcategory") or "").lower()
        metrics = customer_details.get("metrics") or {}

        credit_score   = float(metrics.get("credit_score", 700) or 700)
        income         = float(metrics.get("income", 50000) or 50000)
        monthly_spend  = float(metrics.get("monthly_spend_in_primary_cat", 300) or 300)
        outstanding_debt = float(metrics.get("outstanding_debt_total", 0) or 0)
        total_deposits = float(metrics.get("total_deposits", 10000) or 10000)

        category_type = str(best_product.get("category") or "").lower()
        if category_type == "credit card":
            return self._credit_card_personalization(
                best_product, credit_score, income, monthly_spend, outstanding_debt
            )
        if category_type == "mortgage" or subcategory in ("home equity",):
            return self._mortgage_personalization(best_product, credit_score, income, total_deposits)
        if category_type == "loan":
            return self._loan_personalization(best_product, credit_score, income)
        return None

    def _credit_card_personalization(
        self,
        product: Dict,
        credit_score: float,
        income: float,
        monthly_spend: float,
        outstanding_debt: float,
    ) -> Optional[Dict[str, Any]]:
        min_credit = float(product.get("min_credit_score", 670) or 670)
        if credit_score < min_credit:
            return None

        regular_apr = float(product.get("regular_apr_pct") or 22.99)
        if credit_score >= 740:
            pre_approval_tier  = "excellent"
            approval_confidence = "Pre-approved  -  excellent credit"
            apr = float(product.get("rate_tier_excellent") or regular_apr)
        elif credit_score >= 700:
            pre_approval_tier  = "good"
            approval_confidence = "Likely approved  -  strong credit"
            apr = float(product.get("rate_tier_good") or regular_apr)
        elif credit_score >= 670:
            pre_approval_tier  = "fair"
            approval_confidence = "Conditionally approved  -  good credit"
            apr = regular_apr
        else:
            pre_approval_tier  = "fair_borderline"
            approval_confidence = "Review required  -  borderline qualification"
            apr = regular_apr

        cash_back_pct  = float(product.get("cash_back_pct") or 1.5)
        annual_fee     = float(product.get("annual_fee") or 0)
        intro_months   = int(product.get("intro_apr_months") or 0)

        projected_annual_rewards = monthly_spend * (cash_back_pct / 100) * 12
        net_annual_value = projected_annual_rewards - annual_fee

        balance_transfer_savings = None
        if intro_months > 0 and outstanding_debt > 1000:
            avg_competitor_apr = 22.0
            monthly_rate = avg_competitor_apr / 100 / 12
            interest_saved = outstanding_debt * monthly_rate * intro_months
            balance_transfer_savings = round(interest_saved, 2)

        pitch_parts = [
            f"Your {int(credit_score)} credit score qualifies you for {apr:.2f}% APR ({approval_confidence.lower()})."
        ]
        if net_annual_value > 0:
            pitch_parts.append(
                f"Based on your spending, you'd earn ~${projected_annual_rewards:.0f}/yr in rewards"
                f"  -  ${net_annual_value:.0f} net after the ${annual_fee:.0f} annual fee."
            )
        if balance_transfer_savings and balance_transfer_savings > 100:
            pitch_parts.append(
                f"Transfer your ${outstanding_debt:,.0f} in existing debt and avoid ~${balance_transfer_savings:,.0f}"
                f" in interest over the {intro_months}-month 0% intro period."
            )

        return {
            "product_type": "credit_card",
            "pre_approval_tier": pre_approval_tier,
            "approval_confidence": approval_confidence,
            "personalized_apr": round(apr, 2),
            "projected_annual_rewards_value": round(projected_annual_rewards, 2),
            "annual_fee": annual_fee,
            "net_annual_value": round(net_annual_value, 2),
            "balance_transfer_savings": balance_transfer_savings,
            "intro_apr_months": intro_months,
            "personalized_pitch": " ".join(pitch_parts),
        }

    def _mortgage_personalization(
        self,
        product: Dict,
        credit_score: float,
        income: float,
        total_deposits: float,
    ) -> Dict[str, Any]:
        import math as _math
        income = float(income) if income and not _math.isnan(float(income)) else 0.0
        if income <= 0:
            income = 50_000  # safe fallback  -  no NaN in downstream calculations
        if credit_score >= 740:
            rate = float(product.get("rate_tier_excellent") or product.get("interest_rate") or 6.75)
            tier = "excellent"
        elif credit_score >= 700:
            rate = float(product.get("rate_tier_good") or product.get("interest_rate") or 7.0)
            tier = "good"
        else:
            rate = float(product.get("rate_tier_fair") or product.get("interest_rate") or 7.25)
            tier = "fair"

        product_name = str(product.get("product_name") or "").lower()
        n_months = 180 if "15" in product_name else 360

        # 28% front-end DTI limit
        max_monthly_payment = (income / 12) * 0.28
        monthly_rate = rate / 100 / 12
        if monthly_rate > 0:
            factor = ((1 + monthly_rate) ** n_months - 1) / (monthly_rate * (1 + monthly_rate) ** n_months)
            max_loan = round((max_monthly_payment * factor) / 1000) * 1000
        else:
            max_loan = round((max_monthly_payment * n_months) / 1000) * 1000

        sample_loan = min(max_loan * 0.80, 500_000)
        if monthly_rate > 0:
            monthly_payment = sample_loan * (monthly_rate * (1 + monthly_rate) ** n_months) / ((1 + monthly_rate) ** n_months - 1)
        else:
            monthly_payment = sample_loan / n_months

        pitch = (
            f"Your credit profile qualifies you for our {tier} rate of {rate:.2f}% APR. "
            f"Based on your income, you may qualify for up to ${max_loan:,.0f}. "
            f"Estimated payment: ${monthly_payment:,.0f}/mo on a ${sample_loan:,.0f} loan."
        )

        return {
            "product_type": "mortgage",
            "credit_tier": tier,
            "personalized_rate": round(rate, 3),
            "max_loan_estimate": int(max_loan),
            "sample_loan_amount": int(sample_loan),
            "estimated_monthly_payment": round(monthly_payment, 2),
            "loan_term_months": n_months,
            "personalized_pitch": pitch,
        }

    def _loan_personalization(
        self,
        product: Dict,
        credit_score: float,
        income: float,
    ) -> Dict[str, Any]:
        subcategory = str(product.get("subcategory") or "").lower()

        if credit_score >= 740:
            rate = float(product.get("rate_tier_excellent") or product.get("interest_rate") or 8.99)
            tier = "excellent"
        elif credit_score >= 700:
            rate = float(product.get("rate_tier_good") or product.get("interest_rate") or 12.99)
            tier = "good"
        else:
            rate = float(product.get("rate_tier_fair") or product.get("interest_rate") or 18.99)
            tier = "fair"

        if subcategory == "auto":
            max_loan  = round(min(income * 0.18, 60_000) / 500) * 500
            n_months  = 60
        else:
            max_loan  = round(min(income * 0.30, 50_000) / 500) * 500
            n_months  = 48

        monthly_rate = rate / 100 / 12
        if monthly_rate > 0:
            monthly_payment = max_loan * (monthly_rate * (1 + monthly_rate) ** n_months) / ((1 + monthly_rate) ** n_months - 1)
        else:
            monthly_payment = max_loan / n_months

        pitch = (
            f"Your credit profile qualifies you for our {tier} rate of {rate:.2f}% APR. "
            f"You may qualify for up to ${max_loan:,.0f}. "
            f"Estimated payment: ${monthly_payment:,.0f}/mo over {n_months // 12} years."
        )

        return {
            "product_type": subcategory,
            "credit_tier": tier,
            "personalized_rate": round(rate, 3),
            "max_loan_estimate": int(max_loan),
            "loan_term_months": n_months,
            "estimated_monthly_payment": round(monthly_payment, 2),
            "personalized_pitch": pitch,
        }

    # ── Offer Intelligence Methods ────────────────────────────────────────────

    def _owned_subcategories(self, customer_id: str, transactions_df) -> Optional[List[str]]:
        """Return subcategories the customer has transacted against, or None when data is unavailable.
        None = unknown (skip eligibility checks that require this); [] = confirmed empty."""
        if transactions_df is None:
            return None
        try:
            import pandas as pd
            cust_txns = transactions_df[transactions_df["customer_id"] == customer_id]
            if cust_txns.empty:
                return None
            if "subcategory" in cust_txns.columns:
                return list(cust_txns["subcategory"].dropna().unique())
        except Exception:
            pass
        return None

    def _build_offer_intel_from_experiment(
        self,
        offer_obj: Dict,
        exp_result: Dict,
        customer_details: Dict,
        persona_name: str,
    ) -> Dict[str, Any]:
        """Build offer intelligence dict from a ConversionLiftEngine result."""
        # Determine winning variant_id for reference
        winning_offer_id = exp_result.get("offer_id", "")
        winning_variant_id = next(
            (v["variant_id"] for v in exp_result.get("all_variants", []) if v.get("offer_id") == winning_offer_id),
            "A",
        )

        persona_offer_reason = self._build_persona_offer_reason(
            offer_result={"selected_offer": offer_obj, "offer_score": exp_result.get("lift_abs", 0), "offer_score_breakdown": {}},
            customer_details=customer_details,
            persona_name=persona_name,
        )

        runner_ups = [
            v for v in exp_result.get("all_variants", [])
            if v.get("offer_id") != winning_offer_id and v.get("is_significant", False)
        ]

        return {
            "available": True,
            "selected_offer": offer_obj,
            "offer_score": round(exp_result.get("lift_abs", 0.0), 4),
            "offer_score_breakdown": {},
            "runner_up_offers": runner_ups,
            "selection_method": "experiment_lift",
            "persona_offer_reason": persona_offer_reason,
            "persona_match": exp_result.get("persona_match", "exact"),
            "experiment_data": {
                "experiment_id": exp_result.get("experiment_id", ""),
                "holdout_conversion_rate": exp_result.get("holdout_conversion_rate", 0),
                "winning_conversion_rate": exp_result.get("winning_conversion_rate", 0),
                "lift_abs": exp_result.get("lift_abs", 0),
                "lift_pct": exp_result.get("lift_pct", 0),
                "p_value": exp_result.get("p_value", 1.0),
                "z_stat": exp_result.get("z_stat", 0.0),
                "no_offer_recommended": False,
                "winning_variant_id": winning_variant_id,
                "all_variants": exp_result.get("all_variants", []),
            },
            "channel_attribution": exp_result.get("channel_attribution", {}),
        }

    def _build_persona_offer_reason(
        self,
        offer_result: Dict,
        customer_details: Dict,
        persona_name: str,
    ) -> str:
        """
        Builds a human-readable, persona-specific explanation for why this offer
        was selected for this customer  -  e.g.:
        "For Retiree Depositor (age 68, retiree, goal: retirement savings):
         '5.00% APY Intro Rate' selected because lifestyle profile
         [retirement_focused, retirement_saver] aligns with this offer's target audience."
        """
        metrics       = (customer_details or {}).get("metrics") or {}
        age           = int(float(metrics.get("age", 0) or 0))
        life_stage    = str(metrics.get("life_stage", "") or "").replace("_", " ")
        financial_goal = str(metrics.get("financial_goal", "") or "").replace("_", " ")
        offer         = (offer_result.get("selected_offer") or {})
        offer_name    = str(offer.get("offer_name") or offer.get("offer_id") or "this offer")
        breakdown     = offer_result.get("offer_score_breakdown") or {}
        spend_exp     = (breakdown.get("spending_behavior_match") or {}).get("explanation", "")

        # Build customer context string
        ctx_parts = []
        if age:
            ctx_parts.append(f"age {age}")
        if life_stage:
            ctx_parts.append(life_stage)
        if financial_goal:
            ctx_parts.append(f"goal: {financial_goal}")
        ctx = ", ".join(ctx_parts) if ctx_parts else "customer profile"

        # Use spending_behavior explanation only when it is a positive match signal.
        # Never surface "mismatch" language in a customer-facing reason field.
        ls_exp = (breakdown.get("life_stage_fit") or {}).get("explanation", "")
        if spend_exp and "mismatch" not in spend_exp.lower():
            reason_suffix = spend_exp
        elif ls_exp and "mismatch" not in ls_exp.lower():
            reason_suffix = ls_exp
        else:
            # Generic positive fallback based on offer type
            offer_type = str((offer.get("offer_type") or "")).replace("_", " ")
            if offer_type:
                reason_suffix = f"best {offer_type} available for your profile and financial goals"
            else:
                reason_suffix = "best available offer matching your financial profile and life stage"

        return (
            f"For {persona_name} ({ctx}): "
            f"'{offer_name}' selected because {reason_suffix}."
        )

    def _run_offer_intelligence(
        self,
        best_product: Dict,
        customer_details: Dict,
        churn_risk_score: float,
        churn_category: Optional[str],
        persona_name: str,
        best_channel: str,
        transactions_df=None,
    ) -> Dict[str, Any]:
        """
        Sub-step 2 of Agent C: given the selected best product, find the best
        active marketing offer for this customer and generate personalized content.
        Returns dict with keys 'offer_intelligence' and 'personalized_communication'.
        """
        product_id       = str((best_product or {}).get("product_id") or "")
        customer_details = customer_details or {}
        metrics          = customer_details.get("metrics") or {}
        customer_id      = str(customer_details.get("customer_id", ""))

        # ── Experiment-driven path (primary) ─────────────────────────────────
        if self.lift_engine:
            exp_result = self.lift_engine.get_best_offer(product_id, persona_name)
            if exp_result.get("found"):
                if exp_result.get("no_offer_recommended"):
                    return {
                        "offer_intelligence": {
                            "available": False,
                            "reason": "no_significant_lift",
                            "selection_method": "experiment_lift",
                            "experiment_data": {
                                "experiment_id": exp_result.get("experiment_id", ""),
                                "holdout_conversion_rate": exp_result.get("holdout_conversion_rate", 0),
                                "no_offer_recommended": True,
                                "all_variants": exp_result.get("all_variants", []),
                                "channel_attribution": exp_result.get("channel_attribution", {}),
                            },
                        },
                        "personalized_communication": None,
                    }
                offer_obj = self.offers_by_id.get(exp_result.get("offer_id", ""), {})
                if offer_obj:
                    offer_intel = self._build_offer_intel_from_experiment(
                        offer_obj=offer_obj,
                        exp_result=exp_result,
                        customer_details=customer_details,
                        persona_name=persona_name,
                    )
                    comm_content = self._generate_offer_content(
                        offer=offer_obj,
                        product=best_product,
                        customer_details=customer_details,
                        persona_name=persona_name,
                        best_channel=exp_result.get("channel") or best_channel,
                    )
                    logger.info(
                        f"[AGENT-C] EXPERIMENT PATH | cust={customer_id} | "
                        f"persona={persona_name} | product={product_id} | "
                        f"offer={exp_result.get('offer_id')} | "
                        f"p={exp_result.get('p_value'):.4f} | "
                        f"lift={exp_result.get('lift_pct'):.1f}%"
                    )
                    return {
                        "offer_intelligence": offer_intel,
                        "personalized_communication": comm_content,
                    }

        # ── Formula-based fallback (OfferScorer) ─────────────────────────────
        if not self.offer_scorer:
            return {
                "offer_intelligence": {"available": False, "reason": "Offer scorer not available"},
                "personalized_communication": None,
            }

        owned_subs  = self._owned_subcategories(customer_id, transactions_df)

        # Flatten metrics for OfferScorer (it reads top-level fields)
        flat_customer = dict(metrics)
        flat_customer["customer_id"] = customer_id

        offer_result = self.offer_scorer.select_best_offer(
            product_id=product_id,
            customer=flat_customer,
            churn_risk_score=churn_risk_score,
            churn_category=churn_category,
            owned_subcategories=owned_subs,
            persona=persona_name,
        )
        # selection_method is now set inside select_best_offer; keep for safety
        offer_result.setdefault("selection_method", "formula_score")

        if not offer_result.get("available"):
            logger.info(
                f"[AGENT-C] OFFER INTELLIGENCE | cust={customer_id} | "
                f"persona={persona_name} | product={product_id} → no eligible offer"
            )
            return {
                "offer_intelligence": offer_result,
                "personalized_communication": None,
            }

        # Build persona-specific reason and inject into offer_result
        persona_offer_reason = self._build_persona_offer_reason(
            offer_result=offer_result,
            customer_details=customer_details,
            persona_name=persona_name,
        )
        offer_result["persona_offer_reason"] = persona_offer_reason

        # ── Agent C offer intelligence log ───────────────────────────────────
        selected_offer  = offer_result.get("selected_offer") or {}
        breakdown       = offer_result.get("offer_score_breakdown") or {}
        best_score      = offer_result.get("offer_score", 0)
        prod_name       = str((best_product or {}).get("product_name") or product_id)
        spend_exp       = (breakdown.get("spending_behavior_match") or {}).get("explanation", "")
        ls_exp          = (breakdown.get("life_stage_fit") or {}).get("explanation", "")
        SEP = "=" * 72
        logger.info(f"[AGENT-C] {SEP}")
        logger.info(
            f"[AGENT-C] OFFER INTELLIGENCE | "
            f"Customer: {customer_id} | Persona: {persona_name}"
        )
        logger.info(f"[AGENT-C]   Product   : {product_id} ({prod_name})")
        logger.info(
            f"[AGENT-C]   ✅ SELECTED: {selected_offer.get('offer_id')} "
            f"'{selected_offer.get('offer_name')}' (score: {best_score:.4f})"
        )
        if spend_exp:
            logger.info(f"[AGENT-C]   💡 Behavior: {spend_exp}")
        if ls_exp:
            logger.info(f"[AGENT-C]   🧬 LifeStage: {ls_exp}")
        if persona_offer_reason:
            logger.info(f"[AGENT-C]   📢 Reason   : {persona_offer_reason}")
        runner_ups = offer_result.get("runner_up_offers") or []
        for ru in runner_ups:
            logger.info(
                f"[AGENT-C]   🥈 runner-up: {ru.get('offer_id')} "
                f"'{ru.get('offer_name')}' ({ru.get('offer_score', 0):.4f}) "
                f" -  {ru.get('reason_not_selected', '')}"
            )
        logger.info(f"[AGENT-C] {SEP}")
        # ─────────────────────────────────────────────────────────────────────

        # Generate personalized communication content
        comm_content    = self._generate_offer_content(
            offer=selected_offer,
            product=best_product,
            customer_details=customer_details,
            persona_name=persona_name,
            best_channel=best_channel,
        )

        return {
            "offer_intelligence": offer_result,
            "personalized_communication": comm_content,
        }

    def _generate_offer_content(
        self,
        offer: Dict,
        product: Dict,
        customer_details: Dict,
        persona_name: str,
        best_channel: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Calls Together AI to generate flyer/email/push content.
        Falls back to template if LLM unavailable or fails.
        """
        metrics = customer_details.get("metrics") or {}
        age     = int(float(metrics.get("age", 40) or 40))
        income  = float(metrics.get("income", 40000) or 40000)
        income_tier = (
            "high income" if income >= 100000
            else "mid income" if income >= 50000
            else "moderate income"
        )
        credit_tier = str(metrics.get("credit_tier", "good") or "good")
        goal_hint   = _derive_financial_goal_hint(metrics)
        product_name  = str(product.get("product_name") or product.get("product_id") or "this product")
        subcategory   = str(product.get("subcategory") or product.get("category") or "Banking")
        offer_id      = str(offer.get("offer_id") or "")
        offer_name    = str(offer.get("offer_name") or "")
        terms_summary = str(offer.get("terms_summary") or offer.get("headline_value") or "")
        value_proposition = str(
            offer.get("content_how_to_earn") or offer.get("headline_value") or ""
        )

        # Determine recommended_format from best_channel
        channel_format_map = {
            "in_app": "push_notification",
            "web": "flyer_content",
            "email": "email_content",
            "branch": "flyer_content",
            "direct_mail": "flyer_content",
            "outbound_call": "email_content",
        }
        recommended_format = channel_format_map.get(best_channel, "email_content")

        # Try Together AI
        llm_content = None
        try:
            api_key = os.getenv("TOGETHER_API_KEY", "").strip()
            if api_key:
                from utils.together_ai import together_ai
                llm_content = together_ai.generate_offer_communication_content(
                    customer_profile={
                        "age": age,
                        "income_tier": income_tier,
                        "credit_tier": credit_tier,
                        "persona_name": persona_name,
                        "financial_goal_hint": goal_hint,
                    },
                    product={"product_name": product_name, "subcategory": subcategory},
                    offer={
                        "offer_name": offer_name,
                        "terms_summary": terms_summary,
                        "value_proposition": value_proposition,
                    },
                    best_channel=best_channel,
                )
        except Exception as e:
            logger.warning(f"Offer communication LLM call failed: {e}")

        if llm_content:
            llm_content["offer_id"]           = offer_id
            llm_content["product_name"]       = product_name
            llm_content["persona_name"]       = persona_name
            llm_content["recommended_format"] = recommended_format
            llm_content["financial_goal_hint"]= goal_hint
            return llm_content

        # Template fallback
        hero     = str(offer.get("content_hero_stat") or terms_summary or offer_name)
        how_earn = str(offer.get("content_how_to_earn") or value_proposition)
        b1 = str(offer.get("content_benefit_1") or "")
        b2 = str(offer.get("content_benefit_2") or "")
        b3 = str(offer.get("content_benefit_3") or "")
        benefits_txt = "\n".join(f"• {b}" for b in [b1, b2, b3] if b)

        flyer_headline = f"Your {offer_name}  -  available now"
        flyer_body     = (
            f"Focused on {goal_hint}? The {product_name} with our {offer_name} "
            f"is designed for you. {how_earn}"
        )
        email_subject  = f"A personalized offer on {product_name}"
        email_body     = (
            f"We know you're focused on {goal_hint}. That's why we selected the "
            f"{product_name} with our {offer_name} just for you.\n\n"
            f"{how_earn}\n\n"
            f"Key benefits:\n{benefits_txt}\n\n"
            f"Ready to get started? Visit your nearest branch or apply online today."
        )
        push_notification = f"{hero[:47]}…" if len(hero) > 47 else hero
        bank_name = os.getenv("BANK_NAME", "Your Bank")
        sms_text = (
            f"{bank_name}: {offer_name} on {product_name}. "
            f"{terms_summary[:80]}. Reply STOP to opt out."
        )

        return {
            "offer_id": offer_id,
            "product_name": product_name,
            "persona_name": persona_name,
            "recommended_format": recommended_format,
            "financial_goal_hint": goal_hint,
            "flyer_content": {"headline": flyer_headline, "body": flyer_body},
            "email_content": {"subject": email_subject, "body": email_body},
            "push_notification": push_notification,
            "sms_text": sms_text,
            "generation_source": "template",
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
                f"leads with a product that protects the relationship - not only the highest raw fit score."
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

    # ── Life Event Boost ─────────────────────────────────────────────────────

    _LIFE_EVENT_PRODUCT_MAP: Dict[str, List[str]] = {
        "Job_Change":  ["Checking", "Bank Account", "Savings"],
        "Marriage":    ["Savings", "Mortgage", "Bank Account", "Joint"],
        "Divorce":     ["Checking", "Personal Loan", "Bank Account"],
        "Relocation":  ["Checking", "Mortgage", "Bank Account", "Savings"],
        "Retirement":  ["CD", "Investment", "Wealth Management", "Certificate of Deposit"],
    }
    _LIFE_EVENT_BOOST = 0.10

    def _apply_life_event_boost(
        self,
        candidates: List[Dict[str, Any]],
        customer_details: Dict,
    ) -> List[Dict[str, Any]]:
        """Boost products aligned with the customer's recent life event."""
        metrics = customer_details.get("metrics") or {}
        life_event = str(metrics.get("recent_life_event") or "").strip()
        if not life_event or life_event.lower() in ("", "none", "null"):
            return candidates
        target_subcategories = self._LIFE_EVENT_PRODUCT_MAP.get(life_event, [])
        if not target_subcategories:
            return candidates
        boosted = []
        for c in candidates:
            cc = dict(c)
            cat = str(cc.get("category") or "")
            sub = str(cc.get("subcategory") or "")
            name = str(cc.get("product_name") or "")
            if any(t.lower() in cat.lower() or t.lower() in sub.lower() or t.lower() in name.lower()
                   for t in target_subcategories):
                cc["score"] = float(cc.get("score") or 0) + self._LIFE_EVENT_BOOST
                existing_reason = str(cc.get("reasoning") or "")
                life_note = f"Boosted for recent {life_event.replace('_', ' ')}: well-suited for this life stage."
                cc["reasoning"] = f"{existing_reason} {life_note}".strip() if existing_reason else life_note
            boosted.append(cc)
        return boosted

    def _compute_channels(
        self,
        persona_name: str,
        digital: float,
        churn_category: Optional[str],
        metrics: Dict,
    ):
        """Compute channel order and best channel.
        Uses channel_preference (Digital/Branch/Hybrid) as primary signal;
        falls back to digital engagement score for Hybrid/missing.
        High churn always overrides to outbound first."""
        persona_lower = (persona_name or "").lower()
        is_traditional = "traditional" in persona_lower or "branch" in persona_lower
        is_high_churn = churn_category in ("High", "Critical")
        channel_pref = str(metrics.get("channel_preference") or "Hybrid").strip()

        if is_high_churn:
            channels = [
                {"channel": "outbound_call", "priority": 1, "label": "Outbound call"},
                {"channel": "branch", "priority": 2, "label": "Branch"},
                {"channel": "email", "priority": 3, "label": "Email"},
            ]
            best_channel = "outbound_call"
            best_channel_reason = f"High churn risk ({churn_category}); personal outreach converts best."
        elif channel_pref == "Digital":
            channels = [
                {"channel": "in_app", "priority": 1, "label": "In-app"},
                {"channel": "email", "priority": 2, "label": "Email"},
                {"channel": "web", "priority": 3, "label": "Web"},
            ]
            best_channel = "in_app"
            best_channel_reason = "Customer channel preference: Digital  -  in-app is their primary touchpoint."
        elif channel_pref == "Branch" or is_traditional:
            channels = [
                {"channel": "branch", "priority": 1, "label": "Branch"},
                {"channel": "direct_mail", "priority": 2, "label": "Direct mail"},
                {"channel": "email", "priority": 3, "label": "Email"},
            ]
            best_channel = "branch"
            best_channel_reason = "Customer channel preference: Branch  -  in-person interaction preferred."
        elif digital >= DIGITAL_HIGH:
            channels = [
                {"channel": "in_app", "priority": 1, "label": "In-app"},
                {"channel": "email", "priority": 2, "label": "Email"},
                {"channel": "web", "priority": 3, "label": "Web"},
            ]
            best_channel = "in_app"
            pct = int(digital * 100)
            best_channel_reason = f"Hybrid preference with high digital engagement ({pct}%); in-app recommended."
        elif digital >= DIGITAL_MED:
            channels = [
                {"channel": "email", "priority": 1, "label": "Email"},
                {"channel": "web", "priority": 2, "label": "Web"},
                {"channel": "branch", "priority": 3, "label": "Branch"},
            ]
            best_channel = "email"
            pct = int(digital * 100)
            best_channel_reason = f"Hybrid preference, moderate digital ({pct}%); email has highest open rates."
        else:
            channels = [
                {"channel": "branch", "priority": 1, "label": "Branch"},
                {"channel": "email", "priority": 2, "label": "Email"},
                {"channel": "direct_mail", "priority": 3, "label": "Direct mail"},
            ]
            best_channel = "branch"
            best_channel_reason = "Hybrid preference with lower digital usage; branch or direct mail performs better."

        return channels, best_channel, best_channel_reason

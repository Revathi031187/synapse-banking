"""
Banking 12-Factor Scoring System for Product Recommendations
Adapted from enhanced_12_factor_scorer.py with banking-specific factors

Key differences from retail scoring:
- Eligibility (credit, income, balance) replaces price alignment
- Financial need matching replaces category match
- Relationship depth replaces brand loyalty
- Product pairing (banking cross-sell) replaces co-occurrence
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class Banking12FactorScorer:
    """
    Banking-specific 12-factor scoring system with:
    - Eligibility checks (credit score, income, balance requirements)
    - Financial need matching (age, deposits, income-based products)
    - Relationship depth scoring (tenure, product count)
    - Product pairing affinity (complementary banking products)
    """
    
    # BANKING-SPECIFIC 12-FACTOR WEIGHTS (Total = 100%)
    WEIGHTS = {
        # TIER 1: Eligibility & Core Match (53%)
        'eligibility_score': 0.22,      # Credit score + income + balance requirements
        'financial_need_match': 0.18,   # Product matches customer's financial situation
        'relationship_depth': 0.13,     # Tenure, product count, loyalty (reduced: short tenures common)

        # TIER 2: Strategic Fit & Product Value (31%)
        'product_value': 0.13,          # Product fees, rates, min balance, ROI (increased: key differentiator)
        'product_pairing': 0.10,        # Cross-sell affinity, complementary products (increased: strong banking signal)
        'channel_fit': 0.04,            # Digital vs branch alignment (reduced: Meridian is hybrid bank)

        # TIER 3: Behavioral & Contextual (13%)
        'complexity_match': 0.04,       # Product sophistication vs customer level
        'intent_score': 0.06,           # Cross-sell receptivity — directly measured, strong conversion signal
        'segment_affinity': 0.02,       # Peer behavior in segment
        'transaction_pattern': 0.01,    # Activity level derived from monthly_transaction_volume

        # TIER 4: Quality Signals (7%)
        'product_rating': 0.04,         # Product satisfaction score
        'popularity': 0.03,             # Adoption rate in segment
    }
    
    def __init__(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
        personas: Dict = None
    ):
        self.customers_df = customers_df
        self.products_df = products_df
        self.transactions_df = transactions_df
        self.personas = personas or {}
        
        # Pre-compute statistics for faster scoring
        self._precompute_statistics()
        
        # Verify weights sum to 1.0
        total_weight = sum(self.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.001, f"Weights must sum to 1.0, got {total_weight}"
        logger.info(f"✅ Banking 12-Factor Scorer initialized (weights sum to {total_weight:.3f})")
    
    def _precompute_statistics(self):
        """Pre-compute statistics needed for banking scoring"""
        # Customer product holdings
        self.customer_products = {}
        if self.transactions_df is not None and 'product_id' in self.transactions_df.columns:
            for cid, group in self.transactions_df.groupby('customer_id'):
                key = str(cid).strip()
                self.customer_products[key] = group['product_id'].unique().tolist()

        # Product popularity by segment
        self.segment_product_popularity = {}

        if self.customers_df is None or self.transactions_df is None:
            logger.info("📊 Pre-computed statistics (no transactions data)")
            return

        # Check for both column names (Agent A uses 'cluster', old code used 'macro_segment_id')
        if 'cluster' in self.customers_df.columns:
            segment_col = 'cluster'
        elif 'macro_segment_id' in self.customers_df.columns:
            segment_col = 'macro_segment_id'
        else:
            segment_col = None

        if segment_col and 'product_id' in self.transactions_df.columns:
            transactions_with_segment = self.transactions_df.merge(
                self.customers_df[['customer_id', segment_col]],
                on='customer_id',
                how='left'
            )
            for seg_id, group in transactions_with_segment.groupby(segment_col):
                self.segment_product_popularity[seg_id] = group['product_id'].value_counts().to_dict()

        logger.info(f"📊 Pre-computed statistics for {len(self.customer_products)} customers")
    
    def _merge_factor_weights(self, factor_weights: Dict = None) -> Dict[str, float]:
        """Merge API/UI weights (percentages 0–100 or fractions) with defaults; normalize to sum 1.0."""
        if not factor_weights:
            return dict(self.WEIGHTS)
        keys = list(self.WEIGHTS.keys())
        merged = {}
        for k in keys:
            if k not in factor_weights:
                merged[k] = self.WEIGHTS[k]
                continue
            v = float(factor_weights[k])
            merged[k] = (v / 100.0) if v > 1.5 else v
        s = sum(merged.values())
        if s <= 0:
            return dict(self.WEIGHTS)
        return {k: merged[k] / s for k in keys}
    
    def score_product(
        self,
        customer: Dict,
        product: Dict,
        persona: Dict = None,
        factor_weights: Dict = None,
    ) -> Dict:
        """
        Score a single banking product for a customer using all 12 factors
        
        Args:
            factor_weights: Optional dict of factor_key -> percent (0-100) or fraction; normalized to sum 1.
        
        Returns:
            detailed_breakdown with total_score and factor breakdowns
        """
        wt = self._merge_factor_weights(factor_weights)
        breakdown = {}
        customer_id = customer.get('customer_id', '')
        
        # Extract customer attributes
        credit_score = customer.get('credit_score', 700)
        income = customer.get('income', 50000)
        total_deposits = customer.get('total_deposits', 10000)
        age = customer.get('age', 40)
        num_products = customer.get('num_products', 2)
        digital_engagement = customer.get('digital_engagement_score', 0.5)
        cross_sell_receptivity = customer.get('cross_sell_receptivity', 0.5)
        
        # Extract product attributes
        product_id = product.get('product_id', '')
        min_credit_score = product.get('min_credit_score', 600)
        min_income = product.get('min_income', 0)
        min_balance = product.get('min_balance', 0)
        annual_fee = product.get('annual_fee', 0)
        category = product.get('category', '')
        
        def _add_calculation(contrib: float, weight: float, raw: float, expl: str) -> str:
            """Build calculation string for UI."""
            return f"Raw score {raw*100:.1f}% × {weight*100:.0f}% weight = {contrib*100:.1f}% contribution"

        # ==================== FACTOR 1: ELIGIBILITY SCORE (22%) ====================
        eligibility = self._calculate_eligibility_score(
            credit_score, income, total_deposits,
            min_credit_score, min_income, min_balance
        )
        w1 = wt['eligibility_score']
        c1 = eligibility['score'] * w1
        breakdown['eligibility_score'] = {
            'score': c1,
            'weight': w1,
            'raw_score': eligibility['score'],
            'calculation': _add_calculation(c1, w1, eligibility['score'], eligibility['explanation']),
            'explanation': eligibility['explanation'],
            'sub_scores': eligibility['sub_scores']
        }
        
        # ==================== FACTOR 2: FINANCIAL NEED MATCH (18%) ====================
        financial_need = self._calculate_financial_need_match(
            age, income, total_deposits, num_products, category, product, customer
        )
        w2 = wt['financial_need_match']
        c2 = financial_need['score'] * w2
        breakdown['financial_need_match'] = {
            'score': c2,
            'weight': w2,
            'raw_score': financial_need['score'],
            'calculation': _add_calculation(c2, w2, financial_need['score'], financial_need['explanation']),
            'explanation': financial_need['explanation']
        }
        
        # ==================== FACTOR 3: RELATIONSHIP DEPTH (15%) ====================
        relationship = self._calculate_relationship_depth(num_products, customer.get('months_since_relationship_started') or customer.get('tenure_months', 12))
        w3 = wt['relationship_depth']
        c3 = relationship['score'] * w3
        breakdown['relationship_depth'] = {
            'score': c3,
            'weight': w3,
            'raw_score': relationship['score'],
            'calculation': _add_calculation(c3, w3, relationship['score'], relationship['explanation']),
            'explanation': relationship['explanation']
        }
        
        # ==================== FACTOR 4: PRODUCT VALUE (12%) ====================
        product_value = self._calculate_product_value(
            product, customer, income, total_deposits, persona
        )
        w4 = wt['product_value']
        c4 = product_value['score'] * w4
        breakdown['product_value'] = {
            'score': c4,
            'weight': w4,
            'raw_score': product_value['score'],
            'calculation': _add_calculation(c4, w4, product_value['score'], product_value['explanation']),
            'explanation': product_value['explanation'],
            'details': product_value.get('details', {})
        }
        
        # ==================== FACTOR 5: PRODUCT PAIRING (9%) ====================
        pairing = self._calculate_product_pairing(customer_id, product_id, category, product=product, customer=customer)
        w5 = wt['product_pairing']
        c5 = pairing['score'] * w5
        breakdown['product_pairing'] = {
            'score': c5,
            'weight': w5,
            'raw_score': pairing['score'],
            'calculation': _add_calculation(c5, w5, pairing['score'], pairing['explanation']),
            'explanation': pairing['explanation'],
            'pairs_with': pairing.get('pairs_with', [])
        }
        
        # ==================== FACTOR 6: CHANNEL FIT (7%) ====================
        channel = self._calculate_channel_fit(digital_engagement, product.get('digital_required', False))
        w6 = wt['channel_fit']
        c6 = channel['score'] * w6
        breakdown['channel_fit'] = {
            'score': c6,
            'weight': w6,
            'raw_score': channel['score'],
            'calculation': _add_calculation(c6, w6, channel['score'], channel['explanation']),
            'explanation': channel['explanation']
        }
        
        # ==================== FACTOR 7: COMPLEXITY MATCH (4%) ====================
        complexity = self._calculate_complexity_match(
            digital_engagement, total_deposits, product.get('complexity_score', 2)
        )
        w7 = wt['complexity_match']
        c7 = complexity['score'] * w7
        breakdown['complexity_match'] = {
            'score': c7,
            'weight': w7,
            'raw_score': complexity['score'],
            'calculation': _add_calculation(c7, w7, complexity['score'], complexity['explanation']),
            'explanation': complexity['explanation']
        }
        
        # ==================== FACTOR 8: INTENT SCORE (3%) ====================
        w8 = wt['intent_score']
        c8 = cross_sell_receptivity * w8
        breakdown['intent_score'] = {
            'score': c8,
            'weight': w8,
            'raw_score': cross_sell_receptivity,
            'calculation': _add_calculation(c8, w8, cross_sell_receptivity, f"Cross-sell receptivity: {cross_sell_receptivity*100:.0f}%"),
            'explanation': f"Cross-sell receptivity: {cross_sell_receptivity*100:.0f}%"
        }
        
        # ==================== FACTOR 9: SEGMENT AFFINITY (2%) ====================
        segment_score = self._calculate_segment_affinity(customer, product_id, persona)
        w9 = wt['segment_affinity']
        c9 = segment_score['score'] * w9
        breakdown['segment_affinity'] = {
            'score': c9,
            'weight': w9,
            'raw_score': segment_score['score'],
            'calculation': _add_calculation(c9, w9, segment_score['score'], segment_score['explanation']),
            'explanation': segment_score['explanation']
        }
        
        # ==================== FACTOR 10: TRANSACTION PATTERN (1%) ====================
        # Derive frequency from monthly_transaction_volume (transaction_frequency not in customers.csv)
        _mtv = customer.get('monthly_transaction_volume', 0) or 0
        if _mtv > 50:
            _txn_freq = 'high'
        elif _mtv > 20:
            _txn_freq = 'medium'
        elif _mtv > 5:
            _txn_freq = 'low'
        else:
            _txn_freq = 'very_low'
        transaction = self._calculate_transaction_pattern(customer.get('transaction_frequency', _txn_freq))
        w10 = wt['transaction_pattern']
        c10 = transaction['score'] * w10
        breakdown['transaction_pattern'] = {
            'score': c10,
            'weight': w10,
            'raw_score': transaction['score'],
            'calculation': _add_calculation(c10, w10, transaction['score'], transaction['explanation']),
            'explanation': transaction['explanation']
        }
        
        # ==================== FACTOR 11: PRODUCT RATING (4%) ====================
        rating = product.get('avg_rating', 4.0)
        rating_score = rating / 5.0
        w11 = wt['product_rating']
        c11 = rating_score * w11
        breakdown['product_rating'] = {
            'score': c11,
            'weight': w11,
            'raw_score': rating_score,
            'calculation': _add_calculation(c11, w11, rating_score, f"Product rating: {rating:.1f}/5.0 stars"),
            'explanation': f"Product rating: {rating:.1f}/5.0 stars"
        }
        
        # ==================== FACTOR 12: POPULARITY (3%) ====================
        popularity = self._calculate_popularity(product_id, customer.get('cluster', customer.get('macro_segment_id')))
        w12 = wt['popularity']
        c12 = popularity['score'] * w12
        breakdown['popularity'] = {
            'score': c12,
            'weight': w12,
            'raw_score': popularity['score'],
            'calculation': _add_calculation(c12, w12, popularity['score'], popularity['explanation']),
            'explanation': popularity['explanation']
        }
        
        # ==================== FACTOR 12: RECENCY BOOST (0% - removed for simplicity) ====================
        # Replaced with transaction_pattern above
        
        # ==================== CALCULATE TOTAL SCORE ====================
        total_score = sum(factor['score'] for factor in breakdown.values())
        
        # Add summary
        breakdown['total_score'] = total_score
        breakdown['total_percentage'] = total_score * 100
        
        return breakdown
    
    def _calculate_eligibility_score(
        self, credit_score: float, income: float, deposits: float,
        min_credit: float, min_income: float, min_balance: float,
        product: Dict = None, customer: Dict = None
    ) -> Dict:
        """Calculate eligibility based on credit, income, balance, and JPM credit tier requirements."""

        product = product or {}
        customer = customer or {}

        # Hard block: credit_tier_required == 'excellent' but customer is not excellent
        credit_tier_required = str(product.get('credit_tier_required', 'any')).lower()
        customer_credit_tier = str(customer.get('credit_tier', '')).lower()
        if credit_tier_required == 'excellent' and customer_credit_tier not in ('excellent', ''):
            return {
                'score': 0.0,
                'explanation': f"Requires excellent credit tier; customer is {customer_credit_tier or 'unclassified'}",
                'sub_scores': {'credit': 0.0, 'income': 0.0, 'balance': 0.0},
                'hard_block': True,
            }

        # Hard block: wealth management products require minimum balance
        aum_fee_pct = float(product.get('aum_fee_pct', 0))
        if aum_fee_pct > 0 and min_balance > 0 and deposits < min_balance:
            return {
                'score': 0.0,
                'explanation': f"Wealth product requires ${min_balance:,.0f} minimum; customer has ${deposits:,.0f}",
                'sub_scores': {'credit': 0.0, 'income': 0.0, 'balance': 0.0},
                'hard_block': True,
            }

        # Credit score match (40% of eligibility)
        if credit_score >= min_credit + 50:
            credit_match = 1.0
            credit_status = "well qualified"
        elif credit_score >= min_credit:
            credit_match = 0.8
            credit_status = "qualified"
        elif credit_score >= min_credit - 20:
            credit_match = 0.5
            credit_status = "borderline"
        else:
            credit_match = 0.1
            credit_status = "not qualified"

        # Income match (35% of eligibility)
        if min_income == 0:
            income_match = 1.0
        elif income >= min_income:
            income_match = min(1.0, income / min_income)
        else:
            income_match = (income / min_income) * 0.6

        # Balance match (25% of eligibility)
        if min_balance == 0:
            balance_match = 1.0
        elif deposits >= min_balance:
            balance_match = 1.0
        else:
            balance_match = 0.5

        eligibility_score = (credit_match * 0.4) + (income_match * 0.35) + (balance_match * 0.25)

        explanation = f"Credit: {int(credit_score)} vs {int(min_credit)} required ({credit_status})"
        if min_income > 0:
            explanation += f", Income: ${income:,.0f} vs ${min_income:,.0f} required"

        return {
            'score': eligibility_score,
            'explanation': explanation,
            'sub_scores': {
                'credit': credit_match,
                'income': income_match,
                'balance': balance_match
            }
        }
    
    def _product_kind_for_need(self, product: Dict) -> str:
        """
        Map catalog row to a coarse product kind using subcategory and category.
        Handles Meridian Bank taxonomy: category is product type (Bank Account /
        Certificate of Deposit / Credit Card / Loan / Mortgage / Investment).
        Subcategory values: Checking, Savings, Money Market, 12-Month, 24-Month,
        Cash Back, Travel Rewards, Secured, Balance Transfer, Auto, Personal,
        Home Equity, Student Refinance, 30-Year Fixed, FHA, 15-Year Fixed, Jumbo,
        Cash-Out Refinance, Managed Portfolio, Health Savings.
        """
        sub = str(product.get('subcategory', '') or '').strip().lower()
        cat = str(product.get('category', '') or '').strip().lower()
        name = str(product.get('product_name', '') or '').lower()

        if sub == 'checking':
            return 'Checking'
        if sub in ('savings', 'money market'):
            return 'Savings'
        if sub in ('12-month', '24-month') or cat == 'certificate of deposit':
            return 'Investment'
        if cat == 'credit card':
            return 'Credit_Card'
        if cat == 'investment' or sub in ('managed portfolio', 'health savings'):
            return 'Investment'
        if sub == 'auto' or (cat == 'loan' and 'auto' in name):
            return 'Auto_Loan'
        if sub in ('home equity', 'student refinance', 'personal') or cat == 'loan':
            return 'Other_Loan'
        if cat == 'mortgage':
            return 'Mortgage'
        return 'Other'

    def _calculate_financial_need_match(
        self, age: int, income: float, deposits: float,
        num_products: int, category: str, product: Dict,
        customer: Dict = None
    ) -> Dict:
        """Match product to customer's financial life stage and needs (uses subcategory, not broad CSV category)."""
        kind = self._product_kind_for_need(product)
        score = 0.55
        explanation = "Moderate fit based on your profile"

        # --- Age + product kind (primary driver of differentiation between customers) ---
        if age < 35:
            if kind in ('Checking', 'Credit_Card'):
                score = 0.92
                explanation = "Strong fit: everyday banking and credit for early career"
            elif kind == 'Investment':
                score = 0.68
                explanation = "Early retirement planning; still building other priorities"
            elif kind == 'Auto_Loan':
                score = 0.84
                explanation = "Auto financing is common for younger households"
            elif kind == 'Mortgage':
                score = 0.88
                explanation = "Typical home-buying life stage"
            elif kind == 'Savings':
                score = 0.8
                explanation = "Building savings habit"
        elif age >= 55:
            if kind == 'Investment':
                score = 0.96
                explanation = "Retirement-focused: CDs, IRAs, and growth products align well"
            elif kind in ('Checking', 'Savings'):
                score = 0.84
                explanation = "Stable cash management and liquidity"
            elif kind == 'Auto_Loan':
                score = 0.4
                explanation = "New auto financing is often lower priority near or after retirement"
            elif kind == 'Mortgage':
                score = 0.52
                explanation = "Refinance may apply; new purchase less common than peak earning years"
            elif kind == 'Credit_Card':
                score = 0.66
                explanation = "Credit still useful; balance with income stability"
            elif kind == 'Other_Loan':
                score = 0.5
                explanation = "Evaluate need case-by-case at this life stage"
        else:
            # 35–54: peak borrowing / wealth-building — avoid tying auto loans to CDs/IRAs (same score → same #1 for everyone)
            if kind == 'Investment':
                score = 0.92
                explanation = "Mid-career: prioritize growth, retirement, and rate products"
            elif kind == 'Mortgage':
                score = 0.9
                explanation = "Typical home and refinance life stage"
            elif kind == 'Auto_Loan':
                score = 0.76
                explanation = "Auto credit matters; usually not the only top priority vs deposits/investments"
            elif kind == 'Checking':
                score = 0.81
                explanation = "Primary banking relationship"
            elif kind == 'Savings':
                score = 0.79
                explanation = "Building reserves alongside other goals"
            elif kind == 'Credit_Card':
                score = 0.77
                explanation = "Revolving credit fits mid-career cash flow"
            elif kind == 'Other_Loan':
                score = 0.72
                explanation = "Evaluate specialized lending vs core relationship products"

        # --- Deposits: shift emphasis without erasing age signal ---
        if deposits >= 150000:
            if kind == 'Investment':
                score = max(score, 0.96)
                explanation = "Higher balances suit CDs, IRAs, and investment products"
            elif kind == 'Auto_Loan':
                score = min(score, 0.72)
                explanation = "Strong liquidity may reduce urgency for new installment debt"
        elif deposits < 45000:
            if kind in ('Checking', 'Savings'):
                score = max(score, 0.86)
                explanation = "Foundation products while growing balances"
            if kind == 'Auto_Loan' and income < 72000:
                score = max(score, 0.78)
                explanation = "Affordable financing may matter more with moderate balances"

        # --- Income + young adults ---
        if income < 60000 and age < 35:
            if 'junior' in str(product.get('product_name', '')).lower() or 'teen' in str(product.get('product_name', '')).lower():
                score = max(score, 0.9)
                explanation = "Entry-level products for younger, moderate-income households"

        # --- JPM rewards type matching ---
        rewards_type = str(product.get('rewards_type', 'none')).lower()
        preferred_rewards = str(customer.get('preferred_rewards_type', 'none')).lower() if customer else 'none'
        if rewards_type != 'none' and rewards_type == preferred_rewards:
            score = min(1.0, score + 0.12)
            explanation += f" + rewards match ({rewards_type})"

        # --- Monthly fee sensitivity penalty ---
        monthly_fee = float(product.get('monthly_fee', 0))
        fee_sensitivity_tier = str(customer.get('fee_sensitivity_tier', 'medium')).lower() if customer else 'medium'
        if monthly_fee > 0:
            if fee_sensitivity_tier == 'high':
                score = max(0.1, score - 0.20)
                explanation += f" - fee penalty (${monthly_fee:.2f}/mo, high sensitivity)"
            # Check if fee is waivable for this customer
            waiver_cond = str(product.get('fee_waiver_condition', 'none')).lower()
            has_dd = str(customer.get('has_direct_deposit', 'False')).lower() == 'true' if customer else False
            dd_amt = float(customer.get('monthly_direct_deposit_amt', 0)) if customer else 0
            deposits = float(customer.get('total_deposits', 0)) if customer else deposits
            waived = False
            if waiver_cond.startswith('direct_deposit'):
                threshold = float(waiver_cond.split('_')[-1]) if waiver_cond.split('_')[-1].isdigit() else 500
                waived = has_dd and dd_amt >= threshold
            elif waiver_cond.startswith('balance'):
                threshold = float(waiver_cond.split('_')[-1]) if waiver_cond.split('_')[-1].isdigit() else 1500
                waived = deposits >= threshold
            if waived and monthly_fee > 0:
                score = min(1.0, score + 0.15)
                explanation += f" + fee waiver eligible"

        # --- Financial goal alignment (highest-signal predictor of conversion) ---
        customer_obj = customer or {}
        goal = str(customer_obj.get('financial_goal', '')).lower()
        cat_lower = str(product.get('category', '') or '').strip().lower()

        goal_boosts = {
            'pay_off_debt':         {'credit card': 0.15, 'loan': 0.12},
            'home_purchase':        {'mortgage': 0.20, 'bank account': 0.08, 'certificate of deposit': 0.06},
            'retirement_savings':   {'investment': 0.18, 'certificate of deposit': 0.14, 'bank account': 0.10},
            'grow_wealth':          {'investment': 0.18, 'certificate of deposit': 0.10, 'bank account': 0.08},
            'build_emergency_fund': {'bank account': 0.15, 'certificate of deposit': 0.12},
        }
        goal_boost = goal_boosts.get(goal, {}).get(cat_lower, 0.0)
        if goal_boost > 0:
            score = min(1.0, score + goal_boost)
            explanation += f" + goal match ({goal})"

        # --- Life stage override (more precise than raw age brackets) ---
        life_stage = str(customer_obj.get('life_stage', '')).lower()
        life_stage_score_map = {
            ('student',        'Credit_Card'):  0.88,
            ('student',        'Checking'):     0.90,
            ('young_single',   'Auto_Loan'):    0.90,
            ('young_single',   'Credit_Card'):  0.88,
            ('new_family',     'Mortgage'):     0.94,
            ('new_family',     'Checking'):     0.85,
            ('growing_family', 'Mortgage'):     0.92,
            ('growing_family', 'Other_Loan'):   0.84,
            ('empty_nester',   'Investment'):   0.93,
            ('empty_nester',   'Mortgage'):     0.72,
            ('pre_retiree',    'Investment'):   0.96,
            ('pre_retiree',    'CD'):           0.90,
            ('retiree',        'Investment'):   0.94,
            ('retiree',        'Credit_Card'):  0.55,
        }
        ls_key = (life_stage, kind)
        if ls_key in life_stage_score_map and life_stage:
            # Only override when life_stage gives a materially different signal
            score = life_stage_score_map[ls_key]
            explanation = f"Life stage match: {life_stage} → {kind}"

        # --- Overdraft LOC: strong signal for high-overdraft customers ---
        high_overdraft = int(customer_obj.get('high_overdraft_flag', 0))
        product_name_lower = str(product.get('product_name', '')).lower()
        if high_overdraft and 'overdraft' in product_name_lower:
            score = min(1.0, score + 0.20)
            explanation += " + overdraft LOC match"

        score = max(0.2, min(1.0, float(score)))
        return {
            'score': score,
            'explanation': explanation
        }

    def _calculate_relationship_depth(self, num_products: int, tenure_months: int) -> Dict:
        """Score based on customer relationship depth"""
        
        # Base score from product count (max at 8 products)
        product_score = min(num_products / 8.0, 1.0)
        
        # Tenure bonus (max 20% boost for 5+ years)
        tenure_bonus = min(tenure_months / 60.0, 1.0) * 0.2
        
        score = min(product_score + tenure_bonus, 1.0)
        
        explanation = f"{num_products} products owned, {tenure_months//12} years tenure"
        
        return {
            'score': score,
            'explanation': explanation
        }
    
    def _calculate_product_value(
        self,
        product: Dict,
        customer: Dict,
        customer_income: float,
        customer_deposits: float,
        persona: Dict = None
    ) -> Dict:
        """
        Calculate product value score based on product-specific attributes.
        For Wealth Investors: premium fee-based products get a slight boost so we don't
        over-recommend only free products (they already have relationship; premium can be suitable).
        """
        score = 0
        details = {}
        explanations = []
        
        # Persona: Wealth Investors can get premium (fee) products recommended too
        persona_name = (persona or {}).get('persona_name', '') or (persona or {}).get('name', '')
        is_wealth_investor = 'wealth' in str(persona_name).lower() or 'investor' in str(persona_name).lower()
        
        # Extract product attributes
        annual_fee = float(product.get('annual_fee', 0))
        monthly_fee = float(product.get('monthly_fee', 0))
        min_balance = float(product.get('min_balance', 0))
        subcategory = product.get('subcategory', '').lower()
        category_lower = str(product.get('category', '') or '').strip().lower()

        # Use personalized rate tier if available (JPM products have credit-tier-based rates)
        customer_credit_tier = str(customer.get('credit_tier', '')).lower() if customer else ''
        if customer_credit_tier == 'excellent' and product.get('rate_tier_excellent'):
            interest_rate = float(product.get('rate_tier_excellent', 0))
        elif customer_credit_tier == 'good' and product.get('rate_tier_good'):
            interest_rate = float(product.get('rate_tier_good', 0))
        elif customer_credit_tier == 'fair' and product.get('rate_tier_fair'):
            interest_rate = float(product.get('rate_tier_fair', 0))
        else:
            interest_rate = float(product.get('interest_rate', product.get('interest_rate_apy', 0)))
        
        # ========== 1. FEE SCORE (30%) - Lower is better (with Wealth Investor adjustment) ==========
        fee_score = 0
        if annual_fee == 0:
            fee_score = 1.0
            explanations.append("No annual fee (excellent)")
        elif annual_fee <= 25:
            fee_score = 0.9
            explanations.append(f"Low fee ${annual_fee:.0f}/yr (very good)")
        elif annual_fee <= 50:
            fee_score = 0.75
            explanations.append(f"Modest fee ${annual_fee:.0f}/yr (good)")
        elif annual_fee <= 95:
            fee_score = 0.6
            explanations.append(f"Moderate fee ${annual_fee:.0f}/yr (acceptable)")
        elif annual_fee <= 150:
            fee_score = 0.4
            explanations.append(f"Higher fee ${annual_fee:.0f}/yr (premium)")
        else:
            fee_score = 0.2
            explanations.append(f"High fee ${annual_fee:.0f}/yr (for high-value services)")
        
        # JPM: also consider monthly fee in total cost burden
        total_annual_cost = annual_fee + (monthly_fee * 12)
        max_affordable_fee = customer_deposits * 0.005  # 0.5% of deposits
        if total_annual_cost > max_affordable_fee and total_annual_cost > 0:
            fee_score *= 0.7
            explanations.append(f"(adjusted down: total fees ${total_annual_cost:.0f}/yr vs deposits)")
        elif annual_fee > max_affordable_fee:
            fee_score *= 0.7
            explanations.append(f"(adjusted down: fee high vs deposits)")

        # JPM: intro APR bonus for new-to-credit customers
        intro_apr_months = int(product.get('intro_apr_months', 0))
        num_products = int(customer.get('num_products', 3)) if customer else 3
        if intro_apr_months >= 12 and num_products <= 2 and category_lower == 'credit card':
            fee_score = min(1.0, fee_score + 0.08)
            explanations.append(f"0% intro APR for {intro_apr_months} months (great for new credit users)")

        # Wealth Investors: premium fee-based products are acceptable (don't over-penalize)
        if is_wealth_investor and annual_fee > 0:
            fee_score = min(1.0, fee_score + 0.12)
            explanations.append("(Wealth segment: premium fee acceptable)")
        
        details['fee_score'] = fee_score
        score += fee_score * 0.25

        # ========== 2. INTEREST RATE SCORE (25%) - Higher is better for savings/investment ==========
        rate_score = 0
        if category_lower in ('certificate of deposit', 'investment') or subcategory in ('savings', 'money market', 'managed portfolio', 'health savings', '12-month', '24-month'):
            # For interest-bearing products, higher rates are better
            if interest_rate >= 2.5:
                rate_score = 1.0
                explanations.append(f"Excellent APY: {interest_rate:.2f}%")
            elif interest_rate >= 2.0:
                rate_score = 0.9
                explanations.append(f"Very good APY: {interest_rate:.2f}%")
            elif interest_rate >= 1.5:
                rate_score = 0.8
                explanations.append(f"Good APY: {interest_rate:.2f}%")
            elif interest_rate >= 1.0:
                rate_score = 0.7
                explanations.append(f"Modest APY: {interest_rate:.2f}%")
            elif interest_rate >= 0.5:
                rate_score = 0.6
                explanations.append(f"Standard APY: {interest_rate:.2f}%")
            elif interest_rate > 0:
                rate_score = 0.4
                explanations.append(f"Low APY: {interest_rate:.2f}%")
            else:
                rate_score = 0.3
                explanations.append("No interest")
        elif category_lower in ('credit card', 'loan', 'mortgage') or subcategory in (
                'auto', 'personal', 'home equity', 'student refinance',
                '30-year fixed', 'fha', '15-year fixed', 'jumbo', 'cash-out refinance',
                'cash back', 'travel rewards', 'balance transfer', 'secured'):
            # For loans/credit, LOWER rates are better
            if interest_rate <= 4.0:
                rate_score = 1.0
                explanations.append(f"Excellent rate: {interest_rate:.2f}%")
            elif interest_rate <= 6.0:
                rate_score = 0.9
                explanations.append(f"Very good rate: {interest_rate:.2f}%")
            elif interest_rate <= 8.0:
                rate_score = 0.75
                explanations.append(f"Good rate: {interest_rate:.2f}%")
            elif interest_rate <= 12.0:
                rate_score = 0.6
                explanations.append(f"Standard rate: {interest_rate:.2f}%")
            elif interest_rate <= 15.0:
                rate_score = 0.4
                explanations.append(f"Higher rate: {interest_rate:.2f}%")
            else:
                rate_score = 0.2
                explanations.append(f"High rate: {interest_rate:.2f}%")
        else:
            # Checking accounts - rate less important
            rate_score = 0.7  # Neutral
            if interest_rate > 0:
                rate_score = 0.85
                explanations.append(f"Bonus: earns {interest_rate:.2f}% APY")
        
        details['rate_score'] = rate_score
        score += rate_score * 0.25

        # ========== 3. MINIMUM BALANCE SCORE (15%) - Lower is more accessible ==========
        balance_score = 0
        if min_balance == 0:
            balance_score = 1.0
            explanations.append("No minimum balance required")
        elif min_balance <= 100:
            balance_score = 0.95
            explanations.append(f"Very low minimum: ${min_balance:.0f}")
        elif min_balance <= 500:
            balance_score = 0.85
            explanations.append(f"Low minimum: ${min_balance:.0f}")
        elif min_balance <= 2500:
            balance_score = 0.7
            explanations.append(f"Moderate minimum: ${min_balance:.0f}")
        elif min_balance <= 5000:
            balance_score = 0.55
            explanations.append(f"Higher minimum: ${min_balance:.0f}")
        elif min_balance <= 10000:
            balance_score = 0.4
            explanations.append(f"High minimum: ${min_balance:.0f}")
        else:
            balance_score = 0.25
            explanations.append(f"Premium minimum: ${min_balance:.0f}")
        
        # Adjust based on customer affordability
        if min_balance > customer_deposits * 0.5:
            balance_score *= 0.6  # Big penalty if min balance > 50% of deposits
            explanations.append("(adjusted: high vs your deposits)")
        elif min_balance > customer_deposits * 0.2:
            balance_score *= 0.8  # Moderate penalty
        
        details['balance_score'] = balance_score
        score += balance_score * 0.15

        # ========== 4. FINANCIAL ROI SCORE (15%) - Customer net value ==========
        roi_score = 0.5  # Baseline
        
        # Calculate effective ROI
        if subcategory in ['savings', 'investment']:
            # Savings: (interest earned - fees) / balance required
            if min_balance > 0:
                annual_interest = min_balance * (interest_rate / 100)
                net_value = annual_interest - annual_fee
                roi_percent = (net_value / min_balance) * 100
                
                if roi_percent >= 2.0:
                    roi_score = 1.0
                    explanations.append(f"Excellent ROI: {roi_percent:.2f}%")
                elif roi_percent >= 1.5:
                    roi_score = 0.9
                    explanations.append(f"Very good ROI: {roi_percent:.2f}%")
                elif roi_percent >= 1.0:
                    roi_score = 0.8
                    explanations.append(f"Good ROI: {roi_percent:.2f}%")
                elif roi_percent >= 0.5:
                    roi_score = 0.7
                elif roi_percent >= 0:
                    roi_score = 0.6
                else:
                    roi_score = 0.4
                    explanations.append(f"Negative ROI (fees > interest)")
        elif subcategory in ['checking']:
            # Checking: Value = (convenience + interest) - fees
            if annual_fee == 0:
                roi_score = 0.9
                if interest_rate > 0:
                    roi_score = 1.0
                    explanations.append("Free checking with interest - excellent value")
                else:
                    explanations.append("Free checking - great value")
            else:
                roi_score = 0.6
        else:
            # Loans, credit: Lower cost = better ROI
            if annual_fee == 0 and interest_rate < 10:
                roi_score = 0.9
                explanations.append("Low-cost financing")
            elif annual_fee < 50 and interest_rate < 15:
                roi_score = 0.7
            else:
                roi_score = 0.5
        
        details['roi_score'] = roi_score
        score += roi_score * 0.15

        # ========== 5. PROJECTED BANK REVENUE FROM THIS CUSTOMER (20%) ==========
        # This score is CUSTOMER-SPECIFIC — it estimates how much revenue the bank
        # will earn from THIS customer using THIS product, based on their actual
        # spending, balances, credit behaviour, and financial goals.
        # A free product ranks higher here for a customer whose profile generates
        # meaningful deposit float or interchange, and lower for a low-activity customer.
        aum_fee_pct     = float(product.get('aum_fee_pct', 0))
        regular_apr_pct = float(product.get('regular_apr_pct', interest_rate))

        # Pull customer behavioural signals (all default-safe)
        monthly_spend       = float((customer or {}).get('monthly_spend_in_primary_cat', 200))
        credit_util         = float((customer or {}).get('credit_utilization_ratio', 0.30))
        avg_daily_bal       = float((customer or {}).get('avg_daily_balance', customer_deposits))
        financial_goal      = str((customer or {}).get('financial_goal', '')).lower()
        travel_freq         = str((customer or {}).get('travel_frequency', 'none')).lower()
        total_loan_bal      = float((customer or {}).get('total_loan_balance', 0))
        has_dd              = str((customer or {}).get('has_direct_deposit', 'False')).lower() == 'true'
        dd_amt              = float((customer or {}).get('monthly_direct_deposit_amt', 0))
        age_val             = float((customer or {}).get('age', 40))

        bank_rev_score = 0.0
        rev_explanation = ''

        if category_lower == 'credit card':
            # Bank earns interchange (~1.8 %) on every dollar spent PLUS
            # interest on the revolving balance this customer is likely to carry.
            monthly_interchange = monthly_spend * 0.018
            # Travel-heavy customers amplify revenue on travel-reward cards
            if travel_freq in ('domestic_frequent', 'international_frequent'):
                monthly_interchange *= 1.25
            likely_revolving = avg_daily_bal * 0.25 * credit_util
            monthly_interest  = likely_revolving * (regular_apr_pct / 100 / 12)
            projected_monthly = monthly_interchange + monthly_interest
            # $0 → 0.25 | $25 → 0.55 | $60 → 0.80 | $100+ → 1.0
            bank_rev_score = min(1.0, 0.25 + min(projected_monthly / 100, 0.75))
            rev_explanation = f"Est. ${projected_monthly:.0f}/mo bank revenue (interchange + interest)"

        elif category_lower in ('loan', 'mortgage') or subcategory in (
                'auto', 'personal', 'home equity', 'student refinance',
                '30-year fixed', 'fha', '15-year fixed', 'jumbo', 'cash-out refinance'):
            # Bank earns net interest spread (rate minus ~3 % cost of funds)
            net_spread = max(0.0, interest_rate - 3.0)
            # Weight by how well the customer's goal aligns with this loan type
            goal_fit = 1.0
            if category_lower == 'mortgage' and financial_goal != 'home_purchase':
                goal_fit = 0.40
            elif subcategory == 'personal' and financial_goal not in ('pay_off_debt', 'build_emergency_fund'):
                goal_fit = 0.55
            elif subcategory == 'auto' and age_val > 65:
                goal_fit = 0.45
            bank_rev_score = min(1.0, 0.30 + goal_fit * 0.40 + (net_spread / 22) * 0.30)
            rev_explanation = f"Est. {net_spread:.1f}% net spread, goal alignment {goal_fit:.0%}"

        elif category_lower == 'investment' or subcategory in ('managed portfolio', 'health savings'):
            # Bank earns AUM fees on investable assets above a living-expense buffer
            investable = max(0.0, avg_daily_bal - 15_000)
            projected_annual_aum = investable * (aum_fee_pct / 100) if aum_fee_pct > 0 else investable * 0.0025
            # $0 → 0.25 | $500 → 0.55 | $2000 → 0.85 | $5000+ → 1.0
            bank_rev_score = min(1.0, 0.25 + min(projected_annual_aum / 5_000, 0.75))
            rev_explanation = f"Est. ${projected_annual_aum:.0f}/yr AUM revenue"

        elif category_lower == 'certificate of deposit' or subcategory in ('savings', 'money market', '12-month', '24-month'):
            # Bank borrows from customer; profit = NIM (~2.5 %) on deposit float
            deposit_float_rev = avg_daily_bal * 0.025
            bank_rev_score = min(0.85, 0.25 + min(deposit_float_rev / 5_000, 0.60))
            rev_explanation = f"Est. ${deposit_float_rev:.0f}/yr NIM on deposits"

        else:
            # Checking — free accounts: revenue = NIM on deposit float + direct-deposit stability value
            deposit_float_rev = avg_daily_bal * 0.025
            dd_stability       = (dd_amt * 0.015) if has_dd else 0.0   # sticky DD customer
            total_monthly_rev  = (deposit_float_rev + dd_stability) / 12 + monthly_fee
            bank_rev_score = min(0.80, 0.20 + min(total_monthly_rev / 100, 0.60))
            rev_explanation = f"Est. ${total_monthly_rev:.0f}/mo (float + fees)"

        details['bank_revenue_score'] = bank_rev_score
        details['projected_bank_revenue_explanation'] = rev_explanation
        score += bank_rev_score * 0.20
        if rev_explanation:
            explanations.append(rev_explanation)

        # ========== FINAL SCORE & EXPLANATION ==========
        score = max(0.0, min(1.0, score))  # Clamp to [0,1]

        # Build comprehensive explanation
        explanation_text = " | ".join(explanations[:3])  # Top 3 factors

        return {
            'score': score,
            'explanation': explanation_text,
            'details': details
        }
    
    def _calculate_product_pairing(
        self, customer_id: str, product_id: str, category: str,
        product: Dict = None, customer: Dict = None
    ) -> Dict:
        """Calculate affinity with customer's existing products, using subcategory-based pairing rules."""

        # Complementary subcategory pairs (keyed by owned subcategory → what pairs well next)
        pairing_rules = {
            'Checking':          ['Savings', 'Money Market', '12-Month', '24-Month', 'Cash Back', 'Managed Portfolio'],
            'Savings':           ['12-Month', '24-Month', 'Managed Portfolio', 'Checking'],
            'Money Market':      ['12-Month', '24-Month', 'Managed Portfolio', 'Checking'],
            '12-Month':          ['Savings', 'Money Market', 'Managed Portfolio', '24-Month'],
            '24-Month':          ['Savings', 'Money Market', 'Managed Portfolio'],
            'Cash Back':         ['Personal', 'Managed Portfolio', 'Checking'],
            'Travel Rewards':    ['Managed Portfolio', 'Checking', 'Savings'],
            'Balance Transfer':  ['Checking', 'Savings', 'Personal'],
            'Secured':           ['Checking', 'Savings'],
            'Personal':          ['Checking', 'Savings', 'Cash Back'],
            'Student Refinance': ['Checking', 'Savings'],
            'Auto':              ['Checking', 'Cash Back'],
            'Home Equity':       ['30-Year Fixed', 'Managed Portfolio'],
            '30-Year Fixed':     ['Home Equity', 'Managed Portfolio', 'Checking'],
            'FHA':               ['Checking', 'Savings'],
            '15-Year Fixed':     ['Home Equity', 'Managed Portfolio'],
            'Jumbo':             ['Managed Portfolio', 'Checking'],
            'Cash-Out Refinance': ['Home Equity', 'Managed Portfolio'],
            'Managed Portfolio': ['12-Month', '24-Month', 'Savings'],
            'Health Savings':    ['Checking', 'Savings'],
        }

        # Get customer's current products (keys normalized to str in __init__)
        lookup_id = str(customer_id).strip() if customer_id is not None else ''
        current_products = self.customer_products.get(lookup_id, [])

        product_sub = str((product or {}).get('subcategory', '') or '').strip()
        customer_obj = customer or {}

        if not current_products:
            score = 0.5
            explanation = "No existing products to pair with"
            pairs_with = []
        else:
            pairs_with = []
            for existing_pid in current_products:
                rows = self.products_df[self.products_df['product_id'] == existing_pid]
                if len(rows) > 0:
                    owned_sub = str(rows.iloc[0].get('subcategory', '') or '').strip()
                    complementary = pairing_rules.get(owned_sub, [])
                    if product_sub in complementary:
                        pairs_with.append(owned_sub)

            if pairs_with:
                score = min(0.9, 0.6 + len(pairs_with) * 0.15)
                explanation = f"Pairs well with: {', '.join(pairs_with[:3])}"
            else:
                score = 0.4
                explanation = "Limited pairing with existing products"

        # --- Cross-sell sequencing: reward the "right next step" product ---
        owned_subcats = set()
        for existing_pid in current_products:
            rows = self.products_df[self.products_df['product_id'] == existing_pid]
            if len(rows) > 0:
                owned_subcats.add(str(rows.iloc[0].get('subcategory', '') or '').strip())

        OPTIMAL_SEQUENCE = [
            [],
            ['Checking'],
            ['Checking', 'Savings'],
            ['Checking', 'Savings', 'Money Market', 'Cash Back', 'Travel Rewards'],
        ]
        step_index = min(len(owned_subcats), len(OPTIMAL_SEQUENCE) - 1)
        expected_next = OPTIMAL_SEQUENCE[step_index]
        if product_sub in expected_next:
            score = min(1.0, score + 0.08)
            explanation += " (next logical step)"

        # --- Competitor card signal: favour balance-transfer over regular credit ---
        has_competitor = str(customer_obj.get('has_competitor_credit_card', 'False')).lower() in ('true', '1', 'yes')
        product_name_lower = str((product or {}).get('product_name', '')).lower()
        cat_lower_pairing = str((product or {}).get('category', '') or '').strip().lower()
        if has_competitor and cat_lower_pairing == 'credit card':
            if 'balance transfer' in product_name_lower:
                score = min(1.0, score + 0.15)
                explanation += " + competitor balance-transfer opportunity"
            else:
                score = min(1.0, score + 0.05)
                explanation += " + cross-sell from competitor card"

        # --- High outstanding debt: boost debt-consolidation products ---
        outstanding_debt = float(customer_obj.get('outstanding_debt_total', 0))
        if outstanding_debt > 15000 and product_sub in ('Personal', 'Student Refinance'):
            score = min(1.0, score + 0.12)
            explanation += f" + debt consolidation fit (${outstanding_debt:,.0f} outstanding)"

        return {
            'score': score,
            'explanation': explanation,
            'pairs_with': pairs_with,
        }
    
    def _calculate_channel_fit(self, digital_engagement: float, digital_required: bool) -> Dict:
        """Match product channel requirements to customer preferences"""
        
        if digital_required and digital_engagement > 0.7:
            score = 1.0
            explanation = "Strong digital adoption matches online-only product"
        elif digital_required and digital_engagement < 0.3:
            score = 0.3
            explanation = "Low digital adoption may challenge online-only product"
        elif not digital_required and digital_engagement < 0.5:
            score = 0.9
            explanation = "Branch-available product suits traditional banking preference"
        else:
            score = 0.7
            explanation = "Moderate channel fit"
        
        return {
            'score': score,
            'explanation': explanation
        }
    
    def _calculate_complexity_match(
        self, digital_engagement: float, deposits: float, product_complexity: int
    ) -> Dict:
        """Match product complexity to customer sophistication"""
        
        # Determine customer sophistication
        if deposits > 100000 and digital_engagement > 0.7:
            customer_level = 3  # High sophistication
        elif deposits > 50000 or digital_engagement > 0.5:
            customer_level = 2  # Medium sophistication
        else:
            customer_level = 1  # Lower sophistication
        
        # Score based on match (1-3 scale for complexity)
        complexity_gap = abs(customer_level - product_complexity)
        
        if complexity_gap == 0:
            score = 1.0
            explanation = "Perfect complexity match"
        elif complexity_gap == 1:
            score = 0.7
            explanation = "Acceptable complexity difference"
        else:
            score = 0.4
            explanation = "Significant complexity mismatch"
        
        return {
            'score': score,
            'explanation': explanation
        }
    
    def _calculate_segment_affinity(self, customer: Dict, product_id: str, persona: Dict = None) -> Dict:
        """Calculate what % of customer's segment has this product"""
        
        # Try both column names
        segment_id = customer.get('cluster', customer.get('macro_segment_id'))
        
        if not segment_id or segment_id not in self.segment_product_popularity:
            return {
                'score': 0.5,
                'explanation': "No segment data available"
            }
        
        segment_products = self.segment_product_popularity[segment_id]
        
        # Use the correct column name for counting customers
        if 'cluster' in self.customers_df.columns:
            total_segment_customers = len(self.customers_df[self.customers_df['cluster'] == segment_id])
        else:
            total_segment_customers = len(self.customers_df[self.customers_df['macro_segment_id'] == segment_id])
        
        if product_id in segment_products:
            adoption_count = segment_products[product_id]
            adoption_rate = adoption_count / total_segment_customers if total_segment_customers > 0 else 0
            score = min(adoption_rate * 2, 1.0)  # Scale up adoption rate
            explanation = f"{adoption_rate*100:.0f}% of segment has this product"
        else:
            score = 0.2
            explanation = "New product for this segment"
        
        return {
            'score': score,
            'explanation': explanation
        }
    
    def _calculate_transaction_pattern(self, frequency: str) -> Dict:
        """Score based on customer transaction activity"""
        
        frequency_scores = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5,
            'very_low': 0.3
        }
        
        score = frequency_scores.get(frequency, 0.7)
        explanation = f"Transaction frequency: {frequency}"
        
        return {
            'score': score,
            'explanation': explanation
        }
    
    def _calculate_popularity(self, product_id: str, segment_id: any) -> Dict:
        """Calculate product popularity in customer's segment"""
        
        if not segment_id or segment_id not in self.segment_product_popularity:
            return {
                'score': 0.5,
                'explanation': "No popularity data"
            }
        
        segment_products = self.segment_product_popularity[segment_id]
        
        if product_id in segment_products:
            adoption_count = segment_products[product_id]
            if adoption_count > 100:
                score = 1.0
                explanation = f"Very popular ({adoption_count} customers)"
            elif adoption_count > 50:
                score = 0.8
                explanation = f"Popular ({adoption_count} customers)"
            else:
                score = 0.5
                explanation = f"Moderate adoption ({adoption_count} customers)"
        else:
            score = 0.3
            explanation = "New product"
        
        return {
            'score': score,
            'explanation': explanation
        }


if __name__ == "__main__":
    logger.info("Banking 12-Factor Scorer - Banking-specific scoring system")

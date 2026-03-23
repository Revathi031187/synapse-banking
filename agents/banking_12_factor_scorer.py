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
        # TIER 1: Eligibility & Core Match (55%)
        'eligibility_score': 0.22,      # Credit score + income + balance requirements
        'financial_need_match': 0.18,   # Product matches customer's financial situation
        'relationship_depth': 0.15,     # Tenure, product count, loyalty
        
        # TIER 2: Strategic Fit & Product Value (28%)
        'product_value': 0.12,          # NEW! Product-specific value (fees, rates, min balance, ROI)
        'product_pairing': 0.09,        # Cross-sell affinity, complementary products
        'channel_fit': 0.07,            # Digital vs branch preference alignment
        
        # TIER 3: Behavioral & Contextual (10%)
        'complexity_match': 0.04,       # Product sophistication vs customer level
        'intent_score': 0.03,           # Cross-sell receptivity
        'segment_affinity': 0.02,       # Peer behavior in segment
        'transaction_pattern': 0.01,    # Activity level alignment
        
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
        if 'product_id' in self.transactions_df.columns:
            for cid, group in self.transactions_df.groupby('customer_id'):
                self.customer_products[cid] = group['product_id'].unique().tolist()
        
        # Product popularity by segment
        self.segment_product_popularity = {}
        
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
            age, income, total_deposits, num_products, category, product
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
        relationship = self._calculate_relationship_depth(num_products, customer.get('tenure_months', 12))
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
        pairing = self._calculate_product_pairing(customer_id, product_id, category)
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
        transaction = self._calculate_transaction_pattern(customer.get('transaction_frequency', 'medium'))
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
        min_credit: float, min_income: float, min_balance: float
    ) -> Dict:
        """Calculate eligibility based on credit, income, and balance"""
        
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
        
        # Weighted eligibility score
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
    
    def _calculate_financial_need_match(
        self, age: int, income: float, deposits: float, 
        num_products: int, category: str, product: Dict
    ) -> Dict:
        """Match product to customer's financial life stage and needs"""
        
        score = 0.5  # Default moderate match
        explanation = ""
        
        # Age-based needs
        if age < 35:
            if category in ['Checking', 'Credit_Card', 'Student_Loan']:
                score = 0.9
                explanation = "Excellent match for young professionals"
            elif category in ['Investment', 'Retirement_IRA']:
                score = 0.6
                explanation = "Good for early retirement planning"
        elif age >= 55:
            if category in ['Retirement_IRA', 'CD', 'Investment']:
                score = 0.95
                explanation = "Perfect for retirement-focused customers"
            elif category == 'Mortgage':
                score = 0.3
                explanation = "Less relevant for retirement age"
        else:
            # Middle age (35-54)
            if category in ['Mortgage', 'Investment', 'Insurance']:
                score = 0.9
                explanation = "Ideal for wealth-building phase"
        
        # Deposit-based needs
        if deposits > 100000:
            if category in ['Investment', 'Wealth_Management', 'Premium_Checking']:
                score = max(score, 0.95)
                explanation = "Premium products for high net worth"
        elif deposits < 50000:
            if category in ['Basic_Checking', 'Savings', 'Credit_Building']:
                score = max(score, 0.85)
                explanation = "Foundation products for wealth building"
        
        # Income-based needs
        if income < 60000 and age < 35:
            if 'Student' in str(product.get('product_name', '')) or 'Basic' in str(product.get('product_name', '')):
                score = max(score, 0.9)
                explanation = "Affordable starter products"
        
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
        min_balance = float(product.get('min_balance', 0))
        interest_rate = float(product.get('interest_rate', product.get('interest_rate_apy', 0)))
        subcategory = product.get('subcategory', '').lower()
        
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
        
        # Adjust based on customer affordability
        max_affordable_fee = customer_deposits * 0.005  # 0.5% of deposits
        if annual_fee > max_affordable_fee:
            fee_score *= 0.7  # Penalty for high fees relative to customer wealth
            explanations.append(f"(adjusted down: fee high vs deposits)")
        
        # Wealth Investors: premium fee-based products are acceptable (don't over-penalize)
        if is_wealth_investor and annual_fee > 0:
            fee_score = min(1.0, fee_score + 0.12)
            explanations.append("(Wealth segment: premium fee acceptable)")
        
        details['fee_score'] = fee_score
        score += fee_score * 0.30
        
        # ========== 2. INTEREST RATE SCORE (30%) - Higher is better for savings/investment ==========
        rate_score = 0
        if subcategory in ['savings', 'investment', 'cd', 'ira', 'money market']:
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
        elif subcategory in ['loan', 'credit', 'mortgage']:
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
        score += rate_score * 0.30
        
        # ========== 3. MINIMUM BALANCE SCORE (20%) - Lower is more accessible ==========
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
        score += balance_score * 0.20
        
        # ========== 4. FINANCIAL ROI SCORE (20%) - Overall value ==========
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
        score += roi_score * 0.20
        
        # ========== FINAL SCORE & EXPLANATION ==========
        score = max(0.0, min(1.0, score))  # Clamp to [0,1]
        
        # Build comprehensive explanation
        explanation_text = " | ".join(explanations[:3])  # Top 3 factors
        
        return {
            'score': score,
            'explanation': explanation_text,
            'details': details
        }
    
    def _calculate_product_pairing(self, customer_id: str, product_id: str, category: str) -> Dict:
        """Calculate affinity with customer's existing products"""
        
        # Define complementary product categories
        pairing_rules = {
            'Checking': ['Savings', 'Credit_Card', 'Investment', 'Debit_Card'],
            'Savings': ['CD', 'Investment', 'Retirement_IRA', 'Money_Market'],
            'Credit_Card': ['Loan', 'Investment', 'Line_of_Credit'],
            'Loan': ['Insurance', 'Investment', 'Refinance'],
            'Mortgage': ['Home_Equity_Line', 'Insurance', 'Investment', 'Refinance'],
            'Investment': ['Retirement_IRA', 'Wealth_Management', 'CD'],
            'Business_Checking': ['Business_Loan', 'Merchant_Services', 'Payroll'],
            'Agricultural_Loan': ['Crop_Insurance', 'Equipment_Financing', 'Operating_Line']
        }
        
        # Get customer's current products
        current_products = self.customer_products.get(customer_id, [])
        
        if not current_products:
            return {
                'score': 0.5,
                'explanation': "No existing products to pair with",
                'pairs_with': []
            }
        
        # Check if this product pairs with any existing product
        pairs_with = []
        for existing_pid in current_products:
            existing_product = self.products_df[self.products_df['product_id'] == existing_pid]
            if len(existing_product) > 0:
                existing_category = existing_product.iloc[0].get('category', '')
                complementary_categories = pairing_rules.get(existing_category, [])
                
                if category in complementary_categories:
                    pairs_with.append(existing_category)
        
        if pairs_with:
            score = min(0.9, 0.6 + (len(pairs_with) * 0.15))
            explanation = f"Pairs well with: {', '.join(pairs_with[:3])}"
        else:
            score = 0.4
            explanation = "Limited pairing with existing products"
        
        return {
            'score': score,
            'explanation': explanation,
            'pairs_with': pairs_with
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

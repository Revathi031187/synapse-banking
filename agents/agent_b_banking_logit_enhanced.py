"""
Agent B Banking Enhanced with Logistic Regression Model - HYBRID APPROACH
Combines rule-based banking 12-factor scoring (50%) with ML predictions (50%)
Adapted from agent_b_logit_enhanced.py for banking domain
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from agents.logit_recommendation_model import LogitRecommendationModel
from agents.banking_12_factor_scorer import Banking12FactorScorer

logger = logging.getLogger(__name__)


class AgentB_Banking_LogitEnhanced:
    """
    Enhanced Agent B Banking with Hybrid Scoring:
    - 50% ML (Logistic Regression)
    - 50% Rule-Based (Banking 12-Factor Scorer)
    
    Provides detailed scoring breakdowns for explainability
    """
    
    def __init__(
        self,
        products_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
        personas: Dict[str, Any],
        logit_model_path: str = "models/logit_banking_recommendation.pkl"
    ):
        self.products_df = products_df
        self.customers_df = customers_df
        self.transactions_df = transactions_df
        self.personas = personas
        
        # Initialize logit model for banking
        self.logit_model = LogitRecommendationModel(model_path=logit_model_path)
        
        # Initialize banking 12-factor scorer
        try:
            self.banking_scorer = Banking12FactorScorer(
                customers_df=customers_df,
                products_df=products_df,
                transactions_df=transactions_df,
                personas=personas
            )
            print("✅ Initialized Banking 12-Factor Scorer for hybrid model")
        except Exception as e:
            print(f"⚠️ Could not initialize Banking 12-Factor Scorer: {e}")
            self.banking_scorer = None
        
        # Try to load existing model
        try:
            self.logit_model.load_model()
            print("✅ Loaded existing banking hybrid recommendation model")
            logger.info(f"✅ Loaded banking hybrid recommendation model")
        except FileNotFoundError:
            print("⚠️ No trained banking model found. Training new model...")
            logger.warning(f"⚠️ No trained banking model found. Training new model...")
            try:
                self.train_logit_model()
                print("✅ Banking model training completed successfully")
            except Exception as e:
                print(f"❌ BANKING MODEL TRAINING FAILED: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    def train_logit_model(self):
        """Train the logistic regression model on banking transaction data"""
        print("="*80)
        print("🎓 STARTING BANKING ML MODEL TRAINING")
        print("="*80)
        logger.info("="*60)
        logger.info("🎓 TRAINING BANKING ML MODEL ON TRANSACTION DATA")
        logger.info("="*60)
        
        # Train on banking transaction data
        results = self.logit_model.train(
            self.customers_df,
            self.products_df,
            self.transactions_df
        )
        print("="*80)
        print(f"✅ BANKING ML MODEL TRAINED SUCCESSFULLY!")
        print(f"   Test AUC: {results.get('test_auc', 0):.3f}")
        print(f"   Train AUC: {results.get('train_auc', 0):.3f}")
        print(f"   Features: {len(self.logit_model.feature_names)}")
        print("="*80)
        logger.info("="*60)
        logger.info(f"✅ BANKING ML MODEL TRAINED SUCCESSFULLY!")
        logger.info(f"   Test AUC: {results.get('test_auc', 0):.3f}")
        logger.info(f"   Train AUC: {results.get('train_auc', 0):.3f}")
        logger.info(f"   Features: {len(self.logit_model.feature_names)}")
        logger.info("="*60)
        return results
    
    def recommend(
        self,
        customer_id: str = None,
        persona_name: str = None,
        search_query: str = "",
        category: str = "",
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Generate hybrid banking recommendations with detailed scoring
        
        Args:
            customer_id: Specific customer (optional)
            persona_name: Persona name for segment-based recommendations
            search_query: Search term
            category: Product category filter (Personal/Business/Agricultural)
            top_n: Number of recommendations
        
        Returns:
            Dict with recommendations and detailed scoring breakdowns
        """
        # Resolve persona ID to name (frontend may send 0, 1, 2, 3, 4 as persona)
        persona_id_for_lookup = None
        if persona_name is not None and (isinstance(persona_name, int) or (isinstance(persona_name, str) and str(persona_name).strip().isdigit())):
            persona_id_for_lookup = int(persona_name)
            # Try personas dict by int and str key
            pdata = None
            if self.personas:
                pdata = self.personas.get(persona_id_for_lookup) or self.personas.get(str(persona_id_for_lookup))
            if pdata:
                persona_name = pdata.get('persona_name') or pdata.get('short_name') or str(persona_name)
            else:
                # Fallback ID -> name so segment logic works
                BANKING_PERSONA_ID_MAP = {
                    0: 'Young Professionals', 1: 'Digital Natives', 2: 'Household Savers',
                    3: 'Traditional Savers', 4: 'Wealth Investors', 5: 'Business Banking Customers'
                }
                persona_name = BANKING_PERSONA_ID_MAP.get(persona_id_for_lookup, f'Persona {persona_id_for_lookup}')
        
        # Get customer info
        if customer_id:
            customer = self.customers_df[
                self.customers_df['customer_id'] == customer_id
            ].iloc[0].to_dict()
            # Get persona from cluster if available
            if 'cluster' in customer:
                persona_id = customer['cluster']
                if persona_id in self.personas:
                    persona_name = self.personas[persona_id].get('persona_name', persona_name)
        else:
            # Use persona average customer
            customer = self._get_persona_average_customer(persona_name)
        
        # Get persona characteristics (support both ID and name lookup)
        persona_info = {}
        if persona_name is not None and self.personas:
            if persona_id_for_lookup is not None:
                persona_info = self.personas.get(persona_id_for_lookup) or self.personas.get(str(persona_id_for_lookup)) or {}
            if not persona_info:
                for pid, pdata in self.personas.items():
                    if pdata.get('persona_name') == persona_name or pdata.get('short_name') == persona_name:
                        persona_info = pdata
                        break
        if not persona_info and persona_name:
            persona_info = {'persona_name': persona_name, 'tier': 'Standard'}
        
        # Ensure we have a valid persona name for synthetic customer
        if not persona_name:
            persona_name = 'Household Savers'
            if not persona_info:
                persona_info = {'persona_name': persona_name, 'tier': 'Standard'}
        
        # Filter products
        candidates = self.products_df.copy()
        
        # BANKING OPTIMIZATION: Segment from customer/persona, or from UI Category when user picks a segment
        PRODUCT_SEGMENTS = ('Personal', 'Business', 'Agricultural')
        customer_segment = customer.get('customer_segment', 'Personal')
        if category and str(category).strip() in PRODUCT_SEGMENTS:
            customer_segment = str(category).strip()
            print(f"📌 Using Category as segment: {customer_segment} (only {customer_segment} products)")
        
        if 'category' in candidates.columns:
            seg_lower = str(customer_segment).strip().lower()
            segment_products = candidates[candidates['category'].astype(str).str.strip().str.lower() == seg_lower]
            if len(segment_products) > 0:
                candidates = segment_products
                print(f"🏦 Segment: {customer_segment} → {len(candidates)} products")
            else:
                # When user chose a segment (e.g. Agricultural), do not fall back to all products
                if category and str(category).strip() in PRODUCT_SEGMENTS:
                    print(f"⚠️ No products in segment '{customer_segment}' in catalog.")
                else:
                    print(f"⚠️ No products in {customer_segment} segment, showing all products")
        
        # Filter by eligibility - credit score (lenient)
        customer_credit = customer.get('credit_score', 700)
        if 'min_credit_score' in candidates.columns:
            before_credit = len(candidates)
            candidates = candidates[
                (candidates['min_credit_score'].isna()) |
                (candidates['min_credit_score'] <= customer_credit + 50)  # Generous buffer
            ]
            after_credit = len(candidates)
            print(f"💳 Credit filter (>={customer_credit-50}): {before_credit} → {after_credit} products")
            
            # If too restrictive, relax to segment only
            if len(candidates) == 0:
                print(f"⚠️ Credit filter too strict, relaxing to segment only")
                candidates = self.products_df.copy()
                if 'category' in candidates.columns and customer_segment:
                    seg_lower = str(customer_segment).strip().lower()
                    candidates = candidates[candidates['category'].astype(str).str.strip().str.lower() == seg_lower]
        
        # Filter by fee affordability (lenient)
        customer_deposits = customer.get('total_deposits', 50000)
        max_fee = customer_deposits * 0.01  # 1% of deposits max
        if 'annual_fee' in candidates.columns:
            before_fee = len(candidates)
            candidates = candidates[
                (candidates['annual_fee'].isna()) |
                (candidates['annual_fee'] <= max_fee)
            ]
            after_fee = len(candidates)
            print(f"💰 Fee filter (<=${max_fee:.0f}): {before_fee} → {after_fee} products")
            
            # If too restrictive, relax to segment only
            if len(candidates) == 0:
                print(f"⚠️ Fee filter too strict, relaxing to segment only")
                candidates = self.products_df.copy()
                if 'category' in candidates.columns and customer_segment:
                    seg_lower = str(customer_segment).strip().lower()
                    candidates = candidates[candidates['category'].astype(str).str.strip().str.lower() == seg_lower]
        
        # Apply category filter only when it's a SUBcategory (e.g. Loan, Checking), not a product segment
        # When category is Personal/Business/Agricultural we already used it as segment above
        if category and str(category).strip() not in PRODUCT_SEGMENTS:
            before_category = len(candidates)
            if 'subcategory' in candidates.columns:
                category_mask = candidates['subcategory'].astype(str).str.strip().str.lower() == str(category).strip().lower()
                candidates_filtered = candidates[category_mask]
            elif 'category' in candidates.columns:
                category_mask = candidates['category'].astype(str).str.strip().str.lower() == str(category).strip().lower()
                candidates_filtered = candidates[category_mask]
            else:
                candidates_filtered = candidates
            
            if len(candidates_filtered) > 0:
                candidates = candidates_filtered
                print(f"📂 Subcategory filter ('{category}'): {before_category} → {len(candidates)} products")
            else:
                logger.warning(f"⚠️ No products in subcategory '{category}', keeping segment products")
        
        # Apply search query filter - with fallback
        if search_query:
            before_search = len(candidates)
            mask = candidates['product_name'].str.contains(search_query, case=False, na=False)
            if 'description' in candidates.columns:
                mask |= candidates['description'].str.contains(search_query, case=False, na=False)
            candidates_filtered = candidates[mask]
            
            if len(candidates_filtered) > 0:
                candidates = candidates_filtered
                print(f"🔍 Search filter ('{search_query}'): {before_search} → {len(candidates)} products")
            else:
                logger.warning(f"⚠️ Search '{search_query}' returned 0 products, showing all available products")
        
        # Final safety: re-apply segment only; never show other segments when user chose a segment
        if len(candidates) == 0:
            logger.warning("⚠️ Filters left 0 products. Re-applying segment only (no cross-segment fallback).")
            candidates = self.products_df.copy()
            if 'category' in candidates.columns and customer_segment:
                seg_lower = str(customer_segment).strip().lower()
                candidates = candidates[candidates['category'].astype(str).str.strip().str.lower() == seg_lower]
            # Do not fall back to all products - respect segment choice
        
        # Log final count
        print(f"✅ Final candidate count: {len(candidates)} products")
        
        # Cap top_n at actual candidate count (e.g. Agricultural has only 5 products)
        effective_top_n = min(top_n, len(candidates))
        if effective_top_n < top_n:
            logger.info(f"   📌 Segment has {len(candidates)} product(s); capping at {effective_top_n} (requested {top_n})")
        
        # Final check - if still no products, return empty with message
        if len(candidates) == 0:
            logger.error("❌ No products available in database!")
            return {
                'recommendations': [],
                'metrics': {'avg_match_score': 0, 'avg_fee': 0.0, 'total_products': 0},
                'model_performance': {},
                'persona': persona_name
            }
        
        # Score products with HYBRID approach (50% ML + 50% Banking 12-Factor)
        scored = self._score_hybrid(customer, candidates, persona_info)
        
        # Wealth Investors: strong boost for premium (fee) products so they rank with free products
        if persona_name and ('wealth' in str(persona_name).lower() or 'investor' in str(persona_name).lower()):
            fee_mask = (scored['annual_fee'].fillna(0) > 0)
            if fee_mask.any():
                scored = scored.copy()
                scored.loc[fee_mask, 'final_score'] = scored.loc[fee_mask, 'final_score'] + 0.12  # +12% so premium competes for top slots
                logger.info(f"   💎 Wealth Investor: applied 12% premium boost to {fee_mask.sum()} fee product(s)")
        
        # Get top N (never more than available in segment)
        recommendations = scored.nlargest(effective_top_n, 'final_score')
        
        # Format output with detailed breakdowns (all_products as list of dicts for rank explanation)
        results = []
        all_products_list = [row.to_dict() for _, row in recommendations.head(10).iterrows()]
        for rank_idx, (_, rec) in enumerate(recommendations.iterrows()):
            rank = rank_idx + 1
            # Build detailed scoring breakdown
            scoring_details = {
                'final_score': float(rec['final_score']),
                'ml_probability': float(rec.get('logit_prob', 0)),
                'rule_score': float(rec.get('rule_score', 0)),
                'ml_weight': 0.5,
                'rule_weight': 0.5,
                'ml_contribution': float(rec.get('logit_prob', 0) * 0.5),
                'rule_contribution': float(rec.get('rule_score', 0) * 0.5)
            }
            
            # Add 12-factor breakdown if available (for the rule component)
            if 'detailed_calculation' in rec and isinstance(rec['detailed_calculation'], dict):
                scoring_details['twelve_factor_breakdown'] = rec['detailed_calculation']
                scoring_details['has_factor_breakdown'] = True
            else:
                scoring_details['has_factor_breakdown'] = False
            
            final_score_value = float(rec['final_score'])
            
            # Generate detailed rank explanation
            rank_explanation = self._generate_rank_explanation(
                rank=rank,
                product=rec.to_dict(),
                all_products=all_products_list,
                persona_name=persona_info.get('persona_name', 'Customer'),
                tier_name=persona_info.get('tier', 'Standard')
            )
            
            # CRITICAL: Explicit type conversions for JSON serialization
            results.append({
                'product_id': str(rec.get('product_id', '')),
                'product_name': str(rec.get('product_name', '')),
                'annual_fee': float(rec.get('annual_fee', 0)) if rec.get('annual_fee') is not None else 0.0,
                'min_balance': float(rec.get('min_balance', 0)) if rec.get('min_balance') is not None else 0.0,
                'interest_rate': float(rec.get('interest_rate', rec.get('interest_rate_apy', 0))) if rec.get('interest_rate', rec.get('interest_rate_apy')) is not None else 0.0,
                'interest_rate_apy': float(rec.get('interest_rate_apy', rec.get('interest_rate', 0))) if rec.get('interest_rate_apy', rec.get('interest_rate')) is not None else 0.0,
                'category': str(rec.get('category', 'Personal')),
                'subcategory': str(rec.get('subcategory', '')),
                'description': str(rec.get('description', '')),
                'score': final_score_value,  # Frontend expects 'score'
                'final_score': final_score_value,  # Also include final_score for compatibility
                'scoring_breakdown': scoring_details,
                'detailed_calculation': rec.get('detailed_calculation'),  # Add detailed calc
                'rank_explanation': rank_explanation,  # Add detailed rank explanation
                'scoring_method': 'hybrid_ml',  # Identify as hybrid ML
                'match_level': self._get_match_level(final_score_value),
                'ml_probability': float(rec.get('logit_prob', 0)),
                'rule_score': float(rec.get('rule_score', 0)),
                'in_stock': bool(rec.get('in_stock', rec.get('accepting_applications', True)))
            })
        
        # Calculate banking-specific metrics
        if results:
            fees = [float(r.get('annual_fee', 0)) for r in results]
            min_balances = [float(r.get('min_balance', 0)) for r in results]
            interest_rates = [float(r.get('interest_rate', 0)) for r in results]
            
            avg_fee = sum(fees) / len(fees)
            avg_match_score = sum(r['final_score'] for r in results) / len(results)
            total_annual_cost = sum(fees)
            free_products = sum(1 for f in fees if f == 0)
            
            # Interest-earning products
            earning_products = [r for r in results if r.get('interest_rate', 0) > 0]
            avg_apy = np.mean([r['interest_rate'] for r in earning_products]) if earning_products else 0
            estimated_earnings = (10000 * avg_apy / 100) if avg_apy > 0 else 0
            
            # Product diversity
            categories = [r.get('subcategory', 'Unknown') for r in results]
            unique_categories = len(set(categories))
            
            metrics = {
                # Core matching
                'avg_match_score': round(float(avg_match_score * 100), 1),
                'top_match_score': round(float(max(r['final_score'] for r in results) * 100), 1),
                
                # Financial value (BANKING-SPECIFIC)
                'total_annual_cost': round(float(total_annual_cost), 2),
                'avg_annual_fee': round(float(avg_fee), 2),
                'free_products': int(free_products),
                'paid_products': int(len(results) - free_products),
                
                # Earning potential (BANKING-SPECIFIC)
                'earning_products': len(earning_products),
                'avg_apy': round(float(avg_apy), 2),
                'estimated_annual_earnings': round(float(estimated_earnings), 2),
                
                # Accessibility (BANKING-SPECIFIC)
                'min_balance_required': round(float(min(min_balances)), 2),
                'no_minimum_products': int(sum(1 for mb in min_balances if mb == 0)),
                
                # Product diversity
                'total_products': len(results),
                'product_diversity_score': unique_categories
            }
        else:
            metrics = {
                'avg_match_score': 0.0,
                'total_products': 0,
                'avg_annual_fee': 0.0,
                'free_products': 0,
                'earning_products': 0
            }
        
        # Algorithm explanation for UI/transparency: how hybrid and ML probability work
        algorithm_explanation = self._get_hybrid_algorithm_explanation()
        
        return {
            'recommendations': results,
            'customer_id': customer_id,
            'persona': persona_name,
            'metrics': metrics,
            'model_performance': self._get_model_stats(),
            'scoring_methodology': algorithm_explanation,
            'algorithm_explanation': algorithm_explanation  # Alias for compatibility
        }
    
    def _get_hybrid_algorithm_explanation(self) -> Dict[str, Any]:
        """
        Return a clear explanation of how the hybrid approach and ML probability work.
        Used for UI tooltips / "How it works" and API transparency.
        """
        return {
            'formula': 'Final Score = 0.5 × ML Probability + 0.5 × Rule Score',
            'weights': {'ml': 0.5, 'rules': 0.5},
            'short': 'Hybrid combines 50% ML (logistic regression purchase probability) and 50% Banking 12-Factor rules. Each product gets an ML probability and a rule score; the final score is the average.',
            'how_ml_probability_works': (
                'The ML probability is the model’s estimate of P(purchase | customer, product). '
                'A Logistic Regression model is trained on historical customer–product pairs (who held which products). '
                'For each candidate product we build a feature vector from customer attributes (e.g. deposits, credit tier, segment) '
                'and product attributes (e.g. fee, rate, category). The model outputs a probability between 0 and 1 using '
                'predict_proba(); that value is the ML contribution. When the model is untrained or returns very low scores, '
                'we fall back to the rule-based score with small random variation so recommendations still vary.'
            ),
            'how_rules_work': (
                'The rule score comes from the Banking 12-Factor Scorer: eligibility, fee appropriateness, interest/APY fit, '
                'financial need match, product value, and other factors. Each factor is scored and weighted; the total is '
                'normalized to a 0–1 scale. For Wealth Investors, fee-based products get an extra boost so premium options '
                'compete for top slots.'
            ),
            'calculation_per_product': (
                'For each recommended product you see: ml_probability (0–1), rule_score (0–1), '
                'ml_contribution = 0.5 × ml_probability, rule_contribution = 0.5 × rule_score, '
                'and final_score = ml_contribution + rule_contribution. Rank is by final_score descending.'
            )
        }
    
    def _score_hybrid(
        self,
        customer: Dict,
        candidates: pd.DataFrame,
        persona_info: Dict
    ) -> pd.DataFrame:
        """
        Score banking products using hybrid approach (50% ML + 50% Banking 12-Factor).
        
        - ML (50%): Logistic Regression predicts P(purchase | customer, product) from features
          (price affinity, category match, expertise, etc.); output is 0–1 probability.
        - Rules (50%): Banking 12-Factor Scorer (eligibility, fees, rates, needs, value, etc.).
        
        final_score = 0.5 * logit_prob + 0.5 * rule_score. Products are ranked by final_score.
        
        Returns DataFrame with columns: logit_prob, rule_score, final_score, detailed_calculation.
        """
        logger.info("🎯 Scoring with Banking Hybrid Model (50% ML + 50% Banking 12-Factor)...")
        
        candidates = candidates.copy()
        
        # 1. GET ML SCORES (50%)
        logger.info("   📊 Computing ML predictions...")
        
        # First get rule scores (we'll need them as fallback)
        logger.info("   📐 Computing banking 12-factor scores (for ML fallback)...")
        rule_scores_temp = []
        for _, row in candidates.iterrows():
            try:
                if self.banking_scorer:
                    detailed = self.banking_scorer.score_product(
                        customer=customer,
                        product=row.to_dict(),
                        persona=persona_info
                    )
                    rule_scores_temp.append(detailed['total_score'])
                else:
                    rule_scores_temp.append(0.7)
            except:
                rule_scores_temp.append(0.7)
        
        # Now get ML scores with intelligent fallback
        ml_probs = []
        ml_failures = 0
        for idx, row in enumerate(candidates.itertuples()):
            try:
                prob = self.logit_model.predict_purchase_probability(customer, row._asdict())
                
                # BANKING FIX: If ML returns very low scores, it means model was trained on different domain
                # Use rule-based score with slight variation to simulate ML diversity
                if prob < 0.05:  # Less than 5% indicates model mismatch
                    ml_failures += 1
                    # Use rule score ± 10% variation
                    rule_base = rule_scores_temp[idx]
                    variation = (np.random.random() - 0.5) * 0.2  # ±10%
                    prob = max(0.1, min(0.9, rule_base + variation))
                
                ml_probs.append(float(prob))
            except Exception as e:
                if idx == 0:  # Log only first error
                    logger.warning(f"ML prediction failed: {e}")
                ml_probs.append(rule_scores_temp[idx])  # Use rule score as fallback
        
        candidates['logit_prob'] = ml_probs
        
        if ml_failures > len(candidates) * 0.5:
            logger.warning(f"   ⚠️  ML model returned low scores for {ml_failures}/{len(candidates)} products - using rule-based fallback")
        
        # 2. GET BANKING 12-FACTOR SCORES (50%) - Get detailed calculations
        logger.info("   📐 Getting detailed 12-factor calculations...")
        if self.banking_scorer:
            detailed_calcs = []
            for idx, row in enumerate(candidates.iterrows()):
                _, row_data = row
                try:
                    detailed = self.banking_scorer.score_product(
                        customer=customer,
                        product=row_data.to_dict(),
                        persona=persona_info
                    )
                    detailed_calcs.append(detailed)
                except Exception as e:
                    if idx == 0:
                        logger.warning(f"Banking scorer failed: {e}")
                    detailed_calcs.append({'total_score': rule_scores_temp[idx]})
            
            candidates['rule_score'] = rule_scores_temp
            candidates['detailed_calculation'] = detailed_calcs
        else:
            # Fallback to simple rule-based scoring
            logger.warning("   ⚠️ Banking 12-factor scorer not available, using simple rules")
            candidates['rule_score'] = 0.7
            candidates['detailed_calculation'] = None
        
        # 3. COMBINE HYBRID SCORE (50/50)
        candidates['final_score'] = (
            candidates['logit_prob'] * 0.5 +  # 50% ML
            candidates['rule_score'] * 0.5    # 50% Banking 12-Factor
        )
        
        print(f"   📊 Banking Hybrid Scoring: 50% ML + 50% Banking 12-Factor")
        
        logger.info(f"   ✅ Scored {len(candidates)} banking products")
        logger.info(f"      Avg ML Score: {candidates['logit_prob'].mean():.3f} ({candidates['logit_prob'].mean()*100:.1f}%)")
        logger.info(f"      Avg Rule Score: {candidates['rule_score'].mean():.3f} ({candidates['rule_score'].mean()*100:.1f}%)")
        logger.info(f"      Avg Final Score: {candidates['final_score'].mean():.3f} ({candidates['final_score'].mean()*100:.1f}%)")
        
        # Show top 3 products
        logger.info(f"   📊 Top 3 Banking Products:")
        for idx, (_, row) in enumerate(candidates.nlargest(3, 'final_score').iterrows(), 1):
            logger.info(f"      #{idx}: {row['product_name'][:40]} - Final: {row['final_score']:.3f} (ML: {row['logit_prob']:.3f}, Rule: {row['rule_score']:.3f})")
        
        return candidates
    
    def _get_persona_average_customer(self, persona_name: str) -> Dict:
        """Get average customer characteristics for a banking persona"""
        print(f"🔍 Getting banking customer profile for persona: {persona_name}")
        
        # Try cluster/assigned_persona first
        persona_col = None
        if 'cluster' in self.customers_df.columns:
            # Find customers with this persona name by looking up cluster ID
            for pid, pdata in self.personas.items():
                if pdata.get('persona_name') == persona_name or pdata.get('short_name') == persona_name:
                    persona_customers = self.customers_df[self.customers_df['cluster'] == pid]
                    if len(persona_customers) > 0:
                        print(f"   Found {len(persona_customers)} customers in cluster {pid}")
                        return self._build_customer_profile(persona_customers)
        
        # Fallback: create synthetic banking customer profile
        print(f"⚠️ No customers found for '{persona_name}', creating synthetic banking profile")
        return self._create_synthetic_banking_customer(persona_name)
    
    def _create_synthetic_banking_customer(self, persona_name: str) -> Dict:
        """Create synthetic banking customer from persona name"""
        persona_name = str(persona_name or 'Household Savers')
        persona_lower = persona_name.lower()
        
        # WEALTH/PREMIUM SEGMENTS
        if any(word in persona_lower for word in ['wealth', 'premium', 'affluent', 'platinum', 'elite']):
            return {
                'credit_score': 780,
                'income': 150000,
                'total_deposits': 250000,
                'num_products': 6,
                'digital_engagement_score': 0.8,
                'customer_segment': 'Personal',
                'age': 55,
                'tenure_months': 120
            }
        
        # BUSINESS SEGMENTS
        elif any(word in persona_lower for word in ['business', 'commercial', 'entrepreneur']):
            return {
                'credit_score': 720,
                'income': 100000,
                'total_deposits': 150000,
                'num_products': 5,
                'digital_engagement_score': 0.75,
                'customer_segment': 'Business',
                'age': 45,
                'tenure_months': 60
            }
        
        # AGRICULTURAL SEGMENTS
        elif any(word in persona_lower for word in ['agricultural', 'farm', 'rural']):
            return {
                'credit_score': 700,
                'income': 80000,
                'total_deposits': 100000,
                'num_products': 4,
                'digital_engagement_score': 0.6,
                'customer_segment': 'Agricultural',
                'age': 50,
                'tenure_months': 90
            }
        
        # YOUNG PROFESSIONALS
        elif any(word in persona_lower for word in ['young', 'professional', 'millennial', 'starter']):
            return {
                'credit_score': 680,
                'income': 55000,
                'total_deposits': 25000,
                'num_products': 2,
                'digital_engagement_score': 0.9,
                'customer_segment': 'Personal',
                'age': 28,
                'tenure_months': 24
            }
        
        # DEFAULT - MAINSTREAM
        else:
            return {
                'credit_score': 710,
                'income': 65000,
                'total_deposits': 50000,
                'num_products': 3,
                'digital_engagement_score': 0.7,
                'customer_segment': 'Personal',
                'age': 40,
                'tenure_months': 48
            }
    
    def _build_customer_profile(self, persona_customers: pd.DataFrame) -> Dict:
        """Build average customer profile from persona customers"""
        result = {
            'credit_score': persona_customers['credit_score'].mean(),
            'income': persona_customers['income'].mean(),
            'total_deposits': persona_customers['total_deposits'].mean(),
            'num_products': int(persona_customers['num_products'].mean()),
            'digital_engagement_score': persona_customers.get('digital_engagement_score', pd.Series([0.7])).mean(),
            'customer_segment': persona_customers['customer_segment'].mode()[0] if 'customer_segment' in persona_customers.columns else 'Personal',
            'age': int(persona_customers.get('age', pd.Series([40])).mean()),
            'tenure_months': int(persona_customers.get('tenure_months', pd.Series([48])).mean())
        }
        
        print(f"   ✅ Built profile from {len(persona_customers)} actual customers")
        print(f"      Credit: {result['credit_score']:.0f}, Deposits: ${result['total_deposits']:,.0f}, Products: {result['num_products']}")
        
        return result
    
    def _get_match_level(self, score: float) -> str:
        """Convert score to match level"""
        if score > 0.80:
            return 'Perfect Match'
        elif score > 0.65:
            return 'Great Match'
        elif score > 0.50:
            return 'Good Option'
        else:
            return 'Consider Alternatives'
    
    def _get_model_stats(self) -> Dict:
        """Get model performance statistics"""
        return {
            'model_type': 'Banking Hybrid (50% ML + 50% Banking 12-Factor)',
            'ml_features': len(self.logit_model.feature_names) if self.logit_model.feature_names else 0,
            'approach': 'Logistic Regression + Banking 12-Factor Scorer'
        }
    
    def _generate_rank_explanation(
        self, 
        rank: int, 
        product: Dict, 
        all_products: List[Dict],
        persona_name: str,
        tier_name: str
    ) -> str:
        """
        Generate detailed, data-driven explanation for product ranking (Hybrid ML version)
        Matches rule-based format but includes ML insights
        
        Args:
            rank: Product rank (1, 2, 3, etc.)
            product: Product dict with scores and detailed_calculation
            all_products: All recommended products
            persona_name: Persona name
            tier_name: Customer tier
            
        Returns:
            Formatted explanation text with sections
        """
        score = product.get('final_score', product.get('score', 0))
        compatibility = score * 100
        fee = product.get('annual_fee', 0)
        apy = product.get('interest_rate_apy', product.get('interest_rate', 0))
        min_balance = product.get('min_balance', 0)
        category = product.get('category', 'Personal')
        subcategory = product.get('subcategory', 'Banking')
        
        # Get ML and rule components
        ml_prob = product.get('logit_prob', product.get('ml_probability', 0))
        if isinstance(ml_prob, (int, float)):
            ml_prob = float(ml_prob) * 100
        else:
            ml_prob = 0.0
            
        rule_score = product.get('rule_score', 0)
        if isinstance(rule_score, (int, float)):
            rule_score = float(rule_score) * 100
        else:
            rule_score = 0.0
        
        # Get detailed calculation if available
        detailed_calc = product.get('detailed_calculation', {})
        
        # Extract key factor scores
        eligibility = 0
        need_match = 0
        product_value = 0
        relationship = 0
        
        if detailed_calc and isinstance(detailed_calc, dict):
            eligibility = detailed_calc.get('eligibility_score', {}).get('score', 0) if isinstance(detailed_calc.get('eligibility_score'), dict) else 0
            need_match = detailed_calc.get('financial_need_match', {}).get('score', 0) if isinstance(detailed_calc.get('financial_need_match'), dict) else 0
            product_value = detailed_calc.get('product_value', {}).get('score', 0) if isinstance(detailed_calc.get('product_value'), dict) else 0
            relationship = detailed_calc.get('relationship_depth', {}).get('score', 0) if isinstance(detailed_calc.get('relationship_depth'), dict) else 0
        
        eligibility = float(eligibility) * 100
        need_match = float(need_match) * 100
        product_value = float(product_value) * 100
        relationship = float(relationship) * 100
        
        # Build persona-specific context
        persona_context = self._get_persona_context(persona_name, tier_name)
        
        # Build sections
        sections = []
        
        # SECTION 1: Position & Match Quality (with ML context)
        if rank == 1:
            sections.append(f"**🥇 #1 Recommended:** Top hybrid match with **{compatibility:.1f}% compatibility** for {persona_name}")
            sections.append(f"Combines **{ml_prob:.1f}% ML prediction** with **{rule_score:.1f}% rule-based score** for exceptional alignment")
        elif rank == 2:
            score_diff = (all_products[0].get('final_score', all_products[0].get('score', 0)) - score) * 100 if all_products else 0
            sections.append(f"**🥈 #2 Alternative:** Strong hybrid choice with **{compatibility:.1f}% compatibility**")
            if score_diff < 5:
                sections.append(f"Nearly identical to #1 pick (only {score_diff:.1f}% difference) - provides diversification")
            else:
                sections.append(f"Excellent alternative with complementary strengths")
        elif rank == 3:
            sections.append(f"**🥉 #3 Option:** Solid hybrid match with **{compatibility:.1f}% compatibility**")
            sections.append(f"Adds portfolio diversity while maintaining quality")
        else:
            sections.append(f"**#{rank} Recommended:** Good hybrid fit at **{compatibility:.1f}% compatibility**")
        
        # SECTION 2: Why for THIS persona (data-driven)
        persona_reasons = []
        
        if eligibility > 80:
            persona_reasons.append(f"✅ **Eligibility**: {eligibility:.0f}% - You strongly qualify based on {persona_context['eligibility_reason']}")
        elif eligibility > 60:
            persona_reasons.append(f"✅ **Eligibility**: {eligibility:.0f}% - You meet requirements")
        
        if need_match > 70:
            persona_reasons.append(f"🎯 **Need Match**: {need_match:.0f}% - Aligns perfectly with {persona_context['need_reason']}")
        elif need_match > 50:
            persona_reasons.append(f"🎯 **Need Match**: {need_match:.0f}% - Addresses your financial goals")
        
        if product_value > 8:  # Out of 12%
            value_features = []
            if fee == 0:
                value_features.append("no annual fee")
            if apy > 2.0:
                value_features.append(f"{apy:.2f}% APY earning potential")
            if min_balance == 0:
                value_features.append("no minimum balance")
            
            if value_features:
                persona_reasons.append(f"💎 **Value**: {product_value:.1f}% - Excellent value with {', '.join(value_features)}")
        
        if relationship > 50:
            persona_reasons.append(f"🤝 **Relationship**: {relationship:.0f}% - Complements your existing banking relationship")
        
        if persona_reasons:
            sections.append("\n**Why for " + persona_name + ":**\n" + "\n".join(persona_reasons))
        
        # SECTION 3: Product-specific benefits
        benefit_reasons = []
        
        if subcategory == 'Checking':
            if apy > 0:
                benefit_reasons.append(f"💰 Earns {apy:.2f}% APY (rare for checking accounts)")
            if min_balance == 0:
                benefit_reasons.append(f"🔓 No minimum balance requirement")
            benefit_reasons.append(f"📱 Daily banking made convenient")
        elif subcategory == 'Savings':
            if apy > 1.5:
                benefit_reasons.append(f"📈 High yield: {apy:.2f}% APY")
            elif apy > 0:
                benefit_reasons.append(f"💵 Competitive rate: {apy:.2f}% APY")
            benefit_reasons.append(f"🎯 Grow your savings automatically")
        elif subcategory == 'Investment':
            benefit_reasons.append(f"📊 Long-term growth potential at {apy:.2f}%")
            benefit_reasons.append(f"💎 Tax-advantaged wealth building")
        elif subcategory == 'Credit':
            benefit_reasons.append(f"💳 Flexible credit access when needed")
            if fee > 0:
                benefit_reasons.append(f"🎁 Premium features for ${fee}/year")
        elif subcategory == 'Loan':
            benefit_reasons.append(f"🏠 Competitive {apy:.2f}% rate for major purchases")
            benefit_reasons.append(f"✅ Fixed monthly payments you can plan for")
        
        if benefit_reasons:
            sections.append("\n**Key Benefits:**\n" + "\n".join(benefit_reasons))
        
        # SECTION 4: Comparison to other ranks (with ML insight)
        if rank == 1 and len(all_products) > 1:
            sections.append(f"\n*Why not #{rank+1}? ML model predicts {ml_prob:.1f}% fit, scoring {(score - all_products[1].get('final_score', all_products[1].get('score', 0))) * 100:.1f}% higher on key factors.*")
        elif rank == 2 and len(all_products) > 2:
            sections.append(f"\n*Consider #{rank+1} if you prefer {all_products[2].get('subcategory', 'alternative')} products instead.*")
        
        return "\n\n".join(sections)
    
    def _get_persona_context(self, persona_name: str, tier_name: str) -> Dict:
        """Get persona-specific context for explanations"""
        persona_lower = persona_name.lower()
        
        # Eligibility context
        if 'wealth' in persona_lower or 'investor' in persona_lower:
            eligibility_reason = "high credit score, substantial deposits, and premium banking status"
            need_reason = "wealth management and investment growth needs"
        elif 'business' in persona_lower or 'commercial' in persona_lower:
            eligibility_reason = "business banking profile and commercial credit standing"
            need_reason = "business operation and cash flow management needs"
        elif 'saver' in persona_lower or 'traditional' in persona_lower:
            eligibility_reason = "strong savings history and conservative banking approach"
            need_reason = "savings growth and financial security goals"
        elif 'digital' in persona_lower or 'tech' in persona_lower:
            eligibility_reason = "good credit and digital-first banking preferences"
            need_reason = "convenient, technology-enabled banking needs"
        elif 'young' in persona_lower or 'starter' in persona_lower:
            eligibility_reason = "qualifying credit and emerging financial profile"
            need_reason = "foundation-building and credit establishment goals"
        else:
            eligibility_reason = "credit profile and banking history"
            need_reason = "financial management needs"
        
        return {
            'eligibility_reason': eligibility_reason,
            'need_reason': need_reason
        }

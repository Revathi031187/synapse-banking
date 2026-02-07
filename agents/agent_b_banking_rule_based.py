"""
Agent B Banking with Rule-Based + ML (Logit) Hybrid Approach
Matches Academy Sports implementation with banking-specific rules
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentB_Banking_RuleBased:
    """
    Banking Agent B with Rule-Based + ML Hybrid Recommendations
    
    Combines:
    1. Rule-Based Scoring (50%): Banking-specific business rules
    2. ML Probability (50%): Logit model (when available)
    3. 12-Factor Scoring: Detailed compatibility breakdown
    """
    
    def __init__(
        self,
        customers_df: pd.DataFrame = None,
        products_df: pd.DataFrame = None,
        transactions_df: pd.DataFrame = None,
        personas: Dict = None,
        data_path: str = 'data/preloaded/fmb_bank',
        agent_a=None
    ):
        """Initialize Rule-Based Banking Agent B"""
        # Load data if not provided
        if data_path and (customers_df is None or products_df is None):
            from pathlib import Path
            data_dir = Path(data_path)
            
            if customers_df is None:
                customers_df = pd.read_csv(data_dir / 'customers.csv')
            if products_df is None:
                products_df = pd.read_csv(data_dir / 'products.csv')
            if transactions_df is None:
                try:
                    transactions_df = pd.read_csv(data_dir / 'transactions.csv')
                except:
                    transactions_df = pd.DataFrame()
        
        self.customers_df = customers_df if customers_df is not None else pd.DataFrame()
        self.products_df = products_df if products_df is not None else pd.DataFrame()
        self.transactions_df = transactions_df if transactions_df is not None else pd.DataFrame()
        self.personas = personas or {}
        self.agent_a = agent_a
        self.data_path = data_path
        
        # Initialize 12-Factor Scorer
        try:
            from agents.enhanced_12_factor_scorer import Enhanced12FactorScorer
            logger.info("🔍 [Banking Agent B] Initializing 12-factor scorer...")
            self.enhanced_scorer = Enhanced12FactorScorer(
                customers_df=self.customers_df,
                products_df=self.products_df,
                purchases_df=self.transactions_df,
                personas=self.personas
            )
            logger.info("✅ [Banking Agent B] 12-factor scorer initialized!")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize 12-factor scorer: {e}")
            self.enhanced_scorer = None
        
        # Try to initialize Logit Model (ML component)
        self.logit_model = None
        try:
            from pathlib import Path as PathLib
            from agents.logit_recommendation_model import LogitRecommendationModel
            model_path = PathLib(data_path) / "models" / "logit_banking.pkl"
            self.logit_model = LogitRecommendationModel(model_path=str(model_path))
            if model_path.exists():
                self.logit_model.load_model()
                logger.info("✅ Loaded logit model for ML scoring")
            else:
                logger.info("⚠️ No pre-trained logit model found - using rule-based only")
                self.logit_model = None
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize logit model: {e}")
            self.logit_model = None
        
        logger.info(f"🏦 Banking Agent B (Rule-Based + ML) initialized")
        logger.info(f"  - {len(self.customers_df)} customers")
        logger.info(f"  - {len(self.products_df)} products")
        logger.info(f"  - {len(self.transactions_df)} transactions")
        logger.info(f"  - ML Model: {'✅ Available' if self.logit_model else '❌ Not available (rule-based only)'}")
    
    def get_all_recommendations(
        self,
        customer_id: str,
        search_term: str = None,
        chromadb_collection=None
    ) -> Dict:
        """
        Get all types of recommendations for a customer
        
        Uses hybrid approach:
        - 50% Rule-Based Score (banking business rules)
        - 50% ML Probability (logit model, if available)
        """
        try:
            # Get customer info
            customer = self.customers_df[self.customers_df['customer_id'] == customer_id]
            if len(customer) == 0:
                return {
                    'error': 'Customer not found',
                    'customer_id': customer_id,
                    'tailored_recommendations': [],
                    'similar_products': [],
                    'segment_recommendations': []
                }
            
            customer = customer.iloc[0]
            
            logger.info(f"🎯 Getting recommendations for customer {customer_id}")
            logger.info(f"   Customer: {customer.get('customer_name', 'Unknown')}")
            logger.info(f"   Deposits: ${customer.get('total_deposits', 0):,.0f}")
            logger.info(f"   Products: {customer.get('num_products', 0)}")
            logger.info(f"   Intent: {customer.get('intent_score', 0)*100:.0f}%")
            logger.info(f"   Cluster: {customer.get('cluster', 'Unknown')}")
            
            # Get customer's existing products
            existing_product_ids = self._get_customer_products(customer_id)
            
            # Get candidate products (not already owned)
            candidates = self.products_df[
                ~self.products_df['product_id'].isin(existing_product_ids)
            ].copy()
            
            if len(candidates) == 0:
                return {
                    'customer_id': customer_id,
                    'customer_info': self._get_customer_info_dict(customer),
                    'tailored_recommendations': [],
                    'similar_products': [],
                    'segment_recommendations': [],
                    'recommendation_metadata': {
                        'reason': 'Customer already has all available products',
                        'scoring_method': 'rule_based_ml_hybrid'
                    }
                }
            
            # Score all candidates with hybrid approach
            candidates = self._score_products_hybrid(customer, candidates)
            
            # Get top recommendations
            top_recommendations = candidates.nlargest(10, 'final_score')
            
            # Format recommendations
            tailored = []
            for _, product in top_recommendations.head(5).iterrows():
                rec = self._format_recommendation(customer, product)
                tailored.append(rec)
            
            # Similar products (same category as existing)
            similar = self._get_similar_products(customer, candidates, existing_product_ids)
            
            # Segment-based recommendations
            segment = self._get_segment_recommendations(customer, candidates)
            
            # Build result
            result = {
                'customer_id': customer_id,
                'customer_info': self._get_customer_info_dict(customer),
                'tailored_recommendations': tailored,
                'similar_products': similar,
                'segment_recommendations': segment,
                'recommendation_metadata': {
                    'total_count': len(tailored),
                    'scoring_method': 'rule_based_ml_hybrid' if self.logit_model else 'rule_based',
                    'ml_available': self.logit_model is not None,
                    'rule_weight': 0.5 if self.logit_model else 1.0,
                    'ml_weight': 0.5 if self.logit_model else 0.0
                }
            }
            
            # Enrich with 12-factor details if available
            if self.enhanced_scorer:
                result = self._enrich_with_12_factor(result, customer)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in get_all_recommendations: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'error': str(e),
                'customer_id': customer_id,
                'tailored_recommendations': [],
                'similar_products': [],
                'segment_recommendations': []
            }
    
    def _score_products_hybrid(self, customer, candidates: pd.DataFrame) -> pd.DataFrame:
        """
        Score products using hybrid approach:
        - 50% Rule-Based Score
        - 50% ML Probability (if available)
        """
        # Calculate rule-based scores
        candidates['rule_score'] = candidates.apply(
            lambda product: self._calculate_rule_based_score(customer, product),
            axis=1
        )
        
        # Calculate ML scores if model available
        if self.logit_model:
            try:
                candidates['ml_prob'] = candidates.apply(
                    lambda product: self.logit_model.predict_purchase_probability(
                        customer.to_dict(), product.to_dict()
                    ),
                    axis=1
                )
            except Exception as e:
                logger.warning(f"ML scoring failed: {e}, using rule-based only")
                candidates['ml_prob'] = 0.5
        else:
            candidates['ml_prob'] = 0.5
        
        # Combine scores
        if self.logit_model:
            # Hybrid: 50% rule-based, 50% ML
            candidates['final_score'] = (
                candidates['rule_score'] * 0.5 +
                candidates['ml_prob'] * 0.5
            )
            logger.info(f"   Scoring: Hybrid (50% Rule + 50% ML)")
            logger.info(f"   Avg Rule Score: {candidates['rule_score'].mean():.3f}")
            logger.info(f"   Avg ML Prob: {candidates['ml_prob'].mean():.3f}")
        else:
            # Rule-based only
            candidates['final_score'] = candidates['rule_score']
            logger.info(f"   Scoring: Rule-Based Only (100%)")
            logger.info(f"   Avg Score: {candidates['rule_score'].mean():.3f}")
        
        return candidates
    
    def _calculate_rule_based_score(self, customer, product) -> float:
        """
        Calculate rule-based score using banking business rules
        
        Banking-specific factors:
        1. Eligibility (25%): Credit score, income requirements
        2. Segment Match (20%): Personal/Business/Agricultural
        3. Financial Need (20%): Product fits customer's financial situation
        4. Relationship Depth (15%): Existing products, tenure
        5. Intent Score (10%): Cross-sell receptivity
        6. Channel Fit (10%): Digital vs branch preference
        """
        score = 0.0
        
        # 1. Eligibility Score (25%) - Can customer qualify?
        eligibility = self._calculate_eligibility_score(customer, product)
        score += eligibility * 0.25
        
        # 2. Segment Match (20%) - Personal/Business/Agricultural
        segment_match = self._calculate_segment_match_score(customer, product)
        score += segment_match * 0.20
        
        # 3. Financial Need (20%) - Does product address a need?
        financial_need = self._calculate_financial_need_score(customer, product)
        score += financial_need * 0.20
        
        # 4. Relationship Depth (15%) - Reward loyal customers
        relationship = self._calculate_relationship_score(customer, product)
        score += relationship * 0.15
        
        # 5. Intent Score (10%) - Customer's receptivity
        intent = customer.get('intent_score', customer.get('cross_sell_receptivity', 0.5))
        score += float(intent) * 0.10
        
        # 6. Channel Fit (10%) - Digital product for digital customer?
        channel_fit = self._calculate_channel_fit_score(customer, product)
        score += channel_fit * 0.10
        
        return float(score)
    
    def _calculate_eligibility_score(self, customer, product) -> float:
        """Check if customer meets product requirements"""
        score = 1.0
        
        # Credit score requirement
        if 'min_credit_score' in product.index and pd.notna(product['min_credit_score']):
            required = product['min_credit_score']
            actual = customer.get('credit_score', 650)
            if actual >= required + 50:
                score = 1.0  # Well qualified
            elif actual >= required:
                score = 0.8  # Qualified
            elif actual >= required - 20:
                score = 0.5  # Borderline
            else:
                score = 0.1  # Not qualified
        
        # Income requirement
        if 'min_income' in product.index and pd.notna(product['min_income']):
            required_income = product['min_income']
            actual_income = customer.get('income', 50000)
            if actual_income >= required_income:
                score *= 1.0
            else:
                score *= (actual_income / required_income)
        
        # Balance requirement
        if 'min_balance' in product.index and pd.notna(product['min_balance']):
            required_balance = product['min_balance']
            actual_balance = customer.get('total_deposits', 0)
            if actual_balance >= required_balance:
                score *= 1.0
            else:
                score *= 0.5  # Can't meet minimum
        
        return float(score)
    
    def _calculate_segment_match_score(self, customer, product) -> float:
        """Match product segment to customer segment"""
        customer_segment = customer.get('customer_segment', 'Personal')
        
        if 'target_segment' in product.index:
            target_segment = product['target_segment']
            if pd.isna(target_segment) or target_segment == 'All':
                return 1.0
            elif target_segment == customer_segment:
                return 1.0
            else:
                return 0.3  # Wrong segment
        
        return 0.8  # No segment info
    
    def _calculate_financial_need_score(self, customer, product) -> float:
        """Does product address customer's financial needs?"""
        category = product.get('category', '')
        deposits = customer.get('total_deposits', 0)
        income = customer.get('income', 50000)
        age = customer.get('age', 40)
        
        # High deposits → Investment products
        if deposits > 100000 and category in ['Investments', 'Wealth Management', 'Premium Savings']:
            return 1.0
        
        # Low/medium deposits → Savings, checking
        if deposits < 50000 and category in ['Checking', 'Savings', 'Debit Card']:
            return 0.9
        
        # High income → Premium products
        if income > 150000 and 'Premium' in str(product.get('product_name', '')):
            return 0.95
        
        # Young customers → Basic products, credit building
        if age < 35 and category in ['Credit Cards', 'Student Accounts', 'Checking']:
            return 0.85
        
        # Older customers → Retirement, investment
        if age > 55 and category in ['Investments', 'Retirement Accounts', 'CDs']:
            return 0.9
        
        # Business segment → Business products
        if customer.get('customer_segment') == 'Business' and category in ['Business Banking', 'Commercial Loans']:
            return 1.0
        
        return 0.5  # Neutral
    
    def _calculate_relationship_score(self, customer, product) -> float:
        """Reward deeper relationships"""
        num_products = customer.get('num_products', 1)
        tenure_months = customer.get('tenure_months', customer.get('account_tenure_months', 12))
        
        # Multi-product customers get premium products
        if num_products >= 5:
            return 0.9
        elif num_products >= 3:
            return 0.7
        else:
            return 0.5
    
    def _calculate_channel_fit_score(self, customer, product) -> float:
        """Match digital products to digital customers"""
        digital_engagement = customer.get('digital_engagement_score', 0.5)
        product_name = str(product.get('product_name', '')).lower()
        
        # Digital products for digital customers
        if digital_engagement > 0.7 and ('mobile' in product_name or 'digital' in product_name or 'online' in product_name):
            return 1.0
        
        # Branch products for branch customers
        if digital_engagement < 0.3 and ('premier' in product_name or 'private' in product_name):
            return 0.9
        
        return 0.7  # Neutral
    
    def _get_customer_products(self, customer_id: str) -> List[str]:
        """Get list of products customer already has"""
        existing = []
        
        # Try product_holdings first
        if self.data_path:
            try:
                from pathlib import Path
                holdings_path = Path(self.data_path) / 'product_holdings.csv'
                if holdings_path.exists():
                    holdings_df = pd.read_csv(holdings_path)
                    customer_holdings = holdings_df[
                        (holdings_df['customer_id'] == customer_id) &
                        (holdings_df.get('status', 'active') == 'active')
                    ]
                    existing = customer_holdings['product_id'].tolist()
            except:
                pass
        
        # Fallback to transactions
        if len(existing) == 0 and 'product_id' in self.transactions_df.columns:
            customer_txns = self.transactions_df[self.transactions_df['customer_id'] == customer_id]
            existing = customer_txns['product_id'].unique().tolist()
        
        return existing
    
    def _get_similar_products(self, customer, candidates: pd.DataFrame, existing_products: List[str]) -> List[Dict]:
        """Get products similar to what customer already has"""
        if len(existing_products) == 0:
            return []
        
        # Get categories of existing products
        existing_categories = self.products_df[
            self.products_df['product_id'].isin(existing_products)
        ]['category'].unique()
        
        # Find products in same categories
        similar = candidates[
            candidates['category'].isin(existing_categories)
        ].nlargest(3, 'final_score')
        
        result = []
        for _, product in similar.iterrows():
            rec = self._format_recommendation(customer, product)
            rec['reason'] = f"Similar to your existing {product['category']} products"
            result.append(rec)
        
        return result
    
    def _get_segment_recommendations(self, customer, candidates: pd.DataFrame) -> List[Dict]:
        """Get products popular in customer's segment"""
        cluster_id = customer.get('cluster')
        if pd.isna(cluster_id):
            return []
        
        # Get products popular in this segment
        segment_products = candidates.head(3)  # Simplified for now
        
        result = []
        for _, product in segment_products.iterrows():
            rec = self._format_recommendation(customer, product)
            rec['reason'] = f"Popular among customers in your segment"
            result.append(rec)
        
        return result
    
    def _format_recommendation(self, customer, product) -> Dict:
        """Format product as recommendation"""
        return {
            'product_id': product['product_id'],
            'product_name': product['product_name'],
            'category': product['category'],
            'product_category': product['category'],
            'product_description': product.get('description', product['product_name']),
            'score': float(product.get('final_score', 0.5)),
            'propensity_score': float(product.get('final_score', 0.5)),
            'rule_score': float(product.get('rule_score', 0.5)),
            'ml_probability': float(product.get('ml_prob', 0.5)),
            'reason': self._generate_reason(customer, product),
            'reasoning': self._generate_reason(customer, product),
            'in_stock': product.get('accepting_applications', True),
            'eligibility_status': 'Eligible'  # Simplified
        }
    
    def _generate_reason(self, customer, product) -> str:
        """Generate explanation for recommendation"""
        reasons = []
        
        deposits = customer.get('total_deposits', 0)
        credit_score = customer.get('credit_score', 650)
        digital = customer.get('digital_engagement_score', 0.5)
        
        if credit_score > 750:
            reasons.append(f"excellent credit (score: {credit_score})")
        
        if deposits > 100000:
            reasons.append(f"high deposits (${deposits:,.0f})")
        
        if digital > 0.8:
            reasons.append("strong digital adoption")
        
        if reasons:
            return f"Recommended based on your {', '.join(reasons[:2])}"
        else:
            return f"Good fit for your financial profile"
    
    def _get_customer_info_dict(self, customer) -> Dict:
        """Get customer info for response"""
        return {
            'customer_id': customer['customer_id'],
            'customer_name': customer.get('customer_name', 'Unknown'),
            'total_deposits': float(customer.get('total_deposits', 0)),
            'num_products': int(customer.get('num_products', 0)),
            'credit_score': int(customer.get('credit_score', 650)),
            'intent_score': float(customer.get('intent_score', customer.get('cross_sell_receptivity', 0.5))),
            'cluster': int(customer.get('cluster', -1)) if pd.notna(customer.get('cluster')) else None,
            'customer_segment': customer.get('customer_segment', 'Personal')
        }
    
    def _enrich_with_12_factor(self, result: Dict, customer) -> Dict:
        """Enrich recommendations with 12-factor scoring details"""
        if not self.enhanced_scorer:
            return result
        
        try:
            persona_info = None
            if pd.notna(customer.get('cluster')) and int(customer['cluster']) in self.personas:
                persona_info = self.personas[int(customer['cluster'])]
            
            # Enrich each recommendation type
            for rec_type in ['tailored_recommendations', 'similar_products', 'segment_recommendations']:
                if rec_type in result:
                    for rec in result[rec_type]:
                        try:
                            product_id = rec.get('product_id')
                            product = self.products_df[self.products_df['product_id'] == product_id]
                            
                            if len(product) > 0:
                                product = product.iloc[0]
                                
                                score_12, detailed_breakdown = self.enhanced_scorer.calculate_12_factor_score(
                                    customer=customer,
                                    product=product,
                                    persona_info=persona_info
                                )
                                
                                rec['scoring_method'] = '12_factor'
                                rec['detailed_calculation'] = detailed_breakdown
                                rec['compatibility'] = score_12 * 100
                        except Exception as e:
                            logger.warning(f"Failed to enrich {rec.get('product_id')}: {e}")
            
            logger.info(f"✅ Enriched recommendations with 12-factor scoring")
        except Exception as e:
            logger.error(f"Error enriching with 12-factor: {e}")
        
        return result


if __name__ == "__main__":
    print("Agent B Banking - Rule-Based + ML Hybrid")

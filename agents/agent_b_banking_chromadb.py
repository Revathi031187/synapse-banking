"""
Agent B - Banking Product Recommendations
Uses banking 12-factor scoring to provide personalized financial product recommendations
Adapted from agent_b_academy_chromadb.py for banking domain
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents.banking_12_factor_scorer import Banking12FactorScorer

logger = logging.getLogger(__name__)

try:
    from utils.claude_client import get_claude_client
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    get_claude_client = None


class AgentB_Banking:
    """
    Agent B for Banking: Product Recommendations using 12-Factor Scoring
    
    Recommends banking products based on:
    1. Customer persona (from Agent A)
    2. Financial eligibility (credit, income, balance)
    3. Banking 12-factor scoring system
    """
    
    def __init__(self, data_path: str = 'data/preloaded/fmb_bank', agent_a=None):
        """
        Initialize Agent B Banking
        
        Args:
            data_path: Path to preloaded F&M Bank data
            agent_a: Reference to Agent A for customer persona lookup
        """
        self.data_path = Path(data_path)
        self.products_df = None
        self.personas = {}
        self.agent_a = agent_a
        self.customers_df = None
        self.transactions_df = None
        self.current_dataset_version = None  # Track which dataset is loaded
        self.enhanced_scorer = None
        
        logger.info(f"Agent B Banking initialized with data path: {data_path}")
    
    def load_data(self, dataset_version='v1'):
        """
        Load product, customer, and transaction data
        
        Args:
            dataset_version: 'v1' or 'v2' dataset version
        """
        print(f"[Agent B] load_data() starting  -  path={self.data_path}", flush=True)
        try:
            # Load banking data (no v2 for now, just use v1)
            products_path = self.data_path / 'products.csv'
            customers_path = self.data_path / 'customers.csv'
            transactions_path = self.data_path / 'transactions.csv'

            self.products_df = pd.read_csv(products_path)
            logger.info(f"Loaded {len(self.products_df)} banking products from {products_path.name}")
            print(f"[Agent B] products loaded: {len(self.products_df)}", flush=True)

            if len(self.products_df) == 0:
                logger.error("Products dataframe is empty!")
                return False

            # Load customer and transaction data for customer-specific recommendations
            if customers_path.exists():
                self.customers_df = pd.read_csv(customers_path)
                _col_aliases = {
                    'total_deposit_value':       'total_deposits',
                    'avg_daily_balance_p30days': 'avg_daily_balance',
                    'customer_type':             'customer_segment',
                    'credit_score_trend_p6mo':   'credit_score_trend',
                }
                for new_col, old_col in _col_aliases.items():
                    if new_col in self.customers_df.columns and old_col not in self.customers_df.columns:
                        self.customers_df[old_col] = self.customers_df[new_col]
                logger.info(f"Loaded {len(self.customers_df)} customers from {customers_path.name}")

            from utils.large_file_loader import ensure_csv
            transactions_path = ensure_csv(transactions_path)
            if transactions_path.exists():
                self.transactions_df = pd.read_csv(transactions_path)
                logger.info(f"Loaded {len(self.transactions_df)} transactions from {transactions_path.name}")
            else:
                logger.info("No transactions.csv found  -  12-factor scorer will use monthly_transaction_volume from customers.csv")
            
            # Initialize Banking 12-Factor Scorer
            logger.info("Initializing Banking 12-Factor Scorer ...")
            logger.info(f"  customers_df: {len(self.customers_df)} rows" if self.customers_df is not None else "  customers_df: None")
            logger.info(f"  transactions_df: {len(self.transactions_df)} rows" if self.transactions_df is not None else "  transactions_df: None")
            if self.customers_df is not None:
                try:
                    # Prefer Agent A's clustered customers + transactions so segment popularity / pairing match the live session
                    scorer_customers = self.customers_df
                    # transactions_df is optional (excluded from Databricks App deployments due to 57 MB size)
                    # Banking12FactorScorer handles None/empty transactions gracefully  -  transaction_pattern
                    # factor (weight 0.01) reads monthly_transaction_volume from customers.csv instead.
                    scorer_txn = self.transactions_df if self.transactions_df is not None else pd.DataFrame()
                    if self.agent_a and getattr(self.agent_a, 'customers_df', None) is not None:
                        ca = self.agent_a.customers_df
                        if ca is not None and len(ca) > 0:
                            scorer_customers = ca
                    if self.agent_a and getattr(self.agent_a, 'transactions_df', None) is not None:
                        ta = self.agent_a.transactions_df
                        if ta is not None and len(ta) > 0:
                            scorer_txn = ta
                    personas_for = self.personas
                    if self.agent_a and getattr(self.agent_a, 'personas', None):
                        personas_for = self.agent_a.personas
                    self.enhanced_scorer = Banking12FactorScorer(
                        customers_df=scorer_customers,
                        products_df=self.products_df,
                        transactions_df=scorer_txn,
                        personas=personas_for or {},
                    )
                    logger.info("Banking 12-Factor Scorer initialized successfully")
                except Exception as e:
                    logger.error(f"12-factor scorer init failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    self.enhanced_scorer = None
            else:
                self.enhanced_scorer = None
                logger.warning("Cannot initialize 12-factor scorer: no customer data")
            
            print(f"[Agent B] load_data() SUCCESS", flush=True)
            return True
        except Exception as e:
            import traceback
            logger.error(f"Agent B load_data failed: {e}")
            logger.error(traceback.format_exc())
            print(f"[Agent B] load_data ERROR: {e}", flush=True)
            traceback.print_exc()
            return False
    
    def execute(self, params: Dict) -> Dict:
        """
        Execute Agent B: Generate personalized banking product recommendations
        
        Args:
            params: Dictionary with:
                - customer_id: Optional customer ID (will auto-detect persona)
                - persona: Persona ID or name (required if no customer_id)
                - search_query: Optional search filter
                - category: Optional category filter (Bank Account/Certificate of Deposit/Credit Card/Loan/Mortgage/Investment)
                - top_n: Number of recommendations (default: 10)
                - explain: Whether to include explanations (default: True)
                - dataset_version: 'v1' or 'v2' (default: 'v1')
                
        Returns:
            Dictionary with recommendations and insights
        """
        # Load data if not already loaded OR if dataset version changed
        dataset_version = params.get('dataset_version', 'v1')
        if (self.products_df is None or 
            self.current_dataset_version != dataset_version):
            logger.info(f"Loading Agent B data for dataset version: {dataset_version}")
            if not self.load_data(dataset_version=dataset_version):
                return {'error': 'Failed to load product data'}
            self.current_dataset_version = dataset_version
        
        # Extract parameters
        customer_id = params.get('customer_id')
        persona = params.get('persona')
        search_query = params.get('search_query', '').lower()
        category = params.get('category')
        top_n = params.get('top_n', 10)
        explain = params.get('explain', True)
        
        # Get customer info if customer_id provided
        customer_info = None
        if customer_id:
            customer_info = self._get_customer_info(customer_id)
            if customer_info:
                self._last_customer_info = customer_info  # cache for LLM rationale
                # Use customer's actual persona
                if self.agent_a and hasattr(self.agent_a, 'customers_df') and self.agent_a.customers_df is not None:
                    # Get persona from Agent A's clustering results
                    ca = self.agent_a.customers_df
                    ccol = ca['customer_id'].astype(str).str.strip()
                    customer_row = ca[ccol == str(customer_id).strip()]
                    if not customer_row.empty and 'cluster' in customer_row.columns:
                        cluster_id = customer_row['cluster'].iloc[0]
                        try:
                            cluster_id = int(float(cluster_id))
                        except (TypeError, ValueError):
                            pass
                        persona = self._get_persona_from_cluster(cluster_id)
                        logger.info(f"Using persona '{persona}' from Agent A for customer {customer_id}")
                elif customer_info.get('persona'):
                    persona = customer_info['persona']
                    logger.info(f"Using persona from customer data for {customer_id}")
        
        if not persona:
            return {'error': 'Persona is required (or provide customer_id)'}
        
        # Normalize persona (handle both ID and name)
        persona_name, persona_id = self._normalize_persona(persona)
        
        # Determine customer segment and eligibility range
        if customer_info:
            customer_segment = customer_info.get('customer_segment', 'Personal')
            min_credit, max_fee, tier_name = self._calculate_eligibility_range(customer_info)
        else:
            # Segment-based recommendation - create synthetic customer from persona
            customer_segment, min_credit, max_fee, tier_name = self._calculate_segment_eligibility_range(persona_name)
        
        PRODUCT_TYPES = ('Bank Account', 'Certificate of Deposit', 'Credit Card', 'Loan', 'Mortgage', 'Investment')
        if category and str(category).strip() in PRODUCT_TYPES:
            logger.info(f"📌 Category filter: {category} (only {category} products will be recommended)")

        logger.info(f"💎 {'Customer' if customer_info else 'Segment'} tier: {tier_name}")

        # Build owned-product set for this customer so we never recommend what they already hold
        owned_product_ids: set = set()
        if customer_id and self.transactions_df is not None and 'product_id' in self.transactions_df.columns:
            cid_str = str(customer_id).strip()
            cid_col = self.transactions_df['customer_id'].astype(str).str.strip()
            owned_product_ids = set(self.transactions_df.loc[cid_col == cid_str, 'product_id'].unique())
            if owned_product_ids:
                logger.info(f"🚫 Excluding {len(owned_product_ids)} already-owned products for {customer_id}")

        # Filter products by segment, age, category, and eligibility
        filtered_products = self._filter_products(
            search_query, category, min_credit, max_fee,
            target_segment=customer_segment,
            customer_info=customer_info
        )

        # Remove products the customer already owns
        if owned_product_ids:
            before_own = len(filtered_products)
            filtered_products = [p for p in filtered_products if p.get('product_id') not in owned_product_ids]
            logger.info(f"✂️ Ownership filter: {before_own} → {len(filtered_products)} products")

        if len(filtered_products) == 0:
            logger.warning(f"⚠️ No products found. Relaxing constraints...")
            # Fallback: relax eligibility constraints (still exclude owned)
            filtered_products = self._filter_products(
                search_query, category, min_credit - 100, max_fee * 2
            )
            if owned_product_ids:
                filtered_products = [p for p in filtered_products if p.get('product_id') not in owned_product_ids]
        
        if len(filtered_products) == 0:
            return {
                'status': 'no_products',
                'message': 'No products match the search criteria',
                'recommendations': [],
                'out_of_stock_recommendations': []
            }
        
        # Never recommend more than we have in segment (e.g. Agricultural has only 5 products)
        effective_top_n = min(top_n, len(filtered_products))
        if effective_top_n < top_n:
            logger.info(f"📌 Segment has {len(filtered_products)} product(s); capping recommendations at {effective_top_n} (requested {top_n})")
        
        factor_weights = params.get('factor_weights')
        # Score and rank products
        recommendations = self._score_and_rank(
            persona_name, persona_id, filtered_products, effective_top_n, explain, customer_info, tier_name,
            factor_weights=factor_weights,
        )
        sup = params.get('supervisor_directives')
        if sup:
            try:
                from agents.agent_d_banking import AgentD_Banking
                recommendations = AgentD_Banking.apply_directives_to_recommendations(
                    recommendations,
                    sup,
                    self.products_df,
                    customer_context=customer_info,
                    persona_name=persona_name,
                )
            except Exception as e:
                logger.warning(f"Supervisor directives not applied: {e}")
            else:
                if explain:
                    try:
                        self._refresh_rank_explanations_after_reorder(
                            recommendations, effective_top_n, persona_name, tier_name
                        )
                    except Exception as e:
                        logger.warning(f"Supervisor rank refresh skipped: {e}")
        
        # Separate in-stock and out-of-stock
        in_stock_recs = [r for r in recommendations if r.get('in_stock', True)]
        out_of_stock_recs = [r for r in recommendations if not r.get('in_stock', True)]
        
        # Generate insights (use actual returned count)
        insights = self._generate_insights(persona_name, in_stock_recs[:effective_top_n])
        
        # Prepare response: return only up to effective_top_n (never more than segment size)
        returned_count = len(in_stock_recs[:effective_top_n])
        result = {
            'status': 'success',
            'persona': persona_name,
            'persona_id': persona_id,
            'search_query': search_query,
            'category': category,
            'total_products_considered': len(filtered_products),
            'recommendations': in_stock_recs[:effective_top_n],
            'out_of_stock_recommendations': out_of_stock_recs[:effective_top_n],
            'insights': insights,
            'returned_count': returned_count,
            'requested_count': top_n,
        }
        if effective_top_n < top_n:
            result['count_note'] = (
                f"Showing {returned_count} of {top_n} requested  -  only {len(filtered_products)} products "
                f"available for this customer's segment/filters."
            )
        return result
    
    # Fallback: persona ID -> name when Agent A personas not available or key mismatch
    BANKING_PERSONA_ID_MAP = {
        0: 'Young Professionals', 1: 'Digital Natives', 2: 'Household Savers',
        3: 'Traditional Savers', 4: 'Wealth Investors', 5: 'Business Banking Customers'
    }

    def _normalize_persona(self, persona: any) -> tuple:
        """
        Normalize persona to both name and ID. Robust to int/str keys and missing Agent A.
        
        Args:
            persona: Persona ID (int) or name (str)
            
        Returns:
            Tuple of (persona_name, persona_id)
        """
        # If integer or numeric string, it's a persona ID
        try:
            persona_id = int(persona)
            persona_name = None
            # Try agent_a.personas with int and str key
            if self.agent_a and hasattr(self.agent_a, 'personas') and self.agent_a.personas:
                pdata = self.agent_a.personas.get(persona_id) or self.agent_a.personas.get(str(persona_id))
                if pdata:
                    persona_name = pdata.get('persona_name') or pdata.get('short_name')
            if not persona_name:
                persona_name = self.BANKING_PERSONA_ID_MAP.get(persona_id, f'Persona {persona_id}')
            return persona_name, persona_id
        except (ValueError, TypeError):
            # It's a persona name
            persona_name = str(persona)
            persona_id = None
            if self.agent_a and hasattr(self.agent_a, 'personas'):
                for pid, pdata in self.agent_a.personas.items():
                    if pdata.get('persona_name') == persona_name or pdata.get('short_name') == persona_name:
                        persona_id = pid
                        break
            return persona_name, persona_id
    
    def _calculate_segment_eligibility_range(self, persona_name: str) -> tuple:
        """
        Calculate eligibility range based on SEGMENT/PERSONA name
        
        Args:
            persona_name: Segment/persona name
            
        Returns:
            Tuple of (customer_segment, min_credit, max_fee, tier_name)
        """
        persona_lower = (persona_name or '').lower()
        
        # WEALTH/PREMIUM SEGMENTS - High balance requirements (includes "Wealth Investors")
        if any(word in persona_lower for word in ['wealth', 'investor', 'premium', 'affluent', 'platinum', 'elite', 'private']):
            return ('Personal', 750, 500, "Premium")  # Min credit 750, max fee $500

        # HOUSEHOLD SAVERS (check before traditional so "Household Savers" gets Mainstream)
        elif any(word in persona_lower for word in ['household']):
            return ('Personal', 680, 150, "Mainstream")  # Min credit 680, max fee $150

        # TRADITIONAL/ESTABLISHED SEGMENTS (includes "Traditional Savers")
        elif any(word in persona_lower for word in ['traditional', 'established', 'loyal', 'long-term', 'saver']):
            return ('Personal', 700, 200, "Traditional")  # Min credit 700, max fee $200

        # YOUNG PROFESSIONALS / DIGITAL NATIVES
        elif any(word in persona_lower for word in ['young', 'professional', 'millennial', 'starter', 'digital', 'native']):
            return ('Personal', 650, 100, "Young")  # Min credit 650, max fee $100

        # DEFAULT - Mainstream personal banking
        else:
            logger.info(f"Segment '{persona_name}' mapped to default Mainstream range")
            return ('Personal', 680, 150, "Mainstream")
    
    def _calculate_eligibility_range(self, customer_info: Dict) -> tuple:
        """
        Calculate appropriate eligibility range based on customer's financial profile
        
        Args:
            customer_info: Customer information dictionary
            
        Returns:
            Tuple of (min_credit, max_fee, tier_name)
        """
        if not customer_info:
            return (650, 150, "Unknown")
        
        # Get customer's financial metrics
        credit_score = customer_info.get('credit_score', 700)
        total_deposits = customer_info.get('total_deposits', 50000)
        income = customer_info.get('income', 60000)
        
        # Determine tier based on deposits and income
        if total_deposits >= 200000 and income >= 150000:
            return (credit_score - 50, 500, "Ultra-Premium")  # Can afford high fees
        elif total_deposits >= 100000 and income >= 100000:
            return (credit_score - 50, 300, "Platinum")
        elif total_deposits >= 50000 and income >= 75000:
            return (credit_score - 50, 200, "Gold")
        elif total_deposits >= 25000 and income >= 50000:
            return (credit_score - 50, 100, "Silver")
        elif total_deposits >= 10000 and income >= 35000:
            return (credit_score - 50, 50, "Bronze")
        else:
            return (credit_score - 50, 25, "Entry")

    _LOAN_SUBCATEGORIES = {
        'Auto', 'Personal Loan', 'Home Equity', 'HELOC',
        'Mortgage', 'Agricultural Loan', 'Business Loan'
    }

    def _revenue_products_df(self) -> pd.DataFrame:
        """Return products filtered to revenue-generating products only.

        Excludes products where all direct revenue fields (annual_fee, monthly_fee,
        min_balance, regular_apr_pct, aum_fee_pct) are zero AND the subcategory is
        not a loan type. This removes entry-level free checking/savings (e.g.
        Essential Checking, Basic Savings) that generate no direct bank revenue.

        Note: interest_rate alone is not used as the revenue flag because savings/CD
        products store APY (bank cost) in that column; only loan subcategories store
        a revenue-generating rate there.
        """
        df = self.products_df
        is_loan = df.get('subcategory', pd.Series('', index=df.index)).isin(self._LOAN_SUBCATEGORIES)
        rev_mask = (
            (df.get('annual_fee',      pd.Series(0, index=df.index)).fillna(0).astype(float) > 0) |
            (df.get('monthly_fee',     pd.Series(0, index=df.index)).fillna(0).astype(float) > 0) |
            (df.get('min_balance',     pd.Series(0, index=df.index)).fillna(0).astype(float) > 0) |
            (df.get('regular_apr_pct', pd.Series(0, index=df.index)).fillna(0).astype(float) > 0) |
            (df.get('aum_fee_pct',     pd.Series(0, index=df.index)).fillna(0).astype(float) > 0) |
            (is_loan & (df.get('interest_rate', pd.Series(0, index=df.index)).fillna(0).astype(float) > 0))
        )
        return df[rev_mask]

    def _filter_products(self, search_query: str, category: str = None,
                        min_credit: float = 0, max_fee: float = 999999,
                        target_segment: str = None,
                        customer_info: Dict = None) -> List[Dict]:
        """
        Filter products based on search query, category type, and eligibility.

        Args:
            search_query: Search text
            category: Product type filter (Bank Account/Certificate of Deposit/Credit Card/Loan/Mortgage/Investment)
                      or subcategory keyword
            min_credit: Minimum credit score customer has
            max_fee: Maximum fee customer can afford
            target_segment: Customer segment ('Personal', 'Business', 'Agricultural'); filters to matching products

        Returns:
            List of filtered product dictionaries
        """
        PRODUCT_TYPES = ('Bank Account', 'Certificate of Deposit', 'Credit Card', 'Loan', 'Mortgage', 'Investment')
        df = self._revenue_products_df().copy()
        logger.info(f"💵 Revenue gate: {len(self.products_df)} total → {len(df)} revenue-generating products")

        # Filter by target segment to avoid recommending Business/Agricultural products to Personal customers
        if target_segment and 'target_segment' in df.columns:
            before_seg = len(df)
            df_seg = df[df['target_segment'].astype(str).str.strip() == target_segment]
            if len(df_seg) > 0:
                df = df_seg
                logger.info(f"🎯 Segment filter ('{target_segment}'): {before_seg} → {len(df)} products")
            else:
                logger.warning(f"⚠️ No products for segment '{target_segment}', keeping all revenue products")

        # Snapshot the fully-gated pool so fallbacks never escape revenue/segment restrictions
        _base_pool = df.copy()

        # Age-based hard exclusions  -  remove products unsuitable for the customer's life stage
        if customer_info:
            _age = float(customer_info.get('age', 0) or 0)
            if _age >= 70:
                df = df[~(
                    (df['subcategory'].astype(str) == 'Mortgage') &
                    (df['product_name'].astype(str).str.contains('30yr|30-yr|30 yr', case=False, na=False))
                )]
                logger.info(f"🚫 Age {_age:.0f}: excluded 30-yr mortgage")
            _ctype_excl = str(customer_info.get('customer_type', '') or '')
            if _age < 30 or _ctype_excl in ('Digital_Native', 'Retiree'):
                df = df[~df['subcategory'].astype(str).isin(['Home Equity', 'HELOC'])]
                logger.info(f"🚫 {_ctype_excl}: excluded Home Equity/HELOC")
            # Exclude secured/credit-builder cards for customers who qualify for unsecured cards
            _cs = float(customer_info.get('credit_score', 0) or 0)
            if _cs >= 670:
                df = df[~(
                    (df['subcategory'].astype(str) == 'Credit') &
                    (df['product_name'].astype(str).str.contains('Secured', case=False, na=False))
                )]
                logger.info(f"🚫 Credit {_cs:.0f}: excluded Secured Card (qualifies for unsecured cards)")
            # FHA Mortgage: exclude for High-Net-Worth, Retiree, and Digital_Native
            # Retirees/HNW don't need entry-level govt-backed mortgages
            # Digital_Native (young, mobile-first) profile: Roth IRA / savings products are more appropriate
            if _ctype_excl in ('High_Net_Worth', 'Retiree', 'Digital_Native'):
                df = df[~(df['product_name'].astype(str).str.contains('FHA', case=False, na=False))]
                logger.info(f"🚫 {_ctype_excl}: excluded FHA Mortgage")
            if len(df) == 0:
                df = _base_pool.copy()
            # Homeowner filter  -  renters cannot take out home equity products
            _home_own = str(customer_info.get('home_ownership_type', '') or '').lower()
            if _home_own == 'renter':
                before_home = len(df)
                df = df[~df['subcategory'].astype(str).isin(['Home Equity', 'HELOC'])]
                if len(df) < before_home:
                    logger.info(f"🏠 Renter: excluded Home Equity/HELOC ({before_home} → {len(df)} products)")
            if len(df) == 0:
                df = _base_pool.copy()
            _base_pool = df.copy()   # update base pool so fallbacks also respect age/credit exclusions

        # Filter by product type or subcategory keyword
        if category and str(category).strip():
            cat_val = str(category).strip()
            if cat_val in PRODUCT_TYPES:
                before_cat = len(df)
                df_filtered = df[df['category'].astype(str).str.strip() == cat_val]
                if len(df_filtered) > 0:
                    df = df_filtered
                    logger.info(f"📂 Category filter ('{cat_val}'): {before_cat} → {len(df)} products")
                else:
                    logger.warning(f"⚠️ No products in category '{cat_val}', showing all products")
            elif 'subcategory' in df.columns:
                before_cat = len(df)
                df_sub = df[df['subcategory'].astype(str).str.contains(cat_val, case=False, na=False)]
                if len(df_sub) > 0:
                    df = df_sub
                    logger.info(f"📂 Subcategory filter ('{cat_val}'): {before_cat} → {len(df)} products")
                else:
                    logger.warning(f"⚠️ No products in subcategory '{cat_val}', showing all products")

        # Filter by eligibility  -  credit score (50-point buffer)
        if 'min_credit_score' in df.columns:
            before_credit = len(df)
            df = df[
                (df['min_credit_score'].isna()) |
                (df['min_credit_score'] <= min_credit + 50)
            ]
            logger.info(f"💳 Credit filter (>={min_credit-50}): {before_credit} → {len(df)} products")
            if len(df) == 0:
                logger.warning("⚠️ Credit filter too strict, relaxing to category/subcategory only")
                df = _base_pool.copy()
                if category and str(category).strip():
                    cat_val = str(category).strip()
                    if cat_val in PRODUCT_TYPES:
                        df_cat = df[df['category'].astype(str).str.strip() == cat_val]
                        if len(df_cat) > 0:
                            df = df_cat
                    elif 'subcategory' in df.columns:
                        df_sub = df[df['subcategory'].astype(str).str.contains(cat_val, case=False, na=False)]
                        if len(df_sub) > 0:
                            df = df_sub

        # Filter by fee affordability (lenient)
        # Secured Card is exempt  -  it's a credit-building product appropriate for Entry-tier customers
        if 'annual_fee' in df.columns:
            before_fee = len(df)
            df = df[
                (df['annual_fee'].isna()) |
                (df['annual_fee'] <= max_fee) |
                (df['product_name'].astype(str).str.contains('Secured', case=False, na=False))
            ]
            logger.info(f"💰 Fee filter (<=${max_fee}): {before_fee} → {len(df)} products")
            if len(df) == 0:
                logger.warning("⚠️ Fee filter too strict, relaxing to category only")
                df = _base_pool.copy()
                if category and str(category).strip() in PRODUCT_TYPES:
                    df_cat = df[df['category'].astype(str).str.strip() == str(category).strip()]
                    if len(df_cat) > 0:
                        df = df_cat

        # Filter by search query  -  with fallback
        if search_query:
            before_search = len(df)
            mask = (
                df['product_name'].str.contains(search_query, case=False, na=False) |
                df.get('subcategory', pd.Series(dtype=str)).str.contains(search_query, case=False, na=False) |
                df.get('description', pd.Series(dtype=str)).str.contains(search_query, case=False, na=False)
            )
            df_filtered = df[mask]
            if len(df_filtered) > 0:
                df = df_filtered
                logger.info(f"🔍 Search filter ('{search_query}'): {before_search} → {len(df)} products")
            else:
                logger.warning(f"⚠️ Search '{search_query}' returned 0 products, showing all available products")

        # Final fallback: return base pool (revenue + segment gated) if all filters left nothing
        if len(df) == 0:
            logger.warning("⚠️ All filters left 0 products. Returning base revenue+segment pool.")
            df = _base_pool.copy()

        products = df.to_dict('records')
        logger.info(f"✅ Final product count for recommendations: {len(products)}")
        return products
    
    def _score_and_rank(self, persona_name: str, persona_id: int, products: List[Dict], top_n: int, 
                        explain: bool, customer_info: Dict = None, tier_name: str = "Unknown",
                        factor_weights: Dict = None) -> List[Dict]:
        """
        Score banking products and rank by relevance to persona
        
        Args:
            persona_name: Persona name
            persona_id: Persona ID
            products: List of product dictionaries
            top_n: Number of top products to return
            explain: Whether to include detailed explanations
            customer_info: Customer information for eligibility
            tier_name: Customer tier name
            
        Returns:
            List of ranked product recommendations
        """
        recommendations = []
        
        # Get customer deposits for context
        customer_deposits = 0
        if customer_info:
            customer_deposits = customer_info.get('total_deposits', 0)
        
        import time as _time
        _score_start = _time.monotonic()
        logger.info(
            f"[Agent B] Scoring {len(products)} candidate products for persona='{persona_name}' "
            f"(12-factor scorer={'on' if self.enhanced_scorer else 'off'}, "
            f"customer_info={'provided' if customer_info else 'synthetic'})"
        )
        
        for idx, product in enumerate(products):
            # Try to use Banking 12-Factor Scorer if available
            detailed_breakdown = None
            
            if self.enhanced_scorer:
                try:
                    # If no customer_info, create synthetic customer from persona
                    if not customer_info:
                        customer_info = self._create_synthetic_customer_from_persona(persona_name, tier_name)
                        if idx == 0:
                            print(f"[Agent B]   Created synthetic customer for {persona_name}", flush=True)
                    
                    # Get persona info for segment affinity
                    persona_info = None
                    if self.agent_a and hasattr(self.agent_a, 'personas') and persona_id is not None:
                        persona_info = self.agent_a.personas.get(persona_id, {})
                    
                    # Use banking 12-factor scorer
                    detailed_breakdown = self.enhanced_scorer.score_product(
                        customer=customer_info,
                        product=product,
                        persona=persona_info,
                        factor_weights=factor_weights,
                    )
                    
                    score = detailed_breakdown['total_score']

                    # High-revenue product boost: credit cards and loans surface higher
                    # when the customer demonstrably qualifies (credit + income meet the product's
                    # own minimums). This ensures Agent C receives these as top candidates.
                    if customer_info:
                        _subcat = str(product.get('subcategory', ''))
                        _cs  = float(customer_info.get('credit_score', 0) or 0)
                        _inc = float(customer_info.get('income', 0) or 0)
                        _min_cr  = float(product.get('min_credit_score', 0) or 0)
                        _min_inc = float(product.get('min_income', 0) or 0)
                        _qualifies = (_cs >= _min_cr) and (_inc >= _min_inc)

                        if _qualifies:
                            if _subcat == 'Credit':
                                score = min(score + 0.10, 1.0)
                            elif _subcat in {'Auto', 'Personal Loan', 'Home Equity', 'HELOC', 'Mortgage'}:
                                score = min(score + 0.08, 1.0)

                    # Log EVERY product score (not just first one!)
                    print(f"   Product {idx+1}/{len(products)}: {product.get('product_name', 'Unknown')[:30]} - Score: {score:.4f}")

                    # Generate comprehensive explanation from 12 factors
                    rec_text = f"Comprehensive match score based on banking 12 factors (see detailed calculation below)"
                    logger.info(f"Used banking 12-factor scorer for {product.get('product_name', 'unknown')}: {score:.3f}")

                except Exception as e:
                    if idx == 0:
                        print(f"[Agent B]   12-factor scorer FAILED: {e}", flush=True)
                    logger.error(f"Banking 12-factor scorer failed: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to simple scoring
                    score = 0.7
                    rec_text = "Recommended banking product"
            else:
                if idx == 0:
                    print(f"[Agent B]   No enhanced scorer - using simple scoring", flush=True)
                # Simple fallback scoring
                score = 0.7
                rec_text = "Recommended for your financial profile"
            
            # Build recommendation object with explicit type conversions
            # CRITICAL: Convert numpy/pandas types to Python native types for JSON serialization
            import math as _math
            def _safe_float(v, default=0.0):
                try:
                    f = float(v)
                    return default if (_math.isnan(f) or _math.isinf(f)) else f
                except (TypeError, ValueError):
                    return default

            safe_score = _safe_float(score, 0.7)
            recommendation = {
                'product_id': str(product.get('product_id', '')),
                'product_name': str(product.get('product_name', '')),
                'category': str(product.get('category', '')),
                'subcategory': str(product.get('subcategory', '')),
                'customer_types': str(product.get('customer_types', '')),
                'annual_fee': _safe_float(product.get('annual_fee', 0)),
                'min_balance': _safe_float(product.get('min_balance', 0)),
                'interest_rate': _safe_float(product.get('interest_rate', 0)),
                'interest_rate_apy': _safe_float(
                    product.get('interest_rate_apy', product.get('interest_rate', 0))
                ),
                'score': round(safe_score, 4),
                'compatibility': round(safe_score * 100, 1),
                'match_level': self._get_match_level(safe_score),
                'recommendation_text': rec_text if explain else None,
                'reason': rec_text if explain else None,
                'in_stock': bool(product.get('accepting_applications', True)),
                'avg_rating': _safe_float(product.get('avg_rating', 4.5), 4.5),
                'description': str(product.get('description', ''))
            }
            
            # Add detailed explanation if requested
            if explain and detailed_breakdown:
                recommendation['detailed_calculation'] = detailed_breakdown
                recommendation['scoring_method'] = '12_factor'
            else:
                recommendation['scoring_method'] = 'simple'
            
            recommendations.append(recommendation)
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Wealth Investors: strong boost for premium (fee) products so they rank with free products
        # Triggered by: High_Net_Worth customer_type OR persona name containing wealth keywords
        # Deliberately NOT triggered by deposits/income alone  -  avoids boosting premium cards for Retirees
        _is_wealth = bool(
            customer_info and str(customer_info.get('customer_type', '') or '') == 'High_Net_Worth'
        ) or bool(
            persona_name and any(w in (persona_name or '').lower()
                                 for w in ['wealth', 'investor', 'premium', 'affluent', 'wm'])
        )
        if _is_wealth:
            for r in recommendations:
                if float(r.get('annual_fee', 0) or 0) > 0:
                    r['score'] = round(r['score'] + 0.12, 4)
                    r['compatibility'] = round(r['score'] * 100, 1)
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            logger.info("   💎 Wealth Investor: applied 12% premium boost to fee products and re-ranked")

        # Customer-type affinity: boost products whose customer_types field matches this customer
        # Uses the existing customer_types column in products.csv  -  no hardcoded persona rules needed
        if customer_info:
            _ctype = str(customer_info.get('customer_type', '') or '').strip()
            if _ctype:
                _affinity_applied = False
                for r in recommendations:
                    _ctypes_list = [c.strip() for c in str(r.get('customer_types', '') or '').split(',')]
                    if _ctype in _ctypes_list:
                        r['score'] = round(min(r['score'] + 0.10, 1.0), 4)
                        r['compatibility'] = round(r['score'] * 100, 1)
                        _affinity_applied = True
                if _affinity_applied:
                    recommendations.sort(key=lambda x: x['score'], reverse=True)
                    logger.info(f"   🎯 Customer-type affinity (+10%) applied for '{_ctype}'")

        # Inverse affinity: -5% when product has defined customer_types that exclude this customer's type
        # Penalizes e.g. FHA Mortgage for Wealth Manager, Prestige Checking for Mass_Market
        if customer_info:
            _ctype = str(customer_info.get('customer_type', '') or '').strip()
            if _ctype:
                _penalty_applied = False
                for r in recommendations:
                    _ctypes_field = str(r.get('customer_types', '') or '').strip()
                    if _ctypes_field:
                        _ctypes_list = [c.strip() for c in _ctypes_field.split(',')]
                        if _ctype not in _ctypes_list:
                            r['score'] = round(max(r['score'] - 0.05, 0.0), 4)
                            r['compatibility'] = round(r['score'] * 100, 1)
                            _penalty_applied = True
                if _penalty_applied:
                    recommendations.sort(key=lambda x: x['score'], reverse=True)
                    logger.info(f"   ⬇️ Inverse affinity penalty (-5%) applied for '{_ctype}' mismatches")

        # Deprioritize investment/IRA products for very-low-credit customers who need credit building first
        if customer_info:
            _cs_rank = float(customer_info.get('credit_score', 0) or 0)
            if _cs_rank < 580:
                _inv_penalized = False
                for r in recommendations:
                    _sub = str(r.get('subcategory', '') or '')
                    _pname_inv = str(r.get('product_name', '') or '').lower()
                    if _sub in ('Investment', 'IRA', 'Retirement') or 'ira' in _pname_inv:
                        r['score'] = round(max(r['score'] - 0.15, 0.0), 4)
                        r['compatibility'] = round(r['score'] * 100, 1)
                        _inv_penalized = True
                if _inv_penalized:
                    recommendations.sort(key=lambda x: x['score'], reverse=True)
                    logger.info(f"   ⬇️ Investment/IRA products deprioritized for credit-building customer ({_cs_rank:.0f})")

        # Retiree life-stage correction: savings/retirement products must rank above credit cards.
        # The affinity system can over-boost credit cards if products.csv tags them with "Retiree".
        # This post-affinity correction ensures IRA and CD products are always the top picks.
        if customer_info:
            _ctype_ret = str(customer_info.get('customer_type', '') or '').strip()
            if _ctype_ret == 'Retiree':
                _RETIREE_SAVE = {'CD', 'Investment', 'Savings'}  # covers CDs, IRAs (Investment), Money Market (Savings)
                _ret_corrected = False
                for r in recommendations:
                    _rs = str(r.get('subcategory', '') or '')
                    _rp = str(r.get('product_name', '') or '').lower()
                    if _rs in _RETIREE_SAVE or 'money market' in _rp:
                        r['score'] = round(min(r['score'] + 0.15, 1.0), 4)
                        r['compatibility'] = round(r['score'] * 100, 1)
                        _ret_corrected = True
                    elif _rs == 'Credit':
                        r['score'] = round(max(r['score'] - 0.10, 0.0), 4)
                        r['compatibility'] = round(r['score'] * 100, 1)
                        _ret_corrected = True
                if _ret_corrected:
                    recommendations.sort(key=lambda x: x['score'], reverse=True)
                    logger.info("   📈 Retiree: boosted CD/IRA/Savings (+15%), penalized credit cards (-10%)")

        # Category diversity: max 2 products per subcategory in top-N
        # Prevents 5 CDs or 3 credit cards from dominating a retiree's recommendations
        seen_subcats: Dict[str, int] = {}
        diverse_recs = []
        overflow = []
        for r in recommendations:
            subcat = str(r.get('subcategory', 'Other'))
            if seen_subcats.get(subcat, 0) < 2:
                seen_subcats[subcat] = seen_subcats.get(subcat, 0) + 1
                diverse_recs.append(r)
            else:
                overflow.append(r)
            if len(diverse_recs) >= top_n:
                break
        if len(diverse_recs) < top_n:
            diverse_recs.extend(overflow[:top_n - len(diverse_recs)])
        if len(diverse_recs) < len(recommendations[:top_n]):
            logger.info(f"   🎨 Diversity pass: enforced max-2 per subcategory in top-{top_n}")

        # Add RANK EXPLANATIONS - Why #1, #2, #3, etc.
        top_recommendations = diverse_recs

        # Anomaly detection: flag low differentiation (all top scores within 5%)
        top_scores = [float(r.get('score', 0)) for r in top_recommendations[:5]]
        low_differentiation = len(top_scores) >= 3 and (max(top_scores) - min(top_scores)) < 0.05

        for rank, rec in enumerate(top_recommendations, 1):
            # Generate rank explanation
            rank_explanation = self._generate_rank_explanation(
                rank=rank,
                product=rec,
                all_products=top_recommendations,
                persona_name=persona_name,
                tier_name=tier_name
            )

            # Add rank explanation to the recommendation
            rec['rank'] = rank
            rec['rank_explanation'] = rank_explanation
            if low_differentiation:
                rec['low_differentiation_flag'] = True

            # Update reason to include rank explanation
            if explain and rec.get('reason'):
                rec['reason'] = f"**#{rank} Recommended:** {rank_explanation}\n\n{rec['reason']}"

        # LLM rationale for top 3 (one batched call)
        if CLAUDE_AVAILABLE and get_claude_client and top_recommendations:
            try:
                claude = get_claude_client()
                if claude.is_available():
                    customer_info = {}
                    if hasattr(self, '_last_customer_info'):
                        customer_info = self._last_customer_info
                    rationales = claude.generate_batch_rationale(
                        top3_products=top_recommendations[:3],
                        customer_info=customer_info,
                        persona_name=persona_name,
                    )
                    for rec in top_recommendations[:3]:
                        pid = rec.get('product_id')
                        if pid and pid in rationales:
                            rec['llm_rationale'] = rationales[pid]
            except Exception as e:
                logger.warning(f"Agent B LLM rationale failed: {e}")

        _score_ms = int((_time.monotonic() - _score_start) * 1000)
        logger.info(
            f"[Agent B] Scoring complete for '{persona_name}': {len(recommendations)} products scored, "
            f"top-{len(top_recommendations)} returned (duration={_score_ms}ms)"
        )
        return recommendations

    def _refresh_rank_explanations_after_reorder(
        self,
        recommendations: List[Dict],
        top_n: int,
        persona_name: str,
        tier_name: str,
    ) -> None:
        """After supervisor pin reorders the list, recompute rank + rank_explanation for the returned window."""
        if not recommendations:
            return
        n = min(int(top_n), len(recommendations))
        top = recommendations[:n]
        for rank, rec in enumerate(top, 1):
            rec["rank"] = rank
            try:
                rec["rank_explanation"] = self._generate_rank_explanation(
                    rank=rank,
                    product=rec,
                    all_products=top,
                    persona_name=persona_name,
                    tier_name=tier_name,
                )
            except Exception as e:
                logger.warning("Rank explanation refresh failed at rank %s: %s", rank, e)
                continue
            base = rec.get("recommendation_text") or (
                "Comprehensive match score based on banking 12 factors (see detailed calculation below)"
            )
            rec["reason"] = f"**#{rank} Recommended:** {rec.get('rank_explanation', '')}\n\n{base}"
    
    def _create_synthetic_customer_from_persona(self, persona_name: str, tier_name: str) -> Dict:
        """
        Create a synthetic customer profile from persona characteristics
        
        Args:
            persona_name: Persona name
            tier_name: Customer tier
            
        Returns:
            Synthetic customer dictionary
        """
        persona_lower = persona_name.lower()
        
        # Determine dominant relationship
        if 'wealth' in persona_lower or 'investment' in persona_lower:
            primary_relationship = 'Investment'
        elif 'traditional' in persona_lower:
            primary_relationship = 'Checking'
        else:
            primary_relationship = 'Checking'
        customer_segment = 'Personal'
        
        # Determine financial profile from tier
        if tier_name == "Premium" or tier_name == "Ultra-Premium":
            credit_score = 780
            income = 150000
            total_deposits = 250000
            num_products = 6
            digital_engagement = 0.8
        elif tier_name == "Platinum":
            credit_score = 760
            income = 120000
            total_deposits = 150000
            num_products = 5
            digital_engagement = 0.75
        elif tier_name == "Gold":
            credit_score = 740
            income = 90000
            total_deposits = 80000
            num_products = 4
            digital_engagement = 0.7
        elif tier_name == "Silver":
            credit_score = 710
            income = 65000
            total_deposits = 40000
            num_products = 3
            digital_engagement = 0.6
        elif tier_name == "Bronze":
            credit_score = 680
            income = 45000
            total_deposits = 15000
            num_products = 2
            digital_engagement = 0.5
        else:
            credit_score = 700
            income = 55000
            total_deposits = 25000
            num_products = 2
            digital_engagement = 0.55
        
        synthetic_customer = {
            'customer_id': f'synthetic_{persona_name}',
            'credit_score': credit_score,
            'income': income,
            'total_deposits': total_deposits,
            'num_products': num_products,
            'digital_engagement_score': digital_engagement,
            'cross_sell_receptivity': 0.7,
            'persona': persona_name,
            'tier': tier_name,
            'customer_segment': customer_segment,
            'age': 45,
            'months_since_relationship_started': 36,
            'tenure_months': 36
        }
        
        logger.info(f"✅ Created synthetic customer: Credit={credit_score}, Deposits=${total_deposits:,.0f}, Products={num_products}")
        return synthetic_customer
    
    def _generate_rank_explanation(self, rank: int, product: Dict, all_products: List[Dict], 
                                   persona_name: str, tier_name: str) -> str:
        """
        Generate explanation for WHY this product is ranked at this position
        
        Args:
            rank: Product rank
            product: Current product
            all_products: All top products
            persona_name: Persona name
            tier_name: Tier name
            
        Returns:
            Explanation text
        """
        score = product['score']
        fee = product.get('annual_fee', 0)
        compatibility = product.get('compatibility', 0)
        category = product.get('category', 'Unknown')
        
        explanations = []
        
        # Get detailed calculation for data-driven explanations
        detailed_calc = product.get('detailed_calculation', {})
        eligibility = detailed_calc.get('eligibility_score', {}).get('score', 0) * 100 if detailed_calc else 0
        need_match = detailed_calc.get('financial_need_match', {}).get('score', 0) * 100 if detailed_calc else 0
        product_value = detailed_calc.get('product_value', {}).get('score', 0) * 100 if detailed_calc else 0
        
        apy = product.get('interest_rate_apy', product.get('interest_rate', 0))
        min_balance = product.get('min_balance', 0)
        subcategory = product.get('subcategory', 'Product')
        
        sections = []
        
        # SECTION 1: Rank-specific introduction
        if rank == 1:
            sections.append(f"**🥇 #1 Recommended** | Top match with **{compatibility:.1f}% compatibility**")
            if score >= 0.75:
                sections.append(f"Exceptional alignment with your {persona_name} profile across all 12 banking factors")
            else:
                sections.append(f"Best available option for {persona_name} customers")
        elif rank == 2:
            score_diff = (all_products[0]['score'] - score) * 100 if all_products else 0
            sections.append(f"**🥈 #2 Alternative** | Strong choice at **{compatibility:.1f}% compatibility**")
            if score_diff < 5:
                sections.append(f"Nearly identical to #1 (only {score_diff:.1f}% difference) - provides diversification")
            else:
                sections.append(f"Excellent alternative with complementary strengths")
        elif rank == 3:
            sections.append(f"**🥉 #3 Option** | Solid match at **{compatibility:.1f}% compatibility**")
            sections.append(f"Adds portfolio diversity while maintaining quality")
        else:
            sections.append(f"**#{rank} Recommended** | Good fit at **{compatibility:.1f}% compatibility**")
        
        # SECTION 2: Why for THIS persona (data-driven)
        persona_reasons = []
        if eligibility > 80:
            persona_reasons.append(f"✅ **Eligibility {eligibility:.0f}%**: You strongly qualify - exceeds all requirements for {persona_name}")
        elif eligibility > 60:
            persona_reasons.append(f"✅ **Eligibility {eligibility:.0f}%**: Meets qualification criteria")
        
        if need_match > 70:
            persona_reasons.append(f"🎯 **Need Match {need_match:.0f}%**: Perfectly aligned with {persona_name} financial goals")
        elif need_match > 50:
            persona_reasons.append(f"🎯 **Need Match {need_match:.0f}%**: Addresses your banking needs")
        
        if product_value > 8:
            value_parts = []
            if fee == 0: value_parts.append("no annual fee")
            if apy > 2.0: value_parts.append(f"{apy:.2f}% APY")
            if min_balance == 0: value_parts.append("no minimum")
            if value_parts:
                persona_reasons.append(f"💎 **Value {product_value:.1f}%**: Excellent - {', '.join(value_parts)}")
        
        if persona_reasons:
            sections.append("\n**Why for " + persona_name + ":**\n" + "\n".join(persona_reasons))
        
        # SECTION 3: Product benefits
        benefits = []
        if subcategory == 'Checking':
            if apy > 0: benefits.append(f"💰 Earns {apy:.2f}% APY (rare for checking)")
            if min_balance == 0: benefits.append(f"🔓 No minimum balance")
            benefits.append(f"📱 Convenient daily banking")
        elif subcategory == 'Savings':
            if apy > 1.5: benefits.append(f"📈 High yield: {apy:.2f}% APY")
            elif apy > 0: benefits.append(f"💵 Competitive {apy:.2f}% APY")
            benefits.append(f"🎯 Automated savings growth")
        elif subcategory == 'Investment':
            benefits.append(f"📊 Long-term growth at {apy:.2f}%")
            benefits.append(f"💎 Tax-advantaged wealth building")
        elif subcategory == 'Credit':
            benefits.append(f"💳 Flexible credit access")
            if fee > 0: benefits.append(f"🎁 Premium features (${fee}/year)")
        elif subcategory == 'Loan':
            benefits.append(f"🏠 Competitive {apy:.2f}% rate")
            benefits.append(f"✅ Predictable monthly payments")
        
        if benefits:
            sections.append("\n**Key Benefits:**\n" + "\n".join(benefits))
        
        # Wealth Investor + no-fee product: clarify why free product is still recommended
        persona_lower = (persona_name or "").lower()
        if ("wealth" in persona_lower or "investor" in persona_lower) and fee == 0:
            sections.append("\n*No-fee option recommended for operational liquidity and diversification alongside premium holdings.*")
        
        # Add comparison context
        if rank == 1 and len(all_products) > 1:
            sections.append(f"\n*Why #1? Scores {(score - all_products[1].get('score', 0)) * 100:.1f}% higher than #{rank+1} on critical factors.*")
        
        return "\n\n".join(sections)
    
    def _get_match_level(self, score: float) -> str:
        """
        Convert score to match level
        
        Args:
            score: Score value
            
        Returns:
            Match level string
        """
        if score > 0.80:
            return 'Perfect Match'
        elif score > 0.65:
            return 'Great Match'
        elif score > 0.50:
            return 'Good Option'
        else:
            return 'Consider Alternatives'
    
    def _generate_insights(self, persona_name: str, recommendations: List[Dict]) -> Dict:
        """
        Generate banking-specific insights about recommendations
        
        Args:
            persona_name: Persona name
            recommendations: List of recommendations
            
        Returns:
            Dictionary with banking-focused insights
        """
        if len(recommendations) == 0:
            return {}
        
        # Calculate statistics
        scores = [float(r.get('score') or 0) for r in recommendations]
        fees = [float(r.get('annual_fee', 0)) for r in recommendations]
        min_balances = [float(r.get('min_balance', 0)) for r in recommendations]
        interest_rates = [float(r.get('interest_rate_apy', r.get('interest_rate', 0))) for r in recommendations]
        
        # Banking-specific calculations
        total_annual_fees = sum(fees)
        free_products_count = sum(1 for f in fees if f == 0)
        paid_products_count = len(fees) - free_products_count
        
        # Interest-earning products
        earning_products = [r for r in recommendations if r.get('interest_rate_apy', r.get('interest_rate', 0)) > 0]
        earning_count = len(earning_products)
        
        # Potential annual earnings (rough estimate: $10K deposit @ avg APY)
        avg_apy = np.mean([r.get('interest_rate_apy', r.get('interest_rate', 0)) for r in earning_products]) if earning_products else 0
        potential_earnings = (10000 * avg_apy / 100) if avg_apy > 0 else 0
        
        # Product type breakdown
        categories = [r.get('subcategory', r.get('category', 'Unknown')) for r in recommendations]
        category_counts = pd.Series(categories).value_counts().to_dict()
        
        # Count match levels
        match_level_counts = {}
        for rec in recommendations:
            level = rec.get('match_level') or 'Good Option'
            match_level_counts[level] = match_level_counts.get(level, 0) + 1
        
        # Banking-optimized insights
        insights = {
            # Core matching metrics
            'avg_match_score': round(float(np.mean(scores) * 100), 1),  # As percentage
            'top_match_score': round(float(max(scores) * 100), 1),
            
            # Financial value metrics (BANKING-SPECIFIC)
            'total_annual_cost': round(float(total_annual_fees), 2),
            'avg_annual_fee': round(float(np.mean(fees)), 2),
            'free_products': int(free_products_count),
            'paid_products': int(paid_products_count),
            
            # Earning potential (BANKING-SPECIFIC)
            'earning_products': int(earning_count),
            'avg_apy': round(float(avg_apy), 2),
            'estimated_annual_earnings': round(float(potential_earnings), 2),
            
            # Accessibility (BANKING-SPECIFIC)
            'min_balance_required': round(float(min(min_balances)), 2) if min_balances else 0.0,
            'max_balance_required': round(float(max(min_balances)), 2) if min_balances else 0.0,
            'no_minimum_products': int(sum(1 for mb in min_balances if mb == 0)),
            
            # Product diversity
            'product_types': category_counts,
            'product_diversity_score': len(category_counts),  # Number of different types
            
            # Match quality distribution
            'match_distribution': match_level_counts,
            'excellent_matches': match_level_counts.get('Perfect Match', 0) + match_level_counts.get('Great Match', 0),
            
            # Context
            'persona_summary': self._get_persona_summary(persona_name),
            'value_proposition': self._get_value_proposition(recommendations, persona_name)
        }
        
        return insights
    
    def _get_persona_summary(self, persona_name: str) -> str:
        """Get summary text for persona"""
        persona_lower = persona_name.lower()
        
        if 'wealth' in persona_lower or 'premium' in persona_lower:
            return 'High net worth individuals seeking premium banking services and investment opportunities'
        elif 'traditional' in persona_lower:
            return 'Long-term customers who value relationship banking and personal service'
        elif 'young' in persona_lower:
            return 'Younger customers building their financial foundation with digital-first preferences'
        elif 'business' in persona_lower:
            return 'Business owners needing commercial banking and merchant services'
        elif 'agricultural' in persona_lower:
            return 'Agricultural customers requiring specialized farming and equipment financing'
        else:
            return 'Banking customers seeking personalized financial solutions'
    
    def _get_recommendation_strategy(self, persona_name: str) -> str:
        """Get recommendation strategy for persona"""
        persona_lower = persona_name.lower()
        
        if 'wealth' in persona_lower:
            return 'Prioritizing premium products: investment accounts, wealth management, private banking services'
        elif 'traditional' in persona_lower:
            return 'Focusing on core relationships: checking, savings, certificates of deposit'
        elif 'young' in persona_lower:
            return 'Building foundation: starter accounts, credit building, mobile banking'
        elif 'business' in persona_lower:
            return 'Business solutions: commercial checking, merchant services, business loans'
        elif 'agricultural' in persona_lower:
            return 'Agricultural financing: crop loans, equipment financing, insurance products'
        else:
            return 'Standard banking products ranked by eligibility and fit'
    
    def _get_value_proposition(self, recommendations: List[Dict], persona_name: str) -> str:
        """Get personalized value proposition for these recommendations"""
        if not recommendations:
            return "Personalized banking solutions tailored to your needs"
        
        # Analyze what's being recommended
        has_free = any(r.get('annual_fee', 0) == 0 for r in recommendations)
        has_earning = any(r.get('interest_rate_apy', r.get('interest_rate', 0)) > 0 for r in recommendations)
        has_checking = any('checking' in r.get('subcategory', '').lower() for r in recommendations)
        has_savings = any('savings' in r.get('subcategory', '').lower() for r in recommendations)
        has_credit = any('credit' in r.get('subcategory', '').lower() for r in recommendations)
        has_loans = any('loan' in r.get('subcategory', '').lower() for r in recommendations)
        
        # Build personalized message
        messages = []
        
        if has_free and has_earning:
            messages.append("Free banking with earning potential")
        elif has_free:
            messages.append("No-fee banking solutions")
        elif has_earning:
            messages.append("Maximize your savings with competitive rates")
        
        if has_checking and has_savings:
            messages.append("complete banking relationship")
        elif has_checking:
            messages.append("convenient everyday banking")
        elif has_savings:
            messages.append("grow your savings")
        
        if has_credit:
            messages.append("flexible credit options")
        if has_loans:
            messages.append("competitive loan rates")
        
        if messages:
            return " • ".join(messages).capitalize()
        else:
            return "Personalized product recommendations based on your financial profile"
    
    def _coalesce_customer_metrics(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Replace NaN/None with defaults so 12-factor scoring differs per customer, not all NaN-default."""
        out = dict(row)
        defaults = {
            'credit_score': 700,
            'income': 50000.0,
            'total_deposits': 10000.0,
            'age': 40,
            'num_products': 2,
            'digital_engagement_score': 0.5,
            'cross_sell_receptivity': 0.5,
            'months_since_relationship_started': 12,
            'tenure_months': 12,
        }
        for k, dflt in defaults.items():
            v = out.get(k)
            if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
                out[k] = dflt
            elif pd.isna(v):
                out[k] = dflt
        out['customer_id'] = str(out.get('customer_id', '')).strip()
        return out

    def _get_customer_info(self, customer_id: str) -> Optional[Dict]:
        """
        Get customer information including persona and transaction history.
        Prefer Agent A's customers_df (has cluster + same IDs as the UI) over Agent B's bundled CSV.
        """
        cid = str(customer_id).strip()
        if not cid:
            return None

        df_source = None
        if self.agent_a and getattr(self.agent_a, 'customers_df', None) is not None:
            df_source = self.agent_a.customers_df
        elif self.customers_df is not None:
            df_source = self.customers_df
        else:
            return None

        col = df_source['customer_id'].astype(str).str.strip()
        customer_row = df_source[col == cid]
        if customer_row.empty:
            return None

        customer_info = self._coalesce_customer_metrics(customer_row.iloc[0].to_dict())

        txn_df = None
        if self.agent_a and getattr(self.agent_a, 'transactions_df', None) is not None:
            txn_df = self.agent_a.transactions_df
        elif self.transactions_df is not None:
            txn_df = self.transactions_df

        if txn_df is not None and not txn_df.empty and 'customer_id' in txn_df.columns:
            tcol = txn_df['customer_id'].astype(str).str.strip()
            customer_transactions = txn_df[tcol == cid]
            customer_info['transaction_count'] = len(customer_transactions)
            if 'product_id' in customer_transactions.columns:
                customer_info['owned_products'] = customer_transactions['product_id'].unique().tolist()
            else:
                customer_info['owned_products'] = []
        else:
            customer_info['transaction_count'] = int(customer_info.get('num_products', 0) or 0)
            customer_info['owned_products'] = []

        cl = customer_info.get('cluster')
        if cl is not None and not (isinstance(cl, float) and pd.isna(cl)):
            customer_info['persona'] = self._get_persona_from_cluster(cl)

        return customer_info
    
    def _get_persona_from_cluster(self, cluster_id: int) -> str:
        """
        Map cluster ID to persona name
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Persona name
        """
        # If Agent A is available, use its persona mapping
        if self.agent_a and hasattr(self.agent_a, 'personas') and self.agent_a.personas:
            pa = self.agent_a.personas
            try:
                k = int(float(cluster_id))
            except (TypeError, ValueError):
                k = cluster_id
            pdata = pa.get(k) or pa.get(str(k))
            if pdata:
                return pdata.get('short_name', pdata.get('persona_name', f'Persona {k}'))
        
        return f'Persona {cluster_id}'


if __name__ == "__main__":
    # Test Agent B Banking
    print("="*70)
    print("Agent B - Banking Product Recommendations")
    print("="*70)
    
    agent = AgentB_Banking()
    
    # Test 1: Wealth Investors persona
    print("\n" + "="*70)
    print("Test 1: Wealth Investors searching for 'investment'")
    print("="*70)
    result = agent.execute({
        'persona': 'Wealth Investors',
        'search_query': 'investment',
        'top_n': 5
    })
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Status: {result['status']}")
        print(f"📊 Products considered: {result['total_products_considered']}")
        print(f"\nTop 5 Recommendations:")
        
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n{i}. {rec['product_name']}")
            print(f"   Score: {rec['score']*100:.2f}% | Match: {rec['match_level']}")
            print(f"   Fee: ${rec['annual_fee']} | Min Balance: ${rec['min_balance']}")
    
    print("\n" + "="*70)
    print("✅ Agent B Banking Test Complete!")
    print("="*70)

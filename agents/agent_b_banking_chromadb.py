"""
Agent B - Banking Product Recommendations
Uses banking 12-factor scoring to provide personalized financial product recommendations
Adapted from agent_b_academy_chromadb.py for banking domain
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents.banking_12_factor_scorer import Banking12FactorScorer

logger = logging.getLogger(__name__)


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
        try:
            # Load banking data (no v2 for now, just use v1)
            products_path = self.data_path / 'products.csv'
            customers_path = self.data_path / 'customers.csv'
            transactions_path = self.data_path / 'transactions.csv'
            
            self.products_df = pd.read_csv(products_path)
            logger.info(f"✅ Loaded {len(self.products_df)} banking products from {products_path.name}")
            
            if len(self.products_df) == 0:
                logger.error("❌ Products dataframe is empty!")
                return False
            
            # Load customer and transaction data for customer-specific recommendations
            if customers_path.exists():
                self.customers_df = pd.read_csv(customers_path)
                logger.info(f"✅ Loaded {len(self.customers_df)} customers from {customers_path.name}")
            
            if transactions_path.exists():
                self.transactions_df = pd.read_csv(transactions_path)
                logger.info(f"✅ Loaded {len(self.transactions_df)} transactions from {transactions_path.name}")
            else:
                logger.info("ℹ️  No transactions.csv found")
            
            # Initialize Banking 12-Factor Scorer
            print("\n" + "="*80)
            print("🔍 INITIALIZING BANKING 12-FACTOR SCORER")
            print("="*80)
            print(f"customers_df exists: {self.customers_df is not None}")
            print(f"transactions_df exists: {self.transactions_df is not None}")
            if self.customers_df is not None and self.transactions_df is not None:
                print("✅ Attempting to initialize...")
                try:
                    self.enhanced_scorer = Banking12FactorScorer(
                        customers_df=self.customers_df,
                        products_df=self.products_df,
                        transactions_df=self.transactions_df,
                        personas=self.personas
                    )
                    print("✅✅✅ BANKING 12-FACTOR SCORER INITIALIZED! ✅✅✅")
                    logger.info(f"✅ Initialized Banking 12-Factor Scorer")
                except Exception as e:
                    print(f"❌ INIT FAILED: {e}")
                    import traceback
                    traceback.print_exc()
                    self.enhanced_scorer = None
            else:
                self.enhanced_scorer = None
                print("❌ Cannot initialize - missing data")
                logger.warning("⚠️ Cannot initialize 12-factor scorer (missing customer/transaction data)")
            print("="*80 + "\n")
            
            return True
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def execute(self, params: Dict) -> Dict:
        """
        Execute Agent B: Generate personalized banking product recommendations
        
        Args:
            params: Dictionary with:
                - customer_id: Optional customer ID (will auto-detect persona)
                - persona: Persona ID or name (required if no customer_id)
                - search_query: Optional search filter
                - category: Optional category filter (Personal/Business/Agricultural)
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
                # Use customer's actual persona
                if self.agent_a and hasattr(self.agent_a, 'customers_df') and self.agent_a.customers_df is not None:
                    # Get persona from Agent A's clustering results
                    customer_row = self.agent_a.customers_df[self.agent_a.customers_df['customer_id'] == customer_id]
                    if not customer_row.empty and 'cluster' in customer_row.columns:
                        cluster_id = customer_row['cluster'].iloc[0]
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
        
        # When user explicitly selects a product segment in the Category dropdown, use it for filtering
        # This ensures "Agricultural Banking" returns only Agricultural products, not Personal
        PRODUCT_SEGMENTS = ('Personal', 'Business', 'Agricultural')
        if category and str(category).strip() in PRODUCT_SEGMENTS:
            customer_segment = str(category).strip()
            logger.info(f"📌 Using Category filter as segment: {customer_segment} (only {customer_segment} products will be recommended)")
        
        logger.info(f"💎 {'Customer' if customer_info else 'Segment'} tier: {tier_name} | Segment: {customer_segment}")
        
        # Filter products by segment, category, and eligibility
        filtered_products = self._filter_products(
            search_query, category, customer_segment, min_credit, max_fee
        )
        
        if len(filtered_products) == 0:
            logger.warning(f"⚠️ No products found. Relaxing constraints...")
            # Fallback: relax eligibility constraints
            filtered_products = self._filter_products(
                search_query, category, customer_segment, min_credit - 100, max_fee * 2
            )
        
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
        
        # Score and rank products
        recommendations = self._score_and_rank(
            persona_name, persona_id, filtered_products, effective_top_n, explain, customer_info, tier_name
        )
        
        # Separate in-stock and out-of-stock
        in_stock_recs = [r for r in recommendations if r.get('in_stock', True)]
        out_of_stock_recs = [r for r in recommendations if not r.get('in_stock', True)]
        
        # Generate insights (use actual returned count)
        insights = self._generate_insights(persona_name, in_stock_recs[:effective_top_n])
        
        # Prepare response: return only up to effective_top_n (never more than segment size)
        return {
            'status': 'success',
            'persona': persona_name,
            'persona_id': persona_id,
            'search_query': search_query,
            'category': category,
            'total_products_considered': len(filtered_products),
            'recommendations': in_stock_recs[:effective_top_n],
            'out_of_stock_recommendations': out_of_stock_recs[:effective_top_n],
            'insights': insights
        }
    
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
        
        # BUSINESS SEGMENTS
        elif any(word in persona_lower for word in ['business', 'commercial', 'entrepreneur', 'owner']):
            return ('Business', 700, 300, "Business")  # Min credit 700, max fee $300
        
        # AGRICULTURAL SEGMENTS
        elif any(word in persona_lower for word in ['agricultural', 'farm', 'rural', 'grower']):
            return ('Agricultural', 680, 200, "Agricultural")  # Min credit 680, max fee $200
        
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
    
    def _filter_products(self, search_query: str, category: str = None, customer_segment: str = 'Personal', 
                        min_credit: float = 0, max_fee: float = 999999) -> List[Dict]:
        """
        Filter products based on search query, category, segment, and eligibility
        
        Args:
            search_query: Search text
            category: Category filter
            customer_segment: Personal/Business/Agricultural
            min_credit: Minimum credit score customer has
            max_fee: Maximum fee customer can afford
            
        Returns:
            List of filtered product dictionaries
        """
        df = self.products_df.copy()
        
        # Segment filter: only recommend products that belong to this segment (e.g. Agricultural → 5 products)
        if 'category' in df.columns and customer_segment:
            segment_products = df[df['category'].astype(str).str.strip().str.lower() == str(customer_segment).strip().lower()]
            if len(segment_products) > 0:
                df = segment_products
                logger.info(f"🏦 Filtered to {customer_segment} segment: {len(df)} products")
            else:
                # Try exact match in case of case mismatch
                segment_products = df[df['category'] == customer_segment]
                if len(segment_products) > 0:
                    df = segment_products
                    logger.info(f"🏦 Filtered to {customer_segment} segment: {len(df)} products")
                else:
                    logger.warning(f"⚠️ No products in '{customer_segment}' segment ({len(df)} total in catalog); showing all products")
        
        # Filter by eligibility - credit score (more lenient)
        if 'min_credit_score' in df.columns:
            before_credit = len(df)
            df = df[
                (df['min_credit_score'].isna()) |
                (df['min_credit_score'] <= min_credit + 50)  # Generous 50-point buffer
            ]
            after_credit = len(df)
            logger.info(f"💳 Credit filter (>={min_credit-50}): {before_credit} → {after_credit} products")
            
            # If too restrictive, relax filter
            if len(df) == 0:
                logger.warning(f"⚠️ Credit filter too strict, relaxing to segment only")
                df = self.products_df.copy()
                if 'category' in df.columns and customer_segment:
                    seg_lower = str(customer_segment).strip().lower()
                    df = df[df['category'].astype(str).str.strip().str.lower() == seg_lower]
        
        # Filter by fee affordability (lenient)
        if 'annual_fee' in df.columns:
            before_fee = len(df)
            df = df[
                (df['annual_fee'].isna()) |
                (df['annual_fee'] <= max_fee)
            ]
            after_fee = len(df)
            logger.info(f"💰 Fee filter (<=${max_fee}): {before_fee} → {after_fee} products")
            
            # If too restrictive, relax filter
            if len(df) == 0:
                logger.warning(f"⚠️ Fee filter too strict, relaxing to segment only")
                df = self.products_df.copy()
                if 'category' in df.columns and customer_segment:
                    seg_lower = str(customer_segment).strip().lower()
                    df = df[df['category'].astype(str).str.strip().str.lower() == seg_lower]
        
        # Filter by category: only as SUBcategory when it's not a product segment (Personal/Business/Agricultural)
        # When category IS the segment we already filtered by it above; don't match subcategory to "Agricultural" (would return 0)
        PRODUCT_SEGMENTS = ('Personal', 'Business', 'Agricultural')
        if category and str(category).strip() not in PRODUCT_SEGMENTS and 'subcategory' in df.columns:
            before_cat = len(df)
            df_filtered = df[df['subcategory'].astype(str).str.contains(category, case=False, na=False)]
            if len(df_filtered) > 0:
                df = df_filtered
                logger.info(f"📂 Subcategory filter ('{category}'): {before_cat} → {len(df)} products")
            else:
                logger.warning(f"⚠️ No products in subcategory '{category}', keeping segment products")
        
        # Filter by search query - with fallback
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
                # BANKING OPTIMIZATION: If search returns 0, show top products instead
                logger.warning(f"⚠️ Search '{search_query}' returned 0 products, showing all available products")
        
        # Final safety: never show other segments when user chose a segment (e.g. Agricultural)
        if len(df) == 0:
            logger.warning(f"⚠️ Filters left 0 products. Re-applying segment '{customer_segment}' only (no fallback to other segments).")
            df = self.products_df.copy()
            if 'category' in df.columns and customer_segment:
                seg_lower = str(customer_segment).strip().lower()
                df = df[df['category'].astype(str).str.strip().str.lower() == seg_lower]
            # Do NOT fall back to all products - return only segment products or empty
            if len(df) == 0:
                logger.warning(f"⚠️ No products in segment '{customer_segment}' in catalog. Returning empty.")
        
        # Convert to list of dictionaries
        products = df.to_dict('records')
        logger.info(f"✅ Final product count for recommendations: {len(products)}")
        return products
    
    def _score_and_rank(self, persona_name: str, persona_id: int, products: List[Dict], top_n: int, 
                        explain: bool, customer_info: Dict = None, tier_name: str = "Unknown") -> List[Dict]:
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
        
        print(f"\n🔍 Scoring {len(products)} banking products for {persona_name}...")
        print(f"   enhanced_scorer: {self.enhanced_scorer is not None}")
        print(f"   customer_info: {customer_info is not None}")
        
        for idx, product in enumerate(products):
            # Try to use Banking 12-Factor Scorer if available
            detailed_breakdown = None
            
            if self.enhanced_scorer:
                try:
                    # If no customer_info, create synthetic customer from persona
                    if not customer_info:
                        customer_info = self._create_synthetic_customer_from_persona(persona_name, tier_name)
                        if idx == 0:
                            print(f"   ✅ Created synthetic customer for {persona_name}")
                    
                    # Get persona info for segment affinity
                    persona_info = None
                    if self.agent_a and hasattr(self.agent_a, 'personas') and persona_id is not None:
                        persona_info = self.agent_a.personas.get(persona_id, {})
                    
                    # Use banking 12-factor scorer
                    detailed_breakdown = self.enhanced_scorer.score_product(
                        customer=customer_info,
                        product=product,
                        persona=persona_info
                    )
                    
                    score = detailed_breakdown['total_score']
                    
                    # Log EVERY product score (not just first one!)
                    print(f"   Product {idx+1}/{len(products)}: {product.get('product_name', 'Unknown')[:30]} - Score: {score:.4f}")
                    
                    # Generate comprehensive explanation from 12 factors
                    rec_text = f"Comprehensive match score based on banking 12 factors (see detailed calculation below)"
                    logger.info(f"✅ Used banking 12-factor scorer for {product.get('product_name', 'unknown')}: {score:.3f}")
                    
                except Exception as e:
                    if idx == 0:
                        print(f"   ❌ Banking 12-factor scorer FAILED: {e}")
                    logger.error(f"❌ Banking 12-factor scorer failed: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to simple scoring
                    score = 0.7
                    rec_text = "Recommended banking product"
            else:
                if idx == 0:
                    print(f"   ⚠️ No enhanced scorer - using simple scoring")
                # Simple fallback scoring
                score = 0.7
                rec_text = "Recommended for your financial profile"
            
            # Build recommendation object with explicit type conversions
            # CRITICAL: Convert numpy/pandas types to Python native types for JSON serialization
            recommendation = {
                'product_id': str(product.get('product_id', '')),
                'product_name': str(product.get('product_name', '')),
                'category': str(product.get('category', '')),
                'subcategory': str(product.get('subcategory', '')),
                'annual_fee': float(product.get('annual_fee', 0)) if product.get('annual_fee') is not None else 0.0,
                'min_balance': float(product.get('min_balance', 0)) if product.get('min_balance') is not None else 0.0,
                'interest_rate': float(product.get('interest_rate', 0)) if product.get('interest_rate') is not None else 0.0,
                'interest_rate_apy': float(product.get('interest_rate_apy', product.get('interest_rate', 0))) if product.get('interest_rate_apy', product.get('interest_rate')) is not None else 0.0,
                'score': round(float(score), 4),
                'compatibility': round(float(score) * 100, 1),  # Convert to percentage
                'match_level': self._get_match_level(score),
                'recommendation_text': rec_text if explain else None,
                'reason': rec_text if explain else None,  # Alias for compatibility
                'in_stock': bool(product.get('accepting_applications', True)),
                'avg_rating': float(product.get('avg_rating', 4.5)) if product.get('avg_rating') is not None else 4.5,
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
        # 12-factor scorer already adds +0.12 to fee_score; post-ranking boost ensures fee products don't stay last
        if persona_name and ('wealth' in (persona_name or '').lower() or 'investor' in (persona_name or '').lower()):
            for r in recommendations:
                if float(r.get('annual_fee', 0) or 0) > 0:
                    r['score'] = round(r['score'] + 0.12, 4)  # +12% so premium products compete for top slots
                    r['compatibility'] = round(r['score'] * 100, 1)
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            logger.info("   💎 Wealth Investor: applied 12% premium boost to fee products and re-ranked")
        
        # Add RANK EXPLANATIONS - Why #1, #2, #3, etc.
        top_recommendations = recommendations[:top_n]
        
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
            
            # Update reason to include rank explanation
            if explain and rec.get('reason'):
                rec['reason'] = f"**#{rank} Recommended:** {rank_explanation}\n\n{rec['reason']}"
        
        return recommendations
    
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
        if 'business' in persona_lower:
            primary_relationship = 'Business_Checking'
            customer_segment = 'Business'
        elif 'agricultural' in persona_lower or 'farm' in persona_lower:
            primary_relationship = 'Agricultural_Loan'
            customer_segment = 'Agricultural'
        elif 'wealth' in persona_lower or 'investment' in persona_lower:
            primary_relationship = 'Investment'
            customer_segment = 'Personal'
        elif 'traditional' in persona_lower:
            primary_relationship = 'Checking'
            customer_segment = 'Personal'
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
        scores = [r['score'] for r in recommendations]
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
            level = rec['match_level']
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
    
    def _get_customer_info(self, customer_id: str) -> Dict:
        """
        Get customer information including persona and transaction history
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary with customer information
        """
        if self.customers_df is None:
            return None
        
        customer_row = self.customers_df[self.customers_df['customer_id'] == customer_id]
        
        if customer_row.empty:
            return None
        
        customer_info = customer_row.iloc[0].to_dict()
        
        # Get transaction history if available
        if self.transactions_df is not None and not self.transactions_df.empty:
            customer_transactions = self.transactions_df[self.transactions_df['customer_id'] == customer_id]
            customer_info['transaction_count'] = len(customer_transactions)
            if 'product_id' in customer_transactions.columns:
                customer_info['owned_products'] = customer_transactions['product_id'].unique().tolist()
            else:
                customer_info['owned_products'] = []
        else:
            customer_info['transaction_count'] = customer_info.get('num_products', 0)
            customer_info['owned_products'] = []
        
        # Extract persona from cluster
        if 'cluster' in customer_info:
            customer_info['persona'] = self._get_persona_from_cluster(customer_info['cluster'])
        
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
        if self.agent_a and hasattr(self.agent_a, 'personas'):
            if cluster_id in self.agent_a.personas:
                persona_data = self.agent_a.personas[cluster_id]
                return persona_data.get('short_name', persona_data.get('persona_name', f'Persona {cluster_id}'))
        
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

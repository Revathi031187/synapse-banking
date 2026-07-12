"""
Agent A Enhanced - Banking with Business Constraints
Adapted from Academy Sports agent for banking/financial services
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from pathlib import Path
import sys
import os

try:
    from kmodes.kprototypes import KPrototypes
    KMODES_AVAILABLE = True
except ImportError:
    print("Warning: kmodes not installed. Run: pip install kmodes")
    KMODES_AVAILABLE = False

# Add utils to path for image mapper and optional LLM
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.image_mapper import get_image_mapper
    IMAGE_MAPPER_AVAILABLE = True
except ImportError:
    IMAGE_MAPPER_AVAILABLE = False
    print("Warning: Image mapper not available")
try:
    from utils.together_ai import together_ai
    TOGETHER_AI_AVAILABLE = True
except ImportError:
    TOGETHER_AI_AVAILABLE = False
    together_ai = None

try:
    from utils.claude_client import get_claude_client
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    get_claude_client = None

logger = logging.getLogger(__name__)


class AgentA_Banking_Enhanced:
    """
    Enhanced Agent A for Banking: Dynamic Persona Builder
    
    Identifies 4-5 customer personas based on data-driven clustering with business constraints
    Uses AI to generate persona names and descriptions based on actual cluster characteristics
    """
    
    def __init__(self, data_path: str = 'data/preloaded/banking_nba'):
        """Initialize Enhanced Agent A for Banking"""
        self.data_path = Path(data_path)
        self.customers_df = None
        self.transactions_df = None
        self.products_df = None
        self.cluster_model = None
        self.personas = {}
        
        logger.info(f"🏦 Agent A Banking Enhanced initialized with data path: {data_path}")
    
    def load_data(self, dataset_version='v1'):
        """Load banking customer data from CSV with retry logic"""
        import time
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                customers_path = self.data_path / 'customers.csv'
                transactions_path = self.data_path / 'transactions.csv'
                products_path = self.data_path / 'products.csv'
                
                logger.info(f"📊 Loading Banking dataset (attempt {attempt + 1}/{max_retries})")
                
                # Use engine='python' for robust CSV parsing (handles various line endings)
                self.customers_df = pd.read_csv(customers_path, engine='python')
                self.transactions_df = pd.read_csv(transactions_path, engine='python')
                self.products_df = pd.read_csv(products_path, engine='python')
                
                # DEBUG: Log column info BEFORE derived columns
                logger.info(f"📊 CSV loaded: {len(self.customers_df.columns)} columns")
                logger.info(f"  First 5 columns: {list(self.customers_df.columns[:5])}")
                logger.info(f"  'monthly_transaction_volume' exists: {'monthly_transaction_volume' in self.customers_df.columns}")
                
                # Create derived columns to match expected schema
                self._create_derived_columns()
                
                # DEBUG: Log column info AFTER derived columns
                logger.info(f"  After _create_derived_columns: 'monthly_transaction_volume' exists: {'monthly_transaction_volume' in self.customers_df.columns}")
                
                logger.info(f"✓ Loaded {len(self.customers_df)} customers, {len(self.customers_df.columns)} columns total, {len(self.transactions_df)} transactions, {len(self.products_df)} products")
                return True
                
            except FileNotFoundError as e:
                logger.error(f"Dataset not found (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed after {max_retries} attempts")
                    return False
                    
            except Exception as e:
                logger.error(f"Error loading data (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed after {max_retries} attempts")
                    return False
        
        return False
    
    def _create_derived_columns(self):
        """Create derived columns from banking_nba data to match expected schema"""
        # Backward-compat aliases: new column names → old names expected by all downstream code
        _col_aliases = {
            'total_deposit_value':       'total_deposits',
            'avg_daily_balance_p30days': 'avg_daily_balance',
            'customer_type':             'customer_segment',
            'credit_score_trend_p6mo':   'credit_score_trend',
        }
        for new_col, old_col in _col_aliases.items():
            if new_col in self.customers_df.columns and old_col not in self.customers_df.columns:
                self.customers_df[old_col] = self.customers_df[new_col]

        # Map existing columns to expected names
        if 'login_frequency_30d' in self.customers_df.columns:
            # Normalize login frequency to 0-1 scale
            max_logins = self.customers_df['login_frequency_30d'].max()
            if max_logins > 0:
                self.customers_df['digital_engagement_score'] = self.customers_df['login_frequency_30d'] / max_logins
            else:
                self.customers_df['digital_engagement_score'] = 0.5
        
        # Branch visit frequency (inverse of mobile preference)
        if 'channel_preference' in self.customers_df.columns:
            self.customers_df['branch_visit_frequency'] = self.customers_df['channel_preference'].apply(
                lambda x: 0.1 if x == 'mobile' else (0.5 if x == 'hybrid' else 0.8)
            )
        else:
            self.customers_df['branch_visit_frequency'] = 0.3
        
        # Product adoption velocity (based on products per tenure)
        # Preserve pre-patched num_products from customers.csv if already meaningful
        _has_products_col = (
            'num_products' in self.customers_df.columns
            and self.customers_df['num_products'].notna().all()
            and self.customers_df['num_products'].mean() > 0.5
        )
        if not _has_products_col:
            try:
                if 'product_id' in self.transactions_df.columns:
                    product_counts = self.transactions_df.groupby('customer_id')['product_id'].nunique()
                    self.customers_df['num_products'] = self.customers_df['customer_id'].map(product_counts).fillna(2)
                else:
                    try:
                        holdings_df = pd.read_csv(self.data_path / 'product_holdings.csv')
                        product_counts = holdings_df.groupby('customer_id').size()
                        self.customers_df['num_products'] = self.customers_df['customer_id'].map(product_counts).fillna(2)
                    except:
                        self.customers_df['num_products'] = 2
            except Exception as e:
                logger.warning(f"Could not count products: {e}")
                self.customers_df['num_products'] = 2
        
        # Now calculate product adoption velocity if tenure exists
        tenure_col = 'months_since_relationship_started' if 'months_since_relationship_started' in self.customers_df.columns else 'tenure_months'
        if tenure_col in self.customers_df.columns:
            self.customers_df['product_adoption_velocity'] = (
                self.customers_df['num_products'] / (self.customers_df[tenure_col] + 1)
            ).clip(0, 1)
        else:
            self.customers_df['product_adoption_velocity'] = 0.5
        
        # Cross-sell receptivity (use existing column or calculate from intent_score)
        if 'cross_sell_receptivity' not in self.customers_df.columns:
            if 'intent_score' in self.customers_df.columns:
                self.customers_df['cross_sell_receptivity'] = self.customers_df['intent_score']
            else:
                self.customers_df['cross_sell_receptivity'] = 0.5
        
        # Total deposits (use existing column or calculate from estimated_savings)
        if 'total_deposits' not in self.customers_df.columns:
            if 'estimated_savings' in self.customers_df.columns:
                self.customers_df['total_deposits'] = self.customers_df['estimated_savings']
            else:
                self.customers_df['total_deposits'] = self.customers_df['income'] * 0.15
        
        # Total loan balance (from debt_to_income_ratio)
        if 'debt_to_income_ratio' in self.customers_df.columns:
            self.customers_df['total_loan_balance'] = self.customers_df['income'] * self.customers_df['debt_to_income_ratio']
        else:
            self.customers_df['total_loan_balance'] = 0
        
        # Monthly transaction volume (calculate from actual transactions only - NO FALLBACK)
        if 'monthly_transaction_volume' not in self.customers_df.columns:
            if 'transaction_volume_30d' in self.customers_df.columns:
                self.customers_df['monthly_transaction_volume'] = self.customers_df['transaction_volume_30d']
            elif self.transactions_df is not None and len(self.transactions_df) > 0:
                # Calculate from transactions.csv
                txn_counts = self.transactions_df.groupby('customer_id').size()
                self.customers_df['monthly_transaction_volume'] = self.customers_df['customer_id'].map(txn_counts).fillna(0)
            else:
                # NO FALLBACK - require real data
                raise ValueError("Cannot calculate monthly_transaction_volume: transactions.csv is required")
        
        # Avg daily balance (from estimated_savings)
        if 'estimated_savings' in self.customers_df.columns:
            self.customers_df['avg_daily_balance'] = self.customers_df['estimated_savings']
        else:
            self.customers_df['avg_daily_balance'] = self.customers_df['income'] * 0.10
        
        # Overdraft frequency (estimate from risk_category)
        if 'risk_category' in self.customers_df.columns:
            self.customers_df['overdraft_frequency'] = self.customers_df['risk_category'].apply(
                lambda x: 5 if x == 'high' else (2 if x == 'medium' else 0)
            )
        else:
            self.customers_df['overdraft_frequency'] = 1
        
        # Credit utilization (from debt_to_income_ratio)
        if 'debt_to_income_ratio' in self.customers_df.columns:
            self.customers_df['credit_utilization_ratio'] = self.customers_df['debt_to_income_ratio']
        else:
            self.customers_df['credit_utilization_ratio'] = 0.3
        
        # Map channel preference
        if 'channel_preference' in self.customers_df.columns:
            self.customers_df['channel_preference'] = self.customers_df['channel_preference'].replace({
                'mobile': 'Digital',
                'branch': 'Branch',
                'hybrid': 'Hybrid'
            })
        else:
            self.customers_df['channel_preference'] = 'Hybrid'
        
        # Geographic region (default to Suburban)
        if 'geographic_region' not in self.customers_df.columns:
            self.customers_df['geographic_region'] = 'Suburban'
        
        # Home ownership (estimate from income and age)
        if 'home_ownership' not in self.customers_df.columns:
            self.customers_df['home_ownership'] = self.customers_df.apply(
                lambda row: 'Own' if row['age'] > 50 and row['income'] > 75000 
                else ('Mortgage' if row['age'] > 35 else 'Rent'),
                axis=1
            )
        
        # Life stage (from age)
        if 'life_stage' not in self.customers_df.columns:
            self.customers_df['life_stage'] = self.customers_df['age'].apply(
                lambda age: 'Student' if age < 23 
                else ('Young Professional' if age < 35 
                else ('Family' if age < 55 
                else ('Pre-Retiree' if age < 65 else 'Retiree')))
            )
        
        # Account tenure months
        tenure_col = 'months_since_relationship_started' if 'months_since_relationship_started' in self.customers_df.columns else 'tenure_months'
        if tenure_col in self.customers_df.columns:
            self.customers_df['account_tenure_months'] = self.customers_df[tenure_col]
        else:
            self.customers_df['account_tenure_months'] = 24
        
        # Relationship length years
        self.customers_df['relationship_length_years'] = (self.customers_df['account_tenure_months'] / 12).astype(int)
        
        # Risk tolerance (preserve CSV value if present; derive from risk_category as fallback)
        if 'risk_tolerance' not in self.customers_df.columns:
            if 'risk_category' in self.customers_df.columns:
                self.customers_df['risk_tolerance'] = self.customers_df['risk_category'].astype(str).replace({
                    'low': 'Conservative',
                    'medium': 'Moderate',
                    'high': 'Aggressive'
                })
            else:
                self.customers_df['risk_tolerance'] = 'Moderate'
        
        # Join date (estimate from tenure)
        from datetime import datetime, timedelta
        today = datetime.now()
        self.customers_df['join_date'] = self.customers_df['account_tenure_months'].apply(
            lambda months: (today - timedelta(days=int(months * 30))).strftime('%Y-%m-%d')
        )
        
        logger.info("✅ Created derived columns for clustering")
    
    # Canonical archetype names — one fixed name per archetype type.
    # These are the exact names the business wants: clear, non-technical, universally understandable.
    _ARCHETYPE_CANONICAL_NAMES = {
        'HIGH-VALUE':    'Wealth Builder',
        'EVERYDAY':      'Everyday Essential',
        'DIGITAL-FIRST': 'Digital Native',
        'LOYAL-STABLE':  'Retiree Anchor',
        'AT-RISK':       'At-Risk Borrower',
    }

    # Trait-based fallback pools — used only when archetype pre-classification is unavailable
    _TRAIT_NAME_POOLS = {
        'deposits':     ['Wealth Builder', 'Deep Saver', 'Vault Keeper', 'Capital Grower', 'Legacy Holder'],
        'digital':      ['Digital Native', 'Mobile Pioneer', 'App-First Banker', 'Connected Spender', 'Tech Adopter'],
        'products':     ['Full-Stack Client', 'Relationship Maximizer', 'Deep Bundler', 'Portfolio Builder', 'All-In Banker'],
        'transactions': ['Everyday Essential', 'Active Transactor', 'Daily Driver', 'Frequent Mover', 'Core Spender'],
        'cross_sell':   ['Rising Achiever', 'Growth Seeker', 'Cautious Climber', 'Ready Mover', 'Opportunity Seeker'],
        'income':       ['At-Risk Borrower', 'Income Leader', 'Top Bracket', 'Cautious Spender', 'High Earner'],
    }

    def _generate_dynamic_segment_profile(self, characteristics, percentile, primary_trait, avg_transactions_real, cluster_id=None, used_names=None, extra_stats=None):
        """
        Generate segment name + plain-English description via LLM.
        Returns (name: str, description: str). Falls back to canonical name on failure.
        """
        import time
        extra = extra_stats or {}
        archetype_type = extra.get('archetype_type', '')

        if CLAUDE_AVAILABLE and get_claude_client:
            try:
                client = get_claude_client()
                if client.is_available():
                    t0 = time.monotonic()
                    stats_for_llm = {
                        'avg_income':               characteristics.get('avg_income', 0),
                        'avg_credit_score':         characteristics.get('avg_credit_score', 650),
                        'avg_deposits':             characteristics.get('avg_deposits', 0),
                        'avg_digital_engagement':   characteristics.get('avg_digital', 0.5),
                        'avg_products':             characteristics.get('avg_products', 2.0),
                        'avg_transactions':         avg_transactions_real,
                        'avg_age':                  characteristics.get('avg_age', 40),
                        'dominant_life_stage':      characteristics.get('dominant_life_stage', ''),
                        'dominant_risk_tolerance':  extra.get('dominant_risk', characteristics.get('dominant_risk_tolerance', 'Moderate')),
                        'dominant_financial_goal':  extra.get('dominant_goal', ''),
                        'avg_churn_probability':    extra.get('avg_churn', 0.15),
                        'dominant_clv_tier':        extra.get('dominant_clv_tier', 'Silver'),
                        'primary_trait':            primary_trait,
                        'archetype_type':           archetype_type,
                    }
                    result = client.generate_segment_profile(
                        stats_for_llm,
                        used_names=list(used_names) if used_names else [],
                        segment_type="macro",
                    )
                    duration_ms = int((time.monotonic() - t0) * 1000)
                    llm_name = result.get('name', '')
                    llm_desc = result.get('description', '')
                    if llm_name and 1 <= len(llm_name.split()) <= 4:
                        logger.info(f"LLM segment: '{llm_name}' ({archetype_type}, {duration_ms}ms)")
                        characteristics['_segment_name_source'] = 'llm'
                        characteristics['_segment_description'] = llm_desc
                        return llm_name, llm_desc
            except Exception as e:
                logger.warning(f"Claude segment profile failed, using fallback: {e}")

        # Fallback to canonical name when LLM is unavailable
        fallback_name = self._ARCHETYPE_CANONICAL_NAMES.get(
            archetype_type,
            self._trait_based_segment_name(primary_trait, characteristics, cluster_id, used_names)
        )
        characteristics['_segment_name_source'] = 'rule_based'
        desc = f"{fallback_name} — {archetype_type or primary_trait} customer group."
        characteristics['_segment_description'] = desc
        return fallback_name, desc

    def _generate_dynamic_segment_name(self, characteristics, percentile, primary_trait, avg_transactions_real, cluster_id=None, used_names=None):
        """Thin wrapper kept for backward compat — returns name only."""
        name, _ = self._generate_dynamic_segment_profile(
            characteristics, percentile, primary_trait, avg_transactions_real,
            cluster_id=cluster_id, used_names=used_names,
        )
        return name

    def _trait_based_segment_name(self, primary_trait, characteristics, cluster_id=None, used_names=None):
        """Deterministic fallback: pick the first unused name from the trait pool."""
        pool = self._TRAIT_NAME_POOLS.get(primary_trait, self._TRAIT_NAME_POOLS['deposits'])
        taken = set(used_names or [])
        for name in pool:
            if name not in taken:
                return name
        # All pool names taken — append cluster id to last entry to guarantee uniqueness
        return f"{pool[-1]} {cluster_id or ''}"
    
    def _classify_customer_to_segment(self, row):
        """Deterministic per-customer rule-based segmentation.

        Called after K-Prototypes to override unreliable cluster assignments.
        Rules are calibrated to the v2 Meridian Bank data distributions and
        guarantee the correct 5 archetypes regardless of K-Prototypes initialization.

        Cluster IDs:
          0 = HIGH-VALUE   (Wealth Builder)
          1 = DIGITAL-FIRST (Digital Native)
          2 = EVERYDAY     (Everyday Essential)
          3 = LOYAL-STABLE  (Retiree Anchor)
          4 = AT-RISK       (At-Risk Borrower)
        """
        age      = float(row.get('age', 45) or 45)
        digital  = float(row.get('digital_engagement_score', 0.5) or 0.5)
        deposits = float(row.get('total_deposits', 0) or 0)
        income   = float(row.get('income', 50000) or 50000)
        credit   = float(row.get('credit_score', 650) or 650)
        churn    = float(row.get('churn_probability', 0.2) or
                         row.get('churn_proxy', 0.2) or 0.2)

        # 1. Retiree Anchor — elderly + very low digital (unique age+digital signature)
        #    Retiree patch lo=57, Everyday hi=63 — threshold 63 sits above the new overlap zone
        if age >= 63 and digital < 0.45:
            return 3  # LOYAL-STABLE

        # 2. Digital Native — extremely high digital (0.82-0.99)
        #    Wealth Builder digital is capped at 0.78 in v2 data, gap is clean
        elif digital >= 0.79:
            return 1  # DIGITAL-FIRST

        # 3. At-Risk Borrower — low credit + high churn
        #    At-Risk credit: 512-612; churn: 0.38-0.88. Everyday credit min ~644 — no overlap.
        #    At-Risk deposits now ~$20K; classification relies purely on credit + churn signals.
        elif credit <= 630 and churn >= 0.38:
            return 4  # AT-RISK

        # 4. Wealth Builder — high income (primary separator)
        #    Digital max ~$122K, Everyday max ~$102K — threshold at $128K sits cleanly above both
        elif income >= 128000:
            return 0  # HIGH-VALUE

        # 5. Everyday Essential — residual bucket
        else:
            return 2  # EVERYDAY

    def _relabel_clusters_to_archetypes(self, df):
        """Rename K-Prototypes cluster IDs to canonical archetype IDs by centroid proximity.

        Does NOT reassign customers — only renames cluster labels so downstream
        persona-naming always sees the expected IDs:
          0 = HIGH-VALUE    (Wealth Builder)
          1 = DIGITAL-FIRST (Digital Native)
          2 = EVERYDAY      (Everyday Essential)
          3 = LOYAL-STABLE  (Retiree Anchor)
          4 = AT-RISK       (At-Risk Borrower)
        """
        import numpy as np

        FEATURE_COLS = ['income', 'credit_score', 'total_deposits',
                        'digital_engagement_score', 'age', 'churn_probability']
        available = [c for c in FEATURE_COLS if c in df.columns]

        ARCHETYPE_TARGETS = {
            0: {'income': 195000, 'credit_score': 810, 'total_deposits': 115000,
                'digital_engagement_score': 0.64, 'age': 48, 'churn_probability': 0.09},
            1: {'income':  82000, 'credit_score': 700, 'total_deposits': 42000,
                'digital_engagement_score': 0.92, 'age': 27, 'churn_probability': 0.30},
            2: {'income':  72000, 'credit_score': 710, 'total_deposits': 52000,
                'digital_engagement_score': 0.45, 'age': 41, 'churn_probability': 0.26},
            3: {'income':  38000, 'credit_score': 780, 'total_deposits': 185000,
                'digital_engagement_score': 0.22, 'age': 70, 'churn_probability': 0.07},
            4: {'income':  35000, 'credit_score': 568, 'total_deposits': 10000,
                'digital_engagement_score': 0.52, 'age': 35, 'churn_probability': 0.58},
        }

        cluster_ids = sorted(df['cluster'].unique())
        n_archetypes = 5

        cluster_means = np.array([
            [df.loc[df['cluster'] == cid, col].mean() for col in available]
            for cid in cluster_ids
        ])
        archetype_means = np.array([
            [ARCHETYPE_TARGETS[aid].get(col, 0) for col in available]
            for aid in range(n_archetypes)
        ])

        # Normalize by cross-cluster std so no single feature (e.g. income) dominates
        scales = cluster_means.std(axis=0) + 1e-6
        cm_norm = cluster_means / scales
        am_norm = archetype_means / scales

        # Pairwise Euclidean distances: (n_clusters × n_archetypes)
        dist = np.sqrt(((cm_norm[:, np.newaxis, :] - am_norm[np.newaxis, :, :]) ** 2).sum(axis=2))

        # Greedy assignment: smallest distance first, each cluster/archetype used once
        mapping = {}
        used_archetypes = set()
        for idx in np.argsort(dist.ravel()):
            ci, ai = divmod(int(idx), n_archetypes)
            if cluster_ids[ci] not in mapping and ai not in used_archetypes:
                mapping[cluster_ids[ci]] = ai
                used_archetypes.add(ai)
            if len(mapping) == len(cluster_ids):
                break

        for cid in cluster_ids:
            if cid not in mapping:
                mapping[cid] = 2  # residual → EVERYDAY

        return mapping

    def _classify_archetype(self, characteristics, extra_stats, assigned_types):
        """Rule-based pre-classification into one of 5 banking archetypes.

        Uses THRESHOLD-BASED scoring: each archetype score is 0 for an average customer
        and only rises when stats clearly exceed the archetype threshold. EVERYDAY has a
        small fixed score so it wins whenever no other archetype fires strongly — this
        prevents the majority 'average' cluster from being misclassified as AT-RISK."""
        income   = characteristics.get('avg_income', 0)
        credit   = characteristics.get('avg_credit_score', 650)
        deposits = characteristics.get('avg_deposits', 0)
        digital  = characteristics.get('avg_digital', 0.5)
        age      = characteristics.get('avg_age', 45)
        churn    = extra_stats.get('avg_churn', 0.15)
        txn      = extra_stats.get('avg_transactions', 20)

        all_scores = {
            # HIGH-VALUE: only fires for genuinely high income+credit+deposits
            'HIGH-VALUE': (max(0, income - 100000) / 20000
                           + max(0, credit - 740) / 50
                           + max(0, deposits - 75000) / 25000),
            # DIGITAL-FIRST: high digital AND young AND high transactions
            'DIGITAL-FIRST': (max(0, digital - 0.62) / 0.15
                               + max(0, 37 - age) / 8
                               + max(0, txn - 50) / 20),
            # LOYAL-STABLE: older, branch-preferring, low churn
            'LOYAL-STABLE': (max(0, age - 58) / 8
                              + max(0, 0.42 - digital) / 0.15
                              + max(0, 0.20 - churn) * 5),
            # AT-RISK: genuinely low income + low credit + high churn
            'AT-RISK': (max(0, 50000 - income) / 15000
                        + max(0, 640 - credit) / 50
                        + max(0, churn - 0.28) / 0.25),
            # EVERYDAY: fixed baseline — wins when no strong archetype signal found
            'EVERYDAY': 2.0,
        }
        # Exclude already-assigned archetypes to enforce variety across segments.
        # If all 5 are taken (n > 5 segments), allow reuse — the LLM will generate
        # a variant name since the original is already in used_names.
        scores = {k: v for k, v in all_scores.items() if k not in assigned_types}
        if not scores:
            scores = all_scores  # n > 5: pick best-fit regardless of prior assignments

        return max(scores, key=scores.get)

    def _calculate_real_transaction_metrics(self, cluster_data):
        """
        Calculate transaction metrics - PRIORITIZE customer column (source of truth)
        The monthly_transaction_volume in customers.csv is accurate (10-150 range)
        """
        # PRIMARY: Use customer column data (MOST ACCURATE - generated with correct range)
        if 'monthly_transaction_volume' in cluster_data.columns:
            avg_monthly = cluster_data['monthly_transaction_volume'].mean()
            logger.info(f"  ✓ Using customer column: avg_monthly={avg_monthly:.1f} transactions/month (range: {cluster_data['monthly_transaction_volume'].min():.0f}-{cluster_data['monthly_transaction_volume'].max():.0f})")
            return {
                'total_transactions': int(avg_monthly * len(cluster_data) * 12),
                'avg_transactions_per_customer': float(avg_monthly * 12),
                'monthly_transaction_rate': float(avg_monthly),  # THIS IS SHOWN IN UI
                'transaction_count': int(avg_monthly * len(cluster_data))
            }
        
        # FALLBACK: Use transaction file if customer column missing
        if self.transactions_df is not None and len(self.transactions_df) > 0:
            logger.warning(f"  ⚠ monthly_transaction_volume column NOT FOUND! Falling back to transaction file")
            logger.warning(f"  Available columns: {list(cluster_data.columns[:10])}")
            # Get customer IDs in this cluster
            cluster_customer_ids = cluster_data['customer_id'].tolist()
            
            # Filter transactions for these customers
            cluster_transactions = self.transactions_df[
                self.transactions_df['customer_id'].isin(cluster_customer_ids)
            ].copy()
            
            # Calculate total transactions
            total_transactions = len(cluster_transactions)
            
            # Calculate per-customer average
            txn_per_customer = cluster_transactions.groupby('customer_id').size()
            avg_transactions = txn_per_customer.mean() if len(txn_per_customer) > 0 else 0
            
            # Calculate transaction velocity (last 30 days vs all time)
            if 'transaction_date' in cluster_transactions.columns:
                try:
                    cluster_transactions['transaction_date'] = pd.to_datetime(cluster_transactions['transaction_date'])
                    latest_date = cluster_transactions['transaction_date'].max()
                    thirty_days_ago = latest_date - pd.Timedelta(days=30)
                    
                    recent_txns = cluster_transactions[cluster_transactions['transaction_date'] >= thirty_days_ago]
                    recent_count = len(recent_txns)
                    
                    # Monthly transaction rate
                    if recent_count > 0:
                        monthly_rate = recent_count / len(cluster_customer_ids)
                    else:
                        monthly_rate = total_transactions / len(cluster_customer_ids) / 12
                except:
                    monthly_rate = total_transactions / len(cluster_customer_ids) / 12
            else:
                monthly_rate = total_transactions / len(cluster_customer_ids) / 12
            
            logger.debug(f"  Cluster transaction metrics: total={total_transactions}, avg_per_customer={avg_transactions:.1f}, monthly_rate={monthly_rate:.1f}")
            
            logger.debug(f"  Using transaction file: monthly_rate={monthly_rate:.1f}")
            return {
                'total_transactions': int(total_transactions),
                'avg_transactions_per_customer': float(avg_transactions),
                'monthly_transaction_rate': float(monthly_rate),
                'transaction_count': int(total_transactions)
            }
        else:
            # No data available
            logger.warning("  ⚠ No transaction data available!")
            return {
                'total_transactions': 0,
                'avg_transactions_per_customer': 0,
                'monthly_transaction_rate': 0,
                'transaction_count': 0
            }
    
    def _calculate_dynamic_intent_score(self, cluster_data, gamma_weight):
        """
        Calculate intent score dynamically based on:
        1. Cross-sell receptivity (existing willingness)
        2. Product adoption rate (actual behavior)
        3. Transaction frequency (engagement)
        4. Digital engagement (channel preference)
        5. Gamma weighting (numeric vs categorical emphasis)
        
        The score CHANGES based on gamma value - higher gamma = more weight on transactions/behavior
        """
        
        # Base components (normalized 0-1)
        cross_sell_base = cluster_data['cross_sell_receptivity'].mean() if 'cross_sell_receptivity' in cluster_data.columns else 0.5
        
        # Product adoption velocity (more products = higher intent)
        tenure_col = 'months_since_relationship_started' if 'months_since_relationship_started' in cluster_data.columns else 'tenure_months'
        if 'num_products' in cluster_data.columns and tenure_col in cluster_data.columns:
            product_velocity = (cluster_data['num_products'] / (cluster_data[tenure_col] + 1)).mean()
            product_velocity = min(product_velocity, 1.0)  # Cap at 1.0
        else:
            product_velocity = 0.5
        
        # Transaction engagement (normalized to 0-1 based on max 200 transactions/month)
        if 'monthly_transaction_volume' in cluster_data.columns:
            txn_engagement = min(cluster_data['monthly_transaction_volume'].mean() / 200.0, 1.0)
        else:
            txn_engagement = 0.5
        
        # Digital engagement
        digital_engagement = cluster_data['digital_engagement_score'].mean() if 'digital_engagement_score' in cluster_data.columns else 0.5
        
        # Financial health (credit score normalized)
        if 'credit_score' in cluster_data.columns:
            financial_health = cluster_data['credit_score'].mean() / 850.0
        else:
            financial_health = 0.7
        
        # Calculate weighted intent score based on GAMMA (MORE DRAMATIC DIFFERENCE)
        # High gamma (0.75) = emphasize numeric behaviors (transactions, products, wealth)
        # Low gamma (0.25) = emphasize categorical traits (stated preferences, segments)
        
        # Make the formula MORE sensitive to gamma by using gamma directly as multiplier
        behavior_weight = gamma_weight  # 0.25 or 0.75
        preference_weight = 1 - gamma_weight  # 0.75 or 0.25
        
        # Behavior components (numeric)
        behavior_score = (
            txn_engagement * 0.40 +       # Transaction frequency
            product_velocity * 0.35 +     # Product adoption rate
            financial_health * 0.25       # Financial capability
        )
        
        # Preference components (categorical/stated)
        preference_score = (
            cross_sell_base * 0.60 +      # Stated willingness
            digital_engagement * 0.40     # Channel preference
        )
        
        # Weighted combination based on gamma
        intent_score = (behavior_score * behavior_weight) + (preference_score * preference_weight)
        
        # Add variability boost based on cluster characteristics
        # High-value segments should have higher intent
        if 'total_deposits' in cluster_data.columns:
            avg_deposits = cluster_data['total_deposits'].mean()
            wealth_factor = min(avg_deposits / 50000.0, 1.5)  # Up to 1.5x boost for wealthy segments
            intent_score = min(intent_score * wealth_factor, 0.99)

        # Spread segments that would otherwise round to the same % (e.g. many at 0.55)
        if self.customers_df is not None and 'cross_sell_receptivity' in self.customers_df.columns:
            pop_mean_cs = float(self.customers_df['cross_sell_receptivity'].mean())
            delta_cs = float(cross_sell_base - pop_mean_cs)
            intent_score = float(intent_score + delta_cs * 0.28)
        intent_score = float(min(max(intent_score, 0.08), 0.97))
        
        logger.debug(f"  Intent calculation: cross_sell={cross_sell_base:.2f}, product_vel={product_velocity:.2f}, txn_eng={txn_engagement:.2f}, digital={digital_engagement:.2f}, final={intent_score:.2f}")
        
        return float(intent_score)
    
    def execute(self, params: Dict = None) -> Dict:
        """
        Execute dynamic clustering with business constraints
        
        Args:
            params: Configuration parameters
                - dataset_version: 'v1' (default)
                - n_clusters: Number of clusters to try (4-5 recommended)
                - gamma: Weighting for categorical vs numeric (default 0.5)
        
        Returns:
            Dictionary with personas, visualization data, and validation results
        """
        if not KMODES_AVAILABLE:
            return {'error': 'kmodes not installed'}
        
        if params is None:
            params = {}
        
        # Load data
        dataset_version = params.get('dataset_version', 'v1')
        if not self.load_data(dataset_version):
            return {'error': 'Failed to load data'}
        
        # Clustering parameters
        n_clusters_input = params.get('n_clusters', 5)
        gamma = params.get('gamma', 0.75)  # INCREASED: Weight numeric features (deposits, transactions) more heavily for better separation
        
        # Use exact number requested (no optimization search for speed)
        cluster_range = [n_clusters_input]
        
        # Create enhanced features
        from sklearn.preprocessing import StandardScaler
        
        df_enhanced = self.customers_df.copy()
        
        # ============================================================================
        # DATA VALIDATION - Prevent NaN and missing value errors
        # ============================================================================
        
        # Critical columns for banking
        required_columns = [
            'customer_id', 'digital_engagement_score', 'branch_visit_frequency',
            'product_adoption_velocity', 'cross_sell_receptivity', 'risk_tolerance',
            'channel_preference', 'age', 'income', 'credit_score',
            'total_deposits', 'total_loan_balance', 'monthly_transaction_volume',
            'avg_daily_balance', 'num_products', 'geographic_region',
            'home_ownership', 'life_stage'
        ]
        
        # Validate all required columns exist
        missing_cols = [col for col in required_columns if col not in df_enhanced.columns]
        if missing_cols:
            logger.error(f"❌ Missing required columns: {missing_cols}")
            return {'error': f'Missing required columns: {missing_cols}'}
        
        # Fill NaN values BEFORE any calculations
        numeric_fill_cols = [
            'digital_engagement_score', 'branch_visit_frequency',
            'product_adoption_velocity', 'cross_sell_receptivity',
            'age', 'income', 'credit_score', 'total_deposits',
            'total_loan_balance', 'monthly_transaction_volume',
            'avg_daily_balance', 'num_products', 'overdraft_frequency',
            'credit_utilization_ratio'
        ]
        
        for col in numeric_fill_cols:
            if col in df_enhanced.columns:
                median_val = df_enhanced[col].median()
                if pd.isna(median_val):
                    median_val = 0.0
                df_enhanced[col] = df_enhanced[col].fillna(median_val)
                df_enhanced[col] = df_enhanced[col].replace([np.inf, -np.inf], median_val)
        
        categorical_fill_cols = ['risk_tolerance', 'channel_preference', 'geographic_region', 'home_ownership', 'life_stage']
        for col in categorical_fill_cols:
            if col in df_enhanced.columns:
                df_enhanced[col] = df_enhanced[col].fillna('Unknown')
        
        logger.info("✅ Data validation complete - all NaN values handled")
        
        # ============================================================================
        # Add composite features for banking
        # ============================================================================
        
        # Customer value score (like RFM for banking)
        df_enhanced['customer_value_score'] = (
            (df_enhanced['total_deposits'] / df_enhanced['total_deposits'].max()) * 0.4 +
            (df_enhanced['num_products'] / df_enhanced['num_products'].max()) * 0.3 +
            (df_enhanced['monthly_transaction_volume'] / df_enhanced['monthly_transaction_volume'].max()) * 0.3
        )
        
        # Digital adoption score
        df_enhanced['digital_adoption'] = (
            df_enhanced['digital_engagement_score'] * 0.7 +
            (1 - df_enhanced['branch_visit_frequency']) * 0.3
        )
        
        # Financial health score
        df_enhanced['financial_health'] = (
            (df_enhanced['credit_score'] / 850.0) * 0.5 +
            (1 - df_enhanced['credit_utilization_ratio']) * 0.3 +
            (1 - (df_enhanced['overdraft_frequency'] / 10.0)) * 0.2
        )
        
        # Normalized age — key for separating Retiree Anchor (old) from Digital Native (young)
        if 'age' in df_enhanced.columns:
            age_min = df_enhanced['age'].min()
            age_max = df_enhanced['age'].max()
            df_enhanced['age_normalized'] = (df_enhanced['age'] - age_min) / (age_max - age_min + 1e-6)
        else:
            df_enhanced['age_normalized'] = 0.4

        # Churn/risk proxy — key for isolating the At-Risk Borrower archetype
        if 'churn_probability' in df_enhanced.columns:
            df_enhanced['churn_proxy'] = df_enhanced['churn_probability']
        elif 'overdraft_frequency' in df_enhanced.columns:
            df_max = df_enhanced['overdraft_frequency'].max()
            df_enhanced['churn_proxy'] = (df_enhanced['overdraft_frequency'] / (df_max + 1e-6)).fillna(0.15)
        else:
            df_enhanced['churn_proxy'] = 0.15

        # Select features for clustering with IMPORTANCE WEIGHTING
        # PRIMARY: features that drive the 5 core banking archetypes
        #   Wealth Builder  → total_deposits + income + credit_score (high all three)
        #   Everyday Essential → income (mid) + digital_engagement (low/mid) + cross_sell
        #   Digital Native  → digital_engagement_score + monthly_transaction_volume
        #   Retiree Anchor  → age_normalized (high) + total_deposits (high) + churn_proxy (low)
        #   At-Risk Borrower → credit_score (low) + churn_proxy (high) + income (low)
        primary_features = [
            'total_deposits',             # Wealth tier → Wealth Builder / Retiree Anchor
            'income',                     # Earning power → Wealth Builder / At-Risk
            'credit_score',               # Creditworthiness → At-Risk Borrower
            'monthly_transaction_volume', # Activity level → Digital Native / Everyday Essential
            'digital_engagement_score',   # Channel preference → Digital Native
            'churn_proxy',                # Risk level → At-Risk Borrower
            'age_normalized',             # MOVED to primary: life stage → Retiree Anchor vs Digital Native
        ]

        # Supporting features (1× weight)
        secondary_features = [
            'num_products',
            'cross_sell_receptivity',
            'product_adoption_velocity',
            # Removed: digital_adoption (correlated with digital_engagement_score → was 3× digital weight)
            # Removed: customer_value_score, financial_health (composite / double-counts income + deposits)
        ]

        # BOOST primary features by duplicating them (increases their weight in clustering)
        numeric_cols = primary_features + primary_features + secondary_features  # Primary features count 2x
        
        categorical_cols = [
            'risk_tolerance', 'channel_preference', 'geographic_region',
            'home_ownership', 'life_stage'
        ]
        
        # Prepare data
        X = df_enhanced[numeric_cols + categorical_cols].copy()
        
        # Handle missing values
        for col in numeric_cols:
            X[col] = X[col].fillna(X[col].median())
        for col in categorical_cols:
            X[col] = X[col].fillna('Unknown')
        
        # Scale numeric features with VARIANCE PRESERVATION
        # Use RobustScaler to handle outliers better and preserve differences
        from sklearn.preprocessing import RobustScaler
        scaler = RobustScaler()  # More robust to outliers than StandardScaler
        X_numeric_scaled = scaler.fit_transform(X[numeric_cols])
        
        # AMPLIFY differences by scaling variance
        X_numeric_scaled = X_numeric_scaled * 1.5  # Amplify separation
        
        # Combine scaled numeric with categorical
        X_scaled = X.copy()
        X_scaled[numeric_cols] = X_numeric_scaled
        
        # Get categorical indices
        cat_indices = list(range(len(numeric_cols), len(numeric_cols) + len(categorical_cols)))
        
        try:
            logger.info(f"Using {len(numeric_cols)} numeric features and {len(categorical_cols)} categorical features")
            
            best_overall_model = None
            best_overall_clusters = None
            best_overall_score = -1000
            best_n_clusters = cluster_range[0]
            
            # Try different cluster numbers
            for n_clusters in cluster_range:
                logger.info(f"Trying {n_clusters} clusters...")
                
                # OPTIMIZED: Single run with reduced iterations (50x faster!)
                try:
                    model = KPrototypes(
                        n_clusters=n_clusters,
                        gamma=gamma,
                        init='Cao',
                        n_init=3,        # 3 starts — enough quality, allows boundary variation
                        max_iter=100,
                        random_state=None,  # Non-deterministic: natural variation each run
                        verbose=0
                    )
                    
                    clusters_temp = model.fit_predict(X_scaled.values, categorical=cat_indices)
                    best_model = model
                    best_cost = model.cost_
                    logger.info(f"  Cost: {best_cost:.0f}")
                    
                except Exception as e:
                    logger.error(f"Clustering failed for {n_clusters} clusters: {e}")
                    continue
                
                # Evaluate this clustering solution
                temp_clusters = best_model.predict(X_scaled.values, categorical=cat_indices)
                df_enhanced['cluster'] = temp_clusters
                self.customers_df = df_enhanced
                self.cluster_model = best_model
                
                # Generate personas temporarily to check constraints
                temp_personas = self._generate_personas(numeric_cols, categorical_cols, params)
                
                # Validate business constraints
                temp_validation = self._validate_business_constraints(
                    min_cluster_size_pct=10,
                    min_deposits_per_customer=500
                )
                
                # Score this solution
                score = temp_validation['constraints_met_count'] * 100 - temp_validation['constraints_failed_count'] * 50
                
                logger.info(f"✓ {n_clusters} clusters: score={score}, constraints met={temp_validation['constraints_met_count']}/{n_clusters}")
                
                if score > best_overall_score:
                    best_overall_score = score
                    best_overall_model = best_model
                    best_overall_clusters = temp_clusters
                    best_n_clusters = n_clusters
                    
                    if temp_validation['all_constraints_met']:
                        logger.info(f"✅ Found optimal solution with {n_clusters} clusters!")
                        break
            
            if best_overall_model is None:
                raise Exception("All clustering attempts failed")
            
            # Use best solution
            self.cluster_model = best_overall_model
            clusters = best_overall_clusters
            logger.info(f"✅ Selected {best_n_clusters} clusters with score {best_overall_score}")
            
            # Add clusters to dataframe
            df_enhanced['cluster'] = clusters
            self.customers_df = df_enhanced

            # Relabel K-Prototypes cluster IDs → canonical archetype IDs.
            # Cluster membership is preserved; only the numeric label is renamed.
            # This keeps the natural, organic counts from K-Prototypes while
            # ensuring each cluster maps to the correct archetype for persona naming.
            logger.info("Relabeling K-Prototypes clusters to canonical archetype IDs...")
            relabel_map = self._relabel_clusters_to_archetypes(df_enhanced)
            df_enhanced['cluster'] = df_enhanced['cluster'].map(relabel_map)
            self.customers_df = df_enhanced
            relabel_counts = df_enhanced['cluster'].value_counts().sort_index().to_dict()
            logger.info(f"Segment sizes after relabeling: {relabel_counts}")

            # Generate final personas
            self.personas = self._generate_personas(numeric_cols, categorical_cols)
            
            # Validate final business constraints
            constraints_validation = self._validate_business_constraints(
                min_cluster_size_pct=10,
                min_deposits_per_customer=5000
            )
            
            logger.info(f"✅ Clustering complete with {best_n_clusters} personas")
            logger.info(f"📊 Business constraints met: {constraints_validation['all_constraints_met']}")
            
            # Calculate silhouette score for validation
            silhouette_score = 0.0
            try:
                from sklearn.metrics import silhouette_score as calc_silhouette
                # Use only numeric features for silhouette score
                numeric_data = df_enhanced[numeric_cols].values
                silhouette_score = float(calc_silhouette(numeric_data, df_enhanced['cluster'].values))
                logger.info(f"📊 Silhouette Score: {silhouette_score:.3f}")
            except Exception as e:
                logger.warning(f"Could not calculate silhouette score: {e}")
                silhouette_score = None
            
            # Prepare response (micro-segments are created via separate API call, just like Academy Sports)
            return {
                'success': True,
                'n_clusters': best_n_clusters,
                'personas': self.personas,
                'customers_df': df_enhanced,  # Changed from customers_with_clusters for consistency
                'customers_with_clusters': df_enhanced,
                'constraints_validation': constraints_validation,
                'total_customers': len(df_enhanced),
                'total_deposits': float(df_enhanced['total_deposits'].sum()),
                'total_revenue': float(df_enhanced['total_deposits'].sum()),  # Simplified for demo
                'silhouette_score': silhouette_score,
                'last_refreshed': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Clustering failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def _generate_personas(self, numeric_cols, categorical_cols, params: Dict = None) -> Dict:
        """Generate persona descriptions for each cluster with UNIQUE names"""
        if params is None:
            params = {}
        
        personas = {}
        used_names = set()  # Track used names to prevent duplicates
        used_images = set()  # Track used images to prevent duplicates
        assigned_archetype_types = set()  # Each macro segment gets a distinct archetype type
        
        # Process clusters largest-first so the mega-cluster always gets first pick on archetypes.
        # This prevents a small cluster from claiming EVERYDAY and pushing the majority cluster
        # into a wrong archetype (e.g., LOYAL-STABLE for 63% of customers).
        cluster_ids_by_size = sorted(
            self.customers_df['cluster'].unique(),
            key=lambda cid: -len(self.customers_df[self.customers_df['cluster'] == cid])
        )

        for cluster_id in cluster_ids_by_size:
            cluster_data = self.customers_df[self.customers_df['cluster'] == cluster_id]

            # Calculate statistics
            size = len(cluster_data)
            percentage = (size / len(self.customers_df)) * 100
            
            # Banking-specific metrics
            avg_deposits = cluster_data['total_deposits'].mean()
            avg_income = cluster_data['income'].mean()
            avg_credit_score = cluster_data['credit_score'].mean()
            avg_products = cluster_data['num_products'].mean()
            avg_digital = cluster_data['digital_engagement_score'].mean()
            avg_cross_sell = cluster_data['cross_sell_receptivity'].mean()
            avg_age = cluster_data['age'].mean()
            avg_branch = cluster_data['branch_visit_frequency'].mean()
            
            # Dominant characteristics
            dominant_risk = cluster_data['risk_tolerance'].mode()[0] if len(cluster_data['risk_tolerance'].mode()) > 0 else 'Moderate'
            dominant_channel = cluster_data['channel_preference'].mode()[0] if len(cluster_data['channel_preference'].mode()) > 0 else 'Hybrid'
            dominant_life_stage = cluster_data['life_stage'].mode()[0] if len(cluster_data['life_stage'].mode()) > 0 else 'Unknown'
            
            # Package characteristics for criteria testing
            characteristics = {
                'avg_age': avg_age,
                'avg_income': avg_income,
                'avg_deposits': avg_deposits,
                'avg_digital': avg_digital,
                'avg_branch': avg_branch,
                'avg_products': avg_products,
                'avg_cross_sell': avg_cross_sell,
                'dominant_life_stage': dominant_life_stage
            }
            
            # PERCENTILE-BASED NAMING (matches explanation logic)
            # Calculate this segment's ranking vs all other segments
            import numpy as np
            
            # Get ALL segment values for comparison
            all_segments = []
            for cid in range(len(np.unique(self.customers_df['cluster']))):
                seg_data = self.customers_df[self.customers_df['cluster'] == cid]
                if len(seg_data) > 0:
                    # Calculate real transaction metrics for comparison
                    seg_txn_metrics = self._calculate_real_transaction_metrics(seg_data)
                    all_segments.append({
                        'deposits': seg_data['total_deposits'].mean(),
                        'digital': seg_data['digital_engagement_score'].mean(),
                        'products': seg_data['num_products'].mean(),
                        'transactions': seg_txn_metrics['avg_transactions_per_customer'],  # REAL DATA - NO FALLBACK
                        'cross_sell': seg_data['cross_sell_receptivity'].mean()
                    })
            
            # Calculate percentiles for THIS segment - use real data
            # Note: txn_metrics calculated below, so we use a placeholder here
            avg_transactions_placeholder = 0  # Will be replaced with real value
            
            # Calculate REAL transaction metrics for this cluster first
            txn_metrics_for_ranking = self._calculate_real_transaction_metrics(cluster_data)
            avg_transactions_for_ranking = txn_metrics_for_ranking['avg_transactions_per_customer']
            
            deposit_rank = sum(1 for s in all_segments if s['deposits'] < avg_deposits)
            digital_rank = sum(1 for s in all_segments if s['digital'] < avg_digital)
            products_rank = sum(1 for s in all_segments if s['products'] < avg_products)
            trans_rank = sum(1 for s in all_segments if s['transactions'] < avg_transactions_for_ranking)
            cross_rank = sum(1 for s in all_segments if s['cross_sell'] < avg_cross_sell)
            
            total_segs = len(all_segments)
            
            # Find PRIMARY differentiator (highest rank)
            rankings = {
                'deposits': (deposit_rank / total_segs * 100) if total_segs > 0 else 50,
                'digital': (digital_rank / total_segs * 100) if total_segs > 0 else 50,
                'products': (products_rank / total_segs * 100) if total_segs > 0 else 50,
                'transactions': (trans_rank / total_segs * 100) if total_segs > 0 else 50,
                'cross_sell': (cross_rank / total_segs * 100) if total_segs > 0 else 50
            }
            
            primary_trait = max(rankings, key=rankings.get)
            percentile = rankings[primary_trait]
            
            # ============================================================================
            # DYNAMIC SEGMENT NAMING - Generated from actual data characteristics
            # ============================================================================

            # Calculate REAL transaction metrics first (needed for naming)
            txn_metrics = self._calculate_real_transaction_metrics(cluster_data)
            avg_transactions_real = txn_metrics['monthly_transaction_rate']

            # Collect extra stats for richer LLM prompt
            avg_churn = float(cluster_data['churn_probability'].mean()) if 'churn_probability' in cluster_data.columns else 0.15
            dominant_goal = (cluster_data['financial_goal'].mode()[0]
                             if 'financial_goal' in cluster_data.columns and len(cluster_data['financial_goal'].mode()) > 0
                             else '')
            dominant_clv = (cluster_data['clv_tier'].mode()[0]
                            if 'clv_tier' in cluster_data.columns and len(cluster_data['clv_tier'].mode()) > 0
                            else 'Silver')
            extra_stats = {
                'avg_churn':       avg_churn,
                'dominant_goal':   dominant_goal,
                'dominant_clv_tier': dominant_clv,
                'dominant_risk':   dominant_risk,
            }

            # Add credit score to characteristics so LLM gets it
            characteristics['avg_credit_score'] = float(avg_credit_score)
            characteristics['avg_digital_engagement'] = float(avg_digital)

            # Pre-classify archetype type so the LLM gets a hard constraint, not just inspiration
            extra_stats['avg_transactions'] = avg_transactions_real
            archetype_type = self._classify_archetype(characteristics, extra_stats, assigned_archetype_types)
            assigned_archetype_types.add(archetype_type)
            extra_stats['archetype_type'] = archetype_type
            logger.info(f"  Cluster {cluster_id}: pre-classified as {archetype_type}")

            # Generate UNIQUE dynamic name + description in one LLM call
            persona_name, persona_description = self._generate_dynamic_segment_profile(
                characteristics,
                percentile,
                primary_trait,
                avg_transactions_real,
                cluster_id=cluster_id,
                used_names=list(used_names),
                extra_stats=extra_stats,
            )

            # Dynamic emoji based on primary trait
            emoji_map = {
                'deposits': '💰',
                'transactions': '⚡',
                'digital': '📱',
                'products': '🎁',
                'cross_sell': '🎯'
            }
            emoji = emoji_map.get(primary_trait, '👥')

            # STRICT VALIDATION: Names should NEVER collide
            if persona_name in used_names:
                logger.error(f"CRITICAL ERROR: Duplicate name '{persona_name}' detected!")
                raise ValueError(f"Segment naming logic failed - duplicate '{persona_name}' detected!")

            used_names.add(persona_name)
            logger.info(f"✓ Unique name generated: '{persona_name}'")

            # Generate short name
            short_name = ''.join([word[0].upper() for word in persona_name.split()[:3]])
            if not short_name:
                short_name = f"SEG{cluster_id}"

            # Use LLM-generated description (or rule-based fallback stored in characteristics)
            description = persona_description or characteristics.get('_segment_description', f"{persona_name} — {primary_trait.title()} segment")
            
            logger.info(f"✓ Cluster {cluster_id}: {persona_name} ({primary_trait} @ {percentile:.0f}th percentile)")
            
            # Store basic persona info first (explanations come later)
            characteristics['avg_monthly_transaction_volume'] = avg_transactions_real
            characteristics['monthly_transaction_volume'] = avg_transactions_real  # Add both keys
            characteristics['total_transactions'] = txn_metrics['total_transactions']
            
            segment_explanation = None  # Will be generated in second pass after all personas created
            
            # ============================================================================
            # DYNAMIC CALCULATIONS - Real transaction data & behavior-based intent
            # ============================================================================
            
            # Calculate DYNAMIC intent score (changes with gamma!)
            gamma = params.get('gamma', 0.75)
            dynamic_intent = self._calculate_dynamic_intent_score(cluster_data, gamma)
            
            logger.info(f"  📊 Metrics: {txn_metrics['total_transactions']:,} txns, intent={dynamic_intent:.1%}, name='{persona_name}'")
            
            personas[cluster_id] = {
                'emoji': emoji,
                'cluster_id': int(cluster_id),
                'persona_name': persona_name,
                'name': persona_name,  # Add both for compatibility
                'short_name': short_name,
                'description': description,
                'segment_name_source': characteristics.get('_segment_name_source', 'rule_based'),
                'size': int(size),
                'percentage': float(percentage),
                # Frontend expects these at root level - NOW FULLY DYNAMIC!
                'avg_annual_balance': float(avg_deposits),
                'avg_transactions': float(avg_transactions_real),  # REAL from transactions.csv
                'total_transactions': txn_metrics['total_transactions'],  # Total for segment
                'monthly_transaction_rate': txn_metrics['monthly_transaction_rate'],  # Monthly rate
                'avg_intent_score': float(dynamic_intent),  # DYNAMIC based on behavior + gamma
                'total_revenue': float(cluster_data['total_deposits'].sum()),
                'confidence_avg': 0.85,  # Default confidence score
                'characteristics': {
                    'avg_deposits': float(avg_deposits),
                    'avg_income': float(avg_income),
                    'avg_age': float(avg_age),  # Add age for insights
                    'avg_credit_score': float(avg_credit_score),
                    'avg_products': float(avg_products),
                    'avg_digital_engagement': float(avg_digital),
                    'avg_cross_sell_receptivity': float(avg_cross_sell),
                    'avg_monthly_transaction_volume': float(txn_metrics['monthly_transaction_rate']),  # From real data
                    'monthly_transaction_volume': float(txn_metrics['monthly_transaction_rate']),  # Add both keys for compatibility
                    'total_transactions': txn_metrics['total_transactions'],  # Total for this segment
                    'avg_transactions_per_customer': float(txn_metrics['avg_transactions_per_customer']),  # Per customer
                    'dominant_risk_tolerance': dominant_risk,
                    'dominant_channel': dominant_channel,
                    'dominant_life_stage': dominant_life_stage,
                    'archetype_type': archetype_type,
                },
                'revenue_metrics': {
                    'total_deposits': float(cluster_data['total_deposits'].sum()),
                    'total_revenue_12mo': float(cluster_data['total_deposits'].sum()),  # Simplified
                    'avg_customer_value': float(avg_deposits)
                },
                'special_flags': self._get_special_flags(cluster_data),
                'segment_explanation': segment_explanation  # CRITICAL: Add explanation!
            }
            
            # Enrich with image data if available (matching Academy Sports implementation)
            if IMAGE_MAPPER_AVAILABLE:
                try:
                    image_mapper = get_image_mapper()
                    image_data = image_mapper.get_macro_persona_image(
                        persona_name=persona_name,
                        characteristics=characteristics,
                        size=size,
                        avg_spend=avg_deposits,
                        used_images=used_images
                    )
                    personas[cluster_id].update({
                        'image_url': image_data['image_url'],
                        'image_fallback': image_data['image_fallback'],
                        'color_theme': image_data['color_theme'],
                        'visual_emoji': image_data['emoji']
                    })
                    logger.info(f"  ✓ Enriched with image: {image_data['image_url'][:50]}... and color {image_data['color_theme']}")
                except Exception as e:
                    logger.warning(f"Could not enrich persona with image data: {e}")
        
        # SECOND PASS: Generate explanations now that all personas exist
        # Explanations use peer percentiles across all segments; self.personas must be the
        # in-progress dict (execute() assigns self.personas only after this returns—was empty before).
        logger.info("🔍 Generating unique segment explanations...")
        self.personas = personas
        for cluster_id, persona in personas.items():
            try:
                # Ensure all needed data is in characteristics (per-persona values only)
                persona['characteristics']['avg_age'] = persona['characteristics'].get('avg_age', 45)
                persona['characteristics']['avg_income'] = persona['characteristics'].get('avg_income', 0)
                
                explanation = self._generate_segment_explanation(
                    persona_name=persona['persona_name'],
                    avg_deposits=persona['characteristics']['avg_deposits'],
                    avg_income=persona['characteristics']['avg_income'],
                    avg_digital=persona['characteristics']['avg_digital_engagement'],
                    avg_products=persona['characteristics']['avg_products'],
                    characteristics=persona['characteristics']
                )
                personas[cluster_id]['segment_explanation'] = explanation
                logger.info(f"  ✓ Generated explanation for {persona['persona_name']}")
            except Exception as e:
                logger.warning(f"Could not generate explanation for cluster {cluster_id}: {e}")
                personas[cluster_id]['segment_explanation'] = None
        
        return personas
    
    def _generate_segment_explanation(
        self,
        persona_name: str,
        avg_deposits: float,
        avg_income: float,
        avg_digital: float,
        avg_products: float,
        characteristics: Dict
    ) -> Dict:
        """Compact, unique segment insights: 3 key stats + 3 behaviors + 2 actions."""
        avg_transactions = characteristics.get('avg_monthly_transaction_volume', characteristics.get('monthly_transaction_volume', 0))
        avg_cross_sell = characteristics.get('avg_cross_sell_receptivity', 0)
        avg_credit = characteristics.get('avg_credit_score', 700)
        avg_age = characteristics.get('avg_age', 45)
        
        # Rank each metric against the GLOBAL customer population (all 5000 rows).
        # Previously ranked against only 5 segment averages — with all segments at ~15 txns,
        # one would be "Top 20%" and another "Bottom 20%" even though values were identical.
        _COL_MAP = {
            'avg_deposits':                   'total_deposits',
            'avg_digital_engagement':         'digital_engagement_score',
            'avg_products':                   'num_products',
            'avg_monthly_transaction_volume': 'monthly_transaction_volume',
            'avg_cross_sell_receptivity':     'cross_sell_receptivity',
            'avg_income':                     'income',
            'avg_credit_score':               'credit_score',
        }
        def _rank(val, key):
            col = _COL_MAP.get(key, key)
            if col in self.customers_df.columns:
                vals = self.customers_df[col].dropna().values
                if len(vals) > 0:
                    return float((vals < val).sum() / len(vals)) * 100
            # Fallback to peer-segment comparison only if column not found
            peer_vals = [p.get('characteristics', {}).get(key, 0) for p in self.personas.values()]
            return (sum(v < val for v in peer_vals) / len(peer_vals)) * 100 if peer_vals else 50

        dep_rank  = _rank(avg_deposits,     'avg_deposits')
        dig_rank  = _rank(avg_digital,      'avg_digital_engagement')
        prd_rank  = _rank(avg_products,     'avg_products')
        txn_rank  = _rank(avg_transactions, 'avg_monthly_transaction_volume')
        xsl_rank  = _rank(avg_cross_sell,   'avg_cross_sell_receptivity')
        inc_rank  = _rank(avg_income,       'avg_income')
        crd_rank  = _rank(avg_credit,       'avg_credit_score')

        rankings = {'deposits': dep_rank, 'digital': dig_rank, 'products': prd_rank,
                    'transactions': txn_rank, 'cross_sell': xsl_rank}
        sorted_traits   = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
        primary_trait   = sorted_traits[0][0]
        secondary_trait = sorted_traits[1][0] if len(sorted_traits) > 1 else 'digital'
        trait_combo     = f"{primary_trait}_{secondary_trait}"

        def _rank_label(r):
            if r >= 80: return 'Top 20%'
            if r >= 68: return 'Above avg'   # widened Avg band to 32-68 (±1σ convention)
            if r >= 32: return 'Avg'
            if r >= 20: return 'Below avg'
            return 'Bottom 20%'

        # ── KEY STATS — compact-formatted values so frontend never truncates ──
        def _fmt_usd(v):
            v = float(v or 0)
            if v >= 1_000_000: return f'${v/1_000_000:.1f}M'
            if v >= 1_000:     return f'${v/1_000:.0f}K'
            return f'${v:.0f}'

        # Avg Balance and Digital Engagement are already visible on the macro card — excluded here
        key_stats = [
            {'label': 'Avg Income',       'value': _fmt_usd(avg_income),      'note': _rank_label(inc_rank)},
            {'label': 'Avg Credit Score', 'value': f'{avg_credit:.0f}',       'note': _rank_label(crd_rank)},
            {'label': 'Avg Products',     'value': f'{avg_products:.1f}',     'note': _rank_label(prd_rank)},
            {'label': 'Monthly Txns',     'value': f'{avg_transactions:.0f}', 'note': _rank_label(txn_rank)},
        ]

        # ── KEY BEHAVIORS — keyed on archetype_type, not trait_combo ────────
        # trait_combo is unreliable: when all segments share similar txn counts,
        # the same combo can appear in multiple segments, producing copy-paste bullets.
        archetype_type = characteristics.get('archetype_type', '')
        archetype_behaviors = {
            'HIGH-VALUE': [
                f'High earners (avg ${avg_income:,.0f}/yr) with strong savings discipline',
                'Hold multiple Meridian products — deep, long-term relationship',
                'Low churn risk — financially secure and unlikely to leave',
            ],
            'EVERYDAY': [
                'Core everyday customers relying on checking, savings, and debit',
                'Steady transaction habits and value-conscious about fees',
                f'Middle-income earners (avg ${avg_income:,.0f}/yr) focused on daily financial needs',
            ],
            'DIGITAL-FIRST': [
                'Mobile-first customers who manage all banking through the app',
                'Frequent transactions and high engagement with digital features',
                'Early adopters — respond quickly to in-app offers and new features',
            ],
            'LOYAL-STABLE': [
                'Long-standing, loyal customers who have banked with Meridian for years',
                'Prefer in-branch banking and in-person relationship management',
                f'Stable savings (avg ${avg_deposits:,.0f}) with very low risk of leaving',
            ],
            'AT-RISK': [
                f'Financially stretched customers with avg income ${avg_income:,.0f}/yr and limited savings',
                'Higher likelihood of leaving — need proactive retention outreach',
                'Respond better to financial relief and support offers than upsell campaigns',
            ],
        }
        key_behaviors = list(archetype_behaviors.get(archetype_type, [
            f'Ranked highest in {primary_trait.replace("_", " ")} among all segments',
            f'Secondary strength: {secondary_trait.replace("_", " ")}',
            f'Avg age {avg_age:.0f}, {_fmt_usd(avg_income)} income',
        ]))
        # Replace bullet 2 with the most genuinely distinctive metric for this segment.
        # Digital engagement is intentionally excluded — it is similar across all segments
        # (~50%) and mentioning it as a differentiator misleads the reader.
        distinctive_note = None
        if inc_rank >= 80:
            distinctive_note = f'Top earners — {_fmt_usd(avg_income)} avg income, credit score {avg_credit:.0f}'
        elif inc_rank <= 20:
            distinctive_note = f'Value-focused — {_fmt_usd(avg_income)} avg income, credit score {avg_credit:.0f}'
        elif txn_rank >= 80:
            distinctive_note = f'{avg_transactions:.0f} monthly transactions — top 20% activity level'
        elif txn_rank <= 20:
            distinctive_note = f'{avg_transactions:.0f} monthly transactions — bottom 20% activity level'
        elif prd_rank >= 80:
            distinctive_note = f'{avg_products:.1f} products held — above avg in portfolio depth'
        elif prd_rank <= 20:
            distinctive_note = f'{avg_products:.1f} products held — below avg in portfolio depth'
        elif xsl_rank >= 80:
            distinctive_note = f'{avg_cross_sell*100:.0f}% cross-sell receptivity — top 20% growth signal'
        elif crd_rank <= 20:
            distinctive_note = f'Avg credit score {avg_credit:.0f} — below avg in creditworthiness'
        if distinctive_note and len(key_behaviors) >= 3:
            key_behaviors[2] = distinctive_note

        # ── MARKETING ACTIONS — keyed on archetype_type ──────────────────────
        archetype_actions = {
            'HIGH-VALUE': [
                'Proactive wealth advisory and investment discovery calls',
                'Personalized premium-product campaign by income tier',
            ],
            'EVERYDAY': [
                'Fee waiver and cashback offer for consistent everyday use',
                'Bundle offer: add one complementary product at no annual fee',
            ],
            'DIGITAL-FIRST': [
                'In-app pre-approved offer with one-tap application',
                'Gamified cashback campaign tied to transaction milestones',
            ],
            'LOYAL-STABLE': [
                'Branch-based relationship manager outreach for premium products',
                'Loyalty recognition: preferred rates for long-standing customers',
            ],
            'AT-RISK': [
                'Proactive retention call with financial health check offer',
                'Trigger-based relief offer at overdraft or missed payment event',
            ],
        }
        marketing_recommendations = archetype_actions.get(archetype_type, [
            f'Campaign leading with {primary_trait.replace("_", " ")} benefit',
            'Test one targeted offer via preferred channel',
        ])

        # Tagline templates — {dep}, {dig}, {prd}, {txn}, {xsl} are substituted with
        # this segment's actual metric values so two segments with the same trait_combo
        # always produce different taglines.
        tagline_templates = {
            'deposits_digital':       '${dep:,.0f} avg balance, {dig:.0f}% digital — high-wealth customers who bank online',
            'deposits_products':      '${dep:,.0f} avg balance with {prd:.1f} products — wealth paired with deep product relationships',
            'deposits_transactions':  '${dep:,.0f} avg balance, {txn:.0f} monthly transactions — cash-flow-active wealth holders',
            'deposits_cross_sell':    '${dep:,.0f} avg balance, {xsl:.0f}% growth receptivity — affluent customers ready to expand',
            'digital_deposits':       '{dig:.0f}% digital engagement, ${dep:,.0f} balance — tech-forward customers with financial standing',
            'digital_products':       '{dig:.0f}% digital, {prd:.1f} products — customers who run their financial life through the app',
            'digital_transactions':   '{dig:.0f}% digital, {txn:.0f} monthly transactions — app-first customers with high activity',
            'digital_cross_sell':     '{dig:.0f}% digital, {xsl:.0f}% growth receptivity — online-active customers open to new products',
            'products_deposits':      '{prd:.1f} products held, ${dep:,.0f} balance — multi-product customers with stable wealth',
            'products_digital':       '{prd:.1f} products, {dig:.0f}% digital — broad-portfolio customers who self-serve online',
            'products_transactions':  '{prd:.1f} products, {txn:.0f} monthly transactions — power users active across every account',
            'products_cross_sell':    '{prd:.1f} products, {xsl:.0f}% growth receptivity — multi-product customers looking for the next add',
            'transactions_deposits':  '{txn:.0f} monthly transactions, ${dep:,.0f} balance — frequent transactors with significant wealth',
            'transactions_digital':   '{txn:.0f} monthly transactions, {dig:.0f}% digital — high-cadence mobile-native bankers',
            'transactions_products':  '{txn:.0f} monthly transactions, {prd:.1f} products — active across every product they hold',
            'transactions_cross_sell':'{txn:.0f} monthly transactions, {xsl:.0f}% growth receptivity — active bankers who act on the right offer',
            'cross_sell_deposits':    '{xsl:.0f}% growth receptivity, ${dep:,.0f} balance — affluent customers ready to be asked',
            'cross_sell_digital':     '{xsl:.0f}% growth receptivity, {dig:.0f}% digital — open to offers and easy to reach online',
            'cross_sell_products':    '{xsl:.0f}% growth receptivity, {prd:.1f} products — multi-product holders actively seeking more',
            'cross_sell_transactions':'{xsl:.0f}% growth receptivity, {txn:.0f} transactions — frequent transactors who respond to timely offers',
        }
        template = tagline_templates.get(
            trait_combo,
            f'Defined by {primary_trait.replace("_", " ")} (${avg_deposits:,.0f} balance, {avg_digital*100:.0f}% digital, {avg_products:.1f} products)',
        )
        tagline = template.format(
            dep=avg_deposits, dig=avg_digital * 100, prd=avg_products,
            txn=avg_transactions, xsl=avg_cross_sell * 100, inc=avg_income,
        )

        # Pull LLM-generated description stored during naming pass
        description = characteristics.get('_segment_description', '')

        return {
            'description': description,
            'tagline': tagline,
            'key_stats': key_stats,
            'key_behaviors': key_behaviors,
            'marketing_recommendations': marketing_recommendations,
        }
    
    def _generate_macro_name_explanation(
        self,
        persona_name: str,
        avg_deposits: float,
        avg_digital: float,
        avg_products: float,
        avg_transactions: float,
        primary_trait: str,
        primary_rank: float
    ) -> str:
        """
        Generate SHORT, UNIQUE explanation focused on the SPECIFIC segment name
        1 sentence maximum - explains what the name means for THIS segment
        """
        
        # Extract key name components
        name_lower = persona_name.lower()
        
        # Pattern matching for common name types
        
        # ELITE/PREMIUM patterns
        if 'elite' in name_lower or 'premium' in name_lower:
            if 'saver' in name_lower:
                return f"'{persona_name}' reflects top-tier wealth (${avg_deposits/1000000:.1f}M deposits) combined with long-term savings focus."
            elif 'digital' in name_lower:
                return f"'{persona_name}' combines exceptional wealth (${avg_deposits/1000000:.1f}M) with {avg_digital*100:.0f}% digital adoption—our most tech-savvy affluent customers."
            else:
                return f"'{persona_name}' designates our wealthiest tier with ${avg_deposits/1000000:.1f}M average deposits, representing top {100-primary_rank:.0f}% of customers."
        
        # TRADITIONAL/ESTABLISHED patterns
        elif 'traditional' in name_lower or 'established' in name_lower:
            if 'member' in name_lower:
                return f"'{persona_name}' captures loyal, established customers with ${avg_deposits/1000000:.1f}M deposits who prefer traditional banking relationships."
            else:
                return f"'{persona_name}' reflects steady, conventional banking approach with ${avg_deposits:,.0f} deposits and {avg_products:.0f} core products."
        
        # DIGITAL/TECH patterns
        elif 'digital' in name_lower or 'tech' in name_lower or 'mobile' in name_lower or 'app' in name_lower:
            if 'native' in name_lower:
                return f"'{persona_name}' identifies mobile-first customers with {avg_digital*100:.0f}% digital usage, rarely visiting branches."
            elif 'adopter' in name_lower or 'first' in name_lower:
                return f"'{persona_name}' highlights {avg_digital*100:.0f}% online banking adoption—tech-comfortable customers who embrace digital tools."
            else:
                return f"'{persona_name}' captures {avg_digital*100:.0f}% digital engagement, representing our most technology-forward segment."
        
        # ACTIVE/ENGAGED patterns
        elif 'active' in name_lower or 'engaged' in name_lower or 'frequent' in name_lower:
            if 'earner' in name_lower:
                return f"'{persona_name}' describes high-activity customers with {avg_transactions:.0f} monthly banking events and ${avg_deposits:,.0f} actively managed funds."
            else:
                return f"'{persona_name}' reflects {avg_transactions:.0f} monthly banking events—highly engaged customers who interact frequently."
        
        # COMMUNITY/FAMILY patterns
        elif 'community' in name_lower or 'family' in name_lower or 'household' in name_lower:
            return f"'{persona_name}' represents ultra-high-net-worth customers (${avg_deposits/1000000:.1f}M) with strong local ties and family banking relationships."
        
        # GROWTH/RISING patterns
        elif 'growth' in name_lower or 'rising' in name_lower or 'aspiring' in name_lower:
            return f"'{persona_name}' identifies upwardly mobile customers with ${avg_deposits:,.0f} deposits and growing product portfolios ({avg_products:.1f} products)."
        
        # CORE/MASS patterns
        elif 'core' in name_lower or 'mass' in name_lower or 'steady' in name_lower:
            return f"'{persona_name}' captures our mainstream banking segment with ${avg_deposits:,.0f} deposits, representing typical retail customers."
        
        # SAVER patterns (general)
        elif 'saver' in name_lower:
            if avg_deposits > 1000000:
                return f"'{persona_name}' emphasizes wealth accumulation with ${avg_deposits/1000000:.1f}M in deposits—serious savers building long-term financial security."
            else:
                return f"'{persona_name}' highlights savings-focused behavior with ${avg_deposits:,.0f} deposits, prioritizing financial stability."
        
        # MEMBER patterns (general)
        elif 'member' in name_lower:
            return f"'{persona_name}' denotes established loyalty with ${avg_deposits/1000000:.1f}M deposits and {avg_products:.0f}-product relationships spanning multiple years."
        
        # EARNER patterns (general)
        elif 'earner' in name_lower:
            return f"'{persona_name}' characterizes active income generators with ${avg_deposits:,.0f} deposits and {avg_transactions:.0f} monthly banking events."
        
        # FALLBACK: Use primary trait
        else:
            if primary_trait == 'deposits':
                return f"'{persona_name}' defined by ${avg_deposits:,.0f} average deposits, ranking {primary_rank:.0f}th percentile in wealth."
            elif primary_trait == 'digital':
                return f"'{persona_name}' characterized by {avg_digital*100:.0f}% digital engagement—above {primary_rank:.0f}% of customers."
            elif primary_trait == 'products':
                return f"'{persona_name}' reflects {avg_products:.1f} products held, indicating {primary_rank:.0f}th percentile portfolio depth."
            elif primary_trait == 'transactions':
                return f"'{persona_name}' captures {avg_transactions:.0f} monthly banking events, ranking {primary_rank:.0f}th percentile in activity."
            else:
                return f"'{persona_name}' identifies customers with {primary_rank:.0f}th percentile cross-sell receptivity and growth potential."
    
    def _get_special_flags(self, cluster_data):
        """Identify special characteristics of a cluster"""
        flags = []
        
        avg_deposits = cluster_data['total_deposits'].mean()
        avg_digital = cluster_data['digital_engagement_score'].mean()
        avg_products = cluster_data['num_products'].mean()
        avg_cross_sell = cluster_data['cross_sell_receptivity'].mean()
        
        if avg_deposits > 200000:
            flags.append('high_value')
        if avg_digital > 0.8:
            flags.append('digital_first')
        if avg_products >= 5:
            flags.append('multi_product')
        if avg_cross_sell > 0.7:
            flags.append('cross_sell_ready')
        if cluster_data['credit_score'].mean() > 750:
            flags.append('excellent_credit')
        
        return flags
    
    def _validate_business_constraints(self, min_cluster_size_pct=10, min_deposits_per_customer=5000):
        """Validate that clusters meet banking business constraints"""
        validation = {
            'all_constraints_met': True,
            'constraints_met_count': 0,
            'constraints_failed_count': 0,
            'cluster_validations': {}
        }
        
        total_customers = len(self.customers_df)
        min_size = int(total_customers * (min_cluster_size_pct / 100))
        
        for cluster_id in sorted(self.customers_df['cluster'].unique()):
            cluster_data = self.customers_df[self.customers_df['cluster'] == cluster_id]
            cluster_size = len(cluster_data)
            avg_deposits = cluster_data['total_deposits'].mean()
            
            size_met = cluster_size >= min_size
            deposits_met = avg_deposits >= min_deposits_per_customer
            
            all_met = size_met and deposits_met
            
            validation['cluster_validations'][int(cluster_id)] = {
                'size': int(cluster_size),
                'size_constraint_met': size_met,
                'avg_deposits': float(avg_deposits),
                'deposits_constraint_met': deposits_met,
                'all_constraints_met': all_met
            }
            
            if all_met:
                validation['constraints_met_count'] += 1
            else:
                validation['constraints_failed_count'] += 1
                validation['all_constraints_met'] = False
        
        return validation
    
    def get_all_customers(self, skip=0, limit=50, persona_filter=None, search_query=None, cluster_id=None):
        """Get paginated list of customers with persona assignments.
        If cluster_id is set, only customers in that segment (matches personas / Agent A cluster).
        Loads CSV via load_data() if execute() has not been run yet (dropdowns work before Agent A)."""
        if self.customers_df is None:
            if not self.load_data():
                raise ValueError(
                    "Banking dataset not found. Add data/preloaded/jpm_bank/ CSVs or run Agent A."
                )
        df = self.customers_df.copy()
        if "cluster" not in df.columns:
            df["cluster"] = 0
        else:
            df["cluster"] = pd.to_numeric(df["cluster"], errors="coerce").fillna(0)
        
        # Apply filters
        if cluster_id is not None and str(cluster_id).strip() != "":
            try:
                cid = int(float(cluster_id))
                cnum = pd.to_numeric(df["cluster"], errors="coerce")
                mask = cnum == cid
                if not mask.any():
                    mask = df["cluster"].astype(str).str.strip() == str(cid)
                df = df[mask]
            except (TypeError, ValueError, KeyError):
                pass
        elif persona_filter:
            # Map persona short name to cluster ID
            cluster_ids = [cid for cid, p in self.personas.items() if p['short_name'] == persona_filter]
            if cluster_ids:
                df = df[df['cluster'].isin(cluster_ids)]
        
        if search_query:
            df = df[df['customer_name'].str.contains(search_query, case=False, na=False)]
        
        # Pagination
        total = len(df)
        df_page = df.iloc[skip:skip+limit]
        
        # Prepare response
        customers = []
        for _, row in df_page.iterrows():
            try:
                cid = int(float(row["cluster"]))
            except (TypeError, ValueError):
                cid = 0
            persona = self.personas.get(cid, {})
            if not persona and self.personas:
                for k, p in self.personas.items():
                    try:
                        if int(float(k)) == cid:
                            persona = p
                            break
                    except (TypeError, ValueError):
                        continue
            
            def _s(v, d=''):
                if v is None:
                    return d
                import math as _m
                try:
                    if isinstance(v, float) and _m.isnan(v):
                        return d
                except Exception:
                    pass
                return str(v).strip() or d

            customers.append({
                'customer_id': row['customer_id'],
                'customer_name': row.get('customer_name', row['customer_id']),
                'persona': persona.get('persona_name', 'All customers' if cid == 0 and not self.personas else 'Unknown'),
                'persona_short': persona.get('short_name', '—'),
                'cluster_id': cid,
                'total_deposits': float(row.get('total_deposits', 0) or 0),
                'num_products': int(float(row.get('num_products', 0) or 0)),
                'digital_engagement': float(row.get('digital_engagement_score', 0.5) or 0),
                'channel_preference': _s(row.get('channel_preference'), 'Hybrid'),
                'recent_life_event': _s(row.get('recent_life_event'), ''),
            })
        
        return {
            'customers': customers,
            'total': total,
            'skip': skip,
            'limit': limit,
            'has_more': (skip + limit) < total
        }
    
    def get_customer_details(self, customer_id: str):
        """Get detailed information for a specific customer"""
        if self.customers_df is None:
            raise ValueError("No customer data loaded")
        
        customer = self.customers_df[self.customers_df['customer_id'] == customer_id]
        if len(customer) == 0:
            raise ValueError(f"Customer {customer_id} not found")
        
        customer = customer.iloc[0]

        # 'cluster' is added in-memory when Agent A runs segmentation.
        # The API endpoint rebuilds it from agent_a_results before calling here,
        # but guard defensively in case it's still missing.
        if 'cluster' in customer.index:
            cluster_id = int(customer['cluster'])
        else:
            cluster_id = 0

        persona = self.personas.get(cluster_id, {})
        
        def _safe_str(val, default=''):
            if val is None:
                return default
            import math
            try:
                if isinstance(val, float) and math.isnan(val):
                    return default
            except Exception:
                pass
            return str(val).strip() or default

        def _safe_float(val, default=0.0):
            try:
                return float(val) if val is not None else default
            except (TypeError, ValueError):
                return default

        return {
            'customer_id': customer_id,
            'customer_name': customer['customer_name'],
            'persona': persona.get('persona_name', 'Unknown'),
            'cluster_id': int(cluster_id),
            'metrics': {
                'total_deposits': _safe_float(customer.get('total_deposits'), 10000.0),
                'income': _safe_float(customer.get('income'), 50000.0),
                'credit_score': _safe_float(customer.get('credit_score'), 700.0),
                'num_products': int(_safe_float(customer.get('num_products'), 1)),
                'digital_engagement': _safe_float(customer.get('digital_engagement_score'), 0.5),
                'digital_engagement_score': _safe_float(customer.get('digital_engagement_score'), 0.5),
                'cross_sell_receptivity': _safe_float(customer.get('cross_sell_receptivity'), 0.5),
                # Channel & life event signals
                'channel_preference': _safe_str(customer.get('channel_preference'), 'Hybrid'),
                'recent_life_event': _safe_str(customer.get('recent_life_event'), ''),
                # Financial profile
                'age': _safe_float(customer.get('age'), 40.0),
                'life_stage': _safe_str(customer.get('life_stage'), ''),
                'credit_tier': _safe_str(customer.get('credit_tier'), ''),
                'fee_sensitivity_tier': _safe_str(customer.get('fee_sensitivity_tier'), ''),
                'monthly_spend_in_primary_cat': _safe_float(customer.get('monthly_spend_in_primary_cat'), 300.0),
                'outstanding_debt_total': _safe_float(customer.get('outstanding_debt_total'), 0.0),
                'financial_goal': _safe_str(customer.get('financial_goal'), ''),
                'home_ownership_type': _safe_str(customer.get('home_ownership_type') or customer.get('home_ownership'), ''),
                'months_since_relationship_started': _safe_float(customer.get('months_since_relationship_started'), 12.0),
                'travel_frequency': _safe_str(customer.get('travel_frequency'), 'none'),
                'primary_spending_category': _safe_str(customer.get('primary_spending_category'), ''),
                'nps_score': _safe_float(customer.get('nps_score'), 7.0),
                'has_competitor_credit_card': bool(customer.get('has_competitor_credit_card', False)),
            }
        }
    
    def get_customer_recommendations(self, customer_id: str, agent_b=None):
        """Get product recommendations for a customer (requires Agent B)"""
        if agent_b is None:
            return {'error': 'Agent B required for recommendations'}
        
        # Delegate to Agent B
        return agent_b.get_similar_products(customer_id, n_recommendations=5)


if __name__ == "__main__":
    # Test the agent
    agent = AgentA_Banking_Enhanced()
    result = agent.execute({'n_clusters': 5})
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Clustering successful!")
        print(f"   Personas: {len(result['personas'])}")
        for persona_id, persona in result['personas'].items():
            print(f"   - {persona['persona_name']}: {persona['size']} customers")

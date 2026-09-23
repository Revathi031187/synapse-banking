"""
Agent A Micro - Banking Micro Segmentation
Creates sub-segments within each macro persona based on:
- Digital engagement level
- Product portfolio depth
- Credit utilization
- Transaction velocity
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import sys
import os

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

# ── Per-macro feature sets ────────────────────────────────────────────────────
# Each macro segment type uses 3 features most relevant to its defining trait.
# Customers within a macro are split along THESE dimensions  -  different macros
# split along different axes, so micro sub-groups are meaningfully distinct.
_MICRO_FEATURE_SETS = {
    'deposits':     ['account_maturity', 'portfolio_depth', 'digital_engagement'],
    'digital':      ['transaction_velocity', 'portfolio_depth', 'cross_sell_receptivity'],
    'products':     ['account_maturity', 'transaction_velocity', 'digital_engagement'],
    'transactions': ['account_maturity', 'digital_engagement', 'cross_sell_receptivity'],
    'cross_sell':   ['account_maturity', 'portfolio_depth', 'transaction_velocity'],
    'income':       ['portfolio_depth', 'digital_engagement', 'credit_utilization'],
}

# Human-readable labels used in LLM prompts
_FEATURE_LABELS = {
    'account_maturity':       'account tenure',
    'portfolio_depth':        'product breadth',
    'credit_utilization':     'credit usage',
    'transaction_velocity':   'transaction activity',
    'digital_engagement':     'digital adoption',
    'cross_sell_receptivity': 'openness to new products',
}

# Micro segment rule-based naming ─────────────────────────────────────────────
# Short name appended after the descriptor word: e.g. "Digital Retiree"
_PARENT_SHORT_NAMES = {
    'Wealth Builder':     'Builder',
    'Everyday Essential': 'Essential',
    'Digital Native':     'Native',
    'Retiree Anchor':     'Retiree',
    'At-Risk Borrower':   'Borrower',
}

# Maps (feature_name, direction) → plain-English descriptor word
_FEATURE_DIRECTION_WORDS = {
    ('account_maturity',      'High'): 'Established',
    ('account_maturity',      'Low'):  'New',
    ('portfolio_depth',       'High'): 'Multi-Product',
    ('portfolio_depth',       'Low'):  'Focused',
    ('digital_engagement',    'High'): 'Digital',
    ('digital_engagement',    'Low'):  'Branch',
    ('transaction_velocity',  'High'): 'Active',
    ('transaction_velocity',  'Low'):  'Occasional',
    ('cross_sell_receptivity','High'): 'Growth-Ready',
    ('cross_sell_receptivity','Low'):  'Anchored',
    ('credit_utilization',    'High'): 'Credit-Active',
    ('credit_utilization',    'Low'):  'Credit-Light',
}

# Feature priority: most meaningful differentiator first
_NAMING_PRIORITY = [
    'digital_engagement', 'account_maturity', 'transaction_velocity',
    'portfolio_depth', 'cross_sell_receptivity', 'credit_utilization',
]


def _build_micro_name(feature_profile, split_features, parent_short, used_adjectives):
    """
    Build a plain '[Adjective] [Parent Short Name]' micro segment name.
    Picks the highest-priority non-Mid feature direction, avoiding already-used adjectives.
    """
    candidates = []
    for feat in _NAMING_PRIORITY:
        if feat in split_features and feat in feature_profile:
            direction = feature_profile.get(feat, 'Mid')
            if direction == 'Mid':
                continue
            word = _FEATURE_DIRECTION_WORDS.get((feat, direction))
            if word:
                candidates.append(word)

    for adj in candidates:
        if adj not in used_adjectives:
            return f"{adj} {parent_short}"
    # All preferred adjectives taken  -  use first candidate anyway to avoid "Core X"
    if candidates:
        return f"{candidates[0]} {parent_short}"
    return f"Core {parent_short}"

# Rule-based fallback name pools keyed by macro primary trait.
# Names are plain 2-word archetypes a non-banker immediately understands.
# 8 entries per pool so 4 micro segments across 2 same-trait macros never collide.
_MICRO_FALLBACK_POOLS = {
    'deposits': [
        'Loyal Saver', 'New Wealth', 'Debt-Free Holder', 'Growing Saver',
        'Low-Risk Saver', 'Active Depositor', 'Steady Holder', 'Cautious Saver',
    ],
    'digital': [
        'Mobile First', 'Casual Digital', 'App Explorer', 'Digital Starter',
        'Screen Saver', 'Digital Minimalist', 'Connected Banker', 'Light Digital',
    ],
    'products': [
        'Full Bundle', 'Bundle Starter', 'Core Holder', 'Wide Portfolio',
        'Focused Products', 'Growing Bundler', 'Deep Holder', 'Selective User',
    ],
    'transactions': [
        'Daily Spender', 'Weekend Payer', 'Steady Sender', 'Frequent Buyer',
        'Light Transactor', 'Regular Mover', 'Active Payer', 'Batch Sender',
    ],
    'cross_sell': [
        'Ready Adopter', 'Curious Saver', 'Early Mover', 'Steady Climber',
        'Growth Starter', 'Open Mover', 'Next-Step Ready', 'Careful Grower',
    ],
    'income': [
        'High Earner', 'Budget Wise', 'Growing Earner', 'Careful Spender',
        'Active Earner', 'Conservative Earner', 'Balanced Earner', 'Passive Saver',
    ],
}


class AgentA_Banking_Micro:
    """
    Micro Segmentation Agent for Banking
    
    Creates 3-4 sub-segments within each macro persona to enable
    more granular personalization and targeted financial services
    """
    
    def __init__(self, customers_df: pd.DataFrame, macro_personas: Dict, global_used_names=None):
        """
        Initialize Micro Segmentation Agent

        global_used_names: set/list of names already used across all prior micro segment
        runs in this session  -  prevents cross-macro name collisions.
        """
        self.customers_df = customers_df
        self.macro_personas = macro_personas
        self.micro_segments = {}
        self._global_used_names: set = set(global_used_names or [])

        logger.info(f"Micro Segmentation Agent initialized with {len(customers_df)} customers, "
                    f"{len(self._global_used_names)} globally reserved names")
    
    def _get_primary_trait_from_persona(self, macro_persona: dict) -> str:
        """Derive the primary differentiating trait from a macro persona dict."""
        chars = macro_persona.get('characteristics', {})
        stored = chars.get('_primary_trait', '') or chars.get('primary_trait', '')
        if stored and stored in _MICRO_FEATURE_SETS:
            return stored

        avg_deposits   = float(chars.get('avg_deposits', 0) or 0)
        avg_digital    = float(chars.get('avg_digital_engagement', 0) or 0)
        avg_products   = float(chars.get('avg_products', 0) or chars.get('avg_num_products', 0) or 0)
        avg_txn        = float(chars.get('avg_transactions_per_customer', 0) or chars.get('avg_monthly_transactions', 0) or 0)
        avg_cross_sell = float(chars.get('avg_cross_sell_receptivity', 0) or 0)
        avg_income     = float(chars.get('avg_income', 0) or 0)

        scores = {
            'deposits':     avg_deposits / 50000,
            'digital':      avg_digital / 0.5,
            'products':     avg_products / 3.0,
            'transactions': avg_txn / 20.0,
            'cross_sell':   avg_cross_sell / 0.5,
            'income':       avg_income / 60000,
        }
        return max(scores, key=scores.get)

    def execute(self, macro_segment_id: int, n_micro_segments: int = 4) -> Dict:
        """
        Execute micro segmentation for a specific macro segment
        
        Args:
            macro_segment_id: ID of the macro segment to sub-segment
            n_micro_segments: Number of micro segments to create (default 4)
            
        Returns:
            Dictionary with micro segment definitions and customer assignments
        """
        try:
            # Get customers in this macro segment
            macro_customers = self.customers_df[
                self.customers_df['cluster'] == macro_segment_id
            ].copy()
            
            if len(macro_customers) < n_micro_segments * 2:
                logger.warning(f"Macro segment {macro_segment_id} has too few customers for {n_micro_segments} micro segments")
                n_micro_segments = max(2, len(macro_customers) // 5)
            
            logger.info(f"Creating {n_micro_segments} micro segments for macro segment {macro_segment_id} ({len(macro_customers)} customers)")
            
            # Calculate micro segmentation features (all 6 computed, subset selected below)
            features_df = self._calculate_micro_features(macro_customers)

            # Resolve macro persona  -  needed to determine which features to split on
            macro_persona = None
            for key in [macro_segment_id, str(macro_segment_id), int(macro_segment_id)]:
                if key in self.macro_personas:
                    macro_persona = self.macro_personas[key]
                    break

            if not macro_persona:
                raise KeyError(f"Macro segment {macro_segment_id} not found in personas. Available: {list(self.macro_personas.keys())}")

            macro_name = macro_persona['persona_name']

            # Select features most relevant to THIS macro segment's defining trait
            primary_trait = self._get_primary_trait_from_persona(macro_persona)
            selected_features = list(_MICRO_FEATURE_SETS.get(primary_trait, _MICRO_FEATURE_SETS['deposits']))
            logger.info(f"Macro '{macro_name}' trait='{primary_trait}' → micro features: {selected_features}")

            # Perform K-Means clustering on the selected features only
            micro_assignments = self._cluster_micro_segments(
                features_df,
                n_micro_segments,
                feature_names=selected_features,
            )

            # Add micro segment assignments
            macro_customers['micro_segment'] = micro_assignments

            micro_segments = self._generate_micro_profiles(
                macro_customers,
                macro_segment_id,
                n_micro_segments,
                macro_name,
                primary_trait=primary_trait,
                selected_features=selected_features,
            )
            
            # Store results
            self.micro_segments[macro_segment_id] = {
                'macro_segment_id': macro_segment_id,
                'macro_segment_name': macro_persona['persona_name'],
                'n_micro_segments': n_micro_segments,
                'micro_segments': micro_segments,
                'customer_assignments': macro_customers[['customer_id', 'micro_segment']].to_dict('records')
            }
            
            # Convert micro_segments dict to list for frontend compatibility
            micro_segments_list = []
            for seg_id, seg_data in micro_segments.items():
                # Map backend fields to frontend expectations
                avg_value = seg_data.get('revenue_metrics', {}).get('avg_customer_value', 0.0)
                frontend_seg = {
                    'micro_cluster_id': seg_data.get('micro_segment_id', int(seg_id)),
                    'name': seg_data.get('segment_name', f'Segment {seg_id}'),
                    'size': seg_data.get('size', 0),
                    'percentage': seg_data.get('percentage', 0.0),
                    'avg_spend': avg_value,
                    'avg_annual_balance': avg_value,  # Frontend expects this
                    'ltv_tier': seg_data.get('ltv_tier', 'Bronze'),
                    'characteristics': seg_data.get('characteristics', {}),
                    'revenue_metrics': seg_data.get('revenue_metrics', {}),
                    'top_customers': seg_data.get('top_customers', []),
                    'segment_explanation': seg_data.get('segment_explanation', None)
                }
                micro_segments_list.append(frontend_seg)
            
            # Use the same macro_persona we already found
            return {
                'status': 'success',
                'macro_segment_id': macro_segment_id,
                'macro_segment_name': macro_persona['persona_name'],  # Use the already-found persona
                'n_micro_segments': n_micro_segments,
                'micro_segments': micro_segments_list,
                'total_customers': len(macro_customers)
            }
            
        except Exception as e:
            logger.error(f"Error in micro segmentation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e), 'macro_segment_id': macro_segment_id}
    
    def _calculate_micro_features(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate features for micro segmentation - Banking specific
        
        Features:
        - digital_engagement: Online/mobile banking usage
        - portfolio_depth: Number of products held
        - credit_utilization: How much credit they use
        - transaction_velocity: How often they transact
        
        Args:
            customers_df: Customer data
            
        Returns:
            DataFrame with calculated features
        """
        features = pd.DataFrame(index=customers_df.index)
        
        # 1. Digital Engagement Score
        if 'digital_engagement_score' in customers_df.columns:
            features['digital_engagement'] = customers_df['digital_engagement_score']
        else:
            features['digital_engagement'] = 0.5
        
        # 2. Portfolio Depth (normalized)
        if 'num_products' in customers_df.columns:
            max_products = customers_df['num_products'].max()
            features['portfolio_depth'] = customers_df['num_products'] / (max_products + 1)
        else:
            features['portfolio_depth'] = 0.3
        
        # 3. Credit Utilization  
        if 'credit_utilization_ratio' in customers_df.columns:
            features['credit_utilization'] = customers_df['credit_utilization_ratio']
        else:
            features['credit_utilization'] = 0.3
        
        # 4. Transaction Velocity (normalized transaction count)
        if 'transaction_volume_30d' in customers_df.columns:
            trans_vol = customers_df['transaction_volume_30d']
            features['transaction_velocity'] = (trans_vol - trans_vol.min()) / (trans_vol.max() - trans_vol.min() + 1e-6)
        else:
            features['transaction_velocity'] = 0.5
        
        # 5. Account Age (tenure normalized)
        tenure_col = 'months_since_relationship_started' if 'months_since_relationship_started' in customers_df.columns else 'tenure_months'
        if tenure_col in customers_df.columns:
            tenure = customers_df[tenure_col]
            features['account_maturity'] = (tenure - tenure.min()) / (tenure.max() - tenure.min() + 1e-6)
        else:
            features['account_maturity'] = 0.5
        
        # 6. Cross-sell receptivity
        if 'cross_sell_receptivity' in customers_df.columns:
            features['cross_sell_receptivity'] = customers_df['cross_sell_receptivity']
        else:
            features['cross_sell_receptivity'] = 0.5
        
        return features
    
    def _cluster_micro_segments(
        self,
        features_df: pd.DataFrame,
        n_clusters: int,
        feature_names: list = None,
    ) -> np.ndarray:
        """
        Perform K-Means clustering on a specific subset of micro features.

        feature_names selects which columns to cluster on.  After fitting,
        self._last_cluster_feature_profiles stores a High/Mid/Low profile
        per cluster per feature  -  used downstream to generate meaningful names.
        """
        all_features = [
            'digital_engagement', 'portfolio_depth', 'credit_utilization',
            'transaction_velocity', 'account_maturity', 'cross_sell_receptivity',
        ]
        if feature_names is None:
            feature_names = all_features

        X_raw = features_df[feature_names].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_raw)

        kmeans = KMeans(
            n_clusters=n_clusters,
            init='k-means++',
            n_init=10,
            max_iter=300,
            random_state=42,
        )
        clusters = kmeans.fit_predict(X_scaled)

        # Store raw (unscaled) cluster means so naming code can label High/Mid/Low
        self._last_cluster_feature_profiles: dict = {}
        global_mean = X_raw.mean(axis=0)
        global_std  = X_raw.std(axis=0) + 1e-8
        for cid in range(n_clusters):
            mask = clusters == cid
            if mask.any():
                cluster_mean = X_raw[mask].mean(axis=0)
                profile = {}
                for i, feat in enumerate(feature_names):
                    z = (cluster_mean[i] - global_mean[i]) / global_std[i]
                    profile[feat] = 'High' if z > 0.25 else 'Low' if z < -0.25 else 'Mid'
                self._last_cluster_feature_profiles[cid] = profile

        logger.info(f"K-Means complete (inertia {kmeans.inertia_:.1f}), features={feature_names}")
        return clusters
    
    def _generate_micro_profiles(
        self,
        customers_df: pd.DataFrame,
        macro_segment_id: int,
        n_micro_segments: int,
        macro_name: str = "",
        primary_trait: str = "deposits",
        selected_features: list = None,
    ) -> Dict:
        """
        Generate profiles for each micro segment - Banking specific
        
        Args:
            customers_df: Customer data with micro segment assignments
            macro_segment_id: Parent macro segment ID
            n_micro_segments: Number of micro segments
            macro_name: Name of parent macro segment for unique naming
            
        Returns:
            Dictionary of micro segment profiles
        """
        micro_segments = {}
        # Seed with globally reserved names so no two micro segments across any macro share a name
        used_names = set(self._global_used_names)

        for micro_id in range(n_micro_segments):
            micro_customers = customers_df[customers_df['micro_segment'] == micro_id]
            
            if len(micro_customers) == 0:
                continue
            
            # Calculate characteristics
            def _col_mean(col, default):
                return float(micro_customers[col].mean()) if col in micro_customers.columns else default

            def _col_mode(col, default):
                s = micro_customers[col] if col in micro_customers.columns else None
                return s.mode()[0] if s is not None and len(s.mode()) > 0 else default

            characteristics = {
                'avg_digital_engagement':  _col_mean('digital_engagement_score', 0.5),
                'avg_portfolio_depth':     _col_mean('num_products', 2),
                'avg_credit_utilization':  _col_mean('credit_utilization_ratio', 0.3),
                'avg_transaction_velocity': _col_mean('transaction_volume_30d', 5),
                'avg_account_tenure': float(
                    micro_customers['months_since_relationship_started'].mean()
                    if 'months_since_relationship_started' in micro_customers.columns else (
                        micro_customers['tenure_months'].mean()
                        if 'tenure_months' in micro_customers.columns else 24
                    )
                ),
                'avg_cross_sell_score':    _col_mean('cross_sell_receptivity', 0.5),
                'avg_deposits':            _col_mean('total_deposits', 0),
                'avg_income':              _col_mean('income', 50000),
                'avg_credit_score':        _col_mean('credit_score', 650),
                'avg_age':                 _col_mean('age', 40),
                'dominant_life_stage':     _col_mode('life_stage', ''),
                'dominant_risk_tolerance': _col_mode('risk_tolerance', 'Moderate'),
                'dominant_financial_goal': _col_mode('financial_goal', ''),
                'avg_churn_probability':   _col_mean('churn_probability', 0.15),
            }

            # Attach the High/Mid/Low feature profile for this cluster so the
            # naming function can build context-aware, non-repeating names.
            fp = getattr(self, '_last_cluster_feature_profiles', {}).get(micro_id, {})
            characteristics['_feature_profile'] = fp
            characteristics['_split_features'] = selected_features or []
            characteristics['_macro_primary_trait'] = primary_trait
            
            # Determine Value tier for segment
            avg_deposits = characteristics['avg_deposits']
            if avg_deposits < 25000:
                ltv_tier = 'Bronze'
            elif avg_deposits < 100000:
                ltv_tier = 'Silver'
            elif avg_deposits < 250000:
                ltv_tier = 'Gold'
            else:
                ltv_tier = 'Platinum'
            
            # Generate UNIQUE micro segment name + description in one LLM call
            parent_name = macro_name if macro_name else self.macro_personas[macro_segment_id].get('short_name', f'Macro_{macro_segment_id}')
            segment_name, micro_description = self._generate_micro_segment_profile(
                characteristics,
                ltv_tier,
                parent_name,
                micro_id,
                used_names=used_names,
                macro_segment_id=macro_segment_id,
            )

            # A name reused from the segment-name cache (see
            # _generate_micro_segment_profile) is EXPECTED to already be in
            # used_names  -  that persistent set tracks every name ever used
            # across all past runs, and a cached name was used before by
            # definition. Only treat "already used" as a real collision for a
            # freshly-generated name, not a legitimate historical reuse of
            # this exact (macro_segment_id, micro_id) slot's own name.
            from utils.segment_name_cache import get_cached_name as _get_cached_micro_name
            _is_cache_hit = _get_cached_micro_name('banking_micro', f"{macro_segment_id}:{micro_id}") is not None
            if segment_name in used_names and not _is_cache_hit:
                logger.warning(f"Micro name collision '{segment_name}'  -  regenerating with rule-based fallback")
                fp   = characteristics.get('_feature_profile', {})
                sf   = characteristics.get('_split_features', [])
                ps   = _PARENT_SHORT_NAMES.get(macro_name, macro_name.split()[-1] if macro_name else 'Customer')
                used_adj = {n.split()[0] for n in used_names if len(n.split()) >= 2}
                segment_name = _build_micro_name(fp, sf, ps, used_adj)

            used_names.add(segment_name)
            
            logger.info(f"Generated micro segment: '{segment_name}' (LTV: {ltv_tier}, Size: {len(micro_customers)})")
            
            # Calculate revenue metrics
            total_deposits = float(micro_customers.get('total_deposits', 0).sum())
            avg_deposits_per_customer = total_deposits / len(micro_customers)
            
            # Generate explanation
            micro_explanation = self._generate_micro_segment_explanation(
                characteristics,
                ltv_tier,
                segment_name,
                len(micro_customers),
                avg_deposits_per_customer,
                micro_id=micro_id,
                description=micro_description,
            )
            
            micro_segments[micro_id] = {
                'micro_segment_id': micro_id,
                'segment_name': segment_name,
                'size': len(micro_customers),
                'percentage': round(len(micro_customers) / len(customers_df) * 100, 1),
                'ltv_tier': ltv_tier,
                'characteristics': characteristics,
                'revenue_metrics': {
                    'total_deposits': round(total_deposits, 2),
                    'avg_customer_value': round(avg_deposits_per_customer, 2),
                    'revenue_percentage': round(total_deposits / customers_df.get('total_deposits', 1).sum() * 100, 1)
                },
                'top_customers': self._get_top_customers(micro_customers, n=5),
                'segment_explanation': micro_explanation
            }
        
        return micro_segments
    
    def _generate_micro_segment_profile(
        self,
        characteristics: Dict,
        ltv_tier: str,
        macro_name: str,
        micro_id: int = 0,
        used_names: set = None,
        macro_segment_id: int = None,
    ) -> tuple:
        """
        Generate micro segment name + description in one LLM call.
        Returns (name: str, description: str). Falls back to rule-based on failure.

        The LLM receives:
        - macro parent name (so names feel like sub-categories of that macro)
        - feature profile (High/Mid/Low on each split dimension)
        - globally used names (to prevent cross-macro repeats)

        Reuses a previously-generated name for this same (macro_segment_id,
        micro_id) slot for CACHE_TTL_HOURS (utils/segment_name_cache.py)
        instead of re-generating one on every re-run.
        """
        from utils.segment_name_cache import get_cached_name, save_name
        _cache_key = f"{macro_segment_id}:{micro_id}"

        # NOTE: no "not in used_names" re-check here, unlike the macro cache
        # hook  -  `used_names`/`_global_used_names` for micro is a PERSISTENT
        # registry of every name ever used across ALL past runs (see
        # __init__'s global_used_names param), not a per-run set. A cached
        # name is by definition already in it (that's why it's cached), so
        # that check would reject every real cache hit. Each (macro_segment_id,
        # micro_id) key is only ever looked up once per run, so a cache hit
        # here can't collide with itself within this run.
        _cached = get_cached_name('banking_micro', _cache_key)
        if _cached:
            return _cached['name'], _cached['description']

        feature_profile = characteristics.get('_feature_profile', {})
        split_features  = characteristics.get('_split_features', [])
        macro_trait     = characteristics.get('_macro_primary_trait', 'deposits')

        # ── Build split-dimension context for LLM ──
        dim_parts = []
        for f in split_features:
            direction = feature_profile.get(f, 'Mid')
            if direction != 'Mid':
                label = _FEATURE_LABELS.get(f, f)
                dim_parts.append(f"{label} is {direction.lower()}")
        split_context = '; '.join(dim_parts) if dim_parts else 'no strong differentiator'

        # ── Short parent label (used in fallback AND passed to LLM as format hint) ──
        parent_short = _PARENT_SHORT_NAMES.get(macro_name, macro_name.split()[-1] if macro_name else 'Customer')

        if CLAUDE_AVAILABLE and get_claude_client:
            try:
                client = get_claude_client()
                if client.is_available():
                    stats_for_llm = {
                        'avg_income':              characteristics.get('avg_income', 0),
                        'avg_credit_score':        characteristics.get('avg_credit_score', 650),
                        'avg_deposits':            characteristics.get('avg_deposits', 0),
                        'avg_digital_engagement':  characteristics.get('avg_digital_engagement', 0.5),
                        'avg_products':            characteristics.get('avg_portfolio_depth', 2.0),
                        'avg_transactions':        characteristics.get('avg_transaction_velocity', 5),
                        'avg_age':                 characteristics.get('avg_age', 40),
                        'dominant_life_stage':     characteristics.get('dominant_life_stage', ''),
                        'dominant_risk_tolerance': characteristics.get('dominant_risk_tolerance', 'Moderate'),
                        'dominant_financial_goal': characteristics.get('dominant_financial_goal', ''),
                        'avg_churn_probability':   characteristics.get('avg_churn_probability', 0.15),
                        'primary_trait':           macro_trait,
                        'macro_parent':            macro_name,
                        'parent_short':            parent_short,
                        'split_dimensions':        split_context,
                        'feature_profile':         feature_profile,
                    }
                    result = client.generate_segment_profile(
                        stats_for_llm,
                        used_names=list(used_names) if used_names else [],
                        segment_type="micro",
                    )
                    llm_name = result.get('name', '').strip()
                    llm_desc = result.get('description', '').strip()
                    if llm_name and llm_desc and llm_name not in (used_names or set()):
                        save_name('banking_micro', _cache_key, llm_name, llm_desc, 'llm')
                        return llm_name, llm_desc
                    elif llm_name and llm_desc:
                        # LLM returned a duplicate  -  fall through to rule-based naming
                        # which tracks used adjectives and always produces a unique name
                        logger.warning(f"LLM micro name collision '{llm_name}', using rule-based fallback")
            except Exception as e:
                logger.warning(f"Claude micro profile failed: {e}")

        # ── Fallback: rule-based name + simple description ──
        used_adjectives = {n.split()[0] for n in (used_names or []) if len(n.split()) >= 2}
        segment_name = _build_micro_name(feature_profile, split_features, parent_short, used_adjectives)
        deposits  = characteristics.get('avg_deposits', 0)
        digital   = characteristics.get('avg_digital_engagement', 0.5)
        portfolio = characteristics.get('avg_portfolio_depth', 2.0)
        desc = (
            f"Customers with {split_context}. "
            f"Avg savings ${deposits:,.0f}, {digital*100:.0f}% digital usage, {portfolio:.1f} products held."
        )
        save_name('banking_micro', _cache_key, segment_name, desc, 'rule_based')
        return segment_name, desc

    def _generate_micro_segment_name(self, characteristics, ltv_tier, macro_name, micro_id=0, used_names=None) -> str:
        """Backward-compat wrapper  -  returns name only."""
        name, _ = self._generate_micro_segment_profile(characteristics, ltv_tier, macro_name, micro_id, used_names)
        return name
    
    def _generate_name_explanation(
        self,
        segment_name: str,
        characteristics: Dict,
        ltv_tier: str,
        segment_size: int
    ) -> str:
        """
        Generate SHORT, name-focused explanation (1 sentence)
        Explains what THIS specific micro segment name means
        """
        deposits = characteristics['avg_deposits']
        digital = characteristics['avg_digital_engagement']
        portfolio = characteristics['avg_portfolio_depth']
        velocity = characteristics['avg_transaction_velocity']
        income = characteristics['avg_income']
        
        name_lower = segment_name.lower()
        
        # Pattern-match on segment name components
        
        # ULTRA/PREMIUM patterns
        if 'ultra-premium' in name_lower or 'ultra-high' in name_lower:
            if 'wealth' in name_lower:
                return f"'{segment_name}' identifies {segment_size} ultra-wealthy customers with ${deposits/1000000:.1f}M deposits in the {ltv_tier} tier."
            else:
                return f"'{segment_name}' represents {segment_size} top-tier customers (${deposits/1000000:.1f}M, {ltv_tier}) with exceptional banking value."
        
        # HIGH-VALUE/HIGH-PERFORMANCE patterns
        elif 'high-value' in name_lower or 'high-performance' in name_lower:
            return f"'{segment_name}' captures {segment_size} affluent customers with ${deposits:,.0f} deposits and strong banking engagement ({ltv_tier} tier)."
        
        # HYPERACTIVE patterns
        elif 'hyperactive' in name_lower:
            return f"'{segment_name}' describes {segment_size} extremely active customers with {digital*100:.0f}% digital usage and frequent banking interactions."
        
        # DIGITAL/TECH patterns
        elif 'digital' in name_lower or 'tech' in name_lower:
            if 'user' in name_lower:
                return f"'{segment_name}' highlights {segment_size} tech-savvy customers with {digital*100:.0f}% digital adoption ({ltv_tier} tier)."
            else:
                return f"'{segment_name}' identifies {segment_size} digitally-engaged customers ({digital*100:.0f}% online) with ${deposits:,.0f} deposits."
        
        # MULTI-PRODUCT/DIVERSIFIED patterns
        elif 'multi-product' in name_lower or 'diversified' in name_lower:
            return f"'{segment_name}' represents {segment_size} customers with {portfolio:.1f} avg products held, showing deep banking relationships ({ltv_tier} tier)."
        
        # DUAL-SERVICE patterns
        elif 'dual-service' in name_lower:
            return f"'{segment_name}' captures {segment_size} customers using {portfolio:.1f} core products on average with ${deposits:,.0f} deposits ({ltv_tier} tier)."
        
        # TRADITIONAL/ESTABLISHED patterns
        elif 'traditional' in name_lower or 'established' in name_lower:
            return f"'{segment_name}' describes {segment_size} loyal customers with ${deposits:,.0f} deposits preferring traditional banking relationships ({ltv_tier})."
        
        # AFFLUENT patterns
        elif 'affluent' in name_lower:
            return f"'{segment_name}' identifies {segment_size} high-net-worth customers with ${deposits:,.0f} deposits and {ltv_tier}-tier lifetime value."
        
        # ENGAGED/ACTIVE patterns
        elif 'engaged' in name_lower or 'active' in name_lower:
            return f"'{segment_name}' represents {segment_size} highly engaged customers with frequent banking activity and ${deposits:,.0f} deposits ({ltv_tier})."
        
        # EMERGING/GROWTH patterns
        elif 'emerging' in name_lower or 'growth' in name_lower:
            return f"'{segment_name}' captures {segment_size} upwardly mobile customers with ${deposits:,.0f} deposits and growth potential ({ltv_tier} tier)."
        
        # LEADER patterns
        elif 'leader' in name_lower:
            return f"'{segment_name}' designates {segment_size} top-performing customers with ${deposits/1000000:.1f}M deposits, leading their segment ({ltv_tier} tier)."
        
        # CUSTOMER/USER patterns (generic)
        elif 'customer' in name_lower or 'user' in name_lower:
            return f"'{segment_name}' identifies {segment_size} banking customers with ${deposits:,.0f} deposits and {portfolio:.1f} avg products ({ltv_tier} tier)."
        
        # SEGMENT patterns (generic)
        elif 'segment' in name_lower:
            return f"'{segment_name}' groups {segment_size} customers with ${deposits:,.0f} deposits, {digital*100:.0f}% digital usage ({ltv_tier} tier)."
        
        # FALLBACK: Focus on tier
        else:
            return f"'{segment_name}' represents {segment_size} {ltv_tier}-tier customers with ${deposits:,.0f} deposits and unique banking behaviors."
    
    def _generate_micro_segment_explanation(
        self,
        characteristics: Dict,
        ltv_tier: str,
        segment_name: str,
        segment_size: int,
        avg_customer_value: float,
        micro_id: int = 0,
        description: str = '',
    ) -> Dict:
        """
        Generate COMPLETELY UNIQUE insights for each micro segment.
        `description` is the LLM-generated narrative (name + key facts in one paragraph).
        """
        digital_engagement = characteristics['avg_digital_engagement']
        portfolio_depth = characteristics['avg_portfolio_depth']
        credit_utilization = characteristics['avg_credit_utilization']
        transaction_velocity = characteristics['avg_transaction_velocity']
        avg_products = float(portfolio_depth)
        txn_mo = float(transaction_velocity)
        
        # FORCE COMPLETE UNIQUENESS - Include segment name in EVERY insight
        # This makes duplication impossible
        
        segment_definition = []
        key_behaviors = []
        recommendations = []
        
        # Get actual data ranges
        deposits_range = f"${characteristics.get('avg_deposits', 0):,.0f}"
        income_range = f"${characteristics.get('avg_income', 0):,.0f}"
        
        # Build UNIQUE segment definition with ALL characteristics + emojis for visual clarity
        segment_definition.append(f"**{segment_name}** micro segment ({segment_size} customers)")
        segment_definition.append(
            f"🧭 Sub-cluster #{micro_id + 1}: distinct behavioral slice within the parent macro segment (K-Means cell) - metrics below apply only to this group."
        )
        segment_definition.append(f"💰 Value: {deposits_range} average | {ltv_tier} tier | Income: {income_range}/year")
        segment_definition.append(f"📊 Portfolio: {avg_products:.1f} avg products held | {digital_engagement*100:.0f}% digital engagement")
        segment_definition.append(f"⚡ Activity: {txn_mo:.1f} transactions/mo (avg) | {credit_utilization*100:.0f}% credit utilization")
        
        # KEY BEHAVIORS - COMPLETELY UNIQUE based on segment name + metrics
        # MARKETING OPPORTUNITIES - Actionable directives for sales/marketing (what to DO), unique per micro segment
        if 'Multi-Product' in segment_name:
            key_behaviors.append(f"{segment_name}: {avg_products:.0f}+ products totaling {deposits_range} in {ltv_tier} tier")
            key_behaviors.append(f"Deep product relationships with {digital_engagement*100:.0f}% digital usage and ~{txn_mo:.0f} transactions/mo")
            key_behaviors.append(f"Consolidated banking across checking, savings, loans, investments - {segment_size} customers")
            recommendations.append(f"Offer relationship-based fee waivers for customers maintaining {avg_products:.0f}+ products; run a retention campaign to this micro segment.")
            recommendations.append(f"Propose consolidated relationship pricing and assign a single point of contact for the {segment_size} customers in this micro segment.")
            recommendations.append(f"Cross-sell one complementary product (e.g. investment or insurance) via personalized outreach; use deposit and product data to tailor the offer.")
        
        elif 'Diversified' in segment_name:
            key_behaviors.append(f"{segment_name}: Spread {deposits_range} across {avg_products:.0f} different products - {segment_size} customers")
            key_behaviors.append(f"Diversification strategy with {ltv_tier} tier status, ~{txn_mo:.0f} transactions/mo, {digital_engagement*100:.0f}% digital")
            key_behaviors.append(f"Balanced portfolio approach minimizes risk while maximizing banking relationship value")
            recommendations.append(f"Launch a consolidated dashboard or reporting offer for this micro segment; use it to recommend one next product that fits their portfolio.")
            recommendations.append(f"Run a bundle campaign (e.g. discount or rate incentive) for adding one more product; target the {segment_size} diversified customers with clear benefit.")
            recommendations.append(f"Send segment-specific messaging linking their current {avg_products:.0f} products to one logical add-on (e.g. savings if they have checking only).")
        
        elif 'Growing' in segment_name:
            key_behaviors.append(f"{segment_name}: Expanding portfolios from {deposits_range} baseline in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"Growth trajectory customers increasing products from current {avg_products:.0f} level")
            key_behaviors.append(f"High potential segment with {credit_utilization*100:.0f}% credit usage and {digital_engagement*100:.0f}% digital engagement")
            recommendations.append(f"Run a product-adoption campaign with a small incentive (e.g. bonus rate or waiver) for adding one more product; target this micro segment first.")
            recommendations.append(f"Create a pathway program (e.g. step-up to next tier) and invite the {segment_size} customers with personalized next-step offers.")
            recommendations.append(f"Send educational content (e.g. benefits of savings or credit) followed by a soft product offer; use digital channel if {digital_engagement*100:.0f}%+ digital.")
        
        elif 'Active' in segment_name or 'Frequent' in segment_name or 'Power' in segment_name:
            key_behaviors.append(f"{segment_name}: High-activity users with ~{txn_mo:.0f} transactions/mo managing {deposits_range} - {segment_size} customers")
            key_behaviors.append(f"Conduct frequent transactions across {avg_products:.0f} products with {digital_engagement*100:.0f}% digital adoption")
            key_behaviors.append(f"Generate significant engagement in {ltv_tier} tier through consistent banking activity")
            recommendations.append(f"Offer an activity-based rewards tier (e.g. cashback or fee waivers) for maintaining this transaction level; promote to the {segment_size} customers in this micro segment.")
            recommendations.append(f"Run a campaign that rewards high-activity customers with premium features or a dedicated service option; use preferred channel (app if high digital).")
            recommendations.append(f"Propose a premium checking or payment product that matches their transaction profile; use behavioral triggers to time the offer.")
        
        elif 'Digital' in segment_name or 'Tech' in segment_name:
            key_behaviors.append(f"{segment_name}: {digital_engagement*100:.0f}% digital engagement with {deposits_range} in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"Digital-first with {avg_products:.0f} products and ~{txn_mo:.0f} transactions/mo")
            recommendations.append(f"Deploy in-app and email campaigns for this micro segment; offer one next-best product with a one-tap or instant-apply flow.")
            recommendations.append(f"Invite to beta features or digital-only events; use feedback to refine offers and then roll out to the full {segment_size} customers.")
            recommendations.append(f"Run A/B tests on product and messaging for digital-first users; prioritize app push and in-app placement.")
        
        elif 'Traditional' in segment_name or 'Branch' in segment_name or 'Establish' in segment_name:
            key_behaviors.append(f"{segment_name}: Lower digital adoption ({digital_engagement*100:.0f}%), {deposits_range} in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"Prefer branch or phone with {avg_products:.0f} products and ~{txn_mo:.0f} transactions/mo")
            recommendations.append(f"Use outbound call or branch-led outreach for this micro segment; offer one product with a simple application process.")
            recommendations.append(f"Run a direct mail or branch poster campaign with a clear CTA (e.g. call or visit) for the {segment_size} customers in this micro segment.")
            recommendations.append(f"Train branch staff on a single next-best offer for this profile; track conversion and refine messaging.")
        
        elif 'Affluent' in segment_name or 'Elite' in segment_name or 'Wealth' in segment_name:
            key_behaviors.append(f"{segment_name}: High value {deposits_range} in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"Strong portfolio ({avg_products:.0f} products) and {digital_engagement*100:.0f}% digital; ~{txn_mo:.0f} transactions/mo")
            recommendations.append(f"Propose a relationship manager or premium tier for this micro segment; book discovery calls or invite to an exclusive event.")
            recommendations.append(f"Run a wealth-advisory or investment onboarding campaign; target the {segment_size} customers with personalized, high-touch outreach.")
            recommendations.append(f"Offer an affluent-only benefit (e.g. preferred rates, concierge) and use it to cross-sell one high-value product.")
        
        elif 'Emerging' in segment_name or 'Growth' in segment_name:
            key_behaviors.append(f"{segment_name}: Growth potential with {deposits_range}, {avg_products:.0f} products in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"{digital_engagement*100:.0f}% digital, ~{txn_mo:.0f} transactions/mo, {credit_utilization*100:.0f}% credit utilization")
            recommendations.append(f"Run a first-product or next-product campaign with a small incentive to move this micro segment to the next tier.")
            recommendations.append(f"Send educational content and a single product recommendation (e.g. savings or credit) tailored to their profile; measure conversion.")
            recommendations.append(f"Assign light-touch outbound or in-app follow-up to the {segment_size} customers; test offer and channel.")
        
        # Data-driven fallback: unique actionable recommendations from metrics (no generic "targeted campaigns")
        if len(key_behaviors) == 0:
            key_behaviors.append(f"{segment_name}: {segment_size} customers managing {deposits_range} in {ltv_tier} tier")
            key_behaviors.append(f"Portfolio {avg_products:.0f} products, {digital_engagement*100:.0f}% digital, ~{txn_mo:.0f} transactions/mo")
        
        if len(recommendations) == 0:
            if digital_engagement >= 0.6:
                recommendations.append(f"Run in-app and email offers for the {segment_size} customers in this micro segment; recommend one product that fits {deposits_range} and {ltv_tier} tier.")
            else:
                recommendations.append(f"Use outbound or branch-led outreach for the {segment_size} customers; offer one product with a simple application and clear benefit.")
            if portfolio_depth < 0.8:
                recommendations.append(f"Campaign to add one more product (e.g. savings or credit) for customers at {avg_products:.0f} products; use incentive to test conversion.")
            else:
                recommendations.append(f"Offer relationship rewards (e.g. fee waiver or preferred rate) for maintaining {avg_products:.0f}+ products; use retention messaging.")
            recommendations.append(f"Tailor next-best action for this micro segment using {ltv_tier} tier and {deposits_range}; measure by segment and iterate.")
        
        # UNIQUE marketing opportunities: try LLM first, else personalize so each micro segment is unique
        recommendations = recommendations[:4]
        segment_def_text = "\n".join(segment_definition)
        metrics_for_llm = {
            'avg_deposits': characteristics.get('avg_deposits', 0),
            'avg_income': characteristics.get('avg_income', 0),
            'avg_digital': digital_engagement,
            'avg_products': avg_products,
            'avg_transactions': txn_mo,
            'avg_cross_sell': credit_utilization,
            'avg_age': characteristics.get('avg_age', 45),
        }
        used_llm_recs = False
        if TOGETHER_AI_AVAILABLE and together_ai and os.getenv("TOGETHER_API_KEY"):
            try:
                llm_recs = together_ai.generate_marketing_opportunities(
                    persona_name=segment_name,
                    segment_definition=segment_def_text,
                    key_behaviors=key_behaviors[:4],
                    metrics=metrics_for_llm
                )
                if llm_recs and len(llm_recs) >= 3:
                    recommendations = llm_recs[:4]
                    used_llm_recs = True
            except Exception as e:
                logger.debug(f"LLM marketing opportunities failed for micro {segment_name}, using personalized fallback: {e}")
        if not used_llm_recs:
            # One full clause; no mid-phrase truncation; prefix with metrics so segments differ
            short_recs = []
            deposits_range = f"${characteristics.get('avg_deposits', 0)/1e6:.1f}M" if characteristics.get('avg_deposits', 0) >= 1e6 else f"${characteristics.get('avg_deposits', 0):,.0f}"
            prefix = f"**{segment_name}** ({deposits_range}, {digital_engagement*100:.0f}% digital): "
            for r in recommendations:
                if ";" in r:
                    s = r.split(";")[0].strip()
                    s = s + "." if s and not s.endswith(".") else s
                else:
                    s = r.split(".")[0].strip() + "." if "." in r else r
                if len(s) > 130:
                    s = (s[:127].rsplit(" ", 1)[0] or s[:127]) + "..."
                short_recs.append(prefix + s)
            recommendations = short_recs
        
        # Generate detailed name explanation
        name_explanation = self._generate_name_explanation(
            segment_name=segment_name,
            characteristics=characteristics,
            ltv_tier=ltv_tier,
            segment_size=segment_size
        )
        
        return {
            'description': description,            # LLM-generated narrative paragraph
            'name_explanation': name_explanation,
            'segment_definition': segment_def_text,
            'key_behaviors': key_behaviors[:4],
            'marketing_recommendations': recommendations,
            'segment_size': segment_size,
            'avg_customer_value': avg_customer_value,
        }
    def _get_top_customers(self, customers_df: pd.DataFrame, n: int = 5) -> List[Dict]:
        """
        Get top customers by deposits in a micro segment
        """
        top_customers = customers_df.nlargest(n, 'total_deposits')
        
        return [
            {
                'customer_id': row['customer_id'],
                'customer_name': row.get('customer_name', row.get('name', f"Customer {row['customer_id']}")),
                'total_deposits': round(row.get('total_deposits', 0), 2),
                'num_products': int(row.get('num_products', 1)),
                'digital_engagement': round(row.get('digital_engagement_score', 0.5), 2),
                'cluster': int(row.get('cluster', 0))
            }
            for _, row in top_customers.iterrows()
        ]


if __name__ == "__main__":
    print("="*70)
    print("Agent A Micro - Banking Micro Segmentation")
    print("="*70)
    print("This agent creates sub-segments within macro personas")
    print("Run this through the main API after macro segmentation")
    print("="*70)

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
    print("⚠️  Warning: kmodes not installed. Run: pip install kmodes")
    KMODES_AVAILABLE = False

# Add utils to path for image mapper and optional LLM
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.image_mapper import get_image_mapper
    IMAGE_MAPPER_AVAILABLE = True
except ImportError:
    IMAGE_MAPPER_AVAILABLE = False
    print("⚠️  Warning: Image mapper not available")
try:
    from utils.together_ai import together_ai
    TOGETHER_AI_AVAILABLE = True
except ImportError:
    TOGETHER_AI_AVAILABLE = False
    together_ai = None

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
        # ALWAYS create num_products column first
        try:
            if 'product_id' in self.transactions_df.columns:
                product_counts = self.transactions_df.groupby('customer_id')['product_id'].nunique()
                self.customers_df['num_products'] = self.customers_df['customer_id'].map(product_counts).fillna(2)
            else:
                # Try product_holdings file
                try:
                    holdings_df = pd.read_csv(self.data_path / 'product_holdings.csv')
                    product_counts = holdings_df.groupby('customer_id').size()
                    self.customers_df['num_products'] = self.customers_df['customer_id'].map(product_counts).fillna(2)
                except:
                    self.customers_df['num_products'] = 2  # Default
        except Exception as e:
            logger.warning(f"Could not count products: {e}")
            self.customers_df['num_products'] = 2  # Default
        
        # Now calculate product adoption velocity if tenure exists
        if 'tenure_months' in self.customers_df.columns:
            self.customers_df['product_adoption_velocity'] = (
                self.customers_df['num_products'] / (self.customers_df['tenure_months'] + 1)
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
        
        # Account tenure months (already exists as tenure_months)
        if 'tenure_months' in self.customers_df.columns:
            self.customers_df['account_tenure_months'] = self.customers_df['tenure_months']
        else:
            self.customers_df['account_tenure_months'] = 24
        
        # Relationship length years
        self.customers_df['relationship_length_years'] = (self.customers_df['account_tenure_months'] / 12).astype(int)
        
        # Risk tolerance (from risk_category)
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
    
    def _generate_dynamic_segment_name(self, characteristics, percentile, primary_trait, avg_transactions_real, cluster_id=None):
        """
        Generate COMPLETELY UNIQUE segment names with NO repetition
        
        Strategy: Each segment gets a unique combination that CANNOT repeat
        Uses 5 distinct naming pools to ensure variety
        """
        
        # Extract all key metrics
        deposits = characteristics['avg_deposits']
        digital = characteristics['avg_digital']
        products = characteristics['avg_products']
        cross_sell = characteristics['avg_cross_sell']
        age = characteristics.get('avg_age', 45)
        
        # Define 5 COMPLETELY DIFFERENT naming pools (one per segment)
        # Each pool has unique descriptors that don't overlap
        
        # SIMPLIFIED NAMING - Just 2 words for UI visibility
        naming_pools = [
            # Pool A: Premium segment
            ['Premium Digital', 'Elite Savers', 'Wealth Investors', 'VIP Banking', 'Platinum Members'],
            # Pool B: Growth segment  
            ['Rising Savers', 'Growth Builders', 'Active Earners', 'Aspiring Wealth', 'Dynamic Planners'],
            # Pool C: Established segment
            ['Core Banking', 'Steady Savers', 'Traditional Members', 'Established Customers', 'Reliable Banking'],
            # Pool D: Young/Tech segment
            ['Mobile First', 'Digital Natives', 'Tech Adopters', 'Modern Banking', 'App Users'],
            # Pool E: Family segment
            ['Family Banking', 'Household Savers', 'Community Members', 'Local Banking', 'Neighborhood Partners']
        ]
        
        # Select pool based on cluster_id to guarantee uniqueness
        pool_index = cluster_id % len(naming_pools) if cluster_id is not None else 0
        pool = naming_pools[pool_index]
        
        # Select ONE name from the pool based on combined characteristics
        # This creates a score to pick the best name from the 5 options
        deposit_score = min(4, int(deposits / 300000))  # 0-4
        transaction_score = min(4, int(avg_transactions_real / 8))  # 0-4
        digital_score = min(4, int(digital / 0.20))  # 0-4
        
        # Combined scoring to pick name index (0-4)
        combined_score = (deposit_score + transaction_score + digital_score) // 3
        name_idx = min(4, max(0, combined_score))
        
        unique_name = pool[name_idx]
        
        return unique_name
    
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
        if 'num_products' in cluster_data.columns and 'tenure_months' in cluster_data.columns:
            product_velocity = (cluster_data['num_products'] / (cluster_data['tenure_months'] + 1)).mean()
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
        
        # Add CLV if available (from enhanced data)
        if 'customer_lifetime_value' not in df_enhanced.columns and 'tenure_months' in df_enhanced.columns:
            # Calculate CLV on the fly if not in data
            df_enhanced['annual_transaction_value'] = df_enhanced['monthly_transaction_volume'] * df_enhanced['total_deposits'] * 0.002
            df_enhanced['expected_relationship_years'] = df_enhanced['tenure_months'].apply(lambda x: min(x / 12, 10))
            df_enhanced['customer_lifetime_value'] = (
                df_enhanced['total_deposits'] + 
                (df_enhanced['annual_transaction_value'] * df_enhanced['expected_relationship_years'])
            )
            logger.info("✓ Calculated CLV from existing data")
        
        # Select features for clustering with IMPORTANCE WEIGHTING
        # High-impact features that drive business decisions
        primary_features = [
            'customer_lifetime_value',  # MOST IMPORTANT - Total customer value over lifetime
            'total_deposits',  # Current wealth tier
            'monthly_transaction_volume',  # Activity level
            'cross_sell_receptivity',  # Willingness to buy
            'num_products',  # Relationship depth
            'digital_engagement_score',  # Channel preference
        ]
        
        # Supporting features
        secondary_features = [
            'product_adoption_velocity',
            'income',
            'credit_score',
            'customer_value_score',
            'digital_adoption',
            'financial_health'
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
                    # Remove random_state to allow gamma to affect clustering differently
                    # Gamma changes the distance metric, which should produce different clusters
                    model = KPrototypes(
                        n_clusters=n_clusters,
                        gamma=gamma,
                        init='Huang',
                        n_init=3,  # Multiple inits for better convergence
                        max_iter=50,  # More iterations
                        verbose=0
                        # NO random_state - allow variation with gamma
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
                    min_deposits_per_customer=5000
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
                silhouette_score = float(calc_silhouette(numeric_data, clusters))
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
        
        # NO MORE PREDEFINED ARCHETYPES - Everything is data-driven now!
        
        for cluster_id in sorted(self.customers_df['cluster'].unique()):
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
            avg_transactions_real = txn_metrics['monthly_transaction_rate']  # Use MONTHLY rate, not annual!
            
            # Generate UNIQUE dynamic name based on actual characteristics
            persona_name = self._generate_dynamic_segment_name(
                characteristics, 
                percentile, 
                primary_trait,
                avg_transactions_real,
                cluster_id=cluster_id  # Pass cluster_id for guaranteed uniqueness
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
            
            # STRICT VALIDATION: Names should NEVER collide with new pool-based logic
            if persona_name in used_names:
                # This should NEVER happen - indicates a serious logic error
                logger.error(f"CRITICAL ERROR: Duplicate name '{persona_name}' detected!")
                logger.error(f"  Cluster {cluster_id} attempted to use a name already taken")
                raise ValueError(f"Segment naming logic failed - duplicate '{persona_name}' detected!")
            
            used_names.add(persona_name)
            logger.info(f"✓ Unique name generated: '{persona_name}'")
            
            # Generate short name
            short_name = ''.join([word[0].upper() for word in persona_name.split()[:3]])
            if not short_name:
                short_name = f"SEG{cluster_id}"
            
            # Description with PRIMARY trait
            description = f"{persona_name} - {primary_trait.title()} leaders ({percentile:.0f}th percentile)"
            
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
                'size': int(size),
                'percentage': float(percentage),
                # Frontend expects these at root level - NOW FULLY DYNAMIC!
                'avg_balance': float(avg_deposits),
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
                    'dominant_life_stage': dominant_life_stage
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
        logger.info("🔍 Generating unique segment explanations...")
        for cluster_id, persona in personas.items():
            try:
                # Ensure all needed data is in characteristics
                persona['characteristics']['avg_age'] = persona['characteristics'].get('avg_age', 45)
                persona['characteristics']['avg_income'] = persona['characteristics'].get('avg_income', avg_income)
                
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
        """
        Generate COMPLETELY UNIQUE insights for each segment
        Every segment gets different insights based on its UNIQUE combination of traits
        NO TWO SEGMENTS SHOULD HAVE SAME INSIGHTS
        """
        
        # Get ALL metrics for this segment
        avg_transactions = characteristics.get('avg_monthly_transaction_volume', characteristics.get('monthly_transaction_volume', 0))
        avg_cross_sell = characteristics.get('avg_cross_sell_receptivity', 0)
        avg_credit = characteristics.get('avg_credit_score', 700)
        avg_age = characteristics.get('avg_age', 45)
        
        # Calculate PRECISE PERCENTILES across all segments
        all_deposits = [p.get('characteristics', {}).get('avg_deposits', 0) for p in self.personas.values()]
        all_digital = [p.get('characteristics', {}).get('avg_digital_engagement', 0) for p in self.personas.values()]
        all_products = [p.get('characteristics', {}).get('avg_products', 0) for p in self.personas.values()]
        all_transactions = [p.get('characteristics', {}).get('avg_monthly_transaction_volume', 0) for p in self.personas.values()]
        all_cross_sell = [p.get('characteristics', {}).get('avg_cross_sell_receptivity', 0) for p in self.personas.values()]
        
        import numpy as np
        
        deposit_rank = (sum(d < avg_deposits for d in all_deposits) / len(all_deposits)) * 100 if all_deposits else 50
        digital_rank = (sum(d < avg_digital for d in all_digital) / len(all_digital)) * 100 if all_digital else 50
        products_rank = (sum(p < avg_products for p in all_products) / len(all_products)) * 100 if all_products else 50
        trans_rank = (sum(t < avg_transactions for t in all_transactions) / len(all_transactions)) * 100 if all_transactions else 50
        cross_rank = (sum(c < avg_cross_sell for c in all_cross_sell) / len(all_cross_sell)) * 100 if all_cross_sell else 50
        
        # Find TOP 2 traits (most distinctive)
        rankings = {
            'deposits': deposit_rank,
            'digital': digital_rank,
            'products': products_rank,
            'transactions': trans_rank,
            'cross_sell': cross_rank
        }
        
        sorted_traits = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
        primary_trait = sorted_traits[0][0]
        secondary_trait = sorted_traits[1][0] if len(sorted_traits) > 1 else None
        
        primary_rank = sorted_traits[0][1]
        secondary_rank = sorted_traits[1][1] if len(sorted_traits) > 1 else 0
        
        # Generate COMPLETELY UNIQUE insights based on PRECISE trait combination
        # Format: Use primary + secondary trait to create 25 possible unique combinations (5x5 matrix)
        trait_combo = f"{primary_trait}_{secondary_trait}"
        
        segment_definition = []
        key_behaviors = []
        marketing_recommendations = []
        
        #=======================================================================
        # UNIQUE INSIGHTS ENGINE - NO TWO SEGMENTS GET SAME INSIGHTS
        # Uses precise ranking + trait combination to generate completely unique content
        #=======================================================================
        
        # SEGMENT DEFINITION - Based on precise characteristics + FULL segment name for uniqueness
        segment_definition.append(f"**{persona_name}** segment defined by {primary_trait} leadership")
        
        if primary_trait == 'deposits':
            segment_definition.append(f"💰 Wealth: ${avg_deposits:,.0f} avg deposits ({primary_rank:.0f}th percentile) | Income: ${avg_income:,.0f}/year")
            segment_definition.append(f"🏦 Relationship: {avg_products:.1f} products | {avg_transactions:.0f} monthly transactions | {avg_digital*100:.0f}% digital")
            segment_definition.append(f"👥 Demographics: Age {avg_age:.0f} | Credit {avg_credit:.0f} | {avg_cross_sell*100:.0f}% cross-sell receptive")
        elif primary_trait == 'digital':
            segment_definition.append(f"📱 Digital: {avg_digital*100:.0f}% online ({primary_rank:.0f}th percentile) | {(1-avg_digital)*100:.0f}% branch visits")
            segment_definition.append(f"💰 Financial: ${avg_deposits:,.0f} deposits | {avg_products:.1f} products | {avg_transactions:.0f} transactions/mo")
            segment_definition.append(f"👥 Profile: Age {avg_age:.0f} | Income ${avg_income:,.0f} | {avg_cross_sell*100:.0f}% receptive")
        elif primary_trait == 'products':
            segment_definition.append(f"📊 Portfolio: {avg_products:.1f} products ({primary_rank:.0f}th percentile) | Multi-product relationship")
            segment_definition.append(f"💰 Engagement: ${avg_deposits:,.0f} deposits | {avg_transactions:.0f} monthly transactions | {avg_digital*100:.0f}% digital")
            segment_definition.append(f"👥 Customer: Age {avg_age:.0f} | Income ${avg_income:,.0f} | {avg_cross_sell*100:.0f}% open to growth")
        elif primary_trait == 'transactions':
            segment_definition.append(f"⚡ Activity: {avg_transactions:.0f} transactions/mo ({primary_rank:.0f}th percentile) | High engagement")
            segment_definition.append(f"💰 Value: ${avg_deposits:,.0f} deposits | {avg_products:.1f} products | {avg_digital*100:.0f}% digital usage")
            segment_definition.append(f"👥 Demographics: Age {avg_age:.0f} | Income ${avg_income:,.0f} | Credit {avg_credit:.0f}")
        else:  # cross_sell
            segment_definition.append(f"🎯 Receptivity: {avg_cross_sell*100:.0f}% openness ({primary_rank:.0f}th percentile) | High growth potential")
            segment_definition.append(f"💰 Current: ${avg_deposits:,.0f} deposits | {avg_products:.1f} products | {avg_transactions:.0f} transactions/mo")
            segment_definition.append(f"👥 Profile: Age {avg_age:.0f} | Income ${avg_income:,.0f} | {avg_digital*100:.0f}% digital")
        
        # KEY BEHAVIORS - FORCE UNIQUENESS by including FULL segment context
        # Use segment name + precise metrics to make each insight completely unique
        
        segment_identifier = persona_name  # Use FULL name for complete uniqueness
        
        if trait_combo == 'deposits_digital':
            key_behaviors.append(f"{segment_identifier} segment: ${avg_deposits:,.0f} deposits with {avg_digital*100:.0f}% digital adoption (ranks {primary_rank:.0f}th deposits, {secondary_rank:.0f}th digital)")
            key_behaviors.append(f"Age {avg_age:.0f}, income ${avg_income:,.0f}, holding {avg_products:.1f} products with {avg_transactions:.0f} monthly transactions")
            marketing_recommendations.append(f"Offer a dedicated wealth-management webinar and in-app premium investment onboarding for high-balance digital users in this segment.")
            marketing_recommendations.append(f"Propose a relationship manager introduction for top digital adopters; run targeted in-app campaigns for investment and savings products.")
            marketing_recommendations.append(f"Launch an exclusive digital-only tier (e.g. fee waivers, priority support) for customers who maintain this balance and digital engagement level.")
        
        elif trait_combo == 'deposits_products':
            key_behaviors.append(f"{segment_identifier} portfolio: ${avg_deposits:,.0f} across {avg_products:.1f} products ({primary_rank:.0f}th deposits, {secondary_rank:.0f}th products)")
            key_behaviors.append(f"{segment_identifier} customers: Age {avg_age:.0f}, ${avg_income:,.0f} income, {avg_transactions:.0f} transactions, {avg_digital*100:.0f}% digital")
            marketing_recommendations.append(f"Assign a relationship manager and propose private banking or premium tier for multi-product, high-balance customers in this segment.")
            marketing_recommendations.append(f"Run a loyalty campaign: offer relationship-based fee waivers and exclusive rates for customers holding {avg_products:.0f}+ products with consolidated balances.")
            marketing_recommendations.append(f"Create a cross-sell playbook for this segment: prioritize investment and insurance products given high receptivity ({avg_cross_sell*100:.0f}%).")
        
        elif trait_combo == 'deposits_transactions':
            key_behaviors.append(f"{segment_identifier} active wealth: ${avg_deposits:,.0f} deposits, {avg_transactions:.0f} transactions ({deposit_rank:.0f}th wealth, {trans_rank:.0f}th activity)")
            key_behaviors.append(f"{segment_identifier} profile: Age {avg_age:.0f}, income ${avg_income:,.0f}, {avg_products:.1f} products, {avg_digital*100:.0f}% digital")
            marketing_recommendations.append(f"Create a VIP recognition program (e.g. concierge banking, dedicated line) for high-balance customers with high transaction volume in this segment.")
            marketing_recommendations.append(f"Offer an activity-based rewards tier (cashback or fee waivers) for customers who maintain this transaction level; use it to deepen product adoption.")
            marketing_recommendations.append(f"Run a campaign promoting premium checking or wealth services tailored to busy, high-value customers in this segment.")
        
        elif trait_combo == 'deposits_cross_sell':
            key_behaviors.append(f"{segment_identifier} growth segment: ${avg_deposits:,.0f} with {avg_cross_sell*100:.0f}% receptivity ({deposit_rank:.0f}th deposits, {cross_rank:.0f}th openness)")
            key_behaviors.append(f"{segment_identifier} ready to expand: Age {avg_age:.0f}, ${avg_income:,.0f} income, {avg_transactions:.0f} transactions, {avg_products:.1f} products")
            marketing_recommendations.append(f"Proactively offer wealth-advisory and investment onboarding for this high-balance, high-receptivity segment; book discovery calls.")
            marketing_recommendations.append(f"Run a targeted upsell campaign for premium products (e.g. investment, insurance) using personalized messaging; A/B test by age band.")
            marketing_recommendations.append(f"Assign outbound sales to propose the next best product (e.g. add 1–2 products) for customers currently at {avg_products:.0f} products.")
        
        elif trait_combo == 'digital_deposits':
            key_behaviors.append(f"{segment_identifier} tech-wealthy: {avg_digital*100:.0f}% digital with ${avg_deposits:,.0f} deposits ({digital_rank:.0f}th digital, {deposit_rank:.0f}th wealth)")
            key_behaviors.append(f"{segment_identifier} demographics: Age {avg_age:.0f}, ${avg_income:,.0f} income, {avg_products:.1f} products, {avg_transactions:.0f} transactions")
            marketing_recommendations.append(f"Launch in-app premium features (e.g. investing, budgeting) and invite this segment to exclusive digital-only events or webinars.")
            marketing_recommendations.append(f"Run in-app and email campaigns for high-value digital users: promote security features, premium support, and next-product recommendations.")
            marketing_recommendations.append(f"Offer a digital-first relationship option (video/chat) and one-click applications for products that match this segment's profile.")
        
        elif trait_combo == 'digital_products':
            key_behaviors.append(f"{segment_identifier} digital portfolios: {avg_digital*100:.0f}% online, {avg_products:.1f} products ({digital_rank:.0f}th digital, {products_rank:.0f}th products)")
            key_behaviors.append(f"{segment_identifier} behavior: Age {avg_age:.0f}, ${avg_income:,.0f} income, ${avg_deposits:,.0f} deposits, {avg_transactions:.0f} transactions")
            marketing_recommendations.append(f"Send in-app bundle offers (e.g. savings + investment, or checking + credit) to multi-product digital users in this segment.")
            marketing_recommendations.append(f"Create a digital-only loyalty tier with fee waivers or rewards for customers holding {avg_products:.0f}+ products; promote via app and email.")
            marketing_recommendations.append(f"Launch a consolidated dashboard and smart alerts in the app; use it to cross-sell the next best product for this segment.")
        
        elif trait_combo == 'digital_transactions':
            key_behaviors.append(f"{segment_identifier} mobile champions: {avg_digital*100:.0f}% digital with {avg_transactions:.0f} transactions ({digital_rank:.0f}th digital, {trans_rank:.0f}th activity)")
            key_behaviors.append(f"{segment_identifier} users: Age {avg_age:.0f}, ${avg_income:,.0f} income, ${avg_deposits:,.0f} deposits, {avg_products:.1f} products")
            marketing_recommendations.append(f"Run a gamified rewards or cashback campaign in the app for high-transaction digital users; use milestones to nudge next product adoption.")
            marketing_recommendations.append(f"Offer premium app features (e.g. instant notifications, spending insights) and promote credit or savings products in-app to this segment.")
            marketing_recommendations.append(f"Invite this segment to beta features or early access; use their engagement to refine offers and messaging for similar customers.")
        
        elif trait_combo == 'digital_cross_sell':
            key_behaviors.append(f"Digital converters: {avg_digital*100:.0f}% online with {avg_cross_sell*100:.0f}% receptivity scoring {cross_rank:.0f}th percentile")
            key_behaviors.append(f"Currently hold {avg_products:.1f} products with ${avg_deposits:,.0f} deposits, seeking expansion digitally")
            marketing_recommendations.append(f"Deploy in-app personalized offers (e.g. pre-approved credit, savings goals) with one-tap apply; prioritize products that complement current holdings.")
            marketing_recommendations.append(f"Run a short campaign promoting one additional product (e.g. credit card or savings) via app push and in-app banners for this receptive segment.")
            marketing_recommendations.append(f"Test one-tap application flows and follow up with a light-touch call or chat for high-intent users in this segment.")
        
        elif trait_combo == 'products_deposits':
            key_behaviors.append(f"{segment_identifier} diversified: {avg_products:.1f} products with ${avg_deposits:,.0f} deposits ({products_rank:.0f}th products, {deposit_rank:.0f}th deposits)")
            key_behaviors.append(f"{segment_identifier} engagement: Age {avg_age:.0f}, ${avg_income:,.0f} income, {avg_transactions:.0f} transactions, {avg_digital*100:.0f}% digital, {avg_cross_sell*100:.0f}% receptive")
            marketing_recommendations.append(f"Offer relationship-based rewards (e.g. fee waivers, preferred rates) for customers with {avg_products:.0f}+ products and high consolidated balances; communicate via preferred channel.")
            marketing_recommendations.append(f"Propose a dedicated relationship manager or premium tier for this segment; use a warm outbound campaign tied to their current product mix.")
            marketing_recommendations.append(f"Run a retention and next-best-action campaign: highlight benefits of current products and suggest one complementary product (e.g. investment or insurance).")
        
        elif trait_combo == 'products_digital':
            key_behaviors.append(f"Digital portfolio managers: {avg_products:.1f} products all managed via {avg_digital*100:.0f}% digital channels")
            key_behaviors.append(f"Use mobile app to monitor multiple accounts, investments, and loans simultaneously")
            marketing_recommendations.append(f"Launch and promote a consolidated digital dashboard for this segment; use in-app messaging to cross-sell one additional product that fits their portfolio.")
            marketing_recommendations.append(f"Offer automated transfers and smart savings rules in the app; bundle with a high-value product (e.g. savings or investment) and run an in-app campaign.")
            marketing_recommendations.append(f"Create a segment-specific campaign highlighting multi-product benefits (e.g. fee waivers, single view) and invite them to exclusive digital events.")
        
        elif trait_combo == 'products_transactions':
            key_behaviors.append(f"{segment_identifier} power users: {avg_products:.1f} products, {avg_transactions:.0f} transactions ({products_rank:.0f}th products, {trans_rank:.0f}th activity)")
            key_behaviors.append(f"{segment_identifier} profile: Age {avg_age:.0f}, ${avg_income:,.0f} income, ${avg_deposits:,.0f} deposits, {avg_digital*100:.0f}% digital")
            marketing_recommendations.append(f"Create an activity-based rewards program (e.g. cashback or tier benefits) for customers with high transaction volume and multiple products; promote in-app and email.")
            marketing_recommendations.append(f"Offer a premium tier (e.g. free wire transfers, concierge) unlocked by transaction and product thresholds; target this segment with a dedicated campaign.")
            marketing_recommendations.append(f"Run a campaign promoting convenience products (e.g. premium checking, payment solutions) that match this segment's high usage and multi-product profile.")
        
        elif trait_combo == 'products_cross_sell':
            key_behaviors.append(f"{segment_identifier} expansion ready: {avg_products:.1f} products, {avg_cross_sell*100:.0f}% receptive ({products_rank:.0f}th products, {cross_rank:.0f}th receptivity)")
            key_behaviors.append(f"{segment_identifier} base: Age {avg_age:.0f}, ${avg_income:,.0f} income, ${avg_deposits:,.0f} deposits, {avg_transactions:.0f} transactions, {avg_digital*100:.0f}% digital")
            marketing_recommendations.append(f"Execute a structured cross-sell campaign: recommend the next best product (e.g. credit, investment, or insurance) based on current {avg_products:.0f} products; use sales or automated triggers.")
            marketing_recommendations.append(f"Offer bundle discounts or package pricing for adding one more product; target this segment with personalized messaging and a clear CTA.")
            marketing_recommendations.append(f"Assign outbound or in-app follow-up to high-receptivity customers in this segment; prioritize those with room to grow product count.")
        
        elif trait_combo == 'transactions_deposits':
            key_behaviors.append(f"{segment_identifier} high-touch: {avg_transactions:.0f} transactions with ${avg_deposits:,.0f} deposits ({trans_rank:.0f}th activity, {deposit_rank:.0f}th wealth)")
            key_behaviors.append(f"{segment_identifier} details: Age {avg_age:.0f}, ${avg_income:,.0f} income, {avg_products:.1f} products, {avg_digital*100:.0f}% digital, {avg_cross_sell*100:.0f}% receptive")
            marketing_recommendations.append(f"Offer an unlimited-transactions or premium checking tier for high-balance, high-activity customers; use a direct mail or outbound campaign.")
            marketing_recommendations.append(f"Propose dedicated support or a relationship manager for this segment; highlight convenience and recognition in all touchpoints.")
            marketing_recommendations.append(f"Run a campaign promoting wealth or cash-management features (e.g. sweep, higher limits) that match this segment's transaction and balance profile.")
        
        elif trait_combo == 'transactions_digital':
            key_behaviors.append(f"{segment_identifier} app leaders: {avg_transactions:.0f} transactions at {avg_digital*100:.0f}% digital ({trans_rank:.0f}th activity, {digital_rank:.0f}th digital)")
            key_behaviors.append(f"{segment_identifier} demographics: Age {avg_age:.0f}, ${avg_income:,.0f} income, ${avg_deposits:,.0f} deposits, {avg_products:.1f} products")
            marketing_recommendations.append(f"Launch a digital-only rewards tier (e.g. cashback, points) for high-transaction app users; promote in-app and via push notifications.")
            marketing_recommendations.append(f"Invite this segment to beta features or new app capabilities; use feedback to refine and then roll out next-product offers.")
            marketing_recommendations.append(f"Run an in-app campaign for payment or credit products that fit high transaction volume and digital-first behavior.")
        
        elif trait_combo == 'transactions_products':
            key_behaviors.append(f"Power portfolio users: {avg_transactions:.0f} transactions ({trans_rank:.0f}th) across {avg_products:.1f} products ({products_rank:.0f}th)")
            key_behaviors.append(f"${avg_deposits:,.0f} deposits with {avg_digital*100:.0f}% digital, age {avg_age:.0f}, income ${avg_income:,.0f}")
            marketing_recommendations.append(f"Create a VIP or premium tier for customers with high transaction volume and multiple products; offer fee waivers, priority service, or exclusive benefits.")
            marketing_recommendations.append(f"Run a recognition campaign (e.g. thank-you offers, referral incentives) for this segment; use it to introduce one more high-value product.")
            marketing_recommendations.append(f"Propose a consolidated view and premium service package that rewards both activity and product depth; target via preferred channel.")
        
        elif trait_combo == 'transactions_cross_sell':
            key_behaviors.append(f"{segment_identifier} active receptive: {avg_transactions:.0f} transactions, {avg_cross_sell*100:.0f}% receptive ({trans_rank:.0f}th activity, {cross_rank:.0f}th receptivity)")
            key_behaviors.append(f"{segment_identifier} state: Age {avg_age:.0f}, ${avg_income:,.0f} income, ${avg_deposits:,.0f} deposits, {avg_products:.1f} products, {avg_digital*100:.0f}% digital")
            marketing_recommendations.append(f"Time a cross-sell campaign to peak transaction periods; offer one relevant product (e.g. credit, savings) with a clear, low-friction CTA.")
            marketing_recommendations.append(f"Use behavioral triggers (e.g. after N transactions or login) to show personalized in-app or email offers for this receptive segment.")
            marketing_recommendations.append(f"Assign sales or retargeting to high-activity, high-receptivity customers; test incentive (e.g. bonus rate or waiver) to convert.")
        
        elif trait_combo == 'cross_sell_deposits':
            key_behaviors.append(f"{segment_identifier} affluent receptive: {avg_cross_sell*100:.0f}% openness with ${avg_deposits:,.0f} wealth ({cross_rank:.0f}th receptivity, {deposit_rank:.0f}th wealth)")
            key_behaviors.append(f"{segment_identifier} status: Age {avg_age:.0f}, ${avg_income:,.0f} income, {avg_products:.1f} products, {avg_transactions:.0f} transactions, {avg_digital*100:.0f}% digital")
            marketing_recommendations.append(f"Proactively offer wealth-advisory or private-banking introduction for high-balance, high-receptivity customers; book discovery meetings.")
            marketing_recommendations.append(f"Run a premium product campaign (e.g. investment, insurance, or lending) for this segment; use personalized outreach and preferred channel.")
            marketing_recommendations.append(f"Create an affluent segment program (e.g. exclusive rates, dedicated contact) and invite this segment with a clear next-step offer.")
        
        elif trait_combo == 'cross_sell_digital':
            key_behaviors.append(f"{segment_identifier} digital growth: {avg_cross_sell*100:.0f}% receptive at {avg_digital*100:.0f}% digital ({cross_rank:.0f}th receptivity, {digital_rank:.0f}th digital)")
            key_behaviors.append(f"{segment_identifier} metrics: Age {avg_age:.0f}, ${avg_income:,.0f} income, ${avg_deposits:,.0f} deposits, {avg_products:.1f} products, {avg_transactions:.0f} transactions")
            marketing_recommendations.append(f"Deploy in-app and email offers with instant-apply or one-tap flow for this digital, receptive segment; prioritize one next-best product per customer.")
            marketing_recommendations.append(f"Run a short A/B test of product offers (e.g. credit, savings) in the app; use segment behavior to tailor messaging and placement.")
            marketing_recommendations.append(f"Follow up high-intent in-app actions with a light-touch call or chat to convert; keep messaging consistent with digital experience.")
        
        elif trait_combo == 'cross_sell_products':
            key_behaviors.append(f"Portfolio expanders: {avg_cross_sell*100:.0f}% receptive with {avg_products:.1f} products seeking more ({products_rank:.0f}th percentile)")
            key_behaviors.append(f"${avg_deposits:,.0f} deposits, {avg_transactions:.0f} transactions, age {avg_age:.0f} wanting product expansion")
            marketing_recommendations.append(f"Run an ecosystem expansion campaign: recommend the next best product (e.g. investment, insurance) that complements current {avg_products:.0f} products; use sales or triggered outreach.")
            marketing_recommendations.append(f"Create synergy messaging that links existing products to one new offering (e.g. 'Add savings to your checking'); target this segment with clear benefit and CTA.")
            marketing_recommendations.append(f"Assign a cross-sell playbook for this segment: prioritize one product per customer and measure conversion; iterate on offer and channel.")
        
        elif trait_combo == 'cross_sell_transactions':
            key_behaviors.append(f"{segment_identifier} active prospects: {avg_cross_sell*100:.0f}% receptive with {avg_transactions:.0f} transactions ({cross_rank:.0f}th receptivity, {trans_rank:.0f}th activity)")
            key_behaviors.append(f"{segment_identifier} snapshot: Age {avg_age:.0f}, ${avg_income:,.0f} income, ${avg_deposits:,.0f} deposits, {avg_products:.1f} products, {avg_digital*100:.0f}% digital")
            marketing_recommendations.append(f"Time offers to high-activity periods; run a campaign promoting one product (e.g. credit or savings) with a limited-time incentive for this receptive segment.")
            marketing_recommendations.append(f"Use transaction or login triggers to show personalized next-product offers in-app or via email; test incentive (e.g. bonus or waiver) to improve conversion.")
            marketing_recommendations.append(f"Assign outbound or retargeting to high-activity, high-receptivity customers; use a clear single-product offer and measure by segment.")
        
        # DEFAULT CATCH-ALL for any other combinations
        else:
            key_behaviors.append(f"{segment_identifier} balanced profile: {primary_trait} strength at {primary_rank:.0f}th percentile, {secondary_trait} at {secondary_rank:.0f}th")
            key_behaviors.append(f"{segment_identifier} specifics: Age {avg_age:.0f}, ${avg_income:,.0f} income, ${avg_deposits:,.0f} deposits, {avg_products:.1f} products, {avg_transactions:.0f} transactions")
            marketing_recommendations.append(f"Design a segment-specific campaign that leads with {primary_trait} (e.g. product, channel, or benefit); include a single clear next-step offer.")
            marketing_recommendations.append(f"Test one targeted action: either outbound for high-value customers or in-app/email for digital-first; measure conversion and refine by sub-cohort.")
            marketing_recommendations.append(f"Offer education or value content (e.g. how-to, tips) tied to {secondary_trait}, then follow with a soft product or service recommendation.")
        
        # Add SPECIFIC metrics to make each segment even more unique
        if avg_age < 35:
            key_behaviors.append(f"Young demographic (avg age {avg_age:.0f}) with long growth runway and evolving financial needs")
        elif avg_age > 60:
            key_behaviors.append(f"Mature customers (avg age {avg_age:.0f}) focused on wealth preservation and income generation")
        
        # Add income-specific behavior if notable
        if avg_income > 150000:
            key_behaviors.append(f"High income earners (${avg_income:,.0f}/year) with capacity for premium product adoption")
        elif avg_income < 50000:
            key_behaviors.append(f"Value-conscious customers (${avg_income:,.0f}/year) seeking fee-free and high-value banking")
        
        # Limit to most important insights
        key_behaviors = key_behaviors[:4]
        marketing_recommendations = marketing_recommendations[:4]
        
        # UNIQUE marketing opportunities: try LLM first, else personalize fallback so no two segments are identical
        metrics_for_llm = {
            'avg_deposits': avg_deposits,
            'avg_income': avg_income,
            'avg_digital': avg_digital,
            'avg_products': avg_products,
            'avg_transactions': avg_transactions,
            'avg_cross_sell': avg_cross_sell,
            'avg_age': avg_age,
        }
        segment_def_text = "\n".join(segment_definition)
        used_llm_recs = False
        if TOGETHER_AI_AVAILABLE and together_ai and os.getenv("TOGETHER_API_KEY"):
            try:
                llm_recs = together_ai.generate_marketing_opportunities(
                    persona_name=persona_name,
                    segment_definition=segment_def_text,
                    key_behaviors=key_behaviors,
                    metrics=metrics_for_llm
                )
                if llm_recs and len(llm_recs) >= 3:
                    marketing_recommendations = llm_recs[:4]
                    used_llm_recs = True
            except Exception as e:
                logger.debug(f"LLM marketing opportunities failed for {persona_name}, using personalized fallback: {e}")
        # Fallback: short prefix with segment metrics so each segment looks different; one full clause, no mid-phrase cuts
        if not used_llm_recs:
            short_recs = []
            prefix = f"**{persona_name}** (${avg_deposits/1e6:.1f}M, {avg_digital*100:.0f}% digital): "
            for r in marketing_recommendations:
                if ";" in r:
                    s = r.split(";")[0].strip()
                    s = s + "." if s and not s.endswith(".") else s
                else:
                    s = r.split(".")[0].strip() + "." if "." in r else r
                if len(s) > 130:
                    s = (s[:127].rsplit(" ", 1)[0] or s[:127]) + "..."
                short_recs.append(prefix + s)
            marketing_recommendations = short_recs
        
        # Generate name explanation for macro segment
        name_explanation = self._generate_macro_name_explanation(
            persona_name=persona_name,
            avg_deposits=avg_deposits,
            avg_digital=avg_digital,
            avg_products=avg_products,
            avg_transactions=avg_transactions,
            primary_trait=primary_trait,
            primary_rank=primary_rank
        )
        
        return {
            'name_explanation': name_explanation,  # NEW: Explains why this name
            'segment_definition': segment_def_text,
            'key_behaviors': key_behaviors,
            'marketing_recommendations': marketing_recommendations
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
    
    def get_all_customers(self, skip=0, limit=50, persona_filter=None, search_query=None):
        """Get paginated list of customers with persona assignments"""
        if self.customers_df is None:
            raise ValueError("No customer data loaded. Run execute() first.")
        
        df = self.customers_df.copy()
        
        # Apply filters
        if persona_filter:
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
            cluster_id = row['cluster']
            persona = self.personas.get(cluster_id, {})
            
            customers.append({
                'customer_id': row['customer_id'],
                'customer_name': row['customer_name'],
                'persona': persona.get('persona_name', 'Unknown'),
                'persona_short': persona.get('short_name', 'Unknown'),
                'cluster_id': int(cluster_id),
                'total_deposits': float(row['total_deposits']),
                'num_products': int(row['num_products']),
                'digital_engagement': float(row['digital_engagement_score'])
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
        cluster_id = customer['cluster']
        persona = self.personas.get(cluster_id, {})
        
        return {
            'customer_id': customer_id,
            'customer_name': customer['customer_name'],
            'persona': persona.get('persona_name', 'Unknown'),
            'cluster_id': int(cluster_id),
            'metrics': {
                'total_deposits': float(customer['total_deposits']),
                'income': float(customer['income']),
                'credit_score': float(customer['credit_score']),
                'num_products': int(customer['num_products']),
                'digital_engagement': float(customer['digital_engagement_score']),
                'cross_sell_receptivity': float(customer['cross_sell_receptivity'])
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

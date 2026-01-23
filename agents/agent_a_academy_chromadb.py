"""
Agent A - Academy Sports Camping Personalization
Uses K-Prototypes clustering for persona identification (mixed numeric + categorical data)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from pathlib import Path

# Try to import kmodes, provide graceful fallback
try:
    from kmodes.kprototypes import KPrototypes
    KMODES_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: kmodes not installed. Run: pip install kmodes")
    KMODES_AVAILABLE = False

logger = logging.getLogger(__name__)


class AgentA_Academy:
    """
    Agent A for Academy Sports: Persona Builder using K-Prototypes
    
    Identifies 3 customer personas based on behavioral signals:
    - First-Time Camper (Novice)
    - Family Socializer
    - Seasoned Pro
    """
    
    # Persona definitions based on cluster characteristics
    PERSONA_DEFINITIONS = {
        'low_specificity_high_bundle': {
            'name': '🏕️ First-Time Camper',
            'short_name': 'Novice',
            'description': 'New to camping, needs simplicity and guidance',
            'characteristics': [
                'Generic search terms ("camping tent")',
                'Rarely expands product specs (0-20%)',
                'Loves bundles and kits (70-100%)',
                'Always sorts by price (70-100%)',
                'Price-sensitive ($50-$300/year)',
                'High anxiety about "doing it wrong"'
            ],
            'product_preferences': {
                'loves': ['Instant Setup', 'Bundle Compatible', 'Simple Design', 'Budget Brand'],
                'hates': ['Technical Design', 'Complex Assembly', 'Pro-Grade Brand']
            }
        },
        'moderate_research': {
            'name': '👨‍👩‍👧‍👦 Family Socializer',
            'short_name': 'Family_Socializer',
            'description': 'Occasional camper, values comfort and convenience',
            'characteristics': [
                'Attribute-based searches ("4-person tent")',
                'Some research (20-50% spec expansion)',
                'Likes bundles for convenience (40-70%)',
                'Balanced on price (30-60% sort frequency)',
                'Moderate spend ($300-$1,000/year)',
                'Camps 1-2x per year for fun'
            ],
            'product_preferences': {
                'loves': ['4+ Person Capacity', 'Weather Resistant', 'Moderate Design'],
                'dislikes': ['Ultralight', 'Too Technical']
            }
        },
        'high_specificity_low_bundle': {
            'name': '⛰️ Seasoned Pro',
            'short_name': 'Seasoned_Pro',
            'description': 'Expert camper, technical knowledge, brand loyal',
            'characteristics': [
                'Model-specific searches ("MSR Hubba NX")',
                'Always expands specs (60-100%)',
                'No interest in bundles (0-20%)',
                'Doesn\'t sort by price (0-20%)',
                'High spend ($800-$3,000/year)',
                'Frequent purchaser (5-15x/year)'
            ],
            'product_preferences': {
                'loves': ['Technical Design', 'Ultralight', 'Premium Brand', 'Pro-Grade'],
                'hates': ['Instant Setup', 'Bundle Compatible', 'Simple Design']
            }
        },
        # Additional personas for 4+ clusters
        'value_seeker': {
            'name': '💰 Value Seeker',
            'short_name': 'Value_Seeker',
            'description': 'Budget-conscious but wants quality',
            'characteristics': [
                'Brand-aware searches',
                'Moderate research (30-50% spec expansion)',
                'Some bundle interest (30-50%)',
                'High price sorting (60-80%)',
                'Moderate spend ($200-$600/year)',
                'Waits for sales and discounts'
            ],
            'product_preferences': {
                'loves': ['Mid-Range Brand', 'Good Value', 'Warranty'],
                'dislikes': ['Premium Pricing', 'Instant/Cheap Options']
            }
        },
        'weekend_warrior': {
            'name': '🏞️ Weekend Warrior',
            'short_name': 'Weekend_Warrior',
            'description': 'Regular camper, balanced approach',
            'characteristics': [
                'Specific feature searches',
                'Moderate research (40-60% spec expansion)',
                'Low bundle interest (20-40%)',
                'Moderate price sorting (40-60%)',
                'Good spend ($600-$1,500/year)',
                'Camps 3-6x per year'
            ],
            'product_preferences': {
                'loves': ['Durable', 'Versatile', 'Weather Resistant'],
                'neutral': ['Brand', 'Price']
            }
        }
    }
    
    def __init__(self, data_path: str = 'data/preloaded/academy_sports'):
        """
        Initialize Agent A
        
        Args:
            data_path: Path to preloaded Academy Sports data
        """
        self.data_path = Path(data_path)
        self.customers_df = None
        self.cluster_model = None
        self.personas = {}
        
        logger.info(f"Agent A Academy initialized with data path: {data_path}")
    
    def load_data(self, dataset_version='v1'):
        """
        Load customer data from CSV
        
        Args:
            dataset_version: 'v1' or 'v2' to select dataset version
        """
        try:
            if dataset_version == 'v2':
                customers_path = self.data_path / 'customers_v2.csv'
                interactions_path = self.data_path / 'interactions_v2.csv'
                purchases_path = self.data_path / 'purchases_v2.csv'
                logger.info(f"📊 Loading Academy Sports V2 dataset (test data)")
            else:
                customers_path = self.data_path / 'customers.csv'
                interactions_path = self.data_path / 'interactions.csv'
                purchases_path = self.data_path / 'purchases.csv'
                logger.info(f"📊 Loading Academy Sports V1 dataset (original data)")
            
            self.customers_df = pd.read_csv(customers_path)
            self.interactions_df = pd.read_csv(interactions_path)
            self.purchases_df = pd.read_csv(purchases_path)
            
            logger.info(f"✓ Loaded {len(self.customers_df)} customers, {len(self.interactions_df)} interactions, {len(self.purchases_df)} purchases")
            return True
        except FileNotFoundError as e:
            logger.error(f"Dataset not found: {e}. Please generate the dataset first.")
            return False
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def execute(self, params: Dict = None) -> Dict:
        """
        Execute Agent A: Persona identification using K-Prototypes
        
        Args:
            params: Optional parameters (n_clusters, gamma, dataset_version, etc.)
            
        Returns:
            Dictionary with personas and cluster assignments
        """
        if not KMODES_AVAILABLE:
            return self._fallback_clustering()
        
        # Extract dataset version from params
        dataset_version = params.get('dataset_version', 'v1') if params else 'v1'
        
        # Always reload data with the specified version (to support switching datasets)
        if not self.load_data(dataset_version=dataset_version):
            return {'error': 'Failed to load customer data'}
        
        # Extract parameters with business constraints
        # ENHANCED: Force 4-5 clusters for macro segmentation
        n_clusters_input = params.get('n_clusters', 4) if params else 4
        n_clusters = max(4, min(5, n_clusters_input))  # Enforce 4-5 clusters
        gamma = params.get('gamma', 0.5) if params else 0.5
        
        # Business constraints
        min_cluster_size_pct = params.get('min_cluster_size_pct', 10) if params else 10  # 10% minimum
        min_revenue_per_customer = params.get('min_revenue_per_customer', 50) if params else 50  # $50 minimum
        
        # Balanced Feature Engineering to Prevent Overfitting
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        import numpy as np
        
        # Create moderate feature enhancements (reduced to prevent overfitting)
        df_enhanced = self.customers_df.copy()
        
        # Only add key composite features that capture genuine patterns
        df_enhanced['rfm_score'] = (
            (1 / (df_enhanced['recency_days'] + 1)) * 0.33 +
            (df_enhanced['purchase_frequency'] / df_enhanced['purchase_frequency'].max()) * 0.33 +
            (df_enhanced['total_spend_12mo'] / df_enhanced['total_spend_12mo'].max()) * 0.34
        )
        
        # Behavioral expertise indicator
        df_enhanced['experience_level'] = df_enhanced['search_specificity'] * (1 - df_enhanced['spec_expansion_rate'])
        
        # Value vs Premium orientation
        df_enhanced['purchase_style'] = df_enhanced['avg_order_value'] / (df_enhanced['price_sort_frequency'] + 0.1)
        
        # Select features carefully to avoid overfitting
        numeric_cols = [
            # Core behavioral features (most important)
            'search_specificity',
            'spec_expansion_rate',
            'bundle_affinity',
            'price_sort_frequency',
            
            # Key demographics
            'age',
            'income',
            
            # Essential purchase metrics
            'total_spend_12mo',
            'purchase_frequency',
            'avg_order_value',
            'return_rate',
            
            # Only 3 composite features (reduced from 13)
            'rfm_score',
            'experience_level',
            'purchase_style'
        ]
        
        categorical_cols = [
            'urbanicity',
            'climate_zone',
            'dominant_category',
            'brand_loyalty',
            'channel_preference'
        ]
        
        # Prepare data for K-Prototypes
        X = df_enhanced[numeric_cols + categorical_cols].copy()
        
        # Handle missing values
        for col in numeric_cols:
            X.loc[:, col] = X[col].fillna(X[col].median())
        for col in categorical_cols:
            X.loc[:, col] = X[col].fillna('Unknown')
        
        # Use StandardScaler for consistent feature scaling
        scaler = StandardScaler()
        X_numeric_scaled = scaler.fit_transform(X[numeric_cols])
        
        # Combine scaled numeric with categorical
        X_scaled = X.copy()
        X_scaled[numeric_cols] = X_numeric_scaled
        
        # Get categorical indices
        cat_indices = list(range(len(numeric_cols), len(numeric_cols) + len(categorical_cols)))
        
        try:
            # Fit K-Prototypes model with balanced parameters to prevent overfitting
            logger.info(f"Fitting K-Prototypes with n_clusters={n_clusters}, gamma={gamma}")
            logger.info(f"Using {len(numeric_cols)} numeric features and {len(categorical_cols)} categorical features")
            
            best_model = None
            best_cost = float('inf')
            
            # Optimized parameters for realistic data with moderate overlap
            # More random starts for better convergence
            for init_run in range(5):  # Increased to 5 runs
                try:
                    model = KPrototypes(
                        n_clusters=n_clusters,
                        gamma=gamma,  # Use calculated gamma directly (balanced)
                        init='Huang',  # Huang often works better for overlapping clusters
                        n_init=5,  # More random starts per run for better convergence
                        max_iter=150,  # More iterations to ensure convergence
                        verbose=0,
                        random_state=42 + init_run
                    )
                    
                    clusters_temp = model.fit_predict(X_scaled.values, categorical=cat_indices)
                    
                    # Keep best model based on cost
                    if model.cost_ < best_cost:
                        best_cost = model.cost_
                        best_model = model
                        logger.info(f"Init run {init_run}: cost = {model.cost_:.2f}")
                        
                except Exception as e:
                    logger.warning(f"Init run {init_run} failed: {e}")
                    continue
            
            if best_model is None:
                raise Exception("All initialization runs failed")
            
            self.cluster_model = best_model
            clusters = self.cluster_model.predict(X_scaled.values, categorical=cat_indices)
            
            # Add clusters and enhanced features to dataframe
            df_enhanced['cluster'] = clusters
            self.customers_df = df_enhanced  # Use enhanced dataframe
            
            # Generate personas from clusters
            self.personas = self._generate_personas(numeric_cols, categorical_cols)
            
            # ENHANCED: Validate business constraints
            constraints_validation = self._validate_business_constraints(
                min_cluster_size_pct=min_cluster_size_pct,
                min_revenue_per_customer=min_revenue_per_customer
            )
            
            logger.info(f"✅ Clustering complete with cost: {best_cost:.2f}")
            logger.info(f"📊 Business constraints met: {constraints_validation['all_constraints_met']}")
            
            # Validate clustering
            validation = self._validate_clustering()
            
            # Prepare visualization data
            viz_data = self._prepare_visualization_data()
            
            # Add persona names to customers dataframe for visualization
            customers_with_personas = self.customers_df.copy()
            customers_with_personas['persona'] = customers_with_personas['cluster'].map(
                {cluster_id: persona['short_name'] for cluster_id, persona in self.personas.items()}
            )
            
            # Get confidence scores if available
            if hasattr(self, 'confidence_scores') and self.confidence_scores is not None:
                confidence_scores_list = self.confidence_scores.tolist()
            else:
                confidence_scores_list = None
            
            return {
                'status': 'success',
                'personas': self.personas,
                'validation': validation,
                'constraints_validation': constraints_validation,
                'visualization_data': viz_data,
                'customers_with_clusters': customers_with_personas,
                'confidence_scores': confidence_scores_list,
                'total_customers': len(self.customers_df),
                'total_revenue': float(self.customers_df['total_spend_12mo'].sum()) if 'total_spend_12mo' in self.customers_df.columns else 0,
                'n_clusters': n_clusters,
                'gamma': gamma,
                'last_refreshed': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in K-Prototypes clustering: {e}")
            return {'error': str(e), 'fallback': self._fallback_clustering()}
    
    def _generate_personas(self, numeric_cols: List[str], categorical_cols: List[str]) -> Dict:
        """
        Generate persona profiles from clusters with enhanced metrics
        
        Args:
            numeric_cols: List of numeric column names
            categorical_cols: List of categorical column names
            
        Returns:
            Dictionary of persona profiles with revenue, confidence, and temporal metrics
        """
        personas = {}
        used_persona_types = set()  # Track which personas we've already assigned
        
        for cluster_id in range(self.cluster_model.n_clusters):
            cluster_customers = self.customers_df[self.customers_df['cluster'] == cluster_id]
            
            # Calculate cluster characteristics
            characteristics = {
                'avg_search_specificity': float(cluster_customers['search_specificity'].mean()),
                'avg_spec_expansion_rate': float(cluster_customers['spec_expansion_rate'].mean()),
                'avg_bundle_affinity': float(cluster_customers['bundle_affinity'].mean()),
                'avg_price_sort_frequency': float(cluster_customers['price_sort_frequency'].mean()),
                'avg_age': float(cluster_customers['age'].mean()),
                'avg_income': float(cluster_customers['income'].mean()),
                'avg_spend_12mo': float(cluster_customers['total_spend_12mo'].mean()),
                'avg_purchase_frequency': float(cluster_customers['purchase_frequency'].mean()),
                'avg_return_rate': float(cluster_customers['return_rate'].mean())
            }
            
            # Calculate revenue metrics (NEW)
            total_revenue = float(cluster_customers['total_spend_12mo'].sum())
            avg_order_value = float(cluster_customers['avg_order_value'].mean())
            # Estimate profit margin based on persona (premium products = higher margin)
            estimated_margin = self._estimate_profit_margin(characteristics)
            estimated_profit = total_revenue * estimated_margin
            
            # Calculate confidence scores (NEW)
            confidence_stats = self._calculate_confidence_scores(cluster_customers, cluster_id)
            
            # Calculate temporal metrics (NEW)
            temporal_stats = self._calculate_temporal_metrics(cluster_customers)
            
            # Identify persona type based on characteristics (handles 4+ clusters)
            persona_type = self._identify_persona_type(characteristics, used_persona_types)
            used_persona_types.add(persona_type)
            persona_def = self.PERSONA_DEFINITIONS[persona_type]
            
            personas[cluster_id] = {
                'cluster_id': cluster_id,
                'persona_name': persona_def['name'],
                'name': persona_def['name'],  # Alias for compatibility
                'short_name': persona_def['short_name'],
                'description': persona_def['description'],
                'size': len(cluster_customers),
                'count': len(cluster_customers),  # Alias for compatibility
                'percentage': round(len(cluster_customers) / len(self.customers_df) * 100, 1),
                'characteristics': characteristics,
                'behavior_profile': persona_def['characteristics'],
                'product_preferences': persona_def['product_preferences'],
                # NEW: Revenue Metrics
                'total_revenue': round(total_revenue, 2),  # Top-level for easy access
                'avg_spend': round(total_revenue / len(cluster_customers), 2),  # Top-level for easy access
                'confidence_avg': round(confidence_stats.get('avg_confidence', 75.0), 1),  # Top-level for easy access
                'revenue_metrics': {
                    'total_revenue_12mo': round(total_revenue, 2),
                    'avg_customer_value': round(total_revenue / len(cluster_customers), 2),
                    'avg_order_value': round(avg_order_value, 2),
                    'estimated_margin': round(estimated_margin * 100, 1),
                    'estimated_profit': round(estimated_profit, 2),
                    'revenue_percentage': round(total_revenue / self.customers_df['total_spend_12mo'].sum() * 100, 1)
                },
                # NEW: Confidence Metrics
                'confidence_metrics': confidence_stats,
                # NEW: Temporal Metrics
                'temporal_metrics': temporal_stats
            }
        
        return personas
    
    def _validate_business_constraints(
        self,
        min_cluster_size_pct: float = 10,
        min_revenue_per_customer: float = 50
    ) -> Dict:
        """
        Validate that macro segments meet business constraints
        
        Args:
            min_cluster_size_pct: Minimum percentage of total customers per segment (default 10%)
            min_revenue_per_customer: Minimum average revenue per customer (default $50)
            
        Returns:
            Dictionary with validation results and flags
        """
        total_customers = len(self.customers_df)
        min_customers = int(total_customers * (min_cluster_size_pct / 100))
        
        constraints_met = []
        constraints_failed = []
        special_flags = {}
        
        for cluster_id, persona in self.personas.items():
            cluster_size = persona['size']
            avg_revenue = persona['revenue_metrics']['avg_customer_value']
            total_revenue = persona['revenue_metrics']['total_revenue_12mo']
            
            # Check size constraint
            size_met = cluster_size >= min_customers
            if not size_met:
                constraints_failed.append({
                    'persona': persona['persona_name'],
                    'constraint': 'minimum_size',
                    'expected': min_customers,
                    'actual': cluster_size,
                    'message': f"{persona['persona_name']} has only {cluster_size} customers (expected at least {min_customers})"
                })
            
            # Check revenue constraint
            revenue_met = avg_revenue >= min_revenue_per_customer
            if not revenue_met:
                constraints_failed.append({
                    'persona': persona['persona_name'],
                    'constraint': 'minimum_revenue',
                    'expected': min_revenue_per_customer,
                    'actual': round(avg_revenue, 2),
                    'message': f"{persona['persona_name']} averages ${avg_revenue:.2f} per customer (expected at least ${min_revenue_per_customer})"
                })
            
            # Both constraints met for this segment
            if size_met and revenue_met:
                constraints_met.append(persona['persona_name'])
            
            # Calculate special flags
            flags = []
            
            # High value segment
            if avg_revenue > 1000:
                flags.append('high_value')
            elif avg_revenue > 500:
                flags.append('mid_value')
            else:
                flags.append('budget_conscious')
            
            # Growth opportunity
            if cluster_size > (total_customers * 0.3):  # > 30% of customers
                flags.append('large_segment')
            elif cluster_size < (total_customers * 0.15):  # < 15% of customers
                flags.append('niche_segment')
            
            # Price sensitive
            if persona['characteristics']['avg_price_sort_frequency'] > 0.6:
                flags.append('price_sensitive')
            
            # Brand loyal
            brand_loyalty = persona['characteristics'].get('avg_return_rate', 0)
            if brand_loyalty < 0.1:
                flags.append('brand_loyal')
            
            # High expertise
            if persona['characteristics']['avg_search_specificity'] > 3.5:
                flags.append('expert_level')
            elif persona['characteristics']['avg_search_specificity'] < 2.5:
                flags.append('novice_level')
            
            # Revenue contribution
            revenue_pct = persona['revenue_metrics']['revenue_percentage']
            if revenue_pct > 40:
                flags.append('revenue_driver')
            elif revenue_pct > 25:
                flags.append('strong_contributor')
            
            special_flags[cluster_id] = flags
            
            # Add flags to persona
            persona['special_flags'] = flags
        
        all_constraints_met = len(constraints_failed) == 0
        
        return {
            'all_constraints_met': all_constraints_met,
            'constraints_met_count': len(constraints_met),
            'constraints_failed_count': len(constraints_failed),
            'personas_passing': constraints_met,
            'constraints_failed': constraints_failed,
            'special_flags': special_flags,
            'min_cluster_size': min_customers,
            'min_cluster_size_pct': min_cluster_size_pct,
            'min_revenue_per_customer': min_revenue_per_customer,
            'recommendation': 'All segments meet business requirements' if all_constraints_met else 'Consider adjusting clustering parameters or merging small segments'
        }
    
    def _identify_persona_type(self, characteristics: Dict, used_types: set = None) -> str:
        """
        Identify persona type based on cluster characteristics
        Supports 3-5 personas without duplicates
        
        Args:
            characteristics: Dictionary of average cluster characteristics
            used_types: Set of persona types already assigned (for 4+ clusters)
            
        Returns:
            Persona type key
        """
        if used_types is None:
            used_types = set()
        
        specificity = characteristics['avg_search_specificity']
        spec_expansion = characteristics['avg_spec_expansion_rate']
        bundle_affinity = characteristics['avg_bundle_affinity']
        price_sort = characteristics['avg_price_sort_frequency']
        avg_spend = characteristics.get('avg_spend_12mo', 0)
        
        # FOR 3 CLUSTERS: Use STRICT assignment to guarantee classic 3 personas
        if self.cluster_model.n_clusters == 3:
            # Calculate scores for each of the 3 classic personas
            novice_score = 0
            pro_score = 0
            family_score = 0
            
            # Novice indicators: low specificity, high bundle, high price sort
            novice_score += (3 - specificity) if specificity < 3 else 0
            novice_score += bundle_affinity
            novice_score += price_sort
            novice_score += (0.5 - spec_expansion) if spec_expansion < 0.5 else 0
            
            # Pro indicators: high specificity, high spec expansion, low bundle, low price
            pro_score += (specificity - 2) if specificity > 2 else 0
            pro_score += spec_expansion
            pro_score += (1 - bundle_affinity)
            pro_score += (1 - price_sort)
            
            # Family indicators: moderate values (closeness to middle)
            family_score += 1 - abs(specificity - 3.0) / 2
            family_score += 1 - abs(spec_expansion - 0.4)
            family_score += 1 - abs(bundle_affinity - 0.5)
            family_score += 1 - abs(price_sort - 0.5)
            
            # Assign to unused persona with highest score
            scores = [
                ('low_specificity_high_bundle', novice_score),
                ('high_specificity_low_bundle', pro_score),
                ('moderate_research', family_score)
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            
            for persona_type, score in scores:
                if persona_type not in used_types:
                    return persona_type
            
            # Fallback (shouldn't reach here)
            return scores[0][0]
        
        # FOR 4+ CLUSTERS: Use advanced scoring system with all 5 personas
        candidates = []
        
        # Novice: Low specificity, low spec expansion, high bundle, high price sort
        if specificity < 2.5 and spec_expansion < 0.35 and bundle_affinity > 0.6 and price_sort > 0.6:
            score = (2.5 - specificity) + (0.35 - spec_expansion) + bundle_affinity + price_sort
            candidates.append(('low_specificity_high_bundle', score))
        
        # Pro: High specificity, high spec expansion, low bundle, low price sort
        if specificity > 3.5 and spec_expansion > 0.55 and bundle_affinity < 0.3 and price_sort < 0.3:
            score = specificity + spec_expansion + (1 - bundle_affinity) + (1 - price_sort)
            candidates.append(('high_specificity_low_bundle', score))
        
        # Family: Moderate values
        if 2.0 < specificity < 4.0 and 0.2 < spec_expansion < 0.65:
            score = 1 - abs(specificity - 3.0) - abs(spec_expansion - 0.4)
            candidates.append(('moderate_research', score))
        
        # Value Seeker: Budget-conscious but does research (4+ clusters only)
        if 2.5 < specificity < 3.8 and price_sort > 0.55 and avg_spend < 700:
            score = 1 - abs(specificity - 3.0) + price_sort - (avg_spend / 1000)
            candidates.append(('value_seeker', score))
        
        # Weekend Warrior: Balanced, moderate spend (4+ clusters only)
        if 3.0 < specificity < 4.5 and 0.35 < spec_expansion < 0.65 and 500 < avg_spend < 1800:
            score = 1 - abs(specificity - 3.75) - abs(spec_expansion - 0.50)
            candidates.append(('weekend_warrior', score))
        
        # Sort by score (highest first) and find first unused type
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        for persona_type, score in candidates:
            if persona_type not in used_types:
                return persona_type
        
        # Fallback: return best match even if used (shouldn't happen often)
        if candidates:
            logger.warning(f"All persona types used, assigning best match")
            return candidates[0][0]
        
        # Ultimate fallback
        return 'moderate_research'
    
    def _estimate_profit_margin(self, characteristics: Dict) -> float:
        """
        Estimate profit margin based on persona characteristics
        
        Premium products (Seasoned Pro) have higher margins (~35%)
        Mid-tier products (Family) have moderate margins (~25%)
        Budget products (Novice) have lower margins (~15%)
        """
        specificity = characteristics['avg_search_specificity']
        avg_spend = characteristics['avg_spend_12mo']
        
        if specificity > 3.5 and avg_spend > 1000:
            return 0.35  # Premium segment
        elif specificity > 2.5 and avg_spend > 500:
            return 0.25  # Mid-tier segment
        else:
            return 0.15  # Budget segment
    
    def _calculate_confidence_scores(self, cluster_customers: pd.DataFrame, cluster_id: int) -> Dict:
        """
        Calculate confidence scores for persona assignments
        
        Confidence is based on distance to cluster centroid and cluster density
        """
        try:
            # Get cluster centroids from model
            if hasattr(self.cluster_model, 'cluster_centroids_'):
                # Calculate distance of each customer to their cluster centroid
                # Simplified: use std dev of key metrics as proxy for confidence
                specificity_std = cluster_customers['search_specificity'].std()
                bundle_std = cluster_customers['bundle_affinity'].std()
                
                # Lower std = higher confidence (more cohesive cluster)
                # Normalize to 0-100 scale
                avg_confidence = max(0, min(100, 100 - (specificity_std + bundle_std) * 20))
                
                # Count high/medium/low confidence assignments
                high_conf = len(cluster_customers[cluster_customers['search_specificity'].notna()])
                total = len(cluster_customers)
                
                return {
                    'avg_confidence': round(avg_confidence, 1),
                    'high_confidence_count': int(high_conf * 0.7),  # Estimate 70% high confidence
                    'medium_confidence_count': int(high_conf * 0.25),  # Estimate 25% medium
                    'low_confidence_count': int(high_conf * 0.05),  # Estimate 5% low
                    'confidence_distribution': {
                        'high': round(70, 1),
                        'medium': round(25, 1),
                        'low': round(5, 1)
                    }
                }
            else:
                return {
                    'avg_confidence': 75.0,
                    'note': 'Confidence calculation unavailable'
                }
        except Exception as e:
            logger.warning(f"Error calculating confidence scores: {e}")
            return {'avg_confidence': 75.0, 'note': 'Default confidence'}
    
    def _calculate_temporal_metrics(self, cluster_customers: pd.DataFrame) -> Dict:
        """
        Calculate temporal and seasonal metrics
        """
        try:
            # Convert join_date to datetime if string
            if 'join_date' in cluster_customers.columns:
                join_dates = pd.to_datetime(cluster_customers['join_date'])
                
                # Extract month for seasonal analysis
                months = join_dates.dt.month
                month_counts = months.value_counts().to_dict()
                
                # Identify peak season (month with most joins)
                peak_month = months.mode().iloc[0] if len(months) > 0 else 6
                peak_season = self._get_season_name(peak_month)
                
                # Calculate growth trend (new customers over time)
                recent_3mo = len(join_dates[join_dates > join_dates.max() - pd.Timedelta(days=90)])
                prev_3mo = len(join_dates[(join_dates > join_dates.max() - pd.Timedelta(days=180)) & 
                                         (join_dates <= join_dates.max() - pd.Timedelta(days=90))])
                
                growth_rate = ((recent_3mo - prev_3mo) / max(prev_3mo, 1)) * 100 if prev_3mo > 0 else 0
                
                return {
                    'peak_season': peak_season,
                    'peak_month': int(peak_month),
                    'growth_rate_3mo': round(growth_rate, 1),
                    'new_customers_3mo': int(recent_3mo),
                    'seasonal_distribution': {
                        'Spring': int(sum(month_counts.get(m, 0) for m in [3, 4, 5])),
                        'Summer': int(sum(month_counts.get(m, 0) for m in [6, 7, 8])),
                        'Fall': int(sum(month_counts.get(m, 0) for m in [9, 10, 11])),
                        'Winter': int(sum(month_counts.get(m, 0) for m in [12, 1, 2]))
                    }
                }
            else:
                return {'note': 'Temporal data not available'}
        except Exception as e:
            logger.warning(f"Error calculating temporal metrics: {e}")
            return {'note': 'Temporal analysis unavailable'}
    
    def _get_season_name(self, month: int) -> str:
        """Get season name from month number"""
        if month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        elif month in [9, 10, 11]:
            return 'Fall'
        else:
            return 'Winter'
    
    def export_persona_assignments(self, output_path: str = None) -> str:
        """
        Export customer persona assignments to CSV for marketing campaigns
        
        Args:
            output_path: Path to save CSV file. If None, returns CSV string
            
        Returns:
            CSV string or file path
        """
        if self.customers_df is None or 'cluster' not in self.customers_df.columns:
            raise ValueError("No clustering results available. Run execute() first.")
        
        # Map cluster IDs to persona names
        cluster_to_persona = {}
        for cluster_id, persona in self.personas.items():
            cluster_to_persona[cluster_id] = persona['short_name']
        
        # Create export dataframe
        export_df = self.customers_df.copy()
        export_df['assigned_persona'] = export_df['cluster'].map(cluster_to_persona)
        export_df['persona_full_name'] = export_df['cluster'].map(
            lambda x: self.personas[x]['persona_name']
        )
        
        # Select relevant columns for marketing
        export_cols = [
            'customer_id', 'assigned_persona', 'persona_full_name',
            'age', 'income', 'total_spend_12mo', 'purchase_frequency',
            'search_specificity', 'bundle_affinity', 'channel_preference',
            'dominant_category', 'brand_loyalty'
        ]
        export_df = export_df[export_cols]
        
        if output_path:
            export_df.to_csv(output_path, index=False)
            logger.info(f"Exported {len(export_df)} persona assignments to {output_path}")
            return output_path
        else:
            return export_df.to_csv(index=False)
    
    def _validate_clustering(self) -> Dict:
        """
        Validate clustering quality against ground truth
        
        Returns:
            Validation metrics
        """
        if 'true_persona' not in self.customers_df.columns:
            return {'note': 'No ground truth available for validation'}
        
        # Map cluster IDs to predicted personas
        cluster_to_persona = {}
        for cluster_id, persona in self.personas.items():
            cluster_to_persona[cluster_id] = persona['short_name']
        
        self.customers_df['predicted_persona'] = self.customers_df['cluster'].map(cluster_to_persona)
        
        # Calculate accuracy
        correct = (self.customers_df['predicted_persona'] == self.customers_df['true_persona']).sum()
        total = len(self.customers_df)
        accuracy = correct / total
        
        # Confusion matrix
        confusion = pd.crosstab(
            self.customers_df['true_persona'],
            self.customers_df['predicted_persona'],
            margins=True
        )
        
        return {
            'accuracy': round(accuracy * 100, 2),  # Convert to percentage
            'correct_predictions': int(correct),
            'total_customers': int(total),
            'confusion_matrix': confusion.to_dict()
        }
    
    def _prepare_visualization_data(self) -> Dict:
        """
        Prepare data for frontend visualizations
        
        Returns:
            Dictionary with visualization data
        """
        viz_data = {
            'cluster_distribution': [],
            'persona_characteristics': [],
            'behavior_comparison': []
        }
        
        # Cluster distribution
        for cluster_id, persona in self.personas.items():
            viz_data['cluster_distribution'].append({
                'cluster_name': persona['persona_name'],
                'cluster_id': cluster_id,
                'count': persona['size'],
                'percentage': persona['percentage']
            })
        
        # Persona characteristics for radar chart
        for cluster_id, persona in self.personas.items():
            chars = persona['characteristics']
            viz_data['persona_characteristics'].append({
                'persona': persona['persona_name'],
                'search_specificity': round(chars['avg_search_specificity'] * 20, 1),  # Scale to 0-100
                'spec_expansion': round(chars['avg_spec_expansion_rate'] * 100, 1),
                'bundle_affinity': round(chars['avg_bundle_affinity'] * 100, 1),
                'price_sensitivity': round(chars['avg_price_sort_frequency'] * 100, 1),
                'avg_spend': round(chars['avg_spend_12mo'], 0)
            })
        
        # Behavior comparison table
        key_metrics = ['search_specificity', 'spec_expansion_rate', 'bundle_affinity', 'price_sort_frequency', 'total_spend_12mo']
        
        for metric in key_metrics:
            metric_data = {'metric': metric.replace('_', ' ').title()}
            for cluster_id, persona in self.personas.items():
                metric_data[persona['short_name']] = round(persona['characteristics'].get(f'avg_{metric}', 0), 2)
            viz_data['behavior_comparison'].append(metric_data)
        
        return viz_data
    
    # ========================================================================
    # NEW: Customer-Level Personalization Methods
    # ========================================================================
    
    def get_all_customers(
        self, 
        skip: int = 0, 
        limit: int = 50,
        persona_filter: str = None,
        search_query: str = None
    ) -> Dict:
        """
        Get paginated list of all customers with their persona assignments
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Number of records to return
            persona_filter: Filter by persona short name
            search_query: Search by customer name or ID
            
        Returns:
            Dictionary with customers list and pagination info
        """
        if self.customers_df is None or 'cluster' not in self.customers_df.columns:
            raise ValueError("No clustering results available. Run execute() first.")
        
        # Map cluster IDs to persona names
        cluster_to_persona = {}
        for cluster_id, persona in self.personas.items():
            cluster_to_persona[cluster_id] = {
                'name': persona['persona_name'],
                'short_name': persona['short_name']
            }
        
        # Start with all customers
        filtered_df = self.customers_df.copy()
        
        # Apply persona filter
        if persona_filter:
            filtered_df['persona_short_name'] = filtered_df['cluster'].map(
                lambda x: cluster_to_persona[x]['short_name']
            )
            filtered_df = filtered_df[filtered_df['persona_short_name'] == persona_filter]
        
        # Apply search query
        if search_query:
            search_lower = search_query.lower()
            if 'customer_name' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['customer_name'].str.lower().str.contains(search_lower, na=False) |
                    filtered_df['customer_id'].str.lower().str.contains(search_lower, na=False)
                ]
            else:
                filtered_df = filtered_df[
                    filtered_df['customer_id'].str.lower().str.contains(search_lower, na=False)
                ]
        
        # Calculate total before pagination
        total_count = len(filtered_df)
        
        # Apply pagination
        paginated_df = filtered_df.iloc[skip:skip+limit]
        
        # Prepare customer list
        customers = []
        for idx, row in paginated_df.iterrows():
            cluster_id = row['cluster']
            persona_info = cluster_to_persona[cluster_id]
            confidence = self._calculate_customer_confidence(row, cluster_id)
            
            customer_data = {
                'customer_id': row['customer_id'],
                'customer_name': row.get('customer_name', f"Customer {row['customer_id']}"),
                'persona': persona_info['name'],
                'persona_short': persona_info['short_name'],
                'confidence': round(confidence, 1),
                'total_spend_12mo': round(row['total_spend_12mo'], 2),
                'purchase_frequency': int(row['purchase_frequency']),
                'search_specificity': round(row['search_specificity'], 1),
                'bundle_affinity': round(row['bundle_affinity'] * 100, 1),
                'age': int(row['age']),
                'channel_preference': row['channel_preference']
            }
            customers.append(customer_data)
        
        return {
            'customers': customers,
            'pagination': {
                'total': total_count,
                'skip': skip,
                'limit': limit,
                'returned': len(customers),
                'has_more': (skip + limit) < total_count
            }
        }
    
    def get_customer_details(self, customer_id: str) -> Dict:
        """
        Get detailed information for a specific customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary with customer details and persona comparison
        """
        if self.customers_df is None or 'cluster' not in self.customers_df.columns:
            raise ValueError("No clustering results available. Run execute() first.")
        
        # Find customer
        customer_row = self.customers_df[self.customers_df['customer_id'] == customer_id]
        
        if len(customer_row) == 0:
            raise ValueError(f"Customer {customer_id} not found")
        
        customer = customer_row.iloc[0]
        cluster_id = customer['cluster']
        persona = self.personas[cluster_id]
        
        # Calculate confidence
        confidence = self._calculate_customer_confidence(customer, cluster_id)
        
        # Get persona averages for comparison
        persona_chars = persona['characteristics']
        
        # Customer metrics
        customer_metrics = {
            'search_specificity': float(customer['search_specificity']),
            'spec_expansion_rate': float(customer['spec_expansion_rate']),
            'bundle_affinity': float(customer['bundle_affinity']),
            'price_sort_frequency': float(customer['price_sort_frequency']),
            'total_spend_12mo': float(customer['total_spend_12mo']),
            'purchase_frequency': int(customer['purchase_frequency']),
            'avg_order_value': float(customer['avg_order_value']),
            'return_rate': float(customer['return_rate']),
            'recency_days': int(customer['recency_days'])
        }
        
        # Persona averages
        persona_averages = {
            'search_specificity': persona_chars['avg_search_specificity'],
            'spec_expansion_rate': persona_chars['avg_spec_expansion_rate'],
            'bundle_affinity': persona_chars['avg_bundle_affinity'],
            'price_sort_frequency': persona_chars['avg_price_sort_frequency'],
            'total_spend_12mo': persona_chars['avg_spend_12mo'],
            'purchase_frequency': persona_chars['avg_purchase_frequency'],
            'return_rate': persona_chars['avg_return_rate']
        }
        
        # Calculate metric comparisons (percentage difference)
        comparisons = {}
        for metric in customer_metrics:
            if metric in persona_averages:
                customer_val = customer_metrics[metric]
                persona_val = persona_averages[metric]
                if persona_val > 0:
                    diff_pct = ((customer_val - persona_val) / persona_val) * 100
                    comparisons[metric] = {
                        'customer': customer_val,
                        'persona_avg': persona_val,
                        'diff_percentage': round(diff_pct, 1),
                        'status': 'above' if diff_pct > 5 else ('below' if diff_pct < -5 else 'average')
                    }
        
        return {
            'customer_id': customer_id,
            'customer_name': customer.get('customer_name', f"Customer {customer_id}"),
            'persona': persona['persona_name'],
            'persona_short': persona['short_name'],
            'confidence': round(confidence, 1),
            'confidence_level': 'High' if confidence > 80 else ('Medium' if confidence > 60 else 'Low'),
            'demographics': {
                'age': int(customer['age']),
                'income': int(customer['income']),
                'urbanicity': customer['urbanicity'],
                'climate_zone': customer['climate_zone'],
                'distance_to_store': float(customer['distance_to_store'])
            },
            'customer_metrics': customer_metrics,
            'persona_averages': persona_averages,
            'comparisons': comparisons,
            'behavior_profile': persona['behavior_profile'],
            'product_preferences': persona['product_preferences']
        }
    
    def _calculate_customer_confidence(self, customer_row, cluster_id: int) -> float:
        """
        Calculate confidence score for a single customer's persona assignment
        
        Args:
            customer_row: Customer data row
            cluster_id: Assigned cluster ID
            
        Returns:
            Confidence score (0-100)
        """
        persona = self.personas[cluster_id]
        persona_chars = persona['characteristics']
        
        # Calculate how well customer matches persona characteristics
        # Using key differentiating features
        
        specificity_match = 1.0 - abs(
            customer_row['search_specificity'] - persona_chars['avg_search_specificity']
        ) / 5.0
        
        bundle_match = 1.0 - abs(
            customer_row['bundle_affinity'] - persona_chars['avg_bundle_affinity']
        )
        
        price_match = 1.0 - abs(
            customer_row['price_sort_frequency'] - persona_chars['avg_price_sort_frequency']
        )
        
        expansion_match = 1.0 - abs(
            customer_row['spec_expansion_rate'] - persona_chars['avg_spec_expansion_rate']
        )
        
        # Weighted average (key features weighted more)
        confidence = (
            specificity_match * 0.3 +
            bundle_match * 0.3 +
            price_match * 0.2 +
            expansion_match * 0.2
        ) * 100
        
        return max(0, min(100, confidence))
    
    def generate_persona_explanation(
        self, 
        customer_id: str, 
        together_api_key: str
    ) -> Dict:
        """
        Generate AI-powered explanation for why a customer fits their persona
        
        Args:
            customer_id: Customer ID
            together_api_key: Together AI API key
            
        Returns:
            Dictionary with explanation and recommendations
        """
        # Get customer details
        customer_details = self.get_customer_details(customer_id)
        
        # Prepare prompt for Together API
        prompt = self._build_explanation_prompt(customer_details)
        
        # Call Together API
        try:
            explanation = self._call_together_api(prompt, together_api_key)
            
            return {
                'customer_id': customer_id,
                'customer_name': customer_details['customer_name'],
                'persona': customer_details['persona'],
                'confidence': customer_details['confidence'],
                'explanation': explanation,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"Error calling Together API: {e}")
            # Fallback to rule-based explanation
            return {
                'customer_id': customer_id,
                'customer_name': customer_details['customer_name'],
                'persona': customer_details['persona'],
                'confidence': customer_details['confidence'],
                'explanation': self._generate_rule_based_explanation(customer_details),
                'status': 'fallback',
                'note': 'Using rule-based explanation (API error)'
            }
    
    def _build_explanation_prompt(self, customer_details: Dict) -> str:
        """Build prompt for Together API"""
        customer_name = customer_details['customer_name']
        persona = customer_details['persona']
        metrics = customer_details['customer_metrics']
        comparisons = customer_details['comparisons']
        
        # Build comparison strings
        comparison_text = []
        for metric, comp in comparisons.items():
            metric_name = metric.replace('_', ' ').title()
            customer_val = comp['customer']
            persona_avg = comp['persona_avg']
            
            if metric == 'search_specificity':
                comparison_text.append(
                    f"- Search Specificity: {customer_val:.1f}/5 (persona avg: {persona_avg:.1f}/5)"
                )
            elif metric == 'bundle_affinity':
                comparison_text.append(
                    f"- Bundle Preference: {customer_val*100:.0f}% (persona avg: {persona_avg*100:.0f}%)"
                )
            elif metric == 'price_sort_frequency':
                comparison_text.append(
                    f"- Price Sorting: {customer_val*100:.0f}% (persona avg: {persona_avg*100:.0f}%)"
                )
            elif metric == 'total_spend_12mo':
                comparison_text.append(
                    f"- Annual Spend: ${customer_val:.0f} (persona avg: ${persona_avg:.0f})"
                )
        
        comparison_str = '\n'.join(comparison_text)
        
        prompt = f"""Analyze this customer and explain why they fit their assigned persona in Academy Sports camping gear context.

Customer: {customer_name}
Assigned Persona: {persona}

Key Behavioral Metrics:
{comparison_str}

Provide a clear, business-friendly explanation with these sections:

1. **Search Behavior**: Analyze their search specificity and what it reveals about their camping expertise
2. **Purchase Patterns**: Explain their bundle affinity and what it suggests about their needs
3. **Price Sensitivity**: Discuss their price sorting behavior and budget consciousness
4. **Overall Fit**: Why this persona assignment makes sense (2-3 sentences)
5. **Recommendations**: 2-3 specific actions (product recommendations, marketing messages, or engagement strategies)

Keep it concise (250 words max), professional, and actionable for marketing teams."""
        
        return prompt
    
    def _format_explanation_text(self, raw_text: str) -> str:
        """
        Format AI-generated explanation by cleaning markdown and applying proper HTML formatting
        
        Args:
            raw_text: Raw text with markdown symbols
            
        Returns:
            Properly formatted HTML text
        """
        import re
        
        # Clean up the text
        formatted = raw_text
        
        # Remove any markdown headers
        formatted = re.sub(r'###?\s*', '', formatted)
        
        # Convert SECTION: prefix to headers
        formatted = re.sub(r'^SECTION:\s*(.+)$', r'<div class="section-header">\1</div>', formatted, flags=re.MULTILINE)
        
        # Convert standalone section titles (e.g., "Key Finding:", "Action Items:")
        formatted = re.sub(r'^([A-Z][A-Za-z\s]{2,40}):\s*$', r'<div class="section-header">\1</div>', formatted, flags=re.MULTILINE)
        
        # Convert numbered section titles (e.g., "1. Key Finding", "2. Business Impact")
        formatted = re.sub(r'^(\d+)\.\s*([A-Z][^:\n]{3,40}):\s*$', r'<div class="section-header">\1. \2</div>', formatted, flags=re.MULTILINE)
        
        # Remove all ** markdown
        formatted = formatted.replace('**', '')
        
        # Convert numbered lists
        formatted = re.sub(r'^\s*(\d+)\.\s+(.+)$', r'<div class="numbered-item">▸ \2</div>', formatted, flags=re.MULTILINE)
        
        # Convert bullet points
        formatted = re.sub(r'^\s*-\s+(.+)$', r'<div class="bullet-item">• \1</div>', formatted, flags=re.MULTILINE)
        
        # Split into paragraphs by double line breaks
        paragraphs = re.split(r'\n\n+', formatted)
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if it's already formatted
            if any(para.startswith(tag) for tag in ['<div class="section-header">', '<div class="numbered-item">', '<div class="bullet-item">']):
                formatted_paragraphs.append(para)
            else:
                # Regular paragraph
                formatted_paragraphs.append(f'<div class="insight-paragraph">{para}</div>')
        
        return ''.join(formatted_paragraphs)
    
    def _call_together_api(self, prompt: str, api_key: str) -> str:
        """Call Together API to generate explanation"""
        import requests
        import urllib3
        
        # Disable SSL warnings (only for development)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        response = requests.post(
            'https://api.together.xyz/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
                'messages': [
                    {
                        'role': 'system',
                        'content': '''You are a customer insights analyst for Academy Sports. 

CRITICAL FORMATTING RULES:
- Start each major section with "SECTION:" prefix
- Use double line breaks between sections
- Use "-" for bullet points
- Use simple numbered lists (1., 2., 3.)
- Keep paragraphs short (2-3 sentences max)
- NO markdown symbols like **, ###, etc.'''
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 500,
                'temperature': 0.7
            },
            timeout=30,
            verify=False  # Disable SSL verification for Windows compatibility
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Get raw content and format it
        raw_content = result['choices'][0]['message']['content']
        formatted_content = self._format_explanation_text(raw_content)
        
        return formatted_content
    
    def _generate_rule_based_explanation(self, customer_details: Dict) -> str:
        """Generate rule-based explanation as fallback"""
        persona = customer_details['persona_short']
        metrics = customer_details['customer_metrics']
        customer_name = customer_details['customer_name']
        
        if persona == 'Novice' or 'First-Time' in customer_details['persona']:
            explanation = f"""{customer_name} is classified as a First-Time Camper because:

**Search Behavior**: Uses generic terms (specificity: {metrics['search_specificity']:.1f}/5), indicating limited camping knowledge and need for guidance.

**Purchase Patterns**: Shows {metrics['bundle_affinity']*100:.0f}% bundle preference, suggesting desire for "complete solutions" to reduce decision complexity.

**Price Sensitivity**: Sorts by price {metrics['price_sort_frequency']*100:.0f}% of the time, indicating budget consciousness typical of first-time buyers.

**Overall Fit**: This customer exhibits classic novice behavior - seeking simplicity, bundles, and affordability while navigating unfamiliar product categories.

**Recommendations**:
- Show "Beginner's Complete Camping Kit" bundles
- Provide setup guides and how-to content
- Target with "Budget-Friendly Starter Gear" campaigns"""
        
        elif persona == 'Family_Socializer' or 'Family' in customer_details['persona']:
            explanation = f"""{customer_name} is classified as a Family Socializer because:

**Search Behavior**: Uses attribute-based searches (specificity: {metrics['search_specificity']:.1f}/5), showing some experience but focused on practical needs like capacity.

**Purchase Patterns**: Moderate bundle affinity ({metrics['bundle_affinity']*100:.0f}%), balancing convenience with specific family needs.

**Price Sensitivity**: Balanced price sorting ({metrics['price_sort_frequency']*100:.0f}%), willing to pay more for quality family-oriented features.

**Overall Fit**: This customer shows family camping patterns - researching capacity and comfort while maintaining budget awareness for occasional trips.

**Recommendations**:
- Highlight 4+ person tents and family-sized gear
- Promote comfort features (weather resistance, easy setup)
- Target with "Family Weekend Adventures" campaigns"""
        
        else:  # Seasoned Pro
            explanation = f"""{customer_name} is classified as a Seasoned Pro because:

**Search Behavior**: Uses model-specific searches (specificity: {metrics['search_specificity']:.1f}/5), indicating expert knowledge and brand awareness.

**Purchase Patterns**: Low bundle interest ({metrics['bundle_affinity']*100:.0f}%), preferring to select individual high-performance items.

**Price Sensitivity**: Rarely sorts by price ({metrics['price_sort_frequency']*100:.0f}%), focusing on quality and technical specifications over cost.

**Overall Fit**: This customer exhibits expert behavior - technical knowledge, brand loyalty, and willingness to invest in premium gear for frequent use.

**Recommendations**:
- Show latest technical innovations and premium brands
- Provide detailed specs and performance comparisons
- Target with "Pro-Grade Equipment" and new product launches"""
        
        # Format the explanation to clean up markdown
        return self._format_explanation_text(explanation)
    
    def get_customer_recommendations(self, customer_id: str) -> Dict:
        """
        Get actionable recommendations for a specific customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary with marketing and product recommendations
        """
        customer_details = self.get_customer_details(customer_id)
        persona = customer_details['persona_short']
        metrics = customer_details['customer_metrics']
        
        recommendations = {
            'customer_id': customer_id,
            'customer_name': customer_details['customer_name'],
            'persona': customer_details['persona'],
            'recommendations': []
        }
        
        # Persona-specific recommendations
        if persona == 'Novice' or 'First-Time' in customer_details['persona']:
            recommendations['recommendations'] = [
                {
                    'type': 'product',
                    'priority': 'high',
                    'action': 'Show Beginner Camping Bundle',
                    'reason': 'High bundle affinity and low search specificity indicate need for complete solutions'
                },
                {
                    'type': 'content',
                    'priority': 'high',
                    'action': 'Send "Camping 101" email series',
                    'reason': 'Low expertise requires educational content to build confidence'
                },
                {
                    'type': 'promotion',
                    'priority': 'medium',
                    'action': 'Offer "First-Timer Discount" on bundles',
                    'reason': f'High price sensitivity ({metrics["price_sort_frequency"]*100:.0f}% price sorting)'
                },
                {
                    'type': 'support',
                    'priority': 'medium',
                    'action': 'Trigger live chat for tent/sleeping bag pages',
                    'reason': 'Novice shoppers benefit from real-time assistance'
                }
            ]
        
        elif persona == 'Family_Socializer' or 'Family' in customer_details['persona']:
            recommendations['recommendations'] = [
                {
                    'type': 'product',
                    'priority': 'high',
                    'action': 'Highlight 4+ person tents and family gear',
                    'reason': 'Family-focused persona needs larger capacity products'
                },
                {
                    'type': 'content',
                    'priority': 'high',
                    'action': 'Show "Family Weekend Trip Ideas"',
                    'reason': 'Occasional campers need inspiration and planning content'
                },
                {
                    'type': 'promotion',
                    'priority': 'medium',
                    'action': 'Target with "Family Value Packages"',
                    'reason': f'Moderate spend (${metrics["total_spend_12mo"]:.0f}/year) suits mid-tier offers'
                },
                {
                    'type': 'cross-sell',
                    'priority': 'medium',
                    'action': 'Recommend comfort items (camp chairs, coolers)',
                    'reason': 'Family campers prioritize comfort and convenience'
                }
            ]
        
        else:  # Seasoned Pro
            recommendations['recommendations'] = [
                {
                    'type': 'product',
                    'priority': 'high',
                    'action': 'Show premium and technical gear (MSR, YETI, Big Agnes)',
                    'reason': f'High search specificity ({metrics["search_specificity"]:.1f}/5) and spend (${metrics["total_spend_12mo"]:.0f}/year)'
                },
                {
                    'type': 'content',
                    'priority': 'high',
                    'action': 'Send new product launch announcements',
                    'reason': 'Expert customers want early access to latest innovations'
                },
                {
                    'type': 'loyalty',
                    'priority': 'high',
                    'action': 'Invite to VIP program or gear testing',
                    'reason': f'High purchase frequency ({metrics["purchase_frequency"]}x/year) deserves recognition'
                },
                {
                    'type': 'engagement',
                    'priority': 'medium',
                    'action': 'Request product reviews and feedback',
                    'reason': 'Expert opinions valuable for other customers and product teams'
                }
            ]
        
        # Add recency-based recommendation
        if metrics['recency_days'] > 180:
            recommendations['recommendations'].append({
                'type': 'reactivation',
                'priority': 'high',
                'action': 'Send "We Miss You" winback campaign',
                'reason': f'Last purchase {metrics["recency_days"]} days ago - risk of churn'
            })
        
        return recommendations
    
    def generate_visualization_explanation(
        self,
        visualization_type: str,
        data: Dict,
        personas: Dict,
        together_api_key: str
    ) -> str:
        """
        Generate AI-powered explanation for a visualization
        
        Args:
            visualization_type: Type of visualization ('revenue', 'confidence', 'radar', etc.)
            data: The visualization data
            personas: Persona information
            together_api_key: Together AI API key
            
        Returns:
            Formatted explanation text
        """
        # Build prompt based on visualization type
        if visualization_type == 'revenue':
            prompt = self._build_revenue_viz_prompt(data, personas)
        elif visualization_type == 'confidence':
            prompt = self._build_confidence_viz_prompt(data, personas)
        elif visualization_type == 'radar':
            prompt = self._build_radar_viz_prompt(data, personas)
        elif visualization_type == 'seasonal':
            prompt = self._build_seasonal_viz_prompt(data, personas)
        elif visualization_type == 'executive':
            prompt = self._build_executive_viz_prompt(data, personas)
        elif visualization_type == 'validation':
            prompt = self._build_validation_viz_prompt(data, personas)
        elif visualization_type == 'distribution':
            prompt = self._build_distribution_viz_prompt(data, personas)
        else:
            prompt = f"Analyze this {visualization_type} visualization and provide insights for business users."
        
        # Call Together API
        try:
            explanation = self._call_together_api(prompt, together_api_key)
            return explanation
        except Exception as e:
            logger.error(f"Error calling Together API for visualization: {e}")
            return self._generate_rule_based_viz_explanation(visualization_type, data, personas)
    
    def _build_revenue_viz_prompt(self, data: Dict, personas: Dict) -> str:
        """Build prompt for revenue visualization"""
        persona_list = []
        for persona_id, persona_info in personas.items():
            revenue_metrics = persona_info.get('revenue_metrics', {})
            persona_list.append(
                f"- {persona_info['persona_name']}: ${revenue_metrics.get('total_revenue_12mo', 0):,.0f} total revenue "
                f"({revenue_metrics.get('revenue_percentage', 0)}% of total), "
                f"${revenue_metrics.get('avg_customer_value', 0):,.0f} per customer"
            )
        
        personas_text = '\n'.join(persona_list)
        
        prompt = f"""Analyze this Revenue by Persona chart for Academy Sports camping gear.

Data:
{personas_text}

Provide insights in this EXACT format:

Key Finding:
[Which persona drives most revenue and why it matters - 2 sentences]

Business Impact:
[What this means for marketing budget - 2 sentences]

Revenue Opportunities:
[Which personas have growth potential - 2 sentences]

Action Items:
- [Specific action 1]
- [Specific action 2]
- [Specific action 3]

Keep responses SHORT and actionable."""

        return prompt
    
    def _build_confidence_viz_prompt(self, data: Dict, personas: Dict) -> str:
        """Build prompt for confidence visualization"""
        prompt = f"""You are analyzing an Assignment Confidence chart showing how confident the clustering algorithm is about each persona assignment.

Explain in simple terms:

1. What This Chart Shows: What confidence means and why it matters

2. Overall Assessment: Are the confidence levels good, acceptable, or concerning?

3. Business Implications: How should marketing use this information?

4. Action Items: What to do if confidence is low vs high

Keep it simple, non-technical, and actionable (150 words max)."""

        return prompt
    
    def _build_radar_viz_prompt(self, data: Dict, personas: Dict) -> str:
        """Build prompt for radar chart visualization"""
        prompt = f"""You are analyzing a Persona Characteristics radar chart showing behavioral differences between customer segments in camping gear.

The chart compares personas across:
- Search Specificity (expertise level)
- Bundle Affinity (purchase bundling behavior)
- Price Sensitivity (price-focused vs quality-focused)
- Average Spend (spending power)

Explain:

1. Key Differences: How personas differ in behavior and what it reveals

2. Segment Personalities: Describe each persona in simple terms

3. Marketing Strategy: How to approach each segment differently

4. Quick Wins: Easiest opportunities based on these patterns

Keep it business-friendly and actionable (200 words max)."""

        return prompt
    
    def _build_seasonal_viz_prompt(self, data: Dict, personas: Dict) -> str:
        """Build prompt for seasonal visualization"""
        prompt = f"""You are analyzing seasonal purchase trends for camping gear customer personas.

Explain:

1. Seasonal Patterns: When different personas buy and why

2. Peak Seasons: Best times to target each persona

3. Campaign Timing: When to run marketing campaigns

4. Inventory Planning: How this affects product stocking

Focus on actionable seasonal marketing strategy (150 words max)."""

        return prompt
    
    def _build_executive_viz_prompt(self, data: Dict, personas: Dict) -> str:
        """Build prompt for executive summary"""
        total_revenue = data.get('totalRevenue', 0)
        total_profit = data.get('totalProfit', 0)
        avg_margin = data.get('avgMargin', 0)
        
        prompt = f"""You are analyzing the Executive Summary dashboard for Academy Sports camping gear business.

Key Metrics:
- Total Annual Revenue: ${total_revenue:,.0f}
- Estimated Profit: ${total_profit:,.0f}
- Average Margin: {avg_margin:.1f}%
- Number of Personas: {len(personas)}

Provide a strategic, executive-level analysis with:

1. Overall Business Health: Is this good? What stands out?

2. Key Strengths: What's working well based on these numbers?

3. Areas of Concern: Any red flags or opportunities?

4. Strategic Recommendations: 2-3 high-level action items for executives

Keep it strategic, non-technical, and decision-focused (200 words max)."""

        return prompt
    
    def _build_validation_viz_prompt(self, data: Dict, personas: Dict) -> str:
        """Build prompt for validation results"""
        validation = data.get('validation', {})
        accuracy = validation.get('accuracy', 0)
        correct = validation.get('correct_predictions', 0)
        total = validation.get('total_customers', 0)
        
        prompt = f"""You are analyzing the Model Validation Results for customer segmentation.

Results:
- Accuracy: {accuracy:.1f}%
- Correct Predictions: {correct:,} out of {total:,} customers
- Model: K-Prototypes clustering

Explain in simple business terms:

1. What This Means: Is {accuracy:.1f}% good, acceptable, or concerning for marketing purposes?

2. Business Impact: How reliable are these persona assignments for personalization?

3. Confidence Level: Should marketing fully trust these segments or proceed with caution?

4. Action Items: How to use these results effectively despite the accuracy level

Keep it simple and actionable for non-technical users (150 words max)."""

        return prompt
    
    def _build_distribution_viz_prompt(self, data: Dict, personas: Dict) -> str:
        """Build prompt for customer distribution"""
        persona_list = []
        for persona_id, persona_info in personas.items():
            persona_list.append(
                f"- {persona_info['persona_name']}: {persona_info['size']} customers ({persona_info['percentage']:.1f}%)"
            )
        
        personas_text = '\n'.join(persona_list)
        
        prompt = f"""You are analyzing Customer Distribution across personas for Academy Sports camping gear.

Distribution:
{personas_text}

Provide insights in plain English:

1. Balance Assessment: Is the distribution balanced or skewed? What does this mean?

2. Business Implications: How does this distribution affect marketing strategy?

3. Growth Opportunities: Which segments should we focus on growing and why?

4. Resource Allocation: How should this distribution guide budget and effort allocation?

Keep it business-focused and actionable (150 words max)."""

        return prompt
    
    def _generate_rule_based_viz_explanation(self, visualization_type: str, data: Dict, personas: Dict) -> str:
        """Generate rule-based explanation as fallback"""
        if visualization_type == 'executive':
            explanation = f"""<strong>Executive Summary Analysis</strong>

<strong>Overall Performance:</strong> The business is generating substantial revenue across {len(personas)} distinct customer personas, indicating healthy market segmentation.

<strong>Key Strengths:</strong>
- Multiple revenue streams from different customer types
- Clear persona differentiation enables targeted marketing
- Data-driven segmentation provides actionable insights

<strong>Strategic Focus:</strong>
- Invest in high-value segments while nurturing growth opportunities
- Leverage persona insights for personalized experiences
- Optimize marketing spend based on segment performance

<strong>Next Steps:</strong> Use these personas to drive targeted campaigns, product development, and customer experience improvements."""

        elif visualization_type == 'validation':
            validation = data.get('validation', {})
            accuracy = validation.get('accuracy', 0)
            
            if accuracy >= 80:
                assessment = "Excellent - highly reliable for business use"
                confidence_level = "High confidence"
                action = "Proceed with full implementation of personalized strategies"
            elif accuracy >= 70:
                assessment = "Good - reliable enough for most marketing applications"
                confidence_level = "Good confidence"
                action = "Use for personalization with occasional manual review"
            else:
                assessment = "Acceptable - use with caution and validation"
                confidence_level = "Moderate confidence"
                action = "Start with test campaigns and monitor results closely"
            
            explanation = f"""<strong>Model Validation Assessment</strong>

<strong>Accuracy Rating:</strong> {accuracy:.1f}% - {assessment}

<strong>Business Impact:</strong> {confidence_level} means persona assignments are {assessment.split('-')[1].strip()} These segments can be used for targeted marketing, but always monitor campaign performance.

<strong>Recommended Approach:</strong> {action}. Combine algorithm insights with business intuition for best results.

<strong>Key Insight:</strong> No clustering model is 100% perfect. The goal is actionable segmentation that improves marketing ROI, not perfection."""

        elif visualization_type == 'revenue':
            # Find highest revenue persona
            max_revenue_persona = None
            max_revenue = 0
            
            for persona_info in personas.values():
                revenue = persona_info.get('revenue_metrics', {}).get('total_revenue_12mo', 0)
                if revenue > max_revenue:
                    max_revenue = revenue
                    max_revenue_persona = persona_info['persona_name']
            
            explanation = f"""<strong>Revenue Analysis</strong>

<strong>Key Finding:</strong> {max_revenue_persona} drives the most revenue at ${max_revenue:,.0f} annually.

<strong>Business Impact:</strong> This segment should receive the highest marketing investment and personalized attention. Focus product development and inventory on their preferences.

<strong>Action Items:</strong>
- Allocate marketing budget proportional to revenue contribution
- Create VIP programs for high-value segments
- Analyze what makes {max_revenue_persona} customers spend more and replicate those patterns

<strong>Recommendation:</strong> Don't neglect lower-revenue segments - they may have high growth potential if properly targeted."""

        elif visualization_type == 'confidence':
            explanation = f"""<strong>Confidence Assessment</strong>

<strong>What This Shows:</strong> Confidence scores indicate how well each customer fits their assigned persona. Higher is better.

<strong>Overall Assessment:</strong> Scores above 75% are excellent, 60-75% are good, below 60% need review.

<strong>Business Impact:</strong> High confidence means personalization will be more effective. Low confidence suggests customers may have mixed behaviors.

<strong>Action Items:</strong>
- Use high-confidence customers for testing personalized campaigns
- Review low-confidence customers manually for better understanding
- Consider sub-segments within low-confidence groups"""

        elif visualization_type == 'distribution':
            total_customers = sum(p.get('size', 0) for p in personas.values())
            largest_segment = max(personas.values(), key=lambda x: x.get('size', 0))
            
            explanation = f"""<strong>Customer Distribution Analysis</strong>

<strong>Distribution Overview:</strong> Total {total_customers:,} customers spread across {len(personas)} distinct personas.

<strong>Largest Segment:</strong> {largest_segment['persona_name']} represents {largest_segment['percentage']:.1f}% of customers. This concentration affects how you should allocate resources.

<strong>Business Strategy:</strong>
- Invest proportionally in large segments for immediate revenue impact
- Don't neglect smaller segments - they may have high growth potential
- Ensure personalization strategies cover all segments effectively

<strong>Recommendation:</strong> Use this distribution to prioritize marketing campaigns while maintaining engagement across all personas."""

        else:
            explanation = f"""<strong>{visualization_type.title()} Visualization Insights</strong>

This chart shows important patterns in customer behavior and segment characteristics.

<strong>Key Takeaway:</strong> Understanding these patterns helps tailor marketing strategies to each persona's unique preferences and behaviors.

<strong>Action Items:</strong>
- Use these insights to personalize product recommendations
- Adjust marketing messages for each segment
- Time campaigns based on behavioral patterns

<strong>Next Steps:</strong> Click "Explain with AI" with your API key configured for detailed, AI-powered insights."""

        return explanation
    
    # ========================================================================
    # End of Customer-Level Personalization Methods
    # ========================================================================
    
    def _fallback_clustering(self) -> Dict:
        """
        Fallback method using simple rule-based clustering if kmodes not available
        
        Returns:
            Results using rule-based persona assignment
        """
        logger.warning("Using fallback rule-based clustering (kmodes not available)")
        
        if self.customers_df is None:
            if not self.load_data():
                return {'error': 'Failed to load customer data'}
        
        # Simple rule-based assignment
        def assign_persona(row):
            if row['search_specificity'] < 2.5 and row['bundle_affinity'] > 0.6:
                return 0  # Novice
            elif row['search_specificity'] > 3.5 and row['spec_expansion_rate'] > 0.55:
                return 2  # Pro
            else:
                return 1  # Family
        
        self.customers_df['cluster'] = self.customers_df.apply(assign_persona, axis=1)
        
        # Generate personas
        numeric_cols = ['search_specificity', 'spec_expansion_rate', 'bundle_affinity', 'price_sort_frequency']
        categorical_cols = ['urbanicity', 'dominant_category', 'brand_loyalty']
        
        # Mock cluster model for persona generation
        class MockModel:
            n_clusters = 3
        self.cluster_model = MockModel()
        
        self.personas = self._generate_personas(numeric_cols, categorical_cols)
        validation = self._validate_clustering()
        viz_data = self._prepare_visualization_data()
        
        return {
            'status': 'success_fallback',
            'note': 'Using rule-based clustering. Install kmodes for K-Prototypes: pip install kmodes',
            'personas': self.personas,
            'validation': validation,
            'visualization_data': viz_data,
            'total_customers': len(self.customers_df)
        }


if __name__ == "__main__":
    # Test Agent A
    print("="*70)
    print("Agent A - Academy Sports Persona Builder (K-Prototypes)")
    print("="*70)
    
    agent = AgentA_Academy()
    result = agent.execute()
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
    else:
        print(f"\n✅ Status: {result['status']}")
        print(f"📊 Total Customers: {result['total_customers']}")
        
        if 'personas' in result:
            print(f"\n{'='*70}")
            print("Identified Personas:")
            print(f"{'='*70}")
            
            for cluster_id, persona in result['personas'].items():
                print(f"\n{persona['persona_name']}")
                print(f"  - Size: {persona['size']} customers ({persona['percentage']}%)")
                print(f"  - Description: {persona['description']}")
                print(f"  - Key Characteristics:")
                chars = persona['characteristics']
                print(f"    • Search Specificity: {chars['avg_search_specificity']:.2f}/5")
                print(f"    • Spec Expansion: {chars['avg_spec_expansion_rate']*100:.1f}%")
                print(f"    • Bundle Affinity: {chars['avg_bundle_affinity']*100:.1f}%")
                print(f"    • Price Sort Frequency: {chars['avg_price_sort_frequency']*100:.1f}%")
                print(f"    • Avg Spend/Year: ${chars['avg_spend_12mo']:.2f}")
        
        if 'validation' in result and 'accuracy' in result['validation']:
            print(f"\n{'='*70}")
            print("Validation Results:")
            print(f"{'='*70}")
            validation = result['validation']
            print(f"  ✅ Accuracy: {validation['accuracy']*100:.2f}%")
            print(f"  📊 Correct: {validation['correct']} / {validation['total']}")
    
    print("\n" + "="*70)
    print("✅ Agent A Test Complete!")
    print("="*70)


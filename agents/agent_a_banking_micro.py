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
    print("⚠️  Warning: Image mapper not available")
try:
    from utils.together_ai import together_ai
    TOGETHER_AI_AVAILABLE = True
except ImportError:
    TOGETHER_AI_AVAILABLE = False
    together_ai = None

logger = logging.getLogger(__name__)


class AgentA_Banking_Micro:
    """
    Micro Segmentation Agent for Banking
    
    Creates 3-4 sub-segments within each macro persona to enable
    more granular personalization and targeted financial services
    """
    
    def __init__(self, customers_df: pd.DataFrame, macro_personas: Dict):
        """
        Initialize Micro Segmentation Agent
        
        Args:
            customers_df: DataFrame with customer data and cluster assignments
            macro_personas: Dictionary of macro personas from Agent A
        """
        self.customers_df = customers_df
        self.macro_personas = macro_personas
        self.micro_segments = {}
        
        logger.info(f"Micro Segmentation Agent initialized with {len(customers_df)} customers")
    
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
            
            # Calculate micro segmentation features
            features_df = self._calculate_micro_features(macro_customers)
            
            # Perform K-Means clustering
            micro_assignments = self._cluster_micro_segments(
                features_df, 
                n_micro_segments
            )
            
            # Add micro segment assignments
            macro_customers['micro_segment'] = micro_assignments
            
            # Generate micro segment profiles - handle flexible key types
            macro_persona = None
            for key in [macro_segment_id, str(macro_segment_id), int(macro_segment_id)]:
                if key in self.macro_personas:
                    macro_persona = self.macro_personas[key]
                    break
            
            if not macro_persona:
                raise KeyError(f"Macro segment {macro_segment_id} not found in personas. Available: {list(self.macro_personas.keys())}")
            
            macro_name = macro_persona['persona_name']
            micro_segments = self._generate_micro_profiles(
                macro_customers,
                macro_segment_id,
                n_micro_segments,
                macro_name
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
                    'avg_balance': avg_value,  # Frontend expects this
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
        if 'tenure_months' in customers_df.columns:
            tenure = customers_df['tenure_months']
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
        n_clusters: int
    ) -> np.ndarray:
        """
        Perform K-Means clustering on micro features
        
        Args:
            features_df: Features for clustering
            n_clusters: Number of micro segments
            
        Returns:
            Array of cluster assignments
        """
        # Select features for clustering
        clustering_features = [
            'digital_engagement',
            'portfolio_depth',
            'credit_utilization',
            'transaction_velocity',
            'account_maturity',
            'cross_sell_receptivity'
        ]
        
        X = features_df[clustering_features].values
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # K-Means clustering
        kmeans = KMeans(
            n_clusters=n_clusters,
            init='k-means++',
            n_init=10,
            max_iter=300,
            random_state=42
        )
        
        clusters = kmeans.fit_predict(X_scaled)
        
        logger.info(f"K-Means clustering complete with inertia: {kmeans.inertia_:.2f}")
        
        return clusters
    
    def _generate_micro_profiles(
        self,
        customers_df: pd.DataFrame,
        macro_segment_id: int,
        n_micro_segments: int,
        macro_name: str = ""
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
        used_names = set()
        
        for micro_id in range(n_micro_segments):
            micro_customers = customers_df[customers_df['micro_segment'] == micro_id]
            
            if len(micro_customers) == 0:
                continue
            
            # Calculate characteristics (fixed .get() issue)
            characteristics = {
                'avg_digital_engagement': float(micro_customers['digital_engagement_score'].mean() if 'digital_engagement_score' in micro_customers.columns else 0.5),
                'avg_portfolio_depth': float(micro_customers['num_products'].mean() if 'num_products' in micro_customers.columns else 2),
                'avg_credit_utilization': float(micro_customers['credit_utilization_ratio'].mean() if 'credit_utilization_ratio' in micro_customers.columns else 0.3),
                'avg_transaction_velocity': float(micro_customers['transaction_volume_30d'].mean() if 'transaction_volume_30d' in micro_customers.columns else 5),
                'avg_account_tenure': float(micro_customers['tenure_months'].mean() if 'tenure_months' in micro_customers.columns else 24),
                'avg_cross_sell_score': float(micro_customers['cross_sell_receptivity'].mean() if 'cross_sell_receptivity' in micro_customers.columns else 0.5),
                'avg_deposits': float(micro_customers['total_deposits'].mean() if 'total_deposits' in micro_customers.columns else 0),
                'avg_income': float(micro_customers['income'].mean() if 'income' in micro_customers.columns else 50000)
            }
            
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
            
            # Generate UNIQUE micro segment name
            # Use macro_name parameter or fallback to persona dict
            parent_name = macro_name if macro_name else self.macro_personas[macro_segment_id].get('short_name', f'Macro_{macro_segment_id}')
            segment_name = self._generate_micro_segment_name(
                characteristics,
                ltv_tier,
                parent_name,
                micro_id
            )
            
            # STRICT: No numbers allowed - if duplicate, this is a critical error
            if segment_name in used_names:
                # This should NEVER happen with our new naming logic
                logger.error(f"CRITICAL: Duplicate micro segment name '{segment_name}'!")
                # Add micro_id suffix as last resort (but this indicates a logic bug)
                segment_name = f"{segment_name} (Micro-{chr(65 + micro_id)})"
            
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
                avg_deposits_per_customer
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
    
    def _generate_micro_segment_name(
        self,
        characteristics: Dict,
        ltv_tier: str,
        macro_name: str,
        micro_id: int = 0
    ) -> str:
        """
        Generate UNIQUE micro segment names dynamically
        Works for ANY number of macro segments (3, 4, 5, 6, 7, etc.)
        Each micro gets unique name by combining macro context + micro traits
        """
        digital = characteristics['avg_digital_engagement']
        portfolio = characteristics['avg_portfolio_depth']
        velocity = characteristics['avg_transaction_velocity']
        deposits = characteristics['avg_deposits']
        income = characteristics['avg_income']
        
        # Extract key words from macro name for context
        macro_words = macro_name.split()
        macro_key = macro_words[0] if macro_words else "Banking"
        
        # Define 4 dimension templates (one per micro_id)
        # Each template creates unique names using macro context + characteristics
        
        if micro_id == 0:
            # MICRO A: Value/Wealth Dimension
            if deposits > 2000000:
                descriptor = "Ultra-Premium"
            elif deposits > 1000000:
                descriptor = "High-Value"
            elif deposits > 500000:
                descriptor = "Affluent"
            elif deposits > 200000:
                descriptor = "Upper-Tier"
            else:
                descriptor = "Core"
            name = f"{descriptor} {macro_key} Leaders"
            
        elif micro_id == 1:
            # MICRO B: Activity/Engagement Dimension
            if velocity > 1.5:
                descriptor = "Hyperactive"
            elif velocity > 1.0:
                descriptor = "High-Activity"
            elif velocity > 0.5:
                descriptor = "Engaged"
            else:
                descriptor = "Stable"
            name = f"{descriptor} {macro_key} Users"
            
        elif micro_id == 2:
            # MICRO C: Product/Service Dimension
            if portfolio >= 4:
                descriptor = "Multi-Product"
            elif portfolio >= 3:
                descriptor = "Diversified"
            elif portfolio >= 2:
                descriptor = "Dual-Service"
            else:
                descriptor = "Focused"
            name = f"{descriptor} {macro_key} Customers"
            
        else:  # micro_id == 3
            # MICRO D: Income/Digital Dimension
            if income > 150000 and digital > 0.6:
                descriptor = "Premium Digital"
            elif income > 100000:
                descriptor = "High-Income"
            elif income > 70000:
                descriptor = "Upper-Income"
            elif digital > 0.6:
                descriptor = "Tech-Enabled"
            else:
                descriptor = "Traditional"
            name = f"{descriptor} {macro_key} Segment"
        
        # Result: "Descriptor MacroKey Type (Tier)"
        # Examples:
        #   "Ultra-Premium Savers Leaders (Platinum)"
        #   "Hyperactive Earners Users (Gold)"
        #   "Multi-Product Natives Customers (Silver)"
        #   "Premium Digital Members Segment (Platinum)"
        return f"{name} ({ltv_tier})"
    
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
            return f"'{segment_name}' represents {segment_size} customers with {portfolio*10:.0f} products, showing deep banking relationships ({ltv_tier} tier)."
        
        # DUAL-SERVICE patterns
        elif 'dual-service' in name_lower:
            return f"'{segment_name}' captures {segment_size} customers using {portfolio*10:.0f} core products with ${deposits:,.0f} deposits ({ltv_tier} tier)."
        
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
            return f"'{segment_name}' identifies {segment_size} banking customers with ${deposits:,.0f} deposits and {portfolio*10:.0f} products ({ltv_tier} tier)."
        
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
        avg_customer_value: float
    ) -> Dict:
        """
        Generate COMPLETELY UNIQUE insights for each micro segment
        Uses segment name + characteristics to ensure NO TWO micros have same insights
        """
        digital_engagement = characteristics['avg_digital_engagement']
        portfolio_depth = characteristics['avg_portfolio_depth']
        credit_utilization = characteristics['avg_credit_utilization']
        transaction_velocity = characteristics['avg_transaction_velocity']
        
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
        segment_definition.append(f"💰 Value: {deposits_range} average | {ltv_tier} tier | Income: {income_range}/year")
        segment_definition.append(f"📊 Portfolio: {portfolio_depth*10:.0f} products | {digital_engagement*100:.0f}% digital engagement")
        segment_definition.append(f"⚡ Activity: {transaction_velocity*100:.0f} velocity | {credit_utilization*100:.0f}% credit utilization")
        
        # KEY BEHAVIORS - COMPLETELY UNIQUE based on segment name + metrics
        # MARKETING OPPORTUNITIES - Actionable directives for sales/marketing (what to DO), unique per micro segment
        if 'Multi-Product' in segment_name:
            key_behaviors.append(f"{segment_name}: {portfolio_depth*10:.0f}+ products totaling {deposits_range} in {ltv_tier} tier")
            key_behaviors.append(f"Deep product relationships with {digital_engagement*100:.0f}% digital usage and {transaction_velocity*100:.0f} activity")
            key_behaviors.append(f"Consolidated banking across checking, savings, loans, investments - {segment_size} customers")
            recommendations.append(f"Offer relationship-based fee waivers for customers maintaining {portfolio_depth*10:.0f}+ products; run a retention campaign to this micro segment.")
            recommendations.append(f"Propose consolidated relationship pricing and assign a single point of contact for the {segment_size} customers in this micro segment.")
            recommendations.append(f"Cross-sell one complementary product (e.g. investment or insurance) via personalized outreach; use deposit and product data to tailor the offer.")
        
        elif 'Diversified' in segment_name:
            key_behaviors.append(f"{segment_name}: Spread {deposits_range} across {portfolio_depth*10:.0f} different products - {segment_size} customers")
            key_behaviors.append(f"Diversification strategy with {ltv_tier} tier status, {transaction_velocity*100:.0f} activity, {digital_engagement*100:.0f}% digital")
            key_behaviors.append(f"Balanced portfolio approach minimizes risk while maximizing banking relationship value")
            recommendations.append(f"Launch a consolidated dashboard or reporting offer for this micro segment; use it to recommend one next product that fits their portfolio.")
            recommendations.append(f"Run a bundle campaign (e.g. discount or rate incentive) for adding one more product; target the {segment_size} diversified customers with clear benefit.")
            recommendations.append(f"Send segment-specific messaging linking their current {portfolio_depth*10:.0f} products to one logical add-on (e.g. savings if they have checking only).")
        
        elif 'Growing' in segment_name:
            key_behaviors.append(f"{segment_name}: Expanding portfolios from {deposits_range} baseline in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"Growth trajectory customers increasing products from current {portfolio_depth*10:.0f} level")
            key_behaviors.append(f"High potential segment with {credit_utilization*100:.0f}% credit usage and {digital_engagement*100:.0f}% digital engagement")
            recommendations.append(f"Run a product-adoption campaign with a small incentive (e.g. bonus rate or waiver) for adding one more product; target this micro segment first.")
            recommendations.append(f"Create a pathway program (e.g. step-up to next tier) and invite the {segment_size} customers with personalized next-step offers.")
            recommendations.append(f"Send educational content (e.g. benefits of savings or credit) followed by a soft product offer; use digital channel if {digital_engagement*100:.0f}%+ digital.")
        
        elif 'Active' in segment_name or 'Frequent' in segment_name or 'Power' in segment_name:
            key_behaviors.append(f"{segment_name}: High-activity users with {transaction_velocity*100:.0f} velocity managing {deposits_range} - {segment_size} customers")
            key_behaviors.append(f"Conduct frequent transactions across {portfolio_depth*10:.0f} products with {digital_engagement*100:.0f}% digital adoption")
            key_behaviors.append(f"Generate significant engagement in {ltv_tier} tier through consistent banking activity")
            recommendations.append(f"Offer an activity-based rewards tier (e.g. cashback or fee waivers) for maintaining this transaction level; promote to the {segment_size} customers in this micro segment.")
            recommendations.append(f"Run a campaign that rewards high-activity customers with premium features or a dedicated service option; use preferred channel (app if high digital).")
            recommendations.append(f"Propose a premium checking or payment product that matches their transaction profile; use behavioral triggers to time the offer.")
        
        elif 'Digital' in segment_name or 'Tech' in segment_name:
            key_behaviors.append(f"{segment_name}: {digital_engagement*100:.0f}% digital engagement with {deposits_range} in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"Digital-first with {portfolio_depth*10:.0f} products and {transaction_velocity*100:.0f} transaction velocity")
            recommendations.append(f"Deploy in-app and email campaigns for this micro segment; offer one next-best product with a one-tap or instant-apply flow.")
            recommendations.append(f"Invite to beta features or digital-only events; use feedback to refine offers and then roll out to the full {segment_size} customers.")
            recommendations.append(f"Run A/B tests on product and messaging for digital-first users; prioritize app push and in-app placement.")
        
        elif 'Traditional' in segment_name or 'Branch' in segment_name or 'Establish' in segment_name:
            key_behaviors.append(f"{segment_name}: Lower digital adoption ({digital_engagement*100:.0f}%), {deposits_range} in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"Prefer branch or phone with {portfolio_depth*10:.0f} products and {transaction_velocity*100:.0f} activity")
            recommendations.append(f"Use outbound call or branch-led outreach for this micro segment; offer one product with a simple application process.")
            recommendations.append(f"Run a direct mail or branch poster campaign with a clear CTA (e.g. call or visit) for the {segment_size} customers in this micro segment.")
            recommendations.append(f"Train branch staff on a single next-best offer for this profile; track conversion and refine messaging.")
        
        elif 'Affluent' in segment_name or 'Elite' in segment_name or 'Wealth' in segment_name:
            key_behaviors.append(f"{segment_name}: High value {deposits_range} in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"Strong portfolio ({portfolio_depth*10:.0f} products) and {digital_engagement*100:.0f}% digital; {transaction_velocity*100:.0f} velocity")
            recommendations.append(f"Propose a relationship manager or premium tier for this micro segment; book discovery calls or invite to an exclusive event.")
            recommendations.append(f"Run a wealth-advisory or investment onboarding campaign; target the {segment_size} customers with personalized, high-touch outreach.")
            recommendations.append(f"Offer an affluent-only benefit (e.g. preferred rates, concierge) and use it to cross-sell one high-value product.")
        
        elif 'Emerging' in segment_name or 'Growth' in segment_name:
            key_behaviors.append(f"{segment_name}: Growth potential with {deposits_range}, {portfolio_depth*10:.0f} products in {ltv_tier} tier - {segment_size} customers")
            key_behaviors.append(f"{digital_engagement*100:.0f}% digital, {transaction_velocity*100:.0f} velocity, {credit_utilization*100:.0f}% credit utilization")
            recommendations.append(f"Run a first-product or next-product campaign with a small incentive to move this micro segment to the next tier.")
            recommendations.append(f"Send educational content and a single product recommendation (e.g. savings or credit) tailored to their profile; measure conversion.")
            recommendations.append(f"Assign light-touch outbound or in-app follow-up to the {segment_size} customers; test offer and channel.")
        
        # Data-driven fallback: unique actionable recommendations from metrics (no generic "targeted campaigns")
        if len(key_behaviors) == 0:
            key_behaviors.append(f"{segment_name}: {segment_size} customers managing {deposits_range} in {ltv_tier} tier")
            key_behaviors.append(f"Portfolio {portfolio_depth*10:.0f} products, {digital_engagement*100:.0f}% digital, {transaction_velocity*100:.0f} velocity")
        
        if len(recommendations) == 0:
            if digital_engagement >= 0.6:
                recommendations.append(f"Run in-app and email offers for the {segment_size} customers in this micro segment; recommend one product that fits {deposits_range} and {ltv_tier} tier.")
            else:
                recommendations.append(f"Use outbound or branch-led outreach for the {segment_size} customers; offer one product with a simple application and clear benefit.")
            if portfolio_depth < 0.8:
                recommendations.append(f"Campaign to add one more product (e.g. savings or credit) for customers at {portfolio_depth*10:.0f} products; use incentive to test conversion.")
            else:
                recommendations.append(f"Offer relationship rewards (e.g. fee waiver or preferred rate) for maintaining {portfolio_depth*10:.0f}+ products; use retention messaging.")
            recommendations.append(f"Tailor next-best action for this micro segment using {ltv_tier} tier and {deposits_range}; measure by segment and iterate.")
        
        # UNIQUE marketing opportunities: try LLM first, else personalize so each micro segment is unique
        recommendations = recommendations[:4]
        segment_def_text = "\n".join(segment_definition)
        metrics_for_llm = {
            'avg_deposits': characteristics.get('avg_deposits', 0),
            'avg_income': characteristics.get('avg_income', 0),
            'avg_digital': digital_engagement,
            'avg_products': portfolio_depth * 10,
            'avg_transactions': transaction_velocity * 100,
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
            'name_explanation': name_explanation,  # NEW: Explains why this name
            'segment_definition': segment_def_text,
            'key_behaviors': key_behaviors[:4],  # Top 4
            'marketing_recommendations': recommendations,
            'segment_size': segment_size,
            'avg_customer_value': avg_customer_value
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

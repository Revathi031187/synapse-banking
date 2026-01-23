"""
Agent A Micro - Academy Sports Micro Segmentation
Creates sub-segments within each macro persona based on:
- Brand loyalty
- Expertise level  
- Customer lifetime value (LTV)
- Category specialization
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

# Add utils to path for image mapper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.image_mapper import get_image_mapper
    IMAGE_MAPPER_AVAILABLE = True
except ImportError:
    IMAGE_MAPPER_AVAILABLE = False
    print("⚠️  Warning: Image mapper not available")

logger = logging.getLogger(__name__)


class AgentA_Academy_Micro:
    """
    Micro Segmentation Agent for Academy Sports
    
    Creates 3-4 sub-segments within each macro persona to enable
    more granular personalization and targeted marketing
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
            
            # Generate micro segment profiles
            micro_segments = self._generate_micro_profiles(
                macro_customers,
                macro_segment_id,
                n_micro_segments
            )
            
            # Store results
            self.micro_segments[macro_segment_id] = {
                'macro_segment_id': macro_segment_id,
                'macro_segment_name': self.macro_personas[macro_segment_id]['persona_name'],
                'n_micro_segments': n_micro_segments,
                'micro_segments': micro_segments,
                'customer_assignments': macro_customers[['customer_id', 'micro_segment']].to_dict('records')
            }
            
            # Convert micro_segments dict to list for frontend compatibility
            micro_segments_list = []
            for seg_id, seg_data in micro_segments.items():
                # Get visual enrichment if available
                icons = []
                trait_badges = []
                if IMAGE_MAPPER_AVAILABLE:
                    try:
                        image_mapper = get_image_mapper()
                        icons = image_mapper.get_micro_segment_icons(
                            seg_data.get('segment_name', ''),
                            seg_data.get('characteristics', {})
                        )
                        trait_badges = image_mapper.get_trait_badges(
                            seg_data.get('characteristics', {}),
                            seg_data.get('ltv_tier', 'Bronze')
                        )
                    except Exception as e:
                        logger.warning(f"Could not enrich micro segment with visuals: {e}")
                
                # Map backend fields to frontend expectations
                frontend_seg = {
                    'micro_cluster_id': seg_data.get('micro_segment_id', int(seg_id)),
                    'name': seg_data.get('segment_name', f'Segment {seg_id}'),
                    'size': seg_data.get('size', 0),
                    'percentage': seg_data.get('percentage', 0.0),
                    'avg_spend': seg_data.get('revenue_metrics', {}).get('avg_customer_value', 0.0),
                    'ltv_tier': seg_data.get('ltv_tier', 'Bronze'),
                    'characteristics': seg_data.get('characteristics', {}),
                    'revenue_metrics': seg_data.get('revenue_metrics', {}),
                    'top_customers': seg_data.get('top_customers', []),
                    # Visual enrichment
                    'icons': icons,
                    'trait_badges': trait_badges,
                    # Segment explanation - CRITICAL: Include this for frontend display!
                    'segment_explanation': seg_data.get('segment_explanation', None),
                    # Include original data for reference
                    '_original': seg_data
                }
                micro_segments_list.append(frontend_seg)
            
            return {
                'status': 'success',
                'macro_segment_id': macro_segment_id,
                'macro_segment_name': self.macro_personas[macro_segment_id]['persona_name'],
                'n_micro_segments': n_micro_segments,
                'micro_segments': micro_segments_list,  # Now an array!
                'total_customers': len(macro_customers)
            }
            
        except Exception as e:
            logger.error(f"Error in micro segmentation: {e}")
            return {'error': str(e), 'macro_segment_id': macro_segment_id}
    
    def _calculate_micro_features(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate features for micro segmentation
        
        Features:
        - brand_loyalty_score: % of purchases from dominant brand
        - expertise_level: Based on search specificity and spec expansion
        - ltv_tier: Customer lifetime value tier (0-3)
        - category_focus: How specialized in dominant category
        
        Args:
            customers_df: Customer data
            
        Returns:
            DataFrame with calculated features
        """
        features = pd.DataFrame(index=customers_df.index)
        
        # 1. Brand Loyalty Score
        # Map brand_loyalty categorical to numeric score
        brand_loyalty_map = {
            'None': 0.0,
            'Low': 0.25,
            'Coleman': 0.5,
            'Magellan Outdoors': 0.5,
            'Ozark Trail': 0.5,
            'Big Agnes': 0.75,
            'MSR': 0.75,
            'YETI': 0.75,
            'The North Face': 0.75
        }
        
        features['brand_loyalty_score'] = customers_df['brand_loyalty'].map(
            lambda x: brand_loyalty_map.get(x, 0.5)
        )
        
        # 2. Expertise Level
        # Combination of search specificity and spec expansion
        features['expertise_level'] = (
            (customers_df['search_specificity'] / 5.0) * 0.6 +  # 0-1 scale
            customers_df['spec_expansion_rate'] * 0.4
        )
        
        # 3. LTV Tier (normalized spend)
        spend = customers_df['total_spend_12mo']
        features['ltv_normalized'] = (spend - spend.min()) / (spend.max() - spend.min() + 1e-6)
        
        # Create tiers: Bronze (0-0.25), Silver (0.25-0.5), Gold (0.5-0.75), Platinum (0.75-1.0)
        features['ltv_tier'] = pd.cut(
            features['ltv_normalized'],
            bins=[0, 0.25, 0.5, 0.75, 1.0],
            labels=[0, 1, 2, 3],
            include_lowest=True
        ).astype(int)
        
        # 4. Category Focus Score
        # How focused on dominant category (measured by recency and frequency)
        features['category_focus'] = (
            (1 / (customers_df['recency_days'] + 1)) * 0.5 +  # Recent = more focused
            (customers_df['purchase_frequency'] / customers_df['purchase_frequency'].max()) * 0.5
        )
        
        # 5. Additional behavioral features
        features['bundle_affinity'] = customers_df['bundle_affinity']
        features['price_sensitivity'] = customers_df['price_sort_frequency']
        features['avg_order_value_normalized'] = (
            customers_df['avg_order_value'] / customers_df['avg_order_value'].max()
        )
        
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
            'brand_loyalty_score',
            'expertise_level',
            'ltv_tier',
            'category_focus',
            'bundle_affinity',
            'price_sensitivity'
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
        n_micro_segments: int
    ) -> Dict:
        """
        Generate profiles for each micro segment
        
        Args:
            customers_df: Customer data with micro segment assignments
            macro_segment_id: Parent macro segment ID
            n_micro_segments: Number of micro segments
            
        Returns:
            Dictionary of micro segment profiles
        """
        micro_segments = {}
        used_names = set()  # Track used names to ensure uniqueness
        
        for micro_id in range(n_micro_segments):
            micro_customers = customers_df[customers_df['micro_segment'] == micro_id]
            
            if len(micro_customers) == 0:
                continue
            
            # Calculate characteristics
            characteristics = {
                'avg_brand_loyalty': self._calculate_brand_loyalty_score(micro_customers),
                'avg_expertise': float(micro_customers['search_specificity'].mean()),
                'avg_spec_expansion': float(micro_customers['spec_expansion_rate'].mean()),
                'avg_ltv': float(micro_customers['total_spend_12mo'].mean()),
                'avg_purchase_frequency': float(micro_customers['purchase_frequency'].mean()),
                'avg_bundle_affinity': float(micro_customers['bundle_affinity'].mean()),
                'avg_price_sensitivity': float(micro_customers['price_sort_frequency'].mean()),
                'dominant_category': micro_customers['dominant_category'].mode()[0] if len(micro_customers) > 0 else 'Unknown',
                'dominant_brand': micro_customers['brand_loyalty'].mode()[0] if len(micro_customers) > 0 else 'None'
            }
            
            # Determine LTV tier for segment
            ltv_median = micro_customers['total_spend_12mo'].median()
            if ltv_median < 300:
                ltv_tier = 'Bronze'
            elif ltv_median < 600:
                ltv_tier = 'Silver'
            elif ltv_median < 1000:
                ltv_tier = 'Gold'
            else:
                ltv_tier = 'Platinum'
            
            # Generate UNIQUE micro segment name based on characteristics
            # The new algorithm generates truly distinct names, reducing collision risk
            segment_name = self._generate_micro_segment_name(
                characteristics,
                ltv_tier,
                self.macro_personas[macro_segment_id]['short_name'],
                micro_id
            )
            
            # Ensure uniqueness (should be rare with new algorithm)
            if segment_name in used_names:
                # Add minimal modifier only if collision occurs
                counter = 1
                while f"{segment_name} {counter}" in used_names:
                    counter += 1
                segment_name = f"{segment_name} {counter}"
            
            used_names.add(segment_name)
            
            # Also add explanation of why this name was chosen
            logger.info(f"Generated micro segment name: '{segment_name}' (LTV: {ltv_tier}, Category: {characteristics.get('dominant_category', 'General')})")
            
            # Calculate revenue metrics
            total_revenue = float(micro_customers['total_spend_12mo'].sum())
            avg_revenue = total_revenue / len(micro_customers)
            
            # Generate explanation for this micro segment
            micro_explanation = self._generate_micro_segment_explanation(
                characteristics,
                ltv_tier,
                segment_name,
                len(micro_customers),
                avg_revenue
            )
            
            micro_segments[micro_id] = {
                'micro_segment_id': micro_id,
                'segment_name': segment_name,
                'size': len(micro_customers),
                'percentage': round(len(micro_customers) / len(customers_df) * 100, 1),
                'ltv_tier': ltv_tier,
                'characteristics': characteristics,
                'revenue_metrics': {
                    'total_revenue': round(total_revenue, 2),
                    'avg_customer_value': round(avg_revenue, 2),
                    'revenue_percentage': round(total_revenue / customers_df['total_spend_12mo'].sum() * 100, 1)
                },
                'top_customers': self._get_top_customers(micro_customers, n=5),
                'segment_explanation': micro_explanation
            }
        
        return micro_segments
    
    def _calculate_brand_loyalty_score(self, customers_df: pd.DataFrame) -> float:
        """
        Calculate average brand loyalty score for a group of customers
        
        Args:
            customers_df: Customer data
            
        Returns:
            Average brand loyalty score (0-1)
        """
        brand_loyalty_map = {
            'None': 0.0,
            'Low': 0.25,
            'Coleman': 0.5,
            'Magellan Outdoors': 0.5,
            'Ozark Trail': 0.5,
            'Big Agnes': 0.75,
            'MSR': 0.75,
            'YETI': 0.75,
            'The North Face': 0.75
        }
        
        scores = customers_df['brand_loyalty'].map(lambda x: brand_loyalty_map.get(x, 0.5))
        return float(scores.mean())
    
    def _generate_micro_segment_explanation(
        self,
        characteristics: Dict,
        ltv_tier: str,
        segment_name: str,
        segment_size: int,
        avg_customer_value: float
    ) -> Dict:
        """
        Generate explanation for why customers fall into this micro segment
        
        Returns dict with segment-specific explanations INCLUDING name explanation
        """
        expertise = characteristics['avg_expertise']
        price_sensitivity = characteristics['avg_price_sensitivity']
        purchase_freq = characteristics['avg_purchase_frequency']
        bundle_affinity = characteristics['avg_bundle_affinity']
        dominant_category = characteristics.get('dominant_category', 'General')
        
        # EXPLAIN THE SEGMENT NAME - SIMPLE
        name_explanation = self._explain_segment_name(
            segment_name,
            characteristics,
            ltv_tier
        )
        
        # SIMPLE definition - NO jargon, EASY to understand
        segment_definition = []
        
        # 1. Value Tier (most important)
        if ltv_tier == "Platinum":
            segment_definition.append(f"• **Premium Customer:** ${avg_customer_value:.0f} annual spend - Top-tier buyers")
        elif ltv_tier == "Gold":
            segment_definition.append(f"• **High-Value Customer:** ${avg_customer_value:.0f} annual spend - Quality-focused")
        elif ltv_tier == "Silver":
            segment_definition.append(f"• **Mid-Tier Customer:** ${avg_customer_value:.0f} annual spend - Balanced approach")
        else:
            segment_definition.append(f"• **Budget Customer:** ${avg_customer_value:.0f} annual spend - Value-conscious")
        
        # 2. Expertise - CLEAR language
        if expertise > 4.0:
            segment_definition.append(f"• **Expert Level:** Very knowledgeable - knows exactly what they need")
        elif expertise > 3.0:
            segment_definition.append(f"• **Intermediate:** Comfortable with camping gear")
        else:
            segment_definition.append(f"• **Beginner:** Still learning - needs guidance")
        
        # 3. ONE key behavior (not multiple)
        if bundle_affinity > 0.15:
            segment_definition.append(f"• **Bundle Buyer:** Prefers complete kits ({bundle_affinity*100:.0f}% bundle purchases)")
        elif price_sensitivity > 0.15:
            segment_definition.append(f"• **Price-Conscious:** Compares prices actively ({price_sensitivity*100:.0f}% check prices)")
        elif purchase_freq > 10:
            segment_definition.append(f"• **Frequent Shopper:** Buys {purchase_freq:.0f}x per year")
        else:
            segment_definition.append(f"• **Regular Buyer:** {purchase_freq:.0f} purchases per year")
        
        # 4. Category focus (only if strong)
        if dominant_category and dominant_category not in ['Unknown', 'General']:
            segment_definition.append(f"• **Category Focus:** Prefers {dominant_category}")
        
        # UNIQUE, DIFFERENTIATED behaviors - NO repetition across segments
        key_behaviors = []
        
        # Build behaviors based on PRIMARY distinctive trait (most extreme characteristic)
        traits = [
            ('expertise', expertise, 5.0),
            ('price_sensitivity', price_sensitivity, 1.0),
            ('bundle_affinity', bundle_affinity, 1.0),
            ('purchase_freq', purchase_freq / 20.0, 1.0),  # Normalize to 0-1
            ('brand_loyalty', characteristics.get('avg_brand_loyalty', 0), 1.0)
        ]
        
        # Sort by how extreme each trait is (deviation from midpoint)
        traits_scored = [(name, val, abs(val - (max_val/2)) / (max_val/2)) for name, val, max_val in traits]
        traits_scored.sort(key=lambda x: x[2], reverse=True)
        
        primary_trait = traits_scored[0][0]
        secondary_trait = traits_scored[1][0] if len(traits_scored) > 1 else None
        
        # Generate UNIQUE behaviors based on PRIMARY trait
        if primary_trait == 'expertise':
            if expertise > 4.0:
                key_behaviors.append("Deep product research - compares 5+ models before buying")
                key_behaviors.append("Reads technical specs, reviews, and expert forums")
            elif expertise < 2.5:
                key_behaviors.append("Relies heavily on staff recommendations and popular items")
                key_behaviors.append("Prefers beginner-friendly bundles over individual gear")
            else:
                key_behaviors.append("Moderate research - checks 2-3 options before deciding")
        
        elif primary_trait == 'price_sensitivity':
            if price_sensitivity > 0.15:
                key_behaviors.append("Active price comparison across multiple retailers")
                key_behaviors.append("Waits for seasonal sales and discount events")
            else:
                key_behaviors.append("Values quality and brand reputation over price")
        
        elif primary_trait == 'bundle_affinity':
            if bundle_affinity > 0.15:
                key_behaviors.append("Prefers complete camping kits - 'ready to go' approach")
                key_behaviors.append("Buys coordinated gear sets rather than mixing brands")
            else:
                key_behaviors.append("Curates custom gear setup - selects each item individually")
        
        elif primary_trait == 'purchase_freq':
            if purchase_freq > 10:
                key_behaviors.append(f"Frequent upgrader - shops {purchase_freq:.0f}x per year")
                key_behaviors.append("Always testing new gear and innovations")
            else:
                key_behaviors.append(f"Selective buyer - {purchase_freq:.0f} purchases per year")
        
        # Add SECONDARY behavior ONLY if it's significantly different
        if secondary_trait and traits_scored[1][2] > 0.5:  # Only if secondary trait is also extreme
            if secondary_trait == 'brand_loyalty' and characteristics.get('avg_brand_loyalty', 0) > 0.6:
                key_behaviors.append(f"Strong brand preference - {characteristics.get('avg_brand_loyalty', 0)*100:.0f}% same-brand purchases")
            elif secondary_trait == 'price_sensitivity' and price_sensitivity > 0.15:
                key_behaviors.append("Price-conscious - checks competitor pricing")
            elif secondary_trait == 'bundle_affinity' and bundle_affinity > 0.15:
                key_behaviors.append("Bundle buyer - prefers complete kits")
        
        # Actionable recommendations
        recommendations = []
        if ltv_tier == "Platinum":
            recommendations.append("VIP program: exclusive access and early launches")
            recommendations.append("Premium product recommendations only")
        elif price_sensitivity > 0.15:
            recommendations.append("Highlight deals, sales, and value propositions")
            recommendations.append("Price-match guarantees")
        elif expertise < 2.5:
            recommendations.append("Beginner guides and starter bundles")
            recommendations.append("Simple, clear product descriptions")
        else:
            recommendations.append("Balanced mix of quality and value messaging")
            recommendations.append("Loyalty rewards and exclusive offers")
        
        return {
            'segment_name_explanation': name_explanation,
            'segment_definition': "\n".join(segment_definition),
            'key_behaviors': key_behaviors,
            'marketing_recommendations': recommendations,
            'segment_size': segment_size,
            'avg_customer_value': avg_customer_value
        }
    
    def _explain_segment_name(
        self,
        segment_name: str,
        characteristics: Dict,
        ltv_tier: str
    ) -> str:
        """
        SIMPLE explanation of why this segment has this name
        """
        avg_value = characteristics.get('avg_customer_value', 0)
        brand_loyalty = characteristics['avg_brand_loyalty']
        price_sensitivity = characteristics['avg_price_sensitivity']
        purchase_freq = characteristics['avg_purchase_frequency']
        bundle_affinity = characteristics['avg_bundle_affinity']
        expertise = characteristics['avg_expertise']
        
        name_lower = segment_name.lower()
        
        # Premium/Value tier names
        if any(tier in name_lower for tier in ['premium', 'elite', 'vip', 'platinum', 'high-value']):
            return f"**'{segment_name}'** - {ltv_tier} tier customer (${avg_value:.0f}/year) who invests heavily in quality"
        elif any(tier in name_lower for tier in ['budget', 'thrifty', 'value', 'bronze', 'entry']):
            return f"**'{segment_name}'** - {ltv_tier} tier customer (${avg_value:.0f}/year) focused on value and deals"
        
        # Loyalty-based names
        elif any(loy in name_lower for loy in ['loyal', 'devotee', 'champion', 'trusted']):
            return f"**'{segment_name}'** - Strong brand loyalty ({brand_loyalty*100:.0f}%) with consistent brand preferences"
        
        # Price-sensitive names
        elif any(price in name_lower for price in ['deal', 'bargain', 'price', 'hunter', 'finder']):
            return f"**'{segment_name}'** - Price-conscious ({price_sensitivity*100:.0f}% check prices) who seek best deals"
        
        # Bundle/Kit buyer names
        elif any(bundle in name_lower for bundle in ['bundle', 'kit', 'package', 'system']):
            return f"**'{segment_name}'** - Prefer complete kits ({bundle_affinity*100:.0f}% bundle purchases) over individual items"
        
        # Frequency-based names
        elif any(freq in name_lower for freq in ['frequent', 'active', 'power', 'regular']):
            return f"**'{segment_name}'** - Frequent shoppers ({purchase_freq:.0f}x/year) with high engagement"
        
        # Expertise-based names
        elif any(exp in name_lower for exp in ['expert', 'specialist', 'pro', 'master', 'veteran']):
            return f"**'{segment_name}'** - Expert knowledge ({expertise:.1f}/5) with deep product understanding"
        elif any(beg in name_lower for beg in ['beginner', 'newcomer', 'starter', 'explorer', 'learner']):
            return f"**'{segment_name}'** - Beginner level ({expertise:.1f}/5) still learning about gear"
        
        # Category-based names
        elif any(cat in name_lower for cat in ['trail', 'hik', 'path']):
            return f"**'{segment_name}'** - Focus on hiking and trail products"
        elif any(cat in name_lower for cat in ['sleep', 'rest', 'comfort']):
            return f"**'{segment_name}'** - Prefer sleeping and comfort gear"
        
        # Default
        else:
            return f"**'{segment_name}'** - {ltv_tier} tier with unique shopping patterns (${avg_value:.0f}/year)"
    
    def _generate_micro_segment_name(
        self,
        characteristics: Dict,
        ltv_tier: str,
        macro_name: str,
        micro_id: int = 0
    ) -> str:
        """
        Generate UNIQUE micro segment name based on multiple characteristics
        Uses a multi-dimensional approach to ensure each segment has a distinct, meaningful name
        
        Args:
            characteristics: Segment characteristics
            ltv_tier: LTV tier (Bronze/Silver/Gold/Platinum)
            macro_name: Parent macro segment name
            micro_id: Micro segment ID for uniqueness
            
        Returns:
            Unique segment name based on combination of traits
        """
        # Extract all characteristics
        dominant_category = characteristics.get('dominant_category', 'General')
        brand_loyalty = characteristics['avg_brand_loyalty']
        price_sensitivity = characteristics['avg_price_sensitivity']
        purchase_freq = characteristics['avg_purchase_frequency']
        bundle_affinity = characteristics['avg_bundle_affinity']
        expertise = characteristics['avg_expertise']
        
        # Category descriptors
        category_descriptors = {
            'Hiking Backpacks': ['Trailblazers', 'Trail Seekers', 'Path Finders', 'Hikers'],
            'Sleeping Bags + Airbeds': ['Rest Seekers', 'Sleep Experts', 'Comfort Campers', 'Night Dwellers'],
            'Tents': ['Shelter Specialists', 'Camp Builders', 'Base Camp Pros', 'Refuge Makers'],
            'Camping Furniture': ['Comfort Seekers', 'Site Arrangers', 'Camp Decorators', 'Setup Pros'],
            'Coolers + Drinkware': ['Gear Masters', 'Supply Chiefs', 'Prep Experts', 'Storage Pros'],
            'Footwear': ['Trail Walkers', 'Terrain Specialists', 'Path Treaders', 'Step Masters'],
            'Apparel': ['Outdoor Stylists', 'Weather Prep', 'Gear Wearers', 'Outfit Pros']
        }
        
        # Expertise-based personas
        expertise_personas = {
            'expert': ['Elite', 'Masters', 'Veterans', 'Specialists'],
            'intermediate': ['Enthusiasts', 'Active', 'Regular', 'Experienced'],
            'beginner': ['Starters', 'Explorers', 'Newcomers', 'Learners']
        }
        
        # Value/spending personas
        value_personas = {
            'platinum': ['Premium Buyers', 'Elite Spenders', 'High Rollers', 'VIP Clients'],
            'gold': ['Value Maximizers', 'Smart Spenders', 'Quality Seekers', 'Prime Buyers'],
            'silver': ['Balanced Buyers', 'Mid-Range Shoppers', 'Practical Buyers', 'Steady Customers'],
            'bronze': ['Budget Conscious', 'Value Hunters', 'Deal Seekers', 'Thrifty Buyers']
        }
        
        # Behavior-based personas
        behavior_personas = {
            'bundle_lover': ['Bundle Enthusiasts', 'Kit Buyers', 'Package Seekers', 'Complete Set Buyers'],
            'brand_loyal': ['Brand Devotees', 'Loyal Fans', 'Brand Champions', 'Trusted Buyers'],
            'frequent_buyer': ['Active Shoppers', 'Regular Visitors', 'Frequent Buyers', 'Power Shoppers'],
            'price_sensitive': ['Deal Hunters', 'Price Watchers', 'Discount Seekers', 'Bargain Finders']
        }
        
        # Determine primary dimension (what makes this segment unique)
        dimensions_scores = []
        
        # Score each dimension
        if bundle_affinity > 0.15:
            dimensions_scores.append(('bundle', bundle_affinity * 2))
        if brand_loyalty > 0.6:
            dimensions_scores.append(('loyalty', brand_loyalty * 1.5))
        if purchase_freq > 10:
            dimensions_scores.append(('frequency', purchase_freq / 15.0))
        if price_sensitivity > 0.15:
            dimensions_scores.append(('price', price_sensitivity * 2))
        if expertise > 4.0:
            dimensions_scores.append(('expertise_high', expertise / 5.0))
        elif expertise < 2.5:
            dimensions_scores.append(('expertise_low', (5.0 - expertise) / 5.0))
        
        # Add value tier as a dimension
        tier_scores = {'Bronze': 0.3, 'Silver': 0.5, 'Gold': 0.7, 'Platinum': 0.9}
        dimensions_scores.append(('value', tier_scores.get(ltv_tier, 0.5)))
        
        # Sort by score to get primary and secondary characteristics
        dimensions_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Build name using top 2 dimensions + category
        primary_dim = dimensions_scores[0][0] if dimensions_scores else 'value'
        secondary_dim = dimensions_scores[1][0] if len(dimensions_scores) > 1 else None
        
        # Generate unique name based on dimension combination
        if primary_dim == 'bundle':
            base_options = behavior_personas['bundle_lover']
        elif primary_dim == 'loyalty':
            base_options = behavior_personas['brand_loyal']
        elif primary_dim == 'frequency':
            base_options = behavior_personas['frequent_buyer']
        elif primary_dim == 'price':
            base_options = behavior_personas['price_sensitive']
        elif primary_dim == 'expertise_high':
            base_options = expertise_personas['expert']
        elif primary_dim == 'expertise_low':
            base_options = expertise_personas['beginner']
        else:  # value tier
            tier_key = ltv_tier.lower()
            base_options = value_personas.get(tier_key, ['Outdoor Buyers'])
        
        # Use micro_id to select from options for uniqueness
        name_option = base_options[micro_id % len(base_options)]
        
        # For category-specific naming
        if dominant_category in category_descriptors:
            category_options = category_descriptors[dominant_category]
            category_name = category_options[micro_id % len(category_options)]
            
            # Combine category with behavior/value trait
            # Alternate between formats for variety
            if micro_id % 2 == 0:
                name = category_name
            else:
                name = name_option
        else:
            name = name_option
        
        return name
    
    def _get_top_customers(self, customers_df: pd.DataFrame, n: int = 5) -> List[Dict]:
        """
        Get top customers by spend in a micro segment
        
        Args:
            customers_df: Customer data
            n: Number of top customers to return
            
        Returns:
            List of top customer summaries
        """
        top_customers = customers_df.nlargest(n, 'total_spend_12mo')
        
        return [
            {
                'customer_id': row['customer_id'],
                'customer_name': row.get('customer_name', f"Customer {row['customer_id']}"),
                'total_spend': round(row['total_spend_12mo'], 2),
                'purchase_frequency': int(row['purchase_frequency']),
                # CRITICAL: Include dominant_category so recommendations match the segment!
                'dominant_category': row.get('dominant_category', 'Unknown'),
                'cluster': int(row.get('cluster', 0))  # Macro segment ID
            }
            for _, row in top_customers.iterrows()
        ]
    
    def execute_all_macro_segments(self, n_micro_segments: int = 4) -> Dict:
        """
        Execute micro segmentation for all macro segments
        
        Args:
            n_micro_segments: Number of micro segments per macro segment
            
        Returns:
            Dictionary with all micro segments
        """
        all_results = {}
        
        for macro_id in self.macro_personas.keys():
            result = self.execute(macro_id, n_micro_segments)
            if 'error' not in result:
                all_results[macro_id] = result
        
        return {
            'status': 'success',
            'micro_segments_by_macro': all_results,
            'total_macro_segments': len(all_results),
            'total_micro_segments': sum(
                r['n_micro_segments'] for r in all_results.values()
            )
        }


if __name__ == "__main__":
    print("="*70)
    print("Agent A Micro - Academy Sports Micro Segmentation")
    print("="*70)
    print("This agent creates sub-segments within macro personas")
    print("Run this through the main API after macro segmentation")
    print("="*70)


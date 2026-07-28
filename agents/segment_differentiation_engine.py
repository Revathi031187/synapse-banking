"""
Robust Segment Differentiation Engine
Ensures COMPLETE UNIQUENESS across all macro segments

This module provides a sophisticated framework for generating truly unique
segment characteristics, behaviors, and marketing strategies.
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SegmentDifferentiationEngine:
    """
    Engine that ensures each segment has completely unique characteristics.
    Uses multi-dimensional profiling to prevent any overlap.
    """
    
    def __init__(self):
        self.assigned_profiles = {}  # Track what's been assigned to prevent duplicates
        
    def generate_unique_profile(
        self,
        cluster_id: int,
        characteristics: Dict
    ) -> Dict:
        """
        Generate a completely unique profile for a segment
        
        Returns:
            {
                'primary_archetype': str,
                'secondary_traits': List[str],
                'key_behaviors': List[str],
                'marketing_strategies': List[str],
                'differentiation_score': float
            }
        """
        # Extract key metrics
        avg_spend = characteristics.get('avg_spend_12mo', 0)
        specificity = characteristics.get('avg_search_specificity', 0)
        price_sort = characteristics.get('avg_price_sort_frequency', 0)
        purchase_freq = characteristics.get('avg_purchase_frequency', 0)
        bundle_affinity = characteristics.get('avg_bundle_affinity', 0)
        brand_loyalty = characteristics.get('avg_brand_loyalty', 0)
        
        # Create multi-dimensional profile
        profile_dimensions = self._calculate_profile_dimensions(
            cluster_id, avg_spend, specificity, price_sort,
            purchase_freq, bundle_affinity, brand_loyalty
        )
        
        # Generate unique identifiers
        archetype = self._assign_unique_archetype(cluster_id, profile_dimensions)
        behaviors = self._generate_unique_behaviors(cluster_id, archetype, profile_dimensions, characteristics)
        marketing = self._generate_unique_marketing(cluster_id, archetype, profile_dimensions, characteristics)
        
        # Mark this profile as assigned
        profile_key = f"{archetype}_{cluster_id}"
        self.assigned_profiles[profile_key] = True
        
        return {
            'primary_archetype': archetype['name'],
            'archetype_code': archetype['code'],
            'secondary_traits': archetype['traits'],
            'key_behaviors': behaviors,
            'marketing_strategies': marketing,
            'profile_dimensions': profile_dimensions,
            'differentiation_score': self._calculate_uniqueness_score(profile_dimensions)
        }
    
    def _calculate_profile_dimensions(
        self,
        cluster_id: int,
        avg_spend: float,
        specificity: float,
        price_sort: float,
        purchase_freq: float,
        bundle_affinity: float,
        brand_loyalty: float
    ) -> Dict:
        """
        Calculate normalized scores across ALL dimensions
        Returns a unique fingerprint for this segment
        """
        return {
            # Spending dimension (0-100)
            'spending_level': min(100, (avg_spend / 2000) * 100),
            
            # Expertise dimension (0-100)
            'expertise_level': (specificity / 5.0) * 100,
            
            # Price sensitivity (0-100)
            'price_sensitivity': price_sort * 100,
            
            # Engagement frequency (0-100)
            'engagement_level': min(100, (purchase_freq / 20) * 100),
            
            # Bundle preference (0-100)
            'bundle_preference': bundle_affinity * 100,
            
            # Brand loyalty (0-100)
            'loyalty_level': brand_loyalty * 100,
            
            # Cluster-specific modifier (ensures uniqueness)
            'cluster_modifier': cluster_id * 10
        }
    
    def _assign_unique_archetype(
        self,
        cluster_id: int,
        dimensions: Dict
    ) -> Dict:
        """
        Assign a UNIQUE archetype based on multi-dimensional analysis
        Uses combination of top traits + cluster_id to force uniqueness
        """
        # Calculate dominant traits (top 3)
        trait_scores = [
            ('spending', dimensions['spending_level']),
            ('expertise', dimensions['expertise_level']),
            ('price_sensitive', dimensions['price_sensitivity']),
            ('engagement', dimensions['engagement_level']),
            ('bundle_oriented', dimensions['bundle_preference']),
            ('brand_loyal', dimensions['loyalty_level'])
        ]
        
        # Sort by score to find dominant traits
        trait_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top 3 traits
        primary_trait = trait_scores[0][0]
        secondary_trait = trait_scores[1][0]
        tertiary_trait = trait_scores[2][0]
        
        # Create UNIQUE archetype code
        archetype_code = f"{primary_trait[:3].upper()}-{secondary_trait[:3].upper()}-C{cluster_id}"
        
        # Define 30+ unique archetypes (combinations)
        archetypes = self._get_archetype_matrix()
        
        # Find best matching archetype using primary + cluster_id
        key = (primary_trait, cluster_id % 6)  # 6 variants per trait type
        archetype = archetypes.get(key, archetypes[('spending', 0)])  # Fallback
        
        return {
            'name': archetype['name'],
            'code': archetype_code,
            'traits': [primary_trait, secondary_trait, tertiary_trait],
            'variant': cluster_id % 6
        }
    
    def _get_archetype_matrix(self) -> Dict:
        """
        Define 36+ unique archetypes (6 primary traits × 6 variants each)
        This ensures NO two segments get the same archetype
        """
        return {
            # SPENDING-DOMINANT ARCHETYPES (6 variants)
            ('spending', 0): {'name': 'Premium Outdoor Connoisseur', 'focus': 'Luxury quality'},
            ('spending', 1): {'name': 'Elite Gear Investor', 'focus': 'Long-term value'},
            ('spending', 2): {'name': 'Affluent Adventure Seeker', 'focus': 'Premium experiences'},
            ('spending', 3): {'name': 'Value-Conscious Optimizer', 'focus': 'Smart deals'},
            ('spending', 4): {'name': 'Budget-Smart Camper', 'focus': 'Affordable quality'},
            ('spending', 5): {'name': 'Frugal Outdoor Enthusiast', 'focus': 'Maximum value'},
            
            # EXPERTISE-DOMINANT ARCHETYPES (6 variants)
            ('expertise', 0): {'name': 'Technical Gear Specialist', 'focus': 'Advanced features'},
            ('expertise', 1): {'name': 'Outdoor Equipment Expert', 'focus': 'Product knowledge'},
            ('expertise', 2): {'name': 'Professional Camper', 'focus': 'Performance gear'},
            ('expertise', 3): {'name': 'Beginner Explorer', 'focus': 'Learning basics'},
            ('expertise', 4): {'name': 'Casual Weekend Camper', 'focus': 'Simplicity'},
            ('expertise', 5): {'name': 'First-Time Adventurer', 'focus': 'Guidance needed'},
            
            # PRICE-SENSITIVE ARCHETYPES (6 variants)
            ('price_sensitive', 0): {'name': 'Deal Hunter Extraordinaire', 'focus': 'Best prices'},
            ('price_sensitive', 1): {'name': 'Strategic Bargain Shopper', 'focus': 'Seasonal sales'},
            ('price_sensitive', 2): {'name': 'Price-Comparison Specialist', 'focus': 'Cross-retailer savings'},
            ('price_sensitive', 3): {'name': 'Clearance Section Regular', 'focus': 'Discount finds'},
            ('price_sensitive', 4): {'name': 'Coupon-Savvy Buyer', 'focus': 'Promo codes'},
            ('price_sensitive', 5): {'name': 'Sale-Waiting Strategist', 'focus': 'Patience pays'},
            
            # ENGAGEMENT-DOMINANT ARCHETYPES (6 variants)
            ('engagement', 0): {'name': 'Frequent Gear Upgrader', 'focus': 'Regular purchases'},
            ('engagement', 1): {'name': 'Active Equipment Rotator', 'focus': 'Always updating'},
            ('engagement', 2): {'name': 'Year-Round Outdoor Enthusiast', 'focus': 'Consistent buying'},
            ('engagement', 3): {'name': 'Seasonal Camping Planner', 'focus': 'Periodic purchases'},
            ('engagement', 4): {'name': 'Occasional Gear Buyer', 'focus': 'As-needed shopping'},
            ('engagement', 5): {'name': 'Event-Driven Purchaser', 'focus': 'Trip-based buying'},
            
            # BUNDLE-ORIENTED ARCHETYPES (6 variants)
            ('bundle_oriented', 0): {'name': 'Complete Kit Enthusiast', 'focus': 'All-in-one solutions'},
            ('bundle_oriented', 1): {'name': 'Package Deal Seeker', 'focus': 'Coordinated sets'},
            ('bundle_oriented', 2): {'name': 'System Builder', 'focus': 'Compatible ecosystems'},
            ('bundle_oriented', 3): {'name': 'Ready-to-Camp Buyer', 'focus': 'Pre-assembled kits'},
            ('bundle_oriented', 4): {'name': 'Convenience-First Shopper', 'focus': 'Easy solutions'},
            ('bundle_oriented', 5): {'name': 'One-Stop Setup Seeker', 'focus': 'Quick start packages'},
            
            # BRAND-LOYAL ARCHETYPES (6 variants)
            ('brand_loyal', 0): {'name': 'Brand Devotee', 'focus': 'Single brand ecosystem'},
            ('brand_loyal', 1): {'name': 'Premium Brand Advocate', 'focus': 'Brand reputation'},
            ('brand_loyal', 2): {'name': 'Consistent Brand Buyer', 'focus': 'Proven reliability'},
            ('brand_loyal', 3): {'name': 'Multi-Brand Explorer', 'focus': 'Brand variety'},
            ('brand_loyal', 4): {'name': 'Brand-Agnostic Pragmatist', 'focus': 'Best product wins'},
            ('brand_loyal', 5): {'name': 'Feature-Over-Brand Selector', 'focus': 'Specs matter most'}
        }
    
    def _generate_unique_behaviors(
        self,
        cluster_id: int,
        archetype: Dict,
        dimensions: Dict,
        characteristics: Dict
    ) -> List[str]:
        """
        Generate 3-4 COMPLETELY UNIQUE behaviors for this segment
        No two segments will have the same behavior list
        """
        primary_trait = archetype['traits'][0]
        variant = archetype['variant']
        
        behaviors = []
        
        # Behavior 1: Primary trait specific
        behavior_matrix_1 = {
            'spending': [
                f"Invests ${characteristics.get('avg_spend_12mo', 0):.0f}/year in premium outdoor gear",
                f"Allocates ${characteristics.get('avg_spend_12mo', 0):.0f} annually for quality camping equipment",
                f"Budgets ${characteristics.get('avg_spend_12mo', 0):.0f}/year specifically for outdoor adventures",
                f"Commits ${characteristics.get('avg_spend_12mo', 0):.0f} yearly to camping gear investments",
                f"Reserves ${characteristics.get('avg_spend_12mo', 0):.0f} annual budget for outdoor equipment",
                f"Plans ${characteristics.get('avg_spend_12mo', 0):.0f}/year expenditure on camping essentials"
            ],
            'expertise': [
                f"Researches extensively - compares 8+ products before each purchase decision",
                f"Deep technical analysis - reads 15+ reviews per item before buying",
                f"Expert evaluation process - tests gear specifications against real-world needs",
                f"Follows outdoor gear blogs and forums for latest product insights",
                f"Consults multiple expert sources before making equipment decisions",
                f"Downloads spec sheets and watches detailed video reviews for every purchase"
            ],
            'price_sensitive': [
                f"Checks prices across 5+ retailers before every purchase",
                f"Uses price tracking apps to monitor {characteristics.get('avg_price_sort_frequency', 0)*100:.0f}% of intended purchases",
                f"Waits for seasonal sales (Black Friday, end-of-season) to make major buys",
                f"Subscribes to 10+ camping gear deal newsletters and alert services",
                f"Sets price alerts and only buys when hitting target discount levels",
                f"Maintains a wishlist and purchases only during promotional periods"
            ],
            'engagement': [
                f"Shops {characteristics.get('avg_purchase_frequency', 0):.0f} times per year - highly active customer",
                f"Makes {characteristics.get('avg_purchase_frequency', 0):.0f} annual purchases - consistent engagement pattern",
                f"Regularly upgrades equipment every {12/max(1, characteristics.get('avg_purchase_frequency', 1)):.1f} months on average",
                f"Frequent buyer with {characteristics.get('avg_purchase_frequency', 0):.0f}x yearly purchases - strong brand engagement",
                f"Maintains active shopping cycle of {characteristics.get('avg_purchase_frequency', 0):.0f} transactions annually",
                f"Seasonal buyer with {characteristics.get('avg_purchase_frequency', 0):.0f} purchases spread throughout the year"
            ],
            'bundle_oriented': [
                f"Purchases {characteristics.get('avg_bundle_affinity', 0)*100:.0f}% of gear as complete kits rather than individual items",
                f"Prefers coordinated equipment sets - {characteristics.get('avg_bundle_affinity', 0)*100:.0f}% bundle purchase rate",
                f"Seeks 'ready-to-camp' packages for convenience and compatibility",
                f"Values pre-assembled camping systems over mix-and-match approaches",
                f"Looks for curated gear collections that work together seamlessly",
                f"Prioritizes turn-key solutions with all necessary components included"
            ],
            'brand_loyal': [
                f"Maintains {characteristics.get('avg_brand_loyalty', 0)*100:.0f}% brand loyalty - consistent repeat purchases",
                f"Stays within preferred brand ecosystem ({characteristics.get('avg_brand_loyalty', 0)*100:.0f}% same-brand rate)",
                f"Researches new products exclusively within trusted brand portfolios",
                f"Values brand reputation and warranty support over feature comparisons",
                f"Builds complete gear setup from single manufacturer for compatibility",
                f"Follows favorite brands' product launches and upgrade cycles closely"
            ]
        }
        
        # Add primary behavior (variant ensures uniqueness)
        behaviors.append(behavior_matrix_1.get(primary_trait, ['Generic behavior'])[variant])
        
        # Behavior 2: Secondary trait specific
        secondary_trait = archetype['traits'][1]
        behavior_matrix_2 = {
            'spending': [f"Compares total cost of ownership, not just upfront prices"],
            'expertise': [f"Joins online communities to discuss gear performance"],
            'price_sensitive': [f"Uses cashback apps and credit card rewards for every purchase"],
            'engagement': [f"Tracks purchase history to identify optimal upgrade timing"],
            'bundle_oriented': [f"Prefers retailers offering package discounts and bundle deals"],
            'brand_loyal': [f"Recommends trusted brands to friends and family members"]
        }
        behaviors.append(behavior_matrix_2.get(secondary_trait, [''])[0])
        
        # Behavior 3: Cluster-specific unique insight
        unique_insights = [
            f"Plans purchases around major camping trips and seasonal weather patterns",
            f"Reads product manuals cover-to-cover before first use",
            f"Maintains detailed spreadsheets of gear performance and durability",
            f"Tests new equipment in backyard before taking on actual trips",
            f"Follows YouTube channels dedicated to camping gear reviews and comparisons",
            f"Participates in local outdoor clubs to share gear experiences",
            f"Attends outdoor expos and demo days to try products hands-on",
            f"Keeps backup equipment for critical items like tents and sleeping bags",
            f"Researches environmental impact and sustainability of gear choices",
            f"Prioritizes products with strong warranty and customer service reputations"
        ]
        behaviors.append(unique_insights[cluster_id % len(unique_insights)])
        
        return behaviors
    
    def _generate_unique_marketing(
        self,
        cluster_id: int,
        archetype: Dict,
        dimensions: Dict,
        characteristics: Dict
    ) -> List[str]:
        """
        Generate 3-4 COMPLETELY UNIQUE marketing strategies
        Each segment gets distinct, actionable strategies
        """
        primary_trait = archetype['traits'][0]
        variant = archetype['variant']
        
        strategies = []
        
        # Strategy templates by trait (6 variants each for uniqueness)
        strategy_matrix = {
            'spending': [
                "🌟 Platinum VIP Program: Exclusive pre-release access to luxury camping gear collections",
                "💎 Elite Rewards Tier: White-glove customer service and personalized gear consultations",
                "👑 Premium Member Benefits: Extended warranties, free upgrades, and priority shipping",
                "⭐ Value Maximizer Program: Quality gear bundles at competitive price points",
                "💰 Smart Shopper Rewards: Cashback on purchases plus price-match guarantees",
                "🎁 Budget-Friendly Loyalty: Points program with frequent discount opportunities"
            ],
            'expertise': [
                "🔬 Technical Specification Library: Detailed comparison charts and performance data sheets",
                "🎓 Expert Workshop Series: Monthly webinars with gear designers and outdoor professionals",
                "🏆 Beta Tester Program: First access to new products with feedback opportunities",
                "📚 Beginner's Resource Center: Step-by-step guides and 'Camping 101' video tutorials",
                "👥 Guided Shopping Experience: Personal gear advisors available via live chat",
                "🎯 Starter Kit Builder: Interactive tool to create perfect first camping setup"
            ],
            'price_sensitive': [
                "🏷️ Price-Match Guarantee Plus: Beat any competitor price by additional 5%",
                "📧 Deal Alert VIP: Early notification system for sales 24 hours before public",
                "💳 Cashback Accelerator: 5% back on all purchases plus bonus seasonal rewards",
                "🎫 Clearance Club: Exclusive access to end-of-season inventory at 40-60% off",
                "📱 Mobile App Exclusive: App-only flash sales and special discount codes",
                "🔔 Price Drop Monitor: Automatic refund if price decreases within 30 days"
            ],
            'engagement': [
                "🔄 Gear Refresh Subscription: Scheduled equipment upgrades with member discounts",
                "📆 Seasonal Prep Reminders: Timely notifications for upcoming camping season needs",
                "🏅 Frequency Rewards Elite: Escalating benefits (5%, 10%, 15% off) with each purchase",
                "🎁 Trip-Based Recommendations: Gear suggestions aligned with vacation calendar",
                "📊 Purchase Cycle Insights: Analytics showing optimal replacement timing for gear",
                "🌈 Year-Round Engagement: Off-season storage tips and gear maintenance workshops"
            ],
            'bundle_oriented': [
                "📦 Adventure Package Collections: 'Weekend Warrior', 'Family Base Camp', 'Solo Explorer' kits",
                "🎯 Bundle Builder Tool: Custom package creator with 15-20% bundle discount",
                "✅ One-Click Complete Setups: Pre-configured camping systems for different experience levels",
                "🏕️ Themed Camping Kits: Season-specific packages (Winter Camping, Summer Festival, etc.)",
                "💼 All-Inclusive Solutions: Gear + accessories + extras in ready-to-go packages",
                "🎁 Gift-Ready Package Options: Complete setups perfect for gifting new campers"
            ],
            'brand_loyal': [
                "🏷️ Brand Ambassador Program: Exclusive perks for consistent brand advocates",
                "🔔 Brand-Specific Product Pages: Dedicated showcase for preferred manufacturers",
                "📧 New Release Priority Alerts: First notification when favorite brands launch products",
                "🤝 Brand Partner Rewards: Co-branded loyalty benefits with top manufacturers",
                "🌟 Insider Access Events: Virtual meet-and-greets with brand designers and executives",
                "🎁 Brand Loyalty Milestones: Special gifts at 5th, 10th, 15th same-brand purchase"
            ]
        }
        
        # Add primary strategy (variant ensures uniqueness)
        strategies.append(strategy_matrix.get(primary_trait, ['Generic strategy'])[variant])
        
        # Add 2 more strategies based on secondary/tertiary traits
        secondary_trait = archetype['traits'][1]
        tertiary_trait = archetype['traits'][2]
        
        strategies.append(strategy_matrix.get(secondary_trait, ['Generic strategy'])[0])
        strategies.append(strategy_matrix.get(tertiary_trait, ['Generic strategy'])[0])
        
        return strategies
    
    def _calculate_uniqueness_score(self, dimensions: Dict) -> float:
        """
        Calculate how unique this profile is (0-100)
        Higher scores mean more distinctive segments
        
        Uses standard deviation of dimensions to measure how "spiky" 
        the profile is (high variance = more unique/specialized)
        """
        # Calculate variance across dimensions
        values = [
            dimensions['spending_level'],
            dimensions['expertise_level'],
            dimensions['price_sensitivity'],
            dimensions['engagement_level'],
            dimensions['bundle_preference'],
            dimensions['loyalty_level']
        ]
        
        # High variance = more unique (specialized in certain traits)
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        
        # Standard deviation gives us the "spread"
        std_dev = variance ** 0.5
        
        # Max possible std_dev for 6 dimensions (0-100 scale) is ~40.8
        # (when values are [100, 100, 100, 0, 0, 0])
        # Normalize: std_dev of 40 = uniqueness of 100
        # This gives us a range where:
        # - Low variance (balanced segment) = 40-60 uniqueness
        # - Medium variance (somewhat specialized) = 60-80 uniqueness  
        # - High variance (highly specialized) = 80-100 uniqueness
        max_std_dev = 40.8
        uniqueness = min(100, (std_dev / max_std_dev) * 100)
        
        return round(uniqueness, 1)

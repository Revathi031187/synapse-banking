"""
Cluster Naming Utility
Generates business-friendly, meaningful names for customer clusters
based on their characteristics instead of generic "Cluster 1", "Cluster 2", etc.
"""

from typing import Dict, Any, List
import pandas as pd


class ClusterNamer:
    """Generates meaningful names for customer clusters based on their characteristics"""
    
    def __init__(self):
        pass
    
    def name_banking_cluster(self, persona: Dict[str, Any]) -> str:
        """
        Generate a meaningful name for a banking cluster based on characteristics
        
        Args:
            persona: Dictionary containing cluster statistics
            
        Returns:
            Business-friendly cluster name
        """
        # Extract key metrics
        avg_intent = persona.get('avg_intent', 0)
        avg_engagement = persona.get('avg_engagement', 0)  # login_frequency_30d
        avg_income = persona.get('avg_income', 0)
        avg_credit_score = persona.get('avg_credit_score', 0)
        avg_tenure = persona.get('avg_tenure', 0)
        
        # Categorize metrics
        high_intent = avg_intent > 0.6
        medium_intent = 0.3 < avg_intent <= 0.6
        low_intent = avg_intent <= 0.3
        
        high_engagement = avg_engagement >= 7  # >= 7 logins/month
        medium_engagement = 3 <= avg_engagement < 7
        low_engagement = avg_engagement < 3
        
        high_income = avg_income >= 120000
        medium_income = 60000 <= avg_income < 120000
        
        high_credit = avg_credit_score >= 750
        medium_credit = 650 <= avg_credit_score < 750
        
        long_tenure = avg_tenure >= 36  # 3+ years
        medium_tenure = 12 <= avg_tenure < 36
        new_customer = avg_tenure < 12
        
        # Generate name based on characteristics
        
        # High value segments
        if high_income and high_credit and high_engagement:
            return "💎 Premium Active Clients"
        
        if high_income and high_credit:
            return "🌟 Affluent Banking Clients"
        
        if high_intent and high_engagement and long_tenure:
            return "🎯 Loyal High-Intent Champions"
        
        # Engaged segments
        if high_intent and high_engagement:
            return "🔥 Active Prospects"
        
        if high_engagement and medium_intent:
            return "👤 Engaged Explorers"
        
        if high_engagement and low_intent:
            return "📱 Digital Browsers"
        
        # Intent-driven segments
        if high_intent and medium_engagement:
            return "💰 Ready-to-Convert Prospects"
        
        if high_intent and low_engagement:
            return "🎪 High-Intent Window Shoppers"
        
        if medium_intent and medium_engagement:
            return "🌱 Growing Potential Customers"
        
        # Loyalty segments
        if long_tenure and high_engagement:
            return "🏆 Loyal Active Members"
        
        if long_tenure and medium_engagement:
            return "🤝 Established Customers"
        
        # Value-based segments
        if high_credit and high_intent:
            return "⭐ Prime Credit Prospects"
        
        if medium_credit and high_intent:
            return "📈 Aspiring Borrowers"
        
        # New customer segments
        if new_customer and high_engagement:
            return "✨ New Active Customers"
        
        if new_customer and medium_engagement:
            return "🌟 Fresh Onboardees"
        
        # At-risk segments
        if low_engagement and low_intent:
            return "💤 Dormant Accounts"
        
        if low_engagement and medium_intent:
            return "⚠️ At-Risk Low Engagement"
        
        if medium_engagement and low_intent:
            return "🔄 Periodic Users"
        
        # Default categories
        if high_income:
            return "💼 High-Net-Worth Segment"
        
        if medium_income:
            return "👔 Middle-Income Segment"
        
        # Fallback
        return f"📊 Standard Banking Segment"
    
    def name_retail_cluster(self, persona: Dict[str, Any]) -> str:
        """
        Generate a meaningful name for a retail cluster based on characteristics
        
        Args:
            persona: Dictionary containing cluster statistics
            
        Returns:
            Business-friendly cluster name
        """
        # Extract key metrics
        avg_intent = persona.get('avg_intent', 0)
        avg_engagement = persona.get('avg_engagement', 0)  # web_visits_30d
        avg_recency = persona.get('avg_recency', 0)  # RFM Recency
        avg_frequency = persona.get('avg_frequency', 0)  # RFM Frequency
        avg_monetary = persona.get('avg_monetary', 0)  # RFM Monetary
        avg_aov = persona.get('avg_aov', 0)  # Average Order Value
        avg_income = persona.get('avg_income', 0)
        dominant_category = persona.get('dominant_category', 'Unknown')
        
        # Calculate RFM score
        rfm_score = (avg_recency + avg_frequency + avg_monetary) / 3
        
        # Categorize metrics
        high_intent = avg_intent > 0.6
        medium_intent = 0.3 < avg_intent <= 0.6
        low_intent = avg_intent <= 0.3
        
        high_engagement = avg_engagement > 8  # > 8 visits/month
        medium_engagement = 3 <= avg_engagement <= 8
        low_engagement = avg_engagement < 3
        
        high_rfm = rfm_score >= 4.0  # RFM scale 1-5
        medium_rfm = 2.5 <= rfm_score < 4.0
        low_rfm = rfm_score < 2.5
        
        high_aov = avg_aov >= 150
        medium_aov = 75 <= avg_aov < 150
        
        high_income = avg_income >= 100000
        
        # Generate name based on characteristics
        
        # VIP segments
        if high_rfm and high_engagement and high_aov:
            return "👑 VIP Elite Shoppers"
        
        if high_rfm and high_engagement:
            return "💎 Loyal Champions"
        
        if high_rfm and high_intent:
            return "🌟 High-Value Active Buyers"
        
        # Engaged shoppers
        if high_engagement and high_intent:
            return "🔥 Hot Leads"
        
        if high_engagement and medium_intent:
            return "🛍️ Frequent Browsers"
        
        if high_engagement and low_intent:
            return "👀 Window Shoppers"
        
        # Intent-driven segments
        if high_intent and medium_engagement:
            return "🎯 Ready-to-Buy Prospects"
        
        if high_intent and low_engagement:
            return "💡 Interested Visitors"
        
        if medium_intent and medium_engagement:
            return "🌱 Casual Shoppers"
        
        # RFM-based segments
        if high_rfm and medium_engagement:
            return "🏆 Best Customers"
        
        if medium_rfm and high_engagement:
            return "📈 Growing Regulars"
        
        if medium_rfm and medium_engagement:
            return "🤝 Steady Shoppers"
        
        if low_rfm and high_engagement:
            return "🔍 Browsers Seeking Value"
        
        # AOV-based segments
        if high_aov and high_intent:
            return "💰 High-Ticket Buyers"
        
        if high_aov and medium_engagement:
            return "🎁 Premium Purchasers"
        
        if medium_aov and high_frequency:
            return "🔄 Frequent Mid-Tier Buyers"
        
        # Recency-based segments
        if avg_recency >= 4 and high_engagement:
            return "🆕 Recently Active"
        
        if avg_recency >= 4 and medium_engagement:
            return "✨ New Shoppers"
        
        if avg_recency < 2 and low_engagement:
            return "💤 Dormant Customers"
        
        # At-risk segments
        if low_engagement and low_intent:
            return "⚠️ Inactive Accounts"
        
        if low_engagement and medium_intent:
            return "🔔 Re-Engagement Opportunity"
        
        if medium_engagement and low_intent:
            return "🌊 Occasional Visitors"
        
        # Category-based segments (if available)
        if dominant_category != 'Unknown':
            if high_rfm:
                return f"🏅 {dominant_category} Enthusiasts"
            if high_engagement:
                return f"🛒 {dominant_category} Shoppers"
        
        # Income-based segments
        if high_income and high_engagement:
            return "💼 Affluent Active Shoppers"
        
        if high_income:
            return "💳 High-Income Segment"
        
        # Fallback
        return "📦 Standard Retail Segment"
    
    def assign_cluster_names_bulk(self, personas: List[Dict[str, Any]], industry: str) -> List[Dict[str, Any]]:
        """
        Assign meaningful names to all personas in a list
        
        Args:
            personas: List of persona dictionaries
            industry: 'banking' or 'retail'
            
        Returns:
            Updated personas list with cluster_name field
        """
        named_personas = []
        
        for persona in personas:
            if industry.lower() == 'banking':
                cluster_name = self.name_banking_cluster(persona)
            elif industry.lower() == 'retail':
                cluster_name = self.name_retail_cluster(persona)
            else:
                cluster_name = f"Segment {persona.get('cluster_id', 0)}"
            
            # Add cluster_name to persona
            persona['cluster_name'] = cluster_name
            named_personas.append(persona)
        
        return named_personas


# Global instance
cluster_namer = ClusterNamer()


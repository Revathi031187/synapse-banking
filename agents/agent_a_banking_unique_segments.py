"""
Agent A Enhanced - Banking with Unique Segment Names
Ensures no duplicate persona names and provides detailed explanations
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from pathlib import Path

try:
    from kmodes.kprototypes import KPrototypes
    KMODES_AVAILABLE = True
except ImportError:
    KMODES_AVAILABLE = False

logger = logging.getLogger(__name__)


class AgentA_Banking_UniqueSegments:
    """
    Enhanced Agent A for Banking with unique segment name generation
    Ensures no duplicate names and provides rich explanations
    """
    
    def __init__(self, data_path: str = 'data/preloaded/banking'):
        self.data_path = Path(data_path)
        self.customers_df = None
        self.cluster_model = None
        self.personas = {}
        
    def load_data(self):
        """Load banking data"""
        try:
            self.customers_df = pd.read_csv(self.data_path / 'customers.csv')
            logger.info(f"✓ Loaded {len(self.customers_df)} customers")
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False
    
    def execute(self, n_clusters=5, gamma=0.5):
        """Execute clustering with unique persona names"""
        if not KMODES_AVAILABLE:
            raise ImportError("kmodes package required. Run: pip install kmodes")
        
        # Prepare features
        numeric_cols = [
            'age', 'income', 'credit_score', 'account_balance',
            'digital_engagement_score', 'branch_visit_frequency',
            'product_adoption_rate', 'transaction_frequency',
            'cross_sell_receptivity', 'risk_tolerance',
            'savings_rate', 'investment_interest',
            'intent_score', 'customer_lifetime_value'
        ]
        
        categorical_cols = [
            'geographic_region', 'home_ownership', 'employment_status',
            'marital_status', 'education_level'
        ]
        
        # Prepare data
        df_cluster = self.customers_df[numeric_cols + categorical_cols].copy()
        
        # Fill missing values
        for col in numeric_cols:
            df_cluster[col].fillna(df_cluster[col].median(), inplace=True)
        for col in categorical_cols:
            df_cluster[col].fillna('Unknown', inplace=True)
        
        # Normalize numeric features
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        df_cluster[numeric_cols] = scaler.fit_transform(df_cluster[numeric_cols])
        
        # Categorical indices
        categorical_indices = [df_cluster.columns.get_loc(col) for col in categorical_cols]
        
        # Run clustering
        kproto = KPrototypes(n_clusters=n_clusters, init='Cao', gamma=gamma, verbose=0, n_jobs=-1)
        clusters = kproto.fit_predict(df_cluster.values, categorical=categorical_indices)
        
        self.cluster_model = kproto
        self.customers_df['cluster'] = clusters
        
        # Generate unique personas
        self.personas = self._generate_unique_personas()
        
        # Calculate silhouette score
        from sklearn.metrics import silhouette_score
        try:
            silhouette = silhouette_score(df_cluster[numeric_cols], clusters)
        except:
            silhouette = 0.0
        
        return {
            'status': 'success',
            'personas': self.personas,
            'total_customers': len(self.customers_df),
            'n_clusters': n_clusters,
            'silhouette_score': float(silhouette)
        }
    
    def _generate_unique_personas(self) -> Dict:
        """Generate personas with unique names and rich explanations"""
        personas = {}
        used_names = set()
        
        # Banking persona archetypes with unique patterns
        archetypes = [
            {
                'patterns': ['Premium Wealth Investors', 'Elite Banking Portfolio', 'High Net Worth Advisees'],
                'emoji': '💼',
                'criteria': lambda chars: chars['avg_balance'] > 150000 and chars['avg_intent'] > 0.7
            },
            {
                'patterns': ['Rising Career Professionals', 'Growth-Focused Millennials', 'Ambitious Young Bankers'],
                'emoji': '🚀',
                'criteria': lambda chars: chars['avg_age'] < 40 and chars['avg_income'] > 60000
            },
            {
                'patterns': ['Business Banking Clients', 'Entrepreneur Account Holders', 'SMB Finance Managers'],
                'emoji': '🏢',
                'criteria': lambda chars: chars['avg_balance'] > 50000 and chars['avg_risk'] > 0.6
            },
            {
                'patterns': ['Digital-First Gen Z', 'Mobile Banking Natives', 'Tech-Savvy Customers'],
                'emoji': '📱',
                'criteria': lambda chars: chars['avg_digital'] > 0.75 and chars['avg_age'] < 35
            },
            {
                'patterns': ['Conservative Savers', 'Steady Deposit Builders', 'Risk-Averse Investors'],
                'emoji': '💰',
                'criteria': lambda chars: chars['avg_savings_rate'] > 0.2 and chars['avg_risk'] < 0.4
            },
            {
                'patterns': ['Retirement Planners', 'Pre-Retiree Investors', 'Wealth Preservers'],
                'emoji': '🏡',
                'criteria': lambda chars: chars['avg_age'] > 55 and chars['avg_balance'] > 80000
            },
            {
                'patterns': ['Active Transaction Users', 'High-Frequency Bankers', 'Daily Banking Customers'],
                'emoji': '⚡',
                'criteria': lambda chars: chars['avg_transactions'] > 100
            },
            {
                'patterns': ['Branch-Preferred Customers', 'In-Person Banking Loyalists', 'Traditional Service Seekers'],
                'emoji': '🏛️',
                'criteria': lambda chars: chars['avg_branch_visits'] > 0.6
            },
            {
                'patterns': ['Investment Enthusiasts', 'Portfolio Diversifiers', 'Market Participants'],
                'emoji': '📈',
                'criteria': lambda chars: chars['avg_investment'] > 0.7
            },
            {
                'patterns': ['Budget-Conscious Customers', 'Fee-Sensitive Accounts', 'Value-Seeking Bankers'],
                'emoji': '💸',
                'criteria': lambda chars: chars['avg_income'] < 50000
            }
        ]
        
        for cluster_id in range(self.cluster_model.n_clusters):
            cluster_customers = self.customers_df[self.customers_df['cluster'] == cluster_id]
            
            # Calculate characteristics
            chars = {
                'avg_age': float(cluster_customers['age'].mean()),
                'avg_income': float(cluster_customers['income'].mean()),
                'avg_balance': float(cluster_customers['account_balance'].mean()),
                'avg_credit': float(cluster_customers['credit_score'].mean()),
                'avg_digital': float(cluster_customers['digital_engagement_score'].mean()),
                'avg_branch_visits': float(cluster_customers['branch_visit_frequency'].mean()),
                'avg_transactions': float(cluster_customers['transaction_frequency'].mean()),
                'avg_intent': float(cluster_customers['intent_score'].mean()),
                'avg_risk': float(cluster_customers['risk_tolerance'].mean()),
                'avg_savings_rate': float(cluster_customers['savings_rate'].mean()),
                'avg_investment': float(cluster_customers['investment_interest'].mean())
            }
            
            # Match to best archetype
            best_match = None
            best_score = -1
            
            for archetype in archetypes:
                try:
                    if archetype['criteria'](chars):
                        # Find unused name from this archetype
                        for pattern in archetype['patterns']:
                            if pattern not in used_names:
                                best_match = {'name': pattern, 'emoji': archetype['emoji']}
                                best_score = 1
                                break
                        if best_match:
                            break
                except:
                    continue
            
            # Fallback to generic name if no match
            if not best_match:
                for archetype in archetypes:
                    for pattern in archetype['patterns']:
                        if pattern not in used_names:
                            best_match = {'name': pattern, 'emoji': archetype['emoji']}
                            break
                    if best_match:
                        break
            
            # Final fallback
            if not best_match:
                base_name = f"Banking Segment {cluster_id + 1}"
                counter = 1
                while base_name in used_names:
                    base_name = f"Banking Segment {cluster_id + 1}-{counter}"
                    counter += 1
                best_match = {'name': base_name, 'emoji': '💼'}
            
            persona_name = best_match['name']
            used_names.add(persona_name)
            
            # Generate detailed description
            description = self._generate_description(persona_name, chars)
            
            # Generate segment explanation
            explanation = self._generate_segment_explanation(persona_name, chars, len(cluster_customers))
            
            personas[cluster_id] = {
                'cluster_id': cluster_id,
                'persona_name': persona_name,
                'name': persona_name,
                'emoji': best_match['emoji'],
                'description': description,
                'size': len(cluster_customers),
                'percentage': round(len(cluster_customers) / len(self.customers_df) * 100, 1),
                'avg_balance': round(chars['avg_balance'], 2),
                'avg_transactions': round(chars['avg_transactions'], 1),
                'avg_intent_score': round(chars['avg_intent'], 3),
                'avg_age': round(chars['avg_age'], 1),
                'avg_income': round(chars['avg_income'], 0),
                'avg_credit_score': round(chars['avg_credit'], 0),
                'confidence_avg': 0.85,
                'characteristics': chars,
                'segment_explanation': explanation
            }
        
        return personas
    
    def _generate_description(self, persona_name: str, chars: Dict) -> str:
        """Generate rich description for persona"""
        age = chars['avg_age']
        income = chars['avg_income']
        balance = chars['avg_balance']
        digital = chars['avg_digital']
        
        if 'Wealth' in persona_name or 'Premium' in persona_name or 'Elite' in persona_name:
            return f"Affluent customers (avg age {age:.0f}) with ${balance:,.0f} average balance seeking sophisticated wealth management and premium services"
        elif 'Young' in persona_name or 'Rising' in persona_name or 'Career' in persona_name:
            return f"Career-building professionals (avg age {age:.0f}, ${income:,.0f} income) with high growth potential and digital preferences"
        elif 'Business' in persona_name or 'Entrepreneur' in persona_name or 'SMB' in persona_name:
            return f"Business owners (avg balance ${balance:,.0f}) managing both personal and commercial banking relationships"
        elif 'Digital' in persona_name or 'Mobile' in persona_name or 'Tech' in persona_name:
            return f"Tech-savvy customers (avg age {age:.0f}) with {digital*100:.0f}% digital engagement preferring mobile-first banking"
        elif 'Saver' in persona_name or 'Conservative' in persona_name or 'Steady' in persona_name:
            return f"Cautious savers (${balance:,.0f} avg balance) focused on deposit growth and capital preservation"
        elif 'Retirement' in persona_name or 'Pre-Retiree' in persona_name:
            return f"Near-retirement customers (avg age {age:.0f}) prioritizing income generation and wealth preservation"
        elif 'Budget' in persona_name or 'Value' in persona_name or 'Fee-Sensitive' in persona_name:
            return f"Cost-conscious customers (${income:,.0f} income) seeking fee-free banking and value-driven products"
        elif 'Investment' in persona_name or 'Portfolio' in persona_name or 'Market' in persona_name:
            return f"Investment-focused customers with strong interest in brokerage and wealth management products"
        elif 'Branch' in persona_name or 'Traditional' in persona_name or 'In-Person' in persona_name:
            return f"Traditional banking customers preferring branch interactions and personal service"
        else:
            return f"Customer segment (avg age {age:.0f}, ${balance:,.0f} balance) with distinctive banking behaviors and needs"
    
    def _generate_segment_explanation(self, persona_name: str, chars: Dict, size: int) -> Dict:
        """Generate detailed segment explanation"""
        balance = chars['avg_balance']
        income = chars['avg_income']
        intent = chars['avg_intent']
        digital = chars['avg_digital']
        transactions = chars['avg_transactions']
        
        # Key behaviors
        key_behaviors = []
        if digital > 0.7:
            key_behaviors.append(f"Heavy digital banking usage ({digital*100:.0f}% engagement)")
        if transactions > 80:
            key_behaviors.append(f"High transaction frequency ({transactions:.0f} per month)")
        if balance > 100000:
            key_behaviors.append(f"Substantial account balances (avg ${balance:,.0f})")
        if intent > 0.75:
            key_behaviors.append(f"High intent for new products ({intent*100:.0f}% score)")
        if income > 150000:
            key_behaviors.append(f"High-income earners (avg ${income:,.0f}/year)")
        
        # Marketing recommendations
        recommendations = []
        if 'Wealth' in persona_name or 'Premium' in persona_name:
            recommendations.append("Wealth management and private banking services")
            recommendations.append("Premium credit cards with travel and concierge benefits")
            recommendations.append("Investment advisory and portfolio management")
        elif 'Young' in persona_name or 'Career' in persona_name:
            recommendations.append("Mobile-first banking features and apps")
            recommendations.append("Career development loans and credit building products")
            recommendations.append("Automated savings and investment tools")
        elif 'Business' in persona_name or 'Entrepreneur' in persona_name:
            recommendations.append("Business checking and credit lines")
            recommendations.append("Merchant services and payment processing")
            recommendations.append("Business credit cards and commercial loans")
        elif 'Digital' in persona_name or 'Tech' in persona_name:
            recommendations.append("Cryptocurrency and fintech integrations")
            recommendations.append("API banking and developer tools")
            recommendations.append("Instant payment and peer-to-peer features")
        elif 'Saver' in persona_name or 'Conservative' in persona_name:
            recommendations.append("High-yield savings accounts and CDs")
            recommendations.append("Money market accounts and bonds")
            recommendations.append("FDIC-insured products and capital preservation")
        else:
            recommendations.append("Personalized product recommendations")
            recommendations.append("Fee reduction and value programs")
            recommendations.append("Financial education and planning tools")
        
        # Segment definition
        definition_lines = [
            f"**Customer Profile:** {persona_name} represents {size} customers ({(size/len(self.customers_df)*100):.1f}% of total)",
            f"**Financial Standing:** Average balance of ${balance:,.0f} with ${income:,.0f} annual income",
            f"**Engagement Level:** {self._get_engagement_level(chars)} banking activity",
            f"**Product Intent:** {self._get_intent_level(intent)} interest in new products and services"
        ]
        
        return {
            'segment_definition': "\n".join(definition_lines),
            'key_behaviors': key_behaviors[:5],  # Top 5
            'marketing_recommendations': recommendations[:5],  # Top 5
            'segment_size': size,
            'avg_customer_value': round(balance, 2)
        }
    
    def _get_engagement_level(self, chars: Dict) -> str:
        """Determine engagement level"""
        digital = chars['avg_digital']
        transactions = chars['avg_transactions']
        
        if digital > 0.75 and transactions > 100:
            return "Very High"
        elif digital > 0.6 or transactions > 60:
            return "High"
        elif digital > 0.4 or transactions > 30:
            return "Moderate"
        else:
            return "Low"
    
    def _get_intent_level(self, intent: float) -> str:
        """Determine intent level"""
        if intent > 0.8:
            return "Very High"
        elif intent > 0.65:
            return "High"
        elif intent > 0.5:
            return "Moderate"
        else:
            return "Low"


# Example usage
if __name__ == '__main__':
    agent = AgentA_Banking_UniqueSegments()
    if agent.load_data():
        result = agent.execute(n_clusters=5, gamma=0.5)
        print("\n✅ Clustering Complete!")
        print(f"Found {len(result['personas'])} unique personas:")
        for pid, persona in result['personas'].items():
            print(f"  {persona['emoji']} {persona['persona_name']} - {persona['size']} customers")

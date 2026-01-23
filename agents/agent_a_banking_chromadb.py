"""
Agent A - Banking Persona Builder (ChromaDB Version)
Retrieves pre-computed personas and clusters from vector database
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import json

from utils.chromadb_client import get_chroma_client, COLLECTIONS
from utils.together_ai import together_ai
from utils.logger import get_logger

logger = get_logger("Agent_A_Banking_ChromaDB")


class BankingPersonaBuilderChroma:
    """
    Agent A: Persona Builder for Banking (ChromaDB Version)
    
    Retrieves pre-computed personas and clustering results from ChromaDB
    Much faster than in-memory computation
    """
    
    def __init__(self):
        self.chroma = get_chroma_client()
        self.llm = together_ai
        logger.info("🏦 Agent A (Banking - ChromaDB) initialized")
    
    def execute(self, generate_ai_insights: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Retrieve banking personas from ChromaDB
        
        Args:
            generate_ai_insights: Whether to generate AI strategies
            
        Returns:
            Dictionary with personas and metrics
        """
        logger.info("="*80)
        logger.info("🏦 AGENT A: BANKING PERSONA RETRIEVAL (CHROMADB)")
        logger.info("="*80)
        
        # Step 1: Retrieve all personas from ChromaDB
        logger.info("\n[STEP 1/3] 📦 RETRIEVING PERSONAS FROM CHROMADB")
        personas_data = self.chroma.get_all(COLLECTIONS['banking_personas'])
        
        if not personas_data['ids']:
            logger.error("❌ No personas found in ChromaDB. Run initialization script first!")
            raise ValueError("No personas in database. Run scripts/initialize_chromadb.py")
        
        logger.info(f"   ✓ Retrieved {len(personas_data['ids'])} personas")
        
        # Step 2: Convert to structured format
        logger.info("\n[STEP 2/3] 🔄 FORMATTING PERSONAS")
        personas = self._format_personas(personas_data)
        logger.info(f"   ✓ Formatted {len(personas)} personas")
        
        # Step 3: Generate AI insights if requested
        if generate_ai_insights:
            logger.info("\n[STEP 3/3] 🤖 GENERATING AI INSIGHTS")
            personas = self._generate_ai_insights_batch(personas)
            logger.info(f"   ✓ Generated insights for {len(personas)} personas")
        else:
            logger.info("\n[STEP 3/3] ⏭️  SKIPPING AI INSIGHTS")
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(personas)
        
        # Extract cluster metrics
        cluster_metrics = self._extract_cluster_metrics(personas_data)
        
        # Get individual customers for detailed view
        all_customers_data = self.chroma.get_all(COLLECTIONS['banking_customers'])
        individual_customers = []
        for i, customer_id in enumerate(all_customers_data['ids']):
            customer_meta = all_customers_data['metadatas'][i]
            individual_customers.append({
                "customer_id": customer_id,
                **customer_meta
            })
        
        logger.info("\n" + "="*80)
        logger.info("✅ PERSONA RETRIEVAL COMPLETE")
        logger.info("="*80)
        
        return {
            "personas": personas,  # Cluster-level personas
            "customers": individual_customers,  # Individual customers
            "summary": summary_stats,
            "clustering_metrics": cluster_metrics,  # Frontend expects clustering_metrics
            "visualization_data": self._prepare_visualization_data(personas)
        }
    
    def get_customer_persona(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific customer's persona
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer data with cluster assignment
        """
        try:
            customer_data = self.chroma.get_by_ids(
                collection_name=COLLECTIONS['banking_customers'],
                ids=[customer_id]
            )
            
            if not customer_data['ids']:
                return None
            
            # Extract customer info
            customer = {
                'customer_id': customer_data['ids'][0],
                **customer_data['metadatas'][0]
            }
            
            # Get persona for this cluster
            cluster_id = customer.get('cluster_id')
            if cluster_id is not None:
                persona_data = self.chroma.get_by_ids(
                    collection_name=COLLECTIONS['banking_personas'],
                    ids=[f"persona_{cluster_id}"]
                )
                
                if persona_data['ids']:
                    customer['persona'] = persona_data['metadatas'][0]
            
            return customer
            
        except Exception as e:
            logger.error(f"❌ Error retrieving customer {customer_id}: {e}")
            return None
    
    def search_similar_customers(self, query: str, n_results: int = 10) -> List[Dict]:
        """
        Search for customers by semantic query
        
        Args:
            query: Search query (e.g., "high income customers with mortgage intent")
            n_results: Number of results
            
        Returns:
            List of matching customers
        """
        results = self.chroma.query_similar(
            collection_name=COLLECTIONS['banking_customers'],
            query_texts=[query],
            n_results=n_results
        )
        
        customers = []
        for i, customer_id in enumerate(results['ids'][0]):
            customers.append({
                'customer_id': customer_id,
                'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                **results['metadatas'][0][i]
            })
        
        return customers
    
    def _format_personas(self, personas_data: Dict) -> List[Dict]:
        """Convert ChromaDB response to persona format and enrich with customer data"""
        personas = []
        
        # Get all customers for enrichment
        all_customers_data = self.chroma.get_all(COLLECTIONS['banking_customers'])
        customers_by_cluster = {}
        
        logger.info(f"   📊 Retrieved {len(all_customers_data['ids'])} customers for enrichment")
        
        # Group customers by cluster
        for i, customer_id in enumerate(all_customers_data['ids']):
            customer_meta = all_customers_data['metadatas'][i]
            cluster_id = customer_meta.get('cluster_id')
            if cluster_id is not None:
                if cluster_id not in customers_by_cluster:
                    customers_by_cluster[cluster_id] = []
                customers_by_cluster[cluster_id].append(customer_meta)
        
        logger.info(f"   📊 Grouped into {len(customers_by_cluster)} clusters: {list(customers_by_cluster.keys())}")
        
        for i, persona_id in enumerate(personas_data['ids']):
            metadata = personas_data['metadatas'][i].copy()
            cluster_id = metadata.get('cluster_id')
            
            # Enrich with calculated metrics from actual customers
            if cluster_id is not None and cluster_id in customers_by_cluster:
                cluster_customers = customers_by_cluster[cluster_id]
                total_customers = len(all_customers_data['ids'])
                
                # Calculate missing metrics
                intent_scores = [c.get('intent_score', 0) for c in cluster_customers if c.get('intent_score') is not None]
                login_freqs = [c.get('login_frequency_30d', 0) for c in cluster_customers if c.get('login_frequency_30d') is not None]
                ages = [c.get('age', 0) for c in cluster_customers if c.get('age') is not None]
                incomes = [c.get('income', 0) for c in cluster_customers if c.get('income') is not None]
                credit_scores = [c.get('credit_score', 0) for c in cluster_customers if c.get('credit_score') is not None]
                tenures = [c.get('tenure_months', 0) for c in cluster_customers if c.get('tenure_months') is not None]
                channels = [c.get('channel_preference') for c in cluster_customers if c.get('channel_preference')]
                value_tiers = [c.get('value_tier') for c in cluster_customers if c.get('value_tier')]
                
                # Update persona with calculated values
                metadata['size'] = len(cluster_customers)
                metadata['percentage'] = (len(cluster_customers) / total_customers * 100) if total_customers > 0 else 0
                metadata['avg_intent'] = sum(intent_scores) / len(intent_scores) if intent_scores else 0
                metadata['avg_engagement'] = sum(login_freqs) / len(login_freqs) if login_freqs else 0
                metadata['avg_age'] = sum(ages) / len(ages) if ages else 0
                metadata['avg_income'] = sum(incomes) / len(incomes) if incomes else 0
                metadata['avg_credit_score'] = sum(credit_scores) / len(credit_scores) if credit_scores else 0
                metadata['avg_tenure'] = sum(tenures) / len(tenures) if tenures else 0
                metadata['dominant_channel'] = max(set(channels), key=channels.count) if channels else 'mobile'
                metadata['value_tier'] = max(set(value_tiers), key=value_tiers.count) if value_tiers else 'silver'
                
                logger.info(f"   ✓ Enriched Cluster {cluster_id}: {len(cluster_customers)} customers, avg_intent={metadata['avg_intent']:.2f}, channel={metadata['dominant_channel']}")
            
            # Parse JSON strings back to dicts/lists
            for key in ['product_holdings', 'ai_insights']:
                if key in metadata and isinstance(metadata[key], str):
                    try:
                        metadata[key] = json.loads(metadata[key])
                    except:
                        pass
            
            personas.append(metadata)
        
        return sorted(personas, key=lambda x: x.get('cluster_id', 0))
    
    def _generate_ai_insights_batch(self, personas: List[Dict]) -> List[Dict]:
        """Generate AI insights for personas using Together AI"""
        for persona in personas:
            try:
                # Build context
                context = f"""
                Banking Customer Segment Analysis:
                - Cluster ID: {persona.get('cluster_id')}
                - Size: {persona.get('size')} customers ({persona.get('percentage', 0):.1f}%)
                - Average Age: {persona.get('avg_age', 0):.0f}
                - Average Income: ${persona.get('avg_income', 0):,.0f}
                - Average Credit Score: {persona.get('avg_credit_score', 0):.0f}
                - Average Tenure: {persona.get('avg_tenure', 0):.0f} months
                - Engagement Score: {persona.get('avg_engagement', 0):.2f}
                - Intent Score: {persona.get('avg_intent', 0):.2f}
                - Dominant Channel: {persona.get('dominant_channel', 'mobile')}
                """
                
                # Generate persona profile
                profile_prompt = f"{context}\n\nProvide a concise 2-sentence profile of this customer segment."
                profile = self.llm.generate_text(profile_prompt, max_tokens=100)
                
                # Generate strategy
                strategy_prompt = f"{context}\n\nProvide 3 specific product recommendations and engagement strategies for this segment."
                strategy = self.llm.generate_text(strategy_prompt, max_tokens=150)
                
                persona['ai_insights'] = {
                    'profile': profile.strip(),
                    'strategy': strategy.strip()
                }
                
                logger.info(f"   ✓ Generated insights for Cluster {persona.get('cluster_id')}")
                
            except Exception as e:
                logger.warning(f"   ⚠️ Could not generate insights for Cluster {persona.get('cluster_id')}: {e}")
                persona['ai_insights'] = {
                    'profile': 'Profile generation unavailable',
                    'strategy': 'Strategy generation unavailable'
                }
        
        return personas
    
    def _calculate_summary_stats(self, personas: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics - properly weighted by cluster size"""
        total_customers = sum(p.get('size', 0) for p in personas)
        
        # Calculate weighted averages (weighted by cluster size)
        weighted_engagement = sum(p.get('avg_engagement', 0) * p.get('size', 0) for p in personas)
        weighted_intent = sum(p.get('avg_intent', 0) * p.get('size', 0) for p in personas)
        
        # Count customers in different engagement levels
        high_engagement = sum(p.get('size', 0) for p in personas if p.get('avg_engagement', 0) >= 7)
        low_engagement = sum(p.get('size', 0) for p in personas if p.get('avg_engagement', 0) < 3)
        
        return {
            'total_customers': total_customers,
            'total_clusters': len(personas),
            'avg_cluster_size': total_customers / len(personas) if personas else 0,
            'high_intent_customers': sum(
                p.get('size', 0) for p in personas
                if p.get('avg_intent', 0) > 0.6
            ),
            'high_intent_percentage': (
                sum(p.get('size', 0) for p in personas if p.get('avg_intent', 0) > 0.6) / total_customers * 100
                if total_customers > 0 else 0
            ),
            'high_engagement_customers': high_engagement,
            'low_engagement_customers': low_engagement,
            'avg_engagement': weighted_engagement / total_customers if total_customers > 0 else 0,
            'avg_intent': weighted_intent / total_customers if total_customers > 0 else 0
        }
    
    def _extract_cluster_metrics(self, personas_data: Dict) -> Dict[str, float]:
        """Extract clustering quality metrics"""
        if not personas_data['metadatas']:
            logger.warning("⚠️ No persona metadata found for cluster metrics")
            return {
                'silhouette_score': None,
                'davies_bouldin_score': None,
                'calinski_harabasz_score': None,
                'inertia': None
            }
        
        # Get metrics from first persona (they're all the same across all personas)
        metadata = personas_data['metadatas'][0]
        
        metrics = {
            'silhouette_score': metadata.get('silhouette_score'),
            'davies_bouldin_score': metadata.get('davies_bouldin_score'),
            'calinski_harabasz_score': metadata.get('calinski_harabasz_score'),
            'inertia': metadata.get('inertia')
        }
        
        logger.info(f"   📊 Cluster Metrics: Silhouette={metrics['silhouette_score']}, DB={metrics['davies_bouldin_score']}, CH={metrics['calinski_harabasz_score']}")
        
        return metrics
    
    def _prepare_visualization_data(self, personas: List[Dict]) -> Dict[str, Any]:
        """Prepare data for frontend visualizations"""
        import numpy as np
        
        # Cluster distribution with names
        cluster_distribution = {str(p.get('cluster_id')): p.get('size', 0) for p in personas}
        
        # Engagement distribution (categorize) - aligned with data generation
        engagement_distribution = {"High": 0, "Medium": 0, "Low": 0}
        for p in personas:
            eng = p.get('avg_engagement', 0)
            size = p.get('size', 0)
            if eng >= 7:  # >= 7 logins/month = High
                engagement_distribution["High"] += size
            elif eng >= 3:  # 3-6 logins/month = Medium
                engagement_distribution["Medium"] += size
            else:  # < 3 logins/month = Low
                engagement_distribution["Low"] += size
        
        # Intent distribution (categorize)
        intent_distribution = {"High": 0, "Medium": 0, "Low": 0}
        for p in personas:
            intent = p.get('avg_intent', 0)
            size = p.get('size', 0)
            if intent > 0.7:
                intent_distribution["High"] += size
            elif intent > 0.4:
                intent_distribution["Medium"] += size
            else:
                intent_distribution["Low"] += size
        
        # Create simple 2D scatter data (use cluster metrics as coordinates)
        cluster_scatter_2d = []
        for p in personas:
            cluster_scatter_2d.append({
                'cluster': p.get('cluster_id'),
                'cluster_name': p.get('cluster_name', f"Cluster {p.get('cluster_id')}"),
                'x': p.get('avg_intent', 0) * 100,  # Intent as X
                'y': p.get('avg_engagement', 0),  # Engagement as Y
                'size': p.get('size', 0)
            })
        
        return {
            'cluster_distribution': cluster_distribution,
            'engagement_distribution': engagement_distribution,
            'intent_distribution': intent_distribution,
            'cluster_scatter_2d': cluster_scatter_2d,
            'pca_variance_explained': [0.45, 0.25]  # Placeholder for PCA variance
        }


logger.info("✨ Banking Persona Builder (ChromaDB) module initialized")


"""Main orchestration workflow for the Agentic AI system."""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path

from agents.agent_a_persona import PersonaBuilderAgent
from agents.agent_b_product import ProductMatchmakerAgent
from agents.agent_c_offer import OfferEngineAgent
from agents.agent_d_performance import PerformanceEngineAgent
from agents.agent_e_mmm import MMMStrategicAdvisor
from utils.logger import get_logger

logger = get_logger("Orchestrator")


class AgenticAIOrchestrator:
    """Main orchestrator for the 5-agent personalization system."""
    
    def __init__(self):
        # Initialize all agents
        self.agent_a = PersonaBuilderAgent()
        self.agent_b = ProductMatchmakerAgent()
        self.agent_c = OfferEngineAgent()
        self.agent_d = PerformanceEngineAgent()
        self.agent_e = MMMStrategicAdvisor()
        
        # Shared state
        self.customers_df = None
        self.products_df = None
        self.transactions_df = None
        self.behavioral_df = None
        self.feature_matrix = None
        self.customer_embeddings = None
        self.product_embeddings = None
        
        logger.info("🚀 Agentic AI Orchestrator initialized")
    
    def load_data(
        self,
        data_dir: str = "data/synthetic"
    ):
        """Load all required data."""
        logger.info(f"Loading data from {data_dir}...")
        
        data_path = Path(data_dir)
        
        try:
            self.customers_df = pd.read_csv(data_path / "customers.csv", on_bad_lines='skip')
            self.products_df = pd.read_csv(data_path / "products.csv", on_bad_lines='skip')
            self.transactions_df = pd.read_csv(data_path / "transactions.csv", on_bad_lines='skip')
            self.behavioral_df = pd.read_csv(data_path / "behavioral_events.csv", on_bad_lines='skip')
            
            logger.info(f"✅ Data loaded: {len(self.customers_df)} customers, {len(self.products_df)} products")
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            logger.info("💡 Try regenerating the data if files are corrupted")
            raise
    
    def initialize_system(self):
        """Initialize the entire agent system."""
        logger.info("="*80)
        logger.info("🎬 INITIALIZING AGENTIC AI SYSTEM")
        logger.info("="*80)
        
        # Step 1: Build personas (Agent A)
        logger.info("\n>>> Running Agent A: Persona Builder")
        persona_results = self.agent_a.build_personas(
            self.customers_df,
            self.transactions_df,
            self.behavioral_df
        )
        self.feature_matrix = persona_results['feature_matrix']
        self.customer_embeddings = persona_results['embeddings']
        
        # Step 2: Create product embeddings (Agent B)
        logger.info("\n>>> Running Agent B: Product Matchmaker - Creating embeddings")
        self.product_embeddings = self.agent_b.create_product_embeddings(self.products_df)
        
        # Step 3: Train propensity models (Agent B)
        logger.info("\n>>> Training propensity models")
        self.agent_b.train_propensity_model(
            self.transactions_df,
            self.feature_matrix,
            self.products_df
        )
        
        # Step 4: Initialize performance tracking (Agent D)
        logger.info("\n>>> Initializing Performance Engine")
        
        # Step 5: Collect channel data (Agent E)
        logger.info("\n>>> Running Agent E: MMM Strategic Advisor")
        self.agent_e.collect_channel_data()
        self.agent_e.calculate_attribution()
        
        logger.info("\n" + "="*80)
        logger.info("✅ SYSTEM INITIALIZATION COMPLETE")
        logger.info("="*80 + "\n")
    
    def get_next_best_actions(
        self,
        customer_id: str,
        context: Optional[Dict[str, Any]] = None,
        top_n: int = 3
    ) -> Dict[str, Any]:
        """Get Next Best Actions for a specific customer (end-to-end flow)."""
        logger.info("="*80)
        logger.info(f"🎯 GETTING NEXT BEST ACTIONS FOR CUSTOMER: {customer_id}")
        logger.info("="*80)
        
        if context is None:
            context = {
                'device': 'desktop',
                'location': 'home',
                'session_duration': 300,
                'pages_viewed': 5,
                'hour': 14
            }
        
        # Step 1: Get customer persona (Agent A)
        logger.info("\n[1/5] Agent A: Retrieving customer persona...")
        customer_persona = self.agent_a.get_customer_persona(customer_id, self.feature_matrix)
        
        if 'error' in customer_persona:
            return {'error': f"Customer {customer_id} not found"}
        
        # Get customer embedding
        customer_idx = self.feature_matrix[
            self.feature_matrix['customer_id'] == customer_id
        ].index[0]
        customer_embedding = self.customer_embeddings[customer_idx]
        
        # Step 2: Match products (Agent B)
        logger.info("[2/5] Agent B: Matching products...")
        matched_products_result = self.agent_b.match_products(
            customer_id,
            customer_persona,
            customer_embedding,
            top_n=10
        )
        matched_products = matched_products_result['matched_products']
        
        # Step 3: Generate offers (Agent C)
        logger.info("[3/5] Agent C: Generating personalized offers...")
        offers = self.agent_c.generate_multiple_offers(
            customer_persona,
            matched_products,
            top_n=5
        )
        
        # Step 4: Rank and select NBA (Agent D)
        logger.info("[4/5] Agent D: Ranking offers and selecting NBA...")
        nba_offers = self.agent_d.select_nba(offers, context, top_n=top_n)
        
        # Step 5: Get strategic context (Agent E)
        logger.info("[5/5] Agent E: Providing strategic context...")
        # Channel recommendations already available from Agent C
        
        logger.info("\n" + "="*80)
        logger.info(f"✅ GENERATED {len(nba_offers)} NEXT BEST ACTIONS")
        logger.info("="*80 + "\n")
        
        return {
            'customer_id': customer_id,
            'customer_persona': customer_persona,
            'next_best_actions': nba_offers,
            'context': context,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def record_customer_interaction(
        self,
        customer_id: str,
        offer_id: str,
        action: str,
        revenue: float = 0.0
    ):
        """Record customer interaction for feedback loop."""
        self.agent_d.record_interaction(offer_id, customer_id, action, revenue)
        
        # Add to performance history
        self.agent_d.performance_history.append({
            'customer_id': customer_id,
            'offer_id': offer_id,
            'action': action,
            'revenue': revenue,
            'timestamp': pd.Timestamp.now().isoformat()
        })
    
    def get_system_insights(self) -> Dict[str, Any]:
        """Get overall system insights and recommendations."""
        logger.info("📊 Generating system insights...")
        
        # Persona distribution
        persona_distribution = self.feature_matrix['persona_name'].value_counts().to_dict()
        
        # Intent distribution
        intent_distribution = self.feature_matrix['intent'].value_counts().to_dict()
        
        # Performance metrics
        performance_metrics = self.agent_d.calculate_performance_metrics()
        
        # Budget optimization
        budget_optimization = self.agent_e.optimize_budget_allocation()
        
        # Strategic recommendations
        strategic_recommendations = self.agent_e.generate_strategic_recommendations()
        
        # Frequency optimization
        frequency_optimization = self.agent_e.optimize_frequency()
        
        return {
            'persona_distribution': persona_distribution,
            'intent_distribution': intent_distribution,
            'performance_metrics': performance_metrics,
            'budget_optimization': budget_optimization,
            'strategic_recommendations': strategic_recommendations,
            'frequency_optimization': frequency_optimization,
            'total_customers': len(self.customers_df),
            'active_customers': int(self.customers_df['is_active'].sum()),
            'total_products': len(self.products_df)
        }
    
    def get_customer_list(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of customers for UI."""
        if self.feature_matrix is None:
            return []
        
        customers = self.feature_matrix.head(limit)[
            ['customer_id', 'persona_name', 'intent', 'loyalty_tier', 
             'purchase_propensity', 'monetary_value']
        ].to_dict('records')
        
        return customers
    
    def get_all_personas(self) -> Dict[str, Any]:
        """Get all persona information."""
        if self.feature_matrix is None:
            return {}
        
        personas = {}
        for persona_name in self.feature_matrix['persona_name'].unique():
            persona_customers = self.feature_matrix[
                self.feature_matrix['persona_name'] == persona_name
            ]
            
            personas[persona_name] = {
                'count': len(persona_customers),
                'avg_monetary_value': float(persona_customers['monetary_value'].mean()),
                'avg_frequency': float(persona_customers['frequency'].mean()),
                'avg_recency': float(persona_customers['recency_days'].mean()),
                'avg_purchase_propensity': float(persona_customers['purchase_propensity'].mean())
            }
        
        return personas


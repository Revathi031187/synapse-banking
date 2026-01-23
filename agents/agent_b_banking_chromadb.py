"""
Agent B - Banking Product Matcher (ChromaDB Version)
Uses vector similarity search for intelligent product recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import json

from utils.chromadb_client import get_chroma_client, COLLECTIONS
from utils.together_ai import together_ai
from utils.logger import get_logger

logger = get_logger("Agent_B_Banking_ChromaDB")


class BankingProductMatcherChroma:
    """
    Agent B: Product Matcher for Banking (ChromaDB Version)
    
    Uses vector similarity search to find best product matches
    Much faster than rule-based matching
    """
    
    def __init__(self):
        self.chroma = get_chroma_client()
        self.llm = together_ai
        logger.info("🎯 Agent B (Banking - ChromaDB) initialized")
    
    def execute(
        self,
        customer_id: str,
        top_n: int = 5,
        generate_ai_explanation: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate product recommendations for a customer
        
        Args:
            customer_id: Customer ID
            top_n: Number of products to recommend
            generate_ai_explanation: Whether to generate AI explanations
            
        Returns:
            Dictionary with customer context and recommendations
        """
        logger.info("="*80)
        logger.info(f"🎯 AGENT B: BANKING PRODUCT RECOMMENDATIONS FOR {customer_id}")
        logger.info("="*80)
        
        # Step 1: Retrieve customer data
        logger.info("\n[STEP 1/4] 👤 RETRIEVING CUSTOMER DATA")
        customer_data = self.chroma.get_by_ids(
            collection_name=COLLECTIONS['banking_customers'],
            ids=[customer_id]
        )
        
        if not customer_data['ids']:
            logger.error(f"❌ Customer {customer_id} not found")
            raise ValueError(f"Customer {customer_id} not found in database")
        
        customer = self._format_customer(customer_data, 0)
        logger.info(f"   ✓ Retrieved customer: {customer.get('customer_id')}")
        
        # Step 2: Get customer's persona
        logger.info("\n[STEP 2/4] 🎭 RETRIEVING PERSONA")
        cluster_id = customer.get('cluster_id')
        persona = None
        
        if cluster_id is not None:
            persona_data = self.chroma.get_by_ids(
                collection_name=COLLECTIONS['banking_personas'],
                ids=[f"persona_{cluster_id}"]
            )
            
            if persona_data['ids']:
                persona = self._format_persona(persona_data, 0)
                logger.info(f"   ✓ Retrieved persona for Cluster {cluster_id}")
        
        # Step 3: Find matching products using vector similarity
        logger.info(f"\n[STEP 3/4] 🔍 FINDING MATCHING PRODUCTS (TOP {top_n})")
        recommendations = self._find_matching_products(customer, top_n)
        logger.info(f"   ✓ Found {len(recommendations)} eligible products")
        
        # Step 4: Generate AI explanations if requested
        if generate_ai_explanation and recommendations:
            logger.info("\n[STEP 4/4] 🤖 GENERATING AI EXPLANATIONS")
            recommendations = self._generate_ai_explanations(customer, recommendations)
            logger.info(f"   ✓ Generated explanations for {len(recommendations)} products")
        else:
            logger.info("\n[STEP 4/4] ⏭️  SKIPPING AI EXPLANATIONS")
        
        logger.info("\n" + "="*80)
        logger.info("✅ PRODUCT RECOMMENDATIONS COMPLETE")
        logger.info("="*80)
        
        return {
            "customer_context": {
                **customer,
                "persona": persona
            },
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
    
    def _format_customer(self, customer_data: Dict, index: int) -> Dict:
        """Format customer data from ChromaDB response"""
        metadata = customer_data['metadatas'][index]
        
        # Parse JSON strings
        for key in ['product_holdings']:
            if key in metadata and isinstance(metadata[key], str):
                try:
                    metadata[key] = json.loads(metadata[key])
                except:
                    metadata[key] = []
        
        return {
            'customer_id': customer_data['ids'][index],
            **metadata
        }
    
    def _format_persona(self, persona_data: Dict, index: int) -> Dict:
        """Format persona data from ChromaDB response"""
        metadata = persona_data['metadatas'][index]
        
        # Parse JSON strings
        for key in ['ai_insights']:
            if key in metadata and isinstance(metadata[key], str):
                try:
                    metadata[key] = json.loads(metadata[key])
                except:
                    pass
        
        return metadata
    
    def _find_matching_products(self, customer: Dict, top_n: int) -> List[Dict]:
        """
        Find matching products using vector similarity search
        
        Args:
            customer: Customer data
            top_n: Number of products to return
            
        Returns:
            List of recommended products
        """
        # Build query text from customer profile
        query = self._build_customer_query(customer)
        
        # Search for similar products (get more than needed for filtering)
        results = self.chroma.query_similar(
            collection_name=COLLECTIONS['banking_products'],
            query_texts=[query],
            n_results=top_n * 3  # Get 3x to account for filtering
        )
        
        if not results['ids'] or not results['ids'][0]:
            logger.warning("⚠️ No products found in vector search")
            return []
        
        # Format and filter products
        recommendations = []
        product_holdings = set(customer.get('product_holdings', []))
        
        for i, product_id in enumerate(results['ids'][0]):
            product = self._format_product(results, i)
            
            # Skip if customer already has this product
            if product['product_id'] in product_holdings:
                continue
            
            # Calculate eligibility and propensity
            eligibility = self._calculate_eligibility(customer, product)
            propensity = self._calculate_propensity(customer, product, results['distances'][0][i])
            
            if eligibility > 0.3:  # Relaxed threshold
                recommendations.append({
                    **product,
                    'eligibility_score': round(eligibility, 3),
                    'propensity_score': round(propensity, 3),
                    'overall_score': round((eligibility + propensity) / 2, 3),
                    'similarity_score': round(1 - results['distances'][0][i], 3)
                })
            
            if len(recommendations) >= top_n:
                break
        
        # Sort by overall score
        recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return recommendations[:top_n]
    
    def _build_customer_query(self, customer: Dict) -> str:
        """Build semantic search query from customer profile"""
        query_parts = []
        
        # Demographics
        age = customer.get('age', 0)
        income = customer.get('income', 0)
        credit_score = customer.get('credit_score', 0)
        
        query_parts.append(f"Customer age {age} income ${income:,.0f} credit score {credit_score}")
        
        # Intent signals
        intent_score = customer.get('intent_score', 0)
        if intent_score > 0.6:
            query_parts.append("high purchase intent")
        
        # Engagement
        engagement = customer.get('login_frequency_30d', 0)
        if engagement > 20:
            query_parts.append("highly engaged digital user")
        
        # Life events (if available)
        primary_life_event = customer.get('primary_life_event')
        if primary_life_event:
            query_parts.append(f"experiencing {primary_life_event}")
        
        # Financial profile
        if income > 100000:
            query_parts.append("premium banking products")
        elif income > 50000:
            query_parts.append("standard banking products")
        else:
            query_parts.append("basic banking products")
        
        if credit_score > 750:
            query_parts.append("excellent credit products")
        elif credit_score > 650:
            query_parts.append("good credit products")
        
        return " | ".join(query_parts)
    
    def _format_product(self, results: Dict, index: int) -> Dict:
        """Format product from search results"""
        metadata = results['metadatas'][0][index]
        
        # Parse JSON strings
        for key in ['features', 'eligibility_criteria']:
            if key in metadata and isinstance(metadata[key], str):
                try:
                    metadata[key] = json.loads(metadata[key])
                except:
                    metadata[key] = []
        
        return {
            'product_id': results['ids'][0][index],
            **metadata
        }
    
    def _calculate_eligibility(self, customer: Dict, product: Dict) -> float:
        """Calculate eligibility score (0-1)"""
        score = 1.0
        
        # Credit score check (relaxed)
        min_credit = product.get('min_credit_score', 0)
        if min_credit > 0:
            customer_credit = customer.get('credit_score', 0)
            if customer_credit < min_credit:
                score *= 0.6  # Partial penalty instead of rejection
            elif customer_credit >= min_credit + 50:
                score *= 1.1  # Bonus for high credit
        
        # Income check (relaxed)
        min_income = product.get('min_income', 0)
        if min_income > 0:
            customer_income = customer.get('income', 0)
            if customer_income < min_income * 0.8:  # 80% threshold
                score *= 0.7
            elif customer_income >= min_income * 1.5:
                score *= 1.1
        
        # Age check (with buffer)
        min_age = product.get('min_age', 0)
        max_age = product.get('max_age', 999)
        customer_age = customer.get('age', 0)
        
        if customer_age < min_age - 2 or customer_age > max_age + 2:
            score *= 0.8
        
        return min(score, 1.0)
    
    def _calculate_propensity(self, customer: Dict, product: Dict, distance: float) -> float:
        """Calculate propensity score (0-1) based on likelihood to accept"""
        # Base score from vector similarity
        similarity = 1 - distance
        propensity = similarity * 0.5
        
        # Intent signal
        intent_score = customer.get('intent_score', 0)
        propensity += intent_score * 0.3
        
        # Engagement signal
        engagement = customer.get('login_frequency_30d', 0)
        engagement_score = min(engagement / 30, 1.0)  # Normalize to 0-1
        propensity += engagement_score * 0.2
        
        return min(propensity, 1.0)
    
    def _generate_ai_explanations(
        self,
        customer: Dict,
        recommendations: List[Dict]
    ) -> List[Dict]:
        """Generate AI explanations for recommendations"""
        for rec in recommendations:
            try:
                context = f"""
                Customer Profile:
                - Age: {customer.get('age')}
                - Income: ${customer.get('income', 0):,.0f}
                - Credit Score: {customer.get('credit_score')}
                - Intent Score: {customer.get('intent_score', 0):.2f}
                - Engagement: {customer.get('login_frequency_30d', 0)} logins/month
                
                Product Recommended:
                - Name: {rec.get('product_name')}
                - Type: {rec.get('product_type')}
                - Category: {rec.get('category')}
                - Eligibility Score: {rec.get('eligibility_score', 0):.2f}
                - Propensity Score: {rec.get('propensity_score', 0):.2f}
                """
                
                prompt = f"{context}\n\nIn 2 sentences, explain why this product is a good match for this customer."
                explanation = self.llm.generate(prompt, max_tokens=100)
                
                rec['ai_explanation'] = explanation.strip()
                logger.info(f"   ✓ Generated explanation for {rec['product_name']}")
                
            except Exception as e:
                logger.warning(f"   ⚠️ Could not generate explanation for {rec['product_name']}: {e}")
                rec['ai_explanation'] = "This product matches your profile and financial goals."
        
        return recommendations


logger.info("✨ Banking Product Matcher (ChromaDB) module initialized")


"""
Together AI Service Integration
Handles embeddings and LLM completions for persona generation
"""
import os
from typing import List, Dict, Any
import requests
import numpy as np
from utils.logger import get_logger
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

logger = get_logger("TogetherAI")

# Load API key from environment variable
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "6398823e1e39f337943f109988df04bbdcf19d2ac2b830d2220bde468d886ac3")
TOGETHER_API_BASE = "https://api.together.xyz/v1"

if TOGETHER_API_KEY == "6398823e1e39f337943f109988df04bbdcf19d2ac2b830d2220bde468d886ac3":
    logger.warning("⚠️  Using fallback API key. Set TOGETHER_API_KEY in .env for better reliability")
else:
    logger.info(f"✓ Loaded TOGETHER_API_KEY from .env (ends with ...{TOGETHER_API_KEY[-8:]})")


class TogetherAIService:
    """Service for Together AI API calls."""
    
    def __init__(self):
        self.api_key = TOGETHER_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.info("✨ Together AI Service initialized")
    
    def create_embeddings(self, texts: List[str], model: str = "BAAI/bge-large-en-v1.5") -> np.ndarray:
        """
        Create embeddings for text inputs.
        
        Args:
            texts: List of text strings to embed
            model: Embedding model to use
            
        Returns:
            numpy array of embeddings (n_texts, embedding_dim)
        """
        # Try multiple model names (Together AI may have updated model names)
        models_to_try = [
            model,  # User-provided model
            "BAAI/bge-large-en-v1.5",  # This one works!
            "WhereIsAI/UAE-Large-V1",
            "togethercomputer/m2-bert-80M-8k-retrieval",
            "sentence-transformers/msmarco-bert-base-dot-v5"
        ]
        
        last_error = None
        
        for model_name in models_to_try:
            try:
                logger.info(f"🔮 Trying embeddings with model: {model_name} for {len(texts)} texts...")
                
                url = f"{TOGETHER_API_BASE}/embeddings"
                payload = {
                    "model": model_name,
                    "input": texts
                }
                
                response = requests.post(url, json=payload, headers=self.headers, verify=False, timeout=30)
                
                # Log response details for debugging
                if response.status_code != 200:
                    logger.warning(f"⚠️  Response status: {response.status_code}")
                    logger.warning(f"⚠️  Response body: {response.text[:500]}")
                
                response.raise_for_status()
                
                data = response.json()
                embeddings = np.array([item['embedding'] for item in data['data']])
                
                logger.info(f"✅ Created embeddings with {model_name}: shape {embeddings.shape}")
                return embeddings
                
            except requests.exceptions.HTTPError as e:
                last_error = e
                logger.warning(f"⚠️  HTTP Error for {model_name}: {e}")
                if hasattr(e.response, 'text'):
                    logger.warning(f"⚠️  Response: {e.response.text[:500]}")
                continue
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️  Error for {model_name}: {e}")
                continue
        
        # If all models failed
        logger.error(f"❌ All embedding models failed. Last error: {last_error}")
        logger.info("💡 Falling back to zero embeddings - search will use keyword matching")
        return np.zeros((len(texts), 1024))  # Updated to match BAAI/bge-large-en-v1.5 dimension
    
    def generate_text(
        self, 
        prompt: str, 
        system_message: str = "You are a helpful AI assistant specialized in marketing and customer analysis.",
        model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using LLM.
        
        Args:
            prompt: User prompt
            system_message: System instruction
            model: LLM model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        try:
            logger.info(f"💬 Generating text with {model}...")
            
            url = f"{TOGETHER_API_BASE}/chat/completions"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(url, json=payload, headers=self.headers, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            generated_text = data['choices'][0]['message']['content']
            
            logger.info(f"✅ Generated {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"❌ Error generating text: {e}")
            return "Error generating description"
    
    def generate_persona_name(self, cluster_characteristics: Dict[str, Any]) -> str:
        """Generate a creative persona name based on cluster characteristics."""
        
        prompt = f"""Based on the following customer cluster characteristics, generate a creative and memorable persona name (2-3 words):

Demographics:
- Average Age: {cluster_characteristics.get('avg_age', 'N/A')}
- Gender Distribution: {cluster_characteristics.get('gender_dist', 'N/A')}
- Income Level: {cluster_characteristics.get('income_level', 'N/A')}

Behavior:
- Purchase Frequency: {cluster_characteristics.get('purchase_freq', 'N/A')}
- Average Spend: ${cluster_characteristics.get('avg_spend', 0):.2f}
- Engagement Level: {cluster_characteristics.get('engagement', 'N/A')}

Generate ONLY the persona name, nothing else."""

        return self.generate_text(
            prompt=prompt,
            system_message="You are a marketing expert creating memorable customer personas. Be creative but professional.",
            max_tokens=20,
            temperature=0.8
        ).strip()
    
    def generate_persona_description(self, persona_name: str, cluster_data: Dict[str, Any]) -> str:
        """Generate a detailed persona description."""
        
        prompt = f"""Create a detailed, engaging persona description for "{persona_name}" based on these characteristics:

Demographics:
{cluster_data.get('demographics', {})}

Behavioral Patterns:
{cluster_data.get('behavior', {})}

RFM Analysis:
- Recency: {cluster_data.get('rfm_recency', 'N/A')} days
- Frequency: {cluster_data.get('rfm_frequency', 'N/A')} purchases
- Monetary: ${cluster_data.get('rfm_monetary', 0):.2f}

Create a 2-3 paragraph description that:
1. Describes who this persona is
2. Their typical behaviors and preferences
3. What motivates them and their pain points
4. How to best engage with them

Write in a professional but engaging tone."""

        return self.generate_text(
            prompt=prompt,
            system_message="You are a senior marketing strategist creating actionable customer personas.",
            max_tokens=400,
            temperature=0.7
        )
    
    def generate_product_recommendations_reasoning(
        self, 
        persona_name: str, 
        products: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate reasoning for why products are recommended to a persona."""
        
        reasonings = []
        for product in products[:5]:  # Top 5 products
            prompt = f"""Explain in 1-2 sentences why "{product['name']}" is a great match for the "{persona_name}" persona.

Product: {product['name']}
Category: {product.get('category', 'N/A')}
Price: ${product.get('price', 0):.2f}

Persona: {persona_name}

Be specific and actionable."""

            reasoning = self.generate_text(
                prompt=prompt,
                max_tokens=100,
                temperature=0.6
            ).strip()
            reasonings.append(reasoning)
        
        return reasonings
    
    def explain_clustering_quality(self, metrics: Dict[str, float], n_personas: int) -> str:
        """
        Generate AI explanation of clustering quality metrics.
        
        Args:
            metrics: Dictionary with silhouette_score, davies_bouldin_score, calinski_harabasz_score
            n_personas: Number of personas created
            
        Returns:
            AI-generated explanation of the quality
        """
        prompt = f"""Analyze the following customer segmentation clustering results and provide a clear, actionable explanation:

Number of Personas: {n_personas}

Quality Metrics:
- Silhouette Score: {metrics.get('silhouette_score', 0):.3f} (Range: -1 to 1, higher is better, >0.5 is excellent)
- Davies-Bouldin Index: {metrics.get('davies_bouldin_score', 0):.3f} (Lower is better, <1.0 is excellent)
- Calinski-Harabasz Score: {metrics.get('calinski_harabasz_score', 0):.1f} (Higher is better, >100 is excellent)

Provide a 2-3 sentence explanation that:
1. Summarizes the overall quality (Excellent/Good/Fair/Poor)
2. Explains what this means for the business
3. Gives one actionable recommendation

Be concise and business-focused."""

        return self.generate_text(
            prompt=prompt,
            system_message="You are a data science consultant explaining ML results to marketing executives.",
            max_tokens=200,
            temperature=0.7
        ).strip()
    
    def explain_visualization_pattern(
        self, 
        viz_type: str, 
        n_clusters: int, 
        cluster_sizes: List[int]
    ) -> str:
        """
        Generate AI explanation of visualization patterns.
        
        Args:
            viz_type: 'pca' or 'tsne'
            n_clusters: Number of clusters
            cluster_sizes: List of cluster sizes
            
        Returns:
            AI-generated explanation of what the visualization shows
        """
        method_name = "PCA (Principal Component Analysis)" if viz_type == 'pca' else "t-SNE (t-Distributed Stochastic Neighbor Embedding)"
        
        size_info = ", ".join([f"Persona {i+1}: {size} customers" for i, size in enumerate(cluster_sizes)])
        
        prompt = f"""Explain what this customer segmentation visualization shows to a marketing manager:

Visualization Method: {method_name}
Number of Customer Personas: {n_clusters}
Distribution: {size_info}

Provide a 2-3 sentence explanation that:
1. Explains what the visualization reveals about customer groups
2. Describes the separation/clustering pattern
3. What this means for targeted marketing

Be clear and actionable."""

        return self.generate_text(
            prompt=prompt,
            system_message="You are a marketing analytics expert explaining data visualizations.",
            max_tokens=150,
            temperature=0.7
        ).strip()
    
    def generate_persona_insights(self, persona_data: Dict[str, Any]) -> str:
        """
        Generate AI-powered insights for a specific persona.
        
        Args:
            persona_data: Full persona data including characteristics and metrics
            
        Returns:
            AI-generated insights and recommendations
        """
        prompt = f"""Analyze this customer persona and provide actionable marketing insights:

Persona Name: {persona_data.get('name', 'Unknown')}
Size: {persona_data.get('size', 0)} customers ({persona_data.get('percentage', 0):.1f}%)

Key Metrics:
- Average Recency: {persona_data.get('key_metrics', {}).get('avg_recency_days', 0):.0f} days
- Purchase Frequency: {persona_data.get('key_metrics', {}).get('avg_purchases_per_year', 0):.1f} per year
- Lifetime Value: ${persona_data.get('key_metrics', {}).get('avg_lifetime_value', 0):.0f}
- Engagement Events: {persona_data.get('key_metrics', {}).get('avg_engagement_events', 0):.0f}
- Conversion Rate: {persona_data.get('key_metrics', {}).get('conversion_rate', 0):.1f}%

Provide:
1. One key characteristic (1 sentence)
2. Primary opportunity or risk (1 sentence)
3. One specific marketing recommendation (1 sentence)

Be concise and actionable."""

        return self.generate_text(
            prompt=prompt,
            system_message="You are a senior marketing strategist providing persona insights.",
            max_tokens=200,
            temperature=0.7
        ).strip()
    
    def generate_banking_product_explanation(
        self,
        customer_profile: Dict[str, Any],
        product: Dict[str, Any],
        persona_name: str,
        score_breakdown: Dict[str, Any]
    ) -> str:
        """
        Generate AI explanation for why this banking product is recommended.
        
        Args:
            customer_profile: Customer financial data
            product: Product details
            persona_name: Customer's segment name
            score_breakdown: Detailed scoring factors
            
        Returns:
            AI-generated explanation (2-3 sentences)
        """
        prompt = f"""Explain in 2-3 sentences why "{product.get('product_name', 'this product')}" is an excellent match for this customer.

Customer Profile:
- Segment: {persona_name}
- Credit Score: {customer_profile.get('credit_score', 'N/A')}
- Income: ${customer_profile.get('income', 0):,.0f}/year
- Deposits: ${customer_profile.get('total_deposits', 0):,.0f}
- Current Products: {customer_profile.get('num_products', 0)}
- Age: {customer_profile.get('age', 'N/A')}

Product: {product.get('product_name', 'Unknown Product')}
- Category: {product.get('category', 'N/A')}
- Annual Fee: ${product.get('annual_fee', 0)}
- Min Balance: ${product.get('min_balance', 0):,.0f}
- Interest Rate: {product.get('interest_rate_apy', product.get('interest_rate', 'N/A'))}%

Why Recommended (scoring breakdown):
- Eligibility: {score_breakdown.get('eligibility_score', {}).get('score', 0):.0%} - {score_breakdown.get('eligibility_score', {}).get('explanation', 'N/A')}
- Financial Need: {score_breakdown.get('financial_need_match', {}).get('score', 0):.0%} - {score_breakdown.get('financial_need_match', {}).get('explanation', 'N/A')}
- Relationship Fit: {score_breakdown.get('relationship_depth', {}).get('score', 0):.0%}

Write a clear, professional explanation focusing on:
1. Why they qualify and it's a good fit
2. How it addresses their specific financial needs
3. The tangible benefit they'll gain

Be conversational but professional. No markdown formatting."""

        system_message = """You are a financial advisor at Farmers & Merchants Bank explaining personalized product recommendations. Be helpful, clear, and customer-focused. Avoid jargon."""

        return self.generate_text(
            prompt=prompt,
            system_message=system_message,
            max_tokens=200,
            temperature=0.7
        )
    
    def generate_segment_product_reasoning(
        self,
        persona_name: str,
        persona_characteristics: Dict[str, Any],
        products: List[Dict[str, Any]]
    ) -> str:
        """
        Generate explanation of why these products fit this segment.
        
        Args:
            persona_name: Segment name
            persona_characteristics: Segment characteristics
            products: List of recommended products
            
        Returns:
            AI-generated segment-level reasoning (2-3 sentences)
        """
        prompt = f"""Explain why these banking products are ideal for the "{persona_name}" customer segment.

Segment Profile:
- Average Deposits: ${persona_characteristics.get('avg_deposits', 0):,.0f}
- Average Income: ${persona_characteristics.get('avg_income', 0):,.0f}
- Average Age: {persona_characteristics.get('avg_age', 0):.0f}
- Digital Engagement: {persona_characteristics.get('avg_digital', 0)*100:.0f}%
- Product Ownership: {persona_characteristics.get('avg_products', 0):.1f} products

Recommended Products:
{chr(10).join([f"- {p.get('product_name', 'Unknown')} ({p.get('category', 'N/A')})" for p in products[:3]])}

Provide a 2-3 sentence explanation of:
1. What financial needs this segment has
2. Why these specific products address those needs
3. Expected value/benefit to segment

Be professional and strategic."""

        system_message = "You are a banking strategy consultant explaining segment-based product recommendations."

        return self.generate_text(
            prompt=prompt,
            system_message=system_message,
            max_tokens=150,
            temperature=0.7
        )


# Global instance
together_ai = TogetherAIService()


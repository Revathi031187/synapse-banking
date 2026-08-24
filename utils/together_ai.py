"""
Together AI Service Integration
Handles embeddings and LLM completions for persona generation
"""
import os
import time
from typing import List, Dict, Any, Optional
import requests
import numpy as np
from utils.logger import get_logger
from utils.token_tracker import log_llm_call
from utils.llm_priority_config import get_together_models
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

logger = get_logger("TogetherAI")

# Load API key from environment variable (never commit real keys; get one at api.together.xyz)
TOGETHER_API_KEY = (os.getenv("TOGETHER_API_KEY") or "").strip()
TOGETHER_API_BASE = "https://api.together.xyz/v1"

# Which Together models to try, and in what order, is controlled by
# config/llm_priority.json (utils/llm_priority_config.get_together_models())
# so a human can reorder/prune them without touching code — see that file's
# _readme for how. The old hardcoded list here was found (2026-08-20) to be
# 100% dead — every one of its 5 models was either deprecated/non-serverless
# or rate-limited, so every call silently wasted ~10s per model before giving
# up empty. get_together_models() falls back to a working default list if the
# config file is ever missing.

if not TOGETHER_API_KEY:
    logger.warning("⚠️  TOGETHER_API_KEY is not set — LLM persona text will use fallbacks. Add it to .env")
else:
    logger.info(f"✓ TOGETHER_API_KEY loaded (ends with ...{TOGETHER_API_KEY[-6:]})")


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
        t0 = time.monotonic()

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
                usage = data.get("usage") or {}
                log_llm_call(
                    provider="together", agent="embeddings", call_type="create_embeddings",
                    duration_ms=int((time.monotonic() - t0) * 1000), success=True, model=model_name,
                    prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                    total_tokens=int(usage.get("total_tokens", usage.get("prompt_tokens", 0)) or 0),
                    note="" if usage else f"{len(texts)} texts embedded; provider did not report token usage",
                )

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
        log_llm_call(
            provider="together", agent="embeddings", call_type="create_embeddings",
            duration_ms=int((time.monotonic() - t0) * 1000), success=False, fallback_used=True,
            note=str(last_error)[:200],
        )
        logger.error(f"❌ All embedding models failed. Last error: {last_error}")
        logger.info("💡 Falling back to zero embeddings - search will use keyword matching")
        return np.zeros((len(texts), 1024))  # Updated to match BAAI/bge-large-en-v1.5 dimension
    
    def generate_text(
        self,
        prompt: str,
        system_message: str = "You are a helpful AI assistant specialized in marketing and customer analysis.",
        model: str = "",
        max_tokens: int = 500,
        temperature: float = 0.7,
        agent_name: str = "unknown",
        call_type: str = "general",
    ) -> str:
        """
        Generate text using LLM. Tries several Together models in the order set by
        config/llm_priority.json, then falls back to Claude/Anthropic (via
        claude_client) if every Together model fails — so a Together outage
        degrades to "slower" rather than "silently empty". Set TOGETHER_CHAT_MODEL
        in .env, or pass `model=`, to force a specific model to the front of the list.
        """
        t0 = time.monotonic()
        if not self.api_key or len(self.api_key) < 8:
            logger.debug("Together chat skipped: no API key — trying Claude fallback")
            return self._claude_fallback(prompt, system_message, max_tokens, temperature, agent_name, call_type)

        env_model = (os.getenv("TOGETHER_CHAT_MODEL") or "").strip()
        models_to_try = []
        if env_model:
            models_to_try.append(env_model)
        if model and model not in models_to_try:
            models_to_try.append(model)
        for m in get_together_models():
            if m not in models_to_try:
                models_to_try.append(m)

        url = f"{TOGETHER_API_BASE}/chat/completions"
        safe_max = max(1, min(int(max_tokens), 8192))
        # Avoid empty user content (some APIs return 400)
        user_content = (prompt or "").strip() or "Respond with OK."
        sys_content = (system_message or "").strip() or "You are a helpful assistant."

        last_detail = None
        for mname in models_to_try:
            try:
                payload = {
                    "model": mname,
                    "messages": [
                        {"role": "system", "content": sys_content[:120000]},
                        {"role": "user", "content": user_content[:120000]},
                    ],
                    "max_tokens": safe_max,
                    "temperature": float(temperature),
                }
                response = requests.post(
                    url, json=payload, headers=self.headers, verify=False, timeout=90
                )
                if response.status_code != 200:
                    try:
                        err_body = response.json()
                        detail = err_body.get("error", err_body)
                        last_detail = str(detail)[:500]
                    except Exception:
                        last_detail = response.text[:500]
                    logger.warning(
                        f"Together chat model={mname} status={response.status_code}: {last_detail}"
                    )
                    if response.status_code in (429, 503):
                        import time as _time
                        logger.info(f"Together chat rate-limited ({response.status_code}), backing off 3s before next model…")
                        _time.sleep(3)
                    continue

                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    logger.warning(f"Together chat empty choices for {mname}")
                    continue
                generated_text = (choices[0].get("message") or {}).get("content") or ""
                if not generated_text.strip():
                    continue
                usage = data.get("usage") or {}
                log_llm_call(
                    provider="together", agent=agent_name, call_type=call_type,
                    duration_ms=int((time.monotonic() - t0) * 1000), success=True, model=mname,
                    prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                    completion_tokens=int(usage.get("completion_tokens", 0) or 0),
                    total_tokens=int(usage.get("total_tokens", 0) or 0),
                )
                logger.info(f"✅ Generated {len(generated_text)} chars with {mname}")
                return generated_text

            except requests.exceptions.RequestException as e:
                last_detail = str(e)
                logger.warning(f"Together chat request failed ({mname}): {e}")
                continue

        log_llm_call(
            provider="together", agent=agent_name, call_type=call_type,
            duration_ms=int((time.monotonic() - t0) * 1000), success=False, fallback_used=True,
            note=str(last_detail)[:200] if last_detail else "",
        )
        logger.error(f"❌ All Together chat models failed. Last detail: {last_detail}")
        return self._claude_fallback(prompt, system_message, max_tokens, temperature, agent_name, call_type)

    def _claude_fallback(
        self, prompt: str, system_message: str, max_tokens: int, temperature: float,
        agent_name: str, call_type: str,
    ) -> str:
        """
        Safety net for direct-Together callers (e.g. generate_marketing_opportunities)
        that have no fallback of their own: if every Together model just failed (or
        there's no Together key at all), try Claude/Anthropic once directly before
        giving up completely. Calls claude_client's Anthropic path directly (not its
        generate_text()) so this doesn't re-try Together AI a second time — we
        already know it just failed.
        """
        _t0 = time.monotonic()
        try:
            from utils.claude_client import get_claude_client
            claude = get_claude_client()
            if not claude._anthropic_client:
                return "Error generating description"
            result, usage = claude._call_anthropic(prompt, system_message, max_tokens, temperature, model="")
            result = (result or "").strip()
            if result:
                log_llm_call(
                    provider="anthropic", agent=agent_name, call_type=call_type,
                    duration_ms=int((time.monotonic() - _t0) * 1000), success=True,
                    model=usage.get("model", ""), prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0), total_tokens=usage.get("total_tokens", 0),
                    fallback_used=True,
                )
                logger.info(f"[together_ai] Together unavailable for {call_type} — succeeded via Claude fallback")
                return result
        except Exception as e:
            logger.warning(f"[together_ai] Claude fallback also failed: {e}")
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
            temperature=0.8,
            agent_name="agent_a",
            call_type="persona_name",
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
            temperature=0.7,
            agent_name="agent_a",
            call_type="persona_description",
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
                temperature=0.6,
                agent_name="agent_b",
                call_type="product_reasoning",
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
            temperature=0.7,
            agent_name="agent_a",
            call_type="clustering_quality_explanation",
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
            temperature=0.7,
            agent_name="agent_a",
            call_type="visualization_explanation",
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
            temperature=0.7,
            agent_name="agent_a",
            call_type="persona_insights",
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
            temperature=0.7,
            agent_name="agent_b",
            call_type="banking_product_explanation",
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
            temperature=0.7,
            agent_name="agent_b",
            call_type="segment_product_reasoning",
        )

    def generate_agent_b_vs_c_explanation(
        self,
        persona_name: str,
        churn_category: str,
        agent_b_top_name: str,
        agent_b_top_score: float,
        agent_c_name: str,
        agent_c_score: float,
        agent_b_products_line: str,
    ) -> str:
        """
        Explain why Agent C's one-best offer may differ from Agent B's top match-ranked product.
        Must reference both product names (banking advisors / marketers).
        """
        prompt = f"""You are a banking strategy assistant. Write 3–4 short sentences (plain text, no bullets).

Context:
- Customer segment (persona): {persona_name}
- Churn risk band: {churn_category or "Not elevated"}
- Agent B (product recommender) ranks products by persona/fit. Its top match is "{agent_b_top_name}" at {agent_b_top_score*100:.0f}% match strength.
- Agent C (one-best-offer / retention engine) selected "{agent_c_name}" at {agent_c_score*100:.0f}% after applying retention and business rules.

Agent B top products (for reference): {agent_b_products_line}

Explain clearly:
1) Why leading with "{agent_c_name}" can improve retention or purchase likelihood compared to leading with "{agent_b_top_name}" for this customer context.
2) Mention both product names naturally.
3) If churn is High or Critical, tie the story to protecting the relationship; otherwise focus on best next product to deepen the relationship.

Do not use markdown asterisks or numbered lists."""

        system_message = (
            "You are a concise banking marketing strategist. Be specific and professional. "
            "Always include the exact product names given."
        )

        return self.generate_text(
            prompt=prompt,
            system_message=system_message,
            max_tokens=320,
            temperature=0.55,
            agent_name="agent_c",
            call_type="agent_b_vs_c_explanation",
        )

    def generate_marketing_opportunities(
        self,
        persona_name: str,
        segment_definition: str,
        key_behaviors: List[str],
        metrics: Dict[str, Any]
    ) -> List[str]:
        """
        Generate 3-4 unique, actionable marketing opportunities for a single segment.
        Used so each macro/micro segment gets truthful, strategy-ready recommendations.
        Returns list of strings; empty list on failure.
        """
        try:
            m = metrics
            prompt = f"""Segment name: {persona_name}

Segment definition:
{segment_definition}

Key behaviors:
{chr(10).join('- ' + b for b in key_behaviors[:4])}

Key metrics (use these to keep recommendations truthful):
- Avg deposits: ${m.get('avg_deposits', 0):,.0f}
- Avg income: ${m.get('avg_income', 0):,.0f}/year
- Digital engagement: {m.get('avg_digital', 0)*100:.0f}%
- Avg products: {m.get('avg_products', 0):.1f}
- Monthly transactions: {m.get('avg_transactions', 0):.0f}
- Cross-sell receptivity: {m.get('avg_cross_sell', 0)*100:.0f}%
- Avg age: {m.get('avg_age', 45):.0f}

Generate exactly 3 or 4 opportunities. RULES: Each bullet MUST be one short sentence, max 12–15 words. Start with one action verb: Run, Offer, Propose, Target, Launch. Include segment name or one key number (e.g. 72% digital, $4M deposits). No long explanations. Output only the bullets, one per line, no numbering."""

            system_message = "You are a banking strategy consultant. Output 3-4 very short bullets for marketers. Each bullet: max 15 words, one action verb, one number or segment name. No long sentences. Easy to scan."

            text = self.generate_text(
                prompt=prompt,
                system_message=system_message,
                max_tokens=280,
                temperature=0.6,
                agent_name="agent_a",
                call_type="marketing_opportunities",
            )
            if not text or "Error generating" in text:
                return []
            # Parse into list: split by newline, strip bullets/numbers, keep non-empty
            lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
            cleaned = []
            max_len = 100  # keep bullets scannable
            _preamble_starts = (
                'here are', 'below are', 'the following', 'these are',
                'above are', 'opportunities for', 'here is', 'i have',
            )
            for ln in lines:
                ln = ln.lstrip("0123456789.-*•) ")
                # Skip preamble / header lines
                ln_lower = ln.lower()
                if any(ln_lower.startswith(p) for p in _preamble_starts):
                    continue
                if ln.endswith(':'):
                    continue
                if len(ln) > 20:
                    # Use first sentence only, or truncate to max_len
                    first_sentence = ln.split(".")[0].strip()
                    if first_sentence and len(first_sentence) <= max_len + 10:
                        ln = first_sentence + ("." if not first_sentence.endswith(".") else "")
                    elif len(ln) > max_len:
                        ln = ln[: max_len - 3].rsplit(" ", 1)[0] + "..."
                    cleaned.append(ln)
            return cleaned[:4] if cleaned else []
        except Exception as e:
            logger.warning(f"generate_marketing_opportunities failed: {e}")
            return []


    def generate_complete_customer_analysis(
        self,
        customer: Dict[str, Any],
        recommended_product: Dict[str, Any],
        selected_offer: Optional[Dict[str, Any]] = None,
        persona_name: str = "",
        churn_category: str = "",
    ) -> Dict[str, Any]:
        """
        Comprehensive LLM customer analysis for agentic product recommendation.

        Reads all 52+ customer signals (income, credit, life_stage, financial_goal,
        spending, debt, competitor card, digital engagement, etc.) and produces:
          customer_insight_summary  — who they are and what they need now
          product_fit_rationale     — why THIS product fits THIS customer
          channel_rationale         — which channel and why
          personalized_pitch        — ready-to-use 2-sentence pitch for banker/email
          urgency_signal            — time-sensitive reason to act now (or none)

        Returns {} on any failure — caller uses rule-based fallback.
        """
        age             = int(float(customer.get("age", 40) or 40))
        income          = float(customer.get("income", 40000) or 40000)
        credit_score    = int(float(customer.get("credit_score", 650) or 650))
        total_deposits  = float(customer.get("total_deposits", 5000) or 5000)
        life_stage      = str(customer.get("life_stage", "") or "")
        financial_goal  = str(customer.get("financial_goal", "") or "").replace("_", " ")
        num_products    = int(float(customer.get("num_products", 1) or 1))
        employment_type = str(customer.get("employment_type", "") or "")
        primary_cat     = str(customer.get("primary_spending_category", "") or "")
        monthly_spend   = float(customer.get("monthly_spend_in_primary_cat", 0) or 0)
        debt_total      = float(customer.get("outstanding_debt_total", 0) or 0)
        has_competitor  = bool(customer.get("has_competitor_credit_card", False))
        try:
            high_overdraft = bool(int(float(customer.get("high_overdraft_flag", 0) or 0)))
        except (TypeError, ValueError):
            high_overdraft = False
        digital_raw     = customer.get("digital_engagement_score") or customer.get("digital_engagement")
        digital_score   = float(digital_raw if digital_raw is not None else 0.5)
        pref_channel    = str(customer.get("preferred_channel", "") or "")
        fee_sensitivity = str(customer.get("fee_sensitivity_tier", "medium") or "medium")
        travel_freq     = str(customer.get("travel_frequency", "") or "")
        home_type       = str(customer.get("home_ownership_type", "") or "")
        recent_event    = str(customer.get("recent_life_event", "") or "")

        product_name   = str(recommended_product.get("product_name", "") or "")
        product_subcat = str(recommended_product.get("subcategory", "") or "")
        product_fee    = float(recommended_product.get("annual_fee", 0) or 0)
        raw_rate       = recommended_product.get("interest_rate") or recommended_product.get("interest_rate_apy") or 0
        product_rate   = float(raw_rate or 0)
        is_deposit     = product_subcat.lower() in ("savings", "cd", "investment", "money market")
        rate_label     = f"{product_rate:.2%} {'APY' if is_deposit else 'APR'}" if product_rate else "competitive rate"

        offer_name  = str((selected_offer or {}).get("offer_name", "") or "")
        offer_value = str((selected_offer or {}).get("headline_value", "") or "")
        channel_display = pref_channel or ("mobile app" if digital_score >= 0.65 else "email")

        prompt = f"""You are an AI banking advisor at Meridian Bank. Analyze this customer and generate a precise recommendation report.

CUSTOMER PROFILE:
- Segment: {persona_name}, Age: {age}, Life Stage: {life_stage or 'not specified'}
- Employment: {employment_type or 'not specified'}, Home: {home_type or 'not specified'}
- Income: ${income:,.0f}/yr, Credit Score: {credit_score}, Deposits: ${total_deposits:,.0f}
- Current Meridian products: {num_products}
- Financial Goal: {financial_goal or 'not specified'}
- Primary spending: {primary_cat or 'not specified'} at ${monthly_spend:,.0f}/month
- Outstanding debt: ${debt_total:,.0f}
- Competitor credit card: {'Yes' if has_competitor else 'No'}
- Overdraft issues: {'Yes — frequent' if high_overdraft else 'No'}
- Digital engagement: {digital_score:.0%} (preferred channel: {channel_display})
- Fee sensitivity: {fee_sensitivity}
- Travel frequency: {travel_freq or 'not specified'}
- Recent life event: {recent_event or 'none'}
- Churn risk: {churn_category or 'Normal'}

RECOMMENDED PRODUCT: {product_name} ({product_subcat}), annual fee ${product_fee:.0f}, rate {rate_label}
{f'SELECTED OFFER: {offer_name} — {offer_value}' if offer_name else ''}

Output a JSON object with EXACTLY these 5 keys (no other keys, no markdown):
- "customer_insight_summary": 2 sentences — WHO this customer is and WHAT they need most. Reference age, life stage, goal, and one financial signal.
- "product_fit_rationale": 2 sentences — WHY {product_name} fits THIS customer. Reference credit score, deposits, debt, or spending data specifically.
- "channel_rationale": 1 sentence — WHY use {channel_display} for this customer based on their {digital_score:.0%} digital engagement.
- "personalized_pitch": 2 sentences ready for a banker or email campaign — open with the customer's goal/life stage, close with the product benefit.
- "urgency_signal": 1 sentence about any time-sensitive reason to act now (life event, competitor card, churn risk, debt). If none: "No immediate urgency — recommend standard outreach."

Output ONLY the JSON object."""

        system_msg = (
            "You are a senior AI banking advisor. Output only a valid JSON object — "
            "no markdown, no preamble, no explanation. "
            "Be specific: reference exact numbers from the customer profile."
        )

        raw = self.generate_text(
            prompt=prompt,
            system_message=system_msg,
            max_tokens=650,
            temperature=0.6,
            agent_name="agent_b",
            call_type="complete_customer_analysis",
        )

        if not raw or "Error generating" in raw:
            return {}

        import json as _json
        import re as _re

        cleaned = raw.strip()
        cleaned = _re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = _re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        EXPECTED_KEYS = (
            "customer_insight_summary",
            "product_fit_rationale",
            "channel_rationale",
            "personalized_pitch",
            "urgency_signal",
        )

        def _extract_str_field(text, key):
            m = _re.search(
                rf'"{_re.escape(key)}"\s*:\s*"((?:[^"\\]|\\.)*)"', text, _re.DOTALL
            )
            if m:
                try:
                    return _json.loads('"' + m.group(1) + '"')
                except Exception:
                    return m.group(1)
            return None

        try:
            parsed = _json.loads(cleaned)
        except Exception:
            parsed = {}
            for k in EXPECTED_KEYS:
                v = _extract_str_field(cleaned, k)
                if v is not None:
                    parsed[k] = v

        if not parsed or not set(EXPECTED_KEYS).intersection(parsed.keys()):
            logger.warning("generate_complete_customer_analysis: no usable keys parsed")
            return {}

        return {k: str(parsed.get(k, "")) for k in EXPECTED_KEYS}

    def generate_offer_communication_content(
        self,
        customer_profile: Dict[str, Any],
        product: Dict[str, Any],
        offer: Dict[str, Any],
        best_channel: str,
    ) -> Dict[str, Any]:
        """
        Generate personalized flyer/email/push/SMS content for a selected offer.
        Returns dict with: flyer_content, email_content, push_notification, sms_text,
        generation_source. Falls back to empty dict on failure (caller uses template).
        """
        age         = int(customer_profile.get("age", 40))
        income_tier = str(customer_profile.get("income_tier", "mid income"))
        credit_tier = str(customer_profile.get("credit_tier", "good"))
        persona     = str(customer_profile.get("persona_name", ""))
        goal        = str(customer_profile.get("financial_goal_hint", "growing savings"))
        pname       = str(product.get("product_name", "this product"))
        subcategory = str(product.get("subcategory", "Banking"))
        offer_name  = str(offer.get("offer_name", "this offer"))
        terms       = str(offer.get("terms_summary", ""))
        vp          = str(offer.get("value_proposition", ""))

        system_msg = (
            "You are a bank marketing copywriter. "
            "Output only a single valid JSON object — no preamble, no explanation, no markdown. "
            "Never use ALL CAPS except in push notifications. Keep copy warm, professional, and specific."
        )

        prompt = f"""Customer: age {age}, {income_tier}, {credit_tier} credit, financial goal: {goal}.
Segment: {persona}.
Product: {pname} ({subcategory}).
Offer: {offer_name}.
Offer detail: {vp}
Terms: {terms}
Preferred channel: {best_channel}

Write a JSON object with exactly these keys:
- "flyer_headline": punchy customer-specific headline referencing the offer value, max 12 words
- "flyer_body": 2-3 sentences connecting customer's financial goal to the offer benefit, max 150 words
- "email_subject": email subject line creating urgency or curiosity, max 60 characters
- "email_body": personalized email — opening line addresses financial goal; middle paragraph explains offer clearly with terms; closing is a call to action for {best_channel} channel; max 250 words
- "push_notification": app push text, max 50 characters, include key benefit and a verb
- "sms_text": SMS text, max 160 characters, include product name and offer value

Output ONLY the JSON object."""

        raw = self.generate_text(
            prompt=prompt,
            system_message=system_msg,
            max_tokens=900,
            temperature=0.65,
            agent_name="agent_c",
            call_type="offer_communication_content",
        )

        if not raw or "Error generating" in raw:
            return {}

        # Parse JSON from LLM response
        import json as _json
        import re as _re

        # Strip any markdown code fences
        cleaned = raw.strip()
        cleaned = _re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = _re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        def _extract_field(text, key):
            """Extract a string value for a JSON key even from partial/malformed JSON."""
            import re as _re2
            # Try double-quoted value
            m = _re2.search(rf'"{_re2.escape(key)}"\s*:\s*"((?:[^"\\]|\\.)*)"', text, _re2.DOTALL)
            if m:
                try:
                    return _json.loads('"' + m.group(1) + '"')
                except Exception:
                    return m.group(1)
            return None

        try:
            parsed = _json.loads(cleaned)
        except (_json.JSONDecodeError, Exception):
            # Try partial extraction field-by-field
            parsed = {}
            for k in ("flyer_headline","flyer_body","email_subject","email_body","push_notification","sms_text"):
                v = _extract_field(cleaned, k)
                if v is not None:
                    parsed[k] = v

        if not parsed:
            logger.warning("generate_offer_communication_content: empty parse result")
            return {}

        # Need at least the most important fields
        min_fields = {"flyer_headline", "push_notification"}
        if not min_fields.issubset(parsed.keys()):
            logger.warning(f"generate_offer_communication_content: missing required fields, got {list(parsed.keys())}")
            return {}

        return {
            "flyer_content": {
                "headline": str(parsed.get("flyer_headline", "")),
                "body": str(parsed.get("flyer_body", "")),
            },
            "email_content": {
                "subject": str(parsed.get("email_subject", "")),
                "body": str(parsed.get("email_body", "")),
            },
            "push_notification": str(parsed.get("push_notification", ""))[:55],
            "sms_text": str(parsed.get("sms_text", ""))[:160],
            "generation_source": "llm",
        }


# Global instance
together_ai = TogetherAIService()


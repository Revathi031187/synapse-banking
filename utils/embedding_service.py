"""
Embedding Service for Customer and Product Data
Generates text representations and handles vectorization
"""

import pandas as pd
import json
from typing import Dict, List, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Handles text generation for embedding purposes"""
    
    @staticmethod
    def customer_to_text_banking(customer: Dict[str, Any]) -> str:
        """
        Convert banking customer data to rich text representation
        
        Args:
            customer: Customer dictionary
            
        Returns:
            Text representation for embedding
        """
        parts = []
        
        # Demographics
        parts.append(f"Customer {customer.get('customer_id', 'Unknown')}")
        parts.append(f"Age {customer.get('age', 'Unknown')}")
        parts.append(f"Income ${customer.get('income', 0):,.0f}")
        parts.append(f"Credit score {customer.get('credit_score', 'Unknown')}")
        
        # Banking relationship
        parts.append(f"Tenure {customer.get('tenure_months', 0)} months")
        parts.append(f"Tier {customer.get('value_tier', 'Unknown')}")
        
        # Engagement
        parts.append(f"Login frequency {customer.get('login_frequency_30d', 0)} times")
        parts.append(f"Transaction volume {customer.get('transaction_volume_30d', 0)}")
        
        # Intent signals
        intent_score = customer.get('intent_score', 0)
        parts.append(f"Intent score {intent_score:.2f}")
        
        if customer.get('primary_intent'):
            parts.append(f"Primary intent: {customer['primary_intent']}")
        
        # Life events
        if customer.get('primary_life_event'):
            parts.append(f"Life event: {customer['primary_life_event']}")
        
        # Product holdings
        if customer.get('product_holdings'):
            parts.append(f"Products: {', '.join(customer['product_holdings'])}")
        
        # Channel preferences
        if customer.get('channel_preference'):
            parts.append(f"Prefers {customer['channel_preference']}")
        
        return " | ".join(parts)
    
    @staticmethod
    def customer_to_text_retail(customer: Dict[str, Any]) -> str:
        """
        Convert retail customer data to rich text representation
        
        Args:
            customer: Customer dictionary
            
        Returns:
            Text representation for embedding
        """
        parts = []
        
        # Demographics
        parts.append(f"Customer {customer.get('customer_id', 'Unknown')}")
        parts.append(f"Age {customer.get('age', 'Unknown')}")
        parts.append(f"Income ${customer.get('income', 0):,.0f}")
        
        # RFM scores
        parts.append(f"Recency {customer.get('recency_score', 0)}")
        parts.append(f"Frequency {customer.get('frequency_score', 0)}")
        parts.append(f"Monetary {customer.get('monetary_score', 0)}")
        
        # Shopping behavior
        parts.append(f"AOV ${customer.get('avg_order_value', 0):.2f}")
        parts.append(f"Basket size {customer.get('avg_basket_size', 0):.1f}")
        
        # Engagement
        parts.append(f"Web visits {customer.get('web_visits_30d', 0)}")
        parts.append(f"App usage {customer.get('app_engagement_score', 0):.2f}")
        
        # Purchase intent
        intent_score = customer.get('intent_score', 0)
        parts.append(f"Intent score {intent_score:.2f}")
        
        # Category preferences
        if customer.get('preferred_category'):
            parts.append(f"Prefers {customer['preferred_category']}")
        
        # Marketing responsiveness
        if customer.get('promo_response_rate'):
            parts.append(f"Promo response {customer['promo_response_rate']:.1%}")
        
        # Channel
        if customer.get('channel_preference'):
            parts.append(f"Shops via {customer['channel_preference']}")
        
        return " | ".join(parts)
    
    @staticmethod
    def persona_to_text(persona: Dict[str, Any], industry: str = "banking") -> str:
        """
        Convert persona to text representation
        
        Args:
            persona: Persona dictionary
            industry: 'banking' or 'retail'
            
        Returns:
            Text representation for embedding
        """
        parts = []
        
        # Cluster info
        parts.append(f"Cluster {persona.get('cluster_id', 'Unknown')}")
        parts.append(f"Size {persona.get('size', 0)} customers")
        
        # Core attributes
        parts.append(f"Avg age {persona.get('avg_age', 0):.1f}")
        parts.append(f"Avg income ${persona.get('avg_income', 0):,.0f}")
        
        # Engagement
        parts.append(f"Engagement {persona.get('avg_engagement', 0):.2f}")
        parts.append(f"Intent {persona.get('avg_intent', 0):.2f}")
        
        # AI insights
        if persona.get('ai_insights'):
            parts.append(f"Profile: {persona['ai_insights'].get('profile', '')}")
            parts.append(f"Strategy: {persona['ai_insights'].get('strategy', '')}")
        
        return " | ".join(parts)
    
    @staticmethod
    def product_to_text_banking(product: Dict[str, Any]) -> str:
        """
        Convert banking product to text representation
        
        Args:
            product: Product dictionary
            
        Returns:
            Text representation for embedding
        """
        parts = []
        
        parts.append(f"Product {product.get('product_id', 'Unknown')}")
        parts.append(f"Name {product.get('product_name', 'Unknown')}")
        parts.append(f"Type {product.get('product_type', 'Unknown')}")
        parts.append(f"Category {product.get('category', 'Unknown')}")
        
        # Fees and rates
        if product.get('annual_fee'):
            parts.append(f"Annual fee ${product['annual_fee']}")
        
        if product.get('interest_rate'):
            parts.append(f"Rate {product['interest_rate']}%")
        
        # Requirements
        if product.get('min_credit_score'):
            parts.append(f"Min credit {product['min_credit_score']}")
        
        if product.get('min_income'):
            parts.append(f"Min income ${product['min_income']:,.0f}")
        
        # Benefits
        if product.get('features'):
            parts.append(f"Features: {', '.join(product['features'][:3])}")
        
        return " | ".join(parts)
    
    @staticmethod
    def product_to_text_retail(product: Dict[str, Any]) -> str:
        """
        Convert retail product to text representation
        
        Args:
            product: Product dictionary
            
        Returns:
            Text representation for embedding
        """
        parts = []
        
        parts.append(f"Product {product.get('product_id', 'Unknown')}")
        parts.append(f"Name {product.get('product_name', 'Unknown')}")
        parts.append(f"Category {product.get('category', 'Unknown')}")
        parts.append(f"Subcategory {product.get('subcategory', 'Unknown')}")
        
        # Pricing
        parts.append(f"Price ${product.get('price', 0):.2f}")
        
        # Attributes
        if product.get('brand'):
            parts.append(f"Brand {product['brand']}")
        
        if product.get('rating'):
            parts.append(f"Rating {product['rating']:.1f}/5")
        
        # Tags
        if product.get('tags'):
            parts.append(f"Tags: {', '.join(product['tags'][:3])}")
        
        return " | ".join(parts)
    
    @staticmethod
    def dataframe_to_documents(
        df: pd.DataFrame,
        text_func: callable,
        id_column: str = "customer_id"
    ) -> tuple:
        """
        Convert DataFrame to ChromaDB format
        
        Args:
            df: Source DataFrame
            text_func: Function to convert row to text
            id_column: Column to use as document ID
            
        Returns:
            Tuple of (documents, metadatas, ids)
        """
        documents = []
        metadatas = []
        ids = []
        
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            
            # Generate text representation
            text = text_func(row_dict)
            documents.append(text)
            
            # Prepare metadata (convert numpy types to Python types)
            # ChromaDB doesn't accept None values, so we skip them
            metadata = {}
            for key, value in row_dict.items():
                if pd.isna(value) or value is None:
                    continue  # Skip None/NaN values
                elif isinstance(value, (list, dict)):
                    metadata[key] = json.dumps(value)
                elif hasattr(value, 'item'):  # numpy types
                    val = value.item()
                    if val is not None:  # Double check after conversion
                        metadata[key] = val
                else:
                    metadata[key] = value
            
            metadatas.append(metadata)
            
            # Use ID column
            ids.append(str(row_dict[id_column]))
        
        logger.info(f"✅ Converted {len(documents)} records to documents")
        return documents, metadatas, ids


logger.info("✨ Embedding Service initialized")


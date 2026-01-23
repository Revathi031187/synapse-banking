"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class CustomerContext(BaseModel):
    """Customer context for NBA request."""
    device: str = "desktop"
    location: str = "home"
    session_duration: int = 300
    pages_viewed: int = 5
    hour: int = 14


class NBARequest(BaseModel):
    """Request for Next Best Actions."""
    customer_id: str = Field(..., description="Customer ID")
    context: Optional[CustomerContext] = None
    top_n: int = Field(default=3, ge=1, le=10)


class InteractionRequest(BaseModel):
    """Request to record customer interaction."""
    customer_id: str
    offer_id: str
    action: str = Field(..., description="Action type: view, click, add_to_cart, purchase, ignore")
    revenue: float = Field(default=0.0, ge=0)


class PersonaInfo(BaseModel):
    """Customer persona information."""
    customer_id: str
    persona_cluster: int
    persona_name: str
    intent: str
    intent_confidence: float
    life_event: str
    loyalty_tier: str


class ProductInfo(BaseModel):
    """Product information."""
    product_id: str
    product_name: str
    category: str
    base_price: float


class OfferInfo(BaseModel):
    """Offer information."""
    offer_id: str
    product_id: str
    product_name: str
    pricing: Dict[str, float]
    message: str
    channel: str
    timing: str
    priority: str


class NBAResponse(BaseModel):
    """Response with Next Best Actions."""
    customer_id: str
    customer_persona: Dict[str, Any]
    next_best_actions: List[Dict[str, Any]]
    context: Dict[str, Any]
    timestamp: str


class SystemInsights(BaseModel):
    """System-level insights and metrics."""
    persona_distribution: Dict[str, int]
    intent_distribution: Dict[str, int]
    performance_metrics: Dict[str, float]
    total_customers: int
    active_customers: int
    total_products: int


class StatusResponse(BaseModel):
    """API status response."""
    status: str
    version: str
    timestamp: str
    agents_initialized: bool


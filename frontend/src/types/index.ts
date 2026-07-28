export interface Customer {
  customer_id: string;
  name?: string;
  email?: string;
  age?: number;
  is_active: boolean;
  loyalty_tier: string;
}

export interface Product {
  product_id: string;
  product_name: string;
  category: string;
  price: number;
  description?: string;
}

export interface Transaction {
  transaction_id: string;
  customer_id: string;
  product_id: string;
  total_amount: number;
  transaction_date: string;
  channel: string;
}

export interface BehavioralEvent {
  event_id: string;
  customer_id: string;
  event_type: string;
  timestamp: string;
  metadata?: any;
}

export interface CustomerPersona {
  persona_name: string;
  intent: string;
  intent_confidence: number;
  loyalty_tier: string;
  life_event: string;
  rfm: {
    recency_days: number;
    frequency: number;
    monetary_value: number;
  };
  propensity_scores: {
    purchase: number;
    crosssell: number;
    churn: number;
  };
}

export interface Pricing {
  base_price: number;
  final_price: number;
  discount_pct: number;
}

export interface NextBestAction {
  product_name: string;
  product_id: string;
  priority: 'high' | 'medium' | 'low';
  message: string;
  pricing: Pricing;
  confidence: number;
  channel: string;
  timing: string;
  incentive_type: string;
  bundle_offer?: {
    bundle_name: string;
    bundle_products: string[];
    bundle_price: number;
    total_price: number;
    savings: number;
    bundle_discount_pct: number;
  };
}

export interface NBAResponse {
  customer_persona: CustomerPersona;
  next_best_actions: NextBestAction[];
  timestamp: string;
}

export interface SystemStatus {
  data_generated: boolean;
  system_initialized: boolean;
  orchestrator_ready: boolean;
  initializing?: boolean;
}

export interface AgentInsight {
  agent_id: string;
  agent_name: string;
  metrics: Record<string, any>;
  charts: any[];
}


import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import BankingAdSpend from './BankingAdSpend';
import CustomerSearchSelect from '../../components/CustomerSearchSelect';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import PinnedOfferCard from '../../components/PinnedOfferCard';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  User,
  ChevronDown,
  ChevronUp,
  Mail,
  Globe,
  Building2,
  Smartphone,
  AlertTriangle,
  Target,
  TrendingUp,
  Shield,
  ArrowRight,
  Loader2,
  Users,
  Gift,
  MessageSquare,
  Copy,
  CheckCircle2,
  Tag,
  Zap,
  Clock,
  Send,
  RefreshCw,
  Pencil,
  X,
  Phone,
  FlaskConical,
  BarChart2,
  GitBranch,
  Activity,
  Info,
  MessageCircle,
} from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';
import { useSessionStorageState } from '../../hooks/useSessionStorageState';

const API_BASE = getBankingApiBase();

const AGENT_C_UI_KEY = 'banking-agent-c-v1';

type BankingAgentCUiState = {
  offerScope: 'customer' | 'persona';
  churnRiskView: 'customer' | 'persona';
  /** Customer mode: a real customer_id. Persona mode: a `persona:<id>` marker, set
   * only when "Compute Best Offer" is clicked (no customer picker  -  persona mode is
   * segment-wide, not one hand-picked person); see the offerData queryFn below,
   * which branches on this prefix to call the segment-wide endpoint instead of the
   * per-customer one. */
  selectedCustomerId: string | null;
  /** Customer mode only: the picker's current selection, staged until "Get Best
   * Offer" is clicked (see offerData's useQuery below  -  computing only happens on
   * demand now, never just from picking a customer). */
  pendingCustomerId: string | null;
  explainOpen: boolean;
  selectedPersonaId: string | null;
  activeCommTab: 'push' | 'email' | 'flyer';
  offerScoreOpen: boolean;
  personaOfferScoreOpen: boolean;
  personaCommTab: 'push' | 'email' | 'flyer';
  // Mirror of the last successful one-best-offer response, persisted across a
  // reload (this tab has no merge function stripping it, matching Director's
  // "restore what I left" convention). Seeds the query's initialData so a
  // reload shows the last result immediately with no network call  -  without
  // this, `enabled: !!selectedCustomerId` (also reload-persisted) would fire a
  // fresh fetch the instant the component mounts, since the in-memory
  // QueryClient cache (unlike sessionStorage) does not survive a reload.
  lastResult: { customerId: string; response: unknown } | null;
};

const DEFAULT_AGENT_C_UI: BankingAgentCUiState = {
  offerScope: 'customer',
  churnRiskView: 'customer',
  selectedCustomerId: null,
  pendingCustomerId: null,
  lastResult: null,
  explainOpen: true,
  selectedPersonaId: null,
  activeCommTab: 'push',
  offerScoreOpen: false,
  personaOfferScoreOpen: false,
  personaCommTab: 'push',
};

/** Standalone one-best-offer fetch, given an explicit customer/persona-marker
 * snapshot rather than closing over live component state - used both by the
 * reactive offerData query and by the compute buttons' always-fresh imperative
 * fetchQuery calls. */
async function fetchOneBestOffer(apiBase: string, selectedCustomerId: string | null) {
  const personaMarkerId = selectedCustomerId?.startsWith('persona:') ? selectedCustomerId.slice('persona:'.length) : null;
  const url = personaMarkerId
    ? `${apiBase}/api/banking/agent_c/persona-best-offer?persona_id=${encodeURIComponent(personaMarkerId)}`
    : `${apiBase}/api/banking/agent_c/one-best-offer/${selectedCustomerId}`;
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to load offer');
  }
  return res.json();
}

const channelIcons: Record<string, React.ReactNode> = {
  email: <Mail className="w-4 h-4" />,
  web: <Globe className="w-4 h-4" />,
  in_app: <Smartphone className="w-4 h-4" />,
  branch: <Building2 className="w-4 h-4" />,
  direct_mail: <Mail className="w-4 h-4" />,
  outbound_call: <Smartphone className="w-4 h-4" />,
};

function formatExplanation(text: string | undefined): string[] {
  if (!text) return [];
  return text
    .replace(/\*\*/g, '')
    .split(/\n+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function formatRetentionStrategy(text: string | undefined): string {
  if (!text) return '';
  return text.replace(/\s*\|\s*/g, '\n');
}

function pct(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return ' - ';
  return `${Math.round(v * 100)}%`;
}

/** Compact table cells: expand on demand so more churn rows fit on screen. */
function CollapsibleChurnText({
  text,
  collapseThreshold = 96,
}: {
  text: string;
  /** Show toggle when text is longer than this (Reason copy is often under 160 chars but still clipped in the table). */
  collapseThreshold?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const t = (text || '').trim();
  if (!t) return <span className="text-slate-400"> - </span>;
  const long = t.length > collapseThreshold || t.split(/\n/).length > 2;
  return (
    <div className="min-w-0 max-w-md">
      <div
        className={
          expanded
            ? 'text-slate-600 text-xs leading-snug whitespace-pre-line break-words'
            : 'text-slate-600 text-xs leading-snug whitespace-pre-line break-words line-clamp-2 overflow-hidden'
        }
      >
        {t}
      </div>
      {long && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="mt-1 text-violet-600 text-xs font-medium hover:underline"
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  );
}

type AgentCCustomerMetrics = {
  days_since_last_txn?: number;
  recent_txn_count?: number;
  txn_count_90d?: number;
  avg_txn_amount_90d?: number;
  txn_amount_cv_90d?: number;
  mobile_share_90d?: number;
  branch_share_90d?: number;
  weekend_txn_share_90d?: number;
  active_products_180d?: number;
  inflow_outflow_ratio_90d?: number;
  days_since_last_txn_pct?: number;
  digital_engagement_pct?: number;
  total_deposits_pct?: number;
  txn_count_90d_pct?: number;
  txn_amount_cv_90d_pct?: number;
  active_products_180d_pct?: number;
};

type AgentCPersonaMetrics = {
  avg_days_since_last_txn?: number | null;
  avg_mobile_share_90d?: number | null;
  avg_branch_share_90d?: number | null;
  avg_weekend_txn_share_90d?: number | null;
  avg_txn_count_90d?: number | null;
  avg_txn_amount_90d?: number | null;
  avg_txn_amount_cv_90d?: number | null;
  avg_active_products_180d?: number | null;
  avg_inflow_outflow_ratio_90d?: number | null;
};

type ChurnCohortCustomerRow = {
  customer_id: string;
  customer_name: string;
  churn_risk_score: number;
  churn_risk_category: string;
  churn_risk_reason?: string;
  reason?: string;
  persona?: string;
  recommended_retention_action?: string;
  suggested_retention_offer?: string;
  retention_strategy?: string;
  customer_metrics?: AgentCCustomerMetrics;
};

function ChurnCohortCustomerTable({
  rows,
  title,
  description,
  headerClassName,
  getReasonText,
  onGetOffer,
}: {
  rows: ChurnCohortCustomerRow[];
  title: string;
  description: string;
  headerClassName: string;
  getReasonText: (c: ChurnCohortCustomerRow) => string;
  onGetOffer: (customerId: string) => void;
}) {
  if (rows.length === 0) return null;
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden mb-6 last:mb-0">
      <div className={`px-4 py-3 border-b border-slate-100 ${headerClassName}`}>
        <h3 className="text-sm font-bold text-slate-900">{title}</h3>
        <p className="text-xs text-slate-600 mt-0.5">{description}</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[960px]">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="text-left py-3 px-4 font-semibold text-slate-700">Customer</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-700">Segment</th>
              <th className="text-right py-3 px-4 font-semibold text-slate-700">Risk score</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-700 min-w-[200px] max-w-md">Reason</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-700 min-w-[220px] max-w-lg">
                Retention strategy
              </th>
              <th className="text-left py-3 px-4 font-semibold text-slate-700">Suggested action</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-700">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr
                key={`${c.customer_id}-${c.churn_risk_category}`}
                className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors"
              >
                <td className="py-3 px-4">
                  <p className="font-medium text-slate-900">{c.customer_name}</p>
                  <p className="text-slate-500 text-xs">{c.customer_id}</p>
                </td>
                <td className="py-3 px-4 text-slate-600">{c.persona ?? ' - '}</td>
                <td className="py-3 px-4 text-right">
                  <span
                    className={`font-semibold ${
                      c.churn_risk_category === 'Critical'
                        ? 'text-red-600'
                        : c.churn_risk_category === 'High'
                        ? 'text-amber-600'
                        : c.churn_risk_category === 'Low'
                        ? 'text-emerald-600'
                        : 'text-slate-600'
                    }`}
                  >
                    {c.churn_risk_score?.toFixed(0) ?? ' - '}
                  </span>
                  <span className="text-slate-400 ml-1 text-xs">{c.churn_risk_category}</span>
                </td>
                <td className="py-3 px-4 text-slate-600 align-top max-w-md">
                  <CollapsibleChurnText text={getReasonText(c)} collapseThreshold={52} />
                </td>
                <td className="py-3 px-4 text-slate-600 align-top max-w-lg">
                  <CollapsibleChurnText
                    text={formatRetentionStrategy(c.retention_strategy?.trim() || '') || ''}
                    collapseThreshold={120}
                  />
                  {c.customer_metrics && (
                    <p className="mt-2 text-[11px] text-slate-500">
                      90d txns {c.customer_metrics.txn_count_90d ?? ' - '} | mobile {pct(c.customer_metrics.mobile_share_90d)} |
                      active products {c.customer_metrics.active_products_180d ?? ' - '}
                    </p>
                  )}
                </td>
                <td className="py-3 px-4 text-slate-600 text-xs">
                  {c.recommended_retention_action?.replace(/_/g, ' ') ?? ' - '}
                </td>
                <td className="py-3 px-4">
                  <button
                    type="button"
                    onClick={() => onGetOffer(c.customer_id)}
                    className="inline-flex items-center gap-1 text-violet-600 font-medium hover:text-violet-700"
                  >
                    Get offer
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Offer Intelligence types ──────────────────────────────────────────────────

type OfferScoreCalcDetail = {
  inputs: Record<string, string | number | boolean>;
  formula: string;
  steps: string[];
};

type OfferScoreBreakdownFactor = {
  score: number;
  weight: number;
  explanation: string;
  calculation?: OfferScoreCalcDetail;
};

type ExperimentVariant = {
  variant_id: string;
  offer_id: string;
  offer_name: string;
  offer_type: string;
  channel: string;
  n_exposed: number;
  n_converted: number;
  conversion_rate: number;
  lift_abs: number;
  lift_pct: number;
  z_stat: number;
  p_value: number;
  is_significant: boolean;
};

type ExperimentData = {
  experiment_id: string;
  holdout_conversion_rate: number;
  winning_conversion_rate?: number;
  lift_abs?: number;
  lift_pct?: number;
  p_value?: number;
  z_stat?: number;
  no_offer_recommended: boolean;
  winning_variant_id?: string | null;
  all_variants: ExperimentVariant[];
};

type OfferIntelligenceSection = {
  available: boolean;
  reason?: string;
  selected_offer?: {
    offer_id: string;
    offer_type: string;
    offer_name: string;
    headline_value: string;
    terms_summary: string;
    value_amount?: number;
    value_currency?: string;
    content_hero_stat?: string;
    content_how_to_earn?: string;
    content_benefit_1?: string;
    content_benefit_2?: string;
    content_benefit_3?: string;
    preferred_channel?: string;
    is_evergreen?: boolean;
    offer_end_date?: string | null;
    days_remaining?: number | null;
  };
  offer_score?: number;
  offer_score_breakdown?: Record<string, OfferScoreBreakdownFactor>;
  runner_up_offers?: Array<{
    offer_id?: string;
    offer_name?: string;
    offer_score?: number;
    reason_not_selected?: string;
    is_significant?: boolean;
  }>;
  secondary_offer?: {
    offer_id?: string;
    offer_type?: string;
    offer_name?: string;
    headline_value?: string;
    offer_score?: number;
    content_hero_stat?: string;
  } | null;
  offers_considered?: number;
  offers_blocked_by_eligibility?: number;
  // Experiment-driven path
  selection_method?: 'experiment_lift' | 'formula_score';
  experiment_data?: ExperimentData;
  channel_attribution?: Record<string, number>;
  persona_match?: 'exact' | 'cross_persona';
  // Why this offer was chosen for this customer
  persona_offer_reason?: string;
};

type PersonalizedCommunication = {
  offer_id?: string;
  product_name?: string;
  persona_name?: string;
  recommended_format?: 'push_notification' | 'email_content' | 'flyer_content';
  financial_goal_hint?: string;
  flyer_content?: { headline: string; body: string };
  email_content?: { subject: string; body: string };
  push_notification?: string;
  sms_text?: string;
  generation_source?: 'llm' | 'template';
};

/** API payload from GET /api/banking/agent_c/one-best-offer/:id */
type OneBestOfferPayload = {
  offer?: {
    product_id?: string;
    product_name?: string;
    category?: string;
    subcategory?: string;
    supervisor_pinned?: boolean;
    priority_pin_reason?: string;
  };
  supervisor_pinned?: boolean;
  score?: number;
  reason?: string;
  persona?: string;
  churn_risk_score?: number | null;
  churn_category?: string;
  churn_risk_reason?: string;
  retention_strategy?: string;
  suggested_retention_offer?: string;
  recommended_retention_action?: string;
  customer_metrics?: AgentCCustomerMetrics;
  best_channel?: string;
  best_channel_reason?: string;
  channels?: Array<{ channel: string; priority?: number; label?: string }>;
  explainability?: { why_this_offer?: string; why_our_ai?: string };
  agent_b_top_products?: Array<{ product_id?: string; product_name?: string; score?: number }>;
  agent_c_vs_agent_b?: {
    recommendations_differ: boolean;
    explanation?: string | null;
    explanation_source?: 'llm' | 'template' | null;
  };
  // Offer Intelligence (new)
  offer_intelligence?: OfferIntelligenceSection;
  personalized_communication?: PersonalizedCommunication | null;
  // Agentic Analysis (LLM deep-dive across all 52+ customer signals)
  customer_analysis?: {
    customer_insight_summary?: string;
    product_fit_rationale?: string;
    channel_rationale?: string;
    personalized_pitch?: string;
    urgency_signal?: string;
  } | null;
  // Credit Personalization
  credit_personalization?: {
    product_type?: string;
    pre_approval_tier?: string;
    credit_tier?: string;
    approval_confidence?: string;
    personalized_apr?: number;
    personalized_rate?: number;
    projected_annual_rewards_value?: number;
    annual_fee?: number;
    net_annual_value?: number;
    balance_transfer_savings?: number | null;
    intro_apr_months?: number;
    personalized_pitch?: string;
    estimated_monthly_payment?: number;
    max_loan_amount?: number;
    estimated_monthly_savings?: number;
  } | null;
  // Provenance: did Agent C anchor on Agent B's product?
  selected_from_agent_b?: boolean;
  agent_b_product_rank?: number | null;
};

type PersonaBestOfferPayload = OneBestOfferPayload & {
  persona_name?: string;
  segment_size?: number;
  representative_customer_id?: string;
  representative_customer_name?: string;
  note?: string;
  channel_distribution?: Record<string, number>;
  segment_churn?: {
    segment_size: number;
    at_risk_high_critical_count: number;
    high_count: number;
    critical_count: number;
    avg_churn_score_segment: number;
    avg_churn_score_at_risk: number | null;
    top_retention_action: string;
  };
  segment_churn_summary?: string;
};

// ── Offer type metadata ───────────────────────────────────────────────────────

const OFFER_TYPE_CONFIG: Record<string, { label: string; color: string; bgColor: string }> = {
  signup_bonus:          { label: 'Sign-up Bonus',    color: 'text-amber-700',   bgColor: 'bg-amber-50 border-amber-200' },
  intro_apr:             { label: '0% Intro APR',     color: 'text-purple-700',  bgColor: 'bg-purple-50 border-purple-200' },
  cashback_boost:        { label: 'Cashback Boost',   color: 'text-emerald-700', bgColor: 'bg-emerald-50 border-emerald-200' },
  fee_waiver:            { label: 'Fee Waiver',       color: 'text-blue-700',    bgColor: 'bg-blue-50 border-blue-200' },
  cd_rate_bump:          { label: 'Rate Bump',        color: 'text-teal-700',    bgColor: 'bg-teal-50 border-teal-200' },
  rate_discount:         { label: 'Rate Discount',    color: 'text-sky-700',     bgColor: 'bg-sky-50 border-sky-200' },
  loyalty_reward:        { label: 'Loyalty Reward',   color: 'text-rose-700',    bgColor: 'bg-rose-50 border-rose-200' },
  referral_bonus:        { label: 'Referral Bonus',   color: 'text-violet-700',  bgColor: 'bg-violet-50 border-violet-200' },
  balance_transfer_promo:{ label: 'Balance Transfer', color: 'text-orange-700',  bgColor: 'bg-orange-50 border-orange-200' },
};

const SUBCATEGORY_GRADIENT: Record<string, string> = {
  Credit:       'from-violet-600 to-purple-700',
  Savings:      'from-emerald-600 to-teal-700',
  CD:           'from-amber-600 to-orange-700',
  Mortgage:     'from-blue-600 to-indigo-700',
  'Home Equity':'from-blue-600 to-cyan-700',
  HELOC:        'from-cyan-600 to-blue-700',
  Investment:   'from-indigo-600 to-violet-700',
  Checking:     'from-slate-600 to-slate-700',
  'Auto':       'from-red-600 to-rose-700',
  'Personal Loan': 'from-orange-600 to-red-700',
};

function getSubcategoryGradient(subcategory?: string): string {
  if (!subcategory) return 'from-slate-600 to-slate-700';
  return SUBCATEGORY_GRADIENT[subcategory] ?? 'from-indigo-600 to-violet-700';
}

// ── Offer type hero gradient config ──────────────────────────────────────────
const OFFER_HERO_CONFIG: Record<string, { gradient: string; accent: string; iconBg: string }> = {
  signup_bonus:           { gradient: 'from-amber-500 via-orange-500 to-red-500',    accent: 'text-amber-100',  iconBg: 'bg-amber-400/30' },
  cashback_boost:         { gradient: 'from-emerald-500 via-teal-500 to-cyan-600',   accent: 'text-emerald-100',iconBg: 'bg-emerald-400/30' },
  intro_rate_boost:       { gradient: 'from-blue-500 via-indigo-500 to-violet-600',  accent: 'text-blue-100',   iconBg: 'bg-blue-400/30' },
  fee_waiver:             { gradient: 'from-violet-500 via-purple-500 to-indigo-600',accent: 'text-violet-100', iconBg: 'bg-violet-400/30' },
  rate_discount:          { gradient: 'from-sky-500 via-cyan-500 to-teal-600',       accent: 'text-sky-100',    iconBg: 'bg-sky-400/30' },
  rate_boost:             { gradient: 'from-teal-500 via-emerald-500 to-green-600',  accent: 'text-teal-100',   iconBg: 'bg-teal-400/30' },
  rate_bump:              { gradient: 'from-teal-500 via-emerald-500 to-green-600',  accent: 'text-teal-100',   iconBg: 'bg-teal-400/30' },
  rate_lock:              { gradient: 'from-slate-600 via-slate-700 to-gray-800',    accent: 'text-slate-200',  iconBg: 'bg-slate-400/30' },
  loyalty_reward:         { gradient: 'from-rose-500 via-pink-500 to-fuchsia-600',   accent: 'text-rose-100',   iconBg: 'bg-rose-400/30' },
  balance_transfer_promo: { gradient: 'from-orange-500 via-amber-500 to-yellow-500', accent: 'text-orange-100', iconBg: 'bg-orange-400/30' },
};

function getOfferHeroConfig(offerType?: string) {
  return OFFER_HERO_CONFIG[offerType ?? ''] ?? { gradient: 'from-indigo-600 via-violet-600 to-purple-700', accent: 'text-indigo-100', iconBg: 'bg-indigo-400/30' };
}

// ── Channel metadata ─────────────────────────────────────────────────────────

const CHANNEL_META: Record<string, { label: string; color: string; bg: string; border: string; activeBg: string }> = {
  in_app:        { label: 'In-App Notification', color: 'text-violet-700', bg: 'bg-violet-100', border: 'border-violet-200', activeBg: 'bg-violet-50' },
  email:         { label: 'Email',               color: 'text-blue-700',   bg: 'bg-blue-100',   border: 'border-blue-200',   activeBg: 'bg-blue-50' },
  branch:        { label: 'Branch Visit',         color: 'text-amber-700',  bg: 'bg-amber-100',  border: 'border-amber-200',  activeBg: 'bg-amber-50' },
  direct_mail:   { label: 'Direct Mail',         color: 'text-teal-700',   bg: 'bg-teal-100',   border: 'border-teal-200',   activeBg: 'bg-teal-50' },
  web:           { label: 'Web',                 color: 'text-sky-700',    bg: 'bg-sky-100',    border: 'border-sky-200',    activeBg: 'bg-sky-50' },
  outbound_call: { label: 'Outbound Call',       color: 'text-red-700',    bg: 'bg-red-100',    border: 'border-red-200',    activeBg: 'bg-red-50' },
};

const channelIconsMd: Record<string, React.ReactNode> = {
  email:         <Mail className="w-5 h-5" />,
  web:           <Globe className="w-5 h-5" />,
  in_app:        <Smartphone className="w-5 h-5" />,
  branch:        <Building2 className="w-5 h-5" />,
  direct_mail:   <Mail className="w-5 h-5" />,
  outbound_call: <Smartphone className="w-5 h-5" />,
};

function ChannelDeliveryCard({
  bestChannel,
  channels,
  channelFatigue,
}: {
  bestChannel: string;
  bestChannelReason?: string;
  channels: Array<{ channel: string; priority?: number; label?: string; is_fatigued?: boolean }>;
  offerPreferredChannel?: string;
  customerChannelPref?: string;
  channelFatigue?: Record<string, { is_fatigued: boolean; sent?: number; consecutive_no_open?: number }>;
}) {
  const meta = CHANNEL_META[bestChannel] ?? {
    label: (bestChannel ?? '').replace(/_/g, ' '),
    color: 'text-slate-700', bg: 'bg-slate-100', border: 'border-slate-200', activeBg: 'bg-slate-50',
  };
  const bestFatigued = channelFatigue?.[bestChannel]?.is_fatigued === true;

  // All channels sorted: non-fatigued first
  const sorted = [...channels].sort((a, b) => {
    const aF = channelFatigue?.[a.channel]?.is_fatigued === true || (a as Record<string, unknown>).is_fatigued === true;
    const bF = channelFatigue?.[b.channel]?.is_fatigued === true || (b as Record<string, unknown>).is_fatigued === true;
    return (aF ? 1 : 0) - (bF ? 1 : 0);
  });

  return (
    <div className={`rounded-2xl border ${bestFatigued ? 'border-amber-200 bg-amber-50/30' : `${meta.border} ${meta.activeBg}`} flex items-center gap-3 px-4 py-3`}>
      {/* Channel icon */}
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border ${bestFatigued ? 'bg-amber-100 border-amber-300' : `${meta.bg} ${meta.border}`}`}>
        <span className={bestFatigued ? 'text-amber-600' : meta.color}>{channelIconsMd[bestChannel] ?? <Mail className="w-5 h-5" />}</span>
      </div>

      {/* Channel name + label */}
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-black leading-none ${bestFatigued ? 'text-amber-700' : meta.color}`}>{meta.label}</p>
        <p className="text-[10px] text-slate-400 mt-0.5">AI recommended channel</p>
      </div>

      {/* Status badges */}
      <div className="flex items-center gap-1.5 shrink-0">
        {bestFatigued ? (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-amber-100 border border-amber-300 text-[9px] font-bold text-amber-700">
            <AlertTriangle className="w-2.5 h-2.5" /> FATIGUED
          </span>
        ) : (
          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg ${meta.bg} border ${meta.border} text-[9px] font-bold ${meta.color}`}>
            ★ BEST
          </span>
        )}
        {/* Secondary channels as small dots */}
        <div className="flex items-center gap-0.5 ml-1">
          {sorted.slice(1, 4).map(ch => {
            const isF = channelFatigue?.[ch.channel]?.is_fatigued === true || (ch as Record<string, unknown>).is_fatigued === true;
            const cm = CHANNEL_META[ch.channel];
            return (
              <span key={ch.channel} className={`w-5 h-5 rounded-full flex items-center justify-center border text-[8px] ${isF ? 'bg-amber-50 border-amber-200 text-amber-500' : `${cm?.bg ?? 'bg-slate-50'} ${cm?.border ?? 'border-slate-200'} ${cm?.color ?? 'text-slate-400'}`}`}
                title={`${cm?.label ?? ch.channel}${isF ? ' (fatigued)' : ''}`}>
                {channelIcons[ch.channel] ?? <Mail className="w-2.5 h-2.5" />}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Experiment Lift Panel ─────────────────────────────────────────────────────
// ── MTA Types ─────────────────────────────────────────────────────────────────

type MTAChannelFatigueEntry = {
  sent: number;
  opened: number;
  clicked: number;
  converted: number;
  is_fatigued: boolean;
  consecutive_no_open: number;
  open_rate: number;
  click_rate: number;
  last_sent: string | null;
};

type MTAPersonaChannelStat = {
  sent: number;
  opened: number;
  clicked: number;
  converted: number;
  open_rate: number;
  click_rate: number;
  conversion_rate: number;
  reach_pct: number;
  sample_size: number;
};

type MTAChannelRecommendation = {
  recommended_channel: string;
  signal_source: 'personal' | 'segment' | 'segment_fallback';
  confidence: 'high' | 'medium' | 'low';
  total_personal_sends: number;
  reason: string;
  personal_scores: Record<string, number>;
};

type MTAAiInsight = {
  headline: string;
  reason_lines: Array<{ type: string; text: string }>;
  suppressed_channels: string[];
  top_alternative: string | null;
  best_channel_pct: number;
  persona_conv_rate: number;
};

type MTAJourneyRow = {
  journey_id: string;
  channel: string;
  offer_id: string;
  product_id: string;
  timestamp: string;
  opened: boolean;
  clicked: boolean;
  converted: boolean;
  position: number;
};

// ── MTA constants ─────────────────────────────────────────────────────────────

// All channels the backend may return  -  must match utils/banking_constants.py CHANNELS
const MTA_CHANNELS = ['in_app', 'email', 'sms', 'direct_mail', 'branch', 'outbound_call', 'web'];
// Channels that have journey data in the MTA CSV (used for donut/attribution charts)
const MTA_JOURNEY_CHANNELS = ['in_app', 'email', 'sms', 'direct_mail', 'branch'];
const MTA_CHANNEL_LABELS: Record<string, string> = {
  in_app: 'In-App', email: 'Email', sms: 'SMS', direct_mail: 'Direct Mail',
  branch: 'Branch', outbound_call: 'Outbound Call', web: 'Web',
};
const MTA_CHANNEL_HEX: Record<string, string> = {
  in_app:        '#8b5cf6',
  email:         '#3b82f6',
  sms:           '#14b8a6',
  direct_mail:   '#f59e0b',
  branch:        '#10b981',
  outbound_call: '#f97316',
  web:           '#6366f1',
};
const MTA_CHANNEL_COLORS: Record<string, string> = {
  in_app:        'bg-violet-500',
  email:         'bg-blue-500',
  sms:           'bg-teal-500',
  direct_mail:   'bg-amber-500',
  branch:        'bg-emerald-600',
  outbound_call: 'bg-orange-500',
  web:           'bg-indigo-500',
};
const MTA_CHANNEL_ICONS: Record<string, React.ReactNode> = {
  in_app:        <Smartphone className="w-3.5 h-3.5" />,
  email:         <Mail className="w-3.5 h-3.5" />,
  sms:           <MessageCircle className="w-3.5 h-3.5" />,
  direct_mail:   <Mail className="w-3.5 h-3.5" />,
  branch:        <Building2 className="w-3.5 h-3.5" />,
  outbound_call: <Phone className="w-3.5 h-3.5" />,
  web:           <Globe className="w-3.5 h-3.5" />,
};
const MTA_PERSONAS = ['Digital Native', 'Wealth Builder', 'Everyday Essential', 'Retiree Anchor', 'At-Risk Saver'];

// ── DonutChart (pure SVG, no charting library) ───────────────────────────────
function DonutChart({
  data,
  size = 130,
  thickness = 22,
  centerLabel,
  centerSub,
}: {
  data: Array<{ key: string; value: number; color: string; fatigued?: boolean }>;
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerSub?: string;
}) {
  const cx = size / 2;
  const cy = size / 2;
  const r = (size - thickness) / 2;
  const circ = 2 * Math.PI * r;
  const total = data.reduce((s, d) => s + d.value, 0);
  if (total === 0) return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#e2e8f0" strokeWidth={thickness} />
      <text x={cx} y={cy + 4} textAnchor="middle" style={{ fontSize: 10, fill: '#94a3b8' }}>No data</text>
    </svg>
  );

  let cumFraction = 0;
  const gap = 0.012; // small gap between segments (fraction of circumference)

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Background track */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#f1f5f9" strokeWidth={thickness} />
      {data
        .filter(d => d.value > 0)
        .map(d => {
          const fraction = d.value / total;
          const segLen = Math.max(0, (fraction - gap) * circ);
          const rotation = -90 + cumFraction * 360;
          cumFraction += fraction;
          return (
            <circle
              key={d.key}
              cx={cx} cy={cy} r={r}
              fill="none"
              stroke={d.fatigued ? '#fbbf24' : d.color}
              strokeWidth={thickness - 2}
              strokeDasharray={`${segLen} ${circ - segLen}`}
              transform={`rotate(${rotation} ${cx} ${cy})`}
              strokeLinecap="round"
              opacity={d.fatigued ? 0.6 : 1}
            />
          );
        })}
      {/* Center text */}
      {centerLabel && (
        <text x={cx} y={cy + 4} textAnchor="middle"
          style={{ fontSize: 14, fontWeight: 800, fill: '#1e293b', letterSpacing: '-0.5px' }}>
          {centerLabel}
        </text>
      )}
      {centerSub && (
        <text x={cx} y={cy + 16} textAnchor="middle"
          style={{ fontSize: 8, fill: '#94a3b8' }}>
          {centerSub}
        </text>
      )}
    </svg>
  );
}

// ── MTAIntelligencePanel ──────────────────────────────────────────────────────

function MTAIntelligencePanel({
  mtaAttribution,
  channelFatigue,
  personaChannelStats,
  aiInsight,
  bestChannel,
  persona,
  customerId,
  experimentId,
  pValue,
  channelRecommendation,
}: {
  mtaAttribution?: Record<string, number>;
  channelFatigue?: Record<string, MTAChannelFatigueEntry>;
  personaChannelStats?: Record<string, MTAPersonaChannelStat>;
  aiInsight?: MTAAiInsight;
  bestChannel?: string;
  persona?: string;
  customerId?: string;
  experimentId?: string;
  pValue?: number;
  channelRecommendation?: MTAChannelRecommendation;
}) {
  const [activeTab, setActiveTab] = React.useState<'attribution' | 'journey' | 'insight'>('attribution');

  // ── Customer journey query ─────────────────────────────────────────────────
  const journeyQuery = useQuery({
    queryKey: ['mta-customer-journey', customerId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/mta/customer-journey/${customerId}?days=90`);
      const json = await res.json();
      return (json.data ?? []) as MTAJourneyRow[];
    },
    staleTime: 2 * 60 * 1000,
    enabled: activeTab === 'journey' && !!customerId,
  });

  const hasMTA = mtaAttribution && Object.keys(mtaAttribution).length > 0;
  if (!hasMTA && !channelFatigue && !aiInsight) return null;

  const tabs = [
    { key: 'attribution', label: 'Attribution', icon: <BarChart2 className="w-3.5 h-3.5" /> },
    { key: 'journey',     label: 'Journey',     icon: <GitBranch className="w-3.5 h-3.5" /> },
    { key: 'insight',     label: 'AI Insight',  icon: <Sparkles className="w-3.5 h-3.5" /> },
  ] as const;

  // Sorted attribution entries
  const sortedAttr = Object.entries(mtaAttribution ?? {})
    .filter(([, v]) => v > 0)
    .sort(([, a], [, b]) => b - a);
  const topChannel = sortedAttr[0]?.[0];

  return (
    <div className="rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Panel header */}
      <div className="bg-gradient-to-r from-indigo-700 to-violet-700 px-5 py-3.5 flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-white/15 flex items-center justify-center shrink-0">
          <BarChart2 className="w-4.5 h-4.5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-white font-bold text-sm">Multi-Touch Attribution</p>
          <p className="text-indigo-200 text-xs">Markov removal-effect channel intelligence</p>
        </div>
        {experimentId && (
          <span className="text-[10px] text-indigo-200 font-mono truncate max-w-[140px]">{experimentId}</span>
        )}
      </div>

      {/* ── Signal source pill ── */}
      {channelRecommendation && (
        <div className={`flex items-center gap-2 px-4 py-2 border-b text-[10px] font-semibold ${channelRecommendation.signal_source === 'personal' ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-blue-50 border-blue-200 text-blue-700'}`}>
          {channelRecommendation.signal_source === 'personal'
            ? <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            : <Info className="w-3.5 h-3.5 shrink-0" />}
          <span>{channelRecommendation.signal_source === 'personal' ? 'Personal engagement signal' : 'Segment Markov attribution'}</span>
          <span className="opacity-50">·</span>
          <span className="font-bold">{channelRecommendation.total_personal_sends} sends</span>
          <span className="opacity-50">·</span>
          <span className="uppercase tracking-wide">{channelRecommendation.confidence} confidence</span>
        </div>
      )}

      {/* Tab bar */}
      <div className="flex border-b border-slate-200 bg-slate-50/70 overflow-x-auto">
        {tabs.map(t => (
          <button
            key={t.key}
            type="button"
            onClick={() => setActiveTab(t.key as typeof activeTab)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold whitespace-nowrap transition-colors border-b-2 ${
              activeTab === t.key
                ? 'border-indigo-600 text-indigo-700 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      <div className="p-5">

        {/* ── Tab: Attribution ─────────────────────────────────────────────── */}
        {activeTab === 'attribution' && (
          <div className="space-y-3">
            {/* Markov badge + p-value */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-full px-3 py-1">
                <GitBranch className="w-3 h-3" />
                Markov Chain Attribution
              </span>
              {pValue != null && (
                <span className="text-[11px] text-slate-500 font-mono">
                  p = {pValue < 0.001 ? '<0.001' : pValue.toFixed(4)}
                </span>
              )}
            </div>

            {/* Scope clarifier  -  one-liner */}
            <p className="text-[10px] text-slate-400 leading-relaxed">
              <span className="font-semibold text-indigo-600">%</span> = segment-wide Markov share &nbsp;·&nbsp;
              <span className="font-semibold text-amber-600">Fatigued</span> = this customer's individual history
            </p>

            {/* ── Donut charts: Segment vs Customer ── */}
            <div className="grid grid-cols-2 gap-3">
              {/* Left: Segment Markov attribution */}
              <div className="rounded-xl border border-indigo-100 bg-gradient-to-b from-indigo-50/60 to-white p-3 flex flex-col items-center gap-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">Segment Attribution</p>
                <DonutChart
                  data={MTA_CHANNELS.map(ch => ({
                    key: ch,
                    value: Math.round((mtaAttribution?.[ch] ?? 0) * 1000),
                    color: MTA_CHANNEL_HEX[ch] ?? '#94a3b8',
                  }))}
                  size={130}
                  thickness={24}
                  centerLabel={`${Math.round((mtaAttribution?.[topChannel ?? ''] ?? 0) * 100)}%`}
                  centerSub={MTA_CHANNEL_LABELS[topChannel ?? ''] ?? ''}
                />
                <div className="w-full space-y-1 pt-1">
                  {[...MTA_CHANNELS]
                    .filter(ch => (mtaAttribution?.[ch] ?? 0) > 0.01)
                    .sort((a, b) => (mtaAttribution?.[b] ?? 0) - (mtaAttribution?.[a] ?? 0))
                    .map(ch => (
                      <div key={ch} className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: MTA_CHANNEL_HEX[ch] }} />
                        <span className="text-[9px] text-slate-600 flex-1 truncate">{MTA_CHANNEL_LABELS[ch]}</span>
                        <span className="text-[9px] font-bold text-slate-800">{Math.round((mtaAttribution?.[ch] ?? 0) * 100)}%</span>
                      </div>
                    ))}
                </div>
                <p className="text-[8px] text-slate-400 text-center">Markov removal effect across<br/>all {persona ?? 'segment'} journeys</p>
              </div>

              {/* Right: This customer's channel activity */}
              <div className="rounded-xl border border-slate-100 bg-gradient-to-b from-slate-50/60 to-white p-3 flex flex-col items-center gap-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-600">Your Channel Activity</p>
                {(() => {
                  const totalSent = MTA_CHANNELS.reduce((s, ch) => s + (channelFatigue?.[ch]?.sent ?? 0), 0);
                  const custData = MTA_CHANNELS.map(ch => ({
                    key: ch,
                    value: channelFatigue?.[ch]?.sent ?? 0,
                    color: MTA_CHANNEL_HEX[ch] ?? '#94a3b8',
                    fatigued: channelFatigue?.[ch]?.is_fatigued === true,
                  }));
                  return (
                    <>
                      <DonutChart
                        data={custData}
                        size={130}
                        thickness={24}
                        centerLabel={totalSent > 0 ? String(totalSent) : ' - '}
                        centerSub={totalSent > 0 ? 'total sends' : 'no history'}
                      />
                      <div className="w-full space-y-1 pt-1">
                        {MTA_CHANNELS
                          .filter(ch => (channelFatigue?.[ch]?.sent ?? 0) > 0)
                          .sort((a, b) => (channelFatigue?.[b]?.sent ?? 0) - (channelFatigue?.[a]?.sent ?? 0))
                          .map(ch => {
                            const f = channelFatigue![ch];
                            const isF = f.is_fatigued === true;
                            const openRate = Math.round((f.open_rate ?? 0) * 100);
                            return (
                              <div key={ch} className="flex items-center gap-1.5">
                                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: isF ? '#fbbf24' : (MTA_CHANNEL_HEX[ch] ?? '#94a3b8') }} />
                                <span className={`text-[9px] flex-1 truncate ${isF ? 'text-amber-700 line-through' : 'text-slate-600'}`}>
                                  {MTA_CHANNEL_LABELS[ch]}
                                </span>
                                <span className="text-[9px] font-bold text-slate-700">{f.sent}s/{openRate}%</span>
                              </div>
                            );
                          })}
                        {totalSent === 0 && (
                          <p className="text-[9px] text-slate-400 text-center pt-1">No sends recorded yet</p>
                        )}
                      </div>
                      <p className="text-[8px] text-slate-400 text-center">Sends · Open rate per channel<br/>{(channelFatigue && Object.values(channelFatigue).some(f => f.is_fatigued === true)) ? '🟡 = fatigued (suppressed)' : 'No channels suppressed'}</p>
                    </>
                  );
                })()}
              </div>
            </div>

            {/* Attribution bars  -  sorted high to low */}
            <div className="space-y-2">
              {[...MTA_CHANNELS]
                .sort((a, b) => (mtaAttribution?.[b] ?? 0) - (mtaAttribution?.[a] ?? 0))
                .map(ch => {
                  const pct = Math.round((mtaAttribution?.[ch] ?? 0) * 100);
                  const fatigue = channelFatigue?.[ch];
                  // Strict boolean check  -  avoids React rendering `{0}` as "0"
                  const isFatigued = fatigue?.is_fatigued === true;
                  const isTop = ch === topChannel;
                  const isRecommended = ch === bestChannel;
                  const pStats = personaChannelStats?.[ch];
                  const convPct = pStats ? +(((pStats.conversion_rate ?? 0) * 100).toFixed(1)) : 0;

                  return (
                    <div
                      key={ch}
                      className={`rounded-xl overflow-hidden border transition-all ${
                        isFatigued
                          ? 'border-amber-200 bg-gradient-to-r from-amber-50/80 to-white'
                          : isRecommended
                          ? 'border-blue-200 bg-gradient-to-r from-blue-50/50 to-white shadow-sm'
                          : 'border-slate-100 bg-white'
                      }`}
                    >
                      {/* Top row: icon + label + badges + pct */}
                      <div className="flex items-center gap-2 px-3 pt-3 pb-1.5">
                        <span className={`flex-shrink-0 ${isFatigued ? 'text-amber-500 opacity-60' : isRecommended ? 'text-blue-600' : 'text-slate-400'}`}>
                          {MTA_CHANNEL_ICONS[ch]}
                        </span>
                        <span className={`text-xs font-bold ${isFatigued ? 'text-amber-800 line-through decoration-amber-400 decoration-2' : isRecommended ? 'text-blue-900' : 'text-slate-700'}`}>
                          {MTA_CHANNEL_LABELS[ch]}
                        </span>
                        {ch === bestChannel && !isFatigued && (
                          <span className="text-[10px] font-bold text-blue-700 bg-blue-100 border border-blue-200 px-1.5 py-0.5 rounded-full">
                            ★ RECOMMENDED
                          </span>
                        )}
                        {ch === bestChannel && isFatigued && (
                          <span className="text-[10px] font-bold text-amber-700 bg-amber-100 border border-amber-300 px-1.5 py-0.5 rounded-full inline-flex items-center gap-0.5">
                            <AlertTriangle className="w-2.5 h-2.5" /> RECOMMENDED · FATIGUED
                          </span>
                        )}
                        {ch !== bestChannel && isTop && !isFatigued && (
                          <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 border border-indigo-200 px-1.5 py-0.5 rounded-full">
                            TOP MARKOV
                          </span>
                        )}
                        {ch !== bestChannel && isFatigued && (
                          <span className="text-[10px] font-bold text-amber-700 bg-amber-100 border border-amber-300 px-1.5 py-0.5 rounded-full inline-flex items-center gap-0.5">
                            <AlertTriangle className="w-2.5 h-2.5" /> FATIGUED
                          </span>
                        )}
                        <span className={`ml-auto text-sm font-black ${isFatigued ? 'text-amber-700 opacity-70' : isRecommended ? 'text-blue-700' : 'text-slate-600'}`}>
                          {pct}%
                        </span>
                      </div>

                      {/* Progress bar  -  striped when suppressed */}
                      <div className="px-3 pb-2">
                        <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                          {isFatigued ? (
                            <div
                              className="h-full rounded-full opacity-50"
                              style={{
                                width: `${pct}%`,
                                background: 'repeating-linear-gradient(135deg,#f59e0b 0px,#f59e0b 4px,#fde68a 4px,#fde68a 8px)',
                              }}
                            />
                          ) : (
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${MTA_CHANNEL_COLORS[ch] ?? 'bg-slate-400'}`}
                              style={{ width: `${pct}%` }}
                            />
                          )}
                        </div>
                      </div>

                      {/* Stats row */}
                      <div className="px-3 pb-2.5 flex items-start justify-between gap-2">
                        <div className="space-y-0.5">
                          {fatigue && fatigue.sent > 0 && (
                            <span className={`text-[10px] ${isFatigued ? 'text-amber-700 font-medium' : 'text-slate-400'}`}>
                              {fatigue.sent} sends · {fatigue.opened} opens · {Math.round((fatigue.open_rate ?? 0) * 100)}% open rate
                            </span>
                          )}
                        </div>
                        {convPct > 0 && (
                          <span className="text-[10px] text-slate-400 whitespace-nowrap flex-shrink-0">
                            Segment conv {convPct}%
                          </span>
                        )}
                      </div>

                      {/* Fatigued dual-signal callout */}
                      {isFatigued && (
                        <div className="mx-3 mb-3 rounded-lg border border-amber-300 bg-amber-100 px-3 py-2 flex items-start gap-2">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
                          <div className="text-[10px] text-amber-800 leading-relaxed">
                            <span className="font-semibold">Segment says {pct}%</span>  -  {MTA_CHANNEL_LABELS[ch]} is strong for {persona ?? 'this segment'} overall.
                            <span className="mx-1 text-amber-400">|</span>
                            <span className="font-semibold">This customer: suppressed</span>  -  {fatigue?.sent ?? 0} sends, {fatigue?.opened ?? 0} opens. Not reaching them via this channel.
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
            </div>

            <p className="text-[10px] text-slate-400 text-center pt-1">
              Removal-effect Markov attribution · {MTA_JOURNEY_CHANNELS.length} channels
            </p>

            {/* ── Why recommended ≠ top attribution ── */}
            {bestChannel && topChannel && bestChannel !== topChannel && (() => {
              const topPct  = Math.round((mtaAttribution?.[topChannel]  ?? 0) * 100);
              const bestPct = Math.round((mtaAttribution?.[bestChannel] ?? 0) * 100);
              const topLabel  = MTA_CHANNEL_LABELS[topChannel]  ?? topChannel;
              const bestLabel = MTA_CHANNEL_LABELS[bestChannel] ?? bestChannel;
              const suppressed = Object.entries(channelFatigue ?? {})
                .filter(([, f]) => f.is_fatigued)
                .map(([ch]) => MTA_CHANNEL_LABELS[ch] ?? ch);
              return (
                <div className="rounded-xl border border-violet-200 bg-violet-50 p-3.5 space-y-2.5 mt-1">
                  <div className="flex items-start gap-2">
                    <Info className="w-3.5 h-3.5 text-violet-600 flex-shrink-0 mt-0.5" />
                    <p className="text-[11px] font-bold text-violet-800">
                      Why {bestLabel} ({bestPct}%) is recommended over {topLabel} ({topPct}%)
                    </p>
                  </div>

                  <div className="space-y-2 pl-5">
                    {/* Row 1  -  what Markov % actually measures */}
                    <div className="flex gap-2 items-start">
                      <span className="text-[10px] font-bold text-violet-600 shrink-0 mt-0.5">①</span>
                      <p className="text-[10px] text-violet-700 leading-relaxed">
                        <span className="font-semibold">Markov % = historical credit, not reach probability.</span>{' '}
                        {topLabel} gets {topPct}% because it was used in many past journeys across this segment and removing it causes a large drop in conversion probability.
                        It does not mean {topLabel} is the best channel to send next for every customer in that segment.
                      </p>
                    </div>

                    {/* Row 2  -  persona reach reality */}
                    <div className="flex gap-2 items-start">
                      <span className="text-[10px] font-bold text-violet-600 shrink-0 mt-0.5">②</span>
                      <p className="text-[10px] text-violet-700 leading-relaxed">
                        <span className="font-semibold">Persona reach matters more than attribution rank.</span>{' '}
                        For the <span className="font-semibold">{persona ?? 'this'}</span> persona, {topLabel} has a low reach probability  - 
                        most customers in this segment won't open or engage with it.
                        High attribution for {topLabel} is partly because other personas (e.g. Digital Native) dominate that channel's journey data, inflating its segment-wide score.
                      </p>
                    </div>

                    {/* Row 3  -  suppressed channels */}
                    {suppressed.length > 0 && (
                      <div className="flex gap-2 items-start">
                        <span className="text-[10px] font-bold text-amber-600 shrink-0 mt-0.5">③</span>
                        <p className="text-[10px] text-amber-800 leading-relaxed">
                          <span className="font-semibold">{suppressed.join(', ')} suppressed due to fatigue</span>  -  too many sends with low engagement.
                          The system removed {suppressed.length > 1 ? 'these channels' : 'this channel'} from contention even if {suppressed.length > 1 ? 'their' : 'its'} attribution score would otherwise qualify.
                        </p>
                      </div>
                    )}

                    {/* Row 4  -  final decision logic */}
                    <div className="flex gap-2 items-start">
                      <span className="text-[10px] font-bold text-violet-600 shrink-0 mt-0.5">{suppressed.length > 0 ? '④' : '③'}</span>
                      <p className="text-[10px] text-violet-700 leading-relaxed">
                        <span className="font-semibold">Final pick = best non-fatigued channel aligned to persona preference.</span>{' '}
                        {bestLabel} is the channel this persona is most likely to respond to in person.
                        Its {bestPct}% attribution reflects fewer historical touchpoints in the data  -  not lower effectiveness when used.
                      </p>
                    </div>
                  </div>
                </div>
              );
            })()}

          </div>
        )}

        {/* ── Tab: Journey ─────────────────────────────────────────────────── */}
        {activeTab === 'journey' && (
          <div className="space-y-3">
            {journeyQuery.isLoading && (
              <div className="flex items-center gap-2 text-slate-400 text-xs py-6 justify-center">
                <Loader2 className="w-4 h-4 animate-spin" /> Loading journey…
              </div>
            )}
            {journeyQuery.data && journeyQuery.data.length === 0 && (
              <div className="text-center py-8">
                <GitBranch className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-sm text-slate-400">No touchpoints in last 90 days</p>
                <p className="text-[10px] text-slate-400 mt-1">Recommendation based on {persona ?? 'segment'} Markov data</p>
              </div>
            )}
            {journeyQuery.data && journeyQuery.data.length > 0 && (() => {
              const journeyMap: Record<string, MTAJourneyRow[]> = {};
              journeyQuery.data.forEach(r => {
                if (!journeyMap[r.journey_id]) journeyMap[r.journey_id] = [];
                journeyMap[r.journey_id].push(r);
              });
              const journeyIds = Object.keys(journeyMap).slice(0, 6);
              const total = journeyQuery.data.length;
              const opened = journeyQuery.data.filter(r => r.opened).length;
              const clicked = journeyQuery.data.filter(r => r.clicked).length;
              const converted = journeyQuery.data.filter(r => r.converted).length;

              const numJourneys = Object.keys(journeyMap).length;
              const convJourneys = Object.values(journeyMap).filter(rows => rows.some(r => r.converted)).length;
              const summary = converted > 0
                ? `Contacted ${total} time${total !== 1 ? 's' : ''} across ${numJourneys} campaign${numJourneys !== 1 ? 's' : ''}  -  ${convJourneys} resulted in a conversion.`
                : `Contacted ${total} time${total !== 1 ? 's' : ''} across ${numJourneys} campaign${numJourneys !== 1 ? 's' : ''}  -  no conversions yet.`;

              return (
                <div className="space-y-3">
                  {/* Narrative summary */}
                  <p className="text-[11px] text-slate-600 leading-relaxed bg-slate-50 border border-slate-200 rounded-xl px-3 py-2">
                    {summary}
                  </p>

                  {/* Funnel strip */}
                  <div className="grid grid-cols-4 gap-2">
                    {[
                      { label: 'Touches',   v: total,     pct: null,                             bg: 'bg-slate-50 border-slate-200',   txt: 'text-slate-700' },
                      { label: 'Opened',    v: opened,    pct: total ? Math.round(opened/total*100) : 0,  bg: 'bg-blue-50 border-blue-200',     txt: 'text-blue-700'  },
                      { label: 'Clicked',   v: clicked,   pct: total ? Math.round(clicked/total*100) : 0, bg: 'bg-indigo-50 border-indigo-200', txt: 'text-indigo-700'},
                      { label: 'Converted', v: converted, pct: total ? Math.round(converted/total*100) : 0, bg: converted > 0 ? 'bg-emerald-50 border-emerald-200' : 'bg-slate-50 border-slate-200', txt: converted > 0 ? 'text-emerald-700' : 'text-slate-400' },
                    ].map(s => (
                      <div key={s.label} className={`rounded-xl border ${s.bg} p-2.5 text-center`}>
                        <p className={`text-xl font-black leading-none ${s.txt}`}>{s.v}</p>
                        {s.pct !== null && <p className={`text-[9px] font-bold mt-0.5 ${s.txt} opacity-70`}>{s.pct}%</p>}
                        <p className="text-[8px] uppercase tracking-wide text-slate-400 mt-0.5">{s.label}</p>
                      </div>
                    ))}
                  </div>

                  {/* Legend */}
                  <div className="flex items-center gap-3 text-[9px] text-slate-400 flex-wrap">
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-200 border border-blue-400 inline-block" /> Opened</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-indigo-200 border border-indigo-400 inline-block" /> Clicked</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-emerald-200 border border-emerald-500 inline-block" /> Converted</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-slate-100 border border-slate-300 inline-block" /> Seen only</span>
                  </div>

                  {/* Journey cards */}
                  {journeyIds.map((jid, jidx) => {
                    const rows = journeyMap[jid].sort((a, b) => a.position - b.position);
                    const didConvert = rows.some(r => r.converted);
                    const dateRange = rows.length > 0
                      ? `${rows[0].timestamp.slice(5,10)}${rows.length > 1 ? ' → ' + rows[rows.length-1].timestamp.slice(5,10) : ''}`
                      : '';
                    const channelPath = rows.map(r => MTA_CHANNEL_LABELS[r.channel] ?? r.channel).join(' › ');
                    return (
                      <div key={jid} className={`rounded-xl border overflow-hidden ${didConvert ? 'border-emerald-200' : 'border-slate-200'}`}>
                        {/* Card header */}
                        <div className={`flex items-start gap-2.5 px-3 py-2 border-b ${didConvert ? 'bg-emerald-50 border-emerald-200' : 'bg-slate-50 border-slate-200'}`}>
                          <span className={`w-5 h-5 rounded-full text-[9px] font-black flex items-center justify-center shrink-0 mt-0.5 ${didConvert ? 'bg-emerald-500 text-white' : 'bg-slate-200 text-slate-600'}`}>{jidx + 1}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className={`text-[11px] font-bold ${didConvert ? 'text-emerald-800' : 'text-slate-700'}`}>Campaign {jidx + 1}</span>
                              {didConvert
                                ? <span className="text-[9px] font-bold text-emerald-600 bg-emerald-100 px-1.5 py-0.5 rounded-full">✓ Converted</span>
                                : <span className="text-[9px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded-full">No conversion</span>}
                            </div>
                            <p className="text-[9px] text-slate-400 mt-0.5 truncate">{channelPath}</p>
                          </div>
                          <span className="text-[9px] text-slate-400 shrink-0">{dateRange} · {rows.length} touch{rows.length !== 1 ? 'es' : ''}</span>
                        </div>

                        {/* Timeline */}
                        <div className="px-3 py-3 bg-white overflow-x-auto">
                          <div className="flex items-start min-w-max gap-0">
                            {rows.map((r, idx) => {
                              const statusColor = r.converted ? 'bg-emerald-100 border-emerald-400 text-emerald-600'
                                : r.clicked ? 'bg-indigo-100 border-indigo-400 text-indigo-600'
                                : r.opened  ? 'bg-blue-100 border-blue-400 text-blue-600'
                                : 'bg-slate-100 border-slate-300 text-slate-400';
                              const statusLabel = r.converted ? 'Converted' : r.clicked ? 'Clicked' : r.opened ? 'Opened' : 'Seen';
                              return (
                                <React.Fragment key={idx}>
                                  <div className="flex flex-col items-center gap-1 w-14">
                                    <div className={`w-9 h-9 rounded-full border-2 flex items-center justify-center ${statusColor}`}>
                                      {MTA_CHANNEL_ICONS[r.channel] ?? <Mail className="w-3.5 h-3.5" />}
                                    </div>
                                    <span className="text-[9px] text-slate-600 font-semibold text-center leading-tight">{MTA_CHANNEL_LABELS[r.channel]}</span>
                                    <span className="text-[8px] text-slate-400">{r.timestamp.slice(5,10)}</span>
                                    <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded-full ${
                                      r.converted ? 'bg-emerald-100 text-emerald-700'
                                      : r.clicked ? 'bg-indigo-100 text-indigo-700'
                                      : r.opened  ? 'bg-blue-100 text-blue-700'
                                      : 'bg-slate-100 text-slate-500'
                                    }`}>{statusLabel}</span>
                                  </div>
                                  {idx < rows.length - 1 && (
                                    <div className="flex items-center pb-8 shrink-0">
                                      <div className="w-5 h-0.5 bg-slate-200" />
                                      <span className="text-slate-300 text-xs">›</span>
                                    </div>
                                  )}
                                </React.Fragment>
                              );
                            })}
                            {didConvert && (
                              <div className="flex items-center pb-8 shrink-0">
                                <div className="w-5 h-0.5 bg-emerald-300" />
                                <div className="w-9 h-9 rounded-full bg-emerald-500 border-2 border-emerald-600 flex items-center justify-center ml-0">
                                  <CheckCircle2 className="w-4 h-4 text-white" />
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {Object.keys(journeyMap).length > 6 && (
                    <p className="text-[10px] text-slate-400 text-center">Showing 6 of {Object.keys(journeyMap).length} journeys</p>
                  )}
                </div>
              );
            })()}
          </div>
        )}

        {/* ── Tab: AI Insight ───────────────────────────────────────────────── */}
        {activeTab === 'insight' && (() => {
          const suppressed     = aiInsight?.suppressed_channels ?? [];
          const topAttrChannel = sortedAttr[0]?.[0];
          const secondAttrCh   = sortedAttr[1]?.[0];
          const bestLabel      = MTA_CHANNEL_LABELS[bestChannel ?? ''] ?? bestChannel ?? 'this channel';

          return (
            <div className="space-y-3">

              {/* ── Recommendation headline card ── */}
              <div className="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50 via-indigo-50 to-violet-50 overflow-hidden">
                <div className="px-4 py-3.5 flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shrink-0 shadow-sm">
                    <span className="text-white text-lg">{MTA_CHANNEL_ICONS[bestChannel ?? ''] ?? <Sparkles className="w-5 h-5" />}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-[10px] font-bold uppercase tracking-widest text-blue-500">Recommended Channel</span>
                      {channelRecommendation?.signal_source === 'personal' ? (
                        <span className="text-[9px] font-bold text-emerald-700 bg-emerald-100 border border-emerald-200 px-1.5 py-0.5 rounded-full">Personal signal</span>
                      ) : (
                        <span className="text-[9px] font-bold text-indigo-600 bg-indigo-100 border border-indigo-200 px-1.5 py-0.5 rounded-full">Segment signal</span>
                      )}
                      {suppressed.length > 0 && (
                        <span className="text-[9px] font-bold text-amber-700 bg-amber-100 border border-amber-200 px-1.5 py-0.5 rounded-full">{suppressed.length} suppressed</span>
                      )}
                    </div>
                    <p className="text-base font-black text-slate-800 leading-snug">
                      {bestLabel}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {aiInsight?.headline ?? `Best delivery channel for ${persona ?? 'this customer'}`}
                    </p>
                  </div>
                </div>
                {/* Persona + attribution strip */}
                <div className="flex items-center gap-0 border-t border-blue-200/60 divide-x divide-blue-200/60">
                  <div className="flex-1 px-3 py-2 text-center">
                    <p className="text-[9px] text-blue-400 uppercase tracking-wide">Persona</p>
                    <p className="text-[11px] font-bold text-indigo-700">{persona ?? ' - '}</p>
                  </div>
                  <div className="flex-1 px-3 py-2 text-center">
                    <p className="text-[9px] text-blue-400 uppercase tracking-wide">Attribution</p>
                    <p className="text-[11px] font-bold text-blue-700">{Math.round((mtaAttribution?.[bestChannel ?? ''] ?? 0) * 100)}%</p>
                  </div>
                  <div className="flex-1 px-3 py-2 text-center">
                    <p className="text-[9px] text-blue-400 uppercase tracking-wide">Confidence</p>
                    <p className="text-[11px] font-bold text-indigo-700">{channelRecommendation?.confidence ?? ' - '}</p>
                  </div>
                  {(aiInsight?.persona_conv_rate ?? 0) > 0 && (
                    <div className="flex-1 px-3 py-2 text-center">
                      <p className="text-[9px] text-blue-400 uppercase tracking-wide">Conv. Rate</p>
                      <p className="text-[11px] font-bold text-emerald-700">{aiInsight?.persona_conv_rate ?? 0}%</p>
                    </div>
                  )}
                </div>
              </div>

              {/* ── Signal explanation ── */}
              {(() => {
                const rec = channelRecommendation;
                const isPersonal = rec?.signal_source === 'personal';
                const bestAttrPct = Math.round((mtaAttribution?.[bestChannel ?? ''] ?? 0) * 100);
                return (
                  <div className={`rounded-xl border overflow-hidden ${isPersonal ? 'border-emerald-200' : 'border-indigo-200'}`}>
                    <div className={`flex items-center gap-2.5 px-3.5 py-2.5 ${isPersonal ? 'bg-emerald-50 border-b border-emerald-200' : 'bg-indigo-50 border-b border-indigo-200'}`}>
                      {isPersonal
                        ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        : <Info className="w-4 h-4 text-indigo-500 shrink-0" />}
                      <span className={`text-xs font-bold ${isPersonal ? 'text-emerald-800' : 'text-indigo-800'}`}>
                        {isPersonal ? 'Personal engagement data used' : 'Segment Markov attribution used'}
                      </span>
                    </div>
                    <div className={`px-3.5 py-3 ${isPersonal ? 'bg-white' : 'bg-white'}`}>
                      {isPersonal ? (
                        <div className="space-y-2">
                          <p className="text-[11px] text-slate-600 leading-relaxed">
                            {rec?.total_personal_sends ?? 0}+ sends recorded  -  this customer's own behaviour overrides segment averages.
                            {' '}<span className="font-semibold text-slate-700">{bestLabel}</span> scored highest on personal engagement (clicks × 3 + opens × 1 ÷ sends).
                          </p>
                          {Object.keys(rec?.personal_scores ?? {}).length > 0 && (
                            <div className="space-y-1 mt-2">
                              {Object.entries(rec?.personal_scores ?? {})
                                .sort(([,a],[,b]) => b - a)
                                .map(([ch, s]) => {
                                  const scores = Object.values(rec?.personal_scores ?? {});
                                  const maxScore = Math.max(...scores) || 1;
                                  const isF = channelFatigue?.[ch]?.is_fatigued === true;
                                  const isBest = ch === bestChannel;
                                  return (
                                    <div key={ch} className="flex items-center gap-2">
                                      <span className={`text-[9px] w-16 shrink-0 font-semibold ${isF ? 'text-amber-600 line-through' : isBest ? 'text-blue-700' : 'text-slate-500'}`}>{MTA_CHANNEL_LABELS[ch] ?? ch}</span>
                                      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                                        <div className={`h-full rounded-full transition-all ${isF ? 'bg-amber-300' : isBest ? 'bg-blue-500' : 'bg-slate-300'}`}
                                          style={{ width: `${Math.round((s / maxScore) * 100)}%` }} />
                                      </div>
                                      <span className={`text-[9px] font-bold w-8 text-right ${isF ? 'text-amber-600' : isBest ? 'text-blue-700' : 'text-slate-600'}`}>{s.toFixed(2)}</span>
                                    </div>
                                  );
                                })}
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Fewer than 3 personal sends recorded  -  using{' '}
                          <span className="font-semibold text-indigo-700">{persona ?? 'segment'} Markov model</span> for attribution.
                          {' '}<span className="font-semibold text-slate-700">{bestLabel}</span> carries {bestAttrPct}% segment-level credit.
                          Personal history builds after ≥ 3 sends.
                        </p>
                      )}
                    </div>
                  </div>
                );
              })()}

              {/* ── Evidence chips ── */}
              {(aiInsight?.reason_lines ?? []).length > 0 && (
                <div className="space-y-1.5">
                  {(aiInsight?.reason_lines ?? []).map((line, i) => (
                    <div key={i} className={`flex items-start gap-2.5 rounded-xl px-3 py-2.5 border ${
                      line.type === 'positive' ? 'bg-blue-50 border-blue-100' :
                      line.type === 'warning'  ? 'bg-amber-50 border-amber-200' :
                      'bg-slate-50 border-slate-200'}`}>
                      <span className={`shrink-0 mt-0.5 ${line.type === 'positive' ? 'text-blue-500' : line.type === 'warning' ? 'text-amber-500' : 'text-slate-400'}`}>
                        {line.type === 'positive' ? <CheckCircle2 className="w-3.5 h-3.5" /> : line.type === 'warning' ? <AlertTriangle className="w-3.5 h-3.5" /> : <Info className="w-3.5 h-3.5" />}
                      </span>
                      <p className={`text-[11px] leading-relaxed ${line.type === 'positive' ? 'text-blue-800' : line.type === 'warning' ? 'text-amber-800' : 'text-slate-600'}`}>{line.text}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* ── Channel attribution mini bars ── */}
              <div className="rounded-xl border border-slate-200 overflow-hidden">
                <div className="px-3.5 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
                  <BarChart2 className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-xs font-bold text-slate-700">Markov Attribution  -  {persona ?? 'Segment'}</span>
                  <span className="ml-auto text-[9px] text-slate-400 font-mono">Markov model</span>
                </div>
                <div className="p-3 space-y-1.5">
                  {sortedAttr.slice(0, 5).map(([ch, w]) => {
                    const pct = Math.round(w * 100);
                    const isF = channelFatigue?.[ch]?.is_fatigued === true;
                    const isBest = ch === bestChannel;
                    const pStats = personaChannelStats?.[ch];
                    const convPct = pStats ? +(((pStats.conversion_rate ?? 0) * 100).toFixed(1)) : 0;
                    return (
                      <div key={ch} className={`flex items-center gap-2.5 rounded-lg px-2.5 py-2 ${isBest && !isF ? 'bg-blue-50' : isF ? 'bg-amber-50/60' : 'bg-slate-50'}`}>
                        <span className={`shrink-0 ${isF ? 'text-amber-500' : isBest ? 'text-blue-600' : 'text-slate-400'}`}>{MTA_CHANNEL_ICONS[ch]}</span>
                        <span className={`text-[10px] font-semibold w-20 shrink-0 ${isF ? 'text-amber-700 line-through' : isBest ? 'text-blue-700' : 'text-slate-600'}`}>{MTA_CHANNEL_LABELS[ch]}</span>
                        <div className="flex-1 h-2 bg-white rounded-full overflow-hidden border border-slate-200">
                          <div className="h-full rounded-full transition-all"
                            style={{ width: `${pct}%`, backgroundColor: isF ? '#fbbf24' : isBest ? '#3b82f6' : (MTA_CHANNEL_HEX[ch] ?? '#94a3b8'), opacity: isF ? 0.5 : 1 }} />
                        </div>
                        <span className={`text-[10px] font-black w-8 text-right ${isF ? 'text-amber-600' : isBest ? 'text-blue-700' : 'text-slate-700'}`}>{pct}%</span>
                        {convPct > 0 && <span className="text-[9px] text-slate-400 w-14 text-right shrink-0">{convPct}% conv</span>}
                        {isBest && !isF && <span className="text-[8px] font-bold text-blue-600 bg-blue-100 px-1.5 py-0.5 rounded-full shrink-0">★</span>}
                        {isF && <AlertTriangle className="w-3 h-3 text-amber-500 shrink-0" />}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* ── Best alternative + suppressed ── */}
              <div className="flex flex-col gap-2">
                {aiInsight?.top_alternative && (
                  <div className="flex items-center gap-3 rounded-xl border border-indigo-100 bg-indigo-50/50 px-3 py-2.5">
                    <ArrowRight className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] font-bold text-indigo-800">Best Alternative</p>
                      <p className="text-[9px] text-indigo-500">{Math.round((mtaAttribution?.[aiInsight.top_alternative] ?? 0) * 100)}% attribution · not suppressed</p>
                    </div>
                    <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-indigo-200 bg-white">
                      <span className="text-indigo-500">{MTA_CHANNEL_ICONS[aiInsight.top_alternative]}</span>
                      <span className="text-[10px] font-bold text-indigo-700">{MTA_CHANNEL_LABELS[aiInsight.top_alternative]}</span>
                    </div>
                  </div>
                )}
                {suppressed.length > 0 && (
                  <div className="flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-[10px] font-bold text-amber-800 mb-1.5">{suppressed.length} channel{suppressed.length > 1 ? 's' : ''} suppressed  -  fatigue override</p>
                      <div className="flex flex-wrap gap-1.5">
                        {suppressed.map(ch => {
                          const f = channelFatigue?.[ch];
                          return (
                            <span key={ch} className="inline-flex items-center gap-1 text-[9px] font-bold text-amber-700 bg-white border border-amber-200 px-2 py-1 rounded-full">
                              {MTA_CHANNEL_ICONS[ch]} {MTA_CHANNEL_LABELS[ch]}
                              {f && <span className="text-amber-500 font-normal">· {f.sent} sent, {f.opened ?? 0} opened</span>}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {!aiInsight && (
                <div className="text-center text-slate-400 text-xs py-6 rounded-xl border border-dashed border-slate-200">
                  Run Agent C for this customer to generate MTA insights.
                </div>
              )}
            </div>
          );
        })()}

      </div>
    </div>
  );
}

// ── ExperimentLiftPanel ───────────────────────────────────────────────────────

function ExperimentLiftPanel({ expData }: {
  expData: ExperimentData;
}) {
  const holdoutRate = expData.holdout_conversion_rate ?? 0;
  const variants = expData.all_variants ?? [];
  const winningId = expData.winning_variant_id;

  // Build prose explanation from experiment data
  const winnerVariant = variants.find(v => v.variant_id === winningId);
  const winnerName = winnerVariant?.offer_name ?? 'winning offer';
  const winnerRate = expData.winning_conversion_rate ?? winnerVariant?.conversion_rate ?? 0;
  const liftAbs = expData.lift_abs ?? winnerVariant?.lift_abs ?? 0;
  const pVal = expData.p_value ?? winnerVariant?.p_value ?? 1;
  const sigVariants = variants.filter(v => v.is_significant).length;
  const pLabel = pVal < 0.001 ? 'p<0.001' : `p=${pVal.toFixed(3)}`;
  const decisionExplanation = winnerVariant
    ? `"${winnerName}" converted ${(winnerRate * 100).toFixed(1)}% of exposed customers vs ` +
      `${(holdoutRate * 100).toFixed(1)}% in the holdout  -  ` +
      `an absolute lift of +${(liftAbs * 100).toFixed(1)}pp (${pLabel}). ` +
      (sigVariants > 1
        ? `${sigVariants} of ${variants.length} variants were significant; this had the highest lift.`
        : sigVariants === 1
          ? `It was the only variant to reach statistical significance out of ${variants.length} tested.`
          : `No variants reached significance  -  this offer was selected as best available.`)
    : null;

  const channelColors: Record<string, string> = {
    in_app: 'bg-violet-500',
    email: 'bg-blue-500',
    direct_mail: 'bg-amber-500',
    branch: 'bg-emerald-600',
  };
  const channelLabels: Record<string, string> = {
    in_app: 'In-App',
    email: 'Email',
    direct_mail: 'Direct Mail',
    branch: 'Branch',
  };

  return (
    <div className="px-4 pb-4 space-y-3">
      {/* Key metrics strip */}
      <div className="grid grid-cols-3 gap-2 pt-1">
        <div className="rounded-xl bg-violet-50 border border-violet-100 px-3 py-2.5 text-center">
          <p className="text-[9px] font-bold uppercase tracking-wider text-violet-500 mb-0.5">Holdout rate</p>
          <p className="text-base font-black text-violet-900">{(expData.holdout_conversion_rate * 100).toFixed(1)}%</p>
          <p className="text-[9px] text-violet-400">no offer shown</p>
        </div>
        <div className="rounded-xl bg-emerald-50 border border-emerald-200 px-3 py-2.5 text-center">
          <p className="text-[9px] font-bold uppercase tracking-wider text-emerald-600 mb-0.5">Winner rate</p>
          <p className="text-base font-black text-emerald-800">{((expData.winning_conversion_rate ?? 0) * 100).toFixed(1)}%</p>
          <p className="text-[9px] text-emerald-500">with offer shown</p>
        </div>
        <div className="rounded-xl bg-indigo-50 border border-indigo-100 px-3 py-2.5 text-center">
          <p className="text-[9px] font-bold uppercase tracking-wider text-indigo-500 mb-0.5">Lift</p>
          <p className="text-base font-black text-indigo-800">+{((expData.lift_abs ?? 0) * 100).toFixed(1)}pp</p>
          <p className="text-[9px] text-indigo-400">
            {expData.p_value != null ? (expData.p_value < 0.001 ? 'p<0.001' : `p=${expData.p_value.toFixed(3)}`) : ''}
          </p>
        </div>
      </div>

      {/* Plain-English decision explanation */}
      {decisionExplanation && (
        <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2.5 flex items-start gap-2">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
          <p className="text-[11px] text-emerald-800 leading-relaxed">{decisionExplanation}</p>
        </div>
      )}

      {/* Variants table */}
      <div className="rounded-lg border border-slate-200 overflow-hidden text-[11px]">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="text-left px-3 py-2 text-slate-500 font-semibold">Offer Variant</th>
              <th className="text-right px-3 py-2 text-slate-500 font-semibold">Rate</th>
              <th className="text-right px-3 py-2 text-slate-500 font-semibold">Lift</th>
              <th className="text-right px-3 py-2 text-slate-500 font-semibold w-16">p-value</th>
              <th className="text-center px-3 py-2 text-slate-500 font-semibold w-10">Sig.</th>
            </tr>
          </thead>
          <tbody>
            {variants.map((v) => {
              const isWinner = v.variant_id === winningId;
              return (
                <tr key={v.variant_id} className={`border-b border-slate-100 last:border-0 ${isWinner ? 'bg-emerald-50' : 'bg-white'}`}>
                  <td className="px-3 py-2 font-medium text-slate-700">
                    <div className="flex items-center gap-1.5">
                      {isWinner && <span className="text-emerald-500">★</span>}
                      <span>{v.offer_name}</span>
                    </div>
                    <span className="text-[10px] text-slate-400 capitalize">{v.channel?.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-700">{(v.conversion_rate * 100).toFixed(1)}%</td>
                  <td className={`px-3 py-2 text-right font-mono font-semibold ${v.lift_abs > 0 ? 'text-emerald-700' : 'text-slate-400'}`}>
                    {v.lift_abs > 0 ? `+${(v.lift_abs * 100).toFixed(1)}pp` : ' - '}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-500">
                    {v.p_value < 0.001 ? '<0.001' : v.p_value.toFixed(4)}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {v.is_significant
                      ? <span className="text-emerald-600 font-bold">✓</span>
                      : <span className="text-slate-300">–</span>
                    }
                  </td>
                </tr>
              );
            })}
            {/* Holdout row */}
            <tr className="bg-slate-50 border-t border-slate-200">
              <td className="px-3 py-2 text-slate-500 italic">Holdout (no offer)</td>
              <td className="px-3 py-2 text-right font-mono text-slate-500">{(holdoutRate * 100).toFixed(1)}%</td>
              <td className="px-3 py-2 text-right text-slate-400"> - </td>
              <td className="px-3 py-2 text-right text-slate-400"> - </td>
              <td className="px-3 py-2 text-center text-[10px] text-slate-400">baseline</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  );
}

// ── No-Offer Experiment Panel ─────────────────────────────────────────────────
function NoOfferExperimentPanel({ expData }: { expData?: ExperimentData }) {
  const holdoutRate = expData?.holdout_conversion_rate ?? 0;
  const bestLift = expData?.all_variants
    ? Math.max(...expData.all_variants.map(v => v.lift_abs ?? 0))
    : 0;

  return (
    <div className="rounded-2xl border-2 border-dashed border-amber-200 bg-amber-50 px-6 py-6">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
          <FlaskConical className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <p className="text-sm font-bold text-amber-800">No offer shown  -  experiment result</p>
          <p className="text-sm text-amber-700 mt-1 leading-snug">
            No offer variant achieved statistically significant conversion lift over the holdout
            baseline ({(holdoutRate * 100).toFixed(1)}%) for this customer segment.
          </p>
          {bestLift > 0 && (
            <p className="text-xs text-amber-600 mt-1.5">
              Best variant lift observed: +{(bestLift * 100).toFixed(1)}pp  -  not significant at p &lt; 0.05.
            </p>
          )}
          {expData?.experiment_id && (
            <p className="text-[10px] text-amber-500 font-mono mt-2">{expData.experiment_id}</p>
          )}
        </div>
      </div>
      {expData && expData.all_variants && expData.all_variants.length > 0 && (
        <div className="mt-4 rounded-lg border border-amber-200 overflow-hidden text-[11px]">
          <table className="w-full">
            <thead>
              <tr className="bg-amber-100 border-b border-amber-200">
                <th className="text-left px-3 py-2 text-amber-700 font-semibold">Offer Variant</th>
                <th className="text-right px-3 py-2 text-amber-700 font-semibold">Rate</th>
                <th className="text-right px-3 py-2 text-amber-700 font-semibold">Lift</th>
                <th className="text-right px-3 py-2 text-amber-700 font-semibold">p-value</th>
              </tr>
            </thead>
            <tbody>
              {expData.all_variants.map((v) => (
                <tr key={v.variant_id} className="border-b border-amber-100 last:border-0 bg-white">
                  <td className="px-3 py-2 text-slate-700">{v.offer_name}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-600">{(v.conversion_rate * 100).toFixed(1)}%</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-600">
                    {v.lift_abs > 0 ? `+${(v.lift_abs * 100).toFixed(1)}pp` : ' - '}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-amber-700">{v.p_value?.toFixed(4) ?? ' - '}</td>
                </tr>
              ))}
              <tr className="bg-amber-50 border-t border-amber-200">
                <td className="px-3 py-2 text-amber-600 italic">Holdout (no offer)</td>
                <td className="px-3 py-2 text-right font-mono text-amber-600">{(holdoutRate * 100).toFixed(1)}%</td>
                <td className="px-3 py-2 text-right text-amber-400"> - </td>
                <td className="px-3 py-2 text-right text-amber-400">baseline</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Offer Hero Card (replaces flat Offer Intelligence panel in customer view) ─
function OfferHeroCard({
  offerIntel,
  productName,
  productCategory,
  offerScoreOpen,
  onToggleScore,
}: {
  offerIntel: OfferIntelligenceSection;
  productName?: string;
  productCategory?: string;
  offerScoreOpen: boolean;
  onToggleScore: () => void;
}) {
  const [openFactors, setOpenFactors] = React.useState<Set<string>>(new Set());

  if (!offerIntel.available || !offerIntel.selected_offer) {
    // Experiment suppression: no variant beat the holdout
    if (offerIntel.reason === 'no_significant_lift') {
      return <NoOfferExperimentPanel expData={offerIntel.experiment_data} />;
    }
    return (
      <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 px-6 py-8 text-center">
        <Gift className="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500 font-medium">No active promotional offers for this product</p>
        <p className="text-slate-400 text-sm mt-1">Check back soon for new promotions</p>
      </div>
    );
  }

  const sel = offerIntel.selected_offer;
  const cfg = getOfferHeroConfig(sel.offer_type);
  const typeCfg = OFFER_TYPE_CONFIG[sel.offer_type] ?? { label: sel.offer_type?.replace(/_/g, ' ') ?? 'Offer', color: 'text-white', bgColor: 'bg-white/20 border-white/30' };
  const isExperimentDriven = offerIntel.selection_method === 'experiment_lift';
  const scorePct = isExperimentDriven
    ? Math.round((offerIntel.experiment_data?.lift_pct ?? 0))
    : Math.round((offerIntel.offer_score ?? 0) * 100);
  const benefits = [sel.content_benefit_1, sel.content_benefit_2, sel.content_benefit_3].filter(Boolean);
  const breakdown = offerIntel.offer_score_breakdown ?? {};
  const breakdownEntries = Object.entries(breakdown);

  return (
    <div className="rounded-2xl overflow-hidden shadow-lg border border-slate-200">
      {/* ── Gradient hero section ── */}
      <div className={`bg-gradient-to-br ${cfg.gradient} p-6 relative overflow-hidden`}>
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-48 h-48 rounded-full bg-white/5 -translate-y-12 translate-x-12" />
        <div className="absolute bottom-0 left-0 w-32 h-32 rounded-full bg-black/5 translate-y-8 -translate-x-8" />

        {/* Top row: "Exclusive offer for you" + type badge + urgency */}
        <div className="relative flex items-center justify-between flex-wrap gap-2 mb-4">
          <span className={`text-[10px] font-bold uppercase tracking-widest ${cfg.accent} opacity-80`}>
            Exclusive offer for you
          </span>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-white/20 text-white border border-white/30">
              <Tag className="w-3 h-3" />
              {typeCfg.label}
            </span>
            <UrgencyCountdownChip daysRemaining={sel.days_remaining} isEvergreen={sel.is_evergreen} />
          </div>
        </div>

        {/* Hero stat */}
        <div className="relative mb-2">
          <p className="text-4xl font-black text-white leading-none tracking-tight drop-shadow-sm">
            {sel.content_hero_stat ?? sel.headline_value ?? sel.offer_name}
          </p>
        </div>

        {/* Offer name */}
        <p className={`relative text-base font-semibold ${cfg.accent} mt-1`}>{sel.offer_name}</p>

        {/* Product context */}
        {productName && (
          <div className={`relative mt-3 inline-flex items-center gap-1.5 text-xs font-medium ${cfg.accent} opacity-70`}>
            <span className={`w-1.5 h-1.5 rounded-full bg-white/60`} />
            on {productName}{productCategory ? ` · ${productCategory}` : ''}
          </div>
        )}
      </div>

      {/* ── How to earn ── */}
      {sel.content_how_to_earn && (
        <div className="px-6 py-4 bg-white border-b border-slate-100">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">How to earn it</p>
          <p className="text-sm text-slate-700 leading-relaxed">{sel.content_how_to_earn}</p>
        </div>
      )}

      {/* ── Benefits + score ── */}
      <div className="px-6 py-4 bg-white flex flex-col sm:flex-row gap-5">
        {benefits.length > 0 && (
          <div className="flex-1 space-y-2">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">What you get</p>
            {benefits.map((b, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                </div>
                <span className="text-sm text-slate-700 leading-snug">{b}</span>
              </div>
            ))}
          </div>
        )}
        {/* Score indicator */}
        {scorePct > 0 && (
          <div className="flex flex-col items-center gap-1 sm:w-28 flex-shrink-0">
            <div className="relative w-20 h-20">
              <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="32" fill="none" stroke="#f0fdf4" strokeWidth="8" />
                <circle
                  cx="40" cy="40" r="32" fill="none"
                  stroke={isExperimentDriven ? '#7c3aed' : '#10b981'} strokeWidth="8"
                  strokeDasharray={`${2 * Math.PI * 32}`}
                  strokeDashoffset={`${2 * Math.PI * 32 * (1 - Math.min(scorePct / 100, 1))}`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-lg font-black ${isExperimentDriven ? 'text-violet-700' : 'text-emerald-700'}`}>
                  {isExperimentDriven ? `+${scorePct}` : scorePct}
                </span>
                <span className="text-[10px] text-slate-400 leading-none">{isExperimentDriven ? 'pp lift' : '%'}</span>
              </div>
            </div>
            <p className="text-[11px] font-semibold text-slate-500 text-center">
              {isExperimentDriven ? 'Conv. lift' : 'Offer fit'}
            </p>
            {isExperimentDriven && offerIntel.experiment_data?.p_value != null && (
              <p className="text-[10px] text-violet-500 font-mono text-center">
                p={offerIntel.experiment_data.p_value < 0.001 ? '<0.001' : offerIntel.experiment_data.p_value.toFixed(3)}
              </p>
            )}
            {!isExperimentDriven && (
              <p className="text-[10px] text-slate-400 text-center">{offerIntel.offers_considered ?? 0} scored</p>
            )}
          </div>
        )}
      </div>

      {/* ── Why this offer? (persona_offer_reason) ── */}
      {offerIntel.persona_offer_reason && (
        <div className="px-6 py-3.5 bg-indigo-50 border-t border-indigo-100 flex items-start gap-2.5">
          <Sparkles className="w-3.5 h-3.5 text-indigo-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-500 mb-0.5">Why this offer</p>
            <p className="text-[12px] text-indigo-800 leading-relaxed">{offerIntel.persona_offer_reason}</p>
          </div>
        </div>
      )}

      {/* ── A/B Experiment Results (always visible) or Formula Score Breakdown ── */}
      {isExperimentDriven && offerIntel.experiment_data ? (
        <div className="border-t border-slate-100">
          {/* Explanation header  -  always visible */}
          <div className="px-6 py-3.5 bg-gradient-to-r from-violet-50 to-indigo-50 border-b border-violet-100 flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-violet-600 flex items-center justify-center shrink-0">
              <FlaskConical className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-violet-900">How this offer was selected  -  A/B Experiment</p>
              <p className="text-[10px] text-violet-500 mt-0.5">
                Offer chosen because it outperformed the holdout group with statistical significance
              </p>
            </div>
            {offerIntel.experiment_data.experiment_id && (
              <span className="text-[9px] text-violet-400 font-mono shrink-0 hidden sm:block truncate max-w-[120px]">
                {offerIntel.experiment_data.experiment_id}
              </span>
            )}
          </div>
          {/* Methodology pills */}
          <div className="px-6 py-3 flex flex-wrap gap-2 border-b border-slate-100 bg-white">
            <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold px-2.5 py-1 rounded-full bg-violet-50 border border-violet-200 text-violet-700">
              <FlaskConical className="w-3 h-3" /> Randomized A/B test
            </span>
            <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700">
              <CheckCircle2 className="w-3 h-3" /> Statistically significant (p &lt; 0.05)
            </span>
            <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold px-2.5 py-1 rounded-full bg-slate-50 border border-slate-200 text-slate-600">
              <Users className="w-3 h-3" /> {offerIntel.experiment_data.all_variants?.reduce((s, v) => s + v.n_exposed, 0).toLocaleString() ?? ' - '} customers tested
            </span>
          </div>
          {/* Always-expanded experiment panel */}
          <div className="bg-white">
            <ExperimentLiftPanel
              expData={offerIntel.experiment_data}
            />
          </div>
        </div>
      ) : breakdownEntries.length > 0 && (
        <div className="border-t border-slate-100 bg-slate-50/60">
          <button
            type="button"
            onClick={onToggleScore}
            className="w-full flex items-center gap-2 px-6 py-3 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors text-left"
          >
            <Zap className="w-3.5 h-3.5 text-emerald-500" />
            How this offer fit score was calculated
            {offerScoreOpen ? <ChevronUp className="w-3.5 h-3.5 ml-auto" /> : <ChevronDown className="w-3.5 h-3.5 ml-auto" />}
          </button>
          <AnimatePresence>
            {offerScoreOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                {/* Score explanation context */}
                <div className="px-4 py-3 bg-emerald-50 border-b border-emerald-100 flex items-start gap-2">
                  <Info className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                  <p className="text-[11px] text-emerald-800 leading-relaxed">
                    <span className="font-semibold">Offer fit score = weighted match</span> across {breakdownEntries.length} factors
                    comparing this customer's profile to the offer's requirements. Each factor is scored 0–100%, then
                    multiplied by its weight. A score above 65% signals a strong match.
                  </p>
                </div>
                <div className="px-4 pb-4 pt-3 space-y-1.5">
                  {breakdownEntries.map(([key, val]) => {
                    const factorPct = Math.round(val.score * 100);
                    const factorLabel = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                    const isFactorOpen = openFactors.has(key);
                    const calc = val.calculation;
                    return (
                      <div key={key} className={`rounded-lg overflow-hidden ${calc ? 'border border-slate-100 bg-white' : ''}`}>
                        <div
                          className={calc ? 'cursor-pointer select-none' : ''}
                          onClick={() => {
                            if (!calc) return;
                            setOpenFactors(prev => {
                              const next = new Set(prev);
                              if (next.has(key)) next.delete(key); else next.add(key);
                              return next;
                            });
                          }}
                        >
                          <div className="flex items-center justify-between text-xs pt-2 pb-0.5 px-2.5">
                            <span className="text-slate-700 font-medium">{factorLabel}</span>
                            <div className="flex items-center gap-1">
                              <span className="text-emerald-700 font-semibold">{factorPct}%</span>
                              {calc && (isFactorOpen
                                ? <ChevronUp className="w-3 h-3 text-slate-400" />
                                : <ChevronDown className="w-3 h-3 text-slate-400" />
                              )}
                            </div>
                          </div>
                          <div className="h-1.5 bg-emerald-100 rounded-full overflow-hidden mx-2.5">
                            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${factorPct}%` }} />
                          </div>
                          <p className="text-[11px] text-slate-500 mt-0.5 pb-1.5 px-2.5 leading-snug">{val.explanation}</p>
                        </div>
                        {calc && (
                          <AnimatePresence>
                            {isFactorOpen && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.18 }}
                                className="overflow-hidden"
                              >
                                <div className="bg-slate-50 border-t border-slate-100 px-3 py-2.5 space-y-2">
                                  <div className="grid grid-cols-2 gap-x-3 gap-y-1.5">
                                    {Object.entries(calc.inputs).map(([k, v]) => (
                                      <div key={k}>
                                        <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-wide block">{k}</span>
                                        <span className="text-[11px] text-slate-700 font-medium">{String(v)}</span>
                                      </div>
                                    ))}
                                  </div>
                                  <div className="space-y-1">
                                    {calc.steps.map((step, si) => (
                                      <div key={si} className="flex items-start gap-1.5">
                                        <span className="text-[10px] font-bold text-emerald-500 shrink-0 mt-px">{si + 1}.</span>
                                        <p className="text-[10px] text-slate-600 leading-snug font-mono">{step}</p>
                                      </div>
                                    ))}
                                  </div>
                                  <div className="bg-white rounded border border-emerald-200 px-2.5 py-1.5">
                                    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Formula</span>
                                    <code className="text-[10px] text-emerald-700 font-mono">{calc.formula}</code>
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        )}
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Runner-up chips */}
      {!isExperimentDriven && (offerIntel.runner_up_offers ?? []).length > 0 && (
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Other eligible offers</p>
          <div className="flex flex-wrap gap-2">
            {(offerIntel.runner_up_offers ?? []).slice(0, 3).map((ro, i) => (
              <span key={i} className="inline-flex items-center gap-1 text-xs text-slate-600 bg-white border border-slate-200 rounded-lg px-2.5 py-1 shadow-sm">
                <span className="text-slate-400">#{i + 2}</span>
                {ro.offer_name}
                {ro.offer_score != null && (
                  <span className="text-slate-400 ml-1">{Math.round(ro.offer_score * 100)}%</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Offer Intelligence Panel ──────────────────────────────────────────────────

function OfferIntelligencePanel({
  offerIntel,
  offerScoreOpen,
  onToggleScore,
}: {
  offerIntel: OfferIntelligenceSection;
  offerScoreOpen: boolean;
  onToggleScore: () => void;
}) {
  const [openFactors, setOpenFactors] = React.useState<Set<string>>(new Set());

  if (!offerIntel.available || !offerIntel.selected_offer) {
    if (offerIntel.reason === 'no_significant_lift') {
      return <NoOfferExperimentPanel expData={offerIntel.experiment_data} />;
    }
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 px-5 py-4 text-sm text-slate-500">
        No active promotional offers for this product right now.
      </div>
    );
  }

  const sel = offerIntel.selected_offer;
  const isExperimentDriven = offerIntel.selection_method === 'experiment_lift';
  const typeCfg = OFFER_TYPE_CONFIG[sel.offer_type] ?? { label: sel.offer_type, color: 'text-slate-600', bgColor: 'bg-slate-50 border-slate-200' };
  const scorePct = Math.round((offerIntel.offer_score ?? 0) * 100);
  const breakdown = offerIntel.offer_score_breakdown ?? {};
  const breakdownEntries = Object.entries(breakdown);

  const benefits = [sel.content_benefit_1, sel.content_benefit_2, sel.content_benefit_3].filter(Boolean);

  return (
    <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50/80 via-teal-50/60 to-white shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-3 border-b border-emerald-100 bg-gradient-to-r from-emerald-100/60 to-teal-100/40">
        <Gift className="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <span className="text-sm font-bold text-emerald-900">Offer Intelligence</span>
        {isExperimentDriven && (
          <span className="ml-auto inline-flex items-center gap-1 text-[10px] uppercase tracking-wide font-semibold text-violet-700 bg-violet-50 border border-violet-200 px-2 py-0.5 rounded-full">
            <FlaskConical className="w-3 h-3" />
            A/B Experiment
          </span>
        )}
      </div>

      <div className="p-5">
        {/* Main content: offer details + score */}
        <div className="flex flex-col sm:flex-row gap-5">
          {/* Left: offer details */}
          <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-start gap-2 flex-wrap">
              <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border ${typeCfg.bgColor} ${typeCfg.color}`}>
                <Tag className="w-3 h-3" />
                {typeCfg.label}
              </span>
              <UrgencyCountdownChip daysRemaining={sel.days_remaining} isEvergreen={sel.is_evergreen} />
            </div>

            <div>
              <p className="text-lg font-bold text-slate-900 leading-tight">{sel.offer_name}</p>
              <p className="text-emerald-700 font-semibold text-sm mt-0.5">{sel.headline_value}</p>
            </div>

            {sel.terms_summary && (
              <div className="inline-block bg-white border border-slate-200 rounded-lg px-3 py-1.5">
                <span className="font-mono text-xs text-slate-700">{sel.terms_summary}</span>
              </div>
            )}

            {sel.content_how_to_earn && (
              <p className="text-sm text-slate-600 leading-relaxed">{sel.content_how_to_earn}</p>
            )}

            {benefits.length > 0 && (
              <ul className="space-y-1">
                {benefits.map((b, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    {b}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Right: score indicator */}
          <div className="flex flex-col items-center gap-3 sm:w-36 flex-shrink-0">
            {isExperimentDriven && offerIntel.experiment_data ? (
              <div className="flex flex-col items-center gap-1.5">
                <div className="text-3xl font-black text-violet-700">
                  +{(offerIntel.experiment_data.lift_pct ?? 0).toFixed(1)}pp
                </div>
                <p className="text-xs font-semibold text-slate-600 text-center">Conversion Lift</p>
                <p className="text-[11px] font-mono text-violet-500 text-center">
                  p={offerIntel.experiment_data.p_value != null && offerIntel.experiment_data.p_value < 0.001
                    ? '<0.001'
                    : (offerIntel.experiment_data.p_value ?? 1).toFixed(4)}
                </p>
              </div>
            ) : (
              <>
                <div className="relative w-24 h-24">
                  <svg className="w-24 h-24 -rotate-90" viewBox="0 0 80 80">
                    <circle cx="40" cy="40" r="32" fill="none" stroke="#d1fae5" strokeWidth="8" />
                    <circle
                      cx="40" cy="40" r="32" fill="none"
                      stroke="#10b981" strokeWidth="8"
                      strokeDasharray={`${2 * Math.PI * 32}`}
                      strokeDashoffset={`${2 * Math.PI * 32 * (1 - (offerIntel.offer_score ?? 0))}`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold text-emerald-700">{scorePct}</span>
                    <span className="text-xs text-slate-500">%</span>
                  </div>
                </div>
                <p className="text-xs font-semibold text-slate-600 text-center">Offer Fit Score</p>
                <div className="text-xs text-slate-500 text-center">
                  {offerIntel.offers_considered ?? 0} offers scored
                  {(offerIntel.offers_blocked_by_eligibility ?? 0) > 0 && (
                    <span className="block text-slate-400">{offerIntel.offers_blocked_by_eligibility} ineligible</span>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Experiment panel (always visible) or formula breakdown */}
        {isExperimentDriven && offerIntel.experiment_data ? (
          <div className="mt-4 border-t border-emerald-100 pt-0 -mx-5 -mb-5 overflow-hidden rounded-b-2xl">
            <div className="px-5 py-3 bg-gradient-to-r from-violet-50 to-indigo-50 border-b border-violet-100 flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-lg bg-violet-600 flex items-center justify-center shrink-0">
                <FlaskConical className="w-3 h-3 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-violet-900">How this offer was selected  -  A/B Experiment</p>
                <p className="text-[10px] text-violet-500 mt-0.5">Outperformed holdout group with statistical significance</p>
              </div>
            </div>
            <div className="bg-white">
              <ExperimentLiftPanel
                expData={offerIntel.experiment_data}
                />
            </div>
          </div>
        ) : breakdownEntries.length > 0 && (
          <div className="mt-4 border-t border-emerald-100 pt-3">
            <button
              type="button"
              onClick={onToggleScore}
              className="flex items-center gap-2 text-sm font-semibold text-emerald-800 hover:text-emerald-900 transition-colors w-full text-left"
            >
              <Zap className="w-4 h-4" />
              How this offer fit score was calculated
              {offerScoreOpen ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
            </button>
            <AnimatePresence>
              {offerScoreOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="mt-3 space-y-1.5">
                    {breakdownEntries.map(([key, val]) => {
                      const factorPct = Math.round(val.score * 100);
                      const factorLabel = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                      const isFactorOpen = openFactors.has(key);
                      const calc = val.calculation;
                      return (
                        <div key={key} className={`rounded-lg overflow-hidden ${calc ? 'border border-slate-200 bg-white' : ''}`}>
                          <div
                            className={calc ? 'cursor-pointer select-none' : ''}
                            onClick={() => {
                              if (!calc) return;
                              setOpenFactors(prev => {
                                const next = new Set(prev);
                                if (next.has(key)) next.delete(key); else next.add(key);
                                return next;
                              });
                            }}
                          >
                            <div className="flex items-center justify-between text-xs pt-2 pb-0.5 px-2.5">
                              <span className="text-slate-700 font-medium">{factorLabel}</span>
                              <div className="flex items-center gap-1">
                                <span className="text-emerald-700 font-semibold">{factorPct}%</span>
                                {calc && (isFactorOpen
                                  ? <ChevronUp className="w-3 h-3 text-slate-400" />
                                  : <ChevronDown className="w-3 h-3 text-slate-400" />
                                )}
                              </div>
                            </div>
                            <div className="h-1.5 bg-emerald-100 rounded-full overflow-hidden mx-2.5">
                              <div
                                className="h-full bg-emerald-500 rounded-full transition-all"
                                style={{ width: `${factorPct}%` }}
                              />
                            </div>
                            <p className="text-[11px] text-slate-500 mt-0.5 pb-1.5 px-2.5 leading-snug">{val.explanation}</p>
                          </div>
                          {calc && (
                            <AnimatePresence>
                              {isFactorOpen && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: 'auto', opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  transition={{ duration: 0.18 }}
                                  className="overflow-hidden"
                                >
                                  <div className="bg-slate-50 border-t border-slate-200 px-3 py-2.5 space-y-2">
                                    <div className="grid grid-cols-2 gap-x-3 gap-y-1.5">
                                      {Object.entries(calc.inputs).map(([k, v]) => (
                                        <div key={k}>
                                          <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-wide block">{k}</span>
                                          <span className="text-[11px] text-slate-700 font-medium">{String(v)}</span>
                                        </div>
                                      ))}
                                    </div>
                                    <div className="space-y-1">
                                      {calc.steps.map((step, si) => (
                                        <div key={si} className="flex items-start gap-1.5">
                                          <span className="text-[10px] font-bold text-emerald-500 shrink-0 mt-px">{si + 1}.</span>
                                          <p className="text-[10px] text-slate-600 leading-snug font-mono">{step}</p>
                                        </div>
                                      ))}
                                    </div>
                                    <div className="bg-white rounded border border-emerald-200 px-2.5 py-1.5">
                                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Formula</span>
                                      <code className="text-[10px] text-emerald-700 font-mono">{calc.formula}</code>
                                    </div>
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Runner-up chips */}
        {(offerIntel.runner_up_offers ?? []).length > 0 && (
          <div className="mt-4 pt-3 border-t border-emerald-100">
            <p className="text-xs font-semibold text-slate-500 mb-2">Also considered</p>
            <div className="flex flex-wrap gap-2">
              {offerIntel.runner_up_offers!.map((ru) => (
                <div
                  key={ru.offer_id}
                  className="group relative"
                  title={ru.reason_not_selected}
                >
                  <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-600 cursor-default hover:border-slate-300 transition-colors">
                    {ru.offer_name}
                    {ru.offer_score != null && (
                      <span className="text-slate-400 ml-1">{Math.round(ru.offer_score * 100)}%</span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Secondary offer (different offer type  -  "Also Consider" stack) */}
        {offerIntel.secondary_offer && (
          <div className="mt-4 pt-3 border-t border-emerald-100">
            <p className="text-xs font-semibold text-slate-500 mb-2">Also consider</p>
            <div className="flex items-start gap-3 rounded-lg bg-white border border-slate-200 px-3 py-2.5 hover:border-emerald-300 transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-semibold text-slate-700 truncate">
                    {offerIntel.secondary_offer.offer_name}
                  </span>
                  {offerIntel.secondary_offer.offer_type && (
                    <span className="inline-flex items-center text-[10px] font-semibold px-1.5 py-0.5 rounded bg-violet-100 text-violet-700 uppercase tracking-wide shrink-0">
                      {offerIntel.secondary_offer.offer_type.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>
                {offerIntel.secondary_offer.headline_value && (
                  <p className="text-xs text-slate-500 mt-0.5 truncate">
                    {offerIntel.secondary_offer.content_hero_stat ?? offerIntel.secondary_offer.headline_value}
                  </p>
                )}
              </div>
              {offerIntel.secondary_offer.offer_score != null && (
                <span className="shrink-0 text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                  {Math.round(offerIntel.secondary_offer.offer_score * 100)}%
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Agentic Customer Analysis Panel ─────────────────────────────────────────

function CustomerAnalysisPanel({
  analysis,
}: {
  analysis: NonNullable<OneBestOfferPayload['customer_analysis']>;
}) {
  const paragraph = [
    analysis.product_fit_rationale,
    analysis.personalized_pitch,
  ].filter(Boolean).join(' ');

  if (!paragraph) return null;

  return (
    <div className="rounded-2xl border border-violet-100 bg-violet-50/40 px-5 py-4 flex items-start gap-3">
      <Sparkles className="w-4 h-4 text-violet-500 shrink-0 mt-0.5" />
      <p className="text-sm text-slate-700 leading-relaxed">{paragraph}</p>
    </div>
  );
}

// ── Urgency Countdown Chip ────────────────────────────────────────────────────

function UrgencyCountdownChip({ daysRemaining, isEvergreen }: { daysRemaining?: number | null; isEvergreen?: boolean }) {
  if (isEvergreen) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border bg-slate-50 border-slate-200 text-slate-500">
        <Clock className="w-3 h-3" />
        No expiry
      </span>
    );
  }
  if (daysRemaining == null) return null;
  let cls = 'bg-green-50 border-green-200 text-green-700';
  if (daysRemaining <= 7) cls = 'bg-red-50 border-red-200 text-red-700 animate-pulse';
  else if (daysRemaining <= 30) cls = 'bg-amber-50 border-amber-200 text-amber-700';
  else if (daysRemaining <= 90) cls = 'bg-lime-50 border-lime-200 text-lime-700';
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border ${cls}`}>
      <Clock className="w-3 h-3" />
      {daysRemaining <= 7 ? `Ends in ${daysRemaining}d` : `${daysRemaining}d left`}
    </span>
  );
}

// ── Credit Personalization Card ───────────────────────────────────────────────

function CreditPersonalizationCard({ cp }: { cp: NonNullable<OneBestOfferPayload['credit_personalization']> }) {
  const tierColors: Record<string, string> = {
    excellent: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    good: 'bg-blue-100 text-blue-800 border-blue-200',
    fair: 'bg-amber-100 text-amber-800 border-amber-200',
    fair_borderline: 'bg-orange-100 text-orange-800 border-orange-200',
  };
  const tier = (cp.pre_approval_tier ?? cp.credit_tier ?? '').toLowerCase();
  const tierCls = tierColors[tier] ?? 'bg-slate-100 text-slate-700 border-slate-200';
  const isCard = cp.product_type === 'credit_card';
  const isLoan = cp.product_type === 'mortgage' || cp.product_type === 'auto' || cp.product_type === 'loan';

  return (
    <div className="rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50/80 via-violet-50/60 to-white shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b border-indigo-100 bg-gradient-to-r from-indigo-100/60 to-violet-100/40">
        <Shield className="w-4 h-4 text-indigo-600 flex-shrink-0" />
        <span className="text-sm font-bold text-indigo-900">Your Personalized Terms</span>
        {tier && (
          <span className={`ml-auto text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full border ${tierCls}`}>
            {cp.pre_approval_tier ?? tier}
          </span>
        )}
      </div>
      <div className="p-5">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {cp.approval_confidence && (
            <div className="rounded-xl bg-white border border-indigo-100 px-4 py-3 text-center shadow-sm">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">Approval Confidence</p>
              <p className="text-lg font-bold text-indigo-700">{cp.approval_confidence}</p>
            </div>
          )}
          {(cp.personalized_apr ?? cp.personalized_rate) != null && (
            <div className="rounded-xl bg-white border border-indigo-100 px-4 py-3 text-center shadow-sm">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">
                {isCard ? 'Personalized APR' : 'Your Rate'}
              </p>
              <p className="text-lg font-bold text-indigo-700">
                {((cp.personalized_apr ?? (cp as any).personalized_rate) as number).toFixed(2)}%
              </p>
            </div>
          )}
          {isCard && cp.projected_annual_rewards_value != null && cp.projected_annual_rewards_value > 0 && (
            <div className="rounded-xl bg-white border border-emerald-100 px-4 py-3 text-center shadow-sm">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">Est. Annual Rewards</p>
              <p className="text-lg font-bold text-emerald-700">
                ${cp.projected_annual_rewards_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </p>
            </div>
          )}
          {isCard && cp.net_annual_value != null && (
            <div className="rounded-xl bg-white border border-violet-100 px-4 py-3 text-center shadow-sm">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">Net Annual Value</p>
              <p className={`text-lg font-bold ${cp.net_annual_value >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                {cp.net_annual_value >= 0 ? '+' : ''}${cp.net_annual_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </p>
            </div>
          )}
          {isLoan && cp.estimated_monthly_payment != null && (
            <div className="rounded-xl bg-white border border-indigo-100 px-4 py-3 text-center shadow-sm">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">Est. Monthly Payment</p>
              <p className="text-lg font-bold text-indigo-700">
                ${cp.estimated_monthly_payment.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </p>
            </div>
          )}
          {isLoan && (cp.max_loan_amount ?? (cp as any).max_loan_estimate) != null && (
            <div className="rounded-xl bg-white border border-indigo-100 px-4 py-3 text-center shadow-sm">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">Max Loan Amount</p>
              <p className="text-lg font-bold text-indigo-700">
                ${((cp.max_loan_amount ?? (cp as any).max_loan_estimate) as number).toLocaleString()}
              </p>
            </div>
          )}
          {isCard && cp.balance_transfer_savings != null && cp.balance_transfer_savings > 0 && (
            <div className="rounded-xl bg-white border border-teal-100 px-4 py-3 text-center shadow-sm">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">Balance Transfer Savings</p>
              <p className="text-lg font-bold text-teal-700">
                ${cp.balance_transfer_savings.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </p>
            </div>
          )}
        </div>
        {cp.personalized_pitch && (
          <p className="mt-4 text-sm text-indigo-800 leading-relaxed border-t border-indigo-100 pt-3">{cp.personalized_pitch}</p>
        )}
      </div>
    </div>
  );
}

// ── Communication Preview Panel ───────────────────────────────────────────────

function CommunicationPreviewPanel({
  comm,
  subcategory,
  activeTab,
  onTabChange,
  customerId,
  customerName,
  offerIntelligence,
  personaName,
}: {
  comm: PersonalizedCommunication;
  subcategory?: string;
  activeTab: 'push' | 'email' | 'flyer';
  onTabChange: (t: 'push' | 'email' | 'flyer') => void;
  customerId?: string;
  customerName?: string;
  offerIntelligence?: Record<string, unknown>;
  personaName?: string;
}) {
  const [copied, setCopied] = React.useState(false);

  // Editable content state  -  syncs when comm prop changes (new customer)
  const [localSubject, setLocalSubject] = React.useState(comm.email_content?.subject ?? '');
  const [localBody, setLocalBody] = React.useState(comm.email_content?.body ?? '');
  const [localSms, setLocalSms] = React.useState(comm.sms_text ?? '');
  const [editingSms, setEditingSms] = React.useState(false);
  const [editingEmail, setEditingEmail] = React.useState(false);

  // Send form state
  const [showEmailSend, setShowEmailSend] = React.useState(false);
  const [showSmsSend, setShowSmsSend] = React.useState(false);
  const [recipientEmail, setRecipientEmail] = React.useState('');
  const [recipientPhone, setRecipientPhone] = React.useState('');

  // Async operation state
  const [rephrasing, setRephrasing] = React.useState(false);
  const [sendingEmail, setSendingEmail] = React.useState(false);
  const [sendingSms, setSendingSms] = React.useState(false);

  // Inline notification
  const [toast, setToast] = React.useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };

  // Sync editable fields when a new customer is selected
  React.useEffect(() => {
    setLocalSubject(comm.email_content?.subject ?? '');
    setLocalBody(comm.email_content?.body ?? '');
    setLocalSms(comm.sms_text ?? '');
    setShowEmailSend(false);
    setShowSmsSend(false);
    setEditingEmail(false);
    setEditingSms(false);
    setRecipientEmail('');
    setRecipientPhone('');
    setToast(null);
  }, [comm]);

  const handleCopy = () => {
    let text = '';
    if (activeTab === 'push') text = localSms || (comm.push_notification ?? '');
    else if (activeTab === 'email') text = `${localSubject}\n\n${localBody}`;
    else text = `${comm.flyer_content?.headline ?? ''}\n\n${comm.flyer_content?.body ?? ''}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleRephrase = async () => {
    if (!customerId) { showToast('error', 'Select a customer first'); return; }
    setRephrasing(true);
    try {
      const res = await fetch(`${API_BASE}/api/banking/agent_c/rephrase_offer_content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: customerId,
          persona_name: personaName ?? comm.persona_name ?? '',
          offer_name: String(
            (offerIntelligence as Record<string, unknown>)?.offer_name
            ?? ((offerIntelligence as Record<string, unknown>)?.selected_offer as Record<string, unknown> | undefined)?.offer_name
            ?? comm.offer_id
            ?? ''
          ),
          current_body: localBody,
          tone: 'professional',
        }),
      });
      const data = await res.json();
      if (data.success) {
        if (data.rephrased_body) setLocalBody(data.rephrased_body);
        if (data.rephrased_subject) setLocalSubject(data.rephrased_subject);
        showToast('success', 'Email rephrased successfully');
      } else {
        showToast('error', data.detail ?? 'Rephrase failed');
      }
    } catch {
      showToast('error', 'Rephrase failed  -  check LLM connection');
    } finally {
      setRephrasing(false);
    }
  };

  const handleSendEmail = async () => {
    if (!recipientEmail.trim()) { showToast('error', 'Enter a recipient email'); return; }
    setSendingEmail(true);
    try {
      const res = await fetch(`${API_BASE}/api/banking/agent_c/send_offer_email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: customerId ?? '',
          customer_name: customerName ?? '',
          to_email: recipientEmail.trim(),
          subject: localSubject,
          email_body: localBody,
          offer_intelligence: offerIntelligence ?? {},
          persona_name: personaName ?? comm.persona_name ?? '',
        }),
      });
      const data = await res.json();
      if (data.success) {
        showToast('success', `Email sent to ${recipientEmail.trim()}`);
        setShowEmailSend(false);
        setRecipientEmail('');
      } else {
        showToast('error', data.detail ?? 'Failed to send email');
      }
    } catch {
      showToast('error', 'Send failed  -  check SMTP settings');
    } finally {
      setSendingEmail(false);
    }
  };

  const handleSendSms = async () => {
    if (!recipientPhone.trim()) { showToast('error', 'Enter a phone number'); return; }
    setSendingSms(true);
    try {
      const res = await fetch(`${API_BASE}/api/banking/agent_c/send_offer_sms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: customerId ?? '',
          customer_name: customerName ?? '',
          to_phone: recipientPhone.trim(),
          sms_text: localSms,
        }),
      });
      const data = await res.json();
      if (data.success) {
        showToast('success', `SMS sent to ${recipientPhone.trim()}`);
        setShowSmsSend(false);
        setRecipientPhone('');
      } else {
        showToast('error', data.detail ?? 'Failed to send SMS');
      }
    } catch {
      showToast('error', 'Send failed  -  check Twilio settings');
    } finally {
      setSendingSms(false);
    }
  };

  const isLlm = comm.generation_source === 'llm';
  const gradient = getSubcategoryGradient(subcategory);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
          <Send className="w-3.5 h-3.5 text-white" />
        </div>
        <span className="text-sm font-bold text-slate-800">Email &amp; SMS Outreach</span>
        <span className={`ml-auto text-[10px] uppercase tracking-wide font-semibold px-2 py-0.5 rounded-full border ${
          isLlm
            ? 'text-blue-700 bg-blue-50 border-blue-200'
            : 'text-slate-500 bg-slate-50 border-slate-200'
        }`}>
          {isLlm ? 'AI-generated' : 'Template'}
        </span>
      </div>

      <div>
        {/* Toast notification */}
        {toast && (
          <div className={`flex items-center gap-2 px-3 py-2.5 rounded-xl mb-4 text-sm font-medium ${
            toast.type === 'success'
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            {toast.type === 'success'
              ? <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
              : <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-500" />}
            <span className="flex-1">{toast.msg}</span>
            <button type="button" onClick={() => setToast(null)}>
              <X className="w-3.5 h-3.5 opacity-60 hover:opacity-100" />
            </button>
          </div>
        )}

        {/* ── Email ── */}
        {comm.email_content && (
          <div className="rounded-xl bg-slate-50 overflow-hidden mt-3">
            {/* Header row */}
            <div className="flex items-center gap-2 px-4 py-2.5">
              <Mail className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wide">Email</span>
              <button
                type="button"
                onClick={() => setEditingEmail(!editingEmail)}
                className="ml-auto flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-800"
              >
                <Pencil className="w-3 h-3" />
                {editingEmail ? 'Done' : 'Edit'}
              </button>
            </div>

            {editingEmail ? (
              /* ── Edit mode ── */
              <div className="px-4 pb-3 space-y-2">
                <input
                  type="text"
                  value={localSubject}
                  onChange={(e) => setLocalSubject(e.target.value)}
                  placeholder="Email subject…"
                  className="w-full text-sm font-medium text-slate-800 bg-white border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-blue-400"
                />
                <textarea
                  value={localBody}
                  onChange={(e) => setLocalBody(e.target.value)}
                  rows={6}
                  className="w-full text-sm text-slate-700 leading-relaxed bg-white border border-slate-200 rounded-lg p-3 focus:outline-none focus:border-blue-400 resize-y"
                />
              </div>
            ) : (
              /* ── Preview mode ── */
              <div className="mx-4 mb-3 rounded-xl overflow-hidden border border-slate-200 bg-white shadow-sm">
                {/* Mini email chrome */}
                <div className="bg-gradient-to-r from-slate-700 to-slate-800 px-4 py-2.5 flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-400/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-400/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-400/80" />
                  </div>
                  <span className="text-[10px] text-slate-400 font-medium ml-1">Meridian Bank · Personalized Offer</span>
                </div>
                {/* From / Subject */}
                <div className="px-4 pt-3 pb-2 space-y-1.5 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide w-10 shrink-0">From</span>
                    <span className="text-xs text-slate-600">offers@meridianbank.com</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide w-10 shrink-0">Subj</span>
                    <span className="text-xs font-semibold text-slate-800 truncate">{localSubject || '(no subject)'}</span>
                  </div>
                </div>
                {/* Body preview */}
                <div className="px-4 py-3">
                  <p className="text-sm text-slate-700 leading-relaxed line-clamp-4 whitespace-pre-line">{localBody}</p>
                  {localBody && localBody.length > 200 && (
                    <button
                      type="button"
                      onClick={() => setEditingEmail(true)}
                      className="text-[11px] text-blue-600 hover:text-blue-800 font-medium mt-1"
                    >
                      Read more…
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="px-4 pb-3 flex items-center gap-2 flex-wrap">
              <button
                type="button"
                onClick={handleRephrase}
                disabled={rephrasing}
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 border border-indigo-300 text-indigo-700 bg-white hover:bg-indigo-50 disabled:opacity-50 rounded-lg transition-colors"
              >
                {rephrasing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                {rephrasing ? 'Rephrasing…' : 'Rephrase'}
              </button>
              <button
                type="button"
                onClick={() => setShowEmailSend(!showEmailSend)}
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <Send className="w-3.5 h-3.5" />
                Send Email
              </button>
            </div>

            {showEmailSend && (
              <div className="px-4 pb-4 pt-2 border-t border-slate-200">
                <p className="text-[11px] font-semibold text-slate-500 mb-1.5">Recipient email address</p>
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="customer@example.com"
                    value={recipientEmail}
                    onChange={(e) => setRecipientEmail(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSendEmail(); }}
                    className="flex-1 text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-blue-400 min-w-0 bg-white"
                  />
                  <button
                    type="button"
                    onClick={handleSendEmail}
                    disabled={sendingEmail || !recipientEmail.trim()}
                    className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors whitespace-nowrap"
                  >
                    {sendingEmail ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    {sendingEmail ? 'Sending…' : 'Send Now'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── SMS ── */}
        {localSms && (
          <div className="rounded-xl bg-slate-50 overflow-hidden mt-3">
            <div className="flex items-center gap-2 px-4 py-2.5">
              <Phone className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wide">SMS</span>
              <button
                type="button"
                onClick={() => setEditingSms(!editingSms)}
                className="ml-auto flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-800"
              >
                <Pencil className="w-3 h-3" />
                {editingSms ? 'Done' : 'Edit'}
              </button>
            </div>
            <div className="px-4 pb-3">
              {editingSms ? (
                <textarea
                  value={localSms}
                  onChange={(e) => setLocalSms(e.target.value)}
                  rows={3}
                  maxLength={160}
                  className="w-full text-sm text-slate-700 bg-white border border-slate-200 rounded-lg p-2 focus:outline-none focus:border-blue-400 resize-none"
                />
              ) : (
                <p className="text-sm text-slate-700 leading-relaxed">{localSms}</p>
              )}
              {editingSms && (
                <p className="text-[11px] text-slate-400 text-right mt-1">{localSms.length}/160</p>
              )}
              <div className="mt-2.5">
                <button
                  type="button"
                  onClick={() => setShowSmsSend(!showSmsSend)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <Phone className="w-3.5 h-3.5" />
                  Send SMS
                </button>
              </div>
            </div>
            {showSmsSend && (
              <div className="px-4 pb-4 pt-2 border-t border-slate-200">
                <p className="text-[11px] font-semibold text-slate-500 mb-1.5">Recipient phone number</p>
                <div className="flex gap-2">
                  <input
                    type="tel"
                    placeholder="+91 98765 43210"
                    value={recipientPhone}
                    onChange={(e) => setRecipientPhone(e.target.value)}
                    className="flex-1 text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-blue-400 min-w-0 bg-white"
                  />
                  <button
                    type="button"
                    onClick={handleSendSms}
                    disabled={sendingSms || !recipientPhone.trim()}
                    className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors whitespace-nowrap"
                  >
                    {sendingSms ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    {sendingSms ? 'Sending…' : 'Send'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Goal hint + copy */}
        <div className="flex items-center justify-between mt-3">
          {comm.financial_goal_hint ? (
            <p className="text-xs text-slate-500">
              Tailored for: <span className="font-medium text-emerald-700">{comm.financial_goal_hint}</span>
            </p>
          ) : <span />}
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
          >
            {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function BankingAgentC() {
  const [ui, setUi] = useSessionStorageState<BankingAgentCUiState>(AGENT_C_UI_KEY, DEFAULT_AGENT_C_UI);
  const { offerScope, churnRiskView, selectedCustomerId, pendingCustomerId, lastResult, explainOpen, selectedPersonaId, activeCommTab, offerScoreOpen, personaCommTab } = ui;
  const offerCardRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  // Set immediately on Unpin click so PinnedOfferCard disappears right away instead
  // of waiting on the DELETE + refetch round-trip. Holds the customer_id it applies
  // to, cleared once the refetch confirming the clear actually lands.
  const [optimisticallyUnpinnedOfferId, setOptimisticallyUnpinnedOfferId] = useState<string | null>(null);
  useEffect(() => {
    setOptimisticallyUnpinnedOfferId(null);
  }, [selectedCustomerId]);

  // Deep link from other pages (e.g. Dashboard's "View in Offer & Ad Spend" button):
  // ?persona=<cluster_id> selects that persona in the offer scope and lets the
  // existing scroll-to-offer effect below carry it into view. Also sets the
  // persona: marker directly so the offer computes immediately, matching persona
  // mode's own segment-picker behavior (no separate customer selection step).
  const [searchParams, setSearchParams] = useSearchParams();
  useEffect(() => {
    const personaParam = searchParams.get('persona');
    if (!personaParam) return;
    setUi((p) => ({ ...p, offerScope: 'persona', selectedPersonaId: personaParam, selectedCustomerId: `persona:${personaParam}` }));
    const next = new URLSearchParams(searchParams);
    next.delete('persona');
    setSearchParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // Scroll to offer card once a best offer has actually been computed  -  for
  // either mode, since persona mode's "Compute Best Offer" button (see the segment
  // picker below) sets selectedCustomerId to a `persona:` marker and shares this
  // same effect with Customer mode's search-driven selection.
  useEffect(() => {
    if (!selectedCustomerId) return;
    const t = setTimeout(() => offerCardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 400);
    return () => clearTimeout(t);
  }, [selectedCustomerId]);

  const { data: customersData, isError: customersError, isSuccess: customersSuccess, isLoading: customersLoading } = useQuery({
    queryKey: ['banking-agent-a-customers', 5000],
    queryFn: async () => {
      // Full table, not a capped page  -  the search box below does its own
      // client-side name/ID matching, so a cap silently hides every same-name
      // customer past it (e.g. only 1 of 4 "Aaron Brown" rows would ever be
      // searchable). Matches the limit BankingAgentD already uses.
      const res = await fetch(`${API_BASE}/api/banking/agent_a/customers?limit=5000`);
      if (!res.ok) throw new Error('Failed to fetch customers');
      return res.json();
    },
    retry: false,
  });

  const customers = useMemo(() => {
    return (customersData?.data?.customers ?? []) as Array<{
      customer_id: string;
      customer_name: string;
      persona?: string;
      total_deposits?: number;
      digital_engagement?: number;
      channel_preference?: string;
      recent_life_event?: string;
    }>;
  }, [customersData]);

  // Persona mode never picks a real customer  -  selectedCustomerId carries a
  // `persona:<id>` marker instead, set as soon as a segment is chosen. This branch
  // is what actually swaps in the segment-wide endpoint for that case.
  const personaMarkerId = selectedCustomerId?.startsWith('persona:') ? selectedCustomerId.slice('persona:'.length) : null;

  // Director's Pin/Unpin buttons always operate on a real customer_id under the
  // hood, even when Director itself is in "By persona" mode (it auto-selects a
  // representative customer from the segment, same as here). The persona-best-
  // offer computation itself stays purely segment-aggregate (no representative-
  // customer input) - this is only used to show/unpin an informational "Director
  // pinned this" card when it happens to match. Mirrors Recommender's identical
  // personaRepQuery.
  const personaRepQuery = useQuery({
    queryKey: ['banking-agent-c-persona-rep', personaMarkerId],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE}/api/banking/agent_a/customers?cluster_id=${encodeURIComponent(personaMarkerId ?? '')}&limit=1&skip=0`
      );
      if (!res.ok) return { data: { customers: [] } };
      return res.json();
    },
    enabled: !!personaMarkerId,
    staleTime: 60_000,
  });
  const personaRepCustomerId = String(
    (personaRepQuery.data?.data?.customers?.[0] as { customer_id?: string } | undefined)?.customer_id ?? ''
  ).trim();
  // The real customer_id Director's Pin/Unpin buttons actually operate on for
  // this selection - the persona: marker in persona mode, a real id in customer
  // mode. Anything that needs to read or invalidate this customer's pin status
  // (the query below, and unpinOfferMutation further down) must use THIS, never
  // selectedCustomerId directly - using selectedCustomerId in persona mode would
  // target a `banking-agent-d-pins` cache entry keyed by the persona: marker
  // string, which nothing else (including Director's own pinsQuery) ever reads.
  const offerPinsTargetId = personaMarkerId ? personaRepCustomerId : selectedCustomerId;

  const {
    data: offerData,
    isLoading: offerLoading,
    isFetching: offerFetching,
    isSuccess: offerIsSuccess,
    dataUpdatedAt: offerDataUpdatedAt,
    refetch: refetchOffer,
  } = useQuery({
    queryKey: ['banking-one-best-offer', selectedCustomerId],
    queryFn: () => fetchOneBestOffer(API_BASE, selectedCustomerId),
    // selectedCustomerId is only ever set by an explicit "Get Best Offer"/"Compute
    // Best Offer" click (see the customer- and persona-mode buttons below), or by a
    // deep link from another tab that wants an immediate compute  -  never just from
    // picking a customer/persona in this tab's own pickers. So `enabled` here is
    // already the on-demand trigger; no separate Recompute control is needed
    // elsewhere, since clicking the same button again re-fires this query (either
    // because selectedCustomerId changes, or via the buttons' explicit refetch()
    // call when it doesn't).
    enabled: !!selectedCustomerId,
    // Inherit the app-wide QueryClient default (App.tsx: staleTime: Infinity,
    // refetchOnMount: false)  -  navigating to this tab, or away and back, must show
    // whatever was last computed, not trigger a fresh (LLM-backed, several-second)
    // computation every time.
    //
    // Seeded from the sessionStorage-mirrored last result (see the "on new
    // success" effect below) so a plain reload shows it immediately with no
    // network call  -  selectedCustomerId survives a reload via sessionStorage,
    // but the in-memory QueryClient cache does not, so without this seed
    // `enabled: !!selectedCustomerId` would fire a fresh fetch the instant the
    // component mounts. An in-flight-at-the-exact-moment-of-reload request is
    // not resumed  -  the JS execution context was destroyed by the reload.
    initialData: () =>
      lastResult?.customerId === selectedCustomerId && selectedCustomerId ? lastResult.response : undefined,
  });

  // Runs once per newly-landed successful result (dataUpdatedAt changes exactly
  // then)  -  useQuery has no onSuccess callback in this TanStack Query version.
  // Seeded from the query's OWN dataUpdatedAt at mount (not 0), so resuming an
  // already-cached/initialData-seeded result on a fresh mount doesn't look like
  // a "new" result and doesn't re-fire the sessionStorage write below.
  const lastHandledOfferAtRef = useRef(offerDataUpdatedAt);
  useEffect(() => {
    if (!offerIsSuccess || offerDataUpdatedAt === lastHandledOfferAtRef.current) return;
    lastHandledOfferAtRef.current = offerDataUpdatedAt;
    if (selectedCustomerId) {
      setUi((prev) => ({ ...prev, lastResult: { customerId: selectedCustomerId, response: offerData } }));
    }
  }, [offerIsSuccess, offerDataUpdatedAt, offerData, selectedCustomerId]);

  // Pinning can only be originated from the Director tab now  -  this tab only offers
  // Unpin (via PinnedOfferCard below), scoped to Offer only, independent of
  // Recommender's own pin (each reads its own field server-side; see
  // api/main_unified_chromadb.py). Refetch the offer on success so it reflects the
  // cleared pin immediately.
  const unpinOfferMutation = useMutation({
    mutationFn: async (targetCustomerId: string) => {
      const res = await fetch(
        `${API_BASE}/api/banking/agent_d/pin/offer/${encodeURIComponent(targetCustomerId)}`,
        { method: 'DELETE' }
      );
      if (!res.ok) throw new Error('Failed to unpin');
      return res.json();
    },
    onSuccess: () => {
      // offerPinsTargetId, NOT selectedCustomerId - in persona mode selectedCustomerId
      // is the `persona:<id>` marker, not the real customer_id Director's own pinsQuery
      // (and this tab's own offerPinsStatusQuery) are actually keyed by. Invalidating
      // the wrong key here was why Director's toggle never flipped back to "Pin" after
      // unpinning from this tab in persona mode.
      void queryClient.invalidateQueries({ queryKey: ['banking-agent-d-pins', offerPinsTargetId] });
      // Wait for the refetch to actually land before clearing the optimistic hide,
      // so the card doesn't flash back to "pinned" between clearing the flag and
      // the fresh (unpinned) data arriving.
      void refetchOffer().finally(() => setOptimisticallyUnpinnedOfferId(null));
    },
  });

  const churnQueriesEnabled = customersSuccess && (customersData?.data?.customers?.length ?? 0) > 0;

  const { data: churnHighData, isPending: churnHighPending } = useQuery({
    queryKey: ['banking-churn-cohort', 'High,Critical', 10, 'desc'],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE}/api/banking/churn-cohort?${new URLSearchParams({
          risk: 'High,Critical',
          limit: '10',
          skip: '0',
          order: 'desc',
        })}`
      );
      if (!res.ok) return { cohort: [], total: 0 };
      return res.json();
    },
    enabled: churnQueriesEnabled,
  });

  const { data: churnLowData, isPending: churnLowPending } = useQuery({
    queryKey: ['banking-churn-cohort', 'Low', 10, 'asc'],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE}/api/banking/churn-cohort?${new URLSearchParams({
          risk: 'Low',
          limit: '10',
          skip: '0',
          order: 'asc',
        })}`
      );
      if (!res.ok) return { cohort: [], total: 0 };
      return res.json();
    },
    enabled: churnQueriesEnabled,
  });

  const churnCohortLoading = churnHighPending || churnLowPending;

  const { data: churnByPersonaData } = useQuery({
    queryKey: ['banking-churn-by-persona', 'High,Critical'],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE}/api/banking/agent_c/churn-by-persona?risk=${encodeURIComponent('High,Critical')}`
      );
      if (!res.ok) return { segments: [] };
      return res.json();
    },
    enabled: customersSuccess && (customersData?.data?.customers?.length ?? 0) > 0,
  });

  const { data: personasData } = useQuery({
    queryKey: ['banking-personas'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/personas`);
      if (!res.ok) throw new Error('Failed to fetch personas');
      return res.json();
    },
    enabled: customersSuccess && (customersData?.data?.customers?.length ?? 0) > 0,
  });

  const personas = (personasData?.personas ?? []) as Array<{ id: string; name: string; size: number; percentage?: number }>;

  const offer = offerData?.data as OneBestOfferPayload | undefined;

  // Manual pin toggled from Director  -  this tab's own offer query deliberately
  // inherits the app-wide staleTime: Infinity/refetchOnMount: false (see offerData's
  // useQuery comment above), so a Director-originated pin wouldn't otherwise show up
  // here until the user explicitly recomputes. Poll/refetch aggressively (same
  // options as Director's own pinsQuery) purely to DETECT a mismatch  -  never to
  // auto-trigger a fetch (that's a background auto-compute, which is never
  // allowed here); a passive banner below "Get Best Offer" tells the user a
  // refresh is available instead.
  const offerPinsStatusQuery = useQuery({
    queryKey: ['banking-agent-d-pins', offerPinsTargetId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_d/pins/${encodeURIComponent(String(offerPinsTargetId).trim())}`);
      if (!res.ok) return { recommender_pin_product_id: null as string | null, offer_pin_product_id: null as string | null };
      return res.json();
    },
    enabled: !!offerPinsTargetId,
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
    refetchInterval: 5000,
  });
  // Persona-mode manual pin, checked directly against offerPinsStatusQuery (there's
  // no backend-computed supervisor_pinned field for the segment-aggregate offer -
  // see get_banking_persona_best_offer's docstring: it never takes a customer_id).
  const personaManuallyPinned = Boolean(
    personaMarkerId &&
    offer?.offer?.product_id &&
    offerPinsStatusQuery.data?.offer_pin_product_id === offer.offer.product_id &&
    selectedCustomerId !== optimisticallyUnpinnedOfferId,
  );
  const offerPinChangedSinceCompute = useMemo(() => {
    if (personaMarkerId || !selectedCustomerId) return false;
    if (!offerPinsStatusQuery.isSuccess) return false;
    if (!offer?.offer) return false; // nothing computed yet  -  the next compute picks up the pin naturally
    const pin = String(offerPinsStatusQuery.data?.offer_pin_product_id || '').trim();
    const currentPinnedId = offer.offer.supervisor_pinned ? String(offer.offer.product_id ?? '').trim() : '';
    return currentPinnedId !== pin;
  }, [personaMarkerId, selectedCustomerId, offerPinsStatusQuery.isSuccess, offerPinsStatusQuery.data, offer]);

  const cohortHighRisk = useMemo(
    () => (churnHighData?.cohort ?? []) as ChurnCohortCustomerRow[],
    [churnHighData]
  );
  const cohortLowRisk = useMemo(
    () => (churnLowData?.cohort ?? []) as ChurnCohortCustomerRow[],
    [churnLowData]
  );
  const hasChurnCohortRows = cohortHighRisk.length > 0 || cohortLowRisk.length > 0;

  const churnByPersona = (churnByPersonaData?.segments ?? []) as Array<{
    persona_id: number | string;
    persona_name: string;
    segment_size: number;
    at_risk_count: number;
    high_count: number;
    critical_count: number;
    avg_churn_score_segment: number;
    avg_churn_score_at_risk: number | null;
    top_retention_action?: string;
    retention_strategy: string;
    persona_metrics?: AgentCPersonaMetrics;
  }>;

  function churnReasonText(c: ChurnCohortCustomerRow): string {
    const raw = (c.churn_risk_reason || c.reason || '').trim();
    if (raw) return raw;
    const cat = c.churn_risk_category || 'Elevated';
    const sc = c.churn_risk_score != null ? c.churn_risk_score.toFixed(0) : ' - ';
    return `${cat} risk (${sc}/100): transaction recency, volume trend, balances vs income, product breadth, and digital engagement.`;
  }

  const selectedCustomer = useMemo(
    () => customers.find((c) => c.customer_id === selectedCustomerId),
    [customers, selectedCustomerId]
  );

  // Persona mode has no real customer to display or pin against  -  show the
  // segment's name instead, and pin/unpin (which write to Agent D's per-customer
  // ledger) are hidden entirely rather than acting on a synthetic id.
  const displayCustomerLabel = personaMarkerId
    ? (personas.find((p) => p.id === personaMarkerId)?.name ?? 'Segment')
    : (selectedCustomer?.customer_name ?? selectedCustomerId ?? '');

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">One Best Offer</h1>
        <p className="text-gray-500 text-sm mt-1">Hyper-personalized 1:1 offer per customer with full explainability</p>
      </div>

      <div className="space-y-8">
        {/* One best offer: customer vs persona */}
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08, duration: 0.35 }}
          className="mb-10 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden"
        >
          <div className="px-6 py-5">
            <div className="inline-flex rounded-full border border-slate-200 p-1 bg-white/90 shadow-inner">
              <button
                type="button"
                onClick={() => setUi((p) => ({ ...p, offerScope: 'customer' }))}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
                  offerScope === 'customer'
                    ? 'bg-violet-600 text-white shadow-md'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <User className="w-4 h-4" />
                Customer
              </button>
              <button
                type="button"
                onClick={() => setUi((p) => ({ ...p, offerScope: 'persona' }))}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
                  offerScope === 'persona'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Users className="w-4 h-4" />
                Persona
              </button>
            </div>
          </div>

          <div className="p-6">
            {!customersLoading && (customersError || (customersSuccess && !(customersData?.data?.customers?.length ?? 0))) && (
              <div className="mb-6 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-amber-800 text-sm">
                Run Segmentation and load data first to use Best Offer.
              </div>
            )}

            {offerScope === 'customer' && (
              <>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Select customer</label>
                <CustomerSearchSelect
                  customers={customers}
                  value={pendingCustomerId ?? selectedCustomerId ?? ''}
                  onChange={(id) => setUi((p) => ({ ...p, pendingCustomerId: id }))}
                  loading={customersLoading}
                  emptyListLabel="Run Segmentation and load data first to use Best Offer."
                  placeholder="Search by name or ID..."
                />
                {offerPinChangedSinceCompute && !offerFetching && (
                  <div className="mt-4 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    Pin changed in Director since this was last computed - click Get Best Offer to refresh.
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => {
                    // Falls back to selectedCustomerId so a customer landed on via a
                    // deep link from another tab (which sets selectedCustomerId
                    // directly, bypassing this picker) can still be recomputed by
                    // clicking this button again, without first reselecting them.
                    // Always forces a genuine fresh computation (staleTime: 0 on this
                    // one call) regardless of whether this customer already has
                    // cached data from earlier this session - only switching tabs
                    // shows cached/resumed results; clicking this button never should.
                    const target = pendingCustomerId ?? selectedCustomerId;
                    if (!target) return;
                    setUi((p) => ({ ...p, selectedCustomerId: target, pendingCustomerId: target }));
                    void queryClient.fetchQuery({
                      queryKey: ['banking-one-best-offer', target],
                      queryFn: () => fetchOneBestOffer(API_BASE, target),
                      staleTime: 0,
                    });
                  }}
                  disabled={!(pendingCustomerId ?? selectedCustomerId) || offerFetching}
                  className="mt-4 w-full max-w-xl rounded-xl bg-violet-600 text-white font-semibold px-4 py-3 shadow-sm hover:bg-violet-700 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed transition-colors inline-flex items-center justify-center gap-2"
                >
                  {offerFetching ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Computing...
                    </>
                  ) : (
                    'Get Best Offer'
                  )}
                </button>
                {!selectedCustomerId && (
                  <div className="mt-6 rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/50 p-12 text-center">
                    <Target className="w-14 h-14 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500 font-medium">Select a customer, then click Get Best Offer</p>
                    <p className="text-slate-400 text-sm mt-1">Recommendation, score, reason, and channel plan</p>
                  </div>
                )}
              </>
            )}

            {/* Persona mode: no customer selection step  -  that's what Customer mode
                above is for. Persona mode is segment-wide (aggregate profile + the
                segment's #1 recommended product from Agent B, matching the
                Dashboard's Best Offer card), computed on demand via the button below
                rather than immediately on segment selection. */}
            {offerScope === 'persona' && customersSuccess && (customersData?.data?.customers?.length ?? 0) > 0 && (
              <div className="space-y-4">
                <p className="text-xs text-slate-500">
                  Pick a segment, then click <strong>Compute Best Offer</strong> to see its best offer for the
                  segment as a whole.
                </p>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">Segment (persona)</label>
                  <select
                    value={selectedPersonaId ?? ''}
                    onChange={(e) => {
                      const id = e.target.value || null;
                      setUi((p) => ({ ...p, selectedPersonaId: id, selectedCustomerId: null }));
                    }}
                    className="w-full max-w-xl rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">Select a segment…</option>
                    {personas.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.size} customers)
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={() => {
                    // Always forces a genuine fresh computation - see the customer-
                    // mode button above for why.
                    if (!selectedPersonaId) return;
                    const marker = `persona:${selectedPersonaId}`;
                    setUi((p) => ({ ...p, selectedCustomerId: marker }));
                    void queryClient.fetchQuery({
                      queryKey: ['banking-one-best-offer', marker],
                      queryFn: () => fetchOneBestOffer(API_BASE, marker),
                      staleTime: 0,
                    });
                  }}
                  disabled={!selectedPersonaId || offerFetching}
                  className="w-full max-w-xl rounded-xl bg-indigo-600 text-white font-semibold px-4 py-3 shadow-sm hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed transition-colors inline-flex items-center justify-center gap-2"
                >
                  {offerFetching ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Computing...
                    </>
                  ) : (
                    'Compute Best Offer'
                  )}
                </button>
              </div>
            )}

            {offerScope === 'persona' && (!customersSuccess || (customersData?.data?.customers?.length ?? 0) === 0) && !customersLoading && (
              <p className="text-sm text-slate-500">Load customers from Segmentation to use persona mode.</p>
            )}

            {/* Shared result card  -  populated once selectedCustomerId is set, whether a
                real customer_id from Customer mode's search above, or a `persona:` marker
                set by persona mode's "Compute Best Offer" button above. Kept as a single
                render path so persona mode reuses the exact same computation/markup
                instead of a separate implementation. */}
            {!!selectedCustomerId && (
              <>
                <div className="mt-6">
                  <AnimatePresence mode="wait">
                    {offerLoading || offerFetching ? (
                      <motion.div
                        key="loading"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="rounded-2xl bg-white border border-slate-200 shadow-lg p-12 flex flex-col items-center justify-center min-h-[320px]"
                      >
                        <Loader2 className="w-12 h-12 text-violet-500 animate-spin mb-4" />
                        <p className="text-slate-600 font-medium">
                          Computing best offer for {displayCustomerLabel}...
                        </p>
                      </motion.div>
                    ) : offer?.offer ? (
                      <motion.div
                        ref={offerCardRef}
                        key="offer"
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        transition={{ duration: 0.35 }}
                        className="space-y-6"
                      >
                        {/* Customer mode: offer.offer.supervisor_pinned is backend-computed fresh
                            per compute, straight from the manual pin (this endpoint always applies
                            offer_pin_product_id unconditionally). Persona mode: the segment-aggregate
                            endpoint never takes a customer_id, so there's no supervisor_pinned field -
                            personaManuallyPinned checks the same manual-pin field directly against the
                            segment's representative customer instead (informational only, doesn't
                            rerank which offer is computed for the segment). */}
                        {(personaMarkerId
                          ? personaManuallyPinned
                          : offer.offer.supervisor_pinned && selectedCustomerId !== optimisticallyUnpinnedOfferId) && (
                          <PinnedOfferCard
                            card={{
                              product_id: offer.offer.product_id,
                              product_name: offer.offer.product_name,
                              // Encompass the whole offer, not just the product identity -
                              // same rich source (offer_intelligence.selected_offer) the
                              // OfferHeroCard below already renders from, so the pinned
                              // banner shows the full headline/benefits/terms instead of
                              // a bare title strip.
                              offer_name: offer.offer_intelligence?.selected_offer?.offer_name,
                              headline_value:
                                offer.offer_intelligence?.selected_offer?.content_hero_stat ??
                                offer.offer_intelligence?.selected_offer?.headline_value,
                              content_benefit_1: offer.offer_intelligence?.selected_offer?.content_benefit_1,
                              content_benefit_2: offer.offer_intelligence?.selected_offer?.content_benefit_2,
                              content_benefit_3: offer.offer_intelligence?.selected_offer?.content_benefit_3,
                              terms_summary: offer.offer_intelligence?.selected_offer?.terms_summary,
                              days_remaining: offer.offer_intelligence?.selected_offer?.days_remaining,
                              reason: offer.offer.priority_pin_reason,
                            }}
                            onUnpin={() => {
                              if (!offerPinsTargetId) return;
                              setOptimisticallyUnpinnedOfferId(selectedCustomerId);
                              unpinOfferMutation.mutate(offerPinsTargetId);
                            }}
                            unpinning={unpinOfferMutation.isPending}
                          />
                        )}
                        <div className="rounded-2xl bg-white overflow-hidden">
                          {/* ── Card header: customer + persona ── */}
                          <div className="bg-gradient-to-r from-violet-500/10 via-indigo-500/10 to-blue-500/10 px-6 py-4 border-b border-slate-100">
                            <div className="flex items-start justify-between flex-wrap gap-3">
                              <div>
                                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">One Best Offer</p>
                                <p className="text-xl font-bold text-slate-900 mt-0.5">
                                  {displayCustomerLabel}
                                </p>
                                <p className="text-sm text-slate-500 mt-0.5">{offer.persona}</p>
                              </div>
                              <div className="flex flex-wrap gap-2 mt-1 items-start">
                                {selectedCustomer?.channel_preference && (
                                  <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700">
                                    <Smartphone className="w-3 h-3" />
                                    {selectedCustomer.channel_preference}
                                  </span>
                                )}
                                {selectedCustomer?.recent_life_event && selectedCustomer.recent_life_event !== '' && (
                                  <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-700">
                                    📍 {selectedCustomer.recent_life_event.replace(/_/g, ' ')}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* ── "From Recommender" provenance strip ── */}
                          <div className="px-6 py-2.5 flex items-center flex-wrap gap-2">
                            <ArrowRight className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                            <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">From Recommender:</span>
                            <span className="font-bold text-indigo-900 text-sm">{offer.offer.product_name}</span>
                            {offer.offer.category && (
                              <span className="text-xs text-indigo-400">· {offer.offer.category}</span>
                            )}
                            {offer.agent_b_product_rank != null && (
                              <span className="text-xs bg-indigo-100 text-indigo-600 font-semibold px-2 py-0.5 rounded-full">
                                #{offer.agent_b_product_rank} pick
                              </span>
                            )}
                            <span className="ml-auto text-xs font-semibold text-indigo-500 bg-white border border-indigo-100 px-2 py-0.5 rounded-full">
                              {((offer.score ?? 0) * 100).toFixed(0)}% fit score
                            </span>
                          </div>

                          <div className="p-6 space-y-5">
                            {/* ── Offer Hero Card (always shown; falls back to product spotlight) ── */}
                            {offer.offer_intelligence?.available && offer.offer_intelligence.selected_offer ? (
                              <OfferHeroCard
                                offerIntel={offer.offer_intelligence}
                                productName={offer.offer.product_name}
                                productCategory={offer.offer.category}
                                offerScoreOpen={offerScoreOpen}
                                onToggleScore={() => setUi((p) => ({ ...p, offerScoreOpen: !p.offerScoreOpen }))}
                              />
                            ) : (
                              /* Product spotlight  -  when no active promo exists, show the product big */
                              <div className="rounded-2xl overflow-hidden">
                                <div className={`bg-gradient-to-br ${getSubcategoryGradient(offer.offer.subcategory ?? offer.offer.category)} p-7 relative overflow-hidden`}>
                                  <div className="absolute top-0 right-0 w-48 h-48 rounded-full bg-white/5 -translate-y-12 translate-x-12" />
                                  <div className="absolute bottom-0 left-0 w-32 h-32 rounded-full bg-black/5 translate-y-8 -translate-x-8" />
                                  <p className="relative text-[10px] font-bold uppercase tracking-widest text-white/70 mb-3">
                                    Recommended for you
                                  </p>
                                  <p className="relative text-4xl font-black text-white leading-tight tracking-tight drop-shadow-sm">
                                    {offer.offer.product_name}
                                  </p>
                                  {offer.offer.category && (
                                    <p className="relative text-white/75 text-base font-medium mt-1.5">{offer.offer.category}</p>
                                  )}
                                  <div className="relative mt-4 flex items-center gap-3">
                                    <span className="bg-white/20 border border-white/30 text-white text-sm font-bold px-3 py-1.5 rounded-full">
                                      {((offer.score ?? 0) * 100).toFixed(0)}% match
                                    </span>
                                    <span className="text-white/60 text-xs font-medium">Segment: {offer.persona}</span>
                                  </div>
                                </div>
                                {offer.reason && (
                                  <div className="bg-white px-6 py-4">
                                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">Why this product</p>
                                    <p className="text-sm text-slate-700 leading-relaxed">{offer.reason}</p>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* ── Channel Delivery Card ── */}
                            {(offer.best_channel || (offer.channels ?? []).length > 0) && (
                              <ChannelDeliveryCard
                                bestChannel={offer.best_channel ?? ''}
                                bestChannelReason={offer.best_channel_reason}
                                channels={offer.channels ?? []}
                                offerPreferredChannel={offer.offer_intelligence?.selected_offer?.preferred_channel}
                                customerChannelPref={selectedCustomer?.channel_preference}
                                channelFatigue={(offer as Record<string, unknown>).channel_fatigue as Record<string, { is_fatigued: boolean; sent?: number; consecutive_no_open?: number }> | undefined}
                              />
                            )}


                            {/* ── Agentic Customer Analysis Panel ── */}
                            {Boolean(offer.customer_analysis) && (
                              <CustomerAnalysisPanel analysis={offer.customer_analysis!} />
                            )}


                            {offer.agent_c_vs_agent_b?.recommendations_differ && offer.agent_c_vs_agent_b?.explanation && (
                              <div className="rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50/90 to-indigo-50/50 px-4 py-4 shadow-sm">
                                <div className="flex items-start justify-between gap-2 mb-2">
                                  <p className="text-sm font-bold text-slate-900 flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-blue-600 flex-shrink-0" />
                                    Recommender vs Best Offer
                                  </p>
                                  {offer.agent_c_vs_agent_b.explanation_source === 'llm' && (
                                    <span className="text-[10px] uppercase tracking-wide font-semibold text-blue-700 bg-white/80 border border-blue-100 px-2 py-0.5 rounded-full">
                                      AI explanation
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-slate-600 mb-2">
                                  Recommender ranks products by segment fit; Best Offer picks one best offer for retention and
                                  purchase - shown when they differ.
                                </p>
                                {offer.agent_b_top_products && offer.agent_b_top_products.length > 0 && (
                                  <p className="text-xs text-slate-500 mb-3">
                                    Recommender top matches:{' '}
                                    {offer.agent_b_top_products.map((p, i) => (
                                      <span key={p.product_id ?? i}>
                                        <strong className="text-slate-700">{p.product_name ?? p.product_id}</strong>
                                        {p.score != null && (
                                          <span className="text-slate-400"> ({(p.score * 100).toFixed(0)}%)</span>
                                        )}
                                        {i < (offer.agent_b_top_products?.length ?? 0) - 1 ? ' · ' : ''}
                                      </span>
                                    ))}
                                  </p>
                                )}
                                <p className="text-sm text-slate-800 leading-relaxed">{offer.agent_c_vs_agent_b.explanation}</p>
                              </div>
                            )}
                          </div>

                          {/* ── Credit Personalization Card ── */}
                          {offer.credit_personalization && (
                            <div className="px-6 py-4 border-t border-slate-100">
                              <CreditPersonalizationCard cp={offer.credit_personalization} />
                            </div>
                          )}

                          {/* ── Email & SMS Outreach ── */}
                          {offer.personalized_communication && (offer.personalized_communication.email_content || offer.personalized_communication.sms_text) && (
                            <div className="px-6 py-4 border-t border-slate-100">
                              <CommunicationPreviewPanel
                                comm={offer.personalized_communication}
                                subcategory={offer.offer?.subcategory ?? offer.offer?.category}
                                activeTab="email"
                                onTabChange={(t) => setUi((p) => ({ ...p, activeCommTab: t }))}
                                customerId={selectedCustomerId ?? undefined}
                                customerName={selectedCustomer?.customer_name}
                                offerIntelligence={offer.offer_intelligence as Record<string, unknown>}
                                personaName={offer.persona}
                              />
                            </div>
                          )}

                        </div>
                      </motion.div>
                    ) : (
                      <motion.div
                        ref={offerCardRef}
                        key="no-offer"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="rounded-2xl bg-white border border-slate-200 shadow-lg overflow-hidden"
                      >
                        {/* Header */}
                        <div className="bg-gradient-to-r from-amber-50 via-orange-50 to-white px-6 py-5 border-b border-amber-100 flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-200 flex items-center justify-center flex-shrink-0">
                            <AlertTriangle className="w-5 h-5 text-amber-600" />
                          </div>
                          <div>
                            <p className="font-bold text-slate-900">Manual review recommended</p>
                            <p className="text-sm text-amber-700 mt-0.5">{offer?.reason ?? 'No eligible product passed compliance for this customer.'}</p>
                          </div>
                        </div>
                        <div className="p-6 space-y-4">
                          {/* Best channel  -  still shown so ops knows how to reach the customer */}
                          {offer?.best_channel && (
                            <ChannelDeliveryCard
                              bestChannel={offer.best_channel}
                              bestChannelReason={offer.best_channel_reason}
                              channels={offer.channels ?? []}
                              customerChannelPref={selectedCustomer?.channel_preference}
                              channelFatigue={(offer as Record<string, unknown>).channel_fatigue as Record<string, { is_fatigued: boolean; sent?: number; consecutive_no_open?: number }> | undefined}
                            />
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </>
            )}

          </div>
        </motion.section>

        {/* Churn risk intelligence: hidden from UI */}
        {false && <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.35 }}
          className="mt-14 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden"
        >
          <div className="border-b border-slate-100 bg-gradient-to-r from-amber-50/80 via-white to-indigo-50/40 px-6 py-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2 flex-wrap">
                  <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />
                  Churn risk intelligence
                </h2>
                <p className="text-slate-600 text-sm mt-1 max-w-2xl">
                  <strong className="text-slate-800">Customer</strong>: Two tables  -  up to 10 highest-risk (High/Critical) and up
                  to 10 lowest-risk (Low band), with 1:1 actions.{' '}
                  <strong className="text-slate-800">Persona</strong>: Segment-level churn rollup aligned with the persona list
                  above - use <span className="font-semibold text-indigo-700">Open segment</span> to load that persona in{' '}
                  <strong className="text-slate-800">One best offer</strong>.
                </p>
              </div>
              <div className="inline-flex rounded-full border border-slate-200 p-1 bg-white/90 shadow-inner flex-shrink-0">
                <button
                  type="button"
                  onClick={() => setUi((p) => ({ ...p, churnRiskView: 'customer' }))}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all ${
                    churnRiskView === 'customer'
                      ? 'bg-violet-600 text-white shadow-md'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <User className="w-4 h-4" />
                  Customer
                </button>
                <button
                  type="button"
                  onClick={() => setUi((p) => ({ ...p, churnRiskView: 'persona' }))}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all ${
                    churnRiskView === 'persona'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Users className="w-4 h-4" />
                  Persona
                </button>
              </div>
            </div>
          </div>

          <div className="p-6">
            {!customersLoading && (customersError || (customersSuccess && !(customersData?.data?.customers?.length ?? 0))) && (
              <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-amber-800 text-sm mb-4">
                Run Segmentation and load data to use churn intelligence.
              </div>
            )}

            {customersSuccess && (customersData?.data?.customers?.length ?? 0) > 0 && (
              <>
                {churnRiskView === 'customer' && (
                  <div className="space-y-4">
                    <p className="text-xs text-slate-500 px-1">
                      Two samples from your data: up to 10 <strong className="text-slate-700">High/Critical</strong> (highest
                      scores) and up to 10 <strong className="text-slate-700">Low</strong> (lowest scores). Use{' '}
                      <strong>Show more</strong> where needed.
                    </p>
                    {churnCohortLoading && !hasChurnCohortRows ? (
                      <div className="flex items-center justify-center gap-2 py-10 text-slate-500 text-sm rounded-xl border border-slate-200 bg-white">
                        <Loader2 className="w-5 h-5 animate-spin text-violet-500" />
                        Loading churn samples…
                      </div>
                    ) : (
                      <>
                        <ChurnCohortCustomerTable
                          rows={cohortHighRisk}
                          title="High / Critical risk"
                          description="Highest churn scores  -  prioritize retention and outreach."
                          headerClassName="bg-amber-50/95 border-amber-100"
                          getReasonText={churnReasonText}
                          onGetOffer={(customerId) =>
                            setUi((p) => ({
                              ...p,
                              offerScope: 'customer',
                              churnRiskView: 'customer',
                              selectedCustomerId: customerId,
                            }))
                          }
                        />
                        <ChurnCohortCustomerTable
                          rows={cohortLowRisk}
                          title="Low risk"
                          description="Lowest churn scores in the Low band  -  relationship growth and standard care."
                          headerClassName="bg-emerald-50/95 border-emerald-100"
                          getReasonText={churnReasonText}
                          onGetOffer={(customerId) =>
                            setUi((p) => ({
                              ...p,
                              offerScope: 'customer',
                              churnRiskView: 'customer',
                              selectedCustomerId: customerId,
                            }))
                          }
                        />
                      </>
                    )}
                    {!churnCohortLoading && !hasChurnCohortRows && (
                      <div className="py-12 text-center text-slate-500 text-sm rounded-xl border border-slate-200 bg-white">
                        No churn samples available (need High/Critical and/or Low customers in your data), or churn features are
                        still loading.
                      </div>
                    )}
                  </div>
                )}

                {churnRiskView === 'persona' && (
                  <div className="rounded-xl border border-slate-200 bg-slate-50/30 overflow-hidden">
                    <p className="text-slate-600 text-sm px-4 pt-4 pb-2">
                      Aggregated from customer data (High/Critical bands). Opens the same persona as in <strong>One best offer</strong>{' '}
                      above.
                    </p>
                    <div className="overflow-x-auto px-0 pb-2">
                      <table className="w-full text-sm min-w-[720px]">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200">
                            <th className="text-left py-3 px-4 font-semibold text-slate-700">Persona</th>
                            <th className="text-right py-3 px-4 font-semibold text-slate-700">Size</th>
                            <th className="text-right py-3 px-4 font-semibold text-slate-700">At risk (H/C)</th>
                            <th className="text-right py-3 px-4 font-semibold text-slate-700">Avg score</th>
                            <th className="text-left py-3 px-4 font-semibold text-slate-700 min-w-[140px]">Top action</th>
                            <th className="text-left py-3 px-4 font-semibold text-slate-700 min-w-[280px]">
                              Retention strategy
                            </th>
                            <th className="text-left py-3 px-4 font-semibold text-slate-700">Open</th>
                          </tr>
                        </thead>
                        <tbody>
                          {churnByPersona.map((row) => (
                            <tr
                              key={String(row.persona_id)}
                              className="border-b border-slate-100 hover:bg-white/80 transition-colors bg-white"
                            >
                              <td className="py-3 px-4 font-medium text-slate-900">{row.persona_name}</td>
                              <td className="py-3 px-4 text-right text-slate-600 tabular-nums">{row.segment_size}</td>
                              <td className="py-3 px-4 text-right">
                                <span className="font-semibold text-amber-700 tabular-nums">{row.at_risk_count}</span>
                                <span className="text-slate-400 text-xs ml-1">
                                  ({row.high_count} H · {row.critical_count} C)
                                </span>
                              </td>
                              <td className="py-3 px-4 text-right text-slate-600 text-xs tabular-nums">
                                {row.avg_churn_score_segment}
                                {row.avg_churn_score_at_risk != null ? (
                                  <span className="text-slate-400 block">at-risk {row.avg_churn_score_at_risk}</span>
                                ) : null}
                              </td>
                              <td className="py-3 px-4 text-slate-600 text-xs">
                                {(row.top_retention_action || ' - ').replace(/_/g, ' ')}
                              </td>
                              <td className="py-3 px-4 text-slate-600 align-top max-w-md">
                                <CollapsibleChurnText text={formatRetentionStrategy(row.retention_strategy)} />
                                {row.persona_metrics && (
                                  <p className="mt-2 text-[11px] text-slate-500">
                                    avg 90d txns {row.persona_metrics.avg_txn_count_90d ?? ' - '} | mobile {pct(row.persona_metrics.avg_mobile_share_90d)} |
                                    avg active products {row.persona_metrics.avg_active_products_180d ?? ' - '}
                                  </p>
                                )}
                              </td>
                              <td className="py-3 px-4">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setUi((p) => ({
                                      ...p,
                                      offerScope: 'persona',
                                      selectedPersonaId: String(row.persona_id),
                                    }));
                                  }}
                                  className="inline-flex items-center gap-1 text-indigo-600 font-medium hover:text-indigo-700 text-xs"
                                >
                                  Open segment
                                  <ArrowRight className="w-3.5 h-3.5" />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {churnByPersona.length === 0 && (
                      <div className="py-10 text-center text-slate-500 text-sm">
                        No persona churn rollup yet. Run Segmentation and ensure churn features are available.
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {customersLoading && (
              <div className="flex items-center justify-center gap-2 py-10 text-slate-500 text-sm">
                <Loader2 className="w-5 h-5 animate-spin text-violet-500" />
                Loading customer base…
              </div>
            )}
          </div>
        </motion.section>}
      </div>

      {/* Ad Spend ROI  -  embedded below Best Offer content */}
      <div className="mt-12">
        <BankingAdSpend />
      </div>
    </div>
  );
}

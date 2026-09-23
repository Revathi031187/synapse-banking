import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import PinnedOfferCard, { type PinnedOfferCardData } from '../../components/PinnedOfferCard';
import {
  Search,
  CreditCard,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Star,
  DollarSign,
  ChevronDown,
  Briefcase,
  Wand2,
  RotateCcw,
  Save,
  Target,
  BarChart2,
  User,
  Gift,
  Tag,
  Clock,
} from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';
import { useSessionStorageState } from '../../hooks/useSessionStorageState';
import CustomerSearchSelect from '../../components/CustomerSearchSelect';

/** Banking 12-factor groups  -  mirrors Academy “Product fit / Persona / Social / Freshness” layout */
const FACTOR_WEIGHT_GROUPS: {
  id: string;
  label: string;
  description: string;
  keys: string[];
}[] = [
  {
    id: 'product_value',
    label: 'Product & value fit',
    description:
      'Fees, APY, minimums, and how well the product category matches life stage and financial needs  -  plus cross-sell pairing.',
    keys: ['product_value', 'financial_need_match', 'product_pairing'],
  },
  {
    id: 'persona_eligibility',
    label: 'Persona & eligibility',
    description:
      'Credit, income, and balance requirements, relationship depth with the bank, and product complexity vs customer sophistication.',
    keys: ['eligibility_score', 'relationship_depth', 'complexity_match'],
  },
  {
    id: 'social_quality',
    label: 'Social proof & quality',
    description: 'Product ratings, adoption within the segment, and peer behavior alignment.',
    keys: ['product_rating', 'popularity', 'segment_affinity'],
  },
  {
    id: 'channel_intent',
    label: 'Channel & intent',
    description: 'Digital vs branch fit, cross-sell receptivity, and transaction activity patterns.',
    keys: ['channel_fit', 'intent_score', 'transaction_pattern'],
  },
];

const ALL_BANKING_FACTOR_KEYS = FACTOR_WEIGHT_GROUPS.flatMap((g) => g.keys);

/** Defaults match backend Banking12FactorScorer (sum 100%)  -  always show factors even if API is slow */
const BANKING_DEFAULTS_PERCENT: Record<string, number> = {
  eligibility_score: 22,
  financial_need_match: 18,
  relationship_depth: 13,
  product_value: 13,
  product_pairing: 10,
  channel_fit: 4,
  complexity_match: 4,
  intent_score: 6,
  segment_affinity: 2,
  transaction_pattern: 1,
  product_rating: 4,
  popularity: 3,
};

const DETAILED_CALC_TIER_KEYS: Record<'tier1' | 'tier2' | 'tier3' | 'tier4', string[]> = {
  tier1: ['eligibility_score', 'financial_need_match', 'relationship_depth'],
  tier2: ['product_value', 'product_pairing', 'channel_fit'],
  tier3: ['complexity_match', 'intent_score', 'segment_affinity', 'transaction_pattern'],
  tier4: ['product_rating', 'popularity'],
};

/** Tier caption percentage always reflects the *current* config, not whatever weights happened
 *  to be active when a given recommendation was generated. */
function tierWeightPct(currentPercent: Record<string, number>, tier: keyof typeof DETAILED_CALC_TIER_KEYS): number {
  return DETAILED_CALC_TIER_KEYS[tier].reduce(
    (sum, k) => sum + (Number(currentPercent?.[k]) || 0),
    0
  );
}

/**
 * Recomputes a factor's displayed weight/contribution/calculation string from the *current*
 * config instead of trusting the weight baked into `detailed_calculation` at generation time.
 * Safe because `raw_score` (how well this factor matches, e.g. "Credit: 776 vs 660 required")
 * is independent of weight  -  only the weighted contribution changes when weights change. This
 * guarantees the explanation panel can never show a different weight than the config screen,
 * regardless of what weights were active when the recommendation was actually run.
 */
function liveFactor(
  detailedCalc: any,
  key: string,
  currentPercent: Record<string, number>
): { raw: number; weight: number; score: number; calculation: string; explanation: string } | null {
  const factor = detailedCalc?.[key];
  if (!factor) return null;
  const raw = Number(factor.raw_score) || 0;
  const weight = (Number(currentPercent?.[key]) || 0) / 100;
  const score = raw * weight;
  return {
    raw,
    weight,
    score,
    calculation: `Raw score ${(raw * 100).toFixed(1)}% × ${(weight * 100).toFixed(0)}% weight = ${(score * 100).toFixed(1)}% contribution`,
    explanation: factor.explanation ?? '',
  };
}

const BANKING_FACTOR_LABELS_FALLBACK: Record<string, string> = {
  eligibility_score: 'Eligibility (credit, income, balance)',
  financial_need_match: 'Financial need match',
  relationship_depth: 'Relationship depth & loyalty',
  product_value: 'Product value (fees, APY, min balance)',
  product_pairing: 'Cross-sell / product pairing',
  channel_fit: 'Channel fit (digital vs branch)',
  complexity_match: 'Complexity vs sophistication',
  intent_score: 'Cross-sell intent / receptivity',
  segment_affinity: 'Segment affinity (peer behavior)',
  transaction_pattern: 'Transaction pattern fit',
  product_rating: 'Product rating / quality',
  popularity: 'Popularity in segment',
};

const MATCH_LEVEL_COLORS = {
  'Perfect Match': 'bg-green-100 text-green-800 border-green-300',
  'Great Match': 'bg-blue-100 text-blue-800 border-blue-300',
  'Good Option': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'Consider Alternatives': 'bg-gray-100 text-gray-800 border-gray-300'
};

type BankingAgentBUiState = {
  // Locked to 'rules'  -  the Hybrid ML toggle was removed since rule-based
  // scoring is the only method actually in use; narrowing the type (rather
  // than just no longer rendering a way to change it) means TypeScript itself
  // guarantees nothing can set this to 'logit' again by accident.
  scoringMethod: 'rules';
  mode: 'persona' | 'customer';
  persona: string;
  customerId: string;
  searchQuery: string;
  category: string;
  topN: number;
  expandedExplanations: Record<number, boolean>;
  useAgentDDirectives: boolean;
  factorWeights: Record<string, number>;
  factorLabels: Record<string, string>;
  weightsAccordionOpen: boolean;
  lastAiFactorRationales: Record<string, string>;
  runWeightsAccordionOpen: boolean;
  // Snapshot of the run inputs (JSON-stringified) at the moment "Run" was last
  // explicitly clicked. The run query is only `enabled` when the CURRENT inputs
  // still serialize to this exact value  -  so changing any input (customer, top
  // N, a weight slider, ...) without re-clicking Run structurally cannot trigger
  // a computation. Persists across both SPA navigation and a reload (see
  // mergeAgentBUi), so a resumed/finished run keeps showing without a re-click.
  lastRequestedKey: string | null;
  // Mirror of the last successful run's response, keyed by lastRequestedKey.
  // Seeds executeQuery's initialData so a genuine browser reload shows the last
  // result immediately with no network call  -  without this, lastRequestedKey
  // persisting across a reload (unlike before) would otherwise auto-fire a
  // fresh fetch the instant the component mounts, since the in-memory
  // QueryClient cache (unlike sessionStorage) does not survive a reload.
  lastResult: { key: string; response: unknown } | null;
};

type PriorityPinStory = {
  headline?: string;
  subhead?: string;
  paragraphs?: string[];
  bullets?: string[];
  highlights?: { label: string; value: string }[];
  retention?: string;
  focus_source?: string;
  llm_polished?: boolean;
};

function RichParagraph({ text, className }: { text: string; className?: string }) {
  const parts = text.split(/\*\*/);
  return (
    <p className={className}>
      {parts.map((chunk, i) =>
        i % 2 === 1 ? (
          <strong key={i} className="font-semibold text-slate-900">
            {chunk}
          </strong>
        ) : (
          <span key={i}>{chunk}</span>
        ),
      )}
    </p>
  );
}

/** If rank_explanation still says #2/#3 after a pin, drop that stale header block (backend refresh also fixes this). */
function stripStalePinnedRankIntro(rankExplanation: string | undefined): string {
  if (!rankExplanation) return '';
  const blocks = rankExplanation.split(/\n\n/);
  if (blocks.length < 2) return rankExplanation;
  const head = blocks[0];
  if (/(🥉|#3 Option|#2 Alternative|🥈)/.test(head) && !/(🥇|#1 Recommended)/.test(head)) {
    return blocks.slice(1).join('\n\n');
  }
  return rankExplanation;
}

// Persona mode recommends for a whole segment, so a wider list (5) is more
// useful; single-customer mode is a focused, one-on-one view, so a tighter
// list (3) reads better. Applied whenever mode is set (initial default,
// session restore, and switching modes mid-session).
function topNForMode(mode: 'persona' | 'customer'): number {
  return mode === 'persona' ? 5 : 3;
}

function mergeAgentBUi(saved: Partial<BankingAgentBUiState>, def: BankingAgentBUiState): BankingAgentBUiState {
  return {
    ...def,
    ...saved,
    // lastRequestedKey/lastResult are deliberately NOT reset here (unlike the
    // resets below). This merge function's initializer runs on every fresh
    // mount of this component - including ordinary SPA navigation away from
    // and back to this tab, not just a genuine browser reload (a mounting
    // component instance can't tell the difference from inside this hook).
    // Resetting lastRequestedKey here would wipe an in-progress or just-
    // completed run's resumed state on every tab switch, which is exactly the
    // "show what I left" behavior this tab needs to provide. A genuine reload
    // is handled instead by lastResult seeding executeQuery's initialData
    // (see below), so reload shows the last result with no extra fetch rather
    // than losing it outright.
    // topN is intentionally NOT forced to the mode-appropriate default here -
    // that would silently change it (and therefore recommenderRequestKey) on
    // every plain remount, breaking resumability for anyone who set a
    // non-default Top N before navigating away. The Persona/Customer mode
    // toggle buttons already set topN: topNForMode(mode) explicitly at the
    // point of an actual mode switch, which is the only time it should change.
    weightsAccordionOpen: def.weightsAccordionOpen,
    // Always 'rules'  -  a session-storage value of 'logit' saved before the
    // Hybrid ML toggle was removed would otherwise survive this merge and
    // re-enable dead 'logit'-only branches at runtime despite the narrowed type.
    scoringMethod: 'rules',
    factorWeights: { ...BANKING_DEFAULTS_PERCENT, ...def.factorWeights, ...saved.factorWeights },
    factorLabels: { ...def.factorLabels, ...saved.factorLabels },
    expandedExplanations: saved.expandedExplanations ?? def.expandedExplanations,
    lastAiFactorRationales: { ...def.lastAiFactorRationales, ...saved.lastAiFactorRationales },
  };
}

const DEFAULT_BANKING_AGENT_B_UI: BankingAgentBUiState = {
  scoringMethod: 'rules',
  mode: 'persona',
  persona: '',
  customerId: '',
  searchQuery: '',
  category: '',
  topN: 5,
  expandedExplanations: {},
  useAgentDDirectives: false,
  factorWeights: { ...BANKING_DEFAULTS_PERCENT },
  factorLabels: {},
  weightsAccordionOpen: false,
  lastAiFactorRationales: {},
  runWeightsAccordionOpen: false,
  lastRequestedKey: null,
  lastResult: null,
};

const AGENT_B_UI_KEY = 'banking-agent-b-v1';

// PinnedOfferCard moved to frontend/src/components/PinnedOfferCard.tsx  -  shared
// with the Offer tab so a Director pin looks identical wherever it surfaces.

/** Every input that affects a Recommender run's result  -  the run query's key is
 * derived from a JSON.stringify of exactly this shape (see recommenderRequestKey
 * below), so any change to any of these fields is structurally a different query. */
type RecommenderRunInputs = {
  scoringMethod: 'rules';
  mode: 'persona' | 'customer';
  customerId: string;
  persona: string;
  category: string;
  searchQuery: string;
  topN: number;
  factorWeights: Record<string, number>;
};

/** Standalone fetch for a Recommender run, given an explicit inputs snapshot
 * (rather than closing over live component state)  -  used both by the main
 * run query and by the persona deep-link effect, which needs to await a specific
 * one-off run before it can safely strip its URL params. */
async function fetchRecommenderRun(apiBase: string, inputs: RecommenderRunInputs) {
  let endpoint;
  if (inputs.scoringMethod === 'rules') {
    endpoint = `${apiBase}/api/banking/agent_b/execute`;
  } else {
    // logit  -  scoringMethod is narrowed to 'rules' only, so this is unreachable
    // today, kept only to mirror the shape this replaced.
    endpoint = `${apiBase}/api/banking/agent_b/logit`;
  }

  const requestBody: Record<string, unknown> = {
    search_query: inputs.searchQuery,
    category: inputs.category || null,
    top_n: inputs.topN,
  };

  if (inputs.mode === 'customer') {
    requestBody.customer_id = inputs.customerId;
  } else {
    requestBody.persona = inputs.persona;
  }

  let fwSnapshot: Record<string, number> | undefined;
  if (inputs.scoringMethod === 'rules') {
    requestBody.explain = true;
    fwSnapshot = {};
    ALL_BANKING_FACTOR_KEYS.forEach((k) => {
      const n = Number(inputs.factorWeights[k]);
      fwSnapshot![k] = Number.isFinite(n) ? n : BANKING_DEFAULTS_PERCENT[k] ?? 0;
    });
    requestBody.factor_weights = fwSnapshot;
  }
  // Always request director directives in customer mode  -  the backend silently skips
  // when none exist. Avoids a race where the directives query hasn't resolved yet
  // but the user already clicks Run, causing the tag to be missing intermittently.
  if (inputs.mode === 'customer' && inputs.customerId) {
    requestBody.use_agent_d_directives = true;
  }

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    const detail =
      typeof errBody.detail === 'string'
        ? errBody.detail
        : Array.isArray(errBody.detail)
          ? errBody.detail.map((x: { msg?: string }) => x.msg).join('; ')
          : '';
    throw new Error(
      detail || `Failed to execute Agent B (${inputs.scoringMethod})  -  HTTP ${response.status}`
    );
  }
  const data = await response.json();
  if (inputs.scoringMethod === 'rules') {
    return { ...data, _factorWeightsUsed: fwSnapshot };
  }
  return data;
}

export default function BankingAgentB() {
  const queryClient = useQueryClient();
  const API_BASE_URL = getBankingApiBase();
  const [ui, setUi] = useSessionStorageState(AGENT_B_UI_KEY, DEFAULT_BANKING_AGENT_B_UI, mergeAgentBUi);
  const {
    scoringMethod,
    mode,
    persona,
    customerId,
    searchQuery,
    category,
    topN,
    expandedExplanations,
    useAgentDDirectives,
    factorWeights,
    factorLabels,
    weightsAccordionOpen,
    lastAiFactorRationales,
    runWeightsAccordionOpen,
    lastRequestedKey,
    lastResult,
  } = ui;

  const setFactorWeights = (updater: React.SetStateAction<Record<string, number>>) => {
    setUi((prev) => ({
      ...prev,
      factorWeights: typeof updater === 'function' ? updater(prev.factorWeights) : updater,
    }));
  };
  const setExpandedExplanations = (updater: React.SetStateAction<Record<number, boolean>>) => {
    setUi((prev) => ({
      ...prev,
      expandedExplanations: typeof updater === 'function' ? updater(prev.expandedExplanations) : updater,
    }));
  };

  const [weightsSavedOk, setWeightsSavedOk] = useState<string | null>(null);
  // Set immediately on Unpin click so the button disappears right away instead of
  // waiting on the DELETE + recompute round-trip (which can take several seconds
  // for an LLM-backed rationale run). Cleared once a fresh computation lands.
  const [optimisticallyUnpinnedProductId, setOptimisticallyUnpinnedProductId] = useState<string | null>(null);
  const agentDAutoAppliedRef = React.useRef<string>('');

  const agentDDirectivesQuery = useQuery({
    queryKey: ['banking-agent-d-directives-b', customerId],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE_URL}/api/banking/agent_d/directives/${encodeURIComponent(String(customerId).trim())}`
      );
      if (!res.ok) return { next_visit_directives: null as Record<string, unknown> | null };
      return res.json();
    },
    enabled: mode === 'customer' && !!customerId,
    staleTime: 0,
    gcTime: 5 * 60 * 1000,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
  });

  React.useEffect(() => {
    agentDAutoAppliedRef.current = '';
  }, [customerId]);

  React.useEffect(() => {
    if (mode !== 'customer' || !customerId || !agentDDirectivesQuery.isSuccess) return;
    const pin = (agentDDirectivesQuery.data?.next_visit_directives as { priority_pin_product_id?: string } | null)
      ?.priority_pin_product_id;
    if (!pin || String(pin).trim() === '') return;
    if (agentDAutoAppliedRef.current === customerId) return;
    agentDAutoAppliedRef.current = customerId;
    setUi((prev) => ({ ...prev, useAgentDDirectives: true }));
  }, [
    mode,
    customerId,
    agentDDirectivesQuery.isSuccess,
    agentDDirectivesQuery.data,
  ]);

  // Query to get available personas
  const personasQuery = useQuery({
    queryKey: ['banking-personas'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/personas`);
      if (!response.ok) throw new Error('Failed to fetch personas');
      return response.json();
    },
    staleTime: 60_000,
  });

  const personas = personasQuery.data?.personas || [];

  // Set default persona when personas load
  React.useEffect(() => {
    if (personas.length > 0 && !persona) {
      setUi((prev) => ({ ...prev, persona: personas[0].id }));
    }
  }, [personas, persona]);

  // Query to get customers list (for customer mode)
  // Load even in persona mode so the customer dropdown is ready when switching modes
  const customersQuery = useQuery({
    queryKey: ['banking-customers'],
    queryFn: async () => {
      // Fetch the full customer table (not a capped page)  -  CustomerSearchSelect
      // does its own client-side name/ID matching over whatever it's given, so a
      // capped ?limit here silently hides every same-name customer past the cap
      // (e.g. only 1 of 4 "Aaron Brown" rows would ever be searchable). Matches
      // the limit BankingAgentD already uses for the same search box.
      const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/customers?limit=5000`);
      if (!response.ok) throw new Error('Failed to fetch customers');
      return response.json();
    },
    staleTime: 60_000,
  });

  // Human-readable subject for the "Calculating personalized banking scores
  // for ..." loading message  -  previously interpolated the raw `persona`
  // state (a numeric cluster id, e.g. "0") or just the literal word
  // "customer", giving no indication of who/what was actually being scored.
  const loadingSubjectLabel = useMemo(() => {
    if (mode === 'persona') {
      const p = personas.find((x: { id: string; name?: string }) => x.id === persona);
      return p?.name ?? (persona || 'segment');
    }
    const customersList = customersQuery.data?.data?.customers ?? [];
    const c = customersList.find((x: { customer_id: string; customer_name?: string }) => String(x.customer_id) === String(customerId));
    return c?.customer_name ? `${c.customer_name} (Customer ID: ${customerId})` : `Customer ID: ${customerId}`;
  }, [mode, persona, personas, customerId, customersQuery.data]);

  // Fetch representative customer for the selected persona  -  used to read Director directives in persona mode.
  // Mirrors how Director auto-selects the first customer in a segment.
  const personaRepQuery = useQuery({
    queryKey: ['banking-agent-b-persona-rep', persona],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE_URL}/api/banking/agent_a/customers?cluster_id=${encodeURIComponent(persona)}&limit=1&skip=0`
      );
      if (!res.ok) return { data: { customers: [] } };
      return res.json();
    },
    enabled: mode === 'persona' && !!persona,
    staleTime: 60_000,
  });
  const personaRepCustomerId = String(
    (personaRepQuery.data?.data?.customers?.[0] as { customer_id?: string } | undefined)?.customer_id ?? ''
  ).trim();

  // Manual pin toggled from Director  -  separate from agentDDirectivesQuery's/
  // personaDirectivesQuery's auto-computed priority_pin_product_id (see
  // api/main_unified_chromadb.py: banking_agent_b's use_agent_d_directives
  // merge). Polled/refetched aggressively (same options as Director's own
  // pinsQuery) since Director, not this tab, is the only place a pin can now
  // be set. Covers BOTH modes: Director's Pin/Unpin buttons always operate on
  // a real customer_id under the hood, even when Director itself is in "By
  // persona" mode (it auto-selects the same kind of representative customer
  // this query resolves here via personaRepCustomerId) - so persona mode needs
  // this exact same manual-pin signal, not a different one, to correctly
  // reflect a Director pin/unpin.
  const pinsStatusTargetId = mode === 'persona' ? personaRepCustomerId : customerId;
  const pinsStatusQuery = useQuery({
    queryKey: ['banking-agent-d-pins', pinsStatusTargetId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/agent_d/pins/${encodeURIComponent(pinsStatusTargetId)}`);
      if (!res.ok) return { recommender_pin_product_id: null as string | null, offer_pin_product_id: null as string | null };
      return res.json();
    },
    enabled: !!pinsStatusTargetId,
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
    refetchInterval: 5000,
  });
  const isManuallyPinned = (productId: string | undefined) =>
    !!productId && pinsStatusQuery.data?.recommender_pin_product_id === productId;

  // Directives for persona mode  -  fetched for the representative customer so the Director's offer card
  // can be shown for the matching product in the persona recommendation list.
  const personaDirectivesQuery = useQuery({
    queryKey: ['banking-agent-d-directives-persona', personaRepCustomerId],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE_URL}/api/banking/agent_d/directives/${encodeURIComponent(personaRepCustomerId)}`
      );
      if (!res.ok) return { next_visit_directives: null as Record<string, unknown> | null };
      return res.json();
    },
    enabled: mode === 'persona' && !!personaRepCustomerId,
    staleTime: 0,
    gcTime: 5 * 60 * 1000,
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
  });

  const factorMetaQuery = useQuery({
    queryKey: ['banking-agent-b-factor-meta'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/agent_b/factor-metadata`);
      if (!res.ok) throw new Error('factor-metadata');
      return res.json();
    },
    enabled: scoringMethod === 'rules',
  });

  const factorWeightsQuery = useQuery({
    queryKey: ['banking-agent-b-factor-weights'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/agent_b/factor-weights`);
      if (!res.ok) throw new Error('factor-weights');
      return res.json();
    },
    enabled: scoringMethod === 'rules',
  });

  useEffect(() => {
    if (factorMetaQuery.data?.labels) {
      setUi((prev) => ({
        ...prev,
        factorLabels: factorMetaQuery.data.labels as Record<string, string>,
      }));
    }
  }, [factorMetaQuery.data]);

  useEffect(() => {
    const w = factorWeightsQuery.data?.weights_percent;
    if (w && typeof w === 'object') {
      setFactorWeights((prev) => ({ ...BANKING_DEFAULTS_PERCENT, ...prev, ...(w as Record<string, number>) }));
    }
  }, [factorWeightsQuery.data]);

  const effectiveFactorLabels = useMemo(
    () => ({ ...BANKING_FACTOR_LABELS_FALLBACK, ...factorLabels }),
    [factorLabels]
  );

  const hasAiRunRationales = useMemo(
    () => Object.values(lastAiFactorRationales).some((v) => !!String(v || '').trim()),
    [lastAiFactorRationales]
  );

  const weightsSum = useMemo(() => {
    return ALL_BANKING_FACTOR_KEYS.reduce((s, k) => s + (Number(factorWeights[k]) || 0), 0);
  }, [factorWeights]);
  const weightsValid = weightsSum >= 99 && weightsSum <= 101;

  const saveWeightsMutation = useMutation({
    mutationFn: async () => {
      const weights: Record<string, number> = {};
      ALL_BANKING_FACTOR_KEYS.forEach((k) => {
        const n = Number(factorWeights[k]);
        weights[k] = Number.isFinite(n) ? n : BANKING_DEFAULTS_PERCENT[k] ?? 0;
      });
      const res = await fetch(`${API_BASE_URL}/api/banking/agent_b/factor-weights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weights }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || 'Save failed');
      return j;
    },
    onSuccess: (j) => {
      setWeightsSavedOk(j.message || 'Saved');
      factorWeightsQuery.refetch();
      setTimeout(() => setWeightsSavedOk(null), 4000);
    },
  });

  const aiWeightsMutation = useMutation({
    mutationFn: async (vars: { personaId: number; customerId?: string }) => {
      const body: Record<string, unknown> = { persona_id: vars.personaId };
      if (vars.customerId) body.customer_id = vars.customerId;
      const res = await fetch(`${API_BASE_URL}/api/banking/agent_b/factor-weights/ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || 'AI weights failed');
      return j;
    },
    onSuccess: (j: {
      weights_percent?: Record<string, number>;
      factor_rationales?: Record<string, string>;
    }) => {
      setUi((prev) => ({
        ...prev,
        factorWeights: j.weights_percent ? (j.weights_percent as Record<string, number>) : prev.factorWeights,
        lastAiFactorRationales:
          j.factor_rationales && typeof j.factor_rationales === 'object'
            ? (j.factor_rationales as Record<string, string>)
            : {},
      }));
    },
  });

  const resetWeightsMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/agent_b/factor-weights/reset`, { method: 'POST' });
      if (!res.ok) throw new Error('Reset failed');
      return res.json();
    },
    onSuccess: (j) => {
      setUi((prev) => ({
        ...prev,
        ...(j.weights_percent ? { factorWeights: j.weights_percent as Record<string, number> } : {}),
        lastAiFactorRationales: {},
      }));
      aiWeightsMutation.reset();
      factorWeightsQuery.refetch();
      setWeightsSavedOk(j.message || 'Defaults restored');
      setTimeout(() => setWeightsSavedOk(null), 4000);
    },
  });

  const runAiWeights = () => {
    let personaId = 0;
    if (mode === 'persona' && persona !== '') personaId = Number(persona);
    else if (mode === 'customer' && customerId) {
      const list = customersQuery.data?.data?.customers || [];
      const row = list.find((c: { customer_id: string }) => String(c.customer_id) === String(customerId));
      personaId = row?.cluster_id != null ? Number(row.cluster_id) : 0;
    } else if (personas.length) personaId = Number(personas[0].id);
    if (Number.isNaN(personaId)) personaId = 0;
    aiWeightsMutation.mutate({
      personaId,
      customerId: mode === 'customer' && customerId ? customerId : undefined,
    });
  };

  // Every input that affects a Recommender run, snapshotted together so the run
  // query's key changes exactly when the result would change.
  const recommenderInputs = useMemo<RecommenderRunInputs>(() => ({
    scoringMethod,
    mode,
    customerId,
    persona,
    category,
    searchQuery,
    topN,
    factorWeights,
  }), [scoringMethod, mode, customerId, persona, category, searchQuery, topN, factorWeights]);
  const recommenderRequestKey = useMemo(() => JSON.stringify(recommenderInputs), [recommenderInputs]);

  // Query, not mutation, for the run itself  -  a `useMutation`'s state lives only
  // in this one component instance and is silently dropped if the user navigates
  // away before it resolves (the fetch keeps running server-side, but the result
  // never reaches the UI). A `useQuery` with a stable key is tracked by the
  // shared QueryClient (App.tsx: gcTime: Infinity) regardless of which component
  // is currently mounted, so switching tabs mid-run and coming back shows the
  // finished result (or still-loading state) correctly, and switching back to an
  // already-computed combination shows it instantly with no network call.
  // `enabled` only matches when the CURRENT inputs equal what "Run" was last
  // explicitly clicked for (lastRequestedKey)  -  so this never fires just from
  // changing an input or from remounting with old inputs restored from
  // sessionStorage; only an explicit Run/Recompute click can set that flag.
  const executeQuery = useQuery({
    queryKey: ['banking-agent-b-run', recommenderRequestKey],
    queryFn: () => fetchRecommenderRun(API_BASE_URL, recommenderInputs),
    enabled: lastRequestedKey === recommenderRequestKey,
    // Seeded from the sessionStorage-mirrored last result so a genuine browser
    // reload shows it immediately with no network call, now that
    // lastRequestedKey persists across a reload too (see mergeAgentBUi). An
    // in-flight-at-the-exact-moment-of-reload request is not resumed  -  the JS
    // execution context was destroyed by the reload.
    initialData: () =>
      lastResult?.key === recommenderRequestKey ? lastResult.response : undefined,
  });

  // Runs once per newly-landed successful result (dataUpdatedAt changes exactly
  // then)  -  useQuery has no onSuccess callback in this TanStack Query version.
  // Seeded from the query's OWN dataUpdatedAt at mount (not 0), so resuming an
  // already-cached/initialData-seeded result on a fresh mount doesn't look like
  // a "new" result and doesn't re-fire the invalidate/write below.
  const lastHandledRunAtRef = React.useRef(executeQuery.dataUpdatedAt);
  React.useEffect(() => {
    if (!executeQuery.isSuccess || executeQuery.dataUpdatedAt === lastHandledRunAtRef.current) return;
    lastHandledRunAtRef.current = executeQuery.dataUpdatedAt;
    if (mode === 'customer' && customerId) {
      void queryClient.invalidateQueries({ queryKey: ['banking-agent-d-directives-b', customerId] });
    }
    setOptimisticallyUnpinnedProductId(null);
    setUi((prev) => ({ ...prev, lastResult: { key: recommenderRequestKey, response: executeQuery.data } }));
  }, [executeQuery.isSuccess, executeQuery.dataUpdatedAt, executeQuery.data, mode, customerId, recommenderRequestKey]);

  const lastRunFactorWeights = (executeQuery.data as { _factorWeightsUsed?: Record<string, number> } | undefined)
    ?._factorWeightsUsed ?? null;
  const lastRunWeightsSum = useMemo(() => {
    if (!lastRunFactorWeights) return 0;
    return ALL_BANKING_FACTOR_KEYS.reduce((s, k) => s + (Number(lastRunFactorWeights[k]) || 0), 0);
  }, [lastRunFactorWeights]);

  /** Submits the CURRENT inputs as a run. Always forces a genuine fresh network
   * computation, regardless of whether this exact input combination already has
   * cached data from earlier this session - only switching tabs (enabled/
   * initialData below) shows cached/resumed results; clicking this button never
   * should. staleTime: 0 on this one imperative call overrides the app-wide
   * staleTime: Infinity default, guaranteeing a real fetch every time; it still
   * writes into the same cache entry the reactive executeQuery observes, so the
   * displayed result updates normally once it resolves. */
  const submitRecommenderRun = () => {
    setUi((prev) => ({ ...prev, lastRequestedKey: recommenderRequestKey }));
    void queryClient.fetchQuery({
      queryKey: ['banking-agent-b-run', recommenderRequestKey],
      queryFn: () => fetchRecommenderRun(API_BASE_URL, recommenderInputs),
      staleTime: 0,
    });
  };

  // Pin/unpin are scoped to Recommender only  -  independent of Offer's own
  // pin (each reads its own field server-side; see api/main_unified_chromadb.py).
  // Pinning can only be originated from the Director tab now  -  this tab only offers
  // Unpin (see pinsStatusQuery/manualPinMismatch above for how a Director pin's
  // arrival is surfaced here, and the row button below for why there's no pin half
  // of this anymore).
  const unpinMutation = useMutation({
    mutationFn: async (targetCustomerId: string) => {
      const res = await fetch(
        `${API_BASE_URL}/api/banking/agent_d/pin/recommender/${encodeURIComponent(targetCustomerId)}`,
        { method: 'DELETE' }
      );
      if (!res.ok) throw new Error('Failed to unpin');
      return res.json();
    },
    onSuccess: (_data, targetCustomerId) => {
      void queryClient.invalidateQueries({ queryKey: ['banking-agent-d-directives-b', targetCustomerId] });
      void queryClient.invalidateQueries({ queryKey: ['banking-agent-d-directives-persona'] });
      void queryClient.invalidateQueries({ queryKey: ['banking-agent-d-pins', targetCustomerId] });
      // A direct user action on this tab (not a background auto-trigger), so
      // refreshing the run is still allowed  -  the query is already active
      // (this button only shows once a run exists), so this refetches instantly.
      void queryClient.invalidateQueries({ queryKey: ['banking-agent-b-run', recommenderRequestKey] });
    },
  });

  // Deep link from other pages (e.g. Dashboard's "View in Recommender" button):
  // ?persona=<cluster_id>&category=<type|''> selects persona mode with that
  // persona/category and fires the search immediately, so the page lands
  // already showing computed recommendations instead of just a pre-filled form.
  //
  // The URL params are deliberately NOT stripped until the fetch actually
  // *succeeds* (in the .then() below), not the instant we notice them. This
  // route can genuinely mount twice in a row on this navigation (observed via
  // logging: a first instance starts the request, unmounts before it
  // resolves, and a second instance is what the user actually keeps looking
  // at)  -  stripping the URL eagerly would let that first, doomed attempt
  // "consume" the deep link and leave the surviving instance with nothing.
  // Leaving the URL alone until success means whichever instance is still
  // mounted when a request finally resolves is the one that gets to react to
  // it, and an orphaned attempt simply gets superseded by a retry on the next
  // mount instead of silently swallowing the deep link.
  const [searchParams, setSearchParams] = useSearchParams();
  useEffect(() => {
    const personaParam = searchParams.get('persona');
    if (personaParam === null) return;
    const categoryParam = searchParams.get('category') || '';
    const newTopN = topNForMode('persona');
    setUi((p) => ({ ...p, mode: 'persona', persona: personaParam, category: categoryParam, topN: newTopN }));
    const inputs: RecommenderRunInputs = {
      scoringMethod: 'rules',
      mode: 'persona',
      customerId: '',
      persona: personaParam,
      category: categoryParam,
      searchQuery,
      topN: newTopN,
      factorWeights,
    };
    const key = JSON.stringify(inputs);
    setUi((p) => ({ ...p, lastRequestedKey: key }));
    // fetchQuery dedupes against an already-in-flight fetch for this exact key,
    // which is what protects against this route genuinely mounting twice in a
    // row (observed via logging: a first instance starts the request, unmounts
    // before it resolves, and a second instance is what the user actually keeps
    // looking at)  -  both instances' fetchQuery calls resolve from the SAME
    // underlying request instead of firing a duplicate.
    void queryClient
      .fetchQuery({ queryKey: ['banking-agent-b-run', key], queryFn: () => fetchRecommenderRun(API_BASE_URL, inputs) })
      .then(() => {
        setSearchParams((current) => {
          const next = new URLSearchParams(current);
          next.delete('persona');
          next.delete('category');
          return next;
        }, { replace: true });
      })
      .catch(() => {
        // Leave the URL params in place  -  a genuine backend error will fail
        // the same way on retry, but an orphaned-by-remount attempt gets a
        // real chance to succeed on whichever mount survives.
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fires once per deep link, not on every dependency identity change
  }, [searchParams]);

  // The Recommender never auto-computes. Selecting a customer/persona for the
  // first time, or clicking Run/Recompute, are the only things that trigger a
  // real computation  -  navigating to this tab (or away and back) must show
  // whatever was last computed, exactly as it was left, with no network call.
  //
  // What this effect does is narrower: only CLEAR the stale display when the
  // user actively switches to a *different* customer/persona/mode, so the
  // old selection's numbers don't linger mislabeled under the new selection.
  // It must skip the very first render (mount)  -  otherwise a customer/persona
  // restored from sessionStorage on page load would have its cached results
  // wiped immediately, defeating the "return to the exact state you left"
  // requirement. (An earlier version of this effect also auto-re-ran the
  // computation on every mount/change to guard against a stale-looking
  // mismatch with Agent C's Offer tab  -  that mismatch turned out to be a real
  // scoring bug in banking_12_factor_scorer.py's weight merging, now fixed at
  // the source, so re-running defensively here is no longer needed.)
  const isFirstContextEffect = useRef(true);
  React.useEffect(() => {
    if (isFirstContextEffect.current) {
      isFirstContextEffect.current = false;
      return;
    }
    // No need to explicitly clear the run display here anymore: switching to a
    // different customer/persona/mode changes recommenderRequestKey, which no
    // longer matches lastRequestedKey, so the query's `enabled` gate goes false
    // on its own and nothing from the old selection shows. Only the unrelated
    // per-customer UI bits below need an explicit reset.
    setOptimisticallyUnpinnedProductId(null);
    setUi((prev) => ({
      ...prev,
      lastAiFactorRationales: {},
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: only fire on these three
  }, [customerId, persona, mode]);

  const handleSearch = () => {
    // Validation
    if (mode === 'customer' && !customerId) {
      alert('Please select a customer');
      return;
    }
    if (mode === 'persona' && !persona) {
      alert('Please select a persona');
      return;
    }
    submitRecommenderRun();
  };

  // The query's key already encodes customerId, so data returned for it can
  // only ever be for the current customer  -  no separate mismatch guard needed.
  const executePayload = executeQuery.data;

  const results = executePayload?.results;
  const recommendations = results?.recommendations || [];

  // Neither of these auto-recomputes anymore  -  only an explicit Run/Recompute
  // click may trigger a computation. Instead they derive a plain boolean each
  // render, surfaced as a passive "pin changed - click Run to refresh" banner
  // near the Run button (see JSX below) so the user finds out a refresh is
  // available without one being forced on them.
  //
  // narrativePinMismatch: the auto-computed priority_pin_product_id (from
  // Director's click-tracking / orchestrate) no longer matches the displayed #1.
  const narrativePinMismatch = useMemo(() => {
    if (mode !== 'customer' || !customerId) return false;
    if (!useAgentDDirectives || !agentDDirectivesQuery.isSuccess) return false;
    const pin = String(
      (agentDDirectivesQuery.data?.next_visit_directives as { priority_pin_product_id?: string } | null)
        ?.priority_pin_product_id || '',
    ).trim();
    if (!pin) return false;
    const topId = String(recommendations[0]?.product_id ?? '').trim();
    return topId !== pin;
  }, [mode, customerId, useAgentDDirectives, agentDDirectivesQuery.isSuccess, agentDDirectivesQuery.data, recommendations]);

  // manualPinMismatch: the manual Recommender pin toggled in Director (independent
  // of the auto-computed field above  -  see api/main_unified_chromadb.py's
  // recommender_pin_product_id merge in agent_b/execute) no longer matches.
  const manualPinMismatch = useMemo(() => {
    if (mode !== 'customer' || !customerId) return false;
    if (!pinsStatusQuery.isSuccess) return false;
    if (!executePayload) return false; // nothing computed yet  -  the next Run picks up the pin naturally
    const pin = String(pinsStatusQuery.data?.recommender_pin_product_id || '').trim();
    const pinnedRec = recommendations.find((r: any) => r.supervisor_pinned);
    const currentPinnedId = String(pinnedRec?.product_id ?? '').trim();
    return currentPinnedId !== pin;
  }, [mode, customerId, pinsStatusQuery.isSuccess, pinsStatusQuery.data, executePayload, recommendations]);

  const pinChangedSinceRun = narrativePinMismatch || manualPinMismatch;

  const directivePinReasonUi = String(
    (agentDDirectivesQuery.data as { priority_pin_reason_ui?: string } | undefined)?.priority_pin_reason_ui || '',
  ).trim();

  // In customer mode use the customer-specific directives; in persona mode use the representative's directives.
  const directivePinnedOfferCard = (
    mode === 'customer'
      ? (agentDDirectivesQuery.data as { next_visit_directives?: { pinned_offer_card?: PinnedOfferCardData } } | undefined)
          ?.next_visit_directives?.pinned_offer_card
      : (personaDirectivesQuery.data as { next_visit_directives?: { pinned_offer_card?: PinnedOfferCardData } } | undefined)
          ?.next_visit_directives?.pinned_offer_card
  ) ?? null;
  const bankingSupervisorPinReason = (rec: { priority_pin_reason?: string; supervisor_pinned?: boolean }) => {
    const fromRec = typeof rec.priority_pin_reason === 'string' ? rec.priority_pin_reason.trim() : '';
    if (fromRec) return fromRec;
    if (rec.supervisor_pinned && directivePinReasonUi) return directivePinReasonUi;
    return '';
  };
  const insights = results?.insights || {};
  const scoringMethodology = results?.scoring_methodology || results?.algorithm_explanation || {};

  // DEBUG: Check if 12-factor data is in recommendations
  React.useEffect(() => {
    if (recommendations.length > 0) {
      console.log('\n🔍 DEBUGGING BANKING 12-FACTOR DATA IN FRONTEND');
      console.log('='+'='.repeat(79));
      console.log('Number of recommendations:', recommendations.length);
      console.log('\nFirst recommendation data:');
      console.log('  - product_name:', recommendations[0].product_name);
      console.log('  - score:', recommendations[0].score);
      console.log('  - scoring_method:', recommendations[0].scoring_method);
      console.log('  - detailed_calculation exists:', !!recommendations[0].detailed_calculation);
      if (recommendations[0].detailed_calculation) {
        console.log('  - detailed_calculation keys:', Object.keys(recommendations[0].detailed_calculation));
      }
      console.log('='+'='.repeat(79)+'\n');
    }
  }, [recommendations]);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Header  -  Academy-style */}
        <div className="px-6 pt-6 pb-4 flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 border-b border-gray-100">
          <div className="flex gap-3">
            <div className="shrink-0 p-2.5 rounded-xl bg-blue-50 text-blue-600">
              <Target className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Product Recommendations</h1>
              <p className="text-gray-600 mt-1.5 text-sm md:text-base">
                Personalized financial product recommendations using feature-based (12-factor) scoring
              </p>
            </div>
          </div>
          <Link
            to="/banking/macro-dashboard"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-semibold text-sm shadow-md hover:from-violet-700 hover:to-purple-700 transition-all shrink-0"
          >
            <BarChart2 className="w-5 h-5" />
            View Macro Segments
          </Link>
        </div>

        <div className="p-6 space-y-6">
          {/* Operational mode  -  pill toggle */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Mode</p>
            <div className="inline-flex rounded-full border border-gray-200 p-1 bg-gray-50 shadow-inner">
              <button
                type="button"
                onClick={() => setUi((p) => ({ ...p, mode: 'persona', topN: topNForMode('persona') }))}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
                  mode === 'persona'
                    ? 'bg-emerald-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <BarChart2 className="w-4 h-4" />
                Persona Mode
              </button>
              <button
                type="button"
                onClick={() => setUi((p) => ({ ...p, mode: 'customer', topN: topNForMode('customer') }))}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
                  mode === 'customer'
                    ? 'bg-emerald-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <User className="w-4 h-4" />
                Customer Mode
              </button>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-5">
            {mode === 'persona' ? (
              <div className="flex flex-col">
                <label className="block text-sm font-semibold text-gray-800 mb-2">Customer Persona</label>
                <select
                  value={persona}
                  onChange={(e) => setUi((p) => ({ ...p, persona: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={personasQuery.isLoading}
                >
                  {personasQuery.isLoading ? (
                    <option>Loading personas...</option>
                  ) : personas.length === 0 ? (
                    <option>Run Segmentation first</option>
                  ) : (
                    personas.map((p: { id: string; name: string; size?: number; percentage?: number }) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.size?.toLocaleString() ?? 0} customers
                        {p.percentage != null ? `, ${p.percentage.toFixed(1)}%` : ''})
                      </option>
                    ))
                  )}
                </select>
                {personasQuery.isError && (
                  <p className="text-sm text-red-600 mt-2">
                    Could not load personas ({personasQuery.error?.message ?? 'network error'}). Check API is running and
                    CORS/proxy.
                  </p>
                )}
                {personas.length === 0 && !personasQuery.isLoading && !personasQuery.isError && (
                  <p className="text-sm text-amber-700 mt-2">Run Segmentation for named personas, or use the segment fallback from loaded data.</p>
                )}
              </div>
            ) : (
              <div className="flex flex-col">
                <label className="block text-sm font-semibold text-gray-800 mb-2">Select Customer</label>
                <CustomerSearchSelect
                  customers={customersQuery.data?.data?.customers ?? []}
                  value={customerId}
                  onChange={(id) => setUi((p) => ({ ...p, customerId: id }))}
                  loading={customersQuery.isLoading}
                  emptyListLabel="No customers  -  run Segmentation first"
                  placeholder="Search by name or customer ID…"
                />
                {customersQuery.isError && (
                  <p className="text-sm text-red-600 mt-2">
                    Could not load customers ({customersQuery.error?.message ?? 'network error'}).
                  </p>
                )}
              </div>
            )}
            <div className="flex flex-col">
              <label className="block text-sm font-semibold text-gray-800 mb-2">Product Type (optional)</label>
              <select
                value={category}
                onChange={(e) => setUi((p) => ({ ...p, category: e.target.value }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl bg-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All product types</option>
                <option value="Bank Account">Bank Accounts</option>
                <option value="Certificate of Deposit">Certificates of Deposit</option>
                <option value="Credit Card">Credit Cards</option>
                <option value="Loan">Loans</option>
                <option value="Mortgage">Mortgages</option>
                <option value="Investment">Investments</option>
              </select>
            </div>
          </div>

          <div className="grid md:grid-cols-4 gap-4 items-end">
            <div className="md:col-span-3 flex flex-col">
              <label className="block text-sm font-semibold text-gray-800 mb-2">Search query</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setUi((p) => ({ ...p, searchQuery: e.target.value }))}
                placeholder="e.g., mortgage, high-yield savings, credit card, CD…"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex flex-col">
              <label className="block text-sm font-semibold text-gray-800 mb-2">Top N</label>
              <input
                type="number"
                value={topN}
                onChange={(e) => setUi((p) => ({ ...p, topN: parseInt(e.target.value, 10) || 5 }))}
                min={1}
                max={20}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 tabular-nums"
              />
            </div>
          </div>

          {/* Accordion: factor weights  -  rule-based only */}
          {scoringMethod === 'rules' && (
            <div className="rounded-xl border border-gray-200 bg-gray-50/50 overflow-hidden">
              <button
                type="button"
                onClick={() => setUi((p) => ({ ...p, weightsAccordionOpen: !p.weightsAccordionOpen }))}
                className="w-full flex items-center justify-between gap-3 px-4 py-3.5 text-left hover:bg-gray-100/80 transition-colors"
              >
                <span className="font-semibold text-gray-900">Adjust factor weights (optional)</span>
                <ChevronDown
                  className={`w-5 h-5 text-gray-500 shrink-0 transition-transform duration-200 ${
                    weightsAccordionOpen ? 'rotate-180' : ''
                  }`}
                />
              </button>
              {weightsAccordionOpen && (
                <div className="px-4 pb-5 pt-0 border-t border-gray-200 bg-white space-y-4">
                  <p className="text-xs text-gray-600 leading-relaxed pt-3">
                    All factor weights must sum to <strong>100%</strong> before <strong>Submit weights</strong>. Use{' '}
                    <strong className="text-violet-700">AI recommended weights</strong> for a data-driven starting
                    point, then edit any field. Submitted weights apply to the next rule-based run;{' '}
                    <strong>Reset to defaults</strong> restores the standard banking split.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={runAiWeights}
                      disabled={aiWeightsMutation.isPending}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 text-white text-sm font-medium disabled:opacity-50"
                    >
                      {aiWeightsMutation.isPending ? <span className="animate-pulse">…</span> : <Wand2 className="w-4 h-4" />}
                      AI recommended weights
                    </button>
                    <button
                      type="button"
                      onClick={() => weightsValid && saveWeightsMutation.mutate()}
                      disabled={!weightsValid || saveWeightsMutation.isPending}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium disabled:opacity-50"
                    >
                      <Save className="w-4 h-4" />
                      Submit weights
                    </button>
                    <button
                      type="button"
                      onClick={() => resetWeightsMutation.mutate()}
                      disabled={resetWeightsMutation.isPending}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      <RotateCcw className="w-4 h-4" />
                      Reset to defaults
                    </button>
                  </div>
                  {aiWeightsMutation.data?.note && (
                    <p className="text-xs text-violet-900 bg-violet-50 rounded-lg px-3 py-2 border border-violet-100">
                      <strong>{aiWeightsMutation.data?.source === 'llm' ? 'AI' : 'Heuristic'}:</strong>{' '}
                      {aiWeightsMutation.data?.note}
                    </p>
                  )}
                  {hasAiRunRationales && (
                    <div className="rounded-lg border border-violet-200 bg-violet-50/90 px-3 py-2.5 text-xs text-violet-950 leading-relaxed">
                      <p className="font-semibold text-violet-900 mb-1">Factor explanations (review before Submit)</p>
                      <p>
                        Each slider below shows why that share of the 100-point score is justified for this
                        persona/customer, using fields from your data (credit, deposits, engagement, etc.). Adjust any
                        slider, then <strong>Submit weights</strong> when the total is 100%. Request{' '}
                        <strong>AI recommended weights</strong> again to refresh this text.
                      </p>
                    </div>
                  )}
                  {weightsSavedOk && (
                    <p className="text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
                      {weightsSavedOk}
                    </p>
                  )}
                  <div
                    className={`flex items-center justify-between rounded-xl px-4 py-2.5 border ${
                      weightsValid
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                        : 'bg-amber-50 border-amber-200 text-amber-900'
                    }`}
                  >
                    <span className="text-sm font-semibold">Total</span>
                    <span className="text-lg font-bold tabular-nums">
                      {weightsSum.toFixed(1)}%
                      {weightsValid ? (
                        <CheckCircle2 className="inline w-5 h-5 ml-2 text-emerald-600 align-middle" />
                      ) : (
                        <span className="text-xs font-normal ml-2">→ 100% to submit</span>
                      )}
                    </span>
                  </div>

                  <div className="space-y-4">
                    <p className="text-sm text-gray-600 leading-relaxed">
                      <span className="font-medium text-gray-800">Group labels:</span>{' '}
                      {FACTOR_WEIGHT_GROUPS.map((g, i) => (
                        <span key={g.id}>
                          {i > 0 ? <span className="text-gray-300 mx-1">·</span> : null}
                          <a
                            href={`#banking-factor-${g.id}`}
                            className="text-blue-600 hover:text-blue-800 hover:underline"
                            onClick={(e) => {
                              e.preventDefault();
                              document
                                .getElementById(`banking-factor-${g.id}`)
                                ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            }}
                          >
                            {g.label}
                          </a>
                        </span>
                      ))}
                    </p>
                    {FACTOR_WEIGHT_GROUPS.map((g) => (
                      <div
                        key={g.id}
                        id={`banking-factor-${g.id}`}
                        className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm scroll-mt-24"
                      >
                        <h3 className="text-base font-bold text-gray-900">{g.label}</h3>
                        <p className="text-sm text-gray-500 italic mt-1.5 mb-4 leading-relaxed">{g.description}</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-10 gap-y-3">
                          {g.keys.map((key) => (
                            <div
                              key={key}
                              className="min-w-0 border-b border-gray-100 sm:border-0 pb-3 sm:pb-0 last:border-0 space-y-1.5"
                            >
                              <div className="flex items-center justify-between gap-3">
                                <label
                                  className="text-sm font-medium text-gray-800 leading-snug pr-2 min-w-0"
                                  title={key}
                                >
                                  {effectiveFactorLabels[key] || key}
                                </label>
                                <div className="flex items-center gap-1 shrink-0">
                                  <input
                                    type="number"
                                    min={0}
                                    max={100}
                                    step={0.5}
                                    value={
                                      Number.isFinite(Number(factorWeights[key]))
                                        ? Number(factorWeights[key]).toFixed(1)
                                        : String(BANKING_DEFAULTS_PERCENT[key] ?? 0)
                                    }
                                    onChange={(e) => {
                                      const v = parseFloat(e.target.value);
                                      if (!Number.isNaN(v))
                                        setFactorWeights({
                                          ...factorWeights,
                                          [key]: Math.max(0, Math.min(100, v)),
                                        });
                                    }}
                                    className="w-[4.25rem] border border-gray-300 rounded-md px-2 py-1.5 text-right text-sm font-semibold tabular-nums bg-white"
                                  />
                                  <span className="text-sm text-gray-500 w-5">%</span>
                                </div>
                              </div>
                              {String(lastAiFactorRationales[key] || '').trim() !== '' && (
                                <p className="text-[11px] sm:text-xs text-violet-900/95 bg-violet-50/80 border border-violet-100 rounded-md px-2 py-1.5 leading-snug">
                                  {lastAiFactorRationales[key]}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                    <p className="text-xs text-gray-500">
                      Each <strong>Run</strong> sends the current slider values to the scorer.{' '}
                      <strong>Submit weights</strong> also saves them as the server default when no body is sent.
                      After a rule-based run, the <strong>Factor weights used in this run</strong> section below repeats
                      the same rationales for reference.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {pinChangedSinceRun && !executeQuery.isFetching && (
            <div className="mb-3 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              Pin changed in Director since this was last run - click Run to refresh.
            </div>
          )}
          <button
            type="button"
            onClick={handleSearch}
            disabled={executeQuery.isFetching}
            className="w-full px-6 py-3.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:bg-gray-400 flex items-center justify-center gap-2 font-semibold shadow-md transition-colors"
          >
            <Search className="w-5 h-5" />
            {executeQuery.isFetching ? 'Running…' : 'Get personalized banking recommendations'}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {executeQuery.isFetching && (
        <div className="border rounded-lg p-6 text-center bg-blue-50 border-blue-200">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4 border-blue-600"></div>
          <p className="font-medium text-blue-700">
            Calculating personalized banking scores for {loadingSubjectLabel}...
          </p>
        </div>
      )}

      {/* Error State */}
      {executeQuery.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle className="w-6 h-6" />
            <div>
              <p className="font-medium">Error getting recommendations</p>
              <p className="text-sm">{executeQuery.error instanceof Error ? executeQuery.error.message : String(executeQuery.error)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <>
          {/* Success Message & Insights */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3 text-green-700">
                <CheckCircle2 className="w-6 h-6" />
                <div>
                  <p className="font-medium">Found {recommendations.length} personalized banking products</p>
                  <p className="text-sm text-gray-600">
                    {insights.persona_summary || 'Tailored to your financial profile'}
                  </p>
                </div>
              </div>
              <div className={`px-4 py-2 rounded-full text-sm font-semibold ${
                false
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {false
                  ? 'Hybrid ML (50% ML + 50% Banking Rules)'
                  : 'Banking 12-Factor Scoring'}
              </div>
            </div>

            {/* Count cap notice */}
            {results?.count_note && (
              <div className="mb-4 flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-sm text-amber-800">
                <span>⚠</span>
                <span>{results.count_note}</span>
              </div>
            )}

            {/* Banking-Specific Metrics Grid */}
            {(insights || results.metrics) && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Match Quality */}
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
                  <p className="text-xs text-gray-600 mb-1">Match Quality</p>
                  <p className="text-2xl font-bold text-green-600">
                    {results.metrics?.avg_match_score 
                      ? `${results.metrics.avg_match_score.toFixed(1)}%` 
                      : insights?.avg_match_score
                        ? `${insights.avg_match_score.toFixed(1)}%`
                        : insights?.avg_score 
                        ? `${(insights.avg_score * 100).toFixed(1)}%` 
                        : '0%'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Top: {results.metrics?.top_match_score?.toFixed(1) || insights?.max_score ? (insights.max_score * 100).toFixed(1) : '0'}%
                  </p>
                </div>

                {/* Annual Cost */}
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
                  <p className="text-xs text-gray-600 mb-1">Annual Cost</p>
                  <p className="text-2xl font-bold text-blue-600">
                    ${results.metrics?.total_annual_cost?.toFixed(0) || insights?.total_annual_cost?.toFixed(0) || '0'}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    {results.metrics?.free_products || insights?.free_products || 0} free products
                  </p>
                </div>

                {/* Earning Potential */}
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200">
                  <p className="text-xs text-gray-600 mb-1">Earning Potential</p>
                  <p className="text-2xl font-bold text-purple-600">
                    +${results.metrics?.estimated_annual_earnings?.toFixed(0) || insights?.estimated_annual_earnings?.toFixed(0) || '0'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {results.metrics?.earning_products || insights?.earning_products || 0} products @ {results.metrics?.avg_apy?.toFixed(2) || insights?.avg_apy?.toFixed(2) || '0'}% APY
                  </p>
                </div>

                {/* Accessibility */}
                <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-4 border border-orange-200">
                  <p className="text-xs text-gray-600 mb-1">Easy Access</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {results.metrics?.no_minimum_products || insights?.no_minimum_products || 0}/{results.metrics?.total_products || recommendations.length || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    No minimum balance
                  </p>
                </div>
              </div>
            )}

            {/* Value Proposition & Strategy */}
            {(insights.value_proposition || insights.recommendation_strategy) && (
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                {insights.value_proposition && (
                  <p className="text-sm font-semibold text-blue-900 mb-2">
                    {insights.value_proposition}
                  </p>
                )}
                {insights.persona_summary && (
                  <p className="text-xs text-gray-600 italic">
                    {insights.persona_summary}
                  </p>
                )}
              </div>
            )}

            {/* How Hybrid / ML Works (only when Hybrid ML is selected and we have methodology) */}
            {false && (scoringMethodology.formula || scoringMethodology.how_ml_probability_works) && (
              <details className="mt-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                <summary className="cursor-pointer font-semibold text-purple-900 flex items-center gap-2">
                  📐 How the hybrid algorithm works (50% ML + 50% rules)
                </summary>
                <div className="mt-3 space-y-3 text-sm text-gray-700">
                  {scoringMethodology.formula && (
                    <p><span className="font-semibold text-purple-800">Formula:</span> {scoringMethodology.formula}</p>
                  )}
                  {scoringMethodology.short && (
                    <p>{scoringMethodology.short}</p>
                  )}
                  {scoringMethodology.how_ml_probability_works && (
                    <div>
                      <p className="font-semibold text-purple-800 mb-1">How ML probability works</p>
                      <p className="text-gray-600">{scoringMethodology.how_ml_probability_works}</p>
                    </div>
                  )}
                  {scoringMethodology.how_rules_work && (
                    <div>
                      <p className="font-semibold text-blue-800 mb-1">How rules work</p>
                      <p className="text-gray-600">{scoringMethodology.how_rules_work}</p>
                    </div>
                  )}
                  {scoringMethodology.calculation_per_product && (
                    <p className="text-gray-600 italic">{scoringMethodology.calculation_per_product}</p>
                  )}
                </div>
              </details>
            )}
          </div>

          {scoringMethod === 'rules' && lastRunFactorWeights && hasAiRunRationales && (
            <div className="bg-white rounded-lg shadow border border-violet-100 overflow-hidden">
              <button
                type="button"
                onClick={() => setUi((p) => ({ ...p, runWeightsAccordionOpen: !p.runWeightsAccordionOpen }))}
                className="w-full p-6 flex items-start justify-between gap-3 text-left hover:bg-violet-50/40 transition-colors"
              >
                <div>
                  <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <Wand2 className="w-5 h-5 text-violet-600 shrink-0" />
                    Factor weights used in this run
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Total: <strong className="tabular-nums">{lastRunWeightsSum.toFixed(1)}%</strong>  -  same weights as in the
                    suitability breakdown for each product below.
                  </p>
                </div>
                <ChevronDown
                  className={`w-5 h-5 text-gray-500 shrink-0 transition-transform duration-200 ${
                    runWeightsAccordionOpen ? 'rotate-180' : ''
                  }`}
                />
              </button>
              {runWeightsAccordionOpen && (
                <div className="px-6 pb-6 border-t border-violet-100">
                  <div className="mt-4 space-y-3 max-h-[28rem] overflow-y-auto pr-1">
                    {ALL_BANKING_FACTOR_KEYS.map((k) => {
                      const rationale = String(lastAiFactorRationales[k] || '').trim();
                      if (!rationale) return null;
                      return (
                        <div key={k} className="border-b border-gray-100 pb-3 last:border-0">
                          <div className="flex justify-between gap-3 items-baseline">
                            <span className="text-sm font-medium text-gray-800 min-w-0">{effectiveFactorLabels[k] || k}</span>
                            <span className="text-sm font-semibold text-violet-800 tabular-nums shrink-0">
                              {Number(lastRunFactorWeights[k] ?? 0).toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mt-1.5 leading-relaxed">{rationale}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Recommendations List */}
          <div className="space-y-4">
            {recommendations.map((rec: any, index: number) => (
              <div key={rec.product_id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-l-4" style={{
                borderColor: rec.match_level === 'Perfect Match' ? '#10b981' :
                             rec.match_level === 'Great Match' ? '#3b82f6' :
                             rec.match_level === 'Good Option' ? '#f59e0b' : '#6b7280'
              }}>
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-3 mb-2">
                      <span className="text-2xl font-bold text-gray-400">#{index + 1}</span>
                      <h3 className="text-xl font-bold text-gray-900">{rec.product_name}</h3>
                      {/* The only Unpin control for a pinned row is the one inside the
                          "Director's Pinned Offer" card below (PinnedOfferCard) - this row
                          header used to have its own separate small Unpin pill too, which
                          just duplicated that control. */}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <CreditCard className="w-4 h-4" />
                        {rec.category || 'Personal'}
                      </span>
                      {rec.subcategory && (
                        <>
                          <span>•</span>
                          <span>{rec.subcategory}</span>
                        </>
                      )}
                      {rec.min_credit_score > 0 && (
                        <>
                          <span>•</span>
                          <span>Min Credit: {rec.min_credit_score}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900 mb-1">
                      {rec.annual_fee && rec.annual_fee > 0 ? (
                        `$${rec.annual_fee.toFixed(2)}/year`
                      ) : rec.monthly_fee && rec.monthly_fee > 0 ? (
                        <span className="text-amber-600">${rec.monthly_fee.toFixed(2)}/mo</span>
                      ) : (
                        <span className="text-green-600">Free</span>
                      )}
                    </div>
                    {/* JPM product chips */}
                    <div className="flex flex-wrap gap-1 justify-end mt-1">
                      {rec.cash_back_pct > 0 && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">{rec.cash_back_pct}% Cash Back</span>
                      )}
                      {rec.rewards_type === 'travel_points' && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">Travel Rewards</span>
                      )}
                      {rec.intro_apr_months > 0 && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700">0% Intro {rec.intro_apr_months}mo</span>
                      )}
                      {rec.fee_waiver_condition && rec.fee_waiver_condition !== 'none' && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">Fee Waivable</span>
                      )}
                    </div>
                    {rec.interest_rate > 0 && (
                      <div className="text-sm text-green-600 font-semibold mt-1">
                        {rec.interest_rate.toFixed(2)}% APY
                      </div>
                    )}
                    {rec.min_balance > 0 && (
                      <div className="text-xs text-gray-500">
                        Min: ${rec.min_balance.toLocaleString()}
                      </div>
                    )}
                    <div className={`mt-2 px-3 py-1 rounded-full text-xs font-medium border ${MATCH_LEVEL_COLORS[rec.match_level as keyof typeof MATCH_LEVEL_COLORS] || MATCH_LEVEL_COLORS['Consider Alternatives']}`}>
                      {rec.match_level}
                    </div>
                  </div>
                </div>

                {(() => {
                  const pinStory = rec.priority_pin_story as PriorityPinStory | undefined;
                  const pinFallback = bankingSupervisorPinReason(rec);
                  // Optimistic Unpin drops the whole pinned presentation instantly, not just
                  // the small badges  -  otherwise this panel keeps announcing "Supervisor
                  // Priority" for several seconds until the real recompute lands.
                  const effectivePinned = rec.supervisor_pinned && rec.product_id !== optimisticallyUnpinnedProductId;
                  const rankRaw = rec.rank_explanation as string | undefined;
                  const rankBody = effectivePinned ? stripStalePinnedRankIntro(rankRaw) : rankRaw;
                  const showSpotlight = Boolean(effectivePinned && (pinStory || pinFallback));
                  // Pinned narrative lives only in the spotlight  -  skip green “Why” card to avoid repeating the same copy.
                  const showEmerald = Boolean(
                    !effectivePinned &&
                      (rankBody || rec.recommendation_text || pinFallback),
                  );

                  // Is THIS row the one Director manually pinned (recommender_pin_product_id) -
                  // customer mode gets this straight from the backend-computed rec.supervisor_pinned;
                  // persona mode checks the same field directly since supervisor_pinned is never set
                  // there (directives aren't applied to persona-mode scoring).
                  const manuallyPinnedHere =
                    (mode === 'persona' ? isManuallyPinned(rec.product_id) : rec.supervisor_pinned) &&
                    rec.product_id !== optimisticallyUnpinnedProductId;
                  // Card content: prefer directivePinnedOfferCard (orchestrate()'s richer Agent-C
                  // offer snapshot - offer name, headline, benefits) when it happens to match this
                  // exact product, but that's a DIFFERENT backend field from the manual pin (it's
                  // populated by orchestrate()'s own best-offer computation, not by Pin/Unpin) so it
                  // won't always match. Fall back to a minimal card built straight from this row's
                  // own data, which is always correct for whichever product is actually pinned.
                  const showPinnedOffer = manuallyPinnedHere;
                  const pinnedOfferCardData: PinnedOfferCardData | null = showPinnedOffer
                    ? (directivePinnedOfferCard && String(directivePinnedOfferCard.product_id || '') === String(rec.product_id || '')
                        ? directivePinnedOfferCard
                        : { product_id: rec.product_id, product_name: rec.product_name, reason: pinFallback })
                    : null;

                  return (
                    <>
                      {/* Director offer card  -  shown above spotlight for pinned product */}
                      {showPinnedOffer && pinnedOfferCardData && (
                        <PinnedOfferCard
                          card={pinnedOfferCardData}
                          onUnpin={() => {
                            setOptimisticallyUnpinnedProductId(rec.product_id);
                            unpinMutation.mutate(mode === 'persona' ? personaRepCustomerId : customerId);
                          }}
                          unpinning={unpinMutation.isPending}
                        />
                      )}

                      {showSpotlight && (
                        <div className="mb-4 relative overflow-hidden rounded-2xl border border-violet-200/90 bg-gradient-to-br from-violet-50 via-fuchsia-50/50 to-indigo-50 shadow-md ring-1 ring-violet-100/80">
                          <div className="absolute -right-20 -top-20 h-44 w-44 rounded-full bg-fuchsia-200/25 blur-3xl pointer-events-none" />
                          <div className="absolute -left-10 bottom-0 h-32 w-32 rounded-full bg-indigo-200/20 blur-2xl pointer-events-none" />
                          <div className="relative p-5 sm:p-6 space-y-4">
                            <div className="flex flex-wrap items-start gap-4 justify-between">
                              <div className="min-w-0 flex-1">
                                <p className="text-[11px] font-bold uppercase tracking-widest text-violet-700">
                                  Supervisor lead · this customer
                                </p>
                                <h4 className="text-lg sm:text-xl font-bold text-slate-900 mt-1.5 leading-snug">
                                  {pinStory?.headline ?? 'Why this product is listed first'}
                                </h4>
                                {pinStory?.subhead && (
                                  <p className="text-sm text-slate-600 mt-2 leading-relaxed">{pinStory.subhead}</p>
                                )}
                              </div>
                              {pinStory?.highlights && pinStory.highlights.length > 0 && (
                                <div className="flex flex-wrap gap-2 shrink-0">
                                  {pinStory.highlights.map((h) => (
                                    <div
                                      key={h.label}
                                      className="rounded-xl bg-white/90 border border-violet-100 px-3 py-2 shadow-sm min-w-[5.5rem]"
                                    >
                                      <div className="text-[10px] font-semibold uppercase tracking-wide text-violet-600">
                                        {h.label}
                                      </div>
                                      <div className="text-sm font-bold text-slate-900 tabular-nums">{h.value}</div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                            {pinStory?.paragraphs && pinStory.paragraphs.length > 0 ? (
                              <div className="space-y-3 border-t border-violet-100/80 pt-4">
                                {pinStory.paragraphs.map((para, pi) => (
                                  <RichParagraph
                                    key={pi}
                                    text={para}
                                    className="text-sm text-slate-700 leading-relaxed"
                                  />
                                ))}
                              </div>
                            ) : pinFallback ? (
                              <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-line border-t border-violet-100/80 pt-4">
                                {pinFallback}
                              </div>
                            ) : null}
                            {pinStory?.bullets && pinStory.bullets.length > 0 && (
                              <ul className="grid sm:grid-cols-2 gap-2.5 text-sm text-slate-700 pt-1">
                                {pinStory.bullets.map((b) => (
                                  <li key={b} className="flex gap-2 items-start rounded-lg bg-white/50 px-3 py-2 border border-violet-100/60">
                                    <span className="text-violet-600 font-bold shrink-0">✓</span>
                                    <span>{b}</span>
                                  </li>
                                ))}
                              </ul>
                            )}
                            {pinStory?.retention && (
                              <div className="rounded-xl border border-amber-200/90 bg-gradient-to-r from-amber-50 to-orange-50/80 px-4 py-3 text-sm text-amber-950 leading-relaxed shadow-sm">
                                <span className="font-bold text-amber-900">Retention · </span>
                                {pinStory.retention}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {showEmerald && (
                        <div className="mb-4 overflow-hidden rounded-2xl border border-slate-200 shadow-md">
                          {/* ── Header ── */}
                          <div className="bg-gradient-to-r from-slate-800 via-slate-700 to-emerald-800 px-5 py-4">
                            <div className="flex items-center justify-between gap-3">
                              <div className="flex items-center gap-3">
                                {/* Rank circle */}
                                <div className="w-10 h-10 rounded-xl bg-white/15 border border-white/25 flex items-center justify-center shrink-0">
                                  <span className="text-white font-extrabold text-base leading-none">
                                    #{rec.supervisor_pinned ? '1' : (rec.rank || index + 1)}
                                  </span>
                                </div>
                                <div>
                                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-300">
                                    {rec.supervisor_pinned ? 'Supervisor Priority' : 'Why This Product?'}
                                  </p>
                                  <p className="text-white font-bold text-sm leading-snug mt-0.5">
                                    {rec.supervisor_pinned
                                      ? `Position #1 · ${(rec.score * 100).toFixed(1)}% model fit`
                                      : `Rank #${rec.rank || index + 1} · ${(rec.score * 100).toFixed(1)}% compatibility`}
                                  </p>
                                </div>
                              </div>
                              {/* Score pill */}
                              <div className="shrink-0 flex flex-col items-end">
                                <span className="text-2xl font-extrabold text-white tabular-nums leading-none">
                                  {(rec.score * 100).toFixed(0)}%
                                </span>
                                <span className="text-[10px] text-emerald-300 font-semibold uppercase tracking-wide mt-0.5">match</span>
                              </div>
                            </div>
                            {/* Score bar */}
                            <div className="mt-3 h-1.5 rounded-full bg-white/15 overflow-hidden">
                              <div
                                className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-300 transition-all"
                                style={{ width: `${Math.min(rec.score * 100, 100)}%` }}
                              />
                            </div>
                          </div>

                          {/* ── Body ── */}
                          <div className="bg-white px-5 py-4 space-y-4">
                            {rankBody ? (
                              <>
                                {rankBody.split('\n\n').map((section: string, idx: number) => {
                                  const lines = section.split('\n').filter(Boolean);
                                  /* Detect "Key Benefits:" section header */
                                  const isBenefitBlock = lines.some(l => /key benefits/i.test(l));
                                  if (isBenefitBlock) {
                                    const items = lines.filter(l => !/key benefits/i.test(l) && l.trim());
                                    return (
                                      <div key={idx} className="space-y-1.5">
                                        <p className="text-[11px] font-bold uppercase tracking-widest text-slate-500">Key Benefits</p>
                                        <div className="space-y-1.5">
                                          {items.map((item: string, ii: number) => {
                                            const clean = item.replace(/^[-•*]\s*/, '').replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1').trim();
                                            return (
                                              <div key={ii} className="flex items-start gap-2.5 rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2">
                                                <span className="text-emerald-600 font-bold text-sm shrink-0 mt-0.5">✓</span>
                                                <span className="text-sm text-slate-700 leading-snug">{clean}</span>
                                              </div>
                                            );
                                          })}
                                        </div>
                                      </div>
                                    );
                                  }
                                  return (
                                    <div key={idx} className={idx > 0 ? 'pt-3 border-t border-slate-100' : ''}>
                                      {lines.map((line: string, lineIdx: number) => {
                                        const isItalic = line.trim().startsWith('*') && !line.trim().startsWith('**');
                                        const formattedLine = line
                                          .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>')
                                          .replace(/\*(.*?)\*/g, '<em class="text-slate-500 text-xs">$1</em>');
                                        return (
                                          <p
                                            key={lineIdx}
                                            className={isItalic
                                              ? 'text-xs italic text-slate-500 mt-1'
                                              : 'text-sm text-slate-700 leading-relaxed mb-1'}
                                            dangerouslySetInnerHTML={{ __html: formattedLine }}
                                          />
                                        );
                                      })}
                                    </div>
                                  );
                                })}

                                {/* AI Rationale */}
                                {rec.llm_rationale && (
                                  <div className="rounded-xl overflow-hidden border border-violet-200 shadow-sm">
                                    <div className="bg-gradient-to-r from-violet-700 to-indigo-700 px-4 py-2.5 flex items-center gap-2">
                                      <p className="text-[11px] font-bold uppercase tracking-widest text-violet-200">Why this product fits you</p>
                                    </div>
                                    <div className="bg-white px-4 py-3.5">
                                      <p className="text-base font-semibold text-slate-800 leading-relaxed">{rec.llm_rationale}</p>
                                    </div>
                                  </div>
                                )}

                                {/* Footer */}
                                <div className="flex items-center gap-2 pt-3 border-t border-slate-100">
                                  <span className="text-slate-400 text-xs">📐</span>
                                  <p className="text-[11px] text-slate-400 leading-relaxed">
                                    Comprehensive match score based on banking 12 factors (see detailed calculation below).
                                  </p>
                                </div>
                              </>
                            ) : null}
                            {!rankBody && rec.recommendation_text && (
                              <>
                                <p className="text-sm text-slate-700 leading-relaxed">{rec.reason || rec.recommendation_text}</p>
                                <div className="flex items-center gap-2 pt-3 border-t border-slate-100">
                                  <span className="text-slate-400 text-xs">📐</span>
                                  <p className="text-[11px] text-slate-400">Comprehensive match score based on banking 12 factors (see detailed calculation below).</p>
                                </div>
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </>
                  );
                })()}

                {/* Score Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Suitability Score</span>
                    <span className="font-bold text-gray-900">{(rec.score * 100).toFixed(2)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="h-3 rounded-full transition-all"
                      style={{
                        width: `${Math.min(rec.score * 100, 100)}%`,
                        backgroundColor: rec.score > 0.8 ? '#10b981' :
                                       rec.score > 0.65 ? '#3b82f6' :
                                       rec.score > 0.5 ? '#f59e0b' : '#6b7280'
                      }}
                    />
                  </div>
                  
                  {/* AI Explanation - Collapsible */}
                  <div className="mt-3">
                    <button
                      onClick={() => setExpandedExplanations(prev => ({
                        ...prev,
                        [index]: !prev[index]
                      }))}
                      className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
                    >
                      <svg 
                        className="w-4 h-4 transition-transform duration-200" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                        style={{ transform: expandedExplanations[index] ? 'rotate(90deg)' : 'rotate(0deg)' }}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      <span>How is Suitability Score calculated?</span>
                    </button>
                    
                    {expandedExplanations[index] && (
                      <div className="mt-3 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow-sm animate-fadeIn">
                        <div className="space-y-3">
                          <div className="flex items-start gap-2">
                            <div className="bg-blue-600 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">
                              AI
                            </div>
                            <div className="flex-1">
                              {rec.detailed_calculation && rec.scoring_method === '12_factor' ? (() => {
                                /* BANKING 12-FACTOR DETAILED CALCULATION  -  weight/contribution/calculation are
                                   always recomputed from the *current* config (not the weight baked into this
                                   rec at generation time), so this panel can never disagree with the weight
                                   sliders below it. Only raw_score (weight-independent) comes from the backend. */
                                const currentPercent = factorWeightsQuery.data?.weights_percent ?? BANKING_DEFAULTS_PERCENT;
                                const dc = rec.detailed_calculation;
                                const liveTotal = ALL_BANKING_FACTOR_KEYS.reduce(
                                  (sum, k) => sum + (liveFactor(dc, k, currentPercent)?.score ?? 0),
                                  0
                                );
                                return (
                                <div>
                                  <p className="text-xs font-semibold text-indigo-900 mb-3">
                                    Banking 12-Factor Scoring System
                                  </p>

                                  {/* Total Score */}
                                  <div className="mb-3 p-3 bg-white rounded-lg border-2 border-indigo-300">
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs font-bold text-gray-900">Total Suitability Score</span>
                                      <span className="text-lg font-bold text-indigo-600">{(rec.score * 100).toFixed(1)}%</span>
                                    </div>
                                    {Math.abs(rec.score - liveTotal) > 0.005 && (
                                      <p className="mt-2 pt-2 border-t border-indigo-100 text-[11px] text-gray-500">
                                        12-factor weighted subtotal below: <strong>{(liveTotal * 100).toFixed(1)}%</strong>.
                                        The final score above also includes additional qualification/persona-fit
                                        adjustments applied after the 12-factor scoring, not itemized below.
                                      </p>
                                    )}
                                  </div>

                                  {/* TIER 1: Core Banking Criteria */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
                                    <p className="text-xs font-bold text-indigo-900 mb-3">TIER 1: Core Banking Criteria ({tierWeightPct(currentPercent, 'tier1').toFixed(0)}%)</p>

                                    {/* Eligibility Score */}
                                    {liveFactor(dc, 'eligibility_score', currentPercent) && (
                                      <div className="mb-3 pb-3 border-b border-indigo-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">1. Eligibility Score</span>
                                          <span className="text-sm font-bold text-indigo-700">{(liveFactor(dc, 'eligibility_score', currentPercent)!.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          {liveFactor(dc, 'eligibility_score', currentPercent)!.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(liveFactor(dc, 'eligibility_score', currentPercent)!.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            <p className="font-medium text-indigo-700">📐 {liveFactor(dc, 'eligibility_score', currentPercent)!.calculation}</p>
                                            <p className="italic">🧮 Blends how comfortably credit score, income, and balance clear the product's minimums (40% credit / 35% income / 25% balance).</p>
                                            <p>Banking regulators require strict eligibility criteria. 68% of denied applications cite credit/income issues (FDIC). Must be highest weight to ensure compliance and prevent customer frustration.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Financial Need Match */}
                                    {liveFactor(dc, 'financial_need_match', currentPercent) && (
                                      <div className="mb-3 pb-3 border-b border-indigo-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">2. Financial Need Match</span>
                                          <span className="text-sm font-bold text-indigo-700">{(liveFactor(dc, 'financial_need_match', currentPercent)!.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          {liveFactor(dc, 'financial_need_match', currentPercent)!.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(liveFactor(dc, 'financial_need_match', currentPercent)!.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            <p className="font-medium text-indigo-700">📐 {liveFactor(dc, 'financial_need_match', currentPercent)!.calculation}</p>
                                            <p className="italic">🧮 Starts from a neutral 55% baseline, then adjusts for how well the product category fits the customer's age/life stage, rewards preference, fee sensitivity, and goals.</p>
                                            <p>Products must match life stage: Retirees need income products, young professionals need credit building. McKinsey research shows 72% satisfaction comes from need-product alignment.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Relationship Depth */}
                                    {liveFactor(dc, 'relationship_depth', currentPercent) && (
                                      <div className="mb-0">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">3. Relationship Depth</span>
                                          <span className="text-sm font-bold text-indigo-700">{(liveFactor(dc, 'relationship_depth', currentPercent)!.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          {liveFactor(dc, 'relationship_depth', currentPercent)!.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(liveFactor(dc, 'relationship_depth', currentPercent)!.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            <p className="font-medium text-indigo-700">📐 {liveFactor(dc, 'relationship_depth', currentPercent)!.calculation}</p>
                                            <p className="italic">🧮 Combines products already held (out of 8) with tenure with the bank (up to 5 years)  -  more products and longer tenure score higher.</p>
                                            <p>Customers with 3+ products have 92% retention vs 40% for single-product (Bain & Company). Loyalty drives long-term profitability.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}
                                  </div>

                                  {/* TIER 2: Strategic Fit & Product Value */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border border-blue-200">
                                    <p className="text-xs font-bold text-blue-900 mb-3">TIER 2: Strategic Fit & Product Value ({tierWeightPct(currentPercent, 'tier2').toFixed(0)}%)</p>

                                    {/* Product Value - NEW! */}
                                    {liveFactor(dc, 'product_value', currentPercent) && (
                                      <div className="mb-3 pb-3 border-b border-blue-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">4. Product Value</span>
                                          <span className="text-sm font-bold text-blue-700">{(liveFactor(dc, 'product_value', currentPercent)!.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          {liveFactor(dc, 'product_value', currentPercent)!.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(liveFactor(dc, 'product_value', currentPercent)!.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            <p className="font-medium text-indigo-700">📐 {liveFactor(dc, 'product_value', currentPercent)!.calculation}</p>
                                            <p className="italic">🧮 Blends the product's fee level, APY/rate tier, minimum balance, and (for credit/lending) return-on-cost into one value score.</p>
                                            <p>Fee sensitivity drives 45% of account switching (J.D. Power). Products must differentiate on value: fees, APY, min balance, ROI. Higher weight ensures best-value products rise to top.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Product Pairing */}
                                    {liveFactor(dc, 'product_pairing', currentPercent) && (
                                      <div className="mb-3 pb-3 border-b border-blue-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">5. Product Pairing</span>
                                          <span className="text-sm font-bold text-blue-700">{(liveFactor(dc, 'product_pairing', currentPercent)!.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          {liveFactor(dc, 'product_pairing', currentPercent)!.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(liveFactor(dc, 'product_pairing', currentPercent)!.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            <p className="font-medium text-indigo-700">📐 {liveFactor(dc, 'product_pairing', currentPercent)!.calculation}</p>
                                            <p className="italic">🧮 Looks at products the customer already owns and how many commonly pair with this one; more complementary holdings score higher.</p>
                                            <p>Cross-sell increases customer lifetime value 2-3x. Checking+Savings bundles show 85% higher satisfaction (Accenture Banking Study).</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Channel Fit */}
                                    {liveFactor(dc, 'channel_fit', currentPercent) && (
                                      <div className="mb-0">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">6. Channel Fit</span>
                                          <span className="text-sm font-bold text-blue-700">{(liveFactor(dc, 'channel_fit', currentPercent)!.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          {liveFactor(dc, 'channel_fit', currentPercent)!.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(liveFactor(dc, 'channel_fit', currentPercent)!.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            <p className="font-medium text-indigo-700">📐 {liveFactor(dc, 'channel_fit', currentPercent)!.calculation}</p>
                                            <p className="italic">🧮 Compares the customer's digital engagement level against whether this product favors digital self-service or in-branch service.</p>
                                            <p>78% of millennials prefer mobile banking, 65% of 60+ prefer branches (ABA Survey). Channel mismatch causes 30% lower engagement.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}
                                  </div>

                                  {/* TIER 3: Behavioral & Contextual */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                    <p className="text-xs font-bold text-green-900 mb-3">TIER 3: Behavioral & Contextual ({tierWeightPct(currentPercent, 'tier3').toFixed(0)}%)</p>

                                    {['complexity_match', 'intent_score', 'segment_affinity', 'transaction_pattern'].map((factorKey) => {
                                      const factor = liveFactor(dc, factorKey, currentPercent);
                                      if (!factor) return null;

                                      const factorInfo: Record<string, { name: string; why: string; howCalculated: string }> = {
                                        'complexity_match': {
                                          name: 'Complexity Match',
                                          why: 'Complex products (IRAs, CDs) require financial literacy. 40% of customers abandon overly complex products (Deloitte). Matching sophistication prevents drop-off.',
                                          howCalculated: 'Estimates customer sophistication from deposits and digital engagement, then compares it to the product\'s complexity level; closer match scores higher.'
                                        },
                                        'intent_score': {
                                          name: 'Intent Score',
                                          why: 'Cross-sell receptivity varies widely. Targeting high-intent customers improves conversion 3-5x (Salesforce Banking Report).',
                                          howCalculated: 'Uses the customer\'s cross-sell receptivity score as-is  -  no adjustment is applied.'
                                        },
                                        'segment_affinity': {
                                          name: 'Segment Affinity',
                                          why: 'Peer behavior influences 60% of banking decisions. "People like me" social proof drives adoption in homogeneous segments.',
                                          howCalculated: 'Measures what share of customers in the same segment already hold this product; higher peer adoption scores higher.'
                                        },
                                        'transaction_pattern': {
                                          name: 'Transaction Pattern',
                                          why: 'High-frequency transactors need different products than savers. Activity patterns predict product usage and satisfaction.',
                                          howCalculated: 'Buckets monthly transaction volume into high/medium/low/very-low activity, each mapped to a fixed score.'
                                        }
                                      };

                                      return (
                                        <div key={factorKey} className="mb-2 pb-2 border-b border-green-100 last:border-0">
                                          <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-semibold text-gray-900">{factorInfo[factorKey].name}</span>
                                            <span className="text-xs font-bold text-green-700">{(factor.score * 100).toFixed(1)}%</span>
                                          </div>
                                          <div className="text-xs text-gray-700 mb-1">{factor.explanation}</div>
                                          <details className="mt-1">
                                            <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                              Why {(factor.weight * 100).toFixed(0)}%?
                                            </summary>
                                            <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                              <p className="font-medium text-indigo-700">📐 {factor.calculation}</p>
                                              <p className="italic">🧮 {factorInfo[factorKey].howCalculated}</p>
                                              <p>{factorInfo[factorKey].why}</p>
                                            </div>
                                          </details>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {/* TIER 4: Quality Signals */}
                                  <div className="mb-3 p-3 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border border-orange-200">
                                    <p className="text-xs font-bold text-orange-900 mb-3">TIER 4: Quality Signals ({tierWeightPct(currentPercent, 'tier4').toFixed(0)}%)</p>

                                    {['product_rating', 'popularity'].map((factorKey) => {
                                      const factor = liveFactor(dc, factorKey, currentPercent);
                                      if (!factor) return null;

                                      const factorInfo: Record<string, { name: string; why: string; howCalculated: string }> = {
                                        'product_rating': {
                                          name: 'Product Rating',
                                          why: 'Customer satisfaction ratings predict long-term retention. 4.5+ star products have 80% renewal rates vs 55% for 3-star (Banking Satisfaction Index).',
                                          howCalculated: 'Directly converts the product\'s average star rating (out of 5) into a percentage.'
                                        },
                                        'popularity': {
                                          name: 'Popularity',
                                          why: 'Popular products within segments indicate proven value. Adoption rates signal market validation and reduce perceived risk for customers.',
                                          howCalculated: 'Based on segment adoption count  -  over 100 holders scores highest, over 50 scores moderately, fewer scores lower.'
                                        }
                                      };

                                      return (
                                        <div key={factorKey} className="mb-2 pb-2 border-b border-orange-100 last:border-0">
                                          <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-semibold text-gray-900">{factorInfo[factorKey].name}</span>
                                            <span className="text-xs font-bold text-orange-700">{(factor.score * 100).toFixed(1)}%</span>
                                          </div>
                                          <div className="text-xs text-gray-700 mb-1">{factor.explanation}</div>
                                          <details className="mt-1">
                                            <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                              Why {(factor.weight * 100).toFixed(0)}%?
                                            </summary>
                                            <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                              <p className="font-medium text-indigo-700">📐 {factor.calculation}</p>
                                              <p className="italic">🧮 {factorInfo[factorKey].howCalculated}</p>
                                              <p>{factorInfo[factorKey].why}</p>
                                            </div>
                                          </details>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {/* Summary */}
                                  <div className="mt-3 pt-3 border-t-2 border-indigo-300 bg-indigo-50 p-3 rounded-lg">
                                    <p className="text-xs text-gray-700 mb-2">
                                      <span className="font-semibold">📐 Formula:</span> Sum of all 12 weighted factors
                                    </p>
                                    <p className="text-xs font-bold text-indigo-900 mb-2">
                                      Total Score = {(rec.score * 100).toFixed(1)}%
                                    </p>
                                    <p className="text-xs text-gray-600">
                                      All weights sum to 100%. Each percentage is based on banking research, regulatory requirements, and customer behavior studies.
                                    </p>
                                  </div>
                                </div>
                                );
                              })() : false && rec.scoring_breakdown ? (
                                /* HYBRID ML MODEL EXPLANATION */
                                <div>
                                  <p className="text-xs font-semibold text-purple-900 mb-3">
                                    Banking Hybrid Scoring (50% ML + 50% Rules)
                                  </p>
                                  
                                  {/* Final Score */}
                                  <div className="mb-3 p-3 bg-white rounded-lg border-2 border-purple-300">
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs font-bold text-gray-900">Final Score</span>
                                      <span className="text-lg font-bold text-purple-600">{(rec.scoring_breakdown.final_score * 100).toFixed(1)}%</span>
                                    </div>
                                  </div>

                                  {/* ML Contribution */}
                                  <div className="space-y-2 mb-3">
                                    <div className="flex items-center justify-between p-2 bg-purple-100 rounded">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-purple-900">ML Prediction</span>
                                        <span className="text-xs text-purple-700">(50% weight)</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-purple-700">{(rec.scoring_breakdown.ml_probability * 100).toFixed(1)}% →</span>
                                        <span className="text-sm font-bold text-purple-900">{(rec.scoring_breakdown.ml_contribution * 100).toFixed(1)}%</span>
                                      </div>
                                    </div>
                                    
                                    {/* Rule-Based Contribution */}
                                    <div className="flex items-center justify-between p-2 bg-blue-100 rounded">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-blue-900">📐 Banking Rules</span>
                                        <span className="text-xs text-blue-700">(50% weight)</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-blue-700">{(rec.scoring_breakdown.rule_score * 100).toFixed(1)}% →</span>
                                        <span className="text-sm font-bold text-blue-900">{(rec.scoring_breakdown.rule_contribution * 100).toFixed(1)}%</span>
                                      </div>
                                    </div>
                                  </div>

                                  <div className="mt-3 pt-2 border-t border-purple-200">
                                    <p className="text-xs text-gray-700 mb-2">
                                      <span className="font-semibold">Formula:</span> ({(rec.scoring_breakdown.ml_probability * 100).toFixed(1)}% × 0.5) + ({(rec.scoring_breakdown.rule_score * 100).toFixed(1)}% × 0.5) = {(rec.scoring_breakdown.final_score * 100).toFixed(1)}%
                                    </p>
                                    
                                    {/* 12-Factor Breakdown (expandable) */}
                                    {rec.scoring_breakdown?.twelve_factor_breakdown && (
                                      <details className="mt-2 bg-blue-50 p-2 rounded">
                                        <summary className="text-xs font-semibold text-blue-800 cursor-pointer hover:text-blue-900">
                                          View 12-Factor Banking Rules Breakdown (50% component)
                                        </summary>
                                        <div className="mt-2 space-y-1 pl-2 border-l-2 border-blue-300">
                                          {Object.entries(rec.scoring_breakdown.twelve_factor_breakdown).filter(([key]) => 
                                            !['total_score', 'total_percentage'].includes(key)
                                          ).map(([key, value]: [string, any]) => {
                                            const factorScore = value?.score || 0;
                                            const factorWeight = value?.weight || 0;
                                            return (
                                              <div key={key} className="text-xs">
                                                <span className="text-gray-700">{key.replace(/_/g, ' ')}: </span>
                                                <span className="font-semibold text-blue-800">
                                                  {(factorScore * 100).toFixed(1)}%
                                                </span>
                                                <span className="text-gray-500"> (weight: {(factorWeight * 100).toFixed(0)}%)</span>
                                              </div>
                                            );
                                          })}
                                        </div>
                                      </details>
                                    )}
                                  </div>
                                </div>
                              ) : (
                                /* RULE-BASED EXPLANATION */
                                <div>
                                  <p className="text-xs font-semibold text-blue-900 mb-2">
                                    This score predicts how suitable this banking product is for this customer based on:
                                  </p>
                                  
                                  <div className="space-y-2">
                                    <div className="flex items-start gap-2">
                                      <div className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        25%
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-900">Eligibility Match</p>
                                        <p className="text-xs text-gray-600">Credit score, income, and balance requirements</p>
                                      </div>
                                    </div>
                                    
                                    <div className="flex items-start gap-2">
                                      <div className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        20%
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-900">Financial Need Match</p>
                                        <p className="text-xs text-gray-600">Product features align with customer needs</p>
                                      </div>
                                    </div>
                                    
                                    <div className="flex items-start gap-2">
                                      <div className="bg-purple-100 text-purple-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        15%
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-900">Relationship Depth</p>
                                        <p className="text-xs text-gray-600">Customer tenure and existing products</p>
                                      </div>
                                    </div>
                                    
                                    <div className="flex items-start gap-2">
                                      <div className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        40%
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-900">Other Factors</p>
                                        <p className="text-xs text-gray-600">Behavioral patterns, life stage, profitability potential, etc.</p>
                                      </div>
                                    </div>
                                  </div>
                                  
                                  <div className="mt-3 pt-3 border-t border-blue-200">
                                    <p className="text-xs text-gray-700">
                                      <span className="font-semibold">Banking 12-Factor Formula:</span> Weighted sum of 12 banking-specific factors
                                    </p>
                                    <p className="text-xs text-gray-600 mt-1">
                                      Higher scores indicate products that match customer profile, needs, and financial capacity
                                    </p>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Product Details Grid  -  every condition here must compare with `> 0`,
                    never just truthiness: a legitimately-0 value (no minimum balance, no
                    minimum credit score) is falsy but not boolean `false`, so a bare
                    `value && (<div>...)` renders the literal text "0" instead of nothing
                    once `value` is the only thing left to evaluate. */}
                {(rec.min_balance > 0 || rec.min_credit_score > 0 || rec.interest_rate > 0) && (
                  <div className="grid grid-cols-3 gap-2 mb-4">
                    {rec.min_balance > 0 && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Min Balance</p>
                        <p className="text-sm font-medium text-gray-900">${rec.min_balance.toLocaleString()}</p>
                      </div>
                    )}
                    {rec.min_credit_score > 0 && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Min Credit</p>
                        <p className="text-sm font-medium text-gray-900">{rec.min_credit_score}</p>
                      </div>
                    )}
                    {rec.interest_rate > 0 && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">APY</p>
                        <p className="text-sm font-medium text-gray-900">{rec.interest_rate.toFixed(2)}%</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Recommendation text fallback: shown only if no rank_explanation (unified card above handles both) */}
                {(rec.recommendation_text || rec.reason) && !rec.rank_explanation && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-xs font-semibold text-green-800 mb-2">Why This Product?</p>
                    <div className="text-sm text-gray-800 leading-relaxed">
                      {rec.reason || rec.recommendation_text}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

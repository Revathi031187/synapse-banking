import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
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
  Bot,
} from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';

/** Banking 12-factor groups — mirrors Academy “Product fit / Persona / Social / Freshness” layout */
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
      'Fees, APY, minimums, and how well the product category matches life stage and financial needs — plus cross-sell pairing.',
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

/** Defaults match backend Banking12FactorScorer (sum 100%) — always show factors even if API is slow */
const BANKING_DEFAULTS_PERCENT: Record<string, number> = {
  eligibility_score: 22,
  financial_need_match: 18,
  relationship_depth: 15,
  product_value: 12,
  product_pairing: 9,
  channel_fit: 7,
  complexity_match: 4,
  intent_score: 3,
  segment_affinity: 2,
  transaction_pattern: 1,
  product_rating: 4,
  popularity: 3,
};

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

export default function BankingAgentB() {
  const API_BASE_URL = getBankingApiBase();
  const [scoringMethod, setScoringMethod] = useState<'rules' | 'logit'>('rules'); // Toggle between rule-based and hybrid ML
  const [mode, setMode] = useState<'persona' | 'customer'>('persona'); // Toggle between persona and customer mode
  const [persona, setPersona] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('');
  const [topN, setTopN] = useState(10);
  const [expandedExplanations, setExpandedExplanations] = useState<Record<number, boolean>>({});
  const [useAgentDDirectives, setUseAgentDDirectives] = useState(false);
  const agentDAutoAppliedRef = React.useRef<string>('');

  const agentDDirectivesQuery = useQuery({
    queryKey: ['banking-agent-d-directives-b', customerId],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE_URL}/api/banking/agent_d/directives/${encodeURIComponent(customerId)}`
      );
      if (!res.ok) return { next_visit_directives: null as Record<string, unknown> | null };
      return res.json();
    },
    enabled: mode === 'customer' && !!customerId && scoringMethod === 'rules',
    staleTime: 30_000,
  });

  React.useEffect(() => {
    agentDAutoAppliedRef.current = '';
  }, [customerId]);

  React.useEffect(() => {
    if (
      mode !== 'customer' ||
      !customerId ||
      !agentDDirectivesQuery.isSuccess ||
      scoringMethod !== 'rules'
    )
      return;
    const pin = (agentDDirectivesQuery.data?.next_visit_directives as { priority_pin_product_id?: string } | null)
      ?.priority_pin_product_id;
    if (!pin || String(pin).trim() === '') return;
    if (agentDAutoAppliedRef.current === customerId) return;
    agentDAutoAppliedRef.current = customerId;
    setUseAgentDDirectives(true);
  }, [
    mode,
    customerId,
    scoringMethod,
    agentDDirectivesQuery.isSuccess,
    agentDDirectivesQuery.data,
  ]);
  const [factorWeights, setFactorWeights] = useState<Record<string, number>>(() => ({
    ...BANKING_DEFAULTS_PERCENT,
  }));
  const [factorLabels, setFactorLabels] = useState<Record<string, string>>({});
  const [weightsSavedOk, setWeightsSavedOk] = useState<string | null>(null);
  const [weightsAccordionOpen, setWeightsAccordionOpen] = useState(true);

  // Query to get available personas
  const personasQuery = useQuery({
    queryKey: ['banking-personas'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/personas`);
      if (!response.ok) throw new Error('Failed to fetch personas');
      return response.json();
    }
  });

  const personas = personasQuery.data?.personas || [];

  // Set default persona when personas load
  React.useEffect(() => {
    if (personas.length > 0 && !persona) {
      setPersona(personas[0].id);
    }
  }, [personas, persona]);

  // Query to get customers list (for customer mode)
  const customersQuery = useQuery({
    queryKey: ['banking-customers'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/customers?limit=100`);
      if (!response.ok) throw new Error('Failed to fetch customers');
      return response.json();
    },
    enabled: mode === 'customer'
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
    if (factorMetaQuery.data?.labels) setFactorLabels(factorMetaQuery.data.labels as Record<string, string>);
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

  const resetWeightsMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/agent_b/factor-weights/reset`, { method: 'POST' });
      if (!res.ok) throw new Error('Reset failed');
      return res.json();
    },
    onSuccess: (j) => {
      if (j.weights_percent) setFactorWeights(j.weights_percent);
      factorWeightsQuery.refetch();
      setWeightsSavedOk(j.message || 'Defaults restored');
      setTimeout(() => setWeightsSavedOk(null), 4000);
    },
  });

  const aiWeightsMutation = useMutation({
    mutationFn: async (personaId: number) => {
      const res = await fetch(`${API_BASE_URL}/api/banking/agent_b/factor-weights/ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ persona_id: personaId }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || 'AI weights failed');
      return j;
    },
    onSuccess: (j) => {
      if (j.weights_percent) setFactorWeights(j.weights_percent as Record<string, number>);
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
    aiWeightsMutation.mutate(personaId);
  };

  // Mutation to execute Agent B (supports rule-based and hybrid ML)
  const executeMutation = useMutation({
    mutationFn: async () => {
      let endpoint;
      if (scoringMethod === 'rules') {
        endpoint = `${API_BASE_URL}/api/banking/agent_b/execute`;
      } else { // logit
        endpoint = `${API_BASE_URL}/api/banking/agent_b/logit`;
      }
      
      const requestBody: any = {
        search_query: searchQuery,
        category: category || null,
        top_n: topN
      };

      // Add either customer_id or persona based on mode
      if (mode === 'customer') {
        requestBody.customer_id = customerId;
      } else {
        requestBody.persona = persona;
      }

      // Add explain for rules
      if (scoringMethod === 'rules') {
        requestBody.explain = true;
      }
      if (scoringMethod === 'rules' && mode === 'customer' && customerId && useAgentDDirectives) {
        requestBody.use_agent_d_directives = true;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
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
          detail || `Failed to execute Agent B (${scoringMethod}) — HTTP ${response.status}`
        );
      }
      return response.json();
    }
  });

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
    executeMutation.mutate();
  };

  const results = executeMutation.data?.results;
  const recommendations = results?.recommendations || [];
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
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <div className="max-w-5xl mx-auto bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
        {/* Header — Academy-style */}
        <div className="px-6 pt-6 pb-4 flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 border-b border-gray-100">
          <div className="flex gap-3">
            <div className="shrink-0 p-2.5 rounded-xl bg-blue-50 text-blue-600">
              <Target className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900 tracking-tight">F&M Bank Agent B</h1>
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

        {/* Strategy tabs */}
        <div className="flex border-b border-gray-200 px-2">
          <button
            type="button"
            onClick={() => setScoringMethod('rules')}
            className={`relative px-5 py-3.5 font-semibold text-sm md:text-base transition-all border-b-2 -mb-px flex items-center gap-2 flex-wrap ${
              scoringMethod === 'rules'
                ? 'text-blue-600 border-blue-600 bg-blue-50/50'
                : 'text-gray-500 border-transparent hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            Rule-Based Scoring
            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 text-gray-700 font-medium">
              Banking 12-Factor
            </span>
            {scoringMethod === 'rules' && (
              <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-blue-600 text-white font-bold">
                Current
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => setScoringMethod('logit')}
            className={`relative px-5 py-3.5 font-semibold text-sm md:text-base transition-all border-b-2 -mb-px flex items-center gap-2 flex-wrap ${
              scoringMethod === 'logit'
                ? 'text-purple-600 border-purple-600 bg-purple-50/50'
                : 'text-gray-500 border-transparent hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            Hybrid ML Model
            <span className="text-xs px-2 py-0.5 rounded-full bg-gradient-to-r from-purple-500 to-fuchsia-500 text-white font-medium">
              50% ML + 50% Rules
            </span>
            {scoringMethod === 'logit' && (
              <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-purple-600 text-white font-bold">
                Current
              </span>
            )}
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Operational mode — pill toggle */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Mode</p>
            <div className="inline-flex rounded-full border border-gray-200 p-1 bg-gray-50 shadow-inner">
              <button
                type="button"
                onClick={() => setMode('persona')}
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
                onClick={() => setMode('customer')}
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
                  onChange={(e) => setPersona(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={personasQuery.isLoading}
                >
                  {personasQuery.isLoading ? (
                    <option>Loading personas...</option>
                  ) : personas.length === 0 ? (
                    <option>Run Agent A first</option>
                  ) : (
                    personas.map((p: { id: string; name: string; size?: number; percentage?: number }) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.size?.toLocaleString() ?? 0} customers
                        {p.percentage != null ? `, ${p.percentage.toFixed(1)}%` : ''})
                      </option>
                    ))
                  )}
                </select>
                {personas.length === 0 && !personasQuery.isLoading && (
                  <p className="text-sm text-amber-700 mt-2">Run Agent A clustering to load personas.</p>
                )}
              </div>
            ) : (
              <div className="flex flex-col">
                <label className="block text-sm font-semibold text-gray-800 mb-2">Select Customer</label>
                <select
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl bg-white focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose a customer…</option>
                  {customersQuery.data?.data?.customers?.map((customer: { customer_id: string; customer_name: string }) => (
                    <option key={customer.customer_id} value={customer.customer_id}>
                      {customer.customer_name} ({customer.customer_id})
                    </option>
                  ))}
                </select>
                {scoringMethod === 'rules' && (
                  <div className="mt-3 space-y-2">
                    <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={useAgentDDirectives}
                        onChange={(e) => {
                          setUseAgentDDirectives(e.target.checked);
                          if (!e.target.checked) agentDAutoAppliedRef.current = customerId;
                        }}
                        className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                      />
                      <span>
                        Apply <strong>Agent D</strong> supervisor directives (#1 pin matches supervisor)
                      </span>
                    </label>
                    {mode === 'customer' &&
                      customerId &&
                      (agentDDirectivesQuery.data?.next_visit_directives as { priority_pin_product_id?: string } | null)
                        ?.priority_pin_product_id && (
                        <p
                          className={`text-xs rounded-lg px-3 py-2 border ${
                            useAgentDDirectives
                              ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                              : 'bg-amber-50 text-amber-900 border-amber-200'
                          }`}
                        >
                          <Bot className="inline w-3.5 h-3.5 mr-1 align-middle" />
                          Agent D pinned{' '}
                          <code className="text-[11px] bg-white/60 px-1 rounded">
                            {
                              (agentDDirectivesQuery.data?.next_visit_directives as { priority_pin_product_id: string })
                                .priority_pin_product_id
                            }
                          </code>{' '}
                          as #1 for this customer.
                          {!useAgentDDirectives && (
                            <>
                              {' '}
                              <strong>Check the box above</strong> or your list stays pure 12-factor (e.g. Auto Loans
                              may rank above IRAs).
                            </>
                          )}
                          {useAgentDDirectives && ' Your next run ranks that product first.'}
                        </p>
                      )}
                  </div>
                )}
              </div>
            )}
            <div className="flex flex-col">
              <label className="block text-sm font-semibold text-gray-800 mb-2">Category (optional)</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl bg-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All categories</option>
                <option value="Personal">Personal banking</option>
                <option value="Business">Business banking</option>
                <option value="Agricultural">Agricultural banking</option>
              </select>
            </div>
          </div>

          <div className="grid md:grid-cols-4 gap-4 items-end">
            <div className="md:col-span-3 flex flex-col">
              <label className="block text-sm font-semibold text-gray-800 mb-2">Search query</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g., mortgage, high-yield savings, credit card, CD…"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex flex-col">
              <label className="block text-sm font-semibold text-gray-800 mb-2">Top N</label>
              <input
                type="number"
                value={topN}
                onChange={(e) => setTopN(parseInt(e.target.value, 10) || 10)}
                min={1}
                max={20}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 tabular-nums"
              />
            </div>
          </div>

          {/* Accordion: factor weights — rule-based only */}
          {scoringMethod === 'rules' && (
            <div className="rounded-xl border border-gray-200 bg-gray-50/50 overflow-hidden">
              <button
                type="button"
                onClick={() => setWeightsAccordionOpen((o) => !o)}
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
                    <strong className="text-violet-700">AI recommended weights</strong> for a persona-tuned starting
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
                              className="flex items-center justify-between gap-3 min-w-0 border-b border-gray-100 sm:border-0 pb-2 sm:pb-0 last:border-0"
                            >
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
                          ))}
                        </div>
                      </div>
                    ))}
                    <p className="text-xs text-gray-500">
                      {factorWeightsQuery.data?.is_custom
                        ? 'Saved custom weights are used on Run.'
                        : 'Defaults apply until you submit custom weights.'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={handleSearch}
            disabled={executeMutation.isPending}
            className="w-full px-6 py-3.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:bg-gray-400 flex items-center justify-center gap-2 font-semibold shadow-md transition-colors"
          >
            <Search className="w-5 h-5" />
            {executeMutation.isPending ? 'Running…' : 'Get personalized banking recommendations'}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {executeMutation.isPending && (
        <div className={`border rounded-lg p-6 text-center ${
          scoringMethod === 'logit' 
            ? 'bg-purple-50 border-purple-200' 
            : 'bg-blue-50 border-blue-200'
        }`}>
          <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4 ${
            scoringMethod === 'logit' ? 'border-purple-600' : 'border-blue-600'
          }`}></div>
          <p className={`font-medium ${
            scoringMethod === 'logit' ? 'text-purple-700' : 'text-blue-700'
          }`}>
            {scoringMethod === 'logit' 
              ? `Running Banking Hybrid ML model for ${mode === 'persona' ? persona : 'customer'}...`
              : `Calculating personalized banking scores for ${mode === 'persona' ? persona : 'customer'}...`}
          </p>
          {scoringMethod === 'logit' && (
            <p className="text-sm text-purple-600 mt-2">
              🤖 AI learning from banking transaction patterns
            </p>
          )}
        </div>
      )}

      {/* Error State */}
      {executeMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle className="w-6 h-6" />
            <div>
              <p className="font-medium">Error getting recommendations</p>
              <p className="text-sm">{executeMutation.error?.message}</p>
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
                scoringMethod === 'logit'
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {scoringMethod === 'logit' 
                  ? '🤖 Hybrid ML (50% ML + 50% Banking Rules)'
                  : '📊 Banking 12-Factor Scoring'}
              </div>
            </div>

            {/* Banking-Specific Metrics Grid */}
            {(insights || results.metrics) && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Match Quality */}
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
                  <p className="text-xs text-gray-600 mb-1">🎯 Match Quality</p>
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
                  <p className="text-xs text-gray-600 mb-1">💰 Annual Cost</p>
                  <p className="text-2xl font-bold text-blue-600">
                    ${results.metrics?.total_annual_cost?.toFixed(0) || insights?.total_annual_cost?.toFixed(0) || '0'}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    {results.metrics?.free_products || insights?.free_products || 0} free products
                  </p>
                </div>

                {/* Earning Potential */}
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200">
                  <p className="text-xs text-gray-600 mb-1">📈 Earning Potential</p>
                  <p className="text-2xl font-bold text-purple-600">
                    +${results.metrics?.estimated_annual_earnings?.toFixed(0) || insights?.estimated_annual_earnings?.toFixed(0) || '0'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {results.metrics?.earning_products || insights?.earning_products || 0} products @ {results.metrics?.avg_apy?.toFixed(2) || insights?.avg_apy?.toFixed(2) || '0'}% APY
                  </p>
                </div>

                {/* Accessibility */}
                <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-4 border border-orange-200">
                  <p className="text-xs text-gray-600 mb-1">🔓 Easy Access</p>
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
                    💎 {insights.value_proposition}
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
            {scoringMethod === 'logit' && (scoringMethodology.formula || scoringMethodology.how_ml_probability_works) && (
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
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl font-bold text-gray-400">#{index + 1}</span>
                      <h3 className="text-xl font-bold text-gray-900">{rec.product_name}</h3>
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
                      {rec.min_credit_score && (
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
                      ) : (
                        <span className="text-green-600">Free</span>
                      )}
                    </div>
                    {rec.interest_rate > 0 && (
                      <div className="text-sm text-green-600 font-semibold">
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

                {/* 💡 Why This Product? - Unified, beautifully formatted */}
                {(rec.rank_explanation || rec.recommendation_text) && (
                  <div className="mb-4 overflow-hidden rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50/80 to-teal-50/80 shadow-sm">
                    <div className="border-b border-emerald-200 bg-emerald-100/60 px-4 py-2.5">
                      <p className="text-sm font-bold text-emerald-900 flex items-center gap-2">
                        <span className="text-base">💡</span> Why This Product?
                      </p>
                    </div>
                    <div className="p-4 space-y-4">
                      {rec.rank_explanation && (
                        <div className="space-y-3">
                          <p className="text-xs font-bold text-emerald-800 uppercase tracking-wide flex items-center gap-1.5">
                            <span>🏆</span> Rank #{rec.rank || (index + 1)} · {(rec.score * 100).toFixed(1)}% compatibility
                          </p>
                          <div className="text-sm text-gray-800 leading-relaxed space-y-2">
                            {rec.rank_explanation.split('\n\n').map((section: string, idx: number) => (
                              <div key={idx} className={idx > 0 ? 'mt-3 pt-3 border-t border-emerald-200' : ''}>
                                {section.split('\n').map((line: string, lineIdx: number) => {
                                  const formattedLine = line.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-emerald-900">$1</strong>');
                                  const finalLine = formattedLine.replace(/\*(.*?)\*/g, '<em class="text-gray-600 text-xs">$1</em>');
                                  return (
                                    <p
                                      key={lineIdx}
                                      className={line.startsWith('*') ? 'text-xs italic text-gray-600 mt-2' : 'mb-1'}
                                      dangerouslySetInnerHTML={{ __html: finalLine }}
                                    />
                                  );
                                })}
                              </div>
                            ))}
                          </div>
                          <p className="text-xs text-emerald-800 pt-2 border-t border-emerald-200/80">
                            📐 Comprehensive match score based on banking 12 factors (see detailed calculation below).
                          </p>
                        </div>
                      )}
                      {!rec.rank_explanation && rec.recommendation_text && (
                        <>
                          <div className="text-sm text-gray-800 leading-relaxed">
                            {rec.reason || rec.recommendation_text}
                          </div>
                          <p className="text-xs text-emerald-800 pt-2 border-t border-emerald-200/80">
                            📐 Comprehensive match score based on banking 12 factors (see detailed calculation below).
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                )}

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
                              {rec.detailed_calculation && rec.scoring_method === '12_factor' ? (
                                /* BANKING 12-FACTOR DETAILED CALCULATION */
                                <div>
                                  <p className="text-xs font-semibold text-indigo-900 mb-3">
                                    🏦 Banking 12-Factor Scoring System
                                  </p>
                                  
                                  {/* Total Score */}
                                  <div className="mb-3 p-3 bg-white rounded-lg border-2 border-indigo-300">
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs font-bold text-gray-900">Total Suitability Score</span>
                                      <span className="text-lg font-bold text-indigo-600">{(rec.score * 100).toFixed(1)}%</span>
                                    </div>
                                  </div>

                                  {/* TIER 1: Core Banking Criteria (55%) */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
                                    <p className="text-xs font-bold text-indigo-900 mb-3">🎯 TIER 1: Core Banking Criteria (55%)</p>
                                    
                                    {/* Eligibility Score */}
                                    {rec.detailed_calculation.eligibility_score && (
                                      <div className="mb-3 pb-3 border-b border-indigo-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">1. Eligibility Score</span>
                                          <span className="text-sm font-bold text-indigo-700">{(rec.detailed_calculation.eligibility_score.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.eligibility_score.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.eligibility_score.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.eligibility_score as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {((rec.detailed_calculation.eligibility_score as { calculation?: string }).calculation)}</p>
                                            )}
                                            <p>Banking regulators require strict eligibility criteria. 68% of denied applications cite credit/income issues (FDIC). Must be highest weight to ensure compliance and prevent customer frustration.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Financial Need Match */}
                                    {rec.detailed_calculation.financial_need_match && (
                                      <div className="mb-3 pb-3 border-b border-indigo-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">2. Financial Need Match</span>
                                          <span className="text-sm font-bold text-indigo-700">{(rec.detailed_calculation.financial_need_match.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.financial_need_match.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.financial_need_match.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.financial_need_match as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.financial_need_match as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>Products must match life stage: Retirees need income products, young professionals need credit building. McKinsey research shows 72% satisfaction comes from need-product alignment.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Relationship Depth */}
                                    {rec.detailed_calculation.relationship_depth && (
                                      <div className="mb-0">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">3. Relationship Depth</span>
                                          <span className="text-sm font-bold text-indigo-700">{(rec.detailed_calculation.relationship_depth.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.relationship_depth.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.relationship_depth.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.relationship_depth as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.relationship_depth as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>Customers with 3+ products have 92% retention vs 40% for single-product (Bain & Company). Loyalty drives long-term profitability.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}
                                  </div>

                                  {/* TIER 2: Strategic Fit & Product Value (28%) */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border border-blue-200">
                                    <p className="text-xs font-bold text-blue-900 mb-3">💎 TIER 2: Strategic Fit & Product Value (28%)</p>
                                    
                                    {/* Product Value - NEW! */}
                                    {rec.detailed_calculation.product_value && (
                                      <div className="mb-3 pb-3 border-b border-blue-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">4. Product Value ⭐ NEW</span>
                                          <span className="text-sm font-bold text-blue-700">{(rec.detailed_calculation.product_value.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.product_value.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.product_value.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.product_value as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.product_value as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>Fee sensitivity drives 45% of account switching (J.D. Power). Products must differentiate on value: fees, APY, min balance, ROI. Higher weight ensures best-value products rise to top.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Product Pairing */}
                                    {rec.detailed_calculation.product_pairing && (
                                      <div className="mb-3 pb-3 border-b border-blue-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">5. Product Pairing</span>
                                          <span className="text-sm font-bold text-blue-700">{(rec.detailed_calculation.product_pairing.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.product_pairing.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.product_pairing.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.product_pairing as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.product_pairing as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>Cross-sell increases customer lifetime value 2-3x. Checking+Savings bundles show 85% higher satisfaction (Accenture Banking Study).</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Channel Fit */}
                                    {rec.detailed_calculation.channel_fit && (
                                      <div className="mb-0">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">6. Channel Fit</span>
                                          <span className="text-sm font-bold text-blue-700">{(rec.detailed_calculation.channel_fit.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.channel_fit.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.channel_fit.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.channel_fit as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.channel_fit as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>78% of millennials prefer mobile banking, 65% of 60+ prefer branches (ABA Survey). Channel mismatch causes 30% lower engagement.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}
                                  </div>

                                  {/* TIER 3: Behavioral & Contextual (10%) */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                    <p className="text-xs font-bold text-green-900 mb-3">🎯 TIER 3: Behavioral & Contextual (10%)</p>
                                    
                                    {['complexity_match', 'intent_score', 'segment_affinity', 'transaction_pattern'].map((factorKey) => {
                                      const factor = rec.detailed_calculation[factorKey];
                                      if (!factor) return null;
                                      
                                      const factorInfo: Record<string, { name: string; why: string }> = {
                                        'complexity_match': {
                                          name: 'Complexity Match',
                                          why: 'Complex products (IRAs, CDs) require financial literacy. 40% of customers abandon overly complex products (Deloitte). Matching sophistication prevents drop-off.'
                                        },
                                        'intent_score': {
                                          name: 'Intent Score',
                                          why: 'Cross-sell receptivity varies widely. Targeting high-intent customers improves conversion 3-5x (Salesforce Banking Report).'
                                        },
                                        'segment_affinity': {
                                          name: 'Segment Affinity',
                                          why: 'Peer behavior influences 60% of banking decisions. "People like me" social proof drives adoption in homogeneous segments.'
                                        },
                                        'transaction_pattern': {
                                          name: 'Transaction Pattern',
                                          why: 'High-frequency transactors need different products than savers. Activity patterns predict product usage and satisfaction.'
                                        }
                                      };

                                      return (
                                        <div key={factorKey} className="mb-2 pb-2 border-b border-green-100 last:border-0">
                                          <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-semibold text-gray-900">{factorInfo[factorKey].name}</span>
                                            <span className="text-xs font-bold text-green-700">{(factor.score * 100).toFixed(1)}%</span>
                                          </div>
                                          <div className="text-xs text-gray-700 mb-1">📌 {factor.explanation}</div>
                                          <details className="mt-1">
                                            <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                              Why {(factor.weight * 100).toFixed(0)}%?
                                            </summary>
                                            <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                              {(factor as { calculation?: string }).calculation && (
                                                <p className="font-medium text-indigo-700">📐 {(factor as { calculation?: string }).calculation}</p>
                                              )}
                                              <p>{factorInfo[factorKey].why}</p>
                                            </div>
                                          </details>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {/* TIER 4: Quality Signals (7%) */}
                                  <div className="mb-3 p-3 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border border-orange-200">
                                    <p className="text-xs font-bold text-orange-900 mb-3">⭐ TIER 4: Quality Signals (7%)</p>
                                    
                                    {['product_rating', 'popularity'].map((factorKey) => {
                                      const factor = rec.detailed_calculation[factorKey];
                                      if (!factor) return null;
                                      
                                      const factorInfo: Record<string, { name: string; why: string }> = {
                                        'product_rating': {
                                          name: 'Product Rating',
                                          why: 'Customer satisfaction ratings predict long-term retention. 4.5+ star products have 80% renewal rates vs 55% for 3-star (Banking Satisfaction Index).'
                                        },
                                        'popularity': {
                                          name: 'Popularity',
                                          why: 'Popular products within segments indicate proven value. Adoption rates signal market validation and reduce perceived risk for customers.'
                                        }
                                      };

                                      return (
                                        <div key={factorKey} className="mb-2 pb-2 border-b border-orange-100 last:border-0">
                                          <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-semibold text-gray-900">{factorInfo[factorKey].name}</span>
                                            <span className="text-xs font-bold text-orange-700">{(factor.score * 100).toFixed(1)}%</span>
                                          </div>
                                          <div className="text-xs text-gray-700 mb-1">📌 {factor.explanation}</div>
                                          <details className="mt-1">
                                            <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                              Why {(factor.weight * 100).toFixed(0)}%?
                                            </summary>
                                            <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                              {(factor as { calculation?: string }).calculation && (
                                                <p className="font-medium text-indigo-700">📐 {(factor as { calculation?: string }).calculation}</p>
                                              )}
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
                                      💡 All weights sum to 100%. Each percentage is based on banking research, regulatory requirements, and customer behavior studies.
                                    </p>
                                  </div>
                                </div>
                              ) : scoringMethod === 'logit' && rec.scoring_breakdown ? (
                                /* HYBRID ML MODEL EXPLANATION */
                                <div>
                                  <p className="text-xs font-semibold text-purple-900 mb-3">
                                    🎯 Banking Hybrid Scoring (50% ML + 50% Rules)
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
                                        <span className="text-xs font-bold text-purple-900">🤖 ML Prediction</span>
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
                                          📊 View 12-Factor Banking Rules Breakdown (50% component)
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
                                      💡 Higher scores indicate products that match customer profile, needs, and financial capacity
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

                {/* Product Details Grid */}
                {(rec.min_balance || rec.min_credit_score || rec.interest_rate) && (
                  <div className="grid grid-cols-3 gap-2 mb-4">
                    {rec.min_balance > 0 && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Min Balance</p>
                        <p className="text-sm font-medium text-gray-900">${rec.min_balance.toLocaleString()}</p>
                      </div>
                    )}
                    {rec.min_credit_score && (
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
                    <p className="text-xs font-semibold text-green-800 mb-2">💡 Why This Product?</p>
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

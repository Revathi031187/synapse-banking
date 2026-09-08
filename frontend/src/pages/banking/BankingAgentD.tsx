import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  Users,
  User,
  Loader2,
  Sparkles,
  CreditCard,
  LayoutGrid,
  Gift,
  Clock,
  CheckCircle2,
  Tag,
  TrendingUp,
  Pin,
  PinOff,
  Zap,
  BarChart2,
} from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';
import { useSessionStorageState } from '../../hooks/useSessionStorageState';
import CustomerSearchSelect from '../../components/CustomerSearchSelect';

const API_BASE = getBankingApiBase();

export const AGENT_D_UI_KEY = 'banking-agent-d-v1';

// Every successful orchestrate call this tab session, appended (not overwritten) —
// separate from persistedOrchestrate (which only remembers the latest, for UI resume).
// Consumed by the Activation tab's "Create Dataset" push, which dedupes by timestamp.
export const AGENT_D_SESSION_LOG_KEY = 'banking-agent-d-session-log-v1';

export interface AgentDSessionLogEntry {
  customerId: string;
  timestamp: string; // ISO, stamped client-side the moment this orchestrate call succeeded
  data: unknown; // Agent D's raw orchestrate output (the `data` field of the response)
}

// ── Next Visit Intelligence types ─────────────────────────────────────────────
type DirectorResult = {
  affinity_analysis: {
    top_product_id: string | null;
    top_product_name: string;
    affinity_score: number;
    signal_summary: string;
    signal_breakdown: Record<string, number>;
    signals_received: number;
  };
  next_visit_directives: {
    priority_pin_product_id: string | null;
    priority_pin_reason: string;
    boost_product_ids: string[];
    deprioritize_product_ids: string[];
    focus_source: string;
    affinity_score: number;
    recommended_channel: string | null;
  };
  diverges_from_current: boolean;
  divergence_explanation: string;
};

const CHANNEL_LABELS: Record<string, string> = {
  in_app: 'In-App', email: 'Email', direct_mail: 'Direct Mail', branch: 'Branch',
};
const CHANNEL_COLORS: Record<string, string> = {
  in_app: 'bg-violet-500', email: 'bg-blue-400', direct_mail: 'bg-teal-400', branch: 'bg-amber-400',
};
export const DEFAULT_AGENT_D_UI = {
  mode: 'customer' as 'persona' | 'customer',
  personaId: '',
  customerId: '',
  persistedOrchestrate: null as { customerId: string; response: unknown } | null,
  // True right after the user clicks Unpin, until the next explicit "Load
  // supervisor view" run. orchestrate() always recomputes a pin from
  // underlying signals (last click / incomplete app / saved goal / Agent C's
  // offer / Agent B's #1) and unconditionally overwrites last_directives —
  // so re-running it immediately after an unpin would just re-derive and
  // silently reinstate the same pin. This flag hides pin UI locally instead
  // of re-fetching data that would fight the unpin.
  pinCleared: false,
};

function BoldParts({ text }: { text: string }) {
  const parts = text.split(/\*\*/);
  return (
    <>
      {parts.map((p, i) =>
        i % 2 === 1 ? (
          <strong key={i} className="text-emerald-900">
            {p}
          </strong>
        ) : (
          <span key={i}>{p}</span>
        )
      )}
    </>
  );
}

type OfferCard = {
  product_id?: string;
  product_name?: string;
  category?: string;
  status?: string;
  reasoning?: string;
  offer_name?: string;
  offer_type?: string;
  headline_value?: string;
  content_benefit_1?: string;
  content_benefit_2?: string;
  content_benefit_3?: string;
  days_remaining?: number | null;
  terms_summary?: string;
};

function OfferIntelCard({ offer }: { offer: OfferCard }) {
  const benefits = [offer.content_benefit_1, offer.content_benefit_2, offer.content_benefit_3].filter(Boolean);
  const hasOfferDetails = !!(offer.offer_name || offer.headline_value);

  return (
    <div className="rounded-xl overflow-hidden">
      {/* Header gradient */}
      <div className="bg-gradient-to-r from-violet-700 via-indigo-700 to-blue-700 px-5 py-4 rounded-t-xl">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-widest text-violet-200 mb-1">
              {offer.category || 'Banking'} · {offer.product_id}
            </p>
            <p className="text-white font-bold text-base leading-snug">{offer.product_name}</p>
            {offer.offer_name && (
              <span className="inline-flex items-center gap-1 mt-1.5 px-2 py-0.5 rounded-full bg-white/20 text-white text-xs font-semibold">
                <Tag className="w-3 h-3" />
                {offer.offer_name}
              </span>
            )}
          </div>
          <span className="shrink-0 px-2.5 py-1 rounded-full bg-emerald-400/90 text-emerald-950 text-[11px] font-bold">
            {offer.status || 'Offer ready'}
          </span>
        </div>
        {offer.headline_value && (
          <p className="text-2xl font-extrabold text-white mt-3 leading-tight">{offer.headline_value}</p>
        )}
      </div>

      {/* Body */}
      <div className="bg-white px-5 py-4 space-y-4 rounded-b-xl">
        {/* Urgency badge */}
        {offer.days_remaining != null && offer.days_remaining > 0 && offer.days_remaining < 30 && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
            <Clock className="w-3.5 h-3.5" />
            Offer ends in {offer.days_remaining} days
          </div>
        )}

        {/* Benefits */}
        {benefits.length > 0 && (
          <div className="space-y-2">
            {benefits.map((b, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-slate-700">
                <CheckCircle2 className="w-4 h-4 text-violet-500 shrink-0 mt-0.5" />
                <span>{b}</span>
              </div>
            ))}
          </div>
        )}

        {/* Reasoning */}
        {offer.reasoning && (
          <div className="rounded-xl bg-violet-50 border border-violet-100 px-4 py-3">
            <p className="text-xs font-bold text-violet-800 mb-1 uppercase tracking-wide">Why this offer</p>
            <p className="text-xs text-slate-700 leading-relaxed line-clamp-3">{offer.reasoning}</p>
          </div>
        )}

        {/* Terms */}
        {offer.terms_summary && (
          <p className="text-[11px] text-slate-400 leading-relaxed border-t border-slate-100 pt-3">{offer.terms_summary}</p>
        )}

        {!hasOfferDetails && !offer.reasoning && (
          <p className="text-xs text-slate-500 italic">Run Best Offer Agent for this customer to populate offer details.</p>
        )}
      </div>
    </div>
  );
}

export default function BankingAgentD() {
  const queryClient = useQueryClient();
  const [ui, setUi] = useSessionStorageState(AGENT_D_UI_KEY, DEFAULT_AGENT_D_UI);
  const { mode, personaId, customerId, persistedOrchestrate, pinCleared } = ui;
  const [, setSessionLog] = useSessionStorageState<AgentDSessionLogEntry[]>(AGENT_D_SESSION_LOG_KEY, []);

  const personasQuery = useQuery({
    queryKey: ['banking-personas'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/personas`);
      if (!res.ok) throw new Error('Failed personas');
      return res.json();
    },
    retry: 2,
  });
  const apiPersonas = (personasQuery.data?.personas ?? []) as Array<{
    id: string;
    name: string;
    size?: number;
  }>;

  const customersQuery = useQuery({
    queryKey: ['banking-agent-d-customers'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_a/customers?limit=5000`);
      if (!res.ok) throw new Error('Failed customers');
      return res.json();
    },
    retry: 2,
  });
  const allCustomers = (customersQuery.data?.data?.customers ?? []) as Array<{
    customer_id: string;
    customer_name?: string;
    cluster_id?: number;
  }>;

  /** If /personas is empty (Agent A state lost) but customers have cluster_id */
  const personas = useMemo(() => {
    if (apiPersonas.length > 0) return apiPersonas;
    const byCluster = new Map<string, number>();
    for (const c of allCustomers) {
      const k = c.cluster_id;
      if (k == null) continue;
      const id = String(k);
      byCluster.set(id, (byCluster.get(id) ?? 0) + 1);
    }
    const out: Array<{ id: string; name: string; size?: number }> = [];
    [...byCluster.entries()]
      .sort((a, b) => Number(a[0]) - Number(b[0]))
      .forEach(([id, n]) => {
        out.push({ id, name: `Segment ${id} (${n} in sample)`, size: n });
      });
    return out;
  }, [apiPersonas, allCustomers]);

  /** Server-filtered by cluster: first 500 global customers often omit entire segments */
  const segmentCustomersQuery = useQuery({
    queryKey: ['banking-agent-d-segment-customers', personaId],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE}/api/banking/agent_a/customers?cluster_id=${encodeURIComponent(personaId)}&limit=500&skip=0`
      );
      if (!res.ok) throw new Error('segment customers');
      return res.json();
    },
    enabled: mode === 'persona' && !!personaId,
  });

  const segmentCustomers = (segmentCustomersQuery.data?.data?.customers ?? []) as Array<{
    customer_id: string;
    customer_name?: string;
    cluster_id?: number;
  }>;

  React.useEffect(() => {
    if (personas.length && !personaId) setUi((prev) => ({ ...prev, personaId: String(personas[0].id) }));
  }, [personas, personaId]);

  React.useEffect(() => {
    if (mode !== 'persona' || !personaId || !segmentCustomersQuery.isSuccess) return;
    const list = segmentCustomers;
    if (list.length === 0) {
      setUi((prev) => ({ ...prev, customerId: '' }));
      return;
    }
    const inList = list.some((c) => String(c.customer_id) === String(customerId));
    if (!customerId || !inList) {
      setUi((prev) => ({ ...prev, customerId: String(list[0].customer_id) }));
    }
  }, [mode, personaId, segmentCustomersQuery.isSuccess, segmentCustomers, customerId]);

  const orchestrateMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_d/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: customerId,
          saved_goals: [],
          incomplete_applications: [],
          clicked_product_ids: [],
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Load failed');
      }
      return res.json();
    },
    onSuccess: (payload) => {
      const cid = String(customerId).trim();
      if (cid) {
        setUi((prev) => ({ ...prev, persistedOrchestrate: { customerId: cid, response: payload }, pinCleared: false }));
        setSessionLog((prev) => [
          ...prev,
          { customerId: cid, timestamp: new Date().toISOString(), data: payload?.data },
        ]);
        queryClient.invalidateQueries({ queryKey: ['banking-agent-d-directives-b', cid] });
        queryClient.invalidateQueries({ queryKey: ['banking-agent-d-directives-b'] });
      }
    },
  });

  const cidKey = String(customerId).trim();

  // Recommender's and Offer's pins are independent (each reads its own field
  // server-side) — this is the shared source of truth both cards' toggle
  // buttons read from, refetched (not orchestrate() re-run) after every
  // pin/unpin so a card's button flips immediately without triggering
  // orchestrate()'s slow, unrelated recompute of its own auto-pin narrative.
  const pinsQuery = useQuery({
    queryKey: ['banking-agent-d-pins', cidKey],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_d/pins/${encodeURIComponent(cidKey)}`);
      if (!res.ok) throw new Error('Failed to load pins');
      return res.json() as Promise<{ recommender_pin_product_id: string | null; offer_pin_product_id: string | null }>;
    },
    enabled: !!cidKey,
    staleTime: 0,
    refetchOnMount: 'always',
    // Pinning/unpinning from Recommender or Offer directly (not through this
    // page) doesn't touch anything Director itself would know to invalidate —
    // this is a cheap dict lookup (no LLM calls), so poll it while the tab is
    // open, plus refetch on refocus, so an external change shows up here
    // without requiring a manual reload.
    refetchOnWindowFocus: true,
    refetchInterval: 5000,
  });

  function usePinToggle(scope: 'recommender' | 'offer') {
    const pin = useMutation({
      mutationFn: async (productId: string) => {
        const res = await fetch(`${API_BASE}/api/banking/agent_d/pin/${scope}/${encodeURIComponent(cidKey)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_id: productId }),
        });
        if (!res.ok) throw new Error('Pin failed');
        return res.json();
      },
      onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['banking-agent-d-pins', cidKey] }),
    });
    const unpin = useMutation({
      mutationFn: async () => {
        const res = await fetch(`${API_BASE}/api/banking/agent_d/pin/${scope}/${encodeURIComponent(cidKey)}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Unpin failed');
        return res.json();
      },
      onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['banking-agent-d-pins', cidKey] }),
    });
    return { pin, unpin };
  }
  const recommenderPinToggle = usePinToggle('recommender');
  const offerPinToggle = usePinToggle('offer');
  type OrchestrateBody = NonNullable<typeof orchestrateMutation.data>['data'];
  const data: OrchestrateBody | undefined =
    orchestrateMutation.data?.data ??
    (persistedOrchestrate?.customerId === cidKey
      ? (persistedOrchestrate.response as { data?: OrchestrateBody })?.data
      : undefined);
  const sv = data?.supervisor_view;
  const liveStack = (data?.live_recommendations ?? []) as Array<{
    product_id: string;
    product_name?: string;
    supervisor_slot?: string;
    score?: number;
  }>;
  const bRecs = sv?.agent_b_product_recommendations ?? [];
  const cOffer = sv?.agent_c_primary_offer as OfferCard | undefined | null;
  const focus = sv?.focus_product as { product_id?: string; product_name?: string } | undefined | null;
  const autoPinnedProductId = pinCleared ? undefined : (data?.next_visit_directives as { priority_pin_product_id?: string } | undefined)
    ?.priority_pin_product_id;
  const autoPinnedProduct = autoPinnedProductId
    ? liveStack.find((r) => String(r.product_id) === String(autoPinnedProductId)) ??
      ({
        product_id: String(autoPinnedProductId),
        product_name: String(autoPinnedProductId),
      } as (typeof liveStack)[number])
    : null;

  const canLoad = !!customerId;

  // ── Next Visit Intelligence state ───────────────────────────────────────────
  const [nextVisitResult, setNextVisitResult] = useState<DirectorResult | null>(null);
  const [nextVisitLoading, setNextVisitLoading] = useState(false);

  // Read Agent C channel attribution from TanStack Query cache
  const agentCQueryData = queryClient.getQueryData<{ data?: {
    offer_intelligence?: {
      channel_attribution?: Record<string, number>;
      experiment_data?: { experiment_id?: string; p_value?: number };
    };
    persona?: string;
  } }>(['banking-one-best-offer', customerId]);
  const channelAttribution = agentCQueryData?.data?.offer_intelligence?.channel_attribution ?? null;
  const agentCExpId = agentCQueryData?.data?.offer_intelligence?.experiment_data?.experiment_id ?? null;
  const agentCPValue = agentCQueryData?.data?.offer_intelligence?.experiment_data?.p_value ?? null;

  const winningChannelEntry = channelAttribution
    ? Object.entries(channelAttribution).filter(([, p]) => p > 0).sort(([, a], [, b]) => b - a)[0]
    : null;
  const winningChannelLabel = winningChannelEntry ? (CHANNEL_LABELS[winningChannelEntry[0]] ?? winningChannelEntry[0]) : '';
  const mtaPersonaName = data?.persona_name ?? 'this segment';
  const mtaExplanation = winningChannelEntry
    ? `${winningChannelLabel} outperformed all channels for ${mtaPersonaName} customers — serving this offer via ${winningChannelLabel.toLowerCase()} yields ${Math.round(winningChannelEntry[1] * 100)}% of total segment conversions.`
    : '';

  // Auto-fetch Director when Agent D data loads or customer changes
  React.useEffect(() => {
    if (!customerId) { setNextVisitResult(null); return; }
    const effectiveData = orchestrateMutation.data?.data ??
      (persistedOrchestrate?.customerId === customerId
        ? (persistedOrchestrate.response as { data?: unknown })?.data
        : undefined);
    if (!effectiveData) { setNextVisitResult(null); return; }

    setNextVisitResult(null);
    setNextVisitLoading(true);
    fetch(`${API_BASE}/api/banking/agent_director/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: customerId,
        behavioral_signals: [],
        current_recommended_product_id: autoPinnedProductId ?? focus?.product_id ?? null,
        auto_from_ledger: true,
      }),
    })
      .then(r => r.json())
      .then(json => setNextVisitResult((json.data as DirectorResult) ?? null))
      .catch(() => setNextVisitResult(null))
      .finally(() => setNextVisitLoading(false));
  }, [orchestrateMutation.data, persistedOrchestrate?.customerId, customerId]);

  return (
    <div className="space-y-6 animate-fadeIn">
        <header className="flex gap-3 items-start">
          <div className="p-3 rounded-2xl bg-emerald-100 text-emerald-800 shadow-sm">
            <Bot className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Director: Supervisor</h1>
            <p className="text-slate-600 mt-2 text-sm md:text-base leading-relaxed max-w-3xl">
              <strong>Supervisor view</strong> merges digital signals with the Recommender and Best Offer engines, builds a live product
              stack, updates the impression ledger, and issues pin instructions for the Recommender.
            </p>
          </div>
        </header>

        {/* Control card — supervisor */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-md p-5 md:p-6 space-y-5">
          {(personasQuery.isError || customersQuery.isError) && (
            <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-amber-900 text-sm">
              Could not load personas or customers. Check that the API is running and{' '}
              <Link to="/banking/agent-a" className="font-semibold underline">
                Segmentation
              </Link>{' '}
              has been executed.
            </div>
          )}
          {!personasQuery.isLoading &&
            !customersQuery.isLoading &&
            personas.length === 0 &&
            !personasQuery.isError &&
            !customersQuery.isError && (
              <div className="rounded-xl bg-slate-100 border border-slate-200 px-4 py-3 text-slate-800 text-sm">
                <strong>No segments yet.</strong> Run{' '}
                <Link to="/banking/agent-a" className="text-emerald-700 font-semibold underline">
                  Segmentation
                </Link>{' '}
                once, then reload this page. Persona and customer lists come from that run.
              </div>
            )}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 w-24 shrink-0">Mode</span>
            <div className="flex rounded-xl border border-slate-200 p-1 bg-slate-50">
              <button
                type="button"
                onClick={() => {
                  setUi((prev) => ({ ...prev, mode: 'persona' }));
                }}
                className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  mode === 'persona' ? 'bg-emerald-600 text-white shadow' : 'text-slate-600 hover:bg-white'
                }`}
              >
                <Users className="w-4 h-4" />
                By persona
              </button>
              <button
                type="button"
                onClick={() => {
                  setUi((prev) => ({ ...prev, mode: 'customer' }));
                }}
                className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  mode === 'customer' ? 'bg-emerald-600 text-white shadow' : 'text-slate-600 hover:bg-white'
                }`}
              >
                <User className="w-4 h-4" />
                By customer
              </button>
            </div>
          </div>

          {mode === 'persona' && (
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Persona / segment</label>
                <select
                  className="w-full border border-slate-300 rounded-xl px-3 py-2.5 bg-white"
                  value={personaId}
                  disabled={personas.length === 0 || personasQuery.isLoading}
                  onChange={(e) => {
                    setUi((prev) => ({
                      ...prev,
                      personaId: e.target.value,
                      customerId: '',
                    }));
                    orchestrateMutation.reset();
                  }}
                >
                  {personasQuery.isLoading ? (
                    <option value="">Loading segments…</option>
                  ) : personas.length === 0 ? (
                    <option value="">Run Segmentation first — no segments</option>
                  ) : (
                    personas.map((p) => (
                      <option key={String(p.id)} value={String(p.id)}>
                        {p.name}
                        {p.size != null ? ` (${p.size})` : ''}
                      </option>
                    ))
                  )}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Customer in segment</label>
                <CustomerSearchSelect
                  customers={segmentCustomers}
                  value={customerId}
                  loading={segmentCustomersQuery.isLoading}
                  emptyListLabel="No customers in segment (run Segmentation)"
                  onChange={(id) => {
                    setUi((prev) => ({ ...prev, customerId: id, persistedOrchestrate: null, pinCleared: false }));
                    orchestrateMutation.reset();
                  }}
                />
              </div>
            </div>
          )}

          {mode === 'customer' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Customer</label>
              <CustomerSearchSelect
                className="max-w-xl"
                customers={allCustomers}
                value={customerId}
                loading={customersQuery.isLoading}
                emptyListLabel="No customers — run Segmentation first"
                onChange={(id) => {
                  setUi((prev) => ({ ...prev, customerId: id, persistedOrchestrate: null, pinCleared: false }));
                  orchestrateMutation.reset();
                }}
              />
            </div>
          )}

          <div className="flex flex-wrap gap-3 items-center">
            <button
              type="button"
              disabled={!canLoad || orchestrateMutation.isPending}
              onClick={() => orchestrateMutation.mutate()}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow-lg disabled:opacity-50 min-w-[200px]"
            >
              {orchestrateMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <LayoutGrid className="w-5 h-5" />
              )}
              Load supervisor view
            </button>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed border-t border-slate-100 pt-4">
            After Director runs, open <strong>Recommender</strong> → <strong>Customer mode</strong> → same customer →{' '}
            <strong>Run recommendations</strong>. The <strong>supervisor focus product</strong> is auto-applied as{' '}
            <strong>#1</strong>. Use the <strong>unpin</strong> button on either card below to clear it.
          </p>
        </div>

        {orchestrateMutation.isError && (
          <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-4">
            {(orchestrateMutation.error as Error).message}
          </div>
        )}

        {/* Empty state */}
        {!data && !orchestrateMutation.isPending && (
          <div className="border-2 border-dashed border-slate-300 rounded-2xl py-20 px-6 text-center text-slate-500 text-sm">
            Select mode, choose a customer, then <strong>Load supervisor view</strong>.
          </div>
        )}

        {orchestrateMutation.isPending && (
          <div className="flex justify-center py-16">
            <Loader2 className="w-10 h-10 text-emerald-600 animate-spin" />
          </div>
        )}

        {/* Results */}
        {data && sv && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">

            {/* ── Summary strip ── */}
            <div className="flex flex-wrap items-center gap-3 px-5 py-3.5 rounded-2xl bg-gradient-to-r from-slate-800 to-slate-700 shadow-md">
              <Sparkles className="w-5 h-5 text-amber-400 shrink-0" />
              <span className="text-white font-semibold text-sm">Summary</span>
              <span className="h-4 w-px bg-white/20 shrink-0" />
              <span className="text-slate-300 text-sm">
                Segment: <strong className="text-white">{data.persona_name}</strong>
              </span>
              <span className="h-4 w-px bg-white/20 shrink-0" />
              <span className="text-slate-300 text-sm">
                Customer <strong className="text-white font-mono">{data.customer_id}</strong>
              </span>
            </div>

            {/* ── Two-column grid: Recommender top 3 + Best Offer ── */}
            <div className="grid lg:grid-cols-2 gap-6">

              {/* Recommender top 3 */}
              <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-blue-50 to-indigo-50 flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
                    <CreditCard className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-900">Recommender — Top 3</p>
                    <p className="text-[11px] text-slate-500">12-factor persona fit ranking</p>
                  </div>
                  {bRecs[0]?.product_id && (() => {
                    const isPinned = String(pinsQuery.data?.recommender_pin_product_id ?? '') === String(bRecs[0].product_id);
                    const busy = recommenderPinToggle.pin.isPending || recommenderPinToggle.unpin.isPending;
                    return (
                      <button
                        type="button"
                        onClick={() =>
                          isPinned ? recommenderPinToggle.unpin.mutate() : recommenderPinToggle.pin.mutate(bRecs[0].product_id)
                        }
                        disabled={busy}
                        title={isPinned ? 'Unpin this recommendation' : 'Pin this recommendation'}
                        className={`ml-auto inline-flex items-center gap-1 px-2.5 py-1 rounded-full border text-[11px] font-semibold disabled:opacity-50 ${
                          isPinned ? 'border-blue-200 bg-white text-blue-700 hover:bg-blue-50' : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50'
                        }`}
                      >
                        {isPinned ? <PinOff className="w-3 h-3" /> : <Pin className="w-3 h-3" />}
                        {busy ? 'Working…' : isPinned ? 'Unpin' : 'Pin'}
                      </button>
                    );
                  })()}
                </div>
                <div className="divide-y divide-slate-100">
                  {bRecs.map((r: { product_id: string; product_name: string; category?: string; score: number }, idx: number) => {
                    const pct = Math.round(Number(r.score) * 100);
                    const rankColors = ['text-blue-700 bg-blue-50 border-blue-200', 'text-slate-600 bg-slate-50 border-slate-200', 'text-slate-500 bg-slate-50 border-slate-100'];
                    const barColors = ['bg-blue-500', 'bg-slate-400', 'bg-slate-300'];
                    return (
                      <div key={r.product_id} className={`px-5 py-4 flex items-center gap-4 ${idx === 0 ? 'bg-blue-50/40' : ''}`}>
                        <span className={`shrink-0 w-8 h-8 rounded-xl border flex items-center justify-center text-sm font-extrabold ${rankColors[idx] ?? rankColors[2]}`}>
                          {idx + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-0.5">
                            <p className="font-semibold text-slate-900 text-sm">{r.product_name}</p>
                            {idx === 0 && (
                              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-blue-600 text-white">Top pick</span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-1.5">
                            <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                              <div
                                className={`h-full rounded-full ${barColors[idx] ?? barColors[2]}`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span className="text-[11px] font-bold text-slate-600 tabular-nums shrink-0">{pct}%</span>
                          </div>
                          <span className="text-[10px] uppercase tracking-wide text-slate-400 mt-0.5 block">{r.category || 'Banking'} · {r.product_id}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Best Offer card */}
              <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-violet-50 to-purple-50 flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center shrink-0">
                    <Gift className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-slate-900">Best Offer Agent</p>
                    <p className="text-[11px] text-slate-500">Offer engine — retention & eligibility</p>
                  </div>
                  {cOffer?.product_id && (() => {
                    const isPinned = String(pinsQuery.data?.offer_pin_product_id ?? '') === String(cOffer.product_id);
                    const busy = offerPinToggle.pin.isPending || offerPinToggle.unpin.isPending;
                    return (
                      <button
                        type="button"
                        onClick={() =>
                          isPinned ? offerPinToggle.unpin.mutate() : offerPinToggle.pin.mutate(cOffer.product_id!)
                        }
                        disabled={busy}
                        title={isPinned ? 'Unpin this offer' : 'Pin this offer'}
                        className={`shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-full border text-[11px] font-semibold disabled:opacity-50 ${
                          isPinned ? 'border-violet-200 bg-white text-violet-700 hover:bg-violet-50' : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50'
                        }`}
                      >
                        {isPinned ? <PinOff className="w-3 h-3" /> : <Pin className="w-3 h-3" />}
                        {busy ? 'Working…' : isPinned ? 'Unpin' : 'Pin'}
                      </button>
                    );
                  })()}
                  {cOffer?.status === 'Segment recommendation' && (
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 shrink-0">Segment fallback</span>
                  )}
                </div>
                {cOffer ? (
                  <OfferIntelCard offer={cOffer} />
                ) : (
                  <div className="p-4">
                    <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-200">
                      <span className="text-amber-500 text-lg shrink-0">⚠</span>
                      <p className="text-sm text-amber-800 leading-relaxed">
                        No offer returned — eligibility filters or exclusions may apply. Supervisor still routes using segment fit.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* ── Supervisor instruction panel ── */}
            {focus && (
              <section className="rounded-2xl overflow-hidden border border-emerald-200 shadow-md">
                {/* Header bar */}
                <div className="bg-gradient-to-r from-emerald-700 to-teal-700 px-6 py-4 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-white font-bold text-sm">Director Instruction → Recommender</p>
                    <p className="text-emerald-200 text-xs">Next visit / campaign directive</p>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-emerald-50/60 via-white to-teal-50/30 p-6">
                  <div className="flex flex-col md:flex-row gap-6 items-start">

                    {/* Focus product + offer mini */}
                    <div className="w-full md:w-64 space-y-3 shrink-0">
                      <div className="rounded-2xl overflow-hidden border-2 border-emerald-400 shadow-md">
                        <div className="bg-gradient-to-br from-emerald-600 to-teal-600 px-4 py-3">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-100">Focus product</p>
                          <p className="text-white font-bold text-base mt-0.5 leading-snug">{focus.product_name}</p>
                          <p className="text-emerald-200 text-xs font-mono mt-0.5">{focus.product_id}</p>
                        </div>
                        <div className="bg-white px-4 py-3 flex items-center justify-between">
                          <span className="text-xs text-slate-500">Recommender position</span>
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-600 text-white text-xs font-bold">
                            <Pin className="w-3 h-3" />
                            Pin #1
                          </span>
                        </div>
                      </div>

                      {cOffer?.offer_name && (
                        <div className="rounded-xl bg-gradient-to-br from-indigo-50 to-violet-50 border border-indigo-200 px-4 py-3 space-y-1.5">
                          <p className="text-[10px] font-bold uppercase tracking-wide text-indigo-600 flex items-center gap-1">
                            <Gift className="w-3 h-3" />
                            Active offer
                          </p>
                          <p className="text-sm font-semibold text-slate-900 leading-snug">{cOffer.offer_name}</p>
                          {cOffer.headline_value && (
                            <p className="text-sm font-bold text-indigo-700">{cOffer.headline_value}</p>
                          )}
                          {cOffer.days_remaining != null && cOffer.days_remaining > 0 && cOffer.days_remaining < 30 && (
                            <span className="inline-flex items-center gap-1 text-xs text-amber-700 font-semibold">
                              <Clock className="w-3 h-3" />
                              Expires in {cOffer.days_remaining} days
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Supervisor copy */}
                    <div className="flex-1 space-y-4">
                      <div className="flex items-start gap-3">
                        <TrendingUp className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                        <p className="text-base font-bold text-slate-900 leading-snug">{sv.supervisor_headline}</p>
                      </div>
                      <div className="rounded-xl bg-white border border-emerald-100 shadow-sm px-4 py-3.5">
                        <p className="text-sm text-slate-700 leading-relaxed">
                          <BoldParts text={sv.supervisor_detail} />
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            )}
            {!focus && data && sv && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4 text-sm text-slate-500">
                No focus product pinned — run Best Offer with a valid offer or add an incomplete application signal.
              </div>
            )}

            {/* ── Next Visit Intelligence ── */}
            {data && (
              <section className="rounded-2xl overflow-hidden border border-slate-200 shadow-md">
                {/* Header */}
                <div className="bg-gradient-to-r from-slate-800 to-slate-700 px-6 py-4 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center shrink-0">
                    <TrendingUp className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-white font-bold text-sm">Next Visit Intelligence</p>
                    <p className="text-slate-300 text-xs">Engagement signals → personalized next-session recommendation</p>
                  </div>
                  {nextVisitLoading && (
                    <div className="ml-auto">
                      <Loader2 className="w-4 h-4 text-white/60 animate-spin" />
                    </div>
                  )}
                </div>

                <div className="bg-white p-5 space-y-5">

                  {/* ── Sub-section 1: Engagement Pattern ── */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <LayoutGrid className="w-4 h-4 text-slate-400" />
                      <p className="text-xs font-bold uppercase tracking-wider text-slate-600">Engagement Pattern</p>
                      <span className="text-[11px] text-slate-400">{liveStack.length} products in live stack</span>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {liveStack.slice(0, 6).map((rec) => {
                        const slot = rec.supervisor_slot ?? '';
                        let badge = { label: 'In Queue', cls: 'bg-slate-100 text-slate-600 border-slate-200' };
                        if (slot === 'incomplete_application') badge = { label: 'Applied', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
                        else if (slot === 'saved_goal')          badge = { label: 'Saved',   cls: 'bg-blue-50 text-blue-700 border-blue-200' };
                        else if (slot === 'agent_c_primary')     badge = { label: 'Recommended', cls: 'bg-violet-50 text-violet-700 border-violet-200' };
                        else if ((rec.score ?? 0) > 0.80)        badge = { label: 'High Interest', cls: 'bg-amber-50 text-amber-700 border-amber-200' };
                        return (
                          <div key={rec.product_id} className="flex flex-col gap-1.5 p-3 rounded-xl border bg-slate-50 min-w-[110px] flex-1">
                            <p className="text-[11px] font-semibold text-slate-800 leading-tight truncate">{rec.product_name ?? rec.product_id}</p>
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full border self-start ${badge.cls}`}>{badge.label}</span>
                            <div className="w-full h-1 bg-slate-200 rounded-full overflow-hidden">
                              <div className="h-full bg-violet-400 rounded-full" style={{ width: `${Math.round((rec.score ?? 0.5) * 100)}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="border-t border-slate-100" />

                  {/* ── Sub-section 2: Next Visit Directive ── */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Pin className="w-4 h-4 text-slate-400" />
                      <p className="text-xs font-bold uppercase tracking-wider text-slate-600">Next Visit Directive</p>
                    </div>

                    {nextVisitLoading && !nextVisitResult && (
                      <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Analyzing behavioral signals from impression ledger…
                      </div>
                    )}

                    {nextVisitResult && (
                      <AnimatePresence mode="wait">
                        <motion.div
                          key="nv-result"
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="space-y-3"
                        >
                          {nextVisitResult.next_visit_directives.priority_pin_product_id ? (
                            <div className={`rounded-xl border p-4 ${nextVisitResult.diverges_from_current ? 'border-amber-300 bg-amber-50' : 'border-emerald-200 bg-emerald-50'}`}>
                              <div className="flex items-start justify-between gap-4">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1.5">
                                    {nextVisitResult.diverges_from_current ? (
                                      <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-100 border border-amber-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                                        <Zap className="w-2.5 h-2.5" /> Override
                                      </span>
                                    ) : (
                                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                                        <CheckCircle2 className="w-2.5 h-2.5" /> Aligned
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-sm font-bold text-slate-900 leading-snug">
                                    {liveStack.find(r => r.product_id === nextVisitResult.next_visit_directives.priority_pin_product_id)?.product_name
                                      ?? nextVisitResult.next_visit_directives.priority_pin_product_id}
                                  </p>
                                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                                    {nextVisitResult.next_visit_directives.priority_pin_reason}
                                  </p>
                                  {nextVisitResult.diverges_from_current && nextVisitResult.divergence_explanation && (
                                    <p className="text-[11px] text-amber-700 mt-1.5 italic">{nextVisitResult.divergence_explanation}</p>
                                  )}
                                </div>
                                <div className="shrink-0 text-right">
                                  <p className="text-2xl font-black text-slate-900 leading-none">{(nextVisitResult.affinity_analysis?.affinity_score ?? 0).toFixed(2)}</p>
                                  <p className="text-[10px] text-slate-400 mt-0.5">affinity</p>
                                  {nextVisitResult.next_visit_directives.recommended_channel && (
                                    <span className="inline-block mt-1.5 text-[10px] px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
                                      {nextVisitResult.next_visit_directives.recommended_channel.replace(/_/g, ' ')}
                                    </span>
                                  )}
                                </div>
                              </div>
                              {nextVisitResult.affinity_analysis.signal_summary && (
                                <div className="mt-3 pt-3 border-t border-black/5">
                                  <p className="text-xs text-slate-500 italic">{nextVisitResult.affinity_analysis.signal_summary}</p>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-500">
                              No product reached the affinity threshold from the current impression ledger.
                            </div>
                          )}

                          {/* Signal weight legend */}
                          <div className="flex flex-wrap gap-1.5">
                            {[
                              { label: 'Form fill', w: '1.0' },
                              { label: 'Time >90s', w: '0.70' },
                              { label: 'Click apply', w: '0.60' },
                              { label: 'Learn more', w: '0.35' },
                              { label: 'Time 30-90s', w: '0.25' },
                              { label: 'Page view', w: '0.10' },
                            ].map(s => (
                              <span key={s.label} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 border border-slate-200">
                                {s.label} <span className="font-mono font-bold text-slate-700">{s.w}</span>
                              </span>
                            ))}
                          </div>
                        </motion.div>
                      </AnimatePresence>
                    )}
                  </div>

                  {/* ── Sub-section 3: Multi-Touch Attribution ── */}
                  {channelAttribution && Object.keys(channelAttribution).length > 0 && (
                    <>
                      <div className="border-t border-slate-100" />
                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <BarChart2 className="w-4 h-4 text-slate-400" />
                          <p className="text-xs font-bold uppercase tracking-wider text-slate-600">Channel Attribution</p>
                          <span className="text-[11px] text-slate-400">How conversions were won</span>
                        </div>
                        <div className="space-y-2">
                          {Object.entries(channelAttribution)
                            .filter(([, pct]) => pct > 0)
                            .sort(([, a], [, b]) => b - a)
                            .map(([ch, pct], idx) => (
                              <div key={ch} className="flex items-center gap-3">
                                <span className="text-[11px] text-slate-600 w-20 shrink-0">{CHANNEL_LABELS[ch] ?? ch}</span>
                                <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full rounded-full ${CHANNEL_COLORS[ch] ?? 'bg-slate-400'}`}
                                    style={{ width: `${Math.round(pct * 100)}%` }}
                                  />
                                </div>
                                <span className="text-[11px] font-mono text-slate-600 w-8 text-right">{Math.round(pct * 100)}%</span>
                                {idx === 0 && (
                                  <span className="text-[10px] font-bold text-violet-700 bg-violet-50 border border-violet-200 px-1.5 py-0.5 rounded-full shrink-0">WINNING</span>
                                )}
                              </div>
                            ))}
                        </div>
                        {(agentCExpId || mtaExplanation) && (
                          <div className="mt-3 rounded-xl bg-slate-50 border border-slate-200 px-3 py-2.5 space-y-1">
                            {agentCExpId && (
                              <p className="text-[10px] text-slate-400 font-mono">
                                {agentCExpId}{agentCPValue != null ? ` · p = ${agentCPValue.toFixed(6)}` : ''}
                              </p>
                            )}
                            {mtaExplanation && (
                              <p className="text-xs text-slate-700 leading-relaxed italic">{mtaExplanation}</p>
                            )}
                          </div>
                        )}
                      </div>
                    </>
                  )}

                </div>
              </section>
            )}

          </motion.div>
        )}
    </div>
  );
}

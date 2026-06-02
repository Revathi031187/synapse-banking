import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Bot,
  Users,
  User,
  Loader2,
  Trash2,
  Sparkles,
  CreditCard,
  ArrowRight,
  LayoutGrid,
} from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';
import { useSessionStorageState } from '../../hooks/useSessionStorageState';

const API_BASE = getBankingApiBase();

const AGENT_D_UI_KEY = 'banking-agent-d-v1';
const DEFAULT_AGENT_D_UI = {
  mode: 'customer' as 'persona' | 'customer',
  personaId: '',
  customerId: '',
  persistedOrchestrate: null as { customerId: string; response: unknown } | null,
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

export default function BankingAgentD() {
  const queryClient = useQueryClient();
  const [ui, setUi] = useSessionStorageState(AGENT_D_UI_KEY, DEFAULT_AGENT_D_UI);
  const { mode, personaId, customerId, persistedOrchestrate } = ui;

  const personasQuery = useQuery({
    queryKey: ['banking-personas-d'],
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
        setUi((prev) => ({ ...prev, persistedOrchestrate: { customerId: cid, response: payload } }));
        queryClient.invalidateQueries({ queryKey: ['banking-agent-d-directives-b', cid] });
        queryClient.invalidateQueries({ queryKey: ['banking-agent-d-directives-b'] });
      }
    },
  });

  const resetLedgerMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_d/ledger/${customerId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Reset failed');
      return res.json();
    },
    onSuccess: () => {
      orchestrateMutation.reset();
      setUi((prev) => ({ ...prev, persistedOrchestrate: null }));
    },
  });

  const cidKey = String(customerId).trim();
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
  }>;
  const bRecs = sv?.agent_b_product_recommendations ?? [];
  const cOffer = sv?.agent_c_primary_offer;
  const focus = sv?.focus_product;
  const autoPinnedProductId = (data?.next_visit_directives as { priority_pin_product_id?: string } | undefined)
    ?.priority_pin_product_id;
  const autoPinnedProduct = autoPinnedProductId
    ? liveStack.find((r) => String(r.product_id) === String(autoPinnedProductId)) ??
      ({
        product_id: String(autoPinnedProductId),
        product_name: String(autoPinnedProductId),
      } as (typeof liveStack)[number])
    : null;

  const canLoad = !!customerId;

  return (
    <div className="space-y-6 animate-fadeIn">
        {/* Flow breadcrumb — banking */}
        <nav className="flex flex-wrap items-center gap-1 text-xs md:text-sm text-slate-500">
          <Link to="/banking/data-loader" className="hover:text-emerald-700">
            Data Loader
          </Link>
          <span>/</span>
          <Link to="/banking/agent-a" className="hover:text-emerald-700">
            Agent A
          </Link>
          <span>/</span>
          <Link to="/banking/macro-dashboard" className="hover:text-emerald-700">
            Segments
          </Link>
          <span>/</span>
          <Link to="/banking/agent-b" className="hover:text-emerald-700">
            Agent B
          </Link>
          <span>/</span>
          <Link to="/banking/agent-c" className="hover:text-emerald-700">
            Agent C
          </Link>
          <span>/</span>
          <span className="text-emerald-800 font-semibold">Agent D</span>
        </nav>

        <header className="flex gap-3 items-start">
          <div className="p-3 rounded-2xl bg-emerald-100 text-emerald-800 shadow-sm">
            <Bot className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Agent D: Supervisor</h1>
            <p className="text-slate-600 mt-2 text-sm md:text-base leading-relaxed max-w-3xl">
              <strong>Supervisor view</strong> merges digital signals with Agent B and Agent C, builds a live product
              stack, updates the impression ledger, and issues pin instructions for Agent B.
            </p>
          </div>
        </header>

        {/* Control card — supervisor */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-md p-5 md:p-6 space-y-5">
          {(personasQuery.isError || customersQuery.isError) && (
            <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-amber-900 text-sm">
              Could not load personas or customers. Check that the API is running and{' '}
              <Link to="/banking/agent-a" className="font-semibold underline">
                Agent A
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
                  Banking Agent A (Customer Segmentation)
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
                    <option value="">Run Agent A first — no segments</option>
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
                <select
                  className="w-full border border-slate-300 rounded-xl px-3 py-2.5 bg-white"
                  value={customerId}
                  disabled={segmentCustomersQuery.isLoading}
                  onChange={(e) => {
                    setUi((prev) => ({ ...prev, customerId: e.target.value }));
                    orchestrateMutation.reset();
                  }}
                >
                  {segmentCustomersQuery.isLoading ? (
                    <option value="">Loading customers in segment…</option>
                  ) : segmentCustomers.length === 0 ? (
                    <option value="">No customers in segment (run Agent A)</option>
                  ) : (
                    segmentCustomers.map((c) => (
                      <option key={c.customer_id} value={String(c.customer_id)}>
                        {c.customer_name || c.customer_id} ({c.customer_id})
                      </option>
                    ))
                  )}
                </select>
              </div>
            </div>
          )}

          {mode === 'customer' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Customer</label>
              <select
                className="w-full border border-slate-300 rounded-xl px-3 py-2.5 bg-white max-w-xl"
                value={customerId}
                onChange={(e) => {
                  setUi((prev) => ({ ...prev, customerId: e.target.value }));
                  orchestrateMutation.reset();
                }}
              >
                {customersQuery.isLoading ? (
                  <option value="">Loading customers…</option>
                ) : allCustomers.length === 0 ? (
                  <option value="">No customers — run Agent A first</option>
                ) : (
                  <>
                    <option value="">Select customer…</option>
                    {allCustomers.map((c) => (
                      <option key={c.customer_id} value={String(c.customer_id)}>
                        {c.customer_name || c.customer_id} ({c.customer_id})
                      </option>
                    ))}
                  </>
                )}
              </select>
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
            <button
              type="button"
              disabled={!customerId || resetLedgerMutation.isPending}
              onClick={() => resetLedgerMutation.mutate()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 text-slate-600 text-sm hover:bg-slate-50"
            >
              <Trash2 className="w-4 h-4" />
              Reset impression ledger
            </button>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed border-t border-slate-100 pt-4">
            After Agent D runs, open <strong>Agent B</strong> → <strong>Customer mode</strong> → same customer →{' '}
            <strong>Run recommendations</strong>. The <strong>supervisor focus product</strong> is auto-applied as{' '}
            <strong>#1</strong>. No manual pin required.
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
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <section>
              <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-500" />
                Summary
              </h2>
              <p className="text-sm text-slate-600 mb-4">
                Segment: <strong>{data.persona_name}</strong> · Customer <strong>{data.customer_id}</strong>
              </p>

              {liveStack.length > 0 && (
                <div className="mb-8 rounded-xl border border-emerald-200 bg-emerald-50/40 p-4">
                  <h3 className="text-sm font-bold text-emerald-900 mb-1">
                    Auto-synced to Agent B (#1 pin)
                  </h3>
                  <p className="text-xs text-slate-600 mb-3">
                    Same customer in Agent B (Customer mode) and run recommendations. Agent D automatically pushes
                    the supervisor focus product as <strong>#1</strong> for the next run.
                  </p>
                  {autoPinnedProduct ? (
                    <div className="rounded-lg bg-white border border-slate-200 px-3 py-2 text-sm">
                      <div className="min-w-0">
                        <span className="font-medium text-slate-900">
                          {autoPinnedProduct.product_name || autoPinnedProduct.product_id}
                        </span>
                        <span className="text-xs text-slate-500 font-mono ml-2">{autoPinnedProduct.product_id}</span>
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-600 text-white">
                          AUTO PINNED #1
                        </span>
                        {autoPinnedProduct.supervisor_slot && (
                          <span className="block text-[10px] uppercase text-slate-400 mt-0.5">
                            {String(autoPinnedProduct.supervisor_slot).replace(/_/g, ' ')}
                          </span>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">No auto-pinned product returned in this run.</p>
                  )}
                </div>
              )}

              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                    <CreditCard className="w-4 h-4 text-blue-600" />
                    Agent B: Product recommendations (top 3)
                  </h3>
                  <p className="text-xs text-slate-500 mb-3">{sv.agent_b_note}</p>
                  <div className="grid sm:grid-cols-3 gap-3">
                    {bRecs.map((r: { product_id: string; product_name: string; category?: string; score: number }) => (
                      <div
                        key={r.product_id}
                        className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-blue-200 transition-colors"
                      >
                        <p className="font-semibold text-slate-900 text-sm leading-snug">{r.product_name}</p>
                        <p className="text-xs text-slate-500 mt-1 font-mono">{r.product_id}</p>
                        <p className="text-xs text-blue-700 mt-2">Match score: {(Number(r.score) * 100).toFixed(1)}%</p>
                        <span className="inline-block mt-2 text-[10px] uppercase tracking-wide text-slate-400">
                          {r.category || 'Banking'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-violet-600" />
                    Agent C: Offer engine (primary)
                  </h3>
                  <p className="text-xs text-slate-500 mb-3">{sv.agent_c_note}</p>
                  {cOffer ? (
                    <div className="max-w-md rounded-xl border-2 border-violet-200 bg-gradient-to-br from-violet-50 to-white p-5 shadow-sm">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <span className="text-[10px] font-bold uppercase text-violet-600">Primary offer</span>
                          <p className="font-bold text-slate-900 mt-1">{cOffer.product_name}</p>
                          <p className="text-xs font-mono text-slate-500">{cOffer.product_id}</p>
                        </div>
                        <span className="shrink-0 px-2 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
                          {cOffer.status}
                        </span>
                      </div>
                      {cOffer.reasoning && (
                        <p className="text-xs text-slate-600 mt-3 line-clamp-3">{cOffer.reasoning}</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                      No primary offer returned — eligibility or exclusions may apply. Supervisor still routes Agent B
                      using segment fit.
                    </p>
                  )}
                </div>
              </div>
            </section>

            {/* Supervisor instruction — green panel */}
            <section className="rounded-2xl border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 via-white to-emerald-50/50 p-6 shadow-md">
              <h3 className="text-xs font-bold uppercase tracking-widest text-emerald-800 mb-4 flex items-center gap-2">
                <Bot className="w-4 h-4" />
                Agent D → Supervisor instruction to Agent B (next visit / campaign)
              </h3>

              {focus && (
                <div className="flex flex-col md:flex-row gap-6 items-start">
                  <div className="flex-1 max-w-sm rounded-xl border-2 border-emerald-400 bg-white p-5 shadow-md">
                    <p className="text-[10px] font-bold uppercase text-emerald-700">Focus product</p>
                    <p className="text-lg font-bold text-slate-900 mt-1">{focus.product_name}</p>
                    <p className="text-xs font-mono text-slate-500">{focus.product_id}</p>
                    <span className="inline-block mt-3 px-2 py-1 rounded-lg bg-emerald-600 text-white text-xs font-semibold">
                      Pin #1 next run
                    </span>
                  </div>
                  <div className="flex-1 space-y-3 text-sm text-slate-800 leading-relaxed">
                    <p className="font-semibold text-emerald-900">{sv.supervisor_headline}</p>
                    <p>
                      <BoldParts text={sv.supervisor_detail} />
                    </p>
                    <div className="rounded-xl bg-white/80 border border-emerald-200 p-4 text-xs text-slate-700">
                      <p className="font-bold text-emerald-900 mb-2">Why B and C differ</p>
                      <p>
                        <BoldParts text={sv.why_b_and_c_differ} />
                      </p>
                    </div>
                    <p className="flex items-start gap-2 text-xs text-slate-600 pt-2">
                      <ArrowRight className="w-4 h-4 shrink-0 text-emerald-600 mt-0.5" />
                      <span>
                        <BoldParts text={sv.next_step_hint} />
                      </span>
                    </p>
                  </div>
                </div>
              )}
              {!focus && (
                <p className="text-sm text-slate-600">
                  No focus product pinned — run Agent C with a valid offer or add an incomplete application signal.
                </p>
              )}
            </section>
          </motion.div>
        )}
    </div>
  );
}

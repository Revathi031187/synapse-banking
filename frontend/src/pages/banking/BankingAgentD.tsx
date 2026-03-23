import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  Users,
  User,
  Loader2,
  Trash2,
  Sparkles,
  Bookmark,
  FileWarning,
  MousePointerClick,
  ChevronDown,
  ChevronUp,
  CreditCard,
  ArrowRight,
  LayoutGrid,
  Zap,
  MousePointer2,
} from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';

const API_BASE = getBankingApiBase();

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
  const [mode, setMode] = useState<'persona' | 'customer'>('customer');
  const [personaId, setPersonaId] = useState<string>('');
  const [customerId, setCustomerId] = useState<string>('');
  const [savedGoals, setSavedGoals] = useState<string[]>([]);
  const [abandoned, setAbandoned] = useState<string[]>([]);
  const [clicked, setClicked] = useState<string[]>([]);
  const [pickSaved, setPickSaved] = useState('');
  const [pickAbandoned, setPickAbandoned] = useState('');
  const [pickClicked, setPickClicked] = useState('');
  const [advancedOpen, setAdvancedOpen] = useState(false);

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
      if (k == null || k === '') continue;
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
    if (personas.length && !personaId) setPersonaId(String(personas[0].id));
  }, [personas, personaId]);

  React.useEffect(() => {
    if (mode !== 'persona' || !personaId || !segmentCustomersQuery.isSuccess) return;
    const list = segmentCustomers;
    if (list.length === 0) {
      setCustomerId('');
      return;
    }
    const inList = list.some((c) => String(c.customer_id) === String(customerId));
    if (!customerId || !inList) {
      setCustomerId(String(list[0].customer_id));
    }
  }, [mode, personaId, segmentCustomersQuery.isSuccess, segmentCustomers, customerId]);

  const productsQuery = useQuery({
    queryKey: ['banking-products-d'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/products`);
      if (!res.ok) throw new Error('products');
      return res.json();
    },
  });
  const products = useMemo(() => {
    const raw = productsQuery.data?.products ?? [];
    return Array.isArray(raw) ? raw : [];
  }, [productsQuery.data]);

  const orchestrateMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_d/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: customerId,
          saved_goals: savedGoals,
          incomplete_applications: abandoned,
          clicked_product_ids: clicked,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Load failed');
      }
      return res.json();
    },
  });

  const resetLedgerMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_d/ledger/${customerId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Reset failed');
      return res.json();
    },
    onSuccess: () => orchestrateMutation.reset(),
  });

  const nextBestMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_d/next-best`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: customerId, top_n: 10 }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || 'Next-best failed');
      return j;
    },
  });

  const clickProductMutation = useMutation({
    mutationFn: async (productId: string) => {
      const res = await fetch(`${API_BASE}/api/banking/agent_d/click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: customerId, product_id: productId }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || 'Click failed');
      return j;
    },
  });

  const data = orchestrateMutation.data?.data;
  const sv = data?.supervisor_view;
  const liveStack = (data?.live_recommendations ?? []) as Array<{
    product_id: string;
    product_name?: string;
    supervisor_slot?: string;
  }>;
  const bRecs = sv?.agent_b_product_recommendations ?? [];
  const cOffer = sv?.agent_c_primary_offer;
  const journey = sv?.digital_journey_signals;
  const focus = sv?.focus_product;

  const addPid = (list: string[], setList: (v: string[]) => void, pid: string) => {
    const p = pid.trim();
    if (!p || list.includes(p)) return;
    setList([...list, p]);
  };

  const canLoad = !!customerId;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-emerald-50/40 pb-16">
      <div className="max-w-4xl mx-auto px-4 md:px-6 pt-6 space-y-6">
        {/* Flow breadcrumb — banking */}
        <nav className="flex flex-wrap items-center gap-1 text-xs md:text-sm text-slate-500">
          <Link to="/banking" className="hover:text-emerald-700">
            Dashboard
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
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900">Agent D: Banking orchestration</h1>
            <p className="text-slate-600 mt-2 text-sm md:text-base leading-relaxed max-w-3xl">
              <strong>Next-best</strong> blends Agent B + C with wishlist & incomplete applications, and won&apos;t
              repeat products you saw but didn&apos;t engage until you click. <strong>Supervisor view</strong> below
              summarizes B/C and issues pin instructions for Agent B.
            </p>
          </div>
        </header>

        {/* Next-best real-time engine */}
        <section className="rounded-2xl border-2 border-blue-200 bg-gradient-to-br from-blue-50/80 to-white shadow-md p-5 md:p-6 space-y-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-blue-100 text-blue-700">
              <Zap className="w-6 h-6" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-bold text-slate-900">Next-best products (real-time)</h2>
              <p className="text-sm text-slate-600 mt-1">
                Run <strong>Agent A</strong> first; <strong>Agent B</strong> and <strong>C</strong> power ranking and
                offers. Data tables: <code className="text-xs bg-slate-100 px-1 rounded">wishlist.csv</code>,{' '}
                <code className="text-xs bg-slate-100 px-1 rounded">incomplete_applications.csv</code>, and persisted{' '}
                <code className="text-xs bg-slate-100 px-1 rounded">recommendation_impressions.csv</code>.
              </p>
            </div>
          </div>
          <p className="text-xs text-slate-600 bg-white/80 border border-slate-200 rounded-lg px-3 py-2">
            Products recommended but <strong>not</strong> clicked stay excluded on the next run. Use{' '}
            <strong>Mark engaged</strong> after the customer opens or applies — then that product can surface again.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={!customerId || nextBestMutation.isPending}
              onClick={() => nextBestMutation.mutate()}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {nextBestMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              Get next-best recommendations
            </button>
            {nextBestMutation.data?.uses_agent_b && (
              <span className="text-xs font-semibold px-2 py-1 rounded-full bg-emerald-100 text-emerald-800">
                Uses Agent B
              </span>
            )}
            {nextBestMutation.data?.uses_agent_c && (
              <span className="text-xs font-semibold px-2 py-1 rounded-full bg-violet-100 text-violet-800">
                Uses Agent C
              </span>
            )}
            {nextBestMutation.data?.sources_used?.length > 0 && (
              <span className="text-xs text-slate-500">
                Sources: {nextBestMutation.data.sources_used.join(', ')}
              </span>
            )}
          </div>
          {nextBestMutation.isError && (
            <p className="text-sm text-red-600">{(nextBestMutation.error as Error).message}</p>
          )}
          {nextBestMutation.data?.excluded_count != null && nextBestMutation.data.excluded_count > 0 && (
            <p className="text-sm text-amber-800">
              <strong>{nextBestMutation.data.excluded_count}</strong> product(s) hidden until engaged (prior
              impressions).
            </p>
          )}
          {nextBestMutation.data?.no_repeat_message && (
            <p className="text-xs text-slate-600 italic border-l-4 border-blue-300 pl-3">
              {nextBestMutation.data.no_repeat_message}
            </p>
          )}
          {nextBestMutation.data?.recommendations?.length > 0 && (
            <ul className="space-y-2">
              {nextBestMutation.data.recommendations.map(
                (r: {
                  product_id: string;
                  product_name: string;
                  recommendation_reason?: string;
                  score?: number;
                }) => (
                  <li
                    key={r.product_id}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-3 rounded-xl border border-slate-200 bg-white"
                  >
                    <div>
                      <p className="font-semibold text-slate-900">{r.product_name}</p>
                      <p className="text-xs font-mono text-slate-500">{r.product_id}</p>
                      <p className="text-sm text-blue-800 mt-1">{r.recommendation_reason}</p>
                    </div>
                    <button
                      type="button"
                      disabled={clickProductMutation.isPending}
                      onClick={async () => {
                        try {
                          await clickProductMutation.mutateAsync(r.product_id);
                          nextBestMutation.mutate();
                        } catch {
                          /* toast optional */
                        }
                      }}
                      className="shrink-0 inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-blue-300 text-blue-700 text-sm font-medium hover:bg-blue-50"
                    >
                      <MousePointer2 className="w-4 h-4" />
                      Mark engaged
                    </button>
                  </li>
                )
              )}
            </ul>
          )}
        </section>

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
                  setMode('persona');
                  orchestrateMutation.reset();
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
                  setMode('customer');
                  orchestrateMutation.reset();
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
                    setPersonaId(e.target.value);
                    setCustomerId('');
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
                    setCustomerId(e.target.value);
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
                  setCustomerId(e.target.value);
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

          {/* Optional banking signals */}
          <div className="border border-dashed border-slate-200 rounded-xl overflow-hidden">
            <button
              type="button"
              onClick={() => setAdvancedOpen(!advancedOpen)}
              className="w-full flex items-center justify-between px-4 py-3 text-left text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              <span>Optional: simulate digital journey signals</span>
              {advancedOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            <AnimatePresence>
              {advancedOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-slate-100 bg-slate-50/80 px-4 py-4 space-y-4"
                >
                  <p className="text-xs text-slate-500">
                    Model <strong>incomplete applications</strong> (abandoned card/loan application),{' '}
                    <strong>saved goals</strong> (watchlist), or <strong>in-app engagement</strong>. Leave empty to
                    mirror &quot;no application on file&quot; — supervisor then aligns with Agent C.
                  </p>
                  <div className="grid md:grid-cols-3 gap-3">
                    {[
                      {
                        label: 'Incomplete applications',
                        icon: FileWarning,
                        color: 'rose',
                        list: abandoned,
                        set: setAbandoned,
                        pick: pickAbandoned,
                        setPick: setPickAbandoned,
                      },
                      {
                        label: 'Saved goals / watchlist',
                        icon: Bookmark,
                        color: 'amber',
                        list: savedGoals,
                        set: setSavedGoals,
                        pick: pickSaved,
                        setPick: setPickSaved,
                      },
                      {
                        label: 'Digital engagement',
                        icon: MousePointerClick,
                        color: 'emerald',
                        list: clicked,
                        set: setClicked,
                        pick: pickClicked,
                        setPick: setPickClicked,
                      },
                    ].map((col) => (
                      <div key={col.label} className="text-sm space-y-2">
                        <div className={`flex items-center gap-1 font-medium text-slate-800`}>
                          <col.icon className="w-4 h-4" />
                          {col.label}
                        </div>
                        <select
                          className="w-full border rounded-lg px-2 py-1.5 text-xs"
                          value={col.pick}
                          onChange={(e) => col.setPick(e.target.value)}
                        >
                          <option value="">Add product…</option>
                          {products.map((p: { product_id: string; product_name: string }) => (
                            <option key={p.product_id} value={p.product_id}>
                              {p.product_name}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          className="text-xs px-2 py-1 rounded bg-white border"
                          onClick={() => col.pick && addPid(col.list, col.set, col.pick)}
                        >
                          Add
                        </button>
                        <div className="flex flex-wrap gap-1">
                          {col.list.map((id) => (
                            <span
                              key={id}
                              className="text-xs px-2 py-0.5 bg-white border rounded flex items-center gap-1"
                            >
                              {id}
                              <button type="button" onClick={() => col.set(col.list.filter((x) => x !== id))}>
                                ×
                              </button>
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

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
            After Agent D runs, open <strong>Agent B</strong> → <strong>Customer mode</strong> → same customer → enable{' '}
            <strong>Apply Agent D supervisor directives</strong> → Run recommendations. The{' '}
            <strong>supervisor focus product</strong> (incomplete application or Agent C primary) is pinned{' '}
            <strong>#1</strong>. No need to re-run Agent A.
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
                    Click the product to pin #1 in Agent B
                  </h3>
                  <p className="text-xs text-slate-600 mb-3">
                    Same customer → Agent B (Customer mode) → enable <strong>Apply Agent D supervisor directives</strong>{' '}
                    → Run. The product you click below becomes the <strong>top recommendation</strong>.
                  </p>
                  <ul className="space-y-2 max-h-64 overflow-y-auto">
                    {liveStack.slice(0, 15).map((r) => (
                      <li
                        key={r.product_id}
                        className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-white border border-slate-200 px-3 py-2 text-sm"
                      >
                        <div className="min-w-0">
                          <span className="font-medium text-slate-900">{r.product_name || r.product_id}</span>
                          <span className="text-xs text-slate-500 font-mono ml-2">{r.product_id}</span>
                          {r.supervisor_slot && (
                            <span className="block text-[10px] uppercase text-slate-400 mt-0.5">
                              {String(r.supervisor_slot).replace(/_/g, ' ')}
                            </span>
                          )}
                        </div>
                        <button
                          type="button"
                          disabled={clickProductMutation.isPending}
                          onClick={async () => {
                            try {
                              await clickProductMutation.mutateAsync(r.product_id);
                            } catch {
                              /* handled */
                            }
                          }}
                          className="shrink-0 px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50"
                        >
                          Pin #1 for Agent B
                        </button>
                      </li>
                    ))}
                  </ul>
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

            {/* Digital journey */}
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-bold text-slate-800 mb-3">Digital journey signals (this session)</h3>
              {!journey?.has_incomplete_application &&
                !(journey?.saved_goals_watchlist?.length > 0) &&
                !(journey?.digital_engagement?.length > 0) && (
                  <p className="text-sm text-slate-600 bg-slate-50 rounded-lg px-4 py-6 text-center border border-dashed border-slate-200">
                    <strong>No incomplete application</strong> or other journey flags in this simulation. Supervisor
                    defaults to aligning Agent B with <strong>Agent C&apos;s primary offer</strong> (when available).
                  </p>
                )}
              <div className="space-y-3 text-sm">
                {journey?.incomplete_applications?.length > 0 && (
                  <div className="text-rose-800">
                    <strong>Incomplete application(s):</strong>{' '}
                    {journey.incomplete_applications.map((x: { product_name: string }) => x.product_name).join(', ')}
                  </div>
                )}
                {journey?.saved_goals_watchlist?.length > 0 && (
                  <div className="text-amber-800">
                    <strong>Saved goals:</strong>{' '}
                    {journey.saved_goals_watchlist.map((x: { product_name: string }) => x.product_name).join(', ')}
                  </div>
                )}
                {journey?.digital_engagement?.length > 0 && (
                  <div className="text-emerald-800">
                    <strong>Engaged with:</strong>{' '}
                    {journey.digital_engagement.map((x: { product_name: string }) => x.product_name).join(', ')}
                  </div>
                )}
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
    </div>
  );
}

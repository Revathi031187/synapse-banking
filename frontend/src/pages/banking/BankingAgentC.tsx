import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
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
  Search,
} from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';

const API_BASE = getBankingApiBase();

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

export default function BankingAgentC() {
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [customerSearch, setCustomerSearch] = useState('');
  const [explainOpen, setExplainOpen] = useState(true);
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null);
  const offerCardRef = useRef<HTMLDivElement>(null);

  // Scroll to offer card when customer is selected (e.g. from churn "Get offer")
  useEffect(() => {
    if (!selectedCustomerId) return;
    const t = setTimeout(() => offerCardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 400);
    return () => clearTimeout(t);
  }, [selectedCustomerId]);

  const { data: customersData, isError: customersError, isSuccess: customersSuccess, isLoading: customersLoading } = useQuery({
    queryKey: ['banking-agent-a-customers', 500],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_a/customers?limit=500`);
      if (!res.ok) throw new Error('Failed to fetch customers');
      return res.json();
    },
    retry: false,
  });

  const customers = useMemo(() => {
    const list = (customersData?.data?.customers ?? []) as Array<{
      customer_id: string;
      customer_name: string;
      persona?: string;
      total_deposits?: number;
      digital_engagement?: number;
    }>;
    if (!customerSearch.trim()) return list;
    const q = customerSearch.toLowerCase();
    return list.filter(
      (c) =>
        (c.customer_id && String(c.customer_id).toLowerCase().includes(q)) ||
        (c.customer_name && c.customer_name.toLowerCase().includes(q))
    );
  }, [customersData, customerSearch]);

  const {
    data: offerData,
    isLoading: offerLoading,
    isFetching: offerFetching,
  } = useQuery({
    queryKey: ['banking-one-best-offer', selectedCustomerId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_c/one-best-offer/${selectedCustomerId}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to load offer');
      }
      return res.json();
    },
    enabled: !!selectedCustomerId,
  });

  const { data: churnData } = useQuery({
    queryKey: ['banking-churn-cohort', 'High,Critical', 30],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE}/api/banking/churn-cohort?risk=High,Critical&limit=30&skip=0`
      );
      if (!res.ok) return { cohort: [], total: 0 };
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

  const {
    data: personaOfferData,
    isLoading: personaOfferLoading,
    isFetching: personaOfferFetching,
  } = useQuery({
    queryKey: ['banking-persona-best-offer', selectedPersonaId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/agent_c/persona-best-offer?persona_id=${selectedPersonaId}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to load persona offer');
      }
      return res.json();
    },
    enabled: !!selectedPersonaId,
  });

  const personaOffer = personaOfferData?.data;

  const offer = offerData?.data;
  const cohort = (churnData?.cohort ?? []) as Array<{
    customer_id: string;
    customer_name: string;
    churn_risk_score: number;
    churn_risk_category: string;
    churn_risk_reason?: string;
    reason?: string;
    persona?: string;
    recommended_retention_action?: string;
  }>;

  function churnReasonText(c: (typeof cohort)[0]): string {
    const raw = (c.churn_risk_reason || c.reason || '').trim();
    if (raw) return raw;
    const cat = c.churn_risk_category || 'Elevated';
    const sc = c.churn_risk_score != null ? c.churn_risk_score.toFixed(0) : '—';
    return `${cat} risk (${sc}/100): transaction recency, volume trend, balances vs income, product breadth, and digital engagement.`;
  }

  const selectedCustomer = useMemo(
    () => customers.find((c) => c.customer_id === selectedCustomerId),
    [customers, selectedCustomerId]
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-amber-50/30">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative overflow-hidden rounded-b-3xl bg-gradient-to-br from-violet-600 via-indigo-600 to-blue-700 text-white shadow-xl"
      >
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNiI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMiIvPjwvZz48L2c+PC9zdmc+')] opacity-60" />
        <div className="relative max-w-6xl mx-auto px-6 py-12">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <Sparkles className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Agent C: One Best Offer</h1>
              <p className="text-white/90 text-lg mt-1">
                Hyper-personalized 1:1 offer per customer with full explainability
              </p>
            </div>
          </div>
          <p className="text-white/80 max-w-2xl">
            One recommended product per customer, why the AI chose it, and how to run it across
            channels—so campaigns are actionable for marketing and branch.
          </p>
        </div>
      </motion.div>

      <div className="max-w-6xl mx-auto px-6 py-10">
        {/* Customer selector */}
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.35 }}
          className="mb-10"
        >
          {!customersLoading && (customersError || (customersSuccess && !(customersData?.data?.customers?.length ?? 0))) && (
            <div className="mb-4 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-amber-800 text-sm">
              Run Agent A (Customer Segmentation) and load data first to see customers and one-best-offer.
            </div>
          )}
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Select customer
          </label>
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name or ID..."
              value={customerSearch}
              onChange={(e) => setCustomerSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 rounded-xl border border-slate-200 bg-white shadow-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all"
            />
          </div>
          <div className="mt-2 max-h-56 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            {customers.slice(0, 80).map((c) => (
              <button
                key={c.customer_id}
                type="button"
                onClick={() => setSelectedCustomerId(c.customer_id)}
                className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-0 ${
                  selectedCustomerId === c.customer_id ? 'bg-violet-50 text-violet-800' : ''
                }`}
              >
                <User className="w-5 h-5 text-slate-400 flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-slate-900 truncate">{c.customer_name}</p>
                  <p className="text-sm text-slate-500 truncate">{c.customer_id} · {c.persona ?? '—'}</p>
                </div>
                {selectedCustomerId === c.customer_id && (
                  <div className="w-2 h-2 rounded-full bg-violet-500" />
                )}
              </button>
            ))}
          </div>
        </motion.section>

        {/* One best offer card */}
        <AnimatePresence mode="wait">
          {!selectedCustomerId ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/50 p-12 text-center"
            >
              <Target className="w-14 h-14 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500 font-medium">Select a customer to see their one best offer</p>
              <p className="text-slate-400 text-sm mt-1">Recommendation, score, reason, and channel plan</p>
            </motion.div>
          ) : offerLoading || offerFetching ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="rounded-2xl bg-white border border-slate-200 shadow-lg p-12 flex flex-col items-center justify-center min-h-[320px]"
            >
              <Loader2 className="w-12 h-12 text-violet-500 animate-spin mb-4" />
              <p className="text-slate-600 font-medium">Computing best offer for {selectedCustomer?.customer_name ?? selectedCustomerId}...</p>
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
              <div className="rounded-2xl bg-white border border-slate-200 shadow-xl overflow-hidden">
                <div className="bg-gradient-to-r from-violet-500/10 via-indigo-500/10 to-blue-500/10 px-6 py-4 border-b border-slate-100">
                  <p className="text-sm font-medium text-slate-600">One best offer</p>
                  <p className="text-xl font-bold text-slate-900 mt-0.5">
                    {selectedCustomer?.customer_name ?? selectedCustomerId} · {offer.persona}
                  </p>
                </div>
                <div className="p-6 flex flex-wrap gap-6">
                  <div className="flex-1 min-w-[260px]">
                    <div className="rounded-xl bg-slate-50 p-5 border border-slate-100">
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                        Recommended product
                      </p>
                      <p className="text-2xl font-bold text-slate-900">{offer.offer.product_name}</p>
                      <p className="text-slate-600 mt-1">{offer.offer.category}</p>
                      <div className="mt-4 flex items-center gap-2">
                        <span
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-violet-100 text-violet-800"
                        >
                          Score {(offer.score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-slate-600 mt-4 text-sm leading-relaxed">{offer.reason}</p>
                    </div>
                  </div>
                  <div className="flex-1 min-w-[200px]">
                    {(offer.best_channel || offer.best_channel_reason) && (
                      <div className="mb-3 rounded-lg bg-violet-50 border border-violet-100 px-3 py-2">
                        <p className="text-xs font-semibold uppercase tracking-wider text-violet-600">Best channel</p>
                        <p className="font-semibold text-violet-900 capitalize">
                          {(offer.best_channel ?? '').replace(/_/g, ' ')}
                        </p>
                        {offer.best_channel_reason && (
                          <p className="text-sm text-violet-700 mt-0.5">{offer.best_channel_reason}</p>
                        )}
                      </div>
                    )}
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                      All channels (order)
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {(offer.channels ?? []).slice(0, 4).map((ch: { channel: string; priority?: number; label?: string }) => (
                        <span
                          key={ch.channel}
                          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-100 text-slate-700 text-sm font-medium"
                        >
                          {channelIcons[ch.channel] ?? <Mail className="w-4 h-4" />}
                          {ch.label ?? (ch.channel ?? '').replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                    {(offer.churn_risk_score != null && offer.churn_category) && (
                      <div className="mt-4 flex items-center gap-2 text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                        <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                        <span className="text-sm font-medium">
                          Churn risk: {offer.churn_category} ({offer.churn_risk_score?.toFixed(0)})
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Explainability */}
                <div className="border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setExplainOpen(!explainOpen)}
                    className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-slate-50 transition-colors"
                  >
                    <span className="font-semibold text-slate-800">How the AI got here</span>
                    {explainOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </button>
                  <AnimatePresence>
                    {explainOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className="overflow-hidden"
                      >
                        <div className="px-6 pb-6 space-y-4">
                          <div className="rounded-xl bg-indigo-50/80 p-4 border border-indigo-100">
                            <p className="text-sm font-semibold text-indigo-900 mb-2 flex items-center gap-2">
                              <TrendingUp className="w-4 h-4" /> Why this offer
                            </p>
                            <ul className="list-disc list-inside space-y-1 text-slate-700 text-sm leading-relaxed">
                              {formatExplanation(offer.explainability?.why_this_offer).length > 0
                                ? formatExplanation(offer.explainability?.why_this_offer).map((line, i) => (
                                    <li key={i}>{line.replace(/^•\s*/, '')}</li>
                                  ))
                                : <li>—</li>}
                            </ul>
                          </div>
                          <div className="rounded-xl bg-emerald-50/80 p-4 border border-emerald-100">
                            <p className="text-sm font-semibold text-emerald-900 mb-2 flex items-center gap-2">
                              <Shield className="w-4 h-4" /> Why our AI
                            </p>
                            <ul className="list-disc list-inside space-y-1 text-slate-700 text-sm leading-relaxed">
                              {formatExplanation(offer.explainability?.why_our_ai).length > 0
                                ? formatExplanation(offer.explainability?.why_our_ai).map((line, i) => (
                                    <li key={i}>{line.replace(/^•\s*/, '')}</li>
                                  ))
                                : <li>—</li>}
                            </ul>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              ref={offerCardRef}
              key="no-offer"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-2xl bg-amber-50 border border-amber-200 p-8 text-center"
            >
              <AlertTriangle className="w-12 h-12 text-amber-600 mx-auto mb-3" />
              <p className="font-medium text-amber-900">No offer available</p>
              <p className="text-amber-800 text-sm mt-1">{offer?.reason ?? 'Try another customer.'}</p>
              {(offer?.churn_category === 'High' || offer?.churn_category === 'Critical') && (
                <p className="text-amber-700 text-sm mt-3 font-medium">
                  For high churn risk, prioritize retention outreach (outbound call or branch).
                </p>
              )}
              {offer?.best_channel && (
                <p className="text-amber-700 text-sm mt-2">
                  Best channel: {String(offer.best_channel).replace(/_/g, ' ')} — {offer.best_channel_reason ?? ''}
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Persona-level best offer */}
        {customersSuccess && (customersData?.data?.customers?.length ?? 0) > 0 && (
          <motion.section
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.35 }}
            className="mt-12"
          >
            <h2 className="text-xl font-bold text-slate-800 mb-2">Best offer by segment (persona)</h2>
            <p className="text-slate-600 text-sm mb-4">
              One representative best offer for the whole segment—for segment-level campaigns.
            </p>
            <div className="flex flex-wrap items-center gap-4 mb-4">
              <label className="text-sm font-medium text-slate-700">Persona</label>
              <select
                value={selectedPersonaId ?? ''}
                onChange={(e) => setSelectedPersonaId(e.target.value || null)}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 shadow-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
              >
                <option value="">Select a segment</option>
                {personas.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.size} customers)
                  </option>
                ))}
              </select>
            </div>
            {selectedPersonaId && (
              <>
                {personaOfferLoading || personaOfferFetching ? (
                  <div className="rounded-2xl bg-white border border-slate-200 shadow-lg p-12 flex flex-col items-center justify-center min-h-[200px]">
                    <Loader2 className="w-10 h-10 text-violet-500 animate-spin mb-3" />
                    <p className="text-slate-600 text-sm">Loading persona best offer...</p>
                  </div>
                ) : personaOffer?.offer ? (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-2xl bg-white border border-indigo-200 shadow-lg overflow-hidden"
                  >
                    <div className="bg-indigo-50 px-6 py-3 border-b border-indigo-100">
                      <p className="text-sm font-medium text-indigo-800">
                        {personaOffer.persona_name} · {personaOffer.segment_size} customers
                      </p>
                      <p className="text-xs text-indigo-600 mt-0.5">
                        Representative: {personaOffer.representative_customer_name} ({personaOffer.representative_customer_id})
                      </p>
                    </div>
                    <div className="p-6 flex flex-wrap gap-6">
                      <div className="flex-1 min-w-[220px]">
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Segment best offer</p>
                        <p className="text-xl font-bold text-slate-900">{personaOffer.offer.product_name}</p>
                        <p className="text-slate-600">{personaOffer.offer.category}</p>
                        <span className="inline-flex items-center mt-2 px-3 py-1 rounded-full text-sm font-semibold bg-indigo-100 text-indigo-800">
                          Score {(personaOffer.score * 100).toFixed(0)}%
                        </span>
                        <p className="text-slate-600 mt-3 text-sm">{personaOffer.reason}</p>
                      </div>
                      <div className="flex-1 min-w-[180px]">
                        {personaOffer.best_channel && (
                          <div className="mb-2 rounded-lg bg-indigo-50 px-2 py-1.5">
                            <p className="text-xs font-semibold text-indigo-700">Best channel: {(personaOffer.best_channel ?? '').replace(/_/g, ' ')}</p>
                            {personaOffer.best_channel_reason && (
                              <p className="text-xs text-indigo-600 mt-0.5">{personaOffer.best_channel_reason}</p>
                            )}
                          </div>
                        )}
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Channels</p>
                        <div className="flex flex-wrap gap-2">
                          {(personaOffer.channels ?? []).slice(0, 4).map((ch: { channel: string; label?: string }) => (
                            <span key={ch.channel} className="inline-flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-100 text-slate-700 text-xs font-medium">
                              {channelIcons[ch.channel] ?? <Mail className="w-3 h-3" />}
                              {ch.label ?? ch.channel.replace('_', ' ')}
                            </span>
                          ))}
                        </div>
                        <p className="text-slate-500 text-xs mt-3">{personaOffer.note?.replace(/\*\*/g, '')}</p>
                      </div>
                    </div>
                  </motion.div>
                ) : (
                  <div className="rounded-2xl bg-amber-50 border border-amber-200 p-6 text-center">
                    <p className="text-amber-800 text-sm">{personaOffer?.reason ?? 'No offer for this segment.'}</p>
                  </div>
                )}
              </>
            )}
          </motion.section>
        )}

        {/* Churn cohort */}
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.35 }}
          className="mt-14"
        >
          <h2 className="text-xl font-bold text-slate-800 mb-2 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            High churn risk customers
          </h2>
          <p className="text-slate-600 text-sm mb-4">
            Target these customers with Agent C one-best-offer for retention.
          </p>
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Customer</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Segment</th>
                    <th className="text-right py-3 px-4 font-semibold text-slate-700">Risk score</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-700 min-w-[200px] max-w-md">
                      Reason
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Suggested action</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {cohort.slice(0, 15).map((c) => (
                    <tr
                      key={c.customer_id}
                      className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <p className="font-medium text-slate-900">{c.customer_name}</p>
                        <p className="text-slate-500 text-xs">{c.customer_id}</p>
                      </td>
                      <td className="py-3 px-4 text-slate-600">{c.persona ?? '—'}</td>
                      <td className="py-3 px-4 text-right">
                        <span
                          className={`font-semibold ${
                            c.churn_risk_category === 'Critical'
                              ? 'text-red-600'
                              : c.churn_risk_category === 'High'
                              ? 'text-amber-600'
                              : 'text-slate-600'
                          }`}
                        >
                          {c.churn_risk_score?.toFixed(0) ?? '—'}
                        </span>
                        <span className="text-slate-400 ml-1 text-xs">{c.churn_risk_category}</span>
                      </td>
                      <td
                        className="py-3 px-4 text-slate-600 text-xs leading-snug align-top max-w-md"
                        title={churnReasonText(c)}
                      >
                        {churnReasonText(c)}
                      </td>
                      <td className="py-3 px-4 text-slate-600 text-xs">
                        {c.recommended_retention_action?.replace(/_/g, ' ') ?? '—'}
                      </td>
                      <td className="py-3 px-4">
                        <button
                          type="button"
                          onClick={() => setSelectedCustomerId(c.customer_id)}
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
            {cohort.length === 0 && (
              <div className="py-12 text-center text-slate-500">
                Run Agent A and load data with transactions to see churn-risk cohort.
              </div>
            )}
          </div>
        </motion.section>
      </div>
    </div>
  );
}

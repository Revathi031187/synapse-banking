import { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, TrendingUp, ChevronLeft, ChevronRight, Info,
  AlertTriangle, Star, PenSquare, Database, X,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

// ─── Types ──────────────────────────────────────────────────────────────────
// A per-factor entry from Banking12FactorScorer.score_product()'s breakdown —
// same shape Agent B's Recommender tab uses for its "How is Suitability Score
// calculated?" panel.
interface FactorDetail {
  score: number;
  weight: number;
  raw_score?: number;
  calculation?: string;
  explanation?: string;
}
interface TopProduct {
  rank: number;
  product_id: string;
  name: string;
  category: string | null;
  subcategory: string | null;
  description: string | null;
  annual_fee: number | null;
  monthly_fee: number | null;
  interest_rate: number | null;
  min_balance: number | null;
  score_pct: number;               // Agent B's real 12-factor score (0-100), rule-based, persona mode
  match_level: string | null;      // e.g. "Perfect Match", "Great Match"
  rank_explanation: string | null;
  llm_rationale: string | null;
  detailed_calculation: Record<string, FactorDetail> | null;
}
type OfferProduct = TopProduct;
interface SegmentData {
  id: string;
  name: string;
  short_code: string;
  count: number;
  pct_of_base: number;
  avg_balance: number;
  avg_income: number;
  avg_credit_score: number;
  digital_adoption_pct: number;
  cross_sell_pct: number;
  churn_pct: number;
  health: 'growing' | 'stable' | 'at-risk' | string;
  description: string;
  top_products: TopProduct[];
  featured_offer: string;
  offer_product: OfferProduct | null;
  ad_spend_persona: string;
  representative_customer_id: string | null;
}
interface Portfolio {
  total_customers: number;
  avg_balance: number;
  cross_sell_pct: number;
  churn_pct: number;
}
interface ChannelMetric {
  spend_usd: number;
  attributed_revenue_usd: number;
  roas: number;
}
interface AdSpendMetrics {
  personas: Record<string, Record<string, ChannelMetric>>;
  summary: {
    total_spend_usd: number;
    total_revenue_usd: number;
    blended_roas: number;
    total_roi_pct: number;
    reallocation_opportunity_usd: number;
  };
}
interface MonthlyRow { month: number; month_name: string; spend_usd: number; revenue_usd: number }
interface AdSpendMonthly { data: Record<string, Record<string, MonthlyRow[]>> }

// ─── Constants ──────────────────────────────────────────────────────────────
const CHANNELS = ['in_app', 'email', 'sms', 'branch'];
const CHANNEL_LABELS: Record<string, string> = { in_app: 'In-App', email: 'Email', sms: 'SMS', branch: 'Branch' };

// Segment identity colors. Agent A's cluster names are freshly LLM-generated on
// every run, so they can't be looked up in a fixed name → color map (that map
// would silently miss any name it wasn't written for, leaving `background`
// undefined and white text invisible on the page's white background — the bug
// that prompted this fix). Hashing the name into a fixed palette instead
// guarantees every segment always resolves to a real, visible color.
const SEGMENT_PALETTE = ['#5A7A2E', '#1B3C8C', '#0C7A6A', '#7127B0', '#0E9B6A', '#B45309', '#BE185D'];
function colorForSegment(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  return SEGMENT_PALETTE[hash % SEGMENT_PALETTE.length];
}

// Segment descriptions are LLM-generated multi-sentence paragraphs — trim to
// the first 1-2 sentences for the header; line-clamp is a CSS safety net for
// any sentence that's still too long on its own.
function shortDescription(desc: string): string {
  if (!desc) return desc;
  const sentences = desc.match(/[^.!?]+[.!?]+/g) || [desc];
  return sentences.slice(0, 2).join(' ').trim();
}

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// ─── Format helpers ─────────────────────────────────────────────────────────
function fmtUSD(n: number): string {
  if (Math.abs(n) >= 1_000_000) return '$' + (n / 1_000_000).toFixed(n % 1_000_000 === 0 ? 0 : 1) + 'M';
  if (Math.abs(n) >= 1000) return '$' + Math.round(n / 1000) + 'K';
  return '$' + Math.round(n);
}
function fmtInt(n: number): string { return Math.round(n).toLocaleString('en-US'); }
function churnTone(pct: number): 'good' | 'warning' | 'critical' {
  return pct >= 25 ? 'critical' : pct >= 14 ? 'warning' : 'good';
}
function roasTone(roas: number): 'good' | 'warning' | 'critical' {
  return roas >= 3.5 ? 'good' : roas >= 2.2 ? 'warning' : 'critical';
}
function roasLabel(roas: number): string {
  return roas >= 3.5 ? 'Opportunity' : roas >= 2.2 ? 'Mixed' : 'Underperform';
}

const TONE_CLASSES: Record<string, string> = {
  good: 'bg-green-50 text-green-700',
  warning: 'bg-amber-50 text-amber-700',
  critical: 'bg-red-50 text-red-700',
};
const TONE_TEXT: Record<string, string> = {
  good: 'text-green-600',
  warning: 'text-amber-600',
  critical: 'text-red-600',
};
const TONE_STRIP: Record<string, string> = {
  good: 'bg-green-500',
  warning: 'bg-amber-500',
  critical: 'bg-red-500',
};

// ─── Small shared UI pieces ─────────────────────────────────────────────────
function KpiTile({
  label, value, caption, tone, highlight, tip,
}: { label: string; value: string; caption: string; tone?: 'good' | 'warning' | 'critical'; highlight?: boolean; tip?: string }) {
  const stripColor = highlight ? 'bg-amber-500' : tone ? TONE_STRIP[tone] : null;
  return (
    <div className={`bg-white border rounded-xl shadow-sm overflow-hidden ${highlight ? 'border-amber-300' : 'border-gray-200'}`}>
      {stripColor && <div className={`h-1 ${stripColor}`} />}
      <div className={`p-4 ${highlight ? 'bg-gradient-to-b from-amber-50 to-white' : ''}`}>
        <div className="flex items-center gap-1.5 mb-2">
          <p className="text-[10.5px] font-bold uppercase tracking-wide text-gray-400">{label}</p>
          {tip && <InfoTip text={tip} />}
        </div>
        <div className={`text-[22px] font-extrabold tabular-nums tracking-tight ${tone ? TONE_TEXT[tone] : 'text-gray-900'}`}>{value}</div>
        <p className="text-[11px] text-gray-400 mt-0.5">{caption}</p>
      </div>
    </div>
  );
}

// Hover-to-explain bubble used next to KPIs, chart titles, and section headers —
// tells a marketer (not a data analyst) what a number means and where it comes
// from (which agent / which data file) without cluttering the UI permanently.
const INFO_TIP_WIDTH = 224; // px, matches w-56
const INFO_TIP_VIEWPORT_MARGIN = 8; // px, keep clear of the screen edge

function InfoTip({ text }: { text: string }) {
  const anchorRef = useRef<HTMLSpanElement>(null);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);

  function show() {
    const rect = anchorRef.current?.getBoundingClientRect();
    if (!rect) return;
    // Anchor to the icon's center, then clamp so the (fixed-width) bubble
    // never runs past the left/right edge of the viewport — e.g. for KPIs
    // near the right side of the screen, centering on the icon alone would
    // push the tooltip's right edge off-screen.
    const centerX = rect.left + rect.width / 2;
    const idealLeft = centerX - INFO_TIP_WIDTH / 2;
    const maxLeft = window.innerWidth - INFO_TIP_WIDTH - INFO_TIP_VIEWPORT_MARGIN;
    const clampedLeft = Math.max(INFO_TIP_VIEWPORT_MARGIN, Math.min(idealLeft, maxLeft));
    setPos({ top: rect.top, left: clampedLeft });
  }
  function hide() {
    setPos(null);
  }

  return (
    <span
      ref={anchorRef}
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      <Info tabIndex={0} className="w-3 h-3 text-gray-300 cursor-help" />
      {pos &&
        createPortal(
          <span
            className="fixed w-56 rounded-lg bg-gray-900 text-white text-[11px] leading-snug px-2.5 py-1.5 pointer-events-none transition-opacity"
            style={{
              top: pos.top,
              left: pos.left,
              transform: 'translateY(calc(-100% - 8px))',
              zIndex: 9999,
            }}
          >
            {text}
          </span>,
          document.body,
        )}
    </span>
  );
}

function StatusBadge({ tone, label }: { tone: 'good' | 'warning' | 'critical'; label: string }) {
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full ${TONE_CLASSES[tone]}`}>
      {label}
    </span>
  );
}

function SegmentDot({ name, size = 10 }: { name: string; size?: number }) {
  return <span className="rounded-full flex-shrink-0" style={{ width: size, height: size, background: colorForSegment(name) }} />;
}

// ─── Monthly trend chart (spend bars + revenue line, hover tooltip) ────────
function TrendChart({ spend, revenue, title }: { spend: number[]; revenue: number[]; title: string }) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const W = 720, H = 220, padL = 46, padR = 12, padT = 16, padB = 26;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const maxVal = Math.max(...revenue, ...spend) * 1.15 || 1;
  const n = spend.length;
  const stepX = plotW / n;
  const x = (i: number) => padL + stepX * i + stepX / 2;
  const y = (v: number) => padT + plotH - (v / maxVal) * plotH;

  const revPts = revenue.map((v, i) => [x(i), y(v)] as const);
  const linePath = 'M' + revPts.map(([px, py]) => `${px.toFixed(1)} ${py.toFixed(1)}`).join(' L');
  const areaPath = linePath + ` L${revPts[n - 1][0].toFixed(1)} ${padT + plotH} L${revPts[0][0].toFixed(1)} ${padT + plotH} Z`;
  const barW = Math.min(18, stepX * 0.42);

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[220px] block" role="img" aria-label={title}>
        {[0, 0.5, 1].map((f) => {
          const v = maxVal * f, gy = y(v);
          return (
            <g key={f}>
              <line x1={padL} x2={W - padR} y1={gy} y2={gy} stroke="#EEF1F6" strokeWidth={1} />
              <text x={4} y={gy + 3} fontSize={9.5} fill="#9CA3AF">{fmtUSD(v)}</text>
            </g>
          );
        })}
        <line x1={padL} x2={W - padR} y1={padT + plotH} y2={padT + plotH} stroke="#D1D5DB" strokeWidth={1} />
        {spend.map((v, i) => {
          const by = y(v);
          return (
            <rect key={i} x={x(i) - barW / 2} y={by} width={barW} height={padT + plotH - by} rx={2.5} fill="#CBD5E1" opacity={0.7} />
          );
        })}
        <path d={areaPath} fill="#DBEAFE" opacity={0.6} />
        <path d={linePath} fill="none" stroke="#2563EB" strokeWidth={2.2} strokeLinejoin="round" strokeLinecap="round" />
        {revPts.map(([px, py], i) => (
          <circle key={i} cx={px} cy={py} r={i === n - 1 ? 3.6 : 2.2} fill="#2563EB" />
        ))}
        {MONTH_NAMES.slice(0, n).map((m, i) => (
          <text key={m} x={x(i)} y={H - 6} fontSize={9.5} fill="#9CA3AF" textAnchor="middle">{m}</text>
        ))}
        {hoverIdx !== null && (
          <line x1={x(hoverIdx)} x2={x(hoverIdx)} y1={padT} y2={padT + plotH} stroke="#94A3B8" strokeWidth={1} strokeDasharray="3,3" />
        )}
        <rect
          x={padL} y={padT} width={plotW} height={plotH} fill="transparent"
          onMouseMove={(e) => {
            const rect = (e.target as SVGRectElement).getBoundingClientRect();
            const relX = ((e.clientX - rect.left) / rect.width) * plotW;
            const i = Math.max(0, Math.min(n - 1, Math.round((relX - stepX / 2) / stepX)));
            setHoverIdx(i);
          }}
          onMouseLeave={() => setHoverIdx(null)}
        />
      </svg>
      {hoverIdx !== null && (
        <div
          className="absolute bg-gray-900 text-white text-[11.5px] rounded-lg px-2.5 py-2 pointer-events-none shadow-lg"
          style={{ left: `${(x(hoverIdx) / W) * 100}%`, top: y(Math.max(spend[hoverIdx], revenue[hoverIdx])) - 8, transform: 'translate(-50%, -100%)' }}
        >
          <div className="font-bold mb-1">{MONTH_NAMES[hoverIdx]}</div>
          <div className="flex justify-between gap-3"><span>Spend</span><span>{fmtUSD(spend[hoverIdx])}</span></div>
          <div className="flex justify-between gap-3"><span>Revenue</span><span>{fmtUSD(revenue[hoverIdx])}</span></div>
        </div>
      )}
    </div>
  );
}

function ChannelTable({ rows, subtitle }: { rows: { name: string; roas: number }[]; subtitle: string }) {
  const sorted = [...rows].sort((a, b) => b.roas - a.roas);
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 flex flex-col">
      <div className="flex items-center gap-1.5">
        <p className="text-[14px] font-bold text-gray-900">Channel Performance</p>
        <InfoTip text="ROAS per marketing channel (email, SMS, in-app, branch) — Opportunity ≥3.5×, Mixed 2.2-3.5×, Underperform below that." />
      </div>
      <p className="text-[11.5px] text-gray-400 mb-3">{subtitle}</p>
      <div className="grid grid-cols-[1.3fr_1fr_0.7fr] gap-x-2 text-[10px] font-bold uppercase tracking-wide text-gray-400 pb-2">
        <span>Channel</span><span>Status</span><span className="text-right">ROAS</span>
      </div>
      {sorted.map((c) => (
        <div key={c.name} className="grid grid-cols-[1.3fr_1fr_0.7fr] gap-x-2 items-center py-2.5 border-t border-gray-100 text-[12.5px]">
          <span className="font-semibold text-gray-900">{c.name}</span>
          <StatusBadge tone={roasTone(c.roas)} label={roasLabel(c.roas)} />
          <span className="text-right font-extrabold tabular-nums">{c.roas.toFixed(1)}&times;</span>
        </div>
      ))}
    </div>
  );
}

// ─── Data hooks ─────────────────────────────────────────────────────────────
function useSegments() {
  return useQuery({
    queryKey: ['dashboard-segments'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/dashboard/segments`);
      if (!res.ok) throw new Error('Failed to load segment data');
      const json = await res.json();
      return json as { ready: boolean; segments?: SegmentData[]; portfolio?: Portfolio };
    },
    staleTime: 60_000,
  });
}
function useAdSpendMetrics(enabled: boolean) {
  return useQuery({
    queryKey: ['ad-spend-metrics'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/ad_spend/metrics`);
      if (!res.ok) throw new Error('Failed to load ad spend metrics');
      return (await res.json()) as AdSpendMetrics;
    },
    enabled,
    staleTime: 60_000,
  });
}
function useAdSpendMonthly(enabled: boolean) {
  return useQuery({
    queryKey: ['ad-spend-monthly'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/ad_spend/monthly`);
      if (!res.ok) throw new Error('Failed to load ad spend monthly trend');
      return (await res.json()) as AdSpendMonthly;
    },
    enabled,
    staleTime: 60_000,
  });
}

// ─── Aggregation helpers (client-side, over already-real API data) ────────
function blendedChannels(metrics: AdSpendMetrics): { name: string; roas: number }[] {
  return CHANNELS.map((ch) => {
    let spend = 0, revenue = 0;
    Object.values(metrics.personas).forEach((personaChannels) => {
      const m = personaChannels[ch];
      if (m) { spend += m.spend_usd; revenue += m.attributed_revenue_usd; }
    });
    return { name: CHANNEL_LABELS[ch], roas: spend > 0 ? revenue / spend : 0 };
  });
}
function blendedMonthly(monthly: AdSpendMonthly): { spend: number[]; revenue: number[] } {
  const spend = Array(12).fill(0), revenue = Array(12).fill(0);
  Object.values(monthly.data).forEach((personaChannels) => {
    Object.values(personaChannels).forEach((rows) => {
      rows.forEach((r) => { spend[r.month - 1] += r.spend_usd; revenue[r.month - 1] += r.revenue_usd; });
    });
  });
  return { spend, revenue };
}
function personaMonthly(monthly: AdSpendMonthly, persona: string): { spend: number[]; revenue: number[] } {
  const spend = Array(12).fill(0), revenue = Array(12).fill(0);
  const channels = monthly.data[persona] || {};
  Object.values(channels).forEach((rows) => {
    rows.forEach((r) => { spend[r.month - 1] += r.spend_usd; revenue[r.month - 1] += r.revenue_usd; });
  });
  return { spend, revenue };
}
function personaChannels(metrics: AdSpendMetrics, persona: string): { name: string; roas: number }[] {
  const channels = metrics.personas[persona] || {};
  return CHANNELS.filter((ch) => channels[ch]).map((ch) => ({ name: CHANNEL_LABELS[ch], roas: channels[ch].roas }));
}

// ─── Component ──────────────────────────────────────────────────────────────
type Tab = 'overview' | 'marketing';

export default function BankingSegmentDashboard() {
  const [tab, setTab] = useState<Tab>('overview');
  const [segId, setSegId] = useState<string | null>(null);
  const [descExpanded, setDescExpanded] = useState(false);
  const navigate = useNavigate();

  const segmentsQuery = useSegments();
  const adSpendQuery = useAdSpendMetrics(tab === 'marketing');
  const monthlyQuery = useAdSpendMonthly(tab === 'marketing');

  const segments = segmentsQuery.data?.segments ?? [];
  const portfolio = segmentsQuery.data?.portfolio;
  const activeSeg = useMemo(() => segments.find((s) => s.id === segId) ?? null, [segments, segId]);
  const activeIdx = activeSeg ? segments.indexOf(activeSeg) : -1;

  // Collapse the expanded description again whenever the viewed segment changes.
  useEffect(() => { setDescExpanded(false); }, [segId]);

  if (segmentsQuery.isLoading) {
    return <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">Loading segment data…</div>;
  }
  if (segmentsQuery.isError) {
    return (
      <div className="flex-1 flex items-center justify-center text-center px-6">
        <div>
          <p className="text-gray-700 font-semibold mb-1">Couldn't load segment data</p>
          <p className="text-gray-400 text-sm">Make sure the backend API is running, then refresh.</p>
        </div>
      </div>
    );
  }
  if (segmentsQuery.data?.ready === false || segments.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-center px-6">
        <div className="max-w-md">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mx-auto mb-4">
            <Database className="w-6 h-6 text-blue-600" />
          </div>
          <p className="text-gray-900 font-bold text-[15px] mb-2">No segment data yet</p>
          <p className="text-gray-500 text-[13.5px] leading-relaxed mb-5">
            This dashboard shows real figures from Agent A's customer clusters. Load the banking dataset and run
            clustering first, then come back — every number here will reflect the actual customer segments.
          </p>
          <button
            onClick={() => navigate('/banking/data-loader')}
            className="bg-blue-600 text-white text-[13.5px] font-semibold px-4 py-2.5 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go to Data Loader →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex overflow-hidden min-h-0 bg-gray-50">

      {/* Vertical tab rail (Overview / Marketing Performance) */}
      <nav className="w-48 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col py-4">
        <p className="px-4 pb-2 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Dashboard</p>
        {(['overview', 'marketing'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex items-center gap-2.5 mx-2 px-3 py-2.5 rounded-lg text-[13.5px] font-semibold text-left transition-colors ${
              tab === t ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            {t === 'overview' ? <LayoutDashboard className="w-4 h-4 flex-shrink-0" /> : <TrendingUp className="w-4 h-4 flex-shrink-0" />}
            {t === 'overview' ? 'Overview' : 'Marketing Performance'}
          </button>
        ))}
      </nav>

      {/* Right side: segment rail (fixed) + scrollable content */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0">

        {/* Top strip — segment/cluster rail only */}
        <div className="bg-white border-b border-gray-200 flex-shrink-0">
          <div className="px-6 py-2.5 flex gap-2 overflow-x-auto">
            <button
              onClick={() => setSegId(null)}
              className={`flex items-center gap-2 flex-shrink-0 rounded-full px-3 py-1.5 text-[12.5px] font-semibold border ${
                segId === null ? 'bg-blue-50 border-blue-300 text-gray-900' : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-300'
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600" />
              All Segments <span className="text-gray-400 tabular-nums">{fmtInt(portfolio?.total_customers ?? 0)}</span>
            </button>
            {segments.map((s) => (
              <button
                key={s.id}
                onClick={() => setSegId(s.id)}
                className={`flex items-center gap-2 flex-shrink-0 rounded-full px-3 py-1.5 text-[12.5px] font-semibold border ${
                  segId === s.id ? 'bg-blue-50 border-blue-300 text-gray-900' : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                <SegmentDot name={s.name} size={9} />
                {s.name} <span className="text-gray-400 tabular-nums">{fmtInt(s.count)}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Scrollable content — segment header now scrolls with everything else */}
        <div className="flex-1 overflow-y-auto bg-gradient-to-b from-blue-50/50 via-gray-50 to-gray-50">
          <div className="max-w-6xl mx-auto px-6 py-6">

            {activeSeg && (
              <div className="bg-white border border-gray-200 rounded-xl shadow-sm mb-6 overflow-hidden">
                <div className="h-1.5" style={{ background: colorForSegment(activeSeg.name) }} />
                <div className="px-5 py-4 flex gap-4 items-start">
                  <div
                    className="w-11 h-11 rounded-xl flex-shrink-0 flex items-center justify-center font-black text-white text-sm shadow-sm"
                    style={{ background: colorForSegment(activeSeg.name) }}
                  >
                    {activeSeg.short_code}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 text-[10.5px] font-bold uppercase tracking-wide text-gray-400 mb-1">
                      <button onClick={() => setSegId(segments[(activeIdx - 1 + segments.length) % segments.length].id)} className="w-5 h-5 rounded border border-gray-200 flex items-center justify-center hover:border-gray-400">
                        <ChevronLeft className="w-3 h-3" />
                      </button>
                      SEGMENT {activeIdx + 1} OF {segments.length}
                      <button onClick={() => setSegId(segments[(activeIdx + 1) % segments.length].id)} className="w-5 h-5 rounded border border-gray-200 flex items-center justify-center hover:border-gray-400">
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>
                    <h2 className="text-[19px] font-extrabold text-gray-900 mb-1">{activeSeg.name}</h2>
                    {(() => {
                      const short = shortDescription(activeSeg.description);
                      const hasMore = short !== activeSeg.description;
                      return (
                        <div className="max-w-[62ch]">
                          <p className={`text-[13px] text-gray-500 ${descExpanded ? 'leading-relaxed' : 'leading-snug line-clamp-2'}`}>
                            {descExpanded ? activeSeg.description : short}
                          </p>
                          {hasMore && (
                            <button
                              onClick={() => setDescExpanded((v) => !v)}
                              className="text-[12.5px] text-blue-600 font-semibold hover:underline mt-0.5"
                            >
                              {descExpanded ? 'less' : 'more'}
                            </button>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                  <span className="flex-shrink-0 text-[11.5px] font-bold text-gray-600 bg-gray-50 border border-gray-200 rounded-full px-3 py-1.5 tabular-nums">
                    {fmtInt(activeSeg.count)} customers
                  </span>
                </div>
              </div>
            )}

            {tab === 'overview'
              ? (activeSeg ? <OverviewSegment seg={activeSeg} /> : <OverviewAll segments={segments} portfolio={portfolio!} onSelect={setSegId} />)
              : (
                <MarketingTab
                  seg={activeSeg}
                  segments={segments}
                  metrics={adSpendQuery.data}
                  monthly={monthlyQuery.data}
                  loading={adSpendQuery.isLoading || monthlyQuery.isLoading}
                  onSelect={setSegId}
                />
              )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Overview: all segments ─────────────────────────────────────────────────
function OverviewAll({ segments, portfolio, onSelect }: { segments: SegmentData[]; portfolio: Portfolio; onSelect: (id: string) => void }) {
  const topOffers = [...segments].sort((a, b) => b.count - a.count).slice(0, 5);
  return (
    <>
      <SectionHead
        title="Portfolio Overview" hint={`All ${segments.length} segments · ${fmtInt(portfolio.total_customers)} customers`}
        tip="Blended across all of Agent A's real customer segments for this dataset."
      />
      <div className="grid grid-cols-4 gap-3 mb-8">
        <KpiTile
          label="Addressable Customers" value={fmtInt(portfolio.total_customers)} caption="across 5 personas"
          tip="Total customers across all Agent A segments — the full portfolio this platform can target."
        />
        <KpiTile
          label="Avg. Customer Value" value={fmtUSD(portfolio.avg_balance)} caption="avg. deposit balance, blended"
          tip="Average deposit balance across every customer in the portfolio."
        />
        <KpiTile
          label="Offer Receptivity" value={`${portfolio.cross_sell_pct.toFixed(0)}%`} caption="propensity to accept a targeted offer"
          tip="Average cross-sell receptivity score across the whole portfolio — how likely customers are to say yes to a new offer."
        />
        <KpiTile
          label="Churn Risk" value={`${portfolio.churn_pct.toFixed(0)}%`} tone={churnTone(portfolio.churn_pct)}
          caption={churnTone(portfolio.churn_pct) === 'good' ? 'within healthy range' : 'needs attention'}
          tip="Average churn probability across the whole portfolio, from our churn model."
        />
      </div>

      <SectionHead
        title="Segment Snapshot" hint="Click a segment to see its full detail"
        tip="One card per Agent A segment — best offer is Agent B's #1-ranked persona-mode recommendation for that segment."
      />
      <div className="grid grid-cols-5 gap-3 mb-8">
        {segments.map((s) => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className="text-left bg-white border border-gray-200 border-l-[3px] rounded-xl shadow-sm p-4 hover:border-gray-300 hover:shadow-md transition-all"
            style={{ borderLeftColor: colorForSegment(s.name) }}
          >
            <div className="flex items-center gap-2 mb-3">
              <SegmentDot name={s.name} />
              <div>
                <div className="text-[13px] font-bold text-gray-900 leading-tight">{s.name}</div>
                <div className="text-[11px] text-gray-400 tabular-nums">{fmtInt(s.count)} customers</div>
              </div>
            </div>
            <div className="flex justify-between text-[11.5px] text-gray-500 mb-1">
              <span>Best offer</span><span className="truncate ml-2 text-gray-700 font-medium">{s.offer_product?.name ?? s.top_products[0]?.name ?? '—'}</span>
            </div>
            <div className="flex justify-between items-center text-[11.5px] text-gray-500 mb-2">
              <span>Churn risk</span><StatusBadge tone={churnTone(s.churn_pct)} label={`${s.churn_pct.toFixed(0)}%`} />
            </div>
            <span className="text-[11.5px] font-bold text-blue-600">View details &rarr;</span>
          </button>
        ))}
      </div>

      <SectionHead
        title="Top Offers Across Segments" hint="Ranked by segment size"
        tip="Each segment's #1 Agent B persona-mode recommendation, sorted by how many customers are in that segment."
      />
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 overflow-x-auto">
        <div className="grid grid-cols-[2fr_1.3fr_0.9fr_0.9fr] gap-x-3 min-w-[520px] text-[10px] font-bold uppercase tracking-wide text-gray-400 pb-2">
          <span>Offer</span><span>Persona</span><span className="text-right">Segment Size</span><span className="text-right">Avg. Balance</span>
        </div>
        {topOffers.map((s) => (
          <div key={s.id} className="grid grid-cols-[2fr_1.3fr_0.9fr_0.9fr] gap-x-3 min-w-[520px] items-center py-2.5 border-t border-gray-100 text-[12.5px]">
            <span className="font-bold text-gray-900 truncate">{s.featured_offer.split(' — ')[0] || s.offer_product?.name || '—'}</span>
            <span className="flex items-center gap-1.5 text-gray-600 truncate"><SegmentDot name={s.name} size={8} />{s.name}</span>
            <span className="text-right tabular-nums text-gray-700">{fmtInt(s.count)}</span>
            <span className="text-right tabular-nums font-bold text-gray-900">{fmtUSD(s.avg_balance)}</span>
          </div>
        ))}
      </div>
    </>
  );
}

// ─── Overview: single segment ───────────────────────────────────────────────
function matchScoreTone(pct: number): string {
  if (pct >= 70) return 'text-emerald-700 bg-emerald-50';
  if (pct >= 45) return 'text-blue-600 bg-blue-50';
  return 'text-amber-700 bg-amber-50';
}

// products.csv has no real fee-waiver conditions we surface elsewhere; keep
// factor labels human-readable rather than raw snake_case column names.
function factorLabel(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

// Agent B's rank_explanation/reason strings carry **bold**/*italic* Markdown
// emphasis markers meant for a Markdown-aware renderer — this plain <p> isn't
// one, so strip them rather than showing literal asterisks to the user.
function stripMdEmphasis(s: string): string {
  return s.replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1');
}

function ProductFactChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5">
      <p className="text-[9.5px] font-bold uppercase text-gray-400 mb-0.5">{label}</p>
      <p className="text-[14px] font-extrabold tabular-nums">{value}</p>
    </div>
  );
}

// Detail popup for a single recommended product — the full description, fees,
// rank rationale, and 12-factor breakdown that the compact card intentionally
// leaves out (see ProductCompactCard). Same plain-CSS overlay convention as
// frontend/src/components/CustomerInsightModal.tsx.
function ProductDetailModal({ product, onClose }: { product: TopProduct; onClose: () => void }) {
  const factors = product.detailed_calculation
    ? Object.entries(product.detailed_calculation).filter(([k]) => k !== 'total_score' && k !== 'total_percentage')
    : [];
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[85vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-5 flex items-start justify-between gap-3 flex-shrink-0" style={{ background: 'linear-gradient(120deg, #1B3C8C, #2563EB)' }}>
          <div className="min-w-0">
            <p className="text-[10.5px] font-bold uppercase tracking-wide text-white/75 mb-1">{product.subcategory || product.category || 'Product'}</p>
            <h3 className="text-[18px] font-extrabold text-white leading-tight">{product.name}</h3>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white hover:bg-white/20 rounded-full p-1.5 transition-colors flex-shrink-0">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto min-h-0 p-6 space-y-5">
          <div className="flex items-center gap-2">
            <span className={`text-[12px] font-bold rounded-full px-3 py-1 ${matchScoreTone(product.score_pct)}`}>
              {product.score_pct.toFixed(0)}% match
            </span>
            {product.match_level && <span className="text-[12px] font-semibold text-gray-500">{product.match_level}</span>}
          </div>

          {product.description && <p className="text-[13px] text-gray-600 leading-relaxed">{product.description}</p>}

          <div className="grid grid-cols-2 gap-2.5">
            <ProductFactChip label="Annual Fee" value={product.annual_fee ? `$${product.annual_fee}` : 'None'} />
            {!!product.interest_rate && <ProductFactChip label="Rate" value={`${(product.interest_rate * 100).toFixed(2)}% APY`} />}
            {product.min_balance != null && <ProductFactChip label="Min. Balance" value={fmtUSD(product.min_balance)} />}
            {!!product.monthly_fee && <ProductFactChip label="Monthly Fee" value={`$${product.monthly_fee}`} />}
          </div>

          {product.rank_explanation && (
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
              <p className="text-[10px] font-bold uppercase text-blue-500 mb-1">Why #{product.rank}</p>
              <p className="text-[12.5px] text-blue-900 leading-relaxed">{stripMdEmphasis(product.rank_explanation)}</p>
            </div>
          )}

          {product.llm_rationale && (
            <p className="text-[12.5px] text-gray-500 italic leading-relaxed">&ldquo;{product.llm_rationale}&rdquo;</p>
          )}

          {factors.length > 0 && (
            <div>
              <p className="text-[10.5px] font-bold uppercase tracking-wide text-gray-400 mb-2">12-Factor Match Breakdown</p>
              <div className="space-y-1.5">
                {factors.map(([key, f]) => (
                  <div key={key} className="flex items-center gap-2">
                    <span className="text-[11.5px] text-gray-600 w-40 flex-shrink-0 truncate">{factorLabel(key)}</span>
                    <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.max(0, Math.min(100, (f.raw_score ?? 0) * 100))}%` }}
                      />
                    </div>
                    <span className="text-[11px] font-bold text-gray-700 w-10 text-right tabular-nums">{Math.round((f.raw_score ?? 0) * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ProductCompactCard({ product, onClick }: { product: TopProduct; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white border border-gray-200 rounded-xl shadow-sm p-3 hover:border-blue-300 hover:shadow-md transition-all"
    >
      <div className="flex justify-between items-start gap-3">
        <div className="min-w-0">
          <p className="text-[13.5px] font-bold text-gray-900 truncate">{product.name}</p>
          <span className="text-[10.5px] font-bold uppercase tracking-wide text-blue-500">{product.subcategory || product.category || 'Product'}</span>
        </div>
        <span className={`text-[11px] font-bold rounded-full px-2 py-0.5 flex-shrink-0 whitespace-nowrap ${matchScoreTone(product.score_pct)}`}>
          {product.score_pct.toFixed(0)}% match
        </span>
      </div>
      <div className="flex items-center gap-2 mt-1.5 text-[10.5px] text-gray-400">
        <span>{product.annual_fee ? `$${product.annual_fee}/yr` : 'No annual fee'}</span>
        {!!product.interest_rate && (
          <>
            <span>·</span>
            <span>{(product.interest_rate * 100).toFixed(2)}% APY</span>
          </>
        )}
        <span className="ml-auto text-blue-600 font-semibold">Details →</span>
      </div>
    </button>
  );
}

function OverviewSegment({ seg }: { seg: SegmentData }) {
  const navigate = useNavigate();
  const offer = seg.offer_product;
  const [detailProduct, setDetailProduct] = useState<TopProduct | null>(null);

  return (
    <>
      <div className="grid grid-cols-4 gap-3 mb-8">
        <KpiTile
          label="Segment Size" value={fmtInt(seg.count)} caption={`${seg.pct_of_base.toFixed(0)}% of portfolio`}
          tip="Agent A's real cluster size — the number of customers K-Prototypes clustering assigned to this segment."
        />
        <KpiTile
          label="Avg. Customer Value" value={fmtUSD(seg.avg_balance)} caption="avg. deposit balance"
          tip="Average total deposit balance across this segment's real customers, from Agent A's cluster characteristics."
        />
        <KpiTile
          label="Offer Receptivity" value={`${seg.cross_sell_pct.toFixed(0)}%`} caption="propensity to accept a targeted offer"
          tip="Average cross-sell receptivity score for this segment's customers — how likely they are to say yes to a new product offer."
        />
        <KpiTile
          label="Churn Risk" value={`${seg.churn_pct.toFixed(0)}%`} tone={churnTone(seg.churn_pct)}
          caption={churnTone(seg.churn_pct) === 'good' ? 'within healthy range' : churnTone(seg.churn_pct) === 'warning' ? 'elevated — monitor' : 'high — prioritize retention'}
          tip="Average churn probability across this segment's real customers, from our churn model."
        />
      </div>

      <div className="grid grid-cols-[1.15fr_0.85fr] gap-5 items-stretch">
        <div className="flex flex-col h-[420px]">
          <SectionHead
            title="Recommended Products"
            hint="Agent B · rule-based · persona mode"
            tip="The exact same products and scores Agent B's Recommender tab computes for this persona (rule-based scoring, all product types) — click a product for full details."
          />
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden flex flex-col flex-1 min-h-0">
            <div className="flex-1 overflow-y-auto min-h-0 p-3 space-y-2">
              {seg.top_products.length === 0 && (
                <p className="text-[12.5px] text-gray-400 p-2">No eligible products found for this segment.</p>
              )}
              {seg.top_products.slice(0, 3).map((p) => (
                <ProductCompactCard key={p.rank} product={p} onClick={() => setDetailProduct(p)} />
              ))}
            </div>
            <div className="p-3 border-t border-gray-100 flex-shrink-0">
              <button
                onClick={() => navigate(`/banking/agent-b?persona=${encodeURIComponent(seg.id)}&category=`)}
                className="w-full flex items-center justify-center gap-1.5 text-[12px] font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg py-2.5 transition-colors"
              >
                View in Recommender
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-col h-[420px]">
          <SectionHead
            title="Best Offer" hint=" "
            tip="Rank #1 from Agent B's persona-mode recommendation list for this segment — the same computation as Recommended Products, just the top result."
          />
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden flex flex-col flex-1 min-h-0">
            <div className="p-4 flex-shrink-0" style={{ background: `linear-gradient(120deg, ${colorForSegment(seg.name)}, #2563EB)` }}>
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <p className="text-[10.5px] font-bold uppercase tracking-wide text-white/75">{offer?.category || 'Featured Offer'}</p>
                {offer && (
                  <span className="text-[10.5px] font-bold text-white bg-white/20 rounded-full px-2 py-0.5 flex-shrink-0 whitespace-nowrap">
                    {offer.score_pct.toFixed(0)}% match
                  </span>
                )}
              </div>
              <p className="text-[15px] font-extrabold text-white leading-tight">{offer?.name || seg.featured_offer.split(' — ')[0]}</p>
              {offer?.subcategory && <p className="text-[11px] text-white/70 mt-0.5">{offer.subcategory}</p>}
            </div>
            <div className="p-4 flex-1 overflow-y-auto min-h-0">
              {offer?.description && <p className="text-[12px] text-gray-500 leading-relaxed mb-3">{offer.description}</p>}
              {offer?.rank_explanation && (
                <p className="text-[11.5px] text-gray-500 leading-relaxed mb-3 bg-gray-50 border border-gray-100 rounded-lg p-2.5">{stripMdEmphasis(offer.rank_explanation)}</p>
              )}
              <div className="grid grid-cols-2 gap-2.5">
                <ProductFactChip label="Est. Reach" value={`${fmtInt(seg.count)} customers`} />
                {!!offer?.interest_rate && <ProductFactChip label="Rate" value={`${(offer.interest_rate * 100).toFixed(2)}% APY`} />}
                <ProductFactChip label="Annual Fee" value={offer?.annual_fee ? `$${offer.annual_fee}` : 'None'} />
                {offer?.min_balance != null && <ProductFactChip label="Min. Balance" value={fmtUSD(offer.min_balance)} />}
              </div>
            </div>
            <div className="p-3 border-t border-gray-100 flex-shrink-0">
              <button
                onClick={() => navigate(`/banking/agent-c?persona=${encodeURIComponent(seg.id)}`)}
                className="w-full flex items-center justify-center gap-1.5 text-[12px] font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg py-2.5 transition-colors"
              >
                View in Offer & Ad Spend
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {detailProduct && <ProductDetailModal product={detailProduct} onClose={() => setDetailProduct(null)} />}
    </>
  );
}

// ─── Marketing tab ───────────────────────────────────────────────────────────
function MarketingTab({
  seg, segments, metrics, monthly, loading, onSelect,
}: {
  seg: SegmentData | null; segments: SegmentData[]; metrics?: AdSpendMetrics; monthly?: AdSpendMonthly;
  loading: boolean; onSelect: (id: string) => void;
}) {
  if (loading || !metrics || !monthly) {
    return <div className="text-center text-gray-400 text-sm py-16">Loading marketing performance…</div>;
  }
  return seg
    ? <MarketingSegment seg={seg} metrics={metrics} monthly={monthly} />
    : <MarketingAll segments={segments} metrics={metrics} monthly={monthly} onSelect={onSelect} />;
}

function MarketingAll({
  segments, metrics, monthly, onSelect,
}: { segments: SegmentData[]; metrics: AdSpendMetrics; monthly: AdSpendMonthly; onSelect: (id: string) => void }) {
  const channels = blendedChannels(metrics);
  const best = channels.reduce((a, b) => (b.roas > a.roas ? b : a));
  const worst = channels.reduce((a, b) => (b.roas < a.roas ? b : a));
  const { spend, revenue } = blendedMonthly(monthly);

  const segRevenue = segments.map((s) => {
    const rev = Object.values(metrics.personas[s.ad_spend_persona] || {}).reduce((sum, m) => sum + m.attributed_revenue_usd, 0);
    return { seg: s, revenue: rev };
  });
  const bestSegment = segRevenue.reduce((a, b) => (b.revenue > a.revenue ? b : a));
  const bestSegmentPct = (bestSegment.revenue / metrics.summary.total_revenue_usd) * 100;

  return (
    <>
      <SectionHead
        title="Marketing Performance" hint="Spend, attributed revenue, and channel performance across all 5 segments"
        tip="Mapped to each segment via its closest matching marketing persona."
      />
      <div className="grid grid-cols-4 gap-3 mb-8">
        <KpiTile
          label="Total Ad Spend" value={fmtUSD(metrics.summary.total_spend_usd)} caption="4 channels · 5 segments"
          tip="Sum of spend across email, SMS, in-app, and branch channels, all segments."
        />
        <KpiTile
          label="Attributed Revenue" value={fmtUSD(metrics.summary.total_revenue_usd)} caption="conversions × product value"
          tip="Revenue attributed to marketing campaigns — conversions multiplied by the value of the product converted."
        />
        <KpiTile
          label="Blended ROAS" value={`${metrics.summary.blended_roas.toFixed(2)}×`} tone={roasTone(metrics.summary.blended_roas)} caption="$ returned per $1 spent"
          tip="Total attributed revenue ÷ total ad spend across the whole portfolio."
        />
        <KpiTile
          label="Reallocation Opportunity" value={fmtUSD(metrics.summary.reallocation_opportunity_usd)} tone="warning" highlight caption="modeled upside from rebalancing"
          tip="Modeled extra revenue if budget shifted from the lowest-ROAS channel toward the highest-ROAS channel."
        />
      </div>

      <SectionHead title="What Needs Your Attention" hint="" tip="Automatically generated from the actual best/worst-performing channel and segment in the data below." />
      <div className="grid grid-cols-3 gap-3 mb-8">
        <InsightCard tone="good" icon={<Star className="w-3.5 h-3.5" />} title={`Move budget into ${best.name}`}>
          <p className="text-[11.5px] text-gray-500 leading-relaxed mb-2">{best.name} returns {best.roas.toFixed(1)}&times; ROAS blended across segments — the strongest channel in the portfolio right now.</p>
          <StatusBadge tone="good" label={`${best.roas.toFixed(1)}× return`} />
        </InsightCard>
        <InsightCard tone="critical" icon={<AlertTriangle className="w-3.5 h-3.5" />} title={`${worst.name} returns the least`}>
          <p className="text-[11.5px] text-gray-500 leading-relaxed mb-2">This channel returns {worst.roas.toFixed(1)}&times; blended — the most room to improve of any channel in the portfolio.</p>
          <StatusBadge tone="critical" label={`${worst.roas.toFixed(1)}× return`} />
        </InsightCard>
        <InsightCard tone="neutral" icon={<PenSquare className="w-3.5 h-3.5" />} title={`${bestSegment.seg.name} is your best segment`}>
          <p className="text-[11.5px] text-gray-500 leading-relaxed mb-2">Just {bestSegment.seg.pct_of_base.toFixed(0)}% of customers, driven mainly through {personaChannels(metrics, bestSegment.seg.ad_spend_persona).sort((a, b) => b.roas - a.roas)[0]?.name}, deliver a disproportionate share of attributed revenue.</p>
          <StatusBadge tone="good" label={`${bestSegmentPct.toFixed(0)}% of revenue`} />
        </InsightCard>
      </div>

      <div className="grid grid-cols-[1.6fr_1fr] gap-4 mb-8 items-stretch">
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
          <div className="flex justify-between items-baseline mb-2">
            <div className="flex items-center gap-1.5">
              <p className="text-[14px] font-bold text-gray-900">Spend vs. Attributed Revenue</p>
              <InfoTip text="Monthly spend (bars) vs. attributed revenue (line), blended across all segments." />
            </div>
            <div className="flex gap-4 text-[11.5px] text-gray-500">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-gray-300" />Spend</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-0.5 rounded-full bg-blue-600" />Attributed Revenue</span>
            </div>
          </div>
          <TrendChart spend={spend} revenue={revenue} title="Spend vs. Attributed Revenue, all segments" />
        </div>
        <ChannelTable rows={channels} subtitle="Blended across all segments" />
      </div>

      <SectionHead
        title="Segment Snapshot" hint="Click a segment to see its own channel breakdown"
        tip="Each segment's single best-performing marketing channel by ROAS."
      />
      <div className="grid grid-cols-5 gap-3">
        {segments.map((s) => {
          const best = [...personaChannels(metrics, s.ad_spend_persona)].sort((a, b) => b.roas - a.roas)[0];
          return (
            <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className="text-left bg-white border border-gray-200 border-l-[3px] rounded-xl shadow-sm p-4 hover:border-gray-300 hover:shadow-md transition-all"
            style={{ borderLeftColor: colorForSegment(s.name) }}
          >
              <div className="flex items-center gap-2 mb-3">
                <SegmentDot name={s.name} />
                <div>
                  <div className="text-[13px] font-bold text-gray-900 leading-tight">{s.name}</div>
                  <div className="text-[11px] text-gray-400 tabular-nums">{fmtInt(s.count)} customers</div>
                </div>
              </div>
              <div className="flex justify-between text-[11.5px] text-gray-500 mb-2">
                <span>Best channel</span><span className="text-gray-700 font-medium">{best ? `${best.name} · ${best.roas.toFixed(1)}×` : '—'}</span>
              </div>
              <span className="text-[11.5px] font-bold text-blue-600">View breakdown &rarr;</span>
            </button>
          );
        })}
      </div>
    </>
  );
}

function MarketingSegment({ seg, metrics, monthly }: { seg: SegmentData; metrics: AdSpendMetrics; monthly: AdSpendMonthly }) {
  const persona = seg.ad_spend_persona;
  const channels = [...personaChannels(metrics, persona)].sort((a, b) => b.roas - a.roas);
  const best = channels[0], worst = channels[channels.length - 1];
  const totalSpend = Object.values(metrics.personas[persona] || {}).reduce((s, m) => s + m.spend_usd, 0);
  const totalRevenue = Object.values(metrics.personas[persona] || {}).reduce((s, m) => s + m.attributed_revenue_usd, 0);
  const roas = totalSpend > 0 ? totalRevenue / totalSpend : 0;
  const { spend, revenue } = personaMonthly(monthly, persona);

  return (
    <>
      <div className="grid grid-cols-3 gap-3 mb-6">
        <KpiTile
          label="Segment Ad Spend" value={fmtUSD(totalSpend)} caption="FY2025 total"
          tip={`Ad spend for the "${persona}" marketing persona this segment maps to.`}
        />
        <KpiTile
          label="Attributed Revenue" value={fmtUSD(totalRevenue)} caption="conversions × product value"
          tip="Revenue attributed to this segment's marketing campaigns — conversions multiplied by product value."
        />
        <KpiTile
          label="Segment ROAS" value={`${roas.toFixed(2)}×`} tone={roasTone(roas)} caption="$ returned per $1 spent"
          tip="This segment's attributed revenue ÷ its ad spend."
        />
      </div>

      {best && worst && (
        <InsightCard tone="neutral" icon={<Star className="w-3.5 h-3.5" />} title={`Best channel: ${best.name} (${best.roas.toFixed(1)}× ROAS)`} wide>
          <p className="text-[11.5px] text-gray-500 leading-relaxed">
            {seg.name}'s outreach performs best through {best.name} and worst through {worst.name} ({worst.roas.toFixed(1)}&times;) — consider shifting incremental budget accordingly.
          </p>
        </InsightCard>
      )}

      <div className="grid grid-cols-[1.6fr_1fr] gap-4 mt-6 items-stretch">
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
          <div className="flex items-center gap-1.5 mb-2">
            <p className="text-[14px] font-bold text-gray-900">Spend vs. Attributed Revenue — {seg.name}</p>
            <InfoTip text={`Monthly spend vs. attributed revenue for the "${persona}" marketing persona.`} />
          </div>
          <TrendChart spend={spend} revenue={revenue} title={`Spend vs. Attributed Revenue, ${seg.name}`} />
        </div>
        <ChannelTable rows={channels} subtitle={`${seg.name} only`} />
      </div>
    </>
  );
}

// ─── Shared bits ─────────────────────────────────────────────────────────────
function SectionHead({ title, hint, tip }: { title: string; hint: string; tip?: string }) {
  return (
    <div className="flex items-baseline justify-between mb-3">
      <div className="flex items-center gap-1.5">
        <h3 className="text-[14.5px] font-bold text-gray-900">{title}</h3>
        {tip && <InfoTip text={tip} />}
      </div>
      <p className="text-[12px] text-gray-400">{hint}</p>
    </div>
  );
}

function InsightCard({
  tone, icon, title, children, wide,
}: { tone: 'good' | 'critical' | 'neutral'; icon: React.ReactNode; title: string; children: React.ReactNode; wide?: boolean }) {
  const borderColor = tone === 'good' ? 'border-l-green-500' : tone === 'critical' ? 'border-l-red-500' : 'border-l-blue-500';
  const iconBg = tone === 'good' ? 'bg-green-50 text-green-600' : tone === 'critical' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600';
  return (
    <div className={`bg-white border border-gray-200 border-l-[3px] ${borderColor} rounded-xl shadow-sm p-4 ${wide ? 'mb-2' : ''}`}>
      <div className="flex items-center gap-2 mb-1.5">
        <span className={`w-5.5 h-5.5 rounded-md flex items-center justify-center ${iconBg}`}>{icon}</span>
        <span className="text-[13px] font-bold text-gray-900">{title}</span>
      </div>
      {children}
    </div>
  );
}

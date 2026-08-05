import React, { useState, useEffect, useRef } from 'react';
import { X } from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────
interface Rec { rank: number; name: string; type: string; desc: string }
interface Segment {
  name: string; short: string; color: string; rgb: string; intentColor: string;
  // raw numeric values drive the count-up animation
  countRaw: number;    // actual customer count
  balanceRaw: number;  // avg balance in dollars (e.g. 184000)
  digitalRaw: number;  // digital adoption 0–100
  intentRaw: number;   // intent score 0–100
  income: string; credit: number; desc: string;
  health: 'growing' | 'stable' | 'at-risk';
  recs: Rec[];
  offer: { headline: string; product: string; sub: string };
}

// ─── Segment data ─────────────────────────────────────────────────────────────
const SEGMENTS: Segment[] = [
  {
    name: 'Retiree Depositor', short: 'RD',
    color: '#5A7A2E', rgb: '90,122,46', intentColor: '#D97706',
    countRaw: 900, balanceRaw: 184000, digitalRaw: 25, intentRaw: 41.7,
    income: '$62K', credit: 779, health: 'stable',
    desc: 'Long-standing loyal customers who prefer in-branch banking and value personal relationships above all else',
    recs: [
      { rank: 1, name: 'Meridian Money Market',  type: 'Savings Account',        desc: 'Competitive yield with full daily liquidity and no lock-in period' },
      { rank: 2, name: 'Meridian 12-Month CD',   type: 'Certificate of Deposit', desc: 'Locked-in guaranteed return — ideal for near-term income needs' },
      { rank: 3, name: 'Meridian 24-Month CD',   type: 'Certificate of Deposit', desc: 'Higher APY for customers comfortable with a two-year horizon' },
    ],
    offer: {
      headline: '+0.20% APY on balances over $25K',
      product: 'Meridian Money Market',
      sub: "An exclusive rate boost for Meridian's most loyal long-term depositors — rewarding tenure with a premium yield.",
    },
  },
  {
    name: 'Wealth Accumulator', short: 'WA',
    color: '#1B3C8C', rgb: '27,60,140', intentColor: '#059669',
    countRaw: 950, balanceRaw: 175000, digitalRaw: 64, intentRaw: 61.7,
    income: '$195K', credit: 808, health: 'growing',
    desc: 'High earners with strong savings discipline who hold multiple Meridian products and pursue long-term wealth goals',
    recs: [
      { rank: 1, name: 'Meridian HELOC',           type: 'Home Equity Line',       desc: 'Flexible access to home equity at competitive variable rates' },
      { rank: 2, name: 'Meridian Roth IRA',        type: 'Retirement Account',     desc: 'Tax-free growth for high earners building long-term wealth' },
      { rank: 3, name: 'Meridian Traditional IRA', type: 'Retirement Account',     desc: 'Pre-tax contributions to reduce current-year income exposure' },
    ],
    offer: {
      headline: '$0 annual fee your first year',
      product: 'Meridian HELOC',
      sub: 'Unlock your home equity with no commitment cost in year one — for customers with strong savings discipline and excellent credit.',
    },
  },
  {
    name: 'Everyday Essential', short: 'EE',
    color: '#0C7A6A', rgb: '12,122,106', intentColor: '#D97706',
    countRaw: 1493, balanceRaw: 52000, digitalRaw: 45, intentRaw: 33.2,
    income: '$73K', credit: 708, health: 'stable',
    desc: 'Core everyday customers relying on checking, savings, and debit — middle-income earners with steady transaction habits',
    recs: [
      { rank: 1, name: 'Meridian FHA Mortgage', type: 'Home Loan',               desc: 'Low down-payment path to homeownership for middle-income earners' },
      { rank: 2, name: 'Meridian Money Market', type: 'Savings Account',          desc: 'Everyday savings with competitive yield and no minimums required' },
      { rank: 3, name: 'Meridian 12-Month CD',  type: 'Certificate of Deposit',   desc: 'A simple guaranteed return for surplus short-term savings' },
    ],
    offer: {
      headline: '4.50% APY for the first 6 months',
      product: 'Meridian Money Market',
      sub: "An introductory rate designed to grow everyday savings — built for Meridian's largest and most active customer segment.",
    },
  },
  {
    name: 'Digital Trendsetter', short: 'DT',
    color: '#7127B0', rgb: '113,39,176', intentColor: '#D97706',
    countRaw: 857, balanceRaw: 42600, digitalRaw: 91, intentRaw: 36.5,
    income: '$83K', credit: 698, health: 'stable',
    desc: 'Mobile-first customers who manage all banking through the app — frequent transactions and high engagement with digital features',
    recs: [
      { rank: 1, name: 'Meridian Roth IRA',    type: 'Retirement Account',     desc: 'Tax-free growth for digitally-engaged earners building long-term wealth' },
      { rank: 2, name: 'Meridian 12-Month CD', type: 'Certificate of Deposit', desc: 'Short-horizon guaranteed return for customers between investments' },
      { rank: 3, name: 'Meridian 24-Month CD', type: 'Certificate of Deposit', desc: 'Higher yield for customers with a two-year savings horizon' },
    ],
    offer: {
      headline: 'No annual fee until you turn 35',
      product: 'Meridian Roth IRA',
      sub: "An age-gated fee waiver for the bank's most digitally engaged segment — removing the barrier to long-term wealth building.",
    },
  },
  {
    name: 'At-Risk Saver', short: 'AR',
    color: '#0E9B6A', rgb: '14,155,106', intentColor: '#DC2626',
    countRaw: 800, balanceRaw: 10000, digitalRaw: 52, intentRaw: 8.0,
    income: '$35K', credit: 568, health: 'at-risk',
    desc: 'Financially stretched customers with limited savings and a higher likelihood of leaving — requiring proactive retention outreach',
    recs: [
      { rank: 1, name: 'Meridian Secured Card', type: 'Secured Credit Card',    desc: 'Build or rebuild credit with a fully secured, low-risk card product' },
      { rank: 2, name: 'Meridian 12-Month CD',  type: 'Certificate of Deposit', desc: 'Preserve and grow limited savings with a guaranteed short-term return' },
      { rank: 3, name: 'Meridian 24-Month CD',  type: 'Certificate of Deposit', desc: 'A longer-term CD for customers establishing a consistent savings habit' },
    ],
    offer: {
      headline: '$0 annual fee for your first year',
      product: 'Meridian Secured Card',
      sub: 'Zero-cost entry into credit building — removing the fee barrier for customers who need a financial fresh start.',
    },
  },
];

// ─── Portfolio totals (computed once) ─────────────────────────────────────────
const PORTFOLIO = (() => {
  const totalCustomers = SEGMENTS.reduce((s, seg) => s + seg.countRaw, 0);
  const totalAUM = SEGMENTS.reduce((s, seg) => s + seg.countRaw * seg.balanceRaw, 0);
  const fmtAUM = totalAUM >= 1e9
    ? '$' + (totalAUM / 1e9).toFixed(1) + 'B'
    : '$' + Math.round(totalAUM / 1e6) + 'M';
  return { totalCustomers, fmtAUM };
})();

// ─── Health badge config ──────────────────────────────────────────────────────
const HEALTH = {
  growing:  { label: '↑ Growing',  bg: 'rgba(16,185,129,0.18)',  text: '#6EE7B7' },
  stable:   { label: '→ Stable',   bg: 'rgba(255,255,255,0.09)', text: 'rgba(255,255,255,0.45)' },
  'at-risk':{ label: '↓ At Risk',  bg: 'rgba(239,68,68,0.18)',   text: '#FCA5A5' },
} as const;

// ─── Count-up hook ────────────────────────────────────────────────────────────
function useCountUp(target: number, duration = 550): number {
  const [current, setCurrent] = useState(target);
  const fromRef = useRef(target);
  const rafRef  = useRef<number>(0);

  useEffect(() => {
    const from = fromRef.current;
    if (from === target) return;
    const start = performance.now();

    const tick = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setCurrent(from + (target - from) * eased);
      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        setCurrent(target);
        fromRef.current = target;
      }
    };

    cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return current;
}

// ─── Format helpers ───────────────────────────────────────────────────────────
function fmtCount(n: number)   { return Math.round(n).toLocaleString(); }
function fmtBalance(n: number) {
  const k = n / 1000;
  return '$' + (k >= 100 ? Math.round(k) : +k.toFixed(1)) + 'K';
}
function fmtPct(n: number)     { return Math.round(n) + '%'; }
function fmtIntent(n: number)  { return n.toFixed(1) + '%'; }

// ─── AnimatedMetric ───────────────────────────────────────────────────────────
function AnimatedMetric({
  raw, fmt, label, color, rgb, segColor,
}: {
  raw: number; fmt: (n: number) => string; label: string;
  color?: string; rgb: string; segColor: string;
}) {
  const animated = useCountUp(raw);
  return (
    <div
      className="rounded-[9px] px-3 py-2.5 transition-all duration-300"
      style={{ background: `rgba(${rgb},0.05)`, border: `1px solid rgba(${rgb},0.12)` }}
    >
      <div
        className="text-[18px] font-extrabold tabular-nums leading-tight"
        style={{ color: color || '#0F172A', letterSpacing: '-0.3px' }}
      >
        {fmt(animated)}
      </div>
      <div className="text-[9px] uppercase tracking-[0.4px] text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}

// ─── Offer Details Modal ───────────────────────────────────────────────────────
function OfferDetailsModal({ seg, onClose }: { seg: Segment; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const h = HEALTH[seg.health];
  const matchedRec = seg.recs.find(r => r.name === seg.offer.product);

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto relative"
        onClick={e => e.stopPropagation()}
      >
        <div
          className="absolute top-0 left-0 right-0 h-[3px]"
          style={{ background: seg.color }}
        />

        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg p-1.5 transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="p-6">
          <div
            className="inline-flex items-center gap-1 text-white text-[9px] font-bold uppercase tracking-[0.7px] px-2.5 py-1 rounded-full mb-3"
            style={{ background: seg.color }}
          >
            ★ Best Offer · {seg.name}
          </div>

          <h3 className="text-[22px] font-extrabold text-gray-900 mb-2 leading-tight" style={{ letterSpacing: '-0.5px' }}>
            {seg.offer.headline}
          </h3>
          <p className="text-[13px] text-gray-600 leading-relaxed mb-5">{seg.offer.sub}</p>

          {/* Product card */}
          <div
            className="rounded-xl p-4 mb-5"
            style={{ background: `rgba(${seg.rgb},0.05)`, border: `1px solid rgba(${seg.rgb},0.15)` }}
          >
            <p className="text-[9px] font-bold uppercase tracking-[0.5px] text-gray-400 mb-1">Featured Product</p>
            <p className="text-[15px] font-bold text-gray-900 mb-0.5">{seg.offer.product}</p>
            {matchedRec && (
              <>
                <p className="text-[10.5px] uppercase tracking-[0.3px] text-gray-400 mb-1.5">{matchedRec.type}</p>
                <p className="text-[12px] text-gray-600 leading-snug">{matchedRec.desc}</p>
              </>
            )}
          </div>

          {/* Segment fit */}
          <p className="text-[10px] font-bold uppercase tracking-[0.8px] text-gray-500 mb-2.5">Segment Fit</p>
          <div className="grid grid-cols-2 gap-2.5 mb-5">
            <div className="rounded-lg px-3 py-2.5 border border-gray-200">
              <p className="text-[15px] font-extrabold text-gray-900 tabular-nums">{fmtBalance(seg.balanceRaw)}</p>
              <p className="text-[9px] uppercase tracking-[0.4px] text-gray-500 mt-0.5">Avg Annual Balance</p>
            </div>
            <div className="rounded-lg px-3 py-2.5 border border-gray-200">
              <p className="text-[15px] font-extrabold text-gray-900 tabular-nums">{seg.credit}</p>
              <p className="text-[9px] uppercase tracking-[0.4px] text-gray-500 mt-0.5">Avg Credit Score</p>
            </div>
            <div className="rounded-lg px-3 py-2.5 border border-gray-200">
              <p className="text-[15px] font-extrabold text-gray-900 tabular-nums">{seg.income}</p>
              <p className="text-[9px] uppercase tracking-[0.4px] text-gray-500 mt-0.5">Avg Income</p>
            </div>
            <div className="rounded-lg px-3 py-2.5 border border-gray-200">
              <p className="text-[15px] font-extrabold text-gray-900 tabular-nums">{fmtIntent(seg.intentRaw)}</p>
              <p className="text-[9px] uppercase tracking-[0.4px] text-gray-500 mt-0.5">Intent Score</p>
            </div>
          </div>

          <div className="flex items-center justify-between mb-5">
            <span className="text-[11px] text-gray-500">Portfolio health</span>
            <span
              className="text-[9px] font-bold px-2 py-1 rounded-full whitespace-nowrap"
              style={{ background: h.bg.includes('rgba(255') ? '#F1F5F9' : h.bg, color: h.bg.includes('rgba(255') ? '#64748B' : h.text }}
            >
              {h.label}
            </span>
          </div>

          <p className="text-[11.5px] text-gray-500 leading-relaxed mb-6">{seg.desc}</p>

          <button
            onClick={onClose}
            className="w-full text-white text-[13px] font-bold px-4 py-2.5 rounded-lg transition-all hover:opacity-90"
            style={{ background: seg.color }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function BankingSegmentDashboard() {
  const [activeIdx, setActiveIdx] = useState(0);
  const [showOfferModal, setShowOfferModal] = useState(false);
  const seg = SEGMENTS[activeIdx];

  return (
    <div className="flex-1 flex overflow-hidden min-h-0">

      {/* ══ LEFT SEGMENT SIDEBAR ════════════════════════════════════════ */}
      <aside className="w-52 flex-shrink-0 bg-[#0C1B2E] border-r border-white/[0.07] flex flex-col">

        <p className="px-4 pt-4 pb-2 text-[13px] font-bold uppercase tracking-widest text-white/70 flex-shrink-0">
          Customer Segments
        </p>

        {/* Segment list — scrolls if needed */}
        <div className="flex-1 overflow-y-auto flex flex-col gap-0.5 px-2 min-h-0">
          {SEGMENTS.map((s, idx) => {
            const h = HEALTH[s.health];
            return (
              <button
                key={s.name}
                onClick={() => setActiveIdx(idx)}
                className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-left transition-all ${
                  activeIdx === idx ? 'bg-white/[0.08]' : 'hover:bg-white/[0.04]'
                }`}
                style={activeIdx === idx ? { boxShadow: `inset 3px 0 0 ${s.color}` } : undefined}
              >
                <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: s.color }} />
                <div className="min-w-0 flex-1">
                  <div className="text-[12.5px] font-semibold text-white/85 leading-tight truncate">{s.name}</div>
                  <div className="text-[10.5px] text-white/40 mt-0.5 tabular-nums">{s.countRaw.toLocaleString()} customers</div>
                </div>
                {/* Health badge */}
                <span
                  className="flex-shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded-full whitespace-nowrap"
                  style={{ background: h.bg, color: h.text }}
                >
                  {h.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* ── Portfolio Totals Footer ── */}
        <div className="flex-shrink-0 border-t border-white/[0.07] px-4 py-3">
          <p className="text-[9px] font-bold uppercase tracking-widest text-white/35 mb-2">Portfolio</p>
          <div className="grid grid-cols-3 gap-1">
            <div>
              <div className="text-[13px] font-extrabold text-white/90 tabular-nums leading-tight">
                {SEGMENTS.length}
              </div>
              <div className="text-[8.5px] text-white/35 uppercase tracking-wide mt-0.5">Segments</div>
            </div>
            <div>
              <div className="text-[13px] font-extrabold text-white/90 tabular-nums leading-tight">
                {(PORTFOLIO.totalCustomers / 1000).toFixed(1)}K
              </div>
              <div className="text-[8.5px] text-white/35 uppercase tracking-wide mt-0.5">Customers</div>
            </div>
            <div>
              <div className="text-[13px] font-extrabold text-white/90 tabular-nums leading-tight">
                {PORTFOLIO.fmtAUM}
              </div>
              <div className="text-[8.5px] text-white/35 uppercase tracking-wide mt-0.5">Total AUM</div>
            </div>
          </div>
        </div>
      </aside>

      {/* ══ CENTER CONTENT ══════════════════════════════════════════════ */}
      <main className="flex-1 min-w-0 bg-[#F5F7FB] flex flex-col overflow-hidden">

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">

          {/* Hero */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 relative overflow-hidden flex-shrink-0">
            <div
              className="absolute top-0 left-0 right-0 h-[3px] transition-colors duration-300"
              style={{ background: seg.color }}
            />
            <div className="flex items-start gap-3.5 mb-4">
              <div
                className="w-11 h-11 rounded-[10px] flex-shrink-0 flex items-center justify-center transition-all duration-300"
                style={{ background: `rgba(${seg.rgb},0.10)`, border: `1.5px solid rgba(${seg.rgb},0.20)` }}
              >
                <span className="text-sm font-black" style={{ color: seg.color }}>{seg.short}</span>
              </div>
              <div>
                <p
                  className="text-[9px] font-bold uppercase tracking-[1.1px] mb-1 transition-colors duration-300"
                  style={{ color: seg.color }}
                >
                  Segment {activeIdx + 1} of 5
                </p>
                <h2
                  className="text-[21px] font-extrabold text-gray-900 leading-tight"
                  style={{ letterSpacing: '-0.4px' }}
                >
                  {seg.name}
                </h2>
                <p className="text-[12px] text-gray-500 mt-1 max-w-[480px] leading-relaxed">{seg.desc}</p>
              </div>
            </div>

            {/* Animated metric grid */}
            <div className="grid grid-cols-4 gap-2">
              <AnimatedMetric raw={seg.countRaw}   fmt={fmtCount}   label="Total Customers"    rgb={seg.rgb} segColor={seg.color} />
              <AnimatedMetric raw={seg.balanceRaw} fmt={fmtBalance} label="Avg Annual Balance"  rgb={seg.rgb} segColor={seg.color} />
              <AnimatedMetric raw={seg.digitalRaw} fmt={fmtPct}     label="Digital Adoption"    rgb={seg.rgb} segColor={seg.color} />
              <AnimatedMetric raw={seg.intentRaw}  fmt={fmtIntent}  label="Intent Score"        rgb={seg.rgb} segColor={seg.color} color={seg.intentColor} />
            </div>
          </div>

          {/* Recommendations */}
          <div className="flex-shrink-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.8px] text-gray-500 mb-2.5">Top 3 Recommendations</p>
            <div className="grid grid-cols-3 gap-2.5">
              {seg.recs.map(rec => {
                const RANK_STYLES = [
                  { bg: 'rgba(251,191,36,0.18)', border: 'rgba(217,119,6,0.35)',  color: '#B45309' }, // gold
                  { bg: 'rgba(148,163,184,0.18)', border: 'rgba(100,116,139,0.30)', color: '#475569' }, // silver
                  { bg: 'rgba(180,83,9,0.13)',    border: 'rgba(146,64,14,0.28)',  color: '#92400E' }, // bronze
                ];
                const rs = RANK_STYLES[(rec.rank - 1) % 3];
                return (
                  <div
                    key={rec.rank}
                    className="bg-white rounded-xl border-[1.5px] border-gray-200 p-3.5 transition-all duration-150 hover:-translate-y-0.5 hover:shadow-md cursor-default"
                    onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = `rgba(${seg.rgb},0.40)`; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = ''; }}
                  >
                    <div
                      className="w-6 h-6 rounded-[6px] flex items-center justify-center text-[11px] font-bold mb-2.5"
                      style={{ background: rs.bg, border: `1px solid ${rs.border}`, color: rs.color }}
                    >
                      {rec.rank}
                    </div>
                    <p className="text-[13px] font-bold text-gray-900 leading-snug mb-1">{rec.name}</p>
                    <p className="text-[10px] uppercase tracking-[0.3px] text-gray-400 mb-2">{rec.type}</p>
                    <p className="text-[11.5px] text-gray-500 leading-snug">{rec.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Offer */}
          <div className="flex-shrink-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.8px] text-gray-500 mb-2.5">Featured Offer</p>
            <div
              className="bg-white rounded-xl p-5 relative overflow-hidden transition-all duration-300"
              style={{ border: `1.5px solid rgba(${seg.rgb},0.28)` }}
            >
              <div
                className="absolute top-0 right-0 w-52 h-full pointer-events-none"
                style={{ background: `radial-gradient(ellipse at top right, rgba(${seg.rgb},0.07), transparent 70%)` }}
              />
              <div
                className="inline-flex items-center gap-1 text-white text-[9px] font-bold uppercase tracking-[0.7px] px-2.5 py-1 rounded-full mb-2 transition-colors duration-300"
                style={{ background: seg.color }}
              >
                ★ Best Offer · {seg.name}
              </div>
              <h3
                className="text-[22px] font-extrabold text-gray-900 mb-1 leading-tight"
                style={{ letterSpacing: '-0.5px' }}
              >
                {seg.offer.headline}
              </h3>
              <p className="text-[12px] text-gray-500 max-w-[520px] leading-relaxed mb-4">{seg.offer.sub}</p>
              <div className="flex items-center gap-2.5">
                <button
                  onClick={() => setShowOfferModal(true)}
                  className="text-white text-[12px] font-bold px-4 py-2 rounded-lg transition-all hover:opacity-90 hover:-translate-y-px active:translate-y-0"
                  style={{ background: seg.color }}
                >
                  View Offer Details →
                </button>
                <span className="text-[11px] text-gray-500 bg-gray-50 border border-gray-200 px-2.5 py-1.5 rounded-md">
                  {seg.offer.product}
                </span>
              </div>
            </div>
          </div>

        </div>
      </main>

      {showOfferModal && (
        <OfferDetailsModal seg={seg} onClose={() => setShowOfferModal(false)} />
      )}

    </div>
  );
}

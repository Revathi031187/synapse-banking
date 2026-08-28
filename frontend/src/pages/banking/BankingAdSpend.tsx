import { useRef, useEffect, useCallback, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, DollarSign, BarChart2, Zap, AlertTriangle, CheckCircle2, ArrowUp, ArrowDown, BarChart, LineChart, ChevronDown } from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';

const API_BASE = getBankingApiBase();

// ── Types ──────────────────────────────────────────────────────────────────────

interface CurveParams { L: number; k: number }

interface ChannelMetricsBase {
  sent: number; converted: number; clicked: number; opened: number;
  spend_usd: number; attributed_revenue_usd: number;
  conversion_rate: number; click_rate: number; open_rate: number;
}

// Paid channel: has a fitted S-curve, an optimal spend, and a reallocation status.
interface PaidChannelMetrics extends ChannelMetricsBase {
  owned_channel: false;
  roas: number; roi_pct: number; cost_per_acquisition: number;
  optimal_spend_usd: number; marginal_roas: number; saturation_pct: number;
  status: 'under' | 'over' | 'optimal'; curve_params: CurveParams;
  // True business ROI (adds underwriting + ops cost and risk-adjusts revenue)
  true_roi_pct: number | null;
  true_roas: number | null;
  business_cost_usd: number | null;
  total_cost_usd: number | null;
  risk_adjusted_revenue_usd: number | null;
}

// Owned channel (e.g. email): $0 media spend — funnel + revenue only, nothing
// to optimize, so no curve/status fields exist on this shape at all.
interface OwnedChannelMetrics extends ChannelMetricsBase {
  owned_channel: true;
}

type ChannelMetrics = PaidChannelMetrics | OwnedChannelMetrics;

interface AdSpendData {
  success: boolean;
  personas: Record<string, Record<string, ChannelMetrics>>;
  summary: {
    total_spend_usd: number; total_revenue_usd: number; owned_channel_revenue_usd: number;
    blended_roas: number; total_roi_pct: number; reallocation_opportunity_usd: number;
  };
  channels: string[]; owned_channels: string[]; persona_list: string[];
  cost_benchmarks: Record<string, number>;
  product_value_benchmarks: Record<string, number>;
  biz_cost_benchmarks: Record<string, number>;
  risk_rate_benchmarks: Record<string, number>;
  dataset_version: 'v1' | 'v2' | null;
  data_source: string;
}

interface MonthlyPoint {
  month: number; month_name: string; sent: number; converted: number;
  spend_usd: number; revenue_usd: number; roas: number; roi_pct: number; marginal_roas: number;
}

interface MonthlyData {
  success: boolean;
  data: Record<string, Record<string, MonthlyPoint[]>>;
}

// ── Constants ──────────────────────────────────────────────────────────────────

// Full registry of every channel id known across v1 and v2 datasets — the
// *active* set to render always comes from the backend's `data.channels`
// (which reflects whichever dataset _resolve_ad_spend_dataset() picked), not
// a hardcoded list here, so the page adapts to v1 (4) or v2 (8) automatically.
// Funnel stage labels are channel-appropriate, not one generic set for every
// channel — a video ad isn't "opened," a podcast spot isn't "clicked," and a
// branch conversation was never "sent." [stage1, stage2, stage3, stage4].
type FunnelLabels = readonly [string, string, string, string];
const DEFAULT_FUNNEL_LABELS: FunnelLabels = ['Sent', 'Opened', 'Clicked', 'Converted'];

const CHANNEL_REGISTRY = [
  { id: 'in_app',            label: 'In-App',            icon: '📱', color: '#5b5fc7', bg: '#eef2ff', border: '#c7d2fe', funnelLabels: ['Sent', 'Opened', 'Tapped', 'Converted'] as FunnelLabels },
  { id: 'email',             label: 'Email',              icon: '📧', color: '#0284c7', bg: '#f0f9ff', border: '#bae6fd', funnelLabels: DEFAULT_FUNNEL_LABELS },
  { id: 'sms',               label: 'SMS',                icon: '💬', color: '#d97706', bg: '#fffbeb', border: '#fde68a', funnelLabels: ['Sent', 'Delivered', 'Clicked', 'Converted'] as FunnelLabels },
  { id: 'branch',            label: 'Branch',             icon: '🏦', color: '#059669', bg: '#f0fdf4', border: '#bbf7d0', funnelLabels: ['Contacted', 'Engaged', 'Interested', 'Converted'] as FunnelLabels },
  { id: 'youtube_ads',       label: 'YouTube Ads',        icon: '▶️', color: '#dc2626', bg: '#fef2f2', border: '#fecaca', funnelLabels: ['Sent', 'Viewed', 'Clicked', 'Converted'] as FunnelLabels },
  { id: 'meta_social_ads',   label: 'Meta Paid Social',   icon: '📸', color: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe', funnelLabels: ['Sent', 'Viewed', 'Clicked', 'Converted'] as FunnelLabels },
  { id: 'google_search_ads', label: 'Google Search Ads',  icon: '🔍', color: '#0d9488', bg: '#f0fdfa', border: '#99f6e4', funnelLabels: ['Sent', 'Viewed', 'Clicked', 'Converted'] as FunnelLabels },
  { id: 'podcast_audio_ads', label: 'Podcast/Audio Ads',  icon: '🎙️', color: '#c2410c', bg: '#fff7ed', border: '#fed7aa', funnelLabels: ['Sent', 'Listened', 'Engaged', 'Converted'] as FunnelLabels },
] as const;

interface ChannelMeta {
  id: string; label: string; icon: string; color: string; bg: string; border: string; funnelLabels: FunnelLabels;
}

function channelMeta(id: string): ChannelMeta {
  return CHANNEL_REGISTRY.find(c => c.id === id) ?? {
    id, label: id, icon: '📊', color: '#6b7280', bg: '#f9fafb', border: '#e5e7eb', funnelLabels: DEFAULT_FUNNEL_LABELS,
  };
}

const PERSONAS = [
  { id: 'Digital Native',    color: '#5b5fc7' },
  { id: 'Wealth Builder',    color: '#0284c7' },
  { id: 'Everyday Essential',color: '#059669' },
  { id: 'Retiree Anchor',    color: '#b45309' },
  { id: 'At-Risk Saver',     color: '#dc2626' },
];

// ── Helpers ────────────────────────────────────────────────────────────────────

const fmtK = (v: number, dec = 1) =>
  v >= 1_000_000 ? '$' + (v / 1_000_000).toFixed(dec) + 'M'
  : v >= 1_000   ? '$' + (v / 1_000).toFixed(dec) + 'K'
  : '$' + v.toFixed(0);

const fmtRoas = (v: number) => v.toFixed(1) + '×';
const fmtRoi  = (v: number) => (v >= 0 ? '+' : '') + v.toFixed(0) + '%';

function statusCfg(s: PaidChannelMetrics['status']) {
  if (s === 'under') return { label:'Under-invested', cls:'bg-emerald-50 text-emerald-800 border-emerald-200', icon:ArrowUp,   ic:'text-emerald-600', fill:'rgba(134,239,172,0.35)' };
  if (s === 'over')  return { label:'Over-invested',  cls:'bg-red-50 text-red-800 border-red-200',           icon:ArrowDown, ic:'text-red-600',     fill:'rgba(252,165,165,0.32)' };
  return              { label:'Optimal',          cls:'bg-blue-50 text-blue-800 border-blue-200',          icon:CheckCircle2,ic:'text-blue-600',   fill:'rgba(147,197,253,0.28)' };
}

// ── Insight generators ─────────────────────────────────────────────────────────

// Owned channels (e.g. email) render through OwnedChannelCard instead, so
// this only ever receives paid-channel metrics.
function chInsight(ch: ChannelMeta, m: PaidChannelMetrics, persona: string, all: Record<string, ChannelMetrics>) {
  const delta      = m.optimal_spend_usd - m.spend_usd;
  const uplift     = Math.abs(delta) * m.marginal_roas;
  const cpa        = m.cost_per_acquisition > 0 ? `$${m.cost_per_acquisition.toFixed(0)}` : 'N/A';
  const convRate   = (m.conversion_rate * 100).toFixed(2);
  const bizRoi     = m.true_roi_pct != null ? ` Business ROI (after ops + credit risk) is ${m.true_roi_pct.toFixed(0)}%.` : '';

  if (m.status === 'under') {
    const overId = Object.keys(all).find(id => id !== ch.id && !all[id].owned_channel && (all[id] as PaidChannelMetrics).status === 'over');
    const src    = overId ? channelMeta(overId).label : undefined;
    const satPct = m.saturation_pct;
    return (
      `${ch.label} is only ${satPct}% saturated for ${persona} — the S-curve is still rising steeply. ` +
      `Current marginal return is $${m.marginal_roas.toFixed(2)} per $1 spent, meaning each extra dollar has outsized impact. ` +
      `At ${fmtK(m.spend_usd)}/mo you're generating ${fmtRoas(m.roas)} ROAS with a ${convRate}% conversion rate and ${cpa} CPA. ` +
      `Adding ${fmtK(delta)} to reach the optimal ${fmtK(m.optimal_spend_usd)}` +
      (src ? ` (redirected from over-indexed ${src})` : '') +
      ` would unlock ~${fmtK(uplift)} more attributed revenue without increasing total budget.` +
      bizRoi
    );
  }
  if (m.status === 'over') {
    const waste   = Math.abs(delta);
    const satPct  = m.saturation_pct;
    return (
      `${ch.label} is ${satPct}% saturated — the S-curve has flattened. ` +
      `Marginal return has dropped to $${m.marginal_roas.toFixed(2)} per $1 spent, below the break-even threshold of $1.00. ` +
      `You're spending ${fmtK(m.spend_usd)}/mo but the last ${fmtK(waste)} is generating near-zero incremental revenue. ` +
      `Cutting back to ${fmtK(m.optimal_spend_usd)}/mo frees ${fmtK(waste)} that would earn ${m.marginal_roas.toFixed(1)}–4× more if redeployed to under-invested channels.` +
      bizRoi
    );
  }
  return (
    `${ch.label} is optimally positioned for ${persona}. ` +
    `At ${fmtRoas(m.roas)} ROAS with ${m.marginal_roas.toFixed(2)}× marginal return, spend is right at the curve's inflection point — ` +
    `where each dollar is maximally efficient. Conversion rate is ${convRate}% with ${cpa} CPA. ` +
    `Shifts of ±${fmtK(m.spend_usd * 0.1)} either way move revenue by less than 5%. Hold and monitor.` +
    bizRoi
  );
}

function segInsight(persona: string, d: Record<string, ChannelMetrics>) {
  // Owned channels (email) have nothing to reallocate — this insight is
  // paid-channel budget analysis only.
  const paid = Object.entries(d).filter((e): e is [string, PaidChannelMetrics] => !e[1].owned_channel);
  const active = paid.map(([id]) => channelMeta(id));
  const byId = Object.fromEntries(paid) as Record<string, PaidChannelMetrics>;

  const underChs = active.filter(c => byId[c.id].status === 'under')
    .sort((a, b) => byId[b.id].marginal_roas - byId[a.id].marginal_roas);
  const overChs  = active.filter(c => byId[c.id].status === 'over')
    .sort((a, b) => byId[b.id].spend_usd - byId[a.id].spend_usd);

  const totalUplift = underChs.reduce((s, c) => {
    const m = byId[c.id]; return s + (m.optimal_spend_usd - m.spend_usd) * m.marginal_roas;
  }, 0);
  const totalWaste  = overChs.reduce((s, c) => {
    const m = byId[c.id]; return s + Math.abs(m.optimal_spend_usd - m.spend_usd);
  }, 0);

  const bestUnder  = underChs[0];
  const worstOver  = overChs[0];

  const parts: string[] = [];

  if (bestUnder) {
    const m = byId[bestUnder.id];
    parts.push(
      `${bestUnder.label} is only ${m.saturation_pct}% saturated — delivering ${fmtRoas(m.roas)} ROAS with ` +
      `$${m.marginal_roas.toFixed(2)} marginal return per $1 added.`
    );
  }
  if (worstOver) {
    const m = byId[worstOver.id];
    parts.push(
      `${worstOver.label} has plateaued at ${fmtRoas(m.roas)} ROAS — ` +
      `${fmtK(Math.abs(m.optimal_spend_usd - m.spend_usd))} of monthly spend is past the curve's inflection point.`
    );
  }
  if (underChs.length && overChs.length && totalUplift > 100) {
    parts.push(
      `Shifting ${fmtK(totalWaste)} from ${overChs.map(c => c.label).join(' & ')} → ` +
      `${underChs.map(c => c.label).join(' & ')} would unlock ~${fmtK(totalUplift)}/mo with no budget increase.`
    );
  } else if (!underChs.length) {
    const avgRoas = active.reduce((s, c) => s + byId[c.id].roas, 0) / (active.length || 1);
    parts.push(`All channels near-optimal for ${persona} — blended ${fmtRoas(avgRoas)} ROAS. Consider expanding total budget to grow.`);
  } else if (totalUplift > 100) {
    parts.push(`Adding spend to ${underChs.map(c => c.label).join(' & ')} could unlock ~${fmtK(totalUplift)}/mo.`);
  }

  return parts.join(' ');
}

// ── Canvas: S-curve renderer ───────────────────────────────────────────────────

interface DrawCurveOpts {
  hoverSpend?: number | null;
  simSpend?: number | null;
  maxX?: number; // single source of truth for the chart's x-axis extent — also drives the what-if slider's range
}

function canvasDims(el: HTMLCanvasElement): [number, number] {
  // offsetWidth/Height work even with opacity:0; fall back to parent then constant
  const W = el.offsetWidth  || el.parentElement?.offsetWidth  || 340;
  const H = el.offsetHeight || el.parentElement?.offsetHeight || 156;
  return [W, H];
}

function drawCurve(canvas: HTMLCanvasElement, m: PaidChannelMetrics, color: string, opts: DrawCurveOpts = {}) {
  const { hoverSpend, simSpend } = opts;
  const dpr = window.devicePixelRatio || 1;
  const [W, H] = canvasDims(canvas);
  canvas.width = W * dpr; canvas.height = H * dpr;
  const ctx = canvas.getContext('2d'); if (!ctx) return;
  ctx.scale(dpr, dpr);

  const { L, k } = m.curve_params;
  const cur = m.spend_usd, opt = m.optimal_spend_usd;
  const PAD = { top:18, right:18, bottom:34, left:54 };
  const pw = W - PAD.left - PAD.right, ph = H - PAD.top - PAD.bottom;
  const maxX = opts.maxX ?? Math.max(cur, opt) * 2.8, maxY = L * 0.96;
  const toX = (x: number) => PAD.left + (x / maxX) * pw;
  const toY = (y: number) => PAD.top  + ph - Math.min((y / maxY) * ph, ph);
  const Ry  = (x: number) => L * (1 - Math.exp(-k * x));

  // Grid
  ctx.strokeStyle = '#e8edf5'; ctx.lineWidth = 1;
  for (let i = 1; i <= 4; i++) {
    const y = PAD.top + (ph * i) / 4;
    ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(PAD.left + pw, y); ctx.stroke();
  }
  // Y labels
  ctx.fillStyle = '#8a9ab5'; ctx.font = '9px system-ui,sans-serif'; ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const val = (maxY * (4 - i)) / 4;
    ctx.fillText(val >= 1000 ? '$' + (val/1000).toFixed(0)+'K' : '$'+val.toFixed(0), PAD.left-4, PAD.top+(ph*i/4)+3);
  }
  // X labels
  ctx.textAlign = 'center';
  for (let i = 0; i <= 3; i++) {
    const val = (maxX * i) / 3;
    ctx.fillText(val >= 1000 ? '$'+(val/1000).toFixed(1)+'K' : '$'+val.toFixed(0), PAD.left+(pw*i/3), H-PAD.bottom+14);
  }

  // Fill between cur and opt
  const cfg = statusCfg(m.status);
  const fs = Math.min(cur, opt), fe = Math.max(cur, opt);
  if (fe - fs > 0.5) {
    ctx.beginPath();
    let first = true;
    for (let i = 0; i <= 80; i++) {
      const xv = fs + ((fe - fs) * i) / 80;
      if (first) { ctx.moveTo(toX(xv), toY(Ry(xv))); first = false; }
      else ctx.lineTo(toX(xv), toY(Ry(xv)));
    }
    ctx.lineTo(toX(fe), PAD.top + ph); ctx.lineTo(toX(fs), PAD.top + ph); ctx.closePath();
    ctx.fillStyle = cfg.fill; ctx.fill();
  }

  // Curve
  ctx.beginPath(); let first = true;
  for (let i = 0; i <= 240; i++) {
    const xv = (maxX * i) / 240;
    if (first) { ctx.moveTo(toX(xv), toY(Ry(xv))); first = false; }
    else ctx.lineTo(toX(xv), toY(Ry(xv)));
  }
  ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.lineJoin = 'round'; ctx.stroke();

  // Optimal (green dashed)
  const optX = toX(opt);
  ctx.save(); ctx.setLineDash([4,3]); ctx.strokeStyle = '#22c55e'; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(optX, PAD.top); ctx.lineTo(optX, PAD.top+ph); ctx.stroke(); ctx.restore();

  // Current (red dashed)
  const curX = toX(cur);
  ctx.save(); ctx.setLineDash([4,3]); ctx.strokeStyle = '#f87171'; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(curX, PAD.top); ctx.lineTo(curX, PAD.top+ph); ctx.stroke(); ctx.restore();

  // What-if marker (blue solid)
  if (simSpend != null && Math.abs(simSpend - cur) > cur * 0.02) {
    const sx = toX(simSpend);
    if (sx >= PAD.left && sx <= PAD.left + pw) {
      ctx.save(); ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 2; ctx.setLineDash([3,2]);
      ctx.beginPath(); ctx.moveTo(sx, PAD.top); ctx.lineTo(sx, PAD.top+ph); ctx.stroke(); ctx.restore();
      const sy = toY(Ry(simSpend));
      ctx.beginPath(); ctx.arc(sx, sy, 4, 0, Math.PI*2);
      ctx.fillStyle = '#3b82f6'; ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.font = 'bold 8px system-ui,sans-serif'; ctx.fillStyle = '#1d4ed8'; ctx.textAlign = 'center';
      ctx.fillText('Sim', Math.max(sx, PAD.left+14), PAD.top + 10);
    }
  }

  // Hover crosshair
  if (hoverSpend != null && hoverSpend >= 0 && hoverSpend <= maxX) {
    const hx = toX(hoverSpend), hy = toY(Ry(hoverSpend));
    ctx.save(); ctx.strokeStyle = 'rgba(71,85,105,0.45)'; ctx.lineWidth = 1; ctx.setLineDash([3,2]);
    ctx.beginPath(); ctx.moveTo(hx, PAD.top); ctx.lineTo(hx, PAD.top+ph); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(PAD.left, hy); ctx.lineTo(PAD.left+pw, hy); ctx.stroke();
    ctx.restore();
    ctx.beginPath(); ctx.arc(hx, hy, 3.5, 0, Math.PI*2);
    ctx.fillStyle = 'rgba(71,85,105,0.7)'; ctx.fill();

    // Tooltip box
    const hRev = Ry(hoverSpend);
    const hRoas = hoverSpend > 0 ? hRev / hoverSpend : 0;
    const hMroas = L * k * Math.exp(-k * hoverSpend);
    const line1 = `Spend: ${fmtK(hoverSpend)}/mo`;
    const line2 = `Revenue: ${fmtK(hRev)}  ROAS: ${hRoas.toFixed(1)}×`;
    const line3 = `mROAS: ${hMroas.toFixed(2)}×`;
    ctx.font = '10px system-ui,sans-serif';
    const bw = Math.max(ctx.measureText(line2).width, ctx.measureText(line1).width, ctx.measureText(line3).width) + 16;
    const bh = 50;
    let bx = hx + 8, by = hy - bh - 4;
    if (bx + bw > PAD.left + pw) bx = hx - bw - 8;
    if (by < PAD.top) by = hy + 6;
    ctx.fillStyle = 'rgba(15,23,42,0.88)'; roundRect(ctx, bx, by, bw, bh, 5); ctx.fill();
    ctx.textAlign = 'left'; // reset — inherited 'center' from the axis labels above would centre this text on its start x, overflowing the box on both sides
    ctx.fillStyle = '#fff';
    ctx.fillText(line1, bx+8, by+14);
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(line2, bx+8, by+28);
    ctx.fillText(line3, bx+8, by+42);
  }

  // Current dot
  const dotY = toY(Ry(cur));
  ctx.beginPath(); ctx.arc(curX, dotY, 4.5, 0, Math.PI*2);
  ctx.fillStyle = color; ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke();

  // Labels
  ctx.font = 'bold 9px system-ui,sans-serif'; ctx.textAlign = 'center';
  const clamp = (x: number) => Math.min(Math.max(x, PAD.left+14), PAD.left+pw-14);
  ctx.fillStyle = '#16a34a'; ctx.fillText('Opt', clamp(optX), PAD.top+11);
  ctx.fillStyle = '#ef4444'; ctx.fillText('Now', clamp(curX + (Math.abs(curX-optX)<18?16:0)), PAD.top+11);
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x+r, y); ctx.lineTo(x+w-r, y); ctx.arcTo(x+w,y, x+w,y+r, r);
  ctx.lineTo(x+w, y+h-r); ctx.arcTo(x+w,y+h, x+w-r,y+h, r);
  ctx.lineTo(x+r, y+h); ctx.arcTo(x,y+h, x,y+h-r, r);
  ctx.lineTo(x, y+r); ctx.arcTo(x,y, x+r,y, r); ctx.closePath();
}

// ── Canvas: monthly trend chart (interactive) ──────────────────────────────────

function drawTrend(canvas: HTMLCanvasElement, pts: MonthlyPoint[], color: string, hoverIdx: number | null = null) {
  if (!pts || pts.length === 0) return;
  const dpr = window.devicePixelRatio || 1;
  const [W, H] = canvasDims(canvas);
  if (!W || !H) return;
  canvas.width = W * dpr; canvas.height = H * dpr;
  const ctx = canvas.getContext('2d'); if (!ctx) return;
  ctx.scale(dpr, dpr);

  const PAD = { top:16, right:16, bottom:38, left:56 };
  const pw = W - PAD.left - PAD.right, ph = H - PAD.top - PAD.bottom;
  const n = pts.length;
  const maxRev = Math.max(...pts.map(p => p.revenue_usd)) * 1.15 || 1;
  const barW = (pw / n) * 0.55;
  const barX = (i: number) => PAD.left + (pw * i) / n + (pw / n - barW) / 2;
  const lcx  = (i: number) => PAD.left + (pw * (i + 0.5)) / n;
  const lcy  = (p: MonthlyPoint) => PAD.top + ph - (p.revenue_usd / maxRev) * ph;

  // Grid
  ctx.strokeStyle = '#e8edf5'; ctx.lineWidth = 1;
  for (let i = 1; i <= 4; i++) {
    const y = PAD.top + (ph * i) / 4;
    ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(PAD.left+pw, y); ctx.stroke();
  }

  // Y labels
  ctx.fillStyle = '#8a9ab5'; ctx.font = '9px system-ui,sans-serif'; ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const val = (maxRev * (4 - i)) / 4;
    ctx.fillText(val >= 1000 ? '$'+(val/1000).toFixed(0)+'K' : '$'+val.toFixed(0), PAD.left-4, PAD.top+(ph*i/4)+3);
  }

  // Revenue bars (light) — hover brightens
  pts.forEach((p, i) => {
    const bh = (p.revenue_usd / maxRev) * ph;
    ctx.fillStyle = hoverIdx === i ? color + '45' : color + '28';
    ctx.fillRect(barX(i), PAD.top + ph - bh, barW, bh);
  });

  // Spend bars (solid) — hover brightens
  pts.forEach((p, i) => {
    const bh = (p.spend_usd / maxRev) * ph;
    ctx.fillStyle = hoverIdx === i ? color + 'cc' : color + 'aa';
    ctx.fillRect(barX(i), PAD.top + ph - bh, barW, bh);
  });

  // Revenue trend line
  ctx.beginPath(); let first = true;
  pts.forEach((p, i) => {
    const x = lcx(i), y = lcy(p);
    if (first) { ctx.moveTo(x, y); first = false; } else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.lineJoin = 'round'; ctx.stroke();

  // 3-month rolling average line (revenue)
  const rolling3 = pts.map((_, i) => {
    const window = pts.slice(Math.max(0, i - 1), Math.min(n, i + 2));
    return window.reduce((s, p) => s + p.revenue_usd, 0) / window.length;
  });
  ctx.save();
  ctx.beginPath(); let firstRoll = true;
  rolling3.forEach((rev, i) => {
    const x = lcx(i), y = PAD.top + ph - (rev / maxRev) * ph;
    if (firstRoll) { ctx.moveTo(x, y); firstRoll = false; } else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = '#fff'; ctx.lineWidth = 3.5; ctx.lineJoin = 'round'; ctx.stroke();
  ctx.beginPath(); firstRoll = true;
  rolling3.forEach((rev, i) => {
    const x = lcx(i), y = PAD.top + ph - (rev / maxRev) * ph;
    if (firstRoll) { ctx.moveTo(x, y); firstRoll = false; } else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = color + 'dd'; ctx.lineWidth = 1.8; ctx.setLineDash([4, 3]); ctx.stroke();
  ctx.restore();

  // Dots on line — hover enlarges
  pts.forEach((p, i) => {
    const x = lcx(i), y = lcy(p);
    ctx.beginPath(); ctx.arc(x, y, hoverIdx === i ? 4.5 : 3, 0, Math.PI*2);
    ctx.fillStyle = color; ctx.fill(); ctx.strokeStyle='#fff'; ctx.lineWidth=1.4; ctx.stroke();
  });

  // X labels
  ctx.fillStyle = '#8a9ab5'; ctx.font = '9px system-ui,sans-serif'; ctx.textAlign = 'center';
  pts.forEach((p, i) => { ctx.fillText(p.month_name, lcx(i), H - PAD.bottom + 12); });

  // ROAS labels
  ctx.font = 'bold 8px system-ui,sans-serif'; ctx.fillStyle = color;
  pts.forEach((p, i) => {
    if (p.roas <= 0) return;
    ctx.fillText(p.roas.toFixed(1)+'×', lcx(i), lcy(p) - 8);
  });

  // Hover tooltip
  if (hoverIdx !== null && hoverIdx >= 0 && hoverIdx < n) {
    const p   = pts[hoverIdx];
    const cx  = lcx(hoverIdx);
    const fmt = (v: number) => v >= 1000 ? '$'+(v/1000).toFixed(1)+'K' : '$'+v.toFixed(0);

    // Vertical guide line
    ctx.setLineDash([3, 3]); ctx.strokeStyle = color + '60'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cx, PAD.top); ctx.lineTo(cx, PAD.top + ph); ctx.stroke();
    ctx.setLineDash([]);

    // Tooltip box
    const lines = [p.month_name, `Spend:  ${fmt(p.spend_usd)}`, `Revenue: ${fmt(p.revenue_usd)}`, `ROAS:   ${p.roas.toFixed(1)}×`];
    const tipW = 118, tipH = lines.length * 13 + 12;
    let tipX = cx + 10; if (tipX + tipW > W - 4) tipX = cx - tipW - 10;
    const tipY = PAD.top + 4;
    ctx.fillStyle = 'rgba(15,23,42,0.90)';
    roundRect(ctx, tipX, tipY, tipW, tipH, 5); ctx.fill();
    ctx.textAlign = 'left';
    lines.forEach((l, j) => {
      ctx.fillStyle = j === 0 ? '#fff' : '#cbd5e1';
      ctx.font = j === 0 ? 'bold 9px system-ui,sans-serif' : '9px system-ui,sans-serif';
      ctx.fillText(l, tipX + 8, tipY + 12 + j * 13);
    });
  }
}

// ── Synthetic monthly fallback (S-curve + banking seasonality) ─────────────────
const _SEASONALITY = [1.15, 1.08, 0.98, 0.88, 0.86, 0.82, 0.78, 0.82, 0.95, 1.02, 1.10, 1.18];
const _MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function synthMonthly(spend: number, L: number, k: number): MonthlyPoint[] {
  return _SEASONALITY.map((mult, i) => {
    const s = spend * mult;
    const r = L * (1 - Math.exp(-k * s));
    const roas = s > 0 ? r / s : 0;
    return { month: i+1, month_name: _MONTHS[i], sent: 0, converted: 0,
      spend_usd: Math.round(s * 100) / 100, revenue_usd: Math.round(r * 100) / 100,
      roas: Math.round(roas * 10) / 10, roi_pct: s > 0 ? (r - s) / s * 100 : 0,
      marginal_roas: L * k * Math.exp(-k * s) };
  });
}

function trendInsight(ch: { label: string }, pts: MonthlyPoint[]): string {
  if (!pts || pts.length === 0) return '';
  const activePts = pts.filter(p => p.revenue_usd > 0);
  if (activePts.length === 0) return `${ch.label} generated no attributed revenue across the 12-month window — the channel is inactive or unconverted for this segment.`;

  const best  = activePts.reduce((a, b) => b.roas > a.roas ? b : a);
  const worst = activePts.reduce((a, b) => b.roas < a.roas ? b : a);

  // H1 vs H2 average ROAS
  const h1 = pts.filter(p => p.month <= 6 && p.revenue_usd > 0);
  const h2 = pts.filter(p => p.month  > 6 && p.revenue_usd > 0);
  const avgRoas = (arr: MonthlyPoint[]) => arr.length ? arr.reduce((s, p) => s + p.roas, 0) / arr.length : 0;
  const h1Roas = avgRoas(h1), h2Roas = avgRoas(h2);
  const trend = h2Roas > h1Roas * 1.05 ? 'improving into H2' : h2Roas < h1Roas * 0.95 ? 'declining into H2' : 'stable across the year';

  // Peak season: consecutive months with above-avg ROAS
  const avgAll = avgRoas(activePts);
  const peakMonths = pts.filter(p => p.roas > avgAll * 1.05).map(p => p.month_name);
  const peakStr = peakMonths.length >= 2
    ? `Peak season is ${peakMonths[0]}–${peakMonths[peakMonths.length - 1]}.`
    : peakMonths.length === 1 ? `Highest single month is ${peakMonths[0]}.` : '';

  // Total annual revenue
  const totalRev = pts.reduce((s, p) => s + p.revenue_usd, 0);
  const totalSpend = pts.reduce((s, p) => s + p.spend_usd, 0);
  const annualRoas = totalSpend > 0 ? totalRev / totalSpend : 0;

  return (
    `Annual ${ch.label} performance: ${fmtK(totalSpend)} spend → ${fmtK(totalRev)} revenue (${fmtRoas(annualRoas)} blended ROAS). ` +
    `Best month is ${best.month_name} at ${fmtRoas(best.roas)} ROAS; ` +
    `lowest is ${worst.month_name} at ${fmtRoas(worst.roas)} ROAS. ` +
    `ROAS is ${trend} (H1 avg ${fmtRoas(h1Roas)} vs H2 ${fmtRoas(h2Roas)}). ` +
    peakStr
  ).trim();
}

// ── Canvas: conversion funnel ──────────────────────────────────────────────────

function drawFunnel(canvas: HTMLCanvasElement, m: ChannelMetrics, color: string, labels: FunnelLabels = DEFAULT_FUNNEL_LABELS) {
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.offsetWidth || 340, H = canvas.offsetHeight || 156;
  canvas.width = W * dpr; canvas.height = H * dpr;
  const ctx = canvas.getContext('2d'); if (!ctx) return;
  ctx.scale(dpr, dpr);

  const stages = [
    { label: labels[0], val: m.sent,      pct: 100 },
    { label: labels[1], val: m.opened,    pct: m.sent > 0 ? (m.opened    / m.sent) * 100 : 0 },
    { label: labels[2], val: m.clicked,   pct: m.sent > 0 ? (m.clicked   / m.sent) * 100 : 0 },
    { label: labels[3], val: m.converted, pct: m.sent > 0 ? (m.converted / m.sent) * 100 : 0 },
  ];
  const n = stages.length;

  // Layout: [label 68px] [bar area] [stats 72px]
  const LBL_W = 68, STAT_W = 72;
  const PAD = { top: 10, bottom: 10 };
  const rowH = (H - PAD.top - PAD.bottom) / n;
  const barAreaW = W - LBL_W - STAT_W;
  const barStart = LBL_W;

  stages.forEach((s, i) => {
    const barW = barAreaW * (s.pct / 100);
    const y    = PAD.top + i * rowH;
    const barY = y + rowH * 0.20;
    const barH = rowH * 0.52;
    const midY = barY + barH * 0.62;

    // Background track
    ctx.fillStyle = '#f1f5f9';
    roundRect(ctx, barStart, barY, barAreaW, barH, 3); ctx.fill();

    // Filled bar — opacity steps down per stage
    const alpha = Math.round((1 - i * 0.10) * 255).toString(16).padStart(2, '0');
    ctx.fillStyle = color + alpha;
    if (barW > 2) { roundRect(ctx, barStart, barY, barW, barH, 3); ctx.fill(); }

    // Stage label (left column)
    ctx.font = 'bold 9.5px system-ui,sans-serif';
    ctx.textAlign = 'right'; ctx.fillStyle = '#374151';
    ctx.fillText(s.label, LBL_W - 8, midY);

    // Count inside bar (white if bar wide enough, else channel color outside)
    ctx.font = 'bold 9px system-ui,sans-serif';
    const countStr = s.val.toLocaleString();
    const countW = ctx.measureText(countStr).width;
    if (barW > countW + 16) {
      ctx.textAlign = 'left'; ctx.fillStyle = '#fff';
      ctx.fillText(countStr, barStart + 7, midY);
    } else {
      ctx.textAlign = 'left'; ctx.fillStyle = color;
      ctx.fillText(countStr, barStart + barW + 5, midY);
    }

    // Right stats column: % of total + drop-off
    const pctStr  = s.pct.toFixed(1) + '%';
    ctx.textAlign = 'left'; ctx.fillStyle = '#374151';
    ctx.font = 'bold 9px system-ui,sans-serif';
    ctx.fillText(pctStr, W - STAT_W + 6, midY);

    // Drop-off between rows (shown in right column, between this and next bar)
    if (i < n - 1) {
      const drop = stages[i].pct - stages[i + 1].pct;
      ctx.font = '8.5px system-ui,sans-serif'; ctx.fillStyle = '#ef4444';
      ctx.fillText('▼ ' + drop.toFixed(1) + '%', W - STAT_W + 6, y + rowH - 4);
    }
  });
}

// ── Seasonality sparkline strip ────────────────────────────────────────────────

function drawSparkline(canvas: HTMLCanvasElement, pts: MonthlyPoint[], color: string, hoverIdx: number | null = null) {
  if (!pts || pts.length === 0) return;
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.offsetWidth || 120, H = canvas.offsetHeight || 48;
  canvas.width = W * dpr; canvas.height = H * dpr;
  const ctx = canvas.getContext('2d'); if (!ctx) return;
  ctx.scale(dpr, dpr);
  const n = pts.length;
  const vals = pts.map(p => p.roas);
  const minV = Math.min(...vals), maxV = Math.max(...vals);
  const range = maxV - minV || 1;
  const PAD = { top: 8, right: 6, bottom: 6, left: 6 };
  const pw = W - PAD.left - PAD.right, ph = H - PAD.top - PAD.bottom;
  const x = (i: number) => PAD.left + (pw * i) / (n - 1);
  const y = (v: number) => PAD.top + ph - ((v - minV) / range) * ph;

  // Month gridlines — light dashed vertical line at each of the 12 months
  ctx.save();
  ctx.setLineDash([2, 2]); ctx.strokeStyle = '#e5e7eb'; ctx.lineWidth = 1;
  for (let i = 0; i < n; i++) {
    ctx.beginPath(); ctx.moveTo(x(i), PAD.top); ctx.lineTo(x(i), PAD.top + ph); ctx.stroke();
  }
  ctx.restore();

  // Area fill
  ctx.beginPath();
  vals.forEach((v, i) => { if (i === 0) ctx.moveTo(x(i), y(v)); else ctx.lineTo(x(i), y(v)); });
  ctx.lineTo(x(n - 1), PAD.top + ph); ctx.lineTo(x(0), PAD.top + ph); ctx.closePath();
  const grad = ctx.createLinearGradient(0, PAD.top, 0, PAD.top + ph);
  grad.addColorStop(0, color + '40'); grad.addColorStop(1, color + '05');
  ctx.fillStyle = grad; ctx.fill();

  // Line
  ctx.beginPath();
  vals.forEach((v, i) => { if (i === 0) ctx.moveTo(x(i), y(v)); else ctx.lineTo(x(i), y(v)); });
  ctx.strokeStyle = color; ctx.lineWidth = 1.8; ctx.lineJoin = 'round'; ctx.stroke();

  // Peak dot
  const peakIdx = vals.indexOf(maxV);
  ctx.beginPath(); ctx.arc(x(peakIdx), y(maxV), 3, 0, Math.PI * 2);
  ctx.fillStyle = color; ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.stroke();

  // Hover guide line + dot + tooltip
  if (hoverIdx !== null && hoverIdx >= 0 && hoverIdx < n) {
    const hx = x(hoverIdx), hy = y(vals[hoverIdx]);

    ctx.save();
    ctx.setLineDash([3, 3]); ctx.strokeStyle = color + '90'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(hx, PAD.top); ctx.lineTo(hx, PAD.top + ph); ctx.stroke();
    ctx.restore();

    ctx.beginPath(); ctx.arc(hx, hy, 3.2, 0, Math.PI * 2);
    ctx.fillStyle = color; ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.2; ctx.stroke();

    const label = `${pts[hoverIdx].month_name} · ${pts[hoverIdx].roas.toFixed(1)}×`;
    ctx.font = 'bold 8.5px system-ui,sans-serif';
    const tipW = ctx.measureText(label).width + 10;
    const tipH = 13;
    const tipX = Math.max(2, Math.min(W - tipW - 2, hx - tipW / 2));
    const tipY = 1;
    ctx.fillStyle = 'rgba(15,23,42,0.92)';
    roundRect(ctx, tipX, tipY, tipW, tipH, 3); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.textAlign = 'left';
    ctx.fillText(label, tipX + 5, tipY + 9.5);
  }
}

function SeasonalityStrip({ allMonthly, channels, ownedChannels, personaData }: {
  allMonthly: Record<string, MonthlyPoint[]>;
  channels: ChannelMeta[];       // paid channels only — a ROAS trend needs spend > 0
  ownedChannels: ChannelMeta[];  // e.g. email — shown as a callout, not a sparkline
  personaData: Record<string, ChannelMetrics>;
}) {
  // Map-based, not fixed keys — the channel set varies by dataset (v1: 4, v2: 8).
  const canvasRefs = useRef(new Map<string, HTMLCanvasElement | null>());
  const [hover, setHover] = useState<{ chId: string; idx: number } | null>(null);

  useEffect(() => {
    channels.forEach(ch => {
      const el = canvasRefs.current.get(ch.id);
      const pts = allMonthly[ch.id] ?? [];
      if (el && pts.length) drawSparkline(el, pts, ch.color, hover?.chId === ch.id ? hover.idx : null);
    });
  }, [allMonthly, channels, hover]);

  // Map mouse X to the nearest month index — mirrors the hit-testing pattern
  // used for the main trend chart's hover (ChannelCard.handleMouseMove).
  const handleSparklineMouseMove = (chId: string, pts: MonthlyPoint[]) => (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (pts.length === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const PAD_LEFT = 6, PAD_RIGHT = 6;
    const pw = rect.width - PAD_LEFT - PAD_RIGHT;
    const rawX = e.clientX - rect.left - PAD_LEFT;
    const idx = Math.round((rawX / pw) * (pts.length - 1));
    setHover(idx >= 0 && idx < pts.length ? { chId, idx } : null);
  };
  const handleSparklineMouseLeave = () => setHover(null);

  const peakMonth = (pts: MonthlyPoint[]) => {
    if (!pts.length) return '—';
    return pts.reduce((a, b) => b.roas > a.roas ? b : a).month_name;
  };
  const avgRoas = (pts: MonthlyPoint[]) => {
    const active = pts.filter(p => p.roas > 0);
    return active.length ? active.reduce((s, p) => s + p.roas, 0) / active.length : 0;
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 px-4 py-3">
      <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-3">Seasonality · ROAS trend Jan–Dec 2025</p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {channels.map(ch => {
          const pts = allMonthly[ch.id] ?? [];
          const avg = avgRoas(pts);
          const peak = peakMonth(pts);
          return (
            <div key={ch.id} className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-gray-700 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full inline-block" style={{ background: ch.color }}/>
                  {ch.label}
                </span>
                <span className="text-[10px] text-gray-400">avg {avg > 0 ? avg.toFixed(1) + '×' : '—'}</span>
              </div>
              <canvas
                ref={el => { canvasRefs.current.set(ch.id, el); }}
                onMouseMove={handleSparklineMouseMove(ch.id, pts)}
                onMouseLeave={handleSparklineMouseLeave}
                style={{ width: '100%', height: 48, display: 'block', cursor: 'crosshair' }}
              />
              <div className="flex justify-between text-[9.5px] text-gray-400 mt-0.5">
                <span>Jan</span>
                <span className="font-medium" style={{ color: ch.color }}>↑ {peak}</span>
                <span>Dec</span>
              </div>
            </div>
          );
        })}
      </div>
      {ownedChannels.length > 0 && (
        <p className="text-[10px] text-gray-400 mt-3 pt-2.5 border-t border-gray-100">
          {ownedChannels.map(ch => {
            const rev = personaData[ch.id]?.attributed_revenue_usd ?? 0;
            return `${ch.label} excluded — $0 media spend (owned channel); ${fmtK(rev)} attributed revenue this year, tracked separately.`;
          }).join(' ')}
        </p>
      )}
    </div>
  );
}

// ── Channel Card ───────────────────────────────────────────────────────────────
// Business ROI simulation constants (productValue/bizCost/riskRate) are passed
// in as props, sourced from the API's product_value_benchmarks/biz_cost_benchmarks/
// risk_rate_benchmarks — those mirror whichever generator script (v1 or v2) is
// actually backing the active dataset, so this card never needs its own
// hardcoded copy that could drift from what the server is using.

function ChannelCard({
  ch, metrics, personaName, allData, monthly, productValueBenchmarks, bizCostBenchmarks, riskRateBenchmarks,
}: {
  ch: ChannelMeta;
  metrics: PaidChannelMetrics;
  personaName: string;
  allData: Record<string, ChannelMetrics>;
  monthly: MonthlyPoint[];
  productValueBenchmarks: Record<string, number>;
  bizCostBenchmarks: Record<string, number>;
  riskRateBenchmarks: Record<string, number>;
}) {
  const chartRef   = useRef<HTMLCanvasElement>(null);
  const [view,      setView]      = useState<'curve'|'trend'|'funnel'>('curve');
  const [simSpend,  setSimSpend]  = useState<number>(metrics.spend_usd);
  const [hoverSpend, setHoverSpend] = useState<number | null>(null);
  const [hoverMonth, setHoverMonth] = useState<number | null>(null);

  // Insight from backend (updated on slider settle)
  const [simInsight,        setSimInsight]        = useState<string | null>(null);
  const [simInsightLoading, setSimInsightLoading] = useState(false);

  const cfg      = statusCfg(metrics.status);
  const StatusIcon = cfg.icon;
  const delta    = metrics.optimal_spend_usd - metrics.spend_usd;
  const baseInsight = chInsight(ch, metrics, personaName, allData);

  // ── S-curve helpers ──────────────────────────────────────────────────────
  const { L, k } = metrics.curve_params;
  const Ry    = (x: number) => L * (1 - Math.exp(-k * x));
  const mROAS = (x: number) => L * k * Math.exp(-k * x);

  // ── Instant client-side sim metrics (no latency) ─────────────────────────
  const simRev    = Ry(simSpend);
  const simRoas   = simSpend > 0 ? simRev / simSpend : 0;
  const simRoi    = simSpend > 0 ? (simRev - simSpend) / simSpend * 100 : -100;
  const simMroas  = mROAS(simSpend);
  const simStatus = simMroas > 1.25 ? 'under' : simMroas < 0.80 ? 'over' : 'optimal';

  // True business ROI at sim spend (client-side)
  const pv         = productValueBenchmarks[ch.id] ?? 300;
  const bc         = bizCostBenchmarks[ch.id] ?? 80;
  const rr         = riskRateBenchmarks[ch.id] ?? 0.07;
  const simConv    = pv > 0 ? simRev / pv : 0;
  const simBiz     = simConv * bc;
  const simRiskAdj = simRev * (1 - rr);
  const simTc      = simSpend + simBiz;
  const simTrueRoi = simTc > 0 ? (simRiskAdj - simTc) / simTc * 100 : -100;
  const simTrueRoas= simTc > 0 ? simRiskAdj / simTc : 0;

  const isSimChanged = Math.abs(simSpend - metrics.spend_usd) > metrics.spend_usd * 0.02;

  // ── Debounced backend call for AI insight (350ms after slider settles) ───
  useEffect(() => {
    if (!isSimChanged) { setSimInsight(null); return; }
    const t = setTimeout(async () => {
      setSimInsightLoading(true);
      try {
        const r = await fetch(`${API_BASE}/api/banking/ad_spend/simulate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ persona: personaName, channel: ch.id, sim_spend: simSpend }),
        });
        if (r.ok) { const d = await r.json(); if (d.success) setSimInsight(d.insight); }
      } catch { /* keep previous insight */ } finally { setSimInsightLoading(false); }
    }, 350);
    return () => clearTimeout(t);
  }, [simSpend, isSimChanged, personaName, ch.id]);

  // ── Trend data: real CSV data or S-curve synthetic fallback ─────────────
  const trendPts = monthly.length > 0 ? monthly : synthMonthly(metrics.spend_usd, L, k);

  // Single source of truth for the curve chart's x-axis extent — drives the
  // canvas draw, the hover hit-testing, and the what-if slider's range, so
  // the slider can never disagree with what the chart actually shows.
  const chartMaxX = Math.max(metrics.spend_usd, metrics.optimal_spend_usd) * 2.8;

  // ── Single unified redraw (one canvas, always display:block) ─────────────
  const redraw = useCallback(() => {
    const el = chartRef.current; if (!el) return;
    if (view === 'curve') {
      drawCurve(el, metrics, ch.color, { hoverSpend, simSpend: isSimChanged ? simSpend : null, maxX: chartMaxX });
    } else if (view === 'trend') {
      drawTrend(el, trendPts, ch.color, hoverMonth);
    } else {
      drawFunnel(el, metrics, ch.color, ch.funnelLabels);
    }
  }, [view, metrics, ch.color, ch.funnelLabels, hoverSpend, simSpend, isSimChanged, trendPts, hoverMonth, chartMaxX]);

  useEffect(() => { const r = requestAnimationFrame(redraw); return () => cancelAnimationFrame(r); }, [redraw]);

  useEffect(() => {
    const onResize = () => { requestAnimationFrame(redraw); };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [redraw]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const el = chartRef.current; if (!el) return;
    const rect = el.getBoundingClientRect();
    if (view === 'curve') {
      const PAD_LEFT = 54, PAD_RIGHT = 18;
      const pw = rect.width - PAD_LEFT - PAD_RIGHT;
      const rawX = e.clientX - rect.left - PAD_LEFT;
      const spend = (rawX / pw) * chartMaxX;
      setHoverSpend(spend >= 0 && spend <= chartMaxX ? spend : null);
    } else if (view === 'trend') {
      const PAD_LEFT = 56, PAD_RIGHT = 16;
      const pw = rect.width - PAD_LEFT - PAD_RIGHT;
      const n  = trendPts.length;
      const rawX = e.clientX - rect.left - PAD_LEFT;
      const idx  = Math.floor((rawX / pw) * n);
      setHoverMonth(idx >= 0 && idx < n ? idx : null);
    }
  };

  const handleMouseLeave = () => { setHoverSpend(null); setHoverMonth(null); };

  const sliderMin = 0;
  const sliderMax = chartMaxX;

  const handleReset = () => { setSimSpend(metrics.spend_usd); setSimInsight(null); };

  const simCfg = statusCfg(isSimChanged ? simStatus : metrics.status);

  // Curve: saturation/sim insight. 12-mo: seasonal trend insight. Funnel: drop-off insight.
  const openRate  = metrics.sent > 0 ? (metrics.opened    / metrics.sent * 100).toFixed(1) : '0';
  const clickRate = metrics.sent > 0 ? (metrics.clicked   / metrics.sent * 100).toFixed(1) : '0';
  const convRate  = metrics.sent > 0 ? (metrics.converted / metrics.sent * 100).toFixed(2) : '0';
  const [stage1Label, stage2Label, stage3Label, stage4Label] = ch.funnelLabels;
  const bigDrop   = metrics.opened > 0 && metrics.clicked / metrics.opened < 0.35
    ? stage3Label.toLowerCase()
    : metrics.clicked > 0 && metrics.converted / metrics.clicked < 0.10
      ? stage4Label.toLowerCase() : null;
  const funnelInsight =
    `${ch.label} reached ${metrics.sent.toLocaleString()} contacts — ${openRate}% ${stage2Label.toLowerCase()}, ${clickRate}% ${stage3Label.toLowerCase()}, ${convRate}% ${stage4Label.toLowerCase()}. ` +
    (bigDrop ? `Biggest drop-off is at the ${bigDrop} stage — creative or offer relevance is the likely lever.` : 'Funnel is healthy with no single dominant drop-off stage.');
  const displayInsight = view === 'trend'
    ? trendInsight(ch, trendPts)
    : view === 'funnel'
      ? funnelInsight
      : isSimChanged
        ? (simInsightLoading ? null : (simInsight ?? baseInsight))
        : baseInsight;

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
          style={{ background: ch.bg, border: `1px solid ${ch.border}` }}>
          {ch.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[14px] font-bold text-gray-900">{ch.label}</p>
          <p className="text-[11px] text-gray-500">
            {isSimChanged
              ? <><span className="text-blue-600 font-semibold">{fmtRoas(simRoas)}</span> sim ROAS · mROAS {simMroas.toFixed(2)}× · <span className={simCfg.cls.split(' ')[1]}>{simCfg.label}</span></>
              : <>{fmtRoas(metrics.roas)} ROAS · mROAS {metrics.marginal_roas.toFixed(2)}×</>
            }
          </p>
        </div>
        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1 border ${isSimChanged ? simCfg.cls : cfg.cls}`}>
          {isSimChanged ? <simCfg.icon className={`w-3 h-3 ${simCfg.ic}`}/> : <StatusIcon className={`w-3 h-3 ${cfg.ic}`}/>}
          {isSimChanged ? simCfg.label : cfg.label}
        </span>
        {/* View toggle */}
        <div className="flex border border-gray-200 rounded-md overflow-hidden">
          <button onClick={() => setView('curve')} title="S-curve: revenue vs spend (diminishing returns)"
            className={`px-2.5 py-1.5 text-[10px] font-semibold flex items-center gap-1 transition-colors ${view==='curve' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:bg-gray-50'}`}>
            <LineChart className="w-3 h-3" /> Curve
          </button>
          <button onClick={() => setView('trend')} title="12-month bar chart: actual monthly performance"
            className={`px-2.5 py-1.5 text-[10px] font-semibold flex items-center gap-1 transition-colors border-l border-gray-200 ${view==='trend' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:bg-gray-50'}`}>
            <BarChart className="w-3 h-3" /> 12-mo
          </button>
          <button onClick={() => setView('funnel')} title={`Conversion funnel: ${ch.funnelLabels.join(' → ')}`}
            className={`px-2.5 py-1.5 text-[10px] font-semibold flex items-center gap-1 transition-colors border-l border-gray-200 ${view==='funnel' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:bg-gray-50'}`}>
            <TrendingUp className="w-3 h-3" /> Funnel
          </button>
        </div>
      </div>

      {/* Single canvas — always display:block so offsetWidth is always valid */}
      <div className="px-3 pt-2 pb-0" style={{ height: 160 }}>
        <canvas ref={chartRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{ width: '100%', height: '100%', display: 'block', cursor: 'crosshair' }} />
      </div>

      {view === 'trend' && (
        <div className="px-4 pt-1 pb-1 flex flex-col gap-1">
          <div className="flex items-center gap-4 text-[10px] text-gray-400 flex-wrap">
            <span className="flex items-center gap-1.5"><span className="inline-block w-4 h-3 rounded-sm" style={{background:ch.color+'aa'}}/>Spend</span>
            <span className="flex items-center gap-1.5"><span className="inline-block w-4 h-3 rounded-sm" style={{background:ch.color+'28'}}/>Revenue</span>
            <span className="flex items-center gap-1.5"><span className="w-4 inline-block border-t-2" style={{borderColor:ch.color}}/>Monthly</span>
            <span className="flex items-center gap-1.5"><span className="w-4 inline-block border-t-2 border-dashed" style={{borderColor:ch.color+'cc'}}/>3-mo avg</span>
            <span className="ml-auto text-[9px]">Jan–Dec 2025 · ROAS labels on peaks</span>
          </div>
          <p className="text-[9.5px] text-gray-400 leading-snug">
            <span className="font-semibold text-gray-500">12-Month view:</span> Actual monthly spend (solid bars) vs attributed revenue (light bars) Jan–Dec 2025. ROAS labels show revenue efficiency at each month's peak. Use this to spot seasonal patterns.
          </p>
        </div>
      )}

      {/* Funnel legend */}
      {view === 'funnel' && (
        <div className="px-4 pt-1 pb-1 flex flex-col gap-1">
          <div className="flex items-center gap-3 text-[10px] text-gray-400 flex-wrap">
            {ch.funnelLabels.map((s, i) => (
              <span key={s} className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded-sm" style={{background: ch.color + Math.round((1 - i * 0.12) * 255).toString(16).padStart(2,'0')}}/>
                {s}
              </span>
            ))}
            <span className="ml-auto text-[9px]">Annual totals · % of sent</span>
          </div>
          <p className="text-[9.5px] text-gray-400 leading-snug">
            <span className="font-semibold text-gray-500">Funnel view:</span> Annual contacts {ch.funnelLabels.map(l => l.toLowerCase()).join(' → ')}. Bars show count; right-side % is relative to {stage1Label.toLowerCase()}. Drop-off numbers between stages reveal where to focus creative or targeting improvements.
          </p>
        </div>
      )}

      {/* What-if slider (curve view only, hidden in funnel) */}
      {view === 'curve' && (
        <div className="px-4 pb-3 border-b border-gray-100">
          <div className="flex items-center justify-between text-[10px] mb-1">
            <span className="text-gray-500 font-medium">
              What-if spend: <span className="text-blue-600 font-bold">{fmtK(simSpend)}/mo</span>
            </span>
            {isSimChanged && (
              <span className={`font-bold ${simRev > metrics.attributed_revenue_usd ? 'text-emerald-600' : 'text-red-600'}`}>
                {simRev > metrics.attributed_revenue_usd ? '+' : ''}{fmtK(simRev - metrics.attributed_revenue_usd)} rev · {fmtRoas(simRoas)} ROAS
              </span>
            )}
            {isSimChanged && (
              <button onClick={handleReset} className="text-[10px] text-gray-400 underline ml-2">reset</button>
            )}
          </div>
          <input type="range"
            min={sliderMin} max={sliderMax} step={(sliderMax - sliderMin) / 200}
            value={simSpend}
            onChange={e => setSimSpend(Number(e.target.value))}
            className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
            style={{ accentColor: '#3b82f6', background: `linear-gradient(to right, #3b82f6 ${((simSpend - sliderMin)/(sliderMax - sliderMin))*100}%, #e2e8f0 0%)` }}
          />
          <div className="flex justify-between text-[9px] text-gray-400 mt-0.5">
            <span>{fmtK(sliderMin)}</span>
            <span className="text-emerald-600 font-semibold">Opt {fmtK(metrics.optimal_spend_usd)}</span>
            <span>{fmtK(sliderMax)}</span>
          </div>
          {isSimChanged && (
            <div className="mt-1.5 text-[10px] text-blue-700 bg-blue-50 rounded-md px-2.5 py-1.5 border border-blue-100 flex items-center gap-2">
              <span>At {fmtK(simSpend)}/mo: <strong>{fmtK(simRev)}</strong> revenue · <strong>{fmtRoas(simRoas)}</strong> ROAS · Mktg ROI <strong>{fmtRoi(simRoi)}</strong> · Biz ROI <strong>{fmtRoi(simTrueRoi)}</strong></span>
            </div>
          )}
        </div>
      )}

      {/* AI insight — updates from backend 350ms after slider settles */}
      <div className={`px-4 py-3 border-b border-gray-100 flex gap-2 items-start transition-colors ${isSimChanged ? 'bg-blue-50/30' : 'bg-gray-50'}`}>
        <span className="text-[13px] flex-shrink-0 mt-0.5">{isSimChanged ? '⚡' : '✦'}</span>
        {simInsightLoading ? (
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 border border-blue-400 border-t-transparent rounded-full animate-spin"/>
            <p className="text-[11px] text-blue-500 italic">Recalculating insight…</p>
          </div>
        ) : (
          <p className="text-[11.5px] text-gray-700 leading-relaxed">{displayInsight}</p>
        )}
      </div>

      {/* Status callout — reflects sim state when active (hidden on funnel view) */}
      {view !== 'funnel' && (isSimChanged ? simStatus : metrics.status) === 'over' && (
        <div className="px-4 py-2.5 bg-red-50 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-red-500 flex-shrink-0"/>
          <p className="text-[11px] text-red-700 font-medium">
            {isSimChanged
              ? `At this spend level, marginal return is ${simMroas.toFixed(1)}× — over-indexed. Reduce to optimal ${fmtK(metrics.optimal_spend_usd)}.`
              : `Reduce by ${fmtK(Math.abs(delta))}/mo → save ${fmtK(Math.abs(delta))} to redeploy at higher-ROAS channels`
            }
          </p>
        </div>
      )}
      {view !== 'funnel' && (isSimChanged ? simStatus : metrics.status) === 'under' && (
        <div className="px-4 py-2.5 bg-emerald-50 flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0"/>
          <p className="text-[11px] text-emerald-800 font-medium">
            {isSimChanged
              ? `Still under-invested at ${fmtRoas(simRoas)} ROAS — marginal return ${simMroas.toFixed(1)}× suggests room to grow.`
              : `+${fmtK(delta)}/mo spend → est. +${fmtK(delta * metrics.marginal_roas)} incremental revenue`
            }
          </p>
        </div>
      )}
    </div>
  );
}

// ── Owned Channel Card (e.g. Email) ─────────────────────────────────────────────
// No spend to optimize against — funnel + attributed revenue only, with an
// explicit banner explaining why there's no S-curve/what-if slider here, so
// the $0 spend reads as a deliberate accounting choice rather than missing data.

function OwnedChannelCard({ ch, metrics }: { ch: ChannelMeta; metrics: OwnedChannelMetrics }) {
  const chartRef = useRef<HTMLCanvasElement>(null);

  const redraw = useCallback(() => {
    const el = chartRef.current; if (!el) return;
    drawFunnel(el, metrics, ch.color, ch.funnelLabels);
  }, [metrics, ch.color, ch.funnelLabels]);

  useEffect(() => { const r = requestAnimationFrame(redraw); return () => cancelAnimationFrame(r); }, [redraw]);
  useEffect(() => {
    const onResize = () => requestAnimationFrame(redraw);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [redraw]);

  const convRate = metrics.sent > 0 ? (metrics.converted / metrics.sent * 100).toFixed(2) : '0';

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden flex flex-col">
      <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
          style={{ background: ch.bg, border: `1px solid ${ch.border}` }}>
          {ch.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[14px] font-bold text-gray-900">{ch.label}</p>
          <p className="text-[11px] text-gray-500">{fmtK(metrics.attributed_revenue_usd)} attributed revenue · {convRate}% conversion</p>
        </div>
        <span className="text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1 border bg-gray-50 text-gray-600 border-gray-200">
          Owned Channel
        </span>
      </div>

      <div className="px-3 pt-2 pb-0" style={{ height: 160 }}>
        <canvas ref={chartRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      </div>

      <div className="px-4 py-3 flex flex-col gap-1">
        <div className="flex items-center gap-4 text-[10px] text-gray-400 flex-wrap">
          {ch.funnelLabels.map((s, i) => (
            <span key={s} className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-3 rounded-sm" style={{ background: ch.color + Math.round((1 - i * 0.12) * 255).toString(16).padStart(2, '0') }} />
              {s}
            </span>
          ))}
          <span className="ml-auto text-[9px]">Annual totals · % of sent</span>
        </div>
      </div>

      <div className="px-4 py-3 border-t border-gray-100 bg-gray-50 flex gap-2 items-start">
        <span className="text-[13px] flex-shrink-0 mt-0.5">✦</span>
        <p className="text-[11.5px] text-gray-700 leading-relaxed">
          <span className="font-semibold">Owned Channel — No Ad Spend.</span> Cost here is a flat ESP platform subscription,
          not a per-message media buy, so it's excluded from ROAS/reallocation optimization. The {fmtK(metrics.attributed_revenue_usd)} in
          revenue shown above is real attribution — it's tracked separately from paid-channel blended ROAS rather than blended into it.
        </p>
      </div>
    </div>
  );
}

// ── Channel Comparison Overlay ─────────────────────────────────────────────────

function ChannelCompare({ personaData, persona }: {
  personaData: Record<string, ChannelMetrics>;
  persona: string;
}) {
  // S-curve comparison only makes sense for paid channels — email (owned, $0
  // spend) has no curve_params to plot and is naturally excluded here.
  const activeChannels = Object.keys(personaData)
    .filter(id => !personaData[id].owned_channel)
    .map(channelMeta);
  const [chA, setChA] = useState(activeChannels[0]?.id ?? '');
  const [chB, setChB] = useState(activeChannels[1]?.id ?? '');
  const [open, setOpen] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const drawCompare = useCallback(() => {
    const el = canvasRef.current; if (!el) return;
    const mA = personaData[chA] as PaidChannelMetrics | undefined;
    const mB = personaData[chB] as PaidChannelMetrics | undefined;
    if (!mA || !mB) return;
    const dpr = window.devicePixelRatio || 1;
    const W = el.offsetWidth || 640, H = 220;
    el.width = W * dpr; el.height = H * dpr;
    const ctx = el.getContext('2d'); if (!ctx) return;
    ctx.scale(dpr, dpr);

    const PAD = { top: 20, right: 24, bottom: 40, left: 60 };
    const pw = W - PAD.left - PAD.right, ph = H - PAD.top - PAD.bottom;
    const maxX = Math.max(mA.spend_usd, mB.spend_usd, mA.optimal_spend_usd, mB.optimal_spend_usd) * 2.5;
    const maxY = Math.max(mA.curve_params.L, mB.curve_params.L) * 0.96;
    const toX = (x: number) => PAD.left + (x / maxX) * pw;
    const toY = (y: number) => PAD.top + ph - Math.min((y / maxY) * ph, ph);
    const Ry = (L: number, k: number, x: number) => L * (1 - Math.exp(-k * x));

    // Grid
    ctx.strokeStyle = '#e8edf5'; ctx.lineWidth = 1;
    for (let i = 1; i <= 4; i++) {
      const y = PAD.top + (ph * i) / 4;
      ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(PAD.left + pw, y); ctx.stroke();
    }
    ctx.fillStyle = '#8a9ab5'; ctx.font = '9px system-ui,sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const val = (maxY * (4 - i)) / 4;
      ctx.fillText(val >= 1000 ? '$' + (val / 1000).toFixed(0) + 'K' : '$' + val.toFixed(0), PAD.left - 4, PAD.top + (ph * i / 4) + 3);
    }
    ctx.textAlign = 'center';
    for (let i = 0; i <= 4; i++) {
      const val = (maxX * i) / 4;
      ctx.fillText(val >= 1000 ? '$' + (val / 1000).toFixed(1) + 'K' : '$' + val.toFixed(0), PAD.left + (pw * i / 4), H - PAD.bottom + 14);
    }

    // Draw curve for each channel
    [{ ch: chA, m: mA }, { ch: chB, m: mB }].forEach(({ ch, m }) => {
      const color = channelMeta(ch).color;
      const { L, k } = m.curve_params;

      // Curve
      ctx.beginPath(); let first = true;
      for (let i = 0; i <= 200; i++) {
        const xv = (maxX * i) / 200, yv = Ry(L, k, xv);
        if (first) { ctx.moveTo(toX(xv), toY(yv)); first = false; } else ctx.lineTo(toX(xv), toY(yv));
      }
      ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.lineJoin = 'round'; ctx.stroke();

      // Current marker
      const cx = toX(m.spend_usd), cy = toY(Ry(L, k, m.spend_usd));
      ctx.beginPath(); ctx.arc(cx, cy, 5, 0, Math.PI * 2);
      ctx.fillStyle = color; ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke();

      // Optimal dashed
      ctx.save(); ctx.setLineDash([4, 3]); ctx.strokeStyle = color + '80'; ctx.lineWidth = 1.5;
      const ox = toX(m.optimal_spend_usd);
      ctx.beginPath(); ctx.moveTo(ox, PAD.top); ctx.lineTo(ox, PAD.top + ph); ctx.stroke(); ctx.restore();

      // Labels
      ctx.font = 'bold 9px system-ui,sans-serif'; ctx.textAlign = 'center'; ctx.fillStyle = color;
      ctx.fillText(channelMeta(ch).label, cx, cy - 10);
    });

    // mROAS = 1 break-even line
    ctx.save(); ctx.setLineDash([2, 4]); ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = 1;
    const breakEvenY = toY(maxX * 1); // y where slope=1 isn't directly useful; skip and just note
    ctx.restore();

    // Axis labels
    ctx.fillStyle = '#64748b'; ctx.font = '9px system-ui,sans-serif';
    ctx.textAlign = 'left';
    ctx.save(); ctx.translate(12, PAD.top + ph / 2); ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center'; ctx.fillText('Attributed Revenue ($)', 0, 0); ctx.restore();
    ctx.textAlign = 'center';
    ctx.fillText('Monthly Spend ($)', PAD.left + pw / 2, H - 4);
  }, [chA, chB, personaData]);

  useEffect(() => {
    if (open) { const r = requestAnimationFrame(drawCompare); return () => cancelAnimationFrame(r); }
  }, [open, drawCompare]);

  if (!open) {
    return (
      <button onClick={() => setOpen(true)}
        className="w-full bg-white border border-gray-200 rounded-xl px-5 py-3.5 flex items-center justify-between hover:bg-gray-50 transition-colors group">
        <div className="flex items-center gap-3">
          <span className="text-lg">⚖️</span>
          <div>
            <p className="text-[13px] font-bold text-gray-800">Channel S-Curve Comparison</p>
            <p className="text-[11px] text-gray-400">Overlay two channels on one chart to compare efficiency and find the better next-dollar bet</p>
          </div>
        </div>
        <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
      </button>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="bg-gray-900 px-5 py-3 flex items-center justify-between gap-3 flex-wrap">
        <p className="text-[13px] font-bold text-white">Channel S-Curve Comparison · {persona}</p>
        <div className="flex items-center gap-3">
          {/* Channel A */}
          <select value={chA} onChange={e => setChA(e.target.value)}
            className="text-[11px] bg-gray-800 text-white border border-gray-600 rounded px-2 py-1 font-semibold">
            {activeChannels.filter(ch => ch.id !== chB).map(ch => (
              <option key={ch.id} value={ch.id}>{ch.label}</option>
            ))}
          </select>
          <span className="text-gray-400 text-[11px]">vs</span>
          {/* Channel B */}
          <select value={chB} onChange={e => setChB(e.target.value)}
            className="text-[11px] bg-gray-800 text-white border border-gray-600 rounded px-2 py-1 font-semibold">
            {activeChannels.filter(ch => ch.id !== chA).map(ch => (
              <option key={ch.id} value={ch.id}>{ch.label}</option>
            ))}
          </select>
          <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-white ml-2" title="Collapse">
            <ChevronDown className="w-4 h-4 rotate-180" />
          </button>
        </div>
      </div>

      {/* Comparison canvas */}
      <div className="px-4 pt-3 pb-1" style={{ height: 240 }}>
        <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }}/>
      </div>

      {/* Stats comparison */}
      <div className="px-4 pb-4 grid grid-cols-2 gap-3">
        {[chA, chB].map(chId => {
          const m = personaData[chId] as PaidChannelMetrics;
          const ch = channelMeta(chId);
          const cfg = statusCfg(m.status);
          return (
            <div key={chId} className="rounded-lg border border-gray-200 p-3" style={{ borderLeftColor: ch.color, borderLeftWidth: 3 }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="font-bold text-[12px]" style={{ color: ch.color }}>{ch.icon} {ch.label}</span>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${cfg.cls}`}>{cfg.label}</span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
                <span className="text-gray-400">ROAS <span className="font-bold text-gray-700">{fmtRoas(m.roas)}</span></span>
                <span className="text-gray-400">mROAS <span className="font-bold text-gray-700">{m.marginal_roas.toFixed(2)}×</span></span>
                <span className="text-gray-400">Current <span className="font-bold text-gray-700">{fmtK(m.spend_usd)}/mo</span></span>
                <span className="text-gray-400">Optimal <span className="font-bold text-emerald-600">{fmtK(m.optimal_spend_usd)}/mo</span></span>
                <span className="text-gray-400">Sat. <span className="font-bold text-gray-700">{m.saturation_pct}%</span></span>
                <span className="text-gray-400">CPA <span className="font-bold text-gray-700">${m.cost_per_acquisition.toFixed(0)}</span></span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-gray-100 px-5 py-2.5 bg-gray-50 text-[9.5px] text-gray-400">
        <span className="font-semibold text-gray-500">Reading the chart:</span> Dots mark current spend. Dashed verticals mark optimal spend (mROAS = 1). The steeper the curve at current spend, the more under-invested the channel. Where one curve clearly outpaces the other at the same x-spend level, that channel earns more per dollar.
      </div>
    </div>
  );
}

// ── Export helpers ─────────────────────────────────────────────────────────────

function exportPersonaCSV(persona: string, personaData: Record<string, ChannelMetrics>, monthlyData: Record<string, MonthlyPoint[]>) {
  const paidIds  = Object.keys(personaData).filter(id => !personaData[id].owned_channel);
  const ownedIds = Object.keys(personaData).filter(id => personaData[id].owned_channel);

  const rows: string[] = [
    'Section,Channel,Metric,Value',
    // Summary per paid channel
    ...paidIds.flatMap(id => {
      const ch = channelMeta(id);
      const m = personaData[id] as PaidChannelMetrics;
      return [
        `Optimization,${ch.label},Status,${m.status}`,
        `Optimization,${ch.label},Current Spend ($/mo),${m.spend_usd.toFixed(2)}`,
        `Optimization,${ch.label},Optimal Spend ($/mo),${m.optimal_spend_usd.toFixed(2)}`,
        `Optimization,${ch.label},Delta ($/mo),${(m.optimal_spend_usd - m.spend_usd).toFixed(2)}`,
        `Optimization,${ch.label},ROAS,${m.roas.toFixed(2)}`,
        `Optimization,${ch.label},Marginal ROAS,${m.marginal_roas.toFixed(4)}`,
        `Optimization,${ch.label},Saturation %,${m.saturation_pct}`,
        `Optimization,${ch.label},Conversion Rate %,${(m.conversion_rate * 100).toFixed(2)}`,
        `Optimization,${ch.label},CPA ($),${m.cost_per_acquisition.toFixed(2)}`,
        m.true_roi_pct != null ? `Optimization,${ch.label},Business ROI %,${m.true_roi_pct.toFixed(1)}` : null,
      ].filter(Boolean) as string[];
    }),
    // Owned channels — no ad spend, kept in their own section so a $0 row
    // never reads as "missing" data mixed into the optimization table above.
    '',
    'Section,Channel,Metric,Value',
    ...ownedIds.flatMap(id => {
      const ch = channelMeta(id);
      const m = personaData[id];
      return [
        `Owned Channels (Not Ad Spend),${ch.label},Spend ($/mo),0.00`,
        `Owned Channels (Not Ad Spend),${ch.label},Attributed Revenue ($),${m.attributed_revenue_usd.toFixed(2)}`,
        `Owned Channels (Not Ad Spend),${ch.label},Conversion Rate %,${(m.conversion_rate * 100).toFixed(2)}`,
      ];
    }),
    // Monthly detail (paid channels — owned channels have no spend/ROAS trend)
    '',
    'Month,Channel,Spend ($),Revenue ($),ROAS,Converted',
    ...paidIds.flatMap(id => {
      const ch = channelMeta(id);
      return (monthlyData[id] ?? []).map(p =>
        `${p.month_name},${ch.label},${p.spend_usd.toFixed(2)},${p.revenue_usd.toFixed(2)},${p.roas.toFixed(2)},${p.converted}`
      );
    }),
  ];

  const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `meridian_adspend_${persona.replace(/\s+/g, '_')}.csv`;
  a.click(); URL.revokeObjectURL(url);
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function BankingAdSpend() {
  const [selectedPersona, setSelectedPersona] = useState('Digital Native');
  const [howOpen, setHowOpen] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery<AdSpendData>({
    queryKey: ['banking-ad-spend-metrics'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/api/banking/ad_spend/metrics`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: monthlyData } = useQuery<MonthlyData>({
    queryKey: ['banking-ad-spend-monthly'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/api/banking/ad_spend/monthly`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    },
    staleTime: 30 * 60 * 1000,
  });

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center space-y-3">
        <div className="w-10 h-10 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"/>
        <p className="text-sm text-gray-500">Loading spend metrics from 12-month dataset…</p>
      </div>
    </div>
  );

  if (isError || !data?.success) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center space-y-3">
        <AlertTriangle className="w-10 h-10 text-red-400 mx-auto"/>
        <p className="text-sm text-gray-600">Failed to load ad spend metrics.</p>
        <button onClick={() => refetch()} className="text-sm font-medium text-blue-600 underline">Retry</button>
      </div>
    </div>
  );

  const { summary, personas } = data;
  const personaData = personas[selectedPersona] ?? {};
  const monthly     = monthlyData?.data?.[selectedPersona] ?? {};

  const allChannels   = data.channels.map(channelMeta);
  const paidChannels   = data.channels.filter(id => !data.owned_channels.includes(id)).map(channelMeta);
  const ownedChannels  = data.owned_channels.map(channelMeta);

  const segUplift = paidChannels.reduce((s, ch) => {
    const m = personaData[ch.id] as PaidChannelMetrics | undefined;
    return (!m || m.status !== 'under') ? s : s + (m.optimal_spend_usd - m.spend_usd) * m.marginal_roas;
  }, 0);

  return (
    <div className="space-y-5 pb-10">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Channel Ad Spend Optimization</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Marginal response curves · 12-month dataset (Jan–Dec 2025) · Interactive hover + what-if simulation
          </p>
        </div>
        <span className="text-[11px] px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 font-medium">
          Source: {data.data_source}
        </span>
      </div>

      {/* Metrics bar */}
      <div className="grid grid-cols-3 divide-x divide-gray-200 border border-gray-200 rounded-xl overflow-hidden bg-white">
        {[
          { label:'Total Ad Spend',      value:fmtK(summary.total_spend_usd),                    sub:`across ${paidChannels.length} paid channels${ownedChannels.length ? ` (+${ownedChannels.length} owned)` : ''} · ${PERSONAS.length} segments`, Icon:DollarSign, color:'text-gray-800' },
          { label:'Attributed Revenue',  value:fmtK(summary.total_revenue_usd),                  sub:'annual marketing attributed (paid channels)', Icon:BarChart2,  color:'text-gray-800' },
          { label:'Blended ROAS',        value:fmtRoas(summary.blended_roas),                    sub:'revenue per $ spent',            Icon:TrendingUp,  color:'text-blue-700' },
        ].map(m => (
          <div key={m.label} className="px-4 py-4 flex flex-col items-center text-center">
            <div className="flex items-center justify-center gap-1.5 mb-2">
              <m.Icon className={`w-3.5 h-3.5 ${m.color}`}/>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">{m.label}</p>
            </div>
            <p className={`text-[21px] font-bold tabular-nums leading-none ${m.color}`}>{m.value}</p>
            <p className="text-[10px] text-gray-400 mt-1.5">{m.sub}</p>
          </div>
        ))}
      </div>

      {/* Segment tabs */}
      <div className="border-b border-gray-200 flex overflow-x-auto">
        {PERSONAS.map(p => (
          <button key={p.id} onClick={() => setSelectedPersona(p.id)}
            className={`flex items-center gap-2 px-5 py-3 text-[13px] font-semibold border-b-2 transition-all whitespace-nowrap flex-shrink-0 ${
              selectedPersona === p.id ? 'text-gray-900 border-gray-900' : 'text-gray-500 border-transparent hover:text-gray-700'}`}>
            <span className="w-2 h-2 rounded-full" style={{background:p.color}}/>
            {p.id}
          </button>
        ))}
      </div>

      {/* Segment AI */}
      <div className="border-l-4 border-gray-800 pl-4 py-1">
        <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1">AI · {selectedPersona} Budget Analysis</p>
        <p className="text-[13px] text-gray-700 leading-relaxed">{segInsight(selectedPersona, personaData)}</p>
      </div>

      {/* Seasonality sparkline strip */}
      {monthlyData?.data?.[selectedPersona] && (
        <SeasonalityStrip allMonthly={monthly} channels={paidChannels} ownedChannels={ownedChannels} personaData={personaData} />
      )}

      {/* Channel grid */}
      <div className="grid grid-cols-2 gap-4">
        {allChannels.map(ch => {
          const m = personaData[ch.id];
          if (!m) return (
            <div key={ch.id} className="bg-white rounded-xl border border-gray-200 p-8 flex items-center justify-center">
              <p className="text-sm text-gray-400">No data for {ch.label}</p>
            </div>
          );
          if (m.owned_channel) return (
            <OwnedChannelCard key={`${selectedPersona}-${ch.id}`} ch={ch} metrics={m} />
          );
          return (
            <ChannelCard key={`${selectedPersona}-${ch.id}`}
              ch={ch} metrics={m as PaidChannelMetrics} personaName={selectedPersona}
              allData={personaData} monthly={monthly[ch.id] ?? []}
              productValueBenchmarks={data.product_value_benchmarks}
              bizCostBenchmarks={data.biz_cost_benchmarks}
              riskRateBenchmarks={data.risk_rate_benchmarks} />
          );
        })}
      </div>

      {/* Channel Comparison Overlay */}
      <ChannelCompare personaData={personaData} persona={selectedPersona} />

      {/* Reallocation Reference Panel */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">

        {/* Header */}
        <div className="bg-gray-900 px-5 py-3.5 flex items-center justify-between flex-wrap gap-2">
          <div>
            <p className="text-[13px] font-bold text-white">Reallocation Rationale</p>
            <p className="text-[11px] text-gray-400 mt-0.5">{selectedPersona} · why these moves are recommended</p>
          </div>
          <div className="flex items-center gap-2">
            {segUplift > 0 && (
              <span className="text-[12px] font-bold px-3 py-1.5 bg-emerald-500 text-white rounded-full">
                +{fmtK(segUplift)}/mo potential uplift
              </span>
            )}
            <button
              onClick={() => exportPersonaCSV(selectedPersona, personaData, monthly)}
              className="flex items-center gap-1.5 text-[11px] font-bold px-3 py-1.5 rounded-md bg-gray-700 text-gray-100 hover:bg-gray-600 transition-colors">
              ↓ Export CSV
            </button>
          </div>
        </div>

        {/* How it works — 3-step explanation (collapsible) */}
        <div className="bg-slate-50 border-b border-slate-200">
          <button onClick={() => setHowOpen(o => !o)}
            className="w-full px-5 py-4 flex items-center justify-between hover:bg-slate-100/60 transition-colors">
            <p className="text-[11px] font-bold text-slate-700 uppercase tracking-wide">How this recommendation is calculated?</p>
            <ChevronDown className={`w-4 h-4 text-slate-500 flex-shrink-0 transition-transform ${howOpen ? 'rotate-180' : ''}`} />
          </button>
          {howOpen && (
          <div className="px-5 pb-4 grid grid-cols-3 gap-4">
            {[
              {
                step: '01',
                title: 'Fit the S-curve',
                body: 'We fit R(x) = L×(1−e⁻ᵏˣ) to 12 months of spend/revenue per channel. L is the revenue ceiling; k controls how fast returns diminish. This captures the real-world truth: early spend works hard, later spend faces saturation.',
                color: 'bg-blue-100 text-blue-700',
              },
              {
                step: '02',
                title: 'Identify over/under',
                body: 'Marginal ROAS (mROAS) is the derivative of the curve at current spend. mROAS > 1.25 = under-invested (each extra $1 returns $1.25+). mROAS < 0.80 = over-invested (the curve has flattened, extra spend barely moves revenue).',
                color: 'bg-amber-100 text-amber-700',
              },
              {
                step: '03',
                title: 'Rebalance budget',
                body: "We move dollars from channels past the curve’s knee to channels still on the steep rise — same total spend, higher total revenue. The optimal point is where mROAS = 1: the last dollar spent returns exactly $1.",
                color: 'bg-emerald-100 text-emerald-700',
              },
            ].map(s => (
              <div key={s.step} className="flex gap-3">
                <span className={`text-[10px] font-black px-2 py-0.5 rounded self-start mt-0.5 ${s.color}`}>{s.step}</span>
                <div>
                  <p className="text-[11px] font-bold text-gray-800 mb-1">{s.title}</p>
                  <p className="text-[10.5px] text-gray-500 leading-relaxed">{s.body}</p>
                </div>
              </div>
            ))}
          </div>
          )}
        </div>

        {/* Channel rows */}
        <div className="divide-y divide-gray-100">

          {/* Over-invested — reduce these */}
          {paidChannels.filter(ch => (personaData[ch.id] as PaidChannelMetrics | undefined)?.status === 'over').map(ch => {
            const m   = personaData[ch.id] as PaidChannelMetrics;
            const cut = m.spend_usd - m.optimal_spend_usd;
            const lostRev = cut * m.marginal_roas;
            return (
              <div key={ch.id} className="px-5 py-4 bg-red-50/30">
                <div className="flex items-center gap-3 flex-wrap mb-2">
                  <span className="text-[13px] font-bold w-24" style={{color:ch.color}}>{ch.icon} {ch.label}</span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-red-100 text-red-700 font-semibold border border-red-200">▼ Reduce</span>
                  <span className="text-[12px] text-red-700 tabular-nums font-semibold">{fmtK(m.spend_usd)}/mo</span>
                  <span className="text-gray-400">→</span>
                  <span className="text-[12px] text-gray-700 tabular-nums font-semibold">{fmtK(m.optimal_spend_usd)}/mo</span>
                  <span className="ml-auto text-[12px] text-red-700 font-bold">−{fmtK(cut)} freed</span>
                </div>
                <div className="ml-27 pl-1 space-y-1">
                  <p className="text-[10.5px] text-gray-600 leading-snug">
                    <span className="font-semibold text-red-600">Why reduce?</span> The S-curve has flattened here — marginal return is only <span className="font-bold">${m.marginal_roas.toFixed(2)}</span> per $1 spent ({m.saturation_pct}% saturated). The last {fmtK(cut)} of budget is generating only ~{fmtK(lostRev)} in incremental revenue, well below break-even. Cutting to optimal <span className="font-semibold">{fmtK(m.optimal_spend_usd)}/mo</span> preserves most of the revenue while freeing capital for higher-return channels.
                  </p>
                  <div className="flex gap-4 text-[10px] text-gray-400">
                    <span>ROAS: <span className="font-semibold text-gray-600">{fmtRoas(m.roas)}</span></span>
                    <span>mROAS: <span className="font-semibold text-red-600">{m.marginal_roas.toFixed(2)}×</span></span>
                    <span>Conv. rate: <span className="font-semibold text-gray-600">{(m.conversion_rate*100).toFixed(2)}%</span></span>
                    <span>CPA: <span className="font-semibold text-gray-600">${m.cost_per_acquisition.toFixed(0)}</span></span>
                    {m.true_roi_pct != null && <span>Biz ROI: <span className="font-semibold text-gray-600">{m.true_roi_pct.toFixed(0)}%</span></span>}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Under-invested — increase these */}
          {paidChannels.filter(ch => (personaData[ch.id] as PaidChannelMetrics | undefined)?.status === 'under').map(ch => {
            const m      = personaData[ch.id] as PaidChannelMetrics;
            const add    = m.optimal_spend_usd - m.spend_usd;
            const revGain= add * m.marginal_roas;
            return (
              <div key={ch.id} className="px-5 py-4 bg-emerald-50/30">
                <div className="flex items-center gap-3 flex-wrap mb-2">
                  <span className="text-[13px] font-bold w-24" style={{color:ch.color}}>{ch.icon} {ch.label}</span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 font-semibold border border-emerald-200">▲ Increase</span>
                  <span className="text-[12px] text-gray-700 tabular-nums font-semibold">{fmtK(m.spend_usd)}/mo</span>
                  <span className="text-gray-400">→</span>
                  <span className="text-[12px] text-emerald-700 tabular-nums font-semibold">{fmtK(m.optimal_spend_usd)}/mo</span>
                  <span className="ml-auto text-[12px] text-emerald-700 font-bold">+{fmtK(revGain)} revenue</span>
                </div>
                <div className="space-y-1">
                  <p className="text-[10.5px] text-gray-600 leading-snug">
                    <span className="font-semibold text-emerald-700">Why increase?</span> The S-curve is still steep here — marginal return is <span className="font-bold">${m.marginal_roas.toFixed(2)}</span> per $1 spent, meaning the channel is only <span className="font-semibold">{m.saturation_pct}% saturated</span>. Every additional dollar has high leverage. Adding {fmtK(add)} to reach optimal <span className="font-semibold">{fmtK(m.optimal_spend_usd)}/mo</span> is predicted to generate <span className="font-bold text-emerald-700">+{fmtK(revGain)} in attributed revenue</span> — a {((revGain / add)).toFixed(1)}× return on the incremental spend.
                  </p>
                  <div className="flex gap-4 text-[10px] text-gray-400">
                    <span>ROAS: <span className="font-semibold text-gray-600">{fmtRoas(m.roas)}</span></span>
                    <span>mROAS: <span className="font-semibold text-emerald-600">{m.marginal_roas.toFixed(2)}×</span></span>
                    <span>Conv. rate: <span className="font-semibold text-gray-600">{(m.conversion_rate*100).toFixed(2)}%</span></span>
                    <span>CPA: <span className="font-semibold text-gray-600">${m.cost_per_acquisition.toFixed(0)}</span></span>
                    {m.true_roi_pct != null && <span>Biz ROI: <span className="font-semibold text-gray-600">{m.true_roi_pct.toFixed(0)}%</span></span>}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Optimal — hold */}
          {paidChannels.filter(ch => (personaData[ch.id] as PaidChannelMetrics | undefined)?.status === 'optimal').map(ch => {
            const m = personaData[ch.id] as PaidChannelMetrics;
            return (
              <div key={ch.id} className="px-5 py-3.5 flex items-start gap-3 flex-wrap opacity-70">
                <span className="text-[13px] font-bold w-24 mt-0.5" style={{color:ch.color}}>{ch.icon} {ch.label}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-3 flex-wrap mb-1">
                    <span className="text-[11px] px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold border border-blue-100">✓ Optimal</span>
                    <span className="text-[12px] text-gray-500 tabular-nums">{fmtK(m.spend_usd)}/mo</span>
                    <span className="ml-auto text-[12px] text-gray-400">Hold</span>
                  </div>
                  <p className="text-[10.5px] text-gray-500">
                    mROAS {m.marginal_roas.toFixed(2)}× — at the curve's knee. Revenue is maximally efficient here; shifts either way yield diminishing impact. No action needed.
                  </p>
                </div>
              </div>
            );
          })}

          {/* Owned channels — not part of reallocation, shown for transparency */}
          {ownedChannels.filter(ch => personaData[ch.id]).length > 0 && (
            <div className="px-5 py-3.5 flex items-start gap-3 flex-wrap bg-gray-50/60">
              <span className="text-[13px] font-bold w-24 mt-0.5 text-gray-500">Owned</span>
              <div className="flex-1">
                <p className="text-[10.5px] text-gray-500">
                  {ownedChannels.filter(ch => personaData[ch.id]).map(ch =>
                    `${ch.label}: ${fmtK(personaData[ch.id].attributed_revenue_usd)} attributed revenue, $0 spend`
                  ).join(' · ')} — not included in reallocation (no spend to optimize).
                </p>
              </div>
            </div>
          )}

          {Object.keys(personaData).length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-gray-400">No data for this segment.</div>
          )}
        </div>

        {/* Legend */}
        <div className="border-t border-gray-100 px-5 py-3 bg-gray-50 flex flex-wrap gap-5 text-[10px] text-gray-500 items-center">
          <span className="flex items-center gap-2"><span className="w-5 border-t-2 border-dashed border-green-500 inline-block"/>Optimal spend (mROAS=1)</span>
          <span className="flex items-center gap-2"><span className="w-5 border-t-2 border-dashed border-red-400 inline-block"/>Current spend</span>
          <span className="flex items-center gap-2"><span className="w-5 border-t-2 border-dashed border-blue-500 inline-block"/>What-if (slider)</span>
          <span className="ml-auto text-[9px] text-gray-400">Model: R(x)=L·(1−e<sup>−kx</sup>) · Costs: fully-loaded industry benchmarks · Hover curve for real-time values</span>
        </div>
      </div>
    </div>
  );
}

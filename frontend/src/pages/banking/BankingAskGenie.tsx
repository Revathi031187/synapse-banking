import React from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  BarChart2, Table2, X, Send, ChevronDown, Plus, Sparkles,
  Download, Copy, Check, TrendingUp, PieChart as PieIcon, Activity,
  Trash2, Database,
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

import { getBankingApiBase } from '../../utils/apiBase';

// ── Types ────────────────────────────────────────────────────────────────────

interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'area' | 'none';
  x_col: string;
  y_col: string;
  title: string;
}

interface TableData {
  columns: string[];
  rows: (string | number)[][];
}

interface ChatResponse {
  success: boolean;
  narrative: string;
  sql: string | null;
  table: TableData | null;
  chart: ChartConfig | null;
  follow_ups: string[];
  sql_error?: string | null;
  error?: string;
}

interface ChatEntry {
  question: string;
  answer: ChatResponse;
}

interface ConversationBreak {
  type: 'break';
}

type HistoryItem = ChatEntry | ConversationBreak;

// ── Constants ─────────────────────────────────────────────────────────────────

const PALETTE = [
  '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444',
  '#06B6D4', '#EC4899', '#84CC16', '#F97316', '#6366F1',
];

const CHART_TYPE_ICONS: Record<string, React.ReactNode> = {
  bar:  <BarChart2 className="w-3.5 h-3.5" />,
  line: <TrendingUp className="w-3.5 h-3.5" />,
  pie:  <PieIcon className="w-3.5 h-3.5" />,
  area: <Activity className="w-3.5 h-3.5" />,
};

const SUGGESTED_QUESTIONS = [
  "Which customer segment has the highest churn risk?",
  "Who are the top 10 most valuable customers by CLV?",
  "What is the ROAS by marketing channel and persona?",
  "Which customers started an application but never completed it?",
  "Show average income and credit score by life stage",
  "What products are customers wishlisting but not applying for?",
  "Compare total transaction volume by life stage",
  "Show monthly marketing spend trend across all channels",
];

const STORAGE_KEY = 'segment_ai_history_v2';

// ── CSV export ────────────────────────────────────────────────────────────────

function exportCsv(table: TableData, title: string) {
  const header = table.columns.join(',');
  const rows = table.rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(','));
  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${title.toLowerCase().replace(/\s+/g, '_')}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── CopyButton ────────────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = React.useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1800);
        });
      }}
      className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded border border-slate-600 text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors"
    >
      {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
      {copied ? 'Copied' : 'Copy SQL'}
    </button>
  );
}

// ── Number formatter for Y-axis ───────────────────────────────────────────────

function fmtNum(v: number): string {
  if (Math.abs(v) >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'M';
  if (Math.abs(v) >= 1_000) return (v / 1_000).toFixed(1) + 'K';
  if (Math.abs(v) < 0.01 && v !== 0) return v.toExponential(2);
  if (Math.round(v) === v) return v.toString();
  return v.toFixed(2);
}

function fmtTooltip(v: number): string {
  if (Math.abs(v) >= 1_000_000) return (v / 1_000_000).toFixed(2) + 'M';
  if (Math.abs(v) >= 1_000) return (v / 1_000).toFixed(1) + 'K';
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

// ── Markdown renderer ─────────────────────────────────────────────────────────

function renderInline(text: string, key: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/);
  return (
    <React.Fragment key={key}>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**'))
          return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
        if (part.startsWith('*') && part.endsWith('*'))
          return <em key={i} className="italic text-slate-700">{part.slice(1, -1)}</em>;
        if (part.startsWith('`') && part.endsWith('`'))
          return <code key={i} className="bg-violet-50 text-violet-700 px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
        return part;
      })}
    </React.Fragment>
  );
}

function NarrativeMarkdown({ text }: { text: string }) {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let bulletBuffer: React.ReactNode[] = [];
  let idx = 0;

  const flushBullets = () => {
    if (bulletBuffer.length > 0) {
      elements.push(
        <ul key={`ul-${idx++}`} className="mt-1.5 mb-1.5 space-y-0.5 pl-1">
          {bulletBuffer}
        </ul>
      );
      bulletBuffer = [];
    }
  };

  lines.forEach((line, i) => {
    const isBullet = line.startsWith('- ') || line.startsWith('• ');
    if (!isBullet) flushBullets();

    if (/^## /.test(line)) {
      elements.push(
        <p key={i} className="font-bold text-sm text-slate-900 mt-3 mb-1">
          {renderInline(line.slice(3), `h2-${i}`)}
        </p>
      );
    } else if (/^### /.test(line)) {
      elements.push(
        <p key={i} className="font-semibold text-sm text-slate-800 mt-2 mb-0.5">
          {renderInline(line.slice(4), `h3-${i}`)}
        </p>
      );
    } else if (isBullet) {
      bulletBuffer.push(
        <li key={i} className="flex items-start gap-1.5">
          <span className="mt-1.5 w-1 h-1 rounded-full bg-violet-400 flex-shrink-0" />
          <span className="text-sm text-slate-700 leading-relaxed">
            {renderInline(line.slice(2), `li-${i}`)}
          </span>
        </li>
      );
    } else if (line.trim() === '') {
      elements.push(<div key={i} className="h-1.5" />);
    } else {
      elements.push(
        <p key={i} className="text-sm text-slate-700 leading-relaxed">
          {renderInline(line, `p-${i}`)}
        </p>
      );
    }
  });

  flushBullets();
  return <div className="space-y-0.5">{elements}</div>;
}

// ── ResultChart ───────────────────────────────────────────────────────────────

const BAR_LIMIT = 15;
const PIE_LIMIT = 7;
const LINE_LIMIT = 60;

function ResultChart({
  table,
  config,
}: {
  table: TableData;
  config: ChartConfig;
}) {
  const [activeType, setActiveType] = React.useState<'bar' | 'line' | 'pie' | 'area'>(
    config.type === 'none' ? 'bar' : config.type
  );

  const xIdx = table.columns.indexOf(config.x_col);
  const yIdx = table.columns.indexOf(config.y_col);
  const xi = xIdx >= 0 ? xIdx : 0;
  const yi = yIdx >= 0 ? yIdx : (table.columns.length > 1 ? 1 : 0);

  // All rows → {x, y}, then collapse duplicate x values by averaging y
  const allData = React.useMemo(() => {
    const raw = table.rows
      .map(r => ({ x: String(r[xi] ?? ''), y: parseFloat(String(r[yi] ?? '0')) || 0 }))
      .filter(d => d.x !== '' && !isNaN(d.y));

    // Detect duplicates — if >30% of x values repeat, auto-aggregate
    const uniqueX = new Set(raw.map(d => d.x));
    if (raw.length > 15 && uniqueX.size < raw.length * 0.6) {
      const groups = new Map<string, number[]>();
      raw.forEach(({ x, y }) => {
        if (!groups.has(x)) groups.set(x, []);
        groups.get(x)!.push(y);
      });
      const sumKw = /(revenue|spend|amount|count|total|cost|sales)/i.test(config.y_col);
      const agg: { x: string; y: number }[] = [];
      groups.forEach((ys, x) => {
        const v = sumKw ? ys.reduce((s, v) => s + v, 0) : ys.reduce((s, v) => s + v, 0) / ys.length;
        agg.push({ x, y: Math.round(v * 100) / 100 });
      });
      return agg;
    }
    return raw;
  }, [table.rows, xi, yi, config.y_col]);

  // Per-type slicing
  const { chartData, truncatedFrom } = React.useMemo(() => {
    if (activeType === 'pie') {
      const sorted = [...allData].sort((a, b) => b.y - a.y);
      if (sorted.length <= PIE_LIMIT) return { chartData: sorted, truncatedFrom: 0 };
      const top = sorted.slice(0, PIE_LIMIT);
      const othersY = sorted.slice(PIE_LIMIT).reduce((s, d) => s + d.y, 0);
      return { chartData: [...top, { x: 'Others', y: Math.round(othersY * 100) / 100 }], truncatedFrom: sorted.length };
    }
    if (activeType === 'bar') {
      const sorted = [...allData].sort((a, b) => b.y - a.y);
      if (sorted.length <= BAR_LIMIT) return { chartData: sorted, truncatedFrom: 0 };
      return { chartData: sorted.slice(0, BAR_LIMIT), truncatedFrom: sorted.length };
    }
    // line / area — preserve original order (time series)
    if (allData.length <= LINE_LIMIT) return { chartData: allData, truncatedFrom: 0 };
    return { chartData: allData.slice(0, LINE_LIMIT), truncatedFrom: allData.length };
  }, [allData, activeType]);

  const tickAngle = chartData.length > 6 ? -40 : 0;
  const bottomMargin = chartData.length > 6 ? 70 : 35;
  const margin = { top: 10, right: 20, left: 10, bottom: bottomMargin };

  const typeButtons: Array<'bar' | 'line' | 'area' | 'pie'> = ['bar', 'line', 'area', 'pie'];

  const tooltipStyle = { fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' };
  const tickStyle = { fontSize: 11, fill: '#64748b' };

  // Truncate long x labels
  const truncLabel = (s: string) => s.length > 18 ? s.slice(0, 16) + '…' : s;

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-slate-800">
        <span className="text-xs font-semibold text-slate-300 truncate flex-1">{config.title}</span>
        {truncatedFrom > 0 && (
          <span className="text-[10px] text-slate-500 whitespace-nowrap">
            top {activeType === 'pie' ? PIE_LIMIT : BAR_LIMIT} of {truncatedFrom}
          </span>
        )}
        <div className="flex gap-1">
          {typeButtons.map(t => (
            <button
              key={t}
              type="button"
              onClick={() => setActiveType(t)}
              title={t.charAt(0).toUpperCase() + t.slice(1)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                activeType === t ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700 hover:text-white'
              }`}
            >
              {CHART_TYPE_ICONS[t]}
              <span className="hidden sm:inline capitalize">{t}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="p-4">
        <ResponsiveContainer width="100%" height={300}>
          {activeType === 'bar' ? (
            <BarChart data={chartData} margin={margin}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="x" tick={{ ...tickStyle, fontSize: chartData.length > 8 ? 10 : 11 }}
                angle={tickAngle} textAnchor={tickAngle ? 'end' : 'middle'} interval={0}
                tickFormatter={truncLabel} />
              <YAxis tick={tickStyle} tickFormatter={fmtNum} width={52} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v: number) => [fmtTooltip(v), config.y_col]}
                labelFormatter={(l: string) => l} />
              <Bar dataKey="y" name={config.y_col} radius={[4, 4, 0, 0]} maxBarSize={56}>
                {chartData.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
              </Bar>
            </BarChart>
          ) : activeType === 'line' ? (
            <LineChart data={chartData} margin={margin}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="x" tick={{ ...tickStyle, fontSize: chartData.length > 12 ? 10 : 11 }}
                angle={tickAngle} textAnchor={tickAngle ? 'end' : 'middle'} interval={0}
                tickFormatter={truncLabel} />
              <YAxis tick={tickStyle} tickFormatter={fmtNum} width={52} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v: number) => [fmtTooltip(v), config.y_col]} />
              <Line type="monotone" dataKey="y" name={config.y_col}
                stroke={PALETTE[0]} strokeWidth={2.5} dot={{ r: chartData.length > 20 ? 2 : 4, fill: PALETTE[0] }}
                activeDot={{ r: 5 }} />
            </LineChart>
          ) : activeType === 'area' ? (
            <AreaChart data={chartData} margin={margin}>
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={PALETTE[0]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={PALETTE[0]} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="x" tick={{ ...tickStyle, fontSize: chartData.length > 12 ? 10 : 11 }}
                angle={tickAngle} textAnchor={tickAngle ? 'end' : 'middle'} interval={0}
                tickFormatter={truncLabel} />
              <YAxis tick={tickStyle} tickFormatter={fmtNum} width={52} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v: number) => [fmtTooltip(v), config.y_col]} />
              <Area type="monotone" dataKey="y" name={config.y_col}
                stroke={PALETTE[0]} strokeWidth={2} fill="url(#areaGrad)"
                dot={false} activeDot={{ r: 4 }} />
            </AreaChart>
          ) : (
            // Pie
            <PieChart margin={{ top: 0, right: 20, left: 20, bottom: 0 }}>
              <Pie
                data={chartData}
                dataKey="y"
                nameKey="x"
                cx="50%"
                cy="45%"
                outerRadius={105}
                innerRadius={38}
                paddingAngle={2}
                label={({ name, value, percent }: { name?: string; value?: number; percent?: number }) => {
                  if ((percent ?? 0) <= 0.04) return '';
                  const n = truncLabel(String(name ?? ''));
                  const v = fmtNum(Number(value ?? 0));
                  return `${n} ${v} (${((percent ?? 0) * 100).toFixed(0)}%)`;
                }}
                labelLine={false}
              >
                {chartData.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v: number) => [fmtTooltip(v), config.y_col]} />
              <Legend wrapperStyle={{ fontSize: 11, marginTop: 4 }} />
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ── ResultTable ───────────────────────────────────────────────────────────────

function ResultTable({ table, title }: { table: TableData; title: string }) {
  const [sortCol, setSortCol] = React.useState<number | null>(null);
  const [sortDir, setSortDir] = React.useState<'asc' | 'desc'>('desc');
  const [page, setPage] = React.useState(0);
  const [canScrollRight, setCanScrollRight] = React.useState(false);
  const [canScrollLeft, setCanScrollLeft] = React.useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const PAGE_SIZE = 50;

  const manyColumns = table.columns.length > 6;

  const sorted = React.useMemo(() => {
    if (sortCol === null) return table.rows;
    return [...table.rows].sort((a, b) => {
      const av = a[sortCol], bv = b[sortCol];
      const an = parseFloat(String(av)), bn = parseFloat(String(bv));
      if (!isNaN(an) && !isNaN(bn)) return sortDir === 'asc' ? an - bn : bn - an;
      return sortDir === 'asc' ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
  }, [table.rows, sortCol, sortDir]);

  const pages = Math.ceil(sorted.length / PAGE_SIZE);
  const visible = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleSort = (ci: number) => {
    if (sortCol === ci) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortCol(ci);
      setSortDir('desc');
    }
    setPage(0);
  };

  const checkScroll = React.useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 4);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
  }, []);

  React.useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    checkScroll();
    el.addEventListener('scroll', checkScroll, { passive: true });
    const ro = new ResizeObserver(checkScroll);
    ro.observe(el);
    return () => { el.removeEventListener('scroll', checkScroll); ro.disconnect(); };
  }, [checkScroll, table]);

  return (
    <div className="rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-slate-800">
        <Table2 className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
        <span className="text-xs font-semibold text-slate-300">
          {table.rows.length.toLocaleString()} row{table.rows.length !== 1 ? 's' : ''} · {table.columns.length} columns
        </span>
        {manyColumns && canScrollRight && (
          <span className="text-[10px] text-slate-500 hidden sm:inline">scroll →</span>
        )}
        <div className="ml-auto flex gap-1">
          <button
            type="button"
            onClick={() => exportCsv(table, title)}
            className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded border border-slate-600 text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors"
          >
            <Download className="w-3 h-3" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Scrollable table wrapper with fade shadows */}
      <div className="relative">
        {/* Left fade */}
        {canScrollLeft && (
          <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-8 z-20"
            style={{ background: 'linear-gradient(to right, rgba(241,245,249,0.95), transparent)' }} />
        )}
        {/* Right fade */}
        {canScrollRight && (
          <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-10 z-20"
            style={{ background: 'linear-gradient(to left, rgba(241,245,249,0.95), transparent)' }} />
        )}

        <div ref={scrollRef} className="overflow-x-auto overflow-y-auto max-h-80">
          <table className="text-sm border-collapse" style={{ minWidth: '100%', width: 'max-content' }}>
            <thead className="sticky top-0 bg-slate-100 z-10">
              <tr>
                {table.columns.map((col, ci) => (
                  <th
                    key={ci}
                    onClick={() => handleSort(ci)}
                    className="px-3 py-2 text-left text-xs font-bold text-slate-600 uppercase tracking-wide border-b border-slate-200 whitespace-nowrap cursor-pointer hover:bg-slate-200 select-none"
                  >
                    <span className="flex items-center gap-1">
                      {col}
                      {sortCol === ci && (
                        <span className="text-blue-600">{sortDir === 'desc' ? '↓' : '↑'}</span>
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((row, ri) => (
                <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-3 py-2 text-slate-700 border-b border-slate-100 whitespace-nowrap text-xs">
                      {String(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {pages > 1 && (
        <div className="flex items-center justify-between px-4 py-2 bg-slate-50 border-t border-slate-200 text-xs text-slate-500">
          <span>Page {page + 1} of {pages}</span>
          <div className="flex gap-1">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
              className="px-2 py-0.5 rounded border border-slate-200 disabled:opacity-40 hover:bg-slate-100">
              ‹ Prev
            </button>
            <button disabled={page >= pages - 1} onClick={() => setPage(p => p + 1)}
              className="px-2 py-0.5 rounded border border-slate-200 disabled:opacity-40 hover:bg-slate-100">
              Next ›
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── ChatMessage ───────────────────────────────────────────────────────────────

function ChatMessage({
  entry,
  onFollowUp,
  isPending,
}: {
  entry: ChatEntry;
  onFollowUp: (q: string) => void;
  isPending: boolean;
}) {
  const ans = entry.answer;
  const hasTable = !!(ans.table?.columns.length);
  const hasChart = !!(ans.chart && ans.chart.type !== 'none');
  const [activeView, setActiveView] = React.useState<'table' | 'chart'>(hasChart ? 'chart' : 'table');

  return (
    <div className="space-y-3">
      {/* User bubble */}
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-blue-700 text-white text-sm rounded-2xl rounded-tr-sm px-4 py-3 leading-relaxed shadow-sm">
          {entry.question}
        </div>
      </div>

      {/* AI response */}
      <div className="flex justify-start">
        <div className="max-w-[92%] w-full space-y-3">

          {/* Error state */}
          {!ans.success && ans.error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl rounded-tl-sm px-4 py-3">
              <p className="text-[11px] font-bold text-red-400 uppercase tracking-widest mb-1">Error</p>
              <p className="text-sm text-red-800">{ans.error}</p>
            </div>
          )}

          {/* Narrative */}
          {ans.narrative && (
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3.5 shadow-sm"
              style={{ borderLeft: '3px solid #8B5CF6' }}>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-3.5 h-3.5 text-violet-500 flex-shrink-0" />
                <p className="text-[11px] font-bold text-violet-500 uppercase tracking-widest">Segment AI</p>
              </div>
              <NarrativeMarkdown text={ans.narrative} />
              {ans.sql_error && (
                <p className="mt-2 text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                  Note: {ans.sql_error}
                </p>
              )}
            </div>
          )}

          {/* Table + Chart tabs */}
          {(hasTable || hasChart) && (
            <div className="space-y-2">
              {/* View switcher (only if both exist) */}
              {hasTable && hasChart && (
                <div className="flex gap-1">
                  <button
                    type="button"
                    onClick={() => setActiveView('chart')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                      activeView === 'chart' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <BarChart2 className="w-3.5 h-3.5" /> Chart
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveView('table')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                      activeView === 'table' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <Table2 className="w-3.5 h-3.5" /> Table
                  </button>
                </div>
              )}

              {/* Chart */}
              {hasChart && (activeView === 'chart' || !hasTable) && (
                <ResultChart table={ans.table!} config={ans.chart!} />
              )}

              {/* Table */}
              {hasTable && (activeView === 'table' || !hasChart) && (
                <ResultTable table={ans.table!} title={ans.chart?.title || entry.question} />
              )}
            </div>
          )}

          {/* SQL */}
          {ans.sql && (
            <details className="group">
              <summary className="cursor-pointer inline-flex items-center gap-1.5 text-slate-400 hover:text-slate-600 text-xs font-medium select-none list-none">
                <ChevronDown className="w-3.5 h-3.5 transition-transform group-open:rotate-180" />
                View SQL
              </summary>
              <div className="mt-2 bg-slate-900 rounded-xl p-4 overflow-x-auto">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-slate-500 uppercase tracking-widest">DuckDB</span>
                  <CopyButton text={ans.sql} />
                </div>
                <pre className="text-sm text-emerald-400 font-mono whitespace-pre leading-relaxed">{ans.sql}</pre>
              </div>
            </details>
          )}

          {/* Follow-up chips */}
          {ans.follow_ups.length > 0 && (
            <div className="pt-1">
              <p className="text-[11px] text-slate-400 mb-1.5">You might also ask:</p>
              <div className="flex flex-wrap gap-2">
                {ans.follow_ups.map((fq, fi) => (
                  <button
                    key={fi}
                    onClick={() => onFollowUp(fq)}
                    disabled={isPending}
                    className="text-xs px-3 py-1.5 bg-white border border-slate-200 text-slate-600 rounded-full hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 disabled:opacity-40 transition-colors text-left leading-snug"
                  >
                    {fq}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── ThinkingBubble ────────────────────────────────────────────────────────────

function ThinkingBubble({ question }: { question: string }) {
  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-blue-700 text-white text-sm rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
          {question}
        </div>
      </div>
      <div className="flex justify-start">
        <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-violet-400 animate-pulse flex-shrink-0" />
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Segment AI</p>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400 text-sm">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }} />
            <span className="ml-1 text-xs">Generating SQL and analyzing data…</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function BankingAskGenie() {
  const API_BASE = getBankingApiBase();
  const [question, setQuestion] = React.useState('');

  // Persist history across tab switches via sessionStorage
  const [history, setHistory] = React.useState<HistoryItem[]>(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw) as HistoryItem[];
    } catch { /* ignore */ }
    return [];
  });

  const bottomRef = React.useRef<HTMLDivElement>(null);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  // Save history whenever it changes
  React.useEffect(() => {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history)); } catch { /* ignore */ }
  }, [history]);

  const chatEntries = history.filter((h): h is ChatEntry => !('type' in h));

  // Build conversation history for the API (last 10 exchanges)
  const buildApiHistory = () =>
    chatEntries.slice(-10).flatMap(e => [
      { role: 'user', content: e.question },
      { role: 'assistant', content: e.answer.narrative || '' },
    ]);

  const askMutation = useMutation({
    mutationFn: async (q: string) => {
      const res = await fetch(`${API_BASE}/api/banking/chat/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, history: buildApiHistory() }),
      });
      const data = await res.json();
      if (!res.ok) {
        const d = data?.detail;
        const msg = typeof d === 'string' ? d : JSON.stringify(d);
        throw new Error(msg || 'Request failed');
      }
      return data as ChatResponse;
    },
    onSuccess: (data, q) => {
      setHistory(prev => [...prev, { question: q, answer: data }]);
      setQuestion('');
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    },
  });

  const sendQuestion = React.useCallback((q: string) => {
    const trimmed = q.trim();
    if (!trimmed || askMutation.isPending) return;
    setQuestion(trimmed);
    askMutation.mutate(trimmed);
  }, [askMutation]);

  const startNewChat = React.useCallback(() => {
    setHistory(prev =>
      prev.length > 0 ? [...prev, { type: 'break' }] : prev
    );
  }, []);

  const clearChat = React.useCallback(() => {
    setHistory([]);
    try { sessionStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
  }, []);

  // Auto-grow textarea
  const growTextarea = React.useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 140) + 'px';
  }, []);

  return (
    <div className="space-y-5 animate-fadeIn">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-semibold text-gray-900">Segment AI</h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-violet-50 border border-violet-200 text-[11px] font-medium text-violet-600">
              <Database className="w-3 h-3" />
              10 tables
            </span>
          </div>
          <p className="text-gray-500 text-sm">
            Ask anything about your customers, segments, products, and marketing.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {chatEntries.length > 0 && (
            <>
              <button
                type="button"
                onClick={startNewChat}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-50 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                New Chat
              </button>
              <button
                type="button"
                onClick={clearChat}
                title="Clear all history"
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-red-200 text-red-600 text-sm font-medium hover:bg-red-50 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Clear
              </button>
            </>
          )}
        </div>
      </div>

      {/* Suggested questions — only shown when empty */}
      {history.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-violet-500" />
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Try asking</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {SUGGESTED_QUESTIONS.map((q, i) => (
              <button
                key={i}
                type="button"
                onClick={() => sendQuestion(q)}
                disabled={askMutation.isPending}
                className="text-left text-sm px-4 py-3 bg-slate-50 border border-slate-200 text-slate-700 rounded-xl hover:bg-blue-50 hover:border-blue-200 hover:text-blue-800 disabled:opacity-40 transition-all leading-snug group"
              >
                <span className="text-blue-400 mr-1.5 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                {q}
              </button>
            ))}
          </div>
          <p className="text-[11px] text-slate-400 mt-4 text-center">
            Powered by DuckDB · customers · transactions · ad_spend · impressions · wishlist · and 5 more tables
          </p>
        </div>
      )}

      {/* Chat history */}
      {history.map((item, idx) => {
        if ('type' in item) {
          return (
            <div key={idx} className="flex items-center gap-3 py-1">
              <div className="flex-1 h-px bg-slate-200" />
              <span className="text-xs text-slate-400 font-medium whitespace-nowrap">New conversation</span>
              <div className="flex-1 h-px bg-slate-200" />
            </div>
          );
        }
        return (
          <ChatMessage
            key={idx}
            entry={item as ChatEntry}
            onFollowUp={sendQuestion}
            isPending={askMutation.isPending}
          />
        );
      })}

      {/* Thinking bubble */}
      {askMutation.isPending && <ThinkingBubble question={question} />}

      {/* Network error */}
      {askMutation.isError && (
        <div className="text-sm rounded-xl p-4 border border-red-200 bg-red-50 text-red-800 flex items-center gap-3">
          <X className="w-4 h-4 flex-shrink-0" />
          <span>{(askMutation.error as Error)?.message}</span>
        </div>
      )}

      {/* Scroll anchor */}
      <div ref={bottomRef} />

      {/* Input area */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-md p-3 sticky bottom-4 z-10">
        {chatEntries.length > 0 && (
          <div className="flex items-center gap-1.5 px-1 pb-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <p className="text-[11px] text-slate-400">
              Context active — ask follow-ups like "show as line chart" or "filter to High churn only"
            </p>
          </div>
        )}
        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={question}
            onChange={(e) => { setQuestion(e.target.value); growTextarea(); }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                if (question.trim() && !askMutation.isPending) {
                  e.preventDefault();
                  sendQuestion(question.trim());
                  setTimeout(() => { if (textareaRef.current) { textareaRef.current.style.height = 'auto'; } }, 50);
                }
              }
            }}
            rows={1}
            style={{ minHeight: '40px', maxHeight: '140px', overflowY: 'auto' }}
            className="flex-1 border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none bg-slate-50 placeholder:text-slate-400 leading-snug"
            placeholder={
              chatEntries.length === 0
                ? 'Ask about your customers, segments, products, or marketing…'
                : 'Ask a follow-up or a new question…'
            }
          />
          <button
            type="button"
            disabled={askMutation.isPending || !question.trim()}
            onClick={() => {
              sendQuestion(question.trim());
              setTimeout(() => { if (textareaRef.current) { textareaRef.current.style.height = 'auto'; } }, 50);
            }}
            className="p-2.5 rounded-xl bg-blue-700 text-white hover:bg-blue-800 disabled:opacity-40 transition-colors flex-shrink-0"
            title="Send (Enter)"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[11px] text-slate-400 mt-1.5 px-1">Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}

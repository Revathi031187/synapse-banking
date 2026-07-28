import React from 'react';
import ReactDOM from 'react-dom';
import { useMutation } from '@tanstack/react-query';
import {
  BarChart2, Table2, X, Send, ChevronDown, Plus, Sparkles,
  Download, Copy, Check, TrendingUp, PieChart as PieIcon, Activity,
  Trash2, Database, AlertTriangle, TrendingDown, Minus, Bot,
  FileText, Zap, Package, Maximize2, Minimize2,
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { getBankingApiBase } from '../utils/apiBase';

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
  personas_registered?: boolean;
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

interface AnomalyResult {
  id: string;
  title: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  columns: string[];
  rows: (string | number)[][];
  count: number;
  error?: string;
}

interface ProductPulseMonth { month: string; customers: number; volume: number; }
interface ProductPulseItem {
  product_name: string;
  subcategory: string;
  new_customers: number;
  this_month_volume: number;
  this_month_customers: number;
  kpi_month_label?: string;
  last_month_partial?: boolean;
  momentum: 'Growing' | 'Stable' | 'Declining';
  pct_change: number | null;
  months: ProductPulseMonth[];
}

interface TrendMonth { month: string; value: number; }
interface TrendResult {
  id: string;
  title: string;
  unit: string;
  months: TrendMonth[];
  latest_value: number;
  prev_value: number | null;
  pct_change: number | null;
  direction: 'up' | 'down' | 'flat';
  last_month_partial?: boolean;
  error?: string;
}

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
  { q: "Which customer segment has the highest churn risk?",              category: "Segments",    color: "violet"  },
  { q: "Who are the top 10 most valuable customers by CLV?",             category: "CLV",          color: "blue"    },
  { q: "What is the ROAS by marketing channel and persona?",             category: "Marketing",    color: "emerald" },
  { q: "Which customers started an application but never completed it?", category: "Retention",    color: "amber"   },
  { q: "What are the key characteristics of each customer segment?",     category: "Segments",     color: "violet"  },
  { q: "What products are customers wishlisting but not applying for?",  category: "Products",     color: "indigo"  },
  { q: "Which customer segment generates the highest transaction volume?", category: "Transactions", color: "sky"   },
  { q: "Show monthly marketing spend trend across all channels",         category: "Marketing",    color: "emerald" },
];

const QUESTION_COLORS: Record<string, {
  accent: string; chipBg: string; chipText: string; chipBorder: string;
  iconBg: string; iconText: string; hoverBorder: string; hoverBg: string;
}> = {
  violet:  { accent: '#8B5CF6', chipBg: 'bg-violet-50',  chipText: 'text-violet-700',  chipBorder: 'border-violet-200',  iconBg: 'bg-violet-100',  iconText: 'text-violet-600',  hoverBorder: 'hover:border-violet-300',  hoverBg: 'hover:bg-violet-50/40'  },
  blue:    { accent: '#3B82F6', chipBg: 'bg-blue-50',    chipText: 'text-blue-700',    chipBorder: 'border-blue-200',    iconBg: 'bg-blue-100',    iconText: 'text-blue-600',    hoverBorder: 'hover:border-blue-300',    hoverBg: 'hover:bg-blue-50/40'    },
  emerald: { accent: '#10B981', chipBg: 'bg-emerald-50', chipText: 'text-emerald-700', chipBorder: 'border-emerald-200', iconBg: 'bg-emerald-100', iconText: 'text-emerald-600', hoverBorder: 'hover:border-emerald-300', hoverBg: 'hover:bg-emerald-50/40' },
  amber:   { accent: '#F59E0B', chipBg: 'bg-amber-50',   chipText: 'text-amber-700',   chipBorder: 'border-amber-200',   iconBg: 'bg-amber-100',   iconText: 'text-amber-600',   hoverBorder: 'hover:border-amber-300',   hoverBg: 'hover:bg-amber-50/40'   },
  indigo:  { accent: '#6366F1', chipBg: 'bg-indigo-50',  chipText: 'text-indigo-700',  chipBorder: 'border-indigo-200',  iconBg: 'bg-indigo-100',  iconText: 'text-indigo-600',  hoverBorder: 'hover:border-indigo-300',  hoverBg: 'hover:bg-indigo-50/40'  },
  sky:     { accent: '#0EA5E9', chipBg: 'bg-sky-50',     chipText: 'text-sky-700',     chipBorder: 'border-sky-200',     iconBg: 'bg-sky-100',     iconText: 'text-sky-600',     hoverBorder: 'hover:border-sky-300',     hoverBg: 'hover:bg-sky-50/40'     },
};

const STORAGE_KEY = 'segment_ai_panel_history_v1';

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

function fmtCellNum(n: number): string {
  if (!isFinite(n)) return '—';
  const abs = Math.abs(n);
  if (n === Math.round(n) && n >= 2000 && n <= 2040) return String(n);
  if (abs >= 1_000_000_000) return (n / 1_000_000_000).toFixed(2) + 'B';
  if (abs >= 1_000_000)     return (n / 1_000_000).toFixed(2) + 'M';
  if (abs >= 1_000)         return (n / 1_000).toFixed(1) + 'K';
  if (Math.round(n) !== n)  return n.toFixed(2);
  return String(n);
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
  const processed = React.useMemo(() => {
    let t = text;
    t = t.replace(/\\n/g, '\n');
    t = t.replace(/\\ *\n/g, '\n');
    t = t.replace(/\\$/gm, '');
    t = t.replace(/([.!?;:]) ([*-] (?=[A-Z*`\d]))/g, '$1\n$2');
    t = t.replace(/([^\n]) (## )/g, '$1\n$2');
    t = t.replace(/([^\n]) (### )/g, '$1\n$2');
    t = t.replace(/([.!?]) (\*\*Recommendation)/g, '$1\n\n$2');
    return t;
  }, [text]);

  const lines = processed.split('\n');
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
    const isBullet = line.startsWith('- ') || line.startsWith('• ') || line.startsWith('* ');
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

  const allData = React.useMemo(() => {
    const raw = table.rows
      .map(r => ({ x: String(r[xi] ?? ''), y: parseFloat(String(r[yi] ?? '0')) || 0 }))
      .filter(d => d.x !== '' && !isNaN(d.y));

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
    if (allData.length <= LINE_LIMIT) return { chartData: allData, truncatedFrom: 0 };
    return { chartData: allData.slice(0, LINE_LIMIT), truncatedFrom: allData.length };
  }, [allData, activeType]);

  const maxLabelLen = Math.max(...chartData.map(d => String(d.x).length), 0);
  const tickAngle = maxLabelLen > 12 ? -55 : (chartData.length > 6 ? -40 : 0);
  const bottomMargin = maxLabelLen > 20 ? 130 : maxLabelLen > 12 ? 90 : 35;
  const chartHeight = maxLabelLen > 20 ? 360 : 300;
  const margin = { top: 10, right: 20, left: 10, bottom: bottomMargin };

  const typeButtons: Array<'bar' | 'line' | 'area' | 'pie'> = ['bar', 'line', 'area', 'pie'];

  const tooltipStyle = { fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' };
  const tickStyle = { fontSize: 11, fill: '#64748b' };

  const truncLabel = (s: string) => s.length > 22 ? s.slice(0, 20) + '…' : s;

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
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
        <ResponsiveContainer width="100%" height={chartHeight}>
          {activeType === 'bar' ? (
            <BarChart data={chartData} margin={margin}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="x" tick={{ ...tickStyle, fontSize: chartData.length > 8 ? 10 : 11 }}
                angle={tickAngle} textAnchor={tickAngle ? 'end' : 'middle'} interval={0} />
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
                angle={tickAngle} textAnchor={tickAngle ? 'end' : 'middle'} interval={0} />
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
                angle={tickAngle} textAnchor={tickAngle ? 'end' : 'middle'} interval={0} />
              <YAxis tick={tickStyle} tickFormatter={fmtNum} width={52} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v: number) => [fmtTooltip(v), config.y_col]} />
              <Area type="monotone" dataKey="y" name={config.y_col}
                stroke={PALETTE[0]} strokeWidth={2} fill="url(#areaGrad)"
                dot={false} activeDot={{ r: 4 }} />
            </AreaChart>
          ) : (
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

  const isNumericCol = React.useMemo(() =>
    table.columns.map((_, ci) => {
      const sample = table.rows.find(r => r[ci] !== '' && r[ci] !== null);
      return sample ? typeof sample[ci] === 'number' : false;
    }),
    [table]
  );

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

      <div className="relative">
        {canScrollLeft && (
          <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-8 z-20"
            style={{ background: 'linear-gradient(to right, rgba(241,245,249,0.95), transparent)' }} />
        )}
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
                    className={`px-3 py-2 text-xs font-bold text-slate-600 uppercase tracking-wide border-b border-slate-200 whitespace-nowrap cursor-pointer hover:bg-slate-200 select-none ${isNumericCol[ci] ? 'text-right' : 'text-left'}`}
                  >
                    <span className={`flex items-center gap-1 ${isNumericCol[ci] ? 'justify-end' : ''}`}>
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
                    <td key={ci} className={`px-3 py-2 text-slate-700 border-b border-slate-100 whitespace-nowrap text-xs font-variant-numeric tabular-nums ${isNumericCol[ci] ? 'text-right' : ''}`}>
                      {isNumericCol[ci] && typeof cell === 'number' ? fmtCellNum(cell) : String(cell)}
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

// ── Export Report ─────────────────────────────────────────────────────────────

function exportReport(entry: ChatEntry) {
  const { question, answer: ans } = entry;

  const fmtN = (v: number) => {
    if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(1) + 'B';
    if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(1) + 'M';
    if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(1) + 'K';
    return v.toLocaleString();
  };

  const tableHtml = ans.table
    ? `<table>
        <thead><tr>${ans.table.columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
        <tbody>${ans.table.rows.map(row =>
          `<tr>${row.map(cell => `<td>${typeof cell === 'number' ? fmtN(cell) : cell}</td>`).join('')}</tr>`
        ).join('')}</tbody>
      </table>`
    : '';

  const narrative = (ans.narrative || '')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>');

  const html = `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Segment AI Report — ${question}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 860px; margin: 40px auto; color: #1e293b; padding: 0 24px; }
  .logo { font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: #7c3aed; text-transform: uppercase; margin-bottom: 4px; }
  .question { background: #1d4ed8; color: white; border-radius: 12px; padding: 12px 18px; font-size: 15px; display: inline-block; margin-bottom: 20px; }
  .narrative { background: #faf5ff; border-left: 3px solid #8b5cf6; border-radius: 8px; padding: 16px 20px; font-size: 14px; line-height: 1.7; margin-bottom: 20px; }
  .narrative li { margin: 4px 0; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
  th { background: #0f172a; color: white; padding: 8px 12px; text-align: left; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; }
  td { padding: 7px 12px; border-bottom: 1px solid #e2e8f0; }
  tr:nth-child(even) td { background: #f8fafc; }
  .footer { margin-top: 32px; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 12px; }
  h3 { font-size: 14px; font-weight: 700; color: #1e293b; margin: 16px 0 6px; }
  @media print { body { margin: 20px; } }
</style>
</head><body>
<div class="logo">Meridian Bank · Segment AI Report</div>
<div class="question">${question}</div>
<div class="narrative">${narrative}</div>
${tableHtml ? `<div><strong style="font-size:12px;color:#475569;">Data Table</strong>${tableHtml}</div>` : ''}
<div class="footer">Generated by Segment AI · Meridian Bank Data Platform · ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
</body></html>`;

  const win = window.open('', '_blank');
  if (!win) return;
  win.document.write(html);
  win.document.close();
  setTimeout(() => win.print(), 400);
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
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-blue-700 text-white text-sm rounded-2xl rounded-tr-sm px-4 py-3 leading-relaxed shadow-sm">
          {entry.question}
        </div>
      </div>

      <div className="flex justify-start">
        <div className="max-w-[92%] w-full space-y-3">

          {!ans.success && ans.error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl rounded-tl-sm px-4 py-3">
              <p className="text-[11px] font-bold text-red-400 uppercase tracking-widest mb-1">Error</p>
              <p className="text-sm text-red-800">{ans.error}</p>
            </div>
          )}

          {ans.narrative && (
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3.5 shadow-sm"
              style={{ borderLeft: '3px solid #8B5CF6' }}>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-3.5 h-3.5 text-violet-500 flex-shrink-0" />
                <p className="text-[11px] font-bold text-violet-500 uppercase tracking-widest">Segment AI</p>
              </div>
              <NarrativeMarkdown text={ans.narrative} />
              {/* Only show sql_error note when real data also exists (partial warning).
                  When the query fully failed, the narrative already contains the error. */}
              {ans.sql_error && (hasTable || hasChart) && (
                <p className="mt-2 text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                  Note: {ans.sql_error}
                </p>
              )}
              {ans.table && (
                <p className="mt-2.5 text-[10.5px] text-slate-400 flex items-center gap-1.5">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                  AI-generated summary — verify values in the table below.
                </p>
              )}
            </div>
          )}

          {(hasTable || hasChart) && (
            <div className="space-y-2">
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

              {hasChart && (activeView === 'chart' || !hasTable) && (
                <ResultChart table={ans.table!} config={ans.chart!} />
              )}

              {hasTable && (activeView === 'table' || !hasChart) && (
                <ResultTable table={ans.table!} title={ans.chart?.title || entry.question} />
              )}
            </div>
          )}

          <div className="flex items-center justify-between pt-1">
            <button
              type="button"
              onClick={() => exportReport(entry)}
              className="inline-flex items-center gap-1.5 text-slate-400 hover:text-violet-600 text-xs font-medium transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              Export Report
            </button>

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
          </div>

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
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Agent A Banner ─────────────────────────────────────────────────────────────

function AgentABanner({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
      <Bot className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-amber-800">Agent A not yet run</p>
        <p className="text-xs text-amber-700 mt-0.5 leading-snug">
          AI-refined personas unavailable. Segment questions answer using the <strong>5 Meridian Bank segments</strong> (Retiree Depositor, Wealth Accumulator, Everyday Essential, Digital Trendsetter, At-Risk Saver). Run Agent A for deeper AI-driven segmentation.
        </p>
      </div>
      <button onClick={onDismiss} className="text-amber-400 hover:text-amber-600 flex-shrink-0">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

// ── Anomalies Panel ───────────────────────────────────────────────────────────

const ANOMALY_META: Record<string, {
  whatItMeans: string;
  colDefs: Record<string, string>;
  actionHint: string;
}> = {
  high_value_churn: {
    whatItMeans: "These are your highest-value customers (Gold / Platinum CLV tier) who are statistically likely to close accounts or stop transacting within 90 days. Each lost Platinum customer can represent thousands in lifetime revenue.",
    colDefs: {
      clv:        "Customer Lifetime Value — total expected revenue over this customer's entire relationship with Meridian Bank.",
      churn_prob: "Probability (0–1) the customer will disengage within 90 days. Above 0.6 is considered high-risk.",
      clv_tier:   "CLV segment bucket: Platinum > Gold > Silver > Bronze.",
      income:     "Annual gross income — used to gauge the financial impact of losing this customer.",
    },
    actionHint: "Prioritise personal outreach from relationship managers — especially for Platinum-tier customers.",
  },
  wishlist_gap: {
    whatItMeans: "Products that many customers expressed interest in (wishlist) but rarely converted to purchase. A large gap between wishlisters and buyers usually signals a pricing, eligibility, or awareness barrier.",
    colDefs: {
      wishlisted_by:      "Number of distinct customers who added this product to their wishlist.",
      actually_purchased: "Number of distinct customers who completed at least one transaction for this product.",
      conversion_pct:     "Buyers ÷ Wishlisters × 100. Below 50 % flags a conversion barrier worth investigating.",
    },
    actionHint: "Run a targeted offer or rate promotion for the top-wishlisted products with the lowest conversion.",
  },
  txn_volume_spike: {
    whatItMeans: "Customers whose transaction count is significantly above the typical customer. Could indicate high engagement (power users) or irregular activity worth a compliance review.",
    colDefs: {
      txn_count:            "Total number of transactions recorded for this customer across all products.",
      avg_count:            "Average transaction count across all customers — the baseline being compared against.",
      z_score:              "Standard deviations above the mean transaction count. A z-score above 2 is a statistical outlier.",
      clv_tier:             "CLV segment: Platinum > Gold > Silver > Bronze. Helps distinguish power users from low-value outliers.",
      churn_risk_category:  "Model-assigned churn risk label (High / Medium / Low) — high-volume + high-churn is the most urgent combination.",
    },
    actionHint: "Review high z-score customers for both upsell opportunity (engaged users) and unusual patterns.",
  },
  abandoned_applications: {
    whatItMeans: "Products where customers started an application but never completed it. High abandonment signals friction in the onboarding flow, unclear eligibility requirements, or a drop-off point in the application UI.",
    colDefs: {
      abandoned_count: "Total incomplete application records for this product.",
      pct_of_total:    "This product's share of all abandoned applications site-wide. Higher % means fixing this product will have the biggest impact.",
    },
    actionHint: "Send an 'application recovery' nudge (email or push) to customers with incomplete applications for these products.",
  },
  roas_outliers: {
    whatItMeans: "Channel-persona pairs whose Return on Ad Spend (ROAS) is unusually high or low compared to the overall average. Positive outliers reveal your best-performing marketing mix; negative outliers highlight budget waste.",
    colDefs: {
      roas:        "Return on Ad Spend = Revenue ÷ Ad Spend. A ROAS of 3.5 means $3.50 earned for every $1 spent.",
      total_spend: "Total marketing dollars spent on this channel-persona combination — context for how meaningful the ROAS figure is.",
      z_score:     "Standard deviations from the mean ROAS across all channel-persona pairs. z > 1.5 = significantly above average (great); z < −1.5 = significantly below average (review or cut).",
    },
    actionHint: "Shift budget toward high-ROAS pairs and pause or renegotiate low-ROAS channels.",
  },
};

const SEVERITY_STYLE: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  critical: { bg: 'bg-red-50',    text: 'text-red-700',    border: 'border-red-200',    dot: 'bg-red-500' },
  warning:  { bg: 'bg-amber-50',  text: 'text-amber-700',  border: 'border-amber-200',  dot: 'bg-amber-500' },
  info:     { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200',   dot: 'bg-blue-400' },
};

function AnomaliesPanel({ anomalies, onClose }: { anomalies: AnomalyResult[]; onClose: () => void }) {
  const [active, setActive] = React.useState(anomalies[0]?.id ?? '');
  const current = anomalies.find(a => a.id === active);

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-white shadow-2xl border-l border-slate-200 flex flex-col z-50">
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <h2 className="font-semibold text-slate-900 text-sm">Anomaly Detection</h2>
          <span className="text-[11px] bg-red-100 text-red-700 font-semibold px-2 py-0.5 rounded-full">
            {anomalies.filter(a => a.count > 0).length} active
          </span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-4 h-4" /></button>
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="w-52 flex-shrink-0 border-r border-slate-100 overflow-y-auto bg-slate-50 py-2">
          {anomalies.map(a => {
            const s = SEVERITY_STYLE[a.severity];
            return (
              <button key={a.id} onClick={() => setActive(a.id)}
                className={`w-full text-left px-4 py-3 transition-colors text-xs ${active === a.id ? 'bg-white border-r-2 border-violet-500 font-semibold text-slate-900' : 'text-slate-600 hover:bg-white'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${s.dot}`} />
                  <span className="font-medium leading-snug">{a.title}</span>
                </div>
                <span className={`ml-4 text-[11px] font-semibold ${s.text}`}>{a.count} found</span>
              </button>
            );
          })}
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {current && (() => {
            const meta = ANOMALY_META[current.id];
            return (
              <>
                <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold mb-3 border ${SEVERITY_STYLE[current.severity].bg} ${SEVERITY_STYLE[current.severity].text} ${SEVERITY_STYLE[current.severity].border}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${SEVERITY_STYLE[current.severity].dot}`} />
                  {current.severity.toUpperCase()}
                </div>
                <h3 className="font-semibold text-slate-900 text-sm mb-1">{current.title}</h3>
                <p className="text-xs text-slate-500 mb-3">{current.description}</p>

                {meta && (
                  <div className="bg-blue-50 border border-blue-200 rounded-xl px-3 py-2.5 mb-4">
                    <p className="text-[11px] font-semibold text-blue-700 uppercase tracking-wide mb-1">What this means</p>
                    <p className="text-xs text-blue-900 leading-relaxed">{meta.whatItMeans}</p>
                  </div>
                )}

                {current.error && (
                  <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">{current.error}</p>
                )}

                {current.count === 0 && !current.error && (
                  <div className="text-center py-8 text-slate-400 text-sm">No anomalies detected ✓</div>
                )}

                {current.columns.length > 0 && current.rows.length > 0 && (
                  <>
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="w-full text-xs">
                        <thead className="bg-slate-900 text-white">
                          <tr>{current.columns.map(c => {
                            const def = meta?.colDefs?.[c];
                            return (
                              <th key={c} title={def ?? undefined}
                                className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-[10px] cursor-help">
                                {c}{def && <span className="ml-1 opacity-60">ⓘ</span>}
                              </th>
                            );
                          })}</tr>
                        </thead>
                        <tbody>
                          {current.rows.map((row, ri) => (
                            <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                              {row.map((cell, ci) => (
                                <td key={ci} className="px-3 py-2 text-slate-700">
                                  {typeof cell === 'number' ? cell.toLocaleString() : String(cell ?? '')}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {meta && Object.keys(meta.colDefs).some(k => current.columns.includes(k)) && (
                      <div className="mt-3 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 space-y-1">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Column definitions</p>
                        {current.columns.filter(c => meta.colDefs[c]).map(c => (
                          <div key={c} className="flex gap-2 text-[11px]">
                            <span className="font-semibold text-slate-600 shrink-0 uppercase">{c}</span>
                            <span className="text-slate-500">{meta.colDefs[c]}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {meta?.actionHint && (
                      <div className="mt-3 flex items-start gap-2 bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2.5">
                        <Zap className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                        <p className="text-[11px] text-emerald-800 leading-relaxed"><span className="font-semibold">Suggested action: </span>{meta.actionHint}</p>
                      </div>
                    )}
                  </>
                )}
              </>
            );
          })()}
        </div>
      </div>
    </div>
  );
}

// ── Trends Panel ──────────────────────────────────────────────────────────────

function fmtTrendVal(v: number, unit: string) {
  const abs = Math.abs(v);
  const n = abs >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : abs >= 1e3 ? (v / 1e3).toFixed(1) + 'K' : v.toLocaleString();
  return unit === '$' ? '$' + n : n;
}

function TrendSparkline({ months }: { months: TrendMonth[] }) {
  if (months.length < 2) return null;
  const vals = months.map(m => m.value);
  const max = Math.max(...vals);
  const min = Math.min(...vals);
  const range = max - min || 1;
  const W = 80; const H = 28;
  const pts = vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * W;
    const y = H - ((v - min) / range) * H;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={W} height={H} className="overflow-visible">
      <polyline points={pts} fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinejoin="round" />
      <circle cx={parseFloat(pts.split(' ').pop()!.split(',')[0])} cy={parseFloat(pts.split(' ').pop()!.split(',')[1])} r="2.5" fill="#8b5cf6" />
    </svg>
  );
}

function TrendsPanel({ trends, onClose }: { trends: TrendResult[]; onClose: () => void }) {
  const [active, setActive] = React.useState(trends[0]?.id ?? '');
  const current = trends.find(t => t.id === active);

  const DirIcon = ({ dir }: { dir: string }) => {
    if (dir === 'up')   return <TrendingUp className="w-4 h-4 text-emerald-500" />;
    if (dir === 'down') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-white shadow-2xl border-l border-slate-200 flex flex-col z-50">
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-violet-500" />
          <h2 className="font-semibold text-slate-900 text-sm">Month-over-Month Trends</h2>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-4 h-4" /></button>
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="w-52 flex-shrink-0 border-r border-slate-100 overflow-y-auto bg-slate-50 py-2">
          {trends.map(t => (
            <button key={t.id} onClick={() => setActive(t.id)}
              className={`w-full text-left px-4 py-3 transition-colors ${active === t.id ? 'bg-white border-r-2 border-violet-500' : 'hover:bg-white'}`}>
              <p className={`text-xs font-medium mb-1 ${active === t.id ? 'text-slate-900' : 'text-slate-600'}`}>{t.title}</p>
              <div className="flex items-center gap-1.5">
                <DirIcon dir={t.direction} />
                <span className={`text-[11px] font-semibold ${t.direction === 'up' ? 'text-emerald-600' : t.direction === 'down' ? 'text-red-600' : 'text-slate-500'}`}>
                  {t.pct_change !== null ? `${t.pct_change > 0 ? '+' : ''}${t.pct_change}%` : 'N/A'}
                </span>
              </div>
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {current && (
            <>
              <h3 className="font-semibold text-slate-900 text-sm mb-1">{current.title}</h3>
              <div className="flex items-center gap-4 mb-6">
                <div>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wide">Latest</p>
                  <p className="text-2xl font-bold text-slate-900">{fmtTrendVal(current.latest_value, current.unit)}</p>
                </div>
                {current.prev_value !== null && (
                  <div>
                    <p className="text-[11px] text-slate-400 uppercase tracking-wide">vs Prior Month</p>
                    <div className="flex items-center gap-1">
                      {current.direction === 'up'   && <TrendingUp className="w-4 h-4 text-emerald-500" />}
                      {current.direction === 'down'  && <TrendingDown className="w-4 h-4 text-red-500" />}
                      {current.direction === 'flat'  && <Minus className="w-4 h-4 text-slate-400" />}
                      <span className={`text-lg font-bold ${current.direction === 'up' ? 'text-emerald-600' : current.direction === 'down' ? 'text-red-600' : 'text-slate-500'}`}>
                        {current.pct_change !== null ? `${current.pct_change > 0 ? '+' : ''}${current.pct_change}%` : '—'}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {current.error && (
                <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-4">{current.error}</p>
              )}

              {current.last_month_partial && (
                <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2.5 mb-4">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-[11px] text-amber-800 leading-relaxed">
                    <span className="font-semibold">Last month is partial.</span> The most recent month in the chart contains only part of the month's data — transactions are still being recorded. The MoM % shown above compares the two most recent <em>complete</em> months, so the trend direction is reliable. The last bar may appear lower than expected simply because the month isn't finished yet.
                  </p>
                </div>
              )}

              {current.months.length > 0 ? (
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={current.months} margin={{ top: 4, right: 8, left: 0, bottom: 20 }}>
                      <defs>
                        <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.15} />
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="month" tick={{ fontSize: 9, angle: -35, textAnchor: 'end', dy: 6 }} tickLine={false} interval={0} />
                      <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false}
                        tickFormatter={v => current.unit === '$' ? '$' + (v >= 1e6 ? (v/1e6).toFixed(1)+'M' : v >= 1e3 ? (v/1e3).toFixed(0)+'K' : v) : v >= 1e3 ? (v/1e3).toFixed(0)+'K' : String(v)} />
                      <Tooltip formatter={(v: number) => [fmtTrendVal(v, current.unit), current.title]} />
                      <Area type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} fill="url(#trendGrad)" dot={{ r: 3, fill: '#8b5cf6' }} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400 text-sm">No data available for this period</div>
              )}

              {current.months.length > 0 && (
                <div className="mt-5 overflow-x-auto rounded-xl border border-slate-200">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-900 text-white">
                      <tr>
                        <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-[10px]">Month</th>
                        <th className="px-3 py-2 text-right font-semibold uppercase tracking-wide text-[10px]">Value</th>
                        <th className="px-3 py-2 text-right font-semibold uppercase tracking-wide text-[10px]">MoM Change</th>
                      </tr>
                    </thead>
                    <tbody>
                      {current.months.map((m, i) => {
                        const isLastPartial = current.last_month_partial && i === current.months.length - 1;
                        const prev = current.months[i - 1]?.value;
                        const chg = (!isLastPartial && prev) ? ((m.value - prev) / Math.abs(prev) * 100) : null;
                        return (
                          <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                            <td className="px-3 py-2 text-slate-700 font-medium">
                              <div className="flex items-center gap-1.5">
                                {m.month}
                                {isLastPartial && <span className="text-[9px] bg-amber-100 text-amber-700 font-semibold px-1.5 py-0.5 rounded-full">partial</span>}
                              </div>
                            </td>
                            <td className="px-3 py-2 text-slate-900 text-right font-semibold">{fmtTrendVal(m.value, current.unit)}</td>
                            <td className={`px-3 py-2 text-right font-semibold ${isLastPartial ? 'text-amber-500 italic text-[10px]' : chg === null ? 'text-slate-400' : chg > 0 ? 'text-emerald-600' : chg < 0 ? 'text-red-600' : 'text-slate-400'}`}>
                              {isLastPartial ? 'in progress' : chg === null ? '—' : `${chg > 0 ? '+' : ''}${chg.toFixed(1)}%`}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Product Pulse Panel ───────────────────────────────────────────────────────

const MOMENTUM_STYLE = {
  Growing:   { bg: 'bg-emerald-100', text: 'text-emerald-700', dot: 'bg-emerald-500', bar: '#10b981' },
  Stable:    { bg: 'bg-slate-100',   text: 'text-slate-600',   dot: 'bg-slate-400',   bar: '#94a3b8' },
  Declining: { bg: 'bg-red-100',     text: 'text-red-700',     dot: 'bg-red-500',     bar: '#ef4444' },
};

function PulseSparkline({ months }: { months: { volume: number }[] }) {
  if (months.length < 2) return null;
  const vals = months.map(m => m.volume);
  const max = Math.max(...vals); const min = Math.min(...vals);
  const range = max - min || 1;
  const W = 72; const H = 24;
  const pts = vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * W;
    const y = H - ((v - min) / range) * H;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const lastPt = pts.split(' ').pop()!.split(',');
  return (
    <svg width={W} height={H} className="overflow-visible">
      <polyline points={pts} fill="none" stroke="#6366f1" strokeWidth="1.5" strokeLinejoin="round" />
      <circle cx={parseFloat(lastPt[0])} cy={parseFloat(lastPt[1])} r="2.5" fill="#6366f1" />
    </svg>
  );
}

function ProductPulsePanel({ products, onClose }: { products: ProductPulseItem[]; onClose: () => void }) {
  const [active, setActive] = React.useState(products[0]?.product_name ?? '');
  const [filter, setFilter] = React.useState<'All' | 'Growing' | 'Stable' | 'Declining'>('All');

  const visible = filter === 'All' ? products : products.filter(p => p.momentum === filter);
  const current = visible.find(p => p.product_name === active) ?? visible[0];

  const fmtVol = (v: number) => v >= 1e6 ? '$' + (v / 1e6).toFixed(1) + 'M'
                               : v >= 1e3 ? '$' + (v / 1e3).toFixed(0) + 'K'
                               : '$' + v.toFixed(0);

  const counts = {
    Growing:   products.filter(p => p.momentum === 'Growing').length,
    Stable:    products.filter(p => p.momentum === 'Stable').length,
    Declining: products.filter(p => p.momentum === 'Declining').length,
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-white shadow-2xl border-l border-slate-200 flex flex-col z-50">
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <Package className="w-4 h-4 text-teal-600" />
          <h2 className="font-semibold text-slate-900 text-sm">Product Pulse</h2>
          <div className="flex gap-1.5">
            {(['All', 'Growing', 'Stable', 'Declining'] as const).map(f => (
              <button key={f} onClick={() => { setFilter(f); }}
                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full transition-colors
                  ${filter === f
                    ? f === 'Growing' ? 'bg-emerald-500 text-white'
                      : f === 'Declining' ? 'bg-red-500 text-white'
                      : f === 'Stable' ? 'bg-slate-500 text-white'
                      : 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                {f}{f !== 'All' && ` (${counts[f]})`}
              </button>
            ))}
          </div>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-4 h-4" /></button>
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="w-56 flex-shrink-0 border-r border-slate-100 overflow-y-auto bg-slate-50 py-2">
          {visible.map(p => {
            const ms = MOMENTUM_STYLE[p.momentum];
            return (
              <button key={p.product_name} onClick={() => setActive(p.product_name)}
                className={`w-full text-left px-3 py-2.5 transition-colors ${active === p.product_name ? 'bg-white border-r-2 border-teal-500' : 'hover:bg-white'}`}>
                <div className="flex items-start justify-between gap-1 mb-1">
                  <p className={`text-[11px] font-semibold leading-snug ${active === p.product_name ? 'text-slate-900' : 'text-slate-700'}`}>
                    {p.product_name}
                  </p>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full shrink-0 ${ms.bg} ${ms.text}`}>
                    {p.momentum}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400">{p.subcategory}</span>
                  <PulseSparkline months={p.months} />
                </div>
              </button>
            );
          })}
          {visible.length === 0 && (
            <p className="text-center text-xs text-slate-400 py-8">No products match this filter</p>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {current && (() => {
            const ms = MOMENTUM_STYLE[current.momentum];
            return (
              <>
                <div className="flex items-start justify-between gap-2 mb-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">{current.product_name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{current.subcategory}</p>
                  </div>
                  <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full ${ms.bg} ${ms.text}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${ms.dot}`} />
                    {current.momentum}
                    {current.pct_change !== null && (
                      <span className="ml-0.5">({current.pct_change > 0 ? '+' : ''}{current.pct_change}%)</span>
                    )}
                  </span>
                </div>

                {current.last_month_partial && (
                  <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2.5 mb-4">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                    <p className="text-[11px] text-amber-800 leading-snug">
                      Latest month is incomplete — KPIs and momentum reflect{' '}
                      <strong>{current.kpi_month_label ?? 'last complete month'}</strong> instead.
                      The partial month is still shown in the chart.
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-3 mb-5">
                  {[
                    {
                      label: current.kpi_month_label ? `Volume (${current.kpi_month_label})` : 'Volume (Latest Month)',
                      value: fmtVol(current.this_month_volume),
                    },
                    { label: 'Active Customers', value: current.this_month_customers.toLocaleString() },
                    { label: 'New Customers', value: current.new_customers.toLocaleString() },
                  ].map(kpi => (
                    <div key={kpi.label} className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                      <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">{kpi.label}</p>
                      <p className="text-xl font-bold text-slate-900">{kpi.value}</p>
                    </div>
                  ))}
                </div>

                <div className={`flex items-start gap-2 rounded-xl px-3 py-2.5 mb-4 border ${
                  current.momentum === 'Growing' ? 'bg-emerald-50 border-emerald-200' :
                  current.momentum === 'Declining' ? 'bg-red-50 border-red-200' :
                  'bg-slate-50 border-slate-200'}`}>
                  <Activity className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${
                    current.momentum === 'Growing' ? 'text-emerald-600' :
                    current.momentum === 'Declining' ? 'text-red-600' : 'text-slate-500'}`} />
                  <p className={`text-[11px] leading-relaxed ${
                    current.momentum === 'Growing' ? 'text-emerald-800' :
                    current.momentum === 'Declining' ? 'text-red-800' : 'text-slate-600'}`}>
                    {current.momentum === 'Growing' && `Revenue grew ${current.pct_change !== null ? Math.abs(current.pct_change) + '% ' : ''}comparing the last 2 months to the prior 2 months. Consider featuring this product more prominently in Agent C offers.`}
                    {current.momentum === 'Declining' && `Revenue fell ${current.pct_change !== null ? Math.abs(current.pct_change) + '% ' : ''}comparing the last 2 months to the prior 2 months. Review pricing, eligibility criteria, or channel targeting for this product.`}
                    {current.momentum === 'Stable' && `Revenue is steady (within ±10% compared to the prior 2-month period). No immediate action required.`}
                  </p>
                </div>

                {current.months.length > 0 && (
                  <div className="h-44 mb-5">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={current.months} margin={{ top: 4, right: 8, left: 0, bottom: 20 }}>
                        <defs>
                          <linearGradient id="pulseGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={ms.bar} stopOpacity={0.18} />
                            <stop offset="95%" stopColor={ms.bar} stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="month" tick={{ fontSize: 9, angle: -35, textAnchor: 'end', dy: 6 }} tickLine={false} interval={0} />
                        <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false}
                          tickFormatter={v => v >= 1e6 ? '$' + (v/1e6).toFixed(1)+'M' : v >= 1e3 ? '$' + (v/1e3).toFixed(0)+'K' : '$'+v} />
                        <Tooltip formatter={(v: number) => [fmtVol(v), 'Volume']} />
                        <Area type="monotone" dataKey="volume" stroke={ms.bar} strokeWidth={2}
                          fill="url(#pulseGrad)" dot={{ r: 3, fill: ms.bar }} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {current.months.length > 0 && (
                  <div className="overflow-x-auto rounded-xl border border-slate-200">
                    <table className="w-full text-xs">
                      <thead className="bg-slate-900 text-white">
                        <tr>
                          <th className="px-3 py-2 text-left text-[10px] uppercase tracking-wide font-semibold">Month</th>
                          <th className="px-3 py-2 text-right text-[10px] uppercase tracking-wide font-semibold">Volume</th>
                          <th className="px-3 py-2 text-right text-[10px] uppercase tracking-wide font-semibold">Customers</th>
                          <th className="px-3 py-2 text-right text-[10px] uppercase tracking-wide font-semibold">MoM Δ</th>
                        </tr>
                      </thead>
                      <tbody>
                        {current.months.map((m, i) => {
                          const prevVol = current.months[i - 1]?.volume;
                          const chg = prevVol ? ((m.volume - prevVol) / Math.abs(prevVol) * 100) : null;
                          return (
                            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                              <td className="px-3 py-2 font-medium text-slate-700">{m.month}</td>
                              <td className="px-3 py-2 text-right font-semibold text-slate-900">{fmtVol(m.volume)}</td>
                              <td className="px-3 py-2 text-right text-slate-600">{m.customers.toLocaleString()}</td>
                              <td className={`px-3 py-2 text-right font-semibold ${chg === null ? 'text-slate-400' : chg > 0 ? 'text-emerald-600' : chg < 0 ? 'text-red-600' : 'text-slate-400'}`}>
                                {chg === null ? '—' : `${chg > 0 ? '+' : ''}${chg.toFixed(1)}%`}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      </div>
    </div>
  );
}

// ── Main SegmentAIPanel component ─────────────────────────────────────────────

export default function SegmentAIPanel() {
  const API_BASE = getBankingApiBase();
  const [question, setQuestion] = React.useState('');
  const [isFullscreen, setIsFullscreen] = React.useState(false);

  const [history, setHistory] = React.useState<HistoryItem[]>(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw) as HistoryItem[];
    } catch { /* ignore */ }
    return [];
  });

  const [personasRegistered, setPersonasRegistered] = React.useState<boolean | null>(null);
  const [bannerDismissed, setBannerDismissed] = React.useState(false);
  const [anomalies, setAnomalies] = React.useState<AnomalyResult[] | null>(null);
  const [anomaliesLoading, setAnomaliesLoading] = React.useState(false);
  const [showAnomalies, setShowAnomalies] = React.useState(false);
  const [trends, setTrends] = React.useState<TrendResult[] | null>(null);
  const [trendsLoading, setTrendsLoading] = React.useState(false);
  const [showTrends, setShowTrends] = React.useState(false);
  const [productPulse, setProductPulse] = React.useState<ProductPulseItem[] | null>(null);
  const [productPulseLoading, setProductPulseLoading] = React.useState(false);
  const [showProductPulse, setShowProductPulse] = React.useState(false);

  const bottomRef = React.useRef<HTMLDivElement>(null);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  React.useEffect(() => {
    if (personasRegistered) return;
    const check = () =>
      fetch(`${API_BASE}/api/banking/chat/status`)
        .then(r => r.json())
        .then(d => { if (d.personas_registered) setPersonasRegistered(true); })
        .catch(() => {});

    check();
    const id = setInterval(check, 15_000);
    return () => clearInterval(id);
  }, [API_BASE, personasRegistered]);

  const loadAnomalies = React.useCallback(async () => {
    if (anomaliesLoading) return;
    setAnomaliesLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/banking/chat/anomalies`);
      const d = await r.json();
      setAnomalies(d.anomalies ?? []);
      setShowAnomalies(true);
    } catch { /* ignore */ }
    finally { setAnomaliesLoading(false); }
  }, [API_BASE, anomaliesLoading]);

  const loadTrends = React.useCallback(async () => {
    if (trendsLoading) return;
    setTrendsLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/banking/chat/trends`);
      const d = await r.json();
      setTrends(d.trends ?? []);
      setShowTrends(true);
    } catch { /* ignore */ }
    finally { setTrendsLoading(false); }
  }, [API_BASE, trendsLoading]);

  const loadProductPulse = React.useCallback(async () => {
    if (productPulseLoading) return;
    setProductPulseLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/banking/chat/product-pulse`);
      const d = await r.json();
      setProductPulse(d.products ?? []);
      setShowProductPulse(true);
    } catch { /* ignore */ }
    finally { setProductPulseLoading(false); }
  }, [API_BASE, productPulseLoading]);


  React.useEffect(() => {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history)); } catch { /* ignore */ }
  }, [history]);

  const chatEntries = history.filter((h): h is ChatEntry => !('type' in h));

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
      if (data.personas_registered) setPersonasRegistered(true);
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

  const growTextarea = React.useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 140) + 'px';
  }, []);

  return (
    <>
      {showAnomalies && anomalies && ReactDOM.createPortal(
        <AnomaliesPanel anomalies={anomalies} onClose={() => setShowAnomalies(false)} />,
        document.body
      )}
      {showTrends && trends && ReactDOM.createPortal(
        <TrendsPanel trends={trends} onClose={() => setShowTrends(false)} />,
        document.body
      )}
      {showProductPulse && productPulse && ReactDOM.createPortal(
        <ProductPulsePanel products={productPulse} onClose={() => setShowProductPulse(false)} />,
        document.body
      )}

      <div className={`flex flex-col bg-white flex-shrink-0 ${isFullscreen ? 'fixed inset-0 z-50 w-full' : 'w-[340px] border-l border-gray-200'}`}>
        {/* ── Header row 1: title + expand ── */}
        <div className={`flex items-center gap-2 flex-shrink-0 border-b border-slate-100 ${isFullscreen ? 'px-6 py-4' : 'px-3 pt-2.5 pb-1'}`}>
          <div
            className={`rounded flex-shrink-0 flex items-center justify-center transition-all ${isFullscreen ? 'w-9 h-9 rounded-lg' : 'w-5 h-5'}`}
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
            <svg className={`text-white ${isFullscreen ? 'w-5 h-5' : 'w-3 h-3'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <p className={`font-bold text-slate-900 leading-none truncate ${isFullscreen ? 'text-xl' : 'text-[11.5px]'}`}>Segment AI</p>
            {isFullscreen && <p className="text-sm text-slate-400 mt-0.5">Natural language analytics for Meridian Bank</p>}
          </div>
          {chatEntries.length > 0 && (
            <>
              <button onClick={startNewChat} title="New Chat"
                className={`rounded hover:bg-slate-100 text-slate-400 transition-colors flex-shrink-0 ${isFullscreen ? 'p-2' : 'p-1'}`}>
                <Plus className={isFullscreen ? 'w-5 h-5' : 'w-3.5 h-3.5'} />
              </button>
              <button onClick={clearChat} title="Clear chat"
                className={`rounded hover:bg-red-50 text-red-400 transition-colors flex-shrink-0 ${isFullscreen ? 'p-2' : 'p-1'}`}>
                <Trash2 className={isFullscreen ? 'w-5 h-5' : 'w-3.5 h-3.5'} />
              </button>
            </>
          )}
          <button onClick={() => setIsFullscreen(f => !f)}
            className={`flex-shrink-0 inline-flex items-center gap-1.5 rounded border border-slate-200 text-slate-500 hover:bg-slate-100 transition-colors ${isFullscreen ? 'px-3 py-2 text-sm font-semibold' : 'px-2 py-1'}`}>
            {isFullscreen ? <Minimize2 className={isFullscreen ? 'w-4 h-4' : 'w-3 h-3'} /> : <Maximize2 className="w-3 h-3" />}
            <span className={isFullscreen ? 'text-sm font-semibold' : 'text-[9.5px] font-semibold'}>{isFullscreen ? 'Collapse' : 'Expand'}</span>
          </button>
        </div>

        {/* ── Header row 2: analytics buttons ── */}
        <div className={`flex items-center flex-shrink-0 ${isFullscreen ? 'gap-3 px-6 py-3 border-b border-slate-100' : 'gap-1 px-3 pb-2'}`}>
          <button title="Anomalies"
            onClick={() => anomalies ? setShowAnomalies(true) : loadAnomalies()}
            disabled={anomaliesLoading}
            className={`inline-flex items-center gap-1.5 rounded border border-amber-200 text-amber-700 bg-amber-50 font-semibold hover:bg-amber-100 disabled:opacity-50 transition-colors ${isFullscreen ? 'px-4 py-2 text-sm' : 'px-2 py-1 text-[10px]'}`}>
            <AlertTriangle className={isFullscreen ? 'w-4 h-4' : 'w-3 h-3'} />
            <span>{anomaliesLoading ? '…' : 'Anomalies'}</span>
          </button>
          <button title="Trends"
            onClick={() => trends ? setShowTrends(true) : loadTrends()}
            disabled={trendsLoading}
            className={`inline-flex items-center gap-1.5 rounded border border-violet-200 text-violet-700 bg-violet-50 font-semibold hover:bg-violet-100 disabled:opacity-50 transition-colors ${isFullscreen ? 'px-4 py-2 text-sm' : 'px-2 py-1 text-[10px]'}`}>
            <Zap className={isFullscreen ? 'w-4 h-4' : 'w-3 h-3'} />
            <span>{trendsLoading ? '…' : 'Trends'}</span>
          </button>
          <button title="Product Pulse"
            onClick={loadProductPulse}
            disabled={productPulseLoading}
            className={`inline-flex items-center gap-1.5 rounded border border-teal-200 text-teal-700 bg-teal-50 font-semibold hover:bg-teal-100 disabled:opacity-50 transition-colors ${isFullscreen ? 'px-4 py-2 text-sm' : 'px-2 py-1 text-[10px]'}`}>
            <Package className={isFullscreen ? 'w-4 h-4' : 'w-3 h-3'} />
            <span>{productPulseLoading ? '…' : 'Pulse'}</span>
          </button>
        </div>

        <div className={`flex-1 overflow-y-auto space-y-5 min-h-0 ${isFullscreen ? 'px-6 py-5' : 'px-4 py-4'}`}>
          {personasRegistered === false && !bannerDismissed && (
            <AgentABanner onDismiss={() => setBannerDismissed(true)} />
          )}

          {history.length === 0 && (
            <div>
              <p className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-2 pl-0.5">
                <Sparkles className="w-3 h-3 text-violet-400" />
                Suggestions
              </p>
              {isFullscreen ? (
                <div className="grid grid-cols-2 gap-2">
                  {SUGGESTED_QUESTIONS.map((item, i) => {
                    const c = QUESTION_COLORS[item.color];
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => sendQuestion(item.q)}
                        disabled={askMutation.isPending}
                        className="group text-left bg-white border border-slate-100 rounded-xl px-4 py-3.5 hover:border-slate-200 hover:shadow-sm disabled:opacity-40 transition-all duration-150"
                        style={{ borderLeft: `2px solid ${c.accent}` }}
                      >
                        <p className={`text-[10px] font-bold uppercase tracking-widest mb-1.5 ${c.chipText}`}>
                          {item.category}
                        </p>
                        <p className="text-[13px] text-slate-600 leading-snug font-medium group-hover:text-slate-900 transition-colors">
                          {item.q}
                        </p>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="flex flex-col gap-1.5">
                  {SUGGESTED_QUESTIONS.map((item, i) => {
                    const c = QUESTION_COLORS[item.color];
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => sendQuestion(item.q)}
                        disabled={askMutation.isPending}
                        className="group text-left bg-white border border-slate-100 rounded-lg px-3 py-2 hover:border-slate-200 hover:shadow-sm disabled:opacity-40 transition-all duration-150"
                        style={{ borderLeft: `2px solid ${c.accent}` }}
                      >
                        <p className="text-[11px] text-slate-600 leading-snug group-hover:text-slate-900 transition-colors truncate">
                          {item.q}
                        </p>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}

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

          {askMutation.isPending && <ThinkingBubble question={question} />}

          {askMutation.isError && (
            <div className="text-sm rounded-xl p-4 border border-red-200 bg-red-50 text-red-800 flex items-center gap-3">
              <X className="w-4 h-4 flex-shrink-0" />
              <span>{(askMutation.error as Error)?.message}</span>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className={`bg-white border-t border-gray-200 flex-shrink-0 ${isFullscreen ? 'px-6 py-4' : 'p-3'}`}>
          {chatEntries.length > 0 && (
            <div className={`flex items-center gap-1.5 pb-2 ${isFullscreen ? 'px-0 mb-1' : 'px-1'}`}>
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0" />
              <p className={`text-slate-400 ${isFullscreen ? 'text-sm' : 'text-[10px]'}`}>
                Context active — ask follow-ups like "show as line chart" or "filter to High churn only"
              </p>
            </div>
          )}
          <div className={`flex items-end ${isFullscreen ? 'gap-3' : 'gap-2'}`}>
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
              style={{ minHeight: isFullscreen ? '48px' : '36px', maxHeight: '200px', overflowY: 'auto' }}
              className={`flex-1 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none bg-slate-50 placeholder:text-slate-400 leading-snug ${isFullscreen ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}`}
              placeholder={
                chatEntries.length === 0
                  ? 'Ask about your customers, segments…'
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
              className={`rounded-xl bg-blue-700 text-white hover:bg-blue-800 disabled:opacity-40 transition-colors flex-shrink-0 ${isFullscreen ? 'p-3' : 'p-2'}`}
              title="Send (Enter)"
            >
              <Send className={isFullscreen ? 'w-5 h-5' : 'w-4 h-4'} />
            </button>
          </div>
          <p className={`text-slate-400 mt-1.5 ${isFullscreen ? 'text-sm' : 'text-[11px]'}`}>Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </>
  );
}

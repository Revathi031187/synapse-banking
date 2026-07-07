import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { MessageSquare, RefreshCw, Database, AlertCircle, CheckCircle2, BarChart2, Table2, X } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

import { getBankingApiBase } from '../../utils/apiBase';

interface GenieStatus {
  success?: boolean;
  catalog?: string;
  schema?: string;
  databricks_runtime?: boolean;
  persona_assignments_table?: string;
  persona_definitions_table?: string;
  customers_table_hint?: string;
  databricks_host_set?: boolean;
  databricks_token_set?: boolean;
  genie_space_id_set?: boolean;
  genie_space_id_valid?: boolean;
  databricks_oauth_m2m_set?: boolean;
  azure_service_principal_set?: boolean;
  genie_auth_note?: string;
  databricks_genie_auth_preference?: string | null;
  genie_effective_auth?: string | null;
  databricks_workspace_id_set?: boolean;
  ready_to_ask?: boolean;
}

interface GenieSpaceRow {
  space_id?: string;
  title?: string;
  description?: string | null;
  warehouse_id?: string | null;
}

interface GenieSpacesResponse {
  success?: boolean;
  error?: string;
  spaces?: GenieSpaceRow[];
  next_page_token?: string | null;
}

interface GenieVerifyResponse {
  success?: boolean;
  space_id?: string;
  title?: string;
  description?: string | null;
  warehouse_id?: string | null;
  error?: string;
  hint?: string;
}

interface GenieTable {
  columns: string[];
  rows: string[][];
}

interface GenieAskResponse {
  success?: boolean;
  error?: string;
  hint?: string;
  narrative?: string;
  sql?: string | null;
  table?: GenieTable | null;
  attachments?: Array<{ type?: string; text?: string; sql?: string; title?: string; table?: GenieTable }>;
  conversation_id?: string | null;
  message_id?: string | null;
  raw_attachment_types?: string[];
}

const CHART_COLORS = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444', '#06B6D4', '#EC4899', '#84CC16'];

function GenieResultTable({ table }: { table: { columns: string[]; rows: string[][] } }) {
  const [view, setView] = React.useState<'table' | 'chart'>('table');

  // Detect numeric columns for chart
  const safeRows = table.rows ?? [];
  const numericColIdx = table.columns.findIndex((_, ci) =>
    safeRows.slice(0, 5).every(r => r[ci] !== '' && !isNaN(Number(r[ci])))
  );
  const labelColIdx = numericColIdx > 0 ? 0 : (numericColIdx === 0 ? 1 : 0);
  const canChart = numericColIdx >= 0 && safeRows.length > 0 && table.columns.length >= 2;

  const chartData = canChart
    ? safeRows.slice(0, 50).map(r => ({
        name: r[labelColIdx] ?? '',
        value: Number(r[numericColIdx]),
      }))
    : [];

  return (
    <div className="rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-slate-800">
        <span className="text-xs font-bold text-slate-300 uppercase tracking-widest">
          Results — {table.rows.length} row{table.rows.length !== 1 ? 's' : ''}
        </span>
        <div className="ml-auto flex gap-1">
          <button
            type="button"
            onClick={() => setView('table')}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold transition-colors ${
              view === 'table' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700 hover:text-white'
            }`}
          >
            <Table2 className="w-3.5 h-3.5" /> Table
          </button>
          {canChart && (
            <button
              type="button"
              onClick={() => setView('chart')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold transition-colors ${
                view === 'chart' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700 hover:text-white'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" /> Chart
            </button>
          )}
        </div>
      </div>

      {view === 'table' ? (
        <div className="overflow-x-auto max-h-96">
          <table className="min-w-full text-sm border-collapse">
            <thead className="sticky top-0 bg-slate-100 z-10">
              <tr>
                {table.columns.map((col, ci) => (
                  <th
                    key={ci}
                    className="px-4 py-2.5 text-left text-xs font-bold text-slate-600 uppercase tracking-wide border-b border-slate-200 whitespace-nowrap"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, ri) => (
                <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-4 py-2 text-slate-800 border-b border-slate-100 whitespace-nowrap">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white p-4">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: '#64748b' }}
                angle={chartData.length > 6 ? -35 : 0}
                textAnchor={chartData.length > 6 ? 'end' : 'middle'}
                interval={0}
              />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
                formatter={(v: number) => [v.toLocaleString(), table.columns[numericColIdx]]}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {chartData.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default function BankingAskGenie() {
  const API_BASE = getBankingApiBase();
  const [question, setQuestion] = React.useState('');
  const [spacesResult, setSpacesResult] = React.useState<GenieSpacesResponse | null>(null);
  const [spacesLoading, setSpacesLoading] = React.useState(false);
  const [verifyResult, setVerifyResult] = React.useState<GenieVerifyResponse | null>(null);
  const [verifyLoading, setVerifyLoading] = React.useState(false);
  const [syncDismissed, setSyncDismissed] = React.useState(false);

  const statusQuery = useQuery({
    queryKey: ['banking-genie-status'],
    queryFn: async (): Promise<GenieStatus> => {
      const res = await fetch(`${API_BASE}/api/banking/genie/status`);
      if (!res.ok) throw new Error('Status request failed');
      return res.json();
    },
  });

  const syncMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/banking/genie/sync-personas`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) {
        const d = data?.detail;
        const msg = typeof d === 'string' ? d : 'Sync failed';
        throw new Error(msg);
      }
      return data;
    },
  });

  const loadGenieSpaces = React.useCallback(async () => {
    setSpacesLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/banking/genie/spaces?page_size=50`);
      const data = (await res.json()) as GenieSpacesResponse;
      setSpacesResult(data);
    } finally {
      setSpacesLoading(false);
    }
  }, [API_BASE]);

  const verifyGenieSpace = React.useCallback(async () => {
    setVerifyLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/banking/genie/spaces/verify`);
      const data = (await res.json()) as GenieVerifyResponse;
      setVerifyResult(data);
    } finally {
      setVerifyLoading(false);
    }
  }, [API_BASE]);

  const askMutation = useMutation({
    mutationFn: async (q: string) => {
      const res = await fetch(`${API_BASE}/api/banking/genie/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json();
      if (!res.ok) {
        const d = data?.detail;
        const msg =
          typeof d === 'string' ? d : Array.isArray(d) ? d.map((x: { msg?: string }) => x?.msg).join('; ') : 'Ask failed';
        throw new Error(msg);
      }
      return data as GenieAskResponse;
    },
  });

  const s = statusQuery.data;

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Ask Genie</h1>
        <p className="text-gray-500 text-sm mt-1">
          Natural-language questions against your Unity Catalog data via a Databricks Genie space. Persona context is injected from the latest Segmentation run.
        </p>
      </div>

      {/* Status */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Configuration</h2>
        {statusQuery.isLoading && <p className="text-sm text-gray-500">Loading status…</p>}
        {statusQuery.isError && (
          <div className="flex items-center gap-2 text-amber-700 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            Could not reach API. Is the backend running?
          </div>
        )}
        {s && (
          <ul className="text-sm space-y-2 text-gray-700">
            <li className="flex items-center gap-2">
              {s.ready_to_ask ? (
                <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              )}
              <span>
                Genie ask:{' '}
                <strong>{s.ready_to_ask ? 'ready' : 'not configured'}</strong> (host / credentials / valid space id)
              </span>
            </li>
            {s.genie_space_id_set && s.genie_space_id_valid === false && (
              <li className="text-amber-800">
                <strong>GENIE_SPACE_ID</strong> looks like a placeholder — use the real id from Genie space Settings (hex
                string).
              </li>
            )}
            {(s.databricks_oauth_m2m_set || s.azure_service_principal_set) && (
              <li className="text-green-800">
                OAuth credentials detected (Genie on Azure usually needs this instead of PAT-only).
              </li>
            )}
            {s.genie_effective_auth && (
              <li>
                <strong>Genie SDK auth in use:</strong> {s.genie_effective_auth}
                {s.databricks_genie_auth_preference ? ` (override: ${s.databricks_genie_auth_preference})` : ''}
              </li>
            )}
            {s.genie_auth_note ? (
              <li className="text-amber-900 bg-amber-50 rounded-md px-2 py-1.5">{s.genie_auth_note}</li>
            ) : null}
            <li>
              <strong>Catalog.schema:</strong> {s.catalog}.{s.schema}
            </li>
            <li>
              <strong>Persona tables:</strong> {s.persona_assignments_table},{' '}
              {s.persona_definitions_table}
            </li>
            <li>
              <strong>Customers (hint):</strong> {s.customers_table_hint}
            </li>
            <li>
              <strong>Databricks runtime (Spark):</strong> {s.databricks_runtime ? 'yes' : 'no'} — Delta sync only runs
              on cluster/notebook
            </li>
            <li>
              <strong>DATABRICKS_WORKSPACE_ID:</strong> {s.databricks_workspace_id_set ? 'set' : 'not set'} (optional; try if
              verify fails and admin requires org id)
            </li>
          </ul>
        )}
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        <button
          type="button"
          onClick={() => { setSyncDismissed(false); syncMutation.mutate(); }}
          disabled={syncMutation.isPending}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 text-white text-sm font-medium hover:bg-slate-900 disabled:opacity-50"
        >
          <Database className="w-4 h-4" />
          {syncMutation.isPending ? 'Syncing…' : 'Sync personas to catalog'}
        </button>
        <button
          type="button"
          onClick={() => statusQuery.refetch()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-800 hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh status
        </button>
        <button
          type="button"
          onClick={() => loadGenieSpaces()}
          disabled={spacesLoading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-blue-300 text-sm font-medium text-blue-900 hover:bg-blue-50 disabled:opacity-50"
        >
          <Database className="w-4 h-4" />
          {spacesLoading ? 'Loading spaces…' : 'List Genie spaces'}
        </button>
        <button
          type="button"
          onClick={() => verifyGenieSpace()}
          disabled={verifyLoading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-50"
        >
          <MessageSquare className="w-4 h-4" />
          {verifyLoading ? 'Verifying…' : 'Verify GENIE_SPACE_ID'}
        </button>
      </div>

      {verifyResult && (
        <div
          className={`mb-6 rounded-xl border p-5 text-sm ${
            verifyResult.success ? 'border-green-200 bg-green-50 text-green-900' : 'border-red-200 bg-red-50 text-red-900'
          }`}
        >
          {verifyResult.success ? (
            <div>
              <p className="font-semibold">Genie get_space OK</p>
              <p className="mt-1 font-mono text-xs">space_id: {verifyResult.space_id}</p>
              <p className="mt-1">title: {verifyResult.title}</p>
              {verifyResult.warehouse_id ? (
                <p className="mt-1 font-mono text-xs">warehouse_id: {verifyResult.warehouse_id}</p>
              ) : null}
            </div>
          ) : (
            <div className="space-y-2">
              <p>{verifyResult.error}</p>
              {verifyResult.hint && <p className="text-amber-900 bg-amber-50 border border-amber-200 rounded-lg p-3">{verifyResult.hint}</p>}
            </div>
          )}
        </div>
      )}

      {spacesResult && (
        <div className="mb-6 rounded-xl border border-gray-200 bg-white shadow-sm p-5 text-sm">
          <h2 className="text-sm font-semibold text-gray-900 mb-2">Genie spaces (this workspace)</h2>
          {!spacesResult.success && spacesResult.error && (
            <p className="text-red-700">{spacesResult.error}</p>
          )}
          {spacesResult.success && spacesResult.spaces && spacesResult.spaces.length === 0 && (
            <p className="text-gray-600">No spaces returned — check permissions or create a Genie space in this workspace.</p>
          )}
          {spacesResult.success && spacesResult.spaces && spacesResult.spaces.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 text-gray-500">
                    <th className="py-2 pr-4 font-medium">space_id → set as GENIE_SPACE_ID</th>
                    <th className="py-2 pr-4 font-medium">title</th>
                    <th className="py-2 font-medium">warehouse_id</th>
                  </tr>
                </thead>
                <tbody>
                  {spacesResult.spaces.map((row) => (
                    <tr key={row.space_id} className="border-b border-gray-100">
                      <td className="py-2 pr-4 font-mono text-gray-900">{row.space_id}</td>
                      <td className="py-2 pr-4 text-gray-800">{row.title}</td>
                      <td className="py-2 font-mono text-gray-600">{row.warehouse_id ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {spacesResult.next_page_token ? (
            <p className="mt-2 text-gray-500 text-xs">More pages exist; use API query page_token if needed.</p>
          ) : null}
        </div>
      )}

      {syncMutation.isSuccess && !syncDismissed && (
        <div
          className={`mb-6 text-sm rounded-lg p-4 border flex items-start gap-3 ${
            syncMutation.data?.skipped ? 'bg-slate-50 border-slate-200 text-slate-600' : 'bg-green-50 border-green-200 text-green-900'
          }`}
        >
          <span className="flex-1">{syncMutation.data?.message || 'Sync completed.'}</span>
          <button type="button" onClick={() => setSyncDismissed(true)} className="shrink-0 opacity-50 hover:opacity-100">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      {syncMutation.isError && !syncDismissed && (
        <div className="mb-6 text-sm rounded-lg p-4 border border-red-200 bg-red-50 text-red-900 flex items-start gap-3">
          <span className="flex-1">{(syncMutation.error as Error)?.message}</span>
          <button type="button" onClick={() => setSyncDismissed(true)} className="shrink-0 opacity-50 hover:opacity-100">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <label className="block text-sm font-semibold text-gray-900 mb-2">Question</label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={4}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="e.g. Summarize segment sizes using persona_definitions."
        />
        <button
          type="button"
          disabled={askMutation.isPending || !question.trim()}
          onClick={() => askMutation.mutate(question.trim())}
          className="mt-3 inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-700 text-white text-sm font-semibold hover:bg-blue-800 disabled:opacity-50"
        >
          {askMutation.isPending ? 'Asking…' : 'Ask Genie'}
        </button>
      </div>

      {askMutation.isError && (
        <div className="mt-6 text-sm rounded-lg p-4 border border-red-200 bg-red-50 text-red-900">
          {(askMutation.error as Error)?.message}
        </div>
      )}

      {askMutation.data && (
        <div className="mt-6 space-y-4">
          {!askMutation.data.success && askMutation.data.error && (
            <div className="text-sm space-y-2">
              <div className="text-red-700">{askMutation.data.error}</div>
              {askMutation.data.hint && (
                <div className="text-amber-900 bg-amber-50 border border-amber-200 rounded-lg p-3">{askMutation.data.hint}</div>
              )}
            </div>
          )}

          {/* ── Answer narrative ── */}
          {askMutation.data.narrative && (
            <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
              <h3 className="text-xs font-bold text-blue-700 uppercase tracking-widest mb-2">Answer</h3>
              <div className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">{askMutation.data.narrative}</div>
            </div>
          )}

          {/* ── Result Table ── */}
          {askMutation.data.table && askMutation.data.table.columns.length > 0 && (
            <GenieResultTable table={askMutation.data.table} />
          )}

          {/* ── SQL ── */}
          {askMutation.data.sql && (
            <details open className="text-sm">
              <summary className="cursor-pointer flex items-center gap-1.5 text-slate-500 font-semibold text-xs uppercase tracking-wide mb-2 select-none">
                <span className="w-4 h-4 rounded bg-slate-700 text-white flex items-center justify-center text-[9px] font-bold">SQL</span>
                Generated SQL
              </summary>
              <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto">
                <pre className="text-sm text-green-400 font-mono whitespace-pre">{askMutation.data.sql}</pre>
              </div>
            </details>
          )}
        </div>
      )}

      <p className="mt-8 text-xs text-gray-500">
        See <code className="bg-gray-100 px-1 rounded">docs/GENIE_INSTRUCTIONS_FOR_DATABRICKS.md</code> for Genie space
        instructions and sample SQL. Install <code className="bg-gray-100 px-1 rounded">requirements-databricks.txt</code>{' '}
        on the API host.
      </p>
    </div>
  );
}

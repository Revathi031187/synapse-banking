import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { MessageSquare, RefreshCw, Database, AlertCircle, CheckCircle2 } from 'lucide-react';

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
  ready_to_ask?: boolean;
}

interface GenieAskResponse {
  success?: boolean;
  error?: string;
  hint?: string;
  narrative?: string;
  sql?: string | null;
  attachments?: Array<{ type?: string; text?: string; sql?: string; title?: string }>;
  conversation_id?: string | null;
  message_id?: string | null;
  raw_attachment_types?: string[];
}

export default function BankingAskGenie() {
  const API_BASE = getBankingApiBase();
  const [question, setQuestion] = React.useState('');

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
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-2">
        <MessageSquare className="w-8 h-8 text-blue-700" />
        <h1 className="text-2xl font-bold text-gray-900">Ask Genie</h1>
      </div>
      <p className="text-gray-600 mb-6">
        Natural-language questions against your Unity Catalog data via a Databricks Genie space. Persona context is
        injected from the latest Agent A run.
      </p>

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
          </ul>
        )}
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        <button
          type="button"
          onClick={() => syncMutation.mutate()}
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
      </div>

      {syncMutation.isSuccess && (
        <div
          className={`mb-6 text-sm rounded-lg p-4 border ${
            syncMutation.data?.skipped ? 'bg-amber-50 border-amber-200 text-amber-900' : 'bg-green-50 border-green-200 text-green-900'
          }`}
        >
          {syncMutation.data?.message || 'Sync completed.'}
        </div>
      )}
      {syncMutation.isError && (
        <div className="mb-6 text-sm rounded-lg p-4 border border-red-200 bg-red-50 text-red-900">
          {(syncMutation.error as Error)?.message}
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
          {askMutation.data.narrative && (
            <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Answer</h3>
              <div className="text-sm text-gray-900 whitespace-pre-wrap">{askMutation.data.narrative}</div>
            </div>
          )}
          {askMutation.data.sql && (
            <div className="bg-slate-900 rounded-lg p-4 overflow-x-auto">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">SQL</h3>
              <pre className="text-sm text-green-400 font-mono">{askMutation.data.sql}</pre>
            </div>
          )}
          {askMutation.data.attachments && askMutation.data.attachments.length > 0 && (
            <details className="text-sm">
              <summary className="cursor-pointer text-blue-700 font-medium">Attachments ({askMutation.data.attachments.length})</summary>
              <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-x-auto max-h-64">
                {JSON.stringify(askMutation.data.attachments, null, 2)}
              </pre>
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

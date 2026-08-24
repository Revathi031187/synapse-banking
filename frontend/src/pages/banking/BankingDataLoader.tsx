import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import {
  Database, CheckCircle2, AlertCircle, Eye, X, Upload,
  Play, Users, TrendingUp, BarChart3, Download, DollarSign, Sparkles, ArrowRight
} from 'lucide-react';
import {
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

import { getBankingApiBase } from '../../utils/apiBase';
import { formatCompactUsd } from '../../utils/formatCurrency';
import { useSessionStorageState } from '../../hooks/useSessionStorageState';

const BANKING_COLORS = ['#1e40af', '#0891b2', '#059669', '#f59e0b', '#dc2626'];

const DATA_LOADER_UI_KEY = 'banking-data-loader-v1';
const AGENT_A_UI_KEY = 'banking-agent-a-v1';
const DEFAULT_AGENT_A_UI = {
  nClusters: 5,
  gamma: 0.5,
  resultsEnabled: false,
  pollingStatus: 'idle' as 'idle' | 'running' | 'complete' | 'failed',
};

export default function BankingDataLoader() {
  const API_BASE_URL = getBankingApiBase();
  const queryClient = useQueryClient();

  // ── Data Loader state ──────────────────────────────────────────────────────
  const [ui, setUi] = useSessionStorageState(DATA_LOADER_UI_KEY, { selectedDataset: '' });
  const { selectedDataset } = ui;
  const setSelectedDataset = (name: string) => setUi((prev) => ({ ...prev, selectedDataset: name }));
  const [viewingTable, setViewingTable] = useState<string | null>(null);
  const [tableData, setTableData] = useState<any | null>(null);

  // ── Agent A state ──────────────────────────────────────────────────────────
  const [agentAUi, setAgentAUi] = useSessionStorageState(AGENT_A_UI_KEY, DEFAULT_AGENT_A_UI);
  const { nClusters, gamma, resultsEnabled, pollingStatus } = agentAUi;
  const setPollingStatus = (s: typeof DEFAULT_AGENT_A_UI['pollingStatus']) =>
    setAgentAUi(prev => ({ ...prev, pollingStatus: s }));
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [pollingProgress, setPollingProgress] = useState(0);

  // startPolling lives in a ref so both the mutation callback and the resume-on-mount
  // effect share the same logic without creating circular hook dependencies.
  const startPollingRef = useRef<() => void>(() => {});
  startPollingRef.current = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setPollingProgress(0);
    setPollingStatus('running');
    pollRef.current = setInterval(async () => {
      try {
        const statusRes = await fetch(`${API_BASE_URL}/api/banking/agent_a/status`);
        if (!statusRes.ok) return;
        const statusData = await statusRes.json();
        setPollingProgress(Math.round((statusData.progress ?? 0) * 100));
        if (statusData.status === 'complete') {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          const resultsRes = await fetch(`${API_BASE_URL}/api/banking/agent_a/results`);
          if (resultsRes.ok) {
            const resultsData = await resultsRes.json();
            queryClient.setQueryData(['banking-agent-a-results'], resultsData.results || resultsData);
            setAgentAUi(prev => ({ ...prev, resultsEnabled: true, pollingStatus: 'complete' }));
          } else {
            setPollingStatus('complete');
          }
          // The backend pre-warms the Dashboard tab's per-persona cache and the
          // Segments tab's micro-segment breakdowns before reporting 'complete'
          // (see _run_agent_a_background), so these refetches land fast. Without
          // this, the Dashboard tab's ['dashboard-segments'] query keeps serving
          // its stale "please segment first" response from before this run until
          // a full page reload — this is the actual page users run segmentation
          // from, so this is the invalidation that matters (BankingAgentA.tsx has
          // its own copy of this fix, but isn't the page most users hit).
          queryClient.invalidateQueries({ queryKey: ['dashboard-segments'] });
          queryClient.invalidateQueries({ queryKey: ['banking-agent-a-customers'] });
          queryClient.invalidateQueries({ queryKey: ['ad-spend-metrics'] });
          queryClient.invalidateQueries({ queryKey: ['ad-spend-monthly'] });
          queryClient.invalidateQueries({ queryKey: ['banking-agent-a-results'] });
        } else if (statusData.status === 'failed') {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setPollingStatus('failed');
        }
      } catch { /* network blip — keep polling */ }
    }, 2000);
  };

  // On mount: resume polling if the user navigated away mid-run; otherwise leave
  // existing results intact so navigating back doesn't re-trigger segmentation.
  useEffect(() => {
    if (pollingStatus === 'running') startPollingRef.current();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Data Loader queries / mutations ────────────────────────────────────────
  const { data: datasetsData, isLoading: datasetsLoading } = useQuery({
    queryKey: ['banking-datasets'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/banking/datasets`);
      return res.json();
    }
  });

  const loadMutation = useMutation({
    mutationFn: async (datasetName: string) => {
      const res = await fetch(`${API_BASE_URL}/api/banking/datasets/load`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_name: datasetName })
      });
      if (!res.ok) throw new Error('Failed to load dataset');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['banking-status'] });
      queryClient.invalidateQueries({ queryKey: ['banking-datasets'] });
      queryClient.removeQueries({ queryKey: ['banking-agent-a-results'] });
    }
  });

  const handleViewTable = async (tableName: string) => {
    try {
      const datasetToUse = selectedDataset || datasetsData?.datasets?.[0]?.name || 'banking_v1';
      const res = await fetch(`${API_BASE_URL}/api/banking/datasets/view/${datasetToUse}/${tableName}`);
      if (!res.ok) {
        alert(`Failed to load table: ${res.statusText}`);
        return;
      }
      const data = await res.json();
      setTableData(data);
      setViewingTable(tableName);
    } catch (error) {
      alert(`Error loading table: ${error}`);
    }
  };

  // ── Agent A queries / mutations ────────────────────────────────────────────
  const executeMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n_clusters: nClusters, gamma })
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to execute Agent A: ${errorText}`);
      }
      return response.json();
    },
    onSuccess: () => {
      startPollingRef.current();
    }
  });

  const resultsQuery = useQuery({
    queryKey: ['banking-agent-a-results'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/results`);
      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to fetch results');
      }
      const data = await response.json();
      return data.results || data;
    },
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    enabled: resultsEnabled,
    retry: 1
  });

  const handleExport = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/export`);
      if (!response.ok) {
        let detail = `Export failed (HTTP ${response.status})`;
        try {
          const err = await response.json();
          if (typeof err?.detail === 'string' && err.detail.trim()) detail = err.detail;
        } catch { /* non-json body */ }
        throw new Error(detail);
      }
      const blob = await response.blob();
      if (blob.size === 0) throw new Error('Export returned an empty file');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const cd = response.headers.get('content-disposition') || '';
      const match = cd.match(/filename="?([^"]+)"?/i);
      a.download = match?.[1] || 'banking_personas.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert((error as Error).message || 'Export failed');
    }
  };

  // ── Derived values ─────────────────────────────────────────────────────────
  const datasets = datasetsData?.datasets || [];
  const results = resultsQuery.data;
  const segmentationLoading = executeMutation.isPending || pollingStatus === 'running' || resultsQuery.isLoading;
  const personas = results?.personas || {};
  const vizData = results?.visualization_data || {};

  if (datasetsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700 mx-auto mb-4"></div>
          <div className="text-gray-900 text-xl font-semibold">Loading datasets...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-fadeIn">

      {/* ── SECTION 1: Dataset Loader ────────────────────────────────────── */}
      <section className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Available Datasets</h2>

        {datasets.length === 0 && (
          <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-1" />
              <div>
                <div className="text-amber-900 font-semibold mb-2">No Datasets Found</div>
                <p className="text-amber-800 text-sm mb-3">
                  No pre-loaded datasets detected. Generate banking data by running:
                </p>
                <code className="block bg-gray-900 text-gray-100 p-3 rounded-lg text-sm font-mono">
                  python utils/banking_data_generator.py
                </code>
                <p className="text-amber-800 text-xs mt-2">
                  This will generate 5,000 banking customers with realistic profiles and transactions
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="grid gap-6">
          {datasets.map((dataset: any) => (
            <motion.div
              key={dataset.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`bg-white rounded-xl shadow-sm border-2 cursor-pointer transition-all duration-300 ${
                selectedDataset === dataset.name
                  ? 'border-blue-500 shadow-lg bg-blue-50'
                  : 'border-blue-200 hover:border-blue-400 hover:shadow-md'
              }`}
              onClick={() => setSelectedDataset(dataset.name)}
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {dataset.display_name === 'Banking Platform V1' ? 'Banking Dataset' : (dataset.display_name || dataset.name)}
                      </h3>
                      {dataset.status === 'ready' && (
                        <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                          <CheckCircle2 className="w-4 h-4 mr-1" />
                          Ready
                        </span>
                      )}
                      {dataset.status === 'not_generated' && (
                        <span className="inline-flex items-center px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm font-semibold">
                          <AlertCircle className="w-4 h-4 mr-1" />
                          Generate First
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 text-sm mb-3">{dataset.description}</p>

                    {dataset.tables && (
                      <div className="grid md:grid-cols-3 gap-3 mt-4">
                        {dataset.tables.map((table: any) => (
                          <div key={table.name} className="bg-white rounded-lg border border-blue-100 p-3">
                            <div className="flex items-center justify-between mb-1">
                              <div className="text-sm font-semibold text-gray-900">{table.display_name}</div>
                              {table.loaded && (
                                <button
                                  onClick={(e) => { e.stopPropagation(); handleViewTable(table.name); }}
                                  className="text-blue-700 hover:text-blue-800 p-1"
                                  title="View data"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                            <div className="text-xs text-gray-600">
                              {table.loaded ? (
                                <span className="flex items-center gap-1">
                                  <CheckCircle2 className="w-3 h-3 text-green-600" />
                                  {table.row_count?.toLocaleString() || 0} rows
                                </span>
                              ) : (
                                <span className="text-amber-600">Not loaded</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-blue-100">
                  <button
                    onClick={(e) => { e.stopPropagation(); loadMutation.mutate(dataset.name); }}
                    disabled={loadMutation.isPending || dataset.status !== 'ready'}
                    className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loadMutation.isPending ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Loading Dataset...</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-5 h-5" />
                        <span>Load Dataset into System</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {loadMutation.isSuccess && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-green-50 border-2 border-green-300 rounded-xl p-6"
          >
            <div className="flex items-start space-x-3">
              <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
              <div>
                <div className="text-green-900 font-bold text-lg mb-1">Dataset Loaded Successfully!</div>
                <p className="text-green-800 text-sm">
                  {typeof loadMutation.data?.tables_loaded_count === 'number' && (
                    <>
                      {loadMutation.data.tables_loaded_count} of {loadMutation.data.tables_total_count} tables were
                      successfully loaded.{' '}
                    </>
                  )}
                  The banking dataset has been loaded into ChromaDB. Configure and run Customer Segmentation below.
                </p>
                {!!loadMutation.data?.tables_missing?.length && (
                  <p className="text-amber-700 text-sm mt-2">
                    Not loaded: {loadMutation.data.tables_missing.join(', ')}.
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {loadMutation.isError && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-red-50 border-2 border-red-300 rounded-xl p-6"
          >
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
              <div>
                <div className="text-red-900 font-bold text-lg mb-2">Failed to Load Dataset</div>
                <p className="text-red-800 text-sm">{(loadMutation.error as Error).message}</p>
              </div>
            </div>
          </motion.div>
        )}
      </section>

      {/* Divider */}
      <div className="border-t-2 border-blue-100" />

      {/* ── SECTION 2: Customer Segmentation (Agent A) ───────────────────── */}
      <section className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Customer Segmentation</h1>
          <p className="text-gray-500 text-sm">AI-powered persona identification for retail banking customers</p>
        </div>

        {/* Parameters Card */}
        <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-blue-700 rounded-xl flex items-center justify-center">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-base font-semibold text-gray-900">Segmentation Parameters</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Number of Personas</label>
              <input
                type="number"
                min="3"
                max="10"
                className="input-field"
                value={nClusters}
                onChange={(e) => setAgentAUi((prev) => ({ ...prev, nClusters: Number(e.target.value) }))}
              />
              <p className="text-xs text-gray-500 mt-1">Recommended: 5-7 for retail banking</p>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Gamma (Diversity Weight)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                className="input-field"
                value={gamma}
                onChange={(e) => setAgentAUi((prev) => ({ ...prev, gamma: Number(e.target.value) }))}
              />
              <p className="text-xs text-gray-500 mt-1">Higher values = more diverse segments</p>
            </div>
          </div>

          <button
            onClick={() => executeMutation.mutate()}
            disabled={segmentationLoading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {segmentationLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>{pollingStatus === 'running' ? `Segmenting... ${pollingProgress}%` : 'Starting...'}</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                <span>Run Segmentation Analysis</span>
              </>
            )}
          </button>

          {executeMutation.isError && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-red-800">
                <AlertCircle className="w-5 h-5" />
                <span className="font-semibold">Error</span>
              </div>
              <p className="text-sm text-red-700 mt-1">{(executeMutation.error as Error).message}</p>
            </div>
          )}
        </div>

        {/* Results Section */}
        {results && (
          <>
            {/* Results header with Re-run option */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm font-semibold text-green-700">Segmentation complete</span>
              </div>
              <button
                onClick={() => {
                  setAgentAUi(prev => ({ ...prev, resultsEnabled: false, pollingStatus: 'idle' }));
                  queryClient.removeQueries({ queryKey: ['banking-agent-a-results'] });
                }}
                className="text-xs text-gray-500 hover:text-gray-700 border border-gray-200 hover:border-gray-400 px-3 py-1 rounded-full transition-colors"
              >
                Re-run segmentation
              </button>
            </div>

            {/* Summary Stats */}
            <div className="grid md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <Users className="w-6 h-6 text-blue-700" />
                  <div className="text-sm text-gray-600">Total Customers</div>
                </div>
                <div className="text-3xl font-bold text-gray-900">{results.total_customers || 0}</div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <BarChart3 className="w-6 h-6 text-blue-700" />
                  <div className="text-sm text-gray-600">Personas</div>
                </div>
                <div className="text-3xl font-bold text-gray-900">{Object.keys(personas).length}</div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                  <div className="text-sm text-gray-600">Silhouette Score</div>
                </div>
                <div className="text-3xl font-bold text-gray-900">
                  {results.silhouette_score ? results.silhouette_score.toFixed(3) : 'N/A'}
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
                <button
                  onClick={handleExport}
                  className="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <Download className="w-5 h-5" />
                  <span>Export</span>
                </button>
              </div>
            </div>

            {/* Visualizations */}
            <div className="grid md:grid-cols-2 gap-6">
              {vizData.scatter_data && vizData.scatter_data.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-blue-700" />
                    Customer Distribution
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <ScatterChart>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis type="number" dataKey="x" name="Balance" stroke="#6b7280" />
                      <YAxis type="number" dataKey="y" name="Engagement" stroke="#6b7280" />
                      <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                      <Scatter data={vizData.scatter_data} fill="#1e40af">
                        {vizData.scatter_data.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={BANKING_COLORS[entry.cluster % BANKING_COLORS.length]} />
                        ))}
                      </Scatter>
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              )}

              {vizData.persona_sizes && vizData.persona_sizes.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-700" />
                    Persona Sizes
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={vizData.persona_sizes}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="persona" stroke="#6b7280" />
                      <YAxis stroke="#6b7280" />
                      <Tooltip />
                      <Bar dataKey="count" fill="#1e40af">
                        {vizData.persona_sizes.map((_: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={BANKING_COLORS[index % BANKING_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Personas Grid */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Customer Personas</h2>
              <div className="grid md:grid-cols-3 gap-6">
                {Object.entries(personas).map(([personaId, persona]: [string, any], idx) => (
                  <div key={personaId} className="bg-white rounded-xl shadow-sm border border-blue-200 hover:shadow-lg transition-all p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div
                        className="w-12 h-12 rounded-xl flex items-center justify-center"
                        style={{ backgroundColor: BANKING_COLORS[idx % BANKING_COLORS.length] + '20' }}
                      >
                        <span className="text-2xl">{persona.emoji || '👤'}</span>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-gray-900">{persona.name}</h3>
                        <div className="text-sm text-gray-600">{persona.size} customers</div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Avg Annual Balance</span>
                        <span className="font-semibold text-blue-700 flex items-center gap-1">
                          <DollarSign className="w-4 h-4" />
                          {formatCompactUsd(persona.avg_annual_balance)}
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Avg products held</span>
                        <span className="font-semibold text-gray-900">
                          {persona.characteristics?.avg_products != null
                            ? `${Number(persona.characteristics.avg_products).toFixed(1)}`
                            : '—'}
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Intent Score</span>
                        <span className="font-semibold text-green-600">
                          {persona.avg_intent_score != null ? `${(persona.avg_intent_score * 100).toFixed(1)}%` : 'N/A'}
                        </span>
                      </div>
                    </div>

                    {persona.top_characteristics && persona.top_characteristics.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="text-sm font-semibold text-gray-700 mb-2">Key Characteristics</div>
                        <div className="space-y-1">
                          {persona.top_characteristics.slice(0, 3).map((char: string, i: number) => (
                            <div key={i} className="text-xs text-gray-600 flex items-start gap-1">
                              <span className="text-blue-700">•</span>
                              <span>{char}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {persona.ai_summary && (
                      <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Sparkles className="w-4 h-4 text-blue-700" />
                          <div className="text-xs font-semibold text-blue-900">AI Summary</div>
                        </div>
                        <p className="text-xs text-gray-700">{persona.ai_summary}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Insights Panel */}
            <div className="bg-gradient-to-br from-blue-50 to-amber-50 rounded-xl border border-blue-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-blue-700 rounded-xl flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-base font-semibold text-gray-900">Key Insights</h3>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-white rounded-lg p-4">
                  <div className="text-sm font-semibold text-gray-900 mb-2">Segmentation Quality</div>
                  <p className="text-sm text-gray-600">
                    Silhouette score of {results.silhouette_score?.toFixed(3) || 'N/A'} indicates
                    {results.silhouette_score && results.silhouette_score > 0.5 ? ' excellent' :
                     results.silhouette_score && results.silhouette_score > 0.3 ? ' good' : ' moderate'} cluster separation.
                  </p>
                </div>
                <div className="bg-white rounded-lg p-4">
                  <div className="text-sm font-semibold text-gray-900 mb-2">Next Steps</div>
                  <p className="text-sm text-gray-600 mb-3">
                    Explore macro and micro segments in the interactive dashboard.
                  </p>
                  <Link
                    to="/banking/macro-dashboard"
                    className="inline-flex items-center gap-2 text-blue-700 font-semibold hover:text-blue-800 transition-colors"
                  >
                    <BarChart3 className="w-4 h-4" />
                    View Segments Dashboard
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </div>
          </>
        )}

        {/* No Results State */}
        {!results && !segmentationLoading && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-8 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Users className="w-8 h-8 text-blue-700" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Ready to Segment Customers</h3>
            <p className="text-gray-600 mb-4">
              Configure the parameters above and click "Run Segmentation Analysis" to identify customer personas.
            </p>
            <div className="bg-white rounded-lg p-4 max-w-2xl mx-auto text-left">
              <div className="text-sm font-semibold text-gray-900 mb-2">About Customer Segmentation</div>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-700 mt-0.5 flex-shrink-0" />
                  <span>Identifies distinct customer personas based on banking behavior</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-700 mt-0.5 flex-shrink-0" />
                  <span>Analyzes account balances, transaction patterns, and engagement levels</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-700 mt-0.5 flex-shrink-0" />
                  <span>Enables targeted product recommendations and personalized marketing</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </section>

      {/* ── Table Viewer Modal ───────────────────────────────────────────────── */}
      <AnimatePresence>
        {viewingTable && tableData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={() => { setViewingTable(null); setTableData(null); }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="bg-gradient-to-r from-blue-700 to-blue-800 text-white p-6 flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold flex items-center gap-2">
                    <Database className="w-6 h-6" />
                    {viewingTable}
                  </h3>
                  <p className="text-blue-100 text-sm mt-1">
                    Showing {tableData?.data?.length ?? 0} of {tableData?.total_rows?.toLocaleString() ?? '—'} rows
                  </p>
                </div>
                <button
                  onClick={() => { setViewingTable(null); setTableData(null); }}
                  className="text-white hover:bg-blue-600 p-2 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="p-6 overflow-auto max-h-[calc(90vh-120px)]">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        {tableData.columns?.map((col: string) => (
                          <th
                            key={col}
                            className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap"
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {tableData.data?.map((row: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          {tableData.columns?.map((col: string) => (
                            <td key={col} className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap">
                              {(() => {
                                const val = row[col];
                                if (val === null || val === undefined) return '-';
                                if (typeof val === 'number') {
                                  // Don't add thousands-commas to years, months, IDs, or small integers used as codes
                                  const lc = col.toLowerCase();
                                  const isCode = lc === 'year' || lc === 'month' || lc.endsWith('_id') || lc === 'id' || lc === 'cluster_id';
                                  return isCode ? String(val) : val.toLocaleString();
                                }
                                return String(val);
                              })()}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

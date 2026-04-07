import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, Users, TrendingUp, BarChart3, AlertCircle, CheckCircle2, Download, DollarSign, Sparkles, ArrowRight } from 'lucide-react';
import {
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  PieChart as RePieChart,
  Pie
} from 'recharts';

import { getBankingApiBase } from '../../utils/apiBase';
import { formatCompactUsd } from '../../utils/formatCurrency';
import { useSessionStorageState } from '../../hooks/useSessionStorageState';

const BANKING_COLORS = ['#1e40af', '#0891b2', '#059669', '#f59e0b', '#dc2626'];

const AGENT_A_UI_KEY = 'banking-agent-a-v1';
const DEFAULT_AGENT_A_UI = { nClusters: 5, gamma: 0.5, resultsEnabled: false };

export default function BankingAgentA() {
  const API_BASE_URL = getBankingApiBase();
  const queryClient = useQueryClient();
  const [ui, setUi] = useSessionStorageState(AGENT_A_UI_KEY, DEFAULT_AGENT_A_UI);
  const { nClusters, gamma, resultsEnabled } = ui;

  // Check for cached results on mount
  useEffect(() => {
    const checkCache = () => {
      const cachedResults = queryClient.getQueryData(['banking-agent-a-results']);
      if (cachedResults) {
        setUi((prev) => ({ ...prev, resultsEnabled: true }));
      }
    };
    checkCache();
    const timeout = setTimeout(checkCache, 100);
    return () => clearTimeout(timeout);
  }, [queryClient]);

  // Mutation to execute Agent A
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
    onSuccess: async (data) => {
      setUi((prev) => ({ ...prev, resultsEnabled: true }));
      
      try {
        const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/results`);
        if (response.ok) {
          const resultsData = await response.json();
          const results = resultsData.results || resultsData;
          queryClient.setQueryData(['banking-agent-a-results'], results);
        }
      } catch (error) {
        console.error('Error fetching results:', error);
      }
    }
  });

  // Query to get results
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

  const results = resultsQuery.data;
  const isLoading = executeMutation.isPending || resultsQuery.isLoading;
  const personas = results?.personas || {};
  const vizData = results?.visualization_data || {};

  const handleExport = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/export`);
      if (!response.ok) {
        let detail = `Export failed (HTTP ${response.status})`;
        try {
          const err = await response.json();
          if (typeof err?.detail === 'string' && err.detail.trim()) detail = err.detail;
        } catch {
          /* non-json body */
        }
        throw new Error(detail);
      }
      const blob = await response.blob();
      if (blob.size === 0) {
        throw new Error('Export returned an empty file');
      }
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
      console.error('Export failed:', error);
      alert((error as Error).message || 'Export failed');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2">👥 Customer Segmentation</h1>
        <p className="text-gray-600 text-lg">AI-powered persona identification for retail banking customers</p>
      </div>

      {/* Parameters Card */}
      <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-blue-700 rounded-xl flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">🎯 Segmentation Parameters</h2>
        </div>
        
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Number of Personas
            </label>
            <input 
              type="number" 
              min="3"
              max="10"
              className="input-field"
              value={nClusters}
              onChange={(e) => setUi((prev) => ({ ...prev, nClusters: Number(e.target.value) }))}
            />
            <p className="text-xs text-gray-500 mt-1">Recommended: 5-7 for retail banking</p>
          </div>
          
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Gamma (Diversity Weight)
            </label>
            <input 
              type="number" 
              step="0.1"
              min="0"
              max="1"
              className="input-field"
              value={gamma}
              onChange={(e) => setUi((prev) => ({ ...prev, gamma: Number(e.target.value) }))}
            />
            <p className="text-xs text-gray-500 mt-1">Higher values = more diverse segments</p>
          </div>
        </div>
        
        <button 
          onClick={() => executeMutation.mutate()}
          disabled={isLoading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Running Segmentation...</span>
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
            {/* Customer Distribution Scatter Plot */}
            {vizData.scatter_data && vizData.scatter_data.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-700" />
                  📊 Customer Distribution
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      type="number" 
                      dataKey="x" 
                      name="Balance"
                      stroke="#6b7280"
                    />
                    <YAxis 
                      type="number" 
                      dataKey="y" 
                      name="Engagement"
                      stroke="#6b7280"
                    />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Scatter 
                      data={vizData.scatter_data} 
                      fill="#1e40af"
                    >
                      {vizData.scatter_data.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={BANKING_COLORS[entry.cluster % BANKING_COLORS.length]} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Persona Size Distribution */}
            {vizData.persona_sizes && vizData.persona_sizes.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-blue-700" />
                  👥 Persona Sizes
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={vizData.persona_sizes}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="persona" stroke="#6b7280" />
                    <YAxis stroke="#6b7280" />
                    <Tooltip />
                    <Bar dataKey="count" fill="#1e40af">
                      {vizData.persona_sizes.map((entry: any, index: number) => (
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
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Customer Personas</h2>
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
                      <span className="text-sm text-gray-600">Avg Balance</span>
                      <span className="font-semibold text-blue-700 flex items-center gap-1">
                        <DollarSign className="w-4 h-4" />
                        {formatCompactUsd(persona.avg_balance)}
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
              <h3 className="text-xl font-bold text-gray-900">💡 Key Insights</h3>
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
      {!results && !isLoading && (
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
    </div>
  );
}

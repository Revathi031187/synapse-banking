import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, Users, TrendingUp, BarChart3, AlertCircle, CheckCircle2, Download, DollarSign, Shield, Calendar, PieChart, Activity, Sparkles, X, ArrowRight, Database, ShoppingCart } from 'lucide-react';
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
  Pie,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts';
import AcademyAgentA_CustomerInsights from './AcademyAgentA_CustomerInsights';
import AcademyDataLoader from './AcademyDataLoader';
import { getBankingApiBase } from '../../utils/apiBase';

const API_BASE_URL = getBankingApiBase();

const COLORS = ['#059669', '#2563eb', '#ea580c'];
const COLOR_MAP: Record<string, string> = {
  '🏕️ First-Time Camper': '#059669',
  '👨‍👩‍👧‍👦 Family Socializer': '#2563eb',
  '⛰️ Seasoned Pro': '#ea580c'
};

export default function AcademyAgentAEnhanced() {
  const [activeTab, setActiveTab] = useState<'overview' | 'customer-insights'>('overview');
  const [nClusters, setNClusters] = useState(5);
  const [gamma, setGamma] = useState(0.5);
  const [explainViz, setExplainViz] = useState<string | null>(null);
  const [togetherApiKey, setTogetherApiKey] = useState('');
  const queryClient = useQueryClient();
  
  // ✨ Check for cached results on mount to persist session across navigation
  const [resultsEnabled, setResultsEnabled] = useState(false);

  // Check for cached data on mount and enable results query if data exists
  useEffect(() => {
    const checkCache = () => {
      const cachedResults = queryClient.getQueryData(['academy-agent-a-results']);
      console.log('[Agent A] Checking cache on mount:', cachedResults ? 'FOUND' : 'NOT FOUND');
      if (cachedResults) {
        console.log('[Agent A] ✅ Cached results found - enabling results query');
        setResultsEnabled(true);
      } else {
        console.log('[Agent A] ⚠️ No cached results found');
      }
    };
    
    // Run immediately
    checkCache();
    
    // Also run after a short delay to catch any race conditions
    const timeout = setTimeout(checkCache, 100);
    return () => clearTimeout(timeout);
  }, [queryClient]);

  // Mutation to execute Agent A
  const executeMutation = useMutation({
    mutationFn: async () => {
      console.log(`[Agent A] Executing clustering with ${nClusters} clusters and gamma=${gamma}`);
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n_clusters: nClusters, gamma })
      });
      if (!response.ok) {
        const errorText = await response.text();
        console.error('[Agent A] Execution failed:', errorText);
        throw new Error(`Failed to execute Agent A: ${errorText}`);
      }
      const data = await response.json();
      console.log('[Agent A] Execution completed:', data);
      return data;
    },
    onSuccess: async (data) => {
      console.log('[Agent A] onSuccess callback - enabling results query');
      // Enable results query AFTER successful execution
      setResultsEnabled(true);
      
      // Force an immediate fetch of the results
      console.log('[Agent A] Forcing results fetch...');
      try {
        const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/results`);
        if (response.ok) {
          const resultsData = await response.json();
          const results = resultsData.results || resultsData;
          queryClient.setQueryData(['academy-agent-a-results'], results);
          console.log('[Agent A] Results cached successfully:', results);
        }
      } catch (error) {
        console.error('[Agent A] Error fetching results:', error);
      }
    },
    onError: (error) => {
      console.error('[Agent A] Execution error:', error);
    }
  });

  // Query to get results - ONLY enabled after user clicks "Run Clustering"
  const resultsQuery = useQuery({
    queryKey: ['academy-agent-a-results'],
    queryFn: async () => {
      console.log('[Agent A] Fetching results...');
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/results`);
      if (!response.ok) {
        if (response.status === 404) {
          console.log('[Agent A] No results found (404)');
          return null;
        }
        throw new Error('Failed to fetch results');
      }
      const data = await response.json();
      console.log('[Agent A] Results fetched:', data);
      return data.results || data;
    },
    staleTime: Infinity, // Results persist until explicitly cleared
    gcTime: Infinity, // Keep in cache indefinitely (formerly cacheTime)
    refetchOnMount: false, // Don't refetch on mount - use cached data
    refetchOnWindowFocus: false, // Don't refetch when window regains focus
    enabled: resultsEnabled, // ✨ FIXED: Only enabled after user runs clustering
    retry: 1 // Retry once on failure
  });

  const results = resultsQuery.data;
  const isLoading = executeMutation.isPending || resultsQuery.isLoading;
  const personas = results?.personas || {};
  const vizData = results?.visualization_data || {};

  // Fetch Together AI API key
  useQuery({
    queryKey: ['together-api-key'],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/config/together-api-key`);
        if (!response.ok) return null;
        const result = await response.json();
        if (result.configured && result.api_key) {
          setTogetherApiKey(result.api_key);
        }
        return result;
      } catch {
        return null;
      }
    },
  });

  // Mutation to generate AI explanation for visualizations
  const explainVizMutation = useMutation({
    mutationFn: async ({ vizType, vizData, personas }: { vizType: string; vizData: any; personas: any }) => {
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/explain-visualization`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: togetherApiKey,
          visualization_type: vizType,
          data: vizData,
          personas: personas
        }),
      });
      if (!response.ok) throw new Error('Failed to generate explanation');
      const result = await response.json();
      return result.explanation;
    },
  });

  const handleExport = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/export`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'academy_sports_personas.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleExplainVisualization = (vizType: string, data: any) => {
    setExplainViz(vizType);
    explainVizMutation.mutate({ vizType, vizData: data, personas });
  };

  // Prepare data for revenue chart
  const revenueData = Object.values(personas).map((p: any) => ({
    name: p.persona_name,
    'Total Revenue': p.revenue_metrics?.total_revenue_12mo || 0,
    'Estimated Profit': p.revenue_metrics?.estimated_profit || 0,
    'Avg Customer Value': p.revenue_metrics?.avg_customer_value || 0
  }));

  // Prepare data for confidence distribution
  const confidenceData = Object.values(personas).map((p: any) => ({
    name: p.persona_name,
    'High Confidence': p.confidence_metrics?.high_confidence_count || 0,
    'Medium Confidence': p.confidence_metrics?.medium_confidence_count || 0,
    'Low Confidence': p.confidence_metrics?.low_confidence_count || 0
  }));

  // Prepare seasonal data
  const seasonalData = Object.values(personas).flatMap((p: any) => {
    const seasonal = p.temporal_metrics?.seasonal_distribution || {};
    return Object.entries(seasonal).map(([season, count]) => ({
      season,
      [p.short_name]: count
    }));
  }).reduce((acc: any[], curr) => {
    const existing = acc.find(item => item.season === curr.season);
    if (existing) {
      Object.assign(existing, curr);
    } else {
      acc.push(curr);
    }
    return acc;
  }, []);

  // Prepare radar chart data from backend visualization_data
  const radarData = vizData.persona_characteristics?.length > 0 ? [
    {
      metric: 'Search Specificity',
      ...Object.fromEntries(
        vizData.persona_characteristics.map((p: any) => [p.persona, p.search_specificity])
      )
    },
    {
      metric: 'Spec Expansion',
      ...Object.fromEntries(
        vizData.persona_characteristics.map((p: any) => [p.persona, p.spec_expansion])
      )
    },
    {
      metric: 'Bundle Affinity',
      ...Object.fromEntries(
        vizData.persona_characteristics.map((p: any) => [p.persona, p.bundle_affinity])
      )
    },
    {
      metric: 'Price Sensitivity',
      ...Object.fromEntries(
        vizData.persona_characteristics.map((p: any) => [p.persona, p.price_sensitivity])
      )
    }
  ] : [];

  // Calculate summary metrics with proper fallbacks
  const totalRevenue: number = results && personas ? Object.values(personas).reduce(
    (sum: number, p: any) => sum + (p.revenue_metrics?.total_revenue_12mo || 0),
    0
  ) as number : 0;
  const totalProfit: number = results && personas ? Object.values(personas).reduce(
    (sum: number, p: any) => sum + (p.revenue_metrics?.estimated_profit || 0),
    0
  ) as number : 0;
  const avgMargin: number = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
  const totalCustomers = results?.total_customers || 0;
  const modelAccuracy = results?.validation?.accuracy || 0;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center space-x-3">
            <span className="text-5xl">🏕️</span>
            <span>Agent A: Customer Personas</span>
          </h1>
          <p className="text-gray-600 text-lg">K-Prototypes Clustering for Personalization</p>
        </div>
        
        {results && (
          <button
            onClick={handleExport}
            className="btn-success flex items-center space-x-2"
          >
            <Download className="w-5 h-5" />
            <span>Export to CSV</span>
          </button>
        )}
      </div>

      {/* Data Loader Section - Always visible at top */}
      <AcademyDataLoader />

      {/* Segmentation Overview CTA - Only show after personas are generated */}
      {results && Object.keys(personas).length > 0 && (
        <div className="space-y-4">
          {/* NEW: Visual Macro Dashboard - PRIMARY CTA */}
          <Link to="/academy/macro-dashboard">
            <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-xl shadow-2xl p-6 hover:shadow-3xl transition-all duration-300 transform hover:scale-[1.02] cursor-pointer border-2 border-white/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-white rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
                    <span className="text-4xl">🎯</span>
                  </div>
                  <div className="text-white">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-2xl font-bold">🏕️ Visual Macro Dashboard (NEW!)</h3>
                      <span className="bg-gradient-to-r from-yellow-400 to-orange-400 text-gray-900 text-xs font-bold px-3 py-1 rounded-full animate-pulse shadow-lg">
                        DEMO READY
                      </span>
                    </div>
                    <p className="text-sm opacity-95 font-medium">
                      Interactive dashboard with lifestyle images, micro segments drill-down, and live product recommendations - Perfect for client demos!
                    </p>
                  </div>
                </div>
                <div className="bg-white text-indigo-600 rounded-full p-3 flex-shrink-0 shadow-lg">
                  <ArrowRight className="w-7 h-7" />
                </div>
              </div>
            </div>
          </Link>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="bg-white shadow-sm rounded-xl border border-gray-200 overflow-hidden">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex-1 px-6 py-4 flex items-center justify-center space-x-2 font-medium transition-all ${
              activeTab === 'overview'
                ? 'bg-green-50 text-green-700 border-b-2 border-green-600'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <PieChart className="w-5 h-5" />
            <span>Overview & Personas</span>
          </button>
          <button
            onClick={() => setActiveTab('customer-insights')}
            className={`flex-1 px-6 py-4 flex items-center justify-center space-x-2 font-medium transition-all ${
              activeTab === 'customer-insights'
                ? 'bg-green-50 text-green-700 border-b-2 border-green-600'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Users className="w-5 h-5" />
            <span>Customer Insights</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'customer-insights' ? (
        <AcademyAgentA_CustomerInsights />
      ) : (
        <>
          {/* Data Overview Section - DYNAMIC & MINIMALIZED: Only after clustering completes */}
          {results && Object.keys(personas).length > 0 && totalCustomers > 0 && (
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-3 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Database className="w-5 h-5 text-indigo-600" />
                <h3 className="text-sm font-semibold text-gray-900">Data Analyzed</h3>
              </div>
              <div className="flex items-center gap-6 text-xs">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-blue-600" />
                  <span className="font-bold text-blue-700">{totalCustomers.toLocaleString()}</span>
                  <span className="text-gray-600">customers</span>
                </div>
                <div className="flex items-center gap-2">
                  <ShoppingCart className="w-4 h-4 text-green-600" />
                  <span className="font-bold text-green-700">{results?.product_count || '1,000+'}</span>
                  <span className="text-gray-600">products</span>
                </div>
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-purple-600" />
                  <span className="font-bold text-purple-700">30+</span>
                  <span className="text-gray-600">behavioral signals</span>
                </div>
              </div>
            </div>
          </div>
          )}

          {/* Configuration Card */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
            <Activity className="w-6 h-6 text-green-600" />
            <span>Clustering Configuration</span>
          </h2>
        </div>
        <div className="card-body">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="flex flex-col">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Number of Clusters
              </label>
              <input
                type="number"
                value={nClusters}
                onChange={(e) => setNClusters(Number(e.target.value))}
                min="2"
                max="5"
                className="input-field"
              />
              <p className="text-xs text-gray-500 mt-1">Recommended: 3-4 personas</p>
            </div>
            <div className="flex flex-col">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Gamma (Numeric vs Categorical Balance)
              </label>
              <input
                type="number"
                value={gamma}
                onChange={(e) => setGamma(Number(e.target.value))}
                step="0.1"
                min="0.1"
                max="1.0"
                className="input-field"
              />
              <p className="text-xs text-gray-500 mt-1">0.5 = balanced, {'<'}0.5 = favor numeric, {'>'}0.5 = favor categorical</p>
            </div>
          </div>

          <button
            onClick={() => executeMutation.mutate()}
            disabled={isLoading}
            className="mt-6 w-full btn-primary flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Running K-Prototypes...</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                <span>Run K-Prototypes Clustering</span>
              </>
            )}
          </button>
          
          {/* Last Refreshed Indicator */}
          {results && results.last_refreshed && (
            <div className="mt-4 flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-blue-600" />
                <span className="text-sm text-gray-700">
                  <span className="font-semibold">Last Refreshed:</span> {new Date(results.last_refreshed).toLocaleString()}
                </span>
              </div>
              <div className="text-xs text-blue-600 font-medium">
                ♻️ Refreshes weekly on Sundays at 2 AM
              </div>
            </div>
          )}
          
          {/* Business Constraints Status */}
          {results && results.constraints_validation && (
            <div className={`mt-2 p-3 rounded-lg border ${
              results.constraints_validation.all_constraints_met 
                ? 'bg-green-50 border-green-200' 
                : 'bg-yellow-50 border-yellow-200'
            }`}>
              <div className="flex items-center space-x-2">
                {results.constraints_validation.all_constraints_met ? (
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-yellow-600" />
                )}
                <span className={`text-sm font-semibold ${
                  results.constraints_validation.all_constraints_met 
                    ? 'text-green-700' 
                    : 'text-yellow-700'
                }`}>
                  Business Constraints: {results.constraints_validation.all_constraints_met ? 'All Met ✓' : 'Some Not Met'}
                </span>
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {results.constraints_validation.recommendation}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Executive Summary */}
      {results && totalCustomers > 0 && Object.keys(personas).length > 0 && (
        <>
          <div className="card bg-gradient-to-br from-green-50 to-blue-50">
            <div className="card-body">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
                  <PieChart className="w-7 h-7 text-green-600" />
                  <span>Executive Summary</span>
                </h2>
                {togetherApiKey && (
                  <button
                    onClick={() => handleExplainVisualization('executive', { personas, totalRevenue, totalProfit, avgMargin })}
                    disabled={explainVizMutation.isPending && explainViz === 'executive'}
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{explainVizMutation.isPending && explainViz === 'executive' ? 'Explaining...' : 'Explain with AI'}</span>
                  </button>
                )}
              </div>
              
              <div className="grid md:grid-cols-4 gap-6">
                <div className="bg-white rounded-lg p-5 shadow-sm border border-green-200">
                  <div className="text-gray-600 text-sm font-medium mb-1">Total Annual Revenue</div>
                  <div className="text-3xl font-bold text-green-600">
                    ${(totalRevenue / 1000).toFixed(0)}K
                  </div>
                  <div className="text-sm text-gray-500 mt-1">Last 12 months</div>
                </div>
                
                <div className="bg-white rounded-lg p-5 shadow-sm border border-blue-200">
                  <div className="text-gray-600 text-sm font-medium mb-1">Estimated Profit</div>
                  <div className="text-3xl font-bold text-blue-600">
                    ${(totalProfit / 1000).toFixed(0)}K
                  </div>
                  <div className="text-sm text-gray-500 mt-1">~{avgMargin.toFixed(1)}% margin</div>
                </div>
                
                <div className="bg-white rounded-lg p-5 shadow-sm border border-orange-200">
                  <div className="text-gray-600 text-sm font-medium mb-1">Total Customers</div>
                  <div className="text-3xl font-bold text-orange-600">
                    {totalCustomers > 0 ? totalCustomers.toLocaleString() : '0'}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">{Object.keys(personas).length} personas</div>
                </div>
                
                <div className="bg-white rounded-lg p-5 shadow-sm border border-purple-200">
                  <div className="text-gray-600 text-sm font-medium mb-1">Model Accuracy</div>
                  <div className="text-3xl font-bold text-purple-600">
                    {modelAccuracy > 0 ? `${modelAccuracy.toFixed(1)}%` : '0%'}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {modelAccuracy > 85 ? '✅ Excellent' : modelAccuracy > 60 ? '✓ Good' : modelAccuracy > 0 ? '⚠️ Needs improvement' : 'Not available'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Revenue Chart */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                    <DollarSign className="w-6 h-6 text-green-600" />
                    <span>💰 Revenue by Persona</span>
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Understand which personas drive the most revenue and profit (calculated from actual purchase data)
                  </p>
                </div>
                {togetherApiKey && (
                  <button
                    onClick={() => handleExplainVisualization('revenue', { personas, revenueData })}
                    disabled={explainVizMutation.isPending && explainViz === 'revenue'}
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{explainVizMutation.isPending && explainViz === 'revenue' ? 'Explaining...' : 'Explain with AI'}</span>
                  </button>
                )}
              </div>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    labelStyle={{ color: '#111827', fontWeight: 600 }}
                  />
                  <Legend />
                  <Bar dataKey="Total Revenue" fill="#059669" isAnimationActive={true} animationDuration={1000} radius={[8, 8, 0, 0]} />
                  <Bar dataKey="Estimated Profit" fill="#2563eb" isAnimationActive={true} animationDuration={1000} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              
              <div className="grid md:grid-cols-3 gap-4 mt-6">
                {Object.values(personas).map((p: any, idx) => (
                  <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="text-sm text-gray-600 font-medium">{p.persona_name}</div>
                    <div className="text-2xl font-bold text-gray-900 mt-1">
                      {p.revenue_metrics?.revenue_percentage}%
                    </div>
                    <div className="text-xs text-gray-500">of total revenue</div>
                    <div className="text-sm text-green-600 font-semibold mt-2">
                      ${(p.revenue_metrics?.avg_customer_value || 0).toFixed(0)}/customer
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Confidence Distribution */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                    <Shield className="w-6 h-6 text-blue-600" />
                    <span>🎯 Assignment Confidence</span>
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    How confident are we in each persona assignment? Higher is better (based on clustering distance metrics)
                  </p>
                </div>
                {togetherApiKey && (
                  <button
                    onClick={() => handleExplainVisualization('confidence', { personas, confidenceData })}
                    disabled={explainVizMutation.isPending && explainViz === 'confidence'}
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{explainVizMutation.isPending && explainViz === 'confidence' ? 'Explaining...' : 'Explain with AI'}</span>
                  </button>
                )}
              </div>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={confidenceData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <YAxis dataKey="name" type="category" stroke="#6b7280" width={150} style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    labelStyle={{ color: '#111827', fontWeight: 600 }}
                  />
                  <Legend />
                  <Bar dataKey="High Confidence" stackId="a" fill="#059669" isAnimationActive={true} animationDuration={1000} animationBegin={0} />
                  <Bar dataKey="Medium Confidence" stackId="a" fill="#ea580c" isAnimationActive={true} animationDuration={1000} animationBegin={300} />
                  <Bar dataKey="Low Confidence" stackId="a" fill="#ef4444" isAnimationActive={true} animationDuration={1000} animationBegin={600} />
                </BarChart>
              </ResponsiveContainer>
              
              <div className="grid md:grid-cols-3 gap-4 mt-6">
                {Object.values(personas).map((p: any, idx) => (
                  <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="text-sm text-gray-600 font-medium">{p.persona_name}</div>
                    <div className="text-3xl font-bold text-gray-900 mt-1">
                      {p.confidence_metrics?.avg_confidence || 75}%
                    </div>
                    <div className="text-xs text-gray-500">average confidence</div>
                    <div className="flex items-center space-x-2 mt-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-600 rounded-full h-2 transition-all duration-1000" 
                          style={{ width: `${p.confidence_metrics?.avg_confidence || 75}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Seasonal Trends */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                    <Calendar className="w-6 h-6 text-purple-600" />
                    <span>📅 Seasonal Customer Acquisition</span>
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    When do different personas join? Plan your marketing campaigns accordingly (from registration dates)
                  </p>
                </div>
                {togetherApiKey && (
                  <button
                    onClick={() => handleExplainVisualization('seasonal', { personas, seasonalData })}
                    disabled={explainVizMutation.isPending && explainViz === 'seasonal'}
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{explainVizMutation.isPending && explainViz === 'seasonal' ? 'Explaining...' : 'Explain with AI'}</span>
                  </button>
                )}
              </div>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={seasonalData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="season" stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    labelStyle={{ color: '#111827', fontWeight: 600 }}
                  />
                  <Legend />
                  {Object.keys(personas).map((key, idx) => {
                    const persona = personas[key];
                    return (
                      <Area
                        key={idx}
                        type="monotone"
                        dataKey={persona.short_name}
                        stackId="1"
                        stroke={COLORS[idx % 3]}
                        fill={COLORS[idx % 3]}
                        fillOpacity={0.6}
                        isAnimationActive={true}
                        animationDuration={1500}
                        animationBegin={idx * 200}
                      />
                    );
                  })}
                </AreaChart>
              </ResponsiveContainer>
              
              <div className="grid md:grid-cols-3 gap-4 mt-6">
                {Object.values(personas).map((p: any, idx) => (
                  <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="text-sm text-gray-600 font-medium">{p.persona_name}</div>
                    <div className="text-xl font-bold text-gray-900 mt-1">
                      {p.temporal_metrics?.peak_season || 'Summer'}
                    </div>
                    <div className="text-xs text-gray-500">peak acquisition season</div>
                    <div className="text-sm text-blue-600 font-semibold mt-2">
                      {p.temporal_metrics?.growth_rate_3mo || 0 > 0 ? '📈' : '📉'} 
                      {Math.abs(p.temporal_metrics?.growth_rate_3mo || 0).toFixed(1)}% growth
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Validation Results */}
          {results.validation && (
            <div className="card bg-gradient-to-br from-green-50 to-blue-50">
              <div className="card-body">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
                    <CheckCircle2 className="w-7 h-7 text-green-600" />
                    <span>Validation Results</span>
                  </h2>
                  {togetherApiKey && (
                    <button
                      onClick={() => handleExplainVisualization('validation', { validation: results.validation, personas })}
                      disabled={explainVizMutation.isPending && explainViz === 'validation'}
                      className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      <Sparkles className="w-4 h-4" />
                      <span>{explainVizMutation.isPending && explainViz === 'validation' ? 'Explaining...' : 'Explain with AI'}</span>
                    </button>
                  )}
                </div>
                
                <div className="grid md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-lg p-5 shadow-sm border border-green-200">
                    <div className="text-gray-600 text-sm font-medium mb-1">Accuracy</div>
                    <div className="text-4xl font-bold text-green-600">
                      {results.validation.accuracy?.toFixed(1)}%
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-5 shadow-sm border border-blue-200">
                    <div className="text-gray-600 text-sm font-medium mb-1">Correct Predictions</div>
                    <div className="text-4xl font-bold text-blue-600">
                      {results.validation.correct_predictions?.toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-5 shadow-sm border border-orange-200">
                    <div className="text-gray-600 text-sm font-medium mb-1">Total Customers</div>
                    <div className="text-4xl font-bold text-orange-600">
                      {results.total_customers?.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Enhanced Persona Cards with Business Constraints */}
          <div className="card-grid-3">
            {Object.values(personas).map((persona: any, idx) => (
              <div
                key={idx}
                onClick={() => window.location.href = `/academy/macro-segment/${persona.cluster_id}/micro`}
                className="card hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 cursor-pointer group relative h-full flex flex-col"
              >
                {/* Clickable indicator */}
                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-sm text-blue-600 font-semibold">View Micro Segments →</span>
                </div>
                
                <div className="card-body flex-1 flex flex-col">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{persona.persona_name}</h3>
                  <p className="text-gray-600 text-sm mb-4">{persona.description}</p>
                  
                  {/* Special Flags Badges */}
                  {persona.special_flags && persona.special_flags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {persona.special_flags.map((flag: string, fidx: number) => (
                        <span
                          key={fidx}
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            flag === 'high_value' ? 'bg-purple-100 text-purple-700' :
                            flag === 'revenue_driver' ? 'bg-green-100 text-green-700' :
                            flag === 'price_sensitive' ? 'bg-orange-100 text-orange-700' :
                            flag === 'brand_loyal' ? 'bg-blue-100 text-blue-700' :
                            flag === 'expert_level' ? 'bg-indigo-100 text-indigo-700' :
                            flag === 'novice_level' ? 'bg-yellow-100 text-yellow-700' :
                            flag === 'large_segment' ? 'bg-teal-100 text-teal-700' :
                            'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {flag.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  <div className="space-y-3 flex-1 flex flex-col">
                    {/* Business Metrics - Revenue Potential */}
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-3 border border-green-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-xs text-gray-600 font-medium">Revenue Potential</div>
                          <div className="text-xl font-bold text-green-700">
                            ${persona.revenue_metrics?.avg_customer_value?.toFixed(0)}
                          </div>
                          <div className="text-xs text-gray-500">per customer/year</div>
                        </div>
                        <DollarSign className="w-8 h-8 text-green-600 opacity-50" />
                      </div>
                    </div>
                    
                    {/* Size & Percentage */}
                    <div className="flex items-center justify-between pb-3 border-b border-gray-200">
                      <span className="text-gray-600 text-sm font-medium">Segment Size:</span>
                      <span className="text-gray-900 font-bold">
                        {persona.size?.toLocaleString()} ({persona.percentage}%)
                      </span>
                    </div>
                    
                    {/* Key Behavioral Traits */}
                    <div className="pt-3">
                      <div className="text-sm font-semibold text-gray-900 mb-3">Prominent Traits</div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Search Expertise:</span>
                          <span className="text-gray-900 font-semibold">{persona.characteristics?.avg_search_specificity?.toFixed(1)}/5.0</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Research Depth:</span>
                          <span className="text-gray-900 font-semibold">
                            {(persona.characteristics?.avg_spec_expansion_rate * 100)?.toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Bundle Interest:</span>
                          <span className="text-gray-900 font-semibold">
                            {(persona.characteristics?.avg_bundle_affinity * 100)?.toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Price Focus:</span>
                          <span className="text-gray-900 font-semibold">
                            {(persona.characteristics?.avg_price_sort_frequency * 100)?.toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Avg Annual Spend:</span>
                          <span className="text-green-600 font-bold">
                            ${persona.characteristics?.avg_spend_12mo?.toFixed(0)}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Revenue Share:</span>
                          <span className="text-blue-600 font-bold">
                            {persona.revenue_metrics?.revenue_percentage}%
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Product Preferences */}
                    <div className="pt-3 border-t border-gray-200">
                      <div className="text-sm font-semibold text-gray-900 mb-2">Product Preferences</div>
                      <div className="space-y-2">
                        <div className="text-sm">
                          <span className="text-green-600 font-semibold">✅ Loves:</span>
                          <div className="text-gray-700 mt-1 text-xs">
                            {persona.product_preferences?.loves?.slice(0, 3).join(', ')}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Action hint */}
                    <div className="pt-3 border-t border-gray-200 mt-auto">
                      <div className="text-xs text-blue-600 font-medium group-hover:text-blue-700 transition-colors">
                        Click to explore micro segments →
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Customer Distribution */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                  <span>Customer Distribution by Persona</span>
                </h2>
                {togetherApiKey && (
                  <button
                    onClick={() => handleExplainVisualization('distribution', { personas })}
                    disabled={explainVizMutation.isPending && explainViz === 'distribution'}
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{explainVizMutation.isPending && explainViz === 'distribution' ? 'Explaining...' : 'Explain with AI'}</span>
                  </button>
                )}
              </div>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={Object.values(personas)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="persona_name" stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    labelStyle={{ color: '#111827', fontWeight: 600 }}
                  />
                  <Legend />
                  <Bar dataKey="size" fill="#059669" name="Customers" isAnimationActive={true} animationDuration={1000} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Behavioral Radar */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                    <span>Persona Behavioral Comparison</span>
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Compare key behavioral metrics across personas (calculated from customer interaction data)
                  </p>
                </div>
                {togetherApiKey && (
                  <button
                    onClick={() => handleExplainVisualization('radar', { personas, radarData })}
                    disabled={explainVizMutation.isPending && explainViz === 'radar'}
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{explainVizMutation.isPending && explainViz === 'radar' ? 'Explaining...' : 'Explain with AI'}</span>
                  </button>
                )}
              </div>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e5e7eb" />
                  <PolarAngleAxis dataKey="metric" stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <PolarRadiusAxis stroke="#6b7280" angle={90} domain={[0, 100]} style={{ fontSize: '10px' }} />
                  {vizData.persona_characteristics?.map((p: any, idx: number) => (
                    <Radar
                      key={idx}
                      name={p.persona}
                      dataKey={p.persona}
                      stroke={COLORS[idx % 3]}
                      strokeWidth={2}
                      fill={COLORS[idx % 3]}
                      fillOpacity={0.6}
                      isAnimationActive={true}
                      animationDuration={1500}
                      animationBegin={idx * 300}
                    />
                  ))}
                  <Legend />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {executeMutation.isPending && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="card-body">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <div>
                <div className="text-blue-900 font-semibold">Running K-Prototypes Clustering</div>
                <div className="text-blue-700 text-sm">Analyzing {nClusters} clusters with gamma={gamma}... This may take 30-60 seconds.</div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {!executeMutation.isPending && !results && !executeMutation.isError && (
        <div className="card bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
          <div className="card-body text-center py-12">
            <Users className="w-16 h-16 text-blue-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">✨ Ready to Discover Customer Segments</h3>
            <p className="text-gray-700 mb-4">
              Configure your clustering parameters above and click <strong>"Run K-Prototypes Clustering"</strong> to analyze 5,000 customers.
            </p>
            <p className="text-sm text-gray-600 mb-4">
              ⏱️ Takes ~30-60 seconds · 🎯 Generates 4-5 actionable personas · 📊 Analyzes 30+ behavioral signals
            </p>
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-blue-300 rounded-lg text-sm text-gray-700">
              <span className="font-semibold">💡 Tip:</span>
              After clustering, visit "Macro Dashboard" to explore segments in detail
            </div>
          </div>
        </div>
      )}

      {executeMutation.isError && (
        <div className="card bg-red-50 border-red-200">
          <div className="card-body">
            <div className="flex items-center space-x-3">
              <AlertCircle className="w-8 h-8 text-red-600" />
              <div>
                <div className="text-red-900 font-semibold">Error Running Clustering</div>
                <div className="text-red-700 text-sm">Please check the backend logs and try again.</div>
              </div>
            </div>
          </div>
        </div>
      )}
        </>
      )}

      {/* AI Explanation Modal */}
      {explainViz && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Sparkles className="w-6 h-6 text-white" />
                <h3 className="text-xl font-bold text-white">AI Insights</h3>
              </div>
              <button
                onClick={() => setExplainViz(null)}
                className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
              {explainVizMutation.isPending ? (
                <div className="flex flex-col items-center justify-center py-12 space-y-4">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                  <p className="text-gray-600">Analyzing visualization and generating insights...</p>
                </div>
              ) : explainVizMutation.isError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
                    <div>
                      <h4 className="text-red-900 font-semibold">Failed to generate explanation</h4>
                      <p className="text-red-700 text-sm mt-1">
                        {explainVizMutation.error?.message || 'Please try again or check your API configuration.'}
                      </p>
                    </div>
                  </div>
                </div>
              ) : explainVizMutation.data ? (
                <div 
                  className="ai-explanation max-w-none text-gray-800"
                  dangerouslySetInnerHTML={{ __html: explainVizMutation.data }}
                />
              ) : (
                <div className="text-gray-500 text-center py-8">
                  Click "Explain with AI" to generate insights for this visualization.
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3 border-t border-gray-200">
              <button
                onClick={() => setExplainViz(null)}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium transition-colors"
              >
                Close
              </button>
              {explainVizMutation.data && (
                <button
                  onClick={() => {
                    const vizType = explainViz;
                    const data = vizType === 'revenue' ? { personas, revenueData } : {};
                    explainVizMutation.mutate({ vizType, vizData: data, personas });
                  }}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors flex items-center space-x-2"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Regenerate</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

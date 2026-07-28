import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, Users, TrendingUp, BarChart3, AlertCircle, CheckCircle2, Download, DollarSign, Shield, Calendar, PieChart, Activity } from 'lucide-react';
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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

const COLORS = ['#059669', '#2563eb', '#ea580c'];
const COLOR_MAP: Record<string, string> = {
  '🏕️ First-Time Camper': '#059669',
  '👨‍👩‍👧‍👦 Family Socializer': '#2563eb',
  '⛰️ Seasoned Pro': '#ea580c'
};

export default function AcademyAgentAEnhanced() {
  const [nClusters, setNClusters] = useState(3);
  const [gamma, setGamma] = useState(0.5);
  const queryClient = useQueryClient();

  // ✨ Check for cached results on mount to persist session across navigation
  const [resultsEnabled, setResultsEnabled] = useState(false);

  // Check for cached data on mount and enable results query if data exists
  React.useEffect(() => {
    const checkCache = () => {
      const cachedResults = queryClient.getQueryData(['academy-agent-a-results']);
      console.log('[Agent A Enhanced] Checking cache on mount:', cachedResults ? 'FOUND' : 'NOT FOUND');
      if (cachedResults) {
        console.log('[Agent A Enhanced] ✅ Cached results found - enabling results query');
        setResultsEnabled(true);
      } else {
        console.log('[Agent A Enhanced] ⚠️ No cached results found');
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
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n_clusters: nClusters, gamma })
      });
      if (!response.ok) throw new Error('Failed to execute Agent A');
      return response.json();
    },
    onSuccess: async (data) => {
      console.log('[Agent A Enhanced] onSuccess callback - enabling results query');
      // Enable results query after successful execution
      setResultsEnabled(true);
      
      // Force an immediate fetch of the results
      console.log('[Agent A Enhanced] Forcing results fetch...');
      try {
        const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/results`);
        if (response.ok) {
          const resultsData = await response.json();
          const results = resultsData.results || resultsData;
          queryClient.setQueryData(['academy-agent-a-results'], results);
          console.log('[Agent A Enhanced] Results cached successfully:', results);
        }
      } catch (error) {
        console.error('[Agent A Enhanced] Error fetching results:', error);
      }
    }
  });

  // Query to get results - persists across navigation
  const resultsQuery = useQuery({
    queryKey: ['academy-agent-a-results'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/results`);
      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to fetch results');
      }
      const data = await response.json();
      return data.results || data;
    },
    staleTime: Infinity, // Results persist until explicitly cleared
    gcTime: Infinity, // Keep in cache indefinitely
    refetchOnMount: false, // Don't refetch on mount - use cached data
    refetchOnWindowFocus: false, // Don't refetch when window regains focus
    enabled: resultsEnabled,
    retry: 1
  });

  const results = resultsQuery.data;
  const personas = results?.personas || {};
  const vizData = results?.visualization_data || {};

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

  // Calculate summary metrics
  const totalRevenue: number = Object.values(personas).reduce(
    (sum: number, p: any) => sum + (p.revenue_metrics?.total_revenue_12mo || 0),
    0
  ) as number;
  const totalProfit: number = Object.values(personas).reduce(
    (sum: number, p: any) => sum + (p.revenue_metrics?.estimated_profit || 0),
    0
  ) as number;
  const avgMargin: number = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;

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
            <div>
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
            <div>
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
            disabled={executeMutation.isPending}
            className="mt-6 w-full btn-primary flex items-center justify-center space-x-2"
          >
            <Play className="w-5 h-5" />
            <span>{executeMutation.isPending ? 'Running K-Prototypes...' : 'Run K-Prototypes Clustering'}</span>
          </button>
        </div>
      </div>

      {/* Executive Summary */}
      {results && (
        <>
          <div className="card bg-gradient-to-br from-green-50 to-blue-50">
            <div className="card-body">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center space-x-2">
                <PieChart className="w-7 h-7 text-green-600" />
                <span>Executive Summary</span>
              </h2>
              
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
                    {results.total_customers?.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">{Object.keys(personas).length} personas</div>
                </div>
                
                <div className="bg-white rounded-lg p-5 shadow-sm border border-purple-200">
                  <div className="text-gray-600 text-sm font-medium mb-1">Model Accuracy</div>
                  <div className="text-3xl font-bold text-purple-600">
                    {results.validation?.accuracy?.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {results.validation?.accuracy > 85 ? '✅ Excellent' : results.validation?.accuracy > 60 ? '✓ Good' : '⚠️ Needs improvement'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Revenue Chart */}
          <div className="card">
            <div className="card-header">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                <DollarSign className="w-6 h-6 text-green-600" />
                <span>💰 Revenue by Persona</span>
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Understand which personas drive the most revenue and profit (calculated from actual purchase data)
              </p>
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
              <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                <Shield className="w-6 h-6 text-blue-600" />
                <span>🎯 Assignment Confidence</span>
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                How confident are we in each persona assignment? Higher is better (based on clustering distance metrics)
              </p>
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
              <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                <Calendar className="w-6 h-6 text-purple-600" />
                <span>📅 Seasonal Customer Acquisition</span>
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                When do different personas join? Plan your marketing campaigns accordingly (from registration dates)
              </p>
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
                <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
                  <CheckCircle2 className="w-7 h-7 text-green-600" />
                  <span>Validation Results</span>
                </h2>
                
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

          {/* Persona Cards */}
          <div className="card-grid-3">
            {Object.values(personas).map((persona: any, idx) => (
              <div
                key={idx}
                className="card hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 h-full flex flex-col"
              >
                <div className="card-body flex-1 flex flex-col">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{persona.persona_name}</h3>
                  <p className="text-gray-600 text-sm mb-4">{persona.description}</p>
                  
                  <div className="space-y-3 flex-1 flex flex-col">
                    <div className="flex items-center justify-between pb-3 border-b border-gray-200">
                      <span className="text-gray-600 text-sm font-medium">Size:</span>
                      <span className="text-gray-900 font-bold">
                        {persona.size?.toLocaleString()} ({persona.percentage}%)
                      </span>
                    </div>
                    
                    <div className="pt-3 flex-1 flex flex-col">
                      <div className="text-sm font-semibold text-gray-900 mb-3">Key Behaviors</div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Search Specificity:</span>
                          <span className="text-gray-900 font-semibold">{persona.characteristics?.avg_search_specificity?.toFixed(1)}/5.0</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Spec Expansion:</span>
                          <span className="text-gray-900 font-semibold">
                            {(persona.characteristics?.avg_spec_expansion_rate * 100)?.toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Bundle Affinity:</span>
                          <span className="text-gray-900 font-semibold">
                            {(persona.characteristics?.avg_bundle_affinity * 100)?.toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Avg Spend/Year:</span>
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
                    
                    <div className="pt-3 border-t border-gray-200 mt-auto">
                      <div className="text-sm font-semibold text-gray-900 mb-2">Product Preferences</div>
                      <div className="space-y-2">
                        <div className="text-sm">
                          <span className="text-green-600 font-semibold">✅ Loves:</span>
                          <div className="text-gray-700 mt-1 text-xs line-clamp-2">
                            {persona.product_preferences?.loves?.join(', ')}
                          </div>
                        </div>
                        {persona.product_preferences?.avoids && (
                          <div className="text-sm mt-2">
                            <span className="text-red-600 font-semibold">❌ Avoids:</span>
                            <div className="text-gray-700 mt-1 text-xs line-clamp-2">
                              {persona.product_preferences.avoids.join(', ')}
                            </div>
                          </div>
                        )}
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
              <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                <BarChart3 className="w-6 h-6 text-blue-600" />
                <span>Customer Distribution by Persona</span>
              </h2>
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
              <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                <TrendingUp className="w-6 h-6 text-purple-600" />
                <span>Persona Behavioral Comparison</span>
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Compare key behavioral metrics across personas (calculated from customer interaction data)
              </p>
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
                      fill={COLORS[idx % 3]}
                      fillOpacity={0.3}
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
                <div className="text-blue-700 text-sm">Analyzing 5,000 customers with mixed data types...</div>
              </div>
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
    </div>
  );
}

import { useMutation, useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { useState } from 'react';
import {
  BarChart, Bar, PieChart, Pie, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import ClusterTreeMap from '../../components/visualizations/ClusterTreeMap';
import CustomerFunnelChart from '../../components/visualizations/CustomerFunnelChart';
import ClusterDrillDownModal from '../../components/ClusterDrillDownModal';
import { exportToPNG, exportToCSV, exportToJSON } from '../../utils/exportCharts';

export default function BankingAgentA() {
  const [nClusters, setNClusters] = useState(0); // 0 = Auto
  const [useAI, setUseAI] = useState(false); // Toggle AI strategies
  const [useCache, setUseCache] = useState(true); // Use cached results
  const [selectedCluster, setSelectedCluster] = useState<any>(null);
  const [showDrillDown, setShowDrillDown] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false)

  // Execute Agent A
  const executeMutation = useMutation({
    mutationFn: async (signal?: AbortSignal) => {
      const res = await fetch('http://localhost:8002/api/banking/agent_a/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          n_clusters: nClusters,
          use_cache: useCache
        }),
        signal
      });
      if (!res.ok) throw new Error('Failed to execute Agent A');
      return res.json();
    }
  });

  const handleCancel = () => {
    executeMutation.reset();
  };

  // Get results
  const { data: apiData, refetch } = useQuery({
    queryKey: ['banking-agent-a-results'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8002/api/banking/agent_a/results');
      if (!res.ok) throw new Error('No results available');
      return res.json();
    },
    enabled: false
  });

  const results = apiData?.results;

  const handleExecute = async () => {
    await executeMutation.mutateAsync();
    refetch();
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">👥 Agent A: Banking Persona Builder</h1>
        <p className="text-gray-400">Detect life events, intent signals, and build dynamic customer personas</p>
      </div>

      {/* Configuration */}
      <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
        <h2 className="text-xl font-bold text-white mb-4">Configuration</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Number of Clusters: {nClusters === 0 ? 'Auto (AI Optimized)' : nClusters}
            </label>
            <input
              type="range"
              min="0"
              max="10"
              value={nClusters}
              onChange={(e) => setNClusters(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Auto</span>
              <span>3</span>
              <span>5</span>
              <span>10</span>
            </div>
            {nClusters === 0 && (
              <div className="mt-2 text-xs text-blue-400 bg-blue-900/20 border border-blue-500/30 rounded p-2">
                🤖 AI will analyze your data and automatically select the optimal number of clusters using Silhouette Score
              </div>
            )}
          </div>

          {/* AI Strategies Info */}
          <div className="p-4 bg-blue-900/20 rounded-lg border border-blue-500/20">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🤖</span>
              <div>
                <div className="text-white font-medium">AI Strategy Generation</div>
                <div className="text-xs text-gray-400 mt-1">
                  ✨ Always Enabled - Generates personalized strategies using Together AI
                </div>
              </div>
            </div>
          </div>

          {/* Caching Toggle */}
          <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-purple-500/20">
            <div className="flex-1">
              <div className="text-white font-medium">Use Cached Results</div>
              <div className="text-xs text-gray-400 mt-1">
                {useCache ? '💾 Enabled - Instant if already analyzed' : '🔄 Disabled - Always recompute'}
              </div>
            </div>
            <button
              onClick={() => setUseCache(!useCache)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                useCache ? 'bg-green-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  useCache ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleExecute}
              disabled={executeMutation.isPending}
              className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg font-bold transition-all disabled:opacity-50"
            >
              {executeMutation.isPending ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Executing...
                </span>
              ) : (
                '🚀 Execute Agent A'
              )}
            </button>

            {executeMutation.isPending && (
              <button
                onClick={handleCancel}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold transition-all"
              >
                ✕ Cancel
              </button>
            )}
          </div>
        </div>

        {executeMutation.isSuccess && (
          <div className="mt-4 bg-green-900/20 border border-green-500/30 rounded-lg p-4">
            <div className="text-green-400 font-semibold">✅ Agent A Executed Successfully!</div>
            <p className="text-gray-300 text-sm mt-1">
              Generated {executeMutation.data?.personas_count} personas
            </p>
          </div>
        )}

        {executeMutation.isError && (
          <div className="mt-4 bg-red-900/20 border border-red-500/30 rounded-lg p-4">
            <div className="text-red-400 font-semibold">❌ Execution Failed</div>
            <p className="text-gray-300 text-sm">{(executeMutation.error as Error).message}</p>
          </div>
        )}
      </div>

      {/* Results */}
      {results && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Summary */}
          <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold text-white mb-4">📊 Summary</h2>
            <div className="grid md:grid-cols-5 gap-4">
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-gray-400 text-sm">Total Customers</div>
                <div className="text-2xl font-bold text-white">
                  {results?.summary?.total_customers || 0}
                </div>
              </div>
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-gray-400 text-sm">High Intent (&gt;70%)</div>
                <div className="text-2xl font-bold text-green-400">
                  {results?.summary?.high_intent_customers || 0}
                </div>
              </div>
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-gray-400 text-sm">Life Events</div>
                <div className="text-2xl font-bold text-yellow-400">
                  {results?.personas ? Object.values(results.personas).reduce((sum: number, p: any) => sum + (p.size || 0), 0) : 0}
                </div>
              </div>
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-gray-400 text-sm">Avg Intent Score</div>
                <div className="text-2xl font-bold text-blue-400">
                  {results?.summary?.avg_intent ? (results.summary.avg_intent * 100).toFixed(0) + '%' : '0%'}
                </div>
              </div>
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-gray-400 text-sm">High Engagement</div>
                <div className="text-2xl font-bold text-purple-400">
                  {results?.personas ? Object.values(results.personas).filter((p: any) => (p.avg_engagement || 0) > 10).length : 0}
                </div>
              </div>
            </div>
          </div>

          {/* Visualizations */}
          {results.visualization_data && (
            <div className="space-y-6 mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">📊 Cluster Analysis</h2>
              
              {/* Row 1: Cluster Scatter & Distribution */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Enhanced Cluster Visualization */}
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                  <h3 className="text-lg font-bold text-white mb-4">🎯 Customer Segment Map</h3>
                  <div className="text-xs text-gray-300 mb-3">
                    Each bubble represents a customer segment. Hover for details!
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                      <XAxis 
                        dataKey="x" 
                        name="Intent Score" 
                        stroke="#9ca3af"
                        label={{ value: 'Intent Score →', position: 'insideBottom', offset: -10, fill: '#9ca3af' }}
                      />
                      <YAxis 
                        dataKey="y" 
                        name="Engagement" 
                        stroke="#9ca3af"
                        label={{ value: '← Engagement Level', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                      />
                      <Tooltip 
                        cursor={{ strokeDasharray: '3 3' }} 
                        contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', padding: '12px' }}
                        formatter={(value: any, name: any, props: any) => {
                          if (name === 'Intent Score') return [`${value.toFixed(1)}%`, 'Intent'];
                          if (name === 'Engagement') return [`${value.toFixed(1)} logins/month`, 'Engagement'];
                          return [value, name];
                        }}
                        labelFormatter={(label: any, payload: any) => {
                          if (payload && payload[0]) {
                            return `${payload[0].payload.cluster_name || 'Segment'} (${payload[0].payload.size} customers)`;
                          }
                          return label;
                        }}
                      />
                      <Legend 
                        wrapperStyle={{ paddingTop: '10px' }}
                        iconType="circle"
                      />
                      {[...new Set(results.visualization_data.cluster_scatter_2d.map((d: any) => d.cluster))].map((clusterId: any, idx: number) => {
                        const clusterData = results.visualization_data.cluster_scatter_2d.find((d: any) => d.cluster === clusterId);
                        const clusterName = clusterData?.cluster_name || `Cluster ${clusterId}`;
                        const colors = ['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b'];
                        return (
                          <Scatter
                            key={clusterId}
                            name={clusterName}
                            data={results.visualization_data.cluster_scatter_2d.filter((d: any) => d.cluster === clusterId)}
                            fill={colors[idx % 5]}
                            shape="circle"
                            isAnimationActive={true}
                          >
                            {results.visualization_data.cluster_scatter_2d
                              .filter((d: any) => d.cluster === clusterId)
                              .map((entry: any, index: number) => (
                                <Cell 
                                  key={`cell-${index}`} 
                                  fill={colors[idx % 5]}
                                  fillOpacity={0.8}
                                  stroke={colors[idx % 5]}
                                  strokeWidth={2}
                                  r={Math.max(8, Math.min(entry.size / 5, 20))}
                                />
                              ))
                            }
                          </Scatter>
                        );
                      })}
                    </ScatterChart>
                  </ResponsiveContainer>
                  <div className="text-xs text-gray-400 mt-2">
                    💡 Bubble size = segment size | Position shows Intent (x-axis) vs Engagement (y-axis)
                  </div>
                </div>

                {/* Cluster Distribution */}
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                  <h3 className="text-lg font-bold text-white mb-4">📊 Cluster Distribution</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart 
                      data={results.personas ? Object.values(results.personas).map((p: any) => ({
                        name: p.cluster_name || `Cluster ${p.cluster_id}`,
                        count: p.size,
                        clusterId: p.cluster_id
                      })) : []}
                      margin={{ bottom: 60, left: 10, right: 10, top: 10 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis 
                        dataKey="name" 
                        stroke="#9ca3af"
                        angle={-15}
                        textAnchor="end"
                        height={80}
                        interval={0}
                        style={{ fontSize: '11px' }}
                      />
                      <YAxis stroke="#9ca3af" label={{ value: 'Customers', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                        formatter={(value: any) => [`${value} customers`, 'Count']}
                      />
                      <Bar dataKey="count" fill="#8b5cf6" radius={[8, 8, 0, 0]}>
                        {results.personas && Object.values(results.personas).map((_: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b'][index % 5]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="text-xs text-gray-400 mt-2">
                    Total Clusters: {results.personas ? Object.keys(results.personas).length : 0} | 
                    Click on bars to see different segments
                  </div>
                </div>
              </div>

              {/* Row 2: Engagement & Intent */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Engagement Distribution */}
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                  <h3 className="text-lg font-bold text-white mb-4">⚡ Engagement Levels</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={Object.entries(results.visualization_data.engagement_distribution).map(([level, count]) => ({
                          name: level,
                          value: count
                        }))}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label
                      >
                        {Object.keys(results.visualization_data.engagement_distribution).map((_, index) => (
                          <Cell key={`cell-${index}`} fill={['#10b981', '#f59e0b', '#ef4444'][index % 3]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Intent Distribution */}
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                  <h3 className="text-lg font-bold text-white mb-4">🎯 Intent Levels</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={Object.entries(results.visualization_data.intent_distribution).map(([level, count]) => ({
                          name: level,
                          value: count
                        }))}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label
                      >
                        {Object.keys(results.visualization_data.intent_distribution).map((_, index) => (
                          <Cell key={`cell-${index}`} fill={['#8b5cf6', '#ec4899', '#3b82f6'][index % 3]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Clustering Metrics */}
              <div className="bg-blue-900/20 rounded-xl p-6 border border-blue-500/20">
                <h3 className="text-lg font-bold text-white mb-3">📈 Clustering Quality Metrics</h3>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-gray-400">Silhouette Score</div>
                    <div className="text-2xl font-bold text-green-400">{results.clustering_metrics?.silhouette_score?.toFixed(3) || 'N/A'}</div>
                    <div className="text-xs text-gray-500">Higher is better (0-1)</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">Davies-Bouldin Score</div>
                    <div className="text-2xl font-bold text-yellow-400">{results.clustering_metrics?.davies_bouldin_score?.toFixed(3) || 'N/A'}</div>
                    <div className="text-xs text-gray-500">Lower is better</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">Calinski-Harabasz Score</div>
                    <div className="text-2xl font-bold text-purple-400">{results.clustering_metrics?.calinski_harabasz_score?.toFixed(1) || 'N/A'}</div>
                    <div className="text-xs text-gray-500">Higher is better</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Personas */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-4">👥 Cluster Personas ({Object.keys(results.personas || {}).length} total)</h2>
            <p className="text-sm text-gray-400 mb-4">
              These are cluster-level summaries. Each cluster represents a group of similar customers based on behavioral patterns.
              Use Agent B to get recommendations for individual customers.
            </p>
            <div className="grid gap-4">
              {Object.values(results.personas || {}).map((persona: any) => (
                <div key={persona.cluster_id} className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-white">{persona.cluster_name || `Cluster ${persona.cluster_id}`}</h3>
                      <p className="text-sm text-gray-400">{persona.size} customers ({(persona.percentage || 0).toFixed(1)}%)</p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">Avg Intent Score</div>
                      <div className={`text-2xl font-bold ${
                        (persona.avg_intent || 0) > 0.7 ? 'text-green-400' :
                        (persona.avg_intent || 0) > 0.4 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {((persona.avg_intent || 0) * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <div className="text-xs text-gray-400 uppercase mb-1">Avg Engagement</div>
                      <div className="text-white font-semibold">{(persona.avg_engagement || 0).toFixed(1)} logins/mo</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400 uppercase mb-1">Channel</div>
                      <div className="text-white font-semibold">{persona.dominant_channel || 'mobile'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400 uppercase mb-1">Value Tier</div>
                      <div className="text-white font-semibold">{persona.value_tier || 'silver'}</div>
                    </div>
                  </div>

                  {persona.life_events && persona.life_events.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-purple-500/20">
                      <div className="text-xs text-gray-400 uppercase mb-2">Life Events</div>
                      <div className="flex flex-wrap gap-2">
                        {persona.life_events.map((event: string, idx: number) => (
                          <span key={idx} className="bg-yellow-900/30 text-yellow-300 px-3 py-1 rounded-full text-sm">
                            {event}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {Object.keys(results.personas || {}).length > 10 && (
              <div className="text-center mt-4 text-gray-400 text-sm">
                Showing 10 of {Object.keys(results.personas || {}).length} personas
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Info */}
      {!results && !executeMutation.isPending && (
        <div className="bg-blue-900/20 backdrop-blur-sm rounded-xl p-6 border border-blue-500/20">
          <h3 className="text-lg font-bold text-white mb-3">💡 About Agent A</h3>
          <ul className="text-sm text-gray-300 space-y-2">
            <li>• <strong>Engagement Signals:</strong> Mobile app usage, web visits, branch visits, call center interactions</li>
            <li>• <strong>Intent Signals:</strong> Product page views, application clicks, calculator usage</li>
            <li>• <strong>Life Events:</strong> Relocation, new job, new baby, income changes, spending spikes</li>
            <li>• <strong>Financial Profile:</strong> Income level, credit utilization, account balances, transaction patterns</li>
            <li>• <strong>Dynamic Personas:</strong> AI-powered clustering with Together AI for recommendations</li>
          </ul>
        </div>
      )}
    </div>
  );
}

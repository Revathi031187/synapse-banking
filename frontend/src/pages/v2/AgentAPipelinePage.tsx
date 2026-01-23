import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import ClusterScatterPlot from '../../components/visualizations/ClusterScatterPlot';
import ClusterSizeChart from '../../components/visualizations/ClusterSizeChart';
import ElbowCurveChart from '../../components/visualizations/ElbowCurveChart';

const AgentAPipelinePage = () => {
  const queryClient = useQueryClient();
  const [clusteringAlgo, setClusteringAlgo] = useState('kmeans');
  const [nClusters, setNClusters] = useState<number | null>(null);
  const [showResults, setShowResults] = useState(false);

  // Check if data is loaded
  const { data: status } = useQuery({
    queryKey: ['v2-status'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8001/api/v2/status');
      return response.json();
    },
  });

  // Execute Agent A
  const executeMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('http://localhost:8001/api/v2/agent_a/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clustering_algorithm: clusteringAlgo,
          n_clusters: nClusters
        }),
      });
      if (!response.ok) throw new Error('Failed to execute Agent A');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2-status'] });
      queryClient.invalidateQueries({ queryKey: ['agent-a-results'] });
      setShowResults(true);
    },
  });

  // Get results
  const { data: results, isLoading: resultsLoading } = useQuery({
    queryKey: ['agent-a-results'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8001/api/v2/agent_a/results');
      if (!response.ok) return null;
      const data = await response.json();
      return data; // Simple structure: {status, personas, clustering, visualizations}
    },
    enabled: status?.pipeline_status?.agent_a_complete || showResults,
  });

  const dataLoaded = status?.pipeline_status?.data_loaded;
  const agentAComplete = status?.pipeline_status?.agent_a_complete;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">🤖 Agent A: Persona Builder</h1>
        <p className="text-gray-400">
          Advanced ML clustering and AI-powered persona generation
        </p>
      </div>

      {/* Configuration Panel */}
      {!agentAComplete && (
        <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20 mb-8">
          <h2 className="text-xl font-bold text-white mb-4">Configuration</h2>
          
          {!dataLoaded ? (
            <div className="text-center py-8">
              <p className="text-yellow-400 mb-4">⚠️ No data loaded. Please load a dataset first.</p>
              <a
                href="/data-loader"
                className="inline-block bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                Go to Data Loader
              </a>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Algorithm Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Clustering Algorithm
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { value: 'kmeans', label: 'K-Means', desc: 'Fast, requires K specification', icon: '🎯' },
                    { value: 'dbscan', label: 'DBSCAN', desc: 'Density-based, finds outliers', icon: '🔍' },
                    { value: 'hierarchical', label: 'Hierarchical', desc: 'Tree-based clustering', icon: '🌳' }
                  ].map((algo) => (
                    <button
                      key={algo.value}
                      onClick={() => setClusteringAlgo(algo.value)}
                      className={`p-4 rounded-lg border-2 transition-all text-left ${
                        clusteringAlgo === algo.value
                          ? 'border-purple-500 bg-purple-900/30'
                          : 'border-purple-500/20 bg-white/5 hover:border-purple-500/50'
                      }`}
                    >
                      <div className="text-2xl mb-2">{algo.icon}</div>
                      <div className="font-medium text-white mb-1">{algo.label}</div>
                      <div className="text-xs text-gray-400">{algo.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Number of Clusters */}
              {clusteringAlgo !== 'dbscan' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Number of Clusters (leave empty for auto-detection)
                  </label>
                  <input
                    type="number"
                    min="2"
                    max="10"
                    value={nClusters || ''}
                    onChange={(e) => setNClusters(e.target.value ? parseInt(e.target.value) : null)}
                    placeholder="Auto-detect optimal K"
                    className="w-full bg-white/10 border border-purple-500/30 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  />
                </div>
              )}

              {/* Execute Button */}
              <button
                onClick={() => executeMutation.mutate()}
                disabled={executeMutation.isPending}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-4 rounded-lg font-bold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {executeMutation.isPending ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Executing Agent A...
                  </span>
                ) : (
                  '🚀 Execute Agent A'
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Execution Steps (when running) */}
      <AnimatePresence>
        {executeMutation.isPending && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20 mb-8"
          >
            <h3 className="text-lg font-bold text-white mb-4">Pipeline Execution</h3>
            <div className="space-y-3">
              {[
                '📊 Preprocessing data...',
                '🔧 Engineering features (RFM + behavioral)...',
                '🔍 Finding optimal clusters...',
                '🎯 Performing clustering...',
                '👥 Generating personas with AI...',
                '📈 Preparing visualizations...'
              ].map((step, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.5 }}
                  className="flex items-center space-x-3 text-gray-300"
                >
                  <div className="animate-pulse">⏳</div>
                  <span>{step}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      {(agentAComplete || showResults) && results && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <MetricCard
              label="Personas Created"
              value={results.personas?.n_personas || 0}
              icon="👥"
              color="purple"
              tooltip="Number of distinct customer personas identified through clustering"
            />
            <MetricCard
              label="Silhouette Score"
              value={results.clustering?.metrics?.silhouette_score?.toFixed(3) || 'N/A'}
              icon="📊"
              color="green"
              tooltip="Measures cluster separation quality (Range: -1 to 1). >0.3 = Good, >0.5 = Excellent"
              badge={
                parseFloat(results.clustering?.metrics?.silhouette_score || '0') > 0.5 
                  ? { text: 'Excellent', color: 'green' } 
                  : parseFloat(results.clustering?.metrics?.silhouette_score || '0') > 0.3 
                    ? { text: 'Good', color: 'blue' } 
                    : { text: 'Fair', color: 'yellow' }
              }
            />
            <MetricCard
              label="Davies-Bouldin"
              value={results.clustering?.metrics?.davies_bouldin_score?.toFixed(3) || 'N/A'}
              icon="📉"
              color="blue"
              tooltip="Cluster overlap metric. Lower is better. <1.0 = Excellent separation"
              badge={
                parseFloat(results.clustering?.metrics?.davies_bouldin_score || '999') < 1.0 
                  ? { text: 'Excellent', color: 'green' } 
                  : parseFloat(results.clustering?.metrics?.davies_bouldin_score || '999') < 2.0 
                    ? { text: 'Good', color: 'blue' } 
                    : { text: 'Fair', color: 'yellow' }
              }
            />
            <MetricCard
              label="Calinski-Harabasz"
              value={results.clustering?.metrics?.calinski_harabasz_score?.toFixed(0) || 'N/A'}
              icon="📈"
              color="pink"
              tooltip="Cluster density ratio. Higher is better. Indicates well-defined clusters"
              badge={
                parseFloat(results.clustering?.metrics?.calinski_harabasz_score || '0') > 100 
                  ? { text: 'Excellent', color: 'green' } 
                  : parseFloat(results.clustering?.metrics?.calinski_harabasz_score || '0') > 20 
                    ? { text: 'Good', color: 'blue' } 
                    : { text: 'Fair', color: 'yellow' }
              }
            />
            <MetricCard
              label="Features Used"
              value={results.feature_summary?.total_features || 0}
              icon="🔧"
              color="purple"
              tooltip={`Features: ${results.feature_summary?.feature_list?.join(', ') || 'RFM + Behavioral metrics'}`}
            />
          </div>

          {/* AI Quality Analysis */}
          {results.clustering?.ai_explanation && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/40"
            >
              <div className="flex items-start space-x-4">
                <div className="text-4xl">🤖</div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-white mb-2 flex items-center space-x-2">
                    <span>AI Analysis</span>
                    <span className="text-xs bg-purple-500/30 px-2 py-1 rounded border border-purple-500/50">Powered by Together AI</span>
                  </h3>
                  <p className="text-gray-200 leading-relaxed">
                    {results.clustering.ai_explanation}
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Info Panel */}
          <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 backdrop-blur-sm rounded-xl p-6 border border-blue-500/30">
            <div className="flex items-start space-x-4">
              <div className="text-4xl">💡</div>
              <div>
                <h3 className="text-lg font-bold text-white mb-2">Understanding Your Clustering Quality</h3>
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="font-semibold text-green-400 mb-1">🎯 Silhouette Score</div>
                    <p className="text-gray-300">Measures how similar each customer is to their own persona vs. others. Higher = better separated groups.</p>
                  </div>
                  <div>
                    <div className="font-semibold text-blue-400 mb-1">📉 Davies-Bouldin Index</div>
                    <p className="text-gray-300">Evaluates cluster overlap. Lower = more distinct personas with less confusion.</p>
                  </div>
                  <div>
                    <div className="font-semibold text-pink-400 mb-1">📈 Calinski-Harabasz Score</div>
                    <p className="text-gray-300">Ratio of between-cluster to within-cluster variance. Higher = tighter, more cohesive personas.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Visualizations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ClusterScatterPlot
              data={results.visualizations?.scatter_plot_pca}
              title="PCA Projection (2D)"
            />
            <ClusterScatterPlot
              data={results.visualizations?.scatter_plot_tsne}
              title="t-SNE Projection (2D)"
            />
          </div>

          <ClusterSizeChart data={results.visualizations?.cluster_sizes} />

          {/* Persona Cards */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Generated Personas</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {Object.values(results.personas?.personas || {}).map((persona: any) => (
                <PersonaCard key={persona.id} persona={persona} />
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: string;
  color: string;
  tooltip?: string;
  badge?: { text: string; color: string };
}

const MetricCard = ({ label, value, icon, color, tooltip, badge }: MetricCardProps) => {
  const [showTooltip, setShowTooltip] = useState(false);
  
  const colorClasses = {
    purple: 'from-purple-500 to-pink-500',
    green: 'from-green-500 to-emerald-500',
    blue: 'from-blue-500 to-cyan-500',
    pink: 'from-pink-500 to-rose-500'
  };

  const badgeColors = {
    green: 'bg-green-500/20 text-green-300 border-green-500/30',
    blue: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    yellow: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
  };

  return (
    <div 
      className="bg-white/5 rounded-xl p-6 border border-purple-500/20 hover:border-purple-500/40 transition-all relative group cursor-pointer"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-3xl">{icon}</span>
        <div className={`text-2xl font-bold bg-gradient-to-r ${colorClasses[color as keyof typeof colorClasses]} bg-clip-text text-transparent`}>
          {value}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-400 flex items-center space-x-2">
          <span>{label}</span>
          {tooltip && (
            <span className="text-gray-500 text-xs">ℹ️</span>
          )}
        </div>
        {badge && (
          <span className={`text-xs px-2 py-1 rounded border ${badgeColors[badge.color as keyof typeof badgeColors]}`}>
            {badge.text}
          </span>
        )}
      </div>
      
      {/* Tooltip */}
      {tooltip && showTooltip && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 bg-gray-900 border border-purple-500/30 rounded-lg p-3 shadow-xl"
        >
          <div className="text-xs text-gray-200 leading-relaxed">{tooltip}</div>
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-8 border-transparent border-t-gray-900"></div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

interface PersonaCardProps {
  persona: any;
}

const PersonaCard = ({ persona }: PersonaCardProps) => {
  return (
    <div className="bg-gradient-to-br from-white/5 to-white/10 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20 hover:border-purple-500/50 transition-all">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-2xl font-bold text-white mb-1">{persona.name}</h3>
          <div className="text-sm text-purple-300">
            {persona.size} customers ({persona.percentage.toFixed(1)}%)
          </div>
        </div>
        <div className="text-4xl">👤</div>
      </div>

      <p className="text-gray-300 text-sm mb-4 leading-relaxed">
        {persona.description}
      </p>

      {/* AI Insight */}
      {persona.ai_insight && (
        <div className="mb-4 p-3 bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-lg border border-purple-500/30">
          <div className="flex items-start space-x-2">
            <div className="text-lg flex-shrink-0">🤖</div>
            <div>
              <div className="text-xs font-semibold text-purple-300 mb-1">AI Strategic Insight</div>
              <p className="text-xs text-gray-200 leading-relaxed">{persona.ai_insight}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-3 pt-4 border-t border-purple-500/20">
        <div>
          <div className="text-xs text-gray-400 mb-1">Recency</div>
          <div className="text-sm font-bold text-white">{persona.key_metrics.avg_recency_days.toFixed(0)} days</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 mb-1">Frequency</div>
          <div className="text-sm font-bold text-white">{persona.key_metrics.avg_purchases_per_year.toFixed(1)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 mb-1">LTV</div>
          <div className="text-sm font-bold text-green-400">${persona.key_metrics.avg_lifetime_value.toFixed(0)}</div>
        </div>
      </div>
      
      {persona.key_metrics.avg_engagement_events > 0 && (
        <div className="grid grid-cols-3 gap-3 pt-3 mt-3 border-t border-purple-500/10">
          <div>
            <div className="text-xs text-gray-400 mb-1">Events</div>
            <div className="text-sm font-bold text-cyan-400">{persona.key_metrics.avg_engagement_events.toFixed(0)}</div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Engagement</div>
            <div className="text-sm font-bold text-cyan-400">{persona.key_metrics.avg_engagement_minutes.toFixed(1)} min</div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Conv. Rate</div>
            <div className="text-sm font-bold text-cyan-400">{persona.key_metrics.conversion_rate.toFixed(0)}%</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentAPipelinePage;


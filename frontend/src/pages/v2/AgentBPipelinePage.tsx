import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';

const AgentBPipelinePage = () => {
  const queryClient = useQueryClient();
  const [topN, setTopN] = useState(5);
  const [showResults, setShowResults] = useState(false);

  // Check status
  const { data: status } = useQuery({
    queryKey: ['v2-status'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8001/api/v2/status');
      return response.json();
    },
  });

  // Execute Agent B
  const executeMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('http://localhost:8001/api/v2/agent_b/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ top_n: topN }),
      });
      if (!response.ok) throw new Error('Failed to execute Agent B');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2-status'] });
      queryClient.invalidateQueries({ queryKey: ['agent-b-results'] });
      setShowResults(true);
    },
  });

  // Get results
  const { data: results } = useQuery({
    queryKey: ['agent-b-results'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8001/api/v2/agent_b/results');
      if (!response.ok) return null;
      return response.json();
    },
    enabled: status?.pipeline_status?.agent_b_complete || showResults,
  });

  const agentAComplete = status?.pipeline_status?.agent_a_complete;
  const agentBComplete = status?.pipeline_status?.agent_b_complete;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">🎯 Agent B: Product Matchmaker</h1>
        <p className="text-gray-400">
          AI-powered product recommendations with affinity analysis and propensity modeling
        </p>
      </div>

      {/* Configuration Panel */}
      {!agentBComplete && (
        <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20 mb-8">
          <h2 className="text-xl font-bold text-white mb-4">Configuration</h2>
          
          {!agentAComplete ? (
            <div className="text-center py-8">
              <p className="text-yellow-400 mb-4">⚠️ Agent A must be executed first to create personas.</p>
              <a
                href="/agent-a"
                className="inline-block bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                Go to Agent A
              </a>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Top N Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Number of Products to Recommend per Persona
                </label>
                <div className="flex items-center space-x-4">
                  <input
                    type="range"
                    min="3"
                    max="10"
                    value={topN}
                    onChange={(e) => setTopN(parseInt(e.target.value))}
                    className="flex-1 h-2 bg-purple-900 rounded-lg appearance-none cursor-pointer accent-purple-500"
                  />
                  <span className="text-2xl font-bold text-purple-400 w-12 text-center">{topN}</span>
                </div>
              </div>

              {/* Execute Button */}
              <button
                onClick={() => executeMutation.mutate()}
                disabled={executeMutation.isPending}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-6 py-4 rounded-lg font-bold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {executeMutation.isPending ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Executing Agent B...
                  </span>
                ) : (
                  '🚀 Execute Agent B'
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Execution Steps */}
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
                '🔮 Creating product embeddings...',
                '💝 Calculating persona-product affinity...',
                '📊 Training propensity models...',
                '🎯 Generating recommendations...',
                '📈 Preparing visualizations...'
              ].map((step, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.6 }}
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
      {(agentBComplete || showResults) && results && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              label="Personas Matched"
              value={Object.keys(results.results?.recommendations || {}).length}
              icon="👥"
              color="purple"
            />
            <MetricCard
              label="Total Recommendations"
              value={Object.values(results.results?.recommendations || {}).flat().length}
              icon="🎯"
              color="green"
            />
            <MetricCard
              label="Products per Persona"
              value={topN}
              icon="📦"
              color="blue"
            />
          </div>

          {/* Recommendations by Persona */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Product Recommendations by Persona</h2>
            <div className="space-y-6">
              {Object.entries(results.results?.recommendations || {}).map(([personaId, recommendations]: [string, any]) => (
                <PersonaRecommendations
                  key={personaId}
                  personaId={personaId}
                  recommendations={recommendations}
                />
              ))}
            </div>
          </div>

          {/* Affinity Heatmap (if available) */}
          {results.results?.visualizations?.heatmap && (
            <div className="bg-white/5 rounded-xl p-6 border border-purple-500/20">
              <h3 className="text-xl font-bold text-white mb-4">Persona-Product Affinity Heatmap</h3>
              <p className="text-sm text-gray-400 mb-4">
                Shows purchase affinity scores between personas and top products
              </p>
              <AffinityHeatmap data={results.results.visualizations.heatmap} />
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

interface MetricCardProps {
  label: string;
  value: number;
  icon: string;
  color: string;
}

const MetricCard = ({ label, value, icon, color }: MetricCardProps) => {
  const colorClasses = {
    purple: 'from-purple-500 to-pink-500',
    green: 'from-green-500 to-emerald-500',
    blue: 'from-blue-500 to-cyan-500'
  };

  return (
    <div className="bg-white/5 rounded-xl p-6 border border-purple-500/20">
      <div className="flex items-center justify-between mb-2">
        <span className="text-3xl">{icon}</span>
        <div className={`text-2xl font-bold bg-gradient-to-r ${colorClasses[color as keyof typeof colorClasses]} bg-clip-text text-transparent`}>
          {value}
        </div>
      </div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  );
};

interface PersonaRecommendationsProps {
  personaId: string;
  recommendations: any[];
}

const PersonaRecommendations = ({ personaId, recommendations }: PersonaRecommendationsProps) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="bg-gradient-to-br from-white/5 to-white/10 backdrop-blur-sm rounded-xl border border-purple-500/20">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-6 hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center space-x-4">
          <span className="text-3xl">👤</span>
          <div className="text-left">
            <h3 className="text-xl font-bold text-white">Persona {personaId}</h3>
            <p className="text-sm text-gray-400">{recommendations.length} products recommended</p>
          </div>
        </div>
        <svg
          className={`w-6 h-6 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 space-y-3">
              {recommendations.map((rec) => (
                <ProductRecommendationCard key={rec.rank} recommendation={rec} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

interface ProductRecommendationCardProps {
  recommendation: any;
}

const ProductRecommendationCard = ({ recommendation }: ProductRecommendationCardProps) => {
  return (
    <div className="bg-white/5 rounded-lg p-4 border border-purple-500/10 hover:border-purple-500/30 transition-all">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-bold text-purple-400">#{recommendation.rank}</span>
            <h4 className="text-white font-medium">{recommendation.product_name}</h4>
          </div>
          <div className="flex items-center space-x-3 text-sm text-gray-400">
            <span>{recommendation.category}</span>
            <span>•</span>
            <span className="text-green-400 font-medium">${recommendation.price.toFixed(2)}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500 mb-1">Affinity Score</div>
          <div className="text-lg font-bold text-purple-400">
            {(recommendation.affinity_score * 100).toFixed(1)}%
          </div>
        </div>
      </div>
      
      {recommendation.reasoning && (
        <p className="text-sm text-gray-300 mt-3 pt-3 border-t border-purple-500/10 leading-relaxed">
          💡 {recommendation.reasoning}
        </p>
      )}
    </div>
  );
};

interface AffinityHeatmapProps {
  data: {
    persona_names: string[];
    product_names: string[];
    affinity_values: number[][];
  };
}

const AffinityHeatmap = ({ data }: AffinityHeatmapProps) => {
  if (!data || !data.persona_names || data.persona_names.length === 0) {
    return <div className="text-gray-400 text-center py-8">No heatmap data available</div>;
  }

  const maxValue = Math.max(...data.affinity_values.flat());

  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-full">
        <div className="flex">
          {/* Row labels */}
          <div className="flex flex-col justify-end pb-2">
            <div className="h-12"></div>
            {data.persona_names.map((name, idx) => (
              <div
                key={idx}
                className="h-12 flex items-center justify-end pr-3 text-sm text-gray-300"
              >
                {name}
              </div>
            ))}
          </div>

          {/* Heatmap cells */}
          <div className="flex-1">
            {/* Column labels */}
            <div className="flex mb-2">
              {data.product_names.map((name, idx) => (
                <div
                  key={idx}
                  className="flex-1 min-w-[80px] h-12 flex items-end justify-center"
                >
                  <span className="text-xs text-gray-300 transform -rotate-45 origin-bottom-left truncate max-w-[60px]">
                    {name}
                  </span>
                </div>
              ))}
            </div>

            {/* Cells */}
            {data.affinity_values.map((row, rowIdx) => (
              <div key={rowIdx} className="flex">
                {row.map((value, colIdx) => {
                  const intensity = maxValue > 0 ? value / maxValue : 0;
                  const colorValue = Math.round(intensity * 255);
                  const bgColor = `rgb(${139 - colorValue * 0.3}, ${92 + colorValue * 0.5}, ${246 - colorValue * 0.2})`;
                  
                  return (
                    <div
                      key={colIdx}
                      className="flex-1 min-w-[80px] h-12 flex items-center justify-center border border-purple-500/10 relative group"
                      style={{ backgroundColor: bgColor }}
                    >
                      <span className="text-xs font-medium text-white">
                        {(value * 100).toFixed(0)}%
                      </span>
                      
                      {/* Tooltip on hover */}
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                        {data.persona_names[rowIdx]} × {data.product_names[colIdx]}: {(value * 100).toFixed(1)}%
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentBPipelinePage;


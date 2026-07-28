import { motion, AnimatePresence } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import ClusterRadarChart from './visualizations/ClusterRadarChart';

interface ClusterDrillDownModalProps {
  isOpen: boolean;
  onClose: () => void;
  cluster: {
    cluster_id: number;
    cluster_name: string;
    size: number;
    percentage: number;
    avg_intent: number;
    avg_engagement: number;
    avg_income?: number;
    avg_credit_score?: number;
    avg_tenure?: number;
    avg_age?: number;
    avg_recency?: number;
    avg_frequency?: number;
    avg_monetary?: number;
    avg_aov?: number;
    dominant_channel?: string;
    dominant_category?: string;
  } | null;
  customers?: Array<{
    customer_id: string;
    intent_score: number;
    [key: string]: any;
  }>;
  type: 'banking' | 'retail';
}

const ClusterDrillDownModal = ({ isOpen, onClose, cluster, customers = [], type }: ClusterDrillDownModalProps) => {
  if (!cluster) return null;

  // Sample customer distribution by intent
  const intentDistribution = [
    { range: '0-20%', count: customers.filter(c => c.intent_score <= 0.2).length },
    { range: '21-40%', count: customers.filter(c => c.intent_score > 0.2 && c.intent_score <= 0.4).length },
    { range: '41-60%', count: customers.filter(c => c.intent_score > 0.4 && c.intent_score <= 0.6).length },
    { range: '61-80%', count: customers.filter(c => c.intent_score > 0.6 && c.intent_score <= 0.8).length },
    { range: '81-100%', count: customers.filter(c => c.intent_score > 0.8).length },
  ];

  const getIntentColor = (range: string) => {
    if (range.startsWith('81')) return '#10b981';
    if (range.startsWith('61')) return '#3b82f6';
    if (range.startsWith('41')) return '#f59e0b';
    if (range.startsWith('21')) return '#ef4444';
    return '#7f1d1d';
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-4 md:inset-10 lg:inset-20 bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 rounded-2xl border border-purple-500/30 shadow-2xl z-50 overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 px-6 py-4 border-b border-purple-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">{cluster.cluster_name}</h2>
                  <p className="text-gray-300 text-sm mt-1">
                    {cluster.size} customers ({cluster.percentage.toFixed(1)}% of total)
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Stats Grid */}
              <div className="grid md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gradient-to-br from-purple-900/30 to-purple-900/10 rounded-xl p-4 border border-purple-500/20">
                  <div className="text-gray-400 text-sm mb-1">Avg Intent</div>
                  <div className="text-3xl font-bold text-purple-400">
                    {(cluster.avg_intent * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="bg-gradient-to-br from-blue-900/30 to-blue-900/10 rounded-xl p-4 border border-blue-500/20">
                  <div className="text-gray-400 text-sm mb-1">Avg Engagement</div>
                  <div className="text-3xl font-bold text-blue-400">
                    {cluster.avg_engagement.toFixed(1)}
                  </div>
                </div>
                {type === 'banking' && cluster.avg_income && (
                  <div className="bg-gradient-to-br from-green-900/30 to-green-900/10 rounded-xl p-4 border border-green-500/20">
                    <div className="text-gray-400 text-sm mb-1">Avg Income</div>
                    <div className="text-2xl font-bold text-green-400">
                      ${(cluster.avg_income / 1000).toFixed(0)}k
                    </div>
                  </div>
                )}
                {type === 'banking' && cluster.avg_credit_score && (
                  <div className="bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 rounded-xl p-4 border border-yellow-500/20">
                    <div className="text-gray-400 text-sm mb-1">Avg Credit</div>
                    <div className="text-3xl font-bold text-yellow-400">
                      {cluster.avg_credit_score.toFixed(0)}
                    </div>
                  </div>
                )}
                {type === 'retail' && cluster.avg_aov && (
                  <div className="bg-gradient-to-br from-green-900/30 to-green-900/10 rounded-xl p-4 border border-green-500/20">
                    <div className="text-gray-400 text-sm mb-1">Avg Order Value</div>
                    <div className="text-2xl font-bold text-green-400">
                      ${cluster.avg_aov.toFixed(0)}
                    </div>
                  </div>
                )}
              </div>

              {/* Visualizations Grid */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Radar Chart */}
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                  <h3 className="text-lg font-bold text-white mb-4">📊 Segment Profile</h3>
                  <div className="h-[300px]">
                    <ClusterRadarChart selectedCluster={cluster} type={type} />
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Normalized scores showing relative strengths across key metrics
                  </p>
                </div>

                {/* Intent Distribution */}
                <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                  <h3 className="text-lg font-bold text-white mb-4">🎯 Intent Distribution</h3>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={intentDistribution}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis 
                          dataKey="range" 
                          stroke="#9ca3af"
                          style={{ fontSize: '12px' }}
                        />
                        <YAxis 
                          stroke="#9ca3af"
                          label={{ value: 'Customers', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1f2937',
                            border: '1px solid #374151',
                            borderRadius: '8px'
                          }}
                        />
                        <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                          {intentDistribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={getIntentColor(entry.range)} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    How customers in this segment distribute across intent levels
                  </p>
                </div>
              </div>

              {/* Additional Info */}
              <div className="mt-6 bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
                <h3 className="text-lg font-bold text-white mb-4">📌 Key Characteristics</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {cluster.avg_age && (
                    <div>
                      <span className="text-gray-400">Average Age:</span>
                      <span className="text-white ml-2 font-semibold">{cluster.avg_age.toFixed(0)} years</span>
                    </div>
                  )}
                  {cluster.avg_tenure && (
                    <div>
                      <span className="text-gray-400">Average Tenure:</span>
                      <span className="text-white ml-2 font-semibold">{cluster.avg_tenure.toFixed(0)} months</span>
                    </div>
                  )}
                  {cluster.dominant_channel && (
                    <div>
                      <span className="text-gray-400">Preferred Channel:</span>
                      <span className="text-white ml-2 font-semibold capitalize">{cluster.dominant_channel}</span>
                    </div>
                  )}
                  {cluster.dominant_category && (
                    <div>
                      <span className="text-gray-400">Top Category:</span>
                      <span className="text-white ml-2 font-semibold">{cluster.dominant_category}</span>
                    </div>
                  )}
                  {type === 'retail' && cluster.avg_recency && (
                    <div>
                      <span className="text-gray-400">RFM Recency:</span>
                      <span className="text-white ml-2 font-semibold">{cluster.avg_recency.toFixed(1)}/5</span>
                    </div>
                  )}
                  {type === 'retail' && cluster.avg_frequency && (
                    <div>
                      <span className="text-gray-400">RFM Frequency:</span>
                      <span className="text-white ml-2 font-semibold">{cluster.avg_frequency.toFixed(1)}/5</span>
                    </div>
                  )}
                  {type === 'retail' && cluster.avg_monetary && (
                    <div>
                      <span className="text-gray-400">RFM Monetary:</span>
                      <span className="text-white ml-2 font-semibold">{cluster.avg_monetary.toFixed(1)}/5</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex gap-4">
                <button className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg font-bold transition-all">
                  🎯 Generate Campaign
                </button>
                <button className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white px-6 py-3 rounded-lg font-bold transition-all">
                  📊 Export Data
                </button>
                <button className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-6 py-3 rounded-lg font-bold transition-all">
                  👥 View Customers
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default ClusterDrillDownModal;


import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface ClusterScatterPlotProps {
  data: {
    x: number[];
    y: number[];
    labels: number[];
    cluster_names: Record<number, string>;
    ai_explanation?: string;
  };
  title: string;
}

const COLORS = [
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#10b981', // green
  '#f59e0b', // amber
  '#3b82f6', // blue
  '#ef4444', // red
  '#14b8a6', // teal
  '#f97316', // orange
];

const ClusterScatterPlot = ({ data, title }: ClusterScatterPlotProps) => {
  if (!data) {
    return (
      <div className="bg-white/5 rounded-xl p-6 border border-purple-500/20">
        <h3 className="text-lg font-bold text-white mb-4">{title}</h3>
        <div className="text-center py-12">
          <div className="text-yellow-400 mb-2">⚠️</div>
          <div className="text-gray-400">Visualization data not generated</div>
          <div className="text-xs text-gray-500 mt-2">This might take a moment for large datasets</div>
        </div>
      </div>
    );
  }
  
  if (!data.x || data.x.length === 0) {
    return (
      <div className="bg-white/5 rounded-xl p-6 border border-purple-500/20">
        <h3 className="text-lg font-bold text-white mb-4">{title}</h3>
        <div className="text-center py-12">
          <div className="text-gray-400 mb-2">📊</div>
          <div className="text-gray-400">No data points to display</div>
        </div>
      </div>
    );
  }

  // Transform data for Recharts
  const chartData = data.x.map((xVal, idx) => ({
    x: xVal,
    y: data.y[idx],
    cluster: data.labels[idx],
    name: data.cluster_names[data.labels[idx]] || `Cluster ${data.labels[idx]}`
  }));

  // Group by cluster for legend
  const clusters = Array.from(new Set(data.labels));

  return (
    <div className="bg-white/5 rounded-xl p-6 border border-purple-500/20">
      <h3 className="text-lg font-bold text-white mb-4">{title}</h3>
      
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" />
          <XAxis 
            type="number" 
            dataKey="x" 
            name="Component 1" 
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af' }}
          />
          <YAxis 
            type="number" 
            dataKey="y" 
            name="Component 2" 
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #4b5563',
              borderRadius: '0.5rem',
              color: '#fff'
            }}
            labelFormatter={(value) => `Cluster: ${value}`}
          />
          <Scatter data={chartData} fill="#8b5cf6">
            {chartData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={COLORS[entry.cluster % COLORS.length]}
                opacity={0.8}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 justify-center">
        {clusters.map((clusterId) => (
          <div key={clusterId} className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: COLORS[clusterId % COLORS.length] }}
            />
            <span className="text-sm text-gray-300">
              {data.cluster_names[clusterId] || `Cluster ${clusterId}`}
            </span>
          </div>
        ))}
      </div>

      {/* AI Explanation */}
      {data.ai_explanation && (
        <div className="mt-4 p-4 bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-lg border border-blue-500/20">
          <div className="flex items-start space-x-3">
            <div className="text-2xl flex-shrink-0">🤖</div>
            <div>
              <div className="text-sm font-semibold text-blue-300 mb-1">AI Insight</div>
              <p className="text-sm text-gray-300 leading-relaxed">{data.ai_explanation}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClusterScatterPlot;


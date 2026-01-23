import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ElbowCurveChartProps {
  data: {
    k_values: number[];
    inertias: number[];
    silhouette_scores: number[];
    optimal_k: number;
  };
}

const ElbowCurveChart = ({ data }: ElbowCurveChartProps) => {
  if (!data || !data.k_values) {
    return null;
  }

  const chartData = data.k_values.map((k, idx) => ({
    k,
    inertia: data.inertias[idx],
    silhouette: data.silhouette_scores[idx]
  }));

  return (
    <div className="bg-white/5 rounded-xl p-6 border border-purple-500/20">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">Optimal Cluster Analysis</h3>
        <div className="text-sm text-purple-300">
          Optimal K: <span className="font-bold text-xl">{data.optimal_k}</span>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" />
          <XAxis 
            dataKey="k" 
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af' }}
            label={{ value: 'Number of Clusters (K)', position: 'insideBottom', offset: -5, fill: '#9ca3af' }}
          />
          <YAxis 
            yAxisId="left"
            stroke="#8b5cf6"
            tick={{ fill: '#8b5cf6' }}
            label={{ value: 'Inertia', angle: -90, position: 'insideLeft', fill: '#8b5cf6' }}
          />
          <YAxis 
            yAxisId="right"
            orientation="right"
            stroke="#10b981"
            tick={{ fill: '#10b981' }}
            label={{ value: 'Silhouette Score', angle: 90, position: 'insideRight', fill: '#10b981' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #4b5563',
              borderRadius: '0.5rem',
              color: '#fff'
            }}
          />
          <Legend 
            wrapperStyle={{ color: '#9ca3af' }}
            iconType="line"
          />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="inertia" 
            stroke="#8b5cf6" 
            strokeWidth={2}
            dot={{ fill: '#8b5cf6', r: 4 }}
            name="Inertia (Elbow Method)"
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="silhouette" 
            stroke="#10b981" 
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 4 }}
            name="Silhouette Score"
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="mt-4 text-xs text-gray-400">
        <p>• <span className="text-purple-400">Elbow Method</span>: Look for the "elbow" point where inertia decreases most rapidly</p>
        <p>• <span className="text-green-400">Silhouette Score</span>: Higher is better (measures cluster quality, range: -1 to 1)</p>
      </div>
    </div>
  );
};

export default ElbowCurveChart;


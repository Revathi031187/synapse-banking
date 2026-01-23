import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface ClusterSizeChartProps {
  data: {
    labels: string[];
    sizes: number[];
    percentages: number[];
  };
}

const COLORS = [
  '#8b5cf6', '#ec4899', '#10b981', '#f59e0b',
  '#3b82f6', '#ef4444', '#14b8a6', '#f97316'
];

const ClusterSizeChart = ({ data }: ClusterSizeChartProps) => {
  if (!data || !data.labels || data.labels.length === 0) {
    return (
      <div className="bg-white/5 rounded-xl p-6 border border-purple-500/20">
        <h3 className="text-lg font-bold text-white mb-4">Persona Distribution</h3>
        <div className="text-gray-400 text-center py-12">
          No data available
        </div>
      </div>
    );
  }

  const chartData = data.labels.map((label, idx) => ({
    name: label,
    size: data.sizes[idx],
    percentage: data.percentages[idx]
  }));

  return (
    <div className="bg-white/5 rounded-xl p-6 border border-purple-500/20">
      <h3 className="text-lg font-bold text-white mb-4">Persona Distribution</h3>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" />
          <XAxis 
            dataKey="name" 
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis 
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af' }}
            label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #4b5563',
              borderRadius: '0.5rem',
              color: '#fff'
            }}
            formatter={(value: number, name: string, props: any) => [
              `${value} customers (${props.payload.percentage.toFixed(1)}%)`,
              'Count'
            ]}
          />
          <Bar dataKey="size" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ClusterSizeChart;


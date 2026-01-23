import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, ResponsiveContainer, Tooltip } from 'recharts';

interface ClusterRadarChartProps {
  selectedCluster: {
    cluster_id: number;
    cluster_name: string;
    avg_intent: number;
    avg_engagement: number;
    avg_income?: number;
    avg_credit_score?: number;
    avg_tenure?: number;
    avg_recency?: number;
    avg_frequency?: number;
    avg_monetary?: number;
  };
  type: 'banking' | 'retail';
}

const ClusterRadarChart = ({ selectedCluster, type }: ClusterRadarChartProps) => {
  // Normalize scores to 0-100 scale
  const normalizeScore = (value: number, max: number) => {
    return Math.min(100, (value / max) * 100);
  };

  const bankingData = [
    {
      metric: 'Intent',
      value: selectedCluster.avg_intent * 100,
      fullMark: 100
    },
    {
      metric: 'Engagement',
      value: normalizeScore(selectedCluster.avg_engagement, 15),
      fullMark: 100
    },
    {
      metric: 'Income',
      value: normalizeScore(selectedCluster.avg_income || 0, 200000),
      fullMark: 100
    },
    {
      metric: 'Credit Score',
      value: normalizeScore(selectedCluster.avg_credit_score || 0, 850),
      fullMark: 100
    },
    {
      metric: 'Tenure',
      value: normalizeScore(selectedCluster.avg_tenure || 0, 60),
      fullMark: 100
    }
  ];

  const retailData = [
    {
      metric: 'Intent',
      value: selectedCluster.avg_intent * 100,
      fullMark: 100
    },
    {
      metric: 'Engagement',
      value: normalizeScore(selectedCluster.avg_engagement, 20),
      fullMark: 100
    },
    {
      metric: 'Recency',
      value: (selectedCluster.avg_recency || 0) * 20,
      fullMark: 100
    },
    {
      metric: 'Frequency',
      value: (selectedCluster.avg_frequency || 0) * 20,
      fullMark: 100
    },
    {
      metric: 'Monetary',
      value: (selectedCluster.avg_monetary || 0) * 20,
      fullMark: 100
    }
  ];

  const data = type === 'banking' ? bankingData : retailData;

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis 
            dataKey="metric" 
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
          />
          <PolarRadiusAxis 
            angle={90} 
            domain={[0, 100]}
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 10 }}
          />
          <Radar
            name={selectedCluster.cluster_name}
            dataKey="value"
            stroke="#8b5cf6"
            fill="#8b5cf6"
            fillOpacity={0.6}
            animationDuration={800}
            animationBegin={0}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px'
            }}
            formatter={(value: any) => [`${value.toFixed(1)}%`, 'Score']}
          />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="circle"
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ClusterRadarChart;


import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

interface ClusterTreeMapProps {
  data: Array<{
    cluster_id: number;
    cluster_name: string;
    size: number;
    avg_intent: number;
    avg_engagement: number;
  }>;
  onClusterClick?: (clusterId: number) => void;
}

const COLORS = ['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

const ClusterTreeMap = ({ data, onClusterClick }: ClusterTreeMapProps) => {
  // Transform data for treemap
  const treeData = [{
    name: 'All Clusters',
    children: data.map((cluster, idx) => ({
      name: cluster.cluster_name,
      size: cluster.size,
      cluster_id: cluster.cluster_id,
      avg_intent: cluster.avg_intent,
      avg_engagement: cluster.avg_engagement,
      color: COLORS[idx % COLORS.length]
    }))
  }];

  const CustomContent = (props: any) => {
    const { x, y, width, height, name, size, color, cluster_id, avg_intent } = props;
    
    // Calculate font size based on area
    const area = width * height;
    const fontSize = Math.max(10, Math.min(16, Math.sqrt(area) / 8));
    
    return (
      <g>
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          style={{
            fill: color,
            stroke: '#1f2937',
            strokeWidth: 2,
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
          onClick={() => onClusterClick?.(cluster_id)}
          className="hover:opacity-80"
        />
        {width > 60 && height > 40 && (
          <>
            <text
              x={x + width / 2}
              y={y + height / 2 - 10}
              textAnchor="middle"
              fill="#fff"
              fontSize={fontSize}
              fontWeight="bold"
            >
              {name}
            </text>
            <text
              x={x + width / 2}
              y={y + height / 2 + 10}
              textAnchor="middle"
              fill="#fff"
              fontSize={fontSize - 2}
            >
              {size} customers
            </text>
            <text
              x={x + width / 2}
              y={y + height / 2 + 25}
              textAnchor="middle"
              fill="#e0e0e0"
              fontSize={fontSize - 3}
            >
              Intent: {(avg_intent * 100).toFixed(0)}%
            </text>
          </>
        )}
      </g>
    );
  };

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={treeData}
          dataKey="size"
          stroke="#1f2937"
          fill="#8b5cf6"
          content={<CustomContent />}
        >
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              padding: '12px'
            }}
            formatter={(value: any, name: any, props: any) => {
              const { payload } = props;
              return [
                <div key="tooltip" className="space-y-1">
                  <div className="font-bold text-white">{payload.name}</div>
                  <div className="text-gray-300">Customers: {payload.size}</div>
                  <div className="text-gray-300">Intent: {(payload.avg_intent * 100).toFixed(0)}%</div>
                  <div className="text-gray-300">Engagement: {payload.avg_engagement.toFixed(1)}</div>
                  <div className="text-xs text-gray-400 mt-2">Click to view details</div>
                </div>,
                ''
              ];
            }}
            labelFormatter={() => ''}
          />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
};

export default ClusterTreeMap;


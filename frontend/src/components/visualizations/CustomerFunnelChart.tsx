import { motion } from 'framer-motion';

interface FunnelStage {
  name: string;
  count: number;
  percentage: number;
  color: string;
}

interface CustomerFunnelChartProps {
  stages: FunnelStage[];
}

const CustomerFunnelChart = ({ stages }: CustomerFunnelChartProps) => {
  const maxCount = stages[0]?.count || 1;

  return (
    <div className="w-full py-4">
      {stages.map((stage, index) => {
        const widthPercentage = (stage.count / maxCount) * 100;
        const dropoff = index > 0 
          ? ((stages[index - 1].count - stage.count) / stages[index - 1].count) * 100 
          : 0;

        return (
          <div key={index} className="mb-4">
            {/* Dropoff indicator */}
            {index > 0 && dropoff > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="text-center mb-2"
              >
                <span className="text-red-400 text-sm">
                  ↓ {dropoff.toFixed(1)}% drop-off
                </span>
              </motion.div>
            )}

            {/* Funnel stage */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.15, duration: 0.5 }}
              className="relative"
              style={{
                width: `${widthPercentage}%`,
                margin: '0 auto'
              }}
            >
              <div
                className="rounded-lg p-4 backdrop-blur-sm border border-white/20 cursor-pointer hover:scale-105 transition-transform"
                style={{
                  background: `linear-gradient(135deg, ${stage.color}99, ${stage.color}66)`,
                }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-white font-bold text-lg">{stage.name}</div>
                    <div className="text-gray-200 text-sm mt-1">
                      {stage.count.toLocaleString()} customers
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">
                      {stage.percentage.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-200">of total</div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        );
      })}
    </div>
  );
};

export default CustomerFunnelChart;


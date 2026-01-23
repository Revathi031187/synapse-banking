import { motion } from 'framer-motion';
import type { NextBestAction } from '../types';

interface NBACardProps {
  nba: NextBestAction;
  rank: number;
}

const NBACard = ({ nba, rank }: NBACardProps) => {
  const borderColors = ['border-red-500', 'border-yellow-500', 'border-purple-500', 'border-green-500', 'border-blue-500'];
  const bgColors = ['bg-red-50', 'bg-yellow-50', 'bg-purple-50', 'bg-green-50', 'bg-blue-50'];
  const badgeColors = ['bg-red-600', 'bg-yellow-600', 'bg-purple-600', 'bg-green-600', 'bg-blue-600'];

  const borderColor = borderColors[(rank - 1) % borderColors.length];
  const bgColor = bgColors[(rank - 1) % bgColors.length];
  const badgeColor = badgeColors[(rank - 1) % badgeColors.length];

  return (
    <motion.div
      className={`bg-white border-l-8 ${borderColor} rounded-xl shadow-lg p-6 mb-6 hover:shadow-2xl transition-shadow duration-300`}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: rank * 0.1 }}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-2xl font-black text-gray-900">
          #{rank} {nba.product_name}
        </h3>
        <span className={`${badgeColor} text-white px-4 py-2 rounded-full text-sm font-bold uppercase`}>
          {nba.priority}
        </span>
      </div>

      {/* Message */}
      <div className={`${bgColor} border-l-4 ${borderColor} p-4 rounded-lg mb-4`}>
        <p className="text-sm text-gray-600 font-semibold mb-1">💬 MESSAGE</p>
        <p className="text-gray-900 font-medium text-lg">{nba.message}</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="bg-gray-50 p-4 rounded-lg text-center">
          <p className="text-xs text-gray-500 font-semibold mb-1">💰 PRICE</p>
          <p className="text-2xl font-black text-gray-900">${nba.pricing.final_price.toFixed(2)}</p>
          <p className="text-sm text-green-600 font-bold mt-1">
            {nba.pricing.discount_pct.toFixed(0)}% OFF
          </p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg text-center">
          <p className="text-xs text-gray-500 font-semibold mb-1">⭐ CONFIDENCE</p>
          <p className="text-2xl font-black text-gray-900">{(nba.confidence * 100).toFixed(1)}%</p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg text-center">
          <p className="text-xs text-gray-500 font-semibold mb-1">📦 CHANNEL</p>
          <p className="text-lg font-bold text-gray-900">{nba.channel.replace('_', ' ').toUpperCase()}</p>
        </div>
      </div>

      {/* Details */}
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-4 rounded-lg">
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-600 font-semibold">⏰ Timing:</span>
            <p className="text-gray-900 font-bold mt-1">{nba.timing.replace('_', ' ')}</p>
          </div>
          <div>
            <span className="text-gray-600 font-semibold">🎁 Incentive:</span>
            <p className="text-gray-900 font-bold mt-1">{nba.incentive_type.replace('_', ' ')}</p>
          </div>
          <div>
            <span className="text-gray-600 font-semibold">💸 Savings:</span>
            <p className="text-green-600 font-bold mt-1">
              ${(nba.pricing.base_price - nba.pricing.final_price).toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Bundle Offer */}
      {nba.bundle_offer && (
        <motion.div
          className="mt-4 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-dashed border-green-500 p-4 rounded-lg"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <p className="text-green-800 font-black text-lg mb-2">🎁 BUNDLE OFFER</p>
          <div className="flex justify-between items-center">
            <div>
              <p className="text-green-700 font-semibold">
                {nba.bundle_offer.bundle_name}
              </p>
              <p className="text-sm text-green-600">
                {nba.bundle_offer.bundle_products.length} items included
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-black text-green-700">
                ${nba.bundle_offer.bundle_price.toFixed(2)}
              </p>
              <p className="text-sm text-green-600 font-bold">
                Save ${nba.bundle_offer.savings.toFixed(2)}
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default NBACard;


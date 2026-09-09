import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, User, TrendingUp, ShoppingBag, Target, DollarSign, Award, Package, AlertCircle } from 'lucide-react';
import { getBankingApiBase } from '../utils/apiBase';

const API_BASE_URL = getBankingApiBase();

interface CustomerInsightModalProps {
  customerId: string;
  customerName: string;
  segmentName: string;
  onClose: () => void;
}

export default function CustomerInsightModal({
  customerId,
  customerName,
  segmentName,
  onClose
}: CustomerInsightModalProps) {
  const [showOutOfStock, setShowOutOfStock] = useState(false);
  const [expandedExplanations, setExpandedExplanations] = useState<{[key: number]: boolean}>({});
  const [showAllFactors, setShowAllFactors] = useState<{[key: number]: boolean}>({});

  // Fetch customer details
  const { data: customerData, isLoading: loadingCustomer } = useQuery({
    queryKey: ['customer-details', customerId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/customer/${customerId}`);
      if (!response.ok) throw new Error('Failed to fetch customer details');
      return response.json();
    }
  });

  // Fetch product recommendations
  const { data: recsData, isLoading: loadingRecs } = useQuery({
    queryKey: ['customer-recommendations', customerId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/academy/recommendations/${customerId}/all`);
      if (!response.ok) throw new Error('Failed to fetch recommendations');
      return response.json();
    }
  });

  const customer = customerData?.data;
  const recommendations = recsData?.result || {};
  const tailoredRecs = recommendations.tailored_recommendations || [];
  const outOfStockRecs = recommendations.out_of_stock_tailored || [];
  
  // Debug: Log to see if 12-factor data is present
  React.useEffect(() => {
    if (tailoredRecs.length > 0) {
      console.log('🔍 [Customer Modal] Checking product data structure:');
      console.log('   First product keys:', Object.keys(tailoredRecs[0]));
      console.log('   name:', tailoredRecs[0].name);
      console.log('   product_name:', tailoredRecs[0].product_name);
      console.log('   brand:', tailoredRecs[0].brand);
      console.log('   category:', tailoredRecs[0].category);
      console.log('   main_category:', tailoredRecs[0].main_category);
      console.log('   scoring_method:', tailoredRecs[0].scoring_method);
      console.log('   detailed_calculation exists:', !!tailoredRecs[0].detailed_calculation);
    }
  }, [tailoredRecs]);

  const isLoading = loadingCustomer || loadingRecs;

  // Extract key characteristics
  const getKeyCharacteristics = () => {
    if (!customer) return [];
    
    const metrics = customer.customer_metrics || {};
    const characteristics = [];

    if (metrics.total_spend_12mo) {
      characteristics.push({
        icon: DollarSign,
        label: 'Annual Spend',
        value: `$${metrics.total_spend_12mo.toFixed(0)}`,
        color: 'text-green-600',
        bg: 'bg-green-50'
      });
    }

    if (metrics.purchase_frequency) {
      characteristics.push({
        icon: ShoppingBag,
        label: 'Purchase Frequency',
        value: `${metrics.purchase_frequency.toFixed(1)}x/year`,
        color: 'text-blue-600',
        bg: 'bg-blue-50'
      });
    }

    if (metrics.dominant_category) {
      characteristics.push({
        icon: Package,
        label: 'Favorite Category',
        value: metrics.dominant_category,
        color: 'text-purple-600',
        bg: 'bg-purple-50'
      });
    }

    if (metrics.search_specificity !== undefined) {
      const expertiseLevel = metrics.search_specificity > 4 ? 'Expert' : 
                            metrics.search_specificity > 3 ? 'Experienced' : 
                            metrics.search_specificity > 2 ? 'Moderate' : 'Beginner';
      characteristics.push({
        icon: Target,
        label: 'Product Knowledge',
        value: `${expertiseLevel} (${metrics.search_specificity.toFixed(1)}/5)`,
        color: 'text-indigo-600',
        bg: 'bg-indigo-50'
      });
    }

    if (metrics.bundle_affinity !== undefined) {
      const bundlePref = metrics.bundle_affinity > 0.6 ? 'Loves Bundles' :
                        metrics.bundle_affinity > 0.3 ? 'Occasional' : 'Individual Items';
      characteristics.push({
        icon: Award,
        label: 'Shopping Style',
        value: `${bundlePref} (${(metrics.bundle_affinity * 100).toFixed(0)}%)`,
        color: 'text-orange-600',
        bg: 'bg-orange-50'
      });
    }

    if (metrics.price_sort_frequency !== undefined) {
      const priceSensitivity = metrics.price_sort_frequency > 0.6 ? 'High' :
                               metrics.price_sort_frequency > 0.3 ? 'Moderate' : 'Low';
      characteristics.push({
        icon: TrendingUp,
        label: 'Price Sensitivity',
        value: `${priceSensitivity} (${(metrics.price_sort_frequency * 100).toFixed(0)}%)`,
        color: 'text-red-600',
        bg: 'bg-red-50'
      });
    }

    return characteristics;
  };

  // Generate segment fit explanation
  const getSegmentFitExplanation = () => {
    if (!customer) return null;

    const metrics = customer.customer_metrics || {};
    const reasons = [];

    // Spending pattern
    if (metrics.total_spend_12mo > 1000) {
      reasons.push(`High annual spending of $${metrics.total_spend_12mo.toFixed(0)} indicates premium customer value`);
    } else if (metrics.total_spend_12mo < 300) {
      reasons.push(`Budget-conscious spending of $${metrics.total_spend_12mo.toFixed(0)} aligns with value-seeking behavior`);
    } else {
      reasons.push(`Mid-range spending of $${metrics.total_spend_12mo.toFixed(0)} shows balanced purchasing approach`);
    }

    // Category preference
    if (metrics.dominant_category) {
      reasons.push(`Strong preference for ${metrics.dominant_category} products shapes their segment profile`);
    }

    // Shopping behavior
    if (metrics.bundle_affinity > 0.6) {
      reasons.push(`High bundle affinity (${(metrics.bundle_affinity * 100).toFixed(0)}%) shows preference for complete solutions`);
    } else if (metrics.bundle_affinity < 0.3) {
      reasons.push(`Low bundle affinity (${(metrics.bundle_affinity * 100).toFixed(0)}%) indicates selective, item-focused shopping`);
    }

    // Expertise
    if (metrics.search_specificity > 4) {
      reasons.push(`Expert-level product knowledge (${metrics.search_specificity.toFixed(1)}/5) drives informed purchase decisions`);
    } else if (metrics.search_specificity < 2.5) {
      reasons.push(`Beginner-level experience (${metrics.search_specificity.toFixed(1)}/5) benefits from guided recommendations`);
    }

    // Price behavior
    if (metrics.price_sort_frequency > 0.6) {
      reasons.push(`High price sensitivity (${(metrics.price_sort_frequency * 100).toFixed(0)}%) means deals and value are key motivators`);
    }

    return reasons;
  };

  // Generate recommendation explanation
  const getRecommendationExplanation = (product: any) => {
    if (!customer) return '';

    const metrics = customer.customer_metrics || {};
    const reasons = [];

    // Price match
    const customerAvgPrice = metrics.avg_order_value || metrics.total_spend_12mo / (metrics.purchase_frequency || 1);
    const priceDiff = Math.abs(product.price - customerAvgPrice) / customerAvgPrice;
    
    if (priceDiff < 0.3) {
      reasons.push(`Price ($${product.price.toFixed(2)}) matches your typical purchase range`);
    }

    // Category match
    if (product.category === metrics.dominant_category) {
      reasons.push(`Perfect match for your favorite category: ${product.category}`);
    }

    // Brand match (if available)
    if (product.brand && metrics.favorite_brand && product.brand === metrics.favorite_brand) {
      reasons.push(`Your preferred brand: ${product.brand}`);
    }

    // Quality match based on expertise
    if (metrics.search_specificity > 4 && product.price > 100) {
      reasons.push(`Premium quality aligns with your expert-level standards`);
    } else if (metrics.search_specificity < 2.5 && product.price < 100) {
      reasons.push(`Beginner-friendly and easy to use`);
    }

    // Bundle preference
    if (metrics.bundle_affinity > 0.6 && product.name.toLowerCase().includes('bundle')) {
      reasons.push(`Bundle option matches your shopping preference`);
    }

    if (reasons.length === 0) {
      reasons.push(`Popular choice among similar customers in ${segmentName}`);
    }

    return reasons.join(' • ');
  };

  const characteristics = getKeyCharacteristics();
  const segmentFit = getSegmentFitExplanation();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 px-8 py-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-white rounded-full flex items-center justify-center shadow-lg">
              <User className="w-7 h-7 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">{customerName}</h2>
              <p className="text-blue-100">Customer ID: {customerId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition-all duration-200"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          ) : (
            <>
              {/* Segment Badge */}
              <div className="flex items-center justify-center">
                <div className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-full px-6 py-3">
                  <Target className="w-5 h-5 text-indigo-600" />
                  <span className="font-semibold text-indigo-900">Segment: {segmentName}</span>
                </div>
              </div>

              {/* Key Characteristics */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Award className="w-6 h-6 text-indigo-600" />
                  Key Characteristics
                </h3>
                <div className="grid md:grid-cols-3 gap-4">
                  {characteristics.map((char, idx) => (
                    <div key={idx} className={`${char.bg} border border-gray-200 rounded-xl p-4 transition-all duration-200 hover:shadow-md`}>
                      <div className="flex items-start gap-3">
                        <div className={`${char.color} ${char.bg} rounded-lg p-2`}>
                          <char.icon className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="text-xs font-medium text-gray-600 mb-1">{char.label}</div>
                          <div className={`font-bold ${char.color}`}>{char.value}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Why This Segment */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Target className="w-6 h-6 text-purple-600" />
                  Why This Customer Belongs to "{segmentName}"
                </h3>
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-6">
                  {segmentFit && segmentFit.length > 0 ? (
                    <ul className="space-y-3">
                      {segmentFit.map((reason, idx) => (
                        <li key={idx} className="flex items-start gap-3">
                          <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                            <span className="text-white text-xs font-bold">{idx + 1}</span>
                          </div>
                          <span className="text-gray-800">{reason}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-600">Loading segment analysis...</p>
                  )}
                </div>
              </div>

              {/* Product Recommendations */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <ShoppingBag className="w-6 h-6 text-green-600" />
                  Personalized Product Recommendations
                </h3>
                
                {tailoredRecs.length > 0 ? (
                  <div className="grid md:grid-cols-2 gap-4">
                    {tailoredRecs.slice(0, 4).map((product, idx) => (
                      <div key={idx} className="bg-white border-2 border-gray-200 rounded-xl overflow-hidden hover:border-green-500 hover:shadow-lg transition-all duration-300">
                        <div className="p-5">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <Package className="w-4 h-4 text-green-600" />
                                <span className="text-xs font-semibold text-green-600">TOP PICK #{idx + 1}</span>
                              </div>
                              <h4 className="font-bold text-gray-900 mb-1 line-clamp-2">
                                {product.product_name || product.name || 'Product'}
                              </h4>
                              <p className="text-sm text-gray-600">
                                {product.brand} • {product.main_category || product.category || 'Category'}
                              </p>
                            </div>
                            <div className="text-right ml-4">
                              <div className="text-2xl font-bold text-green-600">${product.price.toFixed(2)}</div>
                            </div>
                          </div>
                          
                          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
                            <div className="flex items-start gap-2">
                              <AlertCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                              <p className="text-xs text-green-800 leading-relaxed">
                                {getRecommendationExplanation(product)}
                              </p>
                            </div>
                          </div>

                          {/* SCORE BAR */}
                          {product.score && (
                            <div className="mb-3">
                              <div className="flex justify-between text-xs mb-1">
                                <span className="text-gray-600">Match Score</span>
                                <span className="font-bold text-gray-900">{(product.score * 100).toFixed(1)}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className="h-2 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 transition-all"
                                  style={{ width: `${Math.min(product.score * 100, 100)}%` }}
                                />
                              </div>
                            </div>
                          )}

                          {/* 12-FACTOR DETAILED EXPLANATION */}
                          {product.detailed_calculation && product.scoring_method === '12_factor' && (
                            <div className="mb-3">
                              <button
                                onClick={() => setExpandedExplanations(prev => ({
                                  ...prev,
                                  [`${idx}`]: !prev[`${idx}`]
                                }))}
                                className="flex items-center gap-2 text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                              >
                                <svg 
                                  className="w-3 h-3 transition-transform duration-200" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  viewBox="0 0 24 24"
                                  style={{ transform: expandedExplanations[`${idx}`] ? 'rotate(90deg)' : 'rotate(0deg)' }}
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                                <span>View Detailed Scoring (12 Factors)</span>
                              </button>

                              {expandedExplanations[`${idx}`] && (
                                <div className="mt-2 p-3 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg text-xs animate-fadeIn">
                                  <p className="font-semibold text-indigo-900 mb-2">📊 12-Factor Scoring Breakdown</p>
                                  
                                  <div className="space-y-2 mb-2">
                                    {/* Show top 4 factors or all 12 based on state */}
                                    {(showAllFactors[idx] 
                                      ? ['price_alignment', 'category_match', 'expertise_match', 'brand_loyalty', 
                                         'value_tier', 'bundle_preference', 'segment_affinity', 'product_rating',
                                         'popularity', 'co_occurrence', 'recency_boost', 'variety_bonus']
                                      : ['price_alignment', 'category_match', 'expertise_match', 'brand_loyalty']
                                    ).map(factor => {
                                      const f = product.detailed_calculation[factor];
                                      if (!f) return null;
                                      return (
                                        <div key={factor} className="flex justify-between items-center py-1 border-b border-blue-100">
                                          <span className="text-gray-700 capitalize">{factor.replace(/_/g, ' ')}</span>
                                          <span className="font-semibold text-indigo-700">{f.result || `${(f.score * 100).toFixed(1)}%`}</span>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {!showAllFactors[idx] && (
                                    <button
                                      onClick={() => setShowAllFactors(prev => ({ ...prev, [idx]: true }))}
                                      className="text-xs text-blue-600 hover:text-blue-800 underline mb-2"
                                    >
                                      + 8 more factors...
                                    </button>
                                  )}

                                  {showAllFactors[idx] && (
                                    <button
                                      onClick={() => setShowAllFactors(prev => ({ ...prev, [idx]: false }))}
                                      className="text-xs text-blue-600 hover:text-blue-800 underline mb-2"
                                    >
                                      - Show less
                                    </button>
                                  )}

                                  <div className="mt-2 pt-2 border-t border-blue-200 flex justify-between items-center">
                                    <span className="font-bold text-gray-900">Total Score</span>
                                    <span className="text-lg font-bold text-indigo-600">
                                      {product.detailed_calculation.total_percentage?.toFixed(1)}%
                                    </span>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <span className="px-2 py-1 bg-gray-100 rounded">{product.main_category || product.category || 'Category'}</span>
                            <span className="px-2 py-1 bg-green-100 text-green-700 rounded font-medium">In Stock</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Package className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                    <p>No recommendations available</p>
                  </div>
                )}

                {/* Out of Stock Section */}
                {outOfStockRecs.length > 0 && (
                  <div className="mt-6">
                    <button
                      onClick={() => setShowOutOfStock(!showOutOfStock)}
                      className="text-sm text-gray-600 hover:text-gray-900 font-medium mb-3"
                    >
                      {showOutOfStock ? '▼' : '▶'} View Out of Stock Recommendations ({outOfStockRecs.length})
                    </button>
                    
                    {showOutOfStock && (
                      <div className="grid md:grid-cols-2 gap-3 opacity-60">
                        {outOfStockRecs.slice(0, 4).map((product, idx) => (
                          <div key={idx} className="bg-gray-50 border border-gray-300 rounded-lg p-4">
                            <h4 className="font-semibold text-gray-700 mb-1">{product.name}</h4>
                            <div className="flex items-center justify-between">
                              <span className="text-lg font-bold text-gray-600">${product.price.toFixed(2)}</span>
                              <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded">Out of Stock</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-8 py-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Recommendations updated based on {customer?.customer_metrics?.purchase_frequency?.toFixed(0) || 0} purchases
            </p>
            <button
              onClick={onClose}
              className="btn-primary"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}



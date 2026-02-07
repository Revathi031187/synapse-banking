import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, User, TrendingUp, CreditCard, Target, DollarSign, Award, Briefcase, AlertCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

interface CustomerInsightModalBankingProps {
  customerId: string;
  customerName: string;
  segmentName: string;
  onClose: () => void;
}

export default function CustomerInsightModalBanking({
  customerId,
  customerName,
  segmentName,
  onClose
}: CustomerInsightModalBankingProps) {
  const [expandedExplanations, setExpandedExplanations] = useState<{[key: number]: boolean}>({});
  const [showAllFactors, setShowAllFactors] = useState<{[key: number]: boolean}>({});

  // Fetch customer details
  const { data: customerData, isLoading: loadingCustomer } = useQuery({
    queryKey: ['banking-customer-details', customerId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/customer/${customerId}`);
      if (!response.ok) throw new Error('Failed to fetch customer details');
      return response.json();
    }
  });

  // Fetch banking product recommendations
  const { data: recsData, isLoading: loadingRecs } = useQuery({
    queryKey: ['banking-customer-recommendations', customerId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/recommendations/${customerId}/all`);
      if (!response.ok) throw new Error('Failed to fetch recommendations');
      return response.json();
    }
  });

  const customer = customerData?.data;
  const recommendations = recsData?.result || {};
  const tailoredRecs = recommendations.tailored_recommendations || [];
  
  // Debug: Log to see if banking 12-factor data is present
  React.useEffect(() => {
    if (tailoredRecs.length > 0) {
      console.log('🏦 [Banking Customer Modal] Checking product data structure:');
      console.log('   First product keys:', Object.keys(tailoredRecs[0]));
      console.log('   product_name:', tailoredRecs[0].product_name);
      console.log('   category:', tailoredRecs[0].category);
      console.log('   scoring_method:', tailoredRecs[0].scoring_method);
      console.log('   detailed_calculation exists:', !!tailoredRecs[0].detailed_calculation);
    }
  }, [tailoredRecs]);

  const isLoading = loadingCustomer || loadingRecs;

  // Extract key banking characteristics
  const getKeyCharacteristics = () => {
    if (!customer) return [];
    
    const metrics = customer.customer_metrics || customer || {};
    const characteristics = [];

    if (metrics.credit_score) {
      const scoreLevel = metrics.credit_score >= 750 ? 'Excellent' :
                        metrics.credit_score >= 700 ? 'Good' :
                        metrics.credit_score >= 650 ? 'Fair' : 'Building';
      characteristics.push({
        icon: Award,
        label: 'Credit Score',
        value: `${metrics.credit_score} (${scoreLevel})`,
        color: 'text-green-600',
        bg: 'bg-green-50'
      });
    }

    if (metrics.total_deposits !== undefined) {
      characteristics.push({
        icon: DollarSign,
        label: 'Total Deposits',
        value: `$${metrics.total_deposits.toLocaleString()}`,
        color: 'text-blue-600',
        bg: 'bg-blue-50'
      });
    }

    if (metrics.income) {
      characteristics.push({
        icon: TrendingUp,
        label: 'Annual Income',
        value: `$${metrics.income.toLocaleString()}`,
        color: 'text-purple-600',
        bg: 'bg-purple-50'
      });
    }

    if (metrics.num_products) {
      characteristics.push({
        icon: Briefcase,
        label: 'Banking Products',
        value: `${metrics.num_products} Active`,
        color: 'text-indigo-600',
        bg: 'bg-indigo-50'
      });
    }

    if (metrics.digital_engagement_score !== undefined) {
      const engagementLevel = metrics.digital_engagement_score > 0.7 ? 'High' :
                             metrics.digital_engagement_score > 0.4 ? 'Moderate' : 'Low';
      characteristics.push({
        icon: CreditCard,
        label: 'Digital Engagement',
        value: `${engagementLevel} (${(metrics.digital_engagement_score * 100).toFixed(0)}%)`,
        color: 'text-orange-600',
        bg: 'bg-orange-50'
      });
    }

    if (metrics.tenure_months !== undefined) {
      const years = Math.floor(metrics.tenure_months / 12);
      const months = metrics.tenure_months % 12;
      const tenureText = years > 0 ? `${years}y ${months}m` : `${months} months`;
      characteristics.push({
        icon: Target,
        label: 'Customer Since',
        value: tenureText,
        color: 'text-red-600',
        bg: 'bg-red-50'
      });
    }

    return characteristics;
  };

  // Generate banking segment fit explanation
  const getSegmentFitExplanation = () => {
    if (!customer) return null;

    const metrics = customer.customer_metrics || customer || {};
    const reasons = [];

    // Credit score assessment
    if (metrics.credit_score) {
      if (metrics.credit_score >= 750) {
        reasons.push(`Excellent credit score of ${metrics.credit_score} qualifies for premium banking products`);
      } else if (metrics.credit_score >= 700) {
        reasons.push(`Good credit score of ${metrics.credit_score} enables access to competitive rates`);
      } else if (metrics.credit_score >= 650) {
        reasons.push(`Fair credit score of ${metrics.credit_score} with opportunities for improvement`);
      } else {
        reasons.push(`Building credit (${metrics.credit_score}) with supportive banking solutions available`);
      }
    }

    // Deposit level
    if (metrics.total_deposits) {
      if (metrics.total_deposits >= 100000) {
        reasons.push(`High deposit balance of $${metrics.total_deposits.toLocaleString()} indicates wealth management needs`);
      } else if (metrics.total_deposits >= 50000) {
        reasons.push(`Substantial deposits of $${metrics.total_deposits.toLocaleString()} show strong financial position`);
      } else if (metrics.total_deposits >= 10000) {
        reasons.push(`Growing deposits of $${metrics.total_deposits.toLocaleString()} suggest expanding banking relationship`);
      } else {
        reasons.push(`Building savings of $${metrics.total_deposits.toLocaleString()} with starter banking products`);
      }
    }

    // Income level
    if (metrics.income) {
      if (metrics.income >= 100000) {
        reasons.push(`High income of $${metrics.income.toLocaleString()} supports premium financial services`);
      } else if (metrics.income >= 50000) {
        reasons.push(`Stable income of $${metrics.income.toLocaleString()} enables diverse product portfolio`);
      }
    }

    // Banking relationship
    if (metrics.num_products) {
      if (metrics.num_products >= 5) {
        reasons.push(`Deep banking relationship with ${metrics.num_products} products shows high engagement`);
      } else if (metrics.num_products >= 3) {
        reasons.push(`Moderate product portfolio (${metrics.num_products} products) with growth potential`);
      } else {
        reasons.push(`Starter relationship (${metrics.num_products} products) ready for expansion`);
      }
    }

    // Digital engagement
    if (metrics.digital_engagement_score !== undefined) {
      if (metrics.digital_engagement_score > 0.7) {
        reasons.push(`High digital engagement (${(metrics.digital_engagement_score * 100).toFixed(0)}%) perfect for online banking solutions`);
      } else if (metrics.digital_engagement_score < 0.4) {
        reasons.push(`Branch-focused customer (${(metrics.digital_engagement_score * 100).toFixed(0)}% digital) values personal service`);
      }
    }

    // Customer segment
    if (metrics.customer_segment) {
      const segmentDesc = {
        'Personal': 'Personal banking needs with individual financial goals',
        'Business': 'Business banking requirements with commercial focus',
        'Agricultural': 'Agricultural banking with specialized farming needs'
      };
      reasons.push(segmentDesc[metrics.customer_segment] || `${metrics.customer_segment} banking customer`);
    }

    return reasons;
  };

  // Generate banking recommendation explanation
  const getRecommendationExplanation = (product: any) => {
    if (!customer) return '';

    const metrics = customer.customer_metrics || customer || {};
    const reasons = [];

    // Credit eligibility
    if (product.min_credit_score && metrics.credit_score) {
      if (metrics.credit_score >= product.min_credit_score + 50) {
        reasons.push(`Well above credit requirement (${product.min_credit_score})`);
      } else if (metrics.credit_score >= product.min_credit_score) {
        reasons.push(`Meets credit requirement (${product.min_credit_score})`);
      }
    }

    // Fee affordability
    if (product.annual_fee === 0) {
      reasons.push('No annual fee');
    } else if (product.annual_fee && metrics.total_deposits) {
      const feeRatio = product.annual_fee / metrics.total_deposits;
      if (feeRatio < 0.001) {
        reasons.push(`Minimal fee ($${product.annual_fee}/year) for your deposit level`);
      }
    }

    // Interest benefit
    if (product.interest_rate > 0) {
      reasons.push(`Competitive ${product.interest_rate.toFixed(2)}% APY to grow savings`);
    }

    // Category match
    if (product.category === metrics.customer_segment) {
      reasons.push(`Perfect fit for ${product.category} banking needs`);
    }

    // Balance requirement
    if (product.min_balance && metrics.total_deposits >= product.min_balance) {
      reasons.push(`Your balance exceeds minimum requirement ($${product.min_balance.toLocaleString()})`);
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

              {/* Key Banking Characteristics */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Award className="w-6 h-6 text-indigo-600" />
                  Key Financial Profile
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

              {/* Banking Product Recommendations */}
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <CreditCard className="w-6 h-6 text-green-600" />
                  Personalized Banking Product Recommendations
                </h3>
                
                {tailoredRecs.length > 0 ? (
                  <div className="grid md:grid-cols-2 gap-4">
                    {tailoredRecs.slice(0, 4).map((product, idx) => (
                      <div key={idx} className="bg-white border-2 border-gray-200 rounded-xl overflow-hidden hover:border-green-500 hover:shadow-lg transition-all duration-300">
                        <div className="p-5">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <Briefcase className="w-4 h-4 text-green-600" />
                                <span className="text-xs font-semibold text-green-600">TOP PICK #{idx + 1}</span>
                              </div>
                              <h4 className="font-bold text-gray-900 mb-1 line-clamp-2">
                                {product.product_name}
                              </h4>
                              <p className="text-sm text-gray-600">
                                {product.category || 'Personal'} • {product.subcategory || 'Banking'}
                              </p>
                            </div>
                            <div className="text-right ml-4">
                              <div className="text-xl font-bold text-green-600">${product.annual_fee?.toFixed(0) || '0'}/yr</div>
                              {product.interest_rate > 0 && (
                                <div className="text-sm text-blue-600 font-semibold">{product.interest_rate.toFixed(2)}% APY</div>
                              )}
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
                                <span className="text-gray-600">Suitability Score</span>
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

                          {/* BANKING 12-FACTOR DETAILED EXPLANATION */}
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
                                <span>View Banking 12-Factor Scoring</span>
                              </button>

                              {expandedExplanations[`${idx}`] && (
                                <div className="mt-2 p-3 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg text-xs animate-fadeIn">
                                  <p className="font-semibold text-indigo-900 mb-2">🏦 Banking 12-Factor Scoring Breakdown</p>
                                  
                                  <div className="space-y-2 mb-2">
                                    {/* Show key banking factors */}
                                    {(showAllFactors[idx] 
                                      ? Object.keys(product.detailed_calculation).filter(k => k !== 'total_score' && typeof product.detailed_calculation[k] === 'object')
                                      : ['eligibility_match', 'financial_need_match', 'relationship_depth', 'profitability_potential'].filter(k => product.detailed_calculation[k])
                                    ).map(factor => {
                                      const f = product.detailed_calculation[factor];
                                      if (!f || typeof f !== 'object') return null;
                                      return (
                                        <div key={factor} className="flex justify-between items-center py-1 border-b border-blue-100">
                                          <span className="text-gray-700 capitalize">{factor.replace(/_/g, ' ')}</span>
                                          <span className="font-semibold text-indigo-700">
                                            {typeof f === 'number' ? `${(f * 100).toFixed(1)}%` : f.result || f.score || 'N/A'}
                                          </span>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {!showAllFactors[idx] && Object.keys(product.detailed_calculation).length > 5 && (
                                    <button
                                      onClick={() => setShowAllFactors(prev => ({ ...prev, [idx]: true }))}
                                      className="text-xs text-blue-600 hover:text-blue-800 underline mb-2"
                                    >
                                      + Show all factors...
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
                                      {product.detailed_calculation.total_score 
                                        ? (product.detailed_calculation.total_score * 100).toFixed(1)
                                        : (product.score * 100).toFixed(1)}%
                                    </span>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <span className="px-2 py-1 bg-gray-100 rounded">{product.category || 'Personal'}</span>
                            {product.min_credit_score && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">Min Credit: {product.min_credit_score}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Briefcase className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                    <p>No recommendations available</p>
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
              Recommendations based on {customer?.customer_metrics?.num_products || customer?.num_products || 0} existing products
            </p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

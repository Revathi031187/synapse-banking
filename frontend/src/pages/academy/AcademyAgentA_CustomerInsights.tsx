import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface Customer {
  customer_id: string;
  customer_name: string;
  persona: string;
  persona_short: string;
  confidence: number;
  total_spend_12mo: number;
  purchase_frequency: number;
  search_specificity: number;
  bundle_affinity: number;
  age: number;
  channel_preference: string;
}

interface CustomerDetails {
  customer_id: string;
  customer_name: string;
  persona: string;
  persona_short: string;
  confidence: number;
  confidence_level: string;
  demographics: {
    age: number;
    income: number;
    urbanicity: string;
    climate_zone: string;
    distance_to_store: number;
  };
  customer_metrics: {
    search_specificity: number;
    spec_expansion_rate: number;
    bundle_affinity: number;
    price_sort_frequency: number;
    total_spend_12mo: number;
    purchase_frequency: number;
    avg_order_value: number;
    return_rate: number;
    recency_days: number;
  };
  persona_averages: {
    search_specificity: number;
    spec_expansion_rate: number;
    bundle_affinity: number;
    price_sort_frequency: number;
    total_spend_12mo: number;
    purchase_frequency: number;
    return_rate: number;
  };
  comparisons: any;
  behavior_profile: string[];
  product_preferences: any;
}

interface Recommendation {
  type: string;
  priority: string;
  action: string;
  reason: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';
const API_BASE = `${API_BASE_URL}/api`;

export default function AcademyAgentA_CustomerInsights() {
  const [searchQuery, setSearchQuery] = useState('');
  const [personaFilter, setPersonaFilter] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [togetherApiKey, setTogetherApiKey] = useState('');
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);

  const pageSize = 50;

  // Fetch Together AI API key from backend
  useQuery({
    queryKey: ['together-api-key'],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE}/config/together-api-key`);
        if (!response.ok) return null;
        const result = await response.json();
        if (result.configured && result.api_key) {
          setTogetherApiKey(result.api_key);
          setShowApiKeyInput(false);
        } else {
          setShowApiKeyInput(true);
        }
        return result;
      } catch {
        setShowApiKeyInput(true);
        return null;
      }
    },
  });

  // Fetch customers with pagination and filters
  const { data: customersData, isLoading: loadingCustomers, refetch } = useQuery({
    queryKey: ['academy-customers', currentPage, personaFilter, searchQuery],
    queryFn: async () => {
      const params = new URLSearchParams({
        skip: (currentPage * pageSize).toString(),
        limit: pageSize.toString(),
      });
      if (personaFilter) params.append('persona_filter', personaFilter);
      if (searchQuery) params.append('search', searchQuery);

      const response = await fetch(`${API_BASE}/academy/agent_a/customers?${params}`);
      if (!response.ok) throw new Error('Failed to fetch customers');
      const result = await response.json();
      return result.data;
    },
  });

  // Fetch customer details
  const { data: customerDetails, isLoading: loadingDetails } = useQuery<CustomerDetails>({
    queryKey: ['academy-customer-details', selectedCustomerId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/academy/agent_a/customer/${selectedCustomerId}`);
      if (!response.ok) throw new Error('Failed to fetch customer details');
      const result = await response.json();
      return result.data;
    },
    enabled: !!selectedCustomerId,
  });

  // Fetch recommendations
  const { data: recommendations } = useQuery({
    queryKey: ['academy-customer-recommendations', selectedCustomerId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/academy/agent_a/customer/${selectedCustomerId}/recommendations`);
      if (!response.ok) throw new Error('Failed to fetch recommendations');
      const result = await response.json();
      return result.data;
    },
    enabled: !!selectedCustomerId,
  });

  // Generate AI explanation
  const explainMutation = useMutation({
    mutationFn: async ({ customerId, apiKey }: { customerId: string; apiKey: string }) => {
      const response = await fetch(`${API_BASE}/academy/agent_a/customer/${customerId}/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey }),
      });
      if (!response.ok) throw new Error('Failed to generate explanation');
      const result = await response.json();
      return result.data;
    },
  });

  // Reset AI explanation when customer changes
  useEffect(() => {
    explainMutation.reset();
  }, [selectedCustomerId]);

  const handleSearch = () => {
    setCurrentPage(0);
    refetch();
  };

  const handleGenerateExplanation = () => {
    if (!selectedCustomerId || !togetherApiKey) return;
    explainMutation.mutate({ customerId: selectedCustomerId, apiKey: togetherApiKey });
  };

  // Prepare radar chart data
  const getRadarData = () => {
    if (!customerDetails) return [];

    const metrics = customerDetails.customer_metrics;
    const averages = customerDetails.persona_averages;

    return [
      {
        metric: 'Search Specificity',
        Customer: (metrics.search_specificity / 5) * 100,
        'Persona Avg': (averages.search_specificity / 5) * 100,
      },
      {
        metric: 'Spec Expansion',
        Customer: metrics.spec_expansion_rate * 100,
        'Persona Avg': averages.spec_expansion_rate * 100,
      },
      {
        metric: 'Bundle Affinity',
        Customer: metrics.bundle_affinity * 100,
        'Persona Avg': averages.bundle_affinity * 100,
      },
      {
        metric: 'Price Sorting',
        Customer: metrics.price_sort_frequency * 100,
        'Persona Avg': averages.price_sort_frequency * 100,
      },
      {
        metric: 'Return Rate',
        Customer: (1 - metrics.return_rate) * 100, // Invert for better visualization
        'Persona Avg': (1 - averages.return_rate) * 100,
      },
    ];
  };

  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 80) return 'bg-green-50 border-green-200';
    if (confidence >= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  // Get priority color
  const getPriorityColor = (priority: string) => {
    if (priority === 'high') return 'bg-red-100 text-red-700 border-red-300';
    if (priority === 'medium') return 'bg-yellow-100 text-yellow-700 border-yellow-300';
    return 'bg-blue-100 text-blue-700 border-blue-300';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2">👤 Customer Insights</h1>
        <p className="text-gray-600">
          Individual customer analysis with AI-powered explanations and personalized recommendations
        </p>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white shadow-md rounded-xl p-6 border border-gray-200">
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-gray-700 mb-2 block">🔍 Search Customer</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search by name or customer ID..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          <div className="w-48">
            <label className="text-sm font-medium text-gray-700 mb-2 block">Filter Persona</label>
            <select
              value={personaFilter || ''}
              onChange={(e) => {
                setPersonaFilter(e.target.value || null);
                setCurrentPage(0);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              <option value="">All Personas</option>
              <option value="Novice">First-Time Camper</option>
              <option value="Family_Socializer">Family Socializer</option>
              <option value="Seasoned_Pro">Seasoned Pro</option>
            </select>
          </div>

          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
          >
            Search
          </button>
        </div>
      </div>

      {/* Customer Grid */}
      <div className="bg-white shadow-md rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-700">Customer Name</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-700">Persona</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-700">Confidence</th>
                <th className="text-right px-6 py-4 text-sm font-semibold text-gray-700">Annual Spend</th>
                <th className="text-center px-6 py-4 text-sm font-semibold text-gray-700">Purchases</th>
                <th className="text-center px-6 py-4 text-sm font-semibold text-gray-700">Action</th>
              </tr>
            </thead>
            <tbody>
              {loadingCustomers ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    <div className="flex items-center justify-center space-x-2">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600"></div>
                      <span>Loading customers...</span>
                    </div>
                  </td>
                </tr>
              ) : customersData?.customers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    No customers found. Try adjusting your filters.
                  </td>
                </tr>
              ) : (
                customersData?.customers.map((customer: Customer) => (
                  <tr
                    key={customer.customer_id}
                    className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-gray-900">{customer.customer_name}</div>
                        <div className="text-xs text-gray-500">{customer.customer_id}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-700">{customer.persona}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-sm font-semibold ${getConfidenceColor(customer.confidence)}`}>
                        {customer.confidence.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="text-sm font-medium text-gray-900">
                        ${customer.total_spend_12mo.toFixed(0)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="text-sm text-gray-700">{customer.purchase_frequency}x</span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => setSelectedCustomerId(customer.customer_id)}
                        className="px-4 py-1 bg-green-100 hover:bg-green-200 text-green-700 rounded-lg text-sm font-medium transition-colors"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {customersData && (
          <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t border-gray-200">
            <div className="text-sm text-gray-700">
              Showing {customersData.pagination.skip + 1} - {customersData.pagination.skip + customersData.pagination.returned} of {customersData.pagination.total} customers
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                disabled={currentPage === 0}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <span className="text-sm text-gray-700">
                Page {currentPage + 1} of {Math.ceil(customersData.pagination.total / pageSize)}
              </span>
              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={!customersData.pagination.has_more}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Customer Detail Modal */}
      <AnimatePresence>
        {selectedCustomerId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedCustomerId(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden shadow-2xl border border-gray-200"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="bg-gradient-to-r from-green-600 to-blue-600 p-6 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="text-5xl">👤</div>
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-1">
                      {customerDetails?.customer_name}
                    </h2>
                    <div className="flex items-center space-x-4">
                      <span className="text-white/90 text-sm">{customerDetails?.customer_id}</span>
                      <span className="text-white/90 text-sm">•</span>
                      <span className="text-white font-medium">{customerDetails?.persona}</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedCustomerId(null)}
                  className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Modal Content */}
              <div className="overflow-y-auto max-h-[calc(90vh-120px)] p-6 space-y-6">
                {loadingDetails ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
                  </div>
                ) : (
                  <>
                    {/* Confidence Score */}
                    <div className={`rounded-xl p-6 border-2 ${getConfidenceBg(customerDetails?.confidence || 0)}`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-medium text-gray-700 mb-1">Confidence Score</div>
                          <div className={`text-4xl font-bold ${getConfidenceColor(customerDetails?.confidence || 0)}`}>
                            {customerDetails?.confidence.toFixed(1)}%
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            {customerDetails?.confidence_level} Confidence
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-600 mb-2">How well this customer matches their persona</div>
                          <div className="flex items-center space-x-2 justify-end">
                            {customerDetails && customerDetails.confidence >= 80 && (
                              <span className="text-green-600">✓ Strong Match</span>
                            )}
                            {customerDetails && customerDetails.confidence >= 60 && customerDetails.confidence < 80 && (
                              <span className="text-yellow-600">~ Good Match</span>
                            )}
                            {customerDetails && customerDetails.confidence < 60 && (
                              <span className="text-red-600">⚠ Weak Match</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* AI Explanation Section */}
                    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-2">
                          <span className="text-2xl">🤖</span>
                          <h3 className="text-xl font-bold text-gray-900">AI-Generated Explanation</h3>
                        </div>
                        <button
                          onClick={() => {
                            if (togetherApiKey && !explainMutation.data) {
                              handleGenerateExplanation();
                            } else if (!togetherApiKey) {
                              setShowApiKeyInput(!showApiKeyInput);
                            } else {
                              // Regenerate
                              handleGenerateExplanation();
                            }
                          }}
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                          {explainMutation.data ? 'Regenerate' : togetherApiKey ? 'Generate Explanation' : 'Configure API Key'}
                        </button>
                      </div>

                      {showApiKeyInput && !togetherApiKey && (
                        <div className="mb-4 space-y-3">
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-3">
                            <p className="text-sm text-blue-800">
                              <strong>ℹ️ API Key Not Configured</strong>
                              <br />
                              To use AI-powered explanations, you need to:
                              <ol className="list-decimal ml-5 mt-2 space-y-1">
                                <li>Get your API key from <a href="https://api.together.xyz/settings/api-keys" target="_blank" rel="noopener noreferrer" className="underline font-medium">Together AI</a></li>
                                <li>Set it in your environment: <code className="bg-blue-100 px-2 py-0.5 rounded">TOGETHER_API_KEY=your_key</code></li>
                                <li>Restart the backend server</li>
                              </ol>
                            </p>
                          </div>
                          <input
                            type="password"
                            value={togetherApiKey}
                            onChange={(e) => setTogetherApiKey(e.target.value)}
                            placeholder="Or enter Together AI API Key manually..."
                            className="w-full px-4 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                          />
                          <button
                            onClick={handleGenerateExplanation}
                            disabled={!togetherApiKey || explainMutation.isPending}
                            className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {explainMutation.isPending ? 'Generating...' : 'Generate AI Explanation'}
                          </button>
                        </div>
                      )}

                      {explainMutation.isPending && (
                        <div className="flex items-center justify-center py-8 space-x-2">
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
                          <span className="text-gray-700">Generating AI explanation...</span>
                        </div>
                      )}

                      {explainMutation.data && (
                        <div className="bg-white rounded-lg p-6 border border-purple-200">
                          <div 
                            className="prose prose-sm max-w-none text-gray-800"
                            style={{
                              lineHeight: '1.7',
                              whiteSpace: 'pre-wrap'
                            }}
                            dangerouslySetInnerHTML={{ 
                              __html: explainMutation.data.explanation
                                .replace(/<strong>/g, '<strong style="color: #1f2937; font-weight: 600; display: block; margin-top: 16px; margin-bottom: 8px; font-size: 1.05em;">')
                                .replace(/\n\n/g, '<br/><br/>')
                                .replace(/\n/g, '<br/>')
                            }}
                          />
                          {explainMutation.data.status === 'fallback' && (
                            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                              <div className="text-sm text-yellow-800">
                                ⚠️ {explainMutation.data.note}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {!explainMutation.data && !explainMutation.isPending && !showApiKeyInput && (
                        <div className="text-center py-8 text-gray-500">
                          <p>Click "Generate Explanation" to get AI-powered insights about why this customer fits their persona.</p>
                        </div>
                      )}
                    </div>

                    {/* Key Metrics Comparison */}
                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Metrics Table */}
                      <div className="bg-white rounded-xl p-6 border border-gray-200">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Key Metrics</h3>
                        <div className="space-y-3">
                          {customerDetails?.comparisons && Object.entries(customerDetails.comparisons).map(([metric, data]: [string, any]) => (
                            <div key={metric} className="flex items-center justify-between py-2 border-b border-gray-100">
                              <div className="text-sm text-gray-700">{metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                              <div className="flex items-center space-x-3">
                                <span className="text-sm font-semibold text-gray-900">
                                  {typeof data.customer === 'number' ? data.customer.toFixed(2) : data.customer}
                                </span>
                                <span className={`text-xs px-2 py-1 rounded ${
                                  data.status === 'above' ? 'bg-green-100 text-green-700' :
                                  data.status === 'below' ? 'bg-red-100 text-red-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {data.diff_percentage > 0 ? '+' : ''}{data.diff_percentage.toFixed(0)}%
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Radar Chart */}
                      <div className="bg-white rounded-xl p-6 border border-gray-200">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">📈 Behavior Comparison</h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <RadarChart data={getRadarData()}>
                            <PolarGrid stroke="#e5e7eb" />
                            <PolarAngleAxis dataKey="metric" stroke="#6b7280" tick={{ fill: '#4b5563', fontSize: 11 }} />
                            <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#e5e7eb" tick={{ fill: '#4b5563', fontSize: 10 }} />
                            <Radar
                              name="Customer"
                              dataKey="Customer"
                              stroke="#10b981"
                              fill="#10b981"
                              fillOpacity={0.6}
                              isAnimationActive={true}
                            />
                            <Radar
                              name="Persona Average"
                              dataKey="Persona Avg"
                              stroke="#6366f1"
                              fill="#6366f1"
                              fillOpacity={0.3}
                              isAnimationActive={true}
                            />
                            <Legend wrapperStyle={{ fontSize: '12px' }} />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: '#ffffff',
                                border: '1px solid #e5e7eb',
                                borderRadius: '8px',
                                fontSize: '12px',
                              }}
                            />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Demographics */}
                    {customerDetails?.demographics && (
                      <div className="bg-white rounded-xl p-6 border border-gray-200">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">👥 Demographics</h3>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Age</div>
                            <div className="text-lg font-semibold text-gray-900">{customerDetails.demographics.age} years</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Income</div>
                            <div className="text-lg font-semibold text-gray-900">${(customerDetails.demographics.income / 1000).toFixed(0)}K</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Location</div>
                            <div className="text-lg font-semibold text-gray-900">{customerDetails.demographics.urbanicity}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Climate</div>
                            <div className="text-lg font-semibold text-gray-900">{customerDetails.demographics.climate_zone}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Store Distance</div>
                            <div className="text-lg font-semibold text-gray-900">{customerDetails.demographics.distance_to_store.toFixed(1)} mi</div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {recommendations && (
                      <div className="bg-white rounded-xl p-6 border border-gray-200">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">🎯 Recommended Actions</h3>
                        <div className="space-y-3">
                          {recommendations.recommendations.map((rec: Recommendation, idx: number) => (
                            <div
                              key={idx}
                              className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center space-x-2">
                                  <span className={`px-2 py-1 rounded text-xs font-medium border ${getPriorityColor(rec.priority)}`}>
                                    {rec.priority.toUpperCase()}
                                  </span>
                                  <span className="text-xs text-gray-500">{rec.type}</span>
                                </div>
                              </div>
                              <div className="font-semibold text-gray-900 mb-1">{rec.action}</div>
                              <div className="text-sm text-gray-600">{rec.reason}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


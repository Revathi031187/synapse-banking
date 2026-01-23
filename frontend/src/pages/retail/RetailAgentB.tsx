import { useMutation, useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { useState } from 'react';

export default function RetailAgentB() {
  const [selectedCustomer, setSelectedCustomer] = useState('');

  // Get customer list from API
  const { data: customersData } = useQuery({
    queryKey: ['retail-customers'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8002/api/retail/customers');
      if (!res.ok) throw new Error('Failed to fetch customers');
      return res.json();
    }
  });

  // Execute Agent B
  const executeMutation = useMutation({
    mutationFn: async (customerId: string) => {
      const res = await fetch('http://localhost:8002/api/retail/agent_b/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: customerId, top_n: 5 })
      });
      if (!res.ok) throw new Error('Failed to execute Agent B');
      return res.json();
    }
  });

  const customers = customersData?.customers || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">🎯 Agent B: Retail Product Matchmaker</h1>
        <p className="text-gray-400">AI-powered product recommendations for e-commerce</p>
      </div>

      {customers.length === 0 && (
        <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-xl p-6">
          <div className="text-yellow-400 font-semibold mb-2">⚠️ Loading Customers</div>
          <p className="text-gray-300">Fetching customer data from ChromaDB...</p>
        </div>
      )}

      {customers.length > 0 && (
        <>
          {/* Customer Selection */}
          <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
            <h2 className="text-xl font-bold text-white mb-4">Select Customer</h2>
            
            <div className="space-y-4">
              <select
                value={selectedCustomer}
                onChange={(e) => setSelectedCustomer(e.target.value)}
                className="w-full bg-gray-800 text-white border border-purple-500/30 rounded-lg px-4 py-3"
              >
                <option value="">Choose a customer...</option>
                {customers.map((customer: any) => (
                  <option key={customer.customer_id} value={customer.customer_id}>
                    {customer.customer_id} - Intent: {(customer.intent_score * 100).toFixed(0)}% | Cluster {customer.cluster_id}
                  </option>
                ))}
              </select>

              <button
                onClick={() => selectedCustomer && executeMutation.mutate(selectedCustomer)}
                disabled={!selectedCustomer || executeMutation.isPending}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg font-bold transition-all disabled:opacity-50"
              >
                {executeMutation.isPending ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Generating Recommendations...
                  </span>
                ) : (
                  '🎯 Get Product Recommendations'
                )}
              </button>
            </div>

            {executeMutation.isError && (
              <div className="mt-4 bg-red-900/20 border border-red-500/30 rounded-lg p-4">
                <div className="text-red-400 font-semibold">❌ Failed to Generate Recommendations</div>
                <p className="text-gray-300 text-sm">{(executeMutation.error as Error).message}</p>
              </div>
            )}
          </div>

          {/* Recommendations */}
          {executeMutation.isSuccess && executeMutation.data && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {/* Customer Context */}
              <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
                <h2 className="text-xl font-bold text-white mb-4">👤 Customer Context</h2>
                <div className="grid md:grid-cols-4 gap-4">
                  <div className="bg-black/30 rounded-lg p-4">
                    <div className="text-gray-400 text-sm">Customer</div>
                    <div className="text-white font-bold">{executeMutation.data.customer_name}</div>
                  </div>
                  <div className="bg-black/30 rounded-lg p-4">
                    <div className="text-gray-400 text-sm">Purchase Frequency</div>
                    <div className="text-white font-bold">{executeMutation.data.purchase_frequency}</div>
                  </div>
                  <div className="bg-black/30 rounded-lg p-4">
                    <div className="text-gray-400 text-sm">Lifetime Value</div>
                    <div className="text-2xl font-bold text-green-400">
                      ${(executeMutation.data.lifetime_value || 0).toFixed(0)}
                    </div>
                  </div>
                  <div className="bg-black/30 rounded-lg p-4">
                    <div className="text-gray-400 text-sm">Recommendations</div>
                    <div className="text-2xl font-bold text-purple-400">
                      {executeMutation.data.recommendations?.length || 0}
                    </div>
                  </div>
                </div>
              </div>

              {/* Product Recommendations */}
              <div>
                <h2 className="text-2xl font-bold text-white mb-4">🛍️ Recommended Products</h2>
                <div className="space-y-4">
                  {executeMutation.data.recommendations?.map((rec: any, idx: number) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className="text-3xl">#{idx + 1}</span>
                            <div>
                              <h3 className="text-2xl font-bold text-white">{rec.product_name}</h3>
                              <p className="text-sm text-gray-400">{rec.category} • ${rec.price}</p>
                            </div>
                          </div>
                        </div>
                        <div className="text-right ml-6">
                          <div className="text-sm text-gray-400">Affinity Score</div>
                          <div className="text-3xl font-bold text-green-400">
                            {(rec.affinity_score * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>

                      {rec.recommendation_type && (
                        <div className="mb-4">
                          <span className="inline-block px-4 py-2 rounded-full text-sm font-semibold bg-blue-900/30 text-blue-400 border border-blue-500/30">
                            {rec.recommendation_type}
                          </span>
                        </div>
                      )}

                      {rec.reasoning && (
                        <div className="bg-blue-900/20 border border-blue-500/20 rounded-lg p-4">
                          <div className="text-sm font-semibold text-blue-300 mb-2">🤖 AI Reasoning</div>
                          <p className="text-gray-300 text-sm">{rec.reasoning}</p>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </>
      )}

      {/* Info */}
      {!executeMutation.data && agentAResults && (
        <div className="bg-blue-900/20 backdrop-blur-sm rounded-xl p-6 border border-blue-500/20">
          <h3 className="text-lg font-bold text-white mb-3">💡 About Agent B</h3>
          <ul className="text-sm text-gray-300 space-y-2">
            <li>• <strong>Product Affinities:</strong> Frequently bought together recommendations</li>
            <li>• <strong>Basket Completion:</strong> Suggest complementary products for current purchases</li>
            <li>• <strong>Category Expansion:</strong> Introduce customers to new product categories</li>
            <li>• <strong>Personalized Offers:</strong> Match promotions to customer preferences</li>
            <li>• <strong>AI Reasoning:</strong> Together AI explains why each product is recommended</li>
          </ul>
        </div>
      )}
    </div>
  );
}

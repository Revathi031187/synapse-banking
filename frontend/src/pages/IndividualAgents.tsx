import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import { getCustomers, getProducts } from '../services/api';
import { useStore } from '../store/useStore';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

const IndividualAgents = () => {
  const { systemStatus } = useStore();
  const [selectedAgent, setSelectedAgent] = useState('agent_a');
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const { data: customers } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers,
    enabled: systemStatus.system_initialized,
  });

  const { data: products } = useQuery({
    queryKey: ['products'],
    queryFn: getProducts,
    enabled: systemStatus.system_initialized,
  });

  if (!systemStatus.system_initialized) {
    return (
      <Card className="text-center py-12">
        <span className="text-6xl mb-4 block">⚠️</span>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">System Not Initialized</h2>
        <p className="text-gray-600">Please initialize the system first.</p>
      </Card>
    );
  }

  const agents = [
    { id: 'agent_a', name: '🎭 Agent A: Persona Builder', color: 'from-purple-600 to-purple-700' },
    { id: 'agent_b', name: '🔍 Agent B: Product Matchmaker', color: 'from-blue-600 to-blue-700' },
    { id: 'agent_c', name: '💰 Agent C: Offer Engine', color: 'from-orange-600 to-orange-700' },
    { id: 'agent_d', name: '🎯 Agent D: Performance Engine', color: 'from-green-600 to-green-700' },
    { id: 'agent_e', name: '📊 Agent E: MMM Advisor', color: 'from-pink-600 to-pink-700' },
  ];

  const handleExecute = async () => {
    setExecuting(true);
    // Simulate agent execution
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Generate mock results based on agent
    const mockResults: any = {
      agent_a: {
        persona_cluster: Math.floor(Math.random() * 5),
        loyalty_tier: ['Platinum', 'Gold', 'Silver', 'Bronze'][Math.floor(Math.random() * 4)],
        purchase_propensity: (Math.random() * 0.6 + 0.2).toFixed(3),
        crosssell_propensity: (Math.random() * 0.5 + 0.1).toFixed(3),
        churn_propensity: (Math.random() * 0.3).toFixed(3),
        rfm_score: Math.floor(Math.random() * 300 + 200),
        segments: [
          { name: 'High-Value', value: 342 },
          { name: 'Budget', value: 486 },
          { name: 'Impulse', value: 298 },
          { name: 'Research', value: 412 },
          { name: 'Dormant', value: 462 },
        ],
      },
      agent_b: {
        top_products: [
          { name: 'Premium Headphones', score: 0.92 },
          { name: 'Smart Watch', score: 0.87 },
          { name: 'Wireless Earbuds', score: 0.84 },
          { name: 'Fitness Tracker', score: 0.81 },
          { name: 'Laptop Stand', score: 0.78 },
        ],
        match_accuracy: (Math.random() * 0.2 + 0.75).toFixed(3),
        total_matches: Math.floor(Math.random() * 50 + 10),
        categories: ['Electronics', 'Fashion', 'Home', 'Sports'],
      },
      agent_c: {
        base_price: (Math.random() * 200 + 50).toFixed(2),
        discount_pct: Math.floor(Math.random() * 20 + 5),
        final_price: 0,
        message: 'Special offer just for you - Limited time!',
        channel: ['Email', 'Push', 'In-App'][Math.floor(Math.random() * 3)],
        timing: ['Morning', 'Afternoon', 'Evening'][Math.floor(Math.random() * 3)],
      },
      agent_d: {
        total_offers: Math.floor(Math.random() * 100 + 50),
        accepted: Math.floor(Math.random() * 40 + 20),
        conversion_rate: (Math.random() * 0.3 + 0.15).toFixed(3),
        avg_revenue: (Math.random() * 100 + 50).toFixed(2),
        performance: [
          { metric: 'CTR', value: (Math.random() * 3 + 2).toFixed(1) },
          { metric: 'Conversion', value: (Math.random() * 2 + 1).toFixed(1) },
          { metric: 'Revenue', value: Math.floor(Math.random() * 20000 + 10000) },
        ],
      },
      agent_e: {
        total_budget: 50000,
        allocation: {
          'Email': 0.30,
          'Social Media': 0.25,
          'In-App': 0.20,
          'Push': 0.15,
          'SMS': 0.10,
        },
        expected_roi: (Math.random() * 200 + 300).toFixed(0),
        channels: [
          { name: 'Email', allocation: 15000, roi: 420 },
          { name: 'Social', allocation: 12500, roi: 350 },
          { name: 'In-App', allocation: 10000, roi: 580 },
          { name: 'Push', allocation: 7500, roi: 290 },
          { name: 'SMS', allocation: 5000, roi: 310 },
        ],
      },
    };

    const agentResult = mockResults[selectedAgent];
    if (selectedAgent === 'agent_c') {
      agentResult.final_price = (agentResult.base_price * (1 - agentResult.discount_pct / 100)).toFixed(2);
    }

    setResult(agentResult);
    setExecuting(false);
  };

  const renderAgentForm = () => {
    switch (selectedAgent) {
      case 'agent_a':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Select Customer</label>
              <select className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 transition-all font-semibold">
                <option>Choose a customer...</option>
                {customers?.slice(0, 20).map((c: any) => (
                  <option key={c.customer_id} value={c.customer_id}>{c.customer_id}</option>
                ))}
              </select>
            </div>
            <p className="text-gray-600 text-sm">Agent A will segment this customer, assign a persona, and calculate propensity scores.</p>
          </div>
        );

      case 'agent_b':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Select Customer</label>
              <select className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 transition-all font-semibold">
                <option>Choose a customer...</option>
                {customers?.slice(0, 20).map((c: any) => (
                  <option key={c.customer_id} value={c.customer_id}>{c.customer_id}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Number of Matches</label>
              <input type="number" defaultValue={5} min={1} max={20} className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 transition-all font-semibold" />
            </div>
            <p className="text-gray-600 text-sm">Agent B will find the best product matches using ML embeddings.</p>
          </div>
        );

      case 'agent_c':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Select Product</label>
              <select className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 transition-all font-semibold">
                <option>Choose a product...</option>
                {products?.slice(0, 20).map((p: any) => (
                  <option key={p.product_id} value={p.product_id}>{p.product_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Base Price ($)</label>
              <input type="number" defaultValue={100} min={1} className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 transition-all font-semibold" />
            </div>
            <p className="text-gray-600 text-sm">Agent C will create a personalized offer with dynamic pricing.</p>
          </div>
        );

      case 'agent_d':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Time Period</label>
              <select className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 transition-all font-semibold">
                <option>Last 7 Days</option>
                <option>Last 30 Days</option>
                <option>Last 90 Days</option>
              </select>
            </div>
            <p className="text-gray-600 text-sm">Agent D will analyze offer performance and calculate key metrics.</p>
          </div>
        );

      case 'agent_e':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Total Budget ($)</label>
              <input type="number" defaultValue={50000} min={1000} step={1000} className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 transition-all font-semibold" />
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Optimization Goal</label>
              <select className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 transition-all font-semibold">
                <option>Maximize ROI</option>
                <option>Maximize Revenue</option>
                <option>Minimize Cost</option>
              </select>
            </div>
            <p className="text-gray-600 text-sm">Agent E will optimize budget allocation across marketing channels.</p>
          </div>
        );

      default:
        return null;
    }
  };

  const renderAgentResults = () => {
    if (!result) return null;

    switch (selectedAgent) {
      case 'agent_a':
        return (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <div className="grid md:grid-cols-3 gap-4">
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-purple-600 mb-2">Cluster {result.persona_cluster}</div>
                  <div className="text-gray-700 font-semibold">Persona Cluster</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-blue-600 mb-2">{result.loyalty_tier}</div>
                  <div className="text-gray-700 font-semibold">Loyalty Tier</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-green-50 to-green-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-green-600 mb-2">{result.rfm_score}</div>
                  <div className="text-gray-700 font-semibold">RFM Score</div>
                </div>
              </Card>
            </div>

            <Card>
              <h3 className="text-xl font-black text-gray-900 mb-4">Propensity Scores</h3>
              <div className="space-y-3">
                {[
                  { label: 'Purchase', value: result.purchase_propensity, color: '#10b981' },
                  { label: 'Cross-sell', value: result.crosssell_propensity, color: '#f59e0b' },
                  { label: 'Churn Risk', value: result.churn_propensity, color: '#ef4444' },
                ].map((score) => (
                  <div key={score.label}>
                    <div className="flex justify-between mb-1">
                      <span className="font-bold text-gray-700">{score.label}</span>
                      <span className="font-bold" style={{ color: score.color }}>{(parseFloat(score.value) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 h-3 rounded-full overflow-hidden">
                      <div className="h-full transition-all duration-500" style={{ width: `${parseFloat(score.value) * 100}%`, backgroundColor: score.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h3 className="text-xl font-black text-gray-900 mb-4">Customer Segments</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={result.segments} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                    {result.segments.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>
        );

      case 'agent_b':
        return (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <div className="grid md:grid-cols-3 gap-4">
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-blue-600 mb-2">{result.total_matches}</div>
                  <div className="text-gray-700 font-semibold">Total Matches</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-green-50 to-green-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-green-600 mb-2">{(parseFloat(result.match_accuracy) * 100).toFixed(1)}%</div>
                  <div className="text-gray-700 font-semibold">Match Accuracy</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-purple-600 mb-2">{result.top_products.length}</div>
                  <div className="text-gray-700 font-semibold">Top Products</div>
                </div>
              </Card>
            </div>

            <Card>
              <h3 className="text-xl font-black text-gray-900 mb-4">🏆 Top 5 Product Matches</h3>
              <div className="space-y-3">
                {result.top_products.map((product: any, index: number) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-black text-gray-900 text-lg">#{index + 1} {product.name}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-black text-blue-600">{(product.score * 100).toFixed(0)}%</div>
                        <div className="text-sm text-gray-600 font-semibold">Match Score</div>
                      </div>
                    </div>
                    <div className="mt-2 bg-gray-200 h-2 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-600 transition-all duration-500" style={{ width: `${product.score * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        );

      case 'agent_c':
        return (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
              <h3 className="text-2xl font-black text-gray-900 mb-6 text-center">💰 Personalized Offer Created</h3>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-sm text-gray-600 font-semibold mb-1">Base Price</div>
                  <div className="text-3xl font-black text-gray-900 line-through">${result.base_price}</div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-gray-600 font-semibold mb-1">Discount</div>
                  <div className="text-3xl font-black text-orange-600">{result.discount_pct}% OFF</div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-gray-600 font-semibold mb-1">Final Price</div>
                  <div className="text-4xl font-black text-green-600">${result.final_price}</div>
                </div>
              </div>
              <div className="mt-6 p-4 bg-white rounded-lg">
                <div className="text-center">
                  <div className="text-sm text-gray-600 font-semibold mb-2">💬 Message</div>
                  <div className="text-xl font-bold text-gray-900">"{result.message}"</div>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-white p-3 rounded-lg text-center">
                  <div className="text-sm text-gray-600 font-semibold">📱 Channel</div>
                  <div className="text-lg font-black text-gray-900 mt-1">{result.channel}</div>
                </div>
                <div className="bg-white p-3 rounded-lg text-center">
                  <div className="text-sm text-gray-600 font-semibold">⏰ Timing</div>
                  <div className="text-lg font-black text-gray-900 mt-1">{result.timing}</div>
                </div>
              </div>
            </Card>
          </motion.div>
        );

      case 'agent_d':
        return (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <div className="grid md:grid-cols-4 gap-4">
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-blue-600 mb-2">{result.total_offers}</div>
                  <div className="text-gray-700 font-semibold text-sm">Total Offers</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-green-50 to-green-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-green-600 mb-2">{result.accepted}</div>
                  <div className="text-gray-700 font-semibold text-sm">Accepted</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-orange-600 mb-2">{(parseFloat(result.conversion_rate) * 100).toFixed(1)}%</div>
                  <div className="text-gray-700 font-semibold text-sm">Conversion</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-purple-600 mb-2">${result.avg_revenue}</div>
                  <div className="text-gray-700 font-semibold text-sm">Avg Revenue</div>
                </div>
              </Card>
            </div>

            <Card>
              <h3 className="text-xl font-black text-gray-900 mb-4">📊 Performance Metrics</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={result.performance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>
        );

      case 'agent_e':
        return (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <Card className="bg-gradient-to-br from-pink-50 to-pink-100">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="text-center">
                  <div className="text-sm text-gray-600 font-semibold mb-1">Total Budget</div>
                  <div className="text-5xl font-black text-pink-600">${result.total_budget.toLocaleString()}</div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-gray-600 font-semibold mb-1">Expected ROI</div>
                  <div className="text-5xl font-black text-green-600">{result.expected_roi}%</div>
                </div>
              </div>
            </Card>

            <Card>
              <h3 className="text-xl font-black text-gray-900 mb-4">💸 Recommended Budget Allocation</h3>
              <div className="space-y-3">
                {result.channels.map((channel: any, index: number) => (
                  <div key={channel.name} className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-black text-gray-900 text-lg">{channel.name}</span>
                      <div className="text-right">
                        <div className="text-2xl font-black text-blue-600">${channel.allocation.toLocaleString()}</div>
                        <div className="text-sm text-green-600 font-bold">{channel.roi}% ROI</div>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 h-3 rounded-full overflow-hidden">
                      <div className="h-full transition-all duration-500" style={{ width: `${(channel.allocation / result.total_budget) * 100}%`, backgroundColor: COLORS[index % COLORS.length] }} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h1 className="text-4xl font-black text-gray-900 mb-2">⚙️ Individual Agent Execution</h1>
      <p className="text-xl text-gray-600 mb-8">Run and test each AI agent separately</p>

      {/* Agent Selector */}
      <div className="flex gap-3 mb-8 overflow-x-auto pb-2">
        {agents.map((agent) => (
          <button
            key={agent.id}
            onClick={() => {
              setSelectedAgent(agent.id);
              setResult(null);
            }}
            className={`px-6 py-3 rounded-lg font-bold whitespace-nowrap transition-all ${
              selectedAgent === agent.id
                ? `bg-gradient-to-r ${agent.color} text-white shadow-lg scale-105`
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            {agent.name}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <Card className="mb-8">
        <h3 className="text-2xl font-black text-gray-900 mb-6">⚙️ Configuration</h3>
        {renderAgentForm()}
        <Button
          onClick={handleExecute}
          loading={executing}
          className="w-full mt-6"
          size="lg"
        >
          🚀 Execute {agents.find(a => a.id === selectedAgent)?.name.split(':')[0]}
        </Button>
      </Card>

      {/* Results */}
      {executing && (
        <Card>
          <LoadingSpinner message={`Executing ${agents.find(a => a.id === selectedAgent)?.name}...`} size="lg" />
        </Card>
      )}

      {result && !executing && (
        <div>
          <h3 className="text-3xl font-black text-gray-900 mb-6">✅ Execution Results</h3>
          {renderAgentResults()}
        </div>
      )}
    </motion.div>
  );
};

export default IndividualAgents;

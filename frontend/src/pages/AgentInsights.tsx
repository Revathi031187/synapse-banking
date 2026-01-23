import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Card from '../components/Card';
import { useStore } from '../store/useStore';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const AgentInsights = () => {
  const { systemStatus } = useStore();
  const [selectedAgent, setSelectedAgent] = useState('agent_a');

  if (!systemStatus.system_initialized) {
    return (
      <Card className="text-center py-12">
        <span className="text-6xl mb-4 block">⚠️</span>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">System Not Initialized</h2>
        <p className="text-gray-600">Please initialize the system first from the Overview page.</p>
      </Card>
    );
  }

  const agents = [
    { id: 'agent_a', name: '🎭 Agent A: Persona Builder', color: '#8b5cf6' },
    { id: 'agent_b', name: '🔍 Agent B: Product Matchmaker', color: '#3b82f6' },
    { id: 'agent_c', name: '💰 Agent C: Offer Engine', color: '#f59e0b' },
    { id: 'agent_d', name: '🎯 Agent D: Performance Engine', color: '#10b981' },
    { id: 'agent_e', name: '📊 Agent E: MMM Advisor', color: '#ec4899' },
  ];

  // Mock data - in real app, fetch from API
  const personaData = [
    { name: 'High-Value Loyalists', count: 342, percentage: 17 },
    { name: 'Budget Shoppers', count: 486, percentage: 24 },
    { name: 'Impulse Buyers', count: 298, percentage: 15 },
    { name: 'Research Driven', count: 412, percentage: 21 },
    { name: 'Dormant Users', count: 462, percentage: 23 },
  ];

  const productMatchData = [
    { category: 'Electronics', matches: 1240, accuracy: 87 },
    { category: 'Fashion', matches: 980, accuracy: 82 },
    { category: 'Home', matches: 756, accuracy: 79 },
    { category: 'Sports', matches: 642, accuracy: 85 },
    { category: 'Books', matches: 534, accuracy: 91 },
  ];

  const offerPerformance = [
    { discount: '5%', conversion: 12, revenue: 24500 },
    { discount: '10%', conversion: 18, revenue: 42300 },
    { discount: '15%', conversion: 24, revenue: 58900 },
    { discount: '20%', conversion: 31, revenue: 71200 },
    { discount: '25%', conversion: 28, revenue: 64800 },
  ];

  const performanceMetrics = [
    { week: 'Week 1', ctr: 3.2, conversion: 1.8, revenue: 12400 },
    { week: 'Week 2', ctr: 3.8, conversion: 2.1, revenue: 15600 },
    { week: 'Week 3', ctr: 4.2, conversion: 2.5, revenue: 18200 },
    { week: 'Week 4', ctr: 4.6, conversion: 2.8, revenue: 21500 },
  ];

  const channelROI = [
    { name: 'Email', roi: 420, spend: 5000 },
    { name: 'Social', roi: 350, spend: 8000 },
    { name: 'In-App', roi: 580, spend: 4000 },
    { name: 'Push', roi: 290, spend: 3000 },
    { name: 'SMS', roi: 310, spend: 2500 },
  ];

  const renderAgentContent = () => {
    switch (selectedAgent) {
      case 'agent_a':
        return (
          <div className="space-y-6">
            <Card>
              <h3 className="text-2xl font-black text-gray-900 mb-4">📊 Customer Segmentation</h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie data={personaData} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                        {personaData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-3">
                  {personaData.map((persona, index) => (
                    <div key={persona.name} className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-gray-900">{persona.name}</span>
                        <span className="text-2xl font-black" style={{ color: COLORS[index] }}>{persona.percentage}%</span>
                      </div>
                      <div className="text-sm text-gray-600">{persona.count.toLocaleString()} customers</div>
                      <div className="mt-2 bg-gray-200 h-2 rounded-full overflow-hidden">
                        <div className="h-full" style={{ width: `${persona.percentage * 4}%`, backgroundColor: COLORS[index] }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>

            <div className="grid md:grid-cols-3 gap-6">
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-purple-600 mb-2">2,000</div>
                  <div className="text-gray-700 font-semibold">Total Customers</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-blue-600 mb-2">87%</div>
                  <div className="text-gray-700 font-semibold">Clustering Accuracy</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-green-50 to-green-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-green-600 mb-2">5</div>
                  <div className="text-gray-700 font-semibold">Persona Clusters</div>
                </div>
              </Card>
            </div>
          </div>
        );

      case 'agent_b':
        return (
          <div className="space-y-6">
            <Card>
              <h3 className="text-2xl font-black text-gray-900 mb-4">🔍 Product Matching Performance</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={productMatchData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="matches" fill="#3b82f6" name="Total Matches" />
                  <Bar yAxisId="right" dataKey="accuracy" fill="#10b981" name="Accuracy %" />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <div className="grid md:grid-cols-3 gap-6">
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-blue-600 mb-2">4,152</div>
                  <div className="text-gray-700 font-semibold">Total Matches</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-green-50 to-green-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-green-600 mb-2">84.8%</div>
                  <div className="text-gray-700 font-semibold">Avg Accuracy</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-purple-600 mb-2">100</div>
                  <div className="text-gray-700 font-semibold">Product Catalog</div>
                </div>
              </Card>
            </div>
          </div>
        );

      case 'agent_c':
        return (
          <div className="space-y-6">
            <Card>
              <h3 className="text-2xl font-black text-gray-900 mb-4">💰 Discount vs Performance</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={offerPerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="discount" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="conversion" stroke="#f59e0b" strokeWidth={3} name="Conversion Rate %" />
                  <Line yAxisId="right" type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={3} name="Revenue ($)" />
                </LineChart>
              </ResponsiveContainer>
            </Card>

            <div className="grid md:grid-cols-4 gap-4">
              <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-orange-600 mb-2">20%</div>
                  <div className="text-gray-700 font-semibold text-sm">Optimal Discount</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-green-50 to-green-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-green-600 mb-2">$71.2K</div>
                  <div className="text-gray-700 font-semibold text-sm">Peak Revenue</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-blue-600 mb-2">31%</div>
                  <div className="text-gray-700 font-semibold text-sm">Max Conversion</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
                <div className="text-center">
                  <div className="text-4xl font-black text-purple-600 mb-2">1,847</div>
                  <div className="text-gray-700 font-semibold text-sm">Offers Created</div>
                </div>
              </Card>
            </div>
          </div>
        );

      case 'agent_d':
        return (
          <div className="space-y-6">
            <Card>
              <h3 className="text-2xl font-black text-gray-900 mb-4">🎯 Performance Trends</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={performanceMetrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="ctr" stroke="#3b82f6" strokeWidth={3} name="CTR %" />
                  <Line yAxisId="left" type="monotone" dataKey="conversion" stroke="#10b981" strokeWidth={3} name="Conversion %" />
                  <Line yAxisId="right" type="monotone" dataKey="revenue" stroke="#f59e0b" strokeWidth={3} name="Revenue ($)" />
                </LineChart>
              </ResponsiveContainer>
            </Card>

            <div className="grid md:grid-cols-3 gap-6">
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-blue-600 mb-2">4.6%</div>
                  <div className="text-gray-700 font-semibold">Current CTR</div>
                  <div className="text-green-600 font-bold mt-2">↑ +43% vs Week 1</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-green-50 to-green-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-green-600 mb-2">2.8%</div>
                  <div className="text-gray-700 font-semibold">Conversion Rate</div>
                  <div className="text-green-600 font-bold mt-2">↑ +55% vs Week 1</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-orange-600 mb-2">$67.7K</div>
                  <div className="text-gray-700 font-semibold">Total Revenue</div>
                  <div className="text-green-600 font-bold mt-2">↑ +73% growth</div>
                </div>
              </Card>
            </div>
          </div>
        );

      case 'agent_e':
        return (
          <div className="space-y-6">
            <Card>
              <h3 className="text-2xl font-black text-gray-900 mb-4">📊 Channel ROI Analysis</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={channelROI}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="roi" fill="#ec4899" name="ROI %" />
                  <Bar yAxisId="right" dataKey="spend" fill="#8b5cf6" name="Spend ($)" />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <div className="grid md:grid-cols-3 gap-6">
              <Card className="bg-gradient-to-br from-pink-50 to-pink-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-pink-600 mb-2">390%</div>
                  <div className="text-gray-700 font-semibold">Avg ROI</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-purple-600 mb-2">$22.5K</div>
                  <div className="text-gray-700 font-semibold">Total Spend</div>
                </div>
              </Card>
              <Card className="bg-gradient-to-br from-green-50 to-green-100">
                <div className="text-center">
                  <div className="text-5xl font-black text-green-600 mb-2">In-App</div>
                  <div className="text-gray-700 font-semibold">Best Channel</div>
                  <div className="text-green-600 font-bold mt-2">580% ROI</div>
                </div>
              </Card>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h1 className="text-4xl font-black text-gray-900 mb-2">🤖 Agent Insights</h1>
      <p className="text-xl text-gray-600 mb-8">Deep dive into how each AI agent makes decisions</p>

      {/* Agent Selector */}
      <div className="flex gap-3 mb-8 overflow-x-auto pb-2">
        {agents.map((agent) => (
          <button
            key={agent.id}
            onClick={() => setSelectedAgent(agent.id)}
            className={`px-6 py-3 rounded-lg font-bold whitespace-nowrap transition-all ${
              selectedAgent === agent.id
                ? 'scale-105 shadow-lg text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
            style={{
              backgroundColor: selectedAgent === agent.id ? agent.color : undefined,
            }}
          >
            {agent.name}
          </button>
        ))}
      </div>

      {/* Agent Content */}
      <motion.div key={selectedAgent} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        {renderAgentContent()}
      </motion.div>
    </motion.div>
  );
};

export default AgentInsights;

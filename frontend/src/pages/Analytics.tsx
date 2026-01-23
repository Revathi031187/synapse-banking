import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Card from '../components/Card';
import LoadingSpinner from '../components/LoadingSpinner';
import { useStore } from '../store/useStore';
import axios from 'axios';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Analytics = () => {
  const { systemStatus } = useStore();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<any>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!systemStatus.system_initialized) {
        return;
      }

      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/api/analytics/full`);
        setAnalytics(response.data);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [systemStatus.system_initialized]);

  if (!systemStatus.system_initialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-12 max-w-md">
          <div className="animate-pulse mb-6">
            <span className="text-6xl block">🤖</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading AI System...</h2>
          <p className="text-gray-600 mb-4">Initializing analytics engine</p>
          <LoadingSpinner size="md" />
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-12">
          <LoadingSpinner message="Analyzing all synthetic data..." size="lg" />
          <p className="text-gray-600 mt-4">Computing metrics for 2000+ customers</p>
        </Card>
      </div>
    );
  }

  if (!analytics) {
    return (
      <Card className="text-center py-12">
        <span className="text-6xl mb-4 block">⚠️</span>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Analytics Not Available</h2>
        <p className="text-gray-600">Unable to load analytics data</p>
      </Card>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="mb-8">
        <h1 className="text-4xl font-black text-gray-900 mb-2">📈 Business Analytics</h1>
        <p className="text-xl text-gray-600">
          Comprehensive insights across all {analytics.total_customers?.toLocaleString()} customers and {analytics.total_transactions?.toLocaleString()} transactions
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <div className="text-center">
            <div className="text-4xl font-black text-blue-600 mb-1">
              ${(analytics.total_revenue / 1000).toFixed(1)}K
            </div>
            <div className="text-gray-700 font-semibold text-sm">Total Revenue</div>
            <div className="text-blue-600 font-bold text-sm mt-1">All Customers</div>
          </div>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-green-100">
          <div className="text-center">
            <div className="text-4xl font-black text-green-600 mb-1">
              {analytics.total_transactions?.toLocaleString()}
            </div>
            <div className="text-gray-700 font-semibold text-sm">Total Orders</div>
            <div className="text-green-600 font-bold text-sm mt-1">Complete Dataset</div>
          </div>
        </Card>
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
          <div className="text-center">
            <div className="text-4xl font-black text-orange-600 mb-1">
              ${analytics.avg_order_value?.toFixed(2)}
            </div>
            <div className="text-gray-700 font-semibold text-sm">Avg Order Value</div>
            <div className="text-orange-600 font-bold text-sm mt-1">Per Transaction</div>
          </div>
        </Card>
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
          <div className="text-center">
            <div className="text-4xl font-black text-purple-600 mb-1">
              {analytics.total_customers?.toLocaleString()}
            </div>
            <div className="text-gray-700 font-semibold text-sm">Total Customers</div>
            <div className="text-purple-600 font-bold text-sm mt-1">Active Users</div>
          </div>
        </Card>
      </div>

      {/* Daily Revenue Trend */}
      {analytics.daily_revenue && analytics.daily_revenue.length > 0 && (
        <Card className="mb-8">
          <h2 className="text-2xl font-black text-gray-900 mb-4">📊 Daily Revenue Trend</h2>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={analytics.daily_revenue}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Area yAxisId="left" type="monotone" dataKey="revenue" stroke="#3b82f6" fillOpacity={1} fill="url(#colorRevenue)" name="Revenue ($)" />
              <Line yAxisId="right" type="monotone" dataKey="orders" stroke="#10b981" strokeWidth={3} name="Orders" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Channel Distribution & Category Performance */}
      <div className="grid md:grid-cols-2 gap-8 mb-8">
        {analytics.channel_distribution && (
          <Card>
            <h2 className="text-2xl font-black text-gray-900 mb-4">📱 Channel Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie 
                  data={analytics.channel_distribution} 
                  dataKey="count" 
                  nameKey="channel" 
                  cx="50%" 
                  cy="50%" 
                  outerRadius={100} 
                  label={(entry) => `${entry.percentage}%`}
                >
                  {analytics.channel_distribution.map((_: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {analytics.channel_distribution.map((channel: any, index: number) => (
                <div key={channel.channel} className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded" style={{ backgroundColor: COLORS[index] }} />
                    <span className="font-semibold text-gray-700">{channel.channel}</span>
                  </div>
                  <span className="font-bold text-gray-900">{channel.count.toLocaleString()} orders</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {analytics.category_performance && (
          <Card>
            <h2 className="text-2xl font-black text-gray-900 mb-4">📦 Category Performance</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.category_performance} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="category" width={120} />
                <Tooltip />
                <Bar dataKey="revenue" fill="#3b82f6" name="Revenue ($)" />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {analytics.category_performance.map((cat: any) => (
                <div key={cat.category} className="flex justify-between items-center">
                  <span className="font-semibold text-gray-700">{cat.category}</span>
                  <span className="font-bold text-gray-900">${(cat.revenue / 1000).toFixed(1)}K</span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Loyalty Tiers & Top Customers */}
      <div className="grid md:grid-cols-2 gap-8 mb-8">
        {analytics.loyalty_distribution && (
          <Card>
            <h2 className="text-2xl font-black text-gray-900 mb-4">💎 Customer Segments</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.loyalty_distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tier" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8b5cf6" name="Customers" />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-4 grid grid-cols-2 gap-4">
              {analytics.loyalty_distribution.slice(0, 2).map((tier: any) => (
                <div key={tier.tier} className="bg-purple-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-black text-purple-600">{tier.count}</div>
                  <div className="text-sm text-gray-700 font-semibold">{tier.tier}</div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {analytics.top_products && (
          <Card>
            <h2 className="text-2xl font-black text-gray-900 mb-4">🏆 Top Products</h2>
            <div className="space-y-3">
              {analytics.top_products.slice(0, 5).map((product: any, index: number) => (
                <motion.div
                  key={product.product_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center justify-between p-3 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="text-2xl font-black text-yellow-600">#{index + 1}</div>
                    <div>
                      <p className="font-bold text-gray-900">{product.product_name}</p>
                      <p className="text-sm text-gray-600">{product.category}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-green-600">${product.total_revenue?.toFixed(0)}</p>
                    <p className="text-sm text-gray-600">{product.purchase_count} sales</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-200">
          <h3 className="text-xl font-black text-gray-900 mb-4">📊 Dataset Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-700">Total Customers:</span>
              <span className="font-bold text-gray-900">{analytics.total_customers?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Total Products:</span>
              <span className="font-bold text-gray-900">{analytics.total_products?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Total Transactions:</span>
              <span className="font-bold text-gray-900">{analytics.total_transactions?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Total Events:</span>
              <span className="font-bold text-gray-900">{analytics.total_events?.toLocaleString()}</span>
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-200">
          <h3 className="text-xl font-black text-gray-900 mb-4">💰 Revenue Stats</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-700">Total Revenue:</span>
              <span className="font-bold text-gray-900">${(analytics.total_revenue / 1000).toFixed(1)}K</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Avg Order Value:</span>
              <span className="font-bold text-gray-900">${analytics.avg_order_value?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Avg Customer Value:</span>
              <span className="font-bold text-gray-900">${analytics.avg_customer_value?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Revenue per Day:</span>
              <span className="font-bold text-gray-900">${(analytics.avg_daily_revenue || 0).toFixed(2)}</span>
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-2 border-purple-200">
          <h3 className="text-xl font-black text-gray-900 mb-4">🎯 AI Performance</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-700">Active Agents:</span>
              <span className="font-bold text-green-600">5 / 5</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">System Status:</span>
              <span className="font-bold text-green-600">Operational</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Data Quality:</span>
              <span className="font-bold text-green-600">Excellent</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">Model Version:</span>
              <span className="font-bold text-gray-900">2.0.0</span>
            </div>
          </div>
        </Card>
      </div>
    </motion.div>
  );
};

export default Analytics;

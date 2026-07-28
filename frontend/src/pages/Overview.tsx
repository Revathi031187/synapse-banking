import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation, useQuery } from '@tanstack/react-query';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import { useStore } from '../store/useStore';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Overview = () => {
  const { systemStatus, setSystemStatus } = useStore();
  const [numCustomers, setNumCustomers] = useState(2000);
  const [numProducts, setNumProducts] = useState(100);
  const [numTransactions, setNumTransactions] = useState(10000);
  const [numEvents, setNumEvents] = useState(20000);

  // Generate data mutation
  const generateMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${API_URL}/api/generate-data`, {
        num_customers: numCustomers,
        num_products: numProducts,
        num_transactions: numTransactions,
        num_events: numEvents
      });
      
      // Poll for completion
      return new Promise((resolve) => {
        const checkStatus = setInterval(async () => {
          try {
            const statusResponse = await axios.get(`${API_URL}/api/status`);
            if (statusResponse.data.data_generated) {
              clearInterval(checkStatus);
              resolve(response.data);
            }
          } catch (error) {
            console.error('Error checking status:', error);
          }
        }, 2000);
      });
    },
    onSuccess: () => {
      setSystemStatus({ ...systemStatus, data_generated: true });
    }
  });

  // Initialize system mutation
  const initializeMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${API_URL}/api/initialize-system`);
      
      // Poll for completion
      return new Promise((resolve) => {
        const checkStatus = setInterval(async () => {
          try {
            const statusResponse = await axios.get(`${API_URL}/api/status`);
            if (statusResponse.data.system_initialized) {
              clearInterval(checkStatus);
              setSystemStatus({
                data_generated: true,
                system_initialized: true,
                orchestrator_ready: true
              });
              resolve(response.data);
            }
          } catch (error) {
            console.error('Error checking status:', error);
          }
        }, 2000);
      });
    }
  });

  // Check status on mount (but don't refetch while loading)
  const statusQuery = useQuery({
    queryKey: ['status'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/status`);
      setSystemStatus(response.data);
      return response.data;
    },
    refetchInterval: 2000, // Check every 2 seconds
    refetchIntervalInBackground: true
  });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-black text-gray-900 mb-2">
          📊 System Overview
        </h1>
        <p className="text-xl text-gray-600">
          Data Generation & System Initialization
        </p>
      </div>

      {/* Step 1: Generate Data */}
      <Card className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-black text-gray-900 mb-2">
              📦 Step 1: Generate Synthetic Data
            </h2>
            <p className="text-gray-600">
              Configure and generate test data for the AI system
            </p>
          </div>
          {systemStatus.data_generated && (
            <div className="flex items-center gap-2 bg-green-100 text-green-700 px-4 py-2 rounded-lg font-semibold">
              <span className="text-xl">✓</span>
              Data Ready
            </div>
          )}
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">
              Number of Customers
            </label>
            <input
              type="number"
              value={numCustomers}
              onChange={(e) => setNumCustomers(Number(e.target.value))}
              min={100}
              max={10000}
              disabled={generateMutation.isPending || systemStatus.data_generated}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all font-semibold disabled:bg-gray-100"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">
              Number of Products
            </label>
            <input
              type="number"
              value={numProducts}
              onChange={(e) => setNumProducts(Number(e.target.value))}
              min={50}
              max={500}
              disabled={generateMutation.isPending || systemStatus.data_generated}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all font-semibold disabled:bg-gray-100"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">
              Number of Transactions
            </label>
            <input
              type="number"
              value={numTransactions}
              onChange={(e) => setNumTransactions(Number(e.target.value))}
              min={1000}
              max={50000}
              disabled={generateMutation.isPending || systemStatus.data_generated}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all font-semibold disabled:bg-gray-100"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">
              Number of Events
            </label>
            <input
              type="number"
              value={numEvents}
              onChange={(e) => setNumEvents(Number(e.target.value))}
              min={1000}
              max={100000}
              disabled={generateMutation.isPending || systemStatus.data_generated}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all font-semibold disabled:bg-gray-100"
            />
          </div>
        </div>

        {generateMutation.isPending ? (
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-8">
            <LoadingSpinner message="Generating synthetic data..." size="lg" />
            <div className="mt-6 space-y-3">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center justify-between bg-white rounded-lg p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">1</div>
                  <span className="font-semibold text-gray-700">Generating {numCustomers.toLocaleString()} customers</span>
                </div>
                <div className="animate-pulse text-blue-600">⏳</div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="flex items-center justify-between bg-white rounded-lg p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">2</div>
                  <span className="font-semibold text-gray-700">Creating {numProducts.toLocaleString()} products</span>
                </div>
                <div className="animate-pulse text-blue-600">⏳</div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 }}
                className="flex items-center justify-between bg-white rounded-lg p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">3</div>
                  <span className="font-semibold text-gray-700">Simulating {numTransactions.toLocaleString()} transactions</span>
                </div>
                <div className="animate-pulse text-blue-600">⏳</div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 }}
                className="flex items-center justify-between bg-white rounded-lg p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">4</div>
                  <span className="font-semibold text-gray-700">Recording {numEvents.toLocaleString()} behavioral events</span>
                </div>
                <div className="animate-pulse text-blue-600">⏳</div>
              </motion.div>
            </div>
            <p className="text-sm text-gray-600 mt-6 text-center font-medium">
              ⏱️ This may take 30-60 seconds • Please wait...
            </p>
          </div>
        ) : (
          <Button
            onClick={() => generateMutation.mutate()}
            disabled={systemStatus.data_generated}
            size="lg"
            className="w-full"
          >
            {systemStatus.data_generated ? '✓ Data Generated' : '📊 Generate Data'}
          </Button>
        )}

        {generateMutation.isError && (
          <div className="mt-4 bg-red-50 border-2 border-red-200 rounded-lg p-4">
            <p className="text-red-700 font-semibold">
              ❌ Error: {(generateMutation.error as any)?.message || 'Failed to generate data'}
            </p>
          </div>
        )}
      </Card>

      {/* Step 2: Initialize System */}
      <Card className={`mb-8 ${!systemStatus.data_generated ? 'opacity-50' : ''}`}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-black text-gray-900 mb-2">
              🤖 Step 2: Initialize AI System
            </h2>
            <p className="text-gray-600">
              Load data and initialize the 5 AI agents
            </p>
          </div>
          {systemStatus.system_initialized && (
            <div className="flex items-center gap-2 bg-green-100 text-green-700 px-4 py-2 rounded-lg font-semibold">
              <span className="text-xl">✓</span>
              System Ready
            </div>
          )}
        </div>

        {initializeMutation.isPending ? (
          <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-8">
            <LoadingSpinner message="Initializing AI agents..." size="lg" />
            <div className="mt-6 space-y-3">
              {[
                { icon: '🎭', name: 'Agent A: Persona Builder', desc: 'Building customer personas...' },
                { icon: '🔍', name: 'Agent B: Product Matchmaker', desc: 'Creating product embeddings...' },
                { icon: '💰', name: 'Agent C: Offer Engine', desc: 'Configuring offer strategies...' },
                { icon: '🎯', name: 'Agent D: Performance Engine', desc: 'Training ranking models...' },
                { icon: '📊', name: 'Agent E: Marketing Mix Modeler', desc: 'Optimizing channel allocation...' },
              ].map((agent, index) => (
                <motion.div
                  key={agent.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.3 }}
                  className="flex items-center justify-between bg-white rounded-lg p-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-2xl">
                      {agent.icon}
                    </div>
                    <div>
                      <p className="font-bold text-gray-900">{agent.name}</p>
                      <p className="text-sm text-gray-600">{agent.desc}</p>
                    </div>
                  </div>
                  <div className="animate-spin w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full"></div>
                </motion.div>
              ))}
            </div>
            <p className="text-sm text-gray-600 mt-6 text-center font-medium">
              ⏱️ This may take 15-30 seconds • Agents are learning from your data...
            </p>
          </div>
        ) : (
          <Button
            onClick={() => initializeMutation.mutate()}
            disabled={!systemStatus.data_generated || systemStatus.system_initialized}
            size="lg"
            className="w-full"
          >
            {systemStatus.system_initialized ? '✓ System Initialized' : '🤖 Initialize System'}
          </Button>
        )}

        {!systemStatus.data_generated && (
          <p className="text-sm text-gray-500 mt-4 text-center">
            ⚠️ Please generate data first
          </p>
        )}

        {initializeMutation.isError && (
          <div className="mt-4 bg-red-50 border-2 border-red-200 rounded-lg p-4">
            <p className="text-red-700 font-semibold">
              ❌ Error: {(initializeMutation.error as any)?.message || 'Failed to initialize system'}
            </p>
            <p className="text-sm text-red-600 mt-2">
              💡 If you see CSV parsing errors, try regenerating the data
            </p>
          </div>
        )}
      </Card>

      {/* Status Summary */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <div className="text-center">
            <div className="text-5xl mb-4">
              {systemStatus.data_generated ? '✓' : '⏳'}
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Data Generation</h3>
            <p className="text-sm text-gray-600">
              {systemStatus.data_generated ? 'Synthetic data ready' : 'Waiting to generate'}
            </p>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
          <div className="text-center">
            <div className="text-5xl mb-4">
              {systemStatus.system_initialized ? '✓' : '⏳'}
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">AI Initialization</h3>
            <p className="text-sm text-gray-600">
              {systemStatus.system_initialized ? '5 agents active' : 'Waiting to initialize'}
            </p>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100">
          <div className="text-center">
            <div className="text-5xl mb-4">
              {systemStatus.system_initialized ? '🚀' : '⏸️'}
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">System Status</h3>
            <p className="text-sm text-gray-600">
              {systemStatus.system_initialized ? 'Ready for NBA generation' : 'Not ready yet'}
            </p>
          </div>
        </Card>
      </div>

      {/* Next Steps */}
      {systemStatus.system_initialized && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8"
        >
          <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900 mb-3">🎉 System Ready!</h3>
              <p className="text-gray-600 mb-6">
                All AI agents are initialized and ready to generate personalized recommendations
              </p>
              <Button 
                onClick={() => window.location.href = '/nba-generator'}
                size="lg"
                className="bg-gradient-to-r from-green-600 to-blue-600"
              >
                Go to NBA Generator →
              </Button>
            </div>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
};

export default Overview;

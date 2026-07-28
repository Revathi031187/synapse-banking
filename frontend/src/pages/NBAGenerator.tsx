import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useMutation, useQuery } from '@tanstack/react-query';
import Card from '../components/Card';
import Button from '../components/Button';
import NBACard from '../components/NBACard';
import LoadingSpinner from '../components/LoadingSpinner';
import { generateNBA, getCustomers } from '../services/api';
import { useStore } from '../store/useStore';
import type { NBAResponse } from '../types';
import { getAutomaticContext, getDeviceLabel, getLocationLabel, detectDevice, detectLocation } from '../utils/deviceDetection';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const NBAGenerator = () => {
  const { systemStatus, nbaResult, setNbaResult } = useStore();
  const [customerId, setCustomerId] = useState('');
  const [autoContext, setAutoContext] = useState(getAutomaticContext());

  // Update context every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setAutoContext(getAutomaticContext());
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const { data: customers, isLoading: customersLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers,
    enabled: true, // Always try to load customers if system is initialized
  });

  const nbaMutation = useMutation({
    mutationFn: generateNBA,
    onSuccess: (data: NBAResponse) => {
      setNbaResult(data);
    },
  });

  const handleGenerate = () => {
    if (!customerId) {
      alert('Please select a customer');
      return;
    }
    const context = generateContextForCustomer(customerId);
    nbaMutation.mutate({ 
      customer_id: customerId, 
      device: context.device,
      location: context.location,
      session_duration: context.session_duration,
      top_n: 3
    });
  };

  // Check system status
  const { data: systemCheck } = useQuery({
    queryKey: ['system-status'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/status`);
      return response.data;
    },
    refetchInterval: 2000,
  });

  if (!systemStatus.system_initialized && !systemCheck?.system_initialized) {
    return (
      <Card className="text-center py-12">
        <span className="text-6xl mb-4 block">⚠️</span>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">System Not Initialized</h2>
        <p className="text-gray-600 mb-4">Please go to Overview and initialize the system first.</p>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-black text-gray-900 mb-2">
          🎯 Next Best Action Generator
        </h1>
        <p className="text-xl text-gray-600">
          Generate personalized offers powered by 5 AI agents working in real-time
        </p>
      </div>

      {/* Input Form */}
      <Card className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <span className="mr-2">👤</span> SELECT CUSTOMER
        </h2>
        
        <div className="mb-6">
          <label className="block text-sm font-bold text-gray-700 mb-2">
            Customer ID
          </label>
          {customersLoading ? (
            <div className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg bg-gray-50 text-gray-500 flex items-center gap-2">
              <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              Loading customers...
            </div>
          ) : !customers || customers.length === 0 ? (
            <div className="w-full px-4 py-3 border-2 border-red-300 rounded-lg bg-red-50 text-red-600">
              ⚠️ No customers found. Please generate data first.
            </div>
          ) : (
            <select
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all font-semibold"
            >
              <option value="">Choose a customer...</option>
              {customers.slice(0, 100).map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>
                  {customer.customer_id}
                </option>
              ))}
            </select>
          )}
          <p className="text-xs text-gray-500 mt-2">
            💡 {customers?.length ? `${customers.length} customers available` : 'Select a customer to generate personalized recommendations'}
          </p>
        </div>

        {/* Auto-detected Context Display */}
        {customerContext && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200 rounded-lg p-6 mb-6">
            <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              <span className="animate-pulse">🔴</span> CUSTOMER CONTEXT (Simulated)
            </h3>
            <div className="grid md:grid-cols-4 gap-4 text-sm">
              <div className="bg-white rounded-lg p-3">
                <p className="text-gray-600 mb-1 font-medium">Device</p>
                <p className="font-bold text-gray-900">{getDeviceLabelFromType(customerContext.device)}</p>
              </div>
              <div className="bg-white rounded-lg p-3">
                <p className="text-gray-600 mb-1 font-medium">Location</p>
                <p className="font-bold text-gray-900">{getLocationLabelFromType(customerContext.location)}</p>
              </div>
              <div className="bg-white rounded-lg p-3">
                <p className="text-gray-600 mb-1 font-medium">Session Time</p>
                <p className="font-bold text-gray-900">⏱️ {Math.floor(customerContext.session_duration / 60)}m {customerContext.session_duration % 60}s</p>
              </div>
              <div className="bg-white rounded-lg p-3">
                <p className="text-gray-600 mb-1 font-medium">Pages Viewed</p>
                <p className="font-bold text-gray-900">👁️ {customerContext.pages_viewed}</p>
              </div>
            </div>
            <p className="text-xs text-gray-600 mt-3 text-center">
              ✨ Context varies by customer to demonstrate AI personalization
            </p>
          </div>
        )}

        <Button
          onClick={handleGenerate}
          loading={nbaMutation.isPending}
          className="w-full mt-8"
          size="lg"
        >
          🚀 GENERATE NEXT BEST ACTIONS
        </Button>
      </Card>

      {/* Loading State */}
      {nbaMutation.isPending && (
        <Card className="text-center">
          <LoadingSpinner message="AI Agents are collaborating..." size="lg" />
          <div className="mt-6 space-y-2">
            {['🎭 Agent A: Building customer persona...', '🔍 Agent B: Matching products...', '💰 Agent C: Creating offers...', '🎯 Agent D: Ranking actions...', '📊 Agent E: Optimizing strategy...'].map((step, index) => (
              <motion.p
                key={step}
                className="text-gray-600 font-medium"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.3 }}
              >
                {step}
              </motion.p>
            ))}
          </div>
        </Card>
      )}

      {/* Results */}
      {nbaResult && !nbaMutation.isPending && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Customer Persona */}
            <div className="lg:col-span-1">
              <Card className="bg-gradient-to-br from-blue-600 to-blue-700 text-white sticky top-24">
                <h2 className="text-2xl font-black mb-4">👤 CUSTOMER PROFILE</h2>
                
                <div className="space-y-3 mb-6">
                  <div>
                    <p className="text-blue-200 text-sm font-semibold">🎭 Persona</p>
                    <p className="text-xl font-bold">{nbaResult.customer_persona.persona_name}</p>
                  </div>
                  
                  <div>
                    <p className="text-blue-200 text-sm font-semibold">🎯 Intent</p>
                    <p className="text-xl font-bold">{nbaResult.customer_persona.intent}</p>
                    <p className="text-sm text-blue-200">
                      {(nbaResult.customer_persona.intent_confidence * 100).toFixed(0)}% confidence
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-blue-200 text-sm font-semibold">🏆 Loyalty</p>
                    <p className="text-xl font-bold">{nbaResult.customer_persona.loyalty_tier}</p>
                  </div>
                </div>

                <div className="border-t border-blue-500 pt-4">
                  <p className="text-blue-200 font-bold mb-3">📊 RFM SCORES</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-blue-200">⏱️ Recency:</span>
                      <span className="font-bold">{nbaResult.customer_persona.rfm.recency_days} days</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-200">🔢 Frequency:</span>
                      <span className="font-bold">{nbaResult.customer_persona.rfm.frequency} purchases</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-200">💰 Monetary:</span>
                      <span className="font-bold">${nbaResult.customer_persona.rfm.monetary_value.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <div className="border-t border-blue-500 pt-4 mt-4">
                  <p className="text-blue-200 font-bold mb-3">🎯 PROPENSITY SCORES</p>
                  <div className="space-y-2">
                    {[
                      { label: 'Purchase', value: nbaResult.customer_persona.propensity_scores.purchase, color: 'bg-green-500' },
                      { label: 'Cross-sell', value: nbaResult.customer_persona.propensity_scores.crosssell, color: 'bg-yellow-500' },
                      { label: 'Churn', value: nbaResult.customer_persona.propensity_scores.churn, color: 'bg-red-500' },
                    ].map((score) => (
                      <div key={score.label}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-blue-200">{score.label}</span>
                          <span className="font-bold">{(score.value * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-blue-800 rounded-full h-2">
                          <div
                            className={`${score.color} h-2 rounded-full transition-all duration-500`}
                            style={{ width: `${score.value * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </div>

            {/* NBA Cards */}
            <div className="lg:col-span-2">
              <h2 className="text-3xl font-black text-gray-900 mb-6">
                🎯 NEXT BEST ACTIONS
              </h2>
              {nbaResult.next_best_actions.map((nba, index) => (
                <NBACard key={index} nba={nba} rank={index + 1} />
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default NBAGenerator;


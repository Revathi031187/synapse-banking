import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useMutation, useQuery } from '@tanstack/react-query';
import Card from '../components/Card';
import Button from '../components/Button';
import NBACard from '../components/NBACard';
import LoadingSpinner from '../components/LoadingSpinner';
import { generateNBA } from '../services/api';
import { useStore } from '../store/useStore';
import type { NBAResponse } from '../types';
import { getAutomaticContext, getDeviceLabel, getLocationLabel, detectDevice, detectLocation, trackPageView } from '../utils/deviceDetection';
import { getCurrentUser } from '../utils/userContext';

const RecommendationsPage = () => {
  const { systemStatus, nbaResult, setNbaResult } = useStore();
  const [autoContext, setAutoContext] = useState(getAutomaticContext());
  const currentUser = getCurrentUser();

  // Track page view
  useEffect(() => {
    trackPageView();
  }, []);

  // Update context every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setAutoContext(getAutomaticContext());
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const nbaMutation = useMutation({
    mutationFn: generateNBA,
    onSuccess: (data: NBAResponse) => {
      setNbaResult(data);
    },
  });

  const handleGenerateRecommendations = () => {
    const context = getAutomaticContext();
    nbaMutation.mutate({ 
      customer_id: currentUser.customerId, 
      device: context.device,
      location: context.location,
      session_duration: context.session_duration,
      top_n: 3 
    });
  };

  // Auto-generate on page load if system is initialized
  useEffect(() => {
    if (systemStatus.system_initialized && !nbaResult && !nbaMutation.isPending) {
      handleGenerateRecommendations();
    }
  }, [systemStatus.system_initialized]);

  if (!systemStatus.system_initialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-12 max-w-md">
          <div className="animate-pulse mb-6">
            <span className="text-6xl block">🤖</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading AI System...</h2>
          <p className="text-gray-600 mb-4">Initializing personalization agents</p>
          <LoadingSpinner size="md" />
        </Card>
      </div>
    );
  }

  const deviceInfo = detectDevice();
  const locationInfo = detectLocation();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="pb-12"
    >
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-2xl p-8 mb-8 text-white shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black mb-2">
              ✨ Recommended For You
            </h1>
            <p className="text-xl opacity-90">
              Personalized picks powered by AI • Updated in real-time
            </p>
          </div>
          <div className="text-6xl animate-bounce">
            {currentUser.avatar || '👤'}
          </div>
        </div>

        {/* Context Display */}
        <div className="mt-6 flex flex-wrap gap-4 text-sm">
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center gap-2">
            <span className="font-semibold">User:</span>
            <span>{currentUser.name}</span>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center gap-2">
            <span>{getDeviceLabel(deviceInfo)}</span>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center gap-2">
            <span>{getLocationLabel(locationInfo)}</span>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center gap-2">
            <span>⏱️ {Math.floor(autoContext.session_duration / 60)}m {autoContext.session_duration % 60}s</span>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 flex items-center gap-2">
            <span>👁️ {autoContext.pages_viewed} pages</span>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {nbaMutation.isPending && (
        <Card className="text-center mb-8">
          <LoadingSpinner message="AI is analyzing your preferences..." size="lg" />
          <div className="mt-6 space-y-2">
            {[
              '🎭 Understanding your preferences...',
              '🔍 Finding perfect matches...',
              '💎 Creating exclusive offers...',
              '🎯 Ranking by relevance...',
              '✨ Personalizing your experience...'
            ].map((step, index) => (
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
            {/* Customer Persona - Sidebar */}
            <div className="lg:col-span-1">
              <Card className="bg-gradient-to-br from-indigo-600 to-purple-700 text-white sticky top-24">
                <h2 className="text-2xl font-black mb-6 flex items-center gap-2">
                  <span>👤</span> YOUR PROFILE
                </h2>
                
                {/* User Info */}
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-4xl">{currentUser.avatar}</span>
                    <div>
                      <p className="font-bold text-lg">{currentUser.name}</p>
                      <p className="text-sm text-indigo-200">{currentUser.email}</p>
                    </div>
                  </div>
                </div>

                {/* Persona Info */}
                <div className="space-y-4 mb-6">
                  <div>
                    <p className="text-indigo-200 text-sm font-semibold">🎭 Shopping Style</p>
                    <p className="text-xl font-bold">{nbaResult.customer_persona.persona_name}</p>
                  </div>
                  
                  <div>
                    <p className="text-indigo-200 text-sm font-semibold">🎯 Current Intent</p>
                    <p className="text-xl font-bold">{nbaResult.customer_persona.intent}</p>
                    <div className="mt-2 bg-white/20 rounded-full h-2">
                      <div 
                        className="bg-green-400 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${nbaResult.customer_persona.intent_confidence * 100}%` }}
                      />
                    </div>
                    <p className="text-sm text-indigo-200 mt-1">
                      {(nbaResult.customer_persona.intent_confidence * 100).toFixed(0)}% confidence
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-indigo-200 text-sm font-semibold">🏆 Status</p>
                    <p className="text-xl font-bold">{nbaResult.customer_persona.loyalty_tier}</p>
                  </div>
                </div>

                {/* RFM Scores */}
                <div className="border-t border-indigo-500 pt-4 mb-4">
                  <p className="text-indigo-200 font-bold mb-3">📊 SHOPPING BEHAVIOR</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between bg-white/10 rounded px-3 py-2">
                      <span className="text-indigo-200">⏱️ Last Purchase:</span>
                      <span className="font-bold">{nbaResult.customer_persona.rfm.recency_days} days ago</span>
                    </div>
                    <div className="flex justify-between bg-white/10 rounded px-3 py-2">
                      <span className="text-indigo-200">🔢 Total Orders:</span>
                      <span className="font-bold">{nbaResult.customer_persona.rfm.frequency}</span>
                    </div>
                    <div className="flex justify-between bg-white/10 rounded px-3 py-2">
                      <span className="text-indigo-200">💰 Total Spent:</span>
                      <span className="font-bold">${nbaResult.customer_persona.rfm.monetary_value.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                {/* Propensity Scores */}
                <div className="border-t border-indigo-500 pt-4">
                  <p className="text-indigo-200 font-bold mb-3">🎯 LIKELIHOOD TO...</p>
                  <div className="space-y-3">
                    {[
                      { label: 'Purchase Soon', value: nbaResult.customer_persona.propensity_scores.purchase, color: 'bg-green-400', emoji: '🛍️' },
                      { label: 'Try New Products', value: nbaResult.customer_persona.propensity_scores.crosssell, color: 'bg-yellow-400', emoji: '✨' },
                      { label: 'Need Attention', value: nbaResult.customer_persona.propensity_scores.churn, color: 'bg-red-400', emoji: '⚠️' },
                    ].map((score) => (
                      <div key={score.label}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-indigo-200">{score.emoji} {score.label}</span>
                          <span className="font-bold">{(score.value * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-indigo-900/50 rounded-full h-2">
                          <div
                            className={`${score.color} h-2 rounded-full transition-all duration-500`}
                            style={{ width: `${score.value * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Refresh Button */}
                <Button
                  onClick={handleGenerateRecommendations}
                  loading={nbaMutation.isPending}
                  className="w-full mt-6 bg-white text-indigo-600 hover:bg-indigo-50"
                >
                  🔄 Refresh Recommendations
                </Button>
              </Card>
            </div>

            {/* Recommendations */}
            <div className="lg:col-span-2">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-black text-gray-900">
                  🎯 Your Personalized Picks
                </h2>
                <div className="text-sm text-gray-500">
                  Updated {new Date().toLocaleTimeString()}
                </div>
              </div>
              
              <div className="space-y-6">
                {nbaResult.next_best_actions.map((nba, index) => (
                  <NBACard key={index} nba={nba} rank={index + 1} />
                ))}
              </div>

              {/* Additional Call to Action */}
              <Card className="mt-8 bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      💡 Want more personalized recommendations?
                    </h3>
                    <p className="text-gray-600">
                      Keep browsing and we'll continue to refine your suggestions in real-time
                    </p>
                  </div>
                  <Button onClick={handleGenerateRecommendations} loading={nbaMutation.isPending}>
                    Get More
                  </Button>
                </div>
              </Card>
            </div>
          </div>
        </motion.div>
      )}

      {/* Empty State (if no results yet) */}
      {!nbaResult && !nbaMutation.isPending && (
        <Card className="text-center py-12">
          <span className="text-6xl mb-4 block">🎁</span>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Ready to discover amazing products?</h2>
          <p className="text-gray-600 mb-6">Let our AI find the perfect matches for you</p>
          <Button onClick={handleGenerateRecommendations} size="lg">
            ✨ Get Personalized Recommendations
          </Button>
        </Card>
      )}
    </motion.div>
  );
};

export default RecommendationsPage;


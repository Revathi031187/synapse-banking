import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, Brain, TrendingUp, Target } from 'lucide-react';

export default function IndustrySelector() {
  const navigate = useNavigate();
  
  const { data: industriesData, isLoading } = useQuery({
    queryKey: ['industries'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8002/api/industries');
      if (!res.ok) throw new Error('Failed to fetch industries');
      return res.json();
    }
  });
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-7xl mb-4 animate-bounce">🚀</div>
          <div className="text-gray-900 text-2xl font-semibold">Loading NBA Platform...</div>
          <div className="text-gray-600 text-sm mt-2">Initializing AI agents</div>
        </div>
      </div>
    );
  }
  
  const industries = industriesData?.industries || [];
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <div className="inline-block mb-6">
            <span className="text-7xl">🚀</span>
          </div>
          <h1 className="text-6xl font-bold text-gray-900 mb-6">
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              NBA Personalization Platform
            </span>
          </h1>
          <p className="text-gray-700 text-2xl mb-3 font-medium">
            AI-Powered Next Best Action Intelligence
          </p>
          <p className="text-gray-500 text-lg">
            Powered by Advanced Machine Learning • LLM-Enhanced Insights
          </p>
          
          {/* Metrics Banner */}
          <div className="flex justify-center gap-8 mt-8">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">3</div>
              <div className="text-sm text-gray-600">Industries</div>
            </div>
            <div className="w-px bg-gray-300"></div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">2</div>
              <div className="text-sm text-gray-600">AI Agents</div>
            </div>
            <div className="w-px bg-gray-300"></div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">∞</div>
              <div className="text-sm text-gray-600">Insights</div>
            </div>
          </div>
        </motion.div>
        
        {/* Industry Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {industries.map((industry: any, index: number) => (
            <motion.button
              key={industry.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02, y: -4 }}
              onClick={() => navigate(`/${industry.id}`)}
              className="card text-left group hover:shadow-2xl transition-all duration-300 overflow-hidden"
            >
              <div className="card-body">
                {/* Icon */}
                <div className="text-7xl mb-6 group-hover:scale-110 transition-transform duration-300">
                  {industry.icon}
                </div>
                
                {/* Title */}
                <h2 className="text-2xl font-bold text-gray-900 mb-3 group-hover:text-blue-600 transition-colors">
                  {industry.name}
                </h2>
                
                {/* Description */}
                <p className="text-gray-600 text-sm mb-6 leading-relaxed">
                  {industry.description}
                </p>
                
                {/* Use Cases */}
                <div className="flex flex-wrap gap-2 mb-6">
                  {industry.use_cases.map((useCase: string) => (
                    <span
                      key={useCase}
                      className="text-xs badge badge-blue"
                    >
                      {useCase}
                    </span>
                  ))}
                </div>
                
                {/* CTA */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200 group-hover:border-blue-300 transition-colors">
                  <span className="text-blue-600 font-semibold text-sm">Launch Platform</span>
                  <ArrowRight className="w-5 h-5 text-blue-600 group-hover:translate-x-2 transition-transform duration-300" />
                </div>
              </div>
            </motion.button>
          ))}
        </div>
        
        {/* Features Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="card bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200"
        >
          <div className="card-body">
            <h3 className="text-3xl font-bold text-gray-900 mb-8 text-center flex items-center justify-center gap-3">
              <Sparkles className="w-8 h-8 text-purple-600" />
              <span>Platform Capabilities</span>
            </h3>
            <div className="grid md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="bg-white rounded-xl p-4 shadow-sm mb-4 inline-block">
                  <Brain className="w-10 h-10 text-blue-600" />
                </div>
                <div className="text-gray-900 font-semibold text-lg mb-2">AI Agents</div>
                <div className="text-gray-600 text-sm">Persona Builder + Product Matchmaker</div>
              </div>
              <div className="text-center">
                <div className="bg-white rounded-xl p-4 shadow-sm mb-4 inline-block">
                  <Target className="w-10 h-10 text-green-600" />
                </div>
                <div className="text-gray-900 font-semibold text-lg mb-2">Signal Detection</div>
                <div className="text-gray-600 text-sm">Life Events, Intent & Behavior Analysis</div>
              </div>
              <div className="text-center">
                <div className="bg-white rounded-xl p-4 shadow-sm mb-4 inline-block">
                  <TrendingUp className="w-10 h-10 text-purple-600" />
                </div>
                <div className="text-gray-900 font-semibold text-lg mb-2">Advanced ML</div>
                <div className="text-gray-600 text-sm">RFM, Clustering & Propensity Models</div>
              </div>
              <div className="text-center">
                <div className="bg-white rounded-xl p-4 shadow-sm mb-4 inline-block">
                  <Sparkles className="w-10 h-10 text-orange-600" />
                </div>
                <div className="text-gray-900 font-semibold text-lg mb-2">AI Insights</div>
                <div className="text-gray-600 text-sm">LLM-Powered Explanations & Context</div>
              </div>
            </div>
          </div>
        </motion.div>
        
        {/* Key Benefits */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-12"
        >
          <h3 className="text-2xl font-bold text-gray-900 text-center mb-8">Why Choose NBA Platform?</h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="card bg-green-50 border-green-200">
              <div className="card-body text-center">
                <div className="text-4xl mb-3">📈</div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Increase Revenue</h4>
                <p className="text-gray-600 text-sm">Target the right customers with the right products at the right time</p>
              </div>
            </div>
            <div className="card bg-blue-50 border-blue-200">
              <div className="card-body text-center">
                <div className="text-4xl mb-3">⚡</div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Real-Time Insights</h4>
                <p className="text-gray-600 text-sm">Get instant persona identification and product recommendations</p>
              </div>
            </div>
            <div className="card bg-purple-50 border-purple-200">
              <div className="card-body text-center">
                <div className="text-4xl mb-3">🎯</div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Personalized Actions</h4>
                <p className="text-gray-600 text-sm">Deliver hyper-personalized experiences that convert</p>
              </div>
            </div>
          </div>
        </motion.div>
        
        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-16 text-center"
        >
          <div className="bg-white rounded-xl shadow-sm p-8 border border-gray-200">
            <p className="text-gray-600 text-sm mb-4">
              Built with modern technologies for enterprise-scale personalization
            </p>
            <div className="flex justify-center gap-6 flex-wrap">
              <span className="text-xs badge badge-blue">React</span>
              <span className="text-xs badge badge-green">FastAPI</span>
              <span className="text-xs badge badge-purple">Together AI</span>
              <span className="text-xs badge badge-orange">Tailwind CSS</span>
              <span className="text-xs badge badge-blue">ChromaDB</span>
            </div>
            <p className="text-gray-500 text-xs mt-6">
              © 2024 NBA Personalization Platform. All rights reserved.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

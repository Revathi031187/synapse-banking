import React from 'react';
import { Link } from 'react-router-dom';
import { Users, ShoppingBag, Target, ArrowRight } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

export default function AcademyDashboard() {
  // Check if Agent A has been run
  const { data: agentAResults } = useQuery({
    queryKey: ['academy-agent-a-results'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/results`);
      if (!response.ok) {
        return null;
      }
      return response.json();
    },
    staleTime: 0,
    refetchOnMount: true,
    retry: false
  });
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section - Minimal & Professional */}
      <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800">
        <div className="max-w-6xl mx-auto px-8 py-16">
          <div className="flex items-center gap-6 mb-6">
            <div className="w-20 h-20 bg-white rounded-2xl flex items-center justify-center shadow-lg">
              <span className="text-4xl">🏕️</span>
            </div>
            <div>
              <h1 className="text-5xl font-bold text-white tracking-tight">Academy Sports</h1>
              <p className="text-xl text-blue-100 mt-2">Customer Intelligence Platform</p>
            </div>
          </div>
          <p className="text-lg text-blue-50 max-w-2xl">
            AI-powered segmentation and personalized product recommendations for outdoor enthusiasts
          </p>
        </div>
      </div>

      {/* Main Actions - Minimal & Clean */}
      <div className="max-w-6xl mx-auto px-8 py-12">
        <div className="grid md:grid-cols-3 gap-6">

          {/* Customer Segmentation */}
          <Link to="/academy/agent-a" className="h-full">
            <div className="group bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden border border-gray-200 hover:border-blue-500 h-full flex flex-col">
              <div className="p-8 flex flex-col flex-1">
                <div className="w-14 h-14 bg-blue-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform flex-shrink-0">
                  <Users className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Customer Segmentation</h3>
                <p className="text-gray-600 mb-6 flex-1">
                  AI-powered macro and micro segmentation with intelligent personas
                </p>
                <div className="flex items-center text-blue-600 font-semibold group-hover:gap-3 gap-2 transition-all mt-auto">
                  <span>Get Started</span>
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>
            </div>
          </Link>

          {/* Visual Dashboard - Conditional link based on Agent A status */}
          <Link to={agentAResults ? "/academy/macro-dashboard" : "/academy/agent-a"} className="h-full">
            <div className="group bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden border border-gray-200 hover:border-indigo-500 h-full flex flex-col">
              <div className="p-8 flex flex-col flex-1">
                <div className="w-14 h-14 bg-indigo-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform flex-shrink-0">
                  <Target className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Visual Dashboard</h3>
                <p className="text-gray-600 mb-6 flex-1">
                  {agentAResults 
                    ? "Interactive visualization of segments with detailed insights"
                    : "⚠️ Run Agent A first to view macro segments"}
                </p>
                <div className="flex items-center text-indigo-600 font-semibold group-hover:gap-3 gap-2 transition-all mt-auto">
                  <span>{agentAResults ? "View Dashboard" : "Run Agent A First"}</span>
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>
            </div>
          </Link>

          {/* Product Recommendations */}
          <Link to="/academy/agent-b" className="h-full">
            <div className="group bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden border border-gray-200 hover:border-purple-500 h-full flex flex-col">
              <div className="p-8 flex flex-col flex-1">
                <div className="w-14 h-14 bg-purple-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform flex-shrink-0">
                  <ShoppingBag className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Product Recommendations</h3>
                <p className="text-gray-600 mb-6 flex-1">
                  Personalized suggestions based on segment behavior
                </p>
                <div className="flex items-center text-purple-600 font-semibold group-hover:gap-3 gap-2 transition-all mt-auto">
                  <span>Explore Products</span>
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* Footer Info - Minimal */}
      <div className="max-w-6xl mx-auto px-8 pb-12">
        <div className="bg-white rounded-xl shadow-sm p-8 border border-gray-200">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">5,000+</div>
              <div className="text-sm text-gray-600">Customer Profiles</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-indigo-600 mb-2">4-5</div>
              <div className="text-sm text-gray-600">Macro Segments</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600 mb-2">57</div>
              <div className="text-sm text-gray-600">Products Catalog</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}



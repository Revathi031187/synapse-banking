import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Users, ShoppingBag, Target, ArrowRight, Database, CheckCircle2, Clock, BarChart3 } from 'lucide-react';

export default function BankingDashboard() {
  const { data: status } = useQuery({
    queryKey: ['banking-status'],
    queryFn: async () => {
      const res = await fetch('/api/banking/status');
      return res.json();
    }
  });
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section - Professional gradient with bank icon */}
      <div className="bg-gradient-to-br from-blue-700 via-blue-600 to-amber-500">
        <div className="max-w-6xl mx-auto px-8 py-16">
          <div className="flex items-center gap-6 mb-6">
            <div className="w-20 h-20 bg-white rounded-2xl flex items-center justify-center shadow-lg">
              <span className="text-4xl">🏦</span>
            </div>
            <div>
              <h1 className="text-5xl font-bold text-white tracking-tight">F&M Bank</h1>
              <p className="text-xl text-blue-50 mt-2">Farmers & Merchants Bank of Central California</p>
            </div>
          </div>
          <p className="text-lg text-blue-50 max-w-2xl">
            Where Banking Is Easy - Since 1916. AI-powered personalization for Personal, Business & Agricultural Banking.
          </p>
        </div>
      </div>

      {/* Main Actions - Clean & Professional */}
      <div className="max-w-6xl mx-auto px-8 py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Get Started</h2>
        <div className="grid md:grid-cols-3 gap-6 mb-12">

          {/* Data Loader */}
          <Link to="/banking/data-loader" className="h-full">
            <div className="group bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden border border-blue-200 hover:border-green-500 h-full flex flex-col">
              <div className="p-8 flex flex-col flex-1">
                <div className="w-14 h-14 bg-green-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform flex-shrink-0">
                  <Database className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">📊 Load Data</h3>
                <p className="text-gray-600 mb-6 flex-1">
                  Load 5,000 banking customers with complete profiles and transactions
                </p>
                <div className="flex items-center text-green-600 font-semibold group-hover:gap-3 gap-2 transition-all mt-auto">
                  <span>Load Dataset</span>
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>
            </div>
          </Link>

          {/* Customer Segmentation */}
          <Link to="/banking/agent-a" className="h-full">
            <div className="group bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden border border-blue-200 hover:border-blue-500 h-full flex flex-col">
              <div className="p-8 flex flex-col flex-1">
                <div className="w-14 h-14 bg-blue-700 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform flex-shrink-0">
                  <Users className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">👥 Customer Segmentation</h3>
                <p className="text-gray-600 mb-6 flex-1">
                  AI-powered persona identification for retail banking customers
                </p>
                <div className="flex items-center text-blue-700 font-semibold group-hover:gap-3 gap-2 transition-all mt-auto">
                  <span>Get Started</span>
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>
            </div>
          </Link>

          {/* Segments View - Conditional link based on Agent A status */}
          <Link to={status?.agent_a_complete ? "/banking/macro-dashboard" : "/banking/agent-a"} className="h-full">
            <div className="group bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden border border-blue-200 hover:border-blue-700 h-full flex flex-col">
              <div className="p-8 flex flex-col flex-1">
                <div className="w-14 h-14 bg-blue-700 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform flex-shrink-0">
                  <BarChart3 className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">📊 Segments View</h3>
                <p className="text-gray-600 mb-6 flex-1">
                  {status?.agent_a_complete 
                    ? "Interactive visualization with macro and micro segments"
                    : "⚠️ Run Agent A first to view segments"}
                </p>
                <div className="flex items-center text-blue-700 font-semibold group-hover:gap-3 gap-2 transition-all mt-auto">
                  <span>{status?.agent_a_complete ? "View Dashboard" : "Run Agent A First"}</span>
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>
            </div>
          </Link>

          {/* Product Recommendations */}
          <Link to="/banking/agent-b" className="h-full">
            <div className="group bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden border border-blue-200 hover:border-amber-500 h-full flex flex-col">
              <div className="p-8 flex flex-col flex-1">
                <div className="w-14 h-14 bg-amber-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform flex-shrink-0">
                  <Target className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">🎯 Product Recommendations</h3>
                <p className="text-gray-600 mb-6 flex-1">
                  Personalized product matching based on customer profiles
                </p>
                <div className="flex items-center text-amber-600 font-semibold group-hover:gap-3 gap-2 transition-all mt-auto">
                  <span>Explore Products</span>
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>
            </div>
          </Link>
        </div>

        {/* Quick Start Guide */}
        <div className="max-w-6xl mx-auto px-8 pb-12">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>🚀</span>
              <span>Quick Start Guide</span>
            </h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0 mt-0.5">1</div>
                <div>
                  <div className="font-semibold text-gray-900">Load Dataset</div>
                  <div className="text-sm text-gray-600">Import 5,000 customers with complete banking profiles</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-blue-700 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0 mt-0.5">2</div>
                <div>
                  <div className="font-semibold text-gray-900">Run Segmentation</div>
                  <div className="text-sm text-gray-600">Use Agent A to create customer personas (High Net Worth, Young Professionals, etc.)</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-blue-700 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0 mt-0.5">3</div>
                <div>
                  <div className="font-semibold text-gray-900">Explore Segments</div>
                  <div className="text-sm text-gray-600">View macro personas and drill down into micro segments</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-amber-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0 mt-0.5">4</div>
                <div>
                  <div className="font-semibold text-gray-900">Generate Recommendations</div>
                  <div className="text-sm text-gray-600">Use Agent B to match products to customer profiles</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Status Overview */}
      <div className="max-w-6xl mx-auto px-8 pb-12">
        <div className="bg-white rounded-xl shadow-sm p-8 border border-blue-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Platform Status</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                {status?.data_loaded ? (
                  <CheckCircle2 className="w-6 h-6 text-blue-700" />
                ) : (
                  <Clock className="w-6 h-6 text-gray-400" />
                )}
              </div>
              <div>
                <div className="text-lg font-bold text-gray-900 mb-1">Data Status</div>
                <div className="text-sm text-gray-600">
                  {status?.data_loaded ? `${status?.customers_count || 0} Customers Loaded` : 'No Data Loaded'}
                </div>
              </div>
            </div>
            
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                {status?.agent_a_complete ? (
                  <CheckCircle2 className="w-6 h-6 text-blue-700" />
                ) : (
                  <Clock className="w-6 h-6 text-gray-400" />
                )}
              </div>
              <div>
                <div className="text-lg font-bold text-gray-900 mb-1">Agent A Status</div>
                <div className="text-sm text-gray-600">
                  {status?.agent_a_complete ? 'Segmentation Complete' : 'Not Run Yet'}
                </div>
              </div>
            </div>
            
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                {status?.agent_b_complete ? (
                  <CheckCircle2 className="w-6 h-6 text-blue-700" />
                ) : (
                  <Clock className="w-6 h-6 text-gray-400" />
                )}
              </div>
              <div>
                <div className="text-lg font-bold text-gray-900 mb-1">Agent B Status</div>
                <div className="text-sm text-gray-600">
                  {status?.agent_b_complete ? 'Recommendations Ready' : 'Not Run Yet'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Overview */}
      <div className="max-w-6xl mx-auto px-8 pb-12">
        <div className="bg-white rounded-xl shadow-sm p-8 border border-blue-200">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">Platform Capabilities</h3>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-700" />
                Customer Segmentation
              </h4>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-blue-700 mt-0.5">•</span>
                  <span>💼 High Net Worth Investors</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-700 mt-0.5">•</span>
                  <span>🚀 Young Professionals</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-700 mt-0.5">•</span>
                  <span>🏢 Small Business Owners</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-700 mt-0.5">•</span>
                  <span>💰 Mass Market Savers</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-700 mt-0.5">•</span>
                  <span>📱 Digital Natives</span>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <ShoppingBag className="w-5 h-5 text-blue-700" />
                Product Recommendations
              </h4>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Credit Cards & Personal Loans</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Investment & Wealth Products</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Mortgages & Home Equity Lines</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Business Banking Solutions</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Cross-sell & Up-sell Opportunities</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Stats */}
      <div className="max-w-6xl mx-auto px-8 pb-12">
        <div className="bg-white rounded-xl shadow-sm p-8 border border-blue-200">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-700 mb-2">{status?.customers_count || '5,000+'}</div>
              <div className="text-sm text-gray-600">Customer Profiles</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-700 mb-2">5-7</div>
              <div className="text-sm text-gray-600">Customer Personas</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-700 mb-2">15+</div>
              <div className="text-sm text-gray-600">Banking Products</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


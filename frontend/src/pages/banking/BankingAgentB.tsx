import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Search, CreditCard, TrendingUp, AlertCircle, CheckCircle2, Star, DollarSign, ChevronDown, Briefcase } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

const MATCH_LEVEL_COLORS = {
  'Perfect Match': 'bg-green-100 text-green-800 border-green-300',
  'Great Match': 'bg-blue-100 text-blue-800 border-blue-300',
  'Good Option': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'Consider Alternatives': 'bg-gray-100 text-gray-800 border-gray-300'
};

export default function BankingAgentB() {
  const [scoringMethod, setScoringMethod] = useState<'rules' | 'logit'>('rules'); // Toggle between rule-based and hybrid ML
  const [mode, setMode] = useState<'persona' | 'customer'>('persona'); // Toggle between persona and customer mode
  const [persona, setPersona] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('');
  const [topN, setTopN] = useState(10);
  const [expandedExplanations, setExpandedExplanations] = useState<Record<number, boolean>>({});

  // Query to get available personas
  const personasQuery = useQuery({
    queryKey: ['banking-personas'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/personas`);
      if (!response.ok) throw new Error('Failed to fetch personas');
      return response.json();
    }
  });

  const personas = personasQuery.data?.personas || [];

  // Set default persona when personas load
  React.useEffect(() => {
    if (personas.length > 0 && !persona) {
      setPersona(personas[0].id);
    }
  }, [personas, persona]);

  // Query to get customers list (for customer mode)
  const customersQuery = useQuery({
    queryKey: ['banking-customers'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/customers?limit=100`);
      if (!response.ok) throw new Error('Failed to fetch customers');
      return response.json();
    },
    enabled: mode === 'customer'
  });

  // Mutation to execute Agent B (supports rule-based and hybrid ML)
  const executeMutation = useMutation({
    mutationFn: async () => {
      let endpoint;
      if (scoringMethod === 'rules') {
        endpoint = `${API_BASE_URL}/api/banking/agent_b/execute`;
      } else { // logit
        endpoint = `${API_BASE_URL}/api/banking/agent_b/logit`;
      }
      
      const requestBody: any = {
        search_query: searchQuery,
        category: category || null,
        top_n: topN
      };

      // Add either customer_id or persona based on mode
      if (mode === 'customer') {
        requestBody.customer_id = customerId;
      } else {
        requestBody.persona = persona;
      }

      // Add explain for rules
      if (scoringMethod === 'rules') {
        requestBody.explain = true;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      if (!response.ok) throw new Error(`Failed to execute Agent B (${scoringMethod})`);
      return response.json();
    }
  });

  const handleSearch = () => {
    // Validation
    if (mode === 'customer' && !customerId) {
      alert('Please select a customer');
      return;
    }
    if (mode === 'persona' && !persona) {
      alert('Please select a persona');
      return;
    }
    executeMutation.mutate();
  };

  const results = executeMutation.data?.results;
  const recommendations = results?.recommendations || [];
  const insights = results?.insights || {};
  const scoringMethodology = results?.scoring_methodology || results?.algorithm_explanation || {};

  // DEBUG: Check if 12-factor data is in recommendations
  React.useEffect(() => {
    if (recommendations.length > 0) {
      console.log('\n🔍 DEBUGGING BANKING 12-FACTOR DATA IN FRONTEND');
      console.log('='+'='.repeat(79));
      console.log('Number of recommendations:', recommendations.length);
      console.log('\nFirst recommendation data:');
      console.log('  - product_name:', recommendations[0].product_name);
      console.log('  - score:', recommendations[0].score);
      console.log('  - scoring_method:', recommendations[0].scoring_method);
      console.log('  - detailed_calculation exists:', !!recommendations[0].detailed_calculation);
      if (recommendations[0].detailed_calculation) {
        console.log('  - detailed_calculation keys:', Object.keys(recommendations[0].detailed_calculation));
      }
      console.log('='+'='.repeat(79)+'\n');
    }
  }, [recommendations]);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              🏦 F&M Bank Agent B
            </h1>
            <p className="text-gray-600 mt-2">
              Personalized Banking Product Recommendations using 12-Factor Scoring
            </p>
          </div>
          {/* View Macro Segments Button */}
          <a
            href="/banking/macro-dashboard"
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span className="font-semibold">View Macro Segments</span>
          </a>
        </div>

        {/* Scoring Method Tabs */}
        <div className="mt-6 border-b border-gray-200">
          <div className="flex space-x-1">
            <button
              onClick={() => setScoringMethod('rules')}
              className={`px-6 py-3 font-semibold transition-all border-b-2 ${
                scoringMethod === 'rules'
                  ? 'text-blue-600 border-blue-600 bg-blue-50'
                  : 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              📊 Rule-Based Scoring
              <span className="ml-2 text-xs px-2 py-1 rounded-full bg-gray-200 text-gray-700">
                Banking 12-Factor
              </span>
            </button>
            <button
              onClick={() => setScoringMethod('logit')}
              className={`px-6 py-3 font-semibold transition-all border-b-2 ${
                scoringMethod === 'logit'
                  ? 'text-purple-600 border-purple-600 bg-purple-50'
                  : 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              🤖 Hybrid ML Model
              <span className="ml-2 text-xs px-2 py-1 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                50% ML + 50% Rules
              </span>
            </button>
          </div>
        </div>

        {/* Mode Toggle (Persona vs Customer) */}
        <div className="mt-6 flex items-center justify-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <button
            onClick={() => setMode('persona')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              mode === 'persona'
                ? 'bg-green-600 text-white shadow-md'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            📊 Persona Mode
          </button>
          <button
            onClick={() => setMode('customer')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              mode === 'customer'
                ? 'bg-green-600 text-white shadow-md'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            👤 Customer Mode
          </button>
        </div>

        {/* Search Form */}
        <div className="mt-6 space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            {/* Conditional selector based on mode */}
            {mode === 'persona' ? (
              <div className="flex flex-col">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Customer Persona
                </label>
                <select
                  value={persona}
                  onChange={(e) => setPersona(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white"
                  disabled={personasQuery.isLoading}
                >
                  {personasQuery.isLoading ? (
                    <option>Loading personas...</option>
                  ) : personas.length === 0 ? (
                    <option>No personas available - Run Agent A first</option>
                  ) : (
                    personas.map((p: any) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.size?.toLocaleString() || 0} customers{p.percentage ? `, ${p.percentage.toFixed(1)}%` : ''})
                      </option>
                    ))
                  )}
                </select>
                {personas.length === 0 && !personasQuery.isLoading && (
                  <p className="text-sm text-orange-600 mt-1">
                    ⚠️ Please run Agent A clustering first to generate personas
                  </p>
                )}
              </div>
            ) : (
              <div className="flex flex-col">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Customer
                </label>
                <select
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white"
                >
                  <option value="">Choose a customer...</option>
                  {customersQuery.data?.data?.customers?.map((customer: any) => (
                    <option key={customer.customer_id} value={customer.customer_id}>
                      {customer.customer_name} ({customer.customer_id})
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className="flex flex-col">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category (Optional)
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white"
              >
                <option value="">All Categories</option>
                <option value="Personal">Personal Banking</option>
                <option value="Business">Business Banking</option>
                <option value="Agricultural">Agricultural Banking</option>
              </select>
            </div>
          </div>

          <div className="grid md:grid-cols-4 gap-4">
            <div className="md:col-span-3 flex flex-col">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Query
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g., checking account, credit card, savings..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div className="flex flex-col">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Top N
              </label>
              <input
                type="number"
                value={topN}
                onChange={(e) => setTopN(parseInt(e.target.value))}
                min={1}
                max={20}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
          </div>

          <button
            onClick={handleSearch}
            disabled={executeMutation.isPending}
            className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 flex items-center justify-center gap-2 transition-colors font-medium"
          >
            <Search className="w-5 h-5" />
            {executeMutation.isPending ? 'Searching...' : 'Get Personalized Banking Recommendations'}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {executeMutation.isPending && (
        <div className={`border rounded-lg p-6 text-center ${
          scoringMethod === 'logit' 
            ? 'bg-purple-50 border-purple-200' 
            : 'bg-blue-50 border-blue-200'
        }`}>
          <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4 ${
            scoringMethod === 'logit' ? 'border-purple-600' : 'border-blue-600'
          }`}></div>
          <p className={`font-medium ${
            scoringMethod === 'logit' ? 'text-purple-700' : 'text-blue-700'
          }`}>
            {scoringMethod === 'logit' 
              ? `Running Banking Hybrid ML model for ${mode === 'persona' ? persona : 'customer'}...`
              : `Calculating personalized banking scores for ${mode === 'persona' ? persona : 'customer'}...`}
          </p>
          {scoringMethod === 'logit' && (
            <p className="text-sm text-purple-600 mt-2">
              🤖 AI learning from banking transaction patterns
            </p>
          )}
        </div>
      )}

      {/* Error State */}
      {executeMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle className="w-6 h-6" />
            <div>
              <p className="font-medium">Error getting recommendations</p>
              <p className="text-sm">{executeMutation.error?.message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <>
          {/* Success Message & Insights */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3 text-green-700">
                <CheckCircle2 className="w-6 h-6" />
                <div>
                  <p className="font-medium">Found {recommendations.length} personalized banking products</p>
                  <p className="text-sm text-gray-600">
                    {insights.persona_summary || 'Tailored to your financial profile'}
                  </p>
                </div>
              </div>
              <div className={`px-4 py-2 rounded-full text-sm font-semibold ${
                scoringMethod === 'logit'
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {scoringMethod === 'logit' 
                  ? '🤖 Hybrid ML (50% ML + 50% Banking Rules)'
                  : '📊 Banking 12-Factor Scoring'}
              </div>
            </div>

            {/* Banking-Specific Metrics Grid */}
            {(insights || results.metrics) && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Match Quality */}
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
                  <p className="text-xs text-gray-600 mb-1">🎯 Match Quality</p>
                  <p className="text-2xl font-bold text-green-600">
                    {results.metrics?.avg_match_score 
                      ? `${results.metrics.avg_match_score.toFixed(1)}%` 
                      : insights?.avg_match_score
                        ? `${insights.avg_match_score.toFixed(1)}%`
                        : insights?.avg_score 
                        ? `${(insights.avg_score * 100).toFixed(1)}%` 
                        : '0%'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Top: {results.metrics?.top_match_score?.toFixed(1) || insights?.max_score ? (insights.max_score * 100).toFixed(1) : '0'}%
                  </p>
                </div>

                {/* Annual Cost */}
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
                  <p className="text-xs text-gray-600 mb-1">💰 Annual Cost</p>
                  <p className="text-2xl font-bold text-blue-600">
                    ${results.metrics?.total_annual_cost?.toFixed(0) || insights?.total_annual_cost?.toFixed(0) || '0'}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    {results.metrics?.free_products || insights?.free_products || 0} free products
                  </p>
                </div>

                {/* Earning Potential */}
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200">
                  <p className="text-xs text-gray-600 mb-1">📈 Earning Potential</p>
                  <p className="text-2xl font-bold text-purple-600">
                    +${results.metrics?.estimated_annual_earnings?.toFixed(0) || insights?.estimated_annual_earnings?.toFixed(0) || '0'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {results.metrics?.earning_products || insights?.earning_products || 0} products @ {results.metrics?.avg_apy?.toFixed(2) || insights?.avg_apy?.toFixed(2) || '0'}% APY
                  </p>
                </div>

                {/* Accessibility */}
                <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-4 border border-orange-200">
                  <p className="text-xs text-gray-600 mb-1">🔓 Easy Access</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {results.metrics?.no_minimum_products || insights?.no_minimum_products || 0}/{results.metrics?.total_products || recommendations.length || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    No minimum balance
                  </p>
                </div>
              </div>
            )}

            {/* Value Proposition & Strategy */}
            {(insights.value_proposition || insights.recommendation_strategy) && (
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                {insights.value_proposition && (
                  <p className="text-sm font-semibold text-blue-900 mb-2">
                    💎 {insights.value_proposition}
                  </p>
                )}
                {insights.persona_summary && (
                  <p className="text-xs text-gray-600 italic">
                    {insights.persona_summary}
                  </p>
                )}
              </div>
            )}

            {/* How Hybrid / ML Works (only when Hybrid ML is selected and we have methodology) */}
            {scoringMethod === 'logit' && (scoringMethodology.formula || scoringMethodology.how_ml_probability_works) && (
              <details className="mt-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                <summary className="cursor-pointer font-semibold text-purple-900 flex items-center gap-2">
                  📐 How the hybrid algorithm works (50% ML + 50% rules)
                </summary>
                <div className="mt-3 space-y-3 text-sm text-gray-700">
                  {scoringMethodology.formula && (
                    <p><span className="font-semibold text-purple-800">Formula:</span> {scoringMethodology.formula}</p>
                  )}
                  {scoringMethodology.short && (
                    <p>{scoringMethodology.short}</p>
                  )}
                  {scoringMethodology.how_ml_probability_works && (
                    <div>
                      <p className="font-semibold text-purple-800 mb-1">How ML probability works</p>
                      <p className="text-gray-600">{scoringMethodology.how_ml_probability_works}</p>
                    </div>
                  )}
                  {scoringMethodology.how_rules_work && (
                    <div>
                      <p className="font-semibold text-blue-800 mb-1">How rules work</p>
                      <p className="text-gray-600">{scoringMethodology.how_rules_work}</p>
                    </div>
                  )}
                  {scoringMethodology.calculation_per_product && (
                    <p className="text-gray-600 italic">{scoringMethodology.calculation_per_product}</p>
                  )}
                </div>
              </details>
            )}
          </div>

          {/* Recommendations List */}
          <div className="space-y-4">
            {recommendations.map((rec: any, index: number) => (
              <div key={rec.product_id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-l-4" style={{
                borderColor: rec.match_level === 'Perfect Match' ? '#10b981' :
                             rec.match_level === 'Great Match' ? '#3b82f6' :
                             rec.match_level === 'Good Option' ? '#f59e0b' : '#6b7280'
              }}>
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl font-bold text-gray-400">#{index + 1}</span>
                      <h3 className="text-xl font-bold text-gray-900">{rec.product_name}</h3>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <CreditCard className="w-4 h-4" />
                        {rec.category || 'Personal'}
                      </span>
                      {rec.subcategory && (
                        <>
                          <span>•</span>
                          <span>{rec.subcategory}</span>
                        </>
                      )}
                      {rec.min_credit_score && (
                        <>
                          <span>•</span>
                          <span>Min Credit: {rec.min_credit_score}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900 mb-1">
                      {rec.annual_fee && rec.annual_fee > 0 ? (
                        `$${rec.annual_fee.toFixed(2)}/year`
                      ) : (
                        <span className="text-green-600">Free</span>
                      )}
                    </div>
                    {rec.interest_rate > 0 && (
                      <div className="text-sm text-green-600 font-semibold">
                        {rec.interest_rate.toFixed(2)}% APY
                      </div>
                    )}
                    {rec.min_balance > 0 && (
                      <div className="text-xs text-gray-500">
                        Min: ${rec.min_balance.toLocaleString()}
                      </div>
                    )}
                    <div className={`mt-2 px-3 py-1 rounded-full text-xs font-medium border ${MATCH_LEVEL_COLORS[rec.match_level as keyof typeof MATCH_LEVEL_COLORS] || MATCH_LEVEL_COLORS['Consider Alternatives']}`}>
                      {rec.match_level}
                    </div>
                  </div>
                </div>

                {/* 💡 Why This Product? - Unified, beautifully formatted */}
                {(rec.rank_explanation || rec.recommendation_text) && (
                  <div className="mb-4 overflow-hidden rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50/80 to-teal-50/80 shadow-sm">
                    <div className="border-b border-emerald-200 bg-emerald-100/60 px-4 py-2.5">
                      <p className="text-sm font-bold text-emerald-900 flex items-center gap-2">
                        <span className="text-base">💡</span> Why This Product?
                      </p>
                    </div>
                    <div className="p-4 space-y-4">
                      {rec.rank_explanation && (
                        <div className="space-y-3">
                          <p className="text-xs font-bold text-emerald-800 uppercase tracking-wide flex items-center gap-1.5">
                            <span>🏆</span> Rank #{rec.rank || (index + 1)} · {(rec.score * 100).toFixed(1)}% compatibility
                          </p>
                          <div className="text-sm text-gray-800 leading-relaxed space-y-2">
                            {rec.rank_explanation.split('\n\n').map((section: string, idx: number) => (
                              <div key={idx} className={idx > 0 ? 'mt-3 pt-3 border-t border-emerald-200' : ''}>
                                {section.split('\n').map((line: string, lineIdx: number) => {
                                  const formattedLine = line.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-emerald-900">$1</strong>');
                                  const finalLine = formattedLine.replace(/\*(.*?)\*/g, '<em class="text-gray-600 text-xs">$1</em>');
                                  return (
                                    <p
                                      key={lineIdx}
                                      className={line.startsWith('*') ? 'text-xs italic text-gray-600 mt-2' : 'mb-1'}
                                      dangerouslySetInnerHTML={{ __html: finalLine }}
                                    />
                                  );
                                })}
                              </div>
                            ))}
                          </div>
                          <p className="text-xs text-emerald-800 pt-2 border-t border-emerald-200/80">
                            📐 Comprehensive match score based on banking 12 factors (see detailed calculation below).
                          </p>
                        </div>
                      )}
                      {!rec.rank_explanation && rec.recommendation_text && (
                        <>
                          <div className="text-sm text-gray-800 leading-relaxed">
                            {rec.reason || rec.recommendation_text}
                          </div>
                          <p className="text-xs text-emerald-800 pt-2 border-t border-emerald-200/80">
                            📐 Comprehensive match score based on banking 12 factors (see detailed calculation below).
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Score Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Suitability Score</span>
                    <span className="font-bold text-gray-900">{(rec.score * 100).toFixed(2)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="h-3 rounded-full transition-all"
                      style={{
                        width: `${Math.min(rec.score * 100, 100)}%`,
                        backgroundColor: rec.score > 0.8 ? '#10b981' :
                                       rec.score > 0.65 ? '#3b82f6' :
                                       rec.score > 0.5 ? '#f59e0b' : '#6b7280'
                      }}
                    />
                  </div>
                  
                  {/* AI Explanation - Collapsible */}
                  <div className="mt-3">
                    <button
                      onClick={() => setExpandedExplanations(prev => ({
                        ...prev,
                        [index]: !prev[index]
                      }))}
                      className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
                    >
                      <svg 
                        className="w-4 h-4 transition-transform duration-200" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                        style={{ transform: expandedExplanations[index] ? 'rotate(90deg)' : 'rotate(0deg)' }}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      <span>How is Suitability Score calculated?</span>
                    </button>
                    
                    {expandedExplanations[index] && (
                      <div className="mt-3 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow-sm animate-fadeIn">
                        <div className="space-y-3">
                          <div className="flex items-start gap-2">
                            <div className="bg-blue-600 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">
                              AI
                            </div>
                            <div className="flex-1">
                              {rec.detailed_calculation && rec.scoring_method === '12_factor' ? (
                                /* BANKING 12-FACTOR DETAILED CALCULATION */
                                <div>
                                  <p className="text-xs font-semibold text-indigo-900 mb-3">
                                    🏦 Banking 12-Factor Scoring System
                                  </p>
                                  
                                  {/* Total Score */}
                                  <div className="mb-3 p-3 bg-white rounded-lg border-2 border-indigo-300">
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs font-bold text-gray-900">Total Suitability Score</span>
                                      <span className="text-lg font-bold text-indigo-600">{(rec.score * 100).toFixed(1)}%</span>
                                    </div>
                                  </div>

                                  {/* TIER 1: Core Banking Criteria (55%) */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
                                    <p className="text-xs font-bold text-indigo-900 mb-3">🎯 TIER 1: Core Banking Criteria (55%)</p>
                                    
                                    {/* Eligibility Score */}
                                    {rec.detailed_calculation.eligibility_score && (
                                      <div className="mb-3 pb-3 border-b border-indigo-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">1. Eligibility Score</span>
                                          <span className="text-sm font-bold text-indigo-700">{(rec.detailed_calculation.eligibility_score.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.eligibility_score.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.eligibility_score.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.eligibility_score as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {((rec.detailed_calculation.eligibility_score as { calculation?: string }).calculation)}</p>
                                            )}
                                            <p>Banking regulators require strict eligibility criteria. 68% of denied applications cite credit/income issues (FDIC). Must be highest weight to ensure compliance and prevent customer frustration.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Financial Need Match */}
                                    {rec.detailed_calculation.financial_need_match && (
                                      <div className="mb-3 pb-3 border-b border-indigo-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">2. Financial Need Match</span>
                                          <span className="text-sm font-bold text-indigo-700">{(rec.detailed_calculation.financial_need_match.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.financial_need_match.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.financial_need_match.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.financial_need_match as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.financial_need_match as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>Products must match life stage: Retirees need income products, young professionals need credit building. McKinsey research shows 72% satisfaction comes from need-product alignment.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Relationship Depth */}
                                    {rec.detailed_calculation.relationship_depth && (
                                      <div className="mb-0">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">3. Relationship Depth</span>
                                          <span className="text-sm font-bold text-indigo-700">{(rec.detailed_calculation.relationship_depth.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.relationship_depth.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.relationship_depth.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.relationship_depth as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.relationship_depth as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>Customers with 3+ products have 92% retention vs 40% for single-product (Bain & Company). Loyalty drives long-term profitability.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}
                                  </div>

                                  {/* TIER 2: Strategic Fit & Product Value (28%) */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border border-blue-200">
                                    <p className="text-xs font-bold text-blue-900 mb-3">💎 TIER 2: Strategic Fit & Product Value (28%)</p>
                                    
                                    {/* Product Value - NEW! */}
                                    {rec.detailed_calculation.product_value && (
                                      <div className="mb-3 pb-3 border-b border-blue-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">4. Product Value ⭐ NEW</span>
                                          <span className="text-sm font-bold text-blue-700">{(rec.detailed_calculation.product_value.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.product_value.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.product_value.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.product_value as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.product_value as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>Fee sensitivity drives 45% of account switching (J.D. Power). Products must differentiate on value: fees, APY, min balance, ROI. Higher weight ensures best-value products rise to top.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Product Pairing */}
                                    {rec.detailed_calculation.product_pairing && (
                                      <div className="mb-3 pb-3 border-b border-blue-100">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">5. Product Pairing</span>
                                          <span className="text-sm font-bold text-blue-700">{(rec.detailed_calculation.product_pairing.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.product_pairing.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.product_pairing.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.product_pairing as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.product_pairing as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>Cross-sell increases customer lifetime value 2-3x. Checking+Savings bundles show 85% higher satisfaction (Accenture Banking Study).</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}

                                    {/* Channel Fit */}
                                    {rec.detailed_calculation.channel_fit && (
                                      <div className="mb-0">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">6. Channel Fit</span>
                                          <span className="text-sm font-bold text-blue-700">{(rec.detailed_calculation.channel_fit.score * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="text-xs text-gray-700 mb-1">
                                          📌 {rec.detailed_calculation.channel_fit.explanation}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                            Why {(rec.detailed_calculation.channel_fit.weight * 100).toFixed(0)}%?
                                          </summary>
                                          <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                            {(rec.detailed_calculation.channel_fit as { calculation?: string }).calculation && (
                                              <p className="font-medium text-indigo-700">📐 {(rec.detailed_calculation.channel_fit as { calculation?: string }).calculation}</p>
                                            )}
                                            <p>78% of millennials prefer mobile banking, 65% of 60+ prefer branches (ABA Survey). Channel mismatch causes 30% lower engagement.</p>
                                          </div>
                                        </details>
                                      </div>
                                    )}
                                  </div>

                                  {/* TIER 3: Behavioral & Contextual (10%) */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                    <p className="text-xs font-bold text-green-900 mb-3">🎯 TIER 3: Behavioral & Contextual (10%)</p>
                                    
                                    {['complexity_match', 'intent_score', 'segment_affinity', 'transaction_pattern'].map((factorKey) => {
                                      const factor = rec.detailed_calculation[factorKey];
                                      if (!factor) return null;
                                      
                                      const factorInfo: Record<string, { name: string; why: string }> = {
                                        'complexity_match': {
                                          name: 'Complexity Match',
                                          why: 'Complex products (IRAs, CDs) require financial literacy. 40% of customers abandon overly complex products (Deloitte). Matching sophistication prevents drop-off.'
                                        },
                                        'intent_score': {
                                          name: 'Intent Score',
                                          why: 'Cross-sell receptivity varies widely. Targeting high-intent customers improves conversion 3-5x (Salesforce Banking Report).'
                                        },
                                        'segment_affinity': {
                                          name: 'Segment Affinity',
                                          why: 'Peer behavior influences 60% of banking decisions. "People like me" social proof drives adoption in homogeneous segments.'
                                        },
                                        'transaction_pattern': {
                                          name: 'Transaction Pattern',
                                          why: 'High-frequency transactors need different products than savers. Activity patterns predict product usage and satisfaction.'
                                        }
                                      };

                                      return (
                                        <div key={factorKey} className="mb-2 pb-2 border-b border-green-100 last:border-0">
                                          <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-semibold text-gray-900">{factorInfo[factorKey].name}</span>
                                            <span className="text-xs font-bold text-green-700">{(factor.score * 100).toFixed(1)}%</span>
                                          </div>
                                          <div className="text-xs text-gray-700 mb-1">📌 {factor.explanation}</div>
                                          <details className="mt-1">
                                            <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                              Why {(factor.weight * 100).toFixed(0)}%?
                                            </summary>
                                            <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                              {(factor as { calculation?: string }).calculation && (
                                                <p className="font-medium text-indigo-700">📐 {(factor as { calculation?: string }).calculation}</p>
                                              )}
                                              <p>{factorInfo[factorKey].why}</p>
                                            </div>
                                          </details>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {/* TIER 4: Quality Signals (7%) */}
                                  <div className="mb-3 p-3 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border border-orange-200">
                                    <p className="text-xs font-bold text-orange-900 mb-3">⭐ TIER 4: Quality Signals (7%)</p>
                                    
                                    {['product_rating', 'popularity'].map((factorKey) => {
                                      const factor = rec.detailed_calculation[factorKey];
                                      if (!factor) return null;
                                      
                                      const factorInfo: Record<string, { name: string; why: string }> = {
                                        'product_rating': {
                                          name: 'Product Rating',
                                          why: 'Customer satisfaction ratings predict long-term retention. 4.5+ star products have 80% renewal rates vs 55% for 3-star (Banking Satisfaction Index).'
                                        },
                                        'popularity': {
                                          name: 'Popularity',
                                          why: 'Popular products within segments indicate proven value. Adoption rates signal market validation and reduce perceived risk for customers.'
                                        }
                                      };

                                      return (
                                        <div key={factorKey} className="mb-2 pb-2 border-b border-orange-100 last:border-0">
                                          <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-semibold text-gray-900">{factorInfo[factorKey].name}</span>
                                            <span className="text-xs font-bold text-orange-700">{(factor.score * 100).toFixed(1)}%</span>
                                          </div>
                                          <div className="text-xs text-gray-700 mb-1">📌 {factor.explanation}</div>
                                          <details className="mt-1">
                                            <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
                                              Why {(factor.weight * 100).toFixed(0)}%?
                                            </summary>
                                            <div className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200 space-y-1">
                                              {(factor as { calculation?: string }).calculation && (
                                                <p className="font-medium text-indigo-700">📐 {(factor as { calculation?: string }).calculation}</p>
                                              )}
                                              <p>{factorInfo[factorKey].why}</p>
                                            </div>
                                          </details>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {/* Summary */}
                                  <div className="mt-3 pt-3 border-t-2 border-indigo-300 bg-indigo-50 p-3 rounded-lg">
                                    <p className="text-xs text-gray-700 mb-2">
                                      <span className="font-semibold">📐 Formula:</span> Sum of all 12 weighted factors
                                    </p>
                                    <p className="text-xs font-bold text-indigo-900 mb-2">
                                      Total Score = {(rec.score * 100).toFixed(1)}%
                                    </p>
                                    <p className="text-xs text-gray-600">
                                      💡 All weights sum to 100%. Each percentage is based on banking research, regulatory requirements, and customer behavior studies.
                                    </p>
                                  </div>
                                </div>
                              ) : scoringMethod === 'logit' && rec.scoring_breakdown ? (
                                /* HYBRID ML MODEL EXPLANATION */
                                <div>
                                  <p className="text-xs font-semibold text-purple-900 mb-3">
                                    🎯 Banking Hybrid Scoring (50% ML + 50% Rules)
                                  </p>
                                  
                                  {/* Final Score */}
                                  <div className="mb-3 p-3 bg-white rounded-lg border-2 border-purple-300">
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs font-bold text-gray-900">Final Score</span>
                                      <span className="text-lg font-bold text-purple-600">{(rec.scoring_breakdown.final_score * 100).toFixed(1)}%</span>
                                    </div>
                                  </div>

                                  {/* ML Contribution */}
                                  <div className="space-y-2 mb-3">
                                    <div className="flex items-center justify-between p-2 bg-purple-100 rounded">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-purple-900">🤖 ML Prediction</span>
                                        <span className="text-xs text-purple-700">(50% weight)</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-purple-700">{(rec.scoring_breakdown.ml_probability * 100).toFixed(1)}% →</span>
                                        <span className="text-sm font-bold text-purple-900">{(rec.scoring_breakdown.ml_contribution * 100).toFixed(1)}%</span>
                                      </div>
                                    </div>
                                    
                                    {/* Rule-Based Contribution */}
                                    <div className="flex items-center justify-between p-2 bg-blue-100 rounded">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-blue-900">📐 Banking Rules</span>
                                        <span className="text-xs text-blue-700">(50% weight)</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-blue-700">{(rec.scoring_breakdown.rule_score * 100).toFixed(1)}% →</span>
                                        <span className="text-sm font-bold text-blue-900">{(rec.scoring_breakdown.rule_contribution * 100).toFixed(1)}%</span>
                                      </div>
                                    </div>
                                  </div>

                                  <div className="mt-3 pt-2 border-t border-purple-200">
                                    <p className="text-xs text-gray-700 mb-2">
                                      <span className="font-semibold">Formula:</span> ({(rec.scoring_breakdown.ml_probability * 100).toFixed(1)}% × 0.5) + ({(rec.scoring_breakdown.rule_score * 100).toFixed(1)}% × 0.5) = {(rec.scoring_breakdown.final_score * 100).toFixed(1)}%
                                    </p>
                                    
                                    {/* 12-Factor Breakdown (expandable) */}
                                    {rec.scoring_breakdown?.twelve_factor_breakdown && (
                                      <details className="mt-2 bg-blue-50 p-2 rounded">
                                        <summary className="text-xs font-semibold text-blue-800 cursor-pointer hover:text-blue-900">
                                          📊 View 12-Factor Banking Rules Breakdown (50% component)
                                        </summary>
                                        <div className="mt-2 space-y-1 pl-2 border-l-2 border-blue-300">
                                          {Object.entries(rec.scoring_breakdown.twelve_factor_breakdown).filter(([key]) => 
                                            !['total_score', 'total_percentage'].includes(key)
                                          ).map(([key, value]: [string, any]) => {
                                            const factorScore = value?.score || 0;
                                            const factorWeight = value?.weight || 0;
                                            return (
                                              <div key={key} className="text-xs">
                                                <span className="text-gray-700">{key.replace(/_/g, ' ')}: </span>
                                                <span className="font-semibold text-blue-800">
                                                  {(factorScore * 100).toFixed(1)}%
                                                </span>
                                                <span className="text-gray-500"> (weight: {(factorWeight * 100).toFixed(0)}%)</span>
                                              </div>
                                            );
                                          })}
                                        </div>
                                      </details>
                                    )}
                                  </div>
                                </div>
                              ) : (
                                /* RULE-BASED EXPLANATION */
                                <div>
                                  <p className="text-xs font-semibold text-blue-900 mb-2">
                                    This score predicts how suitable this banking product is for this customer based on:
                                  </p>
                                  
                                  <div className="space-y-2">
                                    <div className="flex items-start gap-2">
                                      <div className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        25%
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-900">Eligibility Match</p>
                                        <p className="text-xs text-gray-600">Credit score, income, and balance requirements</p>
                                      </div>
                                    </div>
                                    
                                    <div className="flex items-start gap-2">
                                      <div className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        20%
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-900">Financial Need Match</p>
                                        <p className="text-xs text-gray-600">Product features align with customer needs</p>
                                      </div>
                                    </div>
                                    
                                    <div className="flex items-start gap-2">
                                      <div className="bg-purple-100 text-purple-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        15%
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-900">Relationship Depth</p>
                                        <p className="text-xs text-gray-600">Customer tenure and existing products</p>
                                      </div>
                                    </div>
                                    
                                    <div className="flex items-start gap-2">
                                      <div className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        40%
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-900">Other Factors</p>
                                        <p className="text-xs text-gray-600">Behavioral patterns, life stage, profitability potential, etc.</p>
                                      </div>
                                    </div>
                                  </div>
                                  
                                  <div className="mt-3 pt-3 border-t border-blue-200">
                                    <p className="text-xs text-gray-700">
                                      <span className="font-semibold">Banking 12-Factor Formula:</span> Weighted sum of 12 banking-specific factors
                                    </p>
                                    <p className="text-xs text-gray-600 mt-1">
                                      💡 Higher scores indicate products that match customer profile, needs, and financial capacity
                                    </p>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Product Details Grid */}
                {(rec.min_balance || rec.min_credit_score || rec.interest_rate) && (
                  <div className="grid grid-cols-3 gap-2 mb-4">
                    {rec.min_balance > 0 && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Min Balance</p>
                        <p className="text-sm font-medium text-gray-900">${rec.min_balance.toLocaleString()}</p>
                      </div>
                    )}
                    {rec.min_credit_score && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Min Credit</p>
                        <p className="text-sm font-medium text-gray-900">{rec.min_credit_score}</p>
                      </div>
                    )}
                    {rec.interest_rate > 0 && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">APY</p>
                        <p className="text-sm font-medium text-gray-900">{rec.interest_rate.toFixed(2)}%</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Recommendation text fallback: shown only if no rank_explanation (unified card above handles both) */}
                {(rec.recommendation_text || rec.reason) && !rec.rank_explanation && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-xs font-semibold text-green-800 mb-2">💡 Why This Product?</p>
                    <div className="text-sm text-gray-800 leading-relaxed">
                      {rec.reason || rec.recommendation_text}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

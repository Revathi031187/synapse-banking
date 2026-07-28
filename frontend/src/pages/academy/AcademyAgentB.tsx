import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Search, Package, TrendingUp, AlertCircle, CheckCircle2, Star, DollarSign, ChevronDown, ShoppingCart } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

const MATCH_LEVEL_COLORS = {
  'Perfect Match': 'bg-green-100 text-green-800 border-green-300',
  'Great Match': 'bg-blue-100 text-blue-800 border-blue-300',
  'Good Option': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'Consider Alternatives': 'bg-gray-100 text-gray-800 border-gray-300'
};

export default function AcademyAgentB() {
  const [scoringMethod, setScoringMethod] = useState<'rules' | 'logit' | 'nested_logit'>('rules'); // Toggle between rule-based, hybrid ML, and nested logit
  const [mode, setMode] = useState<'persona' | 'customer'>('persona'); // Toggle between persona and customer mode
  const [persona, setPersona] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('');
  const [topN, setTopN] = useState(10);
  const [showOutOfStock, setShowOutOfStock] = useState(false);
  const [expandedExplanations, setExpandedExplanations] = useState<Record<number, boolean>>({});

  // Query to get available personas
  const personasQuery = useQuery({
    queryKey: ['academy-personas'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/academy/personas`);
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
    queryKey: ['academy-customers'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/customers?limit=100`);
      if (!response.ok) throw new Error('Failed to fetch customers');
      return response.json();
    },
    enabled: mode === 'customer' // Only fetch when in customer mode
  });

  // Mutation to execute Agent B (supports rule-based, logit, and nested logit)
  const executeMutation = useMutation({
    mutationFn: async () => {
      let endpoint;
      if (scoringMethod === 'rules') {
        endpoint = `${API_BASE_URL}/api/academy/agent_b/execute`;
      } else if (scoringMethod === 'logit') {
        endpoint = `${API_BASE_URL}/api/academy/agent_b/logit`;
      } else { // nested_logit
        endpoint = `${API_BASE_URL}/api/academy/agent_b/nested_logit`;
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
  const outOfStockRecommendations = results?.out_of_stock_recommendations || [];
  const insights = results?.insights || {};

  // DEBUG: Check if 12-factor data is in recommendations
  React.useEffect(() => {
    if (recommendations.length > 0) {
      console.log('\n🔍 DEBUGGING 12-FACTOR DATA IN FRONTEND');
      console.log('='+'='.repeat(79));
      console.log('Number of recommendations:', recommendations.length);
      console.log('\nFirst recommendation data:');
      console.log('  - product_name:', recommendations[0].product_name);
      console.log('  - score:', recommendations[0].score);
      console.log('  - scoring_method:', recommendations[0].scoring_method);
      console.log('  - detailed_calculation exists:', !!recommendations[0].detailed_calculation);
      if (recommendations[0].detailed_calculation) {
        console.log('  - detailed_calculation keys:', Object.keys(recommendations[0].detailed_calculation));
        console.log('  - total_percentage:', recommendations[0].detailed_calculation.total_percentage);
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
              🎯 Academy Sports Agent B
            </h1>
            <p className="text-gray-600 mt-2">
              Personalized Camping Gear Recommendations using Feature-Based Scoring
            </p>
          </div>
          {/* View Macro Segments Button */}
          <a
            href="/academy/macro-dashboard"
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
                Current
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
            {/* NESTED LOGIT TAB - HIDDEN FOR DEMO */}
            {/* <button
              onClick={() => setScoringMethod('nested_logit')}
              className={`px-6 py-3 font-semibold transition-all border-b-2 ${
                scoringMethod === 'nested_logit'
                  ? 'text-green-600 border-green-600 bg-green-50'
                  : 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              🌳 Nested Logit Model
              <span className="ml-2 text-xs px-2 py-1 rounded-full bg-gradient-to-r from-green-500 to-teal-500 text-white">
                Category → Brand → Product
              </span>
            </button> */}
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
                        {p.name} ({p.size.toLocaleString()} customers, {p.percentage.toFixed(1)}%)
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
                <option value="Tents">Tents + Screen Houses</option>
                <option value="Sleeping Bags">Sleeping Bags + Airbeds</option>
                <option value="Campsite Cooking">Campsite Cooking</option>
                <option value="Flashlights">Flashlights + Lanterns</option>
                <option value="Hiking Backpacks">Hiking Backpacks</option>
                <option value="Hiking Boots">Hiking Boots</option>
                <option value="Camp Furniture">Camp Furniture</option>
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
                placeholder="e.g., tent, backpack, sleeping bag..."
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
            {executeMutation.isPending ? 'Searching...' : 'Get Personalized Recommendations'}
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
              ? `Running Hybrid ML model for ${mode === 'persona' ? persona : 'customer'}...`
              : `Calculating personalized scores for ${mode === 'persona' ? persona : 'customer'}...`}
          </p>
          {scoringMethod === 'logit' && (
            <p className="text-sm text-purple-600 mt-2">
              🤖 AI learning from historical purchase patterns
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
                  <p className="font-medium">Found {recommendations.length} personalized recommendations</p>
                  <p className="text-sm text-gray-600">
                    {insights.persona_summary}
                  </p>
                </div>
              </div>
              <div className={`px-4 py-2 rounded-full text-sm font-semibold ${
                scoringMethod === 'logit'
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                  : scoringMethod === 'nested_logit'
                  ? 'bg-gradient-to-r from-green-500 to-teal-500 text-white'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {scoringMethod === 'logit' 
                  ? '🤖 Hybrid ML (50% ML + 50% Rules)'
                  : scoringMethod === 'nested_logit'
                  ? '🌳 Nested Logit (Category → Brand → Product)'
                  : '📊 Rule-Based Scoring'}
              </div>
            </div>

            {/* Insights Grid - Support both rule-based and ML models */}
            {(insights || results.metrics) && (
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Avg Match Score</p>
                  <p className="text-2xl font-bold text-green-600">
                    {results.metrics?.avg_match_score 
                      ? (results.metrics.avg_match_score * 100).toFixed(1) 
                      : insights?.avg_score 
                        ? (insights.avg_score * 100).toFixed(1) 
                        : '0.0'}%
                  </p>
                </div>
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Products Considered</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {results.metrics?.total_recommendations || results.total_products_considered || recommendations.length || 0}
                  </p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Avg Price</p>
                  <p className="text-2xl font-bold text-purple-600">
                    ${results.metrics?.avg_price 
                      ? results.metrics.avg_price.toFixed(0) 
                      : insights?.avg_price 
                        ? insights.avg_price.toFixed(0) 
                        : '0'}
                  </p>
                </div>
                <div className="bg-orange-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Price Range</p>
                  <p className="text-lg font-bold text-orange-600">
                    {results.metrics?.price_range 
                      ? results.metrics.price_range 
                      : insights?.price_range?.min && insights?.price_range?.max
                        ? `$${insights.price_range.min.toFixed(0)} - $${insights.price_range.max.toFixed(0)}`
                        : '$0 - $0'}
                  </p>
                </div>
              </div>
            )}

            {/* Strategy */}
            {insights.recommendation_strategy && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700">
                  <strong>Strategy:</strong> {insights.recommendation_strategy}
                </p>
              </div>
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
                        <Package className="w-4 h-4" />
                        {rec.brand}
                      </span>
                      <span>•</span>
                      <span>{rec.category}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Star className="w-4 h-4 text-yellow-400" />
                        {rec.avg_rating} ({rec.num_reviews} reviews)
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-gray-900 mb-1">
                      ${rec.price?.toFixed(2)}
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium border ${MATCH_LEVEL_COLORS[rec.match_level as keyof typeof MATCH_LEVEL_COLORS] || MATCH_LEVEL_COLORS['Consider Alternatives']}`}>
                      {rec.match_level}
                    </div>
                  </div>
                </div>

                {/* RANK EXPLANATION - Why this rank? */}
                {rec.rank_explanation && (
                  <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
                    <p className="text-xs font-semibold text-blue-800 mb-1">🏆 Why Ranked #{rec.rank || (index + 1)}?</p>
                    <p className="text-sm text-gray-800 leading-relaxed">
                      {rec.rank_explanation}
                    </p>
                  </div>
                )}

                {/* Score Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Purchase Probability</span>
                    <span className="font-bold text-gray-900">{(rec.score * 100).toFixed(2)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="h-3 rounded-full transition-all"
                      style={{
                        width: `${Math.min(rec.score * 100, 100)}%`,
                        backgroundColor: rec.score > 0.2 ? '#10b981' :
                                       rec.score > 0.1 ? '#3b82f6' :
                                       rec.score > 0.05 ? '#f59e0b' : '#6b7280'
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
                      <span>How is Purchase Probability calculated?</span>
                    </button>
                    
                    {expandedExplanations[index] && (
                      <div className="mt-3 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow-sm animate-fadeIn">
                        <div className="space-y-3">
                          <div className="flex items-start gap-2">
                            <div className="bg-blue-600 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">
                              AI
                            </div>
                            <div className="flex-1">
                              {scoringMethod === 'nested_logit' && rec.nested_breakdown ? (
                                /* NESTED LOGIT MODEL EXPLANATION */
                                <div>
                                  <p className="text-xs font-semibold text-green-900 mb-3">
                                    🌳 Nested Logit Hierarchical Choice Model
                                  </p>
                                  
                                  {/* Overall Probability */}
                                  <div className="mb-3 p-3 bg-white rounded-lg border-2 border-green-300">
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs font-bold text-gray-900">Overall Purchase Probability</span>
                                      <span className="text-lg font-bold text-green-600">{rec.overall_probability?.toFixed(2)}%</span>
                                    </div>
                                  </div>

                                  {/* Hierarchical Breakdown */}
                                  <div className="space-y-2 mb-3">
                                    <p className="text-xs font-semibold text-gray-700 mb-2">Hierarchical Choice Structure:</p>
                                    
                                    {/* Level 1: Category */}
                                    <div className="flex items-center justify-between p-2 bg-green-50 rounded border border-green-200">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-green-900">📂 Level 1: Category Choice</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-sm font-bold text-green-900">{rec.nested_breakdown.category_probability?.toFixed(1)}%</span>
                                      </div>
                                    </div>
                                    
                                    {/* Level 2: Brand */}
                                    <div className="flex items-center justify-between p-2 bg-teal-50 rounded border border-teal-200 ml-4">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-teal-900">🏷️ Level 2: Brand | Category</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-sm font-bold text-teal-900">{rec.nested_breakdown.brand_probability?.toFixed(1)}%</span>
                                      </div>
                                    </div>
                                    
                                    {/* Level 3: Product */}
                                    <div className="flex items-center justify-between p-2 bg-blue-50 rounded border border-blue-200 ml-8">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-blue-900">📦 Level 3: Product | Brand</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-sm font-bold text-blue-900">{rec.nested_breakdown.product_probability?.toFixed(1)}%</span>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Explanation */}
                                  <div className="mt-3 p-3 bg-white rounded border border-green-200">
                                    <p className="text-xs font-semibold text-gray-900 mb-2">How It Works:</p>
                                    <div className="space-y-1.5 text-xs text-gray-700">
                                      <p>• {rec.explanation?.category || `Customer first chooses ${rec.category || 'this category'}`}</p>
                                      <p>• {rec.explanation?.brand || `Then selects ${rec.brand || 'this brand'} within the category`}</p>
                                      <p>• {rec.explanation?.product || 'Finally picks this specific product within the brand'}</p>
                                    </div>
                                  </div>

                                  <div className="mt-3 pt-2 border-t border-green-200">
                                    <p className="text-xs text-gray-700">
                                      <span className="font-semibold">Joint Probability:</span> {rec.nested_breakdown.category_probability?.toFixed(1)}% × {rec.nested_breakdown.brand_probability?.toFixed(1)}% × {rec.nested_breakdown.product_probability?.toFixed(1)}% = {rec.overall_probability?.toFixed(2)}%
                                    </p>
                                    <p className="text-xs text-gray-600 mt-1">
                                      💡 This model captures realistic substitution patterns within product nests (e.g., products within the same brand are more substitutable).
                                    </p>
                                  </div>
                                </div>
                              ) : rec.detailed_calculation && rec.scoring_method === '12_factor' ? (
                                /* 12-FACTOR DETAILED CALCULATION */
                                <div>
                                  <p className="text-xs font-semibold text-indigo-900 mb-3">
                                    📊 Comprehensive 12-Factor Scoring System
                                  </p>
                                  
                                  {/* Total Score */}
                                  <div className="mb-3 p-3 bg-white rounded-lg border-2 border-indigo-300">
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs font-bold text-gray-900">Total Match Score</span>
                                      <span className="text-lg font-bold text-indigo-600">{rec.detailed_calculation.total_percentage?.toFixed(1)}%</span>
                                    </div>
                                  </div>

                                  {/* TIER 1: Core Match Factors */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                                    <p className="text-xs font-bold text-purple-900 mb-3">🎯 TIER 1: Core Match Factors (70%)</p>
                                    
                                    {/* Factor 1: Price Alignment */}
                                    {rec.detailed_calculation.price_alignment && (
                                      <div className="mb-3 pb-3 border-b border-purple-200">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">1. Price Alignment</span>
                                          <span className="text-sm font-bold text-purple-700">{rec.detailed_calculation.price_alignment.result}</span>
                                        </div>
                                        <div className="text-xs text-gray-600 mb-1">
                                          <span className="font-mono bg-gray-100 px-1 rounded">{rec.detailed_calculation.price_alignment.calculation}</span>
                                        </div>
                                        <div className="text-xs text-gray-700">
                                          📌 {rec.detailed_calculation.price_alignment.actual_values}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">Why {(rec.detailed_calculation.price_alignment.weight * 100).toFixed(0)}%?</summary>
                                          <p className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200">
                                            Price is the PRIMARY purchase driver in retail. 25% reflects that 1 in 4 customers cite price as their #1 concern (McKinsey 2023).
                                          </p>
                                        </details>
                                      </div>
                                    )}

                                    {/* Factor 2: Category Match */}
                                    {rec.detailed_calculation.category_match && (
                                      <div className="mb-3 pb-3 border-b border-purple-200">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">2. Category Match</span>
                                          <span className="text-sm font-bold text-purple-700">{rec.detailed_calculation.category_match.result}</span>
                                        </div>
                                        <div className="text-xs text-gray-600 mb-1">
                                          <span className="font-mono bg-gray-100 px-1 rounded">{rec.detailed_calculation.category_match.calculation}</span>
                                        </div>
                                        <div className="text-xs text-gray-700">
                                          📌 {rec.detailed_calculation.category_match.actual_values}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">Why {(rec.detailed_calculation.category_match.weight * 100).toFixed(0)}%?</summary>
                                          <p className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200">
                                            Category determines NEED fulfillment. Equal to price (25%) because a perfect-price product in the wrong category is useless. 78% of shoppers filter by category before price (Amazon 2022).
                                          </p>
                                        </details>
                                      </div>
                                    )}

                                    {/* Factor 3: Expertise Match */}
                                    {rec.detailed_calculation.expertise_match && (
                                      <div className="mb-3 pb-3 border-b border-purple-200">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">3. Expertise Match</span>
                                          <span className="text-sm font-bold text-purple-700">{rec.detailed_calculation.expertise_match.result}</span>
                                        </div>
                                        <div className="text-xs text-gray-600 mb-1">
                                          <span className="font-mono bg-gray-100 px-1 rounded">{rec.detailed_calculation.expertise_match.calculation}</span>
                                        </div>
                                        <div className="text-xs text-gray-700">
                                          📌 {rec.detailed_calculation.expertise_match.actual_values}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">Why {(rec.detailed_calculation.expertise_match.weight * 100).toFixed(0)}%?</summary>
                                          <p className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200">
                                            ~1 in 8 returns (12.5%) are due to "too complicated" (REI data). Product complexity must match user skill level for satisfaction.
                                          </p>
                                        </details>
                                      </div>
                                    )}

                                    {/* Factor 4: Brand Loyalty */}
                                    {rec.detailed_calculation.brand_loyalty && (
                                      <div className="mb-0">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="text-xs font-semibold text-gray-900">4. Brand Loyalty</span>
                                          <span className="text-sm font-bold text-purple-700">{rec.detailed_calculation.brand_loyalty.result}</span>
                                        </div>
                                        <div className="text-xs text-gray-600 mb-1">
                                          <span className="font-mono bg-gray-100 px-1 rounded">{rec.detailed_calculation.brand_loyalty.calculation}</span>
                                        </div>
                                        <div className="text-xs text-gray-700">
                                          📌 {rec.detailed_calculation.brand_loyalty.actual_values}
                                        </div>
                                        <details className="mt-1">
                                          <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">Why {(rec.detailed_calculation.brand_loyalty.weight * 100).toFixed(0)}%?</summary>
                                          <p className="text-xs text-gray-600 mt-1 pl-3 border-l-2 border-blue-200">
                                            Repeat purchase rates increase 60-70% with brand familiarity (Nielsen). Outdoor brands like Osprey see 45% repeat rates.
                                          </p>
                                        </details>
                                      </div>
                                    )}
                                  </div>

                                  {/* TIER 2: Contextual Factors */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border border-blue-200">
                                    <p className="text-xs font-bold text-blue-900 mb-3">🎯 TIER 2: Contextual Factors (15%)</p>
                                    
                                    {['value_tier', 'bundle_preference', 'segment_affinity'].map((factorKey) => {
                                      const factor = rec.detailed_calculation[factorKey];
                                      if (!factor) return null;
                                      
                                      const factorNames = {
                                        'value_tier': 'Value Tier Match',
                                        'bundle_preference': 'Bundle Preference',
                                        'segment_affinity': 'Segment Affinity'
                                      };

                                      return (
                                        <div key={factorKey} className="mb-2 pb-2 border-b border-blue-100 last:border-0">
                                          <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-semibold text-gray-900">{factorNames[factorKey]}</span>
                                            <span className="text-xs font-bold text-blue-700">{factor.result}</span>
                                          </div>
                                          <div className="text-xs text-gray-700">📌 {factor.actual_values}</div>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {/* TIER 3: Social Proof & Quality */}
                                  <div className="mb-4 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                    <p className="text-xs font-bold text-green-900 mb-3">⭐ TIER 3: Social Proof & Quality (10%)</p>
                                    
                                    {['product_rating', 'popularity', 'co_occurrence'].map((factorKey) => {
                                      const factor = rec.detailed_calculation[factorKey];
                                      if (!factor) return null;
                                      
                                      const factorNames = {
                                        'product_rating': 'Product Rating',
                                        'popularity': 'Popularity',
                                        'co_occurrence': 'Co-Occurrence'
                                      };

                                      return (
                                        <div key={factorKey} className="mb-2 pb-2 border-b border-green-100 last:border-0">
                                          <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-semibold text-gray-900">{factorNames[factorKey]}</span>
                                            <span className="text-xs font-bold text-green-700">{factor.result}</span>
                                          </div>
                                          <div className="text-xs text-gray-700">📌 {factor.actual_values}</div>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {/* TIER 4: Temporal Factors */}
                                  <div className="mb-3 p-3 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border border-orange-200">
                                    <p className="text-xs font-bold text-orange-900 mb-3">⏱️ TIER 4: Temporal Factors (5%)</p>
                                    
                                    {['recency_boost', 'variety_bonus'].map((factorKey) => {
                                      const factor = rec.detailed_calculation[factorKey];
                                      if (!factor) return null;
                                      
                                      const factorNames = {
                                        'recency_boost': 'Recency Boost',
                                        'variety_bonus': 'Variety Bonus'
                                      };

                                      return (
                                        <div key={factorKey} className="mb-2 pb-2 border-b border-orange-100 last:border-0">
                                          <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-semibold text-gray-900">{factorNames[factorKey]}</span>
                                            <span className="text-xs font-bold text-orange-700">{factor.result}</span>
                                          </div>
                                          <div className="text-xs text-gray-700">📌 {factor.actual_values}</div>
                                        </div>
                                      );
                                    })}
                                  </div>

                                  {/* Summary */}
                                  <div className="mt-3 pt-3 border-t-2 border-indigo-300 bg-indigo-50 p-3 rounded-lg">
                                    <p className="text-xs text-gray-700 mb-2">
                                      <span className="font-semibold">📐 Formula:</span> Sum of all 12 weighted factors
                                    </p>
                                    <p className="text-xs font-bold text-indigo-900">
                                      Total Score = {rec.detailed_calculation.total_percentage?.toFixed(1)}%
                                    </p>
                                    <p className="text-xs text-gray-600 mt-2">
                                      💡 All weights sum to 100%. Each percentage is research-backed and scientifically justified.
                                    </p>
                                  </div>
                                </div>
                              ) : scoringMethod === 'logit' && rec.scoring_breakdown ? (
                                /* HYBRID ML MODEL EXPLANATION */
                                <div>
                                  <p className="text-xs font-semibold text-purple-900 mb-3">
                                    🎯 Hybrid Scoring Breakdown (50% ML + 50% Rules)
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
                                        <span className="text-xs font-bold text-blue-900">📐 Business Rules</span>
                                        <span className="text-xs text-blue-700">(50% weight)</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs text-blue-700">{(rec.scoring_breakdown.rule_score * 100).toFixed(1)}% →</span>
                                        <span className="text-sm font-bold text-blue-900">{(rec.scoring_breakdown.rule_contribution * 100).toFixed(1)}%</span>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Rule Factor Details */}
                                  <div className="mt-3 p-3 bg-white rounded border border-blue-200">
                                    <p className="text-xs font-semibold text-gray-900 mb-2">Business Rule Factors:</p>
                                    <div className="space-y-1.5">
                                      <div className="flex justify-between text-xs">
                                        <span className="text-gray-700">Price Match ({rec.price ? `$${rec.price}` : 'N/A'})</span>
                                        <span className="font-bold text-green-600">{(rec.scoring_breakdown.price_score * 100).toFixed(1)}%</span>
                                      </div>
                                      <div className="flex justify-between text-xs">
                                        <span className="text-gray-700">Category Match ({rec.category || 'N/A'})</span>
                                        <span className="font-bold text-blue-600">{(rec.scoring_breakdown.category_score * 100).toFixed(1)}%</span>
                                      </div>
                                      <div className="flex justify-between text-xs">
                                        <span className="text-gray-700">Expertise Match ({rec.complexity || 'N/A'})</span>
                                        <span className="font-bold text-purple-600">{(rec.scoring_breakdown.expertise_score * 100).toFixed(1)}%</span>
                                      </div>
                                      <div className="flex justify-between text-xs">
                                        <span className="text-gray-700">Quality Rating ({rec.avg_rating || 'N/A'} ⭐)</span>
                                        <span className="font-bold text-yellow-600">{(rec.scoring_breakdown.rating_score * 100).toFixed(1)}%</span>
                                      </div>
                                    </div>
                                  </div>

                                  <div className="mt-3 pt-2 border-t border-purple-200">
                                    <p className="text-xs text-gray-700">
                                      <span className="font-semibold">Formula:</span> ({(rec.scoring_breakdown.ml_probability * 100).toFixed(1)}% × 0.5) + ({(rec.scoring_breakdown.rule_score * 100).toFixed(1)}% × 0.5) = {(rec.scoring_breakdown.final_score * 100).toFixed(1)}%
                                    </p>
                                  </div>
                                </div>
                              ) : (
                                /* RULE-BASED EXPLANATION */
                                <div>
                                  <p className="text-xs font-semibold text-blue-900 mb-2">
                                    This score predicts how likely this customer is to purchase this product based on:
                                  </p>
                                  
                                  <div className="space-y-2">
                                    <div className="flex items-start gap-2">
                                      <div className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        35%
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-xs font-medium text-gray-900">Price Alignment</p>
                                        <p className="text-xs text-gray-600">How close product price matches persona's typical spending</p>
                                      </div>
                                    </div>
                                    
                                    <div className="flex items-start gap-2">
                                      <div className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                        30%
                                      </div>
                                      <div className="flex-1">
                                    <p className="text-xs font-medium text-gray-900">Category Match</p>
                                    <p className="text-xs text-gray-600">Does it match the persona's preferred product categories?</p>
                                  </div>
                                </div>
                                
                                <div className="flex items-start gap-2">
                                  <div className="bg-purple-100 text-purple-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                    20%
                                  </div>
                                  <div className="flex-1">
                                    <p className="text-xs font-medium text-gray-900">Expertise Match</p>
                                    <p className="text-xs text-gray-600">Product complexity aligns with customer skill level</p>
                                  </div>
                                </div>
                                
                                <div className="flex items-start gap-2">
                                  <div className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                    10%
                                  </div>
                                  <div className="flex-1">
                                    <p className="text-xs font-medium text-gray-900">Bundle Preference</p>
                                    <p className="text-xs text-gray-600">Matches persona's tendency to buy bundled vs individual items</p>
                                  </div>
                                </div>
                                
                                <div className="flex items-start gap-2">
                                  <div className="bg-yellow-100 text-yellow-700 text-xs font-bold px-2 py-1 rounded min-w-[45px] text-center">
                                    5%
                                  </div>
                                  <div className="flex-1">
                                    <p className="text-xs font-medium text-gray-900">Product Rating</p>
                                    <p className="text-xs text-gray-600">Higher-rated products get slight boost for quality assurance</p>
                                  </div>
                                </div>
                              </div>
                              
                              <div className="mt-3 pt-3 border-t border-blue-200">
                                <p className="text-xs text-gray-700">
                                  <span className="font-semibold">Formula:</span> Score = (Price × 0.35) + (Category × 0.30) + (Expertise × 0.20) + (Bundle × 0.10) + (Rating × 0.05)
                                </p>
                                <p className="text-xs text-gray-600 mt-1">
                                  💡 Scores above 20% indicate strong persona alignment. Below 5% suggests poor fit.
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

                {/* Features */}
                {rec.features && (
                  <div className="grid grid-cols-5 gap-2 mb-4">
                    {rec.features.setup_type && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Setup</p>
                        <p className="text-sm font-medium text-gray-900">{rec.features.setup_type}</p>
                      </div>
                    )}
                    {rec.features.complexity && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Complexity</p>
                        <p className="text-sm font-medium text-gray-900">{rec.features.complexity}</p>
                      </div>
                    )}
                    {rec.features.bundle_compatible && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Bundle</p>
                        <p className="text-sm font-medium text-gray-900">{rec.features.bundle_compatible}</p>
                      </div>
                    )}
                    {rec.features.weight_class && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Weight</p>
                        <p className="text-sm font-medium text-gray-900">{rec.features.weight_class}</p>
                      </div>
                    )}
                    {rec.features.weatherproof && (
                      <div className="bg-gray-50 rounded px-3 py-2 text-center">
                        <p className="text-xs text-gray-500">Weather</p>
                        <p className="text-sm font-medium text-gray-900">{rec.features.weatherproof}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Feature Lifts */}
                {rec.feature_lifts && Object.keys(rec.feature_lifts).length > 0 && (
                  <div className="border-t pt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Why this matches {persona}:</p>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(rec.feature_lifts).map(([feature, data]: [string, any]) => (
                        <div key={feature} className={`text-sm px-3 py-2 rounded ${data.boost_percent > 0 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                          <span className="font-medium">{feature}:</span> {data.boost_percent > 0 ? '+' : ''}{data.boost_percent.toFixed(0)}%
                          <span className="text-xs ml-2">({data.lift_factor.toFixed(2)}x)</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendation Text / Why This Product? */}
                {(rec.recommendation_text || rec.reason) && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-xs font-semibold text-green-800 mb-2">💡 Why This Product for This Segment?</p>
                    <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                      {rec.reason || rec.recommendation_text}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Out of Stock Section */}
          {outOfStockRecommendations.length > 0 && (
            <div className="mt-8">
              <button
                onClick={() => setShowOutOfStock(!showOutOfStock)}
                className="w-full bg-gradient-to-r from-gray-100 to-gray-50 hover:from-gray-200 hover:to-gray-100 rounded-lg p-6 transition-all duration-300 border-2 border-gray-200 hover:border-gray-300"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="bg-orange-100 rounded-lg p-3">
                      <ShoppingCart className="w-6 h-6 text-orange-600" />
                    </div>
                    <div className="text-left">
                      <h3 className="text-xl font-bold text-gray-900 flex items-center gap-3">
                        View Out of Stock Products
                        <span className="bg-orange-100 text-orange-700 text-sm font-bold px-3 py-1 rounded-full">
                          {outOfStockRecommendations.length}
                        </span>
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Items matching {mode === 'customer' ? 'this customer' : `${persona} persona`} but temporarily unavailable
                      </p>
                    </div>
                  </div>
                  <div className={`transform transition-transform duration-300 ${showOutOfStock ? 'rotate-180' : ''}`}>
                    <ChevronDown className="w-7 h-7 text-gray-600" />
                  </div>
                </div>
              </button>

              {/* Expandable Out of Stock Section */}
              {showOutOfStock && (
                <div className="mt-6 space-y-4 animate-fadeIn">
                  <div className="flex items-center gap-2 mb-4">
                    <h4 className="text-lg font-semibold text-gray-700">Currently Unavailable</h4>
                    <span className="badge badge-ghost text-xs">Out of Stock</span>
                  </div>
                  {outOfStockRecommendations.map((rec: any, index: number) => (
                    <div key={rec.product_id} className="bg-gray-50 rounded-lg shadow hover:shadow-md transition-shadow p-6 border-l-4 border-gray-400 opacity-75">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-2xl font-bold text-gray-400">#{index + 1}</span>
                            <h3 className="text-xl font-bold text-gray-700">{rec.product_name}</h3>
                            <span className="bg-red-100 text-red-700 text-xs font-bold px-3 py-1 rounded-full">
                              OUT OF STOCK
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-gray-600">
                            <span className="flex items-center gap-1">
                              <Package className="w-4 h-4" />
                              {rec.brand}
                            </span>
                            <span>•</span>
                            <span>{rec.category}</span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Star className="w-4 h-4 text-yellow-400" />
                              {rec.avg_rating} ({rec.num_reviews} reviews)
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-3xl font-bold text-gray-500 mb-1 line-through">
                            ${rec.price?.toFixed(2)}
                          </div>
                          <div className="px-3 py-1 rounded-full text-xs font-medium border bg-gray-200 text-gray-600 border-gray-300">
                            {rec.match_level}
                          </div>
                        </div>
                      </div>

                      <div className="text-sm text-gray-600 bg-white p-3 rounded">
                        💡 This product matches your preferences. You'll be notified when it's back in stock.
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}


import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Search, Star, DollarSign, ShoppingBag, TrendingUp, Package } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api';

export default function AcademyRecommendations() {
  const { customerId } = useParams<{ customerId: string }>();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'similar' | 'segment' | 'search'>('similar');

  // Fetch customer details
  const customerQuery = useQuery({
    queryKey: ['customer-details', customerId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/agent_a/customer/${customerId}`);
      if (!response.ok) throw new Error('Failed to fetch customer details');
      return response.json();
    },
    enabled: !!customerId
  });

  // Fetch similar products
  const similarQuery = useQuery({
    queryKey: ['recommendations-similar', customerId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/recommendations/${customerId}/similar`);
      if (!response.ok) throw new Error('Failed to fetch similar products');
      return response.json();
    },
    enabled: !!customerId && activeTab === 'similar'
  });

  // Fetch segment-based recommendations
  const segmentQuery = useQuery({
    queryKey: ['recommendations-segment', customerId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/recommendations/${customerId}/you-might-like`);
      if (!response.ok) throw new Error('Failed to fetch segment recommendations');
      return response.json();
    },
    enabled: !!customerId && activeTab === 'segment'
  });

  // Fetch search-based recommendations
  const searchQuery = useQuery({
    queryKey: ['recommendations-search', customerId, searchTerm],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/recommendations/${customerId}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search_term: searchTerm })
      });
      if (!response.ok) throw new Error('Failed to fetch search recommendations');
      return response.json();
    },
    enabled: !!customerId && !!searchTerm && activeTab === 'search'
  });

  const customer = customerQuery.data?.result || customerQuery.data;
  const similarData = similarQuery.data?.result;
  const segmentData = segmentQuery.data?.result;
  const searchData = searchQuery.data?.result;

  if (customerQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading customer data...</p>
        </div>
      </div>
    );
  }

  if (customerQuery.isError) {
    return (
      <div className="max-w-7xl mx-auto p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-red-700 mb-2">Error Loading Customer</h2>
          <p className="text-red-600">{customerQuery.error?.toString()}</p>
          <button
            onClick={() => navigate(-1)}
            className="mt-4 btn-secondary"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const renderProductCard = (product: any, reason: string) => (
    <div key={product.product_id} className="card hover:shadow-lg transition-shadow">
      <div className="card-body">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-1">{product.product_name}</h3>
            <p className="text-sm text-gray-600">{product.brand} • {product.category}</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-green-600">${product.price}</div>
            {product.rating && (
              <div className="flex items-center justify-end mt-1 text-sm text-yellow-600">
                <Star className="w-4 h-4 fill-current mr-1" />
                <span>{product.rating}</span>
                <span className="text-gray-400 ml-1">({product.num_reviews})</span>
              </div>
            )}
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
          <p className="text-sm text-blue-700">
            <span className="font-semibold">Why recommended:</span> {reason}
          </p>
        </div>

        <button className="mt-4 w-full btn-primary text-sm">
          View Product Details
        </button>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-8 space-y-8 animate-fadeIn">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate(-1)}
          className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Product Recommendations
            </h1>
            <p className="text-gray-600 text-lg">
              Personalized for {customer?.customer_name || 'Customer'}
            </p>
          </div>
        </div>
      </div>

      {/* Customer Summary Card */}
      {customer && (
        <div className="card bg-gradient-to-br from-green-50 to-blue-50">
          <div className="card-body">
            <div className="grid md:grid-cols-4 gap-6">
              <div>
                <div className="text-sm text-gray-600 mb-1">Customer Name</div>
                <div className="text-lg font-bold text-gray-900">{customer.customer_name}</div>
                <div className="text-sm text-blue-600 font-medium mt-1">{customer.persona}</div>
              </div>
              
              <div>
                <div className="text-sm text-gray-600 mb-1 flex items-center space-x-1">
                  <DollarSign className="w-4 h-4" />
                  <span>Annual Spend</span>
                </div>
                <div className="text-lg font-bold text-green-600">
                  ${customer.customer_metrics?.total_spend_12mo?.toFixed(0)}
                </div>
              </div>
              
              <div>
                <div className="text-sm text-gray-600 mb-1 flex items-center space-x-1">
                  <ShoppingBag className="w-4 h-4" />
                  <span>Purchase Frequency</span>
                </div>
                <div className="text-lg font-bold text-gray-900">
                  {customer.customer_metrics?.purchase_frequency}x/year
                </div>
              </div>
              
              <div>
                <div className="text-sm text-gray-600 mb-1 flex items-center space-x-1">
                  <Package className="w-4 h-4" />
                  <span>Avg Order Value</span>
                </div>
                <div className="text-lg font-bold text-gray-900">
                  ${customer.customer_metrics?.avg_order_value?.toFixed(0)}
                </div>
              </div>
            </div>

            {/* Price Range Indicator */}
            {(similarData?.price_range || segmentData?.price_range) && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  <span className="font-semibold">Typical price range:</span>{' '}
                  ${(similarData?.price_range?.min || segmentData?.price_range?.min)?.toFixed(0)} - $
                  {(similarData?.price_range?.max || segmentData?.price_range?.max)?.toFixed(0)}
                  {' '}(±50% of usual spend)
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="bg-white shadow-sm rounded-xl border border-gray-200 overflow-hidden">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('similar')}
            className={`flex-1 px-6 py-4 flex items-center justify-center space-x-2 font-medium transition-all ${
              activeTab === 'similar'
                ? 'bg-green-50 text-green-700 border-b-2 border-green-600'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <TrendingUp className="w-5 h-5" />
            <span>Similar Products</span>
          </button>
          
          <button
            onClick={() => setActiveTab('segment')}
            className={`flex-1 px-6 py-4 flex items-center justify-center space-x-2 font-medium transition-all ${
              activeTab === 'segment'
                ? 'bg-green-50 text-green-700 border-b-2 border-green-600'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <ShoppingBag className="w-5 h-5" />
            <span>You Might Like</span>
          </button>
          
          <button
            onClick={() => setActiveTab('search')}
            className={`flex-1 px-6 py-4 flex items-center justify-center space-x-2 font-medium transition-all ${
              activeTab === 'search'
                ? 'bg-green-50 text-green-700 border-b-2 border-green-600'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Search className="w-5 h-5" />
            <span>Search & Discover</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'similar' && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Similar to Your Purchases</h2>
          <p className="text-gray-600 mb-6">
            Based on your purchase history in {similarData?.preferred_category || 'camping gear'}
          </p>

          {similarQuery.isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-green-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading recommendations...</p>
            </div>
          ) : similarData?.recommendations?.length > 0 ? (
            <div className="grid md:grid-cols-3 gap-6">
              {similarData.recommendations.map((product: any) =>
                renderProductCard(product, product.reason)
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No similar products found. Try browsing other categories!
            </div>
          )}
        </div>
      )}

      {activeTab === 'segment' && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">You Might Like</h2>
          <p className="text-gray-600 mb-6">
            Popular with other customers in your segment ({segmentData?.segment_size || 0} similar customers)
          </p>

          {segmentQuery.isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-green-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading recommendations...</p>
            </div>
          ) : segmentData?.recommendations?.length > 0 ? (
            <div className="grid md:grid-cols-3 gap-6">
              {segmentData.recommendations.map((product: any) =>
                renderProductCard(product, product.reason)
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No segment recommendations available at this time.
            </div>
          )}
        </div>
      )}

      {activeTab === 'search' && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Search & Discover</h2>
          <p className="text-gray-600 mb-6">
            Find products that match your interests, personalized to your budget
          </p>

          {/* Search Input */}
          <div className="mb-8">
            <div className="flex space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      searchQuery.refetch();
                    }
                  }}
                  placeholder="Search for products (e.g., 'waterproof tent', '4-person sleeping bag')..."
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-600 focus:border-transparent"
                />
              </div>
              <button
                onClick={() => searchQuery.refetch()}
                disabled={!searchTerm || searchQuery.isFetching}
                className="btn-primary px-8"
              >
                {searchQuery.isFetching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>

          {/* Search Results */}
          {searchQuery.isFetching ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-green-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Searching for products...</p>
            </div>
          ) : searchData?.recommendations?.length > 0 ? (
            <>
              <div className="mb-4 text-sm text-gray-600">
                Found {searchData.recommendations.length} products matching "{searchData.search_term}"
                {searchData.method === 'semantic_search' && ' (using AI semantic search)'}
              </div>
              <div className="grid md:grid-cols-3 gap-6">
                {searchData.recommendations.map((product: any) =>
                  renderProductCard(product, product.reason)
                )}
              </div>
            </>
          ) : searchTerm && !searchQuery.isFetching ? (
            <div className="text-center py-12 text-gray-500">
              No products found matching "{searchTerm}". Try different keywords!
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              Enter a search term above to find products
            </div>
          )}
        </div>
      )}
    </div>
  );
}


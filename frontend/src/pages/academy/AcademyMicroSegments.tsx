import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ArrowLeft, Users, DollarSign, TrendingUp, Award, Shield, Star, ChevronRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'];

const LTV_TIER_COLORS: Record<string, string> = {
  'Bronze': '#cd7f32',
  'Silver': '#c0c0c0',
  'Gold': '#ffd700',
  'Platinum': '#e5e4e2'
};

export default function AcademyMicroSegments() {
  const { macroSegmentId } = useParams<{ macroSegmentId: string }>();
  const navigate = useNavigate();
  const [selectedMicroSegment, setSelectedMicroSegment] = useState<number | null>(null);

  // Query macro segment info
  const macroQuery = useQuery({
    queryKey: ['macro-segments'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/academy/macro-segments`);
      if (!response.ok) throw new Error('Failed to fetch macro segments');
      return response.json();
    }
  });

  // Query micro segments
  const microQuery = useQuery({
    queryKey: ['micro-segments', macroSegmentId],
    queryFn: async () => {
      // First try to create, then fetch
      try {
        await fetch(`${API_BASE_URL}/academy/micro-segments/${macroSegmentId}`, {
          method: 'POST'
        });
      } catch (error) {
        console.log('Micro segments may already exist, fetching...');
      }
      
      const response = await fetch(`${API_BASE_URL}/academy/micro-segments/${macroSegmentId}`);
      if (!response.ok) throw new Error('Failed to fetch micro segments');
      return response.json();
    },
    enabled: !!macroSegmentId
  });

  console.log('🔍 AcademyMicroSegments - Data received:', {
    macroSegmentId,
    macroQueryData: macroQuery.data,
    microQueryData: microQuery.data,
    microQuerySuccess: microQuery.isSuccess,
    microQueryError: microQuery.error
  });

  const macroSegment = macroQuery.data?.segments?.find(
    (s: any) => s.cluster_id === parseInt(macroSegmentId || '0')
  );
  const microData = microQuery.data?.result;
  const microSegments = microData?.micro_segments || {};

  console.log('🔍 Parsed data:', {
    macroSegment,
    microData,
    microSegments,
    microSegmentsType: typeof microSegments,
    microSegmentsKeys: Object.keys(microSegments),
    microSegmentsLength: Object.keys(microSegments).length
  });

  if (macroQuery.isLoading || microQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading micro segments...</p>
        </div>
      </div>
    );
  }

  if (macroQuery.isError || microQuery.isError) {
    return (
      <div className="max-w-7xl mx-auto p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-red-700 mb-2">Error Loading Data</h2>
          <p className="text-red-600">
            {macroQuery.error?.toString() || microQuery.error?.toString()}
          </p>
          <button
            onClick={() => navigate('/nba-platform/academy')}
            className="mt-4 btn-secondary"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Macro Segments
          </button>
        </div>
      </div>
    );
  }

  // Check if microSegments is empty
  if (!microSegments || Object.keys(microSegments).length === 0) {
    console.error('❌ No micro segments data available!', {
      microQuery: microQuery.data,
      microData,
      microSegments
    });
    return (
      <div className="max-w-7xl mx-auto p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-yellow-700 mb-2">No Micro Segments Found</h2>
          <p className="text-yellow-600 mb-4">
            Micro segments data is not available. This could be because:
          </p>
          <ul className="list-disc list-inside text-yellow-600 mb-4">
            <li>The macro segment hasn't been created yet</li>
            <li>Agent A needs to be executed first</li>
            <li>The API returned unexpected data format</li>
          </ul>
          <div className="bg-gray-900 text-gray-100 p-3 rounded text-sm font-mono mb-4">
            <div>API Response: {JSON.stringify(microQuery.data, null, 2)}</div>
          </div>
          <button
            onClick={() => navigate('/academy/agent-a')}
            className="btn-primary"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Agent A
          </button>
        </div>
      </div>
    );
  }

  // Prepare data for charts
  const microSizeData = Object.values(microSegments).map((ms: any) => ({
    name: ms.segment_name,
    size: ms.size,
    percentage: ms.percentage
  }));

  const microRevenueData = Object.values(microSegments).map((ms: any) => ({
    name: ms.segment_name.split('-')[0], // Shortened name
    revenue: ms.revenue_metrics?.total_revenue || 0,
    avgValue: ms.revenue_metrics?.avg_customer_value || 0
  }));

  return (
    <div className="max-w-7xl mx-auto p-8 space-y-8 animate-fadeIn">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/academy')}
          className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Macro Segments</span>
        </button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              {macroSegment?.segment_name || 'Micro Segments'}
            </h1>
            <p className="text-gray-600 text-lg">
              {microData?.n_micro_segments || 0} micro segments identified within this macro persona
            </p>
          </div>
          
          {macroSegment && (
            <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg p-4 border border-green-200">
              <div className="text-sm text-gray-600">Macro Segment Size</div>
              <div className="text-2xl font-bold text-gray-900">
                {microData?.total_customers?.toLocaleString()} customers
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Micro Segment Overview */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Size Distribution Chart */}
        <div className="card">
          <div className="card-body">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Segment Size Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={microSizeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.percentage}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="size"
                >
                  {microSizeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Revenue by Micro Segment */}
        <div className="card">
          <div className="card-body">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Revenue by Micro Segment</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={microRevenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="revenue" fill="#10b981" name="Total Revenue ($)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Micro Segment Cards */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
          <Users className="w-7 h-7 text-green-600" />
          <span>Micro Segments</span>
        </h2>
        
        <div className="card-grid-2">
          {Object.entries(microSegments).map(([microId, segment]: [string, any]) => (
            <div
              key={microId}
              onClick={() => setSelectedMicroSegment(selectedMicroSegment === parseInt(microId) ? null : parseInt(microId))}
              className="card hover:shadow-xl transition-all duration-300 cursor-pointer group h-full flex flex-col"
            >
              <div className="card-body flex-1 flex flex-col">
                {/* Header with LTV Tier Badge */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      {segment.segment_name}
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span
                        className="px-3 py-1 rounded-full text-sm font-bold"
                        style={{
                          backgroundColor: `${LTV_TIER_COLORS[segment.ltv_tier]}20`,
                          color: LTV_TIER_COLORS[segment.ltv_tier]
                        }}
                      >
                        {segment.ltv_tier} Tier
                      </span>
                      <span className="text-sm text-gray-600">
                        {segment.size} customers ({segment.percentage}%)
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-green-50 rounded-lg p-3 border border-green-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs text-gray-600">Avg Customer Value</div>
                        <div className="text-lg font-bold text-green-700">
                          ${segment.revenue_metrics?.avg_customer_value?.toFixed(0)}
                        </div>
                      </div>
                      <DollarSign className="w-6 h-6 text-green-600 opacity-50" />
                    </div>
                  </div>

                  <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs text-gray-600">Total Revenue</div>
                        <div className="text-lg font-bold text-blue-700">
                          ${(segment.revenue_metrics?.total_revenue / 1000).toFixed(1)}K
                        </div>
                      </div>
                      <TrendingUp className="w-6 h-6 text-blue-600 opacity-50" />
                    </div>
                  </div>
                </div>

                {/* Characteristics */}
                <div className="space-y-2 pt-3 border-t border-gray-200 flex-1 flex flex-col">
                  <div className="text-sm font-semibold text-gray-900 mb-2">Key Characteristics</div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 flex items-center space-x-2">
                      <Star className="w-4 h-4 text-yellow-500" />
                      <span>Expertise Level:</span>
                    </span>
                    <span className="font-semibold text-gray-900">
                      {segment.characteristics?.avg_expertise?.toFixed(1)}/5.0
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 flex items-center space-x-2">
                      <Award className="w-4 h-4 text-blue-500" />
                      <span>Brand Loyalty:</span>
                    </span>
                    <span className="font-semibold text-gray-900">
                      {(segment.characteristics?.avg_brand_loyalty * 100)?.toFixed(0)}%
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 flex items-center space-x-2">
                      <Shield className="w-4 h-4 text-purple-500" />
                      <span>Preferred Category:</span>
                    </span>
                    <span className="font-semibold text-gray-900 text-xs">
                      {segment.characteristics?.dominant_category}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm mb-auto">
                    <span className="text-gray-600">Avg Purchase Freq:</span>
                    <span className="font-semibold text-gray-900">
                      {segment.characteristics?.avg_purchase_frequency?.toFixed(1)}x/year
                    </span>
                  </div>
                </div>

                {/* Expanded Details */}
                {selectedMicroSegment === parseInt(microId) && (
                  <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                    <h4 className="text-sm font-bold text-gray-900">Top Customers</h4>
                    <div className="space-y-2">
                      {segment.top_customers?.map((customer: any, idx: number) => (
                        <div
                          key={idx}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/academy/customer/${customer.customer_id}/recommendations`);
                          }}
                          className="flex items-center justify-between p-2 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
                        >
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {customer.customer_name}
                            </div>
                            <div className="text-xs text-gray-500">
                              {customer.purchase_frequency}x purchases
                            </div>
                          </div>
                          <div className="text-sm font-bold text-green-600">
                            ${customer.total_spend?.toFixed(0)}
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        // Navigate to recommendations for this segment
                        alert('Segment recommendations coming soon!');
                      }}
                      className="w-full mt-3 btn-primary text-sm"
                    >
                      View Segment Recommendations
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


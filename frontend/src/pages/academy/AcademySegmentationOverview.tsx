import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, Users, Target, TrendingUp, DollarSign, Activity, Layers } from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';

const API_BASE_URL = getBankingApiBase();

interface MacroPersona {
  cluster_id: number;
  persona_name: string;
  short_name: string;
  size: number;
  percentage: number;
  total_revenue: number;
  avg_spend: number;
  confidence_avg: number;
  description: string;
}

interface MicroSegment {
  micro_cluster_id: number;
  name: string;
  size: number;
  percentage: number;
  avg_spend: number;
  characteristics: any;
}

const AcademySegmentationOverview: React.FC = () => {
  const queryClient = useQueryClient();
  const [expandedMacro, setExpandedMacro] = useState<number[]>([]);
  const [loadingMicro, setLoadingMicro] = useState<number[]>([]);
  const [renderError, setRenderError] = useState<string | null>(null);

  // Fetch macro segmentation results
  const { data: macroData, isLoading: macroLoading, error: macroError } = useQuery({
    queryKey: ['academy-agent-a-results'],  // Use same key as Agent A page for consistency
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/results`);
      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to fetch macro results');
      }
      const data = await response.json();
      return data.results || data;  // Extract nested results if present
    },
    refetchOnMount: true,  // Always fetch fresh data when component mounts
    staleTime: 0  // Consider data stale immediately so it refetches
  });

  // Store micro segments by macro cluster
  const [microSegments, setMicroSegments] = useState<Record<number, MicroSegment[]>>({});

  // Load micro segments for a macro cluster
  const loadMicroSegments = async (macroClusterId: number) => {
    setLoadingMicro(prev => [...prev, macroClusterId]);
    
    try {
      console.log(`🚀 Creating micro segments for cluster ${macroClusterId}...`);
      
      // First, create micro segments
      const createResponse = await fetch(
        `${API_BASE_URL}/api/academy/micro-segments/${macroClusterId}`,
        { method: 'POST' }
      );
      
      console.log(`Create response status: ${createResponse.status}`);
      
      if (!createResponse.ok) {
        const errorText = await createResponse.text();
        console.error('Create failed:', errorText);
        throw new Error(`Failed to create micro segments: ${createResponse.status} - ${errorText}`);
      }
      
      const createData = await createResponse.json();
      console.log('Create response:', createData);
      
      // Then fetch them
      console.log(`📥 Fetching micro segments for cluster ${macroClusterId}...`);
      const fetchResponse = await fetch(
        `${API_BASE_URL}/api/academy/micro-segments/${macroClusterId}`
      );
      
      console.log(`Fetch response status: ${fetchResponse.status}`);
      
      if (!fetchResponse.ok) {
        const errorText = await fetchResponse.text();
        console.error('Fetch failed:', errorText);
        throw new Error(`Failed to fetch micro segments: ${fetchResponse.status} - ${errorText}`);
      }
      
      const data = await fetchResponse.json();
      
      // Backend returns { success: true, result: { micro_segments: [...] } }
      const microSegments = data.result?.micro_segments || data.micro_segments || [];
      
      console.log(`✓ Loaded ${microSegments.length} micro segments for cluster ${macroClusterId}`);
      console.log('Micro segments data:', microSegments);
      
      // Validate micro segments have required fields
      const validMicroSegments = microSegments.filter((seg: any) => seg && typeof seg === 'object');
      
      if (validMicroSegments.length === 0 && microSegments.length > 0) {
        console.warn('Warning: Micro segments data is malformed', microSegments);
      }
      
      setMicroSegments(prev => ({
        ...prev,
        [macroClusterId]: validMicroSegments
      }));
    } catch (error) {
      console.error('Error loading micro segments for cluster', macroClusterId, ':', error);
      // Set empty array so user knows it failed
      setMicroSegments(prev => ({
        ...prev,
        [macroClusterId]: []
      }));
    } finally {
      setLoadingMicro(prev => prev.filter(id => id !== macroClusterId));
    }
  };

  // Toggle macro expansion
  const toggleMacro = (macroClusterId: number) => {
    if (expandedMacro.includes(macroClusterId)) {
      // Collapse
      setExpandedMacro(prev => prev.filter(id => id !== macroClusterId));
    } else {
      // Expand
      setExpandedMacro(prev => [...prev, macroClusterId]);
      
      // Load micro segments if not already loaded
      if (!microSegments[macroClusterId]) {
        loadMicroSegments(macroClusterId);
      }
    }
  };

  if (macroLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading segmentation data...</p>
        </div>
      </div>
    );
  }

  // Check if Agent A has been run
  if (!macroData || !macroData.personas || Object.keys(macroData.personas).length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            <Layers className="inline-block mr-3 text-blue-600" size={32} />
            Complete Segmentation Overview
          </h1>
          <p className="text-gray-600 text-lg">
            Hierarchical view of macro personas and their micro segments
          </p>
        </div>

        <div className="card bg-yellow-50 border-yellow-200">
          <div className="card-body text-center py-12">
            <div className="text-6xl mb-4">🏕️</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">No Segmentation Data Available</h2>
            <p className="text-gray-700 mb-6">
              You need to run Agent A (Macro Segmentation) first before viewing this overview.
            </p>
            <div className="flex items-center justify-center gap-4">
              <a href="/academy/agent-a" className="btn-primary">
                Go to Agent A
              </a>
              <a href="/academy" className="btn-secondary">
                Back to Dashboard
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const personas = macroData.personas || {};
  const personaList = Object.values(personas) as MacroPersona[];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          <Layers className="inline-block mr-3 text-blue-600" size={32} />
          Complete Segmentation Overview
        </h1>
        <p className="text-gray-600 text-lg">
          Hierarchical view of macro personas and their micro segments
        </p>
      </div>

      {/* Workflow Explanation */}
      <div className="card bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 mb-8">
        <div className="card-body">
          <h2 className="text-xl font-semibold text-blue-900 mb-4">How Agent A Segmentation Works</h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                <Layers className="text-white" size={28} />
              </div>
              <h3 className="font-semibold text-blue-900 mb-2">Step 1: Macro Segmentation</h3>
              <p className="text-sm text-blue-800">
                K-Prototypes clustering identifies {personaList.length} broad customer personas based on behavior, demographics, and spending patterns
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center mx-auto mb-3">
                <Target className="text-white" size={28} />
              </div>
              <h3 className="font-semibold text-indigo-900 mb-2">Step 2: Micro Segmentation</h3>
              <p className="text-sm text-indigo-800">
                Within each macro persona, K-Means clustering finds 2-3 micro segments with distinct sub-behaviors and needs
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-3">
                <Activity className="text-white" size={28} />
              </div>
              <h3 className="font-semibold text-purple-900 mb-2">Step 3: Personalization</h3>
              <p className="text-sm text-purple-800">
                Each micro segment receives tailored product recommendations and marketing strategies for maximum relevance
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid md:grid-cols-4 gap-4 mb-8">
        <div className="card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm mb-1">Macro Personas</p>
                <p className="text-3xl font-bold">{personaList.length}</p>
              </div>
              <Users className="text-blue-200" size={40} />
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-indigo-500 to-indigo-600 text-white">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-indigo-100 text-sm mb-1">Total Customers</p>
                <p className="text-3xl font-bold">
                  {personaList.reduce((sum, p) => sum + p.size, 0).toLocaleString()}
                </p>
              </div>
              <Target className="text-indigo-200" size={40} />
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm mb-1">Total Revenue</p>
                <p className="text-3xl font-bold">
                  ${(personaList.reduce((sum, p) => sum + p.total_revenue, 0) / 1000000).toFixed(1)}M
                </p>
              </div>
              <DollarSign className="text-purple-200" size={40} />
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-pink-500 to-pink-600 text-white">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-pink-100 text-sm mb-1">Avg Confidence</p>
                <p className="text-3xl font-bold">
                  {(personaList.reduce((sum, p) => sum + p.confidence_avg, 0) / personaList.length).toFixed(1)}%
                </p>
              </div>
              <Activity className="text-pink-200" size={40} />
            </div>
          </div>
        </div>
      </div>

      {/* Hierarchical Segmentation View */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Hierarchical Segmentation Tree</h2>
        
        {personaList.length === 0 ? (
          <div className="card bg-yellow-50 border-yellow-200">
            <div className="card-body text-center py-8">
              <p className="text-gray-600">No personas found in the data</p>
            </div>
          </div>
        ) : null}
        
        {personaList.map((persona, index) => {
          // Validate persona object
          if (!persona || typeof persona !== 'object') {
            console.error('Invalid persona at index', index, persona);
            return null;
          }
          const isExpanded = expandedMacro.includes(persona.cluster_id);
          const isLoadingMicro = loadingMicro.includes(persona.cluster_id);
          const microSegs = microSegments[persona.cluster_id] || [];

          return (
            <div key={persona.cluster_id} className="card border-2 hover:shadow-lg transition-shadow">
              {/* Macro Persona Header */}
              <div 
                className="card-body cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => toggleMacro(persona.cluster_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    {/* Expand/Collapse Icon */}
                    {isExpanded ? (
                      <ChevronDown className="text-blue-600 flex-shrink-0" size={24} />
                    ) : (
                      <ChevronRight className="text-gray-400 flex-shrink-0" size={24} />
                    )}

                    {/* Persona Info */}
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-xl font-bold text-gray-900">
                          {persona.persona_name}
                        </h3>
                        <span className="badge badge-primary">
                          Macro Cluster {persona.cluster_id}
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm mb-3">{persona.description}</p>
                      
                      {/* Metrics */}
                      <div className="flex items-center space-x-6 text-sm">
                        <div className="flex items-center space-x-2">
                          <Users className="text-blue-600" size={16} />
                          <span className="text-gray-700">
                            <span className="font-semibold">{persona.size.toLocaleString()}</span> customers
                            <span className="text-gray-500 ml-1">({persona.percentage.toFixed(1)}%)</span>
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <DollarSign className="text-green-600" size={16} />
                          <span className="text-gray-700">
                            <span className="font-semibold">${persona.total_revenue.toLocaleString()}</span> revenue
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <TrendingUp className="text-purple-600" size={16} />
                          <span className="text-gray-700">
                            <span className="font-semibold">${persona.avg_spend.toFixed(0)}</span> avg spend
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Activity className="text-orange-600" size={16} />
                          <span className="text-gray-700">
                            <span className="font-semibold">{persona.confidence_avg.toFixed(1)}%</span> confidence
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Click hint */}
                  <div className="text-sm text-gray-400 flex-shrink-0">
                    {isExpanded ? 'Click to collapse' : 'Click to see micro segments'}
                  </div>
                </div>
              </div>

              {/* Micro Segments (Expanded) */}
              {isExpanded && (
                <div className="border-t border-gray-200 bg-gray-50 p-6">
                  {isLoadingMicro ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-3"></div>
                      <p className="text-gray-600">Generating micro segments...</p>
                    </div>
                  ) : microSegs.length === 0 ? (
                    <div className="text-center py-8">
                      <Target className="text-gray-400 mx-auto mb-3" size={48} />
                      <p className="text-gray-600">No micro segments available</p>
                    </div>
                  ) : (
                    <>
                      <h4 className="text-lg font-semibold text-gray-900 mb-4">
                        Micro Segments within "{persona.persona_name}"
                      </h4>
                      
                      <div className="grid md:grid-cols-3 gap-4">
                        {microSegs.map((micro, idx) => (
                          <div 
                            key={micro?.micro_cluster_id ?? idx}
                            className="card bg-white border-2 border-indigo-200 hover:border-indigo-400 transition-colors"
                          >
                            <div className="card-body">
                              <div className="flex items-start justify-between mb-3">
                                <h5 className="font-bold text-gray-900">{micro?.name || 'Unnamed Segment'}</h5>
                                <span className="badge badge-secondary text-xs">
                                  {micro?.micro_cluster_id ?? idx}
                                </span>
                              </div>
                              
                              <div className="space-y-2 text-sm">
                                <div className="flex items-center justify-between">
                                  <span className="text-gray-600">Customers:</span>
                                  <span className="font-semibold text-gray-900">
                                    {(micro?.size ?? 0).toLocaleString()} ({(micro?.percentage ?? 0).toFixed(1)}%)
                                  </span>
                                </div>
                                
                                <div className="flex items-center justify-between">
                                  <span className="text-gray-600">Avg Spend:</span>
                                  <span className="font-semibold text-green-700">
                                    ${(micro?.avg_spend ?? 0).toFixed(0)}
                                  </span>
                                </div>
                                
                                {micro?.characteristics && Object.keys(micro.characteristics).length > 0 && (
                                  <div className="mt-3 pt-3 border-t border-gray-200">
                                    <p className="text-xs text-gray-500 mb-2">Key Traits:</p>
                                    <div className="flex flex-wrap gap-1">
                                      {Object.entries(micro.characteristics).slice(0, 3).map(([key, value]: [string, any]) => (
                                        <span 
                                          key={key}
                                          className="badge badge-sm bg-indigo-100 text-indigo-700 border-0"
                                        >
                                          {key}: {typeof value === 'number' ? value.toFixed(1) : String(value)}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Instructions */}
      <div className="card bg-blue-50 border-blue-200 mt-8">
        <div className="card-body">
          <h3 className="font-semibold text-blue-900 mb-3">💡 How to Use This View</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start">
              <span className="mr-2">1.</span>
              <span>Each card represents a <strong>macro persona</strong> (broad customer segment)</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">2.</span>
              <span><strong>Click any card</strong> to expand and see micro segments within that persona</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">3.</span>
              <span>Micro segments show <strong>sub-groups</strong> with distinct behaviors for hyper-personalization</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">4.</span>
              <span>Use this view for <strong>demos, presentations, and strategy planning</strong></span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AcademySegmentationOverview;


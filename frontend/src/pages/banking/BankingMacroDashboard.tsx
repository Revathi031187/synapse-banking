import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  ChevronDown, ChevronUp, Users, Target, TrendingUp, DollarSign,
  Activity, Layers, AlertCircle
} from 'lucide-react';

const BOILERPLATE_PATTERNS = [
  /^(here are (the |some )?(opportunities|behaviors|key behaviors|marketing opportunities))/i,
  /^(the following (are|opportunities|behaviors)|below are|these are)/i,
  /^(opportunities for marketers|key behaviors for)/i,
  /with capacity for premium product adoption/i,
  /^high income earners.*capacity for/i,
];

/** Strip LLM boilerplate phrases that add no information */
function cleanList(items: string[]): string[] {
  return items
    .map(s => s.trim())
    .filter(s => s.length > 6 && !BOILERPLATE_PATTERNS.some(re => re.test(s)));
}

/** Remove markdown bold markers, leading symbols, and emoji characters */
function cleanText(text: string): string {
  return text
    .replace(/\*\*/g, '')
    .replace(/^[\-•→✓]\s*/, '')
    .replace(/[\u{1F000}-\u{1FAFF}]|[\u{2600}-\u{27BF}]|[\u{FE00}-\u{FE0F}]/gu, '')
    .trim();
}

import { getBankingApiBase } from '../../utils/apiBase';
import { formatCompactUsd } from '../../utils/formatCurrency';
import { useSessionStorageState } from '../../hooks/useSessionStorageState';

interface MacroPersona {
  cluster_id: number;
  persona_name: string;
  name: string;
  size: number;
  percentage: number;
  total_revenue: number;
  avg_balance: number;
  avg_transactions: number; // Monthly banking events count (not dollar value)
  avg_intent_score: number;
  confidence_avg: number;
  description: string;
  emoji: string;
  image_url?: string;
  color_theme?: string;
  visual_emoji?: string;
  characteristics?: {
    avg_products?: number;
    avg_digital_engagement?: number;
    [key: string]: unknown;
  };
  segment_explanation?: {
    name_explanation?: string;
    segment_definition?: string;
    key_behaviors: string[];
    marketing_recommendations: string[];
    why_in_segment?: string;
  };
}

interface MicroSegment {
  micro_cluster_id: number;
  name: string;
  size: number;
  percentage: number;
  avg_balance: number;
  avg_spend: number;
  ltv_tier: string;
  characteristics?: {
    avg_portfolio_depth?: number;
    avg_digital_engagement?: number;
    [key: string]: unknown;
  };
  description?: string;
  top_customers?: Array<{customer_id: string; customer_name: string; total_balance?: number; total_deposits?: number}>;
  segment_explanation?: {
    name_explanation?: string;
    segment_definition?: string;
    key_behaviors: string[];
    marketing_recommendations: string[];
    why_in_segment?: string;
  };
}

const MACRO_UI_KEY = 'banking-macro-dashboard-v1';

export default function BankingMacroDashboard() {
  const API_BASE_URL = getBankingApiBase();
  const [ui, setUi] = useSessionStorageState(MACRO_UI_KEY, {
    expandedMacro: null as number | null,
    microSegments: {} as Record<number, MicroSegment[]>,
  });
  const { expandedMacro, microSegments } = ui;
  const [loadingMicro, setLoadingMicro] = React.useState<number[]>([]);

  // Fetch macro segmentation results
  const { data: macroData, isLoading: macroLoading, error: macroError } = useQuery({
    queryKey: ['banking-agent-a-results'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/banking/agent_a/results`);
      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to fetch macro results');
      }
      const data = await response.json();
      return data.results || data;
    },
    staleTime: 0,
    refetchOnMount: true
  });

  // Load micro segments for a macro cluster
  const loadMicroSegments = async (macroClusterId: number) => {
    if (microSegments[macroClusterId]) return; // Already loaded
    
    setLoadingMicro(prev => [...prev, macroClusterId]);
    
    try {
      console.log(`🚀 Creating micro segments for cluster ${macroClusterId}...`);
      
      // Create micro segments
      const createResponse = await fetch(
        `${API_BASE_URL}/api/banking/micro-segments/${macroClusterId}`,
        { method: 'POST' }
      );
      
      if (!createResponse.ok) {
        throw new Error('Failed to create micro segments');
      }
      
      // Fetch micro segments
      const fetchResponse = await fetch(
        `${API_BASE_URL}/api/banking/micro-segments/${macroClusterId}`
      );
      
      if (!fetchResponse.ok) {
        throw new Error('Failed to fetch micro segments');
      }
      
      const data = await fetchResponse.json();
      const microSegs = data.result?.micro_segments || data.micro_segments || [];
      
      console.log(`✓ Loaded ${microSegs.length} micro segments for cluster ${macroClusterId}`);
      
      setUi((prev) => ({
        ...prev,
        microSegments: {
          ...prev.microSegments,
          [macroClusterId]: microSegs,
        },
      }));
    } catch (error) {
      console.error('Error loading micro segments:', error);
      setUi((prev) => ({
        ...prev,
        microSegments: {
          ...prev.microSegments,
          [macroClusterId]: [],
        },
      }));
    } finally {
      setLoadingMicro(prev => prev.filter(id => id !== macroClusterId));
    }
  };

  // Toggle macro expansion
  const toggleMacro = async (macroClusterId: number) => {
    console.log('🔄 toggleMacro called for cluster:', macroClusterId, 'Current expanded:', expandedMacro);
    
    if (expandedMacro === macroClusterId) {
      console.log('📦 Collapsing macro segment:', macroClusterId);
      setUi((prev) => ({ ...prev, expandedMacro: null }));
    } else {
      console.log('📂 Expanding macro segment:', macroClusterId);
      setUi((prev) => ({ ...prev, expandedMacro: macroClusterId }));
      
      if (!microSegments[macroClusterId]) {
        await loadMicroSegments(macroClusterId);
      }
    }
  };

  const personaList: MacroPersona[] = React.useMemo(() => {
    const personas = macroData?.personas;
    if (!personas) return [];
    const list = Object.values(personas) as MacroPersona[];
    return list.sort((a, b) => (b.avg_balance || 0) - (a.avg_balance || 0));
  }, [macroData]);

  if (macroLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-700 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading macro dashboard...</p>
        </div>
      </div>
    );
  }

  if (macroError || !macroData || personaList.length === 0) {
    return (
      <div className="flex justify-center py-8">
        <div className="w-full max-w-2xl">
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-300 rounded-xl p-8 text-center">
            <div className="mb-4">
              <AlertCircle className="w-16 h-16 text-amber-600 mx-auto" />
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-3">Segmentation Not Run Yet</h1>
            <p className="text-gray-700 mb-6">
              Macro segments are not available because <strong>Customer Segmentation hasn't been executed</strong>.
            </p>
            <div className="bg-white rounded-lg p-4 mb-6 text-left">
              <p className="text-sm font-semibold text-gray-900 mb-2">To view macro segments:</p>
              <ol className="text-sm text-gray-700 space-y-1 ml-4">
                <li>1. Go to the <strong>Data Loader</strong> tab</li>
                <li>2. Load the dataset, then click <strong>"Run Segmentation Analysis"</strong></li>
                <li>3. Wait for segmentation to complete</li>
                <li>4. Return to this page to view macro segments</li>
              </ol>
            </div>
            <Link
              to="/banking/data-loader"
              className="inline-flex items-center gap-2 bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-800 transition-colors"
            >
              <Target className="w-5 h-5" />
              Go to Data Loader
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Segments View</h1>
        <p className="text-gray-500 text-sm mt-1">Macro and micro customer segments</p>
      </div>

      <div>
        {/* Macro Persona Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8">
          {personaList.map((persona) => (
            <MacroPersonaCard
              key={persona.cluster_id}
              persona={persona}
              isExpanded={expandedMacro === persona.cluster_id}
              onToggle={() => toggleMacro(persona.cluster_id)}
            />
          ))}
        </div>

        {/* Expanded Micro Segments Below Macro Cards */}
        {expandedMacro !== null && (() => {
          const expandedPersona = personaList.find(p => p.cluster_id === expandedMacro);
          if (!expandedPersona) return null;
          
          return (
            <div className="mt-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg shadow-lg p-8 border-l-4 border-blue-700 animate-fadeIn">
              <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  Micro Segments: {expandedPersona.persona_name || expandedPersona.name}
                </h3>
                <p className="text-gray-600">Detailed sub-segments within this macro persona</p>
              </div>

              {/* Micro Segment Cards */}
              {loadingMicro.includes(expandedMacro) ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700 mx-auto"></div>
                  <p className="text-gray-600 mt-4">Loading micro segments...</p>
                </div>
              ) : microSegments[expandedMacro]?.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {microSegments[expandedMacro].map((micro) => (
                    <MicroSegmentCard
                      key={micro.micro_cluster_id}
                      micro={micro}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-white rounded-lg">
                  <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600">No micro segments available</p>
                </div>
              )}
            </div>
          );
        })()}
      </div>
    </div>
  );
}

// Macro Persona Card Component - Professional Design with Images
function MacroPersonaCard({ persona, isExpanded, onToggle }: any) {
  const [showExplanation, setShowExplanation] = React.useState(false);
  
  // Banking themed images from Unsplash
  const getBankingImage = () => {
    const images = [
      'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=800&q=80', // Business/Office
      'https://images.unsplash.com/photo-1560472355-536de3962603?w=800&q=80', // Finance/Banking
      'https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=800&q=80', // Investment
      'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800&q=80', // Professional
      'https://images.unsplash.com/photo-1554224311-beee4f640552?w=800&q=80', // Team/Business
    ];
    return persona.image_url || images[persona.cluster_id % images.length];
  };
  
  const imageUrl = getBankingImage();
  
  // Professional color schemes for banking
  const getCardColor = () => {
    const colors = [
      '#1e40af', // Blue - High Net Worth
      '#059669', // Green - Young Professionals  
      '#d97706', // Amber - Small Business
      '#7c3aed', // Purple - Digital Natives
      '#dc2626', // Red - Mass Market
    ];
    return persona.color_theme || colors[persona.cluster_id % colors.length];
  };

  const cardColor = getCardColor();

  return (
    <div className="flex flex-col">
      {/* Professional Card Design with Smooth Hover Expansion */}
      <div
        className="bg-white rounded-lg overflow-hidden shadow-md hover:shadow-2xl transition-all duration-500 ease-in-out border-t-4 flex flex-col transform hover:scale-105 hover:-translate-y-2"
        style={{ borderTopColor: cardColor, height: '540px' }}
      >
        {/* Colored Header with Segment Name */}
        <div 
          className="px-4 py-4 text-white font-bold text-base flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: cardColor, height: '80px' }}
        >
          <span className="mr-2 text-xl">{persona.emoji || '💼'}</span>
          <span className="text-center leading-tight line-clamp-2">
            {persona.persona_name || persona.name}
          </span>
        </div>

        {/* Lifestyle Image */}
        <div className="relative h-32 overflow-hidden flex-shrink-0">
          <img 
            src={imageUrl} 
            alt={persona.persona_name || persona.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.src = 'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=800&q=80';
            }}
          />
        </div>

        {/* Metrics Section */}
        <div className="p-4 bg-white flex-1 flex flex-col">
          <div className="mb-2">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-gray-900">
                {persona.size.toLocaleString()}
              </span>
              <span className="text-xs text-gray-600">Customers</span>
            </div>
          </div>

          <div className="border-t border-gray-200 pt-2 mb-2">
            <div className="text-xs text-gray-600 mb-1">Avg Balance</div>
            <div className="text-xl font-bold" style={{ color: cardColor }}>
              {formatCompactUsd(persona.avg_balance)}
            </div>
          </div>

          <div className="border-t border-gray-200 pt-2 mb-1">
            <div className="text-xs text-gray-600 mb-1">Digital adoption</div>
            <div className="text-base font-bold text-blue-600">
              {persona.characteristics?.avg_digital_engagement != null
                ? `${(Number(persona.characteristics.avg_digital_engagement) * 100).toFixed(0)}% online`
                : '—'}
            </div>
          </div>

          <div className="border-t border-gray-200 pt-2 mb-1">
            <div className="text-xs text-gray-600 mb-1">Intent Score</div>
            <div className="text-base font-bold text-green-600">
              {((persona.avg_intent_score || 0) * 100).toFixed(1)}%
            </div>
          </div>

          {/* View Micro-Segments Button - PROMINENT */}
          <div className="mt-auto pt-3 border-t-2 border-gray-300">
            <button 
              onClick={(e) => {
                e.stopPropagation();
                console.log('🔘 View Micro-Segments button clicked for persona:', persona.persona_name);
                onToggle();
              }}
              className={`w-full font-bold py-3 px-4 rounded-lg transition-all duration-300 text-sm flex items-center justify-center gap-2 shadow-lg hover:shadow-xl ${
                isExpanded 
                  ? 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white transform hover:scale-105' 
                  : 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white transform hover:scale-105'
              }`}
            >
              <span className="text-sm font-extrabold">{isExpanded ? 'Hide' : 'View'} Micro-Segments</span>
              {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>
        </div>
      </div>

      {/* Segment Insights Toggle */}
      <div className="mt-2">
        <button
          onClick={(e) => { e.stopPropagation(); setShowExplanation(!showExplanation); }}
          className="w-full text-sm font-medium py-2 px-4 rounded-lg border transition-all duration-200"
          style={{
            borderColor: cardColor + '60',
            color: cardColor,
            backgroundColor: showExplanation ? cardColor + '10' : 'white',
          }}
        >
          {showExplanation ? 'Hide' : 'View'} Segment Insights
        </button>
      </div>

      {/* Segment Insights Panel */}
      {showExplanation && (
        <div className="mt-2 rounded-lg border border-gray-200 overflow-hidden bg-white">
          <div className="px-4 py-2.5 border-b border-gray-100 border-l-4" style={{ borderLeftColor: cardColor }}>
            <span className="text-sm font-semibold text-gray-800">{persona.persona_name || persona.name}</span>
          </div>

          <div className="p-4 space-y-4">
            {persona.segment_explanation ? (() => {
              const expl = persona.segment_explanation;
              const behaviors = cleanList(expl.key_behaviors || []).map(cleanText);
              const actions   = cleanList(expl.marketing_recommendations || []).map(cleanText);
              const definition = cleanText(expl.segment_definition || expl.why_in_segment || '');
              const nameReason = expl.name_explanation ? cleanText(expl.name_explanation) : null;

              return (
                <>
                  {nameReason && (
                    <p className="text-sm text-gray-500 italic leading-relaxed">{nameReason}</p>
                  )}

                  {definition && (
                    <div>
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">What defines this segment</p>
                      <p className="text-sm text-gray-700 leading-relaxed">{definition}</p>
                    </div>
                  )}

                  {behaviors.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Distinct behaviors</p>
                      <ul className="space-y-1.5">
                        {behaviors.map((b, i) => (
                          <li key={i} className="flex gap-2 text-sm text-gray-700 leading-snug">
                            <span className="shrink-0 text-gray-400 mt-0.5">•</span>
                            <span>{b}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {actions.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Marketing actions</p>
                      <ol className="space-y-2">
                        {actions.map((action, i) => (
                          <li key={i} className="flex gap-2 text-sm text-gray-700 leading-snug">
                            <span className="shrink-0 font-semibold text-gray-400 w-5">{i + 1}.</span>
                            <span>{action}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </>
              );
            })() : (
              <div className="space-y-2 text-sm text-gray-600">
                <p>{persona.description || 'No description available'}</p>
                {persona.characteristics?.avg_digital_engagement != null && (
                  <p><span className="font-medium">Digital adoption:</span> {(Number(persona.characteristics.avg_digital_engagement) * 100).toFixed(0)}%</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Micro Segment Card Component (matching Academy Sports)
function MicroSegmentCard({ micro }: { micro: MicroSegment }) {
  const [showDetails, setShowDetails] = React.useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-xl transition-all duration-300 p-6 border border-blue-100 transform hover:scale-105">
      <div className="mb-4">
        <h4 className="font-bold text-lg text-gray-900 mb-2">{micro.name}</h4>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Users className="w-4 h-4" />
          <span>{micro.size} customers ({micro.percentage.toFixed(1)}%)</span>
        </div>
        <div className="mt-1">
          <span className={`text-xs font-semibold px-2 py-1 rounded ${
            micro.ltv_tier === 'Platinum' ? 'bg-purple-100 text-purple-800' :
            micro.ltv_tier === 'Gold' ? 'bg-yellow-100 text-yellow-800' :
            micro.ltv_tier === 'Silver' ? 'bg-gray-200 text-gray-700' :
            'bg-orange-100 text-orange-700'
          }`}>
            {micro.ltv_tier} Tier
          </span>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Avg Balance</span>
          <span className="font-bold text-blue-700">
            {formatCompactUsd(micro.avg_spend || micro.avg_balance || 0)}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Avg products</span>
          <span className="font-bold text-gray-800">
            {micro.characteristics?.avg_portfolio_depth != null
              ? `${Number(micro.characteristics.avg_portfolio_depth).toFixed(1)}`
              : '—'}
          </span>
        </div>
      </div>

      {(() => {
        const tierColor =
          micro.ltv_tier === 'Platinum' ? '#7C3AED' :
          micro.ltv_tier === 'Gold'     ? '#D97706' :
          micro.ltv_tier === 'Silver'   ? '#64748B' :
          micro.ltv_tier === 'Bronze'   ? '#EA580C' : '#3B82F6';

        return (
          <>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="w-full text-sm font-medium py-2 px-3 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-600 transition-colors"
            >
              {showDetails ? 'Hide' : 'Show'} Insights
            </button>

            {showDetails && (
              <div className="mt-3 rounded-lg border border-gray-200 overflow-hidden bg-white">
                <div className="px-4 py-2.5 border-b border-gray-100 border-l-4" style={{ borderLeftColor: tierColor }}>
                  <span className="text-sm font-semibold text-gray-800">{micro.name}</span>
                  <span className="ml-2 text-xs text-gray-400">{micro.ltv_tier} Tier</span>
                </div>

                <div className="p-4 space-y-4">
                  {micro.segment_explanation ? (() => {
                    const definition = cleanText(micro.segment_explanation.segment_definition || micro.segment_explanation.why_in_segment || '');
                    const behaviors  = cleanList(micro.segment_explanation.key_behaviors || []).map(cleanText);
                    const actions    = cleanList(micro.segment_explanation.marketing_recommendations || []).map(cleanText);
                    const nameReason = micro.segment_explanation.name_explanation ? cleanText(micro.segment_explanation.name_explanation) : null;

                    return (
                      <>
                        {nameReason && (
                          <p className="text-sm text-gray-500 italic leading-relaxed">{nameReason}</p>
                        )}

                        {definition && (
                          <div>
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">What defines this segment</p>
                            <p className="text-sm text-gray-700 leading-relaxed">{definition}</p>
                          </div>
                        )}

                        {behaviors.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Distinct behaviors</p>
                            <ul className="space-y-1.5">
                              {behaviors.map((b, i) => (
                                <li key={i} className="flex gap-2 text-sm text-gray-700 leading-snug">
                                  <span className="shrink-0 text-gray-400 mt-0.5">•</span>
                                  <span>{b}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {actions.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Marketing actions</p>
                            <ol className="space-y-2">
                              {actions.map((action, i) => (
                                <li key={i} className="flex gap-2 text-sm text-gray-700 leading-snug">
                                  <span className="shrink-0 font-semibold text-gray-400 w-5">{i + 1}.</span>
                                  <span>{action}</span>
                                </li>
                              ))}
                            </ol>
                          </div>
                        )}
                      </>
                    );
                  })() : (
                    <p className="text-sm text-gray-500">No insight data available.</p>
                  )}

                  {micro.top_customers && micro.top_customers.length > 0 && (
                    <div className="pt-3 border-t border-gray-100">
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Top customers</p>
                      <div className="space-y-1">
                        {micro.top_customers.slice(0, 3).map((customer, idx) => (
                          <div key={idx} className="text-xs text-gray-600 flex justify-between">
                            <span>{customer.customer_name || customer.customer_id}</span>
                            <span className="font-semibold">{formatCompactUsd(customer.total_balance || customer.total_deposits || 0)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        );
      })()}
    </div>
  );
}

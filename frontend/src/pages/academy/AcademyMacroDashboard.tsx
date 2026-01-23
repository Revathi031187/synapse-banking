import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Users, Target, DollarSign, TrendingUp, ChevronDown, ChevronUp,
  Search, ShoppingCart, Heart, Settings, Star, Gift, Map, Tag, Crown, AlertCircle
} from 'lucide-react';
import CustomerInsightModal from '../../components/CustomerInsightModal';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

interface MacroPersona {
  cluster_id: number;
  persona_name: string;
  size: number;
  total_revenue: number;
  avg_spend: number;
  image_url?: string;
  image_fallback?: string;
  color_theme?: string;
  visual_emoji?: string;
  confidence_avg: number;
  characteristics: any;
  segment_explanation?: {
    loyalty_level: string;
    loyalty_reason: string;
    why_in_segment?: string;  // Legacy field
    segment_definition?: string;  // New formatted field with bullet points
    key_behaviors: string[];
    marketing_recommendations: string[];
  };
}

interface MicroSegment {
  micro_cluster_id: number;
  name: string;
  size: number;
  percentage: number;
  avg_spend: number;
  ltv_tier: string;
  icons?: string[];
  trait_badges?: Array<{icon: string; label: string; color: string}>;
  top_customers?: Array<{customer_id: string; customer_name: string; total_spend: number}>;
  segment_explanation?: {
    loyalty_level: string;
    loyalty_reason: string;
    why_in_segment?: string;  // Legacy field
    segment_definition?: string;  // New formatted field with bullet points
    key_behaviors: string[];
    marketing_recommendations: string[];
    segment_size: number;
    avg_customer_value: number;
  };
}

interface Product {
  product_id: string;
  product_name: string;
  category: string;
  price: number;
  brand: string;
}

export default function AcademyMacroDashboard() {
  const [expandedMacro, setExpandedMacro] = useState<number | null>(null);
  const [microSegments, setMicroSegments] = useState<{[key: number]: MicroSegment[]}>({});
  const [loadingMicro, setLoadingMicro] = useState<number[]>([]);
  const [recommendedProducts, setRecommendedProducts] = useState<Product[]>([]);
  const [outOfStockProducts, setOutOfStockProducts] = useState<Product[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);
  const [showOutOfStock, setShowOutOfStock] = useState<boolean>(false);
  const [selectedCustomerForModal, setSelectedCustomerForModal] = useState<any>(null);

  // Fetch macro personas - ALWAYS fetch from backend (not cached) to ensure Agent A has been run
  const { data: macroData, isLoading: macroLoading, error: macroError } = useQuery({
    queryKey: ['academy-agent-a-results'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/academy/agent_a/results`);
      if (!response.ok) {
        if (response.status === 404) {
          // Agent A hasn't been run yet
          return null;
        }
        throw new Error('Failed to load macro personas');
      }
      return response.json();
    },
    staleTime: 0, // ✨ FIXED: Always fetch fresh (was Infinity)
    gcTime: Infinity, // Keep in cache
    refetchOnMount: true, // ✨ FIXED: Always check backend (was false)
    refetchOnWindowFocus: false,
    retry: false // Don't retry on 404
  });

  const personaList: MacroPersona[] = React.useMemo(() => {
    // Backend returns { success: true, results: { personas: {...} } }
    console.log('📊 Macro Dashboard - Raw data:', macroData);
    const personas = macroData?.results?.personas || macroData?.personas;
    console.log('📊 Macro Dashboard - Extracted personas:', personas);
    if (!personas) {
      console.warn('⚠️ No personas found in response');
      return [];
    }
    const list = Object.values(personas) as MacroPersona[];
    const sorted = list.sort((a, b) => b.total_revenue - a.total_revenue);
    console.log(`✓ Loaded ${list.length} macro personas`);
    return sorted;
  }, [macroData]);

  // Load micro segments for a macro persona
  const loadMicroSegments = async (macroClusterId: number) => {
    if (microSegments[macroClusterId]) return; // Already loaded

    setLoadingMicro(prev => [...prev, macroClusterId]);
    
    try {
      // Create micro segments
      await fetch(`${API_BASE_URL}/api/academy/micro-segments/${macroClusterId}`, {
        method: 'POST'
      });
      
      // Fetch micro segments
      const response = await fetch(`${API_BASE_URL}/api/academy/micro-segments/${macroClusterId}`);
      const data = await response.json();
      
      console.log('🔍 Raw micro segments API response:', data);
      const microSegs = data.result?.micro_segments || [];
      console.log(`✓ Parsed ${microSegs.length} micro segments`);
      console.log('📋 First micro segment:', microSegs[0]);
      
      setMicroSegments(prev => ({
        ...prev,
        [macroClusterId]: microSegs
      }));
    } catch (error) {
      console.error('Error loading micro segments:', error);
      setMicroSegments(prev => ({
        ...prev,
        [macroClusterId]: []
      }));
    } finally {
      setLoadingMicro(prev => prev.filter(id => id !== macroClusterId));
    }
  };

  // Toggle macro expansion (no automatic product loading)
  const toggleMacro = async (macroClusterId: number) => {
    console.log('🔄 toggleMacro called for cluster:', macroClusterId, 'Current expanded:', expandedMacro);
    
    if (expandedMacro === macroClusterId) {
      console.log('📦 Collapsing macro segment:', macroClusterId);
      setExpandedMacro(null);
      setRecommendedProducts([]);
      setOutOfStockProducts([]);
      setSelectedCustomer(null);
      setShowOutOfStock(false);
    } else {
      console.log('📂 Expanding macro segment:', macroClusterId);
      setExpandedMacro(macroClusterId);
      
      // Clear previous recommendations
      setRecommendedProducts([]);
      setOutOfStockProducts([]);
      setSelectedCustomer(null);
      setShowOutOfStock(false);
      
      // Load micro segments if not already loaded
      if (!microSegments[macroClusterId]) {
        console.log('⬇️ Loading micro segments for cluster:', macroClusterId);
        loadMicroSegments(macroClusterId);
      } else {
        console.log('✅ Micro segments already loaded for cluster:', macroClusterId);
      }
    }
  };


  // Select a customer for recommendations
  const selectCustomer = async (customer: any) => {
    console.log(`👤 Selected customer: ${customer.customer_name} (${customer.customer_id})`);
    
    // Get the segment name from the current expanded macro
    const currentPersona = personaList.find(p => p.cluster_id === expandedMacro);
    const segmentName = currentPersona?.persona_name || 'Unknown Segment';
    
    // Open modal with customer details
    setSelectedCustomerForModal({
      ...customer,
      segmentName
    });
    
    // Keep old logic for backward compatibility (can be removed later)
    setSelectedCustomer(customer);
    setShowOutOfStock(false);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/academy/recommendations/${customer.customer_id}/all`);
      
      if (!response.ok) {
        throw new Error(`Failed to load recommendations: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('👤 Customer recommendations:', data);
      
      const result = data.result || data;
      
      // Get in-stock products (main recommendations)
      // Priority: 1) tailored_recommendations 2) segment_recommendations 3) similar_products
      let inStockProducts = result.tailored_recommendations?.slice(0, 6) || [];
      
      // FALLBACK: If no tailored recommendations, use segment-based recommendations
      if (inStockProducts.length === 0 && result.segment_recommendations && result.segment_recommendations.length > 0) {
        console.log('⚠️ No tailored recommendations, using segment-based recommendations');
        inStockProducts = result.segment_recommendations.slice(0, 6);
      }
      
      // FALLBACK: If still no recommendations, try similar_products
      if (inStockProducts.length === 0 && result.similar_products && result.similar_products.length > 0) {
        console.log('⚠️ No segment recommendations, using similar products');
        inStockProducts = result.similar_products.slice(0, 6);
      }
      
      // Get out-of-stock products
      const outOfStock = [
        ...(result.out_of_stock_tailored || []),
        ...(result.out_of_stock_similar || []),
        ...(result.out_of_stock_segment || [])
      ].slice(0, 6);
      
      console.log(`✓ Loaded ${inStockProducts.length} in-stock + ${outOfStock.length} out-of-stock products for ${customer.customer_name}`);
      
      setRecommendedProducts(inStockProducts);
      setOutOfStockProducts(outOfStock);
    } catch (error) {
      console.error('❌ Failed to load recommendations:', error);
      alert(`Failed to load recommendations: ${error.message}\n\nPlease ensure Agent B has been run.`);
    }
  };

  if (macroLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading macro dashboard...</p>
        </div>
      </div>
    );
  }

  // Show clear message if Agent A hasn't been run
  if (!macroData || personaList.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-xl p-8 text-center">
            <div className="mb-4">
              <AlertCircle className="w-16 h-16 text-yellow-600 mx-auto" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-3">⚠️ Agent A Not Run Yet</h1>
            <p className="text-gray-700 mb-6">
              Macro segments are not available because <strong>Agent A clustering hasn't been executed</strong>.
            </p>
            <div className="bg-white rounded-lg p-4 mb-6 text-left">
              <p className="text-sm font-semibold text-gray-900 mb-2">📋 To view macro segments:</p>
              <ol className="text-sm text-gray-700 space-y-1 ml-4">
                <li>1. Go to <strong>Agent A: Customer Segmentation</strong> page</li>
                <li>2. Click <strong>"Run K-Prototypes Clustering"</strong></li>
                <li>3. Wait for clustering to complete (~30-60 seconds)</li>
                <li>4. Return to this page to view macro segments</li>
              </ol>
            </div>
            <a 
              href="/academy/agent-a" 
              className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              <Target className="w-5 h-5" />
              Go to Agent A
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Professional Header - Matching Image Style */}
      <div className="bg-gradient-to-r from-blue-700 via-blue-800 to-blue-900 text-white py-5 shadow-md">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center">
                <span className="text-2xl">🏕️</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Macro Segmentation Dashboard</h1>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
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
            <div className="mt-6 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg shadow-lg p-8 border-l-4 border-indigo-600 animate-fadeIn">
              <div className="mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  Micro Segments: {expandedPersona.persona_name}
                </h3>
                <p className="text-gray-600">Detailed sub-segments within this macro persona</p>
              </div>

              {/* Micro Segment Cards */}
              {loadingMicro.includes(expandedMacro) ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                  <p className="text-gray-600 mt-4">Loading micro segments...</p>
                </div>
              ) : microSegments[expandedMacro]?.length > 0 ? (
                <div className="card-grid-4">
                  {microSegments[expandedMacro].map((micro) => (
                    <MicroSegmentCard
                      key={micro.micro_cluster_id}
                      micro={micro}
                      onSelectCustomer={selectCustomer}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-white rounded-lg">
                  <p className="text-gray-600">No micro segments available</p>
                </div>
              )}

              {/* Product Recommendations */}
              {selectedCustomer && (
                <div className="mt-8">
                  <ProductRecommendationsPanel
                    products={recommendedProducts}
                    outOfStockProducts={outOfStockProducts}
                    selectedCustomer={selectedCustomer}
                    currentPersona={expandedPersona}
                    showOutOfStock={showOutOfStock}
                    setShowOutOfStock={setShowOutOfStock}
                  />
                </div>
              )}
            </div>
          );
        })()}
      </div>

      {/* Customer Insight Modal */}
      {selectedCustomerForModal && (
        <CustomerInsightModal
          customerId={selectedCustomerForModal.customer_id}
          customerName={selectedCustomerForModal.customer_name}
          segmentName={selectedCustomerForModal.segmentName}
          onClose={() => setSelectedCustomerForModal(null)}
        />
      )}
    </div>
  );
}

// Macro Persona Card Component - Professional Design Matching Image
function MacroPersonaCard({ persona, isExpanded, onToggle }: any) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const imageUrl = persona.image_url || 'https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800&q=80';
  const colorTheme = persona.color_theme || '#1e40af';
  
  // Professional color schemes from image
  const getCardColor = () => {
    const colors = [
      '#1e40af', // Blue
      '#b91c1c', // Red
      '#15803d', // Green
      '#a16207', // Tan/Gold
      '#1e3a8a', // Navy
    ];
    return colors[persona.cluster_id % colors.length];
  };

  const cardColor = getCardColor();

  const getLoyaltyBadgeColor = (level: string) => {
    if (level === 'HIGH') return 'badge-success';
    if (level === 'MODERATE') return 'badge-warning';
    return 'badge-ghost';
  };

  return (
    <div className="flex flex-col">
      {/* Professional Card Design with Smooth Hover Expansion - FIXED HEIGHT */}
      <div
        className="bg-white rounded-lg overflow-hidden shadow-md hover:shadow-2xl transition-all duration-500 ease-in-out border-t-4 flex flex-col transform hover:scale-105 hover:-translate-y-2"
        style={{ borderTopColor: cardColor, height: '480px' }}
      >
        {/* Colored Header with Segment Name - FIXED HEIGHT FOR ALIGNMENT */}
        <div 
          className="px-4 py-4 text-white font-bold text-base flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: cardColor, height: '80px' }}
        >
          <span className="mr-2 text-xl">{persona.visual_emoji || '🎯'}</span>
          <span className="text-center leading-tight line-clamp-2">{persona.persona_name}</span>
        </div>

        {/* Lifestyle Image */}
        <div className="relative h-32 overflow-hidden flex-shrink-0">
          <img 
            src={imageUrl} 
            alt={persona.persona_name}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.src = 'https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800&q=80';
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
            <div className="text-xs text-gray-600 mb-1">Avg Revenue Potential:</div>
            <div className="text-xl font-bold" style={{ color: cardColor }}>
              ${Math.round(persona.avg_spend)}
            </div>
          </div>

          {/* View Micro-Segments Button - PROMINENT */}
          <div className="mt-auto pt-4 border-t border-gray-200">
            <button 
              onClick={(e) => {
                e.stopPropagation();
                console.log('🔘 View Micro-Segments button clicked for persona:', persona.persona_name);
                onToggle();
              }}
              className={`w-full font-bold py-3.5 px-4 rounded-lg transition-all duration-300 text-base flex items-center justify-center gap-2 shadow-lg hover:shadow-xl ${
                isExpanded 
                  ? 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white transform hover:scale-105' 
                  : 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white transform hover:scale-105'
              }`}
            >
              <span className="text-base">{isExpanded ? '✕ Hide' : '👁️ View'} Micro-Segments</span>
              {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
          </div>
        </div>
      </div>

      {/* Action Buttons Row - Fixed Height */}
      <div className="mt-2 space-y-2">
        {/* Explanation Button */}
        <button 
          onClick={(e) => {
            e.stopPropagation();
            setShowExplanation(!showExplanation);
          }}
          className="w-full btn btn-sm btn-outline"
          style={{ height: '36px' }}
        >
          {showExplanation ? 'Hide' : 'Show'} Segment Insights
        </button>
      
      {/* Expandable Explanation Below Card */}
      {showExplanation && (
        <div className="mt-2 p-5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border-2 border-indigo-200 shadow-md" style={{ minHeight: '280px' }}>
          {persona.segment_explanation ? (
            <>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center">
                  <Target className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-lg text-gray-900">Segment Insights</h4>
                </div>
              </div>
              
              <div className="space-y-4">
                {/* Segment Definition - Removed repetitive "Why This Segment Name?" section */}
                <div>
                  <h5 className="font-bold text-gray-900 mb-1.5">Key Characteristics</h5>
                  <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                    {(persona.segment_explanation.segment_definition || persona.segment_explanation.why_in_segment || '').split('\n').map((line, idx) => {
                      // Format lines with bullet points and bold text
                      const parts = line.split('**');
                      return (
                        <div key={`macro-${persona.cluster_id}-line-${idx}`} className="mb-1.5">
                          {parts.map((part, i) => 
                            i % 2 === 1 ? <strong key={`macro-${persona.cluster_id}-${idx}-bold-${i}`}>{part}</strong> : <span key={`macro-${persona.cluster_id}-${idx}-span-${i}`}>{part}</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
                
                {/* Key Behaviors */}
                {persona.segment_explanation.key_behaviors && persona.segment_explanation.key_behaviors.length > 0 && (
                  <div>
                    <h5 className="font-bold text-gray-900 mb-2">Key Behaviors</h5>
                    <ul className="space-y-1.5">
                      {persona.segment_explanation.key_behaviors.map((behavior: string, idx: number) => (
                        <li key={idx} className="flex items-start text-sm text-gray-700">
                          <span className="mr-2 mt-0.5">•</span>
                          <span className="flex-1">{behavior}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Marketing Recommendations */}
                {persona.segment_explanation.marketing_recommendations && persona.segment_explanation.marketing_recommendations.length > 0 && (
                  <div>
                    <h5 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                      <span>💡</span>
                      <span>Marketing Opportunities</span>
                    </h5>
                    <ul className="space-y-1.5">
                      {persona.segment_explanation.marketing_recommendations.map((rec: string, idx: number) => (
                        <li key={idx} className="flex items-start text-sm text-gray-700">
                          <span className="mr-2 mt-0.5">→</span>
                          <span className="flex-1">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-6">
              <div className="text-gray-400 mb-2">
                <AlertCircle className="w-12 h-12 mx-auto" />
              </div>
              <p className="text-gray-600 font-medium">Segment insights not available</p>
              <p className="text-gray-500 text-sm mt-1">Run Agent A clustering to generate insights</p>
            </div>
          )}
        </div>
      )}

      {/* Key Differences Button */}
      <button 
        onClick={(e) => {
          e.stopPropagation();
          setShowMetrics(!showMetrics);
        }}
        className="w-full btn btn-sm btn-ghost"
        style={{ height: '36px' }}
      >
        {showMetrics ? 'Hide' : 'Show'} Key Differences
      </button>
    </div>
      
      {/* Expandable Key Differences Below Card */}
      {showMetrics && (
        <div className="mt-2 p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg border-2 border-amber-300" style={{ minHeight: '280px' }}>
          <h4 className="font-bold mb-2 text-gray-900 flex items-center gap-2">
            <span>⚡</span>
            <span>How This Differs From Other Segments</span>
          </h4>
          <p className="text-xs text-gray-600 mb-3">Distinctive characteristics compared to other segments:</p>
          <div className="space-y-2 text-sm">
            {/* Only show metrics that are significantly different */}
            {persona.characteristics && (
              <>
                {/* High spenders (>$200) */}
                {persona.avg_spend > 200 && (
                  <div className="bg-green-50 p-2 rounded border-l-4 border-green-500">
                    <p className="font-semibold text-green-900">💰 Premium Spending</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike budget segments:</strong> ${persona.avg_spend.toFixed(0)}/customer - willing to invest in quality
                    </p>
                  </div>
                )}
                
                {/* Budget conscious (<$150) */}
                {persona.avg_spend < 150 && (
                  <div className="bg-blue-50 p-2 rounded border-l-4 border-blue-500">
                    <p className="font-semibold text-blue-900">💵 Value-Focused</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike premium segments:</strong> ${persona.avg_spend.toFixed(0)}/customer - price is key factor
                    </p>
                  </div>
                )}
                
                {/* High expertise (>3.5) */}
                {persona.characteristics.avg_search_specificity > 3.5 && (
                  <div className="bg-purple-50 p-2 rounded border-l-4 border-purple-500">
                    <p className="font-semibold text-purple-900">🎯 Expert Knowledge</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike casual shoppers:</strong> {persona.characteristics.avg_search_specificity.toFixed(1)}/5 expertise - knows exactly what they need
                    </p>
                  </div>
                )}
                
                {/* Beginner (<2.5) */}
                {persona.characteristics.avg_search_specificity < 2.5 && (
                  <div className="bg-yellow-50 p-2 rounded border-l-4 border-yellow-500">
                    <p className="font-semibold text-yellow-900">🌱 Needs Guidance</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike experienced buyers:</strong> {persona.characteristics.avg_search_specificity.toFixed(1)}/5 - relies on recommendations
                    </p>
                  </div>
                )}
                
                {/* Bundle buyers (>15%) */}
                {persona.characteristics.avg_bundle_affinity > 0.15 && (
                  <div className="bg-indigo-50 p-2 rounded border-l-4 border-indigo-500">
                    <p className="font-semibold text-indigo-900">📦 Complete Kit Buyers</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike individual item buyers:</strong> {(persona.characteristics.avg_bundle_affinity * 100).toFixed(0)}% prefer ready-made sets
                    </p>
                  </div>
                )}
                
                {/* Frequent shoppers (>8/year) */}
                {persona.characteristics.avg_purchase_frequency > 8 && (
                  <div className="bg-pink-50 p-2 rounded border-l-4 border-pink-500">
                    <p className="font-semibold text-pink-900">🔄 High Engagement</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike occasional buyers:</strong> {persona.characteristics.avg_purchase_frequency.toFixed(1)}x/year - frequent purchases
                    </p>
                  </div>
                )}
              </>
            )}
            
            {/* If no distinctive features, show basic info */}
            {(!persona.characteristics || 
              (persona.avg_spend >= 150 && persona.avg_spend <= 200 && 
               persona.characteristics.avg_search_specificity >= 2.5 && persona.characteristics.avg_search_specificity <= 3.5 &&
               persona.characteristics.avg_bundle_affinity <= 0.15 &&
               persona.characteristics.avg_purchase_frequency <= 8)) && (
              <div className="bg-gray-50 p-2 rounded border-l-4 border-gray-400">
                <p className="font-semibold text-gray-900">📊 Well-Balanced</p>
                <p className="text-xs text-gray-700">
                  <strong>Unlike specialized segments:</strong> Average across metrics - mainstream outdoor shoppers
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Micro Segment Card Component - Professional Design
function MicroSegmentCard({ micro, onSelectCustomer }: any) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const icons = micro.icons || ['🎯'];
  const badges = micro.trait_badges || [];

  const getLoyaltyBadgeColor = (level: string) => {
    if (level === 'HIGH') return 'bg-green-100 text-green-700';
    if (level === 'MODERATE') return 'bg-yellow-100 text-yellow-700';
    return 'bg-gray-100 text-gray-700';
  };

  // Professional color for micro cards
  const cardBorderColor = '#6366f1'; // Indigo

  return (
    <div className="flex flex-col">
      {/* Professional Micro Card - FIXED HEIGHT FOR ALIGNMENT */}
      <div className="bg-white border-2 border-gray-200 rounded-lg overflow-hidden hover:border-indigo-400 hover:shadow-lg transition-all duration-300 flex flex-col" style={{ height: '480px' }}>
        {/* Header WITHOUT Emojis - FIXED HEIGHT */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 px-4 py-3 border-b-2 border-indigo-200 flex-shrink-0" style={{ height: '90px' }}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-indigo-600 bg-white px-2 py-1 rounded">
              ID: {micro.micro_cluster_id}
            </span>
          </div>
          <h4 className="font-bold text-base text-gray-900 leading-tight line-clamp-2">{micro.name}</h4>
        </div>

        {/* Metrics Section */}
        <div className="p-4 flex-1 flex flex-col overflow-y-auto">
          {/* Customer Count */}
          <div className="mb-3">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-gray-900">
                {micro.size.toLocaleString()}
              </span>
              <span className="text-sm text-gray-600">
                ({micro.percentage.toFixed(1)}%)
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">Customers</div>
          </div>

          {/* Average Spend */}
          <div className="mb-3 pb-3 border-b border-gray-200">
            <div className="text-xs text-gray-600 mb-1">Avg Spend:</div>
            <div className="text-xl font-bold text-green-600">
              ${Math.round(micro.avg_spend)}
            </div>
          </div>

          {/* LTV Tier Badge */}
          <div className="mb-3">
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
              micro.ltv_tier === 'Platinum' || micro.ltv_tier === 'Elite' ? 'bg-purple-100 text-purple-700' :
              micro.ltv_tier === 'Gold' || micro.ltv_tier === 'Premium' ? 'bg-yellow-100 text-yellow-700' :
              micro.ltv_tier === 'Silver' || micro.ltv_tier === 'Standard' ? 'bg-gray-100 text-gray-700' :
              'bg-orange-100 text-orange-700'
            }`}>
              {micro.ltv_tier} Tier
            </span>
          </div>

          {/* Trait Badges */}
          {badges.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {badges.slice(0, 2).map((badge, idx) => (
                <span 
                  key={idx}
                  className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200"
                >
                  {badge.icon} {badge.label}
                </span>
              ))}
            </div>
          )}

          {/* Top Customer - Push to bottom */}
          {micro.top_customers && micro.top_customers.length > 0 && (
            <div className="mt-auto pt-3 border-t border-gray-200">
              <p className="text-xs text-gray-500 uppercase font-semibold mb-2">Example Customer:</p>
              <button
                onClick={() => onSelectCustomer(micro.top_customers[0])}
                className="w-full text-left text-xs bg-gray-50 rounded-lg p-2 hover:bg-indigo-50 transition-colors border border-gray-200 hover:border-indigo-300"
              >
                <div className="font-bold text-gray-900 mb-1 text-xs line-clamp-1">{micro.top_customers[0].customer_name}</div>
                <div className="text-gray-600 text-xs">Spend: <span className="font-semibold">${micro.top_customers[0].total_spend.toFixed(0)}</span></div>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons Row - Fixed Height */}
      <div className="mt-2 space-y-2">
        {/* Explanation Button */}
        <button 
          onClick={() => setShowExplanation(!showExplanation)}
          className="w-full btn btn-sm btn-outline"
          style={{ height: '36px' }}
        >
          {showExplanation ? 'Hide' : 'Show'} Insights
        </button>

        {/* Key Differences Button */}
        <button 
          onClick={() => setShowMetrics(!showMetrics)}
          className="w-full btn btn-sm btn-ghost"
          style={{ height: '36px' }}
        >
          {showMetrics ? 'Hide' : 'Show'} Key Differences
        </button>
      </div>
      
      {/* Expandable Insights Below Card */}
      {showExplanation && (
        <div className="mt-2 p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border-2 border-purple-200 shadow-md" style={{ minHeight: '280px' }}>
          {micro.segment_explanation ? (
            <>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                  <Users className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <h5 className="font-bold text-sm text-gray-900">Micro Segment Insights</h5>
                </div>
              </div>
              
              <div className="space-y-3">
                {/* Removed repetitive "Why This Segment Name?" section */}
                {/* Key Characteristics */}
                <div>
                  <h6 className="font-bold text-gray-900 mb-1">Key Characteristics</h6>
                  <div className="text-xs text-gray-700 leading-relaxed whitespace-pre-line">
                    {(micro.segment_explanation.segment_definition || micro.segment_explanation.why_in_segment || '').split('\n').map((line, idx) => {
                      // Format lines with bullet points and bold text
                      const parts = line.split('**');
                      return (
                        <div key={`micro-${micro.micro_cluster_id}-line-${idx}`} className="mb-1">
                          {parts.map((part, i) => 
                            i % 2 === 1 ? <strong key={`micro-${micro.micro_cluster_id}-${idx}-bold-${i}`}>{part}</strong> : <span key={`micro-${micro.micro_cluster_id}-${idx}-span-${i}`}>{part}</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
                
                {/* Key Behaviors */}
                {micro.segment_explanation.key_behaviors && micro.segment_explanation.key_behaviors.length > 0 && (
                  <div>
                    <h6 className="font-bold text-gray-900 mb-1.5">Behaviors</h6>
                    <ul className="space-y-1">
                      {micro.segment_explanation.key_behaviors.map((behavior: string, idx: number) => (
                        <li key={idx} className="flex items-start text-xs text-gray-700">
                          <span className="mr-1.5 mt-0.5">•</span>
                          <span className="flex-1">{behavior}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Marketing Recommendations */}
                {micro.segment_explanation.marketing_recommendations && micro.segment_explanation.marketing_recommendations.length > 0 && (
                  <div>
                    <h6 className="font-bold text-gray-900 mb-1.5 flex items-center gap-1.5">
                      <span>💡</span>
                      <span>Marketing</span>
                    </h6>
                    <ul className="space-y-1">
                      {micro.segment_explanation.marketing_recommendations.slice(0, 2).map((rec: string, idx: number) => (
                        <li key={idx} className="flex items-start text-xs text-gray-700">
                          <span className="mr-1.5 mt-0.5">→</span>
                          <span className="flex-1">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-4">
              <p className="text-gray-600 text-xs font-medium">Insights not available</p>
              <p className="text-gray-500 text-xs mt-1">Run Agent A to generate</p>
            </div>
          )}
        </div>
      )}
      
      {/* Expandable Key Differences Below Card */}
      {showMetrics && (
        <div className="mt-2 p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg border-2 border-amber-300" style={{ minHeight: '280px' }}>
          <h5 className="font-bold mb-2 text-gray-900 flex items-center gap-1">
            <span>⚡</span>
            <span>How It Differs From Others</span>
          </h5>
          <div className="space-y-1.5">
            {/* Show only distinctive features WITH COMPARATIVE LANGUAGE */}
            {micro.characteristics && (
              <>
                {/* Premium tier */}
                {(micro.ltv_tier === 'Platinum' || micro.ltv_tier === 'Elite') && micro.avg_spend > 250 && (
                  <div className="bg-yellow-50 p-2 rounded border-l-4 border-yellow-500">
                    <p className="font-semibold text-yellow-900">👑 Top Spenders</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike lower tiers:</strong> ${Math.round(micro.avg_spend)}/customer - willing to pay premium for quality
                    </p>
                  </div>
                )}
                
                {/* Budget tier */}
                {micro.avg_spend < 150 && (
                  <div className="bg-green-50 p-2 rounded border-l-4 border-green-500">
                    <p className="font-semibold text-green-900">💰 Value Focused</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike premium segments:</strong> ${Math.round(micro.avg_spend)}/customer - price-conscious shoppers
                    </p>
                  </div>
                )}
                
                {/* High brand loyalty (>50%) */}
                {micro.characteristics.avg_brand_loyalty > 0.5 && (
                  <div className="bg-blue-50 p-2 rounded border-l-4 border-blue-500">
                    <p className="font-semibold text-blue-900">❤️ Brand Devotees</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike brand-switchers:</strong> {(micro.characteristics.avg_brand_loyalty * 100).toFixed(0)}% repeat same brands
                    </p>
                  </div>
                )}
                
                {/* Low brand loyalty */}
                {micro.characteristics.avg_brand_loyalty < 0.3 && (
                  <div className="bg-orange-50 p-2 rounded border-l-4 border-orange-500">
                    <p className="font-semibold text-orange-900">🔄 Brand Switchers</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike brand-loyal segments:</strong> Tries different brands - not tied to one
                    </p>
                  </div>
                )}
                
                {/* High expertise */}
                {micro.characteristics.avg_expertise > 0.7 && (
                  <div className="bg-purple-50 p-2 rounded border-l-4 border-purple-500">
                    <p className="font-semibold text-purple-900">🎯 Expert Knowledge</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike beginners:</strong> {(micro.characteristics.avg_expertise * 5).toFixed(1)}/5 - knows exactly what they need
                    </p>
                  </div>
                )}
                
                {/* Low expertise */}
                {micro.characteristics.avg_expertise < 0.4 && (
                  <div className="bg-yellow-50 p-2 rounded border-l-4 border-yellow-400">
                    <p className="font-semibold text-yellow-900">🌱 Learning Phase</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike experts:</strong> Needs guidance and simplified choices
                    </p>
                  </div>
                )}
                
                {/* Category specialist */}
                {micro.characteristics.dominant_category && micro.characteristics.dominant_category !== 'General' && (
                  <div className="bg-indigo-50 p-2 rounded border-l-4 border-indigo-500">
                    <p className="font-semibold text-indigo-900">🏷️ Specialized Focus</p>
                    <p className="text-xs text-gray-700 truncate">
                      <strong>Unlike generalists:</strong> {micro.characteristics.dominant_category} focused
                    </p>
                  </div>
                )}
                
                {/* Frequent buyers */}
                {micro.characteristics.avg_purchase_frequency > 10 && (
                  <div className="bg-pink-50 p-2 rounded border-l-4 border-pink-500">
                    <p className="font-semibold text-pink-900">🔄 Active Shoppers</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike occasional buyers:</strong> {micro.characteristics.avg_purchase_frequency.toFixed(1)}x/year - high engagement
                    </p>
                  </div>
                )}
                
                {/* Infrequent buyers */}
                {micro.characteristics.avg_purchase_frequency < 5 && (
                  <div className="bg-gray-100 p-2 rounded border-l-4 border-gray-400">
                    <p className="font-semibold text-gray-900">📅 Selective Buyers</p>
                    <p className="text-xs text-gray-700">
                      <strong>Unlike frequent shoppers:</strong> {micro.characteristics.avg_purchase_frequency.toFixed(1)}x/year - careful planners
                    </p>
                  </div>
                )}
              </>
            )}
            
            {/* Basic segment info */}
            <div className="bg-white p-2 rounded mt-2 border border-gray-200">
              <p className="text-xs text-gray-700">
                <span className="font-semibold">{micro.size.toLocaleString()}</span> customers 
                ({micro.percentage.toFixed(1)}% of parent segment)
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Product Recommendations Panel Component
function ProductRecommendationsPanel({ products, outOfStockProducts, selectedCustomer, currentPersona, showOutOfStock, setShowOutOfStock }: any) {
  // Determine the context message
  const getContextMessage = () => {
    if (selectedCustomer && products.length > 0) {
      return {
        title: '👤 Tailored For You',
        subtitle: `Personalized for ${selectedCustomer.customer_name}`,
        badge: 'Personal'
      };
    }
    return null;
  };

  const context = getContextMessage();

  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900">🏕️ Academy Sports</h3>
          <p className="text-sm text-gray-600">Product Recommendations</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="btn btn-ghost btn-sm"><ShoppingCart size={18} /></button>
          <button className="btn btn-ghost btn-sm"><Users size={18} /></button>
        </div>
      </div>

      {/* Context Badge with Customer Details */}
      {context && selectedCustomer && (
        <div className="mb-6 p-5 bg-white rounded-lg border-2 border-purple-200 shadow-sm">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="font-bold text-gray-900">{context.title}</p>
                <p className="text-sm text-gray-600">{context.subtitle}</p>
              </div>
            </div>
            <span className="badge badge-primary text-xs">{context.badge}</span>
          </div>

          {/* Customer Details Grid */}
          <div className="grid grid-cols-3 gap-4 p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
            <div>
              <p className="text-xs text-gray-600 mb-1">Customer Value</p>
              <p className="font-bold text-gray-900">${Math.round(selectedCustomer.total_spend)}</p>
              <p className="text-xs text-gray-500">Annual Spend</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Purchase Frequency</p>
              <p className="font-bold text-gray-900">{selectedCustomer.purchase_frequency}x</p>
              <p className="text-xs text-gray-500">per year</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Preferred Category</p>
              <p className="font-bold text-gray-900 text-sm truncate">{selectedCustomer.dominant_category || 'N/A'}</p>
            </div>
          </div>

          {/* Recommendation Explanation */}
          <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-xs font-semibold text-blue-800 mb-1.5">💡 Personalized Recommendations</p>
            <p className="text-xs text-gray-700 leading-relaxed">
              Each product below is carefully selected for <span className="font-semibold">{selectedCustomer.customer_name || 'this customer'}</span> based on their <span className="font-semibold">${Math.round(selectedCustomer.total_spend)}</span>/year spending tier and <span className="font-semibold">{selectedCustomer.dominant_category || 'camping'}</span> preferences. See individual product explanations below.
            </p>
          </div>
        </div>
      )}

      {/* Product Grid */}
      {products.length > 0 ? (
        <>
          <h4 className="font-semibold text-gray-900 mb-4">
            {selectedCustomer ? 'Top Picks' : 'Recommended Products'}
          </h4>
          <div className="grid grid-cols-3 gap-4">
            {products.slice(0, 3).map((product: any, idx) => (
              <ProductCard key={idx} product={product} inStock={true} />
            ))}
          </div>

          {products.length > 3 && (
            <>
              <h4 className="font-semibold text-gray-900 mt-6 mb-4">You Might Also Like</h4>
              <div className="grid grid-cols-3 gap-4">
                {products.slice(3, 6).map((product: any, idx) => (
                  <ProductCard key={idx} product={product} inStock={true} />
                ))}
              </div>
            </>
          )}

          {/* Out of Stock Toggle Button */}
          {outOfStockProducts && outOfStockProducts.length > 0 && (
            <div className="mt-8 pt-6 border-t-2 border-gray-200">
              <button
                onClick={() => setShowOutOfStock(!showOutOfStock)}
                className="w-full bg-gradient-to-r from-gray-100 to-gray-50 hover:from-gray-200 hover:to-gray-100 rounded-lg p-4 transition-all duration-300 border-2 border-gray-200 hover:border-gray-300"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="bg-orange-100 rounded-lg p-2">
                      <ShoppingCart className="w-5 h-5 text-orange-600" />
                    </div>
                    <div className="text-left">
                      <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                        View Out of Stock Products
                        <span className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-1 rounded-full">
                          {outOfStockProducts.length}
                        </span>
                      </h4>
                      <p className="text-xs text-gray-600 mt-1">
                        Items matching your preferences but temporarily unavailable
                      </p>
                    </div>
                  </div>
                  <div className={`transform transition-transform duration-300 ${showOutOfStock ? 'rotate-180' : ''}`}>
                    <ChevronDown className="w-6 h-6 text-gray-600" />
                  </div>
                </div>
              </button>

              {/* Expandable Out of Stock Section */}
              {showOutOfStock && (
                <div className="mt-6 animate-fade-in">
                  <div className="flex items-center gap-2 mb-4">
                    <h4 className="font-semibold text-gray-700">Currently Unavailable</h4>
                    <span className="badge badge-ghost text-xs">Out of Stock</span>
                  </div>
                  <p className="text-xs text-gray-500 mb-4">
                    These items match your preferences but are temporarily unavailable
                  </p>
                  <div className="grid grid-cols-3 gap-4">
                    {outOfStockProducts.slice(0, 6).map((product: any, idx) => (
                      <ProductCard key={idx} product={product} inStock={false} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
          <ShoppingCart size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-700 font-medium mb-2">No customer selected</p>
          <p className="text-gray-500 text-sm">Select an example customer from a micro segment to see personalized recommendations</p>
        </div>
      )}
    </div>
  );
}

// Product Card Component
function ProductCard({ product, inStock = true }: any) {
  return (
    <div className={`bg-white rounded-lg p-3 hover:shadow-lg transition-shadow relative ${!inStock ? 'opacity-75' : ''}`}>
      {/* Out of Stock Overlay */}
      {!inStock && (
        <div className="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded">
          Out of Stock
        </div>
      )}
      
      <div className={`h-32 rounded mb-2 flex items-center justify-center ${!inStock ? 'bg-gray-200' : 'bg-gray-100'}`}>
        <span className={`text-4xl ${!inStock ? 'grayscale opacity-50' : ''}`}>🎒</span>
      </div>
      
      <h5 className={`font-semibold text-xs mb-1 line-clamp-2 ${!inStock ? 'text-gray-500' : 'text-gray-900'}`}>
        {product.product_name || product.name}
      </h5>
      
      <p className="text-xs text-gray-600 mb-1">{product.brand}</p>
      
      <div className="flex items-center justify-between mb-2">
        <p className={`font-bold text-sm ${!inStock ? 'text-gray-400 line-through' : 'text-gray-900'}`}>
          ${product.price?.toFixed(2) || '0.00'}
        </p>
        {product.rating && (
          <div className="flex items-center gap-1">
            <span className="text-yellow-500 text-xs">⭐</span>
            <span className="text-xs text-gray-600">{product.rating}</span>
          </div>
        )}
        {!inStock && (
          <span className="text-xs text-red-600 font-medium">Unavailable</span>
        )}
      </div>
      
      {/* PERSONALIZED EXPLANATION - WHY THIS PRODUCT SUITS THIS CUSTOMER */}
      {product.reason && (
        <div className="mt-2 pt-2 border-t border-gray-200">
          <p className="text-xs font-semibold text-blue-700 mb-1">💡 Why This Product?</p>
          <p className="text-xs text-gray-700 leading-relaxed line-clamp-3">
            {product.reason}
          </p>
        </div>
      )}
    </div>
  );
}


import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Home, Database, Users, Target, ArrowLeftRight, Sparkles, BarChart3, Layers, MessageSquare } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

interface UnifiedLayoutProps {
  industry: 'banking' | 'retail' | 'academy';
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

export default function UnifiedLayout({ industry }: UnifiedLayoutProps) {
  const navigate = useNavigate();
  
  // Check if Agent A has been run (for Academy industry)
  const { data: agentAResults } = useQuery({
    queryKey: ['academy-agent-a-results'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/academy/personas`);
      if (!response.ok) return null;
      return response.json();
    },
    enabled: industry === 'academy',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false
  });
  
  const hasAgentAResults = agentAResults?.personas && agentAResults.personas.length > 0;
  
  const industryConfig = {
    banking: {
      name: 'F&M Bank',
      subtitle: 'Farmers & Merchants Bank of Central California',
      tagline: 'Where Banking Is Easy - Since 1916',
      icon: '🏦',
      color: 'blue',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-900',
      hoverBg: 'hover:bg-blue-100',
      activeBg: 'bg-blue-600',
      activeText: 'text-white'
    },
    retail: {
      name: 'Retail & E-commerce',
      icon: '🛒',
      color: 'pink',
      bgColor: 'bg-pink-50',
      borderColor: 'border-pink-200',
      textColor: 'text-pink-900',
      hoverBg: 'hover:bg-pink-100',
      activeBg: 'bg-pink-600',
      activeText: 'text-white'
    },
    academy: {
      name: 'Academy Sports - Camping Gear',
      icon: '🏕️',
      color: 'green',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-900',
      hoverBg: 'hover:bg-green-100',
      activeBg: 'bg-green-600',
      activeText: 'text-white'
    }
  };
  
  const config = industryConfig[industry];
  
  const navLinks = industry === 'banking' ? [
    { path: `/${industry}`, label: 'Dashboard', icon: Home },
    { path: `/${industry}/data-loader`, label: 'Data Loader', icon: Database },
    { path: `/${industry}/agent-a`, label: 'Agent A: Personas', icon: Users },
    { path: `/${industry}/macro-dashboard`, label: 'Segments View', icon: BarChart3 },
    { path: `/${industry}/agent-b`, label: 'Agent B: Products', icon: Target },
    { path: `/${industry}/agent-c`, label: 'Agent C: One Best Offer', icon: Sparkles },
    { path: `/${industry}/agent-d`, label: 'Agent D: Supervisor', icon: Layers },
    { path: `/${industry}/ask-genie`, label: 'Ask Genie', icon: MessageSquare }
  ] : industry === 'academy' ? [
    { path: `/${industry}`, label: 'Dashboard', icon: Home },
    { path: `/${industry}/macro-dashboard`, label: 'Visual Dashboard', icon: BarChart3 },
    { path: `/${industry}/agent-a`, label: 'Agent A: Personas', icon: Users },
    { path: `/${industry}/agent-b`, label: 'Agent B: Products', icon: Target }
  ] : [
    { path: `/${industry}`, label: 'Dashboard', icon: Home },
    { path: `/${industry}/agent-a`, label: 'Agent A: Personas', icon: Users },
    { path: `/${industry}/agent-b`, label: 'Agent B: Products', icon: Target }
  ];
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo & Industry */}
            <div className="flex items-center space-x-6">
              <button
                onClick={() => navigate('/')}
                className="flex items-center space-x-3 hover:opacity-80 transition-opacity group"
              >
                <div className="text-3xl">{config.icon}</div>
                <div>
                  <div className="text-gray-900 font-bold text-2xl">
                    {industry === 'academy' ? 'Academy Sports' : config.name}
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Navigation */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-[73px] z-40">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex space-x-2">
            {navLinks.map((link: any) => (
              <NavLink
                key={link.path}
                to={link.path}
                end={link.path === `/${industry}`}
                className={({ isActive }) =>
                  link.highlight 
                    ? `px-6 py-4 flex items-center space-x-3 transition-all font-semibold text-sm border-b-2 ${
                        isActive
                          ? 'bg-gradient-to-r from-green-600 to-blue-600 text-white border-green-600'
                          : 'border-transparent bg-gradient-to-r from-green-50 to-blue-50 text-green-700 hover:from-green-100 hover:to-blue-100'
                      }`
                    : `px-6 py-4 flex items-center space-x-3 transition-all font-medium text-sm border-b-2 ${
                        isActive
                          ? `${config.activeBg} ${config.activeText} border-${config.color}-600`
                          : `border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50`
                      }`
                }
              >
                {({ isActive }) => (
                  <>
                    <link.icon className={`w-5 h-5 ${link.highlight ? (isActive ? 'text-white' : 'text-green-600') : (isActive ? 'text-white' : 'text-gray-500')}`} />
                    <span>{link.label}</span>
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
      
      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <Outlet />
      </div>
      
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="text-gray-600 text-sm">
              © 2024 NBA Personalization Platform. All rights reserved.
            </div>
            <div className="flex items-center space-x-6 text-sm text-gray-600">
              <a href="#" className="hover:text-blue-600 transition-colors">Documentation</a>
              <a href="#" className="hover:text-blue-600 transition-colors">Support</a>
              <a href="#" className="hover:text-blue-600 transition-colors">API</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Home, Database, Users, Target, BarChart3, Search, Crosshair, Star, Activity, Sparkles, Globe, TrendingUp, LayoutDashboard, Plug } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import latentviewLogo from '../assets/latentview-logo.svg';
import { useQuery } from '@tanstack/react-query';

interface UnifiedLayoutProps {
  industry: 'banking' | 'retail' | 'academy';
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

export default function UnifiedLayout({ industry }: UnifiedLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const isDashboard = location.pathname === `/${industry}/dashboard`;
  
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
      name: 'SYNAPSE',
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
    { path: `/${industry}/dashboard`, label: 'Dashboard', icon: LayoutDashboard },
    { path: `/${industry}/segment-ai`, label: 'Segment AI', icon: Sparkles, highlight: true },
    { path: `/${industry}/data-loader`, label: 'Data Loader', icon: Database },
    { path: `/${industry}/macro-dashboard`, label: 'Segments', icon: Search },
    { path: `/${industry}/recommender`, label: 'Recommender', icon: Crosshair },
    { path: `/${industry}/offer-ad-spend`, label: 'Offer & Ad Spend', icon: Star },
    { path: `/${industry}/director`, label: 'Director', icon: Activity },
    { path: `/${industry}/activation`, label: 'Activation', icon: Plug },
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
    <div className={isDashboard ? 'h-screen overflow-hidden bg-gray-50 flex flex-col' : 'min-h-screen bg-gray-50'}>
      {/* Top Bar */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo & Industry */}
            <div className="flex items-center space-x-6">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-3 hover:opacity-80 transition-opacity"
              >
                <img src={latentviewLogo} alt="LatentView" className="h-16 w-auto" />
                <div className="w-px h-6 bg-gray-200" />
                <div
                  className={industry === 'banking' ? 'text-gray-900' : 'text-xl font-black tracking-widest uppercase text-gray-900'}
                  style={industry === 'banking' ? { fontFamily: "'Bebas Neue', sans-serif", fontSize: '2rem', letterSpacing: '0.08em' } : undefined}
                >
                  {industry === 'academy' ? 'Academy Sports' : config.name}
                </div>
              </button>
            </div>

            {/* Right-side actions */}
            {industry === 'banking' && (
              <button
                onClick={() => navigate('/landing')}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-blue-700 text-blue-700 hover:bg-blue-700 hover:text-white font-semibold text-sm transition-all"
              >
                <Globe className="w-4 h-4" />
                Landing Page
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Navigation */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-[73px] z-40">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex justify-center gap-1">
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
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className={isDashboard ? 'flex-1 overflow-hidden flex flex-col' : 'max-w-7xl mx-auto px-6 py-8'}
        >
          <Outlet />
        </motion.div>
      </AnimatePresence>

      {/* Footer — hidden on dashboard (no-scroll layout) */}
      {!isDashboard && <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="text-gray-600 text-sm">
              © 2026 NBA Personalization Platform. All rights reserved.
            </div>
            <div className="flex items-center space-x-6 text-sm text-gray-600">
              <a href="#" className="hover:text-blue-600 transition-colors">Documentation</a>
              <a href="#" className="hover:text-blue-600 transition-colors">Support</a>
              <a href="#" className="hover:text-blue-600 transition-colors">API</a>
            </div>
          </div>
        </div>
      </footer>}
    </div>
  );
}

import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useStore } from '../store/useStore';

const navItems = [
  { path: '/', icon: '📊', label: 'Overview' },
  { path: '/nba-generator', icon: '🎯', label: 'NBA Generator' },
  { path: '/analytics', icon: '📈', label: 'Analytics' },
  { path: '/data-viewer', icon: '💾', label: 'Data Viewer' },
];

const Sidebar = () => {
  const { systemStatus } = useStore();
  
  // Show initializing state
  const isInitializing = systemStatus.initializing || false;
  const isInitialized = systemStatus.system_initialized || false;

  return (
    <motion.aside
      className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 bg-gradient-to-b from-indigo-900 via-purple-900 to-gray-900 shadow-2xl z-40"
      initial={{ x: -264 }}
      animate={{ x: 0 }}
      exit={{ x: -264 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
    >
      <div className="p-6">
        <h2 className="text-lg font-bold text-white mb-6 border-b border-purple-500 pb-3">
          🎯 MENU
        </h2>
        
        <nav className="space-y-2">
          {navItems.map((item, index) => (
            <motion.div
              key={item.path}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <NavLink
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg scale-105'
                      : 'text-gray-300 hover:bg-white/10 hover:text-white hover:scale-102'
                  }`
                }
              >
                <span className="text-2xl">{item.icon}</span>
                <span className="font-semibold">{item.label}</span>
              </NavLink>
            </motion.div>
          ))}
        </nav>

        {/* AI Status */}
        <div className="mt-8 p-4 bg-gradient-to-br from-purple-800/30 to-pink-800/30 backdrop-blur-sm rounded-xl border border-purple-500/20">
          <h3 className="text-purple-300 font-bold text-sm mb-3 flex items-center gap-2">
            🤖 AI SYSTEM
          </h3>
          
          {isInitializing ? (
            <div className="text-center py-2">
              <div className="animate-spin inline-block w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full mb-2"></div>
              <p className="text-xs text-purple-300">Initializing...</p>
            </div>
          ) : isInitialized ? (
            <>
              <div className="space-y-2 text-xs mb-3">
                {['🎭 Persona', '🔍 Product', '💰 Offer', '🎯 Performance', '📊 Marketing'].map((agent) => (
                  <div key={agent} className="flex items-center justify-between bg-white/5 rounded px-2 py-1">
                    <span className="text-gray-300">{agent}</span>
                    <span className="flex items-center space-x-1">
                      <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                      <span className="text-green-400 font-medium text-xs">Active</span>
                    </span>
                  </div>
                ))}
              </div>
              <div className="bg-green-500/20 border border-green-500/30 rounded-lg px-3 py-2 text-center">
                <p className="text-green-300 font-bold text-xs">✓ All Systems Online</p>
              </div>
            </>
          ) : (
            <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg px-3 py-2 text-center">
              <p className="text-yellow-300 font-semibold text-xs">⏳ Not Initialized</p>
              <p className="text-yellow-200 text-xs mt-1">Go to Overview</p>
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
};

export default Sidebar;


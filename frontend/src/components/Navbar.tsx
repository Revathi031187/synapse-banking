import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useStore } from '../store/useStore';

const Navbar = () => {
  const { sidebarOpen, setSidebarOpen, systemStatus } = useStore();

  return (
    <motion.nav
      className="bg-white shadow-lg border-b border-gray-200 sticky top-0 z-50"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <svg
                className="w-6 h-6 text-gray-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            
            <Link to="/" className="flex items-center space-x-3">
              <span className="text-3xl">🎯</span>
              <div>
                <h1 className="text-2xl font-black text-gray-900">
                  Agentic AI Personalization
                </h1>
                <p className="text-sm text-gray-600">
                  5 Autonomous AI Agents • Real-time Decisioning
                </p>
              </div>
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            {/* System Status Indicators */}
            <div className="flex items-center space-x-2 bg-gray-50 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-1">
                <div
                  className={`w-2 h-2 rounded-full ${
                    systemStatus.data_generated ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                />
                <span className="text-xs font-medium text-gray-700">Data</span>
              </div>
              
              <div className="w-px h-4 bg-gray-300" />
              
              <div className="flex items-center space-x-1">
                <div
                  className={`w-2 h-2 rounded-full ${
                    systemStatus.system_initialized ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                />
                <span className="text-xs font-medium text-gray-700">Agents</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;


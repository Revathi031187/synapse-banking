import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

interface LayoutV2Props {
  children: ReactNode;
}

const LayoutV2 = ({ children }: LayoutV2Props) => {
  const location = useLocation();
  
  // Poll system status
  const { data: status } = useQuery({
    queryKey: ['v2-status'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8001/api/v2/status');
      return response.json();
    },
    refetchInterval: 5000,
  });

  const navItems = [
    { path: '/', icon: '🏠', label: 'Dashboard' },
    { path: '/data-loader', icon: '📦', label: 'Data Loader' },
    { path: '/agent-a', icon: '🤖', label: 'Agent A: Personas' },
    { path: '/agent-b', icon: '🎯', label: 'Agent B: Products' },
  ];

  const pipelineStatus = status?.pipeline_status || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      {/* Top Bar */}
      <div className="bg-black/40 backdrop-blur-sm border-b border-purple-500/30">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                ✨ Personalization Platform v2
              </div>
              <div className="text-sm text-gray-400">
                Advanced AI Persona Builder
              </div>
            </div>
            
            {/* Status Indicators */}
            <div className="flex items-center space-x-6">
              <StatusBadge
                label="Data"
                active={pipelineStatus.data_loaded}
              />
              <StatusBadge
                label="Agent A"
                active={pipelineStatus.agent_a_complete}
              />
              <StatusBadge
                label="Agent B"
                active={pipelineStatus.agent_b_complete}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 min-h-screen bg-black/30 backdrop-blur-sm border-r border-purple-500/20">
          <nav className="p-4 space-y-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    flex items-center space-x-3 px-4 py-3 rounded-lg
                    transition-all duration-200
                    ${isActive
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                      : 'text-gray-300 hover:bg-white/10'
                    }
                  `}
                >
                  <span className="text-2xl">{item.icon}</span>
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Dataset Info */}
          {status?.current_dataset && (
            <div className="mx-4 mt-8 p-4 bg-white/5 rounded-lg border border-purple-500/20">
              <div className="text-xs text-gray-400 mb-1">Current Dataset</div>
              <div className="text-sm font-medium text-purple-300 capitalize">
                {status.current_dataset.replace('_', ' ')}
              </div>
            </div>
          )}
        </div>

        {/* Page Content */}
        <div className="flex-1 p-8">
          {children}
        </div>
      </div>
    </div>
  );
};

interface StatusBadgeProps {
  label: string;
  active: boolean;
}

const StatusBadge = ({ label, active }: StatusBadgeProps) => {
  return (
    <div className="flex items-center space-x-2">
      <div
        className={`w-2 h-2 rounded-full ${
          active ? 'bg-green-400 animate-pulse' : 'bg-gray-600'
        }`}
      />
      <span className={`text-sm ${active ? 'text-green-400' : 'text-gray-500'}`}>
        {label}
      </span>
    </div>
  );
};

export default LayoutV2;


import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

export default function BankingDashboard() {
  const navigate = useNavigate();
  
  const { data: status } = useQuery({
    queryKey: ['banking-status'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8002/api/banking/status');
      return res.json();
    }
  });
  
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">🏦 Banking Dashboard</h1>
        <p className="text-gray-400">Next Best Action platform for retail banking</p>
      </div>
      
      {/* Status Cards */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
          <div className="text-3xl mb-2">{status?.pipeline_status?.data_loaded ? '✅' : '⏳'}</div>
          <div className="text-white font-bold mb-1">Data Status</div>
          <div className="text-gray-400 text-sm">
            {status?.pipeline_status?.data_loaded ? 'Dataset Loaded' : 'No Data Loaded'}
          </div>
        </div>
        
        <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
          <div className="text-3xl mb-2">{status?.pipeline_status?.agent_a_complete ? '✅' : '⏳'}</div>
          <div className="text-white font-bold mb-1">Agent A</div>
          <div className="text-gray-400 text-sm">Persona Builder</div>
        </div>
        
        <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
          <div className="text-3xl mb-2">{status?.pipeline_status?.agent_b_complete ? '✅' : '⏳'}</div>
          <div className="text-white font-bold mb-1">Agent B</div>
          <div className="text-gray-400 text-sm">Product Matchmaker</div>
        </div>
      </div>
      
      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 backdrop-blur-sm rounded-xl p-8 border border-blue-500/20">
        <h2 className="text-2xl font-bold text-white mb-6">Quick Start</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <button
            onClick={() => navigate('/banking/data-loader')}
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-4 rounded-lg font-medium transition-all text-left"
          >
            <div className="text-2xl mb-2">📁</div>
            <div>1. Load Banking Data</div>
            <div className="text-xs opacity-80 mt-1">Ms. X scenario with 11K+ records</div>
          </button>
          
          <button
            onClick={() => navigate('/banking/agent-a')}
            disabled={!status?.pipeline_status?.data_loaded}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-4 rounded-lg font-medium transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="text-2xl mb-2">👥</div>
            <div>2. Run Agent A</div>
            <div className="text-xs opacity-80 mt-1">Detect life events & intent</div>
          </button>
          
          <button
            onClick={() => navigate('/banking/agent-b')}
            disabled={!status?.pipeline_status?.agent_a_complete}
            className="bg-pink-600 hover:bg-pink-700 text-white px-6 py-4 rounded-lg font-medium transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="text-2xl mb-2">🎯</div>
            <div>3. Run Agent B</div>
            <div className="text-xs opacity-80 mt-1">Match products to personas</div>
          </button>
          
          <div className="bg-white/5 border border-purple-500/20 px-6 py-4 rounded-lg">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-white font-medium">4. View Results</div>
            <div className="text-xs text-gray-400 mt-1">AI-powered insights & recommendations</div>
          </div>
        </div>
      </div>
      
      {/* Ms. X Scenario */}
      <div className="bg-gradient-to-br from-purple-900/20 to-pink-900/20 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
        <h3 className="text-xl font-bold text-white mb-4">🎯 Featured Scenario: Ms. X</h3>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-white font-semibold mb-2">Customer Profile</h4>
            <ul className="text-sm text-gray-300 space-y-1">
              <li>• Sarah Martinez (CUST000001)</li>
              <li>• Age: 32, 4-year customer</li>
              <li>• Checking + Credit Card</li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-2">Detected Signals</h4>
            <ul className="text-sm text-gray-300 space-y-1">
              <li>✅ High engagement (28 logins/14 days)</li>
              <li>✅ Mortgage intent (2 abandonments)</li>
              <li>✅ Relocation (furniture spending)</li>
              <li>✅ New job (30% income increase)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}


import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import UnifiedLayout from './components/UnifiedLayout';
import BankingDataLoader from './pages/banking/BankingDataLoader';
import BankingAgentB from './pages/banking/BankingAgentB';
import BankingMacroDashboard from './pages/banking/BankingMacroDashboard';
import BankingAgentC from './pages/banking/BankingAgentC';
import BankingAgentD from './pages/banking/BankingAgentD';
import BankingAskGenie from './pages/banking/BankingAskGenie';

// Academy Sports pages (Keep for reference)
import AcademyDashboard from './pages/academy/AcademyDashboard';
import AcademyAgentA from './pages/academy/AcademyAgentA';
import AcademyAgentB from './pages/academy/AcademyAgentB';
import AcademyMicroSegments from './pages/academy/AcademyMicroSegments';
import AcademyRecommendations from './pages/academy/AcademyRecommendations';
import AcademySegmentationOverview from './pages/academy/AcademySegmentationOverview';
import AcademyMacroDashboard from './pages/academy/AcademyMacroDashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: Infinity, // NEVER consider data stale - persist forever until explicit invalidation
      gcTime: Infinity, // NEVER garbage collect - keep in cache until browser refresh
      refetchOnMount: false, // Don't automatically refetch when component mounts
    },
  },
});

// Basename: VITE_BASE_PATH for deployment (e.g. /banking-platform/v1), else /nba-platform/v3 in prod
const basename = import.meta.env.VITE_BASE_PATH || (import.meta.env.MODE === 'production' ? '/nba-platform/v3' : '/');

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router basename={basename}>
        <Routes>
          {/* Redirect root to Banking (primary demo) */}
          <Route path="/" element={<Navigate to="/banking" replace />} />
          
          {/* Banking Routes (NEW - Primary Demo) */}
          <Route path="/banking" element={<UnifiedLayout industry="banking" />}>
            <Route index element={<Navigate to="data-loader" replace />} />
            <Route path="data-loader" element={<BankingDataLoader />} />
            <Route path="macro-dashboard" element={<BankingMacroDashboard />} />
            <Route path="agent-a" element={<Navigate to="/banking/data-loader" replace />} />
            <Route path="agent-b" element={<BankingAgentB />} />
            <Route path="agent-c" element={<BankingAgentC />} />
            <Route path="agent-d" element={<BankingAgentD />} />
            <Route path="ask-genie" element={<BankingAskGenie />} />
            <Route path="customer/:customerId/recommendations" element={<AcademyRecommendations />} />
          </Route>
          
          {/* Academy Sports Routes (Keep for reference) */}
          <Route path="/academy" element={<UnifiedLayout industry="academy" />}>
            <Route index element={<AcademyDashboard />} />
            <Route path="segmentation-overview" element={<AcademySegmentationOverview />} />
            <Route path="macro-dashboard" element={<AcademyMacroDashboard />} />
            <Route path="agent-a" element={<AcademyAgentA />} />
            <Route path="agent-b" element={<AcademyAgentB />} />
            <Route path="macro-segment/:macroSegmentId/micro" element={<AcademyMicroSegments />} />
            <Route path="customer/:customerId/recommendations" element={<AcademyRecommendations />} />
          </Route>

          {/* Catch all - redirect to Banking */}
          <Route path="*" element={<Navigate to="/banking" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;

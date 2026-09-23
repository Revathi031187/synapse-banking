import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import UnifiedLayout from './components/UnifiedLayout';
import { getBankingApiBase } from './utils/apiBase';
import BankingDataLoader from './pages/banking/BankingDataLoader';
import BankingAgentB from './pages/banking/BankingAgentB';
import BankingMacroDashboard from './pages/banking/BankingMacroDashboard';
import BankingAgentC from './pages/banking/BankingAgentC';
import BankingAgentD from './pages/banking/BankingAgentD';
import BankingAskGenie from './pages/banking/BankingAskGenie';
import BankingLanding from './pages/banking/BankingLanding';
import BankingSegmentDashboard from './pages/banking/BankingSegmentDashboard';
import BankingActivation from './pages/banking/BankingActivation';

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

// Entry point for /banking (e.g. landing straight into the app)  -  routes to
// the Dashboard only when there's actually a completed segmentation to show;
// otherwise straight to the Data Loader, so a fresh environment never lands
// on a Dashboard tab that has nothing to display. /api/banking/status is a
// cheap in-memory check (no per-persona computation), so this resolves fast.
function BankingIndexRedirect() {
  const { data, isLoading } = useQuery({
    queryKey: ['banking-status'],
    queryFn: async () => {
      const res = await fetch(`${getBankingApiBase()}/api/banking/status`);
      if (!res.ok) throw new Error('Failed to load status');
      return (await res.json()) as { agent_a_complete: boolean };
    },
    staleTime: 60_000,
  });
  if (isLoading) return null;
  return <Navigate to={data?.agent_a_complete ? 'dashboard' : 'data-loader'} replace />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router basename={basename}>
        <Routes>
          {/* Public landing page  -  personalized on return visits */}
          <Route path="/landing" element={<BankingLanding />} />

          {/* Redirect root to landing page */}
          <Route path="/" element={<Navigate to="/landing" replace />} />
          
          {/* Banking Routes (NEW - Primary Demo) */}
          <Route path="/banking" element={<UnifiedLayout industry="banking" />}>
            <Route index element={<BankingIndexRedirect />} />
            <Route path="dashboard" element={<BankingSegmentDashboard />} />
            <Route path="data-loader" element={<BankingDataLoader />} />
            <Route path="activation" element={<BankingActivation />} />
            <Route path="macro-dashboard" element={<BankingMacroDashboard />} />
            <Route path="agent-a" element={<Navigate to="/banking/data-loader" replace />} />
            <Route path="recommender" element={<BankingAgentB />} />
            <Route path="offer-ad-spend" element={<BankingAgentC />} />
            <Route path="director" element={<BankingAgentD />} />
            <Route path="segment-ai" element={<BankingAskGenie />} />
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

          {/* Catch all - redirect to landing */}
          <Route path="*" element={<Navigate to="/landing" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;

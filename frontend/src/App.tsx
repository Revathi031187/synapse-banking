import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import UnifiedLayout from './components/UnifiedLayout';

// Academy Sports pages only
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

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router basename="/nba-platform/v3">
        <Routes>
          {/* Redirect root to Academy Sports */}
          <Route path="/" element={<Navigate to="/academy" replace />} />
          
          {/* Academy Sports Routes */}
          <Route path="/academy" element={<UnifiedLayout industry="academy" />}>
            <Route index element={<AcademyDashboard />} />
            <Route path="segmentation-overview" element={<AcademySegmentationOverview />} />
            <Route path="macro-dashboard" element={<AcademyMacroDashboard />} />
            <Route path="agent-a" element={<AcademyAgentA />} />
            <Route path="agent-b" element={<AcademyAgentB />} />
            <Route path="macro-segment/:macroSegmentId/micro" element={<AcademyMicroSegments />} />
            <Route path="customer/:customerId/recommendations" element={<AcademyRecommendations />} />
          </Route>

          {/* Catch all - redirect to Academy */}
          <Route path="*" element={<Navigate to="/academy" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;

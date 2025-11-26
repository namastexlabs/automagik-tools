import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { ForgeInspector as AutomagikForgeWebCompanion } from 'forge-inspector';
import { ThemeProvider } from './components/ThemeProvider';
import { isAuthenticated } from './lib/api';
import { useEffect } from 'react';
import Login from './pages/Login';
import Setup from './pages/Setup';
import Dashboard from './pages/Dashboard';
import Catalogue from './pages/Catalogue';
import MyTools from './pages/MyTools';
import Projects from './pages/Projects';
import Agents from './pages/Agents';
import Settings from './pages/Settings';
import AuditLogs from './pages/AuditLogs';
import AdminDashboard from './pages/AdminDashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />;
}

// Smart Root Redirect - checks setup status first
function RootRedirect() {
  const navigate = useNavigate();
  const { data: setupStatus, isLoading } = useQuery({
    queryKey: ['setup-status'],
    queryFn: async () => {
      const response = await fetch('/api/setup/status');
      if (!response.ok) throw new Error('Failed to fetch setup status');
      return response.json();
    },
    retry: 1,
  });

  useEffect(() => {
    if (isLoading) return;

    if (setupStatus?.is_setup_required) {
      // Setup not complete - go to setup wizard
      navigate('/setup', { replace: true });
    } else if (isAuthenticated()) {
      // Setup complete and authenticated - go to dashboard
      navigate('/dashboard', { replace: true });
    } else {
      // Setup complete but not authenticated - go to login
      navigate('/login', { replace: true });
    }
  }, [setupStatus, isLoading, navigate]);

  return <div className="min-h-screen flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
      <p className="mt-4 text-gray-600">Loading...</p>
    </div>
  </div>;
}

// Public Route Component (redirect to dashboard if already authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
  return isAuthenticated() ? <Navigate to="/dashboard" replace /> : <>{children}</>;
}

function App() {
  console.log('[App] Rendering App component with ForgeInspector');
  console.log('[App] NODE_ENV:', process.env.NODE_ENV);
  console.log('[App] In iframe:', window.self !== window.top);

  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <Toaster richColors position="top-right" />
        <AutomagikForgeWebCompanion />
        <BrowserRouter>
          <Routes>
            <Route path="/setup" element={<Setup />} />
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/catalogue"
              element={
                <ProtectedRoute>
                  <Catalogue />
                </ProtectedRoute>
              }
            />
            <Route
              path="/my-tools"
              element={
                <ProtectedRoute>
                  <MyTools />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects"
              element={
                <ProtectedRoute>
                  <Projects />
                </ProtectedRoute>
              }
            />
            <Route
              path="/agents"
              element={
                <ProtectedRoute>
                  <Agents />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              }
            />
            <Route
              path="/audit-logs"
              element={
                <ProtectedRoute>
                  <AuditLogs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<RootRedirect />} />
            <Route path="*" element={<RootRedirect />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;

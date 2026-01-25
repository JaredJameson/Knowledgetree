/**
 * KnowledgeTree - Main Application Component
 * Handles routing and authentication flow
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { SearchPage } from './pages/SearchPage';
import { ChatPage } from './pages/ChatPage';
import BillingPage from './pages/BillingPage';
import PricingPage from './pages/PricingPage';
import SettingsPage from './pages/SettingsPage';
import CrawlPage from './pages/CrawlPage';
import InsightsPage from './pages/InsightsPage';
import WorkflowsPage from './pages/WorkflowsPage';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';

// Wrapper component for protected routes with layout
function ProtectedRouteWithLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <Layout>
        {children}
      </Layout>
    </ProtectedRoute>
  );
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected routes with sidebar */}
      <Route path="/dashboard" element={<ProtectedRouteWithLayout><DashboardPage /></ProtectedRouteWithLayout>} />
      <Route path="/projects" element={<ProtectedRouteWithLayout><ProjectsPage /></ProtectedRouteWithLayout>} />
      <Route path="/documents" element={<ProtectedRouteWithLayout><DocumentsPage /></ProtectedRouteWithLayout>} />
      <Route path="/search" element={<ProtectedRouteWithLayout><SearchPage /></ProtectedRouteWithLayout>} />
      <Route path="/chat" element={<ProtectedRouteWithLayout><ChatPage /></ProtectedRouteWithLayout>} />
      <Route path="/billing" element={<ProtectedRouteWithLayout><BillingPage /></ProtectedRouteWithLayout>} />
      <Route path="/pricing" element={<ProtectedRouteWithLayout><PricingPage /></ProtectedRouteWithLayout>} />
      <Route path="/settings" element={<ProtectedRouteWithLayout><SettingsPage /></ProtectedRouteWithLayout>} />
      <Route path="/crawl" element={<ProtectedRouteWithLayout><CrawlPage /></ProtectedRouteWithLayout>} />
      <Route path="/insights" element={<ProtectedRouteWithLayout><InsightsPage /></ProtectedRouteWithLayout>} />
      <Route path="/workflows" element={<ProtectedRouteWithLayout><WorkflowsPage /></ProtectedRouteWithLayout>} />

      {/* Redirect root to dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Catch-all redirect to dashboard */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;

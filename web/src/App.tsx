import { Navigate, Route, Routes, useLocation, Outlet } from "react-router-dom";
import MarketingLayout from "./layouts/MarketingLayout";
import Homepage from "./pages/Homepage";
import Login from "./pages/Login";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";
import AppLayout from "./layouts/AppLayout";
import Dashboard, { TeamView } from "./pages/Dashboard";
import JobsFeed from "./pages/JobsFeed";
import ApplicationsPage from "./pages/Applications";
import HoldInbox from "./pages/HoldInbox";
import BillingPage from "./pages/Billing";
import SettingsPage from "./pages/Settings";
import Onboarding from "./pages/app/Onboarding";
import { useAuth } from "./hooks/useAuth";
import { useProfile } from "./hooks/useProfile";
import { LoadingSpinner } from "./components/ui/LoadingSpinner";
import { ErrorBoundary } from "./components/ui/ErrorBoundary";
import Pricing from "./pages/Pricing";
import SuccessStories from "./pages/SuccessStories";
import ChromeExtension from "./pages/ChromeExtension";
import Recruiters from "./pages/Recruiters";
import JobNiche from "./pages/JobNiche";
import ComparisonPage from "./pages/ComparisonPage";
import GuidesHome from "./pages/GuidesHome";
import GuidePage from "./pages/GuidePage";

function AuthGuard() {
  const location = useLocation();
  const { session, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Checking sign-in..." />
      </div>
    );
  }
  if (!session) {
    return <Navigate to={`/login?returnTo=${encodeURIComponent(location.pathname + location.search)}`} replace />;
  }
  return <Outlet />;
}

function OnboardingGuard({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { profile, loading, needsOnboarding } = useProfile();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Loading..." />
      </div>
    );
  }

  if (needsOnboarding && location.pathname !== "/app/onboarding") {
    return <Navigate to="/app/onboarding" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      {/* Public Marketing Pages */}
      <Route element={<MarketingLayout />}>
        <Route path="/" element={<Homepage />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/success-stories" element={<SuccessStories />} />
        <Route path="/chrome-extension" element={<ChromeExtension />} />
        <Route path="/recruiters" element={<Recruiters />} />
        <Route path="/jobs/:role/:city" element={<JobNiche />} />
        <Route path="/vs/:competitorSlug" element={<ComparisonPage />} />
        <Route path="/guides" element={<GuidesHome />} />
        <Route path="/guides/:guideSlug" element={<GuidePage />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/terms" element={<Terms />} />
      </Route>

      {/* Auth - Standalone */}
      <Route path="/login" element={<Login />} />

      {/* App Protected Routes */}
      <Route path="/app" element={<AuthGuard />}>
        <Route path="onboarding" element={<Onboarding />} />

        <Route element={<OnboardingGuard><AppLayout /></OnboardingGuard>}>
          <Route index element={<Navigate to="/app/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="jobs" element={<JobsFeed />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="holds" element={<HoldInbox />} />
          <Route path="team" element={<TeamView />} />
          <Route path="billing" element={<BillingPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

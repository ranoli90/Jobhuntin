import { Navigate, Route, Routes, useLocation, Outlet } from "react-router-dom";
import MarketingLayout from "./layouts/MarketingLayout";
import Homepage from "./pages/Homepage";
import Login from "./pages/Login";
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
      <Route path="/" element={<Homepage />} />
      <Route element={<MarketingLayout />}>
        <Route path="/login" element={<Login />} />
      </Route>

      <Route path="/app" element={<AuthGuard />}>
        <Route element={<AppLayout />}>
          <Route path="onboarding" element={<Onboarding />} />

          <Route path="*" element={
            <OnboardingGuard>
              <Routes>
                <Route index element={<Navigate to="/app/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="jobs" element={<JobsFeed />} />
                <Route path="applications" element={<ApplicationsPage />} />
                <Route path="holds" element={<HoldInbox />} />
                <Route path="team" element={<TeamView />} />
                <Route path="billing" element={<BillingPage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
              </Routes>
            </OnboardingGuard>
          } />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

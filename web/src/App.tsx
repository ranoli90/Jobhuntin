import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import ScrollToTop from "./components/ScrollToTop";
import MarketingLayout from "./layouts/MarketingLayout";
import Homepage from "./pages/Homepage";
import Pricing from "./pages/Pricing";
import SuccessStories from "./pages/SuccessStories";
import ChromeExtension from "./pages/ChromeExtension";
import Recruiters from "./pages/Recruiters";
import JobNiche from "./pages/JobNiche";
import ComparisonPage from "./pages/ComparisonPage";
import GuidesHome from "./pages/GuidesHome";
import GuidePage from "./pages/GuidePage";
import Login from "./pages/Login";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";
import AuthGuard from "./guards/AuthGuard";
import AppLayout from "./layouts/AppLayout";
import Dashboard, { JobsView, ApplicationsView, HoldsView, TeamView, BillingView } from "./pages/Dashboard";
import Onboarding from "./pages/app/Onboarding";
import Settings from "./pages/Settings";
import { useProfile } from "./hooks/useProfile";
import { LoadingSpinner } from "./components/ui/LoadingSpinner";

function OnboardingGuard({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { loading, needsOnboarding } = useProfile();

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
    <>
      <ScrollToTop />
      <Routes>
        {/* Public Marketing Pages & Auth */}
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
          <Route path="/login" element={<Login />} />
        </Route>

        {/* App Protected Routes */}
        <Route path="/app" element={<AuthGuard />}>
          <Route path="onboarding" element={<Onboarding />} />

          <Route element={<OnboardingGuard><AppLayout /></OnboardingGuard>}>
            <Route index element={<Navigate to="/app/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="jobs" element={<JobsView />} />
            <Route path="applications" element={<ApplicationsView />} />
            <Route path="holds" element={<HoldsView />} />
            <Route path="team" element={<TeamView />} />
            <Route path="billing" element={<BillingView />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

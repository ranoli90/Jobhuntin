import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import React, { Suspense } from 'react';
import ScrollToTop from "./components/ScrollToTop";
import MarketingLayout from "./layouts/MarketingLayout";
import AuthGuard from "./guards/AuthGuard";
import AppLayout from "./layouts/AppLayout";
import { useProfile } from "./hooks/useProfile";
import { LoadingSpinner } from "./components/ui/LoadingSpinner";

// Lazy Load Pages for Performance
const Homepage = React.lazy(() => import("./pages/Homepage"));
const Pricing = React.lazy(() => import("./pages/Pricing"));
const SuccessStories = React.lazy(() => import("./pages/SuccessStories"));
const ChromeExtension = React.lazy(() => import("./pages/ChromeExtension"));
const Recruiters = React.lazy(() => import("./pages/Recruiters"));
const JobNiche = React.lazy(() => import("./pages/JobNiche"));
const ComparisonPage = React.lazy(() => import("./pages/ComparisonPage"));
const GuidesHome = React.lazy(() => import("./pages/GuidesHome"));
const GuidePage = React.lazy(() => import("./pages/GuidePage"));
const Login = React.lazy(() => import("./pages/Login"));
const Privacy = React.lazy(() => import("./pages/Privacy"));
const Terms = React.lazy(() => import("./pages/Terms"));
const Dashboard = React.lazy(() => import("./pages/Dashboard"));
const Onboarding = React.lazy(() => import("./pages/app/Onboarding"));
const Settings = React.lazy(() => import("./pages/Settings"));
const NotFound = React.lazy(() => import("./pages/NotFound"));

// Import Dashboard sub-components directly if they are exported from the same file, 
// or lazy load them if they are heavy. For now, assuming they are light enough or part of Dashboard bundle.
// If they are exported from Dashboard.tsx, we can't easily lazy load them individually without changing Dashboard.tsx 
// to export them as default from separate files. 
// However, since we are lazy loading Dashboard, these imports will happen when Dashboard chunk loads.
// We need to import them from the module.
import { JobsView, ApplicationsView, HoldsView, TeamView, BillingView } from "./pages/Dashboard";

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

// Loading Fallback
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-slate-50">
    <LoadingSpinner label="Loading..." />
  </div>
);

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Suspense fallback={<PageLoader />}>
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
            <Route path="*" element={<NotFound />} />
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
        </Routes>
      </Suspense>
    </>
  );
}

import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import React, { Suspense } from 'react';
import { Helmet } from "react-helmet-async";
import ScrollToTop from "./components/ScrollToTop";
import MarketingLayout from "./layouts/MarketingLayout";
import AuthGuard from "./guards/AuthGuard";
import AppLayout from "./layouts/AppLayout";
import { useProfile } from "./hooks/useProfile";
import { LoadingSpinner } from "./components/ui/LoadingSpinner";
import { config } from "./config";
import { useGoogleAnalytics } from "./hooks/useGoogleAnalytics";

// Lazy Load Pages for Performance
const Homepage = React.lazy(() => import("./pages/Homepage"));
const Pricing = React.lazy(() => import("./pages/Pricing"));
const SuccessStories = React.lazy(() => import("./pages/SuccessStories"));
const ChromeExtension = React.lazy(() => import("./pages/ChromeExtension"));
const Recruiters = React.lazy(() => import("./pages/Recruiters"));
const JobNiche = React.lazy(() => import("./pages/JobNiche"));
const ComparisonPage = React.lazy(() => import("./pages/ComparisonPage"));
const AlternativeTo = React.lazy(() => import("./pages/AlternativeTo"));
const ReviewPage = React.lazy(() => import("./pages/ReviewPage"));
const SwitchFrom = React.lazy(() => import("./pages/SwitchFrom"));
const PricingVs = React.lazy(() => import("./pages/PricingVs"));
const CategoryHub = React.lazy(() => import("./pages/CategoryHub"));
const GuidesHome = React.lazy(() => import("./pages/GuidesHome"));
const GuidePage = React.lazy(() => import("./pages/GuidePage"));
const Login = React.lazy(() => import("./pages/Login"));
const Privacy = React.lazy(() => import("./pages/Privacy"));
const Terms = React.lazy(() => import("./pages/Terms"));
const Dashboard = React.lazy(() => import("./pages/Dashboard"));
const Onboarding = React.lazy(() => import("./pages/app/Onboarding"));
const Settings = React.lazy(() => import("./pages/Settings"));
const NotFound = React.lazy(() => import("./pages/NotFound"));
const About = React.lazy(() => import("./pages/About"));
const Locations = React.lazy(() => import("./pages/Locations"));

// Dashboard sub-component wrappers for lazy loading
const JobsViewWrapper = React.lazy(() => import("./pages/Dashboard").then(module => ({ default: module.JobsView })));
const ApplicationsViewWrapper = React.lazy(() => import("./pages/Dashboard").then(module => ({ default: module.ApplicationsView })));
const HoldsViewWrapper = React.lazy(() => import("./pages/Dashboard").then(module => ({ default: module.HoldsView })));
const TeamViewWrapper = React.lazy(() => import("./pages/Dashboard").then(module => ({ default: module.TeamView })));
const BillingViewWrapper = React.lazy(() => import("./pages/Dashboard").then(module => ({ default: module.BillingView })));

// Dashboard sub-components are exported from Dashboard.tsx and will be loaded when Dashboard chunk loads

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
  const location = useLocation();
  const isAppRoute = location.pathname.startsWith("/app");

  // Track page views on route change
  useGoogleAnalytics();

  return (
    <>
      <Helmet>
        <title>JobHuntin | AI Job Search Automation & Auto-Apply</title>
        <meta name="description" content="Land your dream job with JobHuntin. Our AI agent swipes, tailors your resume, and auto-applies to 100s of jobs daily. Built for high-volume, high-quality hunting." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={config.urls.homepage} />
        <meta property="og:title" content="JobHuntin | AI Job Search Automation & Auto-Apply" />
        <meta property="og:description" content="Land your dream job with JobHuntin. Our AI agent swipes, tailors your resume, and auto-applies to 100s of jobs daily." />
        <meta property="og:image" content={`${config.urls.og}/api/og?job=AI%20Job%20Hunter&company=JobHuntin&score=100&location=Global`} />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="JobHuntin | AI Job Search Automation & Auto-Apply" />
        <meta name="twitter:description" content="Land your dream job with JobHuntin. Our AI agent swipes, tailors your resume, and auto-applies to 100s of jobs daily." />
        <meta name="twitter:image" content={`${config.urls.og}/api/og?job=AI%20Job%20Hunter&company=JobHuntin&score=100&location=Global`} />
        {isAppRoute && <meta name="robots" content="noindex, nofollow" />}
        <link rel="canonical" href={`${config.urls.homepage}${location.pathname === "/" ? "" : location.pathname}`} />
      </Helmet>
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
            <Route path="/alternative-to/:competitorSlug" element={<AlternativeTo />} />
            <Route path="/reviews/:competitorSlug" element={<ReviewPage />} />
            <Route path="/switch-from/:competitorSlug" element={<SwitchFrom />} />
            <Route path="/pricing-vs/:competitorSlug" element={<PricingVs />} />
            <Route path="/best/:categorySlug" element={<CategoryHub />} />
            <Route path="/guides" element={<GuidesHome />} />
            <Route path="/guides/:guideSlug" element={<GuidePage />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/about" element={<About />} />
            <Route path="/locations" element={<Locations />} />
            <Route path="/login" element={<Login />} />
            <Route path="*" element={<NotFound />} />
          </Route>

          {/* App Protected Routes */}
          <Route path="/app" element={<AuthGuard />}>
            <Route path="onboarding" element={<Onboarding />} />

            <Route element={<OnboardingGuard><AppLayout /></OnboardingGuard>}>
              <Route index element={<Navigate to="/app/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="jobs" element={<React.Suspense fallback={<PageLoader />}><JobsViewWrapper /></React.Suspense>} />
              <Route path="applications" element={<React.Suspense fallback={<PageLoader />}><ApplicationsViewWrapper /></React.Suspense>} />
              <Route path="holds" element={<React.Suspense fallback={<PageLoader />}><HoldsViewWrapper /></React.Suspense>} />
              <Route path="team" element={<React.Suspense fallback={<PageLoader />}><TeamViewWrapper /></React.Suspense>} />
              <Route path="billing" element={<React.Suspense fallback={<PageLoader />}><BillingViewWrapper /></React.Suspense>} />
              <Route path="settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </>
  );
}


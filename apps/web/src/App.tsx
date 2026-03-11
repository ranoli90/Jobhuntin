import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import React, { Suspense } from "react";
import { Helmet } from "react-helmet-async";
import { AlertCircle } from "lucide-react";
import { Button } from "./components/ui/Button";
import ScrollToTop from "./components/ScrollToTop";
import MarketingLayout from "./layouts/MarketingLayout";
import AuthGuard from "./guards/AuthGuard";
import AdminGuard from "./guards/AdminGuard";
import AppLayout from "./layouts/AppLayout";
import { useProfile } from "./hooks/useProfile";
import { LoadingSpinner } from "./components/ui/LoadingSpinner";
import { config } from "./config";
import { useGoogleAnalytics } from "./hooks/useGoogleAnalytics";
import { CookieConsent } from "./components/CookieConsent";
import { OfflineBanner } from "./components/OfflineBanner";
import { ErrorBoundary, RouteErrorBoundary } from "./components/ErrorBoundary";
import { ToastShelf } from "./components/ui/ToastShelf";

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
const BlogHome = React.lazy(() => import("./pages/BlogHome"));
const BlogPost = React.lazy(() => import("./pages/BlogPost"));
const ToolsHub = React.lazy(() => import("./pages/ToolsHub"));
const JobrightVsJobhuntin = React.lazy(
  () => import("./pages/JobrightVsJobhuntin"),
);
const Login = React.lazy(() => import("./pages/Login"));
const Privacy = React.lazy(() => import("./pages/Privacy"));
const Terms = React.lazy(() => import("./pages/Terms"));
const Dashboard = React.lazy(() => import("./pages/Dashboard"));
const Onboarding = React.lazy(() => import("./pages/app/Onboarding"));
const Billing = React.lazy(() => import("./pages/app/Billing"));
const AppNotFound = React.lazy(() => import("./pages/app/NotFound"));
const Settings = React.lazy(() => import("./pages/Settings"));
const Sessions = React.lazy(() => import("./pages/app/Sessions"));
const NotFound = React.lazy(() => import("./pages/NotFound"));
const Maintenance = React.lazy(() => import("./pages/Maintenance"));
const About = React.lazy(() => import("./pages/About"));
const Contact = React.lazy(() => import("./pages/Contact"));
const Locations = React.lazy(() => import("./pages/Locations"));
const TopicPage = React.lazy(() => import("./pages/TopicPage"));
const AuthorPage = React.lazy(() => import("./pages/AuthorPage"));

// AI Feature Pages
const MatchesPage = React.lazy(() => import("./pages/app/matches"));
const AITailorPage = React.lazy(() => import("./pages/app/ai-tailor"));
const ATSScorePage = React.lazy(() => import("./pages/app/ats-score"));

// Phase 12.1 Agent Improvements Pages
const AgentImprovementsPage = React.lazy(
  () => import("./pages/app/agent-improvements"),
);
const DLQDashboardPage = React.lazy(() => import("./pages/app/dlq-dashboard"));
const ScreenshotCapturePage = React.lazy(
  () => import("./pages/app/screenshot-capture"),
);

// Phase 13.1 Communication Pages
const CommunicationPreferencesPage = React.lazy(
  () => import("./pages/app/communication-preferences"),
);
const NotificationHistoryPage = React.lazy(
  () => import("./pages/app/notification-history"),
);

// Phase 14.1 User Experience Pages
const PipelineViewPage = React.lazy(() => import("./pages/app/pipeline-view"));
const ApplicationExportPage = React.lazy(
  () => import("./pages/app/application-export"),
);
const FollowUpRemindersPage = React.lazy(
  () => import("./pages/app/follow-up-reminders"),
);
const InterviewPracticePage = React.lazy(
  () => import("./pages/app/interview-practice"),
);
const MultiResumePage = React.lazy(() => import("./pages/app/multi-resume"));
const ApplicationNotesPage = React.lazy(
  () => import("./pages/app/application-notes"),
);

// Admin Pages
const ApplicationDetailPage = React.lazy(
  () => import("./pages/app/ApplicationDetailPage"),
);
const AdminUsagePage = React.lazy(() => import("./pages/admin/usage"));
const AdminMatchesPage = React.lazy(() => import("./pages/admin/matches"));
const AdminAlertsPage = React.lazy(() => import("./pages/admin/alerts"));
const AdminSourcesPage = React.lazy(() => import("./pages/admin/sources"));

// Dashboard sub-component wrappers for lazy loading
const JobsViewWrapper = React.lazy(() => import("./pages/dashboard/JobsView"));
const ApplicationsViewWrapper = React.lazy(
  () => import("./pages/dashboard/ApplicationsView"),
);
const HoldsViewWrapper = React.lazy(
  () => import("./pages/dashboard/HoldsView"),
);
const TeamViewWrapper = React.lazy(() => import("./pages/dashboard/TeamView"));
// Dashboard sub-components are exported from Dashboard.tsx and will be loaded when Dashboard chunk loads

// Job Alerts Page
const JobAlertsPage = React.lazy(() => import("./pages/app/JobAlerts"));

/**
 * Bi-directional onboarding guard:
 * - Users who haven't completed onboarding are redirected TO /app/onboarding
 * - Users who HAVE completed onboarding are redirected AWAY from /app/onboarding
 */
function OnboardingGuard({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { loading, needsOnboarding, error } = useProfile();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Loading..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center gap-4 p-4 text-center">
        <div className="rounded-full bg-destructive/10 p-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
        </div>
        <h2 className="text-xl font-semibold">We couldn&apos;t connect</h2>
        <p className="text-muted-foreground max-w-sm">
          We couldn&apos;t load your profile. Please check your internet
          connection and try again.
        </p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Try again
        </Button>
      </div>
    );
  }

  // User still needs onboarding — redirect to onboarding page
  if (needsOnboarding && location.pathname !== "/app/onboarding") {
    return <Navigate to="/app/onboarding" replace />;
  }

  return <>{children}</>;
}

/**
 * Prevents already-onboarded users from re-entering the onboarding flow.
 */
function CompletedOnboardingRedirect({
  children,
}: {
  children: React.ReactNode;
}) {
  const { loading, needsOnboarding } = useProfile();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Loading..." />
      </div>
    );
  }

  // Already completed onboarding — redirect to dashboard
  if (!needsOnboarding) {
    return <Navigate to="/app/dashboard" replace />;
  }

  return <>{children}</>;
}

// Loading Fallback
const PageLoader = () => (
  <div
    className="min-h-screen flex items-center justify-center bg-[#fafaf9] dark:bg-slate-950 dark:text-slate-100"
    role="status"
    aria-label="Loading page"
  >
    <LoadingSpinner label="Loading..." />
  </div>
);

export default function App() {
  const location = useLocation();

  // Track page views on route change
  useGoogleAnalytics();

  React.useEffect(() => {
    import("quicklink").then(({ listen }) => listen());
  }, []);

  return (
    <>
      <OfflineBanner />
      <Helmet
        defaultTitle="JobHuntin — The Application Engine That Runs While You Sleep"
        titleTemplate="%s | JobHuntin"
      >
        <meta
          name="description"
          content="Upload your resume. Our platform tailors every application and submits to hundreds of jobs daily."
        />
        <meta property="og:type" content="website" />
        <meta property="og:site_name" content="JobHuntin" />
        <meta property="og:locale" content="en_US" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:site" content="@jobhuntin" />
        <meta name="twitter:creator" content="@jobhuntin" />
        {location.pathname.startsWith("/app") && (
          <meta name="robots" content="noindex, nofollow" />
        )}
        {/* SEO #7: Canonical only for routes without page-level SEO (SEO component overrides when present) */}
        <link
          rel="canonical"
          href={`${config.urls.homepage}${location.pathname === "/" ? "" : location.pathname}`}
        />
        <link
          rel="alternate"
          hrefLang="en"
          href={`${config.urls.homepage}${location.pathname}`}
        />
        <link
          rel="alternate"
          hrefLang="x-default"
          href={`${config.urls.homepage}${location.pathname}`}
        />
      </Helmet>
      <ScrollToTop />
      <ToastShelf />
      <ErrorBoundary showToast reportError>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Public Marketing Pages & Auth */}
            <Route element={<MarketingLayout />}>
              <Route
                path="/"
                element={
                  <RouteErrorBoundary>
                    <Homepage />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/pricing"
                element={
                  <RouteErrorBoundary>
                    <Pricing />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/success-stories"
                element={
                  <RouteErrorBoundary>
                    <SuccessStories />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/chrome-extension"
                element={
                  <RouteErrorBoundary>
                    <ChromeExtension />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/recruiters"
                element={
                  <RouteErrorBoundary>
                    <Recruiters />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/jobs/:role/:city"
                element={
                  <RouteErrorBoundary>
                    <JobNiche />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/vs/:competitorSlug"
                element={
                  <RouteErrorBoundary>
                    <ComparisonPage />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/alternative-to/:competitorSlug"
                element={
                  <RouteErrorBoundary>
                    <AlternativeTo />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/reviews/:competitorSlug"
                element={
                  <RouteErrorBoundary>
                    <ReviewPage />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/switch-from/:competitorSlug"
                element={
                  <RouteErrorBoundary>
                    <SwitchFrom />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/pricing-vs/:competitorSlug"
                element={
                  <RouteErrorBoundary>
                    <PricingVs />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/best/:categorySlug"
                element={
                  <RouteErrorBoundary>
                    <CategoryHub />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/guides"
                element={
                  <RouteErrorBoundary>
                    <GuidesHome />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/guides/:guideSlug"
                element={
                  <RouteErrorBoundary>
                    <GuidePage />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/blog"
                element={
                  <RouteErrorBoundary>
                    <BlogHome />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/blog/:slug"
                element={
                  <RouteErrorBoundary>
                    <BlogPost />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/tools"
                element={
                  <RouteErrorBoundary>
                    <ToolsHub />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/vs/jobright"
                element={
                  <RouteErrorBoundary>
                    <JobrightVsJobhuntin />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/privacy"
                element={
                  <RouteErrorBoundary>
                    <Privacy />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/terms"
                element={
                  <RouteErrorBoundary>
                    <Terms />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/about"
                element={
                  <RouteErrorBoundary>
                    <About />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/contact"
                element={
                  <RouteErrorBoundary>
                    <Contact />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/locations"
                element={
                  <RouteErrorBoundary>
                    <Locations />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/topics/:slug"
                element={
                  <RouteErrorBoundary>
                    <TopicPage />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/authors/:authorId"
                element={
                  <RouteErrorBoundary>
                    <AuthorPage />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/login"
                element={
                  <RouteErrorBoundary>
                    <Login />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="/maintenance"
                element={
                  <RouteErrorBoundary>
                    <Maintenance />
                  </RouteErrorBoundary>
                }
              />
              <Route
                path="*"
                element={
                  <RouteErrorBoundary>
                    <NotFound />
                  </RouteErrorBoundary>
                }
              />
            </Route>

            {/* App Protected Routes */}
            <Route path="/app" element={<AuthGuard />}>
              <Route
                path="onboarding"
                element={
                  <CompletedOnboardingRedirect>
                    <RouteErrorBoundary>
                      <Onboarding />
                    </RouteErrorBoundary>
                  </CompletedOnboardingRedirect>
                }
              />

              <Route
                element={
                  <OnboardingGuard>
                    <AppLayout />
                  </OnboardingGuard>
                }
              >
                <Route
                  index
                  element={<Navigate to="/app/dashboard" replace />}
                />
                <Route
                  path="dashboard"
                  element={
                    <RouteErrorBoundary>
                      <Dashboard />
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="jobs"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <JobsViewWrapper />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="applications"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <ApplicationsViewWrapper />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="applications/:id"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <ApplicationDetailPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="holds"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <HoldsViewWrapper />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="team"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <TeamViewWrapper />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="job-alerts"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <JobAlertsPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="billing"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <Billing />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="settings"
                  element={
                    <RouteErrorBoundary>
                      <Settings />
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="sessions"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <Sessions />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />

                {/* AI Feature Routes */}
                <Route
                  path="matches"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <MatchesPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="tailor"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <AITailorPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="ats-score"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <ATSScorePage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />

                {/* Phase 12.1 Agent Improvements Routes */}
                <Route
                  path="agent-improvements"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <AgentImprovementsPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="dlq-dashboard"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <DLQDashboardPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="screenshot-capture"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <ScreenshotCapturePage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />

                {/* Phase 13.1 Communication Routes */}
                <Route
                  path="communication-preferences"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <CommunicationPreferencesPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="notification-history"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <NotificationHistoryPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />

                {/* Phase 14.1 User Experience Routes */}
                <Route
                  path="pipeline-view"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <PipelineViewPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="application-export"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <ApplicationExportPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="follow-up-reminders"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <FollowUpRemindersPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="interview-practice"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <InterviewPracticePage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="multi-resume"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <MultiResumePage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />
                <Route
                  path="application-notes"
                  element={
                    <RouteErrorBoundary>
                      <React.Suspense fallback={<PageLoader />}>
                        <ApplicationNotesPage />
                      </React.Suspense>
                    </RouteErrorBoundary>
                  }
                />

                {/* Admin Routes */}
                <Route path="admin" element={<AdminGuard />}>
                  <Route
                    path="usage"
                    element={
                      <RouteErrorBoundary>
                        <React.Suspense fallback={<PageLoader />}>
                          <AdminUsagePage />
                        </React.Suspense>
                      </RouteErrorBoundary>
                    }
                  />
                  <Route
                    path="matches"
                    element={
                      <RouteErrorBoundary>
                        <React.Suspense fallback={<PageLoader />}>
                          <AdminMatchesPage />
                        </React.Suspense>
                      </RouteErrorBoundary>
                    }
                  />
                  <Route
                    path="alerts"
                    element={
                      <RouteErrorBoundary>
                        <React.Suspense fallback={<PageLoader />}>
                          <AdminAlertsPage />
                        </React.Suspense>
                      </RouteErrorBoundary>
                    }
                  />
                  <Route
                    path="sources"
                    element={
                      <RouteErrorBoundary>
                        <React.Suspense fallback={<PageLoader />}>
                          <AdminSourcesPage />
                        </React.Suspense>
                      </RouteErrorBoundary>
                    }
                  />
                </Route>

                <Route
                  path="*"
                  element={
                    <React.Suspense fallback={<PageLoader />}>
                      <AppNotFound />
                    </React.Suspense>
                  }
                />
              </Route>
            </Route>
          </Routes>
        </Suspense>
      </ErrorBoundary>
      <CookieConsent />
    </>
  );
}

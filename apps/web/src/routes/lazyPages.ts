/**
 * Lazy-loaded page components, organized by feature area.
 *
 * Extracted from App.tsx (FE-002) to reduce the 120-line import block
 * into a single grouped import. Each page is React.lazy() loaded for
 * code-splitting.
 */
import React from "react";

// ---------------------------------------------------------------------------
// Marketing / Public Pages
// ---------------------------------------------------------------------------
export const Homepage = React.lazy(() => import("../pages/Homepage"));
export const Pricing = React.lazy(() => import("../pages/Pricing"));
export const SuccessStories = React.lazy(() => import("../pages/SuccessStories"));
export const ChromeExtension = React.lazy(() => import("../pages/ChromeExtension"));
export const Recruiters = React.lazy(() => import("../pages/Recruiters"));
export const JobNiche = React.lazy(() => import("../pages/JobNiche"));
export const ComparisonPage = React.lazy(() => import("../pages/ComparisonPage"));
export const AlternativeTo = React.lazy(() => import("../pages/AlternativeTo"));
export const ReviewPage = React.lazy(() => import("../pages/ReviewPage"));
export const SwitchFrom = React.lazy(() => import("../pages/SwitchFrom"));
export const PricingVs = React.lazy(() => import("../pages/PricingVs"));
export const CategoryHub = React.lazy(() => import("../pages/CategoryHub"));
export const Locations = React.lazy(() => import("../pages/Locations"));
export const TopicPage = React.lazy(() => import("../pages/TopicPage"));
export const AuthorPage = React.lazy(() => import("../pages/AuthorPage"));
export const About = React.lazy(() => import("../pages/About"));
export const Contact = React.lazy(() => import("../pages/Contact"));
export const JobrightVsJobhuntin = React.lazy(
  () => import("../pages/JobrightVsJobhuntin"),
);

// ---------------------------------------------------------------------------
// Content / Blog / Guides
// ---------------------------------------------------------------------------
export const GuidesHome = React.lazy(() => import("../pages/GuidesHome"));
export const GuidePage = React.lazy(() => import("../pages/GuidePage"));
export const BlogHome = React.lazy(() => import("../pages/BlogHome"));
export const BlogPost = React.lazy(() => import("../pages/BlogPost"));
export const ToolsHub = React.lazy(() => import("../pages/ToolsHub"));

// ---------------------------------------------------------------------------
// Auth / Legal
// ---------------------------------------------------------------------------
export const Login = React.lazy(() => import("../pages/Login"));
export const Privacy = React.lazy(() => import("../pages/Privacy"));
export const Terms = React.lazy(() => import("../pages/Terms"));

// ---------------------------------------------------------------------------
// Core App Pages
// ---------------------------------------------------------------------------
export const Dashboard = React.lazy(() => import("../pages/Dashboard"));
export const Onboarding = React.lazy(() => import("../pages/app/Onboarding"));
export const Billing = React.lazy(() => import("../pages/app/Billing"));
export const AppNotFound = React.lazy(() => import("../pages/app/NotFound"));
export const Settings = React.lazy(() => import("../pages/Settings"));
export const Sessions = React.lazy(() => import("../pages/app/Sessions"));
export const NotFound = React.lazy(() => import("../pages/NotFound"));
export const Maintenance = React.lazy(() => import("../pages/Maintenance"));

// ---------------------------------------------------------------------------
// AI Feature Pages
// ---------------------------------------------------------------------------
export const MatchesPage = React.lazy(() => import("../pages/app/matches"));
export const AITailorPage = React.lazy(() => import("../pages/app/ai-tailor"));
export const ATSScorePage = React.lazy(() => import("../pages/app/ats-score"));

// ---------------------------------------------------------------------------
// Agent Improvements (Phase 12.1)
// ---------------------------------------------------------------------------
export const AgentImprovementsPage = React.lazy(
  () => import("../pages/app/agent-improvements"),
);
export const DLQDashboardPage = React.lazy(
  () => import("../pages/app/dlq-dashboard"),
);
export const ScreenshotCapturePage = React.lazy(
  () => import("../pages/app/screenshot-capture"),
);

// ---------------------------------------------------------------------------
// Communication (Phase 13.1)
// ---------------------------------------------------------------------------
export const CommunicationPreferencesPage = React.lazy(
  () => import("../pages/app/communication-preferences"),
);
export const NotificationHistoryPage = React.lazy(
  () => import("../pages/app/notification-history"),
);

// ---------------------------------------------------------------------------
// User Experience (Phase 14.1)
// ---------------------------------------------------------------------------
export const PipelineViewPage = React.lazy(
  () => import("../pages/app/pipeline-view"),
);
export const ApplicationExportPage = React.lazy(
  () => import("../pages/app/application-export"),
);
export const FollowUpRemindersPage = React.lazy(
  () => import("../pages/app/follow-up-reminders"),
);
export const InterviewPracticePage = React.lazy(
  () => import("../pages/app/interview-practice"),
);
export const MultiResumePage = React.lazy(
  () => import("../pages/app/multi-resume"),
);
export const ApplicationNotesPage = React.lazy(
  () => import("../pages/app/application-notes"),
);

// ---------------------------------------------------------------------------
// Admin Pages
// ---------------------------------------------------------------------------
export const ApplicationDetailPage = React.lazy(
  () => import("../pages/app/ApplicationDetailPage"),
);
export const AdminUsagePage = React.lazy(() => import("../pages/admin/usage"));
export const AdminMatchesPage = React.lazy(
  () => import("../pages/admin/matches"),
);
export const AdminAlertsPage = React.lazy(
  () => import("../pages/admin/alerts"),
);
export const AdminSourcesPage = React.lazy(
  () => import("../pages/admin/sources"),
);

// ---------------------------------------------------------------------------
// Dashboard Sub-Components
// ---------------------------------------------------------------------------
export const JobsViewWrapper = React.lazy(
  () => import("../pages/dashboard/JobsView"),
);
export const ApplicationsViewWrapper = React.lazy(
  () => import("../pages/dashboard/ApplicationsView"),
);
export const HoldsViewWrapper = React.lazy(
  () => import("../pages/dashboard/HoldsView"),
);
export const TeamViewWrapper = React.lazy(
  () => import("../pages/dashboard/TeamView"),
);

// ---------------------------------------------------------------------------
// Jobs & Alerts
// ---------------------------------------------------------------------------
export const JobAlertsPage = React.lazy(() => import("../pages/app/JobAlerts"));
export const SavedJobsPage = React.lazy(
  () => import("../pages/app/SavedJobs"),
);

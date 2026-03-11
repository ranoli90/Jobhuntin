import { FocusTrap } from "focus-trap-react";
import {
  ArrowUpRight,
  BarChart3,
  Briefcase,
  DollarSign,
  Inbox,
  Rocket,
  MessageCircle,
  CheckCircle,
  Clock,
  Zap,
  Quote,
  Send,
  Users,
  Loader2,
  Sparkles,
  AlertTriangle,
  Radar,
  MoreVertical,
  Eye,
  Pause,
  Trash2,
  Filter,
  MapPin,
  BriefcaseIcon,
  Sun,
  Sunset,
  Moon,
  TrendingUp,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { useBilling } from "../../hooks/useBilling";
import { useApplications } from "../../hooks/useApplications";
import { useProfile } from "../../hooks/useProfile";
import { useNavigate } from "react-router-dom";
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useTransform,
  useReducedMotion,
} from "framer-motion";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { apiPost, apiGet } from "../../lib/api";
import { pushToast } from "../../lib/toast";
import { fireSuccessConfetti } from "../../lib/confetti";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { useJobs } from "../../hooks/useJobs";
import type { JobFilters } from "../../hooks/useJobs";
import { formatCurrency, formatDate } from "../../lib/format";
import { t, formatT, getLocale, isRTLLanguage } from "../../lib/i18n";
import { useSessionMilestone } from "../../hooks/useCelebrations";
import { telemetry } from "../../lib/telemetry";
import { AnimatedNumber, statusVariant } from "./shared";

function getGreeting(firstName?: string): {
  text: string;
  Icon: React.ElementType;
} {
  const hour = new Date().getHours();
  const name = firstName ? `, ${firstName}` : "";
  if (hour < 12) return { text: `Good morning${name}`, Icon: Sun };
  if (hour < 17) return { text: `Good afternoon${name}`, Icon: Sunset };
  return { text: `Good evening${name}`, Icon: Moon };
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { status } = useBilling();
  const { profile } = useProfile();
  const {
    applications,
    holdApplications,
    byStatus,
    stats,
    queueStats,
    isLoading,
    error,
    refetch,
  } = useApplications();

  const shouldReduceMotion = useReducedMotion();

  const locale = getLocale();
  const rtl = isRTLLanguage(locale);

  const totalApps = applications.length || 1; // avoid /0
  const activeCount = byStatus.APPLYING + byStatus.APPLIED;
  const activeProgress = Math.min(
    100,
    Math.round((activeCount / totalApps) * 100),
  );
  const appliedRate =
    applications.length > 0
      ? Math.round((byStatus.APPLIED / applications.length) * 100)
      : 0;
  const appliedProgress = Math.min(100, appliedRate);
  const holdProgress = Math.min(
    100,
    Math.round((byStatus.HOLD / totalApps) * 100),
  );
  const totalProgress = Math.min(
    100,
    Math.round(
      (applications.length / Math.max(applications.length, 100)) * 100,
    ),
  );

  const metrics = [
    {
      label: "Active Applications",
      value: activeCount,
      icon: Briefcase,
      color: "from-blue-500 to-blue-600",
      bg: "bg-blue-50",
      text: "text-blue-600",
      iconColor: "text-blue-500",
      progress: activeProgress,
    },
    {
      label: "Applied Rate",
      value: `${appliedRate}%`,
      icon: BarChart3,
      color: "from-emerald-500 to-emerald-600",
      bg: "bg-emerald-50",
      text: "text-emerald-600",
      iconColor: "text-emerald-500",
      progress: appliedProgress,
    },
    {
      label: "Needs Your Input",
      value: byStatus.HOLD,
      icon: Inbox,
      color: "from-amber-500 to-amber-600",
      bg: "bg-amber-50",
      text: "text-amber-600",
      iconColor: "text-amber-500",
      progress: holdProgress,
      title:
        "Applications where the form asked a question we need you to answer",
    },
    {
      label: "Total Applications",
      value: applications.length,
      icon: Zap,
      color: "from-brand-primary to-brand-primaryHover",
      bg: "bg-brand-primary/10",
      text: "text-brand-primary",
      iconColor: "text-brand-primary",
      progress: totalProgress,
    },
  ];

  const greeting = getGreeting(
    profile?.contact?.first_name || profile?.contact?.full_name?.split(" ")[0],
  );
  const recentApps = applications.slice(0, 5);

  return (
    <motion.div
      initial={shouldReduceMotion ? undefined : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={shouldReduceMotion ? undefined : { duration: 0.5 }}
      className="space-y-3 max-w-7xl mx-auto px-4 lg:px-6 pb-8"
    >
      {error && (
        <div
          className="flex items-center gap-3 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800"
          role="alert"
        >
          <AlertTriangle
            className="h-5 w-5 text-red-500 flex-shrink-0"
            aria-hidden
          />
          <div className="flex-1">
            <p className="font-bold text-sm">Unable to load dashboard data</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-red-600 font-bold text-xs"
            onClick={() => refetch()}
            aria-label="Retry loading dashboard"
          >
            Try again
          </Button>
        </div>
      )}
      {queueStats &&
        (queueStats.queue_ahead > 0 || queueStats.eta_minutes > 0) && (
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-sm"
            role="status"
          >
            <Clock
              className="h-4 w-4 text-blue-600 flex-shrink-0"
              aria-hidden
            />
            <span>
              {queueStats.queue_ahead > 0 && (
                <>{queueStats.queue_ahead} ahead in queue</>
              )}
              {queueStats.queue_ahead > 0 &&
                queueStats.eta_minutes > 0 &&
                " • "}
              {queueStats.eta_minutes > 0 && (
                <>~{queueStats.eta_minutes} min estimated</>
              )}
            </span>
          </div>
        )}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <motion.div
          initial={shouldReduceMotion ? undefined : { opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={shouldReduceMotion ? undefined : { delay: 0.1 }}
        >
          <div className="flex items-center gap-2 mb-0.5">
            <greeting.Icon className="h-4 w-4 text-amber-400" aria-hidden />
            <p className="text-sm font-semibold text-brand-muted">
              {greeting.text}
            </p>
          </div>
          <h1 className="font-display text-xl md:text-2xl font-bold text-brand-text">
            Your Dashboard
          </h1>
        </motion.div>
        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
          <Button
            className="group relative overflow-hidden gap-2 px-6 py-3 rounded-xl bg-brand-primary hover:bg-brand-primaryHover text-white shadow-lg shadow-brand-primary/20 transition-all duration-300"
            onClick={() => navigate("/app/jobs")}
          >
            <span className="relative z-10 flex items-center gap-2">
              <Rocket
                className="h-5 w-5 transition-transform group-hover:rotate-12"
                aria-hidden
              />
              <span className="font-medium">Find Jobs</span>
            </span>
          </Button>
        </motion.div>
      </div>

      {applications.length === 0 && !isLoading ? (
        <Card className="p-8 text-center border-brand-primary/20 bg-brand-primary/5 rounded-xl">
          <Rocket className="h-12 w-12 text-brand-primary mx-auto mb-4" />
          <h2 className="text-xl font-bold text-brand-text mb-2">
            Welcome to your dashboard!
          </h2>
          <p className="text-brand-muted mb-2 max-w-md mx-auto">
            You haven&apos;t applied to any jobs yet. Swipe right on jobs you
            like and our AI will apply for you automatically.
          </p>
          <p className="text-brand-muted/80 text-sm mb-6 max-w-md mx-auto">
            Start by browsing jobs matched to your profile — it only takes a few
            swipes.
          </p>
          <Button
            onClick={() => navigate("/app/jobs")}
            className="bg-brand-primary hover:bg-brand-primaryHover text-white"
          >
            <Rocket className="mr-2 h-4 w-4" /> Browse Jobs
          </Button>
        </Card>
      ) : (
        <div className="-mx-1 overflow-x-auto pb-1 lg:mx-0">
          <div className="flex gap-2 md:grid md:grid-cols-2 xl:grid-cols-4 min-w-full px-1">
            {metrics.map((metric, index) => (
              <motion.div
                key={metric.label}
                initial={shouldReduceMotion ? undefined : { opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={
                  shouldReduceMotion
                    ? undefined
                    : { delay: 0.05 * index, duration: 0.4 }
                }
                className="h-full min-w-[240px] md:min-w-0"
                title={
                  "title" in metric && metric.title ? metric.title : undefined
                }
              >
                <Card
                  className="h-full border-brand-border bg-white hover:border-brand-primary/30 transition-colors duration-200 group rounded-xl"
                  shadow="sm"
                  tone="glass"
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-3">
                      <p className="text-sm text-brand-muted">{metric.label}</p>
                      <p className="text-2xl font-semibold text-brand-text tabular-nums">
                        {isLoading ? (
                          <span className="inline-block h-7 w-14 bg-slate-100 rounded animate-pulse"></span>
                        ) : (typeof metric.value === "string" ? (
                          metric.value
                        ) : (
                          <AnimatedNumber
                            value={metric.value}
                            shouldReduceMotion={!!shouldReduceMotion}
                          />
                        ))}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 h-1.5 w-full bg-brand-gray rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full rounded-full bg-gradient-to-r ${metric.color}`}
                      initial={
                        shouldReduceMotion
                          ? { width: `${metric.progress}%` }
                          : { width: 0 }
                      }
                      animate={{ width: `${metric.progress}%` }}
                      transition={
                        shouldReduceMotion
                          ? undefined
                          : {
                              delay: 0.2 + index * 0.08,
                              duration: 0.6,
                              type: "spring",
                            }
                      }
                    />
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-3 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card
              className="relative overflow-hidden border-amber-200/50 bg-gradient-to-br from-amber-50/50 to-white"
              tone="glass"
            >
              <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-amber-500/5 blur-3xl"></div>
                <div className="absolute -left-10 -bottom-10 h-40 w-40 rounded-full bg-amber-500/5 blur-3xl"></div>
              </div>

              <div className="relative z-10 space-y-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-100 text-amber-600">
                      <Inbox className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-amber-900/60">
                        Items needing your input
                      </p>
                      <p className="text-2xl font-bold text-slate-900">
                        {isLoading ? (
                          <span className="inline-block h-7 w-24 bg-slate-100 rounded animate-pulse"></span>
                        ) : (
                          `${holdApplications.length} Pending`
                        )}
                      </p>
                    </div>
                  </div>
                  <Badge className="bg-amber-100 text-amber-700 border-amber-200 hover:bg-amber-200 transition-colors">
                    Needs attention
                  </Badge>
                </div>
                <div className="space-y-3">
                  {isLoading ? (
                    <div className="rounded-xl bg-white/50 p-4 border border-slate-100">
                      <div className="h-4 w-[75%] rounded bg-slate-100 animate-pulse"></div>
                      <div className="mt-2 h-3 w-[50%] rounded bg-slate-50 animate-pulse"></div>
                    </div>
                  ) : holdApplications.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-amber-200 bg-amber-50/30 p-6 text-center">
                      <CheckCircle className="mx-auto h-8 w-8 text-amber-500/50 mb-2" />
                      <p className="text-amber-900/80 font-medium">
                        No pending questions
                      </p>
                      <p className="text-sm text-amber-900/50">
                        You're all caught up!
                      </p>
                    </div>
                  ) : (
                    <motion.div
                      className="space-y-3"
                      initial="hidden"
                      animate="visible"
                      variants={{
                        hidden: { opacity: 0 },
                        visible: {
                          opacity: 1,
                          transition: {
                            staggerChildren: 0.1,
                          },
                        },
                      }}
                    >
                      {holdApplications.slice(0, 3).map((app, index) => (
                        <motion.div
                          key={app.id}
                          className="group flex items-center justify-between rounded-xl bg-white p-4 shadow-sm border border-slate-100 transition-all hover:shadow-md hover:border-amber-200"
                          variants={{
                            hidden: { opacity: 0, y: 10 },
                            visible: {
                              opacity: 1,
                              y: 0,
                              transition: {
                                type: "spring",
                                stiffness: 300,
                                damping: 20,
                              },
                            },
                          }}
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-amber-600">
                              <MessageCircle className="h-3.5 w-3.5" />
                            </div>
                            <div className="min-w-0">
                              <p className="truncate font-medium text-slate-900">
                                {app.company ?? "Unknown"}
                              </p>
                              <p className="text-xs text-slate-500 truncate">
                                {app.hold_question?.slice(0, 50)}
                                {app.hold_question &&
                                app.hold_question.length > 50
                                  ? "..."
                                  : ""}
                              </p>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs font-medium text-amber-600 hover:bg-amber-50 hover:text-amber-700 transition-colors"
                            onClick={() =>
                              navigate(`/app/applications/${app.id}`)
                            }
                          >
                            Review
                          </Button>
                        </motion.div>
                      ))}
                    </motion.div>
                  )}
                </div>
                {holdApplications.length > 3 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-3 border-amber-200 text-amber-700 hover:bg-amber-50 hover:text-amber-800 transition-colors"
                    onClick={() => navigate("/app/applications")}
                  >
                    View all {holdApplications.length} items
                  </Button>
                )}
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <Card className="border-slate-200 bg-white" tone="glass">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-slate-500">
                    Recent Activity
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs"
                    onClick={() => navigate("/app/applications")}
                  >
                    View all
                  </Button>
                </div>
                {recentApps.length === 0 ? (
                  <p className="text-sm text-slate-400 text-center py-4">
                    No applications yet
                  </p>
                ) : (
                  <div className="space-y-3">
                    {recentApps.map((app) => (
                      <div
                        key={app.id}
                        className="flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-xs">
                            {(app.company ?? "").charAt(0) || "?"}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-slate-900">
                              {app.company ?? "Unknown"}
                            </p>
                            <p className="text-xs text-slate-500">
                              {app.job_title}
                              {app.last_activity
                                ? ` · ${formatDate(app.last_activity, locale)}`
                                : ""}
                            </p>
                          </div>
                        </div>
                        <Badge
                          variant={statusVariant(app.status)}
                          className="text-[10px]"
                        >
                          {app.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        </div>

        <div className="space-y-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card
              className="relative overflow-hidden border-brand-primary/20 bg-gradient-to-br from-brand-primary/5 to-white"
              tone="glass"
            >
              <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-brand-primary/5 blur-3xl"></div>
                <div className="absolute -left-10 -bottom-10 h-40 w-40 rounded-full bg-brand-primary/5 blur-3xl"></div>
              </div>

              <div className="relative z-10 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-brand-muted">
                      Your plan
                    </p>
                    <p className="text-2xl font-bold text-brand-text">
                      {status?.plan ?? "FREE"}
                    </p>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-primary/10 text-brand-primary">
                    <Zap className="h-5 w-5" />
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-brand-muted">Status</span>
                    <span className="font-medium text-emerald-600 capitalize">
                      {status?.subscription_status ?? "active"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-brand-muted">Applied Rate</span>
                    <span className="font-medium text-emerald-600">
                      {appliedRate}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-brand-muted">Next Billing</span>
                    <div className="flex items-center text-brand-text">
                      <Clock className="h-3.5 w-3.5 mr-1 text-brand-muted" />
                      <span>
                        {status?.current_period_end
                          ? formatDate(status.current_period_end, locale)
                          : "No upcoming bill"}
                      </span>
                    </div>
                  </div>
                </div>

                <Button
                  className="w-full mt-2 bg-slate-900 hover:bg-black text-white hover:shadow-lg transition-all"
                  onClick={() => navigate("/app/billing")}
                >
                  View plans
                </Button>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}

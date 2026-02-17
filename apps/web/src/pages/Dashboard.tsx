import { ArrowUpRight, BarChart3, Briefcase, DollarSign, Inbox, Rocket, MessageCircle, CheckCircle, Clock, Zap, Quote, Send, Users, Loader2, Sparkles, AlertTriangle, Radar } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBilling } from "../hooks/useBilling";
import { useApplications } from "../hooks/useApplications";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence, useMotionValue, useTransform, useReducedMotion } from "framer-motion";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiPost, apiGet } from "../lib/api";
import { pushToast } from "../lib/toast";
import { fireSuccessConfetti } from "../lib/confetti";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { useJobs } from "../hooks/useJobs";
import type { JobFilters } from "../hooks/useJobs";
import { formatCurrency, formatDate } from "../lib/format";
import { t, isRTL, getLocale } from "../lib/i18n";
import { useSessionMilestone } from "../hooks/useCelebrations";

// N-10: Centralised status → Badge variant mapping
function statusVariant(status: string): 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'APPLIED': return 'success';
    case 'HOLD': return 'warning';
    case 'FAILED':
    case 'REJECTED': return 'error';
    default: return 'default';
  }
}

// N-8: Tier pricing extracted to a constant so it isn't recreated every render
const BILLING_TIERS = [
  { name: "FREE" as const, price: "$0", features: ["10 applications", "Basic tailoring", "Standard support"], actionKey: null },
  { name: "PRO" as const, price: "$19", features: ["Unlimited apps", "Priority queue", "Interview coach"], recommended: true, actionKey: "upgrade" as const },
  { name: "TEAM" as const, price: "$49", features: ["10 team seats", "API access", "White-label reports"], actionKey: "addSeats" as const },
] as const;

// N-2: Shared locale helper – used by all sub-views
const sharedLocale = getLocale();
const sharedRtl = isRTL(sharedLocale);

// M-12: Page size for ApplicationsView pagination
const APPLICATIONS_PAGE_SIZE = 20;

/**
 * L-3: JobCard wrapper — provides drag threshold visual feedback.
 * Shows green/red overlay tint as the user drags past the ±100px threshold.
 */
function JobCard({
  job,
  isTop,
  idx,
  shouldReduceMotion,
  swipeDirection,
  onSwipe,
  locale,
  children,
}: {
  job: { id: string };
  isTop: boolean;
  idx: number;
  shouldReduceMotion: boolean;
  swipeDirection: 'left' | 'right' | null;
  onSwipe: (direction: 'ACCEPT' | 'REJECT') => void;
  locale: string | undefined;
  children: React.ReactNode;
}) {
  const x = useMotionValue(0);
  // L-3: opacity for accept overlay (right drag ➡ green)
  const acceptOpacity = useTransform(x, [0, 100, 200], [0, 0, 0.25]);
  // L-3: opacity for reject overlay (left drag ➡ red)
  const rejectOpacity = useTransform(x, [0, -100, -200], [0, 0, 0.25]);

  return (
    <motion.div
      style={{
        zIndex: idx,
        position: 'absolute',
        width: '100%',
        x,
      }}
      initial={shouldReduceMotion ? undefined : { scale: 0.95, opacity: 0, y: 20 }}
      animate={{
        scale: isTop ? 1 : 0.95,
        opacity: 1,
        y: isTop ? 0 : 20,
        rotate: isTop ? 0 : idx % 2 === 0 ? 1 : -1,
      }}
      exit={
        shouldReduceMotion
          ? undefined
          : {
            x: swipeDirection === 'left' ? -1000 : 1000,
            opacity: 0,
            rotate: swipeDirection === 'left' ? -20 : 20,
            transition: { duration: 0.5 },
          }
      }
      drag={isTop && !shouldReduceMotion ? 'x' : false}
      dragConstraints={{ left: 0, right: 0 }}
      onDragEnd={(_, info) => {
        if (info.offset.x > 100) onSwipe('ACCEPT');
        else if (info.offset.x < -100) onSwipe('REJECT');
      }}
    >
      {/* L-3: Accept overlay (green) */}
      <motion.div
        className="absolute inset-0 rounded-2xl bg-emerald-500 z-20 pointer-events-none flex items-center justify-center"
        style={{ opacity: acceptOpacity }}
      >
        <span className="text-6xl text-white font-black">✓</span>
      </motion.div>
      {/* L-3: Reject overlay (red) */}
      <motion.div
        className="absolute inset-0 rounded-2xl bg-red-500 z-20 pointer-events-none flex items-center justify-center"
        style={{ opacity: rejectOpacity }}
      >
        <span className="text-6xl text-white font-black">✕</span>
      </motion.div>
      {children}
    </motion.div>
  );
}

const AnimatedNumber = ({ value, duration = 1.5 }: { value: number | string; duration?: number }) => {
  const [displayValue, setDisplayValue] = useState(0);
  const prevValueRef = useRef(0);

  useEffect(() => {
    const numValue = Number(value);
    if (isNaN(numValue) || numValue < 0) {
      setDisplayValue(numValue || 0);
      return;
    }

    const start = prevValueRef.current;
    const end = numValue;
    prevValueRef.current = end;

    if (start === end) {
      setDisplayValue(end);
      return;
    }

    const diff = end - start;
    const increment = diff / (duration * 60); // 60fps
    let current = start;

    const timer = setInterval(() => {
      current += increment;
      if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
        setDisplayValue(end);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(current));
      }
    }, 1000 / 60);

    return () => clearInterval(timer);
  }, [value, duration]);

  return <span>{typeof value === 'string' ? value : displayValue}</span>;
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { status } = useBilling();
  const { applications, holdApplications, byStatus, stats, isLoading, error } = useApplications();

  const shouldReduceMotion = useReducedMotion();

  // N-2: Use shared locale instead of duplicating detection
  const locale = sharedLocale;
  const rtl = sharedRtl;

  // L-2: Compute data-driven progress values
  const totalApps = applications.length || 1; // avoid /0
  const activeCount = byStatus.APPLYING + byStatus.APPLIED;
  const activeProgress = Math.min(100, Math.round((activeCount / totalApps) * 100));
  const successProgress = Math.min(100, stats.successRate);
  const holdProgress = Math.min(100, Math.round((byStatus.HOLD / totalApps) * 100));
  const monthlyProgress = Math.min(100, Math.round((stats.monthlyApps / Math.max(stats.monthlyApps, 100)) * 100));

  const metrics = [
    {
      label: "Active Applications",
      value: activeCount,
      icon: Briefcase,
      color: 'from-blue-500 to-blue-600',
      bg: 'bg-blue-50',
      text: 'text-blue-600',
      iconColor: 'text-blue-500',
      progress: activeProgress,
    },
    {
      label: "Success Rate",
      value: `${stats.successRate}%`,
      icon: BarChart3,
      color: 'from-emerald-500 to-emerald-600',
      bg: 'bg-emerald-50',
      text: 'text-emerald-600',
      iconColor: 'text-emerald-500',
      progress: successProgress,
    },
    {
      label: "Pending HOLDs",
      value: byStatus.HOLD,
      icon: Inbox,
      color: 'from-amber-500 to-amber-600',
      bg: 'bg-amber-50',
      text: 'text-amber-600',
      iconColor: 'text-amber-500',
      progress: holdProgress,
    },
    {
      label: "Total Applications",
      value: stats.monthlyApps,
      icon: Zap,
      color: 'from-primary-500 to-primary-600',
      bg: 'bg-primary-50',
      text: 'text-primary-600',
      iconColor: 'text-primary-500',
      progress: monthlyProgress,
    },
  ];

  return (
    <motion.div
      initial={shouldReduceMotion ? undefined : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={shouldReduceMotion ? undefined : { duration: 0.5 }}
      className="space-y-3 max-w-7xl mx-auto px-4 lg:px-6 pb-8"
    >
      {/* M-5: Error banner when data fetch fails */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800">
          <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" />
          <div className="flex-1">
            <p className="font-bold text-sm">Unable to load dashboard data</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
          <Button variant="ghost" size="sm" className="text-red-600 font-bold text-xs" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <p className="text-[10px] font-medium uppercase tracking-[0.4em] text-slate-500">Dashboard</p>
          <h1 className="font-display text-xl md:text-2xl font-bold text-slate-900">
            Your Command Center
          </h1>
        </motion.div>
        <motion.div
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Button
            className="group relative overflow-hidden gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white shadow-lg shadow-primary-500/20 transition-all duration-300"
            onClick={() => navigate("/app/jobs")}
          >
            <span className="relative z-10 flex items-center gap-2">
              <Rocket className="h-5 w-5 transition-transform group-hover:rotate-12" />
              <span className="font-medium">Find Jobs</span>
            </span>
          </Button>
        </motion.div>
      </div>

      <div className="-mx-1 overflow-x-auto pb-1 lg:mx-0">
        <div className="flex gap-2 md:grid md:grid-cols-2 xl:grid-cols-4 min-w-full px-1">
          {metrics.map((metric, index) => (
            <motion.div
              key={metric.label}
              initial={shouldReduceMotion ? undefined : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={shouldReduceMotion ? undefined : { delay: 0.05 * index, duration: 0.4 }}
              className="h-full min-w-[240px] md:min-w-0"
            >
              <Card
                className="h-full border-slate-200 bg-white/60 hover:bg-white transition-all duration-300 group"
                shadow="sm"
                tone="glass"
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
                      <metric.icon className={`h-4 w-4 ${metric.iconColor}`} />
                      <span>{metric.label}</span>
                    </div>
                    <p className="text-2xl font-bold text-slate-900">
                      {isLoading ? (
                        <span className="inline-block h-8 w-16 bg-slate-100 rounded animate-pulse"></span>
                      ) : typeof metric.value === 'string' ? (
                        metric.value
                      ) : (
                        <AnimatedNumber value={metric.value} />
                      )}
                    </p>
                  </div>
                </div>
                {/* L-2: Data-driven progress bar */}
                <div className="mt-4 h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full bg-gradient-to-r ${metric.color}`}
                    initial={shouldReduceMotion ? { width: `${metric.progress}%` } : { width: 0 }}
                    animate={{ width: `${metric.progress}%` }}
                    transition={shouldReduceMotion ? undefined : { delay: 0.2 + index * 0.08, duration: 0.6, type: 'spring' }}
                  />
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="relative overflow-hidden border-amber-200/50 bg-gradient-to-br from-amber-50/50 to-white" tone="glass">
              {/* Animated background elements */}
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
                      <p className="text-sm font-medium text-amber-900/60">HOLD QUEUE</p>
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
                      <div className="h-4 w-3/4 rounded bg-slate-100 animate-pulse"></div>
                      <div className="mt-2 h-3 w-1/2 rounded bg-slate-50 animate-pulse"></div>
                    </div>
                  ) : holdApplications.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-amber-200 bg-amber-50/30 p-6 text-center">
                      <CheckCircle className="mx-auto h-8 w-8 text-amber-500/50 mb-2" />
                      <p className="text-amber-900/80 font-medium">No pending questions</p>
                      <p className="text-sm text-amber-900/50">You're all caught up!</p>
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
                            staggerChildren: 0.1
                          }
                        }
                      }}
                    >
                      {holdApplications.slice(0, 3).map((app, idx) => (
                        <motion.div
                          key={app.id}
                          className="group flex items-center justify-between rounded-xl bg-white p-4 shadow-sm border border-slate-100 transition-all hover:shadow-md hover:border-amber-200"
                          variants={{
                            hidden: { opacity: 0, y: 10 },
                            visible: {
                              opacity: 1,
                              y: 0,
                              transition: { type: 'spring', stiffness: 300, damping: 20 }
                            }
                          }}
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-amber-600">
                              <MessageCircle className="h-3.5 w-3.5" />
                            </div>
                            <div className="min-w-0">
                              <p className="truncate font-medium text-slate-900">{app.company}</p>
                              <p className="text-xs text-slate-500 truncate">
                                {app.hold_question?.slice(0, 50)}{app.hold_question && app.hold_question.length > 50 ? '...' : ''}
                              </p>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs font-medium text-amber-600 hover:bg-amber-50 hover:text-amber-700 transition-colors"
                            onClick={() => navigate("/app/applications")}
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
                    View all {holdApplications.length} holds
                  </Button>
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
            <Card className="relative overflow-hidden border-primary-200/50 bg-gradient-to-br from-primary-50/50 to-white" tone="glass">
              {/* Animated background elements */}
              <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-primary-500/5 blur-3xl"></div>
                <div className="absolute -left-10 -bottom-10 h-40 w-40 rounded-full bg-primary-500/5 blur-3xl"></div>
              </div>

              <div className="relative z-10 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-primary-900/60">CURRENT PLAN</p>
                    <p className="text-2xl font-bold text-slate-900">{status?.plan ?? "FREE"}</p>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-100 text-primary-600">
                    <Zap className="h-5 w-5" />
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Status</span>
                    <span className="font-medium text-emerald-600 capitalize">{status?.subscription_status ?? "active"}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Success Rate</span>
                    <span className="font-medium text-emerald-600">{stats.successRate}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Next Billing</span>
                    <div className="flex items-center text-slate-900">
                      <Clock className="h-3.5 w-3.5 mr-1 text-slate-400" />
                      <span>{status?.current_period_end ? formatDate(status.current_period_end, locale) : "No upcoming bill"}</span>
                    </div>
                  </div>
                </div>

                <Button
                  className="w-full mt-2 bg-slate-900 hover:bg-black text-white hover:shadow-lg transition-all"
                  onClick={() => navigate("/app/billing")}
                >
                  Upgrade Plan
                </Button>
              </div>
            </Card>
          </motion.div>

        </div>
      </div>
    </motion.div>
  );
}

export function JobsView() {
  // M-3: Debounced filter — local input value updates instantly, API filters update after 400ms
  const [localLocation, setLocalLocation] = useState("");
  const [filters, setFilters] = useState<JobFilters>({ location: "" });
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleLocationChange = useCallback((value: string) => {
    setLocalLocation(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setFilters(f => ({ ...f, location: value }));
    }, 400);
  }, []);

  const { jobs, isLoading, isFetching, hasNextPage, fetchNextPage, isFetchingNextPage } = useJobs(filters);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [swipeCount, setSwipeCount] = useState(0);
  const streakToasted = useRef<Set<number>>(new Set());
  const alertedMatches = useRef<Set<string>>(new Set());
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null);
  const swipeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const shouldReduceMotion = useReducedMotion();
  const [statusMessage, setStatusMessage] = useState("");
  const { celebrate: celebrateSession } = useSessionMilestone();
  // N-2: Use shared locale
  const locale = sharedLocale;
  const rtl = sharedRtl;

  // Undo functionality state
  const [lastSwipe, setLastSwipe] = useState<{
    jobId: string;
    direction: "ACCEPT" | "REJECT";
    previousIndex: number;
    timestamp: number;
  } | null>(null);
  const [isUndoing, setIsUndoing] = useState(false);
  const undoTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // H-1: Cleanup timeouts on unmount to prevent state updates on unmounted component
  useEffect(() => {
    return () => {
      if (swipeTimeoutRef.current) clearTimeout(swipeTimeoutRef.current);
      if (undoTimeoutRef.current) clearTimeout(undoTimeoutRef.current);
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);


  // N-5: Swipe milestones use [1, 5, 10, 25] – session milestone hook handles [50, 100]
  useEffect(() => {
    const milestones = [1, 5, 10, 25];
    milestones.forEach((m) => {
      if (swipeCount >= m && !streakToasted.current.has(m)) {
        streakToasted.current.add(m);
        pushToast({
          title: m === 1 ? "First swipe logged" : `🔥 ${m} swipes`,
          description: m === 1 ? "Matchmaker engaged—keep going for tailored leads." : "Momentum unlocked. Radar will adapt to your preferences.",
          tone: "success",
        });
      }
    });
  }, [swipeCount]);

  const currentJob = jobs[currentIndex];

  // Session milestone celebration
  useEffect(() => {
    celebrateSession(jobs.length);
  }, [jobs.length, celebrateSession]);

  useEffect(() => {
    if (currentJob?.id && currentJob.match_score && currentJob.match_score >= 80 && !alertedMatches.current.has(currentJob.id)) {
      alertedMatches.current.add(currentJob.id);
      pushToast({
        title: t("dashboard.matchAlert", locale),
        description: `${currentJob.title} @ ${currentJob.company}`,
        tone: "success",
      });
    }
  }, [currentJob, locale]);

  // Prefetch next page when near end
  useEffect(() => {
    if (hasNextPage && currentIndex >= jobs.length - 3 && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [currentIndex, fetchNextPage, hasNextPage, isFetchingNextPage, jobs.length]);

  const handleSwipe = async (direction: "ACCEPT" | "REJECT") => {
    if (!currentJob) return;

    // M-4: Capture job reference before any state updates to avoid stale closure
    const swipedJob = currentJob;

    setSwipeDirection(direction === "ACCEPT" ? "right" : "left");
    setStatusMessage(`${direction === "ACCEPT" ? "Accepting" : "Rejecting"} ${swipedJob.title} at ${swipedJob.company}`);

    // Store previous state for undo
    const previousIndex = currentIndex;

    try {
      // Record swipe decision with API
      await apiPost("applications", { job_id: swipedJob.id, decision: direction });

      // Store last swipe for undo functionality (10 second window)
      setLastSwipe({
        jobId: swipedJob.id,
        direction,
        previousIndex,
        timestamp: Date.now(),
      });

      // Clear undo state after 10 seconds (backend allows up to 10s for latency)
      if (undoTimeoutRef.current) clearTimeout(undoTimeoutRef.current);
      undoTimeoutRef.current = setTimeout(() => {
        setLastSwipe(null);
      }, 10_000);

      setCurrentIndex(prev => prev + 1);
      setSwipeCount(prev => prev + 1);

      if (direction === "ACCEPT") {
        fireSuccessConfetti();
        pushToast({
          title: "Match queued! 🚀",
          description: `AI is now tailoring your resume for ${swipedJob.company}. Undo available for 10s.`,
          tone: "success"
        });
        setStatusMessage(`Accepted ${swipedJob.title} at ${swipedJob.company}`);
      } else {
        pushToast({
          title: "Job passed",
          description: `Undo available for 10s.`,
          tone: "neutral"
        });
        setStatusMessage(`Rejected ${swipedJob.title} at ${swipedJob.company}`);
      }
    } catch (error) {
      // Revert UI state on API failure
      setSwipeDirection(null);
      pushToast({
        title: "Failed to record decision",
        description: "Please try again.",
        tone: "error"
      });
      setStatusMessage("Failed to record decision, please try again.");
    } finally {
      // Clear swipe direction after animation
      if (swipeTimeoutRef.current) clearTimeout(swipeTimeoutRef.current);
      swipeTimeoutRef.current = setTimeout(() => {
        setSwipeDirection(null);
        swipeTimeoutRef.current = null;
      }, shouldReduceMotion ? 0 : 500);
    }
  };

  // Undo last swipe action
  const handleUndoSwipe = async () => {
    if (!lastSwipe || isUndoing) return;

    setIsUndoing(true);

    try {
      // Call API to undo the swipe decision
      await apiPost(`applications/${lastSwipe.jobId}/undo`, {});

      // Restore previous state
      setCurrentIndex(lastSwipe.previousIndex);
      setSwipeCount(prev => Math.max(0, prev - 1));
      setLastSwipe(null);

      if (undoTimeoutRef.current) {
        clearTimeout(undoTimeoutRef.current);
        undoTimeoutRef.current = null;
      }

      pushToast({
        title: "Swipe undone",
        description: "You can now make a new decision on this job.",
        tone: "success"
      });
      setStatusMessage("Swipe undone - make a new decision");
    } catch (error) {
      pushToast({
        title: "Failed to undo",
        description: "The decision could not be undone.",
        tone: "error"
      });
    } finally {
      setIsUndoing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="space-y-4 w-full max-w-md">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse rounded-3xl border border-slate-200 bg-white p-6 space-y-3 shadow-sm">
              <div className="h-4 w-24 bg-slate-200 rounded" />
              <div className="h-6 w-3/4 bg-slate-200 rounded" />
              <div className="h-4 w-1/2 bg-slate-200 rounded" />
              <div className="h-20 w-full bg-slate-100 rounded-xl" />
              <div className="flex gap-2">
                <div className="h-10 w-24 bg-slate-200 rounded-full" />
                <div className="h-10 w-20 bg-slate-100 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (currentIndex >= jobs.length) {
    return (
      <Card tone="lagoon" className="flex flex-col items-center justify-center p-12 text-center border-dashed border-2">
        <div className="h-20 w-20 rounded-full bg-lagoon-100 flex items-center justify-center mb-6">
          <CheckCircle className="h-10 w-10 text-lagoon-600" />
        </div>
        <h2 className="text-3xl font-black text-slate-900 mb-4">{t("dashboard.sweepComplete", locale)}</h2>
        <p className="text-slate-500 max-w-md mx-auto mb-8 font-medium">
          {t("dashboard.noMatches", locale)}
        </p>
        <div className="flex flex-col gap-3 w-full max-w-sm">
          <Button variant="outline" onClick={() => setCurrentIndex(0)}>
            {t("dashboard.reviewSwipes", locale)}
          </Button>
          {hasNextPage && (
            <Button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
              {isFetchingNextPage ? t("dashboard.loadingMore", locale) : t("dashboard.loadMore", locale)}
            </Button>
          )}
          {!hasNextPage && (
            <Button variant="ghost" onClick={() => setFilters({ location: "", keywords: "" })}>
              {t("dashboard.resetFilters", locale)}
            </Button>
          )}
        </div>
      </Card>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-6" dir={rtl ? "rtl" : undefined}>
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">{t("dashboard.activeRadar", locale)}</h2>
          <p className="text-slate-500 font-medium">{t("dashboard.swipeRight", locale)}</p>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder={t("dashboard.filterPlaceholder", locale)}
            aria-label="Filter jobs by location"
            className="px-4 py-2 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 transition-all outline-none bg-white font-medium"
            value={localLocation}
            onChange={(e) => handleLocationChange(e.target.value)}
          />
          <Badge variant="primary" className="py-2 px-4 rounded-xl">
            {jobs.length - currentIndex} jobs remaining
          </Badge>
        </div>
      </div>

      <div
        className="relative h-[clamp(420px,60vh,640px)] w-full max-w-md mx-auto perspective-1000"
        role="region"
        aria-label="Job swipe deck"
      >
        <div className="sr-only" aria-live="polite">{statusMessage}</div>
        <AnimatePresence>
          {jobs.slice(currentIndex, currentIndex + 2).reverse().map((job, idx) => {
            const isTop = idx === (jobs.slice(currentIndex, currentIndex + 2).length - 1);
            return (
              <JobCard
                key={job.id}
                job={job}
                isTop={isTop}
                idx={idx}
                shouldReduceMotion={!!shouldReduceMotion}
                swipeDirection={swipeDirection}
                onSwipe={handleSwipe}
                locale={locale}
              >
                <Card
                  className="p-0 overflow-hidden shadow-2xl border-slate-100 h-full flex flex-col"
                  shadow="lift"
                >
                  <div className="bg-slate-900 p-8 text-white relative">
                    {job.match_score != null && (
                      <div className="absolute top-4 right-4 bg-primary-500 text-white text-[10px] font-black px-2 py-1 rounded flex items-center gap-1">
                        <Sparkles className="w-3 h-3" /> AI MATCH: {Math.round(job.match_score)}%
                      </div>
                    )}
                    <div className="flex items-center gap-4 mb-4">
                      <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
                        <Briefcase className="w-6 h-6 text-primary-400" />
                      </div>
                      <div>
                        <p className="text-primary-400 text-[10px] font-black uppercase tracking-widest">{job.location || 'Remote'}</p>
                        <h3 className="text-xl font-bold truncate leading-tight">{job.company}</h3>
                      </div>
                    </div>
                    <h2 className="text-2xl font-black leading-tight mb-2">{job.title}</h2>
                    <div className="flex gap-2">
                      <Badge className="bg-white/10 text-white border-transparent">{job.job_type || 'Full-time'}</Badge>
                      <Badge className="bg-primary-500/20 text-primary-400 border-transparent">
                        <DollarSign className="h-4 w-4" /> {job.salary_min ? `${formatCurrency(job.salary_min, locale)}+` : "Salary shared on match"}
                      </Badge>
                    </div>
                  </div>

                  <div className="p-8 flex-1 bg-white overflow-y-auto no-scrollbar">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Role Analysis</h4>
                    <p className="text-slate-600 font-medium leading-relaxed mb-6">
                      {job.description || "No description provided."}
                    </p>

                    {job.requirements && job.requirements.length > 0 && (
                      <div className="space-y-4">
                        {job.requirements.slice(0, 3).map((req: string, i: number) => (
                          <div key={i} className="flex items-start gap-3">
                            <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <CheckCircle className="w-3 h-3 text-emerald-600" />
                            </div>
                            <p className="text-sm text-slate-700 font-medium">{req}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="p-6 border-t border-slate-100 bg-slate-50 flex items-center justify-center gap-8">
                    {/* Undo button - only shown when there's a recent swipe */}
                    {lastSwipe && (
                      <button
                        type="button"
                        onClick={handleUndoSwipe}
                        disabled={isUndoing}
                        aria-label="Undo last swipe"
                        className="w-12 h-12 rounded-full bg-amber-100 border border-amber-200 flex items-center justify-center text-amber-600 hover:bg-amber-200 transition-all shadow-sm active:scale-90 focus:outline-none focus:ring-2 focus:ring-amber-200 disabled:opacity-50"
                      >
                        {isUndoing ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowUpRight className="w-5 h-5 rotate-[-135deg]" />}
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => handleSwipe("REJECT")}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleSwipe("REJECT"); } }}
                      aria-label="Reject job"
                      className="w-14 h-14 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-400 hover:text-red-500 hover:border-red-200 hover:bg-red-50 transition-all shadow-sm active:scale-90 focus:outline-none focus:ring-2 focus:ring-red-200"
                    >
                      <Zap className="w-6 h-6 transform rotate-180" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSwipe("ACCEPT")}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleSwipe("ACCEPT"); } }}
                      aria-label="Accept job"
                      className="w-16 h-16 rounded-full bg-primary-600 flex items-center justify-center text-white hover:bg-primary-500 transition-all shadow-xl shadow-primary-500/30 active:scale-90 ring-4 ring-primary-500/10 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-600"
                    >
                      <Rocket className="w-8 h-8" />
                    </button>
                  </div>
                </Card>
              </JobCard>
            );
          })}
        </AnimatePresence>
      </div>

      <div className="text-center">
        <p className="text-xs text-slate-400 font-bold uppercase tracking-[0.2em] mb-2">Instructions</p>
        <p className="text-sm text-slate-500 font-medium italic">
          Swipe RIGHT <Rocket className="inline w-3 h-3 mx-1" /> to initialize AI Application Engine. <br />
          Swipe LEFT <Zap className="inline w-3 h-3 mx-1 rotate-180" /> to discard match and move to next signal.
        </p>
      </div>

      {hasNextPage && (
        <div className="flex justify-center">
          <Button
            variant="outline"
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="flex items-center gap-2"
          >
            {isFetchingNextPage && <Loader2 className="w-4 h-4 animate-spin" />}
            {isFetchingNextPage ? t("dashboard.loadingMore", locale) : t("dashboard.loadMore", locale)}
          </Button>
        </div>
      )}
    </div>
  );
}



export function ApplicationsView() {
  const navigate = useNavigate();
  const { applications, isLoading } = useApplications();
  const [searchTerm, setSearchTerm] = useState("");
  const locale = sharedLocale; // N-2: shared locale
  // M-12: Client-side pagination
  const [page, setPage] = useState(0);

  const filteredApps = useMemo(
    () => applications.filter(app =>
      app.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.job_title.toLowerCase().includes(searchTerm.toLowerCase())
    ),
    [applications, searchTerm]
  );

  const totalPages = Math.max(1, Math.ceil(filteredApps.length / APPLICATIONS_PAGE_SIZE));
  const pagedApps = filteredApps.slice(page * APPLICATIONS_PAGE_SIZE, (page + 1) * APPLICATIONS_PAGE_SIZE);

  // Reset page when search changes
  useEffect(() => { setPage(0); }, [searchTerm]);

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <LoadingSpinner label="Decrypting application signals..." />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-4">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 md:gap-6">
        <div>
          <h2 className="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">Active Transmissions</h2>
          <p className="text-slate-500 font-medium">Monitoring {applications.length} automated application threads.</p>
        </div>
        <div className="relative w-full md:w-72">
          <input
            type="text"
            placeholder="Search company or title..."
            className="w-full px-10 py-3 rounded-2xl border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 transition-all outline-none bg-white font-medium shadow-sm"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        </div>
      </div>

      {/* Mobile Card List */}
      <div className="grid gap-3 md:hidden">
        {pagedApps.length === 0 ? (
          <Card className="flex flex-col items-center justify-center p-8 text-center" shadow="sm">
            <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center mb-4">
              <Radar className="w-8 h-8 text-slate-400 animate-pulse" />
            </div>
            <h3 className="text-lg font-black text-slate-900 mb-2">Signal Silence</h3>
            <p className="text-slate-500 font-medium mb-6 max-w-xs">
              {searchTerm ? "No transmissions found matching your encryption key." : "Your agent hasn't intercepted any opportunities yet."}
            </p>
            {!searchTerm && (
              <Button onClick={() => navigate('/app/jobs')} className="font-bold text-xs uppercase rounded-xl">
                Start Hunting <Rocket className="ml-2 w-4 h-4" />
              </Button>
            )}
          </Card>
        ) : (
          pagedApps.map((app) => (
            <Card key={app.id} className="p-4 border-slate-200" shadow="sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-sm shadow-sm">
                  {app.company.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-slate-900">{app.company}</p>
                  <p className="text-xs text-slate-500 font-medium truncate">{app.job_title}</p>
                </div>
                <Badge
                  variant={statusVariant(app.status)}
                  className="rounded-lg px-3 py-1 font-bold text-[10px] tracking-wider uppercase border-none"
                >
                  {app.status === 'APPLYING' && <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse mr-2" />}
                  {app.status}
                </Badge>
              </div>
              <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-slate-400" />
                  {app.last_activity ? formatDate(app.last_activity, locale) : 'Just now'}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="font-bold text-xs uppercase text-slate-400 hover:text-primary-600"
                  onClick={() => navigate(`/app/applications/${app.id}`)}
                >
                  Details <ArrowUpRight className="ml-1 w-3 h-3" />
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Desktop Table */}
      <Card className="p-0 overflow-hidden border-slate-200 hidden md:block" shadow="sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Candidate/Target</th>
                <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Status</th>
                <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Last Signal</th>
                <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {pagedApps.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-24 text-center">
                    <div className="flex flex-col items-center justify-center">
                      <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center mb-6 relative">
                        <Radar className="w-10 h-10 text-slate-300" />
                        <div className="absolute inset-0 rounded-full border border-slate-100 animate-ping opacity-20" />
                      </div>
                      <h3 className="text-xl font-black text-slate-900 mb-2">No Active Transmissions</h3>
                      <p className="text-slate-500 font-medium mb-8 max-w-sm">
                        {searchTerm ? "We couldn't locate any signals matching your search parameters." : "Your frequency is clear. Initialize a hunt to start intercepting job signals."}
                      </p>
                      {!searchTerm && (
                        <Button onClick={() => navigate('/app/jobs')} variant="primary" className="font-bold uppercase rounded-xl shadow-lg shadow-primary-500/20">
                          Initialize Hunt <Rocket className="ml-2 w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                pagedApps.map((app) => (
                  <tr key={app.id} className="group hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-sm shadow-sm">
                          {app.company.charAt(0)}
                        </div>
                        <div>
                          <p className="font-bold text-slate-900 group-hover:text-primary-600 transition-colors">{app.company}</p>
                          <p className="text-xs text-slate-500 font-medium">{app.job_title}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge
                        variant={statusVariant(app.status)}
                        className="rounded-lg px-3 py-1 font-bold text-[10px] tracking-wider uppercase border-none"
                      >
                        {app.status === 'APPLYING' && <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse mr-2" />}
                        {app.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-sm text-slate-600 font-medium">
                        <Clock className="w-4 h-4 text-slate-400" />
                        {app.last_activity ? formatDate(app.last_activity, locale) : 'Just now'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="font-bold text-xs uppercase text-slate-400 hover:text-primary-600"
                        onClick={() => navigate(`/app/applications/${app.id}`)}
                      >
                        Details <ArrowUpRight className="ml-1 w-3 h-3" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* M-12: Pagination controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-400 font-medium">
            Showing {page * APPLICATIONS_PAGE_SIZE + 1}–{Math.min((page + 1) * APPLICATIONS_PAGE_SIZE, filteredApps.length)} of {filteredApps.length}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage(p => Math.max(0, p - 1))}
              className="text-xs font-bold"
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages - 1}
              onClick={() => setPage(p => p + 1)}
              className="text-xs font-bold"
            >
              Next
            </Button>
          </div>
        </div>
      )}

      <div className="p-4 bg-primary-50 rounded-2xl border border-primary-100 flex items-center gap-4">
        <div className="h-10 w-10 rounded-full bg-white flex items-center justify-center text-primary-500 shadow-sm flex-shrink-0">
          <Zap className="h-5 w-5" />
        </div>
        <p className="text-sm text-primary-900 font-medium font-display leading-tight">
          Your AI agent is actively monitoring <span className="font-black">new job signals</span> across LinkedIn and Wellfound. New matches will appear in your Radar shortly.
        </p>
      </div>
    </div>
  );
}


export function HoldsView() {
  const { holdApplications, answerHold, snoozeApplication, isLoading, isSubmitting } = useApplications();
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const shouldReduceMotion = useReducedMotion();

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <LoadingSpinner label="Opening communication channels..." />
      </div>
    );
  }

  if (holdApplications.length === 0) {
    return (
      <Card tone="lagoon" className="flex flex-col items-center justify-center p-12 text-center border-dashed border-2">
        <div className="h-20 w-20 rounded-full bg-lagoon-100 flex items-center justify-center mb-6">
          <CheckCircle className="h-10 w-10 text-lagoon-600" />
        </div>
        <h2 className="text-3xl font-black text-slate-900 mb-4">Command Clear</h2>
        <p className="text-slate-500 max-w-md mx-auto mb-8 font-medium">
          The AI engine has 100% of the information it needs to continue all active hunts.
        </p>
      </Card>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-6 px-4 lg:px-0">
      <div>
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">HOLD Inbox</h2>
        <p className="text-slate-500 font-medium">Your AI agent needs clarification on these {holdApplications.length} threads.</p>
      </div>

      <div className="space-y-6">
        {holdApplications.map((app, idx) => (
          <motion.div
            key={app.id}
            initial={shouldReduceMotion ? undefined : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={shouldReduceMotion ? undefined : { delay: idx * 0.05, duration: 0.25 }}
          >
            <Card className="p-0 overflow-hidden border-slate-200" shadow="lift">
              <div className="bg-slate-50 border-b border-slate-200 p-3 sm:p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-xs">
                    {app.company.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">{app.company}</h3>
                    <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">{app.job_title}</p>
                  </div>
                </div>
                <Badge variant="warning" className="rounded-md font-bold text-[10px]">RESPONSE REQUIRED</Badge>
              </div>

              <div className="p-4 sm:p-6 space-y-6">
                <div className="bg-amber-50 rounded-2xl p-4 sm:p-6 border border-amber-100 relative">
                  <Quote className="absolute top-4 left-4 w-12 h-12 text-amber-200/50 -z-0" />
                  <p className="text-amber-900 font-medium leading-relaxed relative z-10">
                    "I've encountered a specific question on the portal: <span className="font-black italic">'{app.hold_question}'</span>. How should I proceed?"
                  </p>
                </div>

                <div className="space-y-4">
                  <textarea
                    className="w-full p-4 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 transition-all outline-none bg-white font-medium min-h-[100px]"
                    maxLength={5000}
                    placeholder="Type your response here... (e.g. Yes, I have 5 years experience with Kubernetes)"
                    value={answers[app.id] || ""}
                    onChange={(e) => setAnswers(prev => ({ ...prev, [app.id]: e.target.value }))}
                  />
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 sticky bottom-0 bg-white/90 backdrop-blur p-2 rounded-xl border border-slate-100">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-slate-400 hover:text-slate-600 font-bold text-xs uppercase"
                      disabled={isSubmitting(`snooze-${app.id}`)}
                      onClick={() => snoozeApplication(app.id)}
                    >
                      {isSubmitting(`snooze-${app.id}`) ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Clock className="w-4 h-4 mr-2" />} Snooze 24h
                    </Button>
                    <Button
                      disabled={!answers[app.id] || isSubmitting(app.id)}
                      onClick={() => answerHold(app.id, answers[app.id])}
                      className="bg-primary-600 hover:bg-primary-500 text-white font-bold rounded-xl px-6 sm:px-8 shadow-lg shadow-primary-500/20"
                    >
                      {isSubmitting(app.id) ? <Loader2 className="ml-2 w-4 h-4 animate-spin" /> : <Send className="ml-2 w-4 h-4" />}
                      {isSubmitting(app.id) ? "Sending..." : "Send Instructions"}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}


export function TeamView() {
  const navigate = useNavigate();
  const { status, plan } = useBilling();
  const isSolo = plan !== "TEAM";

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-6 px-4 lg:px-0">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Workspace</h2>
          <p className="text-slate-500 font-medium">Collaborate and manage shared hunting pipelines.</p>
        </div>
        <Button
          variant="outline"
          className="rounded-xl font-bold text-xs uppercase"
          onClick={() => navigate("/app/billing")}
        >
          {plan === "TEAM" ? "Add Seats" : "Upgrade to Team"}
        </Button>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
        <div className="lg:col-span-2">
          <Card className="p-0 overflow-hidden border-slate-200" shadow="sm">
            <div className="bg-slate-50 border-b border-slate-200 px-8 py-4">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Active Members</p>
            </div>
            <div className="divide-y divide-slate-100 italic">
              <div className="px-8 py-6 flex items-center justify-between bg-white">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-primary-500 flex items-center justify-center text-white font-bold">{status?.tenant_id?.slice(0, 2).toUpperCase() || 'ME'}</div>
                  <div>
                    <p className="font-bold text-slate-900">You (Owner)</p>
                    <p className="text-xs text-slate-500 font-medium">Workspace Owner</p>
                  </div>
                </div>
                <Badge variant="default" className="font-bold text-[10px] uppercase">Active</Badge>
              </div>
              {isSolo && (
                <div className="px-8 py-12 flex flex-col items-center justify-center text-center bg-slate-50/50">
                  <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-300 mb-4 border border-dashed border-slate-300">
                    <Users className="w-6 h-6" />
                  </div>
                  <h4 className="font-bold text-slate-900 mb-1">No teammates yet</h4>
                  <p className="text-sm text-slate-500 max-w-xs mx-auto mb-6">Upgrade to Agency to add up to 10 teammates and share your job pipeline.</p>
                  <Button size="sm" variant="primary" onClick={() => navigate("/app/billing")} className="font-bold text-xs uppercase px-6">Upgrade to Agency</Button>
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="p-8 border-slate-100 bg-primary-50/30" shadow="sm">
            <h3 className="text-lg font-black text-slate-900 mb-4 font-display">Shared Intelligence</h3>
            <ul className="space-y-4">
              {[
                "Unified Job Radar",
                "Shared Hold Inbox",
                "Collaborative Tailoring",
                "Centralized Billing"
              ].map(feat => (
                <li key={feat} className="flex items-start gap-3 text-sm text-slate-600 font-medium">
                  <div className="w-5 h-5 rounded-full bg-white flex items-center justify-center text-primary-500 shadow-sm flex-shrink-0">
                    <CheckCircle className="w-3 h-3" />
                  </div>
                  {feat}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}


export function BillingView() {
  const { status, plan, usage, upgrade, addSeats, manageBilling } = useBilling();
  const shouldReduceMotion = useReducedMotion();

  const usageUsed = usage?.monthly_used ?? 0;
  const usageLimit = usage?.monthly_limit ?? 100;
  const usagePercent = usage?.percentage_used ?? 0;
  const periodEnd = status?.current_period_end
    ? new Date(status.current_period_end).toLocaleDateString()
    : null;

  // N-8: Map constant tier config to runtime actions
  const actionMap: Record<string, (() => Promise<void>) | null> = { upgrade, addSeats };
  const tiers = BILLING_TIERS.map(t => ({
    ...t,
    action: t.actionKey ? actionMap[t.actionKey] ?? null : null,
  }));

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-6 px-4 lg:px-0">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Billing & Quota</h2>
          <p className="text-slate-500 font-medium">Manage your subscription and usage telemetry.</p>
        </div>
        <Badge variant="primary" className="py-2 px-4 rounded-xl font-bold">
          Plan: {plan || "FREE"}
        </Badge>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
        <div className="lg:col-span-2 space-y-6 lg:space-y-8">
          <Card className="p-6 lg:p-8 border-slate-200" shadow="sm">
            <h3 className="text-xl font-black text-slate-900 mb-6 font-display">Current Allocation</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-end">
                <p className="text-sm font-bold text-slate-500 uppercase">Monthly Volume</p>
                <p className="text-sm font-black text-slate-900">{usageUsed} / {usageLimit}</p>
              </div>
              <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                <motion.div
                  initial={shouldReduceMotion ? { width: `${Math.min(usagePercent, 100)}%` } : { width: 0 }}
                  animate={{ width: `${Math.min(usagePercent, 100)}%` }}
                  className="h-full bg-primary-500"
                />
              </div>
              <div className="flex justify-between text-xs text-slate-400 font-medium">
                <span>{usage?.monthly_remaining ?? usageLimit - usageUsed} remaining</span>
                {periodEnd && <span>Resets {periodEnd}</span>}
              </div>
            </div>
          </Card>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
            {tiers.map((tier) => (
              <Card
                key={tier.name}
                className={`p-6 flex flex-col items-center text-center transition-all hover:shadow-lg ${tier.recommended ? "border-primary-500 shadow-xl shadow-primary-500/10 ring-1 ring-primary-500" : "border-slate-100"
                  }`}
              >
                <h4 className="font-black text-slate-900 text-lg mb-1">{tier.name}</h4>
                <p className="text-3xl font-black text-slate-900 mb-6">{tier.price}</p>
                <ul className="space-y-3 mb-8 flex-1">
                  {tier.features.map(f => (
                    <li key={f} className="text-xs text-slate-500 font-medium flex items-center gap-2">
                      <CheckCircle className="w-3 h-3 text-emerald-500" /> {f}
                    </li>
                  ))}
                </ul>
                <Button
                  variant={tier.recommended ? "primary" : "outline"}
                  className="w-full font-bold text-xs uppercase rounded-xl"
                  disabled={tier.name === plan}
                  onClick={tier.action ? async () => { try { await tier.action!(); } catch (e) { pushToast({ title: "Checkout failed", description: (e as Error).message, tone: "error" }); } } : undefined}
                >
                  {tier.name === plan ? "Current" : "Upgrade"}
                </Button>
              </Card>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <Card className="bg-slate-900 text-white p-8 border-none overflow-hidden relative" shadow="lift">
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary-500/20 rounded-full blur-3xl" />
            <h3 className="text-xl font-bold mb-4 relative z-10">Subscription</h3>
            <div className="space-y-3 relative z-10">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">Status</span>
                <span className="capitalize font-medium">{status?.subscription_status ?? "active"}</span>
              </div>
              {status?.provider && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Provider</span>
                  <span className="capitalize font-medium">{status.provider}</span>
                </div>
              )}
              {periodEnd && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Renews</span>
                  <span className="font-medium">{periodEnd}</span>
                </div>
              )}
            </div>
            {plan !== "FREE" && (
              <Button
                variant="ghost"
                className="w-full mt-4 text-white/50 hover:text-white hover:bg-white/5 text-xs font-bold uppercase transition-colors"
                onClick={() => manageBilling()}
              >
                Manage Billing Portal <ArrowUpRight className="ml-2 w-3 h-3" />
              </Button>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}


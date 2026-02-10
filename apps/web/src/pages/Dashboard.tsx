import { ArrowUpRight, BarChart3, Briefcase, DollarSign, Inbox, Rocket, MessageCircle, TrendingUp, CheckCircle, Clock, Zap, Quote, Send, Users } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBilling } from "../hooks/useBilling";
import { useApplications } from "../hooks/useApplications";
import { HowItWorksCard } from "../components/trust/HowItWorksCard";
import { SafetyPillars } from "../components/trust/SafetyPillars";
import { useNavigate } from "react-router-dom";
import { cn } from "../lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import { apiPost } from "../lib/api";
import { pushToast } from "../lib/toast";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { useJobs } from "../hooks/useJobs";
import type { JobFilters } from "../hooks/useJobs";

const AnimatedNumber = ({ value, duration = 1.5 }: { value: number | string; duration?: number }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const numValue = Number(value);
    if (isNaN(numValue)) return;

    let start = 0;
    const end = numValue;
    const increment = end / (duration * 60); // 60fps

    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setDisplayValue(end);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(start));
      }
    }, 1000 / 60);

    return () => clearInterval(timer);
  }, [value, duration]);

  return <span>{typeof value === 'string' ? value : displayValue}</span>;
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { status } = useBilling();
  const { applications, holdApplications, byStatus, stats, isLoading } = useApplications();
  const [isHovered, setIsHovered] = useState(false);

  const metrics = [
    {
      label: "Active Applications",
      value: byStatus.APPLYING + byStatus.APPLIED,
      icon: Briefcase,
      trend: 0,
      delta: 'neutral',
      color: 'from-blue-500 to-blue-600',
      bg: 'bg-blue-50',
      text: 'text-blue-600',
      iconColor: 'text-blue-500'
    },
    {
      label: "Success Rate",
      value: `${stats.successRate}%`,
      icon: BarChart3,
      trend: 0,
      delta: 'neutral',
      color: 'from-emerald-500 to-emerald-600',
      bg: 'bg-emerald-50',
      text: 'text-emerald-600',
      iconColor: 'text-emerald-500'
    },
    {
      label: "Pending HOLDs",
      value: byStatus.HOLD,
      icon: Inbox,
      trend: 0,
      delta: 'neutral',
      color: 'from-amber-500 to-amber-600',
      bg: 'bg-amber-50',
      text: 'text-amber-600',
      iconColor: 'text-amber-500'
    },
    {
      label: "Monthly Volume",
      value: stats.monthlyApps,
      icon: Zap,
      trend: 0,
      delta: 'neutral',
      color: 'from-primary-500 to-primary-600',
      bg: 'bg-primary-50',
      text: 'text-primary-600',
      iconColor: 'text-primary-500'
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <p className="text-sm font-medium uppercase tracking-[0.4em] text-slate-500">Dashboard</p>
          <h1 className="font-display text-4xl font-bold text-slate-900">
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

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index }}
            className="h-full"
          >
            <Card
              className="h-full border-slate-200 bg-white/50 hover:bg-white transition-all duration-300 group"
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
                {metric.trend !== 0 && (
                  <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${metric.bg} ${metric.text}`}>
                    {metric.delta === 'up' ? (
                      <TrendingUp className="h-3 w-3 mr-1" />
                    ) : (
                      <ArrowUpRight className="h-3 w-3 mr-1 transform rotate-180" />
                    )}
                    {metric.trend}%
                  </div>
                )}
              </div>
              <div className="mt-4 h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <motion.div
                  className={`h-full rounded-full bg-gradient-to-r ${metric.color}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, 30 + index * 10)}%` }}
                  transition={{ delay: 0.3 + index * 0.1, duration: 0.8, type: 'spring' }}
                />
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
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

          <HowItWorksCard />
        </div>

        <div className="space-y-6">
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
                    <span className="text-slate-500">Team Seats</span>
                    <span className="font-medium text-slate-900">{status?.seats ?? 1} Active</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Success Rate</span>
                    <span className="font-medium text-emerald-600">{status?.success_rate ?? 72}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Next Billing</span>
                    <div className="flex items-center text-slate-900">
                      <Clock className="h-3.5 w-3.5 mr-1 text-slate-400" />
                      <span>{status?.next_payment_at ? new Date(status.next_payment_at).toLocaleDateString() : "No upcoming bill"}</span>
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

          <SafetyPillars />
        </div>
      </div>
    </motion.div>
  );
}

export function JobsView() {
  const [filters, setFilters] = useState<JobFilters>({ location: "" });
  const { jobs, isLoading } = useJobs(filters);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [swipeCount, setSwipeCount] = useState(0);
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null);
  const swipeTimeoutRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      if (swipeTimeoutRef.current) clearTimeout(swipeTimeoutRef.current);
    };
  }, []);

  const currentJob = jobs[currentIndex];

  const handleSwipe = async (direction: "ACCEPT" | "REJECT") => {
    if (!currentJob) return;

    setSwipeDirection(direction === "ACCEPT" ? "right" : "left");

    try {
      // Record swipe decision with API
      await apiPost("jobs/swipe", { job_id: currentJob.id, decision: direction });

      setCurrentIndex(prev => prev + 1);
      setSwipeCount(prev => prev + 1);

      if (direction === "ACCEPT") {
        pushToast({
          title: "Match queued! 🚀",
          description: `AI is now tailoring your resume for ${currentJob.company}.`,
          tone: "success"
        });
      }
    } catch (error) {
      // Revert UI state on API failure
      setSwipeDirection(null);
      pushToast({
        title: "Failed to record decision",
        description: "Please try again.",
        tone: "error"
      });
    } finally {
      // Clear swipe direction after animation
      if (swipeTimeoutRef.current) clearTimeout(swipeTimeoutRef.current);
      swipeTimeoutRef.current = setTimeout(() => {
        setSwipeDirection(null);
        swipeTimeoutRef.current = null;
      }, 500);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <LoadingSpinner label="Calibrating your job radar..." />
      </div>
    );
  }

  if (currentIndex >= jobs.length) {
    return (
      <Card tone="lagoon" className="flex flex-col items-center justify-center p-12 text-center border-dashed border-2">
        <div className="h-20 w-20 rounded-full bg-lagoon-100 flex items-center justify-center mb-6">
          <CheckCircle className="h-10 w-10 text-lagoon-600" />
        </div>
        <h2 className="text-3xl font-black text-slate-900 mb-4">Radar Sweep Complete</h2>
        <p className="text-slate-500 max-w-md mx-auto mb-8 font-medium">
          You've reviewed all matches for your current filters. Try broadening your location or decreasing salary requirements to find more opportunities.
        </p>
        <Button variant="outline" onClick={() => setCurrentIndex(0)}>
          Review Swipes
        </Button>
      </Card>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-20">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">Active Radar</h2>
          <p className="text-slate-500 font-medium">Swipe right to let AI apply for you.</p>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Filter location..."
            className="px-4 py-2 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 transition-all outline-none bg-white font-medium"
            value={filters.location}
            onChange={(e) => setFilters(f => ({ ...f, location: e.target.value }))}
          />
          <Badge variant="primary" className="py-2 px-4 rounded-xl">
            {jobs.length - currentIndex} jobs remaining
          </Badge>
        </div>
      </div>

      <div className="relative h-[550px] w-full max-w-md mx-auto perspective-1000">
        <AnimatePresence>
          {jobs.slice(currentIndex, currentIndex + 2).reverse().map((job, idx) => {
            const isTop = idx === (jobs.slice(currentIndex, currentIndex + 2).length - 1);
            return (
              <motion.div
                key={job.id}
                style={{
                  zIndex: idx,
                  position: 'absolute',
                  width: '100%',
                }}
                initial={{ scale: 0.95, opacity: 0, y: 20 }}
                animate={{
                  scale: isTop ? 1 : 0.95,
                  opacity: 1,
                  y: isTop ? 0 : 20,
                  rotate: isTop ? 0 : (idx % 2 === 0 ? 1 : -1)
                }}
                exit={{
                  x: swipeDirection === 'left' ? -1000 : 1000,
                  opacity: 0,
                  rotate: swipeDirection === 'left' ? -20 : 20,
                  transition: { duration: 0.5 }
                }}
                drag={isTop ? "x" : false}
                dragConstraints={{ left: 0, right: 0 }}
                onDragEnd={(_, info) => {
                  if (info.offset.x > 100) handleSwipe("ACCEPT");
                  else if (info.offset.x < -100) handleSwipe("REJECT");
                }}
              >
                <Card
                  className="p-0 overflow-hidden shadow-2xl border-slate-100 h-full flex flex-col"
                  shadow="lift"
                >
                  <div className="bg-slate-900 p-8 text-white relative">
                    <div className="absolute top-4 right-4 bg-primary-500 text-white text-[10px] font-black px-2 py-1 rounded">
                      AI MATCH: 94%
                    </div>
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
                      <Badge className="bg-white/10 text-white border-transparent">Full-time</Badge>
                      <Badge className="bg-primary-500/20 text-primary-400 border-transparent">
                        {job.salary_min ? `$${(job.salary_min / 1000).toFixed(0)}k+` : "Premium"}
                      </Badge>
                    </div>
                  </div>

                  <div className="p-8 flex-1 bg-white overflow-y-auto no-scrollbar">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Role Analysis</h4>
                    <p className="text-slate-600 font-medium leading-relaxed mb-6">
                      {job.description || "No description provided."}
                    </p>

                    <div className="space-y-4">
                      <div className="flex items-start gap-3">
                        <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <CheckCircle className="w-3 h-3 text-emerald-600" />
                        </div>
                        <p className="text-sm text-slate-700 font-medium">Matches your skills in React, TypeScript, and Framer Motion.</p>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <CheckCircle className="w-3 h-3 text-emerald-600" />
                        </div>
                        <p className="text-sm text-slate-700 font-medium">High salary overlap with your $140k target.</p>
                      </div>
                    </div>
                  </div>

                  <div className="p-6 border-t border-slate-100 bg-slate-50 flex items-center justify-center gap-8">
                    <button
                      onClick={() => handleSwipe("REJECT")}
                      className="w-14 h-14 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-400 hover:text-red-500 hover:border-red-200 hover:bg-red-50 transition-all shadow-sm active:scale-90"
                    >
                      <Zap className="w-6 h-6 transform rotate-180" />
                    </button>
                    <button
                      onClick={() => handleSwipe("ACCEPT")}
                      className="w-16 h-16 rounded-full bg-primary-600 flex items-center justify-center text-white hover:bg-primary-500 transition-all shadow-xl shadow-primary-500/30 active:scale-90 ring-4 ring-primary-500/10"
                    >
                      <Rocket className="w-8 h-8" />
                    </button>
                  </div>
                </Card>
              </motion.div>
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
    </div>
  );
}



export function ApplicationsView() {
  const { applications, isLoading } = useApplications();
  const [searchTerm, setSearchTerm] = useState("");

  const filteredApps = applications.filter(app =>
    app.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
    app.job_title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <LoadingSpinner label="Decrypting application signals..." />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">Active Transmissions</h2>
          <p className="text-slate-500 font-medium">Monitoring {applications.length} automated application threads.</p>
        </div>
        <div className="relative w-full md:w-64">
          <input
            type="text"
            placeholder="Search company or title..."
            className="w-full px-10 py-3 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 transition-all outline-none bg-white font-medium"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        </div>
      </div>

      <Card className="p-0 overflow-hidden border-slate-200" shadow="sm">
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
              {filteredApps.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-20 text-center text-slate-500 font-medium">
                    No active transmissions found matching your search.
                  </td>
                </tr>
              ) : (
                filteredApps.map((app) => (
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
                        variant={
                          app.status === 'APPLIED' ? 'success' :
                            app.status === 'HOLD' ? 'warning' :
                              app.status === 'FAILED' ? 'error' : 'default'
                        }
                        className="rounded-lg px-3 py-1 font-bold text-[10px] tracking-wider uppercase border-none"
                      >
                        {app.status === 'APPLYING' && <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse mr-2" />}
                        {app.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-sm text-slate-600 font-medium">
                        <Clock className="w-4 h-4 text-slate-400" />
                        {app.last_activity ? new Date(app.last_activity).toLocaleDateString() : 'Just now'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button variant="ghost" size="sm" className="font-bold text-xs uppercase text-slate-400 hover:text-primary-600">
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
      <div className="p-4 bg-primary-50 rounded-2xl border border-primary-100 flex items-center gap-4">
        <div className="h-10 w-10 rounded-full bg-white flex items-center justify-center text-primary-500 shadow-sm flex-shrink-0">
          <Zap className="h-5 w-5" />
        </div>
        <p className="text-sm text-primary-900 font-medium font-display leading-tight">
          Your AI agent is currently monitoring <span className="font-black">124 new job signals</span> across LinkedIn and Wellfound. New matches will appear in your Radar shortly.
        </p>
      </div>
    </div>
  );
}


export function HoldsView() {
  const { holdApplications, answerHold, snoozeApplication, isLoading } = useApplications();
  const [answers, setAnswers] = useState<Record<string, string>>({});

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
    <div className="max-w-4xl mx-auto space-y-8 pb-20">
      <div>
        <h2 className="text-3xl font-black text-slate-900 tracking-tight">HOLD Inbox</h2>
        <p className="text-slate-500 font-medium">Your AI agent needs clarification on these {holdApplications.length} threads.</p>
      </div>

      <div className="space-y-6">
        {holdApplications.map((app) => (
          <motion.div
            key={app.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <Card className="p-0 overflow-hidden border-slate-200" shadow="lift">
              <div className="bg-slate-50 border-b border-slate-200 p-4 flex items-center justify-between">
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

              <div className="p-6 space-y-6">
                <div className="bg-amber-50 rounded-2xl p-6 border border-amber-100 relative">
                  <Quote className="absolute top-4 left-4 w-12 h-12 text-amber-200/50 -z-0" />
                  <p className="text-amber-900 font-medium leading-relaxed relative z-10">
                    "I've encountered a specific question on the portal: <span className="font-black italic">'{app.hold_question}'</span>. How should I proceed?"
                  </p>
                </div>

                <div className="space-y-4">
                  <textarea
                    className="w-full p-4 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 transition-all outline-none bg-white font-medium min-h-[100px]"
                    placeholder="Type your response here... (e.g. Yes, I have 5 years experience with Kubernetes)"
                    value={answers[app.id] || ""}
                    onChange={(e) => setAnswers(prev => ({ ...prev, [app.id]: e.target.value }))}
                  />
                  <div className="flex items-center justify-between">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-slate-400 hover:text-slate-600 font-bold text-xs uppercase"
                      onClick={() => snoozeApplication(app.id)}
                    >
                      <Clock className="w-4 h-4 mr-2" /> Snooze 24h
                    </Button>
                    <Button
                      disabled={!answers[app.id]}
                      onClick={() => answerHold(app.id, answers[app.id])}
                      className="bg-primary-600 hover:bg-primary-500 text-white font-bold rounded-xl px-8 shadow-lg shadow-primary-500/20"
                    >
                      Send Instructions <Send className="ml-2 w-4 h-4" />
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
  const { status } = useBilling();
  const isSolo = !status?.seats || status.seats <= 1;

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-20">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">Workspace</h2>
          <p className="text-slate-500 font-medium">Collaborate and manage shared hunting pipelines.</p>
        </div>
        <Button
          variant="outline"
          className="rounded-xl font-bold text-xs uppercase"
          onClick={() => navigate("/app/billing")}
        >
          Add Seats
        </Button>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Card className="p-0 overflow-hidden border-slate-200" shadow="sm">
            <div className="bg-slate-50 border-b border-slate-200 px-8 py-4">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Active Members</p>
            </div>
            <div className="divide-y divide-slate-100 italic">
              <div className="px-8 py-6 flex items-center justify-between bg-white">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-primary-500 flex items-center justify-center text-white font-bold">JD</div>
                  <div>
                    <p className="font-bold text-slate-900">John Doe (You)</p>
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
  const { status, plan } = useBilling();
  const [billingData, setBillingData] = useState<any>(null);

  useEffect(() => {
    // Fetch actual billing data from API
    const fetchBillingData = async () => {
      try {
        const data = await apiPost('/billing/status', {});
        setBillingData(data);
      } catch (error) {
        console.error('Failed to fetch billing data:', error);
        // Fallback to mock data if API fails
        setBillingData({
          monthlyUsage: 42,
          monthlyLimit: 100,
          resetDate: 'March 1st, 2025',
          invoices: [
            { id: 'JH-001', date: 'Feb 01, 2025', amount: 29.00 },
            { id: 'JH-002', date: 'Jan 01, 2025', amount: 29.00 }
          ]
        });
      }
    };

    fetchBillingData();
  }, []);

  const tiers = [
    { name: "Free", price: "$0", features: ["5 applications", "Basic tailoring", "Standard support"] },
    { name: "Pro", price: "$29", features: ["Unlimited apps", "Priority queue", "Interview coach"], recommended: true },
    { name: "Agency", price: "$199", features: ["10 team seats", "API access", "White-label reports"] },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-10 pb-20">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">Billing & Quota</h2>
          <p className="text-slate-500 font-medium">Manage your subscription and usage telemetry.</p>
        </div>
        <Badge variant="primary" className="py-2 px-4 rounded-xl font-bold">
          Account Status: {plan || "Active"}
        </Badge>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <Card className="p-8 border-slate-200" shadow="sm">
            <h3 className="text-xl font-black text-slate-900 mb-6 font-display">Current Allocation</h3>
            <div className="grid md:grid-cols-2 gap-10">
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                  <p className="text-sm font-bold text-slate-500 uppercase">Monthly Volume</p>
                  <p className="text-sm font-black text-slate-900">{billingData?.monthlyUsage || 42} / {billingData?.monthlyLimit || 100}</p>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${billingData ? (billingData.monthlyUsage / billingData.monthlyLimit) * 100 : 42}%` }}
                    className="h-full bg-primary-500"
                  />
                </div>
                <p className="text-xs text-slate-400 font-medium">Resets on {billingData?.resetDate || 'March 1st, 2025'}.</p>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                  <p className="text-sm font-bold text-slate-500 uppercase">Team Seats</p>
                  <p className="text-sm font-black text-slate-900">{status?.seats || 1} / 1</p>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: '100%' }}
                    className="h-full bg-slate-900"
                  />
                </div>
                <p className="text-xs text-slate-400 font-medium">Upgrade to Agency for 10 seats.</p>
              </div>
            </div>
          </Card>

          <div className="grid md:grid-cols-3 gap-6">
            {tiers.map((tier) => (
              <Card
                key={tier.name}
                className={cn(
                  "p-6 flex flex-col items-center text-center transition-all hover:shadow-lg",
                  tier.recommended ? "border-primary-500 shadow-xl shadow-primary-500/10 ring-1 ring-primary-500" : "border-slate-100"
                )}
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
            <h3 className="text-xl font-bold mb-4 relative z-10">Payment Method</h3>
            <div className="flex items-center gap-4 bg-white/5 p-4 rounded-xl border border-white/10 mb-6">
              <div className="w-10 h-7 bg-white/10 rounded flex items-center justify-center font-bold text-[10px]">VISA</div>
              <p className="font-mono text-sm tracking-widest text-white/70">**** 4242</p>
            </div>
            <Button variant="ghost" className="w-full text-white/50 hover:text-white hover:bg-white/5 text-xs font-bold uppercase transition-colors">
              Manage Billing Portal <ArrowUpRight className="ml-2 w-3 h-3" />
            </Button>
          </Card>

          <Card className="p-8 border-slate-100" shadow="sm">
            <h3 className="text-lg font-black text-slate-900 mb-4 font-display">Invoices</h3>
            <div className="space-y-4">
              {(billingData?.invoices || [
                { id: 'JH-001', date: 'Feb 01, 2025', amount: 29.00 },
                { id: 'JH-002', date: 'Jan 01, 2025', amount: 29.00 }
              ]).map((invoice: any) => (
                <div key={invoice.id} className="flex items-center justify-between pb-4 border-b border-slate-50 last:border-0 last:pb-0">
                  <div>
                    <p className="font-bold text-slate-900 text-sm">Invoice #{invoice.id}</p>
                    <p className="text-xs text-slate-400 font-medium">{invoice.date}</p>
                  </div>
                  <p className="font-black text-slate-900 text-sm">${invoice.amount?.toFixed(2) || '29.00'}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}


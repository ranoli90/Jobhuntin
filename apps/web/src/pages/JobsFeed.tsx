import * as React from "react";
import { useMemo, useState, useEffect } from "react";
import { Filter, RefreshCcw, Briefcase, CheckCircle, ArrowRight, Eye, Zap } from "lucide-react";
import { JobCard } from "../components/Jobs/JobCard";
import { JobDetailDrawer } from "../components/Jobs/JobDetailDrawer";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { EmptyState } from "../components/ui/EmptyState";
import { useJobs, type JobPosting } from "../hooks/useJobs";
import { useSwipe } from "../hooks/useSwipe";
import { useApplications } from "../hooks/useApplications";
import { useJobMatchScores } from "../hooks/useJobMatchScores";
import { COPY } from "../copy";
import { useNavigate } from "react-router-dom";
import { useProfile } from "../hooks/useProfile";
import { motion, AnimatePresence } from "framer-motion";

export default function JobsFeed() {
  const navigate = useNavigate();
  const { profile, loading: profileLoading } = useProfile();
  const [filters, setFilters] = useState({
    location: profile?.preferences?.location || "",
    minSalary: profile?.preferences?.salary_min || 0,
    keywords: profile?.preferences?.role_type || ""
  });

  // Sync filters once profile loads
  React.useEffect(() => {
    if (profile?.preferences) {
      setFilters({
        location: profile.preferences.location || "",
        minSalary: profile.preferences.salary_min || 0,
        keywords: profile.preferences.role_type || ""
      });
    }
  }, [profile]);

  const { jobs, isLoading, refetch } = useJobs({
    location: filters.location || undefined,
    keywords: filters.keywords || undefined,
    minSalary: filters.minSalary || undefined,
  });
  const { applications, byStatus, isLoading: appsLoading } = useApplications();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedJob, setSelectedJob] = useState<JobPosting | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [savedJobs, setSavedJobs] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem("savedJobs");
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });

  const stack = useMemo(() => jobs.slice(currentIndex, currentIndex + 3), [jobs, currentIndex]);

  // AI Job Match Scoring
  const jobScoring = useJobMatchScores();

  // Set profile for scoring when it loads
  useEffect(() => {
    if (profile) {
      jobScoring.setProfile({
        preferences: profile.preferences,
        contact: profile.contact,
        headline: profile.headline,
        bio: profile.bio,
      });
    }
  }, [profile]);

  // Score jobs when they load
  useEffect(() => {
    if (jobs.length > 0 && profile) {
      // Score visible jobs first, then rest in background
      jobScoring.scoreJobs(stack);
      // Score next batch in background after a short delay
      const timer = setTimeout(() => {
        const nextBatch = jobs.slice(currentIndex + 3, currentIndex + 10);
        if (nextBatch.length > 0) {
          jobScoring.scoreJobs(nextBatch);
        }
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [jobs, currentIndex, profile]);

  const { handleSwipe, isSubmitting, lastResult, clearResult } = useSwipe({
    onComplete: () => setCurrentIndex((prev) => prev + 1),
  });

  const handleDecision = (decision: "ACCEPT" | "REJECT", job: JobPosting) => {
    if (isSubmitting) return;
    handleSwipe(job.id, decision);
  };

  const handleViewDetail = (job: JobPosting) => {
    setSelectedJob(job);
    setIsDrawerOpen(true);
  };

  const handleSaveJob = (jobId: string) => {
    setSavedJobs((prev) => {
      const next = new Set(prev);
      if (next.has(jobId)) {
        next.delete(jobId);
      } else {
        next.add(jobId);
      }
      try {
        localStorage.setItem("savedJobs", JSON.stringify([...next]));
      } catch {
        // ignore storage failures (private mode / quota)
      }
      return next;
    });
  };

  const showConfirmModal = lastResult?.decision === "ACCEPT" && lastResult?.success;

  // Get recently applied applications from API
  const recentAccepts = applications
    .filter((app) => app.status === "APPLIED")
    .slice(0, 5);

  return (
    <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] max-w-7xl mx-auto px-4 md:px-0">
      <section className="space-y-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary-500 animate-pulse" />
              <p className="text-[10px] uppercase font-black tracking-[0.4em] text-slate-400">Intelligence Stream</p>
            </div>
            <h1 className="font-display text-5xl font-black text-slate-900 tracking-tight leading-none italic">Hyper-Hunt.</h1>
            <p className="text-slate-500 font-medium">Auto-filtering millions of listings for your digital twin.</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()} className="self-start md:self-auto rounded-xl hover:bg-slate-100 text-slate-500 font-black h-12 px-6 border border-slate-200">
            <RefreshCcw className="mr-2 h-4 w-4" />
            SYNC STREAM
          </Button>
        </div>

        <Card tone="glass" shadow="lift" className="p-6 border-slate-200/60 overflow-hidden relative group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary-500/5 rounded-full blur-3xl" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
            <div className="space-y-2">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-1">Geospatial AOI</label>
              <div className="relative">
                <input
                  className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3.5 text-sm font-bold text-slate-900 outline-none focus:ring-4 focus:ring-primary-500/5 focus:border-primary-500 transition-all placeholder:text-slate-300"
                  placeholder="Remote / Tech Hubs"
                  value={filters.location}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFilters((prev) => ({ ...prev, location: e.target.value }))
                  }
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-1">Fiscal Baseline ($)</label>
              <input
                type="number"
                className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3.5 text-sm font-bold text-slate-900 outline-none focus:ring-4 focus:ring-primary-500/5 focus:border-primary-500 transition-all placeholder:text-slate-300"
                placeholder="120000"
                value={filters.minSalary || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFilters((prev) => ({ ...prev, minSalary: Number(e.target.value) }))
                }
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-1">Role Identifier</label>
              <input
                className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3.5 text-sm font-bold text-slate-900 outline-none focus:ring-4 focus:ring-primary-500/5 focus:border-primary-500 transition-all placeholder:text-slate-300"
                placeholder="Staff AI Engineer"
                value={filters.keywords}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFilters((prev) => ({ ...prev, keywords: e.target.value }))
                }
              />
            </div>
          </div>
          <div className="mt-6 pt-6 border-t border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <Filter className="h-4 w-4" />
              </div>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Active Filters Optimizing Feed</p>
            </div>
            <Badge variant="outline" className="text-[10px] font-black bg-primary-50 text-primary-600 border-primary-100 uppercase py-1 px-3">
              {jobs.length} Matches Found
            </Badge>
          </div>
        </Card>

        <div className="mt-10 relative h-[520px]">
          {isLoading ? <LoadingSpinner label="Loading jobs" className="pt-20" /> : null}
          {!isLoading && stack.length === 0 ? (
            <EmptyState
              title={COPY.empty.jobs.title}
              description={COPY.empty.jobs.description}
              actionLabel={COPY.empty.jobs.action}
              icon={<Filter className="h-8 w-8 text-brand-ink/40" />}
              onAction={() => refetch()}
            />
          ) : null}
          {stack.map((job, idx) => (
            <JobCard
              key={job.id}
              job={job}
              index={idx}
              isActive={idx === 0}
              onSwipe={(decision) => handleDecision(decision, job)}
              onViewDetail={() => handleViewDetail(job)}
              isSaved={savedJobs.has(job.id)}
              onSave={() => handleSaveJob(job.id)}
              matchScore={jobScoring.getScore(job.id)?.score}
              matchScoreLoading={jobScoring.isScoring(job.id)}
            />
          ))}
        </div>

        {/* Job Detail Drawer */}
        <JobDetailDrawer
          job={selectedJob}
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          onApply={() => selectedJob && handleDecision("ACCEPT", selectedJob)}
          onSave={() => selectedJob && handleSaveJob(selectedJob.id)}
          isSaved={selectedJob ? savedJobs.has(selectedJob.id) : false}
        />

        {/* Apply Confirmation Modal */}
        {showConfirmModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-6">
            <Card tone="lagoon" className="w-full max-w-md p-8 text-center shadow-2xl">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-brand-lagoon/20">
                <CheckCircle className="h-8 w-8 text-brand-lagoon" />
              </div>
              <h3 className="font-display text-2xl text-brand-ink">Application sent!</h3>
              <p className="mt-2 text-brand-ink/70">
                JobHuntin will handle the heavy lifting. We'll notify you when there's an update.
              </p>
              <div className="mt-6 space-y-3">
                <Button
                  variant="lagoon"
                  wobble
                  className="w-full gap-2"
                  onClick={() => {
                    clearResult();
                    navigate("/app/applications");
                  }}
                >
                  View in Applications
                  <ArrowRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  className="w-full"
                  onClick={() => clearResult()}
                >
                  Keep swiping
                </Button>
              </div>
            </Card>
          </div>
        )}
      </section>

      <section className="space-y-8">
        <div className="rounded-[2.5rem] bg-[#0d1117] text-white p-8 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 rounded-full blur-[80px]" />
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
              <div>
                <h2 className="font-display text-3xl font-black italic">Recent Accepts</h2>
                <p className="text-[10px] uppercase font-black tracking-[0.3em] text-white/40 mt-1">Autonomous Submission Queue</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-black text-primary-400 leading-none">{byStatus.APPLIED}</p>
                <p className="text-[10px] uppercase font-black tracking-widest text-white/30">Total Apps</p>
              </div>
            </div>

            <div className="space-y-4">
              {appsLoading ? (
                <div className="flex items-center gap-3 p-4 rounded-2xl bg-white/5 border border-white/5">
                  <LoadingSpinner size="sm" />
                  <span className="text-xs font-black text-white/40 uppercase tracking-widest">Scanning status...</span>
                </div>
              ) : recentAccepts.length > 0 ? (
                recentAccepts.map((app, i) => (
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    key={app.id}
                    className="flex items-center justify-between p-5 rounded-2xl bg-white/[0.03] border border-white/[0.05] hover:bg-white/[0.06] hover:border-white/[0.1] transition-all group/item"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-black text-white text-lg truncate group-hover/item:text-primary-400 transition-colors uppercase tracking-tight">{app.job_title}</p>
                      <p className="text-xs font-bold text-white/40 uppercase tracking-widest">{app.company}</p>
                    </div>
                    <div className="ml-4 h-10 w-10 rounded-xl bg-primary-500/20 text-primary-400 flex items-center justify-center group-hover/item:bg-primary-500 group-hover/item:text-white transition-all">
                      <ArrowRight className="h-5 w-5" />
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="p-8 text-center rounded-[2rem] border border-dashed border-white/10 bg-white/[0.02]">
                  <Briefcase className="h-10 w-10 text-white/10 mx-auto mb-4" />
                  <p className="text-xs font-black text-white/30 uppercase tracking-[0.2em]">{COPY.empty.applications.title}</p>
                  <p className="text-[10px] text-white/20 mt-2 font-medium max-w-[180px] mx-auto italic">Accept a job to initiate our high-velocity application engine.</p>
                </div>
              )}

              {!appsLoading && recentAccepts.length > 0 && (
                <Button variant="outline" size="sm" className="w-full h-14 rounded-2xl bg-white/[0.03] border-white/10 text-white/60 hover:text-white hover:bg-white/10 hover:border-white/20 font-black text-xs uppercase tracking-[0.2em] transition-all mt-6" onClick={() => navigate("/app/applications")}>
                  OPEN MISSION CONTROL
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Global Safety & Ops Cards */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-6 rounded-[2rem] bg-white border border-slate-200 shadow-sm group hover:shadow-md transition-all">
            <div className="h-10 w-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Eye className="h-5 w-5" />
            </div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Human-In-The-Loop</p>
            <p className="text-sm font-bold text-slate-900 leading-tight">Safety monitors active</p>
          </div>
          <div className="p-6 rounded-[2rem] bg-white border border-slate-200 shadow-sm group hover:shadow-md transition-all">
            <div className="h-10 w-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Zap className="h-5 w-5" />
            </div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Latent Sync</p>
            <p className="text-sm font-bold text-slate-900 leading-tight">&lt;800ms API Response</p>
          </div>
        </div>
      </section>
    </div>
  );
}

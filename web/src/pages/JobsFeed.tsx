import * as React from "react";
import { useMemo, useState } from "react";
import { Filter, RefreshCcw, Briefcase, CheckCircle, ArrowRight, Eye } from "lucide-react";
import { JobCard } from "../components/Jobs/JobCard";
import { JobDetailDrawer } from "../components/Jobs/JobDetailDrawer";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { EmptyState } from "../components/ui/EmptyState";
import { useJobs, type JobPosting } from "../hooks/useJobs";
import { useSwipe } from "../hooks/useSwipe";
import { useApplications } from "../hooks/useApplications";
import { COPY } from "../copy";
import { useNavigate } from "react-router-dom";

export default function JobsFeed() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({ location: "", minSalary: 0, keywords: "" });
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
    <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">Jobs feed</p>
            <h1 className="font-display text-4xl">Swipe with intent</h1>
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCcw className="mr-2 h-4 w-4" /> Refresh
          </Button>
        </div>

        <div className="mt-6 rounded-3xl border border-white/70 bg-white/70 p-5 shadow-inner">
          <div className="flex flex-wrap gap-4">
            <label className="flex flex-col text-xs uppercase tracking-[0.3em] text-brand-ink/60">
              Location
              <input
                className="mt-2 rounded-2xl border border-brand-ink/10 bg-brand-shell/70 px-4 py-2 text-base text-brand-ink"
                placeholder="Remote"
                value={filters.location}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFilters((prev) => ({ ...prev, location: e.target.value }))
                }
              />
            </label>
            <label className="flex flex-col text-xs uppercase tracking-[0.3em] text-brand-ink/60">
              Min salary
              <input
                type="number"
                className="mt-2 rounded-2xl border border-brand-ink/10 bg-brand-shell/70 px-4 py-2 text-base text-brand-ink"
                placeholder="90000"
                value={filters.minSalary || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFilters((prev) => ({ ...prev, minSalary: Number(e.target.value) }))
                }
              />
            </label>
            <label className="flex flex-col text-xs uppercase tracking-[0.3em] text-brand-ink/60">
              Keywords
              <input
                className="mt-2 rounded-2xl border border-brand-ink/10 bg-brand-shell/70 px-4 py-2 text-base text-brand-ink"
                placeholder="product design"
                value={filters.keywords}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFilters((prev) => ({ ...prev, keywords: e.target.value }))
                }
              />
            </label>
          </div>
          <div className="mt-4 text-sm text-brand-ink/70 flex items-center gap-2">
            <Filter className="h-4 w-4" /> Set filters to find your perfect match.
          </div>
        </div>

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

      <section className="rounded-3xl border border-white/80 bg-white/90 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.12)]">
        <h2 className="font-display text-2xl">Recent accepts</h2>
        <p className="text-sm text-brand-ink/70">
          {appsLoading ? "Loading..." : `${byStatus.APPLIED} applications submitted`}
        </p>
        <div className="mt-6 space-y-4">
          {appsLoading ? (
            <div className="text-sm text-brand-ink/50">Loading applications...</div>
          ) : recentAccepts.length > 0 ? (
            recentAccepts.map((app) => (
              <div key={app.id} className="rounded-2xl border border-brand-shell/80 bg-brand-shell/50 px-4 py-3">
                <p className="font-semibold text-brand-ink">{app.job_title}</p>
                <p className="text-sm text-brand-ink/70">{app.company}</p>
              </div>
            ))
          ) : (
            <EmptyState 
              title={COPY.empty.applications.title}
              description={COPY.empty.applications.description}
              actionLabel={COPY.empty.applications.action}
              icon={<Briefcase className="h-8 w-8 text-brand-ink/40" />}
              onAction={() => {}}
            />
          )}
          {!appsLoading && recentAccepts.length > 0 && (
            <Button variant="outline" size="sm" className="w-full" onClick={() => navigate("/app/applications")}>
              View all applications
            </Button>
          )}
        </div>
      </section>
    </div>
  );
}

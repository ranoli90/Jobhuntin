import { motion, useReducedMotion } from "framer-motion";
import { useJobs, type JobFilters } from "../../hooks/useJobs";
import { useProfile } from "../../hooks/useProfile";
import { Button } from "../../components/ui/Button";

import { Card } from "../../components/ui/Card";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { AnimatedNumber } from "./shared";
import { Check, X, Undo2, Radar } from "lucide-react";
import React, { useState, useCallback, useMemo } from "react";
import { Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { apiPost } from "../../lib/api";
import { pushToast } from "../../lib/toast";
import { telemetry } from "../../lib/telemetry";

interface SwipeRecord {
  direction: "accept" | "reject";
  timestamp: number;
}

export default function JobsView() {
  const queryClient = useQueryClient();
  const { profile } = useProfile();
  const filters: JobFilters = useMemo(
    () => ({
      location: profile?.preferences?.location,
      isRemote: profile?.preferences?.remote_only,
      minSalary: profile?.preferences?.salary_min,
    }),
    [profile?.preferences],
  );
  const { jobs, isLoading, refetch } = useJobs(filters);
  const shouldReduceMotion = useReducedMotion();

  // Local swipe state — tracks which jobs have been swiped and in which direction
  const [swipedJobs, setSwipedJobs] = useState<Map<string, SwipeRecord>>(
    new Map(),
  );
  // CRITICAL: Use Set instead of single string to prevent race conditions in concurrent swipes
  const [submittingSet, setSubmittingSet] = useState<Set<string>>(new Set());
  const [undoStack, setUndoStack] = useState<string[]>([]);
  const [lastAppliedForUndo, setLastAppliedForUndo] = useState<{
    jobId: string;
    until: number;
  } | null>(null);

  const appliedCount = useMemo(
    () =>
      [...swipedJobs.values()].filter((r) => r.direction === "accept").length,
    [swipedJobs],
  );
  const rejectedCount = useMemo(
    () =>
      [...swipedJobs.values()].filter((r) => r.direction === "reject").length,
    [swipedJobs],
  );

  // Filter out already-swiped jobs
  const visibleJobs = useMemo(
    () => jobs.filter((index) => !swipedJobs.has(index.id)),
    [jobs, swipedJobs],
  );

  const handleSwipe = useCallback(
    async (jobId: string, action: "accept" | "reject") => {
      // CRITICAL: Use Set to prevent race conditions - multiple swipes can't pass check
      if (swipedJobs.has(jobId) || submittingSet.has(jobId)) return;

      // Add to submitting set atomically
      setSubmittingSet((previous) => {
        const next = new Set(previous);
        next.add(jobId);
        return next;
      });

      // Optimistically record the swipe locally
      setSwipedJobs((previous) => {
        const next = new Map(previous);
        next.set(jobId, { direction: action, timestamp: Date.now() });
        return next;
      });
      if (action === "reject") {
        // MEDIUM: Limit undoStack size more aggressively to prevent memory growth
        setUndoStack((previous) => [...previous.slice(-2), jobId].slice(-3));
      }

      try {
        await apiPost(
          "/me/applications",
          {
            job_id: jobId,
            decision: action.toUpperCase(), // ACCEPT or REJECT
          },
          { headers: { "Idempotency-Key": crypto.randomUUID() } },
        );

        const job = jobs.find((index) => index.id === jobId);
        if (action === "accept") {
          telemetry.track("application_created", {
            job_id: jobId,
            company: job?.company,
            title: job?.title,
          });
          pushToast({ title: "Applied!", tone: "success" });
          setSwipeAnnouncement(
            `Applied to ${job?.title || "job"} at ${job?.company || "company"}`,
          );
          queryClient.invalidateQueries({ queryKey: ["applications"] });
          queryClient.invalidateQueries({ queryKey: ["jobs"] });
          setLastAppliedForUndo({ jobId, until: Date.now() + 10_000 });
        } else {
          setSwipeAnnouncement(
            `Skipped ${job?.title || "job"} at ${job?.company || "company"}`,
          );
        }

        // MEDIUM: Focus management after swipe - focus next card (with cleanup)
        const focusTimeoutId = setTimeout(() => {
          const nextCard = document.querySelector(
            '[role="article"][tabindex="0"]',
          ) as HTMLElement;
          if (nextCard) {
            nextCard.focus();
          }
        }, 100);
        // Store timeout ID for cleanup (handled by component cleanup)
        if (focusTimeoutReference.current)
          clearTimeout(focusTimeoutReference.current);
        focusTimeoutReference.current = focusTimeoutId;
      } catch (error) {
        const err = error as Error & {
          status?: number;
          response?: { status?: number };
        };
        const statusCode = err.status || err.response?.status;

        if (import.meta.env.DEV) console.error("[JobsView] Swipe failed:", err);

        // HIGH: Handle quota exceeded error (402 Payment Required)
        if (statusCode === 402) {
          pushToast({
            title: "Application limit reached",
            description:
              "You've reached your plan's application limit. Upgrade to continue applying.",
            tone: "error",
          });
          // Navigate to billing page after a delay (with cleanup)
          if (navigationTimeoutRef.current)
            clearTimeout(navigationTimeoutRef.current);
          navigationTimeoutRef.current = setTimeout(() => {
            // Check if component is still mounted before navigating
            if (navigationTimeoutRef.current) {
              window.location.href = "/app/billing";
            }
          }, 2000);
        } else {
          // Rollback the optimistic update for other errors
          setSwipedJobs((previous) => {
                        const next = new Map(previous);
            next.delete(jobId);
            return next;
          });
          pushToast({
            title: action === "accept" ? "Could not apply" : "Could not skip",
            description: err.message || "Please try again.",
            tone: "error",
          });
        }
      } finally {
        // Remove from submitting set
        setSubmittingSet((previous) => {
                    const next = new Set(previous);
          next.delete(jobId);
          return next;
        });
      }
    },
    [swipedJobs, submittingSet, jobs],
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (visibleJobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 px-6">
        <div className="w-12 h-12 rounded-full border-2 border-brand-border flex items-center justify-center mb-6">
          <Check className="w-5 h-5 text-brand-muted" />
        </div>
        <h3 className="text-lg font-semibold text-brand-text mb-1">
          You're all caught up
        </h3>
        <p className="text-sm text-brand-muted text-center max-w-xs mb-6">
          No new jobs matching your profile right now. We're continuously
          scanning and will notify you when we find something.
        </p>
        <Button
          variant="outline"
          className="text-sm font-medium rounded-xl px-5 py-2.5 border-brand-border text-brand-text hover:bg-brand-gray transition-colors"
          onClick={() => refetch()}
          aria-label="Refresh job listings"
        >
          Refresh
        </Button>
        <Link
          to="/app/job-alerts"
          className="text-sm font-medium text-brand-primary hover:text-brand-primaryHover mt-3"
        >
          Set up job alerts →
        </Link>
      </div>
    );
  }

  const topJob = visibleJobs[0];

  // HIGH: Add keyboard navigation for swiping (accessibility)
  React.useEffect(() => {
    if (!topJob || submittingSet.has(topJob.id)) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if focus is on the page (not in input fields)
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Arrow Right or 'D' key = Accept/Apply
      if (e.key === "ArrowRight" || e.key === "d" || e.key === "D") {
        e.preventDefault();
        handleSwipe(topJob.id, "accept");
      }
      // Arrow Left or 'A' key = Reject/Skip
      else if (e.key === "ArrowLeft" || e.key === "a" || e.key === "A") {
        e.preventDefault();
        handleSwipe(topJob.id, "reject");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [topJob, handleSwipe, submittingSet]);

  // MEDIUM: Add live region for screen reader announcements
  const [swipeAnnouncement, setSwipeAnnouncement] = React.useState<string>("");

  // MEDIUM: Refs for timeout cleanup
  const focusTimeoutReference = React.useRef<NodeJS.Timeout | null>(null);
  const navigationTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  // MEDIUM: Cleanup state and timeouts on unmount to prevent memory leaks
  React.useEffect(() => {
    if (!lastAppliedForUndo || lastAppliedForUndo.until <= Date.now()) return;
    const t = setTimeout(
      () => setLastAppliedForUndo(null),
      lastAppliedForUndo.until - Date.now(),
    );
    return () => clearTimeout(t);
  }, [lastAppliedForUndo]);

  React.useEffect(() => {
    return () => {
      setSwipedJobs(new Map());
      setSubmittingSet(new Set());
      setUndoStack([]);
      setLastAppliedForUndo(null);
      if (focusTimeoutReference.current)
        clearTimeout(focusTimeoutReference.current);
      if (navigationTimeoutRef.current)
        clearTimeout(navigationTimeoutRef.current);
    };
  }, []);

  return (
    <main className="space-y-6" aria-label="Job applications">
      {/* MEDIUM: Live region for screen reader announcements */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {swipeAnnouncement}
      </div>
      {/* HIGH: Keyboard shortcuts hint */}
      <div className="text-xs text-slate-500 dark:text-slate-400 text-center mb-2">
        <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-xs">
          ←
        </kbd>{" "}
        or{" "}
        <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-xs">
          A
        </kbd>{" "}
        to skip •{" "}
        <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-xs">
          →
        </kbd>{" "}
        or{" "}
        <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-xs">
          D
        </kbd>{" "}
        to apply
      </div>
      {/* MEDIUM: Skip link for accessibility */}
      <a
        href="#job-actions"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded"
      >
        Skip to job actions
      </a>
      <div id="job-card-description" className="sr-only">
        Swipe left to skip, right to apply. Use arrow keys or A/D keys for
        keyboard navigation.
      </div>
      <section aria-labelledby="stats-heading">
        <h2 id="stats-heading" className="sr-only">
          Application Statistics
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-4 flex flex-col items-center justify-center rounded-xl border-brand-border">
            <p className="text-sm font-medium text-brand-muted">Applied</p>
            <p
              className="text-3xl font-bold text-green-600"
              aria-label={`Applied to ${appliedCount} jobs`}
            >
              <AnimatedNumber value={appliedCount} />
            </p>
          </Card>
          <Card className="p-4 flex flex-col items-center justify-center rounded-xl border-brand-border">
            <p className="text-sm font-medium text-brand-muted">Skipped</p>
            <p
              className="text-3xl font-bold text-red-600"
              aria-label={`Skipped ${rejectedCount} jobs`}
            >
              <AnimatedNumber value={rejectedCount} />
            </p>
          </Card>
          <Card className="p-4 flex flex-col items-center justify-center rounded-xl border-brand-border">
            <p className="text-sm font-medium text-brand-muted">Remaining</p>
            <p
              className="text-3xl font-bold"
              aria-label={`${visibleJobs.length} jobs remaining`}
            >
              <AnimatedNumber value={visibleJobs.length} />
            </p>
          </Card>
        </div>
      </section>

      <section aria-labelledby="jobs-heading">
        <h2 id="jobs-heading" className="sr-only">
          Job Cards
        </h2>
        <div
          className="relative h-[450px] w-full max-w-md mx-auto"
          role="region"
          aria-label="Job card stack"
        >
          {/* MEDIUM: Limit visible jobs to prevent memory issues with large lists */}
          {/* Note: Only render top 3 for card stack UI, but limit underlying array */}
          {visibleJobs
            .slice(0, Math.min(3, visibleJobs.length))
            .map((job, index) => (
              <motion.div
                key={job.id}
                className="absolute w-full h-full"
                style={{ zIndex: 3 - index }}
                drag={index === 0 && !submittingSet.has(job.id) ? "x" : false}
                dragConstraints={{ left: -200, right: 200 }} // HIGH: Fix drag constraints to allow swiping
                onDragEnd={(_, info) => {
                  if (info.offset.x > 100) handleSwipe(job.id, "accept");
                  if (info.offset.x < -100) handleSwipe(job.id, "reject");
                }}
                initial={
                  shouldReduceMotion ? undefined : { scale: 0.95, opacity: 0 }
                }
                animate={{
                  scale: index === 0 ? 1 : 0.95 - index * 0.02,
                  opacity: 1,
                  y: index * 8,
                }}
                transition={{ duration: shouldReduceMotion ? 0.1 : 0.3 }}
              >
                <Card
                  className="w-full h-full p-6 flex flex-col justify-between bg-white border border-brand-border shadow-lg rounded-xl"
                  role="article"
                  aria-labelledby={`job-${job.id}-title`}
                  tabIndex={index === 0 ? 0 : -1} // HIGH: Make top card keyboard focusable
                  aria-label={`${job.title || "Job"} at ${job.company || "Company"}. Press Arrow Right or D to apply, Arrow Left or A to skip.`}
                  aria-describedby={
                    index === 0 ? "job-card-description" : undefined
                  }
                >
                  <div>
                    <h3
                      id={`job-${job.id}-title`}
                      className="text-xl font-bold text-brand-text"
                    >
                      {job.title}
                    </h3>
                    <p className="text-brand-text/80">
                      {job.company ?? "Company"}
                    </p>
                    <p className="text-sm text-brand-muted mt-1">
                      {job.location}
                    </p>
                    {job.match_score != undefined && (
                      <p
                        className="text-xs font-medium text-brand-primary mt-1"
                        title="Match score based on your profile (skills, location, salary fit)"
                      >
                        {Math.round(
                          Number(job.match_score) <= 1
                            ? Number(job.match_score) * 100
                            : Number(job.match_score),
                        )}
                        % match
                      </p>
                    )}
                  </div>
                  <p className="text-brand-text/90 text-sm line-clamp-4 my-3">
                    {job.description ?? "No description provided"}
                  </p>
                  <div className="flex justify-between items-center text-xs text-brand-muted">
                    <span>
                      {job.salary_min != undefined &&
                      job.salary_max != undefined
                        ? `$${(job.salary_min / 1000).toFixed(0)}k – $${(job.salary_max / 1000).toFixed(0)}k`
                        : job.salary_min == null
                        ? "Salary not specified"
                        : "From $" + (job.salary_min / 1000).toFixed(0) + "k"}
                    </span>
                    <span>{job.job_type || ""}</span>
                  </div>
                </Card>
              </motion.div>
            ))}
        </div>
      </section>

      <div
        id="job-actions"
        className="flex justify-center gap-4 mt-4"
        role="group"
        aria-label="Job actions"
      >
        <Button
          variant="outline"
          size="icon"
          className="w-16 h-16 rounded-full bg-red-100 text-red-600 hover:bg-red-200"
          onClick={() => handleSwipe(topJob.id, "reject")}
          disabled={!topJob || submittingSet.has(topJob.id)}
          aria-label="Skip this job"
          aria-describedby={`job-${topJob?.id}-title`}
        >
          <X className="w-8 h-8" aria-hidden="true" />
        </Button>
        {(undoStack.length > 0 ||
          (lastAppliedForUndo && lastAppliedForUndo.until > Date.now())) && (
          <Button
            variant="outline"
            size="icon"
            className="w-12 h-12 rounded-full bg-brand-gray text-brand-text hover:bg-brand-border/50"
            onClick={async () => {
              if (lastAppliedForUndo && lastAppliedForUndo.until > Date.now()) {
                try {
                  await apiPost(
                    `/me/applications/${lastAppliedForUndo.jobId}/undo`,
                    {},
                  );
                  setSwipedJobs((previous) => {
                    const next = new Map(previous);
                    next.delete(lastAppliedForUndo.jobId);
                    return next;
                  });
                  setLastAppliedForUndo(null);
                  queryClient.invalidateQueries({ queryKey: ["applications"] });
                  queryClient.invalidateQueries({ queryKey: ["jobs"] });
                  pushToast({ title: "Application undone", tone: "success" });
                } catch {
                  pushToast({
                    title: "Could not undo",
                    description: "Your application could not be reverted.",
                    tone: "error",
                  });
                }
              } else if (undoStack.length > 0) {
                const lastRejected = undoStack.at(-1);
                if (!lastRejected) return;
                const id = lastRejected;
                setUndoStack((previous) => previous.slice(0, -1));
                setSwipedJobs((previous) => {
                  const next = new Map(previous);
                  next.delete(id);
                  return next;
                });
              }
            }}
            aria-label={
              lastAppliedForUndo && lastAppliedForUndo.until > Date.now()
                ? "Undo last apply"
                : "Undo last skip"
            }
          >
            <Undo2 className="w-5 h-5" />
          </Button>
        )}
        <Button
          variant="outline"
          size="icon"
          className="w-16 h-16 rounded-full bg-green-100 text-green-600 hover:bg-green-200"
          onClick={() => handleSwipe(topJob.id, "accept")}
          disabled={!topJob || submittingSet.has(topJob.id)}
          aria-label="Apply to this job"
          aria-describedby={`job-${topJob?.id}-title`}
        >
          <Check className="w-8 h-8" aria-hidden="true" />
        </Button>
      </div>
    </main>
  );
}

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
import { apiPost } from "../../lib/api";
import { pushToast } from "../../lib/toast";

interface SwipeRecord {
    direction: "accept" | "reject";
    timestamp: number;
}

export default function JobsView() {
    const { profile } = useProfile();
    const filters: JobFilters = useMemo(() => ({
        location: profile?.preferences?.location,
        isRemote: profile?.preferences?.remote_only,
        minSalary: profile?.preferences?.salary_min,
    }), [profile?.preferences]);
    const { jobs, isLoading, refetch } = useJobs(filters);
    const shouldReduceMotion = useReducedMotion();

    // Local swipe state — tracks which jobs have been swiped and in which direction
    const [swipedJobs, setSwipedJobs] = useState<Map<string, SwipeRecord>>(new Map());
    const [submitting, setSubmitting] = useState<string | null>(null);
    const [undoStack, setUndoStack] = useState<string[]>([]);

    const appliedCount = useMemo(
        () => [...swipedJobs.values()].filter((r) => r.direction === "accept").length,
        [swipedJobs]
    );
    const rejectedCount = useMemo(
        () => [...swipedJobs.values()].filter((r) => r.direction === "reject").length,
        [swipedJobs]
    );

    // Filter out already-swiped jobs
    const visibleJobs = useMemo(
        () => jobs.filter((j) => !swipedJobs.has(j.id)),
        [jobs, swipedJobs]
    );

    const handleSwipe = useCallback(
        async (jobId: string, action: "accept" | "reject") => {
            if (swipedJobs.has(jobId) || submitting) return;
            setSubmitting(jobId);

            // Optimistically record the swipe locally
            setSwipedJobs((prev) => {
                const next = new Map(prev);
                next.set(jobId, { direction: action, timestamp: Date.now() });
                return next;
            });
            if (action === "reject") {
                setUndoStack((prev) => [...prev.slice(-4), jobId].slice(-5));
            }

            try {
                await apiPost("/me/applications", {
                    job_id: jobId,
                    decision: action.toUpperCase(), // ACCEPT or REJECT
                });

                if (action === "accept") {
                    pushToast({ title: "Applied!", tone: "success" });
                }
            } catch (error) {
                const err = error as Error;
                if (import.meta.env.DEV) console.error("[JobsView] Swipe failed:", err);
                // Rollback the optimistic update
                setSwipedJobs((prev) => {
                    const next = new Map(prev);
                    next.delete(jobId);
                    return next;
                });
                pushToast({
                    title: action === "accept" ? "Apply failed" : "Skip failed",
                    description: err.message || "Please try again",
                    tone: "error",
                });
            } finally {
                setSubmitting(null);
            }
        },
        [swipedJobs, submitting]
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
                <div className="w-12 h-12 rounded-full border-2 border-slate-200 flex items-center justify-center mb-6">
                    <Check className="w-5 h-5 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-1">
                    You're all caught up
                </h3>
                <p className="text-sm text-slate-500 text-center max-w-xs mb-6">
                    No new jobs matching your profile right now. We're continuously scanning and will notify you when we find something.
                </p>
                <Button
                    variant="outline"
                    className="text-sm font-medium rounded-lg px-5 py-2.5 border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
                    onClick={() => refetch()}
                    aria-label="Refresh job listings"
                >
                    Refresh
                </Button>
                <Link
                    to="/app/settings"
                    className="text-sm font-medium text-primary-600 hover:text-primary-700 mt-3"
                >
                    Set up job alerts →
                </Link>
            </div>
        );
    }

    const topJob = visibleJobs[0];

    return (
        <main className="space-y-6" aria-label="Job applications">
            <section aria-labelledby="stats-heading">
                <h2 id="stats-heading" className="sr-only">Application Statistics</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="p-4 flex flex-col items-center justify-center">
                    <p className="text-sm font-medium text-gray-500">Applied</p>
                    <p className="text-3xl font-bold text-green-600" aria-label={`Applied to ${appliedCount} jobs`}>
                        <AnimatedNumber value={appliedCount} />
                    </p>
                </Card>
                <Card className="p-4 flex flex-col items-center justify-center">
                    <p className="text-sm font-medium text-gray-500">Skipped</p>
                    <p className="text-3xl font-bold text-red-600" aria-label={`Skipped ${rejectedCount} jobs`}>
                        <AnimatedNumber value={rejectedCount} />
                    </p>
                </Card>
                <Card className="p-4 flex flex-col items-center justify-center">
                    <p className="text-sm font-medium text-gray-500">Remaining</p>
                    <p className="text-3xl font-bold" aria-label={`${visibleJobs.length} jobs remaining`}>
                        <AnimatedNumber value={visibleJobs.length} />
                    </p>
                </Card>
                </div>
            </section>

            <section aria-labelledby="jobs-heading">
                <h2 id="jobs-heading" className="sr-only">Job Cards</h2>
                <div className="relative h-[450px] w-full max-w-md mx-auto" role="region" aria-label="Job card stack">
                {visibleJobs.slice(0, 3).map((job, index) => (
                    <motion.div
                        key={job.id}
                        className="absolute w-full h-full"
                        style={{ zIndex: 3 - index }}
                        drag={index === 0 && !submitting ? "x" : false}
                        dragConstraints={{ left: 0, right: 0 }}
                        onDragEnd={(_, info) => {
                            if (info.offset.x > 100)
                                handleSwipe(job.id, "accept");
                            if (info.offset.x < -100)
                                handleSwipe(job.id, "reject");
                        }}
                        initial={shouldReduceMotion ? undefined : { scale: 0.95, opacity: 0 }}
                        animate={{
                            scale: index === 0 ? 1 : 0.95 - index * 0.02,
                            opacity: 1,
                            y: index * 8,
                        }}
                        transition={{ duration: shouldReduceMotion ? 0.1 : 0.3 }}
                    >
                        <Card className="w-full h-full p-6 flex flex-col justify-between bg-white shadow-lg rounded-xl" role="article" aria-labelledby={`job-${job.id}-title`}>
                            <div>
                                <h3 id={`job-${job.id}-title`} className="text-xl font-bold">{job.title}</h3>
                                <p className="text-gray-600">{job.company}</p>
                                <p className="text-sm text-gray-500 mt-1">{job.location}</p>
                                {job.match_score != null && (
                                    <p className="text-xs font-medium text-primary-600 mt-1">
                                        {Math.round(
                                            Number(job.match_score) <= 1
                                                ? Number(job.match_score) * 100
                                                : Number(job.match_score)
                                        )}% match
                                    </p>
                                )}
                            </div>
                            <p className="text-gray-700 text-sm line-clamp-4 my-3">
                                {job.description}
                            </p>
                            <div className="flex justify-between items-center text-xs text-gray-500">
                                <span>
                                    {job.salary_min && job.salary_max
                                        ? `$${(job.salary_min / 1000).toFixed(0)}k – $${(job.salary_max / 1000).toFixed(0)}k`
                                        : job.salary_min
                                            ? `From $${(job.salary_min / 1000).toFixed(0)}k`
                                            : ""}
                                </span>
                                <span>{job.job_type || ""}</span>
                            </div>
                        </Card>
                    </motion.div>
                ))}

            </div>
            </section>

            <div className="flex justify-center gap-4 mt-4" role="group" aria-label="Job actions">
                <Button
                    variant="outline"
                    size="icon"
                    className="w-16 h-16 rounded-full bg-red-100 text-red-600 hover:bg-red-200"
                    onClick={() => handleSwipe(topJob.id, "reject")}
                    disabled={!topJob || !!submitting}
                    aria-label="Skip this job"
                    aria-describedby={`job-${topJob?.id}-title`}
                >
                    <X className="w-8 h-8" aria-hidden="true" />
                </Button>
                {undoStack.length > 0 && (
                    <Button
                        variant="outline"
                        size="icon"
                        className="w-12 h-12 rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200"
                        onClick={() => {
                            const lastRejected = undoStack[undoStack.length - 1];
                            setUndoStack(prev => prev.slice(0, -1));
                            setSwipedJobs(prev => { const next = new Map(prev); next.delete(lastRejected); return next; });
                        }}
                        aria-label="Undo last skip"
                    >
                        <Undo2 className="w-5 h-5" />
                    </Button>
                )}
                <Button
                    variant="outline"
                    size="icon"
                    className="w-16 h-16 rounded-full bg-green-100 text-green-600 hover:bg-green-200"
                    onClick={() => handleSwipe(topJob.id, "accept")}
                    disabled={!topJob || !!submitting}
                    aria-label="Apply to this job"
                    aria-describedby={`job-${topJob?.id}-title`}
                >
                    <Check className="w-8 h-8" aria-hidden="true" />
                </Button>
            </div>
        </main>
    );
}

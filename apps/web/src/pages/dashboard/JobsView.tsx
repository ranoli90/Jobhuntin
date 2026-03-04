import { motion, useReducedMotion } from "framer-motion";
import { useJobs, type JobFilters } from "../../hooks/useJobs";
import { Button } from "../../components/ui/Button";

import { Card } from "../../components/ui/Card";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { AnimatedNumber } from "./shared";
import { Check, X, Undo2 } from "lucide-react";
import React, { useState, useCallback, useMemo } from "react";
import { apiPost } from "../../lib/api";
import { pushToast } from "../../lib/toast";

interface SwipeRecord {
    direction: "accept" | "reject";
    timestamp: number;
}

export default function JobsView() {
    // Empty filters — dashboard shows all matching jobs
    const filters: JobFilters = useMemo(() => ({}), []);
    const { jobs, isLoading, refetch } = useJobs(filters);
    const shouldReduceMotion = useReducedMotion();

    // Local swipe state — tracks which jobs have been swiped and in which direction
    const [swipedJobs, setSwipedJobs] = useState<Map<string, SwipeRecord>>(new Map());
    const [submitting, setSubmitting] = useState<string | null>(null);

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

            try {
                await apiPost("/applications", {
                    job_id: jobId,
                    decision: action.toUpperCase(), // ACCEPT or REJECT
                });

                if (action === "accept") {
                    pushToast({ title: "Applied!", tone: "success" });
                }
            } catch (error) {
                const err = error as Error;
                console.error("[JobsView] Swipe failed:", err);
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
            <div className="text-center p-8 bg-gray-50 rounded-lg">
                <h3 className="text-2xl font-bold text-gray-800">You're all caught up!</h3>
                <p className="text-gray-600 mt-2">
                    There are no new jobs matching your profile right now. Check back later!
                </p>
                <Button className="mt-4" onClick={() => refetch()}>
                    Refresh Jobs
                </Button>
            </div>
        );
    }

    const topJob = visibleJobs[0];

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="p-4 flex flex-col items-center justify-center">
                    <p className="text-sm font-medium text-gray-500">Applied</p>
                    <p className="text-3xl font-bold text-green-600">
                        <AnimatedNumber value={appliedCount} />
                    </p>
                </Card>
                <Card className="p-4 flex flex-col items-center justify-center">
                    <p className="text-sm font-medium text-gray-500">Skipped</p>
                    <p className="text-3xl font-bold text-red-600">
                        <AnimatedNumber value={rejectedCount} />
                    </p>
                </Card>
                <Card className="p-4 flex flex-col items-center justify-center">
                    <p className="text-sm font-medium text-gray-500">Remaining</p>
                    <p className="text-3xl font-bold">
                        <AnimatedNumber value={visibleJobs.length} />
                    </p>
                </Card>
            </div>

            <div className="relative h-[450px] w-full max-w-md mx-auto">
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
                        <Card className="w-full h-full p-6 flex flex-col justify-between bg-white shadow-lg rounded-xl">
                            <div>
                                <h3 className="text-xl font-bold">{job.title}</h3>
                                <p className="text-gray-600">{job.company}</p>
                                <p className="text-sm text-gray-500 mt-1">{job.location}</p>
                                {job.match_score != null && (
                                    <p className="text-xs font-medium text-primary-600 mt-1">
                                        {Math.round(job.match_score * 100)}% match
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

            <div className="flex justify-center gap-4 mt-4">
                <Button
                    variant="outline"
                    size="icon"
                    className="w-16 h-16 rounded-full bg-red-100 text-red-600 hover:bg-red-200"
                    onClick={() => handleSwipe(topJob.id, "reject")}
                    disabled={!topJob || !!submitting}
                >
                    <X className="w-8 h-8" />
                </Button>
                <Button
                    variant="outline"
                    size="icon"
                    className="w-16 h-16 rounded-full bg-green-100 text-green-600 hover:bg-green-200"
                    onClick={() => handleSwipe(topJob.id, "accept")}
                    disabled={!topJob || !!submitting}
                >
                    <Check className="w-8 h-8" />
                </Button>
            </div>
        </div>
    );
}

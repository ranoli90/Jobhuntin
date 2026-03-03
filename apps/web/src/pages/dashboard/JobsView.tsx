import { motion, useReducedMotion } from "framer-motion";
import { useJobs } from "../../hooks/useJobs";
import { Button } from "../../components/ui/Button";
import { SwipeInstruction } from "../../components/ui/SwipeInstruction";
import { Card } from "../../components/ui/Card";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { AnimatedNumber } from "./shared";
import { Check, X } from "lucide-react";
import React from "react";

export default function JobsView() {
    const { jobs, recordInteraction, isLoading, swipedJobs, appliedCount, rejectedCount, outOfJobs } = useJobs();
    const shouldReduceMotion = useReducedMotion();

    const handleSwipe = (jobId: string, action: "accept" | "reject") => {
        if (swipedJobs.has(jobId)) return;
        recordInteraction(jobId, action);
    };

    if (isLoading) {
        return <div className="flex items-center justify-center h-64"><LoadingSpinner /></div>;
    }

    if (outOfJobs) {
        return (
            <div className="text-center p-8 bg-gray-50 rounded-lg">
                <h3 className="text-2xl font-bold text-gray-800">You're all caught up!</h3>
                <p className="text-gray-600 mt-2">There are no new jobs matching your profile right now. Check back later!</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="p-4 flex flex-col items-center justify-center">
                    <p className="text-sm font-medium text-gray-500">Applied</p>
                    <p className="text-3xl font-bold text-green-600"><AnimatedNumber value={appliedCount} /></p>
                </Card>
                <Card className="p-4 flex flex-col items-center justify-center">
                    <p className="text-sm font-medium text-gray-500">Rejected</p>
                    <p className="text-3xl font-bold text-red-600"><AnimatedNumber value={rejectedCount} /></p>
                </Card>
                <Card className="p-4 flex flex-col items-center justify-center">
                    <p className="text-sm font-medium text-gray-500">Total Swipes</p>
                    <p className="text-3xl font-bold"><AnimatedNumber value={appliedCount + rejectedCount} /></p>
                </Card>
            </div>

            <div className="relative h-[450px] w-full max-w-md mx-auto">
                {jobs.map((job, index) => (
                    <motion.div
                        key={job.id}
                        className="absolute w-full h-full"
                        style={{ zIndex: jobs.length - index }}
                        drag={!swipedJobs.has(job.id) ? "x" : false}
                        dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
                        onDragEnd={(_, info) => {
                            if (info.offset.x > 100) handleSwipe(job.id, "accept");
                            if (info.offset.x < -100) handleSwipe(job.id, "reject");
                        }}
                        animate={{
                            x: swipedJobs.has(job.id) ? (job.id.includes("accept") ? 500 : -500) : 0,
                            opacity: swipedJobs.has(job.id) ? 0 : 1,
                            transition: { duration: shouldReduceMotion ? 0.1 : 0.5 }
                        }}
                    >
                        <Card className="w-full h-full p-6 flex flex-col justify-between bg-white shadow-lg rounded-xl">
                            <div>
                                <h3 className="text-xl font-bold">{job.title}</h3>
                                <p className="text-gray-600">{job.company}</p>
                                <p className="text-sm text-gray-500 mt-1">{job.location}</p>
                            </div>
                            <p className="text-gray-700 text-sm line-clamp-4">{job.description}</p>
                            <div className="flex justify-between items-center text-xs text-gray-500">
                                <span>{job.salary}</span>
                                <span>{job.type}</span>
                            </div>
                        </Card>
                    </motion.div>
                ))}
                {!outOfJobs && <SwipeInstruction />}
            </div>
            <div className="flex justify-center gap-4 mt-4">
                <Button variant="outline" size="icon" className="w-16 h-16 rounded-full bg-red-100 text-red-600 hover:bg-red-200" onClick={() => handleSwipe(jobs[0]?.id, "reject")} disabled={!jobs[0] || swipedJobs.has(jobs[0]?.id)}>
                    <X className="w-8 h-8" />
                </Button>
                <Button variant="outline" size="icon" className="w-16 h-16 rounded-full bg-green-100 text-green-600 hover:bg-green-200" onClick={() => handleSwipe(jobs[0]?.id, "accept")} disabled={!jobs[0] || swipedJobs.has(jobs[0]?.id)}>
                    <Check className="w-8 h-8" />
                </Button>
            </div>
        </div>
    );
}

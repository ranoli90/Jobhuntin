import * as React from "react";
import { cn } from "../../lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> { }

export function Skeleton({ className, ...props }: SkeletonProps) {
    return (
        <div
            role="status"
            aria-label="Loading"
            aria-busy="true"
            className={cn("animate-pulse rounded-md bg-slate-200/60", className)}
            {...props}
        />
    );
}

export function OnboardingSkeleton() {
    return (
        <div className="space-y-6 w-full px-1">
            <div className="flex items-center gap-4 border-b border-slate-100 pb-6">
                <Skeleton className="h-12 w-16 rounded-[1.5rem]" />
                <div className="space-y-2 flex-1">
                    <Skeleton className="h-8 w-1/2" />
                    <Skeleton className="h-4 w-1/3" />
                </div>
            </div>

            <div className="grid gap-6">
                <div className="space-y-3">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-12 w-full rounded-2xl" />
                </div>
                <div className="space-y-3">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-12 w-full rounded-2xl" />
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                    <Skeleton className="h-24 w-full rounded-2xl" />
                    <Skeleton className="h-24 w-full rounded-2xl" />
                </div>
            </div>
        </div>
    );
}

// Resume Step Skeleton
export function ResumeStepSkeleton() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="space-y-2">
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
            </div>

            {/* Upload Area */}
            <div className="relative">
                <div className="border-2 border-dashed border-slate-200 rounded-2xl p-8 md:p-12 bg-slate-50">
                    <div className="flex flex-col items-center gap-4">
                        <Skeleton className="w-16 h-16 rounded-2xl" />
                        <div className="text-center space-y-2">
                            <Skeleton className="h-6 w-48 mx-auto" />
                            <Skeleton className="h-4 w-64 mx-auto" />
                        </div>
                        <Skeleton className="h-12 w-32 rounded-xl" />
                    </div>
                </div>
                {/* Upload progress overlay */}
                <div className="absolute inset-0 bg-white/80 backdrop-blur-[1px] rounded-2xl flex flex-col items-center justify-center gap-3 z-10">
                    <div className="w-32 h-1 bg-slate-100 rounded-full overflow-hidden">
                        <Skeleton className="h-full w-full" />
                    </div>
                    <Skeleton className="h-4 w-24" />
                </div>
            </div>

            {/* LinkedIn Input */}
            <div className="space-y-2">
                <div className="flex items-center gap-2">
                    <Skeleton className="h-px flex-1" />
                    <Skeleton className="h-4 w-8" />
                    <Skeleton className="h-px flex-1" />
                </div>
                <Skeleton className="h-12 w-full rounded-xl" />
            </div>

            {/* Parsed Preview */}
            <div className="rounded-2xl border border-slate-200 bg-white shadow-lg overflow-hidden">
                <div className="bg-gradient-to-r p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Skeleton className="w-8 h-8 rounded-lg" />
                            <div className="space-y-1">
                                <Skeleton className="h-4 w-48" />
                                <Skeleton className="h-3 w-32" />
                            </div>
                        </div>
                        <Skeleton className="w-12 h-6 rounded-full" />
                    </div>
                </div>
                <div className="p-4 space-y-3">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <div className="pt-3 border-t border-slate-100">
                        <Skeleton className="h-4 w-24 mb-2" />
                        <div className="flex flex-wrap gap-2">
                            {Array.from({ length: 6 }).map((_, i) => (
                                <Skeleton key={`skill-skeleton-${i}`} className="h-6 w-16 rounded-full" />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Preferences Step Skeleton
export function PreferencesStepSkeleton() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="space-y-2">
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
            </div>

            {/* AI Suggestions */}
            <div className="grid md:grid-cols-2 gap-4">
                {Array.from({ length: 2 }).map((_, i) => (
                    <div key={`ai-suggestion-${i}`} className="rounded-xl border border-slate-200 bg-white p-4">
                        <div className="flex items-center gap-3 mb-3">
                            <Skeleton className="w-8 h-8 rounded-lg" />
                            <div className="flex-1">
                                <Skeleton className="h-4 w-32 mb-1" />
                                <Skeleton className="h-3 w-24" />
                            </div>
                        </div>
                        <div className="space-y-2">
                            {Array.from({ length: 3 }).map((_, j) => (
                                <Skeleton key={`ai-suggestion-${i}-item-${j}`} className="h-4 w-full" />
                            ))}
                        </div>
                        <div className="flex gap-2 mt-3">
                            <Skeleton className="h-8 w-20 rounded-lg" />
                            <Skeleton className="h-8 w-16 rounded-lg" />
                        </div>
                    </div>
                ))}
            </div>

            {/* Form Fields */}
            <div className="space-y-4">
                <div className="space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-12 w-full rounded-xl" />
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-12 w-full rounded-xl" />
                    </div>
                    <div className="space-y-2">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-12 w-full rounded-xl" />
                    </div>
                </div>
            </div>

            {/* Toggle Options */}
            <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                    <div key={`preference-${i}`} className="flex items-center gap-4 p-4 rounded-xl border border-slate-100">
                        <Skeleton className="w-8 h-8 rounded-lg" />
                        <div className="flex-1">
                            <Skeleton className="h-4 w-32 mb-1" />
                            <Skeleton className="h-3 w-48" />
                        </div>
                        <Skeleton className="w-12 h-6 rounded-full" />
                    </div>
                ))}
            </div>
        </div>
    );
}

// Skill Review Step Skeleton
export function SkillReviewStepSkeleton() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="space-y-2">
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
            </div>

            {/* Skills Grid */}
            <div className="grid gap-3">
                {Array.from({ length: 6 }).map((_, i) => (
                    <div key={`skill-review-${i}`} className="rounded-xl border border-slate-200 bg-white p-4">
                        <div className="flex items-center gap-3">
                            <Skeleton className="w-10 h-10 rounded-lg" />
                            <div className="flex-1">
                                <Skeleton className="h-5 w-32 mb-1" />
                                <Skeleton className="h-4 w-48 mb-2" />
                                <div className="flex items-center gap-2">
                                    <Skeleton className="h-2 w-24 rounded-full" />
                                    <Skeleton className="h-4 w-16" />
                                </div>
                            </div>
                            <Skeleton className="w-8 h-8 rounded-lg" />
                        </div>
                    </div>
                ))}
            </div>

            {/* Add Skills Section */}
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6">
                <div className="text-center space-y-3">
                    <Skeleton className="w-12 h-12 rounded-lg mx-auto" />
                    <Skeleton className="h-5 w-48 mx-auto" />
                    <Skeleton className="h-4 w-64 mx-auto" />
                    <Skeleton className="h-10 w-32 rounded-xl mx-auto" />
                </div>
            </div>
        </div>
    );
}

// Work Style Step Skeleton
export function WorkStyleStepSkeleton() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="space-y-2">
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
            </div>

            {/* Questions */}
            <div className="space-y-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="rounded-xl border border-slate-200 bg-white p-6">
                        <div className="space-y-4">
                            <div className="flex items-center gap-2">
                                <Skeleton className="w-6 h-6 rounded-full" />
                                <Skeleton className="h-5 w-3/4" />
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {Array.from({ length: 4 }).map((_, j) => (
                                    <div key={j} className="flex items-center gap-3 p-3 rounded-lg border border-slate-100">
                                        <Skeleton className="w-4 h-4 rounded-full" />
                                        <Skeleton className="h-4 w-full" />
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export function JobCardSkeleton() {
    return (
        <div className="w-full max-w-md mx-auto">
            <div className="bg-slate-900 p-8 text-white rounded-2xl shadow-2xl border-slate-100 h-full flex flex-col">
                <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
                        <Skeleton className="h-6 w-6 rounded" />
                    </div>
                    <div className="flex-1">
                        <Skeleton className="h-4 w-32 mb-2" />
                        <Skeleton className="h-6 w-48" />
                    </div>
                </div>
                <div className="space-y-3">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-20 w-full rounded-xl" />
                </div>
                <div className="flex gap-2 mt-4">
                    <Skeleton className="h-10 w-24 rounded-full" />
                    <Skeleton className="h-10 w-20 rounded-full" />
                </div>
            </div>
        </div>
    );
}

export function ApplicationCardSkeleton() {
    return (
        <div className="p-4 rounded-2xl border border-slate-200 bg-white animate-pulse">
            <div className="flex items-center gap-3">
                <Skeleton className="w-10 h-10 rounded-lg" />
                <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-3 w-16" />
                </div>
                <Skeleton className="h-6 w-16 rounded-lg" />
            </div>
            <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Skeleton className="w-4 h-4 rounded" />
                    <Skeleton className="h-4 w-20" />
                </div>
                <Skeleton className="h-8 w-16 rounded-lg" />
            </div>
        </div>
    );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="space-y-3">
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="p-4 border border-slate-200 rounded-lg animate-pulse">
                    <div className="flex items-center gap-4">
                        <Skeleton className="w-10 h-10 rounded-lg" />
                        <div className="flex-1 space-y-2">
                            <Skeleton className="h-4 w-32" />
                            <Skeleton className="h-3 w-24" />
                        </div>
                        <Skeleton className="w-20 h-6 rounded-lg" />
                        <Skeleton className="w-16 h-6 rounded-lg" />
                    </div>
                </div>
            ))}
        </div>
    );
}

// Pricing Page Skeleton — matches Free + Pro editorial layout
export function PricingSkeleton() {
    return (
        <div className="min-h-screen bg-[#F7F6F3] pb-20">
            {/* Hero Skeleton */}
            <div className="h-64 sm:h-80 bg-[#1A2744]" />
            <main className="max-w-[900px] mx-auto px-6 -mt-12 relative z-10">
                {/* Free section */}
                <div className="rounded-2xl border-2 border-[#E9E9E7] bg-white p-8 sm:p-10 lg:p-12 shadow-lg mb-6">
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
                        <div className="flex-1">
                            <Skeleton className="h-3 w-24 mb-2" />
                            <Skeleton className="h-10 w-64 mb-3" />
                            <Skeleton className="h-4 w-full max-w-md mb-6" />
                            <div className="space-y-3">
                                {Array.from({ length: 5 }).map((_, i) => (
                                    <div key={i} className="flex items-center gap-3">
                                        <Skeleton className="w-5 h-5 rounded-full" />
                                        <Skeleton className="h-4 w-48" />
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="lg:w-[280px] shrink-0">
                            <Skeleton className="h-12 w-16 mb-1" />
                            <Skeleton className="h-4 w-20 mb-6" />
                            <Skeleton className="h-12 w-full rounded-lg" />
                        </div>
                    </div>
                </div>

                {/* Pro section */}
                <div className="rounded-2xl border border-white/10 bg-[#2D2A26] p-8 sm:p-10 lg:p-12">
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
                        <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                                <Skeleton className="h-3 w-12 bg-white/30" />
                                <Skeleton className="w-4 h-4 rounded bg-white/30" />
                            </div>
                            <Skeleton className="h-8 w-56 mb-3 bg-white/30" />
                            <Skeleton className="h-4 w-full max-w-md mb-6 bg-white/20" />
                            <div className="space-y-3">
                                {Array.from({ length: 5 }).map((_, i) => (
                                    <div key={i} className="flex items-center gap-3">
                                        <Skeleton className="w-5 h-5 rounded-full bg-white/30" />
                                        <Skeleton className="h-4 w-44 bg-white/30" />
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="lg:w-[240px] shrink-0">
                            <Skeleton className="h-10 w-20 mb-1 bg-white/30" />
                            <Skeleton className="h-3 w-28 mb-6 bg-white/20" />
                            <Skeleton className="h-12 w-full rounded-lg bg-white" />
                        </div>
                    </div>
                </div>

                {/* Trust */}
                <div className="mt-16 text-center">
                    <Skeleton className="h-3 w-40 mx-auto mb-4" />
                    <div className="flex justify-center gap-8">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <Skeleton key={i} className="h-5 w-20" />
                        ))}
                    </div>
                </div>

                {/* FAQ */}
                <div className="mt-24 border-t border-[#E9E9E7] pt-16">
                    <Skeleton className="h-8 w-64 mx-auto mb-12" />
                    <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
                        {Array.from({ length: 4 }).map((_, i) => (
                            <div key={i} className="border-b border-[#E9E9E7] pb-6">
                                <Skeleton className="h-6 w-full mb-2" />
                                <Skeleton className="h-4 w-3/4" />
                            </div>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    );
}

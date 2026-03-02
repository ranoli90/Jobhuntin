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

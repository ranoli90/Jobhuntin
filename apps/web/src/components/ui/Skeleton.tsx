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

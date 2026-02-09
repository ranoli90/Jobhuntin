import * as React from "react";
import { cn } from "../../lib/utils";

const sizeMap: Record<string, string> = {
  sm: "h-5 w-5 border-2",
  md: "h-8 w-8 border-[3px]",
  lg: "h-10 w-10 border-4",
  xl: "h-14 w-14 border-4",
};

export interface LoadingSpinnerProps {
  label?: string;
  className?: string;
  size?: string;
}

export function LoadingSpinner({ label = "Loading", className, size = "lg" }: LoadingSpinnerProps) {
  const spinnerSize = sizeMap[size] ?? sizeMap.lg;
  return (
    <div className={cn("flex flex-col items-center gap-3 text-brand-ink/70", className)}>
      <div className={cn("animate-spin rounded-full border-brand-sunrise/40 border-t-brand-sunrise", spinnerSize)} />
      <p className="text-sm font-medium uppercase tracking-[0.3em]">{label}</p>
    </div>
  );
}

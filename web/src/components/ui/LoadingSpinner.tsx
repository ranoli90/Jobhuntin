import * as React from "react";
import { cn } from "../../lib/utils";

interface LoadingSpinnerProps {
  label?: string;
  className?: string;
}

export function LoadingSpinner({ label = "Loading", className }: LoadingSpinnerProps) {
  return (
    <div className={cn("flex flex-col items-center gap-3 text-brand-ink/70", className)}>
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-sunrise/40 border-t-brand-sunrise" />
      <p className="text-sm font-medium uppercase tracking-[0.3em]">{label}</p>
    </div>
  );
}

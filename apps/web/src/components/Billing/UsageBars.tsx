import * as React from "react";
import { cn } from "../../lib/utils";

interface UsageBarsProps {
  used: number;
  limit?: number;
  label?: string;
  className?: string;
}

export function UsageBars({ used, limit, label, className }: UsageBarsProps) {
  const percentage = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const isUnlimited = !limit || limit === 0;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-brand-ink/70">{label ?? "Applications"}</span>
        <span className="font-semibold text-brand-ink">
          {isUnlimited ? "∞ Unlimited" : `${used} / ${limit}`}
        </span>
      </div>
      <div className="h-3 w-full rounded-full bg-brand-shell/70 overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            isUnlimited
              ? "w-full bg-gradient-to-r from-brand-lagoon to-brand-sunrise"
              : percentage > 80
                ? "bg-brand-sunrise"
                : "bg-brand-lagoon"
          )}
          style={{ width: isUnlimited ? "100%" : `${percentage}%` }}
        />
      </div>
    </div>
  );
}

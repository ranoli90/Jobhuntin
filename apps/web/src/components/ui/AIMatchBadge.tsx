/**
 * AIMatchBadge - Displays an AI-generated match score with visual styling
 *
 * Shows a percentage score with color coding based on match quality.
 * Includes loading and error states.
 */

import * as React from "react";
import { cn } from "../../lib/utils";
import { getScoreColor, getScoreLabel } from "../../hooks/useJobMatchScores";

// Sparkles icon
const SparklesIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 3L13.4 8.6L19 10L13.4 11.4L12 17L10.6 11.4L5 10L10.6 8.6L12 3Z" />
  </svg>
);

export interface AIMatchBadgeProperties {
  score?: number;
  loading?: boolean;
  error?: boolean;
  /** Show detailed label (e.g., "Great Match") */
  showLabel?: boolean;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function AIMatchBadge({
  score,
  loading = false,
  error = false,
  showLabel = false,
  size = "md",
  className,
}: AIMatchBadgeProperties) {
  const sizeClasses = {
    sm: "text-[10px] px-1.5 py-0.5 gap-1",
    md: "text-xs px-2 py-1 gap-1.5",
    lg: "text-sm px-3 py-1.5 gap-2",
  };

  const iconSizes = {
    sm: "w-2.5 h-2.5",
    md: "w-3 h-3",
    lg: "w-4 h-4",
  };

  if (loading) {
    return (
      <div
        className={cn(
          "inline-flex items-center rounded-full border font-semibold animate-pulse",
          "bg-violet-50 border-violet-200 text-violet-500",
          sizeClasses[size],
          className,
        )}
      >
        <SparklesIcon className={cn(iconSizes[size], "animate-spin")} />
        <span>Scoring...</span>
      </div>
    );
  }

  if (error || score === undefined) {
    return null;
  }

  const colorClass = getScoreColor(score);
  const label = getScoreLabel(score);

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border font-bold",
        colorClass,
        sizeClasses[size],
        className,
      )}
      title={`AI Match Score: ${score}% - ${label}`}
    >
      <SparklesIcon className={iconSizes[size]} />
      <span className="tabular-nums">{score}%</span>
      {showLabel && <span className="font-medium opacity-80">· {label}</span>}
    </div>
  );
}

/**
 * Compact version for use in lists
 */
export function AIMatchScoreCompact({
  score,
  className,
}: {
  score: number;
  className?: string;
}) {
  const colorClass =
    score >= 80
      ? "text-emerald-600"
      : score >= 60
        ? "text-amber-600"
        : "text-slate-400";

  return (
    <div
      className={cn("flex items-center gap-1", colorClass, className)}
      title={`AI Match: ${score}%`}
    >
      <SparklesIcon className="w-3 h-3" />
      <span className="text-xs font-bold tabular-nums">{score}%</span>
    </div>
  );
}

import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";

interface ProgressRingProperties {
  /** 0–100 percentage */
  progress: number;
  /** Current step label, e.g. "3 of 7" */
  stepLabel?: string;
  /** Size in px (default 120) */
  size?: number;
  /** Stroke width (default 6) */
  strokeWidth?: number;
  className?: string;
}

export function ProgressRing({
  progress,
  stepLabel,
  size = 120,
  strokeWidth = 6,
  className = "",
}: ProgressRingProperties) {
  const shouldReduceMotion = useReducedMotion();
  const safeProgress = Number.isFinite(progress) ? Math.max(0, Math.min(100, progress)) : 0;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (safeProgress / 100) * circumference;
  const center = size / 2;

  // Milestone glow at 25%, 50%, 75%, 100%
  const isMilestone = [25, 50, 75, 100].includes(Math.round(safeProgress));

  return (
    <div
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
      role="progressbar"
      aria-valuenow={Math.round(safeProgress)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Profile ${Math.round(safeProgress)}% complete`}
    >
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Gradient definition */}
        <defs>
          <linearGradient
            id="progress-gradient"
            x1="0%"
            y1="0%"
            x2="100%"
            y2="100%"
          >
            <stop offset="0%" stopColor="#455DD3" />
            <stop offset="100%" stopColor="#17BEBB" />
          </linearGradient>
          {isMilestone && (
            <filter id="progress-glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          )}
        </defs>

        {/* Background track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-slate-100 dark:text-slate-800"
        />

        {/* Progress arc */}
        <motion.circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="url(#progress-gradient)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={
            shouldReduceMotion
              ? { duration: 0 }
              : { duration: 0.8, ease: "easeOut" }
          }
          filter={isMilestone ? "url(#progress-glow)" : undefined}
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          key={Math.round(safeProgress)}
          initial={shouldReduceMotion ? undefined : { scale: 1.3, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="text-2xl font-black text-slate-900 dark:text-white tabular-nums"
        >
          {Math.round(safeProgress)}%
        </motion.span>
        {stepLabel && (
          <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">
            {stepLabel}
          </span>
        )}
      </div>
    </div>
  );
}

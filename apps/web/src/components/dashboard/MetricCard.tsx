import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { Card } from "../ui/Card";
import { useReducedMotion } from "framer-motion";

interface MetricCardProps {
  /** Metric label */
  label: string;
  /** Metric value (number or string) */
  value: number | string;
  /** Lucide icon component */
  icon: LucideIcon;
  /** Gradient color classes */
  color: string;
  /** Background color class */
  bg: string;
  /** Text color class */
  text: string;
  /** Icon color class */
  iconColor: string;
  /** Progress percentage for bar */
  progress?: number;
  /** Optional description text */
  description?: string;
  /** Optional click handler */
  onClick?: () => void;
  /** Loading state */
  isLoading?: boolean;
}

function AnimatedNumber({
  value,
  shouldReduceMotion,
}: {
  value: number;
  shouldReduceMotion: boolean;
}) {
  return (
    <motion.span
      initial={shouldReduceMotion ? undefined : { opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={shouldReduceMotion ? undefined : { duration: 0.4, type: "spring" }}
    >
      {value}
    </motion.span>
  );
}

function safeProgress(n: number): number {
  return Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
}

export function MetricCard({
  label,
  value,
  icon: Icon,
  color,
  bg,
  text,
  iconColor,
  progress = 0,
  description,
  onClick,
  isLoading = false,
}: MetricCardProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={shouldReduceMotion ? undefined : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={shouldReduceMotion ? undefined : { duration: 0.4 }}
      className="h-full"
      whileHover={onClick ? { scale: 1.02 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
    >
      <Card
        className={`h-full border-brand-border bg-white hover:border-brand-primary/30 transition-colors duration-200 group rounded-xl ${
          onClick ? "cursor-pointer" : ""
        }`}
        shadow="sm"
        tone="glass"
        onClick={onClick}
      >
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <p className="text-sm text-brand-muted font-medium">{label}</p>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-semibold text-brand-text tabular-nums">
                {isLoading ? (
                  <span className="inline-block h-7 w-14 bg-slate-100 rounded animate-pulse"></span>
                ) : typeof value === "string" ? (
                  value
                ) : (
                  <AnimatedNumber
                    value={value}
                    shouldReduceMotion={!!shouldReduceMotion}
                  />
                )}
              </p>
              {description && (
                <span className="text-xs text-brand-muted">{description}</span>
              )}
            </div>
          </div>
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-xl ${bg} ${iconColor}`}
          >
            <Icon className="h-5 w-5" aria-hidden />
          </div>
        </div>
        {progress > 0 && (
          <div className="mt-4 h-1.5 w-full bg-brand-gray rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full bg-gradient-to-r ${color}`}
              initial={
                shouldReduceMotion
                  ? { width: `${safeProgress(progress)}%` }
                  : { width: "0%" }
              }
              animate={{ width: `${safeProgress(progress)}%` }}
              transition={
                shouldReduceMotion
                  ? undefined
                  : { delay: 0.2, duration: 0.6, type: "spring" }
              }
            />
          </div>
        )}
      </Card>
    </motion.div>
  );
}

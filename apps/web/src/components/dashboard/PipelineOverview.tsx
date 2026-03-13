import { motion } from "framer-motion";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import {
  Briefcase,
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  TrendingUp,
  ArrowRight,
} from "lucide-react";

export type ApplicationStatus =
  | "APPLYING"
  | "APPLIED"
  | "HOLD"
  | "INTERVIEWING"
  | "OFFER"
  | "REJECTED"
  | "WITHDRAWN";

interface PipelineStage {
  /** Stage name */
  label: string;
  /** Stage count */
  count: number;
  /** Status type */
  status: ApplicationStatus;
  /** Icon component */
  Icon: typeof Briefcase;
  /** Color theme */
  color: string;
}

interface PipelineOverviewProps {
  /** Pipeline stages data */
  stages: PipelineStage[];
  /** Total applications */
  total: number;
  /** Loading state */
  isLoading?: boolean;
  /** Navigate to applications handler */
  onViewAll?: () => void;
}

const statusColors: Record<
  ApplicationStatus,
  { bg: string; text: string; border: string }
> = {
  APPLYING: { bg: "bg-blue-100", text: "text-blue-700", border: "border-blue-200" },
  APPLIED: { bg: "bg-purple-100", text: "text-purple-700", border: "border-purple-200" },
  HOLD: { bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-200" },
  INTERVIEWING: { bg: "bg-indigo-100", text: "text-indigo-700", border: "border-indigo-200" },
  OFFER: { bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200" },
  REJECTED: { bg: "bg-red-100", text: "text-red-700", border: "border-red-200" },
  WITHDRAWN: { bg: "bg-slate-100", text: "text-slate-700", border: "border-slate-200" },
};

function safeProgress(count: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((count / total) * 100);
}

export function PipelineOverview({
  stages,
  total,
  isLoading,
  onViewAll,
}: PipelineOverviewProps) {
  if (isLoading) {
    return (
      <Card className="p-6 border-brand-border bg-white rounded-xl" shadow="sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-40 bg-slate-100 rounded" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 bg-slate-50 rounded-xl" />
            ))}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 border-brand-border bg-white rounded-xl" shadow="sm">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-brand-primary" />
          <h3 className="font-semibold text-brand-text">Application Pipeline</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-brand-muted">
            {total} total applications
          </span>
          {onViewAll && (
            <Button variant="ghost" size="sm" onClick={onViewAll}>
              View all
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          )}
        </div>
      </div>

      {/* Pipeline visualization */}
      <div className="relative">
        {/* Connecting line */}
        <div className="absolute top-6 left-0 right-0 h-0.5 bg-slate-100" />

        <div className="grid grid-cols-4 gap-4 relative">
          {stages.map((stage, index) => {
            const progress = safeProgress(stage.count, total);
            const colors = statusColors[stage.status];

            return (
              <motion.div
                key={stage.status}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.4 }}
                className="relative"
              >
                <div className="flex flex-col items-center">
                  {/* Icon with count */}
                  <div
                    className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-xl ${colors.bg} ${colors.border} border-2 mb-3`}
                  >
                    <stage.Icon className={`h-5 w-5 ${colors.text}`} />
                    <span
                      className={`absolute -top-1 -right-1 flex items-center justify-center min-w-[20px] h-5 px-1.5 text-xs font-bold ${colors.text} bg-white ${colors.border} border rounded-full`}
                    >
                      {stage.count}
                    </span>
                  </div>

                  {/* Label */}
                  <p className="text-sm font-medium text-brand-text text-center">
                    {stage.label}
                  </p>

                  {/* Progress bar */}
                  <div className="w-full mt-2">
                    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${colors.bg.replace("bg-", "bg-").replace("-100", "-500")}`}
                        initial={{ width: "0%" }}
                        animate={{ width: `${progress}%` }}
                        transition={{ delay: 0.2 + index * 0.1, duration: 0.5 }}
                      />
                    </div>
                    <p className="text-xs text-brand-muted text-center mt-1">
                      {progress}%
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

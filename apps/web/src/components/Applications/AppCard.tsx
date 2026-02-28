import * as React from "react";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import type { ApplicationRecord } from "../../hooks/useApplications";
import { cn } from "../../lib/utils";

const STATUS_LABEL: Record<ApplicationRecord["status"], string> = {
  APPLYING: "Applying",
  APPLIED: "Applied",
  HOLD: "Needs Input",
  FAILED: "Failed",
};

const STATUS_TONE: Record<ApplicationRecord["status"], string> = {
  APPLYING: "bg-brand-shell text-brand-ink",
  APPLIED: "bg-green-100 text-green-900",
  HOLD: "bg-yellow-100 text-yellow-900",
  FAILED: "bg-red-100 text-red-900",
};

interface AppCardProps {
  application: ApplicationRecord;
  onAnswerHold?: (id: string) => void;
  className?: string;
}

export function AppCard({ application, onAnswerHold, className }: AppCardProps) {
  return (
    <div className={cn("rounded-3xl border border-white/70 bg-white px-6 py-5 shadow-sm", className)}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-brand-ink/70">{application.company}</p>
          <p className="text-xl font-semibold text-brand-ink">{application.job_title}</p>
        </div>
        <Badge variant="outline" className={cn("text-xs", STATUS_TONE[application.status])}>
          {STATUS_LABEL[application.status]}
        </Badge>
      </div>
      {application.summary ? <p className="mt-2 text-sm text-brand-ink/70">{application.summary}</p> : null}
      {application.status === "HOLD" && application.hold_question ? (
        <div className="mt-4 rounded-2xl border border-dashed border-brand-ink/20 bg-brand-shell/60 px-4 py-3 text-sm text-brand-ink">
          <p className="font-semibold">HOLD question</p>
          <p>{application.hold_question}</p>
          {onAnswerHold ? (
            <Button size="sm" variant="lagoon" className="mt-3" onClick={() => onAnswerHold(application.id)}>
              Answer now
            </Button>
          ) : null}
        </div>
      ) : null}
      <div className="mt-4 text-xs uppercase tracking-[0.3em] text-brand-ink/50">
        Updated {application.last_activity ? new Date(application.last_activity).toLocaleDateString(navigator.language || 'en-US') : "today"}
      </div>
    </div>
  );
}

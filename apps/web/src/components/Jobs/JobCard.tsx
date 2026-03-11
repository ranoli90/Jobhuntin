import * as React from "react";
import {
  Briefcase,
  MapPin,
  DollarSign,
  Eye,
  Bookmark,
  AlertTriangle,
  Loader2,
  Sparkles,
  Zap,
} from "lucide-react";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { AIMatchBadge } from "../ui/AIMatchBadge";
import type { JobPosting } from "../../hooks/useJobs";
import { useSavedJobs } from "../../hooks/useSavedJobs";
import { cn } from "../../lib/utils";
import { formatCurrency } from "../../lib/format";

interface SkillMatchPreview {
  matched: string[];
  missing: string[];
}

export interface JobCardProperties {
  job: JobPosting;
  index: number;
  isActive: boolean;
  onSwipe: (decision: "ACCEPT" | "REJECT", job: JobPosting) => void;
  onViewDetail: () => void;
  isSaved: boolean;
  onSave: () => void;
  matchScore?: number;
  matchScoreLoading?: boolean;
  dealbreakers?: {
    salaryMismatch?: boolean;
    locationMismatch?: boolean;
    visaIssue?: boolean;
  };
  matchExplanation?: string;
  skillMatch?: SkillMatchPreview;
  onQuickApply?: () => void;
  isApplying?: boolean;
}

function DealbreakerIndicator({
  type,
  tooltip,
}: {
  type: "salary" | "location" | "visa";
  tooltip: string;
}) {
  return (
    <div className="flex items-center gap-1 text-amber-800" title={tooltip}>
      <AlertTriangle className="w-3.5 h-3.5" />
      <span className="text-xs font-medium">
        {type === "salary" && "Salary"}
        {type === "location" && "Location"}
        {type === "visa" && "Visa"}
      </span>
    </div>
  );
}

function SkillMatchTooltip({
  skillMatch,
  score,
}: {
  skillMatch: SkillMatchPreview;
  score: number;
}) {
  return (
    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-xl opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity pointer-events-none z-50">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="w-4 h-4 text-primary-400" />
        <span className="font-semibold">Skill Match Analysis</span>
      </div>
      <div className="space-y-2">
        <div>
          <p className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">
            Matched ({skillMatch.matched.length})
          </p>
          <div className="flex flex-wrap gap-1">
            {skillMatch.matched.slice(0, 5).map((skill, index) => (
              <span
                key={index}
                className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-300 rounded text-[10px]"
              >
                {skill}
              </span>
            ))}
            {skillMatch.matched.length > 5 && (
              <span className="text-slate-400 text-[10px]">
                +{skillMatch.matched.length - 5} more
              </span>
            )}
          </div>
        </div>
        <div>
          <p className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">
            Missing ({skillMatch.missing.length})
          </p>
          <div className="flex flex-wrap gap-1">
            {skillMatch.missing.slice(0, 3).map((skill, index) => (
              <span
                key={index}
                className="px-1.5 py-0.5 bg-red-500/20 text-red-300 rounded text-[10px]"
              >
                {skill}
              </span>
            ))}
            {skillMatch.missing.length > 3 && (
              <span className="text-slate-400 text-[10px]">
                +{skillMatch.missing.length - 3} more
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-slate-900" />
    </div>
  );
}

function MatchExplanationTooltip({
  explanation,
  visible,
}: {
  explanation: string;
  visible?: boolean;
}) {
  return (
    <div
      className={cn(
        "absolute bottom-full right-0 mb-2 w-72 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-xl transition-opacity pointer-events-none z-50",
        visible
          ? "opacity-100"
          : "opacity-0 group-hover/explain:opacity-100 group-focus-within/explain:opacity-100",
      )}
    >
      <p className="text-slate-300 leading-relaxed">{explanation}</p>
      <div className="absolute bottom-0 right-4 translate-y-1/2 rotate-45 w-2 h-2 bg-slate-900" />
    </div>
  );
}

export function JobCard({
  job,
  index,
  isActive,
  onSwipe,
  onViewDetail,
  matchScore,
  matchScoreLoading,
  dealbreakers,
  matchExplanation,
  skillMatch,
  onQuickApply,
  isApplying = false,
}: Omit<JobCardProperties, "isSaved" | "onSave">) {
  const { isJobSaved, saveJob, isSaving } = useSavedJobs();
  const isSaved = isJobSaved(job.id);
  const [showExplanation, setShowExplanation] = React.useState(false);

  const hasDealbreakers =
    dealbreakers?.salaryMismatch ||
    dealbreakers?.locationMismatch ||
    dealbreakers?.visaIssue;

  const handleSave = () => {
    saveJob(job.id);
  };

  return (
    <div
      className={cn(
        "absolute inset-0 rounded-3xl border border-white/70 bg-white px-8 py-10 shadow-md transition-all",
        isActive ? "z-20" : "z-10 translate-y-6 scale-[0.98] opacity-80",
      )}
      style={{ transform: `translateY(${index * 6}px)` }}
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">
              Headline
            </p>
            {matchScore !== undefined || matchScoreLoading ? (
              <div className="group relative" tabIndex={0}>
                <AIMatchBadge
                  score={matchScore}
                  loading={matchScoreLoading}
                  size="sm"
                />
                {skillMatch && matchScore !== undefined && (
                  <SkillMatchTooltip
                    skillMatch={skillMatch}
                    score={matchScore}
                  />
                )}
              </div>
            ) : null}
          </div>
          <h2 className="font-display text-3xl text-brand-ink">{job.title}</h2>
          <p className="text-brand-ink/70">{job.company}</p>
        </div>
        {job.logo_url ? (
          <img
            src={job.logo_url}
            alt={`${job.company} logo`}
            className="h-16 w-16 rounded-2xl object-cover"
            loading="lazy"
          />
        ) : null}
      </div>

      <div className="mt-6 grid gap-4 text-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-brand-ink/70">
            <MapPin className="h-4 w-4" />
            {job.location ?? "Remote"}
          </div>
          <div className="flex items-center gap-2">
            {job.is_remote && (
              <Badge variant="success" size="sm" className="text-[10px]">
                Remote
              </Badge>
            )}
            {dealbreakers?.locationMismatch && (
              <DealbreakerIndicator
                type="location"
                tooltip="Location doesn't match your preferences"
              />
            )}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-brand-ink/70">
            <DollarSign className="h-4 w-4" />
            {job.salary_min
              ? `${formatCurrency(job.salary_min)}+`
              : "Salary shared on match"}
          </div>
          {dealbreakers?.salaryMismatch && (
            <DealbreakerIndicator
              type="salary"
              tooltip="Salary below your minimum requirement"
            />
          )}
        </div>

        {job.source && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="capitalize">{job.source.replace("_", " ")}</span>
            {job.date_posted && (
              <>
                <span>•</span>
                <span>{job.date_posted}</span>
              </>
            )}
          </div>
        )}

        {dealbreakers?.visaIssue && (
          <div className="flex items-center gap-2 text-amber-800 bg-amber-50 px-3 py-1.5 rounded-lg">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-xs font-medium">
              May require visa sponsorship
            </span>
          </div>
        )}

        <p className="text-brand-ink/80 line-clamp-3">{job.description}</p>

        {skillMatch && skillMatch.matched.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {skillMatch.matched.slice(0, 4).map((skill, index_) => (
              <Badge
                key={index_}
                variant="success"
                size="sm"
                className="text-[10px]"
              >
                {skill}
              </Badge>
            ))}
            {skillMatch.matched.length > 4 && (
              <Badge variant="default" size="sm" className="text-[10px]">
                +{skillMatch.matched.length - 4}
              </Badge>
            )}
          </div>
        )}
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-4">
        <Button
          size="lg"
          variant="lagoon"
          onClick={() => onQuickApply?.() ?? onSwipe("ACCEPT", job)}
          disabled={isApplying}
          className="gap-2"
        >
          {isApplying ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Applying...
            </>
          ) : (
            <>
              <Zap className="h-4 w-4" />
              Apply 1-click
            </>
          )}
        </Button>

        <Button
          size="lg"
          variant="ghost"
          onClick={() => onSwipe("REJECT", job)}
        >
          Pass
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className="gap-2"
          onClick={onViewDetail}
        >
          <Eye className="h-4 w-4" />
          View details
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className="gap-2"
          onClick={handleSave}
          disabled={isSaving}
        >
          <Bookmark className={`h-4 w-4 ${isSaved ? "fill-current" : ""}`} />
          {isSaving ? "Saving..." : isSaved ? "Saved" : "Save"}
        </Button>

        {matchExplanation && (
          <div className="group/explain relative ml-auto">
            <button
              type="button"
              className="text-xs text-slate-500 hover:text-slate-600 flex items-center gap-1 transition-colors"
              onClick={() => setShowExplanation((s) => !s)}
              aria-expanded={showExplanation}
            >
              <Sparkles className="w-3 h-3" />
              Why this match?
            </button>
            <MatchExplanationTooltip
              explanation={matchExplanation}
              visible={showExplanation}
            />
          </div>
        )}

        {!matchExplanation && matchScore !== undefined && matchScore >= 80 ? (
          <Badge variant="lagoon" className="ml-auto">
            Great Match
          </Badge>
        ) : (
          !hasDealbreakers && (
            <Badge variant="lagoon" className="ml-auto">
              Unlimited PRO swipes
            </Badge>
          )
        )}

        {hasDealbreakers && (
          <Badge variant="warning" className="ml-auto">
            Review Details
          </Badge>
        )}
      </div>
    </div>
  );
}

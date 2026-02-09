import * as React from "react";
import { Briefcase, MapPin, DollarSign, Eye, Bookmark } from "lucide-react";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import type { JobPosting } from "../../hooks/useJobs";
import { cn } from "../../lib/utils";

export interface JobCardProps {
  job: JobPosting;
  index: number;
  isActive: boolean;
  onSwipe: (decision: "ACCEPT" | "REJECT", job: JobPosting) => void;
  onViewDetail: () => void;
  isSaved: boolean;
  onSave: () => void;
}

export function JobCard({ job, index, isActive, onSwipe, onViewDetail, isSaved, onSave }: JobCardProps) {
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
          <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">Headline</p>
          <h2 className="font-display text-3xl text-brand-ink">{job.title}</h2>
          <p className="text-brand-ink/70">{job.company}</p>
        </div>
        {job.logo_url ? <img src={job.logo_url} className="h-16 w-16 rounded-2xl object-cover" /> : null}
      </div>
      <div className="mt-6 grid gap-4 text-sm">
        <div className="flex items-center gap-3 text-brand-ink/70">
          <MapPin className="h-4 w-4" /> {job.location ?? "Remote"}
        </div>
        <div className="flex items-center gap-3 text-brand-ink/70">
          <DollarSign className="h-4 w-4" /> {job.salary_min ? `$${job.salary_min.toLocaleString()}+` : "Salary shared on match"}
        </div>
        <p className="text-brand-ink/80 line-clamp-3">{job.description}</p>
      </div>
      <div className="mt-8 flex flex-wrap items-center gap-4">
        <Button size="lg" variant="lagoon" wobble onClick={() => onSwipe("ACCEPT", job)}>
          Apply 1-click
        </Button>
        <Button size="lg" variant="ghost" onClick={() => onSwipe("REJECT", job)}>
          Pass
        </Button>
        <Button variant="ghost" size="sm" className="gap-2" onClick={onViewDetail}>
          <Eye className="h-4 w-4" />
          View details
        </Button>
        <Button variant="ghost" size="sm" className="gap-2" onClick={onSave}>
          <Bookmark className={`h-4 w-4 ${isSaved ? "fill-current" : ""}`} />
          {isSaved ? "Saved" : "Save"}
        </Button>
        <Badge variant="lagoon" className="ml-auto">
          Unlimited PRO swipes
        </Badge>
      </div>
    </div>
  );
}

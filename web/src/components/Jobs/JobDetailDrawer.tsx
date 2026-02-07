import * as React from "react";
import { X, MapPin, DollarSign, ExternalLink, Bookmark, Share2, CheckCircle, Briefcase, Sparkles } from "lucide-react";
import { Button } from "./Button";
import { Card } from "./Card";
import { Badge } from "./Badge";
import type { JobPosting } from "../../hooks/useJobs";

interface JobDetailDrawerProps {
  job: JobPosting | null;
  isOpen: boolean;
  onClose: () => void;
  onApply: () => void;
  onSave: () => void;
  isSaved: boolean;
}

export function JobDetailDrawer({ job, isOpen, onClose, onApply, onSave, isSaved }: JobDetailDrawerProps) {
  if (!isOpen || !job) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 z-40 bg-black/40 transition-opacity" 
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl overflow-y-auto bg-white shadow-2xl">
        <div className="p-8">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              {job.logo_url ? (
                <img src={job.logo_url} alt={job.company} className="h-16 w-16 rounded-2xl object-cover" />
              ) : (
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-shell">
                  <Briefcase className="h-8 w-8 text-brand-ink/40" />
                </div>
              )}
              <div>
                <h2 className="font-display text-2xl text-brand-ink">{job.title}</h2>
                <p className="text-brand-ink/70">{job.company}</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Quick info */}
          <div className="mt-6 flex flex-wrap gap-3">
            <Badge variant="shell" className="flex items-center gap-2">
              <MapPin className="h-3 w-3" />
              {job.location || "Remote"}
            </Badge>
            {(job.salary_min || job.salary_max) && (
              <Badge variant="shell" className="flex items-center gap-2">
                <DollarSign className="h-3 w-3" />
                {job.salary_min && `$${job.salary_min.toLocaleString()}`}
                {job.salary_min && job.salary_max && " — "}
                {job.salary_max && `$${job.salary_max.toLocaleString()}`}
                {!job.salary_max && "+"}
              </Badge>
            )}
          </div>

          {/* What Skedaddle submits section */}
          <Card tone="lagoon" className="mt-6 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-5 w-5 text-brand-lagoon" />
              <h3 className="font-display text-lg">What Skedaddle submits</h3>
            </div>
            <ul className="space-y-2 text-sm text-brand-ink/80">
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-brand-lagoon mt-0.5" />
                <span>Your resume and profile summary</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-brand-lagoon mt-0.5" />
                <span>Personalized cover letter based on the job description</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-brand-lagoon mt-0.5" />
                <span>Your contact information and availability preferences</span>
              </li>
            </ul>
            <p className="mt-3 text-xs text-brand-ink/60">
              We'll handle the application automatically. You can track progress in your Applications dashboard.
            </p>
          </Card>

          {/* Full description */}
          <div className="mt-6">
            <h3 className="font-display text-lg mb-3">About this role</h3>
            <div className="prose prose-sm max-w-none text-brand-ink/80">
              {job.description ? (
                <p className="whitespace-pre-line">{job.description}</p>
              ) : (
                <p className="text-brand-ink/50 italic">No detailed description available.</p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="mt-8 space-y-3">
            <Button 
              variant="lagoon" 
              wobble 
              size="lg" 
              className="w-full gap-2"
              onClick={() => {
                onApply();
                onClose();
              }}
            >
              Apply via Skedaddle
              <Sparkles className="h-4 w-4" />
            </Button>
            
            <div className="flex gap-3">
              <Button 
                variant="outline" 
                className="flex-1 gap-2"
                onClick={onSave}
              >
                <Bookmark className={`h-4 w-4 ${isSaved ? "fill-current" : ""}`} />
                {isSaved ? "Saved" : "Save for later"}
              </Button>
              <Button 
                variant="outline" 
                className="flex-1 gap-2"
                onClick={() => {
                  if (job.url) window.open(job.url, "_blank");
                }}
                disabled={!job.url}
              >
                <ExternalLink className="h-4 w-4" />
                View original
              </Button>
            </div>
            
            <Button 
              variant="ghost" 
              className="w-full gap-2"
              onClick={() => {
                navigator.share?.({
                  title: job.title,
                  text: `Check out this ${job.title} position at ${job.company}`,
                  url: job.url || window.location.href,
                }).catch(() => {
                  navigator.clipboard.writeText(job.url || window.location.href);
                });
              }}
            >
              <Share2 className="h-4 w-4" />
              Share with a friend
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}

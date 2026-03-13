import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  Search,
  FileText,
  Briefcase,
  Inbox,
  Bell,
  FolderOpen,
  Users,
  Mail,
  Calendar,
  Sparkles,
  Plus,
  Bookmark,
  Shield,
  Monitor,
  LayoutGrid,
  CheckCircle2,
} from "lucide-react";
import { Button } from "./Button";
import { cn } from "../../lib/utils";

const iconMap = {
  search: Search,
  file: FileText,
  job: Briefcase,
  inbox: Inbox,
  bell: Bell,
  folder: FolderOpen,
  users: Users,
  mail: Mail,
  calendar: Calendar,
  sparkles: Sparkles,
  bookmark: Bookmark,
  shield: Shield,
  monitor: Monitor,
  layoutgrid: LayoutGrid,
  check: CheckCircle2,
};

interface EmptyStateProperties {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
  iconName?: keyof typeof iconMap;
  className?: string;
  compact?: boolean;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
  iconName,
  className,
  compact = false,
  secondaryActionLabel,
  onSecondaryAction,
}: EmptyStateProperties) {
  const shouldReduceMotion = useReducedMotion();

  // Get icon component if iconName is provided
  const IconComponent = iconName ? iconMap[iconName] : null;

  return (
    <motion.div
      role="status"
      aria-live="polite"
      initial={shouldReduceMotion ? undefined : { opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={
        shouldReduceMotion ? undefined : { duration: 0.4, ease: "easeOut" }
      }
      className={cn(
        "rounded-3xl border-2 border-dashed border-slate-200 bg-gradient-to-br from-white to-slate-50 text-center relative overflow-hidden",
        compact ? "px-6 py-8" : "px-8 py-14",
        className,
      )}
    >
      <div className="absolute -top-16 -right-16 w-48 h-48 bg-primary-500/5 rounded-full blur-3xl pointer-events-none" />
      {(icon || IconComponent) && (
        <motion.div
          initial={shouldReduceMotion ? undefined : { scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={
            shouldReduceMotion
              ? undefined
              : { delay: 0.15, type: "spring", stiffness: 200 }
          }
          className={cn(
            "mx-auto mb-5 flex items-center justify-center rounded-2xl bg-slate-100 shadow-inner",
            compact ? "h-12 w-12" : "h-16 w-16",
          )}
        >
          {icon ||
            (IconComponent && (
              <IconComponent
                className={cn(
                  "text-slate-400",
                  compact ? "w-6 h-6" : "w-8 h-8",
                )}
              />
            ))}
        </motion.div>
      )}
      <p
        className={cn(
          "font-display font-bold text-slate-900",
          compact ? "text-lg" : "text-xl",
        )}
      >
        {title}
      </p>
      {description ? (
        <p
          className={cn(
            "mt-2 text-slate-500 max-w-md mx-auto font-medium",
            compact ? "text-sm" : "text-base",
          )}
        >
          {description}
        </p>
      ) : null}
      {actionLabel || secondaryActionLabel ? (
        <div
          className={cn(
            "flex gap-3 justify-center",
            compact ? "mt-4" : "mt-6",
            secondaryActionLabel ? "flex-col sm:flex-row" : "",
          )}
        >
          {actionLabel ? (
            <motion.div
              whileHover={shouldReduceMotion ? undefined : { scale: 1.03 }}
              whileTap={shouldReduceMotion ? undefined : { scale: 0.97 }}
            >
              <Button
                className="shadow-lg shadow-primary-500/10"
                onClick={onAction}
                size={compact ? "sm" : "md"}
              >
                <Plus className="w-4 h-4 mr-2" />
                {actionLabel}
              </Button>
            </motion.div>
          ) : null}
          {secondaryActionLabel ? (
            <Button
              variant="outline"
              onClick={onSecondaryAction}
              size={compact ? "sm" : "md"}
            >
              {secondaryActionLabel}
            </Button>
          ) : null}
        </div>
      ) : null}
    </motion.div>
  );
}

// Pre-configured empty states for common use cases

export function NoJobsEmptyState({ onSearch }: { onSearch?: () => void }) {
  return (
    <EmptyState
      iconName="job"
      title="No jobs found"
      description="We couldn't find any jobs matching your criteria. Try adjusting your filters or search for something different."
      actionLabel="Search Jobs"
      onAction={onSearch}
    />
  );
}

export function NoApplicationsEmptyState({
  onBrowse,
}: {
  onBrowse?: () => void;
}) {
  return (
    <EmptyState
      iconName="file"
      title="No applications yet"
      description="You haven't applied to any jobs yet. Start browsing and let our AI help you apply!"
      actionLabel="Browse Jobs"
      onAction={onBrowse}
    />
  );
}

export function NoNotificationsEmptyState() {
  return (
    <EmptyState
      iconName="bell"
      title="No notifications"
      description="You're all caught up! We'll notify you when there are updates on your applications."
      compact
    />
  );
}

export function NoMatchesEmptyState({
  onAdjustPreferences,
}: {
  onAdjustPreferences?: () => void;
}) {
  return (
    <EmptyState
      iconName="search"
      title="No matches yet"
      description="We haven't found jobs matching your preferences yet. Try adjusting your criteria to see more results."
      actionLabel="Adjust Preferences"
      onAction={onAdjustPreferences}
    />
  );
}

export function NoResumesEmptyState({ onUpload }: { onUpload?: () => void }) {
  return (
    <EmptyState
      iconName="file"
      title="No resumes uploaded"
      description="Upload your resume to get started. Our AI will analyze it and find the best job matches for you."
      actionLabel="Upload Resume"
      onAction={onUpload}
    />
  );
}

export function NoSearchResultsEmptyState({
  onClear,
}: {
  onClear?: () => void;
}) {
  return (
    <EmptyState
      iconName="search"
      title="No results found"
      description="We couldn't find anything matching your search. Try different keywords or clear your filters."
      actionLabel="Clear Search"
      onAction={onClear}
      secondaryActionLabel="Browse All"
    />
  );
}

export function InboxEmptyState() {
  return (
    <EmptyState
      iconName="mail"
      title="Your inbox is empty"
      description="Messages from employers and updates will appear here."
      compact
    />
  );
}

export function NoTeamMembersEmptyState({
  onInvite,
}: {
  onInvite?: () => void;
}) {
  return (
    <EmptyState
      iconName="users"
      title="No team members yet"
      description="Invite your team members to collaborate on job searches."
      actionLabel="Invite Members"
      onAction={onInvite}
    />
  );
}

export function ComingSoonEmptyState({
  featureName,
  description,
  className,
}: {
  featureName: string;
  description?: string;
  className?: string;
}) {
  return (
    <EmptyState
      iconName="sparkles"
      title={`${featureName} coming soon`}
      description={
        description ?? "We're working on something exciting. Stay tuned for updates!"
      }
      compact
      className={className}
    />
  );
}

// Additional pre-built variants for specific use cases

export function NoSavedJobsEmptyState({
  onBrowse,
  onClearSearch,
  hasSearchTerm = false,
}: {
  onBrowse?: () => void;
  onClearSearch?: () => void;
  hasSearchTerm?: boolean;
}) {
  return (
    <EmptyState
      iconName="bookmark"
      title={hasSearchTerm ? "No saved jobs match your search" : "No saved jobs yet"}
      description={
        hasSearchTerm
          ? "Try adjusting your search terms or clear the search to see all saved jobs."
          : "Start saving jobs you're interested in to see them here. We'll help you keep track of positions you want to apply to."
      }
      actionLabel={hasSearchTerm ? "Clear Search" : "Browse Jobs"}
      onAction={hasSearchTerm ? onClearSearch : onBrowse}
    />
  );
}

export function NoSessionsEmptyState({
  onRefresh,
}: {
  onRefresh?: () => void;
}) {
  return (
    <EmptyState
      iconName="monitor"
      title="No active sessions"
      description="You don't have any active sessions at the moment. Sign in to start a new session."
      compact
      actionLabel="Refresh"
      onAction={onRefresh}
    />
  );
}

export function UnauthorizedEmptyState({
  onGoBack,
  onGoHome,
  message,
}: {
  onGoBack?: () => void;
  onGoHome?: () => void;
  message?: string;
}) {
  return (
    <EmptyState
      iconName="shield"
      title="Access Denied"
      description={message ?? "You don't have permission to access this content."}
      actionLabel="Go Back"
      onAction={onGoBack}
      secondaryActionLabel="Go Home"
      onSecondaryAction={onGoHome}
    />
  );
}

export function NoPipelineItemsEmptyState({
  onBrowseJobs,
  stageName,
}: {
  onBrowseJobs?: () => void;
  stageName?: string;
}) {
  return (
    <EmptyState
      iconName="layoutgrid"
      title={`No applications in ${stageName ?? "this stage"}`}
      description="Applications will appear here as you move through the hiring process."
      actionLabel="Browse Jobs"
      onAction={onBrowseJobs}
      compact
    />
  );
}

export function NoActivitiesEmptyState({
  onBrowse,
}: {
  onBrowse?: () => void;
}) {
  return (
    <EmptyState
      iconName="check"
      title="No activities yet"
      description="Your recent activities will appear here. Start exploring jobs to see your activity history."
      actionLabel="Browse Jobs"
      onAction={onBrowse}
    />
  );
}

export function ErrorEmptyState({
  onRetry,
  message,
}: {
  onRetry?: () => void;
  message?: string;
}) {
  return (
    <EmptyState
      iconName="inbox"
      title="Something went wrong"
      description={message ?? "We encountered an error while loading this content. Please try again."}
      actionLabel="Try Again"
      onAction={onRetry}
    />
  );
}

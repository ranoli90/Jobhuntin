import * as React from "react";
import { cn } from "../../lib/utils";

// ============================================
// CORE SKELETON COMPONENT
// ============================================

interface SkeletonProperties extends React.HTMLAttributes<HTMLDivElement> {
  /** Custom width */
  width?: string | number;
  /** Custom height */
  height?: string | number;
  /** Roundness */
  rounded?: "none" | "sm" | "md" | "lg" | "xl" | "full";
}

export function Skeleton({
  className,
  width,
  height,
  rounded = "md",
  ...properties
}: SkeletonProperties) {
  const roundedClasses = {
    none: "",
    sm: "rounded-sm",
    md: "rounded-md",
    lg: "rounded-lg",
    xl: "rounded-xl",
    full: "rounded-full",
  };

  return (
    <div
      role="status"
      aria-label="Loading content"
      aria-busy="true"
      className={cn(
        "animate-pulse bg-slate-200/60 dark:bg-slate-700/50",
        roundedClasses[rounded],
        className,
      )}
      style={{ width, height }}
      {...properties}
    />
  );
}

// ============================================
// SKELETON CARD COMPONENT
// ============================================

interface SkeletonCardProperties {
  /** Number of content lines to show */
  lines?: number;
  /** Show header with avatar */
  showHeader?: boolean;
  /** Show footer with action buttons */
  showFooter?: boolean;
  /** Card variant: 'default' (white), 'dark' (slate-900), 'bordered' */
  variant?: "default" | "dark" | "bordered";
  /** Additional class names */
  className?: string;
}

export function SkeletonCard({
  lines = 3,
  showHeader = false,
  showFooter = false,
  variant = "default",
  className,
}: SkeletonCardProperties) {
  const variantClasses = {
    default: "bg-white dark:bg-slate-800",
    dark: "bg-slate-900",
    bordered: "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700",
  };

  return (
    <div
      role="status"
      aria-label="Loading card content"
      aria-busy="true"
      className={cn(
        "rounded-xl p-4 shadow-sm",
        variantClasses[variant],
        className,
      )}
    >
      {showHeader && (
        <div className="flex items-center gap-3 mb-4">
          <Skeleton rounded="full" className="h-10 w-10" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
      )}

      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, index) => (
          <Skeleton
            key={index}
            className={cn(
              "h-4 w-full",
              index === lines - 1 ? "w-2/3" : "",
            )}
          />
        ))}
      </div>

      {showFooter && (
        <div className="flex gap-2 mt-4 pt-3 border-t border-slate-100 dark:border-slate-700">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-16" />
        </div>
      )}
    </div>
  );
}

// ============================================
// SKELETON TABLE COMPONENT
// ============================================

interface SkeletonTableProperties {
  /** Number of rows */
  rows?: number;
  /** Number of columns */
  columns?: number;
  /** Show table header */
  showHeader?: boolean;
  /** Additional class names */
  className?: string;
}

export function SkeletonTable({
  rows = 5,
  columns = 4,
  showHeader = true,
  className,
}: SkeletonTableProperties) {
  const columnWidths = [
    "w-1/4", // First column (typically name/title)
    "w-1/4", // Second column
    "w-1/6", // Third column (typically status)
    "w-1/6", // Fourth column (typically actions)
    "w-1/5", // Fifth column
    "w-1/5", // Sixth column
  ];

  return (
    <div
      role="status"
      aria-label="Loading table content"
      aria-busy="true"
      className={cn("overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700", className)}
    >
      {/* Table Header */}
      {showHeader && (
        <div className="bg-slate-50 dark:bg-slate-800/50 p-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-4">
            {Array.from({ length: columns }).map((_, index) => (
              <Skeleton
                key={`header-${index}`}
                className={cn("h-4", columnWidths[index] || "w-24")}
              />
            ))}
          </div>
        </div>
      )}

      {/* Table Body */}
      <div className="bg-white dark:bg-slate-900">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div
            key={rowIndex}
            className="flex items-center gap-4 p-4 border-b border-slate-100 dark:border-slate-800 last:border-b-0"
          >
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton
                key={`row-${rowIndex}-col-${colIndex}`}
                className={cn(
                  "h-4",
                  columnWidths[colIndex] || "w-24",
                  colIndex === 0 && rowIndex === 0 && "h-6 w-6 rounded-full", // Avatar placeholder
                )}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================
// SKELETON LIST COMPONENT
// ============================================

interface SkeletonListProperties {
  /** Number of items */
  items?: number;
  /** Show avatars */
  showAvatars?: boolean;
  /** Show action buttons */
  showActions?: boolean;
  /** Item height variant */
  itemHeight?: "sm" | "md" | "lg";
  /** Additional class names */
  className?: string;
}

export function SkeletonList({
  items = 5,
  showAvatars = true,
  showActions = false,
  itemHeight = "md",
  className,
}: SkeletonListProperties) {
  const heightClasses = {
    sm: "h-12",
    md: "h-16",
    lg: "h-20",
  };

  return (
    <div
      role="status"
      aria-label="Loading list content"
      aria-busy="true"
      className={cn("space-y-2", className)}
    >
      {Array.from({ length: items }).map((_, index) => (
        <div
          key={index}
          className={cn(
            "flex items-center gap-3 p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700",
            heightClasses[itemHeight],
          )}
        >
          {showAvatars && (
            <Skeleton rounded="full" className="h-10 w-10 shrink-0" />
          )}
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-1/4" />
          </div>
          {showActions && (
            <div className="flex gap-2">
              <Skeleton className="h-8 w-16" />
              <Skeleton className="h-8 w-8" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ============================================
// SKELETON FORM COMPONENT
// ============================================

interface SkeletonFormProperties {
  /** Number of form fields */
  fields?: number;
  /** Show labels */
  showLabels?: boolean;
  /** Show submit button */
  showSubmit?: boolean;
  /** Field layout: 'single' or 'grid' */
  layout?: "single" | "grid";
  /** Additional class names */
  className?: string;
}

export function SkeletonForm({
  fields = 4,
  showLabels = true,
  showSubmit = true,
  layout = "single",
  className,
}: SkeletonFormProperties) {
  const fieldHeights = [
    "h-12", // Input field
    "h-24", // Textarea
    "h-12", // Select
    "h-10", // Checkbox/Switch
  ];

  return (
    <div
      role="status"
      aria-label="Loading form content"
      aria-busy="true"
      className={cn("space-y-4", className)}
    >
      {Array.from({ length: fields }).map((_, index) => (
        <div
          key={index}
          className={cn(
            layout === "grid" && index % 2 === 0 && "grid grid-cols-2 gap-4",
          )}
        >
          {showLabels && (
            <Skeleton className="h-4 w-24 mb-2" />
          )}
          <Skeleton
            className={cn(
              "w-full",
              fieldHeights[index % fieldHeights.length],
            )}
          />
        </div>
      ))}

      {showSubmit && (
        <div className="flex gap-3 pt-4">
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-32" />
        </div>
      )}
    </div>
  );
}

// ============================================
// SKELETON PROFILE COMPONENT
// ============================================

interface SkeletonProfileProperties {
  /** Show cover photo */
  showCover?: boolean;
  /** Show bio */
  showBio?: boolean;
  /** Number of stats */
  statsCount?: number;
  /** Show action buttons */
  showActions?: boolean;
  /** Additional class names */
  className?: string;
}

export function SkeletonProfile({
  showCover = true,
  showBio = true,
  statsCount = 4,
  showActions = true,
  className,
}: SkeletonProfileProperties) {
  return (
    <div
      role="status"
      aria-label="Loading profile content"
      aria-busy="true"
      className={cn("space-y-4", className)}
    >
      {/* Cover Photo */}
      {showCover && (
        <Skeleton className="h-32 w-full rounded-xl" />
      )}

      {/* Profile Header */}
      <div className="flex items-end gap-4 -mt-12 relative z-10">
        <Skeleton rounded="full" className="h-24 w-24 border-4 border-white dark:border-slate-800" />
        <div className="flex-1 pb-2">
          <Skeleton className="h-6 w-40 mb-2" />
          <Skeleton className="h-4 w-32" />
        </div>
        {showActions && (
          <div className="flex gap-2 pb-2">
            <Skeleton className="h-9 w-24" />
            <Skeleton className="h-9 w-24" />
          </div>
        )}
      </div>

      {/* Bio */}
      {showBio && (
        <div className="space-y-2 pt-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 pt-4">
        {Array.from({ length: statsCount }).map((_, index) => (
          <div
            key={index}
            className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-800"
          >
            <Skeleton className="h-6 w-12 mx-auto mb-1" />
            <Skeleton className="h-3 w-16 mx-auto" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================
// SKELETON CHART COMPONENT
// ============================================

interface SkeletonChartProperties {
  /** Chart type for styling */
  type?: "bar" | "line" | "pie" | "area";
  /** Number of data points */
  dataPoints?: number;
  /** Show legend */
  showLegend?: boolean;
  /** Show axes */
  showAxes?: boolean;
  /** Height of chart */
  height?: string | number;
  /** Additional class names */
  className?: string;
}

export function SkeletonChart({
  type = "bar",
  dataPoints = 6,
  showLegend = true,
  showAxes = true,
  height = 200,
  className,
}: SkeletonChartProperties) {
  return (
    <div
      role="status"
      aria-label="Loading chart content"
      aria-busy="true"
      className={cn("relative", className)}
      style={{ height }}
    >
      {/* Chart Area */}
      <div className="absolute inset-0 flex items-end justify-around gap-2 p-4">
        {Array.from({ length: dataPoints }).map((_, index) => {
          const heights = ["40%", "65%", "45%", "80%", "55%", "70%", "60%", "85%"];
          return (
            <div
              key={index}
              className={cn(
                "flex-1 bg-slate-100 dark:bg-slate-700 rounded-t",
                type === "bar" && "",
                type === "line" && "h-1 rounded-full",
                type === "pie" && "rounded-full",
                type === "area" && "rounded-t",
              )}
              style={{ height: heights[index % heights.length] }}
            />
          );
        })}
      </div>

      {/* X-Axis */}
      {showAxes && (
        <div className="absolute bottom-0 left-0 right-0 flex justify-around p-2 border-t border-slate-200 dark:border-slate-700">
          {Array.from({ length: dataPoints }).map((_, index) => (
            <Skeleton key={index} className="h-3 w-8" />
          ))}
        </div>
      )}

      {/* Legend */}
      {showLegend && (
        <div className="absolute top-0 right-0 flex gap-3 p-2">
          <div className="flex items-center gap-1">
            <Skeleton className="h-3 w-3 rounded-full" />
            <Skeleton className="h-2 w-12" />
          </div>
          <div className="flex items-center gap-1">
            <Skeleton className="h-3 w-3 rounded-full" />
            <Skeleton className="h-2 w-12" />
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================
// SKELETON DASHBOARD COMPONENT
// ============================================

interface SkeletonDashboardProperties {
  /** Number of widget rows */
  rows?: number;
  /** Number of columns per row */
  columns?: number;
  /** Show sidebar */
  showSidebar?: boolean;
  /** Show header */
  showHeader?: boolean;
  /** Additional class names */
  className?: string;
}

export function SkeletonDashboard({
  rows = 3,
  columns = 3,
  showSidebar = true,
  showHeader = true,
  className,
}: SkeletonDashboardProperties) {
  const widgetTypes = [
    "stat", // Stat card
    "chart", // Mini chart
    "list", // List widget
    "table", // Table widget
    "card", // Generic card
  ];

  return (
    <div
      role="status"
      aria-label="Loading dashboard content"
      aria-busy="true"
      className={cn("space-y-4", className)}
    >
      {/* Header */}
      {showHeader && (
        <div className="flex items-center justify-between mb-6">
          <div className="space-y-2">
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-9 w-32" />
            <Skeleton className="h-9 w-9" />
          </div>
        </div>
      )}

      {/* Main Content Grid */}
      <div className={showSidebar ? "grid grid-cols-1 lg:grid-cols-4 gap-4" : "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"}>
        {/* Sidebar (if shown) */}
        {showSidebar && (
          <div className="lg:col-span-1 space-y-4">
            {/* Profile Widget */}
            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3 mb-4">
                <Skeleton rounded="full" className="h-12 w-12" />
                <div className="space-y-1">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-3 w-16" />
                </div>
              </div>
              <div className="space-y-2">
                <Skeleton className="h-2 w-full" />
                <Skeleton className="h-2 w-3/4" />
              </div>
            </div>

            {/* Quick Stats */}
            <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <Skeleton className="h-4 w-20 mb-3" />
              {Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="flex justify-between py-2">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-3 w-8" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Widget Grid */}
        <div className={showSidebar ? "lg:col-span-3" : "col-span-3"}>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <div
              key={rowIndex}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4"
            >
              {Array.from({ length: columns }).map((_, colIndex) => {
                const widgetType = widgetTypes[(rowIndex * columns + colIndex) % widgetTypes.length];
                
                return (
                  <div
                    key={`${rowIndex}-${colIndex}`}
                    className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  >
                    {/* Stat Widget */}
                    {widgetType === "stat" && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Skeleton className="h-4 w-20" />
                          <Skeleton className="h-8 w-8 rounded-full" />
                        </div>
                        <Skeleton className="h-8 w-16" />
                        <Skeleton className="h-2 w-full rounded-full" />
                      </div>
                    )}

                    {/* Chart Widget */}
                    {widgetType === "chart" && (
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-24 w-full rounded" />
                      </div>
                    )}

                    {/* List Widget */}
                    {widgetType === "list" && (
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-24 mb-2" />
                        {Array.from({ length: 4 }).map((__, i) => (
                          <div key={i} className="flex items-center gap-2">
                            <Skeleton rounded="full" className="h-6 w-6" />
                            <Skeleton className="h-3 flex-1" />
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Table Widget */}
                    {widgetType === "table" && (
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-24 mb-2" />
                        {Array.from({ length: 3 }).map((__, i) => (
                          <div key={i} className="flex items-center justify-between py-1">
                            <Skeleton className="h-3 w-32" />
                            <Skeleton className="h-3 w-12" />
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Generic Card */}
                    {widgetType === "card" && (
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-3/4" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================
// EXISTING SKELETON COMPONENTS (Enhanced)
// ============================================

export function OnboardingSkeleton() {
  return (
    <div className="space-y-6 w-full px-1">
      <div className="flex items-center gap-4 border-b border-slate-100 dark:border-slate-800 pb-6">
        <Skeleton className="h-12 w-16 rounded-[1.5rem]" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-4 w-1/3" />
        </div>
      </div>

      <div className="grid gap-6">
        <div className="space-y-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-12 w-full rounded-2xl" />
        </div>
        <div className="space-y-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-12 w-full rounded-2xl" />
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <Skeleton className="h-24 w-full rounded-2xl" />
          <Skeleton className="h-24 w-full rounded-2xl" />
        </div>
      </div>
    </div>
  );
}

export function ResumeStepSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-[75%]" />
        <Skeleton className="h-4 w-[50%]" />
      </div>

      {/* Upload Area */}
      <div className="relative">
        <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-2xl p-8 md:p-12 bg-slate-50 dark:bg-slate-800/50">
          <div className="flex flex-col items-center gap-4">
            <Skeleton className="w-16 h-16 rounded-2xl" />
            <div className="text-center space-y-2">
              <Skeleton className="h-6 w-48 mx-auto" />
              <Skeleton className="h-4 w-64 mx-auto" />
            </div>
            <Skeleton className="h-12 w-32 rounded-xl" />
          </div>
        </div>
        {/* Upload progress overlay */}
        <div className="absolute inset-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-[1px] rounded-2xl flex flex-col items-center justify-center gap-3 z-10">
          <div className="w-32 h-1 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
            <Skeleton className="h-full w-full" />
          </div>
          <Skeleton className="h-4 w-24" />
        </div>
      </div>

      {/* LinkedIn Input */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Skeleton className="h-px flex-1" />
          <Skeleton className="h-4 w-8" />
          <Skeleton className="h-px flex-1" />
        </div>
        <Skeleton className="h-12 w-full rounded-xl" />
      </div>

      {/* Parsed Preview */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Skeleton className="w-8 h-8 rounded-lg" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-32" />
              </div>
            </div>
            <Skeleton className="w-12 h-6 rounded-full" />
          </div>
        </div>
        <div className="p-4 space-y-3">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-[75%]" />
          <div className="pt-3 border-t border-slate-100 dark:border-slate-700">
            <Skeleton className="h-4 w-24 mb-2" />
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton
                  key={`skill-skeleton-${index}`}
                  className="h-6 w-16 rounded-full"
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function PreferencesStepSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-[75%]" />
        <Skeleton className="h-4 w-[50%]" />
      </div>

      {/* AI Suggestions */}
      <div className="grid md:grid-cols-2 gap-4">
        {Array.from({ length: 2 }).map((_, index) => (
          <div
            key={`ai-suggestion-${index}`}
            className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4"
          >
            <div className="flex items-center gap-3 mb-3">
              <Skeleton className="w-8 h-8 rounded-lg" />
              <div className="flex-1">
                <Skeleton className="h-4 w-32 mb-1" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, index_) => (
                <Skeleton
                  key={`ai-suggestion-${index}-item-${index_}`}
                  className="h-4 w-full"
                />
              ))}
            </div>
            <div className="flex gap-2 mt-3">
              <Skeleton className="h-8 w-20 rounded-lg" />
              <Skeleton className="h-8 w-16 rounded-lg" />
            </div>
          </div>
        ))}
      </div>

      {/* Form Fields */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-12 w-full rounded-xl" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-12 w-full rounded-xl" />
          </div>
        </div>
      </div>

      {/* Toggle Options */}
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div
            key={`preference-${index}`}
            className="flex items-center gap-4 p-4 rounded-xl border border-slate-100 dark:border-slate-700"
          >
            <Skeleton className="w-8 h-8 rounded-lg" />
            <div className="flex-1">
              <Skeleton className="h-4 w-32 mb-1" />
              <Skeleton className="h-3 w-48" />
            </div>
            <Skeleton className="w-12 h-6 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function SkillReviewStepSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-[75%]" />
        <Skeleton className="h-4 w-[50%]" />
      </div>

      {/* Skills Grid */}
      <div className="grid gap-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div
            key={`skill-review-${index}`}
            className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4"
          >
            <div className="flex items-center gap-3">
              <Skeleton className="w-10 h-10 rounded-lg" />
              <div className="flex-1">
                <Skeleton className="h-5 w-32 mb-1" />
                <Skeleton className="h-4 w-48 mb-2" />
                <div className="flex items-center gap-2">
                  <Skeleton className="h-2 w-24 rounded-full" />
                  <Skeleton className="h-4 w-16" />
                </div>
              </div>
              <Skeleton className="w-8 h-8 rounded-lg" />
            </div>
          </div>
        ))}
      </div>

      {/* Add Skills Section */}
      <div className="rounded-xl border border-dashed border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-6">
        <div className="text-center space-y-3">
          <Skeleton className="w-12 h-12 rounded-lg mx-auto" />
          <Skeleton className="h-5 w-48 mx-auto" />
          <Skeleton className="h-4 w-64 mx-auto" />
          <Skeleton className="h-10 w-32 rounded-xl mx-auto" />
        </div>
      </div>
    </div>
  );
}

export function WorkStyleStepSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-[75%]" />
        <Skeleton className="h-4 w-[50%]" />
      </div>

      {/* Questions */}
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6"
          >
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Skeleton className="w-6 h-6 rounded-full" />
                <Skeleton className="h-5 w-3/4" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 rounded-lg border border-slate-100 dark:border-slate-700"
                  >
                    <Skeleton className="w-4 h-4 rounded-full" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function JobCardSkeleton() {
  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-slate-900 p-8 text-white rounded-2xl shadow-2xl border-slate-100 h-full flex flex-col">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
            <Skeleton className="h-6 w-6 rounded" />
          </div>
          <div className="flex-1">
            <Skeleton className="h-4 w-32 mb-2" />
            <Skeleton className="h-6 w-48" />
          </div>
        </div>
        <div className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-[75%]" />
          <Skeleton className="h-20 w-full rounded-xl" />
        </div>
        <div className="flex gap-2 mt-4">
          <Skeleton className="h-10 w-24 rounded-full" />
          <Skeleton className="h-10 w-20 rounded-full" />
        </div>
      </div>
    </div>
  );
}

export function ApplicationCardSkeleton() {
  return (
    <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 animate-pulse">
      <div className="flex items-center gap-3">
        <Skeleton className="w-10 h-10 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-16" />
        </div>
        <Skeleton className="h-6 w-16 rounded-lg" />
      </div>
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Skeleton className="w-4 h-4 rounded" />
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="h-8 w-16 rounded-lg" />
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg animate-pulse"
        >
          <div className="flex items-center gap-4">
            <Skeleton className="w-10 h-10 rounded-lg" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="w-20 h-6 rounded-lg" />
            <Skeleton className="w-16 h-6 rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function PricingSkeleton() {
  return (
    <div className="min-h-screen bg-[#F7F6F3] dark:bg-slate-900 pb-20">
      {/* Hero Skeleton */}
      <div className="h-64 sm:h-80 bg-[#1A2744] dark:bg-slate-800" />
      <main className="max-w-[900px] mx-auto px-6 -mt-12 relative z-10">
        {/* Free section */}
        <div className="rounded-2xl border-2 border-[#E9E9E7] dark:border-slate-700 bg-white dark:bg-slate-800 p-8 sm:p-10 lg:p-12 shadow-lg mb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
            <div className="flex-1">
              <Skeleton className="h-3 w-24 mb-2" />
              <Skeleton className="h-10 w-64 mb-3" />
              <Skeleton className="h-4 w-full max-w-md mb-6" />
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <Skeleton className="w-5 h-5 rounded-full" />
                    <Skeleton className="h-4 w-48" />
                  </div>
                ))}
              </div>
            </div>
            <div className="lg:w-[280px] shrink-0">
              <Skeleton className="h-12 w-16 mb-1" />
              <Skeleton className="h-4 w-20 mb-6" />
              <Skeleton className="h-12 w-full rounded-lg" />
            </div>
          </div>
        </div>

        {/* Pro section */}
        <div className="rounded-2xl border border-white/10 dark:border-slate-700 bg-[#2D2A26] dark:bg-slate-800 p-8 sm:p-10 lg:p-12">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Skeleton className="h-3 w-12 bg-white/30 dark:bg-slate-600" />
                <Skeleton className="w-4 h-4 rounded bg-white/30 dark:bg-slate-600" />
              </div>
              <Skeleton className="h-8 w-56 mb-3 bg-white/30 dark:bg-slate-600" />
              <Skeleton className="h-4 w-full max-w-md mb-6 bg-white/20 dark:bg-slate-700" />
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <Skeleton className="w-5 h-5 rounded-full bg-white/30 dark:bg-slate-600" />
                    <Skeleton className="h-4 w-44 bg-white/30 dark:bg-slate-600" />
                  </div>
                ))}
              </div>
            </div>
            <div className="lg:w-[240px] shrink-0">
              <Skeleton className="h-10 w-20 mb-1 bg-white/30 dark:bg-slate-600" />
              <Skeleton className="h-3 w-28 mb-6 bg-white/20 dark:bg-slate-700" />
              <Skeleton className="h-12 w-full rounded-lg bg-white dark:bg-slate-600" />
            </div>
          </div>
        </div>

        {/* Trust */}
        <div className="mt-16 text-center">
          <Skeleton className="h-3 w-40 mx-auto mb-4" />
          <div className="flex justify-center gap-8">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-5 w-20" />
            ))}
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-24 border-t border-[#E9E9E7] dark:border-slate-700 pt-16">
          <Skeleton className="h-8 w-64 mx-auto mb-12" />
          <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="border-b border-[#E9E9E7] dark:border-slate-700 pb-6">
                <Skeleton className="h-6 w-full mb-2" />
                <Skeleton className="h-4 w-[75%]" />
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

// ============================================
// EXPORTS
// ============================================

/** Re-export all skeleton components for easy importing */
export const Skeletons = {
  Skeleton,
  SkeletonCard,
  SkeletonTable,
  SkeletonList,
  SkeletonForm,
  SkeletonProfile,
  SkeletonChart,
  SkeletonDashboard,
  OnboardingSkeleton,
  ResumeStepSkeleton,
  PreferencesStepSkeleton,
  SkillReviewStepSkeleton,
  WorkStyleStepSkeleton,
  JobCardSkeleton,
  ApplicationCardSkeleton,
  TableSkeleton,
  PricingSkeleton,
};

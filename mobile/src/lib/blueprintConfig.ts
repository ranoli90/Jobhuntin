/**
 * Blueprint-conditional UI configuration.
 *
 * Maps blueprint_key → display labels, status mappings, and feature flags
 * so the frontend can render slightly different UX per vertical without
 * scattering conditionals throughout components.
 */

import type { ApplicationStatus } from "../types";

// ---------------------------------------------------------------------------
// Per-blueprint UI config
// ---------------------------------------------------------------------------

export interface BlueprintUIConfig {
  /** Human-readable name for this vertical */
  displayName: string;

  /** Map task status → user-facing label */
  statusLabels: Record<ApplicationStatus, string>;

  /** Label for the "target" (e.g., "Job" for Sorce, "Grant" for grants) */
  targetLabel: string;

  /** Label for the action (e.g., "Apply" for jobs, "Submit" for grants) */
  actionLabel: string;

  /** Whether the swipe-based feed is used (jobs) vs. a list/search UI */
  useSwipeFeed: boolean;
}

// ---------------------------------------------------------------------------
// Registered configs
// ---------------------------------------------------------------------------

export const BLUEPRINT_CONFIGS: Record<string, BlueprintUIConfig> = {
  "job-app": {
    displayName: "Job Applications",
    statusLabels: {
      QUEUED: "Queued",
      PROCESSING: "Bot is applying\u2026",
      REQUIRES_INPUT: "Bot needs info",
      APPLIED: "Applied \u2705",
      SUBMITTED: "Submitted \u2705",
      COMPLETED: "Completed \u2705",
      FAILED: "Failed",
    },
    targetLabel: "Job",
    actionLabel: "Apply",
    useSwipeFeed: true,
  },
  grant: {
    displayName: "Grant Applications",
    statusLabels: {
      QUEUED: "Queued",
      PROCESSING: "Submitting\u2026",
      REQUIRES_INPUT: "Needs info",
      APPLIED: "Submitted \u2705",
      SUBMITTED: "Submitted \u2705",
      COMPLETED: "Completed \u2705",
      FAILED: "Failed",
    },
    targetLabel: "Grant",
    actionLabel: "Submit",
    useSwipeFeed: false,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const DEFAULT_BLUEPRINT = "job-app";

export function getBlueprintConfig(blueprintKey?: string | null): BlueprintUIConfig {
  return BLUEPRINT_CONFIGS[blueprintKey ?? DEFAULT_BLUEPRINT] ?? BLUEPRINT_CONFIGS[DEFAULT_BLUEPRINT];
}

export function getStatusLabel(
  status: ApplicationStatus,
  blueprintKey?: string | null
): string {
  const config = getBlueprintConfig(blueprintKey);
  return config.statusLabels[status] ?? status;
}

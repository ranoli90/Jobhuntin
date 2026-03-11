/**
 * Shared LinkedIn URL validation - used by ResumeStep and Onboarding to ensure consistency.
 * Matches: linkedin.com/in/username and optional path segments.
 */
export const LINKEDIN_PROFILE_REGEX =
  /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+(\/[a-zA-Z0-9_-]*)*\/?$/i;

export function isValidLinkedInUrl(url: string | null | undefined): boolean {
  if (!url || typeof url !== "string") return false;
  const trimmed = url.trim();
  return trimmed.length > 0 && LINKEDIN_PROFILE_REGEX.test(trimmed);
}

/**
 * Product Hunt launch utilities.
 *
 * Provides:
 *   - UTM parameter extraction from deep links
 *   - PH-specific analytics tagging
 *   - Launch day badge configuration
 */

import { track } from "./analytics";
import { Linking } from "react-native";

// ---------------------------------------------------------------------------
// UTM extraction
// ---------------------------------------------------------------------------

export interface UTMParams {
  utm_source: string | null;
  utm_medium: string | null;
  utm_campaign: string | null;
  utm_content: string | null;
  ref: string | null;
}

/**
 * Parse UTM parameters from a URL string.
 */
export function parseUTMParams(url: string): UTMParams {
  try {
    const parsed = new URL(url);
    return {
      utm_source: parsed.searchParams.get("utm_source"),
      utm_medium: parsed.searchParams.get("utm_medium"),
      utm_campaign: parsed.searchParams.get("utm_campaign"),
      utm_content: parsed.searchParams.get("utm_content"),
      ref: parsed.searchParams.get("ref"),
    };
  } catch {
    return { utm_source: null, utm_medium: null, utm_campaign: null, utm_content: null, ref: null };
  }
}

/**
 * Track the app open with UTM attribution.
 * Call once on app launch after getting the initial URL.
 */
export async function trackAppOpenWithAttribution(): Promise<UTMParams | null> {
  try {
    const initialUrl = await Linking.getInitialURL();
    if (!initialUrl) return null;

    const utm = parseUTMParams(initialUrl);
    if (utm.utm_source || utm.ref) {
      track("app_opened", {
        utm_source: utm.utm_source,
        utm_medium: utm.utm_medium,
        utm_campaign: utm.utm_campaign,
        utm_content: utm.utm_content,
        ref: utm.ref,
        initial_url: initialUrl,
      });
      return utm;
    }
    return null;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Product Hunt specific
// ---------------------------------------------------------------------------

/** Product Hunt post URL — update with real URL on launch day. */
export const PRODUCT_HUNT_URL = "https://www.producthunt.com/posts/sorce";

/** UTM link to embed in PH description / first comment. */
export const PH_DOWNLOAD_LINK =
  "https://sorce.app/download?utm_source=producthunt&utm_medium=referral&utm_campaign=launch_day";

/**
 * Product Hunt badge config for the landing page.
 * Embed this SVG in the web landing page on launch day.
 */
export const PH_BADGE_HTML = `
<a href="${PRODUCT_HUNT_URL}?utm_source=badge-featured"
   target="_blank"
   rel="noopener noreferrer">
  <img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=YOUR_POST_ID&theme=dark"
       alt="Sorce - AI that fills out job applications for you | Product Hunt"
       style="width: 250px; height: 54px;"
       width="250" height="54" />
</a>
`;

/**
 * Track a Product Hunt-sourced signup.
 */
export function trackProductHuntSignup(): void {
  track("onboarding_started", {
    utm_source: "producthunt",
    utm_campaign: "launch_day",
  });
}

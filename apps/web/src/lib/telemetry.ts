// Telemetry tracking utility - respects cookie consent
const CONSENT_KEY = 'jobhuntin-cookie-consent';

function hasAnalyticsConsent(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const consent = localStorage.getItem(CONSENT_KEY);
    if (!consent) return false;
    const parsed = JSON.parse(consent);
    return parsed.analytics !== false;
  } catch {
    return false;
  }
}

export const telemetry = {
  track: (event: string, properties?: Record<string, any>) => {
    // In development, log to console
    if (import.meta.env.DEV) {
      console.log("[Telemetry]", event + ":", properties);
      return;
    }

    // Only send to analytics if user has consented (GDPR)
    if (!hasAnalyticsConsent()) return;

    try {
      if (typeof window !== 'undefined' && (window as any).gtag) {
        (window as any).gtag('event', event, properties);
      }
    } catch (error) {
      console.warn('Telemetry tracking failed:', error);
    }
  }
};

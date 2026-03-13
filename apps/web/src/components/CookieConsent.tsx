import { useState, useEffect, useRef, useCallback } from "react";
import { FocusTrap } from "focus-trap-react";
import { Button } from "./ui/Button";
import { t, getLocale } from "../lib/i18n";
import { getConsent, saveConsent as saveConsentApi, ConsentPreferences } from "../lib/consent";

declare global {
  interface Window {
    gtag?: (command: string, ...arguments_: unknown[]) => void;
  }
}

const CONSENT_KEY = "jobhuntin-cookie-consent-v2";
const CONSENT_EXPIRY_MONTHS = 12;
const CONSENT_VERSION = "2.0";

interface ConsentPreferences {
  essential: boolean; // Always true for functionality
  analytics: boolean;
  marketing: boolean;
}

export function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState<ConsentPreferences>({
    essential: true,
    analytics: false,
    marketing: false,
  });
  const containerReference = useRef<HTMLDivElement>(null);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadConsent = async () => {
      setLoading(true);
      try {
        // Try to fetch consent from backend
        const response = await getConsent();
        const consent = response.preferences;

        // Check if consent is outdated (version or expiry)
        const isVersionOutdated = response.version !== CONSENT_VERSION;
        const lastUpdated = response.last_updated ? new Date(response.last_updated).getTime() : 0;
        let isExpired = false;

        if (lastUpdated) {
          const expiry = lastUpdated + CONSENT_EXPIRY_MONTHS * 30 * 24 * 60 * 60 * 1000;
          isExpired = Date.now() > expiry;
        }

        if (isVersionOutdated || isExpired) {
          // Remove from localStorage and show banner
          localStorage.removeItem(CONSENT_KEY);
          setVisible(true);
        } else if (consent) {
          // Load existing preferences
          setPreferences({
            essential: true,
            analytics: consent.analytics || false,
            marketing: consent.marketing || false,
          });
          // Store in localStorage as backup
          localStorage.setItem(
            CONSENT_KEY,
            JSON.stringify({
              analytics: consent.analytics || false,
              marketing: consent.marketing || false,
              ts: lastUpdated,
              version: response.version,
            }),
          );
        } else {
          // No consent found, show banner
          setVisible(true);
        }
      } catch {
        // Fallback to localStorage if API fails
        const raw = localStorage.getItem(CONSENT_KEY);
        if (!raw) {
          setVisible(true);
          return;
        }
        try {
          const consent = JSON.parse(raw);
          // Check if consent is outdated (version or expiry)
          const isVersionOutdated = consent?.version !== CONSENT_VERSION;
          const ts = consent?.ts;
          let isExpired = false;

          if (ts && typeof ts === "number") {
            const expiry = ts + CONSENT_EXPIRY_MONTHS * 30 * 24 * 60 * 60 * 1000;
            isExpired = Date.now() > expiry;
          }

          if (isVersionOutdated || isExpired) {
            localStorage.removeItem(CONSENT_KEY);
            setVisible(true);
          } else if (ts) {
            // Load existing preferences
            setPreferences({
              essential: true,
              analytics: consent.analytics || false,
              marketing: consent.marketing || false,
            });
          } else {
            setVisible(true);
          }
        } catch {
          setVisible(true);
        }
      } finally {
        setLoading(false);
      }
    };

    loadConsent();
  }, []);

  useEffect(() => {
    if (visible) {
      document.body.classList.add("cookie-consent-visible");
    } else {
      document.body.classList.remove("cookie-consent-visible");
    }
    return () => document.body.classList.remove("cookie-consent-visible");
  }, [visible]);

  // Allow reopening preferences from footer/settings
  useEffect(() => {
    const handler = () => setShowPreferences(true);
    window.addEventListener("showCookiePreferences", handler);
    return () => window.removeEventListener("showCookiePreferences", handler);
  }, []);

  const saveConsent = useCallback(async (prefs: ConsentPreferences) => {
    // Store in localStorage as backup
    localStorage.setItem(
      CONSENT_KEY,
      JSON.stringify({
        analytics: prefs.analytics,
        marketing: prefs.marketing,
        ts: Date.now(),
        version: CONSENT_VERSION,
      }),
    );

    // Sync with backend API (fire and forget, don't block UI)
    saveConsentApi(prefs).catch((err) => {
      console.error("Failed to sync consent to backend:", err);
    });

    // Update Google Analytics consent
    if (typeof window !== "undefined" && window.gtag) {
      window.gtag("consent", "update", {
        analytics_storage: prefs.analytics ? "granted" : "denied",
        ad_storage: prefs.marketing ? "granted" : "denied",
        ad_user_data: prefs.marketing ? "granted" : "denied",
        ad_personalization: prefs.marketing ? "granted" : "denied",
      });
    }

    // Dispatch custom event for other components
    window.dispatchEvent(
      new CustomEvent("cookieConsentChanged", {
        detail: prefs,
      }),
    );

    setPreferences(prefs);
    setVisible(false);
    setShowPreferences(false);
  }, []);

  const acceptAll = useCallback(() => {
    saveConsent({
      essential: true,
      analytics: true,
      marketing: true,
    });
  }, [saveConsent]);

  const acceptEssentialOnly = useCallback(() => {
    saveConsent({
      essential: true,
      analytics: false,
      marketing: false,
    });
  }, [saveConsent]);

  const saveCustomPreferences = useCallback(() => {
    saveConsent(preferences);
  }, [preferences, saveConsent]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        if (showPreferences) {
          setShowPreferences(false);
        } else {
          acceptEssentialOnly();
        }
      }
    },
    [showPreferences, acceptEssentialOnly],
  );

  if (!visible && !showPreferences) return null;

  const locale = getLocale();

  if (showPreferences) {
    return (
      <FocusTrap
        active={showPreferences}
        focusTrapOptions={{
          allowOutsideClick: false,
          escapeDeactivates: true,
        }}
      >
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div
            ref={containerReference}
            role="dialog"
            aria-modal="true"
            aria-labelledby="cookie-preferences-title"
            className="bg-white dark:bg-slate-900 rounded-xl shadow-xl max-w-md w-full p-6 border border-slate-200 dark:border-slate-700"
            onKeyDown={handleKeyDown}
          >
            <h2
              id="cookie-preferences-title"
              className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4"
            >
              {t("cookies.managePreferences", locale) || "Manage preferences"}
            </h2>

            <div className="space-y-4 mb-6">
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="essential"
                  checked={preferences.essential}
                  disabled
                  className="mt-1.5 h-4 w-4 rounded border-slate-300 text-[#455DD3] focus:ring-[#455DD3]"
                />
                <div className="flex-1">
                  <label
                    htmlFor="essential"
                    className="font-medium text-slate-900 dark:text-slate-100"
                  >
                    {t("cookies.essential", locale) || "Essential"}
                  </label>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {t("cookies.essentialDescription", locale) ||
                      "Required for the site to function."}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="analytics"
                  checked={preferences.analytics}
                  onChange={(e) =>
                    setPreferences((previous) => ({
                      ...previous,
                      analytics: e.target.checked,
                    }))
                  }
                  className="mt-1.5 h-4 w-4 rounded border-slate-300 text-[#455DD3] focus:ring-[#455DD3]"
                />
                <div className="flex-1">
                  <label
                    htmlFor="analytics"
                    className="font-medium text-slate-900 dark:text-slate-100"
                  >
                    {t("cookies.analytics", locale) || "Analytics"}
                  </label>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {t("cookies.analyticsDescription", locale) ||
                      "Helps us understand site usage."}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="marketing"
                  checked={preferences.marketing}
                  onChange={(e) =>
                    setPreferences((previous) => ({
                      ...previous,
                      marketing: e.target.checked,
                    }))
                  }
                  className="mt-1.5 h-4 w-4 rounded border-slate-300 text-[#455DD3] focus:ring-[#455DD3]"
                />
                <div className="flex-1">
                  <label
                    htmlFor="marketing"
                    className="font-medium text-slate-900 dark:text-slate-100"
                  >
                    {t("cookies.marketing", locale) || "Marketing"}
                  </label>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {t("cookies.marketingDescription", locale) ||
                      "Used for advertising and remarketing."}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setShowPreferences(false)}
                className="flex-1 min-h-[44px]"
              >
                {t("cookies.cancel", locale) || "Cancel"}
              </Button>
              <Button
                onClick={saveCustomPreferences}
                className="flex-1 min-h-[44px] bg-[#455DD3] hover:bg-[#3A4FB8]"
              >
                {t("cookies.savePreferences", locale) || "Save preferences"}
              </Button>
            </div>
          </div>
        </div>
      </FocusTrap>
    );
  }

  return (
    <FocusTrap
      active={visible}
      focusTrapOptions={{
        initialFocus: () =>
          containerReference.current?.querySelector<HTMLElement>(
            "[data-consent-accept]",
          ) ??
          containerReference.current?.querySelector<HTMLElement>("button") ??
          false,
        fallbackFocus: () => containerReference.current || document.body,
        allowOutsideClick: false,
        escapeDeactivates: false,
        clickOutsideDeactivates: false,
      }}
    >
      <div
        ref={containerReference}
        role="dialog"
        aria-modal="true"
        aria-labelledby="cookie-consent-title"
        aria-describedby="cookie-consent-description"
        className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 shadow-lg md:flex md:items-center md:justify-between md:px-8"
        onKeyDown={handleKeyDown}
      >
        <p id="cookie-consent-title" className="sr-only">
          {t("cookies.title", locale) || "Cookie consent"}
        </p>
        <p
          id="cookie-consent-description"
          className="text-sm text-slate-600 dark:text-slate-400 mb-4 md:mb-0 md:mr-6 flex-1 max-w-2xl"
        >
          {t("cookies.description", locale)}{" "}
          <a
            href="/privacy#cookies"
            className="underline text-[#455DD3] hover:text-[#3A4FB8] font-medium"
          >
            {t("cookies.privacyPolicy", locale)}
          </a>{" "}
          {t("cookies.forDetails", locale)}
        </p>
        <div className="flex flex-wrap gap-2 shrink-0 items-center">
          <Button
            variant="outline"
            size="sm"
            onClick={acceptEssentialOnly}
            data-consent-reject
            aria-label={t("cookies.rejectAll", locale)}
            className="min-h-[44px]"
          >
            {t("cookies.rejectAll", locale)}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowPreferences(true)}
            aria-label={t("cookies.managePreferences", locale)}
            className="min-h-[44px]"
          >
            {t("cookies.managePreferences", locale)}
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={acceptAll}
            data-consent-accept
            aria-label={t("cookies.acceptAll", locale)}
            className="min-h-[44px] bg-[#455DD3] hover:bg-[#3A4FB8]"
          >
            {t("cookies.acceptAll", locale)}
          </Button>
        </div>
      </div>
    </FocusTrap>
  );
}

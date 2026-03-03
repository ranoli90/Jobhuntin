import { useState, useEffect, useRef, useCallback } from 'react';
import { FocusTrap } from 'focus-trap-react';
import { Button } from './ui/Button';
import { t, getLocale } from '../lib/i18n';

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

const CONSENT_KEY = 'jobhuntin-cookie-consent';
const CONSENT_EXPIRY_MONTHS = 12; // L4: GDPR - re-prompt after 12 months

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
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const raw = localStorage.getItem(CONSENT_KEY);
    if (!raw) {
      setVisible(true);
      return;
    }
    try {
      const consent = JSON.parse(raw);
      const ts = consent?.ts;
      if (ts && typeof ts === 'number') {
        const expiry = ts + CONSENT_EXPIRY_MONTHS * 30 * 24 * 60 * 60 * 1000;
        if (Date.now() > expiry) {
          localStorage.removeItem(CONSENT_KEY);
          setVisible(true);
        } else {
          // Load existing preferences
          setPreferences({
            essential: true,
            analytics: consent.analytics || false,
            marketing: consent.marketing || false,
          });
        }
      }
    } catch {
      setVisible(true);
    }
  }, []);

  useEffect(() => {
    if (visible) {
      document.body.classList.add('cookie-consent-visible');
    } else {
      document.body.classList.remove('cookie-consent-visible');
    }
    return () => document.body.classList.remove('cookie-consent-visible');
  }, [visible]);

  const saveConsent = useCallback((prefs: ConsentPreferences) => {
    localStorage.setItem(CONSENT_KEY, JSON.stringify({ 
      analytics: prefs.analytics, 
      marketing: prefs.marketing, 
      ts: Date.now() 
    }));
    
    // Update Google Analytics consent
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('consent', 'update', {
        analytics_storage: prefs.analytics ? 'granted' : 'denied',
        ad_storage: prefs.marketing ? 'granted' : 'denied'
      });
    }
    
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

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      if (showPreferences) {
        setShowPreferences(false);
      } else {
        acceptEssentialOnly();
      }
    }
  }, [showPreferences, acceptEssentialOnly]);

  if (!visible && !showPreferences) return null;

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
            ref={containerRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="cookie-preferences-title"
            className="bg-white dark:bg-slate-900 rounded-xl shadow-xl max-w-md w-full p-6 border border-slate-200 dark:border-slate-700"
            onKeyDown={handleKeyDown}
          >
            <h2 id="cookie-preferences-title" className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">
              {t("cookies.managePreferences", getLocale())}
            </h2>
            
            <div className="space-y-4 mb-6">
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="essential"
                  checked={preferences.essential}
                  disabled
                  className="mt-1 rounded border-slate-300"
                />
                <div className="flex-1">
                  <label htmlFor="essential" className="font-medium text-slate-900 dark:text-slate-100">
                    {t("cookies.essential", getLocale())}
                  </label>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {t("cookies.essentialDescription", getLocale())}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="analytics"
                  checked={preferences.analytics}
                  onChange={(e) => setPreferences(prev => ({ ...prev, analytics: e.target.checked }))}
                  className="mt-1 rounded border-slate-300"
                />
                <div className="flex-1">
                  <label htmlFor="analytics" className="font-medium text-slate-900 dark:text-slate-100">
                    {t("cookies.analytics", getLocale())}
                  </label>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {t("cookies.analyticsDescription", getLocale())}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="marketing"
                  checked={preferences.marketing}
                  onChange={(e) => setPreferences(prev => ({ ...prev, marketing: e.target.checked }))}
                  className="mt-1 rounded border-slate-300"
                />
                <div className="flex-1">
                  <label htmlFor="marketing" className="font-medium text-slate-900 dark:text-slate-100">
                    {t("cookies.marketing", getLocale())}
                  </label>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {t("cookies.marketingDescription", getLocale())}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setShowPreferences(false)} className="flex-1">
                {t("cookies.cancel", getLocale())}
              </Button>
              <Button onClick={saveCustomPreferences} className="flex-1">
                {t("cookies.savePreferences", getLocale())}
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
        initialFocus: () => containerRef.current?.querySelector<HTMLElement>('[data-consent-reject]') ?? containerRef.current?.querySelector<HTMLElement>('button') ?? false,
        allowOutsideClick: false,
        escapeDeactivates: true,
      }}
    >
    <div
      ref={containerRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="cookie-consent-title"
      aria-describedby="cookie-consent-description"
      className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 shadow-lg md:flex md:items-center md:justify-between md:px-8"
      onKeyDown={handleKeyDown}
    >
      <p id="cookie-consent-title" className="sr-only">{t("cookies.title", getLocale())}</p>
      <p id="cookie-consent-description" className="text-sm text-slate-600 dark:text-slate-400 mb-3 md:mb-0 md:mr-6">
        {t("cookies.description", getLocale())}{' '}
        <a href="/privacy#cookies" className="underline text-brand-accent hover:text-brand-ink">
          {t("cookies.privacyPolicy", getLocale())}
        </a>{' '}
        {t("cookies.forDetails", getLocale())}
      </p>
      <div className="flex flex-wrap gap-2 shrink-0">
        <Button variant="outline" size="sm" onClick={acceptEssentialOnly} data-consent-reject aria-label={t("cookies.rejectAll", getLocale())}>
          {t("cookies.rejectAll", getLocale())}
        </Button>
        <Button variant="outline" size="sm" onClick={() => setShowPreferences(true)} aria-label={t("cookies.managePreferences", getLocale())}>
          {t("cookies.managePreferences", getLocale())}
        </Button>
        <Button variant="primary" size="sm" onClick={acceptAll} aria-label={t("cookies.acceptAll", getLocale())}>
          {t("cookies.acceptAll", getLocale())}
        </Button>
      </div>
    </div>
    </FocusTrap>
  );
}

import { useState, useEffect, useRef, useCallback } from 'react';
import { FocusTrap } from 'focus-trap-react';
import { Button } from './ui/Button';
import { t, getLocale } from '../lib/i18n';

const CONSENT_KEY = 'jobhuntin-cookie-consent';
const CONSENT_EXPIRY_MONTHS = 12; // L4: GDPR - re-prompt after 12 months

export function CookieConsent() {
  const [visible, setVisible] = useState(false);
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

  const accept = useCallback(() => {
    localStorage.setItem(CONSENT_KEY, JSON.stringify({ analytics: true, marketing: false, ts: Date.now() }));
    setVisible(false);
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('consent', 'update', { analytics_storage: 'granted', ad_storage: 'denied' });
    }
  }, []);

  const decline = useCallback(() => {
    localStorage.setItem(CONSENT_KEY, JSON.stringify({ analytics: false, marketing: false, ts: Date.now() }));
    setVisible(false);
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('consent', 'update', { analytics_storage: 'denied', ad_storage: 'denied' });
    }
  }, []);

  if (!visible) return null;

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      decline();
    }
  }, [decline]);

  return (
    <FocusTrap
      active={visible}
      focusTrapOptions={{
        initialFocus: () => containerRef.current?.querySelector<HTMLElement>('[data-consent-reject]') ?? containerRef.current?.querySelector<HTMLElement>('button') ?? false,
        allowOutsideClick: false,
        escapeDeactivates: false,
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
        <Button variant="outline" size="sm" onClick={decline} data-consent-reject aria-label={t("cookies.rejectAll", getLocale())}>
          {t("cookies.rejectAll", getLocale())}
        </Button>
        <a
          href="/privacy#cookies"
          className="inline-flex items-center justify-center h-9 min-h-[36px] px-3 text-sm font-medium rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-400 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          aria-label={t("cookies.managePreferences", getLocale())}
        >
          {t("cookies.managePreferences", getLocale())}
        </a>
        <Button variant="primary" size="sm" onClick={accept} aria-label={t("cookies.acceptAnalytics", getLocale())}>
          {t("cookies.acceptAnalytics", getLocale())}
        </Button>
      </div>
    </div>
    </FocusTrap>
  );
}

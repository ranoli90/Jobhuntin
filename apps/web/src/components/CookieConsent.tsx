import { useState, useEffect, useRef, useCallback } from 'react';
import { FocusTrap } from 'focus-trap-react';
import { Button } from './ui/Button';

const CONSENT_KEY = 'jobhuntin-cookie-consent';

export function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const consent = localStorage.getItem(CONSENT_KEY);
    if (!consent) {
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
      <p id="cookie-consent-title" className="sr-only">Cookie consent</p>
      <p id="cookie-consent-description" className="text-sm text-slate-600 dark:text-slate-400 mb-3 md:mb-0 md:mr-6">
        We use cookies for analytics to improve your experience. By clicking &quot;Accept analytics&quot;, you consent
        to analytics cookies. &quot;Reject all&quot; uses only essential cookies. Press Escape to reject. See our{' '}
        <a href="/privacy#cookies" className="underline text-brand-accent hover:text-brand-ink">
          Privacy Policy
        </a>{' '}
        for details.
      </p>
      <div className="flex flex-wrap gap-2 shrink-0">
        <Button variant="outline" size="sm" onClick={decline} data-consent-reject aria-label="Reject all non-essential cookies">
          Reject all
        </Button>
        <a
          href="/privacy#cookies"
          className="inline-flex items-center justify-center h-9 min-h-[36px] px-3 text-sm font-medium rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-400 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          aria-label="Manage cookie preferences"
        >
          Manage preferences
        </a>
        <Button variant="primary" size="sm" onClick={accept} aria-label="Accept analytics cookies">
          Accept analytics
        </Button>
      </div>
    </div>
    </FocusTrap>
  );
}

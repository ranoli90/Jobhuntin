import { useState, useEffect, useRef, useCallback } from 'react';
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

  const accept = useCallback(() => {
    localStorage.setItem(CONSENT_KEY, JSON.stringify({ analytics: true, ts: Date.now() }));
    setVisible(false);
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('consent', 'update', { analytics_storage: 'granted' });
    }
  }, []);

  const decline = useCallback(() => {
    localStorage.setItem(CONSENT_KEY, JSON.stringify({ analytics: false, ts: Date.now() }));
    setVisible(false);
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('consent', 'update', { analytics_storage: 'denied' });
    }
  }, []);

  // Focus trap: keep focus within dialog when visible
  useEffect(() => {
    if (!visible || !containerRef.current) return;

    const el = containerRef.current;
    const focusables = el.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusables[0];
    const last = focusables[focusables.length - 1];

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };

    first?.focus();
    el.addEventListener('keydown', handleKeyDown);
    return () => el.removeEventListener('keydown', handleKeyDown);
  }, [visible]);

  if (!visible) return null;

  return (
    <div
      ref={containerRef}
      role="dialog"
      aria-modal="true"
      aria-label="Cookie consent"
      aria-describedby="cookie-consent-description"
      className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white border-t border-slate-200 shadow-lg md:flex md:items-center md:justify-between md:px-8"
    >
      <p id="cookie-consent-description" className="text-sm text-slate-600 mb-3 md:mb-0 md:mr-6">
        We use cookies for analytics to improve your experience. By clicking &quot;Accept all&quot;, you consent
        to the use of cookies. See our{' '}
        <a href="/privacy" className="underline text-brand-accent hover:text-brand-ink">
          Privacy Policy
        </a>{' '}
        for details.
      </p>
      <div className="flex gap-3 shrink-0">
        <Button variant="outline" size="sm" onClick={decline} aria-label="Reject all cookies">
          Reject all
        </Button>
        <Button variant="primary" size="sm" onClick={accept} aria-label="Accept all cookies">
          Accept all
        </Button>
      </div>
    </div>
  );
}

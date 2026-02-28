import { useState, useEffect } from 'react';
import { Button } from './ui/Button';

const CONSENT_KEY = 'jobhuntin-cookie-consent';

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem(CONSENT_KEY);
    if (!consent) {
      setVisible(true);
    }
  }, []);

  const accept = () => {
    localStorage.setItem(CONSENT_KEY, JSON.stringify({ analytics: true, ts: Date.now() }));
    setVisible(false);
  };

  const decline = () => {
    localStorage.setItem(CONSENT_KEY, JSON.stringify({ analytics: false, ts: Date.now() }));
    setVisible(false);
    // Disable GA if already loaded
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('consent', 'update', {
        analytics_storage: 'denied',
      });
    }
  };

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white border-t border-slate-200 shadow-lg md:flex md:items-center md:justify-between md:px-8"
    >
      <p className="text-sm text-slate-600 mb-3 md:mb-0 md:mr-6">
        We use cookies for analytics to improve your experience. By clicking "Accept", you consent
        to the use of cookies.{' '}
        <a href="/privacy" className="underline text-brand-accent hover:text-brand-ink">
          Privacy Policy
        </a>
      </p>
      <div className="flex gap-3 shrink-0">
        <Button variant="outline" size="sm" onClick={decline}>
          Decline
        </Button>
        <Button variant="primary" size="sm" onClick={accept}>
          Accept
        </Button>
      </div>
    </div>
  );
}

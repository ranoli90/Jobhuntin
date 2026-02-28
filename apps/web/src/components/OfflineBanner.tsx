import { useState, useEffect } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';

const MAX_OFFLINE_DISPLAY_MS = 10000; // Auto-dismiss after 10s to reduce intrusion

export function OfflineBanner() {
  const [offline, setOffline] = useState(!navigator.onLine);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const goOffline = () => {
      setOffline(true);
      setDismissed(false);
    };
    const goOnline = () => setOffline(false);
    window.addEventListener('offline', goOffline);
    window.addEventListener('online', goOnline);
    return () => {
      window.removeEventListener('offline', goOffline);
      window.removeEventListener('online', goOnline);
    };
  }, []);

  // Auto-dismiss after a while to reduce intrusion
  useEffect(() => {
    if (!offline || dismissed) return;
    const t = setTimeout(() => setDismissed(true), MAX_OFFLINE_DISPLAY_MS);
    return () => clearTimeout(t);
  }, [offline, dismissed]);

  if (!offline || dismissed) return null;

  return (
    <div role="alert" className="fixed top-0 left-0 right-0 z-[100] bg-amber-700 text-white px-4 py-2 text-center text-sm font-medium flex items-center justify-center gap-2">
      <WifiOff className="w-4 h-4 shrink-0" aria-hidden />
      <span>You&apos;re offline. Some features may be unavailable.</span>
      <button
        type="button"
        onClick={() => window.location.reload()}
        className="ml-2 flex items-center gap-1 px-2 py-1 rounded bg-white/20 hover:bg-white/30 transition-colors text-xs font-bold"
        aria-label="Retry connection"
      >
        <RefreshCw className="w-3 h-3" aria-hidden />
        Retry
      </button>
    </div>
  );
}

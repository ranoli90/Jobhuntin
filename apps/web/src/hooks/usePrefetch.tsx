import * as React from "react";
import { useNavigate, useLocation } from "react-router-dom";

// Prefetch cache to avoid duplicate requests
const prefetchCache = new Set<string>();

interface PrefetchOptions {
  delay?: number;
  priority?: "high" | "low";
}

export function usePrefetch() {
  const navigate = useNavigate();
  const location = useLocation();

  const prefetch = React.useCallback(
    (path: string, options: PrefetchOptions = {}) => {
      const { delay = 100, priority = "low" } = options;

      // Don't prefetch current page
      if (path === location.pathname) return;

      // Don't prefetch if already cached
      if (prefetchCache.has(path)) return;

      const timer = setTimeout(() => {
        // Use requestIdleCallback for low priority or setTimeout as fallback
        const schedule =
          priority === "low" && "requestIdleCallback" in window
            ? window.requestIdleCallback
            : (callback: () => void) => setTimeout(callback, 0);

        schedule(() => {
          // Mark as cached
          prefetchCache.add(path);

          // Prefetch route component if it's a code-split route
          // This would need to be integrated with your route definitions
          const link = document.createElement("link");
          link.rel = "prefetch";
          link.href = path;
          document.head.append(link);
        });
      }, delay);

      return () => clearTimeout(timer);
    },
    [location.pathname],
  );

  const prefetchWithNavigate = React.useCallback(
    (path: string) => {
      prefetch(path, { priority: "high" });
      navigate(path);
    },
    [prefetch, navigate],
  );

  return { prefetch, prefetchWithNavigate };
}

// Hook for hover-based prefetching
export function useHoverPrefetch() {
  const { prefetch } = usePrefetch();

  return React.useCallback(
    (path: string) => ({
      onMouseEnter: () => prefetch(path),
      onFocus: () => prefetch(path),
    }),
    [prefetch],
  );
}

// Component wrapper for links with prefetch
interface PrefetchLinkProperties extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  to: string;
  children: React.ReactNode;
  prefetchDelay?: number;
}

export function PrefetchLink({
  to,
  children,
  prefetchDelay = 100,
  onMouseEnter,
  onFocus,
  ...properties
}: PrefetchLinkProperties) {
  const { prefetch } = usePrefetch();

  const handleMouseEnter = React.useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>) => {
      prefetch(to, { delay: prefetchDelay });
      onMouseEnter?.(e);
    },
    [prefetch, to, prefetchDelay, onMouseEnter],
  );

  const handleFocus = React.useCallback(
    (e: React.FocusEvent<HTMLAnchorElement>) => {
      prefetch(to, { delay: prefetchDelay });
      onFocus?.(e);
    },
    [prefetch, to, prefetchDelay, onFocus],
  );

  return (
    <a
      href={to}
      onMouseEnter={handleMouseEnter}
      onFocus={handleFocus}
      {...properties}
    >
      {children}
    </a>
  );
}

// Utility to prefetch multiple routes at once
export function prefetchRoutes(paths: string[]) {
  for (const path of paths) {
    if (prefetchCache.has(path)) continue;

    prefetchCache.add(path);
    const link = document.createElement("link");
    link.rel = "prefetch";
    link.href = path;
    document.head.append(link);
  }
}

// Preload critical routes on app mount
export function usePrefetchCriticalRoutes() {
  React.useEffect(() => {
    const criticalRoutes = ["/pricing", "/login", "/about"];

    // Prefetch after initial page load
    const timer = setTimeout(() => {
      prefetchRoutes(criticalRoutes);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);
}

export default usePrefetch;

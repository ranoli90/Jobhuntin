import { useState, useEffect, useRef } from "react";

/**
 * Dynamically imports JSON data to avoid bundling it in the initial chunk.
 * Pass a stable import, e.g. () => import('../data/locations.json').
 */
export function useDynamicData<T>(importFn: () => Promise<{ default: T }>): {
  data: T | null;
  loading: boolean;
  error: Error | null;
} {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const fnRef = useRef(importFn);
  fnRef.current = importFn;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fnRef.current()
      .then((mod) => {
        if (!cancelled) {
          setData(mod.default);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, loading, error };
}

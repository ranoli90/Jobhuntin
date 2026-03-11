import { useState, useEffect, useRef } from "react";

/**
 * Dynamically imports JSON data to avoid bundling it in the initial chunk.
 * Pass a stable import, e.g. () => import('../data/locations.json').
 */
export function useDynamicData<T>(
  importFunction: () => Promise<{ default: T }>,
): {
  data: T | null;
  loading: boolean;
  error: Error | null;
} {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const functionReference = useRef(importFunction);
  functionReference.current = importFunction;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    functionReference
      .current()
      .then((module_) => {
        if (!cancelled) {
          setData(module_.default);
        }
      })
      .catch((error_) => {
        if (!cancelled) {
          setError(
            error_ instanceof Error ? error_ : new Error(String(error_)),
          );
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

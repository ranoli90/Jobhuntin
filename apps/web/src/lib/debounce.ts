import { useCallback, useRef } from "react";

/**
 * Debounce hook for delaying function execution
 * @param func - Function to debounce
 * @param delay - Delay in milliseconds
 * @param deps - Dependencies for the callback
 * @returns Debounced function
 */
export function useDebounce<T extends (...arguments_: any[]) => any>(
  function_: T,
  delay: number,
  deps: React.DependencyList = [],
): T {
  const timeoutReference = useRef<NodeJS.Timeout>();

  return useCallback((...arguments_: Parameters<T>) => {
    if (timeoutReference.current) {
      clearTimeout(timeoutReference.current);
    }

    timeoutReference.current = setTimeout(() => {
      function_(...arguments_);
    }, delay);
  }, deps) as T;
}

/**
 * Simple debounce function for non-hook usage
 */
export function debounce<T extends (...arguments_: any[]) => any>(
  function_: T,
  delay: number,
): (...arguments_: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;

  return (...arguments_: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => function_(...arguments_), delay);
  };
}

/**
 * Throttle hook for limiting function execution frequency
 */
export function useThrottle<T extends (...arguments_: any[]) => any>(
  function_: T,
  limit: number,
  deps: React.DependencyList = [],
): T {
  const inThrottle = useRef(false);

  return useCallback((...arguments_: Parameters<T>) => {
    if (!inThrottle.current) {
      function_(...arguments_);
      inThrottle.current = true;
      setTimeout(() => {
        inThrottle.current = false;
      }, limit);
    }
  }, deps) as T;
}

/**
 * Simple throttle function for non-hook usage
 */
export function throttle<T extends (...arguments_: any[]) => any>(
  function_: T,
  limit: number,
): (...arguments_: Parameters<T>) => void {
  let inThrottle: boolean;

  return (...arguments_: Parameters<T>) => {
    if (!inThrottle) {
      function_(...arguments_);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

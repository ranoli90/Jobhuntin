import { useCallback, useRef } from 'react';

/**
 * Debounce hook for delaying function execution
 * @param func - Function to debounce
 * @param delay - Delay in milliseconds
 * @param deps - Dependencies for the callback
 * @returns Debounced function
 */
export function useDebounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number,
  deps: React.DependencyList = []
): T {
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      func(...args);
    }, delay);
  }, deps) as T;
}

/**
 * Simple debounce function for non-hook usage
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

/**
 * Throttle hook for limiting function execution frequency
 */
export function useThrottle<T extends (...args: any[]) => any>(
  func: T,
  limit: number,
  deps: React.DependencyList = []
): T {
  const inThrottle = useRef(false);

  return useCallback((...args: Parameters<T>) => {
    if (!inThrottle.current) {
      func(...args);
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
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

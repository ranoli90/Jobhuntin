/**
 * Wrap a lazy component with its own ErrorBoundary for isolated error handling.
 * This prevents one failed component from crashing the entire app.
 */

import React, { Suspense } from 'react';
import { ErrorBoundary } from './ErrorBoundary';
import { LoadingSpinner } from './ui/LoadingSpinner';

interface SafeLazyProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  name?: string;
}

export function SafeLazy({ children, fallback, name }: SafeLazyProps) {
  return (
    <ErrorBoundary 
      showToast 
      fallback={
        <div className="p-8 text-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-2">
            Failed to load {name || 'component'}
          </h3>
          <p className="text-gray-600 dark:text-slate-400 mb-4">
            Please try refreshing the page
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Refresh Page
          </button>
        </div>
      }
    >
      <Suspense fallback={fallback || <LoadingSpinner label="Loading..." />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}

/**
 * HOC to wrap a lazy-loaded component with SafeLazy
 */
export function withSafeLazy<P extends object>(
  Component: React.ComponentType<P>,
  name?: string
): React.FC<P> {
  return function SafeLazyWrapper(props: P) {
    return (
      <SafeLazy name={name}>
        <Component {...props} />
      </SafeLazy>
    );
  };
}

import React from 'react';
import { AlertCircle, RefreshCw, Home, ArrowLeft } from 'lucide-react';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';
import { pushToast } from '../lib/toast';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  showToast?: boolean;
  reportError?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ error, errorInfo });

    // Report error if enabled
    if (this.props.reportError && !import.meta.env.DEV) {
      this._reportError({ error, errorInfo });
    }
    
    // Show user-facing toast
    if (this.props.showToast) {
      pushToast({
        title: "Something went wrong",
        description: "We've been notified. Please try refreshing the page.",
        tone: "error",
      });
    }
    
    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  _reportError = async (errorDetails: { error: Error; errorInfo: React.ErrorInfo }) => {
    try {
      // Here you could integrate with error reporting services like Sentry
      if (import.meta.env.DEV) console.error('Error reported:', errorDetails);
    } catch (reportingError) {
      if (import.meta.env.DEV) console.error('Failed to report error:', reportingError);
    }
  };

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-6 max-w-md mx-auto text-center">
          <div className="mb-4">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-2">Something went wrong</h2>
          <p className="text-gray-600 dark:text-slate-400 mb-4">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Try again
            </button>
            <a
              href="mailto:support@jobhuntin.com?subject=Error%20Report"
              className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors font-medium text-center"
            >
              Report issue
            </a>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Simple async error boundary hook
export function useAsyncError() {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = React.useCallback(() => {
    setError(null);
  }, []);

  const catchError = React.useCallback((error: Error) => {
    setError(error);
  }, []);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return { catchError, resetError, error };
}

// HOC for wrapping components with error boundaries
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Partial<ErrorBoundaryProps>
) {
  return function WrappedComponent(props: P) {
    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}

// Enhanced Error Fallback UI
interface ErrorFallbackProps {
  error: Error | null;
  onReset?: () => void;
  className?: string;
}

export function ErrorFallback({ error, onReset, className }: ErrorFallbackProps) {
  const handleGoBack = () => {
    window.history.back();
  };

  const handleGoHome = () => {
    window.location.href = "/";
  };

  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div
      className={cn(
        "min-h-screen bg-slate-50 flex items-center justify-center p-4",
        className
      )}
    >
      <div className="max-w-md w-full bg-white rounded-3xl shadow-xl border border-slate-200 p-8 text-center">
        <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <AlertCircle className="w-10 h-10 text-red-500" />
        </div>

        <h1 className="text-2xl font-black text-slate-900 mb-3">
          Something went wrong
        </h1>

        <p className="text-slate-500 mb-6 leading-relaxed">
          We apologize for the inconvenience. An unexpected error has occurred.
          Our team has been notified.
        </p>

        {error && import.meta.env.DEV && (
          <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-200 text-left overflow-auto">
            <p className="text-xs font-mono text-red-600 mb-2">{error.toString()}</p>
            {error.stack && (
              <pre className="text-[10px] font-mono text-slate-400 whitespace-pre-wrap">
                {error.stack}
              </pre>
            )}
          </div>
        )}

        <div className="space-y-3">
          {onReset && (
            <Button
              onClick={onReset}
              className="w-full h-12 rounded-xl"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          )}

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handleGoBack}
              className="flex-1 h-12 rounded-xl"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>

            <Button
              variant="outline"
              onClick={handleGoHome}
              className="flex-1 h-12 rounded-xl"
            >
              <Home className="w-4 h-4 mr-2" />
              Home
            </Button>
          </div>

          <button
            onClick={handleReload}
            className="text-sm text-slate-400 hover:text-slate-600 transition-colors"
          >
            Reload page
          </button>
        </div>
      </div>
    </div>
  );
}

// Route-specific error boundary wrapper
interface RouteErrorBoundaryProps {
  children: React.ReactNode;
}

export function RouteErrorBoundary({ children }: RouteErrorBoundaryProps) {
  return (
    <ErrorBoundary
      showToast
      reportError
      fallback={
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 mb-2">Page Error</h1>
            <p className="text-slate-500 mb-4">This page failed to load</p>
            <Button onClick={() => window.location.reload()}>
              Reload Page
            </Button>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

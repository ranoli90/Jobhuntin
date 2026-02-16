import * as React from "react";
import { AlertTriangle, RefreshCw, Bug } from "lucide-react";
import { Button } from "./ui/Button";
import { pushToast } from "../lib/toast";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onReset?: () => void;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  showToast?: boolean;
  reportError?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null, 
      errorId: null, 
      retryCount: 0 
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { 
      hasError: true, 
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });
    
    // Generate unique error ID
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.setState({ errorId });
    
    // Enhanced error logging
    const errorDetails = {
      errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      retryCount: this.state.retryCount,
    };
    
    // Log to console in development
    if (import.meta.env.DEV) {
      console.error("[ErrorBoundary] Caught error:", errorDetails);
    }
    
    // Report to error tracking service
    if (this.props.reportError && !import.meta.env.DEV) {
      this._reportError(errorDetails);
    }
    
    // Show user-facing toast
    if (this.props.showToast) {
      pushToast({
        title: "Something went wrong",
        description: "We've been notified. Please try refreshing the page.",
        tone: "error",
        action: {
          label: "Report Issue",
          onClick: () => this._reportError(errorDetails),
        },
      });
    }
    
    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  _reportError = async (errorDetails: any) => {
    try {
      // Send to error tracking service (e.g., Sentry, LogRocket, etc.)
      // This is a placeholder - implement with your error tracking service
      console.log("Error reported:", errorDetails);
      
      // Example: Sentry
      // Sentry.captureException(errorDetails.error, {
      //   extra: errorDetails,
      //   tags: ['error-boundary'],
      // });
      
      // Example: Custom endpoint
      await fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorDetails),
      });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null, 
      errorId: null, 
      retryCount: this.state.retryCount + 1 
    });
    this.props.onReset?.();
  };

  handleReload = () => {
    // Clear any cached data before reload
    if ('caches' in window) {
      caches.keys().then(names => {
        Promise.all(names.map(name => caches.delete(name)));
      });
    }
    window.location.reload();
  };

  handleRetry = () => {
    this.handleReset();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen w-full flex items-center justify-center p-6 bg-gradient-to-br from-slate-50 to-slate-100">
          <div className="max-w-lg w-full text-center space-y-8">
            {/* Error Icon */}
            <div className="mx-auto w-20 h-20 rounded-2xl bg-red-50 border border-red-200 flex items-center justify-center shadow-lg">
              <Bug className="w-10 h-10 text-red-500" />
            </div>
            
            {/* Error Message */}
            <div className="space-y-4">
              <h1 className="text-2xl font-bold text-slate-900">Something went wrong</h1>
              <p className="text-lg text-slate-600 leading-relaxed">
                An unexpected error occurred. We've been notified and are looking into it.
              </p>
              
              {/* Error ID for support */}
              {this.state.errorId && (
                <div className="p-3 bg-slate-100 rounded-lg border border-slate-200">
                  <p className="text-sm font-mono text-slate-600">
                    Error ID: {this.state.errorId}
                  </p>
                </div>
              )}
              
              {/* Retry Count */}
              {this.state.retryCount > 0 && (
                <p className="text-sm text-slate-500">
                  Retry attempt #{this.state.retryCount}
                </p>
              )}
            </div>

            {/* Development Error Details */}
            {import.meta.env.DEV && this.state.error && (
              <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-left space-y-2">
                <p className="text-sm font-semibold text-red-800">Error Details:</p>
                <p className="text-xs font-mono text-red-600 break-all whitespace-pre-wrap">
                  {this.state.error.message}
                </p>
                <p className="text-xs font-mono text-red-600 break-all whitespace-pre-wrap">
                  {this.state.error.stack}
                </p>
                <p className="text-xs font-mono text-red-600 break-all whitespace-pre-wrap">
                  Component Stack: {this.state.errorInfo?.componentStack}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                variant="outline" 
                onClick={this.handleRetry}
                className="w-full sm:w-auto"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
              <Button 
                onClick={this.handleReload}
                className="w-full sm:w-auto"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Page
              </Button>
            </div>

            {/* Support Info */}
            <div className="text-center space-y-2">
              <p className="text-sm text-slate-500">
                If the problem persists, please contact our support team.
              </p>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => this._reportError({
                  errorId: this.state.errorId,
                  error: this.state.error,
                  errorInfo: this.state.errorInfo,
                  timestamp: new Date().toISOString(),
                  userAgent: navigator.userAgent,
                  url: window.location.href,
                  retryCount: this.state.retryCount,
                })}
              >
                Report Issue
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Hook to create a resettable error boundary
 */
export function useErrorBoundary() {
  const [error, setError] = React.useState<Error | null>(null);
  const [errorId, setErrorId] = React.useState<string | null>(null);
  const [retryCount, setRetryCount] = React.useState(0);

  const resetBoundary = React.useCallback(() => {
    setError(null);
    setErrorId(null);
    setRetryCount(0);
  }, []);

  const showBoundary = React.useCallback((err: Error) => {
    setError(err);
    setErrorId(`error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    setRetryCount(prev => prev + 1);
  }, []);

  if (error) {
    throw error;
  }

  return { resetBoundary, showBoundary, error, errorId, retryCount };
}

/**
 * Async Error Boundary for handling async operations
 */
export function AsyncErrorBoundary({ 
  children, 
  fallback, 
  onError 
}: { 
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error) => void;
}) {
  const [error, setError] = React.useState<Error | null>(null);
  const [errorInfo, setErrorInfo] = React.useState<React.ErrorInfo | null>(null);

  const resetError = React.useCallback(() => {
    setError(null);
    setErrorInfo(null);
  }, []);

  const handleAsyncError = React.useCallback(async (promise: Promise<any>) => {
    try {
      return await promise;
    } catch (err) {
      setError(err as Error);
        setErrorInfo({
          componentStack: '',
        });
        
        if (onError) {
          onError(err as Error);
        }
        
        throw err;
    }
  }, [onError]);

  if (error) {
    return fallback || (
      <div className="p-4 border border-red-300 rounded-lg bg-red-50">
        <h3 className="text-red-800 font-semibold">Async Error</h3>
        <p className="text-red-600 text-sm mt-2">{error.message}</p>
        <button 
          onClick={resetError}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return <>{handleAsyncError(children)}</>;
}

/**
 * Network Error Boundary for handling network failures
 */
export function NetworkErrorBoundary({ 
  children, 
  fallback, 
  onNetworkError 
}: { 
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onNetworkError?: (error: Error) => void;
}) {
  const [networkError, setNetworkError] = React.useState<Error | null>(null);
  const [isOnline, setIsOnline] = React.useState(navigator.onLine);

  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const resetNetworkError = React.useCallback(() => {
    setNetworkError(null);
  }, []);

  const handleNetworkError = React.useCallback((error: Error) => {
    setNetworkError(error);
    if (onNetworkError) {
      onNetworkError(error);
    }
  }, [onNetworkError]);

  if (networkError || !isOnline) {
    return fallback || (
      <div className="p-4 border border-yellow-300 rounded-lg bg-yellow-50">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-3 h-3 rounded-full bg-yellow-400 animate-pulse" />
          <h3 className="text-yellow-800 font-semibold">
            {networkError ? 'Network Error' : 'Offline'}
          </h3>
        </div>
        
        <p className="text-yellow-700 text-sm mb-3">
          {networkError ? networkError.message : 'You appear to be offline. Please check your internet connection.'}
        </p>
        
        <div className="flex gap-2">
          <button 
            onClick={resetNetworkError}
            className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
          >
            Retry
          </button>
          {!isOnline && (
            <button 
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
            >
              Refresh
            </button>
          )}
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Route Error Boundary for handling navigation errors
 */
export function RouteErrorBoundary({ 
  children, 
  fallback, 
  onRouteError 
}: { 
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onRouteError?: (error: Error) => void;
}) {
  const [routeError, setRouteError] = React.useState<Error | null>(null);

  const resetRouteError = React.useCallback(() => {
    setRouteError(null);
  }, []);

  const handleRouteError = React.useCallback((error: Error) => {
    setRouteError(error);
    if (onRouteError) {
      onRouteError(error);
    }
  }, [onRouteError]);

  if (routeError) {
    return fallback || (
      <div className="p-4 border border-orange-300 rounded-lg bg-orange-50">
        <h3 className="text-orange-800 font-semibold">Navigation Error</h3>
        <p className="text-orange-700 text-sm mb-3">{routeError.message}</p>
        <button 
          onClick={resetRouteError}
          className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * HOC for wrapping components with error boundaries
 */
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

/**
 * HOC for wrapping components with async error boundaries
 */
export function withAsyncErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Partial<ErrorBoundaryProps>
) {
  return function WrappedComponent(props: P) {
    return (
      <AsyncErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </AsyncErrorBoundary>
    );
  };
}

/**
 * HOC for wrapping components with network error boundaries
 */
export function withNetworkErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Partial<ErrorBoundaryProps>
) {
  return function WrappedComponent(props: P) {
    return (
      <NetworkErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </NetworkErrorBoundary>
    );
  };
}

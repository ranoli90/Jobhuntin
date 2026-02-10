/**
 * Enhanced Error Boundary Component
 * Microsoft-level implementation with comprehensive error handling and recovery
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Bug, Send } from 'lucide-react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  isRecovering: boolean;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onRetry?: () => void;
  maxRetries?: number;
  showErrorDetails?: boolean;
  enableErrorReporting?: boolean;
}

interface ErrorReport {
  errorId: string;
  timestamp: string;
  userAgent: string;
  url: string;
  userId?: string;
  error: {
    message: string;
    stack: string;
    name: string;
  };
  componentStack: string;
  buildVersion: string;
  environment: string;
}

class EnhancedErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeouts: Map<string, any> = new Map();

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRecovering: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const errorId = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    this.setState({
      error,
      errorInfo,
      errorId,
    });

    // Call custom error handler
    this.props.onError?.(error, errorInfo);

    // Log error for debugging
    console.group('🚨 Enhanced Error Boundary Caught Error');
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Error ID:', errorId);
    console.groupEnd();

    // Send error report if enabled
    if (this.props.enableErrorReporting !== false) {
      this.sendErrorReport(error, errorInfo, errorId);
    }
  }

  private sendErrorReport = async (error: Error, errorInfo: ErrorInfo, errorId: string) => {
    try {
      const report: ErrorReport = {
        errorId,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        userId: this.getUserId(),
        error: {
          message: error.message,
          stack: error.stack || '',
          name: error.name || 'UnknownError',
        },
        componentStack: errorInfo.componentStack || '',
        buildVersion: (import.meta as any).env?.VITE_APP_VERSION || 'unknown',
        environment: import.meta.env.MODE || 'unknown',
      };

      // Send to error reporting service
      await fetch('/api/errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(report),
      }).catch(err => {
        console.warn('Failed to send error report:', err);
      });

      // Also send to external service if configured
      const externalEndpoint = (import.meta as any).env?.VITE_ERROR_REPORTING_ENDPOINT;
      if (externalEndpoint) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        fetch(externalEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(report),
          signal: controller.signal,
        }).then(() => clearTimeout(timeoutId))
          .catch(err => {
            clearTimeout(timeoutId);
            console.warn('Failed to send external error report:', err);
          });
      }
    } catch (err) {
      console.warn('Error reporting failed:', err);
    }
  };

  private getUserId(): string | undefined {
    try {
      // Try to get user ID from various sources
      return (
        (window as any).__USER_ID__ ||
        localStorage.getItem('userId') ||
        sessionStorage.getItem('userId')
      );
    } catch {
      return undefined;
    }
  }

  private handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    const { retryCount, errorId } = this.state;

    if (retryCount >= maxRetries) {
      console.warn('Max retries reached for error:', errorId);
      return;
    }

    // Clear any existing timeout for this error
    const existingTimeout = this.retryTimeouts.get(errorId || '');
    if (existingTimeout) {
      clearTimeout(existingTimeout);
      this.retryTimeouts.delete(errorId || '');
    }

    this.setState({ isRecovering: true });

    // Exponential backoff for retry
    const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);

    const timeoutId = setTimeout(() => {
      this.setState(prev => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
        retryCount: prev.retryCount + 1,
        isRecovering: false,
      }));

      this.props.onRetry?.();
    }, delay);

    if (errorId) {
      this.retryTimeouts.set(errorId, timeoutId);
    }
  };

  private handleReset = () => {
    // Clear all timeouts
    this.retryTimeouts.forEach(timeoutId => clearTimeout(timeoutId));
    this.retryTimeouts.clear();

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRecovering: false,
    });
  };

  private sendManualReport = async () => {
    const { error, errorInfo, errorId } = this.state;
    if (!error || !errorInfo) return;

    try {
      await this.sendErrorReport(error, errorInfo, errorId || 'manual');

      // Show success message
      if (typeof window !== 'undefined') {
        const message = document.createElement('div');
        message.innerHTML = `
          <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 9999;
            font-family: system-ui;
            font-size: 14px;
          ">
            ✓ Error report sent successfully
          </div>
        `;
        document.body.appendChild(message);

        setTimeout(() => {
          document.body.removeChild(message);
        }, 3000);
      }
    } catch (err) {
      console.error('Failed to send manual report:', err);
    }
  };

  componentWillUnmount() {
    // Clear all timeouts
    this.retryTimeouts.forEach(timeoutId => clearTimeout(timeoutId));
    this.retryTimeouts.clear();
  }

  render() {
    const { children, fallback, showErrorDetails = true, maxRetries = 3 } = this.props;
    const { hasError, error, errorInfo, errorId, retryCount, isRecovering } = this.state;

    if (hasError && error) {
      // Custom fallback component
      if (fallback) {
        return fallback;
      }

      const canRetry = retryCount < maxRetries;
      const isRetryableError = this.isRetryableError(error);

      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
          <div className="max-w-lg w-full bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
            {/* Error Header */}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900 mb-1">
                  Something went wrong
                </h1>
                <p className="text-sm text-slate-600">
                  We're sorry, but an unexpected error occurred.
                </p>
              </div>
            </div>

            {/* Error Actions */}
            <div className="flex gap-3 mb-6">
              {canRetry && isRetryableError && (
                <button
                  onClick={this.handleRetry}
                  disabled={isRecovering}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <RefreshCw className={`w-4 h-4 ${isRecovering ? 'animate-spin' : ''}`} />
                  {isRecovering ? 'Recovering...' : 'Try Again'}
                </button>
              )}

              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Reset
              </button>

              {this.props.enableErrorReporting !== false && (
                <button
                  onClick={this.sendManualReport}
                  className="flex items-center gap-2 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  <Send className="w-4 h-4" />
                  Report Issue
                </button>
              )}
            </div>

            {/* Error Details */}
            {showErrorDetails && (
              <details className="bg-slate-50 border border-slate-200 rounded-lg p-4 mb-6">
                <summary className="cursor-pointer font-medium text-slate-700 mb-2 hover:text-slate-900">
                  Error Details
                </summary>
                <div className="space-y-3 text-sm">
                  {errorId && (
                    <div>
                      <span className="font-medium text-slate-700">Error ID:</span>
                      <code className="ml-2 px-2 py-1 bg-slate-200 rounded text-slate-800">
                        {errorId}
                      </code>
                    </div>
                  )}

                  <div>
                    <span className="font-medium text-slate-700">Message:</span>
                    <div className="mt-1 p-2 bg-red-50 border border-red-200 rounded text-red-800">
                      {error.message}
                    </div>
                  </div>

                  {error.stack && (
                    <div>
                      <span className="font-medium text-slate-700">Stack Trace:</span>
                      <pre className="mt-1 p-2 bg-slate-100 rounded text-slate-800 text-xs overflow-auto max-h-32">
                        {error.stack}
                      </pre>
                    </div>
                  )}

                  {retryCount > 0 && (
                    <div className="text-amber-600">
                      <span className="font-medium">Retry attempts:</span> {retryCount}/{maxRetries}
                    </div>
                  )}
                </div>
              </details>
            )}

            {/* Help Section */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Bug className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">Need help?</p>
                  <p className="text-blue-700">
                    If this problem persists, please contact our support team with the Error ID above.
                    You can also try refreshing the page or clearing your browser cache.
                  </p>
                </div>
              </div>
            </div>

            {/* Debug Info (development only) */}
            {import.meta.env.DEV && errorInfo && (
              <details className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <summary className="cursor-pointer font-medium text-yellow-800 mb-2">
                  Debug Information (Development)
                </summary>
                <pre className="text-xs text-yellow-900 overflow-auto max-h-48">
                  {JSON.stringify(errorInfo, null, 2)}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return children;
  }

  private isRetryableError(error: Error): boolean {
    // Define which errors are retryable
    const retryableErrors = [
      'NetworkError',
      'TimeoutError',
      'AbortError',
      'TypeError', // Often temporary network issues
    ];

    const retryablePatterns = [
      /network/i,
      /timeout/i,
      /connection/i,
      /fetch/i,
      /502/, // Bad Gateway
      /503/, // Service Unavailable
      /504/, // Gateway Timeout
    ];

    return retryableErrors.includes(error.name) ||
      retryablePatterns.some(pattern => pattern.test(error.message));
  }
}

// Hook for using error boundaries
export function useErrorBoundary() {
  const handleError = (error: Error, errorInfo: ErrorInfo) => {
    // Log to external service
    console.error('Error caught by boundary:', error, errorInfo);

    // You can integrate with Sentry, LogRocket, etc.
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack,
          },
        },
      });
    }
  };

  return { handleError };
}

export default EnhancedErrorBoundary;

import * as React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "./ui/Button";
import { pushToast } from "../lib/toast";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onReset?: () => void;
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
    this.setState({ errorInfo });
    
    // Log to console in development, could send to error reporting service in production
    if (import.meta.env.DEV) {
      console.error("[ErrorBoundary] Caught error:", error, errorInfo);
    }
    
    // Show user-facing toast
    pushToast({
      title: "Something went wrong",
      description: "We've been notified. Please try refreshing the page.",
      tone: "error",
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    this.props.onReset?.();
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[50vh] w-full flex items-center justify-center p-6">
          <div className="max-w-md w-full text-center space-y-6">
            <div className="mx-auto w-16 h-16 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-xl font-bold text-slate-900">Something went wrong</h2>
              <p className="text-sm text-slate-500">
                An unexpected error occurred. We've been notified and are looking into it.
              </p>
            </div>

            {import.meta.env.DEV && this.state.error && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-100 text-left">
                <p className="text-xs font-mono text-red-600 break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={this.handleReset}>
                Try Again
              </Button>
              <Button onClick={this.handleReload}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Page
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

  const resetBoundary = React.useCallback(() => {
    setError(null);
  }, []);

  const showBoundary = React.useCallback((err: Error) => {
    setError(err);
  }, []);

  if (error) {
    throw error;
  }

  return { resetBoundary, showBoundary };
}

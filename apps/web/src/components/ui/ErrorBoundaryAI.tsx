import React, { Component, ReactNode, ReactElement } from "react";
import { AlertCircle, RefreshCw, AlertTriangle, Wifi, FileWarning } from "lucide-react";
import { Button } from "./Button";
import { cn } from "../../lib/utils";

export type AIErrorType = "rate_limit" | "validation" | "network" | "server" | "unknown";

interface AIErrorInfo {
  type: AIErrorType;
  message: string;
  userMessage: string;
  retryable: boolean;
  suggestedAction?: string;
}

function categorizeError(error: Error): AIErrorInfo {
  const message = error.message.toLowerCase();
  const status = (error as Error & { status?: number }).status;

  if (status === 429 || message.includes("rate limit") || message.includes("too many requests")) {
    return {
      type: "rate_limit",
      message: error.message,
      userMessage: "You're making requests too quickly. Please wait a moment and try again.",
      retryable: true,
      suggestedAction: "Wait 30 seconds before retrying",
    };
  }

  if (status === 400 || status === 422 || message.includes("invalid") || message.includes("validation")) {
    return {
      type: "validation",
      message: error.message,
      userMessage: "The request data is invalid. Please check your input and try again.",
      retryable: false,
      suggestedAction: "Review your input data",
    };
  }

  if (
    message.includes("network") ||
    message.includes("fetch") ||
    message.includes("timeout") ||
    message.includes("connection") ||
    status === 503
  ) {
    return {
      type: "network",
      message: error.message,
      userMessage: "A network error occurred. Please check your connection and try again.",
      retryable: true,
      suggestedAction: "Check your internet connection",
    };
  }

  if (status && status >= 500) {
    return {
      type: "server",
      message: error.message,
      userMessage: "Something went wrong on our end. Our team has been notified.",
      retryable: true,
      suggestedAction: "Try again in a few minutes",
    };
  }

  return {
    type: "unknown",
    message: error.message,
    userMessage: "An unexpected error occurred. Please try again.",
    retryable: true,
  };
}

interface Props {
  children: ReactNode;
  fallback?: ReactElement;
  onRetry?: () => void;
  onReportError?: (error: Error, errorInfo: AIErrorInfo) => void;
  className?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: AIErrorInfo | null;
}

export class ErrorBoundaryAI extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): State {
    const errorInfo = categorizeError(error);
    return { hasError: true, error, errorInfo };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("AI Error caught by boundary:", error, errorInfo);

    if (this.props.onReportError && this.state.errorInfo) {
      this.props.onReportError(error, this.state.errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    this.props.onRetry?.();
  };

  handleReportError = () => {
    if (this.state.error && this.state.errorInfo && this.props.onReportError) {
      this.props.onReportError(this.state.error, this.state.errorInfo);
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { errorInfo } = this.state;
      if (!errorInfo) return null;

      return (
        <div className={cn("flex items-center justify-center p-8", this.props.className)}>
          <div className="max-w-md w-full bg-white rounded-xl shadow-lg border border-slate-200 p-6">
            <div className="flex items-center justify-center w-14 h-14 mx-auto rounded-full mb-4">
              {errorInfo.type === "rate_limit" && (
                <div className="bg-amber-100 rounded-full p-3">
                  <AlertTriangle className="w-6 h-6 text-amber-600" />
                </div>
              )}
              {errorInfo.type === "network" && (
                <div className="bg-blue-100 rounded-full p-3">
                  <Wifi className="w-6 h-6 text-blue-600" />
                </div>
              )}
              {errorInfo.type === "validation" && (
                <div className="bg-purple-100 rounded-full p-3">
                  <FileWarning className="w-6 h-6 text-purple-600" />
                </div>
              )}
              {(errorInfo.type === "server" || errorInfo.type === "unknown") && (
                <div className="bg-red-100 rounded-full p-3">
                  <AlertCircle className="w-6 h-6 text-red-600" />
                </div>
              )}
            </div>

            <h2 className="text-lg font-bold text-center text-slate-900 mb-2">
              {errorInfo.type === "rate_limit" && "Rate Limited"}
              {errorInfo.type === "network" && "Connection Error"}
              {errorInfo.type === "validation" && "Invalid Request"}
              {errorInfo.type === "server" && "Server Error"}
              {errorInfo.type === "unknown" && "Something Went Wrong"}
            </h2>

            <p className="text-center text-slate-600 mb-4 text-sm">
              {errorInfo.userMessage}
            </p>

            {errorInfo.suggestedAction && (
              <p className="text-center text-slate-500 text-xs mb-4">
                Suggestion: {errorInfo.suggestedAction}
              </p>
            )}

            <div className="flex flex-col gap-2">
              {errorInfo.retryable && (
                <Button
                  onClick={this.handleRetry}
                  className="w-full gap-2"
                  variant="primary"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </Button>
              )}

              <Button
                onClick={this.handleReportError}
                variant="ghost"
                className="w-full text-xs"
              >
                Report this issue
              </Button>
            </div>

            {import.meta.env.DEV && this.state.error && (
              <details className="mt-4 p-3 bg-slate-50 rounded text-xs">
                <summary className="cursor-pointer font-mono text-slate-500">
                  Error details (dev only)
                </summary>
                <pre className="mt-2 text-slate-600 overflow-auto max-h-32">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export function useAIErrorHandler() {
  const categorize = (error: Error): AIErrorInfo => categorizeError(error);

  const getErrorMessage = (error: Error): string => {
    return categorizeError(error).userMessage;
  };

  const isRetryable = (error: Error): boolean => {
    return categorizeError(error).retryable;
  };

  return {
    categorize,
    getErrorMessage,
    isRetryable,
  };
}

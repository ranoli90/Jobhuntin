import * as React from "react";
import { Button } from "./Button";
import { Card } from "./Card";
import { LoadingSpinner } from "./LoadingSpinner";
import { Wifi, WifiOff, Clock, AlertTriangle, RefreshCw } from "lucide-react";
import { resumeUploadRetry, ResumeUploadState } from "../../lib/resumeUploadRetry";

interface ResumeUploadRetryProps {
  onRetry: () => Promise<void>;
  onClear: () => void;
  className?: string;
}

/**
 * Component for handling resume upload retries with offline persistence
 */
export function ResumeUploadRetry({ onRetry, onClear, className }: ResumeUploadRetryProps) {
  const [uploadState, setUploadState] = React.useState<ResumeUploadState>({
    isUploading: false,
    canRetry: false,
    retryCount: 0,
    nextRetryIn: 0,
    isOffline: !navigator.onLine,
  });
  const [retryMessage, setRetryMessage] = React.useState<string>("");
  const [isRetrying, setIsRetrying] = React.useState(false);

  // Update state periodically
  React.useEffect(() => {
    const updateState = async () => {
      const state = await resumeUploadRetry.getUploadState();
      const message = await resumeUploadRetry.getRetryMessage();
      setUploadState(state);
      setRetryMessage(message);
    };

    updateState();
    
    // Update every second for countdown
    const interval = setInterval(updateState, 1000);
    
    return () => clearInterval(interval);
  }, []);

  // Set up automatic retry
  React.useEffect(() => {
    if (uploadState.canRetry && !uploadState.isOffline) {
      resumeUploadRetry.setupRetryTimer(async () => {
        setIsRetrying(true);
        try {
          await onRetry();
        } catch (error) {
          console.error('Auto-retry failed:', error);
        } finally {
          setIsRetrying(false);
        }
      });
    }
    
    return () => resumeUploadRetry.clearRetryTimer();
  }, [uploadState.canRetry, uploadState.isOffline, onRetry]);

  const handleManualRetry = async () => {
    if (!uploadState.canRetry || isRetrying) return;
    
    setIsRetrying(true);
    try {
      await onRetry();
    } catch (error) {
      console.error('Manual retry failed:', error);
    } finally {
      setIsRetrying(false);
    }
  };

  const handleClear = () => {
    resumeUploadRetry.clearRetryTimer();
    onClear();
  };

  // Don't render if there's no pending upload
  if (uploadState.retryCount === 0 && !uploadState.error) {
    return null;
  }

  const getVariant = (): "default" | "sunrise" | "mango" | "shell" => {
    if (uploadState.isOffline) return "sunrise";
    if (uploadState.retryCount >= 3) return "mango";
    if (uploadState.canRetry) return "shell";
    return "sunrise";
  };

  const getIcon = () => {
    if (uploadState.isOffline) return <WifiOff className="h-5 w-5" />;
    if (uploadState.retryCount >= 3) return <AlertTriangle className="h-5 w-5" />;
    if (uploadState.canRetry) return <Clock className="h-5 w-5" />;
    return <RefreshCw className="h-5 w-5" />;
  };

  return (
    <Card tone={getVariant()} shadow="lift" className={`p-4 ${className}`}>
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${
          uploadState.isOffline ? 'bg-yellow-100 text-yellow-600' :
          uploadState.retryCount >= 3 ? 'bg-red-100 text-red-600' :
          'bg-blue-100 text-blue-600'
        }`}>
          {getIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm mb-1">
            {uploadState.isOffline ? "Offline - Resume Saved" :
             uploadState.retryCount >= 3 ? "Upload Failed" :
             "Resume Upload Pending"}
          </h3>
          
          <p className="text-xs text-gray-600 mb-3">
            {retryMessage}
          </p>
          
          {uploadState.error && (
            <div className="text-xs text-red-600 mb-3 p-2 bg-red-50 rounded">
              {uploadState.error}
            </div>
          )}
          
          <div className="flex items-center gap-2">
            {uploadState.canRetry && !uploadState.isOffline && (
              <Button
                size="sm"
                onClick={handleManualRetry}
                disabled={isRetrying}
                className="text-xs"
              >
                {isRetrying ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-1" />
                    Retrying...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Retry Now
                  </>
                )}
              </Button>
            )}
            
            <Button
              size="sm"
              variant="outline"
              onClick={handleClear}
              className="text-xs"
            >
              Clear
            </Button>
          </div>
          
          {uploadState.retryCount > 0 && (
            <div className="mt-2 text-xs text-gray-500">
              Attempt {uploadState.retryCount} of 3
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

export default ResumeUploadRetry;

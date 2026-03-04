import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Sparkles, FileText, Search, Send } from "lucide-react";
import { cn } from "../../lib/utils";

interface LoadingOverlayProps {
  isLoading: boolean;
  children?: React.ReactNode;
  className?: string;
  blur?: boolean;
  message?: string;
  submessage?: string;
  variant?: "spinner" | "skeleton" | "pulse";
}

export function LoadingOverlay({
  isLoading,
  children,
  className,
  blur = true,
  message = "Loading...",
  submessage,
  variant = "spinner",
}: LoadingOverlayProps) {
  return (
    <div className={cn("relative", className)}>
      {children}
      
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className={cn(
              "absolute inset-0 z-50 flex flex-col items-center justify-center",
              blur ? "bg-white/80 backdrop-blur-sm" : "bg-white/90",
              "dark:bg-slate-900/80"
            )}
          >
            {variant === "spinner" && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
              >
                <Loader2 className="w-10 h-10 text-primary-600" />
              </motion.div>
            )}
            
            {variant === "pulse" && (
              <div className="flex space-x-2">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="w-3 h-3 bg-primary-600 rounded-full"
                    animate={{
                      scale: [1, 1.2, 1],
                      opacity: [1, 0.5, 1],
                    }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      delay: i * 0.2,
                    }}
                  />
                ))}
              </div>
            )}
            
            <p className="mt-4 text-slate-600 font-medium">{message}</p>
            {submessage && (
              <p className="mt-1 text-sm text-slate-400">{submessage}</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface LoadingStateProps {
  message?: string;
  submessage?: string;
  className?: string;
  icon?: React.ReactNode;
}

export function LoadingState({
  message = "Loading...",
  submessage,
  className,
  icon,
}: LoadingStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12", className)}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        className="mb-4"
      >
        {icon || <Loader2 className="w-8 h-8 text-primary-600" />}
      </motion.div>
      <p className="text-slate-600 font-medium">{message}</p>
      {submessage && <p className="mt-1 text-sm text-slate-400">{submessage}</p>}
    </div>
  );
}

// Page loading state with full-screen overlay
export function PageLoader({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-950">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
      >
        <Sparkles className="w-12 h-12 text-primary-600" />
      </motion.div>
      <p className="mt-6 text-slate-600 font-medium animate-pulse">{message}</p>
    </div>
  );
}

// Async action button with loading state
interface AsyncButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading: boolean;
  loadingText?: string;
  children: React.ReactNode;
}

export function AsyncButton({
  isLoading,
  loadingText = "Loading...",
  children,
  disabled,
  className,
  ...props
}: AsyncButtonProps) {
  return (
    <button
      disabled={disabled || isLoading}
      className={cn(
        "relative inline-flex items-center justify-center",
        "disabled:opacity-70 disabled:cursor-not-allowed",
        className
      )}
      {...props}
    >
      <span className={cn(isLoading && "invisible")}>{children}</span>
      
      {isLoading && (
        <span className="absolute inset-0 flex items-center justify-center">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="sr-only">{loadingText}</span>
        </span>
      )}
    </button>
  );
}

// Inline loading spinner
export function InlineLoader({ className }: { className?: string }) {
  return (
    <Loader2 className={cn("w-4 h-4 animate-spin text-primary-600", className)} />
  );
}

// Content skeleton for cards
export function ContentSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-4 bg-slate-200 rounded",
            i === 0 && "w-3/4",
            i === 1 && "w-1/2",
            i > 1 && "w-full"
          )}
        />
      ))}
    </div>
  );
}

// Specific loading states for different contexts
export function SearchLoadingState() {
  return (
    <LoadingState
      icon={<Search className="w-8 h-8 text-primary-600" />}
      message="Searching for jobs..."
      submessage="Finding the best matches for you"
    />
  );
}

export function SubmitLoadingState() {
  return (
    <LoadingState
      icon={<Send className="w-8 h-8 text-primary-600" />}
      message="Submitting application..."
      submessage="Tailoring your resume for this role"
    />
  );
}

export function DocumentLoadingState() {
  return (
    <LoadingState
      icon={<FileText className="w-8 h-8 text-primary-600" />}
      message="Loading document..."
      submessage="Please wait a moment"
    />
  );
}

export default LoadingOverlay;

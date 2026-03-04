import * as React from "react";
import { cn } from "../../lib/utils";

interface SocialLoginButtonProps {
  provider: "google" | "linkedin";
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

const GoogleIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      fill="#4285F4"
    />
    <path
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      fill="#34A853"
    />
    <path
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      fill="#FBBC05"
    />
    <path
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      fill="#EA4335"
    />
  </svg>
);

const LinkedInIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="#0A66C2" xmlns="http://www.w3.org/2000/svg">
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
  </svg>
);

export function SocialLoginButton({
  provider,
  onClick,
  disabled,
  className,
}: SocialLoginButtonProps) {
  const isGoogle = provider === "google";
  const isLinkedIn = provider === "linkedin";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "w-full h-12 px-4 rounded-xl border font-semibold text-sm",
        "flex items-center justify-center gap-3",
        "transition-all duration-200",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none",
        isGoogle && [
          "bg-white border-slate-200 text-slate-700",
          "hover:bg-slate-50 hover:border-slate-300",
          "focus-visible:ring-slate-500",
          "shadow-sm hover:shadow-md",
        ],
        isLinkedIn && [
          "bg-[#0A66C2] border-[#0A66C2] text-white",
          "hover:bg-[#0958a8] hover:border-[#0958a8]",
          "focus-visible:ring-[#0A66C2]",
          "shadow-sm hover:shadow-md",
        ],
        className
      )}
      aria-label={`Continue with ${isGoogle ? "Google" : "LinkedIn"}`}
    >
      {isGoogle && <GoogleIcon />}
      {isLinkedIn && <LinkedInIcon />}
      <span>Continue with {isGoogle ? "Google" : "LinkedIn"}</span>
    </button>
  );
}

interface SocialLoginDividerProps {
  text?: string;
}

export function SocialLoginDivider({ text = "or" }: SocialLoginDividerProps) {
  return (
    <div className="relative flex items-center gap-4 py-4">
      <div className="flex-1 h-px bg-slate-200" />
      <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
        {text}
      </span>
      <div className="flex-1 h-px bg-slate-200" />
    </div>
  );
}

interface SocialLoginGroupProps {
  onGoogleClick?: () => void;
  onLinkedInClick?: () => void;
  disabled?: boolean;
  className?: string;
}

export function SocialLoginGroup({
  onGoogleClick,
  onLinkedInClick,
  disabled,
  className,
}: SocialLoginGroupProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <SocialLoginButton
        provider="google"
        onClick={onGoogleClick}
        disabled={disabled}
      />
      <SocialLoginButton
        provider="linkedin"
        onClick={onLinkedInClick}
        disabled={disabled}
      />
    </div>
  );
}

export default SocialLoginGroup;

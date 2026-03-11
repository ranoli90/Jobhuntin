import React, { useState, useEffect, useRef } from "react";
import { botProtection } from "../../lib/botProtection";

interface CaptchaProperties {
  onSuccess: (token: string) => void;
  onError?: (error: string) => void;
  className?: string;
  size?: "normal" | "compact";
  theme?: "light" | "dark";
  disabled?: boolean;
}

/**
 * Captcha component that supports hCaptcha, reCAPTCHA, and Cloudflare Turnstile
 * Automatically detects which provider is configured and renders the appropriate captcha
 */
export function Captcha({
  onSuccess,
  onError,
  className = "",
  size = "normal",
  theme = "light",
}: CaptchaProperties) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const containerReference = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const initializeCaptcha = async () => {
      if (!containerReference.current) return;

      try {
        setIsLoading(true);
        setError(null);

        // Load captcha script if not already loaded
        await botProtection.loadCaptcha();

        if (!mounted) return;

        // Execute captcha challenge
        const token = await botProtection.executeCaptcha(
          containerReference.current,
        );

        if (mounted) {
          setIsLoading(false);
          onSuccess(token);
        }
      } catch (error_) {
        if (mounted) {
          setIsLoading(false);
          const errorMessage =
            error_ instanceof Error ? error_.message : "Captcha failed to load";
          setError(errorMessage);
          onError?.(errorMessage);
        }
      }
    };

    initializeCaptcha();

    return () => {
      mounted = false;
      // Cleanup captcha widget if needed
      if (widgetId.current) {
        // Provider-specific cleanup would go here
        widgetId.current = null;
      }
    };
  }, [onSuccess, onError]);

  // Reset captcha
  const resetCaptcha = () => {
    if (containerReference.current) {
      containerReference.current.innerHTML = "";
    }
    setError(null);
    setIsLoading(true);
    // Re-trigger the effect
    setTimeout(() => {
      // Force re-render
    }, 100);
  };

  return (
    <div className={`captcha-container ${className}`}>
      {isLoading && (
        <div className="flex items-center justify-center p-4 border border-slate-200 rounded-lg bg-slate-50">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-slate-600">Loading captcha...</span>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 border border-red-200 rounded-lg bg-red-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 text-red-500">
                <svg fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <span className="text-sm text-red-700">{error}</span>
            </div>
            <button
              onClick={resetCaptcha}
              className="text-sm text-red-600 hover:text-red-800 font-medium"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      <div
        ref={containerReference}
        className={`captcha-widget ${
          size === "compact" ? "scale-90 origin-top-left" : ""
        } ${theme === "dark" ? "dark-theme" : "light-theme"}`}
        style={{ minHeight: isLoading ? "0" : "70px" }}
      />

      {!isLoading && theme === "dark" && (
        <style>{`
          .captcha-widget iframe {
            filter: invert(1) hue-rotate(180deg);
          }
        `}</style>
      )}
    </div>
  );
}

/**
 * Captcha form field component that can be used in forms
 */
export interface CaptchaFieldProperties {
  value?: string;
  onChange?: (token: string) => void;
  onValidate?: (isValid: boolean) => void;
  error?: string;
  disabled?: boolean;
  className?: string;
}

export function CaptchaField({
  value,
  onChange,
  onValidate,
  error,
  disabled,
  className = "",
}: CaptchaFieldProperties) {
  const [token, setToken] = useState<string | null>(value || null);
  const [isValid, setIsValid] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(error || null);

  const handleCaptchaSuccess = (captchaToken: string) => {
    setToken(captchaToken);
    setIsValid(true);
    setFieldError(null);
    onChange?.(captchaToken);
    onValidate?.(true);
  };

  const handleCaptchaError = (errorMessage: string) => {
    setToken(null);
    setIsValid(false);
    setFieldError(errorMessage);
    onValidate?.(false);
  };

  // Reset when disabled changes
  useEffect(() => {
    if (disabled) {
      setToken(null);
      setIsValid(false);
    }
  }, [disabled]);

  // Sync with external error prop
  useEffect(() => {
    if (error !== fieldError) {
      setFieldError(error ?? null);
    }
  }, [error, fieldError]);

  return (
    <div className={`captcha-field ${className}`}>
      <Captcha
        onSuccess={handleCaptchaSuccess}
        onError={handleCaptchaError}
        disabled={disabled}
      />

      {fieldError && (
        <div className="mt-2 text-sm text-red-600">{fieldError}</div>
      )}

      {isValid && (
        <div className="mt-2 text-sm text-green-600 flex items-center space-x-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <span>Verification successful</span>
        </div>
      )}
    </div>
  );
}

export default Captcha;

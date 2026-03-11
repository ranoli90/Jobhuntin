import * as React from "react";
import { FocusTrap } from "focus-trap-react";
import { Button } from "./Button";
import { Input } from "./Input";
import { cn } from "../../lib/utils";

interface ReAuthModalProperties {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (password: string) => void | Promise<void>;
  title?: string;
  description?: string;
  isLoading?: boolean;
  error?: string;
}

/**
 * Re-authentication modal for sensitive operations
 */
export function ReAuthModal({
  isOpen,
  onClose,
  onSuccess,
  title = "Re-authentication Required",
  description = "For your security, please confirm your password to continue.",
  isLoading = false,
  error,
}: ReAuthModalProperties) {
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const submitButtonReference = React.useRef<HTMLButtonElement>(null);

  // Reset form when modal closes
  React.useEffect(() => {
    if (!isOpen) {
      setPassword("");
      setShowPassword(false);
    }
  }, [isOpen]);

  // Focus on submit button when password is entered
  React.useEffect(() => {
    if (password && submitButtonReference.current) {
      submitButtonReference.current.focus();
    }
  }, [password]);

  const formReference = React.useRef<HTMLFormElement>(null);

  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  // Click outside to close
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!password.trim()) {
      return;
    }

    try {
      const pwd = password.trim();
      await onSuccess(pwd);
      setPassword("");
    } catch {
      // Error handling is managed by parent component
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="reauth-title"
      aria-describedby="reauth-description"
    >
      <FocusTrap
        active={isOpen}
        focusTrapOptions={{
          initialFocus: () =>
            formReference.current?.querySelector<HTMLElement>(
              "#reauth-password",
            ) ?? false,
          allowOutsideClick: true,
          escapeDeactivates: true,
          returnFocusOnDeactivate: true,
          onDeactivate: onClose,
        }}
      >
        <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
          <form ref={formReference} onSubmit={handleSubmit} className="p-6">
            {/* Header */}
            <div className="mb-6">
              <h3
                id="reauth-title"
                className="text-lg font-semibold text-gray-900 mb-2"
              >
                {title}
              </h3>
              <p id="reauth-description" className="text-gray-600 text-sm">
                {description}
              </p>
            </div>

            {/* Password Input */}
            <div className="mb-4">
              <label
                htmlFor="reauth-password"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Password
              </label>
              <div className="relative">
                <Input
                  id="reauth-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pr-10"
                  required
                  autoFocus
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                      />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isLoading}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                ref={submitButtonReference}
                type="submit"
                disabled={!password.trim() || isLoading}
                className="flex-1"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin mr-2" />
                    Verifying...
                  </>
                ) : (
                  "Confirm"
                )}
              </Button>
            </div>
          </form>
        </div>
      </FocusTrap>
    </div>
  );
}

export default ReAuthModal;

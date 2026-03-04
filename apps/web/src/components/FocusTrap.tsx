import * as React from "react";

interface FocusTrapProps {
  children: React.ReactNode;
  isActive?: boolean;
  initialFocus?: boolean;
  restoreFocus?: boolean;
  onEscape?: () => void;
}

export function FocusTrap({
  children,
  isActive = true,
  initialFocus = true,
  restoreFocus = true,
  onEscape
}: FocusTrapProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const previousFocusRef = React.useRef<HTMLElement | null>(null);

  // Store previously focused element
  React.useEffect(() => {
    if (isActive && restoreFocus) {
      previousFocusRef.current = document.activeElement as HTMLElement;
    }
  }, [isActive, restoreFocus]);

  // Initial focus
  React.useEffect(() => {
    if (!isActive || !initialFocus) return;

    const container = containerRef.current;
    if (!container) return;

    // Find first focusable element
    const focusableElements = getFocusableElements(container);
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
  }, [isActive, initialFocus]);

  // Restore focus on unmount/deactivate
  React.useEffect(() => {
    return () => {
      if (restoreFocus && previousFocusRef.current) {
        previousFocusRef.current.focus();
      }
    };
  }, [restoreFocus]);

  // Handle tab key navigation
  React.useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;

      const container = containerRef.current;
      if (!container) return;

      const focusableElements = getFocusableElements(container);
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      // Shift + Tab
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    // Handle Escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && onEscape) {
        onEscape();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isActive, onEscape]);

  return <div ref={containerRef}>{children}</div>;
}

// Helper to get all focusable elements within a container
function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const selector = [
    'button:not([disabled]):not([aria-hidden="true"])',
    'a[href]:not([aria-hidden="true"])',
    'input:not([disabled]):not([type="hidden"]):not([aria-hidden="true"])',
    'select:not([disabled]):not([aria-hidden="true"])',
    'textarea:not([disabled]):not([aria-hidden="true"])',
    '[tabindex]:not([tabindex="-1"]):not([disabled]):not([aria-hidden="true"])'
  ].join(", ");

  return Array.from(container.querySelectorAll(selector));
}

// Hook for managing focus within a modal/dialog
export function useFocusTrap(isActive: boolean, options?: {
  initialFocus?: boolean;
  restoreFocus?: boolean;
  onEscape?: () => void;
}) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const previousFocusRef = React.useRef<HTMLElement | null>(null);

  React.useEffect(() => {
    if (!isActive) return;

    const container = containerRef.current;
    if (!container) return;

    // Store previous focus
    if (options?.restoreFocus !== false) {
      previousFocusRef.current = document.activeElement as HTMLElement;
    }

    // Set initial focus
    if (options?.initialFocus !== false) {
      const focusableElements = getFocusableElements(container);
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    }

    // Handle tab navigation
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Tab") {
        if (e.key === "Escape" && options?.onEscape) {
          options.onEscape();
        }
        return;
      }

      const focusableElements = getFocusableElements(container);
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      if (options?.restoreFocus !== false && previousFocusRef.current) {
        previousFocusRef.current.focus();
      }
    };
  }, [isActive, options]);

  return containerRef;
}

export default FocusTrap;

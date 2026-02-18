import { motion, AnimatePresence } from "framer-motion";
import { ReactNode, useEffect, useState, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { Button } from "../ui/Button";

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  side?: "left" | "right";
  drawerId?: string;
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function MobileDrawer({ isOpen, onClose, children, side = "left", drawerId }: MobileDrawerProps) {
  const [mounted, setMounted] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<Element | null>(null);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // Lock body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      document.body.style.touchAction = 'none';
      document.body.classList.add('menu-open');
    } else {
      document.body.style.overflow = '';
      document.body.style.touchAction = '';
      document.body.classList.remove('menu-open');
    }
    return () => {
      document.body.style.overflow = '';
      document.body.style.touchAction = '';
      document.body.classList.remove('menu-open');
    };
  }, [isOpen]);

  // Save trigger element to restore focus on close
  useEffect(() => {
    if (isOpen) {
      triggerRef.current = document.activeElement;
    } else if (triggerRef.current && triggerRef.current instanceof HTMLElement) {
      triggerRef.current.focus();
      triggerRef.current = null;
    }
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Focus trap: keep Tab cycling within the drawer
  const handleFocusTrap = useCallback(
    (e: KeyboardEvent) => {
      if (e.key !== "Tab" || !drawerRef.current) return;

      const focusableElements = drawerRef.current.querySelectorAll(FOCUSABLE_SELECTOR);
      if (focusableElements.length === 0) return;

      const firstFocusable = focusableElements[0] as HTMLElement;
      const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement;

      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          e.preventDefault();
          lastFocusable.focus();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable.focus();
        }
      }
    },
    []
  );

  useEffect(() => {
    if (!isOpen) return;
    document.addEventListener("keydown", handleFocusTrap);
    return () => document.removeEventListener("keydown", handleFocusTrap);
  }, [isOpen, handleFocusTrap]);

  // Auto-focus first focusable element when drawer opens
  useEffect(() => {
    if (isOpen && drawerRef.current) {
      // Small delay to ensure animation has started and elements are rendered
      const timeout = setTimeout(() => {
        const firstFocusable = drawerRef.current?.querySelector(FOCUSABLE_SELECTOR) as HTMLElement | null;
        firstFocusable?.focus();
      }, 100);
      return () => clearTimeout(timeout);
    }
  }, [isOpen]);

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence mode="wait">
      {isOpen && (
        <div
          id={drawerId}
          className="fixed inset-0 z-[100] md:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation menu"
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 bg-stone-900/60 backdrop-blur-sm"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onClose();
            }}
            aria-hidden="true"
          />

          {/* Drawer */}
          <motion.div
            ref={drawerRef}
            initial={{ x: side === "left" ? "-100%" : "100%" }}
            animate={{ x: 0 }}
            exit={{ x: side === "left" ? "-100%" : "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 350, mass: 0.8 }}
            className={`absolute inset-y-0 ${side === "left" ? "left-0 border-r" : "right-0 border-l"} w-[85vw] max-w-[320px] flex flex-col bg-stone-900 shadow-[0_0_50px_rgba(0,0,0,0.5)] border-stone-700 ring-1 ring-stone-700/50`}
            onClick={(e) => e.stopPropagation()}
          >
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body
  );
}

export function MobileDrawerHeader({ children, onClose }: { children: ReactNode; onClose?: () => void }) {
  return (
    <div className="flex items-center justify-between border-b border-stone-800 px-6 py-5">
      {children}
      {onClose && (
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onClose();
          }}
          className="p-3 -mr-3 text-stone-400 hover:text-white transition-colors active:scale-90 touch-manipulation"
          aria-label="Close menu"
        >
          <X className="h-6 w-6" />
        </button>
      )}
    </div>
  );
}

export function MobileDrawerBody({ children }: { children: ReactNode }) {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      {children}
    </div>
  );
}

export function MobileDrawerFooter({ children }: { children: ReactNode }) {
  return (
    <div className="border-t border-stone-800 px-4 py-4">
      {children}
    </div>
  );
}

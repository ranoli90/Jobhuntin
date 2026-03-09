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
      // Immediately unlock on close
      document.body.style.overflow = '';
      document.body.style.touchAction = '';
      document.body.classList.remove('menu-open');
    }
    return () => {
      // Always clean up on unmount or re-render
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

  // Don't auto-focus - can cause issues on mobile and interfere with close

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <div
          id={drawerId}
          className="fixed inset-0 z-[100] md:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation menu"
        >
          {/* Backdrop - tap/click to close menu */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 z-[9998] bg-slate-900/50 backdrop-blur-sm cursor-pointer"
            onPointerDown={(e) => {
              if (e.target === e.currentTarget) {
                e.preventDefault();
                onClose();
              }
            }}
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                e.preventDefault();
                onClose();
              }
            }}
            role="button"
            tabIndex={-1}
            aria-label="Close menu"
          />

          {/* Drawer */}
          <motion.div
            ref={drawerRef}
            initial={{ x: side === "left" ? "-100%" : "100%" }}
            animate={{ x: 0 }}
            exit={{ x: side === "left" ? "-100%" : "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 350, mass: 0.8 }}
            className={`absolute inset-y-0 ${side === "left" ? "left-0 border-r" : "right-0 border-l"} w-[85vw] max-w-[360px] flex flex-col bg-white dark:bg-slate-900 shadow-2xl shadow-slate-900/20 dark:shadow-black/40 border-slate-100 dark:border-slate-700`}
            onClick={(e) => e.stopPropagation()}
            style={{ zIndex: 9999 }}
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
  const handleClose = useCallback((e: React.MouseEvent | React.PointerEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onClose?.();
  }, [onClose]);

  return (
    <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700 px-6 py-5">
      {children}
      {onClose && (
        <button
          type="button"
          onClick={handleClose}
          onPointerDown={handleClose}
          className="p-3 -mr-3 min-w-[44px] min-h-[44px] flex items-center justify-center text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all active:scale-95 touch-manipulation"
          aria-label="Close menu"
        >
          <X className="h-6 w-6" aria-hidden />
        </button>
      )}
    </div>
  );
}

export function MobileDrawerBody({ children }: { children: ReactNode }) {
  return (
    <div className="flex-1 overflow-y-auto px-5 py-5">
      {children}
    </div>
  );
}

export function MobileDrawerFooter({ children }: { children: ReactNode }) {
  return (
    <div className="border-t border-slate-100 dark:border-slate-700 px-5 py-5 bg-slate-50/50 dark:bg-slate-800/50">
      {children}
    </div>
  );
}

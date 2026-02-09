import { motion, AnimatePresence } from "framer-motion";
import { ReactNode, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { Button } from "../ui/Button";

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  side?: "left" | "right";
}

export function MobileDrawer({ isOpen, onClose, children, side = "left" }: MobileDrawerProps) {
  const [mounted, setMounted] = useState(false);

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

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence mode="wait">
      {isOpen && (
        <div className="fixed inset-0 z-[100] md:hidden">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onClose();
            }}
            aria-hidden="true"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: side === "left" ? "-100%" : "100%" }}
            animate={{ x: 0 }}
            exit={{ x: side === "left" ? "-100%" : "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 350, mass: 0.8 }}
            className={`absolute inset-y-0 ${side === "left" ? "left-0 border-r" : "right-0 border-l"} w-[85vw] max-w-[320px] flex flex-col bg-white shadow-[0_0_50px_rgba(0,0,0,0.1)] border-slate-100 ring-1 ring-slate-900/5`}
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
    <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
      {children}
      {onClose && (
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onClose();
          }}
          className="p-3 -mr-3 text-slate-400 hover:text-slate-900 transition-colors active:scale-90 touch-manipulation"
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
    <div className="border-t border-slate-200 px-4 py-4">
      {children}
    </div>
  );
}

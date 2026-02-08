import { motion, AnimatePresence } from "framer-motion";
import { ReactNode } from "react";
import { X } from "lucide-react";
import { Button } from "../ui/Button";

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  side?: "left" | "right";
}

export function MobileDrawer({ isOpen, onClose, children, side = "left" }: MobileDrawerProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/50 md:hidden"
            onClick={onClose}
            aria-hidden="true"
          />
          
          {/* Drawer */}
          <motion.div
            initial={{ x: side === "left" ? "-100%" : "100%" }}
            animate={{ x: 0 }}
            exit={{ x: side === "left" ? "-100%" : "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className={`fixed inset-y-0 ${side === "left" ? "left-0 border-r" : "right-0 border-l"} z-50 w-64 flex flex-col bg-white shadow-xl md:hidden`}
          >
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export function MobileDrawerHeader({ children, onClose }: { children: ReactNode; onClose?: () => void }) {
  return (
    <div className="flex items-center justify-between border-b border-slate-200 px-4 py-6 pb-4">
      {children}
      {onClose && (
        <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close menu">
          <X className="h-5 w-5" />
        </Button>
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

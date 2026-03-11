import * as React from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  HelpCircle,
  X,
  MessageCircle,
  Book,
  Mail,
  ExternalLink,
} from "lucide-react";
import { cn } from "../lib/utils";

interface HelpButtonProperties {
  className?: string;
}

export function HelpButton({ className }: HelpButtonProperties) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [isAppPage, setIsAppPage] = React.useState(false);
  const menuReference = React.useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  // Check if on app page (client-side only to avoid hydration mismatch)
  React.useEffect(() => {
    setIsAppPage(window.location.pathname.startsWith("/app"));
  }, []);

  // Close on Escape key
  React.useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen]);

  // Close on click outside
  React.useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        menuReference.current &&
        !menuReference.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  if (isAppPage) return null;

  return (
    <div
      ref={menuReference}
      className={cn(
        "fixed bottom-6 right-6 z-40 md:z-50 md:bottom-6 md:right-6",
        "max-md:bottom-24 max-md:right-4",
        className,
      )}
    >
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.9, y: 20 }}
            transition={shouldReduceMotion ? { duration: 0 } : { type: "spring", damping: 25, stiffness: 300 }}
            className="absolute bottom-16 right-0 w-64 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden"
          >
            <div className="p-4 bg-black dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-white font-bold text-lg">How can we help?</h3>
              <p className="text-gray-400 text-sm">Choose an option below</p>
            </div>

            <div className="p-2">
              <a
                href="/guides"
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-100 transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-gray-200 flex items-center justify-center group-hover:bg-gray-300 transition-colors">
                  <Book className="w-5 h-5 text-black" />
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Help Center</p>
                  <p className="text-xs text-slate-500">
                    Browse guides & tutorials
                  </p>
                </div>
              </a>

              <a
                href="mailto:support@jobhuntin.com"
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-100 transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-gray-200 flex items-center justify-center group-hover:bg-gray-300 transition-colors">
                  <Mail className="w-5 h-5 text-black" />
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Email Support</p>
                  <p className="text-xs text-slate-500">Get help via email</p>
                </div>
              </a>

              <a
                href="https://twitter.com/jobhuntin"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-100 transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-gray-200 flex items-center justify-center group-hover:bg-gray-300 transition-colors">
                  <MessageCircle className="w-5 h-5 text-black" />
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Twitter/X</p>
                  <p className="text-xs text-slate-500 flex items-center gap-1">
                    @jobhuntin <ExternalLink className="w-3 h-3" />
                  </p>
                </div>
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        whileHover={shouldReduceMotion ? undefined : { scale: 1.05 }}
        whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
        className={cn(
          "w-14 h-14 rounded-full shadow-lg flex items-center justify-center border border-gray-200",
          "bg-white text-black hover:bg-gray-100",
          "transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2",
        )}
        aria-label={isOpen ? "Close help menu" : "Open help menu"}
        aria-expanded={isOpen}
      >
        <motion.div
          animate={{ rotate: shouldReduceMotion ? 0 : isOpen ? 90 : 0 }}
          transition={{ duration: shouldReduceMotion ? 0 : 0.2 }}
        >
          {isOpen ? (
            <X className="w-6 h-6" />
          ) : (
            <HelpCircle className="w-6 h-6" />
          )}
        </motion.div>
      </motion.button>
    </div>
  );
}

export default HelpButton;

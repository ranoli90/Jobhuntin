import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { HelpCircle, X, MessageCircle, Book, Mail, ExternalLink } from "lucide-react";
import { cn } from "../lib/utils";

interface HelpButtonProps {
  className?: string;
}

export function HelpButton({ className }: HelpButtonProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);
  
  // Don't show on app pages (they have their own navigation)
  const isAppPage = typeof window !== 'undefined' && window.location.pathname.startsWith('/app');
  
  // Close on Escape key
  React.useEffect(() => {
    if (!isOpen) return;
    
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);
  
  // Close on click outside
  React.useEffect(() => {
    if (!isOpen) return;
    
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);
  
  if (isAppPage) return null;

  return (
    <div ref={menuRef} className={cn("fixed bottom-6 right-6 z-50", className)}>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="absolute bottom-16 right-0 w-64 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden"
          >
            <div className="p-4 bg-primary-600">
              <h3 className="text-white font-bold text-lg">How can we help?</h3>
              <p className="text-white/80 text-sm">Choose an option below</p>
            </div>
            
            <div className="p-2">
              <a
                href="/guides"
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                  <Book className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Help Center</p>
                  <p className="text-xs text-slate-500">Browse guides & tutorials</p>
                </div>
              </a>
              
              <a
                href="mailto:support@jobhuntin.com"
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center group-hover:bg-emerald-100 transition-colors">
                  <Mail className="w-5 h-5 text-emerald-600" />
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
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-sky-50 flex items-center justify-center group-hover:bg-sky-100 transition-colors">
                  <MessageCircle className="w-5 h-5 text-sky-600" />
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
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={cn(
          "w-14 h-14 rounded-full shadow-2xl flex items-center justify-center",
          "bg-primary-600 text-white hover:bg-primary-700",
          "transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        )}
        aria-label={isOpen ? "Close help menu" : "Open help menu"}
        aria-expanded={isOpen}
      >
        <motion.div
          animate={{ rotate: isOpen ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          {isOpen ? <X className="w-6 h-6" /> : <HelpCircle className="w-6 h-6" />}
        </motion.div>
      </motion.button>
    </div>
  );
}

export default HelpButton;

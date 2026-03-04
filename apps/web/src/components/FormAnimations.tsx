import { motion } from "framer-motion";
import { cn } from "../lib/utils";

interface ShakeAnimationProps {
  children: React.ReactNode;
  isError?: boolean;
  className?: string;
}

export function ShakeAnimation({ children, isError, className }: ShakeAnimationProps) {
  return (
    <motion.div
      animate={isError ? {
        x: [0, -10, 10, -10, 10, 0],
        transition: { duration: 0.4 }
      } : {}}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface FormErrorAnimationProps {
  children: React.ReactNode;
  show: boolean;
  className?: string;
}

export function FormErrorAnimation({ children, show, className }: FormErrorAnimationProps) {
  return (
    <motion.div
      initial={{ opacity: 0, height: 0, y: -10 }}
      animate={show ? { 
        opacity: 1, 
        height: "auto", 
        y: 0,
        transition: { type: "spring", damping: 20, stiffness: 300 }
      } : { 
        opacity: 0, 
        height: 0, 
        y: -10 
      }}
      className={cn("overflow-hidden", className)}
    >
      {children}
    </motion.div>
  );
}

interface SuccessPulseProps {
  children: React.ReactNode;
  isSuccess?: boolean;
  className?: string;
}

export function SuccessPulse({ children, isSuccess, className }: SuccessPulseProps) {
  return (
    <motion.div
      animate={isSuccess ? {
        scale: [1, 1.02, 1],
        transition: { duration: 0.3 }
      } : {}}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface FieldHighlightProps {
  children: React.ReactNode;
  isFocused?: boolean;
  isValid?: boolean;
  isError?: boolean;
  className?: string;
}

export function FieldHighlight({ 
  children, 
  isFocused, 
  isValid, 
  isError,
  className 
}: FieldHighlightProps) {
  const getBorderColor = () => {
    if (isError) return "border-red-500 ring-2 ring-red-500/20";
    if (isValid) return "border-emerald-500 ring-2 ring-emerald-500/20";
    if (isFocused) return "border-primary-500 ring-2 ring-primary-500/20";
    return "border-slate-200";
  };

  return (
    <motion.div
      animate={{
        borderColor: isError ? "#ef4444" : isValid ? "#10b981" : isFocused ? "#6366f1" : "#e2e8f0",
      }}
      transition={{ duration: 0.2 }}
      className={cn("rounded-xl border-2 transition-colors", getBorderColor(), className)}
    >
      {children}
    </motion.div>
  );
}

interface CheckmarkAnimationProps {
  show: boolean;
  className?: string;
}

export function CheckmarkAnimation({ show, className }: CheckmarkAnimationProps) {
  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={show ? { scale: 1, opacity: 1 } : { scale: 0, opacity: 0 }}
      transition={{ type: "spring", damping: 15, stiffness: 300 }}
      className={className}
    >
      <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <motion.path
          initial={{ pathLength: 0 }}
          animate={show ? { pathLength: 1 } : { pathLength: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 13l4 4L19 7"
        />
      </svg>
    </motion.div>
  );
}

export default ShakeAnimation;

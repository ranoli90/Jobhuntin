import * as React from "react";
import { motion } from "framer-motion";
import { Button } from "./Button";
import { cn } from "../../lib/utils";

interface EmptyStateProps {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
  className?: string;
}

export function EmptyState({ title, description, actionLabel, onAction, icon, className }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={cn(
        "rounded-3xl border-2 border-dashed border-slate-200 bg-gradient-to-br from-white to-slate-50 px-8 py-14 text-center relative overflow-hidden",
        className
      )}
    >
      <div className="absolute -top-16 -right-16 w-48 h-48 bg-primary-500/5 rounded-full blur-3xl pointer-events-none" />
      {icon && (
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.15, type: "spring", stiffness: 200 }}
          className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100 shadow-inner"
        >
          {icon}
        </motion.div>
      )}
      <p className="font-display text-xl font-bold text-slate-900">{title}</p>
      {description ? <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto font-medium">{description}</p> : null}
      {actionLabel ? (
        <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
          <Button className="mt-6 shadow-lg shadow-primary-500/10" onClick={onAction}>
            {actionLabel}
          </Button>
        </motion.div>
      ) : null}
    </motion.div>
  );
}

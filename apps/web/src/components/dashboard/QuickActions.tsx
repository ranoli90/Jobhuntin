import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { ArrowRight, Search, FileText, HelpCircle } from "lucide-react";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";

interface QuickAction {
  /** Action label */
  label: string;
  /** Action description */
  description: string;
  /** Lucide icon */
  icon: LucideIcon;
  /** Color theme */
  color: string;
  /** Click handler */
  onClick: () => void;
  /** Badge count (optional) */
  badge?: number;
}

interface QuickActionsProps {
  /** Array of quick actions */
  actions: QuickAction[];
  /** Loading state */
  isLoading?: boolean;
}

export function QuickActions({ actions, isLoading }: QuickActionsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-3 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card
            key={i}
            className="p-6 border-brand-border bg-white rounded-xl"
            shadow="sm"
          >
            <div className="animate-pulse space-y-3">
              <div className="h-10 w-10 bg-slate-100 rounded-xl" />
              <div className="h-5 w-24 bg-slate-100 rounded" />
              <div className="h-4 w-32 bg-slate-50 rounded" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {actions.map((action, index) => (
        <motion.div
          key={action.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1, duration: 0.4 }}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Card
            className={`p-6 border-brand-border bg-white hover:border-brand-primary/30 transition-all duration-200 cursor-pointer group rounded-xl ${action.color}`}
            shadow="sm"
            onClick={action.onClick}
          >
            <div className="flex items-start justify-between">
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-2">
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-xl ${action.color.replace(
                      "hover:",
                      ""
                    )} bg-opacity-10`}
                  >
                    <action.icon className="h-5 w-5" aria-hidden />
                  </div>
                  {action.badge !== undefined && action.badge > 0 && (
                    <span className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 text-xs font-bold text-white bg-red-500 rounded-full">
                      {action.badge}
                    </span>
                  )}
                </div>
                <div>
                  <p className="font-semibold text-brand-text">{action.label}</p>
                  <p className="text-sm text-brand-muted">{action.description}</p>
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-brand-muted group-hover:text-brand-primary group-hover:translate-x-1 transition-all" />
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}

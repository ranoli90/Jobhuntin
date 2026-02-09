import * as React from "react";
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
    <div className={cn("rounded-3xl border border-dashed border-brand-ink/20 bg-white/80 px-6 py-12 text-center", className)}>
      {icon && <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-brand-shell">{icon}</div>}
      <p className="font-display text-2xl text-brand-ink">{title}</p>
      {description ? <p className="mt-2 text-sm text-brand-ink/70">{description}</p> : null}
      {actionLabel ? (
        <Button className="mt-6" onClick={onAction} variant="lagoon">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}

import * as React from "react";
import { X } from "lucide-react";
import { subscribeToasts, type ToastPayload } from "../../lib/toast";
import { cn } from "../../lib/utils";

interface ToastWithId extends Required<ToastPayload> {}

export function ToastShelf() {
  const [items, setItems] = React.useState<ToastWithId[]>([]);

  React.useEffect(() => {
    return subscribeToasts((toast) => {
      setItems((previous) => [...previous, toast]);
      setTimeout(() => dismiss(toast.id), 4000);
    });
  }, []);

  const dismiss = (id: string) => {
    setItems((previous) => previous.filter((toast) => toast.id !== id));
  };

  if (items.length === 0) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed right-6 top-6 z-[60] flex w-80 flex-col gap-3"
    >
      {items.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "rounded-2xl border px-4 py-3 shadow-lg backdrop-blur text-sm",
            toast.tone === "success" &&
              "bg-brand-lagoon/20 dark:bg-emerald-500/20 border-brand-lagoon/40 dark:border-emerald-500/40",
            toast.tone === "error" &&
              "bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700 text-red-900 dark:text-red-100",
            toast.tone === "info" &&
              "bg-brand-shell dark:bg-slate-800 border-brand-shell/80 dark:border-slate-600",
          )}
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-semibold text-brand-ink dark:text-slate-100">
                {toast.title}
              </p>
              {toast.description ? (
                <p className="text-xs text-brand-ink/70 dark:text-slate-300">
                  {toast.description}
                </p>
              ) : null}
            </div>
            <button
              aria-label="Dismiss notification"
              onClick={() => dismiss(toast.id)}
              className="text-brand-ink/60 hover:text-brand-ink dark:text-slate-400 dark:hover:text-slate-100"
            >
              <X className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

import * as React from "react";
import { X } from "lucide-react";
import { subscribeToasts, type ToastPayload } from "../../lib/toast";
import { cn } from "../../lib/utils";

interface ToastWithId extends Required<ToastPayload> {}

export function ToastShelf() {
  const [items, setItems] = React.useState<ToastWithId[]>([]);

  React.useEffect(() => {
    return subscribeToasts((toast) => {
      setItems((prev) => [...prev, toast]);
      setTimeout(() => dismiss(toast.id), 4000);
    });
  }, []);

  const dismiss = (id: string) => {
    setItems((prev) => prev.filter((toast) => toast.id !== id));
  };

  if (!items.length) return null;

  return (
    <div className="fixed right-6 top-6 z-[60] flex w-80 flex-col gap-3">
      {items.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "rounded-2xl border px-4 py-3 shadow-lg backdrop-blur text-sm",
            toast.tone === "success" && "bg-brand-lagoon/20 border-brand-lagoon/40",
            toast.tone === "error" && "bg-red-100 border-red-300 text-red-900",
            toast.tone === "info" && "bg-brand-shell border-brand-shell/80",
          )}
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-semibold text-brand-ink">{toast.title}</p>
              {toast.description ? <p className="text-xs text-brand-ink/70">{toast.description}</p> : null}
            </div>
            <button onClick={() => dismiss(toast.id)} className="text-brand-ink/60 hover:text-brand-ink">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

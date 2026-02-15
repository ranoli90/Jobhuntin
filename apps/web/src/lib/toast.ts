export type ToastPayload = {
  id?: string;
  title: string;
  description?: string;
  tone?: "success" | "error" | "info" | "warning" | "neutral";
};

const TOAST_EVENT = "jobhuntin-toast";

export function pushToast(payload: ToastPayload) {
  if (typeof window === "undefined") return;
  const detail = {
    id: payload.id ?? `toast-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    ...payload,
  } as Required<ToastPayload>;
  window.dispatchEvent(new CustomEvent(TOAST_EVENT, { detail }));
}

export function subscribeToasts(callback: (payload: Required<ToastPayload>) => void) {
  if (typeof window === "undefined") return () => undefined;
  const handler = (event: Event) => {
    const custom = event as CustomEvent<Required<ToastPayload>>;
    callback(custom.detail);
  };
  window.addEventListener(TOAST_EVENT, handler as EventListener);
  return () => window.removeEventListener(TOAST_EVENT, handler as EventListener);
}

import { useEffect, useState } from "react";

interface BillingStatus {
  plan: "FREE" | "PRO" | "TEAM";
  seats?: number;
  mrr?: number;
  success_rate?: number;
  invoice_history?: { id: string; amount: number; status: string; created_at: string }[];
  next_payment_at?: string;
}

interface BillingUsage {
  applications_used: number;
  applications_limit?: number;
}

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export function useBilling() {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [usage, setUsage] = useState<BillingUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [statusResp, usageResp] = await Promise.all([
          fetch(`${API_BASE}/billing/status`, { credentials: "include" }),
          fetch(`${API_BASE}/billing/usage`, { credentials: "include" }),
        ]);
        if (!statusResp.ok) throw new Error("Billing status unavailable");
        if (!usageResp.ok) throw new Error("Usage unavailable");
        const statusJson = (await statusResp.json()) as BillingStatus;
        const usageJson = (await usageResp.json()) as BillingUsage;
        if (!cancelled) {
          setStatus(statusJson);
          setUsage(usageJson);
        }
      } catch (err) {
        if (!cancelled) setError((err as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const upgrade = async () => {
    const resp = await fetch(`${API_BASE}/billing/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!resp.ok) throw new Error("Checkout failed");
    const json = (await resp.json()) as { checkout_url: string };
    window.location.href = json.checkout_url;
  };

  const addSeats = async () => {
    const resp = await fetch(`${API_BASE}/billing/team-checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!resp.ok) throw new Error("Team checkout failed");
    const json = (await resp.json()) as { checkout_url: string };
    window.location.href = json.checkout_url;
  };

  return {
    plan: status?.plan ?? "FREE",
    status,
    usage,
    loading,
    error,
    upgrade,
    addSeats,
  } as const;
}

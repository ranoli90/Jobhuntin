import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../lib/api";

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

export function useBilling() {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [usage, setUsage] = useState<BillingUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [statusJson, usageJson] = await Promise.all([
          apiGet<BillingStatus>("billing/status"),
          apiGet<BillingUsage & { monthly_used?: number; monthly_limit?: number }>("billing/usage"),
        ]);
        if (!cancelled) {
          setStatus(statusJson);
          setUsage({
            applications_used: usageJson.applications_used ?? usageJson.monthly_used ?? 0,
            applications_limit: usageJson.applications_limit ?? usageJson.monthly_limit,
          });
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

  const baseUrl = typeof window !== "undefined" ? window.location.origin : "";

  const upgrade = async () => {
    const json = await apiPost<{ checkout_url: string }>("billing/checkout", {
      success_url: `${baseUrl}/app/billing?success=1`,
      cancel_url: `${baseUrl}/app/billing`,
    });
    window.location.href = json.checkout_url;
  };

  const addSeats = async () => {
    const json = await apiPost<{ checkout_url: string }>("billing/team-checkout", {
      success_url: `${baseUrl}/app/billing?success=1`,
      cancel_url: `${baseUrl}/app/billing`,
    });
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

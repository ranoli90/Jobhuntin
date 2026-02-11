import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../lib/api";

interface BillingStatus {
  tenant_id: string;
  plan: "FREE" | "PRO" | "TEAM";
  provider: string | null;
  provider_customer_id: string | null;
  subscription_status: string;
  current_period_end: string | null;
}

interface BillingUsage {
  tenant_id: string;
  plan: string;
  monthly_limit: number | null;
  monthly_used: number;
  monthly_remaining: number | null;
  concurrent_limit: number | null;
  concurrent_used: number;
  percentage_used: number;
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

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useCallback } from "react";
import { apiGet, apiPost } from "../lib/api";
import { pushToast } from "../lib/toast";

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

interface BillingData {
  status: BillingStatus;
  usage: BillingUsage;
}

async function fetchBillingData(): Promise<BillingData> {
  const [status, usage] = await Promise.all([
    apiGet<BillingStatus>("billing/status"),
    apiGet<BillingUsage & { monthly_used?: number; monthly_limit?: number }>("billing/usage"),
  ]);
  return { status, usage };
}

export function useBilling() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["billing"],
    queryFn: fetchBillingData,
    staleTime: 30_000, // Consider data fresh for 30s
    refetchOnWindowFocus: true, // Refetch when user returns to tab (e.g. from Stripe)
  });

  const status = query.data?.status ?? null;
  const usage = query.data?.usage ?? null;

  // M-11: Detect ?success=1 param (from Stripe redirect) and celebrate
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("success") === "1") {
      pushToast({
        title: "Upgrade successful! 🎉",
        description: "Your new plan is now active. It may take a moment to fully reflect.",
        tone: "success",
      });
      // Poll aggressively for a short time to pick up webhook-driven changes
      const interval = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ["billing"] });
      }, 3000);
      const timeout = setTimeout(() => clearInterval(interval), 30_000);
      // Clean up the URL so reloads don't re-trigger
      const url = new URL(window.location.href);
      url.searchParams.delete("success");
      window.history.replaceState({}, "", url.toString());
      return () => {
        clearInterval(interval);
        clearTimeout(timeout);
      };
    }
  }, [queryClient]);

  const baseUrl = typeof window !== "undefined" ? window.location.origin : "";

  const upgrade = useCallback(async () => {
    const json = await apiPost<{ checkout_url: string }>("billing/checkout", {
      success_url: `${baseUrl}/app/billing?success=1`,
      cancel_url: `${baseUrl}/app/billing`,
    });
    window.location.href = json.checkout_url;
  }, [baseUrl]);

  const addSeats = useCallback(async () => {
    const json = await apiPost<{ checkout_url: string }>("billing/team-checkout", {
      success_url: `${baseUrl}/app/billing?success=1`,
      cancel_url: `${baseUrl}/app/billing`,
    });
    window.location.href = json.checkout_url;
  }, [baseUrl]);

  // M-10: Separate portal action for managing existing subscriptions
  const manageBilling = useCallback(async () => {
    try {
      const json = await apiPost<{ portal_url?: string; checkout_url?: string }>("billing/portal", {
        return_url: `${baseUrl}/app/billing`,
      });
      const url = json.portal_url || json.checkout_url;
      if (url) {
        window.location.href = url;
      } else {
        pushToast({ title: "Portal unavailable", description: "Please contact support to manage your subscription.", tone: "warning" });
      }
    } catch (err) {
      // Fallback: if billing/portal doesn't exist yet, redirect to checkout
      pushToast({ title: "Billing portal error", description: (err as Error).message, tone: "error" });
    }
  }, [baseUrl]);

  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["billing"] });
  }, [queryClient]);

  return {
    plan: status?.plan ?? "FREE",
    status,
    usage,
    loading: query.isLoading,
    error: query.error ? (query.error as Error).message : null,
    upgrade,
    addSeats,
    manageBilling,
    refetch,
  } as const;
}

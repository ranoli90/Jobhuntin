import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useCallback } from "react";
import { apiGet, apiPost } from "../lib/api";
import { pushToast } from "../lib/toast";
import { useAuth } from "./useAuth";

interface BillingStatus {
  tenant_id: string;
  plan: "FREE" | "PRO" | "TEAM" | "ENTERPRISE";
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

export interface BillingTier {
  name: "FREE" | "PRO" | "TEAM";
  price: string;
  features: string[];
  actionKey: string | null;
  recommended: boolean;
}

interface BillingData {
  status: BillingStatus;
  usage: BillingUsage;
  tiers: BillingTier[];
}

async function fetchBillingData(): Promise<BillingData> {
  const [status, usage, tiers] = await Promise.all([
    apiGet<BillingStatus>("billing/status"),
    apiGet<BillingUsage & { monthly_used?: number; monthly_limit?: number }>("billing/usage"),
    apiGet<BillingTier[]>("billing/tiers"),
  ]);
  return { status, usage, tiers };
}

// #24: Fallback when API unavailable (e.g. loading, 401)
const DEFAULT_TIERS: BillingTier[] = [
  { name: "FREE", price: "$0", features: ["10 applications", "Basic tailoring", "Standard support"], actionKey: null, recommended: false },
  { name: "PRO", price: "$19", features: ["Unlimited apps", "Priority queue", "Interview coach"], actionKey: "upgrade", recommended: true },
  { name: "TEAM", price: "$49", features: ["10 team seats", "API access", "White-label reports"], actionKey: "addSeats", recommended: false },
];

export function useBilling() {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const query = useQuery({
    queryKey: ["billing"],
    queryFn: fetchBillingData,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true, // Refetch when user returns to tab (e.g. from Stripe)
    enabled: !!user, // Don't call billing API when logged out (avoids 401 redirect from Pricing page)
  });

  const status = query.data?.status ?? null;
  const usage = query.data?.usage ?? null;
  const tiers = query.data?.tiers ?? DEFAULT_TIERS;

  // M-11: Detect ?success=1 or ?success=true param (from Stripe redirect) and celebrate
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const isSuccess = params.get("success") === "true" || params.get("success") === "1";
    if (isSuccess) {
      pushToast({
        title: "Upgrade successful! 🎉",
        description: "Your new plan is now active. It may take a moment to fully reflect.",
        tone: "success",
      });
      // Poll with exponential backoff (2s, 4s, 8s, 16s); stop when tab hidden
      const delays = [2000, 4000, 8000, 16000];
      const timeouts: ReturnType<typeof setTimeout>[] = [];
      const cancelAll = () => {
        timeouts.forEach(clearTimeout);
        timeouts.length = 0;
      };
      let elapsed = 0;
      for (let i = 0; i < delays.length; i++) {
        elapsed += delays[i];
        const t = setTimeout(() => {
          if (document.visibilityState === "hidden") {
            cancelAll();
            return;
          }
          queryClient.invalidateQueries({ queryKey: ["billing"] });
        }, elapsed);
        timeouts.push(t);
      }
      const cleanup = setTimeout(cancelAll, 30_000);
      const onVisibilityChange = () => {
        if (document.visibilityState === "hidden") cancelAll();
      };
      document.addEventListener("visibilitychange", onVisibilityChange);
      // Clean up the URL so reloads don't re-trigger
      const url = new URL(window.location.href);
      url.searchParams.delete("success");
      window.history.replaceState({}, "", url.toString());
      return () => {
        cancelAll();
        clearTimeout(cleanup);
        document.removeEventListener("visibilitychange", onVisibilityChange);
      };
    }
  }, [queryClient]);

  const baseUrl = typeof window !== "undefined" ? window.location.origin : "";

  const upgrade = useCallback(async (billingPeriod: "monthly" | "annual" = "monthly") => {
    const json = await apiPost<{ checkout_url: string }>("billing/checkout", {
      success_url: `${baseUrl}/app/billing?success=1`,
      cancel_url: `${baseUrl}/app/billing`,
      billing_period: billingPeriod,
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
      pushToast({ title: "Could not open billing portal", description: (err as Error).message || "Please try again or contact support.", tone: "error" });
    }
  }, [baseUrl]);

  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["billing"] });
  }, [queryClient]);

  return {
    plan: status?.plan ?? "FREE",
    status,
    usage,
    tiers,
    loading: query.isLoading,
    error: query.error ? (query.error as Error).message : null,
    upgrade,
    addSeats,
    manageBilling,
    refetch,
  } as const;
}

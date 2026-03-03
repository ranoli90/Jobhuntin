import { FocusTrap } from "focus-trap-react";
import { ArrowUpRight, BarChart3, Briefcase, DollarSign, Inbox, Rocket, MessageCircle, CheckCircle, Clock, Zap, Quote, Send, Users, Loader2, Sparkles, AlertTriangle, Radar, MoreVertical, Eye, Pause, Trash2, Filter, MapPin, BriefcaseIcon } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { useBilling } from "../../hooks/useBilling";
import { useApplications } from "../../hooks/useApplications";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence, useMotionValue, useTransform, useReducedMotion } from "framer-motion";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiPost, apiGet, getApiBase, getAuthHeaders } from "../../lib/api";
import { pushToast } from "../../lib/toast";
import { fireSuccessConfetti } from "../../lib/confetti";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { useJobs } from "../../hooks/useJobs";
import type { JobFilters } from "../../hooks/useJobs";
import { formatCurrency, formatDate } from "../../lib/format";
import { t, formatT, getLocale, isRTLLanguage } from "../../lib/i18n";
import { useSessionMilestone } from "../../hooks/useCelebrations";
import { telemetry } from "../../lib/telemetry";
import { AnimatedNumber, statusVariant } from "./shared";


const BILLING_TIERS = [
    { name: "FREE" as const, price: "$0", features: ["10 applications", "Basic tailoring", "Standard support"], actionKey: null, recommended: false },
    { name: "PRO" as const, price: "$19", features: ["Unlimited apps", "Priority queue", "Interview coach"], recommended: true, actionKey: "upgrade" as const },
    { name: "TEAM" as const, price: "$49", features: ["10 team seats", "API access", "White-label reports"], actionKey: "addSeats" as const, recommended: false },
  ] as const;


export default function BillingView() {
    const { status, plan, usage, upgrade, addSeats, manageBilling, loading: isLoading, error } = useBilling();
    const shouldReduceMotion = useReducedMotion();
  
    if (isLoading) {
      return (
        <div className="max-w-6xl mx-auto space-y-6 pb-6 px-4 lg:px-0" aria-busy="true" aria-label="Loading billing">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-2">
              <div className="h-8 w-48 bg-slate-200 rounded animate-pulse" />
              <div className="h-4 w-64 bg-slate-100 rounded animate-pulse" />
            </div>
            <div className="h-8 w-24 bg-slate-100 rounded-xl animate-pulse" />
          </div>
          <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="p-6 lg:p-8 border border-slate-200 rounded-2xl animate-pulse">
                <div className="h-6 w-40 bg-slate-200 rounded mb-6" />
                <div className="space-y-4">
                  <div className="h-4 w-full bg-slate-100 rounded" />
                  <div className="h-3 w-full bg-slate-100 rounded-full" />
                </div>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-6 border border-slate-200 rounded-2xl animate-pulse">
                    <div className="h-6 w-24 bg-slate-200 rounded mb-4" />
                    <div className="h-8 w-16 bg-slate-100 rounded mb-2" />
                    <div className="h-4 w-full bg-slate-100 rounded" />
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-6">
              <div className="p-6 border border-slate-200 rounded-2xl animate-pulse">
                <div className="h-6 w-32 bg-slate-200 rounded mb-4" />
                <div className="h-4 w-full bg-slate-100 rounded mb-2" />
                <div className="h-4 w-3/4 bg-slate-100 rounded" />
              </div>
            </div>
          </div>
        </div>
      );
    }
  
    const usageUsed = usage?.monthly_used ?? 0;
    const usageLimit = usage?.monthly_limit ?? 100;
    const usagePercent = usage?.percentage_used ?? 0;
    const periodEnd = status?.current_period_end
      ? new Date(status.current_period_end).toLocaleDateString()
      : null;
  
    const actionMap: Record<string, (() => Promise<void>) | null> = { upgrade, addSeats };
    const tiers = BILLING_TIERS.map(t => ({
      ...t,
      action: t.actionKey ? actionMap[t.actionKey] ?? null : null,
    }));
  
    return (
      <div className="max-w-6xl mx-auto space-y-6 pb-6 px-4 lg:px-0">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">Billing & Quota</h2>
            <p className="text-slate-500 font-medium">Manage your subscription and usage.</p>
          </div>
          <Badge variant="primary" className="py-2 px-4 rounded-xl font-bold">
            Plan: {plan || "FREE"}
          </Badge>
        </div>
  
        {error && (
          <div className="flex items-center gap-3 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800" role="alert">
            <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" aria-hidden />
            <div className="flex-1">
              <p className="font-bold text-sm">Unable to load billing data</p>
              <p className="text-xs text-red-600 mt-0.5">{error}</p>
            </div>
          </div>
        )}
  
        <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
          <div className="lg:col-span-2 space-y-6 lg:space-y-8">
            <Card className="p-6 lg:p-8 border-slate-200" shadow="sm">
              <h3 className="text-xl font-black text-slate-900 mb-6 font-display">Current Allocation</h3>
              <div className="space-y-4">
                  <div className="flex justify-between items-end">
                  <p className="text-sm font-bold text-slate-500 uppercase">Monthly Volume</p>
                  <p className="text-sm font-black text-slate-900">{usageUsed} / {usageLimit}</p>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={shouldReduceMotion ? { width: `${Math.min(usagePercent, 100)}%` } : { width: 0 }}
                    animate={{ width: `${Math.min(usagePercent, 100)}%` }}
                    className="h-full bg-primary-500"
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-500 font-medium">
                  <span>{usage?.monthly_remaining ?? usageLimit - usageUsed} remaining</span>
                  {periodEnd && <span>Resets {periodEnd}</span>}
                </div>
              </div>
            </Card>
  
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
              {tiers.map((tier) => (
                <Card
                  key={tier.name}
                  className={`p-6 flex flex-col items-center text-center transition-all hover:shadow-lg ${tier.recommended ? "border-primary-500 shadow-xl shadow-primary-500/10 ring-1 ring-primary-500" : "border-slate-100"
                    }`}
                >
                  <h4 className="font-black text-slate-900 text-lg mb-1">{tier.name}</h4>
                  <p className="text-3xl font-black text-slate-900 mb-6">{tier.price}</p>
                  <ul className="space-y-3 mb-8 flex-1">
                    {tier.features.map(f => (
                      <li key={f} className="text-xs text-slate-500 font-medium flex items-center gap-2">
                        <CheckCircle className="w-3 h-3 text-emerald-500" /> {f}
                      </li>
                    ))}
                  </ul>
                  <Button
                    variant={tier.recommended ? "primary" : "outline"}
                    className="w-full font-bold text-xs uppercase rounded-xl"
                    disabled={tier.name === plan}
                    onClick={tier.action ? async () => {
                      if (tier.actionKey === "upgrade") telemetry.track("upgrade_clicked", { tier: tier.name });
                      if (tier.actionKey === "addSeats") telemetry.track("add_seats_clicked", { tier: tier.name });
                      try { await tier.action!(); } catch (e) { pushToast({ title: "Checkout failed", description: (e as Error).message, tone: "error" }); }
                    } : undefined}
                  >
                    {tier.name === plan ? "Current" : "Upgrade"}
                  </Button>
                </Card>
              ))}
            </div>
          </div>
  
          <div className="space-y-6">
            <Card className="bg-slate-900 text-white p-8 border-none overflow-hidden relative" shadow="lift">
              <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary-500/20 rounded-full blur-3xl" />
              <h3 className="text-xl font-bold mb-4 relative z-10">Subscription</h3>
              <div className="space-y-3 relative z-10">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Status</span>
                  <span className="capitalize font-medium">{status?.subscription_status ?? "active"}</span>
                </div>
                {status?.provider && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60">Provider</span>
                    <span className="capitalize font-medium">{status.provider}</span>
                  </div>
                )}
                {periodEnd && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60">Renews</span>
                    <span className="font-medium">{periodEnd}</span>
                  </div>
                )}
              </div>
              {plan !== "FREE" && (
                <Button
                  variant="ghost"
                  className="w-full mt-4 text-white/50 hover:text-white hover:bg-white/5 text-xs font-bold uppercase transition-colors"
                  onClick={() => manageBilling()}
                >
                  Manage Billing Portal <ArrowUpRight className="ml-2 w-3 h-3" />
                </Button>
              )}
            </Card>
          </div>
        </div>
      </div>
    );
  }
  
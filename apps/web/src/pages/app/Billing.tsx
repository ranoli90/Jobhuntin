import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import {
  ArrowUpRight,
  CheckCircle,
  AlertTriangle,
  FileText,
  Download,
  Loader2,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Page } from "../../components/ui/Page";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/Table";
import { useBilling } from "../../hooks/useBilling";
import { motion, useReducedMotion } from "framer-motion";
import { pushToast } from "../../lib/toast";
import { telemetry } from "../../lib/telemetry";

interface Invoice {
  id: string;
  created: number;
  total: number;
  invoice_pdf: string;
}

export default function Billing() {
  const {
    status,
    plan,
    usage,
    tiers,
    upgrade,
    addSeats,
    manageBilling,
    refetch,
    loading: billingLoading,
    error,
  } = useBilling();
  const shouldReduceMotion = useReducedMotion();

  const { data: invoices = [], isLoading: invoicesLoading } = useQuery<
    Invoice[]
  >({
    queryKey: ["invoices"],
    queryFn: () => api.get<Invoice[]>("/billing/invoices"),
  });

  const isLoading = billingLoading;

  if (isLoading) {
    return (
      <Page title="Billing & Quota">
        <div
          className="max-w-6xl mx-auto space-y-6 pb-6 px-4 lg:px-0"
          aria-busy="true"
          aria-label="Loading billing"
        >
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-2">
              <div className="h-8 w-48 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
              <div className="h-4 w-64 bg-slate-100 dark:bg-slate-800 rounded animate-pulse" />
            </div>
            <div className="h-8 w-24 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
          </div>
          <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="p-6 lg:p-8 border border-slate-200 dark:border-slate-800 rounded-2xl animate-pulse">
                <div className="h-6 w-40 bg-slate-200 dark:bg-slate-700 rounded mb-6" />
                <div className="space-y-4">
                  <div className="h-4 w-full bg-slate-100 dark:bg-slate-800 rounded" />
                  <div className="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full" />
                </div>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                {[1, 2, 3].map((index) => (
                  <div
                    key={index}
                    className="p-6 border border-slate-200 dark:border-slate-800 rounded-2xl animate-pulse"
                  >
                    <div className="h-6 w-24 bg-slate-200 dark:bg-slate-700 rounded mb-4" />
                    <div className="h-8 w-16 bg-slate-100 dark:bg-slate-800 rounded mb-2" />
                    <div className="h-4 w-full bg-slate-100 dark:bg-slate-800 rounded" />
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-6">
              <div className="p-6 border border-slate-200 dark:border-slate-800 rounded-2xl animate-pulse">
                <div className="h-6 w-32 bg-slate-200 dark:bg-slate-700 rounded mb-4" />
                <div className="h-4 w-full bg-slate-100 dark:bg-slate-800 rounded mb-2" />
                <div className="h-4 w-[75%] bg-slate-100 dark:bg-slate-800 rounded" />
              </div>
            </div>
          </div>
        </div>
      </Page>
    );
  }

  const usageUsed = usage?.monthly_used ?? 0;
  const usageLimit = usage?.monthly_limit ?? 100;
  const usagePercent = usage?.percentage_used ?? 0;
  const periodEnd = status?.current_period_end
    ? new Date(status.current_period_end).toLocaleDateString()
    : null;

  const actionMap: Record<string, (() => Promise<void>) | null> = {
    upgrade,
    addSeats,
  };
  const tiersWithActions = tiers.map((t) => ({
    ...t,
    action: t.actionKey ? (actionMap[t.actionKey] ?? null) : null,
  }));

  return (
    <Page title="Billing & Quota">
      <div className="max-w-6xl mx-auto space-y-6 pb-6 px-4 lg:px-0">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
              Billing & Quota
            </h2>
            <p className="text-slate-500 dark:text-slate-400 font-medium">
              Manage your subscription, usage, and invoices.
            </p>
          </div>
          <Badge variant="primary" className="py-2 px-4 rounded-xl font-bold">
            Plan: {plan || "FREE"}
          </Badge>
        </div>

        {error && (
          <div
            className="flex items-center gap-3 p-4 rounded-2xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-red-800 dark:text-red-200"
            role="alert"
          >
            <AlertTriangle
              className="h-5 w-5 text-red-500 flex-shrink-0"
              aria-hidden
            />
            <div className="flex-1">
              <p className="font-bold text-sm">Unable to load billing data</p>
              <p className="text-xs text-red-600 dark:text-red-300 mt-0.5">
                {error}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="shrink-0"
            >
              Retry
            </Button>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
          <div className="lg:col-span-2 space-y-6 lg:space-y-8">
            <Card
              className="p-6 lg:p-8 border-slate-200 dark:border-slate-800"
              shadow="sm"
            >
              <h3 className="text-xl font-black text-slate-900 dark:text-slate-100 mb-6 font-display">
                Current Allocation
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                  <p className="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase">
                    Monthly Volume
                  </p>
                  <p className="text-sm font-black text-slate-900 dark:text-slate-100">
                    {usageUsed} / {usageLimit}
                  </p>
                </div>
                <div className="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={
                      shouldReduceMotion
                        ? { width: `${Math.min(usagePercent, 100)}%` }
                        : { width: 0 }
                    }
                    animate={{ width: `${Math.min(usagePercent, 100)}%` }}
                    className="h-full bg-primary-500"
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 font-medium">
                  <span>
                    {usage?.monthly_remaining ?? usageLimit - usageUsed}{" "}
                    remaining
                  </span>
                  {periodEnd && <span>Resets {periodEnd}</span>}
                </div>
              </div>
            </Card>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
              {tiersWithActions.map((tier) => (
                <Card
                  key={tier.name}
                  className={`p-6 flex flex-col items-center text-center transition-all hover:shadow-lg ${tier.recommended ? "border-primary-500 shadow-xl shadow-primary-500/10 ring-1 ring-primary-500" : "border-slate-100 dark:border-slate-800"}`}
                >
                  <h4 className="font-black text-slate-900 dark:text-slate-100 text-lg mb-1">
                    {tier.name}
                  </h4>
                  <p className="text-3xl font-black text-slate-900 dark:text-slate-100 mb-6">
                    {tier.price}
                  </p>
                  <ul className="space-y-3 mb-8 flex-1">
                    {tier.features.map((f) => (
                      <li
                        key={f}
                        className="text-xs text-slate-500 dark:text-slate-400 font-medium flex items-center gap-2"
                      >
                        <CheckCircle className="w-3 h-3 text-emerald-500" /> {f}
                      </li>
                    ))}
                  </ul>
                  <Button
                    variant={tier.recommended ? "primary" : "outline"}
                    className="w-full font-bold text-xs uppercase rounded-xl"
                    disabled={tier.name === plan}
                    onClick={
                      tier.action
                        ? async () => {
                            if (tier.actionKey === "upgrade")
                              telemetry.track("upgrade_clicked", {
                                tier: tier.name,
                              });
                            if (tier.actionKey === "addSeats")
                              telemetry.track("add_seats_clicked", {
                                tier: tier.name,
                              });
                            try {
                              await tier.action!();
                            } catch (error_) {
                              pushToast({
                                title: "Checkout failed",
                                description:
                                  (error_ as Error).message ||
                                  "Please try again or use a different payment method.",
                                tone: "error",
                              });
                            }
                          }
                        : undefined
                    }
                  >
                    {tier.name === plan ? "Current" : "Upgrade"}
                  </Button>
                </Card>
              ))}
            </div>

            {/* Invoices section */}
            <Card
              className="p-6 lg:p-8 border-slate-200 dark:border-slate-800"
              shadow="sm"
            >
              <h3 className="text-xl font-black text-slate-900 dark:text-slate-100 mb-4 font-display">
                Invoice History
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
                View and download your invoices. All transactions are securely
                processed through Stripe.
              </p>
              <div className="overflow-x-auto -mx-2 sm:mx-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="min-w-[120px]">Date</TableHead>
                      <TableHead className="min-w-[100px]">Amount</TableHead>
                      <TableHead className="min-w-[100px] text-right">
                        Action
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoicesLoading ? (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center py-8">
                          <div className="flex items-center justify-center gap-2 text-slate-500">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Loading invoices...
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : invoices?.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center py-12">
                          <div className="flex flex-col items-center gap-3">
                            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                              <FileText className="w-6 h-6 text-slate-400" />
                            </div>
                            <div>
                              <p className="text-slate-900 dark:text-slate-100 font-medium">
                                No invoices yet
                              </p>
                              <p className="text-sm text-slate-500 dark:text-slate-400">
                                Your billing history will appear here
                              </p>
                            </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : (
                      invoices?.map((invoice) => (
                        <TableRow key={invoice.id}>
                          <TableCell className="font-medium">
                            {new Date(
                              invoice.created * 1000,
                            ).toLocaleDateString("en-US", {
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                            })}
                          </TableCell>
                          <TableCell className="font-bold text-slate-900 dark:text-slate-100">
                            ${(invoice.total / 100).toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right">
                            <a
                              href={invoice.invoice_pdf}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-medium text-sm hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded"
                              aria-label={`Download invoice from ${new Date(invoice.created * 1000).toLocaleDateString()}`}
                            >
                              <Download className="w-4 h-4" />
                              Download
                            </a>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </Card>
          </div>

          <div className="space-y-6">
            {/* LOW: Payment Methods Section */}
            <Card className="p-6" shadow="sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  Payment Methods
                </h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    pushToast({
                      title: "Payment methods feature coming soon",
                      tone: "info",
                    });
                  }}
                >
                  Add Payment Method
                </Button>
              </div>
              <div className="text-center py-8 text-slate-500">
                <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>
                  No payment methods on file. Add a payment method to enable
                  automatic billing.
                </p>
              </div>
            </Card>

            {/* LOW: Usage Charts Section */}
            <Card className="p-6" shadow="sm">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">
                Usage Over Time
              </h3>
              <div className="h-48 flex items-center justify-center border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-lg">
                <div className="text-center text-slate-500">
                  <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Usage charts coming soon</p>
                  <p className="text-xs mt-1">
                    Track your application usage trends over time
                  </p>
                </div>
              </div>
            </Card>

            <Card
              className="bg-slate-900 dark:bg-slate-950 text-white p-8 border-none overflow-hidden relative"
              shadow="lift"
            >
              <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary-500/20 rounded-full blur-3xl" />
              <h3 className="text-xl font-bold mb-4 relative z-10">
                Subscription
              </h3>
              <div className="space-y-3 relative z-10">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Status</span>
                  <span className="capitalize font-medium">
                    {status?.subscription_status ?? "active"}
                  </span>
                </div>
                {status?.provider && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60">Provider</span>
                    <span className="capitalize font-medium">
                      {status.provider}
                    </span>
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
                  Manage Billing Portal{" "}
                  <ArrowUpRight className="ml-2 w-3 h-3" />
                </Button>
              )}
            </Card>
          </div>
        </div>
      </div>
    </Page>
  );
}

import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { CreditCard, Receipt, Users } from "lucide-react";
import { useBilling } from "../hooks/useBilling";
import { pushToast } from "../lib/toast";
import { UsageBars } from "../components/Billing/UsageBars";
import { UpgradeCard } from "../components/Billing/UpgradeCard";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { DataTable } from "../components/ui/DataTable";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { EmptyState } from "../components/ui/EmptyState";

export default function BillingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { plan, status, usage, loading, error, upgrade, addSeats } = useBilling();

  useEffect(() => {
    if (searchParams.get("success") === "1") {
      pushToast({ title: "Payment successful! Your plan is updated.", tone: "success" });
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner label="Loading billing" />
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        title="Billing unavailable"
        description={error}
        actionLabel="Retry"
        onAction={() => window.location.reload()}
      />
    );
  }

  const invoices = status?.invoice_history ?? [];

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">Billing</p>
        <h1 className="font-display text-4xl">Plan & usage</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="space-y-6">
          <UpgradeCard
            currentPlan={plan}
            onUpgrade={upgrade}
            onAddSeats={addSeats}
          />

          <Card tone="shell" shadow="lift" className="p-6">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-brand-ink" />
              <h2 className="font-display text-xl">Team</h2>
            </div>
            <p className="mt-2 text-sm text-brand-ink/70">
              {status?.seats ? `${status.seats} seats active` : "Solo plan — invite teammates to unlock team features."}
            </p>
            <Button variant="ghost" className="mt-4" onClick={addSeats}>
              {status?.seats ? "Manage seats" : "Add seats"}
            </Button>
          </Card>
        </div>

        <div className="space-y-6">
          <Card tone="shell" shadow="lift" className="p-6">
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-brand-ink" />
              <h2 className="font-display text-xl">Usage this month</h2>
            </div>
            <div className="mt-4 space-y-4">
              <UsageBars
                used={usage?.applications_used ?? 0}
                limit={plan === "FREE" ? 50 : plan === "PRO" ? 200 : undefined}
                label="Applications submitted"
              />
              <div className="flex items-center justify-between text-sm">
                <span className="text-brand-ink/70">Plan</span>
                <Badge variant="lagoon">{plan}</Badge>
              </div>
              {status?.next_payment_at && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-brand-ink/70">Next billing</span>
                  <span className="text-brand-ink">{new Date(status.next_payment_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </Card>

          <Card tone="shell" shadow="lift" className="p-6">
            <div className="flex items-center gap-2">
              <Receipt className="h-5 w-5 text-brand-ink" />
              <h2 className="font-display text-xl">Invoice history</h2>
            </div>
            <div className="mt-4">
              <DataTable
                data={invoices}
                columns={[
                  { header: "ID", key: "id", render: (v) => (v as string).slice(0, 8) + "..." },
                  { header: "Amount", key: "amount", render: (v) => `$${v}` },
                  { header: "Status", key: "status", render: (v) => <Badge variant="outline">{v as string}</Badge> },
                  { header: "Date", key: "created_at", render: (v) => new Date(v as string).toLocaleDateString() },
                ]}
                emptyLabel="No invoices yet"
              />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

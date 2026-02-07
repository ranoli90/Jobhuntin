import { useEffect, useState } from "react";
import { getBillingUsage, getBillingStatus, createPortal, addSeats, type BillingUsage, type BillingStatus } from "../lib/api";

export default function UsagePage() {
  const [usage, setUsage] = useState<BillingUsage | null>(null);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [seatInput, setSeatInput] = useState("");

  useEffect(() => {
    Promise.all([getBillingUsage(), getBillingStatus()])
      .then(([u, b]) => { setUsage(u); setBilling(b); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handlePortal = async () => {
    try {
      const { portal_url } = await createPortal();
      window.open(portal_url, "_blank");
    } catch (err) {
      alert(String(err));
    }
  };

  const handleAddSeats = async () => {
    const seats = parseInt(seatInput, 10);
    if (isNaN(seats) || seats < 3) { alert("Minimum 3 seats"); return; }
    try {
      await addSeats(seats);
      alert(`Seats updated to ${seats}`);
      setSeatInput("");
      const u = await getBillingUsage();
      setUsage(u);
    } catch (err) {
      alert(String(err));
    }
  };

  if (loading) return <p className="text-muted-foreground">Loading usage...</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Usage & Billing</h1>

      {billing && (
        <div className="bg-card border border-border rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Current Plan</p>
              <p className="text-xl font-bold text-primary">{billing.plan}</p>
            </div>
            <button onClick={handlePortal} className="px-4 py-2 bg-muted text-foreground rounded-md text-sm hover:bg-muted/80 transition-colors">
              Manage in Stripe
            </button>
          </div>
          {billing.subscription_status !== "none" && (
            <p className="text-xs text-muted-foreground">
              Status: {billing.subscription_status}
              {billing.current_period_end && ` · Renews ${new Date(billing.current_period_end).toLocaleDateString()}`}
            </p>
          )}
        </div>
      )}

      {usage && (
        <div className="bg-card border border-border rounded-lg p-5 space-y-4">
          <h2 className="font-semibold">Monthly Quota</h2>
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Applications</span>
              <span className="font-medium">{usage.monthly_used} / {usage.monthly_limit}</span>
            </div>
            <div className="h-3 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  usage.percentage_used >= 90 ? "bg-red-500" : usage.percentage_used >= 70 ? "bg-yellow-500" : "bg-primary"
                }`}
                style={{ width: `${Math.min(100, usage.percentage_used)}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground">{usage.monthly_remaining} remaining · {usage.percentage_used}% used</p>
          </div>
          <div className="flex justify-between text-sm pt-2 border-t border-border">
            <span className="text-muted-foreground">Concurrent Processing</span>
            <span className="font-medium">{usage.concurrent_used} / {usage.concurrent_limit}</span>
          </div>
        </div>
      )}

      {billing && (billing.plan === "TEAM" || billing.plan === "ENTERPRISE") && (
        <div className="bg-card border border-border rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">Manage Seats</h2>
          <p className="text-sm text-muted-foreground">
            Additional seats beyond the included 3 are $49/seat/month, prorated.
          </p>
          <div className="flex gap-2">
            <input
              type="number"
              min={3}
              placeholder="Total seats"
              value={seatInput}
              onChange={(e) => setSeatInput(e.target.value)}
              className="w-32 px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button onClick={handleAddSeats} className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 transition-opacity">
              Update Seats
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { getM3Dashboard, getTeamOverview, getBillingStatus, type TeamOverview, type BillingStatus } from "../lib/api";

interface MRRByPlan { plan: string; tenant_count: number; plan_mrr: number }

export default function EnterpriseDashboard() {
  const [team, setTeam] = useState<TeamOverview | null>(null);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [mrr, setMrr] = useState<MRRByPlan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getTeamOverview(), getBillingStatus(), getM3Dashboard()])
      .then(([t, b, d]) => {
        setTeam(t);
        setBilling(b);
        setMrr((d as any).mrr_by_plan || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-muted-foreground">Loading enterprise dashboard...</p>;

  const totalMRR = mrr.reduce((s, r) => s + (r.plan_mrr || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Enterprise Console</h1>
          <p className="text-sm text-muted-foreground">
            Plan: <span className="text-primary font-semibold">{billing?.plan || "—"}</span>
            {billing?.subscription_status && ` · ${billing.subscription_status}`}
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-primary">${(totalMRR / 100).toLocaleString()}</p>
          <p className="text-xs text-muted-foreground">Total MRR</p>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Team Members", value: team?.member_count ?? 0 },
          { label: "Seats", value: `${team?.tenant.seat_count ?? 0}/${team?.tenant.max_seats ?? 0}` },
          { label: "Apps This Month", value: team?.total_apps_this_month ?? 0 },
          { label: "Pending Invites", value: team?.pending_invites ?? 0 },
        ].map((s) => (
          <div key={s.label} className="bg-card border border-border rounded-lg p-5">
            <p className="text-2xl font-bold text-foreground">{s.value}</p>
            <p className="text-sm text-muted-foreground">{s.label}</p>
          </div>
        ))}
      </div>

      {/* MRR by Plan */}
      {mrr.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-5">
          <h2 className="font-semibold mb-3">MRR by Plan</h2>
          <div className="space-y-2">
            {mrr.map((r) => (
              <div key={r.plan} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${
                    r.plan === "ENTERPRISE" ? "bg-purple-500" :
                    r.plan === "TEAM" ? "bg-blue-500" :
                    r.plan === "PRO" ? "bg-green-500" : "bg-muted"
                  }`} />
                  <span className="text-foreground font-medium">{r.plan}</span>
                  <span className="text-muted-foreground">({r.tenant_count} tenants)</span>
                </div>
                <span className="font-bold">${((r.plan_mrr || 0) / 100).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SLA & Contract */}
      <div className="bg-card border border-border rounded-lg p-5">
        <h2 className="font-semibold mb-3">Enterprise Contract</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">SLA Tier</p>
            <p className="font-medium text-foreground">Standard (99.9% uptime)</p>
          </div>
          <div>
            <p className="text-muted-foreground">Support</p>
            <p className="font-medium text-foreground">Priority email + Slack</p>
          </div>
          <div>
            <p className="text-muted-foreground">Data Residency</p>
            <p className="font-medium text-foreground">US (AWS us-east-1)</p>
          </div>
          <div>
            <p className="text-muted-foreground">SSO</p>
            <p className="font-medium text-primary">Configured</p>
          </div>
        </div>
      </div>
    </div>
  );
}

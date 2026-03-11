import { useEffect, useState } from "react";
import { getTeamOverview, getBillingUsage, type TeamOverview, type BillingUsage } from "../lib/api";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <p className="text-2xl font-bold text-foreground">{value}</p>
      <p className="text-sm text-muted-foreground">{label}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  );
}

function ProgressBar({ label, value, max, color = "bg-primary" }: { label: string; value: number; max: number; color?: string }) {
  const pct = Math.min(100, Math.round((value / Math.max(max, 1)) * 100));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-foreground font-medium">{value} / {max}</span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [team, setTeam] = useState<TeamOverview | null>(null);
  const [usage, setUsage] = useState<BillingUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getTeamOverview(), getBillingUsage()])
      .then(([t, u]) => { setTeam(t); setUsage(u); setError(null); })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Could not load dashboard");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-muted-foreground">Loading dashboard...</p>;
  if (error) return <p className="text-red-400">{error}</p>;
  if (!team) return <p className="text-red-400">Could not load team data.</p>;

  const t = team.tenant;
  const members = team.members ?? [];
  if (!t) return <p className="text-red-400">Invalid team data.</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t.team_name || t.name}</h1>
        <p className="text-sm text-muted-foreground">Plan: <span className="font-medium text-primary">{t.plan}</span></p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Team Members" value={team.member_count} sub={`${team.pending_invites} pending`} />
        <StatCard label="Seats" value={`${t.seat_count} / ${t.max_seats}`} />
        <StatCard label="Apps This Month" value={team.total_apps_this_month} />
        <StatCard label="Apps All Time" value={team.total_apps_all_time} />
      </div>

      {usage && (
        <div className="bg-card border border-border rounded-lg p-5 space-y-4">
          <h2 className="font-semibold">Quota Usage</h2>
          <ProgressBar
            label="Monthly Applications"
            value={usage.monthly_used}
            max={usage.monthly_limit}
            color={usage.percentage_used >= 90 ? "bg-red-500" : usage.percentage_used >= 70 ? "bg-yellow-500" : "bg-primary"}
          />
          <ProgressBar
            label="Concurrent Processing"
            value={usage.concurrent_used}
            max={usage.concurrent_limit}
          />
        </div>
      )}

      <div className="bg-card border border-border rounded-lg p-5 overflow-x-auto">
        <h2 className="font-semibold mb-3">Member Activity</h2>
        <table className="w-full text-sm min-w-[400px]">
          <thead>
            <tr className="text-muted-foreground text-left border-b border-border">
              <th className="pb-2">Member</th>
              <th className="pb-2">Role</th>
              <th className="pb-2 text-right">This Month</th>
              <th className="pb-2 text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.user_id} className="border-b border-border/50">
                <td className="py-2">
                  <div className="font-medium">{m.name || m.email}</div>
                  {m.name && <div className="text-xs text-muted-foreground">{m.email}</div>}
                </td>
                <td className="py-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    m.role === "OWNER" ? "bg-primary/20 text-primary" :
                    m.role === "ADMIN" ? "bg-yellow-500/20 text-yellow-400" :
                    "bg-muted text-muted-foreground"
                  }`}>{m.role}</span>
                </td>
                <td className="py-2 text-right font-medium">{m.apps_this_month}</td>
                <td className="py-2 text-right text-muted-foreground">{m.apps_total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface AuthorBlueprint {
  id: string; slug: string; name: string; version: string;
  approval_status: string; install_count: number;
  rating_avg: number; price_cents: number; created_at: string;
}

interface Earnings {
  total_earned_cents: number; pending_cents: number;
  paid_out_cents: number; total_payouts: number; total_installs: number;
}

async function authHeaders(): Promise<Record<string, string>> {
  // SECURITY: Use httpOnly cookie-based authentication instead of localStorage tokens
  // This prevents XSS attacks from stealing auth tokens
  const h: Record<string, string> = { "Content-Type": "application/json" };
  // No Authorization header needed - token is sent via httpOnly cookie
  return h;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers = await authHeaders();
  const opts: RequestInit = { 
    method, 
    headers,
    credentials: "include"  // SECURITY: Include httpOnly cookies for authentication
  };
  if (body) opts.body = JSON.stringify(body);
  const resp = await fetch(`${API_BASE}${path}`, opts);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API ${resp.status}: ${text}`);
  }
  return resp.json() as Promise<T>;
}

export default function AuthorDashboard() {
  const [blueprints, setBlueprints] = useState<AuthorBlueprint[]>([]);
  const [earnings, setEarnings] = useState<Earnings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [bpResp, eResp] = await Promise.all([
          request<AuthorBlueprint[]>("GET", "/marketplace/author/blueprints"),
          request<Earnings>("GET", "/marketplace/author/earnings"),
        ]);
        if (bpResp) setBlueprints(bpResp);
        if (eResp) setEarnings(eResp);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <p className="text-muted-foreground">Loading author dashboard...</p>;

  const statusColor = (s: string) => ({
    approved: "bg-green-500/20 text-green-400",
    pending: "bg-yellow-500/20 text-yellow-400",
    rejected: "bg-red-500/20 text-red-400",
  }[s] || "bg-muted text-muted-foreground");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Author Dashboard</h1>

      {/* Earnings */}
      {earnings && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Earned", value: `$${(earnings.total_earned_cents / 100).toFixed(2)}` },
            { label: "Pending", value: `$${(earnings.pending_cents / 100).toFixed(2)}` },
            { label: "Paid Out", value: `$${(earnings.paid_out_cents / 100).toFixed(2)}` },
            { label: "Total Installs", value: earnings.total_installs.toLocaleString() },
          ].map((s) => (
            <div key={s.label} className="bg-card border border-border rounded-lg p-4">
              <p className="text-xl font-bold text-foreground">{s.value}</p>
              <p className="text-xs text-muted-foreground">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Blueprints */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-muted-foreground text-left border-b border-border bg-muted/30">
              <th className="px-4 py-3">Blueprint</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Installs</th>
              <th className="px-4 py-3 text-right">Rating</th>
              <th className="px-4 py-3 text-right">Price</th>
            </tr>
          </thead>
          <tbody>
            {blueprints.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                No blueprints yet. Submit your first blueprint!
              </td></tr>
            ) : blueprints.map((bp) => (
              <tr key={bp.id} className="border-b border-border/50 hover:bg-muted/10">
                <td className="px-4 py-3">
                  <div className="font-medium text-foreground">{bp.name}</div>
                  <div className="text-xs text-muted-foreground">{bp.slug} · v{bp.version}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(bp.approval_status)}`}>
                    {bp.approval_status}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">{bp.install_count}</td>
                <td className="px-4 py-3 text-right text-yellow-400">{bp.rating_avg > 0 ? bp.rating_avg.toFixed(1) : "—"}</td>
                <td className="px-4 py-3 text-right">{bp.price_cents > 0 ? `$${(bp.price_cents / 100).toFixed(2)}` : "Free"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

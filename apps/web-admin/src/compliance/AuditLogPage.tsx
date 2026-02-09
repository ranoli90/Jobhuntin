import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface AuditEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource: string;
  resource_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const t = data.session?.access_token;
  return t ? { Authorization: `Bearer ${t}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [actionFilter, setActionFilter] = useState("");
  const pageSize = 25;

  const load = async (p: number = page, action: string = actionFilter) => {
    setLoading(true);
    try {
      const h = await authHeaders();
      const params = new URLSearchParams({ limit: String(pageSize), offset: String(p * pageSize) });
      if (action) params.set("action", action);
      const r = await fetch(`${API_BASE}/billing/audit-log?${params}`, { headers: h });
      if (r.ok) {
        const data = await r.json();
        setLogs(data.logs || []);
        setTotal(data.total || 0);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleFilter = () => { setPage(0); load(0, actionFilter); };
  const handleExport = async () => {
    try {
      const h = await authHeaders();
      const r = await fetch(`${API_BASE}/billing/audit-log/export?days=90`, { headers: h });
      if (r.ok) {
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = "audit_log.csv"; a.click();
        URL.revokeObjectURL(url);
      } else { alert("Export failed"); }
    } catch (e) { alert(String(e)); }
  };

  const actionColor = (a: string) => {
    if (a.includes("login")) return "text-green-400";
    if (a.includes("removed") || a.includes("delete")) return "text-red-400";
    if (a.includes("configured") || a.includes("changed")) return "text-yellow-400";
    return "text-muted-foreground";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Audit Log</h1>
          <p className="text-sm text-muted-foreground">SOC 2 compliance trail — {total} total entries</p>
        </div>
        <button onClick={handleExport}
          className="px-4 py-2 bg-muted text-foreground rounded-md text-sm hover:bg-muted/80 transition-colors">
          Export CSV (90 days)
        </button>
      </div>

      <div className="flex gap-2">
        <input value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}
          placeholder="Filter by action (e.g. sso, member, billing)"
          className="flex-1 px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
        <button onClick={handleFilter}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium">
          Filter
        </button>
      </div>

      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-muted-foreground text-left border-b border-border bg-muted/30">
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Resource</th>
              <th className="px-4 py-3">User ID</th>
              <th className="px-4 py-3">IP</th>
              <th className="px-4 py-3">Details</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">No audit entries</td></tr>
            ) : logs.map((entry) => (
              <tr key={entry.id} className="border-b border-border/50 hover:bg-muted/10">
                <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                  {new Date(entry.created_at).toLocaleString()}
                </td>
                <td className={`px-4 py-3 font-medium ${actionColor(entry.action)}`}>
                  {entry.action}
                </td>
                <td className="px-4 py-3">
                  <span className="text-foreground">{entry.resource}</span>
                  {entry.resource_id && (
                    <span className="text-muted-foreground text-xs ml-1">({entry.resource_id.slice(0, 8)})</span>
                  )}
                </td>
                <td className="px-4 py-3 text-muted-foreground font-mono text-xs">
                  {entry.user_id?.slice(0, 8) || "—"}
                </td>
                <td className="px-4 py-3 text-muted-foreground text-xs">{entry.ip_address || "—"}</td>
                <td className="px-4 py-3 text-muted-foreground text-xs max-w-xs truncate">
                  {JSON.stringify(entry.details).slice(0, 60)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {total > pageSize && (
        <div className="flex justify-between items-center">
          <button disabled={page === 0} onClick={() => { setPage(page - 1); load(page - 1); }}
            className="px-3 py-1 text-sm text-muted-foreground hover:text-foreground disabled:opacity-50">
            Previous
          </button>
          <span className="text-sm text-muted-foreground">
            Page {page + 1} of {Math.ceil(total / pageSize)}
          </span>
          <button disabled={(page + 1) * pageSize >= total} onClick={() => { setPage(page + 1); load(page + 1); }}
            className="px-3 py-1 text-sm text-muted-foreground hover:text-foreground disabled:opacity-50">
            Next
          </button>
        </div>
      )}
    </div>
  );
}

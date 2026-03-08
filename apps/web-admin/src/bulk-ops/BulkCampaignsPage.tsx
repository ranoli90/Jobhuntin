import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Campaign {
  id: string;
  name: string;
  status: string;
  filters: Record<string, string>;
  total_jobs: number;
  applied: number;
  failed: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
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

export default function BulkCampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  // Create form
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [creating, setCreating] = useState(false);

  const load = async () => {
    try {
      const r = await request<Campaign[]>("GET", "/bulk/campaigns");
      setCampaigns(r);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      await request("POST", "/bulk/campaigns", {
        name: name.trim(),
        filters: { title: title.trim(), location: location.trim() },
      });
      setName(""); setTitle(""); setLocation(""); setShowCreate(false);
      load();
    } catch (e) { alert(String(e)); }
    finally { setCreating(false); }
  };

  const handleStart = async (id: string) => {
    await request("POST", `/bulk/campaigns/${id}/start`);
    load();
  };

  const statusColor = (s: string) => {
    switch (s) {
      case "running": return "bg-blue-500/20 text-blue-400";
      case "completed": return "bg-green-500/20 text-green-400";
      case "paused": return "bg-yellow-500/20 text-yellow-400";
      case "draft": return "bg-muted text-muted-foreground";
      default: return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Bulk Campaigns</h1>
          <p className="text-sm text-muted-foreground">
            Apply to multiple jobs at once with filtered criteria.
          </p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90">
          {showCreate ? "Cancel" : "New Campaign"}
        </button>
      </div>

      {showCreate && (
        <div className="bg-card border border-border rounded-lg p-5 space-y-4">
          <h2 className="font-semibold">Create Campaign</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Campaign Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Data Analyst NYC Batch"
                className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
            </div>
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Job Title Filter</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Data Analyst"
                className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
            </div>
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Location Filter</label>
              <input value={location} onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. New York, NY"
                className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
            </div>
          </div>
          <button onClick={handleCreate} disabled={creating || !name.trim()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50">
            {creating ? "Creating..." : "Create Campaign"}
          </button>
        </div>
      )}

      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-muted-foreground text-left border-b border-border bg-muted/30">
              <th className="px-4 py-3">Campaign</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Filters</th>
              <th className="px-4 py-3 text-right">Jobs</th>
              <th className="px-4 py-3 text-right">Applied</th>
              <th className="px-4 py-3 text-right">Failed</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
            ) : campaigns.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">No campaigns yet</td></tr>
            ) : campaigns.map((c) => (
              <tr key={c.id} className="border-b border-border/50 hover:bg-muted/10">
                <td className="px-4 py-3">
                  <div className="font-medium text-foreground">{c.name}</div>
                  <div className="text-xs text-muted-foreground">{new Date(c.created_at).toLocaleDateString()}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(c.status)}`}>
                    {c.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-muted-foreground text-xs">
                  {Object.entries(c.filters).filter(([, v]) => v).map(([k, v]) => `${k}: ${v}`).join(", ") || "—"}
                </td>
                <td className="px-4 py-3 text-right font-medium">{c.total_jobs}</td>
                <td className="px-4 py-3 text-right text-green-400">{c.applied}</td>
                <td className="px-4 py-3 text-right text-red-400">{c.failed}</td>
                <td className="px-4 py-3 text-right">
                  {c.status === "draft" && (
                    <button onClick={() => handleStart(c.id)}
                      className="text-xs text-primary hover:underline">Start</button>
                  )}
                  {c.status === "running" && (
                    <span className="text-xs text-blue-400">In progress...</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

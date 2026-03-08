import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface ApiKey {
  id: string; name: string; key_prefix: string; tier: string;
  rate_limit_rpm: number; monthly_quota: number; calls_this_month: number;
  is_active: boolean; last_used_at: string | null; created_at: string;
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

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("Default");
  const [newKeyTier, setNewKeyTier] = useState("free");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const load = async () => {
    try {
      const data = await request<ApiKey[]>("GET", "/developer/api-keys");
      setKeys(data);
    } catch (e) {
      alert(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const createKey = async () => {
    setCreating(true);
    try {
      const data = await request("POST", "/developer/api-keys", {
        name: newKeyName, tier: newKeyTier
      });
      setCreatedKey(data.raw_key);
      load();
    } catch (e) { alert(String(e)); }
    finally { setCreating(false); }
  };

  const revokeKey = async (id: string) => {
    if (!confirm("Revoke this API key? This cannot be undone.")) return;
    await request("DELETE", `/developer/api-keys/${id}`);
    load();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">API Keys</h1>
        <p className="text-sm text-muted-foreground">Manage API keys for the Sorce Platform API v2.</p>
      </div>

      {/* Create key */}
      <div className="bg-card border border-border rounded-lg p-5 space-y-3">
        <h2 className="font-semibold text-foreground">Create New Key</h2>
        <div className="flex gap-3">
          <input value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="Key name" className="flex-1 px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
          <select value={newKeyTier} onChange={(e) => setNewKeyTier(e.target.value)}
            className="px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm">
            <option value="free">Free (100/mo)</option>
            <option value="pro">Pro (10k/mo, $99)</option>
            <option value="enterprise">Enterprise (unlimited)</option>
          </select>
          <button onClick={createKey} disabled={creating}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium">
            {creating ? "Creating..." : "Create Key"}
          </button>
        </div>
        {createdKey && (
          <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-md">
            <p className="text-xs text-green-400 font-semibold mb-1">Key created — copy it now (shown only once):</p>
            <code className="text-sm text-green-300 select-all break-all">{createdKey}</code>
          </div>
        )}
      </div>

      {/* Key list */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-muted-foreground text-left border-b border-border bg-muted/30">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Key</th>
              <th className="px-4 py-3">Tier</th>
              <th className="px-4 py-3 text-right">Usage</th>
              <th className="px-4 py-3">Last Used</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
            ) : keys.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">No API keys yet.</td></tr>
            ) : keys.map((k) => (
              <tr key={k.id} className="border-b border-border/50">
                <td className="px-4 py-3 font-medium text-foreground">{k.name}</td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{k.key_prefix}...</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    k.tier === "enterprise" ? "bg-purple-500/20 text-purple-400"
                    : k.tier === "pro" ? "bg-blue-500/20 text-blue-400"
                    : "bg-muted text-muted-foreground"
                  }`}>{k.tier}</span>
                </td>
                <td className="px-4 py-3 text-right">{k.calls_this_month}/{k.monthly_quota || "∞"}</td>
                <td className="px-4 py-3 text-muted-foreground text-xs">
                  {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : "Never"}
                </td>
                <td className="px-4 py-3">
                  <button onClick={() => revokeKey(k.id)}
                    className="text-xs text-red-400 hover:text-red-300">Revoke</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Tier comparison */}
      <div className="bg-card border border-border rounded-lg p-5">
        <h2 className="font-semibold text-foreground mb-4">API Tiers</h2>
        <div className="grid grid-cols-3 gap-4">
          {[
            { tier: "Free", price: "$0/mo", limit: "100 calls/mo", rpm: "60 RPM", features: ["Read & write", "Webhook callbacks"] },
            { tier: "Pro", price: "$99/mo", limit: "10,000 calls/mo", rpm: "300 RPM", features: ["Batch submissions", "Priority support", "Usage analytics"] },
            { tier: "Enterprise", price: "Custom", limit: "Unlimited", rpm: "Custom", features: ["Dedicated support", "SLA", "Staffing API", "Custom webhooks"] },
          ].map((t) => (
            <div key={t.tier} className="border border-border rounded-lg p-4 space-y-2">
              <h3 className="font-bold text-foreground">{t.tier}</h3>
              <p className="text-lg font-bold text-primary">{t.price}</p>
              <p className="text-xs text-muted-foreground">{t.limit} · {t.rpm}</p>
              <ul className="text-xs text-muted-foreground space-y-1 mt-2">
                {t.features.map((f) => <li key={f}>✓ {f}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

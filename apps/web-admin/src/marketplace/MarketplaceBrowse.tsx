import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Blueprint {
  id: string; slug: string; name: string; description: string;
  category: string; author_name: string; version: string;
  install_count: number; rating_avg: number; rating_count: number;
  price_cents: number; is_featured: boolean; icon_url: string | null;
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

export default function MarketplaceBrowse() {
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
  const [categories, setCategories] = useState<Array<{ category: string; count: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [installing, setInstalling] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: "20", sort: "popular" });
      if (search) params.set("search", search);
      if (category) params.set("category", category);
      const [bpResp, catResp] = await Promise.all([
        fetch(`${API_BASE}/marketplace/blueprints?${params}`, { credentials: "include" }),
        fetch(`${API_BASE}/marketplace/categories`, { credentials: "include" }),
      ]);
      if (bpResp.ok) { const d = await bpResp.json(); setBlueprints(d.blueprints || []); }
      if (catResp.ok) setCategories(await catResp.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [category]);

  const handleInstall = async (id: string) => {
    setInstalling(id);
    try {
      const h = await authHeaders();
      const r = await fetch(`${API_BASE}/marketplace/blueprints/${id}/install`, {
        method: "POST", 
        headers: h, 
        credentials: "include",  // SECURITY: Include httpOnly cookies for authentication
        body: JSON.stringify({ config: {} }),
      });
      if (r.ok) { alert("Blueprint installed!"); load(); }
      else { const e = await r.json().catch(() => ({})); alert(e.detail || "Install failed"); }
    } catch (e) { alert(String(e)); }
    finally { setInstalling(null); }
  };

  const stars = (avg: number) => "★".repeat(Math.round(avg)) + "☆".repeat(5 - Math.round(avg));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Blueprint Marketplace</h1>
        <p className="text-sm text-muted-foreground">Community-built automation blueprints for every use case.</p>
      </div>

      {/* Search + Filter */}
      <div className="flex gap-3">
        <input value={search} onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          placeholder="Search blueprints..."
          className="flex-1 px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm">
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c.category} value={c.category}>{c.category} ({c.count})</option>
          ))}
        </select>
        <button onClick={load} className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium">
          Search
        </button>
      </div>

      {/* Blueprint Grid */}
      {loading ? (
        <p className="text-muted-foreground text-center py-12">Loading marketplace...</p>
      ) : blueprints.length === 0 ? (
        <p className="text-muted-foreground text-center py-12">No blueprints found.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {blueprints.map((bp) => (
            <div key={bp.id} className="bg-card border border-border rounded-lg p-5 flex flex-col">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-lg">
                    {bp.icon_url ? <img src={bp.icon_url} alt="" className="w-6 h-6" /> : "📦"}
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">{bp.name}</h3>
                    <p className="text-xs text-muted-foreground">by {bp.author_name}</p>
                  </div>
                </div>
                {bp.is_featured && (
                  <span className="text-[10px] bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full font-semibold">
                    FEATURED
                  </span>
                )}
              </div>

              <p className="text-sm text-muted-foreground flex-1 mb-3">{bp.description}</p>

              <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                <span className="text-yellow-400">{stars(bp.rating_avg)} <span className="text-muted-foreground">({bp.rating_count})</span></span>
                <span>{bp.install_count.toLocaleString()} installs</span>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  {bp.price_cents > 0 ? (
                    <span className="font-bold text-foreground">${(bp.price_cents / 100).toFixed(2)}/mo</span>
                  ) : (
                    <span className="text-green-400 font-semibold text-sm">Free</span>
                  )}
                </div>
                <button
                  onClick={() => handleInstall(bp.id)}
                  disabled={installing === bp.id}
                  className="px-4 py-1.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50"
                >
                  {installing === bp.id ? "Installing..." : "Install"}
                </button>
              </div>

              <div className="flex gap-2 mt-3">
                <span className="text-[10px] bg-muted px-2 py-0.5 rounded-full text-muted-foreground">{bp.category}</span>
                <span className="text-[10px] bg-muted px-2 py-0.5 rounded-full text-muted-foreground">v{bp.version}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

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

const CATEGORIES = ["job-applications", "grants", "vendor-onboarding", "scholarships", "compliance", "hr-forms", "insurance", "general"];

export default function SubmitBlueprint() {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [longDesc, setLongDesc] = useState("");
  const [category, setCategory] = useState("general");
  const [price, setPrice] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (!name.trim() || !slug.trim() || !description.trim()) {
      alert("Name, slug, and description are required"); return;
    }
    setSubmitting(true);
    try {
      const h = await authHeaders();
      const r = await fetch(`${API_BASE}/marketplace/blueprints/submit`, {
        method: "POST", 
        headers: h,
        credentials: "include",  // SECURITY: Include httpOnly cookies for authentication
        body: JSON.stringify({
          name: name.trim(), slug: slug.trim().toLowerCase().replace(/\s+/g, "-"),
          description: description.trim(), long_description: longDesc.trim(),
          category, price_cents: Math.round(price * 100),
        }),
      });
      if (r.ok) {
        setSubmitted(true);
      } else {
        const e = await r.json().catch(() => ({}));
        alert(e.detail || "Submission failed");
      }
    } catch (e) { alert(String(e)); }
    finally { setSubmitting(false); }
  };

  if (submitted) {
    return (
      <div className="max-w-xl mx-auto text-center py-16 space-y-4">
        <div className="text-5xl">🎉</div>
        <h2 className="text-2xl font-bold text-foreground">Blueprint Submitted!</h2>
        <p className="text-muted-foreground">Your blueprint is being reviewed. You'll be notified once it's approved.</p>
        <button onClick={() => { setSubmitted(false); setName(""); setSlug(""); setDescription(""); setLongDesc(""); setCategory("general"); setPrice(0); }}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium">
          Submit Another
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Submit a Blueprint</h1>
        <p className="text-sm text-muted-foreground">Share your automation with the community. Authors earn 70% revenue share.</p>
      </div>

      <div className="bg-card border border-border rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-muted-foreground block mb-1">Blueprint Name *</label>
            <input value={name} onChange={(e) => { const v = e.target.value; setName(v); setSlug((prev) => prev ? prev : v.toLowerCase().replace(/\s+/g, "-")); }}
              placeholder="e.g. Scholarship Applications"
              className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
          </div>
          <div>
            <label className="text-sm text-muted-foreground block mb-1">Slug *</label>
            <input value={slug} onChange={(e) => setSlug(e.target.value)}
              placeholder="e.g. scholarship-app"
              className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm font-mono" />
          </div>
        </div>

        <div>
          <label className="text-sm text-muted-foreground block mb-1">Short Description *</label>
          <input value={description} onChange={(e) => setDescription(e.target.value)}
            placeholder="One-line description of what this blueprint does"
            className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
        </div>

        <div>
          <label className="text-sm text-muted-foreground block mb-1">Full Description</label>
          <textarea value={longDesc} onChange={(e) => setLongDesc(e.target.value)} rows={4}
            placeholder="Detailed description, use cases, supported portals..."
            className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-muted-foreground block mb-1">Category</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm">
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-muted-foreground block mb-1">Monthly Price ($)</label>
            <input type="number" value={price} onChange={(e) => setPrice(Number(e.target.value))}
              min={0} step={0.99} placeholder="0 = free"
              className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
            {price > 0 && <p className="text-xs text-muted-foreground mt-1">You earn: ${(price * 0.7).toFixed(2)}/install/mo (70%)</p>}
          </div>
        </div>

        <button onClick={handleSubmit} disabled={submitting}
          className="w-full py-2.5 bg-primary text-primary-foreground rounded-md font-medium text-sm hover:opacity-90 disabled:opacity-50">
          {submitting ? "Submitting..." : "Submit for Review"}
        </button>
      </div>
    </div>
  );
}

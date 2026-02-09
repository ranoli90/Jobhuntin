import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface SSOConfig {
  tenant_id: string;
  provider: string;
  is_active: boolean;
  entity_id: string;
  sso_url: string;
}

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const t = data.session?.access_token;
  return t ? { Authorization: `Bearer ${t}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

export default function SSOConfigPage() {
  const [config, setConfig] = useState<SSOConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [provider, setProvider] = useState("saml");
  const [entityId, setEntityId] = useState("");
  const [ssoUrl, setSsoUrl] = useState("");
  const [certificate, setCertificate] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const h = await authHeaders();
        const r = await fetch(`${API_BASE}/sso/config`, { headers: h });
        if (r.ok) {
          const c: SSOConfig = await r.json();
          setConfig(c);
          setProvider(c.provider || "saml");
          setEntityId(c.entity_id);
          setSsoUrl(c.sso_url);
        }
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const h = await authHeaders();
      const r = await fetch(`${API_BASE}/sso/config`, {
        method: "POST", headers: h,
        body: JSON.stringify({ provider, entity_id: entityId, sso_url: ssoUrl, certificate }),
      });
      if (r.ok) {
        const c = await r.json();
        setConfig(c);
        alert("SSO configuration saved!");
      } else {
        const err = await r.json().catch(() => ({}));
        alert(err.detail || "Failed to save");
      }
    } catch (e) { alert(String(e)); }
    finally { setSaving(false); }
  };

  if (loading) return <p className="text-muted-foreground">Loading SSO config...</p>;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">SSO Configuration</h1>
        <p className="text-sm text-muted-foreground">
          Configure SAML 2.0 or OIDC single sign-on for your organization.
        </p>
      </div>

      {config?.is_active && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-green-400 text-sm">
          SSO is active — members can sign in via your identity provider.
        </div>
      )}

      <div className="bg-card border border-border rounded-lg p-5 space-y-4">
        <div>
          <label className="text-sm text-muted-foreground block mb-1">Provider</label>
          <select value={provider} onChange={(e) => setProvider(e.target.value)}
            className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm">
            <option value="saml">SAML 2.0</option>
            <option value="oidc">OpenID Connect</option>
          </select>
        </div>

        <div>
          <label className="text-sm text-muted-foreground block mb-1">IdP Entity ID</label>
          <input value={entityId} onChange={(e) => setEntityId(e.target.value)}
            placeholder="https://idp.yourcompany.com/saml/metadata"
            className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
        </div>

        <div>
          <label className="text-sm text-muted-foreground block mb-1">SSO URL</label>
          <input value={ssoUrl} onChange={(e) => setSsoUrl(e.target.value)}
            placeholder="https://idp.yourcompany.com/saml/sso"
            className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm" />
        </div>

        <div>
          <label className="text-sm text-muted-foreground block mb-1">X.509 Certificate (PEM)</label>
          <textarea value={certificate} onChange={(e) => setCertificate(e.target.value)}
            rows={4} placeholder="-----BEGIN CERTIFICATE-----"
            className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm font-mono" />
        </div>

        <div className="bg-muted/50 rounded-lg p-3 text-xs text-muted-foreground space-y-1">
          <p><strong>SP Metadata URL:</strong> {API_BASE}/sso/saml/metadata</p>
          <p><strong>ACS URL:</strong> {API_BASE}/sso/saml/acs</p>
          <p><strong>Entity ID:</strong> {API_BASE}/sso/saml/metadata</p>
        </div>

        <button onClick={handleSave} disabled={saving}
          className="w-full py-2 bg-primary text-primary-foreground rounded-md font-medium text-sm hover:opacity-90 disabled:opacity-50">
          {saving ? "Saving..." : "Save SSO Configuration"}
        </button>
      </div>
    </div>
  );
}

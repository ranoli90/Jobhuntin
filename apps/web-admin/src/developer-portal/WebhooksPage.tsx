import { useEffect, useState } from "react";
import { apiRequest } from "../lib/api";

interface Webhook {
  id: string; url: string; events: string[]; is_active: boolean;
  failure_count: number; last_success_at: string | null; created_at: string;
}

const EVENT_OPTIONS = [
  "application.completed", "application.failed", "application.hold",
  "application.queued", "staffing.batch_completed",
];

export default function WebhooksPage() {
  const [hooks, setHooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [events, setEvents] = useState<string[]>(["application.completed", "application.failed"]);
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);

  const load = async () => {
    setError(null);
    try {
      const data = await apiRequest<Webhook[]>("GET", "/developer/webhooks");
      setHooks(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load webhooks";
      setError(message);
      setHooks([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!url.trim()) return;
    try {
      const data = await apiRequest<{ secret?: string }>("POST", "/developer/webhooks", { url, events });
      setCreatedSecret(data.secret ?? null);
      setUrl("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create webhook");
    }
  };

  const remove = async (id: string) => {
    try {
      await apiRequest("DELETE", `/developer/webhooks/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete webhook");
    }
  };

  const toggleEvent = (ev: string) => {
    setEvents((prev) => prev.includes(ev) ? prev.filter((e) => e !== ev) : [...prev, ev]);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Webhooks</h1>
        <p className="text-sm text-muted-foreground">Receive real-time notifications when application status changes.</p>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-between gap-4">
          <p className="text-sm text-red-400 font-medium">{error}</p>
          <button
            onClick={() => { setError(null); setLoading(true); load(); }}
            className="text-sm font-medium text-red-400 hover:text-red-300 underline"
          >
            Retry
          </button>
        </div>
      )}

      <div className="bg-card border border-border rounded-lg p-5 space-y-3">
        <h2 className="font-semibold text-foreground">Add Webhook Endpoint</h2>
        <input value={url} onChange={(e) => setUrl(e.target.value)}
          placeholder="https://your-server.com/webhook"
          className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm"
          aria-label="Webhook URL" />
        <div className="flex flex-wrap gap-2">
          {EVENT_OPTIONS.map((ev) => (
            <button key={ev} onClick={() => toggleEvent(ev)}
              className={`text-xs px-3 py-1 rounded-full border ${
                events.includes(ev) ? "bg-primary/10 border-primary text-primary" : "border-border text-muted-foreground"
              }`}>{ev}</button>
          ))}
        </div>
        <button onClick={create} className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium">
          Create Webhook
        </button>
        {createdSecret && (
          <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-md">
            <p className="text-xs text-green-400 font-semibold mb-1">Signing secret (shown once):</p>
            <code className="text-sm text-green-300 select-all break-all">{createdSecret}</code>
          </div>
        )}
      </div>

      <div className="bg-card border border-border rounded-lg overflow-x-auto overflow-hidden">
        <table className="w-full text-sm min-w-[500px]">
          <thead>
            <tr className="text-muted-foreground text-left border-b border-border bg-muted/30">
              <th className="px-4 py-3">URL</th>
              <th className="px-4 py-3">Events</th>
              <th className="px-4 py-3">Failures</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
            ) : hooks.length === 0 ? (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">No webhooks configured.</td></tr>
            ) : hooks.map((h) => (
              <tr key={h.id} className="border-b border-border/50">
                <td className="px-4 py-3 font-mono text-xs text-foreground">{h.url}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {h.events.map((e) => (
                      <span key={e} className="text-[10px] bg-muted px-2 py-0.5 rounded-full text-muted-foreground">{e}</span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  {h.failure_count > 0 ? (
                    <span className="text-red-400 text-xs">{h.failure_count} failures</span>
                  ) : <span className="text-green-400 text-xs">Healthy</span>}
                </td>
                <td className="px-4 py-3">
                  <button onClick={() => remove(h.id)} className="text-xs text-red-400 hover:text-red-300">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

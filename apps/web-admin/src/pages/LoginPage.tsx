import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const returnTo = window.location.pathname || "/";
      const resp = await fetch(`${API_BASE}/auth/magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          return_to: returnTo,
          admin_redirect: true,
        }),
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        const detail = data?.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail[0]?.msg ?? detail.join(", ")
              : "Request failed";
        setError(msg || "Request failed");
        return;
      }
      setSent(true);
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="w-full max-w-sm space-y-6 p-8 bg-card rounded-xl border border-border">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-primary">Check your email</h1>
            <p className="text-sm text-muted-foreground mt-1">
              We sent a sign-in link to your email. Click the link to sign in,
              then return to this admin dashboard.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="w-full max-w-sm space-y-6 p-8 bg-card rounded-xl border border-border">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-primary">Sorce Admin</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Team management portal. Sign in with a magic link.
          </p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            aria-label="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full min-h-[44px] py-2 bg-primary text-primary-foreground rounded-md font-medium text-sm hover:opacity-90 disabled:opacity-50 transition-opacity focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            {loading ? "Sending link..." : "Send sign-in link"}
          </button>
        </form>
      </div>
    </div>
  );
}

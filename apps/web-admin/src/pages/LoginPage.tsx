import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        setError(data.detail || "Login failed");
        return;
      }
      const data = await resp.json();
      sessionStorage.setItem("auth_token", data.token);
      window.location.reload();
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="w-full max-w-sm space-y-6 p-8 bg-card rounded-xl border border-border">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-primary">Sorce Admin</h1>
          <p className="text-sm text-muted-foreground mt-1">Team management portal</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-primary text-primary-foreground rounded-md font-medium text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}

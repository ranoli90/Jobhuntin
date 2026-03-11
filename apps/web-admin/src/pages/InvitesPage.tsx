import { useEffect, useState } from "react";
import { getTeamInvites, inviteMember, type TeamInvite } from "../lib/api";

export default function InvitesPage() {
  const [invites, setInvites] = useState<TeamInvite[]>([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("MEMBER");
  const [sending, setSending] = useState(false);

  const load = () => {
    getTeamInvites()
      .then(setInvites)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setSending(true);
    try {
      await inviteMember(email.trim(), role);
      setEmail("");
      load();
    } catch (err) {
      alert(String(err));
    } finally {
      setSending(false);
    }
  };

  const statusColor = (s: string) => {
    switch (s) {
      case "pending": return "bg-yellow-500/20 text-yellow-400";
      case "accepted": return "bg-green-500/20 text-green-400";
      case "expired": return "bg-muted text-muted-foreground";
      case "revoked": return "bg-red-500/20 text-red-400";
      default: return "bg-muted text-muted-foreground";
    }
  };

  if (loading) return <p className="text-muted-foreground">Loading invites...</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Team Invites</h1>

      <form onSubmit={handleInvite} className="bg-card border border-border rounded-lg p-5 space-y-3">
        <h2 className="font-semibold">Invite a New Member</h2>
        <div className="flex gap-2">
          <input
            type="email"
            placeholder="colleague@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="flex-1 px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            required
            aria-label="Email address"
          />
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="px-3 py-2 bg-muted border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label="Role"
          >
            <option value="MEMBER">Member</option>
            <option value="ADMIN">Admin</option>
          </select>
          <button
            type="submit"
            disabled={sending}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {sending ? "Sending..." : "Send Invite"}
          </button>
        </div>
      </form>

      <div className="bg-card border border-border rounded-lg overflow-x-auto overflow-hidden">
        <table className="w-full text-sm min-w-[400px]">
          <thead>
            <tr className="text-muted-foreground text-left border-b border-border bg-muted/30">
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Sent</th>
              <th className="px-4 py-3">Expires</th>
            </tr>
          </thead>
          <tbody>
            {invites.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-muted-foreground">No invites yet</td></tr>
            ) : invites.map((inv) => (
              <tr key={inv.id} className="border-b border-border/50">
                <td className="px-4 py-3 font-medium">{inv.email}</td>
                <td className="px-4 py-3 text-muted-foreground">{inv.role}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(inv.status)}`}>{inv.status}</span>
                </td>
                <td className="px-4 py-3 text-muted-foreground">{new Date(inv.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3 text-muted-foreground">{new Date(inv.expires_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

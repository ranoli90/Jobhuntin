import { useEffect, useState } from "react";
import { getTeamMembers, removeMember, type TeamMember } from "../lib/api";

export default function MembersPage() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);

  const load = () => {
    getTeamMembers()
      .then(setMembers)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleRemove = async (userId: string, email: string) => {
    if (!confirm(`Remove ${email} from the team?`)) return;
    setRemoving(userId);
    try {
      await removeMember(userId);
      setMembers((prev) => prev.filter((m) => m.user_id !== userId));
    } catch (err) {
      alert(String(err));
    } finally {
      setRemoving(null);
    }
  };

  if (loading) return <p className="text-muted-foreground">Loading members...</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Team Members</h1>
        <span className="text-sm text-muted-foreground">{members.length} member(s)</span>
      </div>

      <div className="bg-card border border-border rounded-lg overflow-x-auto overflow-hidden">
        <table className="w-full text-sm min-w-[500px]">
          <thead>
            <tr className="text-muted-foreground text-left border-b border-border bg-muted/30">
              <th className="px-4 py-3">Member</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3 text-right">Apps (Month)</th>
              <th className="px-4 py-3 text-right">Apps (Total)</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.user_id} className="border-b border-border/50 hover:bg-muted/10 transition-colors">
                <td className="px-4 py-3">
                  <div className="font-medium">{m.name || "—"}</div>
                  <div className="text-xs text-muted-foreground">{m.email}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    m.role === "OWNER" ? "bg-primary/20 text-primary" :
                    m.role === "ADMIN" ? "bg-yellow-500/20 text-yellow-400" :
                    "bg-muted text-muted-foreground"
                  }`}>{m.role}</span>
                </td>
                <td className="px-4 py-3 text-right font-medium">{m.apps_this_month}</td>
                <td className="px-4 py-3 text-right text-muted-foreground">{m.apps_total}</td>
                <td className="px-4 py-3 text-right">
                  {m.role !== "OWNER" && (
                    <button
                      onClick={() => handleRemove(m.user_id, m.email)}
                      disabled={removing === m.user_id}
                      className="min-h-[44px] min-w-[44px] px-3 text-xs text-red-400 hover:text-red-300 disabled:opacity-50 transition-colors focus-visible:ring-2 focus-visible:ring-primary rounded"
                      aria-label={`Remove ${m.email}`}
                    >
                      {removing === m.user_id ? "Removing..." : "Remove"}
                    </button>
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

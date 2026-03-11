/**
 * TeamOwnerScreen — mobile view for TEAM plan owners.
 *
 * Shows team overview, member list, quick invite, and usage stats.
 * Deep links to the web admin for full management.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  TextInput,
  Alert,
  Linking,
} from "react-native";
import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../lib/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TeamMember {
  user_id: string;
  role: string;
  email: string;
  name: string | null;
  apps_this_month: number;
  apps_total: number;
}

interface TeamOverview {
  tenant: {
    id: string;
    name: string;
    team_name: string | null;
    plan: string;
    seat_count: number;
    max_seats: number;
  };
  members: TeamMember[];
  member_count: number;
  pending_invites: number;
  total_apps_this_month: number;
  total_apps_all_time: number;
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}`, "Content-Type": "application/json" }
    : { "Content-Type": "application/json" };
}

async function fetchTeamOverview(): Promise<TeamOverview> {
  const headers = await getAuthHeaders();
  const resp = await fetch(`${API_BASE_URL}/billing/team`, { headers });
  if (!resp.ok) throw new Error(`Failed: ${resp.status}`);
  return resp.json();
}

async function sendInvite(email: string): Promise<void> {
  const headers = await getAuthHeaders();
  const resp = await fetch(`${API_BASE_URL}/billing/invite`, {
    method: "POST",
    headers,
    body: JSON.stringify({ email, role: "MEMBER" }),
  });
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data.detail || `Failed: ${resp.status}`);
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TeamOwnerScreen() {
  const [team, setTeam] = useState<TeamOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviting, setInviting] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchTeamOverview();
      setTeam(data);
    } catch (err) {
      console.error("Failed to load team:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleInvite = async () => {
    if (!inviteEmail.trim()) return;
    setInviting(true);
    try {
      await sendInvite(inviteEmail.trim());
      Alert.alert("Invite Sent", `Invitation sent to ${inviteEmail}`);
      setInviteEmail("");
      load();
    } catch (err) {
      Alert.alert("Could not send invite", String(err) || "Please try again.");
    } finally {
      setInviting(false);
    }
  };

  const openAdminDashboard = () => {
    Linking.openURL("https://admin.sorce.app");
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  if (!team) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Could not load team data.</Text>
      </View>
    );
  }

  const t = team.tenant;

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.teamName}>{t.team_name || t.name}</Text>
        <View style={styles.planBadge}>
          <Text style={styles.planText}>{t.plan}</Text>
        </View>
      </View>

      {/* Stats grid */}
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{team.member_count}</Text>
          <Text style={styles.statLabel}>Members</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{t.seat_count}/{t.max_seats}</Text>
          <Text style={styles.statLabel}>Seats</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{team.total_apps_this_month}</Text>
          <Text style={styles.statLabel}>Apps/Month</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{team.pending_invites}</Text>
          <Text style={styles.statLabel}>Pending</Text>
        </View>
      </View>

      {/* Quick invite */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Invite</Text>
        <View style={styles.inviteRow}>
          <TextInput
            style={styles.inviteInput}
            placeholder="colleague@company.com"
            placeholderTextColor="#64748B"
            value={inviteEmail}
            onChangeText={setInviteEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />
          <TouchableOpacity
            style={styles.inviteButton}
            onPress={handleInvite}
            disabled={inviting}
          >
            {inviting ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.inviteButtonText}>Invite</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>

      {/* Members list */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Team Members</Text>
        {team.members.map((m) => (
          <View key={m.user_id} style={styles.memberRow}>
            <View style={styles.memberInfo}>
              <Text style={styles.memberName}>{m.name || m.email}</Text>
              {m.name && <Text style={styles.memberEmail}>{m.email}</Text>}
            </View>
            <View style={styles.memberMeta}>
              <Text style={[styles.roleBadge,
                m.role === "OWNER" && styles.roleOwner,
                m.role === "ADMIN" && styles.roleAdmin,
              ]}>{m.role}</Text>
              <Text style={styles.memberApps}>{m.apps_this_month} this mo</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Open full admin */}
      <TouchableOpacity style={styles.adminButton} onPress={openAdminDashboard}>
        <Text style={styles.adminButtonText}>Open Full Admin Dashboard</Text>
      </TouchableOpacity>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F172A", padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0F172A" },
  errorText: { color: "#EF4444", fontSize: 14 },

  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 20 },
  teamName: { color: "#F8FAFC", fontSize: 24, fontWeight: "700", flex: 1 },
  planBadge: { backgroundColor: "#3B82F6", paddingHorizontal: 12, paddingVertical: 4, borderRadius: 6 },
  planText: { color: "#FFFFFF", fontSize: 12, fontWeight: "700" },

  statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10, marginBottom: 20 },
  statCard: {
    flex: 1,
    minWidth: "45%",
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
  },
  statValue: { color: "#F8FAFC", fontSize: 22, fontWeight: "700" },
  statLabel: { color: "#94A3B8", fontSize: 11, marginTop: 2 },

  section: { backgroundColor: "#1E293B", borderRadius: 12, padding: 16, marginBottom: 16 },
  sectionTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600", marginBottom: 12 },

  inviteRow: { flexDirection: "row", gap: 8 },
  inviteInput: {
    flex: 1,
    backgroundColor: "#0F172A",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#334155",
    color: "#F8FAFC",
    fontSize: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  inviteButton: {
    backgroundColor: "#3B82F6",
    borderRadius: 8,
    paddingHorizontal: 16,
    justifyContent: "center",
    alignItems: "center",
  },
  inviteButtonText: { color: "#FFFFFF", fontSize: 14, fontWeight: "600" },

  memberRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#334155",
  },
  memberInfo: { flex: 1 },
  memberName: { color: "#F8FAFC", fontSize: 14, fontWeight: "500" },
  memberEmail: { color: "#94A3B8", fontSize: 12 },
  memberMeta: { alignItems: "flex-end" },
  roleBadge: {
    color: "#94A3B8",
    fontSize: 10,
    fontWeight: "600",
    backgroundColor: "#334155",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    overflow: "hidden",
    marginBottom: 2,
  },
  roleOwner: { backgroundColor: "#3B82F620", color: "#3B82F6" },
  roleAdmin: { backgroundColor: "#F59E0B20", color: "#F59E0B" },
  memberApps: { color: "#64748B", fontSize: 11 },

  adminButton: {
    backgroundColor: "#334155",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginBottom: 8,
  },
  adminButtonText: { color: "#CBD5E1", fontSize: 14, fontWeight: "600" },
});

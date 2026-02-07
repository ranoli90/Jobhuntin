/**
 * EnterpriseAdminScreen — mobile view for ENTERPRISE plan owners.
 *
 * Extends TeamOwnerScreen with enterprise-specific features:
 * SSO status, SLA info, audit log preview, priority queue stats.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Linking,
} from "react-native";
import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../lib/config";

interface TeamOverview {
  tenant: {
    id: string; name: string; team_name: string | null;
    plan: string; seat_count: number; max_seats: number;
  };
  members: Array<{ user_id: string; role: string; email: string; name: string | null; apps_this_month: number }>;
  member_count: number;
  pending_invites: number;
  total_apps_this_month: number;
  total_apps_all_time: number;
}

interface AlertItem {
  name: string;
  level: string;
  message: string;
  value: unknown;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}`, "Content-Type": "application/json" }
    : { "Content-Type": "application/json" };
}

export default function EnterpriseAdminScreen() {
  const [team, setTeam] = useState<TeamOverview | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const h = await getAuthHeaders();
      const [teamResp, dashResp] = await Promise.all([
        fetch(`${API_BASE_URL}/billing/team`, { headers: h }),
        fetch(`${API_BASE_URL}/admin/m4-dashboard`, { headers: h }),
      ]);
      if (teamResp.ok) setTeam(await teamResp.json());
      if (dashResp.ok) {
        const d = await dashResp.json();
        setAlerts(d.alerts || []);
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return <View style={s.center}><ActivityIndicator size="large" color="#8B5CF6" /></View>;
  }

  if (!team) {
    return <View style={s.center}><Text style={s.errorText}>Could not load enterprise data.</Text></View>;
  }

  const t = team.tenant;

  return (
    <ScrollView style={s.container}>
      {/* Header */}
      <View style={s.header}>
        <Text style={s.teamName}>{t.team_name || t.name}</Text>
        <View style={s.planBadge}>
          <Text style={s.planText}>ENTERPRISE</Text>
        </View>
      </View>

      {/* Active alerts */}
      {alerts.length > 0 && (
        <View style={s.alertsSection}>
          {alerts.map((a, i) => (
            <View key={i} style={[s.alertCard,
              a.level === "critical" && s.alertCritical,
              a.level === "warning" && s.alertWarning,
            ]}>
              <Text style={s.alertTitle}>{a.name.replace(/_/g, " ").toUpperCase()}</Text>
              <Text style={s.alertMessage}>{a.message}</Text>
            </View>
          ))}
        </View>
      )}

      {/* KPI Grid */}
      <View style={s.statsGrid}>
        {[
          { label: "Members", value: team.member_count },
          { label: "Seats", value: `${t.seat_count}/${t.max_seats}` },
          { label: "Apps/Month", value: team.total_apps_this_month },
          { label: "All Time", value: team.total_apps_all_time },
        ].map((stat) => (
          <View key={stat.label} style={s.statCard}>
            <Text style={s.statValue}>{stat.value}</Text>
            <Text style={s.statLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      {/* Enterprise features */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>Enterprise Features</Text>
        {[
          { label: "SSO", status: "Active", color: "#10B981" },
          { label: "SLA Tier", status: "Standard (99.9%)", color: "#8B5CF6" },
          { label: "Priority Queue", status: "Enabled", color: "#10B981" },
          { label: "Audit Log", status: "SOC 2 Ready", color: "#8B5CF6" },
          { label: "Data Export", status: "Available", color: "#10B981" },
          { label: "Bulk Operations", status: "Enabled", color: "#10B981" },
        ].map((f) => (
          <View key={f.label} style={s.featureRow}>
            <Text style={s.featureLabel}>{f.label}</Text>
            <Text style={[s.featureStatus, { color: f.color }]}>{f.status}</Text>
          </View>
        ))}
      </View>

      {/* Top members */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>Top Members This Month</Text>
        {team.members
          .sort((a, b) => b.apps_this_month - a.apps_this_month)
          .slice(0, 5)
          .map((m) => (
            <View key={m.user_id} style={s.memberRow}>
              <View style={{ flex: 1 }}>
                <Text style={s.memberName}>{m.name || m.email}</Text>
                <Text style={s.memberRole}>{m.role}</Text>
              </View>
              <Text style={s.memberApps}>{m.apps_this_month} apps</Text>
            </View>
          ))}
      </View>

      {/* Actions */}
      <TouchableOpacity style={s.primaryButton} onPress={() => Linking.openURL("https://admin.sorce.app/enterprise")}>
        <Text style={s.primaryButtonText}>Open Enterprise Console</Text>
      </TouchableOpacity>

      <TouchableOpacity style={s.secondaryButton} onPress={() => Linking.openURL("https://admin.sorce.app/audit-log")}>
        <Text style={s.secondaryButtonText}>View Audit Log</Text>
      </TouchableOpacity>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F172A", padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0F172A" },
  errorText: { color: "#EF4444", fontSize: 14 },

  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 16 },
  teamName: { color: "#F8FAFC", fontSize: 22, fontWeight: "700", flex: 1 },
  planBadge: { backgroundColor: "#8B5CF6", paddingHorizontal: 12, paddingVertical: 4, borderRadius: 6 },
  planText: { color: "#FFFFFF", fontSize: 11, fontWeight: "800", letterSpacing: 0.5 },

  alertsSection: { marginBottom: 16, gap: 8 },
  alertCard: { borderRadius: 10, padding: 12, borderLeftWidth: 4, borderLeftColor: "#94A3B8", backgroundColor: "#1E293B" },
  alertCritical: { borderLeftColor: "#EF4444", backgroundColor: "#7F1D1D20" },
  alertWarning: { borderLeftColor: "#F59E0B", backgroundColor: "#78350F20" },
  alertTitle: { color: "#F8FAFC", fontSize: 11, fontWeight: "700", letterSpacing: 0.5, marginBottom: 2 },
  alertMessage: { color: "#CBD5E1", fontSize: 13 },

  statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10, marginBottom: 16 },
  statCard: { flex: 1, minWidth: "45%", backgroundColor: "#1E293B", borderRadius: 12, padding: 14, alignItems: "center" },
  statValue: { color: "#F8FAFC", fontSize: 22, fontWeight: "700" },
  statLabel: { color: "#94A3B8", fontSize: 11, marginTop: 2 },

  section: { backgroundColor: "#1E293B", borderRadius: 12, padding: 16, marginBottom: 16 },
  sectionTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600", marginBottom: 12 },

  featureRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: "#334155" },
  featureLabel: { color: "#CBD5E1", fontSize: 14 },
  featureStatus: { fontSize: 13, fontWeight: "600" },

  memberRow: { flexDirection: "row", alignItems: "center", paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: "#334155" },
  memberName: { color: "#F8FAFC", fontSize: 14, fontWeight: "500" },
  memberRole: { color: "#94A3B8", fontSize: 11 },
  memberApps: { color: "#8B5CF6", fontSize: 14, fontWeight: "600" },

  primaryButton: { backgroundColor: "#8B5CF6", borderRadius: 12, padding: 16, alignItems: "center", marginBottom: 10 },
  primaryButtonText: { color: "#FFFFFF", fontSize: 15, fontWeight: "700" },
  secondaryButton: { backgroundColor: "#334155", borderRadius: 12, padding: 16, alignItems: "center", marginBottom: 8 },
  secondaryButtonText: { color: "#CBD5E1", fontSize: 14, fontWeight: "600" },
});

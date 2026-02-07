/**
 * DashboardHome v3 — dashboard-first redesign.
 *
 * Shows at-a-glance: active applications, needs input count,
 * recent activity feed, quick actions, and marketplace picks.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  ActivityIndicator, RefreshControl,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { supabase } from "../../lib/supabase";
import { API_BASE_URL } from "../../lib/config";
import { track } from "../../lib/analytics";

interface DashboardData {
  active_count: number;
  hold_count: number;
  completed_today: number;
  completed_week: number;
  total_all_time: number;
  recent: Array<{ id: string; job_title: string; status: string; updated_at: string }>;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : {};
}

export default function DashboardHome() {
  const nav = useNavigation<any>();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const h = await getAuthHeaders();
      const r = await fetch(`${API_BASE_URL}/me/dashboard`, { headers: h });
      if (r.ok) setData(await r.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); track("dashboard_viewed"); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  if (loading) return <View style={s.center}><ActivityIndicator size="large" color="#6366F1" /></View>;

  const d = data || { active_count: 0, hold_count: 0, completed_today: 0, completed_week: 0, total_all_time: 0, recent: [] };

  return (
    <ScrollView style={s.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#6366F1" />}>
      {/* Hero card */}
      <View style={s.heroCard}>
        <Text style={s.heroTitle}>Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"}</Text>
        <View style={s.heroStats}>
          <View style={s.heroStatItem}>
            <Text style={s.heroStatValue}>{d.active_count}</Text>
            <Text style={s.heroStatLabel}>In Progress</Text>
          </View>
          <View style={[s.heroStatItem, d.hold_count > 0 && s.heroStatAlert]}>
            <Text style={[s.heroStatValue, d.hold_count > 0 && { color: "#F59E0B" }]}>{d.hold_count}</Text>
            <Text style={s.heroStatLabel}>Need Input</Text>
          </View>
          <View style={s.heroStatItem}>
            <Text style={s.heroStatValue}>{d.completed_today}</Text>
            <Text style={s.heroStatLabel}>Today</Text>
          </View>
        </View>
      </View>

      {/* Alert banner */}
      {d.hold_count > 0 && (
        <TouchableOpacity style={s.alertBanner} onPress={() => nav.navigate("Applications", { filter: "REQUIRES_INPUT" })}>
          <Text style={s.alertText}>⚡ {d.hold_count} application{d.hold_count > 1 ? "s" : ""} need your input</Text>
          <Text style={s.alertArrow}>→</Text>
        </TouchableOpacity>
      )}

      {/* Quick actions */}
      <View style={s.quickActions}>
        {[
          { label: "Browse Jobs", icon: "🔍", screen: "Jobs" },
          { label: "My Apps", icon: "📋", screen: "Applications" },
          { label: "Marketplace", icon: "🛒", screen: "Marketplace" },
          { label: "Profile", icon: "👤", screen: "Profile" },
        ].map((a) => (
          <TouchableOpacity key={a.label} style={s.quickAction} onPress={() => nav.navigate(a.screen)}>
            <Text style={s.quickActionIcon}>{a.icon}</Text>
            <Text style={s.quickActionLabel}>{a.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Weekly summary */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>This Week</Text>
        <View style={s.weekGrid}>
          <View style={s.weekStat}>
            <Text style={s.weekValue}>{d.completed_week}</Text>
            <Text style={s.weekLabel}>Completed</Text>
          </View>
          <View style={s.weekStat}>
            <Text style={s.weekValue}>{d.total_all_time}</Text>
            <Text style={s.weekLabel}>All Time</Text>
          </View>
        </View>
      </View>

      {/* Recent activity */}
      {d.recent.length > 0 && (
        <View style={s.section}>
          <Text style={s.sectionTitle}>Recent Activity</Text>
          {d.recent.slice(0, 5).map((item) => (
            <TouchableOpacity key={item.id} style={s.activityRow}
              onPress={() => nav.navigate("ApplicationDetail", { id: item.id })}>
              <View style={{ flex: 1 }}>
                <Text style={s.activityTitle} numberOfLines={1}>{item.job_title}</Text>
                <Text style={s.activityTime}>{new Date(item.updated_at).toLocaleDateString()}</Text>
              </View>
              <View style={[s.statusBadge, statusStyle(item.status)]}>
                <Text style={s.statusText}>{item.status}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

function statusStyle(status: string) {
  switch (status) {
    case "APPLIED": case "COMPLETED": case "SUBMITTED": return { backgroundColor: "#10B98120" };
    case "PROCESSING": return { backgroundColor: "#6366F120" };
    case "REQUIRES_INPUT": return { backgroundColor: "#F59E0B20" };
    case "FAILED": return { backgroundColor: "#EF444420" };
    default: return { backgroundColor: "#64748B20" };
  }
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F172A" },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0F172A" },

  heroCard: { margin: 16, backgroundColor: "#1E293B", borderRadius: 16, padding: 20 },
  heroTitle: { color: "#F8FAFC", fontSize: 24, fontWeight: "700", marginBottom: 16 },
  heroStats: { flexDirection: "row", justifyContent: "space-around" },
  heroStatItem: { alignItems: "center", paddingVertical: 8, paddingHorizontal: 16, borderRadius: 12 },
  heroStatAlert: { backgroundColor: "#F59E0B10", borderWidth: 1, borderColor: "#F59E0B30" },
  heroStatValue: { color: "#F8FAFC", fontSize: 28, fontWeight: "800" },
  heroStatLabel: { color: "#94A3B8", fontSize: 11, marginTop: 2 },

  alertBanner: { marginHorizontal: 16, marginBottom: 12, backgroundColor: "#F59E0B15", borderWidth: 1, borderColor: "#F59E0B30", borderRadius: 12, padding: 14, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  alertText: { color: "#F59E0B", fontSize: 14, fontWeight: "600", flex: 1 },
  alertArrow: { color: "#F59E0B", fontSize: 18, fontWeight: "700" },

  quickActions: { flexDirection: "row", marginHorizontal: 16, marginBottom: 16, gap: 10 },
  quickAction: { flex: 1, backgroundColor: "#1E293B", borderRadius: 12, paddingVertical: 14, alignItems: "center" },
  quickActionIcon: { fontSize: 20, marginBottom: 4 },
  quickActionLabel: { color: "#CBD5E1", fontSize: 11, fontWeight: "500" },

  section: { marginHorizontal: 16, marginBottom: 16, backgroundColor: "#1E293B", borderRadius: 16, padding: 16 },
  sectionTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600", marginBottom: 12 },

  weekGrid: { flexDirection: "row", gap: 12 },
  weekStat: { flex: 1, backgroundColor: "#334155", borderRadius: 10, padding: 14, alignItems: "center" },
  weekValue: { color: "#F8FAFC", fontSize: 22, fontWeight: "700" },
  weekLabel: { color: "#94A3B8", fontSize: 11, marginTop: 2 },

  activityRow: { flexDirection: "row", alignItems: "center", paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: "#334155" },
  activityTitle: { color: "#F8FAFC", fontSize: 14, fontWeight: "500" },
  activityTime: { color: "#64748B", fontSize: 11, marginTop: 2 },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  statusText: { fontSize: 10, fontWeight: "700", color: "#CBD5E1" },
});

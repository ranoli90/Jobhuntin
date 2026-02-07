/**
 * M1 Founder Dashboard — shows key beta metrics at a glance.
 *
 * Fetches from GET /admin/m1-dashboard and renders:
 *   - M1 target progress bars (MAU, apps processed, success rate)
 *   - MRR / PRO subscribers
 *   - Daily application chart (last 14 days)
 *   - Top failure reasons
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../lib/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface M1Targets {
  mau_target: number;
  mau_current: number;
  mau_pct: number;
  apps_target: number;
  apps_current: number;
  apps_pct: number;
  success_rate_target: number;
  success_rate_current: number;
  pro_subscribers: number;
  mrr: number;
}

interface ActiveUsers {
  mau: number;
  wau: number;
  dau: number;
}

interface AgentSuccess {
  total_7d: number;
  success_7d: number;
  partial_7d: number;
  failure_7d: number;
  success_rate_7d: number;
  total_30d: number;
  success_30d: number;
  partial_30d: number;
  failure_30d: number;
  success_rate_30d: number;
}

interface DailyStat {
  day: string;
  total_created: number;
  total_succeeded: number;
  total_failed: number;
  total_on_hold: number;
  unique_users: number;
}

interface FailureReason {
  reason: string;
  count: number;
}

interface DashboardData {
  active_users: ActiveUsers;
  agent_success: AgentSuccess;
  total_applications: number;
  daily_stats: DailyStat[];
  m1_targets: M1Targets;
  top_failures: FailureReason[];
  live_counts: { total_users: number; signups_today: number };
}

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

async function fetchDashboard(): Promise<DashboardData> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const token = session?.access_token;

  const resp = await fetch(`${API_BASE_URL}/admin/m1-dashboard`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!resp.ok) {
    throw new Error(`Dashboard fetch failed: ${resp.status}`);
  }
  return resp.json();
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ProgressBar({
  label,
  current,
  target,
  unit = "",
  color = "#3B82F6",
}: {
  label: string;
  current: number;
  target: number;
  unit?: string;
  color?: string;
}) {
  const pct = Math.min(100, Math.round((current / Math.max(target, 1)) * 100));
  return (
    <View style={styles.progressContainer}>
      <View style={styles.progressHeader}>
        <Text style={styles.progressLabel}>{label}</Text>
        <Text style={styles.progressValue}>
          {current.toLocaleString()}{unit} / {target.toLocaleString()}{unit}
        </Text>
      </View>
      <View style={styles.progressTrack}>
        <View
          style={[
            styles.progressFill,
            { width: `${pct}%`, backgroundColor: pct >= 100 ? "#10B981" : color },
          ]}
        />
      </View>
      <Text style={styles.progressPct}>{pct}%</Text>
    </View>
  );
}

function MetricCard({
  label,
  value,
  subtitle,
}: {
  label: string;
  value: string | number;
  subtitle?: string;
}) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
      {subtitle ? <Text style={styles.metricSubtitle}>{subtitle}</Text> : null}
    </View>
  );
}

function DailyChart({ stats }: { stats: DailyStat[] }) {
  if (stats.length === 0) return null;
  const maxVal = Math.max(...stats.map((s) => s.total_created), 1);

  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Daily Applications (14d)</Text>
      <View style={styles.chartContainer}>
        {stats
          .slice()
          .reverse()
          .map((stat) => {
            const height = Math.max(4, (stat.total_created / maxVal) * 80);
            const dayLabel = new Date(stat.day).toLocaleDateString("en", {
              month: "short",
              day: "numeric",
            });
            return (
              <View key={stat.day} style={styles.chartBar}>
                <Text style={styles.chartBarValue}>{stat.total_created}</Text>
                <View
                  style={[
                    styles.chartBarFill,
                    { height, backgroundColor: "#3B82F6" },
                  ]}
                />
                <Text style={styles.chartBarLabel}>{dayLabel}</Text>
              </View>
            );
          })}
      </View>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Main Screen
// ---------------------------------------------------------------------------

export default function DashboardScreen() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const d = await fetchDashboard();
      setData(d);
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    load();
  }, [load]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error || "No data"}</Text>
      </View>
    );
  }

  const { m1_targets: t, active_users: au, agent_success: as_, top_failures } = data;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <Text style={styles.title}>M1 Dashboard</Text>
      <Text style={styles.subtitle}>Closed Beta Progress</Text>

      {/* M1 Target Progress */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>M1 Targets</Text>
        <ProgressBar
          label="Monthly Active Users"
          current={t.mau_current}
          target={t.mau_target}
          color="#8B5CF6"
        />
        <ProgressBar
          label="Applications Processed"
          current={t.apps_current}
          target={t.apps_target}
          color="#3B82F6"
        />
        <ProgressBar
          label="Agent Success Rate"
          current={t.success_rate_current}
          target={t.success_rate_target}
          unit="%"
          color="#10B981"
        />
      </View>

      {/* Key Metrics Row */}
      <View style={styles.metricsRow}>
        <MetricCard label="MRR" value={`$${t.mrr.toLocaleString()}`} />
        <MetricCard label="PRO Subs" value={t.pro_subscribers} />
        <MetricCard label="DAU" value={au.dau} subtitle={`WAU: ${au.wau}`} />
        <MetricCard
          label="Signups Today"
          value={data.live_counts.signups_today}
        />
      </View>

      {/* Agent Performance */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Agent Performance</Text>
        <View style={styles.metricsRow}>
          <MetricCard
            label="7d Success"
            value={`${as_.success_rate_7d ?? 0}%`}
            subtitle={`${as_.success_7d}/${as_.total_7d}`}
          />
          <MetricCard
            label="30d Success"
            value={`${as_.success_rate_30d ?? 0}%`}
            subtitle={`${as_.success_30d}/${as_.total_30d}`}
          />
          <MetricCard label="30d Failed" value={as_.failure_30d} />
          <MetricCard label="30d Partial" value={as_.partial_30d} />
        </View>
      </View>

      {/* Daily Chart */}
      <DailyChart stats={data.daily_stats} />

      {/* Top Failures */}
      {top_failures.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Top Failures (7d)</Text>
          {top_failures.map((f, i) => (
            <View key={i} style={styles.failureRow}>
              <Text style={styles.failureCount}>{f.count}x</Text>
              <Text style={styles.failureReason} numberOfLines={2}>
                {f.reason}
              </Text>
            </View>
          ))}
        </View>
      )}

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
  loadingText: { color: "#94A3B8", marginTop: 12, fontSize: 14 },
  errorText: { color: "#EF4444", fontSize: 14 },

  title: { color: "#F8FAFC", fontSize: 28, fontWeight: "700", marginTop: 8 },
  subtitle: { color: "#94A3B8", fontSize: 14, marginBottom: 20 },

  section: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600", marginBottom: 12 },

  // Progress bars
  progressContainer: { marginBottom: 14 },
  progressHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  progressLabel: { color: "#CBD5E1", fontSize: 13 },
  progressValue: { color: "#94A3B8", fontSize: 12 },
  progressTrack: { height: 8, backgroundColor: "#334155", borderRadius: 4, overflow: "hidden" },
  progressFill: { height: 8, borderRadius: 4 },
  progressPct: { color: "#64748B", fontSize: 11, marginTop: 2, textAlign: "right" },

  // Metric cards
  metricsRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 16 },
  metricCard: {
    flex: 1,
    minWidth: 70,
    backgroundColor: "#1E293B",
    borderRadius: 10,
    padding: 12,
    alignItems: "center",
  },
  metricValue: { color: "#F8FAFC", fontSize: 22, fontWeight: "700" },
  metricLabel: { color: "#94A3B8", fontSize: 11, marginTop: 4 },
  metricSubtitle: { color: "#64748B", fontSize: 10, marginTop: 2 },

  // Chart
  chartContainer: { flexDirection: "row", alignItems: "flex-end", justifyContent: "space-between", height: 110 },
  chartBar: { alignItems: "center", flex: 1 },
  chartBarValue: { color: "#94A3B8", fontSize: 9, marginBottom: 2 },
  chartBarFill: { width: 12, borderRadius: 3 },
  chartBarLabel: { color: "#64748B", fontSize: 8, marginTop: 4, textAlign: "center" },

  // Failures
  failureRow: { flexDirection: "row", alignItems: "center", paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: "#334155" },
  failureCount: { color: "#EF4444", fontSize: 14, fontWeight: "600", width: 36 },
  failureReason: { color: "#CBD5E1", fontSize: 12, flex: 1 },
});

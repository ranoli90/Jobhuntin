/**
 * Upgrade Screen — shows quota usage + PRO upgrade CTA.
 *
 * Displays current plan usage, PRO benefits, and handles
 * the Stripe Checkout flow via in-app browser.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Linking,
} from "react-native";
import {
  getUsage,
  getBillingStatus,
  createCheckout,
  createPortalSession,
  type UsageInfo,
  type BillingStatus,
} from "../api/billing";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function UpgradeScreen() {
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [u, b] = await Promise.all([getUsage(), getBillingStatus()]);
      setUsage(u);
      setBilling(b);
    } catch (err) {
      console.error("Failed to load billing info:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleUpgrade = async () => {
    setUpgrading(true);
    try {
      const { checkout_url } = await createCheckout();
      await Linking.openURL(checkout_url);
    } catch (err) {
      Alert.alert("Error", "Could not start checkout. Please try again.");
      console.error("Checkout error:", err);
    } finally {
      setUpgrading(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const { portal_url } = await createPortalSession();
      await Linking.openURL(portal_url);
    } catch (err) {
      Alert.alert("Error", "Could not open billing portal.");
      console.error("Portal error:", err);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  const isPro = usage?.plan === "PRO" || usage?.plan === "ENTERPRISE";
  const pctUsed = usage?.percentage_used ?? 0;
  const barColor = pctUsed >= 90 ? "#EF4444" : pctUsed >= 70 ? "#F59E0B" : "#3B82F6";

  return (
    <ScrollView style={styles.container}>
      {/* Current Plan */}
      <View style={styles.planCard}>
        <Text style={styles.planBadge}>{usage?.plan ?? "FREE"}</Text>
        <Text style={styles.planTitle}>
          {isPro ? "You're on Sorce PRO" : "You're on the Free plan"}
        </Text>
      </View>

      {/* Usage */}
      {usage && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>This Month's Usage</Text>

          <View style={styles.usageRow}>
            <Text style={styles.usageLabel}>Applications</Text>
            <Text style={styles.usageValue}>
              {usage.monthly_used} / {usage.monthly_limit}
            </Text>
          </View>
          <View style={styles.progressTrack}>
            <View
              style={[
                styles.progressFill,
                {
                  width: `${Math.min(100, pctUsed)}%`,
                  backgroundColor: barColor,
                },
              ]}
            />
          </View>
          <Text style={styles.usageRemaining}>
            {usage.monthly_remaining} remaining
          </Text>

          <View style={[styles.usageRow, { marginTop: 12 }]}>
            <Text style={styles.usageLabel}>Concurrent Processing</Text>
            <Text style={styles.usageValue}>
              {usage.concurrent_used} / {usage.concurrent_limit}
            </Text>
          </View>
        </View>
      )}

      {/* PRO Benefits (only show on FREE) */}
      {!isPro && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Upgrade to PRO — $29/month</Text>

          {[
            ["200 applications/month", "vs 25 on Free"],
            ["10 concurrent processing", "vs 2 on Free"],
            ["Priority processing queue", "Your apps go first"],
            ["Application analytics", "Track your success rate"],
            ["Email digest", "Weekly application summary"],
          ].map(([title, sub], i) => (
            <View key={i} style={styles.benefitRow}>
              <Text style={styles.benefitCheck}>✓</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.benefitTitle}>{title}</Text>
                <Text style={styles.benefitSub}>{sub}</Text>
              </View>
            </View>
          ))}

          <TouchableOpacity
            style={styles.upgradeButton}
            onPress={handleUpgrade}
            disabled={upgrading}
          >
            {upgrading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.upgradeButtonText}>Upgrade to PRO</Text>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Manage Subscription (only show on PRO) */}
      {isPro && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Manage Subscription</Text>
          {billing?.current_period_end && (
            <Text style={styles.periodText}>
              Current period ends:{" "}
              {new Date(billing.current_period_end).toLocaleDateString()}
            </Text>
          )}
          <TouchableOpacity
            style={styles.manageButton}
            onPress={handleManageSubscription}
          >
            <Text style={styles.manageButtonText}>
              Manage Billing in Stripe
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Quota warning banner */}
      {!isPro && pctUsed >= 80 && (
        <View style={styles.warningBanner}>
          <Text style={styles.warningText}>
            ⚠️ You've used {Math.round(pctUsed)}% of your free applications this
            month. Upgrade to PRO for 200 apps/month.
          </Text>
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
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#0F172A",
  },

  // Plan card
  planCard: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 20,
    alignItems: "center",
    marginBottom: 16,
  },
  planBadge: {
    color: "#3B82F6",
    fontSize: 13,
    fontWeight: "700",
    backgroundColor: "#1E3A5F",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 20,
    overflow: "hidden",
    marginBottom: 8,
  },
  planTitle: { color: "#F8FAFC", fontSize: 20, fontWeight: "600" },

  // Section
  section: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    color: "#E2E8F0",
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 12,
  },

  // Usage
  usageRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  usageLabel: { color: "#CBD5E1", fontSize: 14 },
  usageValue: { color: "#F8FAFC", fontSize: 14, fontWeight: "600" },
  usageRemaining: { color: "#64748B", fontSize: 12, marginTop: 4 },
  progressTrack: {
    height: 8,
    backgroundColor: "#334155",
    borderRadius: 4,
    overflow: "hidden",
  },
  progressFill: { height: 8, borderRadius: 4 },

  // Benefits
  benefitRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 10,
  },
  benefitCheck: { color: "#10B981", fontSize: 16, marginRight: 10, marginTop: 1 },
  benefitTitle: { color: "#F8FAFC", fontSize: 14, fontWeight: "500" },
  benefitSub: { color: "#94A3B8", fontSize: 12 },

  // Buttons
  upgradeButton: {
    backgroundColor: "#3B82F6",
    borderRadius: 10,
    padding: 16,
    alignItems: "center",
    marginTop: 16,
  },
  upgradeButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },
  manageButton: {
    backgroundColor: "#334155",
    borderRadius: 10,
    padding: 14,
    alignItems: "center",
    marginTop: 8,
  },
  manageButtonText: { color: "#CBD5E1", fontSize: 14, fontWeight: "600" },
  periodText: { color: "#94A3B8", fontSize: 13, marginBottom: 8 },

  // Warning
  warningBanner: {
    backgroundColor: "#451A03",
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: "#F59E0B",
    marginBottom: 16,
  },
  warningText: { color: "#FCD34D", fontSize: 13 },
});

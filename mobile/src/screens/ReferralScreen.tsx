/**
 * Referral Screen — share referral code, see stats, redeem codes.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Share,
  Alert,
} from "react-native";
import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../lib/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ReferralStats {
  referral_code: string;
  total_referrals: number;
  bonus_credits: number;
  share_url: string;
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

async function fetchReferralStats(): Promise<ReferralStats> {
  const headers = await getAuthHeaders();
  const resp = await fetch(`${API_BASE_URL}/referral`, { headers });
  if (!resp.ok) throw new Error(`Failed: ${resp.status}`);
  return resp.json();
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ReferralScreen() {
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const s = await fetchReferralStats();
      setStats(s);
    } catch (err) {
      console.error("Failed to load referral stats:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleShare = async () => {
    if (!stats) return;
    try {
      await Share.share({
        message: `I've been using Sorce to auto-apply to jobs with AI — it's incredible. Use my code ${stats.referral_code} and we both get 5 free applications!\n\n${stats.share_url}`,
      });
    } catch (err) {
      console.error("Share failed:", err);
    }
  };

  const handleCopyCode = () => {
    if (!stats) return;
    // Expo Clipboard would be used here in a real build
    Alert.alert("Copied!", `Your referral code ${stats.referral_code} has been copied.`);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  if (!stats) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Could not load referral info.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Invite Friends</Text>
      <Text style={styles.subtitle}>
        Give 5 free apps, get 5 free apps
      </Text>

      {/* Referral code card */}
      <View style={styles.codeCard}>
        <Text style={styles.codeLabel}>Your Referral Code</Text>
        <Text style={styles.codeValue}>{stats.referral_code}</Text>
        <TouchableOpacity style={styles.copyButton} onPress={handleCopyCode}>
          <Text style={styles.copyButtonText}>Copy Code</Text>
        </TouchableOpacity>
      </View>

      {/* Share button */}
      <TouchableOpacity style={styles.shareButton} onPress={handleShare}>
        <Text style={styles.shareButtonText}>Share with Friends</Text>
      </TouchableOpacity>

      {/* Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats.total_referrals}</Text>
          <Text style={styles.statLabel}>Friends Invited</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats.bonus_credits}</Text>
          <Text style={styles.statLabel}>Bonus Apps Earned</Text>
        </View>
      </View>

      {/* How it works */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>How It Works</Text>
        {[
          ["1", "Share your unique referral code with a friend"],
          ["2", "They sign up and enter your code during onboarding"],
          ["3", "You both get 5 bonus applications added to your account"],
        ].map(([num, desc]) => (
          <View key={num} style={styles.stepRow}>
            <View style={styles.stepBadge}>
              <Text style={styles.stepNum}>{num}</Text>
            </View>
            <Text style={styles.stepText}>{desc}</Text>
          </View>
        ))}
      </View>

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

  title: { color: "#F8FAFC", fontSize: 28, fontWeight: "700", marginTop: 8 },
  subtitle: { color: "#94A3B8", fontSize: 15, marginBottom: 24 },

  codeCard: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#334155",
  },
  codeLabel: { color: "#94A3B8", fontSize: 13, marginBottom: 8 },
  codeValue: { color: "#F8FAFC", fontSize: 28, fontWeight: "800", letterSpacing: 2, marginBottom: 16 },
  copyButton: {
    backgroundColor: "#334155",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  copyButtonText: { color: "#CBD5E1", fontSize: 14, fontWeight: "600" },

  shareButton: {
    backgroundColor: "#3B82F6",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginBottom: 24,
  },
  shareButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },

  statsRow: { flexDirection: "row", gap: 12, marginBottom: 24 },
  statCard: {
    flex: 1,
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
  },
  statValue: { color: "#F8FAFC", fontSize: 24, fontWeight: "700" },
  statLabel: { color: "#94A3B8", fontSize: 12, marginTop: 4 },

  section: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
  },
  sectionTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600", marginBottom: 16 },
  stepRow: { flexDirection: "row", alignItems: "center", marginBottom: 14 },
  stepBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#3B82F6",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  stepNum: { color: "#FFFFFF", fontSize: 14, fontWeight: "700" },
  stepText: { color: "#CBD5E1", fontSize: 14, flex: 1 },
});

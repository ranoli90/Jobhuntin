import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from "react-native";
import { useRoute, useNavigation } from "@react-navigation/native";
import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../lib/config";
import { semanticMatch, SemanticMatchResponse } from "../api/client";

interface RouteParams {
  jobId: string;
  jobTitle?: string;
  company?: string;
}

function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
  return (
    <View style={styles.scoreBarContainer}>
      <View style={styles.scoreBarHeader}>
        <Text style={styles.scoreBarLabel}>{label}</Text>
        <Text style={styles.scoreBarValue}>{Math.round(score * 100)}%</Text>
      </View>
      <View style={styles.scoreBarTrack}>
        <View
          style={[
            styles.scoreBarFill,
            { width: `${Math.min(100, score * 100)}%`, backgroundColor: color },
          ]}
        />
      </View>
    </View>
  );
}

function SkillChip({ skill, matched }: { skill: string; matched: boolean }) {
  return (
    <View
      style={[
        styles.skillChip,
        { backgroundColor: matched ? "#10B98120" : "#EF444420" },
      ]}
    >
      <Text
        style={[
          styles.skillChipText,
          { color: matched ? "#10B981" : "#EF4444" },
        ]}
      >
        {skill}
      </Text>
    </View>
  );
}

function DealbreakerWarning({ reasons }: { reasons: string[] }) {
  if (reasons.length === 0) return null;

  return (
    <View style={styles.dealbreakerContainer}>
      <Text style={styles.dealbreakerTitle}>Dealbreaker Issues</Text>
      {reasons.map((reason, i) => (
        <View key={i} style={styles.dealbreakerItem}>
          <Text style={styles.dealbreakerBullet}>!</Text>
          <Text style={styles.dealbreakerText}>{reason}</Text>
        </View>
      ))}
    </View>
  );
}

export default function MatchResultsScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { jobId, jobTitle, company } = route.params as RouteParams;

  const [data, setData] = useState<SemanticMatchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedExplanation, setExpandedExplanation] = useState(false);

  const load = useCallback(async () => {
    if (!jobId) {
      setError("No job ID provided");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        setError("Not authenticated");
        return;
      }

      const result = await semanticMatch(session.access_token, jobId);
      setData(result);
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [jobId]);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    load();
  }, [load]);

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "#10B981";
    if (score >= 0.6) return "#F59E0B";
    return "#EF4444";
  };

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence) {
      case "high":
        return { text: "High Confidence", color: "#10B981" };
      case "medium":
        return { text: "Medium Confidence", color: "#F59E0B" };
      default:
        return { text: "Low Confidence", color: "#EF4444" };
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Analyzing job match...</Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error || "No match data available"}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={load}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const confidenceBadge = getConfidenceBadge(data.confidence);
  const scoreColor = getScoreColor(data.score);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.headerLabel}>Semantic Match Analysis</Text>
        <Text style={styles.headerTitle}>
          {jobTitle || "Match Results"}
        </Text>
        {company && <Text style={styles.headerSubtitle}>{company}</Text>}
      </View>

      <View style={styles.scoreCard}>
        <View style={styles.scoreMain}>
          <View style={[styles.scoreCircle, { borderColor: scoreColor }]}>
            <Text style={[styles.scoreMainValue, { color: scoreColor }]}>
              {Math.round(data.score * 100)}
            </Text>
            <Text style={[styles.scoreMainUnit, { color: scoreColor }]}>%</Text>
          </View>
          <View style={styles.scoreBadges}>
            <View style={[styles.confidenceBadge, { backgroundColor: confidenceBadge.color + "20" }]}>
              <Text style={[styles.confidenceBadgeText, { color: confidenceBadge.color }]}>
                {confidenceBadge.text}
              </Text>
            </View>
            <View
              style={[
                styles.dealbreakerBadge,
                { backgroundColor: data.passed_dealbreakers ? "#10B98120" : "#EF444420" },
              ]}
            >
              <Text
                style={[
                  styles.dealbreakerBadgeText,
                  { color: data.passed_dealbreakers ? "#10B981" : "#EF4444" },
                ]}
              >
                {data.passed_dealbreakers ? "Passed" : "Failed"} Dealbreakers
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.scoreBreakdown}>
          <ScoreBar
            label="Semantic Similarity"
            score={data.semantic_similarity}
            color="#8B5CF6"
          />
          <ScoreBar
            label="Skill Match"
            score={data.skill_match_ratio}
            color="#3B82F6"
          />
          <ScoreBar
            label="Experience Alignment"
            score={data.experience_alignment}
            color="#10B981"
          />
        </View>
      </View>

      <DealbreakerWarning reasons={data.dealbreaker_reasons} />

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Skill Gap Analysis</Text>

        {data.matched_skills.length > 0 && (
          <View style={styles.skillSection}>
            <Text style={styles.skillSectionTitle}>Matched Skills ({data.matched_skills.length})</Text>
            <View style={styles.skillChipsContainer}>
              {data.matched_skills.map((skill, i) => (
                <SkillChip key={i} skill={skill} matched={true} />
              ))}
            </View>
          </View>
        )}

        {data.missing_skills.length > 0 && (
          <View style={styles.skillSection}>
            <Text style={styles.skillSectionTitle}>Missing Skills ({data.missing_skills.length})</Text>
            <View style={styles.skillChipsContainer}>
              {data.missing_skills.map((skill, i) => (
                <SkillChip key={i} skill={skill} matched={false} />
              ))}
            </View>
          </View>
        )}
      </View>

      <TouchableOpacity
        style={styles.section}
        onPress={() => setExpandedExplanation(!expandedExplanation)}
      >
        <View style={styles.explanationHeader}>
          <Text style={styles.sectionTitle}>Match Explanation</Text>
          <Text style={styles.expandIcon}>{expandedExplanation ? "—" : "+"}</Text>
        </View>
        {expandedExplanation && (
          <View style={styles.explanationContent}>
            <Text style={styles.explanationText}>{data.reasoning}</Text>
          </View>
        )}
      </TouchableOpacity>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F172A", padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0F172A" },
  loadingText: { color: "#94A3B8", marginTop: 12, fontSize: 14 },
  errorText: { color: "#EF4444", fontSize: 14, textAlign: "center", marginBottom: 16 },

  header: { marginBottom: 20 },
  headerLabel: { color: "#64748B", fontSize: 12, textTransform: "uppercase", letterSpacing: 1 },
  headerTitle: { color: "#F8FAFC", fontSize: 24, fontWeight: "700", marginTop: 4 },
  headerSubtitle: { color: "#94A3B8", fontSize: 14, marginTop: 4 },

  scoreCard: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  scoreMain: { alignItems: "center", marginBottom: 20 },
  scoreCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 6,
    justifyContent: "center",
    alignItems: "center",
    flexDirection: "row",
  },
  scoreMainValue: { fontSize: 48, fontWeight: "700" },
  scoreMainUnit: { fontSize: 24, fontWeight: "600" },
  scoreBadges: { flexDirection: "row", gap: 8, marginTop: 12 },
  confidenceBadge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20 },
  confidenceBadgeText: { fontSize: 12, fontWeight: "600" },
  dealbreakerBadge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20 },
  dealbreakerBadgeText: { fontSize: 12, fontWeight: "600" },

  scoreBreakdown: { gap: 12 },
  scoreBarContainer: {},
  scoreBarHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  scoreBarLabel: { color: "#CBD5E1", fontSize: 13 },
  scoreBarValue: { color: "#94A3B8", fontSize: 13, fontWeight: "600" },
  scoreBarTrack: { height: 6, backgroundColor: "#334155", borderRadius: 3, overflow: "hidden" },
  scoreBarFill: { height: 6, borderRadius: 3 },

  dealbreakerContainer: {
    backgroundColor: "#EF444410",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#EF444430",
  },
  dealbreakerTitle: { color: "#EF4444", fontSize: 14, fontWeight: "600", marginBottom: 8 },
  dealbreakerItem: { flexDirection: "row", alignItems: "flex-start", marginBottom: 4 },
  dealbreakerBullet: { color: "#EF4444", fontSize: 14, fontWeight: "700", marginRight: 8 },
  dealbreakerText: { color: "#FCA5A5", fontSize: 13, flex: 1 },

  section: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600", marginBottom: 12 },

  skillSection: { marginBottom: 12 },
  skillSectionTitle: { color: "#94A3B8", fontSize: 12, marginBottom: 8 },
  skillChipsContainer: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  skillChip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  skillChipText: { fontSize: 12, fontWeight: "500" },

  explanationHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  expandIcon: { color: "#64748B", fontSize: 20 },
  explanationContent: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#334155",
  },
  explanationText: { color: "#CBD5E1", fontSize: 14, lineHeight: 22 },

  retryButton: {
    backgroundColor: "#3B82F6",
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: { color: "#FFFFFF", fontSize: 14, fontWeight: "600" },
});

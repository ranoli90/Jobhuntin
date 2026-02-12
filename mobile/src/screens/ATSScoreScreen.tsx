import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { supabase } from "../lib/supabase";
import { atsScore, ATSScoreResponse } from "../api/client";

const ATS_PLATFORMS = [
  "Greenhouse", "Lever", "Workday", "iCIMS", "Taleo",
  "BrassRing", "Jobvite", "SmartRecruiters", "Recruitee",
  "BambooHR", "Ashby", "Hired",
];

const ATS_METRICS = [
  { key: "keyword_match", label: "Keyword Match" },
  { key: "skills_relevance", label: "Skills Relevance" },
  { key: "experience_alignment", label: "Experience Alignment" },
  { key: "quantifiable_achievements", label: "Quantifiable Achievements" },
  { key: "action_verbs", label: "Action Verbs" },
  { key: "format_score", label: "Format Score" },
  { key: "section_completeness", label: "Section Completeness" },
  { key: "contact_info", label: "Contact Info" },
  { key: "summary_quality", label: "Summary Quality" },
  { key: "education_relevance", label: "Education Relevance" },
  { key: "certification_match", label: "Certifications" },
  { key: "readability_score", label: "Readability" },
  { key: "length_score", label: "Length Score" },
  { key: "ats_compatibility", label: "ATS Compatibility" },
  { key: "spelling_grammar", label: "Spelling & Grammar" },
  { key: "consistency", label: "Consistency" },
  { key: "dates_format", label: "Date Format" },
  { key: "bullet_points", label: "Bullet Points" },
  { key: "file_format", label: "File Format" },
  { key: "personalization", label: "Personalization" },
  { key: "industry_keywords", label: "Industry Keywords" },
  { key: "soft_skills", label: "Soft Skills" },
  { key: "technical_skills", label: "Technical Skills" },
];

function MetricBar({ label, value }: { label: string; value: number }) {
  const getColor = (v: number) => {
    if (v >= 0.7) return "#10B981";
    if (v >= 0.5) return "#F59E0B";
    return "#EF4444";
  };

  return (
    <View style={styles.metricBar}>
      <View style={styles.metricBarHeader}>
        <Text style={styles.metricBarLabel} numberOfLines={1}>{label}</Text>
        <Text style={[styles.metricBarValue, { color: getColor(value) }]}>
          {Math.round(value * 100)}%
        </Text>
      </View>
      <View style={styles.metricBarTrack}>
        <View
          style={[
            styles.metricBarFill,
            { width: `${Math.min(100, value * 100)}%`, backgroundColor: getColor(value) },
          ]}
        />
      </View>
    </View>
  );
}

function RecommendationItem({ text, index }: { text: string; index: number }) {
  return (
    <View style={styles.recommendationItem}>
      <View style={styles.recommendationNumber}>
        <Text style={styles.recommendationNumberText}>{index + 1}</Text>
      </View>
      <Text style={styles.recommendationText}>{text}</Text>
    </View>
  );
}

export default function ATSScoreScreen() {
  const navigation = useNavigation();

  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [data, setData] = useState<ATSScoreResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detectedPlatform, setDetectedPlatform] = useState<string | null>(null);

  const detectPlatform = (text: string): string | null => {
    const lower = text.toLowerCase();
    for (const platform of ATS_PLATFORMS) {
      if (lower.includes(platform.toLowerCase())) {
        return platform;
      }
    }
    return null;
  };

  const handleScore = useCallback(async () => {
    if (!resumeText.trim()) {
      setError("Please enter your resume text");
      return;
    }

    if (!jobDescription.trim()) {
      setError("Please enter the job description");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setDetectedPlatform(detectPlatform(jobDescription));

      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        setError("Not authenticated");
        return;
      }

      const result = await atsScore(session.access_token, resumeText, jobDescription);
      setData(result);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [resumeText, jobDescription]);

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return "#10B981";
    if (score >= 0.5) return "#F59E0B";
    return "#EF4444";
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backButton}>Back</Text>
        </TouchableOpacity>
        <View>
          <Text style={styles.headerLabel}>AI Tools</Text>
          <Text style={styles.headerTitle}>ATS Score Dashboard</Text>
        </View>
      </View>

      <View style={styles.inputSection}>
        <Text style={styles.inputLabel}>Your Resume</Text>
        <TextInput
          style={[styles.textArea, styles.textAreaResume]}
          placeholder="Paste your resume text here..."
          placeholderTextColor="#64748B"
          value={resumeText}
          onChangeText={setResumeText}
          multiline
          numberOfLines={8}
          textAlignVertical="top"
        />
      </View>

      <View style={styles.inputSection}>
        <Text style={styles.inputLabel}>Job Description</Text>
        <TextInput
          style={[styles.textArea, styles.textAreaJob]}
          placeholder="Paste the job description here..."
          placeholderTextColor="#64748B"
          value={jobDescription}
          onChangeText={setJobDescription}
          multiline
          numberOfLines={8}
          textAlignVertical="top"
        />
      </View>

      <TouchableOpacity
        style={[styles.calculateButton, loading && styles.calculateButtonDisabled]}
        onPress={handleScore}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#FFFFFF" />
        ) : (
          <Text style={styles.calculateButtonText}>Calculate ATS Score</Text>
        )}
      </TouchableOpacity>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Analyzing resume against job description...</Text>
        </View>
      )}

      {data && !loading && (
        <View style={styles.resultsSection}>
          <View style={styles.scoreCard}>
            <View style={styles.scoreMainRow}>
              <View style={[styles.scoreCircle, { borderColor: getScoreColor(data.overall_score) }]}>
                <Text style={[styles.scoreMainValue, { color: getScoreColor(data.overall_score) }]}>
                  {Math.round(data.overall_score * 100)}
                </Text>
                <Text style={[styles.scoreMainUnit, { color: getScoreColor(data.overall_score) }]}>%</Text>
              </View>
              <View style={styles.scoreMainInfo}>
                <Text style={styles.scoreMainLabel}>Overall ATS Score</Text>
                {detectedPlatform && (
                  <View style={styles.platformBadge}>
                    <Text style={styles.platformBadgeText}>{detectedPlatform}</Text>
                  </View>
                )}
              </View>
            </View>
            <View style={styles.scoreProgressBar}>
              <View
                style={[
                  styles.scoreProgressBarFill,
                  {
                    width: `${Math.min(100, data.overall_score * 100)}%`,
                    backgroundColor: getScoreColor(data.overall_score),
                  },
                ]}
              />
            </View>
          </View>

          <View style={styles.metricsCard}>
            <Text style={styles.metricsTitle}>23 Metrics Analysis</Text>
            <View style={styles.metricsGrid}>
              {ATS_METRICS.map((metric) => (
                <MetricBar
                  key={metric.key}
                  label={metric.label}
                  value={data.metrics[metric.key] ?? 0}
                />
              ))}
            </View>
          </View>

          {data.recommendations.length > 0 && (
            <View style={styles.recommendationsCard}>
              <Text style={styles.recommendationsTitle}>Optimization Recommendations</Text>
              {data.recommendations.map((rec, i) => (
                <RecommendationItem key={i} text={rec} index={i} />
              ))}
            </View>
          )}
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F172A", padding: 16 },

  header: { marginBottom: 20, flexDirection: "row", alignItems: "center", gap: 16 },
  backButton: { color: "#3B82F6", fontSize: 14 },
  headerLabel: { color: "#64748B", fontSize: 12, textTransform: "uppercase", letterSpacing: 1 },
  headerTitle: { color: "#F8FAFC", fontSize: 24, fontWeight: "700" },

  inputSection: { marginBottom: 16 },
  inputLabel: { color: "#E2E8F0", fontSize: 14, fontWeight: "600", marginBottom: 8 },
  textArea: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
    fontSize: 14,
    color: "#F8FAFC",
    borderWidth: 1,
    borderColor: "#334155",
  },
  textAreaResume: { minHeight: 150 },
  textAreaJob: { minHeight: 150 },

  calculateButton: {
    backgroundColor: "#3B82F6",
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: "center",
    marginBottom: 16,
  },
  calculateButtonDisabled: { opacity: 0.6 },
  calculateButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "600" },

  errorContainer: {
    backgroundColor: "#EF444420",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  errorText: { color: "#FCA5A5", fontSize: 14, textAlign: "center" },

  loadingContainer: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 40,
    alignItems: "center",
    marginBottom: 16,
  },
  loadingText: { color: "#94A3B8", fontSize: 14, marginTop: 12 },

  resultsSection: { gap: 16 },

  scoreCard: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    padding: 20,
  },
  scoreMainRow: { flexDirection: "row", alignItems: "center", marginBottom: 16 },
  scoreCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 4,
    justifyContent: "center",
    alignItems: "center",
    flexDirection: "row",
  },
  scoreMainValue: { fontSize: 32, fontWeight: "700" },
  scoreMainUnit: { fontSize: 16, fontWeight: "600" },
  scoreMainInfo: { marginLeft: 16, flex: 1 },
  scoreMainLabel: { color: "#94A3B8", fontSize: 14, marginBottom: 8 },
  platformBadge: {
    backgroundColor: "#334155",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
    alignSelf: "flex-start",
  },
  platformBadgeText: { color: "#CBD5E1", fontSize: 12 },
  scoreProgressBar: {
    height: 8,
    backgroundColor: "#334155",
    borderRadius: 4,
    overflow: "hidden",
  },
  scoreProgressBarFill: { height: 8, borderRadius: 4 },

  metricsCard: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
  },
  metricsTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600", marginBottom: 16 },
  metricsGrid: { gap: 12 },

  metricBar: {},
  metricBarHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  metricBarLabel: { color: "#94A3B8", fontSize: 12, flex: 1 },
  metricBarValue: { fontSize: 12, fontWeight: "600", marginLeft: 8 },
  metricBarTrack: { height: 4, backgroundColor: "#334155", borderRadius: 2, overflow: "hidden" },
  metricBarFill: { height: 4, borderRadius: 2 },

  recommendationsCard: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
  },
  recommendationsTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600", marginBottom: 16 },
  recommendationItem: { flexDirection: "row", alignItems: "flex-start", marginBottom: 12 },
  recommendationNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "#F59E0B20",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  recommendationNumberText: { color: "#F59E0B", fontSize: 12, fontWeight: "700" },
  recommendationText: { color: "#CBD5E1", fontSize: 13, flex: 1, lineHeight: 20 },
});

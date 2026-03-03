import React, { useState, useCallback, useRef } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { supabase } from "../lib/supabase";
import { tailorResume, TailorResumeResponse, atsScore } from "../api/client";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system";

function ProgressIndicator({ progress }: { progress: number }) {
  return (
    <View style={styles.progressContainer}>
      <View style={styles.progressRow}>
        <ActivityIndicator color="#3B82F6" />
        <Text style={styles.progressText}>Tailoring your resume...</Text>
        <Text style={styles.progressValue}>{progress}%</Text>
      </View>
      <View style={styles.progressBar}>
        <View style={[styles.progressFill, { width: `${progress}%` }]} />
      </View>
    </View>
  );
}

function ScoreComparison({ before, after }: { before: number; after: number }) {
  const getColor = (score: number) => {
    if (score >= 0.7) return "#10B981";
    if (score >= 0.5) return "#F59E0B";
    return "#EF4444";
  };

  const improvement = after > before;

  return (
    <View style={styles.scoreComparison}>
      <View style={styles.scoreCompareItem}>
        <Text style={styles.scoreCompareLabel}>Before</Text>
        <Text style={[styles.scoreCompareValue, { color: getColor(before) }]}>
          {Math.round(before * 100)}%
        </Text>
      </View>
      <View style={styles.scoreCompareArrow}>
        <Text style={styles.arrowText}>→</Text>
      </View>
      <View style={styles.scoreCompareItem}>
        <Text style={styles.scoreCompareLabel}>After</Text>
        <Text style={[styles.scoreCompareValue, { color: getColor(after) }]}>
          {Math.round(after * 100)}%
        </Text>
        {improvement && (
          <View style={styles.improvementBadge}>
            <Text style={styles.improvementText}>+{Math.round((after - before) * 100)}%</Text>
          </View>
        )}
      </View>
    </View>
  );
}

function SkillChips({ skills, title, variant }: { skills: string[]; title: string; variant: "primary" | "secondary" }) {
  if (skills.length === 0) return null;

  const bgColor = variant === "primary" ? "#3B82F620" : "#06B6D420";
  const textColor = variant === "primary" ? "#60A5FA" : "#22D3EE";

  return (
    <View style={styles.skillChipsSection}>
      <Text style={styles.skillChipsTitle}>{title}</Text>
      <View style={styles.skillChipsContainer}>
        {skills.map((skill, i) => (
          <View key={i} style={[styles.skillChip, { backgroundColor: bgColor }]}>
            <Text style={[styles.skillChipText, { color: textColor }]}>{skill}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

export default function TailorResumeScreen() {
  const navigation = useNavigation();

  const [resumeFile, setResumeFile] = useState<string | null>(null);
  const [resumeFileName, setResumeFileName] = useState<string | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [inputMode, setInputMode] = useState<"url" | "paste">("paste");
  const [jobUrl, setJobUrl] = useState("");

  const [data, setData] = useState<TailorResumeResponse | null>(null);
  const [beforeScore, setBeforeScore] = useState<number | null>(null);
  const [afterScore, setAfterScore] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handlePickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: "application/pdf",
        copyToCacheDirectory: true,
      });

      if (result.canceled) return;

      const asset = result.assets[0];
      setResumeFile(asset.uri);
      setResumeFileName(asset.name);

      try {
        const text = await FileSystem.readAsStringAsync(asset.uri);
        setResumeText(text.substring(0, 10000));
      } catch {
        Alert.alert("Note", "Could not extract text from PDF. Please paste resume text manually.");
      }
    } catch (err) {
      Alert.alert("Error", "Failed to pick document");
    }
  };

  const handleTailor = useCallback(async () => {
    if (!resumeText.trim()) {
      setError("Please upload your resume or paste the text");
      return;
    }

    if (inputMode === "paste" && !jobDescription.trim()) {
      setError("Please enter the job description");
      return;
    }

    if (inputMode === "url" && !jobUrl.trim()) {
      setError("Please enter the job URL");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setProgress(0);

      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        setError("Not authenticated");
        return;
      }

      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      try {
        const beforeResult = await atsScore(
          session.access_token,
          resumeText,
          jobDescription
        );
        if (beforeResult) {
          setBeforeScore(beforeResult.overall_score);
        }

        const result = await tailorResume(
          session.access_token,
          { resume_text: resumeText },
          { description: jobDescription, url: jobUrl }
        );
        setData(result);

        const afterResult = await atsScore(
          session.access_token,
          result.tailored_summary,
          jobDescription
        );
        if (afterResult) {
          setAfterScore(afterResult.overall_score);
        }

        setProgress(100);
      } finally {
        clearInterval(progressInterval);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [resumeText, jobDescription, jobUrl, inputMode]);

  const handleReset = () => {
    setResumeFile(null);
    setResumeFileName(null);
    setResumeText("");
    setJobDescription("");
    setJobUrl("");
    setData(null);
    setBeforeScore(null);
    setAfterScore(null);
    setProgress(0);
    setError(null);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backButton}>Back</Text>
        </TouchableOpacity>
        <View>
          <Text style={styles.headerLabel}>AI Tools</Text>
          <Text style={styles.headerTitle}>Resume Tailor</Text>
        </View>
        {data && (
          <TouchableOpacity onPress={handleReset}>
            <Text style={styles.resetButton}>Start Over</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.uploadSection}>
        <Text style={styles.uploadLabel}>Upload Resume</Text>
        <TouchableOpacity style={styles.uploadButton} onPress={handlePickDocument}>
          {resumeFileName ? (
            <View style={styles.uploadSuccess}>
              <Text style={styles.uploadSuccessIcon}>✓</Text>
              <Text style={styles.uploadSuccessText}>{resumeFileName}</Text>
              <Text style={styles.uploadSuccessHint}>Tap to change</Text>
            </View>
          ) : (
            <View style={styles.uploadPlaceholder}>
              <Text style={styles.uploadIcon}>📄</Text>
              <Text style={styles.uploadText}>Drop your resume here or tap to upload</Text>
              <Text style={styles.uploadHint}>PDF only, max 5MB</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <View style={styles.inputSection}>
        <Text style={styles.inputLabel}>Job Details</Text>
        <View style={styles.modeToggle}>
          <TouchableOpacity
            style={[styles.modeButton, inputMode === "url" && styles.modeButtonActive]}
            onPress={() => setInputMode("url")}
          >
            <Text style={[styles.modeButtonText, inputMode === "url" && styles.modeButtonTextActive]}>
              URL
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeButton, inputMode === "paste" && styles.modeButtonActive]}
            onPress={() => setInputMode("paste")}
          >
            <Text style={[styles.modeButtonText, inputMode === "paste" && styles.modeButtonTextActive]}>
              Paste
            </Text>
          </TouchableOpacity>
        </View>

        {inputMode === "url" ? (
          <TextInput
            style={styles.urlInput}
            placeholder="https://example.com/jobs/..."
            placeholderTextColor="#64748B"
            value={jobUrl}
            onChangeText={setJobUrl}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
        ) : (
          <TextInput
            style={styles.textArea}
            placeholder="Paste the job description here..."
            placeholderTextColor="#64748B"
            value={jobDescription}
            onChangeText={setJobDescription}
            multiline
            numberOfLines={6}
            textAlignVertical="top"
          />
        )}
      </View>

      {loading && progress > 0 && progress < 100 && (
        <ProgressIndicator progress={progress} />
      )}

      <TouchableOpacity
        style={[styles.tailorButton, loading && styles.tailorButtonDisabled]}
        onPress={handleTailor}
        disabled={loading}
      >
        {loading ? (
          <View style={styles.tailorButtonLoading}>
            <ActivityIndicator color="#FFFFFF" />
            <Text style={styles.tailorButtonText}>Tailoring...</Text>
          </View>
        ) : (
          <Text style={styles.tailorButtonText}>Tailor Resume</Text>
        )}
      </TouchableOpacity>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {data && (
        <View style={styles.resultsSection}>
          {beforeScore !== null && afterScore !== null && (
            <View style={styles.scoreCard}>
              <Text style={styles.scoreCardTitle}>ATS Score Comparison</Text>
              <ScoreComparison before={beforeScore} after={afterScore} />
            </View>
          )}

          <View style={styles.summaryCard}>
            <View style={styles.summaryHeader}>
              <Text style={styles.summaryTitle}>Tailored Summary</Text>
              <TouchableOpacity>
                <Text style={styles.downloadButton}>Download</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.summaryContent}>
              <Text style={styles.summaryText}>{data.tailored_summary}</Text>
            </View>
          </View>

          <View style={styles.skillsRow}>
            <View style={styles.skillsCard}>
              <SkillChips
                skills={data.highlighted_skills}
                title="Highlighted Skills"
                variant="primary"
              />
            </View>
            <View style={styles.skillsCard}>
              <SkillChips
                skills={data.added_keywords}
                title="Added Keywords"
                variant="secondary"
              />
            </View>
          </View>
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F172A", padding: 16 },

  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 20 },
  backButton: { color: "#3B82F6", fontSize: 14 },
  headerLabel: { color: "#64748B", fontSize: 12, textTransform: "uppercase", letterSpacing: 1 },
  headerTitle: { color: "#F8FAFC", fontSize: 24, fontWeight: "700" },
  resetButton: { color: "#94A3B8", fontSize: 14 },

  uploadSection: { marginBottom: 16 },
  uploadLabel: { color: "#E2E8F0", fontSize: 14, fontWeight: "600", marginBottom: 8 },
  uploadButton: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    borderWidth: 2,
    borderColor: "#334155",
    borderStyle: "dashed",
    padding: 24,
    alignItems: "center",
  },
  uploadPlaceholder: { alignItems: "center" },
  uploadIcon: { fontSize: 32, marginBottom: 8 },
  uploadText: { color: "#94A3B8", fontSize: 14, marginBottom: 4 },
  uploadHint: { color: "#64748B", fontSize: 12 },
  uploadSuccess: { alignItems: "center" },
  uploadSuccessIcon: { color: "#10B981", fontSize: 24, marginBottom: 4 },
  uploadSuccessText: { color: "#10B981", fontSize: 14, fontWeight: "500" },
  uploadSuccessHint: { color: "#64748B", fontSize: 12, marginTop: 4 },

  inputSection: { marginBottom: 16 },
  inputLabel: { color: "#E2E8F0", fontSize: 14, fontWeight: "600", marginBottom: 8 },
  modeToggle: { flexDirection: "row", gap: 8, marginBottom: 12 },
  modeButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: "#1E293B",
    alignItems: "center",
  },
  modeButtonActive: { backgroundColor: "#3B82F6" },
  modeButtonText: { color: "#94A3B8", fontSize: 14, fontWeight: "500" },
  modeButtonTextActive: { color: "#FFFFFF" },
  urlInput: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
    fontSize: 14,
    color: "#F8FAFC",
    borderWidth: 1,
    borderColor: "#334155",
  },
  textArea: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
    fontSize: 14,
    color: "#F8FAFC",
    borderWidth: 1,
    borderColor: "#334155",
    minHeight: 150,
  },

  progressContainer: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  progressRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  progressText: { color: "#94A3B8", fontSize: 14, flex: 1 },
  progressValue: { color: "#3B82F6", fontSize: 14, fontWeight: "700" },
  progressBar: {
    height: 6,
    backgroundColor: "#334155",
    borderRadius: 3,
    marginTop: 12,
    overflow: "hidden",
  },
  progressFill: { height: 6, backgroundColor: "#3B82F6", borderRadius: 3 },

  tailorButton: {
    backgroundColor: "#3B82F6",
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: "center",
    marginBottom: 16,
  },
  tailorButtonDisabled: { opacity: 0.6 },
  tailorButtonLoading: { flexDirection: "row", alignItems: "center", gap: 8 },
  tailorButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "600" },

  errorContainer: {
    backgroundColor: "#EF444420",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  errorText: { color: "#FCA5A5", fontSize: 14, textAlign: "center" },

  resultsSection: { gap: 16 },

  scoreCard: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
  },
  scoreCardTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600", marginBottom: 16 },
  scoreComparison: { flexDirection: "row", alignItems: "center", justifyContent: "center" },
  scoreCompareItem: { alignItems: "center", flex: 1 },
  scoreCompareLabel: { color: "#94A3B8", fontSize: 12, marginBottom: 4 },
  scoreCompareValue: { fontSize: 32, fontWeight: "700" },
  scoreCompareArrow: { paddingHorizontal: 16 },
  arrowText: { color: "#64748B", fontSize: 24 },
  improvementBadge: {
    backgroundColor: "#10B98120",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
    marginTop: 8,
  },
  improvementText: { color: "#10B981", fontSize: 12, fontWeight: "600" },

  summaryCard: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 16,
  },
  summaryHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 12 },
  summaryTitle: { color: "#E2E8F0", fontSize: 16, fontWeight: "600" },
  downloadButton: { color: "#3B82F6", fontSize: 14 },
  summaryContent: {
    backgroundColor: "#0F172A",
    borderRadius: 8,
    padding: 12,
  },
  summaryText: { color: "#CBD5E1", fontSize: 14, lineHeight: 22 },

  skillsRow: { flexDirection: "row", gap: 12 },
  skillsCard: { flex: 1, backgroundColor: "#1E293B", borderRadius: 12, padding: 12 },
  skillChipsSection: {},
  skillChipsTitle: { color: "#94A3B8", fontSize: 12, marginBottom: 8 },
  skillChipsContainer: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  skillChip: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  skillChipText: { fontSize: 11, fontWeight: "500" },
});

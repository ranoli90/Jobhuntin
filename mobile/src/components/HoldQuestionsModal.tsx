/**
 * Part 4: Frontend – HoldQuestionsModal
 *
 * Modal / screen that surfaces pending "hold" questions from the agent
 * and lets the user provide answers, then re-queues the application.
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Modal,
} from "react-native";
import type { ApplicationInput, AnswerItem } from "../types";
import {
  useApplicationStore,
  usePendingInputs,
} from "../stores/applicationStore";

interface HoldQuestionsModalProps {
  visible: boolean;
  applicationId: string;
  onClose: () => void;
}

export const HoldQuestionsModal: React.FC<HoldQuestionsModalProps> = ({
  visible,
  applicationId,
  onClose,
}) => {
  const pendingInputs = usePendingInputs(applicationId);
  const submitApplicationInputs = useApplicationStore(
    (s) => s.submitApplicationInputs
  );

  // Local draft answers keyed by input id
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset drafts when inputs change
  useEffect(() => {
    const initial: Record<string, string> = {};
    pendingInputs.forEach((inp) => {
      initial[inp.id] = "";
    });
    setDrafts(initial);
    setError(null);
  }, [applicationId, pendingInputs.length]);

  const allAnswered = pendingInputs.every(
    (inp) => (drafts[inp.id] ?? "").trim().length > 0
  );

  const handleSubmit = async () => {
    if (!allAnswered) return;
    setSubmitting(true);
    setError(null);

    const answers: AnswerItem[] = pendingInputs.map((inp) => ({
      input_id: inp.id,
      answer: drafts[inp.id].trim(),
    }));

    try {
      await submitApplicationInputs(applicationId, answers);
      onClose();
    } catch (err: any) {
      setError(err.message ?? "We couldn't submit your response. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Bot needs your help</Text>
          <TouchableOpacity onPress={onClose}>
            <Text style={styles.closeButton}>Close</Text>
          </TouchableOpacity>
        </View>

        <ScrollView
          style={styles.scrollArea}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {pendingInputs.length === 0 ? (
            <Text style={styles.emptyText}>
              No pending questions. The bot will continue automatically.
            </Text>
          ) : (
            pendingInputs.map((inp: ApplicationInput) => (
              <View key={inp.id} style={styles.questionBlock}>
                <Text style={styles.questionText}>{inp.question}</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Your answer…"
                  placeholderTextColor="#9ca3af"
                  value={drafts[inp.id] ?? ""}
                  onChangeText={(text) =>
                    setDrafts((prev) => ({ ...prev, [inp.id]: text }))
                  }
                  editable={!submitting}
                />
              </View>
            ))
          )}

          {error && <Text style={styles.errorText}>{error}</Text>}
        </ScrollView>

        {pendingInputs.length > 0 && (
          <View style={styles.footer}>
            <TouchableOpacity
              style={[
                styles.submitButton,
                (!allAnswered || submitting) && styles.submitButtonDisabled,
              ]}
              onPress={handleSubmit}
              disabled={!allAnswered || submitting}
            >
              {submitting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitButtonText}>
                  Submit & Resume Bot
                </Text>
              )}
            </TouchableOpacity>
          </View>
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f9fafb",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
    backgroundColor: "#fff",
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
  },
  closeButton: {
    fontSize: 15,
    color: "#3b82f6",
    fontWeight: "600",
  },
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  emptyText: {
    fontSize: 15,
    color: "#6b7280",
    textAlign: "center",
    marginTop: 40,
  },
  questionBlock: {
    marginBottom: 20,
  },
  questionText: {
    fontSize: 15,
    fontWeight: "600",
    color: "#374151",
    marginBottom: 8,
  },
  input: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: "#111827",
  },
  errorText: {
    color: "#ef4444",
    fontSize: 14,
    marginTop: 8,
    textAlign: "center",
  },
  footer: {
    padding: 20,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
  },
  submitButton: {
    backgroundColor: "#3b82f6",
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "700",
  },
});

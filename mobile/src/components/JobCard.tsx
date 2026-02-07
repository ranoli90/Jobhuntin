/**
 * Part 4: Frontend – JobCard component
 *
 * Renders a job card with a real-time status badge based on the
 * application state driven by the agent worker.
 */

import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import type { Job, Application } from "../types";
import {
  useApplicationStore,
  useApplicationStatusLabel,
  useIsProcessing,
  usePendingInputs,
} from "../stores/applicationStore";

interface JobCardProps {
  job: Job;
  application?: Application;
  onPressHold?: (applicationId: string) => void;
}

export const JobCard: React.FC<JobCardProps> = ({
  job,
  application,
  onPressHold,
}) => {
  const statusLabel = useApplicationStatusLabel(application?.id ?? "");
  const isProcessing = useIsProcessing(application?.id ?? "");
  const pendingInputs = usePendingInputs(application?.id ?? "");

  const badgeColor = (): string => {
    if (!application) return "#ccc";
    switch (application.status) {
      case "PROCESSING":
        return "#3b82f6"; // blue
      case "REQUIRES_INPUT":
        return "#f59e0b"; // amber
      case "APPLIED":
        return "#10b981"; // green
      case "FAILED":
        return "#ef4444"; // red
      case "QUEUED":
      default:
        return "#6b7280"; // gray
    }
  };

  return (
    <View style={styles.card}>
      <Text style={styles.title}>{job.title}</Text>
      <Text style={styles.company}>{job.company}</Text>
      {job.location && <Text style={styles.location}>{job.location}</Text>}
      {job.salary_min != null && (
        <Text style={styles.salary}>
          ${job.salary_min.toLocaleString()}
          {job.salary_max != null ? ` – $${job.salary_max.toLocaleString()}` : "+"}
        </Text>
      )}

      {application && (
        <View style={styles.statusRow}>
          <View style={[styles.badge, { backgroundColor: badgeColor() }]}>
            <Text style={styles.badgeText}>{statusLabel}</Text>
          </View>

          {isProcessing && (
            <Text style={styles.typingIndicator}>Bot is typing…</Text>
          )}

          {application.status === "REQUIRES_INPUT" &&
            pendingInputs.length > 0 && (
              <TouchableOpacity
                style={styles.holdButton}
                onPress={() => onPressHold?.(application.id)}
              >
                <Text style={styles.holdButtonText}>
                  Answer {pendingInputs.length} question
                  {pendingInputs.length > 1 ? "s" : ""}
                </Text>
              </TouchableOpacity>
            )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 20,
    marginVertical: 8,
    marginHorizontal: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 4,
  },
  company: {
    fontSize: 15,
    color: "#6b7280",
    marginBottom: 2,
  },
  location: {
    fontSize: 13,
    color: "#9ca3af",
    marginBottom: 4,
  },
  salary: {
    fontSize: 14,
    fontWeight: "600",
    color: "#059669",
    marginBottom: 8,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 8,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "600",
  },
  typingIndicator: {
    fontSize: 12,
    color: "#3b82f6",
    fontStyle: "italic",
  },
  holdButton: {
    backgroundColor: "#f59e0b",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  holdButtonText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "600",
  },
});

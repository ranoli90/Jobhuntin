/**
 * Reusable error banner for inline error display.
 */

import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  message,
  onRetry,
  onDismiss,
}) => (
  <View style={styles.container}>
    <Text style={styles.message}>{message}</Text>
    <View style={styles.actions}>
      {onRetry && (
        <TouchableOpacity onPress={onRetry} style={styles.button}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      )}
      {onDismiss && (
        <TouchableOpacity onPress={onDismiss} style={styles.button}>
          <Text style={styles.dismissText}>Dismiss</Text>
        </TouchableOpacity>
      )}
    </View>
  </View>
);

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#fef2f2",
    borderWidth: 1,
    borderColor: "#fecaca",
    borderRadius: 10,
    padding: 14,
    marginHorizontal: 16,
    marginVertical: 8,
  },
  message: {
    fontSize: 14,
    color: "#991b1b",
    lineHeight: 20,
  },
  actions: {
    flexDirection: "row",
    gap: 12,
    marginTop: 10,
  },
  button: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  retryText: {
    color: "#3b82f6",
    fontSize: 13,
    fontWeight: "600",
  },
  dismissText: {
    color: "#6b7280",
    fontSize: 13,
    fontWeight: "600",
  },
});

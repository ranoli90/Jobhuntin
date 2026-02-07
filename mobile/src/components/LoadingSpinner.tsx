/**
 * Reusable loading spinner with optional message.
 */

import React from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";

interface LoadingSpinnerProps {
  message?: string;
  size?: "small" | "large";
  color?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message,
  size = "large",
  color = "#3b82f6",
}) => (
  <View style={styles.container}>
    <ActivityIndicator size={size} color={color} />
    {message && <Text style={styles.message}>{message}</Text>}
  </View>
);

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  message: {
    marginTop: 12,
    fontSize: 14,
    color: "#6b7280",
    textAlign: "center",
  },
});

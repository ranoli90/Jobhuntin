/**
 * Onboarding Flow — 3-step screen sequence for new users.
 *
 * Step 1: Welcome + value prop
 * Step 2: Resume upload
 * Step 3: Referral code (optional) + start swiping
 *
 * Tracks analytics events and marks onboarding complete on finish.
 */

import React, { useState, useRef } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  FlatList,
  TextInput,
  ActivityIndicator,
  Alert,
} from "react-native";
import { track } from "../lib/analytics";
import { supabase } from "../lib/supabase";
import { API_BASE_URL } from "../lib/config";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface OnboardingProps {
  onComplete: () => void;
  onPickResume: () => Promise<boolean>;  // returns true if resume uploaded
}

interface SlideData {
  key: string;
  title: string;
  description: string;
  emoji: string;
}

const SLIDES: SlideData[] = [
  {
    key: "welcome",
    title: "Welcome to Sorce",
    description: "Swipe right on jobs you like.\nOur AI fills out the application for you.",
    emoji: "\uD83D\uDE80",
  },
  {
    key: "resume",
    title: "Upload Your Resume",
    description: "We'll parse your resume to auto-fill job applications accurately.",
    emoji: "\uD83D\uDCC4",
  },
  {
    key: "referral",
    title: "Got a Referral Code?",
    description: "Enter a friend's code and you both get 5 bonus applications.",
    emoji: "\uD83C\uDF81",
  },
];

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}`, "Content-Type": "application/json" }
    : { "Content-Type": "application/json" };
}

async function completeOnboarding(referralCode: string | null): Promise<void> {
  const headers = await getAuthHeaders();
  await fetch(`${API_BASE_URL}/onboarding/complete`, {
    method: "POST",
    headers,
    body: JSON.stringify({ referral_code: referralCode || null }),
  });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function OnboardingScreen({ onComplete, onPickResume }: OnboardingProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [referralCode, setReferralCode] = useState("");
  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const goToNext = () => {
    if (currentIndex < SLIDES.length - 1) {
      const next = currentIndex + 1;
      flatListRef.current?.scrollToIndex({ index: next, animated: true });
      setCurrentIndex(next);
    }
  };

  const handleResumeUpload = async () => {
    setLoading(true);
    try {
      const success = await onPickResume();
      if (success) {
        setResumeUploaded(true);
        track("onboarding_resume_uploaded", {});
        goToNext();
      }
    } catch (err) {
      Alert.alert("Upload Failed", "Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      await completeOnboarding(referralCode || null);
      track("onboarding_completed", { had_referral: !!referralCode });
    } catch (err) {
      console.error("Onboarding complete error:", err);
    } finally {
      setLoading(false);
      onComplete();
    }
  };

  const renderSlide = ({ item, index }: { item: SlideData; index: number }) => (
    <View style={[styles.slide, { width: SCREEN_WIDTH }]}>
      <Text style={styles.emoji}>{item.emoji}</Text>
      <Text style={styles.slideTitle}>{item.title}</Text>
      <Text style={styles.slideDesc}>{item.description}</Text>

      {/* Step-specific content */}
      {item.key === "welcome" && (
        <TouchableOpacity style={styles.primaryButton} onPress={goToNext}>
          <Text style={styles.primaryButtonText}>Get Started</Text>
        </TouchableOpacity>
      )}

      {item.key === "resume" && (
        <View style={styles.stepContent}>
          {resumeUploaded ? (
            <View style={styles.successBadge}>
              <Text style={styles.successText}>Resume uploaded!</Text>
            </View>
          ) : (
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={handleResumeUpload}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.primaryButtonText}>Upload Resume (PDF)</Text>
              )}
            </TouchableOpacity>
          )}
          <TouchableOpacity style={styles.skipButton} onPress={goToNext}>
            <Text style={styles.skipButtonText}>Skip for now</Text>
          </TouchableOpacity>
        </View>
      )}

      {item.key === "referral" && (
        <View style={styles.stepContent}>
          <TextInput
            style={styles.codeInput}
            placeholder="Enter referral code (optional)"
            placeholderTextColor="#64748B"
            value={referralCode}
            onChangeText={setReferralCode}
            autoCapitalize="characters"
            autoCorrect={false}
          />
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={handleFinish}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.primaryButtonText}>Start Swiping</Text>
            )}
          </TouchableOpacity>
        </View>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={SLIDES}
        renderItem={renderSlide}
        horizontal
        pagingEnabled
        scrollEnabled={false}
        showsHorizontalScrollIndicator={false}
        keyExtractor={(item) => item.key}
      />

      {/* Pagination dots */}
      <View style={styles.dotsRow}>
        {SLIDES.map((_, i) => (
          <View
            key={i}
            style={[styles.dot, i === currentIndex && styles.dotActive]}
          />
        ))}
      </View>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F172A" },
  slide: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
  },
  emoji: { fontSize: 64, marginBottom: 24 },
  slideTitle: { color: "#F8FAFC", fontSize: 28, fontWeight: "700", textAlign: "center", marginBottom: 12 },
  slideDesc: { color: "#94A3B8", fontSize: 16, textAlign: "center", lineHeight: 24, marginBottom: 32 },

  stepContent: { width: "100%", alignItems: "center" },

  primaryButton: {
    backgroundColor: "#3B82F6",
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 32,
    width: "100%",
    alignItems: "center",
    marginBottom: 12,
  },
  primaryButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },

  skipButton: { padding: 12 },
  skipButtonText: { color: "#64748B", fontSize: 14 },

  successBadge: {
    backgroundColor: "#064E3B",
    borderRadius: 10,
    padding: 14,
    width: "100%",
    alignItems: "center",
    marginBottom: 12,
  },
  successText: { color: "#10B981", fontSize: 15, fontWeight: "600" },

  codeInput: {
    backgroundColor: "#1E293B",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
    color: "#F8FAFC",
    fontSize: 16,
    padding: 14,
    width: "100%",
    textAlign: "center",
    letterSpacing: 1,
    marginBottom: 16,
  },

  dotsRow: {
    flexDirection: "row",
    justifyContent: "center",
    paddingBottom: 48,
    gap: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#334155",
  },
  dotActive: {
    backgroundColor: "#3B82F6",
    width: 24,
  },
});

/**
 * Smart Pre-Fill — learns from HOLD question answers to auto-fill future forms.
 *
 * Stores field_label → answer mappings in `answer_memory` table.
 * On new HOLD questions, suggests previous answers for matching labels.
 */

import { supabase } from "../../lib/supabase";
import { API_BASE_URL } from "../../lib/config";

export interface MemorizedAnswer {
  field_label: string;
  field_type: string;
  answer_value: string;
  use_count: number;
  last_used_at: string;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}`, "Content-Type": "application/json" }
    : { "Content-Type": "application/json" };
}

/**
 * Get all memorized answers for the current user.
 */
export async function getMemorizedAnswers(): Promise<MemorizedAnswer[]> {
  const h = await getAuthHeaders();
  const r = await fetch(`${API_BASE_URL}/me/answer-memory`, { headers: h });
  if (!r.ok) return [];
  return r.json();
}

/**
 * Save an answer to memory for future pre-fill.
 */
export async function saveAnswer(
  fieldLabel: string,
  fieldType: string,
  answerValue: string,
): Promise<void> {
  const h = await getAuthHeaders();
  await fetch(`${API_BASE_URL}/me/answer-memory`, {
    method: "POST",
    headers: h,
    body: JSON.stringify({
      field_label: fieldLabel,
      field_type: fieldType,
      answer_value: answerValue,
    }),
  });
}

/**
 * Match HOLD question labels against memorized answers.
 * Returns a map of field_label → suggested answer.
 */
export async function getSuggestionsForFields(
  fieldLabels: string[],
): Promise<Record<string, string>> {
  const memory = await getMemorizedAnswers();
  const suggestions: Record<string, string> = {};

  for (const label of fieldLabels) {
    const normalized = label.toLowerCase().trim();

    // Exact match first
    const exact = memory.find(
      (m) => m.field_label.toLowerCase().trim() === normalized,
    );
    if (exact) {
      suggestions[label] = exact.answer_value;
      continue;
    }

    // Fuzzy match — check if label contains known keywords
    const fuzzy = memory.find((m) => {
      const mNorm = m.field_label.toLowerCase().trim();
      return (
        normalized.includes(mNorm) ||
        mNorm.includes(normalized) ||
        levenshteinSimilarity(normalized, mNorm) > 0.7
      );
    });
    if (fuzzy) {
      suggestions[label] = fuzzy.answer_value;
    }
  }

  return suggestions;
}

/**
 * Batch save multiple answers after a HOLD question set is completed.
 */
export async function batchSaveAnswers(
  answers: Array<{ label: string; type: string; value: string }>,
): Promise<void> {
  const promises = answers
    .filter((a) => a.value.trim().length > 0)
    .map((a) => saveAnswer(a.label, a.type, a.value));
  await Promise.allSettled(promises);
}

// Simple Levenshtein similarity (0-1)
function levenshteinSimilarity(a: string, b: string): number {
  if (a === b) return 1;
  const maxLen = Math.max(a.length, b.length);
  if (maxLen === 0) return 1;

  const matrix: number[][] = [];
  for (let i = 0; i <= a.length; i++) {
    matrix[i] = [i];
    for (let j = 1; j <= b.length; j++) {
      if (i === 0) { matrix[i][j] = j; continue; }
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1),
      );
    }
  }
  return 1 - matrix[a.length][b.length] / maxLen;
}

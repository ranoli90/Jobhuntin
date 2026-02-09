import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "../lib/api";

export interface MemorizedAnswer {
  field_label: string;
  field_type: string;
  answer_value: string;
  use_count: number;
  last_used_at: string;
}

/**
 * Fetch all memorized answers for the current user.
 */
async function getMemorizedAnswers(): Promise<MemorizedAnswer[]> {
  return apiGet<MemorizedAnswer[]>("me/answer-memory");
}

/**
 * Save an answer to memory for future pre-fill.
 */
async function saveAnswer(payload: {
  field_label: string;
  field_type: string;
  answer_value: string;
}): Promise<void> {
  await apiPost("me/answer-memory", payload);
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
      if (i === 0) {
        matrix[i][j] = j;
        continue;
      }
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)
      );
    }
  }
  return 1 - matrix[a.length][b.length] / maxLen;
}

export function useAnswerMemory() {
  const queryClient = useQueryClient();

  const { data: memory = [], isLoading } = useQuery({
    queryKey: ["answer-memory"],
    queryFn: getMemorizedAnswers,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const saveMutation = useMutation({
    mutationFn: saveAnswer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["answer-memory"] });
    },
  });

  /**
   * Get suggestions for a specific field label based on memory.
   */
  const getSuggestion = (fieldLabel: string): string | null => {
    if (!memory.length) return null;
    const normalized = fieldLabel.toLowerCase().trim();

    // 1. Exact match
    const exact = memory.find(
      (m) => m.field_label.toLowerCase().trim() === normalized
    );
    if (exact) return exact.answer_value;

    // 2. Fuzzy match
    const fuzzy = memory.find((m) => {
      const mNorm = m.field_label.toLowerCase().trim();
      return (
        normalized.includes(mNorm) ||
        mNorm.includes(normalized) ||
        levenshteinSimilarity(normalized, mNorm) > 0.7
      );
    });

    return fuzzy ? fuzzy.answer_value : null;
  };

  return {
    memory,
    isLoading,
    getSuggestion,
    saveAnswer: saveMutation.mutateAsync,
  };
}

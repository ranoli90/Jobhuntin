import { useState, useCallback } from "react";
import { pushToast } from "../lib/toast";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

type Decision = "ACCEPT" | "REJECT";

interface SwipeResult {
  jobId: string;
  decision: Decision;
  success: boolean;
}

interface SwipeOptions {
  onComplete?: (jobId: string, decision: Decision) => void;
}

export function useSwipe({ onComplete }: SwipeOptions = {}) {
  const [isSubmitting, setSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState<SwipeResult | null>(null);

  const handleSwipe = useCallback(
    async (jobId: string, decision: Decision) => {
      if (!jobId) return;
      setSubmitting(true);
      try {
        const resp = await fetch(`${API_BASE}/applications`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ job_id: jobId, decision }),
        });
        if (!resp.ok) throw new Error("Unable to record swipe");
        pushToast({ title: decision === "ACCEPT" ? "Applied" : "Skipped", tone: "success" });
        setLastResult({ jobId, decision, success: true });
        onComplete?.(jobId, decision);
      } catch (error) {
        pushToast({ title: "Swipe failed", description: (error as Error).message, tone: "error" });
        setLastResult({ jobId, decision, success: false });
      } finally {
        setSubmitting(false);
      }
    },
    [onComplete],
  );

  const clearResult = useCallback(() => setLastResult(null), []);

  return { handleSwipe, isSubmitting, lastResult, clearResult };
}

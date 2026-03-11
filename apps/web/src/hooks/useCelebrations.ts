import { useRef } from "react";
import { pushToast } from "../lib/toast";

export function useFirstSaveCelebration() {
  const toasted = useRef<Set<string>>(new Set());

  const celebrate = (jobId: string, jobTitle: string, company: string) => {
    if (toasted.current.has(jobId)) return;
    toasted.current.add(jobId);
    pushToast({
      title: "First job saved! 🎯",
      description: `${jobTitle} @ ${company} is now in your shortlist.`,
      tone: "success",
    });
  };

  return { celebrate };
}

export function useSessionMilestone() {
  // N-5: Session milestones use higher thresholds to avoid overlapping with
  // per-swipe milestones [1, 5, 10, 25] defined in JobsView.
  const milestones = [50, 100, 250, 500];
  const toasted = useRef<Set<number>>(new Set());

  const celebrate = (count: number) => {
    for (const m of milestones) {
      if (count >= m && !toasted.current.has(m)) {
        toasted.current.add(m);
        pushToast({
          title: `🔥 ${m} jobs viewed`,
          description: "You're building momentum—keep scouting!",
          tone: "success",
        });
      }
    }
  };

  return { celebrate };
}

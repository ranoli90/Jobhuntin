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
  const milestones = [10, 25, 50, 100];
  const toasted = useRef<Set<number>>(new Set());

  const celebrate = (count: number) => {
    milestones.forEach((m) => {
      if (count >= m && !toasted.current.has(m)) {
        toasted.current.add(m);
        pushToast({
          title: `🔥 ${m} jobs viewed`,
          description: "You're building momentum—keep scouting!",
          tone: "success",
        });
      }
    });
  };

  return { celebrate };
}

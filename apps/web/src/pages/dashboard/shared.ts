import { useReducedMotion } from "framer-motion";
import React, { useEffect, useRef, useState } from "react";
import { getLocale, isRTLLanguage } from "../../lib/i18n";

// Shared locale helper – used by all sub-views
export const sharedLocale = getLocale();
export const sharedRtl = isRTLLanguage(sharedLocale);

// N-10: Centralised status → Badge variant mapping
export function statusVariant(status: string): 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'APPLIED': return 'success';
    case 'HOLD': return 'warning';
    case 'FAILED':
    case 'REJECTED': return 'error';
    default: return 'default';
  }
}

// D14/B1: BILLING_TIERS hardcoded; consider fetching from /billing/tiers API when available
export const BILLING_TIERS = [
  { name: "FREE" as const, price: "$0", features: ["10 applications", "Basic tailoring", "Standard support"], actionKey: null, recommended: false },
  { name: "PRO" as const, price: "$19", features: ["Unlimited apps", "Priority queue", "Interview coach"], recommended: true, actionKey: "upgrade" as const },
  { name: "TEAM" as const, price: "$49", features: ["10 team seats", "API access", "White-label reports"], actionKey: "addSeats" as const, recommended: false },
] as const;

// M-12: Page size for ApplicationsView pagination
export const APPLICATIONS_PAGE_SIZE = 20;

export const AnimatedNumber = ({ value, duration = 1000, shouldReduceMotion = false }: { value: number | string; duration?: number; shouldReduceMotion?: boolean }) => {
  const [displayValue, setDisplayValue] = useState(0);
  const prevValueRef = useRef(0);

  useEffect(() => {
    const numValue = Number(value);
    if (isNaN(numValue) || numValue < 0) {
      setDisplayValue(numValue || 0);
      return;
    }

    const start = prevValueRef.current;
    const end = numValue;
    prevValueRef.current = end;

    if (start === end || shouldReduceMotion) {
      setDisplayValue(end);
      return;
    }

    const startTime = performance.now();
    let rafId: number;

    function animate(currentTime: number) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplayValue(Math.round(start + (end - start) * eased));
      if (progress < 1) {
        rafId = requestAnimationFrame(animate);
      }
    }

    rafId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafId);
  }, [value, duration, shouldReduceMotion]);

  return <span>{typeof value === 'string' ? value : displayValue}</span>;
};
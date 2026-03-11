import { useReducedMotion } from "framer-motion";
import React, { useEffect, useRef, useState } from "react";
import { getLocale, isRTLLanguage } from "../../lib/i18n";

// Shared locale helper – used by all sub-views
export const sharedLocale = getLocale();
export const sharedRtl = isRTLLanguage(sharedLocale);

// N-10: Centralised status → Badge variant mapping
export function statusVariant(
  status: string,
): "success" | "warning" | "error" | "default" {
  switch (status) {
    case "APPLIED": {
      return "success";
    }
    case "HOLD": {
      return "warning";
    }
    case "FAILED":
    case "REJECTED": {
      return "error";
    }
    default: {
      return "default";
    }
  }
}

// M-12: Page size for ApplicationsView pagination
export const APPLICATIONS_PAGE_SIZE = 20;

export const AnimatedNumber = ({
  value,
  duration = 1000,
  shouldReduceMotion = false,
}: {
  value: number | string;
  duration?: number;
  shouldReduceMotion?: boolean;
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const previousValueReference = useRef(0);

  useEffect(() => {
    const numberValue = Number(value);
    if (isNaN(numberValue) || numberValue < 0) {
      setDisplayValue(numberValue || 0);
      return;
    }

    const start = previousValueReference.current;
    const end = numberValue;
    previousValueReference.current = end;

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

  return <span>{typeof value === "string" ? value : displayValue}</span>;
};

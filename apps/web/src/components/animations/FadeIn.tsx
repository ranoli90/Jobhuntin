import React, { useState, useEffect, useRef } from "react";
import { cn } from "../../lib/utils";

interface FadeInProperties {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  threshold?: number;
}

function usePrefersReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mq.matches);
    const handler = () => setPrefersReducedMotion(mq.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);
  return prefersReducedMotion;
}

export function FadeIn({
  children,
  className = "",
  delay = 0,
  threshold = 0.08,
}: FadeInProperties) {
  const reference = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const prefersReducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    const element = reference.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold },
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [threshold]);

  const showImmediately = prefersReducedMotion || visible;

  return (
    <div
      ref={reference}
      className={cn(
        "transition-all ease-out",
        prefersReducedMotion ? "duration-0" : "duration-700",
        showImmediately ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10",
        className,
      )}
      style={{ transitionDelay: prefersReducedMotion ? "0ms" : `${delay}ms` }}
    >
      {children}
    </div>
  );
}

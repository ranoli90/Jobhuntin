import React, { useState, useEffect, useRef } from "react";
import { cn } from "../../lib/utils";

interface FadeInProperties {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  threshold?: number;
}

export function FadeIn({
  children,
  className = "",
  delay = 0,
  threshold = 0.08,
}: FadeInProperties) {
  const reference = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

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

  return (
    <div
      ref={reference}
      className={cn(
        "transition-all duration-700 ease-out",
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10",
        className,
      )}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

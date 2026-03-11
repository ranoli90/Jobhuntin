/**
 * M6: Accessibility Improvements - Skip Link Component
 *
 * Provides a skip link for keyboard users to jump to main content.
 * WCAG 2.1 AA requirement for keyboard navigation.
 */

import * as React from "react";
import { cn } from "../lib/utils";

interface SkipLinkProperties {
  href: string;
  children: React.ReactNode;
  className?: string;
}

export function SkipLink({ href, children, className }: SkipLinkProperties) {
  return (
    <a
      href={href}
      className={cn(
        "sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50",
        "focus:px-4 focus:py-2 focus:bg-brand-primary focus:text-white",
        "focus:rounded-lg focus:font-medium focus:shadow-lg",
        "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-primary",
        className,
      )}
    >
      {children}
    </a>
  );
}

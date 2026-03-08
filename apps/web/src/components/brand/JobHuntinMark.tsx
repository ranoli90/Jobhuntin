/**
 * Custom JobHuntin brand mark — a document with an upward arrow (resume + apply).
 * Unique, brandable, not a generic briefcase.
 */
import React from 'react';
import { cn } from '../../lib/utils';

interface JobHuntinMarkProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = { sm: 16, md: 20, lg: 24 };

export function JobHuntinMark({ className, size = 'md' }: JobHuntinMarkProps) {
  const s = sizeMap[size];
  return (
    <svg
      width={s}
      height={s}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("shrink-0", className)}
      aria-hidden
    >
      {/* Document body */}
      <path
        d="M7 3h6l5 5v11a2 2 0 01-2 2H7a2 2 0 01-2-2V5a2 2 0 012-2z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Folded corner */}
      <path
        d="M13 3v5h5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Upward arrow (apply/send) */}
      <path
        d="M12 11v6M9 14l3-3 3 3"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

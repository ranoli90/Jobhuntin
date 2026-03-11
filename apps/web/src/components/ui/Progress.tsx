import React from "react";
export const Progress = ({
  value = 0,
  className = "",
}: {
  value?: number;
  className?: string;
}) => (
  <div
    className={`h-2 w-full rounded-full bg-slate-100 overflow-hidden ${className}`}
  >
    <div
      className="h-full bg-primary-600 rounded-full transition-all duration-300"
      style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
    />
  </div>
);

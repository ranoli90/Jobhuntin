import React from "react";
export const Checkbox = ({
  checked,
  onCheckedChange,
  className = "",
  ...properties
}: {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  className?: string;
  [key: string]: unknown;
}) => (
  <input
    type="checkbox"
    checked={checked}
    onChange={(e) => onCheckedChange?.(e.target.checked)}
    className={`h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500 ${className}`}
    {...properties}
  />
);

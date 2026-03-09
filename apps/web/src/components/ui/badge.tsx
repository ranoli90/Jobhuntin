import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "outline" | "destructive" | "success" | "warning" | "error" | "primary" | "lagoon";
  size?: "sm" | "md" | "lg";
}

export function Badge({ className, variant = "default", size, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
        {
          default: "border-transparent bg-primary-100 text-primary-800",
          secondary: "border-transparent bg-slate-100 text-slate-800",
          outline: "text-slate-950 border-slate-200",
          destructive: "border-transparent bg-red-100 text-red-800",
          success: "border-transparent bg-green-100 text-green-800",
          warning: "border-transparent bg-amber-100 text-amber-800",
          error: "border-transparent bg-red-100 text-red-800",
          primary: "border-transparent bg-primary-100 text-primary-800",
          lagoon: "border-transparent bg-primary-100 text-primary-800",
        }[variant],
        size === "sm" && "text-[10px] px-1.5 py-0",
        size === "lg" && "text-sm px-3 py-1",
        className
      )}
      {...props}
    />
  );
}

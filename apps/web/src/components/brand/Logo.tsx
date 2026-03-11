import React from "react";
import { Link } from "react-router-dom";
import { cn } from "../../lib/utils";
import { JobHuntinMark } from "./JobHuntinMark";

interface LogoProperties {
  className?: string;
  iconOnly?: boolean;
  to?: string;
  onClick?: () => void;
  size?: "sm" | "md" | "lg";
  variant?: "light" | "dark";
}

export function Logo({
  className,
  iconOnly = false,
  to = "/",
  onClick,
  size = "md",
  variant = "light",
}: LogoProperties) {
  const sizeClasses = {
    sm: {
      container: "gap-1.5",
      iconBox: "p-1.5 rounded-lg",
      text: "text-base",
    },
    md: { container: "gap-2", iconBox: "p-2 rounded-xl", text: "text-xl" },
    lg: { container: "gap-3", iconBox: "p-2.5 rounded-2xl", text: "text-2xl" },
  };

  const currentSize = sizeClasses[size];
  const isDark = variant === "dark";

  const content = (
    <div className={cn("flex items-center", currentSize.container, className)}>
      <div
        className={cn(
          currentSize.iconBox,
          "flex items-center justify-center shrink-0 transition-all duration-300",
          isDark
            ? "bg-white/10 text-white"
            : "bg-gradient-to-br from-[#455DD3] via-[#5B6FDB] to-[#17BEBB] text-white shadow-lg shadow-[#455DD3]/25",
        )}
      >
        <JobHuntinMark
          size={size === "sm" ? "sm" : size === "lg" ? "lg" : "md"}
        />
      </div>
      {!iconOnly && (
        <span className={cn("font-black tracking-tight", currentSize.text)}>
          <span className={isDark ? "text-white" : "text-[#2D2A26]"}>Job</span>
          <span className={isDark ? "text-[#7DD3CF]" : "text-[#17BEBB]"}>
            {/* teal - visible on both */}Huntin
          </span>
        </span>
      )}
    </div>
  );

  if (to) {
    return (
      <Link
        to={to}
        onClick={onClick}
        className="inline-block focus:outline-none focus-visible:ring-2 focus-visible:ring-[#455DD3] focus-visible:ring-offset-2 rounded-lg"
        aria-label={iconOnly ? "JobHuntin home" : undefined}
      >
        {content}
      </Link>
    );
  }

  return content;
}

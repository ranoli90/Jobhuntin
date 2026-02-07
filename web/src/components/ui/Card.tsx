import * as React from "react";
import { cn } from "../../lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  shadow?: "lift" | "float" | "none";
  tone?: "shell" | "sunrise" | "lagoon" | "ink";
}

const toneClassMap: Record<NonNullable<CardProps["tone"]>, string> = {
  shell: "bg-[#FFF8F1] border-[#FFE7D4]",
  sunrise: "bg-[#FFE9DF] border-[#FFCDB7]",
  lagoon: "bg-[#E0FFFE] border-[#B0F2F0]",
  ink: "bg-[#101828] border-[#101828] text-white",
};

const shadowClassMap: Record<NonNullable<CardProps["shadow"]>, string> = {
  lift: "shadow-[0_18px_40px_rgba(16,24,40,0.08)]",
  float: "shadow-[0_30px_70px_rgba(16,24,40,0.15)]",
  none: "",
};

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, shadow = "lift", tone = "shell", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-[28px] border p-6 transition-transform duration-300 ease-scoot hover:-translate-y-1",
        toneClassMap[tone],
        shadowClassMap[shadow],
        className,
      )}
      {...props}
    >
      {children}
    </div>
  ),
);
Card.displayName = "Card";

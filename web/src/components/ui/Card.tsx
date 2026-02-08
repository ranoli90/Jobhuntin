import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const cardVariants = cva(
  "rounded-xl border p-6 transition-all duration-200",
  {
    variants: {
      variant: {
        default: "bg-white border-slate-200",
        primary: "bg-primary-50 border-primary-200",
        secondary: "bg-slate-50 border-slate-200",
        ghost: "bg-transparent border-transparent",
      },
      shadow: {
        sm: "shadow-sm",
        md: "shadow-md",
        lg: "shadow-lg",
        none: "",
        lift: "shadow-lg hover:shadow-xl hover:-translate-y-1",
      },
      tone: {
        default: "",
        sunrise: "bg-amber-50/50 border-amber-200",
        lagoon: "bg-cyan-50/50 border-cyan-200",
        mango: "bg-orange-50/50 border-orange-200",
        ink: "bg-slate-900 text-white border-slate-800",
        shell: "bg-slate-50/50 border-slate-200",
      },
    },
    defaultVariants: {
      variant: "default",
      shadow: "sm",
      tone: "default",
    },
  },
);

export interface CardProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof cardVariants> {
  tone?: "default" | "sunrise" | "lagoon" | "mango" | "ink" | "shell";
  shadow?: "sm" | "md" | "lg" | "none" | "lift";
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, variant, shadow, tone, ...props }: CardProps, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, shadow, tone }), className)}
      {...props}
    >
      {children}
    </div>
  ),
);
Card.displayName = "Card";

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
      },
    },
    defaultVariants: {
      variant: "default",
      shadow: "sm",
    },
  },
);

export interface CardProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof cardVariants> {}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, variant, shadow, ...props }: CardProps, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, shadow }), className)}
      {...props}
    >
      {children}
    </div>
  ),
);
Card.displayName = "Card";

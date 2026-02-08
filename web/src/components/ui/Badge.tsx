import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium transition-colors border",
  {
    variants: {
      variant: {
        default: "bg-slate-100 text-slate-700 border-slate-200",
        primary: "bg-primary-100 text-primary-700 border-primary-200",
        success: "bg-success-100 text-success-700 border-success-200",
        warning: "bg-warning-100 text-warning-700 border-warning-200",
        error: "bg-error-100 text-error-700 border-error-200",
        outline: "bg-white text-slate-700 border-slate-300",
        lagoon: "bg-cyan-50 text-cyan-700 border-cyan-200",
        mango: "bg-amber-50 text-amber-700 border-amber-200",
      },
      size: {
        sm: "rounded text-[11px] px-2 py-0.5",
        md: "rounded-md",
        lg: "rounded-lg px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, size, ...props }: BadgeProps, ref) => (
    <span ref={ref} className={cn(badgeVariants({ variant, size }), className)} {...props} />
  ),
);
Badge.displayName = "Badge";

export { badgeVariants };

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full text-xs font-semibold uppercase tracking-wide px-3 py-1 transition-all",
  {
    variants: {
      variant: {
        outline: "bg-white text-[#101828] border border-[#FFD1BE]",
        mango: "bg-[#FFC857] text-[#4D3200] shadow-badge",
        lagoon: "bg-[#17BEBB] text-[#072524] shadow-badge",
        ink: "bg-[#101828] text-white",
      },
    },
    defaultVariants: {
      variant: "outline",
    },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, ...props }: BadgeProps, ref) => (
    <span ref={ref} className={cn(badgeVariants({ variant }), className)} {...props} />
  ),
);
Badge.displayName = "Badge";

export { badgeVariants };

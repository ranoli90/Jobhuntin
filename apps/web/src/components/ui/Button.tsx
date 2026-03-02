import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] relative overflow-hidden group",
  {
    variants: {
      variant: {
        primary:
          "bg-primary-600 text-white shadow-sm hover:bg-primary-500 hover:shadow-md hover:scale-[1.02] active:scale-[0.98] before:absolute before:inset-0 before:bg-white before:opacity-0 before:transition-opacity before:duration-200 hover:before:opacity-10 dark:before:bg-black dark:before:opacity-0 dark:hover:before:opacity-10",
        secondary:
          "bg-primary-700 text-white shadow-sm hover:bg-primary-600 hover:shadow-md hover:scale-[1.02] active:scale-[0.98] before:absolute before:inset-0 before:bg-white before:opacity-0 before:transition-opacity before:duration-200 hover:before:opacity-10 dark:before:bg-black dark:before:opacity-0 dark:hover:before:opacity-10",
        outline:
          "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-400 hover:scale-[1.02] active:scale-[0.98] dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800",
        ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-900 hover:scale-[1.02] active:scale-[0.98] dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100",
        danger: "bg-error-600 text-white shadow-sm hover:bg-error-700 hover:shadow-md hover:scale-[1.02] active:scale-[0.98] before:absolute before:inset-0 before:bg-white before:opacity-0 before:transition-opacity before:duration-200 hover:before:opacity-10",
        success: "bg-success-600 text-white shadow-sm hover:bg-success-700 hover:shadow-md hover:scale-[1.02] active:scale-[0.98] before:absolute before:inset-0 before:bg-white before:opacity-0 before:transition-opacity before:duration-200 hover:before:opacity-10",
        lagoon: "bg-cyan-600 text-white shadow-sm hover:bg-cyan-700 hover:shadow-md hover:scale-[1.02] active:scale-[0.98] before:absolute before:inset-0 before:bg-white before:opacity-0 before:transition-opacity before:duration-200 hover:before:opacity-10",
      },
      size: {
        sm: "h-9 min-h-[44px] px-3 text-sm rounded-md md:min-h-[36px] md:h-9",
        md: "h-11 min-h-[44px] px-4 text-sm rounded-lg md:min-h-0",
        lg: "h-12 min-h-[44px] px-6 text-base rounded-lg",
        icon: "h-11 min-h-[44px] min-w-[44px] p-0 rounded-lg md:min-h-0 md:min-w-0 md:h-10 md:w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size }), className)}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { buttonVariants };

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center font-semibold rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100",
  {
    variants: {
      variant: {
        primary:
          "bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500 shadow-lg shadow-primary-600/20 hover:shadow-primary-600/30 active:scale-95",
        secondary:
          "bg-slate-100 text-slate-900 hover:bg-slate-200 focus-visible:ring-slate-500 active:scale-95",
        ghost: "bg-transparent text-slate-900 hover:bg-slate-100 focus-visible:ring-slate-500 active:scale-95",
        outline: "bg-transparent border-2 border-slate-200 text-slate-700 hover:border-primary-200 hover:bg-primary-50/50 focus-visible:ring-primary-500 active:scale-95",
        danger: "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500 shadow-lg shadow-red-600/20 active:scale-95",
        success: "bg-emerald-600 text-white hover:bg-emerald-700 focus-visible:ring-emerald-500 shadow-lg shadow-emerald-600/20 active:scale-95",
        lagoon: "bg-cyan-600 text-white hover:bg-cyan-700 focus-visible:ring-cyan-500 shadow-lg shadow-cyan-600/20 active:scale-95",
      },
      size: {
        sm: "h-10 px-4 text-xs rounded-xl",
        md: "h-12 px-6 text-sm rounded-xl",
        lg: "h-14 px-8 text-base rounded-2xl",
        xl: "h-16 px-10 text-lg rounded-2xl",
        icon: "h-12 w-12 rounded-xl",
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

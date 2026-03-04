import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center font-semibold rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all duration-200",
  {
    variants: {
      variant: {
        primary:
          "bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500 shadow-xl shadow-indigo-600/20 hover:shadow-indigo-600/30 active:scale-95 transform",
        secondary:
          "bg-slate-100 text-slate-900 hover:bg-slate-200 focus:ring-slate-500 active:scale-95 transform",
        ghost: "bg-transparent text-slate-900 hover:bg-slate-100 focus:ring-slate-500 active:scale-95 transform",
        outline: "bg-transparent border-2 border-slate-200 text-slate-700 hover:border-indigo-200 hover:bg-indigo-50/50 focus:ring-indigo-500 active:scale-95 transform",
        danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
        success: "bg-emerald-600 text-white hover:bg-emerald-700 focus:ring-emerald-500",
        lagoon: "bg-cyan-600 text-white hover:bg-cyan-700 focus:ring-cyan-500",
      },
      size: {
        sm: "h-9 px-4 text-xs rounded-xl",
        md: "h-11 px-5 text-sm rounded-xl",
        lg: "h-14 px-8 text-lg rounded-2xl",
        icon: "h-11 w-11",
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

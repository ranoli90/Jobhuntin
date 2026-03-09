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
          "bg-brand-primary text-white hover:bg-brand-primaryHover focus-visible:ring-brand-primary shadow-sm active:scale-[0.98]",
        secondary:
          "bg-brand-gray text-brand-text hover:bg-brand-border/50 focus-visible:ring-brand-primary active:scale-[0.98]",
        default:
          "bg-brand-primary text-white hover:bg-brand-primaryHover focus-visible:ring-brand-primary shadow-sm active:scale-[0.98]",
        ghost: "bg-transparent text-gray-700 hover:bg-gray-100 focus-visible:ring-gray-300 active:scale-[0.98]",
        outline: "bg-transparent border border-gray-200 text-black hover:bg-gray-50 focus-visible:ring-gray-300 active:scale-[0.98]",
        danger: "bg-red-500 text-white hover:bg-red-600 focus-visible:ring-red-400 shadow-sm active:scale-[0.98]",
        destructive: "bg-red-500 text-white hover:bg-red-600 focus-visible:ring-red-400 shadow-sm active:scale-[0.98]",
        success: "bg-emerald-500 text-white hover:bg-emerald-600 focus-visible:ring-emerald-400 shadow-sm active:scale-[0.98]",
        lagoon: "bg-gray-800 text-white hover:bg-black focus-visible:ring-gray-500 shadow-sm active:scale-[0.98]",
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

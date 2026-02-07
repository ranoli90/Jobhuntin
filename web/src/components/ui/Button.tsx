import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-full font-semibold transition-all duration-300 ease-scoot focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 active:translate-y-[1px]",
  {
    variants: {
      variant: {
        primary:
          "bg-[#FF9C6B] text-white shadow-[0_18px_40px_rgba(255,156,107,0.35)] hover:-translate-y-0.5 hover:shadow-[0_25px_55px_rgba(255,156,107,0.45)] focus-visible:ring-[#FF9C6B]/40",
        secondary:
          "bg-[#101828] text-white hover:bg-[#1d2740]",
        lagoon:
          "bg-[#17BEBB] text-[#0B1C1C] shadow-pill hover:-translate-y-0.5 hover:bg-[#11a6a3]",
        outline:
          "border border-[#FF9C6B] text-[#FF9C6B] bg-transparent hover:bg-[#FFF2E8]",
        ghost: "text-[#101828] hover:bg-[#FFF2E8]",
      },
      size: {
        sm: "px-4 py-2 text-sm",
        md: "px-6 py-2.5 text-base",
        lg: "px-8 py-3 text-lg",
        icon: "h-10 w-10 p-0",
      },
      wobble: {
        true: "hover:-rotate-1",
        false: "",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
      wobble: false,
    },
  },
);

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, wobble, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, wobble }), className)}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { buttonVariants };

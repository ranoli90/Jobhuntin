import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const cardVariants = cva(
  "rounded-xl border p-6 transition-all duration-200",
  {
    variants: {
      variant: {
        default: "bg-white border-brand-border",
        primary: "bg-brand-primary/10 border-brand-primary/20",
        secondary: "bg-brand-gray border-brand-border",
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
        glass: "bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl border-white/50 dark:border-slate-700/50 shadow-xl shadow-slate-200/50 dark:shadow-slate-950/50",
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
  tone?: "default" | "sunrise" | "lagoon" | "mango" | "ink" | "shell" | "glass";
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

export const CardHeader = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`px-6 pt-6 pb-2 ${className}`}>{children}</div>
);

export const CardTitle = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <h3 className={`text-lg font-semibold text-slate-900 ${className}`}>{children}</h3>
);

export const CardContent = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`px-6 pb-6 ${className}`}>{children}</div>
);

export const CardDescription = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <p className={`text-sm text-slate-500 ${className}`}>{children}</p>
);

export const CardFooter = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`px-6 pb-6 pt-2 border-t border-slate-100 ${className}`}>{children}</div>
);

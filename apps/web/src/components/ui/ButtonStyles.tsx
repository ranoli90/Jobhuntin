import React from 'react';
import { cn } from '../../lib/utils';

// Consistent button styles system
export const buttonVariants = {
  // Primary buttons
  primary: "bg-[#2D2A26] text-white font-medium hover:bg-[#4A4540] hover:scale-105 hover:shadow-lg transition-all duration-200",
  
  // Secondary buttons  
  secondary: "border border-[#E9E9E7] text-[#2D2A26] font-medium hover:bg-[#F7F6F3] hover:border-[#2D2A26] hover:scale-105 transition-all duration-200",
  
  // Accent buttons
  accent: "bg-primary-600 text-white font-medium hover:bg-primary-700 hover:scale-105 hover:shadow-lg transition-all duration-200",
  
  // Ghost buttons
  ghost: "text-[#2D2A26] font-medium hover:bg-[#F7F6F3] hover:scale-105 transition-all duration-200",
  // Outline buttons
  outline: "border border-slate-300 bg-white text-slate-700 font-medium hover:bg-slate-50 hover:border-slate-400 transition-all duration-200",
  // Destructive buttons
  destructive: "bg-red-600 text-white font-medium hover:bg-red-700 transition-all duration-200",
  // Lagoon (alias for accent)
  lagoon: "bg-primary-600 text-white font-medium hover:bg-primary-700 hover:scale-105 hover:shadow-lg transition-all duration-200",
  // Default (alias for primary)
  default: "bg-[#2D2A26] text-white font-medium hover:bg-[#4A4540] hover:scale-105 hover:shadow-lg transition-all duration-200",
};

export const buttonSizes = {
  sm: "h-10 px-4 text-sm",
  md: "h-12 px-6 text-base", 
  lg: "h-14 px-8 text-lg",
  xl: "h-16 px-10 text-xl",
  icon: "h-10 w-10 p-0",
};

export const buttonRadius = {
  sm: "rounded-md",
  md: "rounded-lg", 
  lg: "rounded-xl",
  xl: "rounded-2xl",
};

// Consistent card styles system
export const cardVariants = {
  default: "bg-white border border-[#E9E9E7] rounded-xl shadow-sm",
  elevated: "bg-white border border-[#E9E9E7] rounded-xl shadow-lg",
  interactive: "bg-white border border-[#E9E9E7] rounded-xl hover:border-[#2D2A26] hover:shadow-xl hover:scale-105 transition-all duration-300 cursor-pointer",
  dark: "bg-[#2D2A26] text-white rounded-xl shadow-xl",
};

export const cardPadding = {
  sm: "p-4",
  md: "p-6",
  lg: "p-8", 
  xl: "p-10",
  xxl: "p-12",
  xxxl: "p-16",
};

// Reusable button component
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof buttonVariants;
  size?: keyof typeof buttonSizes;
  radius?: keyof typeof buttonRadius;
  children: React.ReactNode;
  /** When true, merge props onto child element instead of rendering button */
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      radius = 'lg',
      className = '',
      children,
      asChild,
      ...props
    },
    ref
  ) => {
    const classes = cn(
      buttonVariants[variant],
      buttonSizes[size],
      buttonRadius[radius],
      className
    );
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement<{ className?: string; ref?: React.Ref<unknown> }>, {
        className: cn(classes, (children as React.ReactElement).props.className),
        ref,
      });
    }
    return (
      <button ref={ref} className={classes} {...props}>
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

// Reusable card component  
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof cardVariants;
  padding?: keyof typeof cardPadding;
  className?: string;
  children: React.ReactNode;
  /** Passthrough for design tokens (e.g. tone, shadow) - merged into className */
  tone?: string;
  shadow?: string;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      padding = 'lg',
      className = '',
      children,
      tone,
      shadow,
      ...rest
    },
    ref
  ) => (
    <div
      ref={ref}
      className={cn(cardVariants[variant], cardPadding[padding], tone, shadow, className)}
      {...rest}
    >
      {children}
    </div>
  )
);
Card.displayName = 'Card';

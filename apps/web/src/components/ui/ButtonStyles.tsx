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
};

export const buttonSizes = {
  sm: "h-10 px-4 text-sm",
  md: "h-12 px-6 text-base", 
  lg: "h-14 px-8 text-lg",
  xl: "h-16 px-10 text-xl",
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
}

export function Button({
  variant = 'primary',
  size = 'md', 
  radius = 'lg',
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        buttonVariants[variant],
        buttonSizes[size], 
        buttonRadius[radius],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

// Reusable card component  
interface CardProps {
  variant?: keyof typeof cardVariants;
  padding?: keyof typeof cardPadding;
  className?: string;
  children: React.ReactNode;
}

export function Card({
  variant = 'default',
  padding = 'lg',
  className = '',
  children
}: CardProps) {
  return (
    <div className={cn(cardVariants[variant], cardPadding[padding], className)}>
      {children}
    </div>
  );
}

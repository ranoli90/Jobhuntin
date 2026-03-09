import React from 'react';
import { cn } from '@/lib/utils';

export interface CardStylesProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'outlined' | 'filled';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  clickable?: boolean;
}

export const CardStyles: React.FC<CardStylesProps> = ({
  children,
  className,
  variant = 'default',
  size = 'md',
  padding = 'md',
  hover = false,
  clickable = false,
}) => {
  const baseClasses = 'relative overflow-hidden transition-all duration-200';
  
  const variantClasses = {
    default: 'bg-white border border-gray-200',
    elevated: 'bg-white border border-gray-200 shadow-lg',
    outlined: 'bg-white border-2 border-gray-300',
    filled: 'bg-gray-50 border border-gray-200',
  };
  
  const sizeClasses = {
    sm: 'rounded-lg',
    md: 'rounded-xl',
    lg: 'rounded-2xl',
    xl: 'rounded-3xl',
  };
  
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-10',
  };
  
  const hoverClasses = hover ? 'hover:shadow-xl hover:border-gray-300' : '';
  const clickableClasses = clickable ? 'cursor-pointer active:scale-[0.98]' : '';
  
  return (
    <div
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        paddingClasses[padding],
        hoverClasses,
        clickableClasses,
        className
      )}
    >
      {children}
    </div>
  );
};

export default CardStyles;

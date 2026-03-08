import React from 'react';
import { cn } from '../../lib/utils';

// Skeleton loader components for loading states

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'button';
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export function Skeleton({ className, variant = 'rectangular', size = 'md' }: SkeletonProps) {
  const variants = {
    text: 'h-4 w-full',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
    button: 'rounded-lg h-10 w-24',
  };

  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6', 
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  return (
    <div
      className={cn(
        'animate-pulse bg-[#E9E9E7]',
        variants[variant],
        size !== 'md' && variant === 'circular' && sizes[size],
        className
      )}
    />
  );
}

// Card skeleton loader
export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="bg-white border border-[#E9E9E7] rounded-xl p-8 shadow-sm">
      <div className="space-y-4">
        <Skeleton variant="circular" size="lg" />
        <div className="space-y-2">
          <Skeleton variant="text" />
          <Skeleton variant="text" className="w-3/4" />
        </div>
        <div className="space-y-2">
          {Array.from({ length: lines }).map((_, i) => (
            <Skeleton key={i} variant="text" className={i === lines - 1 ? 'w-2/3' : ''} />
          ))}
        </div>
      </div>
    </div>
  );
}

// Feature card skeleton
export function FeatureCardSkeleton() {
  return (
    <div className="p-16 bg-white rounded-xl border border-[#E9E9E7] shadow-sm">
      <div className="space-y-6">
        <Skeleton variant="rectangular" size="xl" className="h-16 w-16" />
        <Skeleton variant="text" className="h-8 w-3/4" />
        <div className="space-y-2">
          <Skeleton variant="text" />
          <Skeleton variant="text" className="w-4/5" />
          <Skeleton variant="text" className="w-3/5" />
        </div>
      </div>
    </div>
  );
}

// Button skeleton loader
export function ButtonSkeleton({ width = 'w-24' }: { width?: string }) {
  return (
    <div className={cn('animate-pulse bg-[#E9E9E7] rounded-lg h-10', width)} />
  );
}

// Progress indicator
interface ProgressProps {
  value?: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
}

export function Progress({ value = 0, max = 100, className = '', showLabel = false }: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  
  return (
    <div className={cn('w-full space-y-2', className)}>
      {showLabel && (
        <div className="flex justify-between text-sm text-[#5A5653]">
          <span>Progress</span>
          <span>{Math.round(percentage)}%</span>
        </div>
      )}
      <div className="w-full bg-[#E9E9E7] rounded-full h-2 overflow-hidden">
        <div 
          className="bg-[#2D2A26] h-full rounded-full transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// Loading spinner
export function Spinner({ size = 'md', className = '' }: { size?: 'sm' | 'md' | 'lg'; className?: string }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className={cn('animate-spin', sizes[size], className)}>
      <svg
        className="w-full h-full text-[#2D2A26]"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        ></circle>
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
    </div>
  );
}

// Loading overlay
interface LoadingOverlayProps {
  isLoading: boolean;
  children: React.ReactNode;
  message?: string;
}

export function LoadingOverlay({ isLoading, children, message = 'Loading...' }: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center rounded-xl">
          <div className="text-center space-y-4">
            <Spinner size="lg" />
            <p className="text-[#5A5653] font-medium">{message}</p>
          </div>
        </div>
      )}
    </div>
  );
}

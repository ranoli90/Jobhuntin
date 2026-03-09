import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  error?: boolean;
  onClear?: () => void;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, icon, error, onClear, ...props }, ref) => {
    const inputClasses = cn(
      "flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
      error && "border-red-500 focus-visible:ring-red-500",
      icon && "pl-10",
      className
    );
    const input = (
      <input type={type} className={inputClasses} ref={ref} {...props} />
    );
    if (icon) {
      return (
        <div className="relative flex w-full items-center">
          <span className="absolute left-3 text-slate-400">{icon}</span>
          {input}
        </div>
      );
    }
    return input;
  }
);
Input.displayName = "Input";

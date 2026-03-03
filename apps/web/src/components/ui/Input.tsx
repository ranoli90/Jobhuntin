import * as React from "react"
import { cn } from "../../lib/utils"

import { X, Eye, EyeOff } from "lucide-react"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode
  error?: boolean
  helperText?: string
  onClear?: () => void
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, icon, error, helperText, onClear, value, ...props }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false)
    const isPassword = type === "password"
    const inputType = isPassword ? (showPassword ? "text" : "password") : type

    return (
      <div className="relative group">
        {icon && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary-500 transition-colors duration-200 pointer-events-none">
            {icon}
          </div>
        )}
        <input
          type={inputType}
          value={value}
          className={cn(
            "flex w-full rounded-2xl border border-gray-100 bg-white/50 px-4 py-4 text-base ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/30 focus-visible:ring-offset-2 focus-visible:border-primary-500 disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-slate-100 transition-all duration-200 font-medium text-slate-900",
            icon && "pl-12",
            (onClear || isPassword) && "pr-12",
            error && "border-red-500 focus-visible:ring-red-500/10 focus-visible:border-red-500 bg-red-50/50",
            className
          )}
          ref={ref}
          {...props}
        />
        {isPassword && !onClear && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary-500 p-1 rounded-full hover:bg-slate-100 transition-all duration-200"
            aria-label={showPassword ? "Hide password" : "Show password"}
            aria-pressed={showPassword}
            role="switch"
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" aria-hidden />
            ) : (
              <Eye className="h-4 w-4" aria-hidden />
            )}
          </button>
        )}
        {onClear && value && !isPassword && (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-500 p-1 rounded-full hover:bg-red-50 transition-all duration-200"
            aria-label="Clear input"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        )}
        {helperText && (
          <p className={cn(
            "mt-1 text-xs",
            error ? "text-red-500" : "text-gray-500"
          )}>
            {helperText}
          </p>
        )}
      </div>
    )
  }
)
Input.displayName = "Input"

export { Input }

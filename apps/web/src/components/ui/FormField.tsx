import * as React from "react";
import { cn } from "../../lib/utils";
import { Label } from "./Label";

export interface FormFieldProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * The label text for the field
   */
  label?: string;
  /**
   * The HTML ID for the input element
   */
  htmlFor?: string;
  /**
   * Error message to display
   */
  error?: string;
  /**
   * Helper text to display below the input
   */
  helperText?: string;
  /**
   * Whether the field is required (adds asterisk)
   */
  required?: boolean;
  /**
   * Whether to show error state styling
   */
  showError?: boolean;
  /**
   * Optional icon to display before the input
   */
  icon?: React.ReactNode;
  /**
   * Position of the icon
   */
  iconPosition?: "left" | "right";
  /**
   * The input element
   */
  children?: React.ReactNode;
}

/**
 * FormField - A wrapper component that provides consistent styling for form fields
 * with label, input, error display, and helper text
 */
export const FormField = React.forwardRef<HTMLDivElement, FormFieldProps>(
  (
    {
      className,
      label,
      htmlFor,
      error,
      helperText,
      required,
      showError = true,
      icon,
      iconPosition = "left",
      children,
      ...props
    },
    ref,
  ) => {
    const hasError = showError && !!error;
    const errorId = htmlFor ? `${htmlFor}-error` : undefined;
    const helperId = htmlFor ? `${htmlFor}-helper` : undefined;

    return (
      <div
        ref={ref}
        className={cn("space-y-2", className)}
        {...props}
      >
        {label && (
          <Label
            htmlFor={htmlFor}
            className={cn(hasError && "text-red-600")}
          >
            {label}
            {required && (
              <span className="text-red-500 ml-1" aria-hidden="true">
                *
              </span>
            )}
          </Label>
        )}

        {children}

        {(error || helperText) && (
          <p
            id={hasError ? errorId : helperId}
            className={cn(
              "text-sm",
              hasError
                ? "text-red-500"
                : "text-gray-500",
            )}
            role={hasError ? "alert" : undefined}
            aria-live={hasError ? "polite" : undefined}
          >
            {hasError ? error : helperText}
          </p>
        )}
      </div>
    );
  },
);

FormField.displayName = "FormField";

/**
 * Hook for managing form field state
 */
export function useFormField<T extends string = string>({
  name,
  initialValue = "" as T,
  validate,
  validateOn = "blur" as const,
}: {
  name: string;
  initialValue?: T;
  validate?: (value: T) => string | null;
  validateOn?: "blur" | "change" | "submit" | "all";
}) {
  const [value, setValue] = React.useState<T>(initialValue);
  const [error, setError] = React.useState<string | null>(null);
  const [touched, setTouched] = React.useState(false);

  const validateField = React.useCallback(
    (val: T): string | null => {
      if (validate) {
        return validate(val);
      }
      return null;
    },
    [validate],
  );

  const handleChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const newValue = e.target.value as T;
      setValue(newValue);

      if (validateOn === "change" || validateOn === "all") {
        const validationError = validateField(newValue);
        setError(validationError);
      }
    },
    [validateField, validateOn],
  );

  const handleBlur = React.useCallback(() => {
    setTouched(true);
    if (validateOn === "blur" || validateOn === "all") {
      const validationError = validateField(value);
      setError(validationError);
    }
  }, [validateField, validateOn, value]);

  const reset = React.useCallback((newValue?: T) => {
    setValue(newValue ?? (initialValue as T));
    setError(null);
    setTouched(false);
  }, [initialValue]);

  return {
    value,
    error,
    touched,
    isError: touched && !!error,
    handleChange,
    handleBlur,
    setValue,
    setError,
    reset,
  };
}

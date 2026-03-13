import * as React from "react";
import { cn } from "../../lib/utils";
import { Input, InputProps } from "./Input";
import { FormField, useFormField } from "./FormField";

export interface FormInputProps extends Omit<InputProps, "error" | "onChange" | "value"> {
  /**
   * The name of the input
   */
  name: string;
  /**
   * Label text
   */
  label?: string;
  /**
   * HTML ID for the input
   */
  htmlFor?: string;
  /**
   * Whether the field is required
   */
  required?: boolean;
  /**
   * Validation function
   */
  validate?: (value: string) => string | null;
  /**
   * When to validate
   */
  validateOn?: "blur" | "change" | "submit" | "all";
  /**
   * Initial value
   */
  initialValue?: string;
  /**
   * Error message (for external error handling)
   */
  error?: string;
  /**
   * Helper text to display below the input
   */
  helperText?: string;
  /**
   * Callback when value changes
   */
  onChange?: (value: string) => void;
  /**
   * Callback when field is validated
   */
  onValidate?: (isValid: boolean, error: string | null) => void;
}

/**
 * FormInput - Enhanced input with built-in validation
 */
export const FormInput = React.forwardRef<HTMLInputElement, FormInputProps>(
  (
    {
      name,
      label,
      htmlFor,
      required,
      validate,
      validateOn = "blur",
      initialValue = "",
      error: externalError,
      helperText,
      onChange,
      onValidate,
      className,
      id,
      ...props
    },
    ref,
  ) => {
    const inputId = id || htmlFor || name;
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;

    const {
      value,
      error,
      isError,
      handleChange,
      handleBlur,
      setValue,
      setError,
      reset,
    } = useFormField({
      name,
      initialValue,
      validate,
      validateOn,
    });

    // Combine internal and external errors
    const displayError = externalError || error;
    const hasError = !!displayError;

    const handleInputChange = React.useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value;
        setValue(newValue as never);
        onChange?.(newValue);
      },
      [setValue, onChange],
    );

    const handleInputBlur = React.useCallback(
      (e: React.FocusEvent<HTMLInputElement>) => {
        handleBlur();
        if (validate) {
          const validationError = validate(value);
          onValidate?.(!validationError, validationError);
        }
        props.onBlur?.(e);
      },
      [handleBlur, validate, value, onValidate, props.onBlur],
    );

    // Expose methods via ref
    React.useImperativeHandle(
      ref,
      () => ({
        ...(Object.create({
          get value() {
            return value;
          },
          set value(val: string) {
            setValue(val as never);
          },
          focus: () => {
            const input = document.getElementById(inputId);
            input?.focus();
          },
          blur: () => {
            const input = document.getElementById(inputId);
            input?.blur();
          },
        })),
      }),
      [value, setValue, inputId],
    );

    return (
      <FormField
        label={label}
        htmlFor={inputId}
        required={required}
        error={displayError}
        helperText={!hasError ? helperText : undefined}
        showError={true}
      >
        <Input
          {...props}
          id={inputId}
          name={name}
          ref={ref}
          value={value}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          error={hasError}
          aria-invalid={hasError}
          aria-describedby={hasError ? errorId : helperText ? helperId : undefined}
          aria-required={required}
          className={className}
        />
      </FormField>
    );
  },
);

FormInput.displayName = "FormInput";

/**
 * Create a configured FormInput with preset validations
 */
export function createFormInput(config: {
  name: string;
  label: string;
  required?: boolean;
  type?: "email" | "url" | "tel" | "text";
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  patternMessage?: string;
  validateOn?: "blur" | "change" | "submit" | "all";
}) {
  const { name, label, required, type, minLength, maxLength, pattern, patternMessage, validateOn } = config;

  const validate = (value: string): string | null => {
    if (required && !value.trim()) {
      return `${label} is required`;
    }

    if (value) {
      if (minLength && value.length < minLength) {
        return `${label} must be at least ${minLength} characters`;
      }

      if (maxLength && value.length > maxLength) {
        return `${label} must be no more than ${maxLength} characters`;
      }

      if (pattern && !pattern.test(value)) {
        return patternMessage || `Invalid ${label.toLowerCase()} format`;
      }

      // Type-specific validation
      if (type === "email" && value) {
        const emailRegex = /^[\w!#$%&'*+./=?^`{|}~-]+@(?:[\dA-Za-z](?:[\dA-Za-z-]{0,61}[\dA-Za-z])?\.)+[\dA-Za-z](?:[\dA-Za-z-]{0,61}[\dA-Za-z])?$/;
        if (!emailRegex.test(value)) {
          return "Please enter a valid email address";
        }
      }

      if (type === "url" && value) {
        try {
          const parsed = new URL(value);
          if (!["http:", "https:"].includes(parsed.protocol)) {
            return "URL must use HTTP or HTTPS protocol";
          }
        } catch {
          return "Please enter a valid URL";
        }
      }

      if (type === "tel" && value) {
        const phoneRegex = /^\+?[\d\s()-]{10,}$/;
        if (!phoneRegex.test(value)) {
          return "Please enter a valid phone number";
        }
      }
    }

    return null;
  };

  return {
    name,
    label,
    required,
    validate,
    validateOn: validateOn || "blur",
    type: type || "text",
    minLength,
    maxLength,
    pattern,
  };
}

/**
 * Preset configurations for common form fields
 */
export const FormInputPresets = {
  email: (name: string, label: string = "Email", required: boolean = true) =>
    createFormInput({
      name,
      label,
      required,
      type: "email",
      validateOn: "blur",
    }),

  password: (name: string, label: string = "Password", required: boolean = true) =>
    createFormInput({
      name,
      label,
      required,
      minLength: 10,
      maxLength: 128,
      validateOn: "blur",
    }),

  phone: (name: string, label: string = "Phone Number", required: boolean = false) =>
    createFormInput({
      name,
      label,
      required,
      type: "tel",
      minLength: 10,
      maxLength: 15,
      validateOn: "blur",
    }),

  url: (name: string, label: string = "Website", required: boolean = false) =>
    createFormInput({
      name,
      label,
      required,
      type: "url",
      validateOn: "blur",
    }),

  name: (name: string, label: string = "Name", required: boolean = true) =>
    createFormInput({
      name,
      label,
      required,
      minLength: 2,
      maxLength: 100,
      pattern: /^[\s'A-Za-z\-]+$/,
      patternMessage: "Name can only contain letters, spaces, hyphens, and apostrophes",
      validateOn: "blur",
    }),

  requiredText: (name: string, label: string, minLength?: number, maxLength?: number) =>
    createFormInput({
      name,
      label,
      required: true,
      minLength,
      maxLength,
      validateOn: "blur",
    }),

  optionalText: (name: string, label: string, minLength?: number, maxLength?: number) =>
    createFormInput({
      name,
      label,
      required: false,
      minLength,
      maxLength,
      validateOn: "blur",
    }),
};

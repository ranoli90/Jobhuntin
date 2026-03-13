import * as React from "react";
import { cn } from "../../lib/utils";
import { Eye, EyeOff, CheckCircle, XCircle } from "lucide-react";
import { Input, InputProps } from "./Input";
import { FormField } from "./FormField";
import {
  PasswordStrength,
  PasswordStrengthCalculator,
  Validator,
} from "../../lib/validation";

export interface PasswordInputProps extends Omit<InputProps, "type" | "error"> {
  /**
   * The name of the input
   */
  name: string;
  /**
   * Label text
   */
  label?: string;
  /**
   * Whether the field is required
   */
  required?: boolean;
  /**
   * Show password strength meter
   */
  showStrength?: boolean;
  /**
   * Minimum password length requirement
   */
  minLength?: number;
  /**
   * Maximum password length
   */
  maxLength?: number;
  /**
   * Whether to show confirmation field
   */
  showConfirmation?: boolean;
  /**
   * Label for confirmation field
   */
  confirmationLabel?: string;
  /**
   * Value of the confirmation field (if showing)
   */
  confirmationValue?: string;
  /**
   * Callback when confirmation value changes
   */
  onConfirmationChange?: (value: string) => void;
  /**
   * Error message for confirmation mismatch
   */
  confirmationError?: string;
  /**
   * Custom validation function
   */
  validatePassword?: (password: string) => { isValid: boolean; errors: string[] };
  /**
   * Helper text
   */
  helperText?: string;
  /**
   * Callback when value changes
   */
  onChange?: (value: string) => void;
}

interface PasswordRequirement {
  label: string;
  test: (password: string) => boolean;
}

/**
 * Default password requirements
 */
const DEFAULT_REQUIREMENTS: PasswordRequirement[] = [
  { label: "At least 10 characters", test: (p) => p.length >= 10 },
  { label: "One lowercase letter", test: (p) => /[a-z]/.test(p) },
  { label: "One uppercase letter", test: (p) => /[A-Z]/.test(p) },
  { label: "One number", test: (p) => /\d/.test(p) },
  { label: "One special character", test: (p) => /[!\"#$%&'()*+,./:;<=>?@[\\\]^_{|}\\-]/.test(p) },
];

/**
 * PasswordInput - Password field with show/hide toggle and optional strength meter
 */
export const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  (
    {
      name,
      label,
      required,
      showStrength = true,
      minLength = 10,
      maxLength = 128,
      showConfirmation = false,
      confirmationLabel = "Confirm Password",
      confirmationValue,
      onConfirmationChange,
      confirmationError,
      validatePassword,
      helperText,
      onChange,
      value,
      className,
      id,
      ...props
    },
    ref,
  ) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const [showConfirmationPassword, setShowConfirmationPassword] = React.useState(false);
    const [touched, setTouched] = React.useState(false);

    const inputId = id || name;
    const confirmationId = `${name}-confirm`;
    const errorId = `${inputId}-error`;
    const requirementsId = `${inputId}-requirements`;

    const passwordValue = value as string || "";
    const passwordStrength = React.useMemo(
      () => PasswordStrengthCalculator.calculate(passwordValue),
      [passwordValue],
    );

    // Custom validation if provided
    const validationResult = React.useMemo(() => {
      if (validatePassword && passwordValue) {
        return validatePassword(passwordValue);
      }
      // Use default Validator otherwise
      if (passwordValue) {
        const result = Validator.password(passwordValue);
        return { isValid: result.isValid, errors: result.errors };
      }
      return { isValid: true, errors: [] };
    }, [passwordValue, validatePassword]);

    const error = !validationResult.isValid && touched
      ? validationResult.errors[0]
      : undefined;

    const handleChange = React.useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange?.(e.target.value);
        props.onChange?.(e);
      },
      [onChange, props.onChange],
    );

    const handleBlur = React.useCallback(() => {
      setTouched(true);
      props.onBlur?.(new FocusEvent("blur", { bubbles: true }));
    }, [props.onBlur]);

    const requirements = showStrength ? DEFAULT_REQUIREMENTS : [];

    return (
      <div className="space-y-4">
        <FormField
          label={label || "Password"}
          htmlFor={inputId}
          required={required}
          error={error}
          showError={touched}
          helperText={
            !showStrength
              ? helperText
              : `Password must meet ${requirements.length} requirements`
          }
        >
          <div className="relative">
            <Input
              {...props}
              id={inputId}
              name={name}
              ref={ref}
              type={showPassword ? "text" : "password"}
              value={value}
              onChange={handleChange}
              onBlur={handleBlur}
              error={!!error && touched}
              autoComplete="new-password"
              aria-invalid={!!error && touched}
              aria-describedby={showStrength ? requirementsId : undefined}
              className={cn("pr-12", className)}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-primary-500 min-h-[44px] min-w-[44px] p-2 rounded-full hover:bg-slate-100 transition-all duration-200 flex items-center justify-center"
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" aria-hidden />
              ) : (
                <Eye className="h-4 w-4" aria-hidden />
              )}
            </button>
          </div>
        </FormField>

        {/* Password Strength Meter */}
        {showStrength && passwordValue && (
          <div className="space-y-2" id={requirementsId}>
            {/* Strength Bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-gray-600">
                <span>Password Strength</span>
                <span
                  className={cn(
                    "font-medium",
                    passwordStrength.strength === "weak" && "text-red-500",
                    passwordStrength.strength === "fair" && "text-yellow-500",
                    passwordStrength.strength === "good" && "text-blue-500",
                    passwordStrength.strength === "strong" && "text-green-500",
                  )}
                >
                  {PasswordStrengthCalculator.getStrengthLabel(passwordStrength.strength)}
                </span>
              </div>
              <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full transition-all duration-300",
                    PasswordStrengthCalculator.getStrengthColor(passwordStrength.strength),
                  )}
                  style={{
                    width: `${(passwordStrength.score / 10) * 100}%`,
                  }}
                  role="progressbar"
                  aria-valuenow={passwordStrength.score}
                  aria-valuemin={0}
                  aria-valuemax={10}
                  aria-label={`Password strength: ${passwordStrength.strength}`}
                />
              </div>
            </div>

            {/* Requirements List */}
            {touched && (
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-sm" aria-label="Password requirements">
                {requirements.map((req, index) => {
                  const passed = req.test(passwordValue);
                  return (
                    <li
                      key={index}
                      className={cn(
                        "flex items-center gap-2",
                        passed ? "text-green-600" : "text-gray-500",
                      )}
                    >
                      {passed ? (
                        <CheckCircle className="h-4 w-4 flex-shrink-0" aria-hidden />
                      ) : (
                        <XCircle className="h-4 w-4 flex-shrink-0" aria-hidden />
                      )}
                      <span>{req.label}</span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}

        {/* Confirmation Field */}
        {showConfirmation && (
          <FormField
            label={confirmationLabel}
            htmlFor={confirmationId}
            required={required}
            error={confirmationError}
            showError={!!confirmationError}
          >
            <div className="relative">
              <Input
                id={confirmationId}
                name={`${name}_confirmation`}
                type={showConfirmationPassword ? "text" : "password"}
                value={confirmationValue}
                onChange={(e) => onConfirmationChange?.(e.target.value)}
                error={!!confirmationError}
                autoComplete="new-password"
                aria-invalid={!!confirmationError}
                aria-describedby={confirmationError ? `${confirmationId}-error` : undefined}
                className={cn("pr-12")}
              />
              <button
                type="button"
                onClick={() => setShowConfirmationPassword(!showConfirmationPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-primary-500 min-h-[44px] min-w-[44px] p-2 rounded-full hover:bg-slate-100 transition-all duration-200 flex items-center justify-center"
                aria-label={showConfirmationPassword ? "Hide password" : "Show password"}
                aria-pressed={showConfirmationPassword}
              >
                {showConfirmationPassword ? (
                  <EyeOff className="h-4 w-4" aria-hidden />
                ) : (
                  <Eye className="h-4 w-4" aria-hidden />
                )}
              </button>
            </div>
          </FormField>
        )}
      </div>
    );
  },
);

PasswordInput.displayName = "PasswordInput";

/**
 * Hook for managing password field with confirmation
 */
export function usePasswordField(options?: {
  name?: string;
  minLength?: number;
  validateOn?: "blur" | "change" | "all";
}) {
  const { minLength = 10, validateOn = "blur" } = options || {};

  const [password, setPassword] = React.useState("");
  const [confirmation, setConfirmation] = React.useState("");
  const [touched, setTouched] = React.useState({ password: false, confirmation: false });

  const passwordResult = React.useMemo(() => {
    if (!password) return { isValid: true, errors: [], warnings: [] };
    return Validator.password(password);
  }, [password]);

  const confirmationError = React.useMemo(() => {
    if (!touched.confirmation || !confirmation) return null;
    if (password !== confirmation) {
      return "Passwords do not match";
    }
    return null;
  }, [password, confirmation, touched.confirmation]);

  const isValid = passwordResult.isValid && !confirmationError;

  const handlePasswordChange = React.useCallback((value: string) => {
    setPassword(value);
    if (validateOn === "change" || validateOn === "all") {
      setTouched((prev) => ({ ...prev, password: true }));
    }
  }, [validateOn]);

  const handleConfirmationChange = React.useCallback((value: string) => {
    setConfirmation(value);
    if (validateOn === "change" || validateOn === "all") {
      setTouched((prev) => ({ ...prev, confirmation: true }));
    }
  }, [validateOn]);

  const handleBlur = React.useCallback((field: "password" | "confirmation") => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }, []);

  const reset = React.useCallback(() => {
    setPassword("");
    setConfirmation("");
    setTouched({ password: false, confirmation: false });
  }, []);

  return {
    password,
    confirmation,
    passwordError: touched.password && !passwordResult.isValid ? passwordResult.errors[0] : undefined,
    confirmationError,
    isValid,
    strength: PasswordStrengthCalculator.calculate(password),
    handlePasswordChange,
    handleConfirmationChange,
    handleBlur,
    reset,
  };
}

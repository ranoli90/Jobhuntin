/**
 * Application Error Types and Helper Functions
 * 
 * Provides detailed error explanations for application failures,
 * including user-friendly messages and troubleshooting suggestions.
 */

/**
 * Error codes for application failures
 * These map to specific failure scenarios that can occur during job applications
 */
export enum ApplicationErrorCode {
  CAPTCHA_FAILED = "CAPTCHA_FAILED",
  FORM_CHANGED = "FORM_CHANGED",
  RATE_LIMITED = "RATE_LIMITED",
  LOGIN_REQUIRED = "LOGIN_REQUIRED",
  SESSION_EXPIRED = "SESSION_EXPIRED",
  NETWORK_ERROR = "NETWORK_ERROR",
  UNKNOWN_ERROR = "UNKNOWN_ERROR",
}

/**
 * Structure for detailed error information
 */
export interface ApplicationErrorDetail {
  code: ApplicationErrorCode;
  title: string;
  description: string;
  troubleshooting: string[];
  isRetryable: boolean;
}

/**
 * Maps error codes to detailed error information
 */
const errorDetails: Record<ApplicationErrorCode, ApplicationErrorDetail> = {
  [ApplicationErrorCode.CAPTCHA_FAILED]: {
    code: ApplicationErrorCode.CAPTCHA_FAILED,
    title: "CAPTCHA Verification Failed",
    description: "The automated security check could not be completed. The employer's website detected unusual activity.",
    troubleshooting: [
      "The employer uses advanced bot detection that our system cannot bypass",
      "This may be a temporary issue - try applying again in a few hours",
      "Consider applying directly on the company's careers page",
      "Some companies block automated applications - manual application may be needed",
    ],
    isRetryable: true,
  },
  [ApplicationErrorCode.FORM_CHANGED]: {
    code: ApplicationErrorCode.FORM_CHANGED,
    title: "Application Form Changed",
    description: "The job application form on the employer's website has been updated or modified since we last accessed it.",
    troubleshooting: [
      "The company has updated their application process",
      "Our AI agent will need to adapt to the new form structure",
      "The application has been queued for retry with the updated form",
      "This usually resolves automatically on the next attempt",
    ],
    isRetryable: true,
  },
  [ApplicationErrorCode.RATE_LIMITED]: {
    code: ApplicationErrorCode.RATE_LIMITED,
    title: "Too Many Requests",
    description: "The employer has temporarily blocked further applications due to rate limiting. This usually happens when too many applications come from the same source.",
    troubleshooting: [
      "The company's application system is receiving too many submissions",
      "We've automatically spaced out retry attempts",
      "This is usually a temporary cooldown period",
      "The application will be retried automatically when the limit lifts",
    ],
    isRetryable: true,
  },
  [ApplicationErrorCode.LOGIN_REQUIRED]: {
    code: ApplicationErrorCode.LOGIN_REQUIRED,
    title: "Login Required",
    description: "This position requires an existing account with the employer. We couldn't access the application without valid credentials.",
    troubleshooting: [
      "This job posting requires candidates to have an existing account",
      "You may need to create an account on the company's portal first",
      "Check if the job posting mentions required login credentials",
      "Consider applying directly through the company's website with your credentials",
    ],
    isRetryable: false,
  },
  [ApplicationErrorCode.SESSION_EXPIRED]: {
    code: ApplicationErrorCode.SESSION_EXPIRED,
    title: "Session Timed Out",
    description: "The session with the employer's website expired before the application could be submitted. This can happen with longer application processes.",
    troubleshooting: [
      "The application session expired during submission",
      "Our system will automatically retry with a fresh session",
      "This commonly happens with multi-step application forms",
      "The retry should complete successfully",
    ],
    isRetryable: true,
  },
  [ApplicationErrorCode.NETWORK_ERROR]: {
    code: ApplicationErrorCode.NETWORK_ERROR,
    title: "Network Connection Issue",
    description: "A network error occurred while trying to submit the application. This could be due to connectivity issues or server problems.",
    troubleshooting: [
      "There was a temporary network connectivity issue",
      "Our system will automatically retry the submission",
      "Check your internet connection if this persists",
      "This is often a temporary server issue on the employer's side",
    ],
    isRetryable: true,
  },
  [ApplicationErrorCode.UNKNOWN_ERROR]: {
    code: ApplicationErrorCode.UNKNOWN_ERROR,
    title: "Application Failed",
    description: "An unexpected error occurred while submitting your application. Our team has been notified and will investigate.",
    troubleshooting: [
      "An unexpected error occurred during application submission",
      "The application has been logged for review",
      "Our team will analyze what happened and attempt recovery",
      "You can try applying again if needed",
    ],
    isRetryable: true,
  },
};

/**
 * Get error details for a given error code
 */
export function getErrorDetail(code: ApplicationErrorCode): ApplicationErrorDetail {
  return errorDetails[code] ?? errorDetails[ApplicationErrorCode.UNKNOWN_ERROR];
}

/**
 * Get user-friendly error title
 */
export function getErrorTitle(code: ApplicationErrorCode): string {
  return getErrorDetail(code).title;
}

/**
 * Get user-friendly error description
 */
export function getErrorDescription(code: ApplicationErrorCode): string {
  return getErrorDetail(code).description;
}

/**
 * Get troubleshooting suggestions for an error
 */
export function getTroubleshootingSuggestions(code: ApplicationErrorCode): string[] {
  return getErrorDetail(code).troubleshooting;
}

/**
 * Check if an error is retryable
 */
export function isErrorRetryable(code: ApplicationErrorCode): boolean {
  return getErrorDetail(code).isRetryable;
}

/**
 * Parse error code from API response or error object
 * Falls back to UNKNOWN_ERROR if the code is not recognized
 */
export function parseErrorCode(error: unknown): ApplicationErrorCode {
  if (!error) {
    return ApplicationErrorCode.UNKNOWN_ERROR;
  }

  // Try to extract error code from various error formats
  const errorString = String(error).toUpperCase();
  
  // Check for known error patterns in the error message
  if (errorString.includes("CAPTCHA") || errorString.includes("BOT")) {
    return ApplicationErrorCode.CAPTCHA_FAILED;
  }
  if (errorString.includes("FORM") && errorString.includes("CHANGE")) {
    return ApplicationErrorCode.FORM_CHANGED;
  }
  if (errorString.includes("RATE") || errorString.includes("429")) {
    return ApplicationErrorCode.RATE_LIMITED;
  }
  if (errorString.includes("LOGIN") || errorString.includes("AUTH")) {
    return ApplicationErrorCode.LOGIN_REQUIRED;
  }
  if (errorString.includes("SESSION") || errorString.includes("EXPIRE")) {
    return ApplicationErrorCode.SESSION_EXPIRED;
  }
  if (errorString.includes("NETWORK") || errorString.includes("CONNECTION") || errorString.includes("TIMEOUT")) {
    return ApplicationErrorCode.NETWORK_ERROR;
  }

  // Default to unknown error
  return ApplicationErrorCode.UNKNOWN_ERROR;
}

/**
 * Get all available error codes
 */
export function getAllErrorCodes(): ApplicationErrorCode[] {
  return Object.values(ApplicationErrorCode);
}

/**
 * Format error for display in UI
 * Returns a complete error object with all details
 */
export function formatApplicationError(error: unknown): ApplicationErrorDetail {
  const code = parseErrorCode(error);
  return getErrorDetail(code);
}

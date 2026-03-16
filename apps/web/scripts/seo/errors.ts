/**
 * SEO Engine Error Handling
 * 
 * Comprehensive error handling with custom error classes, error codes,
 * and utility functions for the SEO engine.
 * 
 * @module seo/errors
 */

// ============================================================================
// Error Codes
// ============================================================================

/**
 * SEO Engine Error Codes
 * 
 * Comprehensive error codes for all SEO engine operations.
 */
export enum SEO_ERROR_CODES {
    // General errors (1xxx)
    UNKNOWN_ERROR = 'SEO_1000',
    CONFIGURATION_ERROR = 'SEO_1001',
    INITIALIZATION_ERROR = 'SEO_1002',

    // Google API errors (2xxx)
    GOOGLE_API_ERROR = 'SEO_2000',
    GOOGLE_AUTH_ERROR = 'SEO_2001',
    GOOGLE_QUOTA_ERROR = 'SEO_2002',
    GOOGLE_RATE_LIMIT_ERROR = 'SEO_2003',
    GOOGLE_API_RESPONSE_ERROR = 'SEO_2004',
    GOOGLE_SEARCH_CONSOLE_ERROR = 'SEO_2005',

    // Validation errors (3xxx)
    VALIDATION_ERROR = 'SEO_3000',
    INVALID_INPUT_ERROR = 'SEO_3001',
    SCHEMA_VALIDATION_ERROR = 'SEO_3002',

    // State management errors (4xxx)
    STATE_ERROR = 'SEO_4000',
    STATE_CORRUPTION_ERROR = 'SEO_4001',
    STATE_LOCK_ERROR = 'SEO_4002',
    STATE_TRANSITION_ERROR = 'SEO_4003',

    // Rate limiting errors (5xxx)
    RATE_LIMIT_ERROR = 'SEO_5000',
    DAILY_LIMIT_EXCEEDED = 'SEO_5001',
    CONCURRENT_REQUEST_ERROR = 'SEO_5002',

    // Content generation errors (6xxx)
    CONTENT_GENERATION_ERROR = 'SEO_6000',
    LLM_API_ERROR = 'SEO_6001',
    CONTENT_VALIDATION_ERROR = 'SEO_6002',
    CONTENT_TOO_LONG_ERROR = 'SEO_6003',
    CONTENT_TOO_SHORT_ERROR = 'SEO_6004',

    // Database errors (7xxx)
    DATABASE_ERROR = 'SEO_7000',
    DATABASE_CONNECTION_ERROR = 'SEO_7001',
    DATABASE_QUERY_ERROR = 'SEO_7002',
    DATABASE_TRANSACTION_ERROR = 'SEO_7003',
    DATABASE_TIMEOUT_ERROR = 'SEO_7004',

    // Retry errors (8xxx)
    RETRY_EXHAUSTED_ERROR = 'SEO_8000',
    RETRY_TIMEOUT_ERROR = 'SEO_8001',
}

// ============================================================================
// Error Context Interface
// ============================================================================

/**
 * Error context for structured error reporting
 */
export interface ErrorContext {
    /** Unique identifier for this error occurrence */
    errorId: string;
    /** Error code from SEO_ERROR_CODES */
    code: SEO_ERROR_CODES;
    /** Human-readable error message */
    message: string;
    /** Original error that was caught */
    originalError?: Error;
    /** Additional context data */
    context?: Record<string, unknown>;
    /** Timestamp when error occurred */
    timestamp: string;
    /** Whether the error is retryable */
    retryable: boolean;
    /** Number of retry attempts made */
    retryCount?: number;
    /** Operation that was being performed */
    operation?: string;
    /** Additional metadata */
    metadata?: Record<string, unknown>;
}

// ============================================================================
// Base Error Class
// ============================================================================

/**
 * Base SEO Error class
 * 
 * All SEO engine errors extend this base class for consistent error handling.
 */
export class SEOError extends Error {
    /** Unique error code */
    public readonly code: SEO_ERROR_CODES;
    /** Whether this error is retryable */
    public readonly retryable: boolean;
    /** Original error if this wraps another error */
    public readonly originalError?: Error;
    /** Additional context */
    public readonly context?: Record<string, unknown>;
    /** Timestamp */
    public readonly timestamp: string;

    constructor(
        code: SEO_ERROR_CODES,
        message: string,
        options?: {
            retryable?: boolean;
            originalError?: Error;
            context?: Record<string, unknown>;
        }
    ) {
        super(message);
        this.name = 'SEOError';
        this.code = code;
        this.retryable = options?.retryable ?? false;
        this.originalError = options?.originalError;
        this.context = options?.context;
        this.timestamp = new Date().toISOString();

        // Maintains proper stack trace in V8 environments
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, SEOError);
        }
    }

    /**
     * Convert error to JSON-serializable object
     */
    toJSON(): Record<string, unknown> {
        return {
            name: this.name,
            code: this.code,
            message: this.message,
            retryable: this.retryable,
            timestamp: this.timestamp,
            context: this.context,
            stack: this.stack,
            originalError: this.originalError ? {
                name: this.originalError.name,
                message: this.originalError.message,
                stack: this.originalError.stack,
            } : undefined,
        };
    }

    /**
     * Convert to structured error context
     */
    toContext(operation?: string): ErrorContext {
        return {
            errorId: generateErrorId(),
            code: this.code,
            message: this.message,
            originalError: this.originalError,
            context: this.context,
            timestamp: this.timestamp,
            retryable: this.retryable,
            operation,
        };
    }
}

// ============================================================================
// Google API Errors
// ============================================================================

/**
 * Google API Error
 * 
 * Base class for all Google API-related errors.
 */
export class GoogleAPIError extends SEOError {
    /** Google API service name */
    public readonly service: string;
    /** API endpoint that was called */
    public readonly endpoint?: string;
    /** HTTP status code if available */
    public readonly statusCode?: number;

    constructor(
        message: string,
        options?: {
            service: string;
            endpoint?: string;
            statusCode?: number;
            retryable?: boolean;
            originalError?: Error;
            context?: Record<string, unknown>;
        }
    ) {
        super(SEO_ERROR_CODES.GOOGLE_API_ERROR, message, {
            retryable: options?.retryable,
            originalError: options?.originalError,
            context: {
                ...options?.context,
                service: options?.service,
                endpoint: options?.endpoint,
                statusCode: options?.statusCode,
            },
        });
        this.name = 'GoogleAPIError';
        this.service = options?.service ?? 'unknown';
        this.endpoint = options?.endpoint;
        this.statusCode = options?.statusCode;
    }
}

/**
 * Google Authentication Error
 */
export class GoogleAuthError extends GoogleAPIError {
    constructor(
        message: string,
        options?: {
            service?: string;
            endpoint?: string;
            originalError?: Error;
        }
    ) {
        super(message, {
            service: options?.service ?? 'auth',
            endpoint: options?.endpoint,
            retryable: false,
            originalError: options?.originalError,
        });
        this.name = 'GoogleAuthError';
    }
}

/**
 * Google Quota Error
 */
export class GoogleQuotaError extends GoogleAPIError {
    /** Quota metric that was exceeded */
    public readonly quotaMetric?: string;
    /** Limit that was hit */
    public readonly limit?: number;
    /** Current usage */
    public readonly currentUsage?: number;

    constructor(
        message: string,
        options?: {
            service?: string;
            quotaMetric?: string;
            limit?: number;
            currentUsage?: number;
            originalError?: Error;
        }
    ) {
        super(message, {
            service: options?.service ?? 'quota',
            retryable: true,
            originalError: options?.originalError,
            context: {
                quotaMetric: options?.quotaMetric,
                limit: options?.limit,
                currentUsage: options?.currentUsage,
            },
        });
        this.name = 'GoogleQuotaError';
        this.quotaMetric = options?.quotaMetric;
        this.limit = options?.limit;
        this.currentUsage = options?.currentUsage;
    }
}

// ============================================================================
// Validation Errors
// ============================================================================

/**
 * Validation Error
 * 
 * Raised when input validation fails.
 */
export class ValidationError extends SEOError {
    /** Field that failed validation */
    public readonly field: string;
    /** Value that caused the validation failure */
    public readonly invalidValue?: unknown;

    constructor(
        field: string,
        message: string,
        options?: {
            invalidValue?: unknown;
            originalError?: Error;
        }
    ) {
        super(SEO_ERROR_CODES.VALIDATION_ERROR, `Validation error in ${field}: ${message}`, {
            retryable: false,
            originalError: options?.originalError,
            context: {
                field,
                invalidValue: options?.invalidValue,
            },
        });
        this.name = 'ValidationError';
        this.field = field;
        this.invalidValue = options?.invalidValue;
    }
}

// ============================================================================
// State Management Errors
// ============================================================================

/**
 * State Error
 * 
 * Raised when state management operations fail.
 */
export class StateError extends SEOError {
    /** Type of state operation that failed */
    public readonly operation: 'get' | 'set' | 'update' | 'delete' | 'lock' | 'unlock';
    /** State key that was being operated on */
    public readonly stateKey?: string;

    constructor(
        message: string,
        options?: {
            operation?: StateError['operation'];
            stateKey?: string;
            retryable?: boolean;
            originalError?: Error;
        }
    ) {
        super(SEO_ERROR_CODES.STATE_ERROR, message, {
            retryable: options?.retryable ?? false,
            originalError: options?.originalError,
            context: {
                operation: options?.operation,
                stateKey: options?.stateKey,
            },
        });
        this.name = 'StateError';
        this.operation = options?.operation ?? 'get';
        this.stateKey = options?.stateKey;
    }
}

/**
 * State Corruption Error
 * 
 * Raised when state data is corrupted or inconsistent.
 */
export class StateCorruptionError extends StateError {
    constructor(
        message: string,
        options?: {
            stateKey?: string;
            originalError?: Error;
        }
    ) {
        super(message, {
            operation: 'get',
            stateKey: options?.stateKey,
            retryable: false,
            originalError: options?.originalError,
        });
        this.name = 'StateCorruptionError';
    }
}

// ============================================================================
// Rate Limiting Errors
// ============================================================================

/**
 * Rate Limit Error
 * 
 * Raised when rate limits are exceeded.
 */
export class RateLimitError extends SEOError {
    /** Type of rate limit */
    public readonly limitType: 'daily' | 'concurrent' | 'api' | 'custom';
    /** Limit that was exceeded */
    public readonly limit: number;
    /** Current usage */
    public readonly currentUsage: number;
    /** When the rate limit will reset */
    public readonly resetAt?: string;
    /** Retry after seconds */
    public readonly retryAfter?: number;

    constructor(
        message: string,
        options: {
            limitType: RateLimitError['limitType'];
            limit: number;
            currentUsage: number;
            resetAt?: string;
            retryAfter?: number;
        }
    ) {
        super(SEO_ERROR_CODES.RATE_LIMIT_ERROR, message, {
            retryable: true,
            context: {
                limitType: options.limitType,
                limit: options.limit,
                currentUsage: options.currentUsage,
                resetAt: options.resetAt,
                retryAfter: options.retryAfter,
            },
        });
        this.name = 'RateLimitError';
        this.limitType = options.limitType;
        this.limit = options.limit;
        this.currentUsage = options.currentUsage;
        this.resetAt = options.resetAt;
        this.retryAfter = options.retryAfter;
    }
}

// ============================================================================
// Content Generation Errors
// ============================================================================

/**
 * Content Generation Error
 * 
 * Raised when content generation fails.
 */
export class ContentGenerationError extends SEOError {
    /** Type of content being generated */
    public readonly contentType?: string;
    /** Topic or keyword for content */
    public readonly topic?: string;
    /** Generation attempt number */
    public readonly attempt?: number;

    constructor(
        message: string,
        options?: {
            contentType?: string;
            topic?: string;
            attempt?: number;
            retryable?: boolean;
            originalError?: Error;
        }
    ) {
        super(SEO_ERROR_CODES.CONTENT_GENERATION_ERROR, message, {
            retryable: options?.retryable ?? true,
            originalError: options?.originalError,
            context: {
                contentType: options?.contentType,
                topic: options?.topic,
                attempt: options?.attempt,
            },
        });
        this.name = 'ContentGenerationError';
        this.contentType = options?.contentType;
        this.topic = options?.topic;
        this.attempt = options?.attempt;
    }
}

/**
 * LLM API Error
 * 
 * Raised when the LLM API call fails.
 */
export class LLMAPIError extends ContentGenerationError {
    /** Model being used */
    public readonly model?: string;
    /** API response status code */
    public readonly statusCode?: number;

    constructor(
        message: string,
        options?: {
            model?: string;
            statusCode?: number;
            topic?: string;
            attempt?: number;
            originalError?: Error;
        }
    ) {
        super(message, {
            contentType: 'llm',
            topic: options?.topic,
            attempt: options?.attempt,
            retryable: true,
            originalError: options?.originalError,
        });
        this.name = 'LLMAPIError';
        this.model = options?.model;
        this.statusCode = options?.statusCode;
    }
}

// ============================================================================
// Database Errors
// ============================================================================

/**
 * Database Error
 * 
 * Base class for database-related errors.
 */
export class DatabaseError extends SEOError {
    /** Type of database operation */
    public readonly operation: 'query' | 'insert' | 'update' | 'delete' | 'connect' | 'transaction';
    /** Table being accessed */
    public readonly table?: string;
    /** SQL that caused the error (sanitized) */
    public readonly sql?: string;

    constructor(
        message: string,
        options?: {
            operation?: DatabaseError['operation'];
            table?: string;
            sql?: string;
            retryable?: boolean;
            originalError?: Error;
        }
    ) {
        super(SEO_ERROR_CODES.DATABASE_ERROR, message, {
            retryable: options?.retryable ?? false,
            originalError: options?.originalError,
            context: {
                operation: options?.operation,
                table: options?.table,
                sql: options?.sql,
            },
        });
        this.name = 'DatabaseError';
        this.operation = options?.operation ?? 'query';
        this.table = options?.table;
        this.sql = options?.sql;
    }
}

/**
 * Database Connection Error
 */
export class DatabaseConnectionError extends DatabaseError {
    constructor(
        message: string,
        options?: {
            originalError?: Error;
        }
    ) {
        super(message, {
            operation: 'connect',
            retryable: true,
            originalError: options?.originalError,
        });
        this.name = 'DatabaseConnectionError';
    }
}

/**
 * Database Query Error
 */
export class DatabaseQueryError extends DatabaseError {
    constructor(
        message: string,
        options?: {
            table?: string;
            sql?: string;
            originalError?: Error;
        }
    ) {
        super(message, {
            operation: 'query',
            table: options?.table,
            sql: options?.sql,
            retryable: false,
            originalError: options?.originalError,
        });
        this.name = 'DatabaseQueryError';
    }
}

// ============================================================================
// Error Message Templates
// ============================================================================

/**
 * Error message templates
 */
export const ERROR_MESSAGES = {
    // Google API
    GOOGLE_AUTH_FAILED: 'Google API authentication failed: {details}',
    GOOGLE_QUOTA_EXCEEDED: 'Google API quota exceeded for {service}: {details}',
    GOOGLE_RATE_LIMIT: 'Google API rate limit exceeded. Retry after {retryAfter} seconds',
    GOOGLE_API_RESPONSE_INVALID: 'Invalid response from Google API: {details}',

    // Validation
    VALIDATION_REQUIRED: '{field} is required',
    VALIDATION_INVALID_FORMAT: '{field} has invalid format: {details}',
    VALIDATION_OUT_OF_RANGE: '{field} must be between {min} and {max}',
    VALIDATION_TOO_LONG: '{field} must be less than {max} characters',
    VALIDATION_TOO_SHORT: '{field} must be at least {min} characters',

    // State
    STATE_CORRUPTED: 'State corrupted for key {key}: {details}',
    STATE_LOCK_FAILED: 'Failed to acquire lock for {key}',
    STATE_NOT_FOUND: 'State not found for key: {key}',

    // Rate Limiting
    RATE_LIMIT_DAILY: 'Daily limit of {limit} exceeded ({current}/{limit})',
    RATE_LIMIT_CONCURRENT: 'Concurrent request limit of {limit} exceeded',
    RATE_LIMIT_RETRY_AFTER: 'Rate limit exceeded. Retry after {seconds} seconds',

    // Content Generation
    CONTENT_GENERATION_FAILED: 'Content generation failed: {details}',
    CONTENT_LLM_ERROR: 'LLM API error: {details}',
    CONTENT_VALIDATION_FAILED: 'Generated content validation failed: {details}',
    CONTENT_TOO_LONG: 'Generated content exceeds maximum length of {max} characters',
    CONTENT_TOO_SHORT: 'Generated content below minimum length of {min} characters',

    // Database
    DB_CONNECTION_FAILED: 'Database connection failed: {details}',
    DB_QUERY_FAILED: 'Database query failed: {details}',
    DB_TRANSACTION_FAILED: 'Database transaction failed: {details}',
    DB_TIMEOUT: 'Database operation timed out after {timeout}ms',

    // Retry
    RETRY_EXHAUSTED: 'All {maxRetries} retry attempts exhausted',
    RETRY_TIMEOUT: 'Operation timed out after {timeout}ms',
} as const;

/**
 * Format error message template with variables
 */
export function formatErrorMessage(
    template: string,
    variables: Record<string, string | number>
): string {
    let result = template;
    for (const [key, value] of Object.entries(variables)) {
        result = result.replace(new RegExp(`\\{${key}\\}`, 'g'), String(value));
    }
    return result;
}

// ============================================================================
// Error Handling Utilities
// ============================================================================

/**
 * Generate a unique error ID
 */
function generateErrorId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Check if an error is retryable
 * 
 * @param error - The error to check
 * @returns True if the error is retryable
 */
export function isRetryable(error: unknown): boolean {
    if (error instanceof SEOError) {
        return error.retryable;
    }

    if (error instanceof Error) {
        // Check for network-related errors
        const networkErrors = [
            'ECONNREFUSED',
            'ECONNRESET',
            'ETIMEDOUT',
            'ENOTFOUND',
            'ENETUNREACH',
            'EAI_AGAIN',
        ];

        if ('code' in error && typeof error.code === 'string' && networkErrors.includes(error.code)) {
            return true;
        }

        // Check error message patterns
        const retryablePatterns = [
            /ECONNREFUSED/i,
            /ECONNRESET/i,
            /ETIMEDOUT/i,
            /timeout/i,
            /temporary failure/i,
            /service unavailable/i,
            /too many requests/i,
            /rate limit/i,
            /quota/i,
            /429/i,
            /5\d{2}/, // 5xx errors
        ];

        for (const pattern of retryablePatterns) {
            if (pattern.test(error.message)) {
                return true;
            }
        }
    }

    return false;
}

/**
 * Safely extract error message from any error type
 * 
 * @param error - The error to extract message from
 * @returns The error message string
 */
export function getErrorMessage(error: unknown): string {
    if (error === null) {
        return 'Unknown error (null)';
    }

    if (error === undefined) {
        return 'Unknown error (undefined)';
    }

    if (typeof error === 'string') {
        return error;
    }

    if (error instanceof Error) {
        return error.message;
    }

    // Handle objects with message property
    if (typeof error === 'object' && error !== null && 'message' in error) {
        const msg = (error as Record<string, unknown>).message;
        if (typeof msg === 'string') {
            return msg;
        }
    }

    // Handle unknown objects
    if (typeof error === 'object') {
        try {
            return JSON.stringify(error);
        } catch {
            return '[Object]';
        }
    }

    return String(error);
}

/**
 * Main error handler function
 * 
 * @param error - The error to handle
 * @param operation - Optional operation context
 * @param additionalContext - Additional context to include
 * @returns Structured error context
 */
export function handleError(
    error: unknown,
    operation?: string,
    additionalContext?: Record<string, unknown>
): ErrorContext {
    const isSEOError = error instanceof SEOError;

    const context: ErrorContext = {
        errorId: generateErrorId(),
        code: isSEOError ? error.code : SEO_ERROR_CODES.UNKNOWN_ERROR,
        message: getErrorMessage(error),
        timestamp: new Date().toISOString(),
        retryable: isRetryable(error),
        operation,
        context: additionalContext,
    };

    if (isSEOError) {
        context.originalError = error.originalError;
        if (error.context) {
            context.context = { ...error.context, ...additionalContext };
        }
        if ('retryCount' in error && typeof (error as Record<string, unknown>).retryCount === 'number') {
            context.retryCount = (error as Record<string, unknown>).retryCount as number;
        }
    } else if (error instanceof Error) {
        context.originalError = error;
        context.context = {
            ...additionalContext,
            stack: error.stack,
        };
    }

    return context;
}

/**
 * Serialize error for logging
 * 
 * @param error - Error to serialize
 * @returns JSON-serializable object
 */
export function serializeError(error: unknown): Record<string, unknown> {
    if (error instanceof SEOError) {
        return error.toJSON();
    }

    if (error instanceof Error) {
        return {
            name: error.name,
            message: error.message,
            stack: error.stack,
        };
    }

    // Try to serialize as-is
    try {
        return JSON.parse(JSON.stringify(error));
    } catch {
        return {
            message: String(error),
        };
    }
}

/**
 * Check if error is a specific SEO error type
 */
export function isSEOError(error: unknown): error is SEOError {
    return error instanceof SEOError;
}

/**
 * Check if error is a Google API error
 */
export function isGoogleAPIError(error: unknown): error is GoogleAPIError {
    return error instanceof GoogleAPIError;
}

/**
 * Check if error is a validation error
 */
export function isValidationError(error: unknown): error is ValidationError {
    return error instanceof ValidationError;
}

/**
 * Check if error is a rate limit error
 */
export function isRateLimitError(error: unknown): error is RateLimitError {
    return error instanceof RateLimitError;
}

/**
 * Check if error is a database error
 */
export function isDatabaseError(error: unknown): error is DatabaseError {
    return error instanceof DatabaseError;
}

// ============================================================================
// Type Guards for Error Codes
// ============================================================================

/**
 * Check if error code is a Google API error
 */
export function isGoogleErrorCode(code: SEO_ERROR_CODES): boolean {
    return code.startsWith('SEO_2');
}

/**
 * Check if error code is a validation error
 */
export function isValidationErrorCode(code: SEO_ERROR_CODES): boolean {
    return code.startsWith('SEO_3');
}

/**
 * Check if error code is a state error
 */
export function isStateErrorCode(code: SEO_ERROR_CODES): boolean {
    return code.startsWith('SEO_4');
}

/**
 * Check if error code is a rate limit error
 */
export function isRateLimitErrorCode(code: SEO_ERROR_CODES): boolean {
    return code.startsWith('SEO_5');
}

/**
 * Check if error code is a content generation error
 */
export function isContentErrorCode(code: SEO_ERROR_CODES): boolean {
    return code.startsWith('SEO_6');
}

/**
 * Check if error code is a database error
 */
export function isDatabaseErrorCode(code: SEO_ERROR_CODES): boolean {
    return code.startsWith('SEO_7');
}

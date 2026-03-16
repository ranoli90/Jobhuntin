/**
 * SEO Engine Retry Logic
 * 
 * Comprehensive retry logic with exponential backoff, circuit breaker pattern,
 * and specialized retry handlers for different operation types.
 * 
 * @module seo/retry
 */

// ============================================================================
// Imports
// ============================================================================

import {
    SEOError,
    SEO_ERROR_CODES,
    isRetryable,
    GoogleAPIError,
    GoogleQuotaError,
    RateLimitError,
    LLMAPIError,
} from './errors';

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Backoff strategy types
 */
export type BackoffStrategy = 'exponential' | 'linear' | 'fixed' | 'jittered';

/**
 * HTTP methods that can be retried
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

/**
 * Retry configuration interface
 */
export interface RetryConfig {
    /** Maximum number of retry attempts */
    maxRetries: number;
    /** Base delay in milliseconds */
    baseDelay: number;
    /** Maximum delay in milliseconds */
    maxDelay: number;
    /** Backoff multiplier for exponential/linear strategies */
    backoffMultiplier: number;
    /** HTTP status codes that should trigger a retry */
    retryableStatuses: number[];
    /** Timeout for the entire operation in milliseconds */
    timeout: number;
    /** Backoff strategy to use */
    strategy: BackoffStrategy;
    /** Whether to use jitter (recommended for production) */
    useJitter: boolean;
    /** Callback function called before each retry */
    onRetry?: (attempt: number, error: Error) => void | Promise<void>;
    /** Callback function called when all retries are exhausted */
    onExhausted?: (error: Error, attempts: number) => void | Promise<void>;
}

/**
 * Circuit breaker states
 */
export type CircuitBreakerState = 'closed' | 'open' | 'half-open';

/**
 * Circuit breaker configuration
 */
export interface CircuitBreakerConfig {
    /** Number of failures before opening the circuit */
    failureThreshold: number;
    /** Number of successes needed to close the circuit from half-open */
    successThreshold: number;
    /** Time in milliseconds before attempting to close the circuit */
    timeout: number;
    /** Monitoring window in milliseconds */
    monitoringWindow: number;
    /** Half-open maximum requests */
    halfOpenMaxRequests: number;
}

/**
 * Retry result
 */
export interface RetryResult<T> {
    /** Whether the operation succeeded */
    success: boolean;
    /** The result value if successful */
    value?: T;
    /** Error if failed */
    error?: Error;
    /** Number of attempts made */
    attempts: number;
    /** Total time spent in milliseconds */
    totalTimeMs: number;
}

/**
 * Function type for retryable operations
 */
export type RetryableFunction<T> = () => Promise<T> | T;

/**
 * Default retry configuration
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 30000,
    backoffMultiplier: 2,
    retryableStatuses: [408, 429, 500, 502, 503, 504],
    timeout: 30000,
    strategy: 'exponential',
    useJitter: true,
};

/**
 * Default circuit breaker configuration
 */
export const DEFAULT_CIRCUIT_BREAKER_CONFIG: CircuitBreakerConfig = {
    failureThreshold: 5,
    successThreshold: 2,
    timeout: 60000,
    monitoringWindow: 120000,
    halfOpenMaxRequests: 3,
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Generate a unique error ID
 */
function generateErrorId(): string {
    return `retry_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Check if an error is retryable based on status code
 */
export function isStatusRetryable(status: number, retryableStatuses: number[]): boolean {
    return retryableStatuses.includes(status);
}

/**
 * Calculate delay using exponential backoff
 */
export function calculateExponentialBackoff(
    attempt: number,
    baseDelay: number,
    maxDelay: number,
    multiplier: number,
    useJitter: boolean
): number {
    const exponentialDelay = baseDelay * Math.pow(multiplier, attempt);
    const cappedDelay = Math.min(exponentialDelay, maxDelay);

    if (useJitter) {
        // Add jitter between 0% and 25% of the delay
        const jitter = cappedDelay * Math.random() * 0.25;
        return Math.floor(cappedDelay + jitter);
    }

    return Math.floor(cappedDelay);
}

/**
 * Calculate delay using linear backoff
 */
export function calculateLinearBackoff(
    attempt: number,
    baseDelay: number,
    maxDelay: number,
    multiplier: number,
    useJitter: boolean
): number {
    const linearDelay = baseDelay * (1 + (attempt * multiplier));
    const cappedDelay = Math.min(linearDelay, maxDelay);

    if (useJitter) {
        const jitter = cappedDelay * Math.random() * 0.25;
        return Math.floor(cappedDelay + jitter);
    }

    return Math.floor(cappedDelay);
}

/**
 * Calculate delay using fixed backoff
 */
export function calculateFixedBackoff(
    baseDelay: number,
    useJitter: boolean
): number {
    if (useJitter) {
        const jitter = baseDelay * Math.random() * 0.25;
        return Math.floor(baseDelay + jitter);
    }

    return baseDelay;
}

/**
 * Calculate delay using jittered backoff (full jitter)
 */
export function calculateJitteredBackoff(
    attempt: number,
    baseDelay: number,
    maxDelay: number,
    multiplier: number
): number {
    const exponentialDelay = baseDelay * Math.pow(multiplier, attempt);
    const cappedDelay = Math.min(exponentialDelay, maxDelay);

    // Full jitter: random value between 0 and capped delay
    return Math.floor(Math.random() * cappedDelay);
}

/**
 * Calculate delay based on strategy
 */
export function calculateDelay(
    attempt: number,
    config: RetryConfig
): number {
    switch (config.strategy) {
        case 'exponential':
            return calculateExponentialBackoff(
                attempt,
                config.baseDelay,
                config.maxDelay,
                config.backoffMultiplier,
                config.useJitter
            );
        case 'linear':
            return calculateLinearBackoff(
                attempt,
                config.baseDelay,
                config.maxDelay,
                config.backoffMultiplier,
                config.useJitter
            );
        case 'fixed':
            return calculateFixedBackoff(config.baseDelay, config.useJitter);
        case 'jittered':
            return calculateJitteredBackoff(
                attempt,
                config.baseDelay,
                config.maxDelay,
                config.backoffMultiplier
            );
        default:
            return calculateExponentialBackoff(
                attempt,
                config.baseDelay,
                config.maxDelay,
                config.backoffMultiplier,
                config.useJitter
            );
    }
}

/**
 * Create a timeout promise
 */
function createTimeoutPromise<T>(
    ms: number,
    operationName: string
): Promise<T> {
    return new Promise((_, reject) => {
        setTimeout(() => {
            reject(
                new SEOError(
                    SEO_ERROR_CODES.RETRY_TIMEOUT_ERROR,
                    `Operation "${operationName}" timed out after ${ms}ms`,
                    {
                        retryable: true,
                        context: { timeoutMs: ms, operationName },
                    }
                )
            );
        }, ms);
    });
}

/**
 * Race a promise against a timeout
 */
async function raceWithTimeout<T>(
    promise: Promise<T>,
    ms: number,
    operationName: string
): Promise<T> {
    if (ms <= 0 || ms === Infinity) {
        return promise;
    }

    return Promise.race([promise, createTimeoutPromise<T>(ms, operationName)]);
}

// ============================================================================
// Main Retry Function
// ============================================================================

/**
 * Retry a function with exponential backoff
 * 
 * @param fn - The function to retry
 * @param config - Retry configuration
 * @param operationName - Name of the operation for logging
 * @returns Promise resolving to the result
 * 
 * @example
 * ```typescript
 * const result = await retry(
 *   () => fetchDataFromAPI(),
 *   { maxRetries: 3, baseDelay: 1000, strategy: 'exponential' },
 *   'fetchData'
 * );
 * ```
 */
export async function retry<T>(
    fn: RetryableFunction<T>,
    config: Partial<RetryConfig> = {},
    operationName: string = 'operation'
): Promise<T> {
    const finalConfig: RetryConfig = {
        ...DEFAULT_RETRY_CONFIG,
        ...config,
    };

    let lastError: Error | undefined;
    let attempts = 0;
    const startTime = Date.now();

    while (attempts <= finalConfig.maxRetries) {
        attempts++;

        try {
            const result = await raceWithTimeout(
                Promise.resolve(fn()),
                finalConfig.timeout,
                operationName
            );

            return result;
        } catch (error) {
            lastError = error instanceof Error ? error : new Error(String(error));

            // Check if we should retry
            const shouldRetry = attempts <= finalConfig.maxRetries &&
                isErrorRetryable(lastError, finalConfig);

            if (!shouldRetry) {
                throw lastError;
            }

            // Call onRetry callback if provided
            if (finalConfig.onRetry) {
                await finalConfig.onRetry(attempts, lastError);
            }

            // Calculate delay and wait
            if (attempts <= finalConfig.maxRetries) {
                const delay = calculateDelay(attempts, finalConfig);
                await sleep(delay);
            }
        }
    }

    // All retries exhausted
    if (finalConfig.onExhausted && lastError) {
        await finalConfig.onExhausted(lastError, attempts);
    }

    throw lastError || new Error('Retry failed with no error');
}

/**
 * Check if an error is retryable
 */
function isErrorRetryable(error: Error, config: RetryConfig): boolean {
    // Check if it's a known SEO error with retryable flag
    if (error instanceof SEOError) {
        return error.retryable;
    }

    // Check for HTTP status code in error context
    if (error instanceof GoogleAPIError && error.statusCode) {
        return isStatusRetryable(error.statusCode, config.retryableStatuses);
    }

    // Check for rate limit errors
    if (error instanceof RateLimitError) {
        return true;
    }

    // Check for Google quota errors
    if (error instanceof GoogleQuotaError) {
        return true;
    }

    // Check for generic retryable interface
    if ('retryable' in error && typeof (error as any).retryable === 'boolean') {
        return (error as any).retryable;
    }

    // Check for status code in error message or properties
    const statusCode = extractStatusCode(error);
    if (statusCode !== null) {
        return isStatusRetryable(statusCode, config.retryableStatuses);
    }

    // Default to retryable for network errors
    return isNetworkError(error);
}

/**
 * Extract HTTP status code from error
 */
function extractStatusCode(error: Error): number | null {
    // Check if error has statusCode property
    if ('statusCode' in error && typeof (error as any).statusCode === 'number') {
        return (error as any).statusCode;
    }

    // Check context for status code
    if (error instanceof SEOError && error.context) {
        const statusCode = error.context.statusCode;
        if (typeof statusCode === 'number') {
            return statusCode;
        }
    }

    return null;
}

/**
 * Check if error is a network error
 */
function isNetworkError(error: Error): boolean {
    const networkErrors = [
        'ECONNREFUSED',
        'ETIMEDOUT',
        'ENOTFOUND',
        'ENETUNREACH',
        'EAI_AGAIN',
    ];

    // Check error code
    if ('code' in error && typeof (error as any).code === 'string') {
        return networkErrors.includes((error as any).code);
    }

    // Check error message
    const message = error.message.toLowerCase();
    return (
        message.includes('network') ||
        message.includes('timeout') ||
        message.includes('connection')
    );
}

// ============================================================================
// Retry Result Wrapper
// ============================================================================

/**
 * Execute a function and return a structured result
 * 
 * @param fn - The function to execute
 * @param config - Retry configuration
 * @param operationName - Name of the operation
 * @returns Promise resolving to RetryResult
 */
export async function retryWithResult<T>(
    fn: RetryableFunction<T>,
    config: Partial<RetryConfig> = {},
    operationName: string = 'operation'
): Promise<RetryResult<T>> {
    const startTime = Date.now();

    try {
        const value = await retry(fn, config, operationName);
        return {
            success: true,
            value,
            attempts: 1,
            totalTimeMs: Date.now() - startTime,
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error : new Error(String(error)),
            attempts: config.maxRetries ? config.maxRetries + 1 : 1,
            totalTimeMs: Date.now() - startTime,
        };
    }
}

// ============================================================================
// Decorators
// ============================================================================

/**
 * Create a retryable decorator
 * 
 * @param config - Retry configuration
 * @returns Decorator function
 * 
 * @example
 * ```typescript
 * class MyService {
 *   @retryable({ maxRetries: 3, baseDelay: 1000 })
 *   async fetchData(): Promise<Data> {
 *     // ...
 *   }
 * }
 * ```
 */
export function retryable(config: Partial<RetryConfig> = {}) {
    return function <T extends (...args: any[]) => Promise<any>>(
        target: any,
        propertyKey: string,
        descriptor: TypedPropertyDescriptor<T>
    ): TypedPropertyDescriptor<T> {
        const originalMethod = descriptor.value;

        if (!originalMethod) {
            return descriptor;
        }

        const wrappedMethod = async function (...args: any[]): Promise<any> {
            return retry(
                () => originalMethod.apply(this, args),
                config,
                `${target.constructor?.name || 'unknown'}.${propertyKey}`
            );
        } as T;

        descriptor.value = wrappedMethod;
        return descriptor;
    };
}

/**
 * Create a retryable higher-order function
 * 
 * @param fn - Function to make retryable
 * @param config - Retry configuration
 * @param operationName - Operation name for logging
 * @returns Retryable function
 * 
 * @example
 * ```typescript
 * const retryableFetch = retryable(
 *   () => fetchData(),
 *   { maxRetries: 3 },
 *   'fetchData'
 * );
 * const result = await retryableFetch();
 * ```
 */
export function retryable<T>(
    fn: RetryableFunction<T>,
    config: Partial<RetryConfig> = {},
    operationName: string = 'retryable-operation'
): () => Promise<T> {
    return async () => retry(fn, config, operationName);
}

// ============================================================================
// Specialized Retry Handlers
// ============================================================================

/**
 * Retry configuration for Google API calls
 */
export const GOOGLE_API_RETRY_CONFIG: Partial<RetryConfig> = {
    maxRetries: 5,
    baseDelay: 1000,
    maxDelay: 60000,
    backoffMultiplier: 2,
    strategy: 'exponential',
    useJitter: true,
    retryableStatuses: [429, 500, 502, 503, 504],
    timeout: 30000,
};

/**
 * Retry configuration for database operations
 */
export const DATABASE_RETRY_CONFIG: Partial<RetryConfig> = {
    maxRetries: 3,
    baseDelay: 500,
    maxDelay: 10000,
    backoffMultiplier: 2,
    strategy: 'exponential',
    useJitter: true,
    retryableStatuses: [408, 429, 500, 502, 503, 504],
    timeout: 15000,
};

/**
 * Retry configuration for LLM API calls
 */
export const LLM_RETRY_CONFIG: Partial<RetryConfig> = {
    maxRetries: 4,
    baseDelay: 2000,
    maxDelay: 120000,
    backoffMultiplier: 2,
    strategy: 'exponential',
    useJitter: true,
    retryableStatuses: [408, 429, 500, 502, 503, 504],
    timeout: 60000,
};

/**
 * Retry a Google API call with appropriate configuration
 * 
 * @param fn - Function to execute
 * @param config - Optional override configuration
 * @param operationName - Operation name for logging
 * @returns Promise resolving to result
 */
export async function retryGoogleAPI<T>(
    fn: RetryableFunction<T>,
    config: Partial<RetryConfig> = {},
    operationName: string = 'google-api'
): Promise<T> {
    return retry(
        fn,
        { ...GOOGLE_API_RETRY_CONFIG, ...config },
        operationName
    );
}

/**
 * Retry a database operation with appropriate configuration
 * 
 * @param fn - Function to execute
 * @param config - Optional override configuration
 * @param operationName - Operation name for logging
 * @returns Promise resolving to result
 */
export async function retryDatabase<T>(
    fn: RetryableFunction<T>,
    config: Partial<RetryConfig> = {},
    operationName: string = 'database'
): Promise<T> {
    return retry(
        fn,
        { ...DATABASE_RETRY_CONFIG, ...config },
        operationName
    );
}

/**
 * Retry an LLM API call with appropriate configuration
 * 
 * @param fn - Function to execute
 * @param config - Optional override configuration
 * @param operationName - Operation name for logging
 * @returns Promise resolving to result
 */
export async function retryLLM<T>(
    fn: RetryableFunction<T>,
    config: Partial<RetryConfig> = {},
    operationName: string = 'llm-api'
): Promise<T> {
    return retry(
        fn,
        { ...LLM_RETRY_CONFIG, ...config },
        operationName
    );
}

// ============================================================================
// Circuit Breaker Pattern
// ============================================================================

/**
 * Circuit Breaker for preventing cascading failures
 * 
 * @example
 * ```typescript
 * const breaker = new CircuitBreaker({
 *   failureThreshold: 5,
 *   successThreshold: 2,
 *   timeout: 60000,
 * });
 * 
 * try {
 *   const result = await breaker.execute(() => fetchData());
 * } catch (error) {
 *   if (breaker.state === 'open') {
 *     // Circuit is open, handle appropriately
 *   }
 * }
 * ```
 */
export class CircuitBreaker {
    private state: CircuitBreakerState = 'closed';
    private failures: number = 0;
    private successes: number = 0;
    private lastFailureTime: number = 0;
    private halfOpenRequests: number = 0;
    private failureTimestamps: number[] = [];

    public readonly config: CircuitBreakerConfig;

    constructor(config: Partial<CircuitBreakerConfig> = {}) {
        this.config = {
            ...DEFAULT_CIRCUIT_BREAKER_CONFIG,
            ...config,
        };
    }

    /**
     * Get current circuit state
     */
    getState(): CircuitBreakerState {
        this.checkStateTransition();
        return this.state;
    }

    /**
     * Check if circuit allows requests
     */
    isAvailable(): boolean {
        this.checkStateTransition();
        return this.state !== 'open';
    }

    /**
     * Execute a function through the circuit breaker
     */
    async execute<T>(fn: RetryableFunction<T>): Promise<T> {
        this.checkStateTransition();

        if (this.state === 'open') {
            throw new SEOError(
                SEO_ERROR_CODES.RETRY_EXHAUSTED_ERROR,
                `Circuit breaker is open. Failed ${this.config.failureThreshold} times.`,
                {
                    retryable: false,
                    context: {
                        state: this.state,
                        failures: this.failures,
                        lastFailureTime: this.lastFailureTime,
                    },
                }
            );
        }

        try {
            const result = await Promise.resolve(fn());
            this.onSuccess();
            return result;
        } catch (error) {
            this.onFailure();
            throw error;
        }
    }

    /**
     * Execute a function with retry through the circuit breaker
     */
    async executeWithRetry<T>(
        fn: RetryableFunction<T>,
        retryConfig: Partial<RetryConfig> = {}
    ): Promise<T> {
        return this.execute(() => retry(fn, retryConfig, 'circuit-breaker-execution'));
    }

    /**
     * Handle successful execution
     */
    private onSuccess(): void {
        this.halfOpenRequests = 0;

        if (this.state === 'half-open') {
            this.successes++;
            if (this.successes >= this.config.successThreshold) {
                this.reset();
            }
        } else {
            this.failures = 0;
        }

        this.cleanOldFailures();
    }

    /**
     * Handle failed execution
     */
    private onFailure(): void {
        this.failures++;
        this.lastFailureTime = Date.now();
        this.failureTimestamps.push(this.lastFailureTime);

        if (this.state === 'half-open') {
            this.open();
        } else if (this.failures >= this.config.failureThreshold) {
            this.open();
        }

        this.cleanOldFailures();
    }

    /**
     * Open the circuit
     */
    private open(): void {
        this.state = 'open';
        this.halfOpenRequests = 0;
        this.successes = 0;
    }

    /**
     * Reset the circuit to closed state
     */
    reset(): void {
        this.state = 'closed';
        this.failures = 0;
        this.successes = 0;
        this.halfOpenRequests = 0;
        this.failureTimestamps = [];
    }

    /**
     * Check if state should transition from open to half-open
     */
    private checkStateTransition(): void {
        if (this.state === 'open') {
            const timeSinceLastFailure = Date.now() - this.lastFailureTime;
            if (timeSinceLastFailure >= this.config.timeout) {
                this.state = 'half-open';
                this.halfOpenRequests = 0;
                this.successes = 0;
            }
        }
    }

    /**
     * Clean up old failure timestamps outside monitoring window
     */
    private cleanOldFailures(): void {
        const cutoff = Date.now() - this.config.monitoringWindow;
        this.failureTimestamps = this.failureTimestamps.filter(ts => ts > cutoff);
        this.failures = this.failureTimestamps.length;
    }

    /**
     * Get circuit breaker metrics
     */
    getMetrics(): {
        state: CircuitBreakerState;
        failures: number;
        successes: number;
        lastFailureTime: number | null;
        isAvailable: boolean;
    } {
        return {
            state: this.getState(),
            failures: this.failures,
            successes: this.successes,
            lastFailureTime: this.lastFailureTime || null,
            isAvailable: this.isAvailable(),
        };
    }
}

// ============================================================================
// Circuit Breaker Registry
// ============================================================================

/**
 * Registry for managing multiple circuit breakers
 */
export class CircuitBreakerRegistry {
    private breakers: Map<string, CircuitBreaker> = new Map();
    private defaultConfig: Partial<CircuitBreakerConfig>;

    constructor(defaultConfig: Partial<CircuitBreakerConfig> = {}) {
        this.defaultConfig = defaultConfig;
    }

    /**
     * Get or create a circuit breaker for a given name
     */
    get(name: string, config?: Partial<CircuitBreakerConfig>): CircuitBreaker {
        if (!this.breakers.has(name)) {
            this.breakers.set(name, new CircuitBreaker({
                ...this.defaultConfig,
                ...config,
            }));
        }
        return this.breakers.get(name)!;
    }

    /**
     * Get all circuit breakers
     */
    getAll(): Map<string, CircuitBreaker> {
        return new Map(this.breakers);
    }

    /**
     * Reset a specific circuit breaker
     */
    reset(name: string): void {
        const breaker = this.breakers.get(name);
        if (breaker) {
            breaker.reset();
        }
    }

    /**
     * Reset all circuit breakers
     */
    resetAll(): void {
        this.breakers.forEach(breaker => breaker.reset());
    }

    /**
     * Remove a circuit breaker
     */
    remove(name: string): void {
        this.breakers.delete(name);
    }

    /**
     * Get all circuit breaker metrics
     */
    getAllMetrics(): Record<string, ReturnType<CircuitBreaker['getMetrics']>> {
        const metrics: Record<string, any> = {};
        this.breakers.forEach((breaker, name) => {
            metrics[name] = breaker.getMetrics();
        });
        return metrics;
    }
}

// ============================================================================
// Exports
// ============================================================================

export default {
    retry,
    retryWithResult,
    retryable,
    retryGoogleAPI,
    retryDatabase,
    retryLLM,
    CircuitBreaker,
    CircuitBreakerRegistry,
    sleep,
    calculateDelay,
    DEFAULT_RETRY_CONFIG,
    DEFAULT_CIRCUIT_BREAKER_CONFIG,
    GOOGLE_API_RETRY_CONFIG,
    DATABASE_RETRY_CONFIG,
    LLM_RETRY_CONFIG,
};

/**
 * SEO Infrastructure Unit Tests
 * 
 * Comprehensive unit tests for core SEO infrastructure modules:
 * - errors.ts: Error classes and error codes
 * - retry.ts: Retry logic, circuit breaker, backoff strategies
 * - google-api.ts: API key validation
 * - database.ts: Query building and sanitization
 * 
 * Note: These tests require proper vitest configuration to run.
 * Run with: cd apps/web && npx vitest run
 * 
 * @module seo/__tests__/seo-infrastructure.test
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// ============================================================================
// Mock Dependencies
// ============================================================================

// Mock the pg module (Database uses Pool from pg)
vi.mock('pg', () => ({
    Pool: vi.fn().mockImplementation(() => ({
        query: vi.fn(),
        end: vi.fn(),
        connect: vi.fn(),
    })),
}));

// Mock process.env for tests
const originalEnv = { ...process.env };

// ============================================================================
// Tests for errors.ts
// ============================================================================

describe('SEO Error Infrastructure', () => {
    beforeEach(() => {
        vi.resetModules();
        process.env = { ...originalEnv };
    });

    afterEach(() => {
        process.env = { ...originalEnv };
    });

    describe('SEO_ERROR_CODES', () => {
        it('should have all required error codes defined', async () => {
            const { SEO_ERROR_CODES } = await import('../errors');

            // General errors (1xxx)
            expect(SEO_ERROR_CODES.UNKNOWN_ERROR).toBe('SEO_1000');
            expect(SEO_ERROR_CODES.CONFIGURATION_ERROR).toBe('SEO_1001');
            expect(SEO_ERROR_CODES.INITIALIZATION_ERROR).toBe('SEO_1002');

            // Google API errors (2xxx)
            expect(SEO_ERROR_CODES.GOOGLE_API_ERROR).toBe('SEO_2000');
            expect(SEO_ERROR_CODES.GOOGLE_AUTH_ERROR).toBe('SEO_2001');
            expect(SEO_ERROR_CODES.GOOGLE_QUOTA_ERROR).toBe('SEO_2002');
            expect(SEO_ERROR_CODES.GOOGLE_RATE_LIMIT_ERROR).toBe('SEO_2003');

            // Validation errors (3xxx)
            expect(SEO_ERROR_CODES.VALIDATION_ERROR).toBe('SEO_3000');
            expect(SEO_ERROR_CODES.INVALID_INPUT_ERROR).toBe('SEO_3001');

            // State management errors (4xxx)
            expect(SEO_ERROR_CODES.STATE_ERROR).toBe('SEO_4000');
            expect(SEO_ERROR_CODES.STATE_CORRUPTION_ERROR).toBe('SEO_4001');

            // Rate limiting errors (5xxx)
            expect(SEO_ERROR_CODES.RATE_LIMIT_ERROR).toBe('SEO_5000');
            expect(SEO_ERROR_CODES.DAILY_LIMIT_EXCEEDED).toBe('SEO_5001');

            // Database errors (7xxx)
            expect(SEO_ERROR_CODES.DATABASE_ERROR).toBe('SEO_7000');
            expect(SEO_ERROR_CODES.DATABASE_CONNECTION_ERROR).toBe('SEO_7001');
            expect(SEO_ERROR_CODES.DATABASE_QUERY_ERROR).toBe('SEO_7002');

            // Retry errors (8xxx)
            expect(SEO_ERROR_CODES.RETRY_EXHAUSTED_ERROR).toBe('SEO_8000');
            expect(SEO_ERROR_CODES.RETRY_TIMEOUT_ERROR).toBe('SEO_8001');
        });
    });

    describe('SEOError', () => {
        it('should create error with correct properties', async () => {
            const { SEOError, SEO_ERROR_CODES } = await import('../errors');

            const error = new SEOError(
                SEO_ERROR_CODES.UNKNOWN_ERROR,
                'Test error message',
                { retryable: true, context: { key: 'value' } }
            );

            expect(error.message).toBe('Test error message');
            expect(error.code).toBe(SEO_ERROR_CODES.UNKNOWN_ERROR);
            expect(error.retryable).toBe(true);
            expect(error.context).toEqual({ key: 'value' });
            expect(error.timestamp).toBeDefined();
            expect(error.name).toBe('SEOError');
        });

        it('should default retryable to false', async () => {
            const { SEOError, SEO_ERROR_CODES } = await import('../errors');

            const error = new SEOError(
                SEO_ERROR_CODES.UNKNOWN_ERROR,
                'Test error message'
            );

            expect(error.retryable).toBe(false);
        });

        it('should serialize to JSON correctly', async () => {
            const { SEOError, SEO_ERROR_CODES } = await import('../errors');

            const originalError = new Error('Original error');
            const error = new SEOError(
                SEO_ERROR_CODES.UNKNOWN_ERROR,
                'Test error message',
                { retryable: true, originalError }
            );

            const json = error.toJSON();

            expect(json.name).toBe('SEOError');
            expect(json.code).toBe(SEO_ERROR_CODES.UNKNOWN_ERROR);
            expect(json.message).toBe('Test error message');
            expect(json.retryable).toBe(true);
            expect(json.timestamp).toBeDefined();
            expect(json.originalError).toBeDefined();
        });

        it('should convert to context correctly', async () => {
            const { SEOError, SEO_ERROR_CODES } = await import('../errors');

            const error = new SEOError(
                SEO_ERROR_CODES.UNKNOWN_ERROR,
                'Test error message',
                { retryable: true }
            );

            const context = error.toContext('test-operation');

            expect(context.errorId).toBeDefined();
            expect(context.code).toBe(SEO_ERROR_CODES.UNKNOWN_ERROR);
            expect(context.message).toBe('Test error message');
            expect(context.retryable).toBe(true);
            expect(context.operation).toBe('test-operation');
            expect(context.timestamp).toBeDefined();
        });
    });

    describe('GoogleAPIError', () => {
        it('should create Google API error with service info', async () => {
            const { GoogleAPIError } = await import('../errors');

            const error = new GoogleAPIError(
                'API request failed',
                {
                    service: 'customsearch',
                    endpoint: 'v1',
                    statusCode: 500,
                    retryable: true
                }
            );

            expect(error.message).toBe('API request failed');
            expect(error.service).toBe('customsearch');
            expect(error.endpoint).toBe('v1');
            expect(error.statusCode).toBe(500);
            expect(error.retryable).toBe(true);
            expect(error.name).toBe('GoogleAPIError');
        });

        it('should default service to unknown', async () => {
            const { GoogleAPIError } = await import('../errors');

            const error = new GoogleAPIError('API request failed');

            expect(error.service).toBe('unknown');
        });
    });

    describe('GoogleAuthError', () => {
        it('should create auth error with retryable false', async () => {
            const { GoogleAuthError } = await import('../errors');

            const error = new GoogleAuthError('Authentication failed', {
                service: 'oauth2'
            });

            expect(error.name).toBe('GoogleAuthError');
            expect(error.retryable).toBe(false);
            expect(error.service).toBe('oauth2');
        });
    });

    describe('GoogleQuotaError', () => {
        it('should create quota error with quota info', async () => {
            const { GoogleQuotaError } = await import('../errors');

            const error = new GoogleQuotaError('Quota exceeded', {
                quotaMetric: 'requests',
                limit: 100,
                currentUsage: 100
            });

            expect(error.name).toBe('GoogleQuotaError');
            expect(error.retryable).toBe(true);
            expect(error.quotaMetric).toBe('requests');
            expect(error.limit).toBe(100);
            expect(error.currentUsage).toBe(100);
        });
    });

    describe('ValidationError', () => {
        it('should create validation error with field info', async () => {
            const { ValidationError } = await import('../errors');

            const error = new ValidationError(
                'email',
                'Invalid email format',
                { invalidValue: 'not-an-email' }
            );

            expect(error.name).toBe('ValidationError');
            expect(error.field).toBe('email');
            expect(error.invalidValue).toBe('not-an-email');
            expect(error.retryable).toBe(false);
            expect(error.message).toContain('email');
        });
    });

    describe('StateError', () => {
        it('should create state error with operation info', async () => {
            const { StateError } = await import('../errors');

            const error = new StateError('State operation failed', {
                operation: 'set',
                stateKey: 'user:123',
                retryable: true
            });

            expect(error.name).toBe('StateError');
            expect(error.operation).toBe('set');
            expect(error.stateKey).toBe('user:123');
            expect(error.retryable).toBe(true);
        });
    });

    describe('StateCorruptionError', () => {
        it('should create corruption error with retryable false', async () => {
            const { StateCorruptionError } = await import('../errors');

            const error = new StateCorruptionError('State data corrupted', {
                stateKey: 'cache:key'
            });

            expect(error.name).toBe('StateCorruptionError');
            expect(error.retryable).toBe(false);
            expect(error.stateKey).toBe('cache:key');
        });
    });

    describe('RateLimitError', () => {
        it('should create rate limit error with limit info', async () => {
            const { RateLimitError } = await import('../errors');

            const error = new RateLimitError('Rate limit exceeded', {
                limitType: 'daily',
                limit: 1000,
                currentUsage: 1000,
                retryAfter: 3600
            });

            expect(error.name).toBe('RateLimitError');
            expect(error.limitType).toBe('daily');
            expect(error.limit).toBe(1000);
            expect(error.currentUsage).toBe(1000);
            expect(error.retryAfter).toBe(3600);
            expect(error.retryable).toBe(true);
        });
    });

    describe('ContentGenerationError', () => {
        it('should create content generation error', async () => {
            const { ContentGenerationError } = await import('../errors');

            const error = new ContentGenerationError('Content generation failed', {
                contentType: 'meta_description',
                topic: 'job hunting',
                attempt: 2
            });

            expect(error.name).toBe('ContentGenerationError');
            expect(error.contentType).toBe('meta_description');
            expect(error.topic).toBe('job hunting');
            expect(error.attempt).toBe(2);
            expect(error.retryable).toBe(true);
        });
    });

    describe('LLMAPIError', () => {
        it('should create LLM API error with model info', async () => {
            const { LLMAPIError } = await import('../errors');

            const error = new LLMAPIError('LLM request failed', {
                model: 'gpt-4',
                statusCode: 429
            });

            expect(error.name).toBe('LLMAPIError');
            expect(error.model).toBe('gpt-4');
            expect(error.statusCode).toBe(429);
            expect(error.retryable).toBe(true);
        });
    });

    describe('DatabaseError', () => {
        it('should create database error with operation info', async () => {
            const { DatabaseError } = await import('../errors');

            const error = new DatabaseError('Query failed', {
                operation: 'query',
                table: 'seo_jobs',
                sql: 'SELECT * FROM seo_jobs'
            });

            expect(error.name).toBe('DatabaseError');
            expect(error.operation).toBe('query');
            expect(error.table).toBe('seo_jobs');
            expect(error.sql).toBe('SELECT * FROM seo_jobs');
        });
    });

    describe('DatabaseConnectionError', () => {
        it('should create connection error with retryable true', async () => {
            const { DatabaseConnectionError } = await import('../errors');

            const error = new DatabaseConnectionError('Connection refused');

            expect(error.name).toBe('DatabaseConnectionError');
            expect(error.operation).toBe('connect');
            expect(error.retryable).toBe(true);
        });
    });

    describe('DatabaseQueryError', () => {
        it('should create query error', async () => {
            const { DatabaseQueryError } = await import('../errors');

            const error = new DatabaseQueryError('Query syntax error', {
                table: 'users'
            });

            expect(error.name).toBe('DatabaseQueryError');
            expect(error.operation).toBe('query');
            expect(error.table).toBe('users');
        });
    });

    describe('isRetryable', () => {
        it('should return true for retryable SEOError', async () => {
            const { SEOError, SEO_ERROR_CODES, isRetryable } = await import('../errors');

            const error = new SEOError(
                SEO_ERROR_CODES.UNKNOWN_ERROR,
                'Test',
                { retryable: true }
            );

            expect(isRetryable(error)).toBe(true);
        });

        it('should return false for non-retryable SEOError', async () => {
            const { SEOError, SEO_ERROR_CODES, isRetryable } = await import('../errors');

            const error = new SEOError(
                SEO_ERROR_CODES.UNKNOWN_ERROR,
                'Test',
                { retryable: false }
            );

            expect(isRetryable(error)).toBe(false);
        });

        it('should return true for network errors', async () => {
            const { isRetryable } = await import('../errors');

            const networkError = new Error('ECONNREFUSED');
            (networkError as any).code = 'ECONNREFUSED';

            expect(isRetryable(networkError)).toBe(true);
        });

        it('should return true for timeout errors', async () => {
            const { isRetryable } = await import('../errors');

            const timeoutError = new Error('Connection timeout');

            expect(isRetryable(timeoutError)).toBe(true);
        });
    });

    describe('Error code type guards', () => {
        it('should correctly identify Google error codes', async () => {
            const { SEO_ERROR_CODES, isGoogleErrorCode } = await import('../errors');

            expect(isGoogleErrorCode(SEO_ERROR_CODES.GOOGLE_API_ERROR)).toBe(true);
            expect(isGoogleErrorCode(SEO_ERROR_CODES.GOOGLE_AUTH_ERROR)).toBe(true);
            expect(isGoogleErrorCode(SEO_ERROR_CODES.GOOGLE_QUOTA_ERROR)).toBe(true);
        });

        it('should correctly identify validation error codes', async () => {
            const { SEO_ERROR_CODES, isValidationErrorCode } = await import('../errors');

            expect(isValidationErrorCode(SEO_ERROR_CODES.VALIDATION_ERROR)).toBe(true);
            expect(isValidationErrorCode(SEO_ERROR_CODES.INVALID_INPUT_ERROR)).toBe(true);
        });

        it('should correctly identify database error codes', async () => {
            const { SEO_ERROR_CODES, isDatabaseErrorCode } = await import('../errors');

            expect(isDatabaseErrorCode(SEO_ERROR_CODES.DATABASE_ERROR)).toBe(true);
            expect(isDatabaseErrorCode(SEO_ERROR_CODES.DATABASE_CONNECTION_ERROR)).toBe(true);
        });

        it('should correctly identify rate limit error codes', async () => {
            const { SEO_ERROR_CODES, isRateLimitErrorCode } = await import('../errors');

            expect(isRateLimitErrorCode(SEO_ERROR_CODES.RATE_LIMIT_ERROR)).toBe(true);
            expect(isRateLimitErrorCode(SEO_ERROR_CODES.DAILY_LIMIT_EXCEEDED)).toBe(true);
        });
    });

    describe('formatErrorMessage', () => {
        it('should format error message with variables', async () => {
            const { formatErrorMessage } = await import('../errors');

            const message = formatErrorMessage(
                'Failed to connect to {host}:{port}',
                { host: 'localhost', port: 5432 }
            );

            expect(message).toBe('Failed to connect to localhost:5432');
        });

        it('should handle numeric variables', async () => {
            const { formatErrorMessage } = await import('../errors');

            const message = formatErrorMessage(
                'Retry after {seconds} seconds',
                { seconds: 30 }
            );

            expect(message).toBe('Retry after 30 seconds');
        });
    });
});

// ============================================================================
// Tests for retry.ts
// ============================================================================

describe('Retry Logic Infrastructure', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.resetModules();
    });

    describe('sleep', () => {
        it('should resolve after specified milliseconds', async () => {
            const { sleep } = await import('../retry');

            const start = Date.now();
            await sleep(100);
            const elapsed = Date.now() - start;

            expect(elapsed).toBeGreaterThanOrEqual(90);
        });
    });

    describe('calculateExponentialBackoff', () => {
        it('should calculate exponential delay correctly', async () => {
            const { calculateExponentialBackoff } = await import('../retry');

            // Without jitter: baseDelay * multiplier^attempt
            const delay = calculateExponentialBackoff(0, 1000, 30000, 2, false);
            expect(delay).toBe(1000); // 1000 * 2^0 = 1000

            const delay2 = calculateExponentialBackoff(1, 1000, 30000, 2, false);
            expect(delay2).toBe(2000); // 1000 * 2^1 = 2000

            const delay3 = calculateExponentialBackoff(2, 1000, 30000, 2, false);
            expect(delay3).toBe(4000); // 1000 * 2^2 = 4000
        });

        it('should cap at maxDelay', async () => {
            const { calculateExponentialBackoff } = await import('../retry');

            const delay = calculateExponentialBackoff(10, 1000, 30000, 2, false);
            expect(delay).toBe(30000); // Would be 1024000 but capped at 30000
        });

        it('should add jitter when enabled', async () => {
            const { calculateExponentialBackoff } = await import('../retry');

            vi.spyOn(Math, 'random').mockReturnValue(0.5);

            // With jitter: 1000 + (1000 * 0.5 * 0.25) = 1000 + 125 = 1125
            const delay = calculateExponentialBackoff(0, 1000, 30000, 2, true);
            expect(delay).toBe(1125);
        });
    });

    describe('calculateLinearBackoff', () => {
        it('should calculate linear delay correctly', async () => {
            const { calculateLinearBackoff } = await import('../retry');

            // Linear: baseDelay * (1 + attempt * multiplier)
            const delay = calculateLinearBackoff(0, 1000, 30000, 1, false);
            expect(delay).toBe(1000); // 1000 * (1 + 0) = 1000

            const delay2 = calculateLinearBackoff(1, 1000, 30000, 1, false);
            expect(delay2).toBe(2000); // 1000 * (1 + 1) = 2000

            const delay3 = calculateLinearBackoff(2, 1000, 30000, 1, false);
            expect(delay3).toBe(3000); // 1000 * (1 + 2) = 3000
        });

        it('should cap at maxDelay', async () => {
            const { calculateLinearBackoff } = await import('../retry');

            const delay = calculateLinearBackoff(50, 1000, 30000, 1, false);
            expect(delay).toBe(30000);
        });
    });

    describe('calculateFixedBackoff', () => {
        it('should return fixed delay', async () => {
            const { calculateFixedBackoff } = await import('../retry');

            const delay = calculateFixedBackoff(1000, false);
            expect(delay).toBe(1000);
        });

        it('should add jitter when enabled', async () => {
            const { calculateFixedBackoff } = await import('../retry');

            vi.spyOn(Math, 'random').mockReturnValue(0.5);

            const delay = calculateFixedBackoff(1000, true);
            // 1000 + (1000 * 0.5 * 0.25) = 1125
            expect(delay).toBe(1125);
        });
    });

    describe('calculateJitteredBackoff (Full Jitter)', () => {
        it('should return random value between 0 and capped delay', async () => {
            const { calculateJitteredBackoff } = await import('../retry');

            vi.spyOn(Math, 'random').mockReturnValue(0.5);

            // exponentialDelay = 1000 * 2^0 = 1000
            // cappedDelay = min(1000, 30000) = 1000
            // return floor(random * cappedDelay) = floor(0.5 * 1000) = 500
            const delay = calculateJitteredBackoff(0, 1000, 30000, 2);
            expect(delay).toBe(500);
        });

        it('should return 0 when random returns 0', async () => {
            const { calculateJitteredBackoff } = await import('../retry');

            vi.spyOn(Math, 'random').mockReturnValue(0);

            const delay = calculateJitteredBackoff(0, 1000, 30000, 2);
            expect(delay).toBe(0);
        });
    });

    describe('calculateDelay', () => {
        it('should use exponential strategy by default', async () => {
            const { calculateDelay, DEFAULT_RETRY_CONFIG } = await import('../retry');

            const delay = calculateDelay(1, DEFAULT_RETRY_CONFIG);
            // With default config: baseDelay=1000, multiplier=2, useJitter=true
            // Expected: 1000 * 2^1 = 2000 (capped), plus jitter
            expect(delay).toBeGreaterThanOrEqual(2000);
        });

        it('should use linear strategy when specified', async () => {
            const { calculateDelay } = await import('../retry');

            const delay = calculateDelay(1, {
                maxRetries: 3,
                baseDelay: 1000,
                maxDelay: 30000,
                backoffMultiplier: 1,
                retryableStatuses: [],
                timeout: 30000,
                strategy: 'linear',
                useJitter: false
            });

            // Linear: 1000 * (1 + 1 * 1) = 2000
            expect(delay).toBe(2000);
        });

        it('should use fixed strategy when specified', async () => {
            const { calculateDelay } = await import('../retry');

            const delay = calculateDelay(5, {
                maxRetries: 3,
                baseDelay: 1000,
                maxDelay: 30000,
                backoffMultiplier: 2,
                retryableStatuses: [],
                timeout: 30000,
                strategy: 'fixed',
                useJitter: false
            });

            // Fixed: always returns baseDelay
            expect(delay).toBe(1000);
        });

        it('should use jittered strategy when specified', async () => {
            const { calculateDelay } = await import('../retry');

            vi.spyOn(Math, 'random').mockReturnValue(0.5);

            const delay = calculateDelay(0, {
                maxRetries: 3,
                baseDelay: 1000,
                maxDelay: 30000,
                backoffMultiplier: 2,
                retryableStatuses: [],
                timeout: 30000,
                strategy: 'jittered',
                useJitter: false // Not used for jittered strategy
            });

            // Jittered: returns random between 0 and 1000 = 500
            expect(delay).toBe(500);
        });
    });

    describe('DEFAULT_RETRY_CONFIG', () => {
        it('should have correct default values', async () => {
            const { DEFAULT_RETRY_CONFIG } = await import('../retry');

            expect(DEFAULT_RETRY_CONFIG.maxRetries).toBe(3);
            expect(DEFAULT_RETRY_CONFIG.baseDelay).toBe(1000);
            expect(DEFAULT_RETRY_CONFIG.maxDelay).toBe(30000);
            expect(DEFAULT_RETRY_CONFIG.backoffMultiplier).toBe(2);
            expect(DEFAULT_RETRY_CONFIG.strategy).toBe('exponential');
            expect(DEFAULT_RETRY_CONFIG.useJitter).toBe(true);
            expect(DEFAULT_RETRY_CONFIG.retryableStatuses).toContain(429);
            expect(DEFAULT_RETRY_CONFIG.retryableStatuses).toContain(500);
        });
    });

    describe('retry function', () => {
        it('should succeed on first attempt', async () => {
            const { retry } = await import('../retry');

            const result = await retry(() => Promise.resolve('success'));

            expect(result).toBe('success');
        });

        it('should retry on failure and succeed', async () => {
            const { retry } = await import('../retry');

            let attempts = 0;
            const result = await retry(
                () => {
                    attempts++;
                    if (attempts < 2) {
                        return Promise.reject(new Error('Temporary error'));
                    }
                    return Promise.resolve('success');
                },
                { maxRetries: 3, baseDelay: 10 },
                'test-operation'
            );

            expect(result).toBe('success');
            expect(attempts).toBe(2);
        });

        it('should throw when retries exhausted', async () => {
            const { retry } = await import('../retry');

            await expect(
                retry(
                    () => Promise.reject(new Error('Permanent error')),
                    { maxRetries: 2, baseDelay: 10 },
                    'test-operation'
                )
            ).rejects.toThrow('Permanent error');
        });

        it('should call onRetry callback before each retry', async () => {
            const { retry } = await import('../retry');

            const onRetry = vi.fn();
            let attempts = 0;

            await retry(
                () => {
                    attempts++;
                    if (attempts < 3) {
                        return Promise.reject(new Error('Error'));
                    }
                    return Promise.resolve('success');
                },
                { maxRetries: 5, baseDelay: 10, onRetry },
                'test-operation'
            );

            expect(onRetry).toHaveBeenCalledTimes(2);
        });
    });

    describe('retryWithResult', () => {
        it('should return success result', async () => {
            const { retryWithResult } = await import('../retry');

            const result = await retryWithResult(() => Promise.resolve('data'));

            expect(result.success).toBe(true);
            expect(result.value).toBe('data');
            expect(result.attempts).toBe(1);
            expect(result.totalTimeMs).toBeDefined();
        });

        it('should return failure result', async () => {
            const { retryWithResult } = await import('../retry');

            const result = await retryWithResult(
                () => Promise.reject(new Error('Failed')),
                { maxRetries: 0 }
            );

            expect(result.success).toBe(false);
            expect(result.error).toBeDefined();
            expect(result.attempts).toBe(1);
        });
    });

    describe('CircuitBreaker', () => {
        it('should start in closed state', async () => {
            const { CircuitBreaker } = await import('../retry');

            const breaker = new CircuitBreaker();

            expect(breaker.getState()).toBe('closed');
            expect(breaker.isAvailable()).toBe(true);
        });

        it('should open after failure threshold', async () => {
            const { CircuitBreaker } = await import('../retry');

            const breaker = new CircuitBreaker({
                failureThreshold: 3,
                successThreshold: 2,
                timeout: 60000
            });

            // Fail 3 times
            for (let i = 0; i < 3; i++) {
                await expect(breaker.execute(() => Promise.reject(new Error('Error')))).rejects.toThrow();
            }

            expect(breaker.getState()).toBe('open');
            expect(breaker.isAvailable()).toBe(false);
        });

        it('should allow request in half-open state after timeout', async () => {
            const { CircuitBreaker } = await import('../retry');

            const breaker = new CircuitBreaker({
                failureThreshold: 2,
                successThreshold: 1,
                timeout: 100
            });

            // Fail to open the circuit
            await expect(breaker.execute(() => Promise.reject(new Error('Error')))).rejects.toThrow();
            await expect(breaker.execute(() => Promise.reject(new Error('Error')))).rejects.toThrow();

            expect(breaker.getState()).toBe('open');

            // Advance time past timeout
            vi.advanceTimersByTime(101);

            // Next call should be in half-open state
            expect(breaker.getState()).toBe('half-open');
            expect(breaker.isAvailable()).toBe(true);
        });

        it('should close after success threshold in half-open', async () => {
            const { CircuitBreaker } = await import('../retry');

            const breaker = new CircuitBreaker({
                failureThreshold: 2,
                successThreshold: 2,
                timeout: 100
            });

            // Open the circuit
            await expect(breaker.execute(() => Promise.reject(new Error('Error')))).rejects.toThrow();
            await expect(breaker.execute(() => Promise.reject(new Error('Error')))).rejects.toThrow();

            // Move to half-open
            vi.advanceTimersByTime(101);

            // Succeed twice to close
            await breaker.execute(() => Promise.resolve('success'));
            await breaker.execute(() => Promise.resolve('success'));

            expect(breaker.getState()).toBe('closed');
        });
    });

    describe('Specialized retry configs', () => {
        it('should have Google API retry config', async () => {
            const { GOOGLE_API_RETRY_CONFIG } = await import('../retry');

            expect(GOOGLE_API_RETRY_CONFIG.maxRetries).toBe(5);
            expect(GOOGLE_API_RETRY_CONFIG.baseDelay).toBe(1000);
            expect(GOOGLE_API_RETRY_CONFIG.strategy).toBe('exponential');
        });

        it('should have database retry config', async () => {
            const { DATABASE_RETRY_CONFIG } = await import('../retry');

            expect(DATABASE_RETRY_CONFIG.maxRetries).toBe(3);
            expect(DATABASE_RETRY_CONFIG.baseDelay).toBe(500);
        });

        it('should have LLM retry config', async () => {
            const { LLM_RETRY_CONFIG } = await import('../retry');

            expect(LLM_RETRY_CONFIG.maxRetries).toBe(4);
            expect(LLM_RETRY_CONFIG.baseDelay).toBe(2000);
            expect(LLM_RETRY_CONFIG.timeout).toBe(60000);
        });
    });

    describe('retryable function', () => {
        it('should create retryable function', async () => {
            const { retryable } = await import('../retry');

            let attempts = 0;
            const fn = retryable(
                () => {
                    attempts++;
                    if (attempts < 2) {
                        return Promise.reject(new Error('Error'));
                    }
                    return Promise.resolve('success');
                },
                { maxRetries: 3 },
                'test'
            );

            const result = await fn();

            expect(result).toBe('success');
            expect(attempts).toBe(2);
        });
    });
});

// ============================================================================
// Tests for google-api.ts
// ============================================================================

describe('Google API Infrastructure', () => {
    beforeEach(() => {
        vi.resetModules();
        process.env = { ...originalEnv };
    });

    afterEach(() => {
        process.env = { ...originalEnv };
    });

    describe('validateApiKey', () => {
        it('should return invalid for undefined key', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey(undefined);

            expect(result.isValid).toBe(false);
            expect(result.error).toContain('required');
        });

        it('should return invalid for empty string', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey('');

            expect(result.isValid).toBe(false);
            expect(result.error).toContain('empty');
        });

        it('should return invalid for whitespace-only string', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey('   ');

            expect(result.isValid).toBe(false);
            expect(result.error).toContain('empty');
        });

        it('should return invalid for key too short', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey('abc123');

            expect(result.isValid).toBe(false);
            expect(result.error).toContain('too short');
        });

        it('should return invalid for key too long', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey('a'.repeat(51));

            expect(result.isValid).toBe(false);
            expect(result.error).toContain('too long');
        });

        it('should return invalid for key with invalid characters', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey('abc123!@#$%^&*()');

            expect(result.isValid).toBe(false);
            expect(result.error).toContain('invalid characters');
        });

        it('should return valid for standard 39-character key', async () => {
            const { validateApiKey } = await import('../google-api');

            // Standard API key format (39 chars, alphanumeric with - and _)
            const result = validateApiKey('AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789');

            expect(result.isValid).toBe(true);
            expect(result.metadata).toBeDefined();
            expect(result.metadata?.length).toBe(39);
        });

        it('should return valid for server key (40 chars)', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey('AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_');

            expect(result.isValid).toBe(true);
            expect(result.metadata?.format).toBe('server');
        });

        it('should return warnings for lowercase-only key', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey('aizaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');

            expect(result.isValid).toBe(true);
            expect(result.warnings).toBeDefined();
            expect(result.warnings?.[0]).toContain('lowercase');
        });

        it('should return warnings for uppercase-only key', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey('AIZASYABCDEFGHIJKLMNOPQRSTUVWXYZ012345');

            expect(result.isValid).toBe(true);
            expect(result.warnings).toBeDefined();
            expect(result.warnings?.[0]).toContain('uppercase');
        });

        it('should extract prefix correctly', async () => {
            const { validateApiKey } = await import('../google-api');

            const result = validateApiKey('AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789');

            expect(result.metadata?.prefix).toBe('AIza');
        });
    });

    describe('isValidKeyFormat', () => {
        it('should return false for undefined', async () => {
            const { isValidKeyFormat } = await import('../google-api');

            expect(isValidKeyFormat(undefined)).toBe(false);
        });

        it('should return false for null', async () => {
            const { isValidKeyFormat } = await import('../google-api');

            expect(isValidKeyFormat(null)).toBe(false);
        });

        it('should return false for empty string', async () => {
            const { isValidKeyFormat } = await import('../google-api');

            expect(isValidKeyFormat('')).toBe(false);
        });

        it('should return true for valid key format', async () => {
            const { isValidKeyFormat } = await import('../google-api');

            expect(isValidKeyFormat('AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')).toBe(true);
        });

        it('should return true for key with hyphens and underscores', async () => {
            const { isValidKeyFormat } = await import('../google-api');

            expect(isValidKeyFormat('AIzaSy-ABC_DEFGHIJKLMNOPQRSTUVWXYZ01')).toBe(true);
        });

        it('should trim whitespace', async () => {
            const { isValidKeyFormat } = await import('../google-api');

            expect(isValidKeyFormat('  AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789  ')).toBe(true);
        });
    });

    describe('DEFAULT_GOOGLE_API_CONFIG', () => {
        it('should have correct defaults', async () => {
            const { DEFAULT_GOOGLE_API_CONFIG } = await import('../google-api');

            expect(DEFAULT_GOOGLE_API_CONFIG.baseURL).toBe('https://www.googleapis.com');
            expect(DEFAULT_GOOGLE_API_CONFIG.timeout).toBe(30000);
            expect(DEFAULT_GOOGLE_API_CONFIG.validateOnInit).toBe(true);
            expect(DEFAULT_GOOGLE_API_CONFIG.rateLimit.requestsPerSecond).toBe(10);
            expect(DEFAULT_GOOGLE_API_CONFIG.rateLimit.requestsPerMinute).toBe(100);
        });
    });

    describe('DEFAULT_RATE_LIMIT_CONFIG', () => {
        it('should have correct defaults', async () => {
            const { DEFAULT_RATE_LIMIT_CONFIG } = await import('../google-api');

            expect(DEFAULT_RATE_LIMIT_CONFIG.requestsPerSecond).toBe(10);
            expect(DEFAULT_RATE_LIMIT_CONFIG.requestsPerMinute).toBe(100);
            expect(DEFAULT_RATE_LIMIT_CONFIG.maxConcurrent).toBe(5);
            expect(DEFAULT_RATE_LIMIT_CONFIG.queueSize).toBe(1000);
            expect(DEFAULT_RATE_LIMIT_CONFIG.enableBurst).toBe(true);
        });
    });

    describe('GOOGLE_API_ENV_VARS', () => {
        it('should have correct env var names', async () => {
            const { GOOGLE_API_ENV_VARS } = await import('../google-api');

            expect(GOOGLE_API_ENV_VARS.API_KEY).toBe('GOOGLE_API_KEY');
            expect(GOOGLE_API_ENV_VARS.BASE_URL).toBe('GOOGLE_API_BASE_URL');
            expect(GOOGLE_API_ENV_VARS.TIMEOUT).toBe('GOOGLE_API_TIMEOUT');
            expect(GOOGLE_API_ENV_VARS.RATE_LIMIT_RPS).toBe('GOOGLE_API_RATE_LIMIT_RPS');
        });
    });

    describe('validateEnvironmentConfig', () => {
        it('should throw when API key is not set', async () => {
            delete process.env.GOOGLE_API_KEY;
            const { validateEnvironmentConfig } = await import('../google-api');

            expect(() => validateEnvironmentConfig()).toThrow('GOOGLE_API_KEY');
        });

        it('should throw when API key format is invalid', async () => {
            process.env.GOOGLE_API_KEY = 'short';
            const { validateEnvironmentConfig } = await import('../google-api');

            expect(() => validateEnvironmentConfig()).toThrow('Invalid API key format');
        });

        it('should accept valid API key', async () => {
            process.env.GOOGLE_API_KEY = 'AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
            const { validateEnvironmentConfig } = await import('../google-api');

            const config = validateEnvironmentConfig();

            expect(config.apiKey).toBeDefined();
        });

        it('should parse optional timeout', async () => {
            process.env.GOOGLE_API_KEY = 'AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
            process.env.GOOGLE_API_TIMEOUT = '60000';
            const { validateEnvironmentConfig } = await import('../google-api');

            const config = validateEnvironmentConfig();

            expect(config.timeout).toBe(60000);
        });

        it('should reject invalid timeout range', async () => {
            process.env.GOOGLE_API_KEY = 'AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
            process.env.GOOGLE_API_TIMEOUT = '500';
            const { validateEnvironmentConfig } = await import('../google-api');

            expect(() => validateEnvironmentConfig()).toThrow('Timeout must be between');
        });

        it('should parse optional base URL', async () => {
            process.env.GOOGLE_API_KEY = 'AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
            process.env.GOOGLE_API_BASE_URL = 'https://custom.googleapis.com';
            const { validateEnvironmentConfig } = await import('../google-api');

            const config = validateEnvironmentConfig();

            expect(config.baseURL).toBe('https://custom.googleapis.com');
        });

        it('should reject invalid base URL', async () => {
            process.env.GOOGLE_API_KEY = 'AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
            process.env.GOOGLE_API_BASE_URL = 'not-a-url';
            const { validateEnvironmentConfig } = await import('../google-api');

            expect(() => validateEnvironmentConfig()).toThrow('Invalid base URL');
        });

        it('should parse rate limit RPS', async () => {
            process.env.GOOGLE_API_KEY = 'AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
            process.env.GOOGLE_API_RATE_LIMIT_RPS = '50';
            const { validateEnvironmentConfig } = await import('../google-api');

            const config = validateEnvironmentConfig();

            expect(config.rateLimit?.requestsPerSecond).toBe(50);
        });
    });
});

// ============================================================================
// Tests for database.ts
// ============================================================================

describe('Database Infrastructure', () => {
    beforeEach(() => {
        vi.resetModules();
        process.env = { ...originalEnv };
        process.env.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb';
    });

    afterEach(() => {
        process.env = { ...originalEnv };
        vi.resetModules();
    });

    describe('getDatabaseConfig', () => {
        it('should throw when DATABASE_URL is not set', async () => {
            delete process.env.DATABASE_URL;
            // Need to reimport after deleting env var
            const { getDatabaseConfig } = await import('../database');

            expect(() => getDatabaseConfig()).toThrow('DATABASE_URL');
        });

        it('should return config from environment', async () => {
            process.env.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb';
            const { getDatabaseConfig } = await import('../database');

            const config = getDatabaseConfig();

            expect(config.connectionString).toBe('postgresql://user:pass@localhost:5432/testdb');
            expect(config.pool.max).toBe(20);
            expect(config.pool.min).toBe(2);
        });

        it('should parse pool config from environment', async () => {
            process.env.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb';
            process.env.DB_POOL_MAX = '30';
            process.env.DB_POOL_MIN = '5';
            const { getDatabaseConfig } = await import('../database');

            const config = getDatabaseConfig();

            expect(config.pool.max).toBe(30);
            expect(config.pool.min).toBe(5);
        });

        it('should parse SSL config from environment', async () => {
            process.env.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb';
            process.env.DB_SSL_ENABLED = 'true';
            const { getDatabaseConfig } = await import('../database');

            const config = getDatabaseConfig();

            expect(config.ssl.enabled).toBe(true);
        });

        it('should parse query timeout from environment', async () => {
            process.env.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb';
            process.env.DB_QUERY_TIMEOUT_MS = '60000';
            const { getDatabaseConfig } = await import('../database');

            const config = getDatabaseConfig();

            expect(config.queryTimeoutMs).toBe(60000);
        });
    });

    describe('DEFAULT_POOL_CONFIG', () => {
        it('should have correct defaults', async () => {
            const { DEFAULT_POOL_CONFIG } = await import('../database');

            expect(DEFAULT_POOL_CONFIG.max).toBe(20);
            expect(DEFAULT_POOL_CONFIG.min).toBe(2);
            expect(DEFAULT_POOL_CONFIG.idleTimeoutMs).toBe(30000);
            expect(DEFAULT_POOL_CONFIG.connectionTimeoutMs).toBe(10000);
            expect(DEFAULT_POOL_CONFIG.maxLifetimeMs).toBe(3600000);
        });
    });

    describe('DEFAULT_SSL_CONFIG', () => {
        it('should have correct defaults', async () => {
            const { DEFAULT_SSL_CONFIG } = await import('../database');

            expect(DEFAULT_SSL_CONFIG.enabled).toBe(false);
            expect(DEFAULT_SSL_CONFIG.mode).toBe('require');
            expect(DEFAULT_SSL_CONFIG.rejectUnauthorized).toBe(false);
        });
    });
});

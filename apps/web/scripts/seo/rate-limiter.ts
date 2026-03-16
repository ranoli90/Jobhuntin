/**
 * Rate Limiter Module
 * 
 * Token bucket algorithm implementation for API rate limiting.
 * Provides configurable rate limiting for SEO API calls to prevent
 * hitting external service limits.
 */

import { SEOEngineError, ErrorCode } from './errors.js';

/**
 * Rate limiter configuration
 */
export interface RateLimiterConfig {
    /** Maximum requests allowed per minute */
    maxRequestsPerMinute: number;
    /** Optional: Maximum burst capacity (defaults to maxRequestsPerMinute) */
    burstCapacity?: number;
}

/**
 * Token bucket rate limiter implementation
 * 
 * Uses the token bucket algorithm to control request rates:
 * - Tokens are added at a constant rate (refillRate)
 * - Each request consumes a token
 * - If no tokens available, request must wait
 * 
 * This allows for burst traffic while maintaining average rate limits.
 */
export class RateLimiter {
    private tokens: number;
    private readonly maxTokens: number;
    private readonly refillRate: number; // tokens per millisecond
    private lastRefillTime: number;
    private readonly burstCapacity: number;

    /**
     * Create a new rate limiter
     * 
     * @param maxRequestsPerMinute - Maximum requests allowed per minute
     * @param burstCapacity - Optional burst capacity (defaults to maxRequestsPerMinute)
     */
    constructor(maxRequestsPerMinute: number, burstCapacity?: number) {
        if (maxRequestsPerMinute <= 0) {
            throw new SEOEngineError(
                'Rate limiter must have positive maxRequestsPerMinute',
                ErrorCode.VALIDATION_FAILED,
                { maxRequestsPerMinute }
            );
        }

        this.maxTokens = maxRequestsPerMinute;
        this.burstCapacity = burstCapacity ?? maxRequestsPerMinute;
        this.tokens = this.maxTokens;
        this.refillRate = this.maxTokens / 60000; // tokens per millisecond
        this.lastRefillTime = Date.now();
    }

    /**
     * Acquire a token, waiting if necessary
     * 
     * If tokens are available, returns immediately.
     * If no tokens available, waits until tokens are replenished.
     * 
     * @returns Promise that resolves when a token is acquired
     */
    async acquire(): Promise<void> {
        this.refill();

        if (this.tokens >= 1) {
            this.tokens -= 1;
            return;
        }

        // Calculate wait time for tokens to replenish
        const tokensNeeded = 1;
        const waitTimeMs = (tokensNeeded - this.tokens) / this.refillRate;

        // Wait for tokens to become available
        await this.sleep(waitTimeMs);

        // Refill again after waiting
        this.refill();
        this.tokens -= 1;
    }

    /**
     * Try to acquire a token without waiting
     * 
     * @returns true if token acquired, false if no tokens available
     */
    tryAcquire(): boolean {
        this.refill();

        if (this.tokens >= 1) {
            this.tokens -= 1;
            return true;
        }

        return false;
    }

    /**
     * Get current token count (for monitoring/debugging)
     * 
     * @returns Current available tokens
     */
    getAvailableTokens(): number {
        this.refill();
        return Math.floor(this.tokens);
    }

    /**
     * Reset the rate limiter
     * 
     * Restores all tokens to maximum capacity.
     * Useful for testing or after a period of inactivity.
     */
    reset(): void {
        this.tokens = this.maxTokens;
        this.lastRefillTime = Date.now();
    }

    /**
     * Refill tokens based on elapsed time
     */
    private refill(): void {
        const now = Date.now();
        const elapsed = now - this.lastRefillTime;

        // Add tokens based on elapsed time
        const tokensToAdd = elapsed * this.refillRate;
        this.tokens = Math.min(this.tokens + tokensToAdd, this.burstCapacity);
        this.lastRefillTime = now;
    }

    /**
     * Sleep for specified milliseconds
     */
    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, Math.ceil(ms)));
    }
}

/**
 * Create a rate limiter from configuration
 * 
 * @param config - Rate limiter configuration
 * @returns Configured RateLimiter instance
 */
export function createRateLimiter(config: RateLimiterConfig): RateLimiter {
    return new RateLimiter(config.maxRequestsPerMinute, config.burstCapacity);
}

/**
 * Common rate limiter presets
 */
export const RateLimiterPresets = {
    /** Google Indexing API: 100 requests per 100 seconds */
    googleIndexing: () => new RateLimiter(100, 100),

    /** Google Search Console: 60 requests per minute */
    searchConsole: () => new RateLimiter(60, 60),

    /** General API: 60 requests per minute */
    general: () => new RateLimiter(60, 60),

    /** Aggressive: 120 requests per minute */
    aggressive: () => new RateLimiter(120, 120),

    /** Conservative: 30 requests per minute */
    conservative: () => new RateLimiter(30, 30),
} as const;

/**
 * Create a composed rate limiter that handles multiple rate limiters
 * Useful when working with multiple APIs with different limits
 */
export class MultiRateLimiter {
    private limiters: Map<string, RateLimiter>;

    constructor() {
        this.limiters = new Map();
    }

    /**
     * Add a named rate limiter
     */
    addLimiter(name: string, limiter: RateLimiter): void {
        this.limiters.set(name, limiter);
    }

    /**
     * Acquire tokens from all limiters
     * Waits for the slowest limiter
     */
    async acquireAll(): Promise<void> {
        const promises: Promise<void>[] = [];

        for (const [, limiter] of Array.from(this.limiters.entries())) {
            promises.push(limiter.acquire());
        }

        await Promise.all(promises);
    }

    /**
     * Try to acquire from all limiters without waiting
     * 
     * @returns true if all limiters have tokens available
     */
    tryAcquireAll(): boolean {
        for (const [, limiter] of Array.from(this.limiters.entries())) {
            if (!limiter.tryAcquire()) {
                return false;
            }
        }
        return true;
    }

    /**
     * Reset all limiters
     */
    resetAll(): void {
        for (const [, limiter] of Array.from(this.limiters.entries())) {
            limiter.reset();
        }
    }
}

export default RateLimiter;

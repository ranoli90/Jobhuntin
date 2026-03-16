/**
 * Google API Wrapper
 * 
 * Comprehensive Google API wrapper with configuration validation,
 * API key validation, rate limiting using token bucket algorithm,
 * and specialized methods for Google Search operations.
 * 
 * @module seo/google-api
 */

// ============================================================================
// Imports
// ============================================================================

import {
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    ValidationError as SEOValidationError,
    SEO_ERROR_CODES,
} from './errors';

import { retryGoogleAPI, RetryConfig } from './retry';

import { Logger, LogLevel, APILogger } from './logger';

import { MetricsCollector, SEO_METRIC_NAMES, MetricType } from './metrics';

import { validateUrl, validateTopic, validateCompetitor } from './validators';

import { getConfig } from './config';

// ============================================================================
// Google API Configuration
// ============================================================================

/**
 * Google API configuration interface
 */
export interface GoogleAPIConfig {
    /** Google API key for authentication */
    apiKey: string;
    /** Base URL for Google API */
    baseURL: string;
    /** Request timeout in milliseconds */
    timeout: number;
    /** Rate limit configuration */
    rateLimit: RateLimitConfig;
    /** Enable/disable API key validation on init */
    validateOnInit: boolean;
    /** Custom user agent */
    userAgent: string;
}

/**
 * Rate limit configuration
 */
export interface RateLimitConfig {
    /** Maximum requests per second */
    requestsPerSecond: number;
    /** Maximum requests per minute */
    requestsPerMinute: number;
    /** Maximum concurrent requests */
    maxConcurrent: number;
    /** Queue size limit (0 for unlimited) */
    queueSize: number;
    /** Enable burst handling */
    enableBurst: boolean;
}

/**
 * Default Google API configuration
 */
export const DEFAULT_GOOGLE_API_CONFIG: GoogleAPIConfig = {
    apiKey: '',
    baseURL: 'https://www.googleapis.com',
    timeout: 30000,
    rateLimit: {
        requestsPerSecond: 10,
        requestsPerMinute: 100,
        maxConcurrent: 5,
        queueSize: 1000,
        enableBurst: true,
    },
    validateOnInit: true,
    userAgent: 'SEO-Engine/1.0',
};

/**
 * Default rate limit configuration
 */
export const DEFAULT_RATE_LIMIT_CONFIG: RateLimitConfig = {
    requestsPerSecond: 10,
    requestsPerMinute: 100,
    maxConcurrent: 5,
    queueSize: 1000,
    enableBurst: true,
};

// ============================================================================
// Environment Variable Validation
// ============================================================================

/**
 * Environment variable names for Google API
 */
export const GOOGLE_API_ENV_VARS = {
    API_KEY: 'GOOGLE_API_KEY',
    BASE_URL: 'GOOGLE_API_BASE_URL',
    TIMEOUT: 'GOOGLE_API_TIMEOUT',
    RATE_LIMIT_RPS: 'GOOGLE_API_RATE_LIMIT_RPS',
    RATE_LIMIT_RPM: 'GOOGLE_API_RATE_LIMIT_RPM',
    MAX_CONCURRENT: 'GOOGLE_API_MAX_CONCURRENT',
} as const;

/**
 * Validate environment variable configuration
 * 
 * @returns Validated configuration object
 * @throws Error if required environment variables are missing or invalid
 */
export function validateEnvironmentConfig(): Partial<GoogleAPIConfig> {
    const config: Partial<GoogleAPIConfig> = {};

    // Validate required API key
    const apiKey = process.env[GOOGLE_API_ENV_VARS.API_KEY];
    if (!apiKey) {
        throw new SEOValidationError(
            'GOOGLE_API_KEY',
            'Required environment variable GOOGLE_API_KEY is not set',
            process.env[GOOGLE_API_ENV_VARS.API_KEY]
        );
    }

    // Validate API key format
    const validationResult = validateApiKey(apiKey);
    if (!validationResult.isValid) {
        throw new SEOValidationError(
            'GOOGLE_API_KEY',
            `Invalid API key format: ${validationResult.error}`,
            apiKey
        );
    }

    config.apiKey = apiKey;

    // Validate optional base URL
    if (process.env[GOOGLE_API_ENV_VARS.BASE_URL]) {
        const baseURL = process.env[GOOGLE_API_ENV_VARS.BASE_URL];
        try {
            new URL(baseURL);
            config.baseURL = baseURL;
        } catch {
            throw new SEOValidationError(
                'GOOGLE_API_BASE_URL',
                'Invalid base URL format',
                baseURL
            );
        }
    }

    // Validate timeout
    if (process.env[GOOGLE_API_ENV_VARS.TIMEOUT]) {
        const timeout = parseInt(process.env[GOOGLE_API_ENV_VARS.TIMEOUT], 10);
        if (isNaN(timeout) || timeout < 1000 || timeout > 300000) {
            throw new SEOValidationError(
                'GOOGLE_API_TIMEOUT',
                'Timeout must be between 1000 and 300000 milliseconds',
                timeout
            );
        }
        config.timeout = timeout;
    }

    // Validate rate limit RPS
    if (process.env[GOOGLE_API_ENV_VARS.RATE_LIMIT_RPS]) {
        const rps = parseInt(process.env[GOOGLE_API_ENV_VARS.RATE_LIMIT_RPS], 10);
        if (isNaN(rps) || rps < 1 || rps > 100) {
            throw new SEOValidationError(
                'GOOGLE_API_RATE_LIMIT_RPS',
                'Rate limit RPS must be between 1 and 100',
                rps
            );
        }
        if (!config.rateLimit) {
            config.rateLimit = { ...DEFAULT_RATE_LIMIT_CONFIG };
        }
        config.rateLimit.requestsPerSecond = rps;
    }

    // Validate rate limit RPM
    if (process.env[GOOGLE_API_ENV_VARS.RATE_LIMIT_RPM]) {
        const rpm = parseInt(process.env[GOOGLE_API_ENV_VARS.RATE_LIMIT_RPM], 10);
        if (isNaN(rpm) || rpm < 1 || rpm > 6000) {
            throw new SEOValidationError(
                'GOOGLE_API_RATE_LIMIT_RPM',
                'Rate limit RPM must be between 1 and 6000',
                rpm
            );
        }
        if (!config.rateLimit) {
            config.rateLimit = { ...DEFAULT_RATE_LIMIT_CONFIG };
        }
        config.rateLimit.requestsPerMinute = rpm;
    }

    // Validate max concurrent
    if (process.env[GOOGLE_API_ENV_VARS.MAX_CONCURRENT]) {
        const maxConcurrent = parseInt(process.env[GOOGLE_API_ENV_VARS.MAX_CONCURRENT], 10);
        if (isNaN(maxConcurrent) || maxConcurrent < 1 || maxConcurrent > 50) {
            throw new SEOValidationError(
                'GOOGLE_API_MAX_CONCURRENT',
                'Max concurrent must be between 1 and 50',
                maxConcurrent
            );
        }
        if (!config.rateLimit) {
            config.rateLimit = { ...DEFAULT_RATE_LIMIT_CONFIG };
        }
        config.rateLimit.maxConcurrent = maxConcurrent;
    }

    return config;
}

// ============================================================================
// API Key Validation
// ============================================================================

/**
 * API key validation result
 */
export interface ApiKeyValidationResult {
    /** Whether the key is valid */
    isValid: boolean;
    /** Error message if invalid */
    error?: string;
    /** Warning messages */
    warnings?: string[];
    /** Key metadata if available */
    metadata?: {
        length: number;
        prefix?: string;
        format: 'standard' | 'server' | 'browser';
    };
}

/**
 * Google API key format patterns
 */
const GOOGLE_API_KEY_PATTERNS = {
    // Standard API key (39 characters, alphanumeric)
    STANDARD: /^[A-Za-z0-9_-]{39}$/,
    // Server key (40 characters)
    SERVER: /^[A-Za-z0-9_-]{40}$/,
    // Browser key (39 characters)
    BROWSER: /^[A-Za-z0-9_-]{39}$/,
    // iOS key (40 characters)
    IOS: /^[A-Za-z0-9_-]{40}$/,
};

/**
 * Minimum and maximum key lengths
 */
const MIN_KEY_LENGTH = 20;
const MAX_KEY_LENGTH = 50;

/**
 * Check if key format is valid (not empty, correct length, alphanumeric)
 * 
 * @param key - The API key to validate
 * @returns True if format is valid
 */
export function isValidKeyFormat(key: string | undefined | null): boolean {
    // Check if key exists and is a string
    if (!key || typeof key !== 'string') {
        return false;
    }

    // Check trimmed key is not empty
    const trimmedKey = key.trim();
    if (trimmedKey.length === 0) {
        return false;
    }

    // Check length constraints
    if (trimmedKey.length < MIN_KEY_LENGTH || trimmedKey.length > MAX_KEY_LENGTH) {
        return false;
    }

    // Check key contains only alphanumeric characters, hyphens, and underscores
    if (!/^[A-Za-z0-9_-]+$/.test(trimmedKey)) {
        return false;
    }

    return true;
}

/**
 * Validate Google API key format and structure
 * 
 * @param key - The API key to validate
 * @returns Validation result with details
 */
export function validateApiKey(key: string | undefined | null): ApiKeyValidationResult {
    const warnings: string[] = [];

    // Check if key exists
    if (!key || typeof key !== 'string') {
        return {
            isValid: false,
            error: 'API key is required and must be a non-empty string',
        };
    }

    const trimmedKey = key.trim();

    // Check if empty after trimming
    if (trimmedKey.length === 0) {
        return {
            isValid: false,
            error: 'API key cannot be empty',
        };
    }

    // Check length
    if (trimmedKey.length < MIN_KEY_LENGTH) {
        return {
            isValid: false,
            error: `API key is too short (minimum ${MIN_KEY_LENGTH} characters)`,
        };
    }

    if (trimmedKey.length > MAX_KEY_LENGTH) {
        return {
            isValid: false,
            error: `API key is too long (maximum ${MAX_KEY_LENGTH} characters)`,
        };
    }

    // Check alphanumeric with allowed characters
    if (!/^[A-Za-z0-9_-]+$/.test(trimmedKey)) {
        return {
            isValid: false,
            error: 'API key contains invalid characters (only alphanumeric, hyphens, and underscores allowed)',
        };
    }

    // Determine key format
    let format: 'standard' | 'server' | 'browser' = 'standard';
    if (GOOGLE_API_KEY_PATTERNS.SERVER.test(trimmedKey)) {
        format = 'server';
    } else if (GOOGLE_API_KEY_PATTERNS.BROWSER.test(trimmedKey)) {
        format = 'browser';
    } else if (trimmedKey.length === 39) {
        format = 'standard';
    }

    // Warn about common issues
    if (trimmedKey === trimmedKey.toLowerCase()) {
        warnings.push('API key contains only lowercase characters');
    }

    if (trimmedKey === trimmedKey.toUpperCase()) {
        warnings.push('API key contains only uppercase characters');
    }

    // Extract prefix if any
    const prefix = trimmedKey.substring(0, 4);

    return {
        isValid: true,
        warnings: warnings.length > 0 ? warnings : undefined,
        metadata: {
            length: trimmedKey.length,
            prefix,
            format,
        },
    };
}

/**
 * Test API key validity with a simple API call
 * 
 * @param apiKey - The API key to test
 * @param baseURL - Optional base URL override
 * @returns Promise resolving to validity result
 */
export async function testApiKeyValidity(
    apiKey: string,
    baseURL: string = DEFAULT_GOOGLE_API_CONFIG.baseURL
): Promise<{ isValid: boolean; error?: string; responseTime?: number }> {
    const startTime = Date.now();

    try {
        // Use the Custom Search API to test the key
        const testUrl = `${baseURL}/customsearch/v1?key=${apiKey}&cx=test&q=test`;

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(testUrl, {
            method: 'GET',
            signal: controller.signal,
            headers: {
                'User-Agent': 'SEO-Engine/1.0',
            },
        });

        clearTimeout(timeoutId);

        const responseTime = Date.now() - startTime;

        // Check response status
        if (response.status === 200) {
            return {
                isValid: true,
                responseTime,
            };
        } else if (response.status === 403) {
            return {
                isValid: false,
                error: 'API key is invalid or has been revoked',
                responseTime,
            };
        } else if (response.status === 429) {
            return {
                isValid: true,
                error: 'API key is valid but rate limited',
                responseTime,
            };
        } else {
            return {
                isValid: false,
                error: `API returned unexpected status: ${response.status}`,
                responseTime,
            };
        }
    } catch (error) {
        const responseTime = Date.now() - startTime;

        if (error instanceof Error) {
            if (error.name === 'AbortError') {
                return {
                    isValid: false,
                    error: 'API key validation timed out',
                    responseTime,
                };
            }

            return {
                isValid: false,
                error: `Network error: ${error.message}`,
                responseTime,
            };
        }

        return {
            isValid: false,
            error: 'Unknown error during API key validation',
            responseTime,
        };
    }
}

// ============================================================================
// Rate Limiter (Token Bucket Algorithm)
// ============================================================================

/**
 * Queued request with metadata
 */
interface QueuedRequest<T> {
    /** Unique request ID */
    id: string;
    /** Request function */
    fn: () => Promise<T>;
    /** Resolve function */
    resolve: (value: T) => void;
    /** Reject function */
    reject: (error: Error) => void;
    /** Request priority (higher = more urgent) */
    priority: number;
    /** Timestamp when request was queued */
    queuedAt: number;
    /** Number of retries attempted */
    retries: number;
}

/**
 * Rate limiter using token bucket algorithm
 */
export class RateLimiter {
    private tokens: number;
    private lastRefill: number;
    private requestsPerSecond: number;
    private requestsPerMinute: number;
    private maxConcurrent: number;
    private queueSize: number;
    private enableBurst: boolean;
    private queue: QueuedRequest<any>[];
    private processing: number;
    private logger: Logger;

    /**
     * Create a new rate limiter
     * 
     * @param config - Rate limit configuration
     * @param logger - Optional logger instance
     */
    constructor(
        config: Partial<RateLimitConfig> = {},
        logger?: Logger
    ) {
        this.requestsPerSecond = config.requestsPerSecond ?? DEFAULT_RATE_LIMIT_CONFIG.requestsPerSecond;
        this.requestsPerMinute = config.requestsPerMinute ?? DEFAULT_RATE_LIMIT_CONFIG.requestsPerMinute;
        this.maxConcurrent = config.maxConcurrent ?? DEFAULT_RATE_LIMIT_CONFIG.maxConcurrent;
        this.queueSize = config.queueSize ?? DEFAULT_RATE_LIMIT_CONFIG.queueSize;
        this.enableBurst = config.enableBurst ?? DEFAULT_RATE_LIMIT_CONFIG.enableBurst;

        // Initialize token bucket
        this.tokens = this.enableBurst ? this.requestsPerSecond : 0;
        this.lastRefill = Date.now();

        this.queue = [];
        this.processing = 0;
        this.logger = logger ?? new Logger({ level: LogLevel.INFO });

        // Start refill interval
        this.startRefillInterval();
    }

    /**
     * Start the token refill interval
     */
    private startRefillInterval(): void {
        // Refill every 100ms for smooth rate limiting
        setInterval(() => this.refillTokens(), 100);

        // Also refill per second
        setInterval(() => this.refillTokensPerSecond(), 1000);
    }

    /**
     * Refill tokens based on time elapsed (per second)
     */
    private refillTokensPerSecond(): void {
        const now = Date.now();
        const elapsed = (now - this.lastRefill) / 1000;

        if (elapsed >= 1) {
            const tokensToAdd = Math.floor(elapsed * this.requestsPerSecond);
            this.tokens = Math.min(this.tokens + tokensToAdd, this.requestsPerSecond);
            this.lastRefill = now;
        }
    }

    /**
     * Refill tokens smoothly
     */
    private refillTokens(): void {
        // Add fractional tokens every 100ms
        const tokensPerTick = this.requestsPerSecond / 10;

        // Check if we can add tokens (respecting per-minute limit)
        const estimatedRPM = this.estimateCurrentRPM();

        if (estimatedRPM < this.requestsPerMinute) {
            this.tokens = Math.min(this.tokens + tokensPerTick, this.requestsPerSecond);
        }
    }

    /**
     * Estimate current requests per minute
     */
    private estimateCurrentRPM(): number {
        // Simple estimation based on recent queue activity
        const now = Date.now();
        const recentRequests = this.queue.filter(
            r => now - r.queuedAt < 60000
        ).length + this.processing;

        return recentRequests;
    }

    /**
     * Wait for available tokens
     */
    private async waitForToken(): Promise<void> {
        while (this.tokens < 1) {
            // Calculate wait time
            const waitTime = Math.ceil((1 - this.tokens) / (this.requestsPerSecond / 1000));
            await new Promise(resolve => setTimeout(resolve, Math.min(waitTime, 100)));
        }

        this.tokens -= 1;
    }

    /**
     * Wait for concurrent slot
     */
    private async waitForConcurrentSlot(): Promise<void> {
        while (this.processing >= this.maxConcurrent) {
            await new Promise(resolve => setTimeout(resolve, 50));
        }

        this.processing += 1;
    }

    /**
     * Execute a request with rate limiting
     * 
     * @param fn - Function to execute
     * @param priority - Request priority (higher = more urgent)
     * @returns Promise resolving to function result
     */
    async execute<T>(fn: () => Promise<T>, priority: number = 0): Promise<T> {
        // Check queue size
        if (this.queueSize > 0 && this.queue.length >= this.queueSize) {
            throw new Error(`Rate limit queue full (max ${this.queueSize} requests)`);
        }

        return new Promise((resolve, reject) => {
            const request: QueuedRequest<T> = {
                id: `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
                fn,
                resolve,
                reject,
                priority,
                queuedAt: Date.now(),
                retries: 0,
            };

            // Add to queue sorted by priority
            this.addToQueue(request);

            // Try to process
            this.processQueue();
        });
    }

    /**
     * Add request to queue
     */
    private addToQueue<T>(request: QueuedRequest<T>): void {
        this.queue.push(request);

        // Sort by priority (higher first) then by time (earlier first)
        this.queue.sort((a, b) => {
            if (a.priority !== b.priority) {
                return b.priority - a.priority;
            }
            return a.queuedAt - b.queuedAt;
        });
    }

    /**
     * Process queued requests
     */
    private async processQueue(): Promise<void> {
        // Process as many requests as possible
        while (this.queue.length > 0 && this.processing < this.maxConcurrent) {
            const request = this.queue.shift();

            if (!request) break;

            // Wait for token and concurrent slot
            try {
                await this.waitForToken();
                await this.waitForConcurrentSlot();

                // Execute the request
                this.executeRequest(request);
            } catch (error) {
                request.reject(error instanceof Error ? error : new Error(String(error)));
            }
        }
    }

    /**
     * Execute a single request
     */
    private async executeRequest<T>(request: QueuedRequest<T>): Promise<void> {
        try {
            const result = await request.fn();
            request.resolve(result);
        } catch (error) {
            request.reject(error instanceof Error ? error : new Error(String(error)));
        } finally {
            this.processing -= 1;

            // Try to process more requests
            this.processQueue();
        }
    }

    /**
     * Get current queue size
     */
    getQueueSize(): number {
        return this.queue.length;
    }

    /**
     * Get number of currently processing requests
     */
    getProcessingCount(): number {
        return this.processing;
    }

    /**
     * Get available tokens
     */
    getAvailableTokens(): number {
        return Math.floor(this.tokens);
    }

    /**
     * Get current rate (estimated RPM)
     */
    getCurrentRate(): number {
        return this.estimateCurrentRPM();
    }

    /**
     * Clear the queue
     */
    clearQueue(): void {
        const cleared = this.queue.length;
        this.queue.forEach(req => {
            req.reject(new Error('Queue cleared'));
        });
        this.queue = [];

        this.logger.debug(`Cleared ${cleared} requests from rate limit queue`);
    }

    /**
     * Get queue statistics
     */
    getStats(): {
        queueSize: number;
        processing: number;
        availableTokens: number;
        estimatedRPM: number;
    } {
        return {
            queueSize: this.queue.length,
            processing: this.processing,
            availableTokens: this.getAvailableTokens(),
            estimatedRPM: this.getCurrentRate(),
        };
    }
}

// ============================================================================
// Google Search API Wrapper
// ============================================================================

/**
 * Search options
 */
export interface SearchOptions {
    /** Number of results to return (1-10) */
    numResults?: number;
    /** Start index for pagination */
    startIndex?: number;
    /** Safe search level */
    safeSearch?: 'off' | 'medium' | 'high';
    /** Language code */
    language?: string;
    /** Country code */
    country?: string;
    /** Search type (images, news, etc.) */
    searchType?: 'search' | 'images' | 'news' | 'videos';
    /** File type filter */
    fileType?: string;
    /** Date restriction (past number of days) */
    dateRestrict?: number;
}

/**
 * Search result item
 */
export interface SearchResultItem {
    /** Result title */
    title: string;
    /** Result URL */
    url: string;
    /** Result snippet/description */
    snippet?: string;
    /** Display URL */
    displayUrl?: string;
    /** MIME type */
    mimeType?: string;
    /** File format */
    fileFormat?: string;
    /** Image info (if image search) */
    image?: {
        url: string;
        width?: number;
        height?: number;
        byteSize?: number;
        thumbnailUrl?: string;
    };
    /** Page map data */
    pageMap?: Record<string, any>;
}

/**
 * Search result
 */
export interface SearchResult {
    /** Array of search results */
    items: SearchResultItem[];
    /** Total number of results */
    totalResults: number;
    /** Number of results returned */
    count: number;
    /** Search query */
    query: string;
    /** Whether there are more results */
    hasMore: boolean;
    /** Next start index for pagination */
    nextStartIndex?: number;
}

/**
 * Page speed result
 */
export interface PageSpeedResult {
    /** URL analyzed */
    url: string;
    /** Loading experience metrics */
    loadingExperience?: {
        overall_category: 'FAST' | 'NEEDS_WORK' | 'SLOW' | 'MODERATE';
        metrics?: Record<string, {
            percentiles: {
                p75: number;
            };
            category: string;
        }>;
    };
    /** Lighthouse performance score (0-100) */
    lighthouseResult?: {
        categories: {
            performance: {
                score: number;
            };
        };
        audits?: Record<string, any>;
    };
    /** Request ID */
    requestId?: string;
}

/**
 * URL submission result
 */
export interface URLSubmissionResult {
    /** URL submitted */
    url: string;
    /** Whether submission was successful */
    success: boolean;
    /** Message from Google */
    message?: string;
    /** Error details if failed */
    error?: {
        code: string;
        message: string;
    };
    /** Timestamp of submission */
    submittedAt: string;
}

/**
 * Index status result
 */
export interface IndexStatusResult {
    /** URL checked */
    url: string;
    /** Whether URL is indexed */
    indexed: boolean;
    /** Indexing status */
    status: 'INDEXED' | 'NOT_INDEXED' | 'UNKNOWN' | 'ERROR';
    /** Last crawled date if available */
    lastCrawled?: string;
    /** Error message if error */
    error?: string;
    /** Additional metadata */
    metadata?: Record<string, any>;
}

/**
 * Google Search API wrapper class
 */
export class GoogleSearchAPI {
    private config: GoogleAPIConfig;
    private rateLimiter: RateLimiter;
    private logger: APILogger;
    private metrics: MetricsCollector;
    private initialized: boolean;

    /**
     * Create a new Google Search API instance
     * 
     * @param config - Optional configuration override
     */
    constructor(config?: Partial<GoogleAPIConfig>) {
        // Merge configurations
        const envConfig = this.loadEnvironmentConfig();
        const mergedConfig = { ...DEFAULT_GOOGLE_API_CONFIG, ...envConfig, ...config };

        this.config = mergedConfig as GoogleAPIConfig;
        this.rateLimiter = new RateLimiter(this.config.rateLimit);
        this.logger = new APILogger({
            name: 'GoogleSearchAPI',
            level: LogLevel.INFO,
        });
        this.metrics = new MetricsCollector();
        this.initialized = false;

        // Validate on init if enabled
        if (this.config.validateOnInit) {
            this.initialize();
        }
    }

    /**
     * Load configuration from environment
     */
    private loadEnvironmentConfig(): Partial<GoogleAPIConfig> {
        try {
            return validateEnvironmentConfig();
        } catch (error) {
            // Log warning but don't throw during config loading
            this.logger.warn('Failed to load environment config', {
                error: error instanceof Error ? error.message : String(error),
            });
            return {};
        }
    }

    /**
     * Initialize and validate API key
     */
    async initialize(): Promise<void> {
        if (this.initialized) {
            return;
        }

        // Validate API key format
        const validation = validateApiKey(this.config.apiKey);
        if (!validation.isValid) {
            throw new GoogleAuthError(
                `Invalid API key format: ${validation.error}`,
                { service: 'customsearch' }
            );
        }

        // Test API key with a simple call
        const keyTest = await testApiKeyValidity(this.config.apiKey, this.config.baseURL);

        if (!keyTest.isValid) {
            throw new GoogleAuthError(
                `API key validation failed: ${keyTest.error}`,
                { service: 'customsearch' }
            );
        }

        this.initialized = true;
        this.logger.info('Google Search API initialized', {
            responseTime: keyTest.responseTime,
        });
    }

    /**
     * Perform a Google search
     * 
     * @param query - Search query
     * @param options - Search options
     * @returns Search results
     */
    async search(
        query: string,
        options?: SearchOptions
    ): Promise<SearchResult> {
        // Validate inputs
        const validatedQuery = validateTopic(query);

        if (options?.numResults !== undefined && (options.numResults < 1 || options.numResults > 10)) {
            throw new SEOValidationError(
                'numResults',
                'Number of results must be between 1 and 10',
                options.numResults
            );
        }

        // Track metrics
        const startTime = Date.now();
        let attempts = 0;

        return this.rateLimiter.execute(async () => {
            attempts++;

            this.logger.info('Executing search', {
                query: validatedQuery,
                options,
                attempt: attempts,
            });

            // Build URL
            const params = new URLSearchParams({
                key: this.config.apiKey,
                cx: process.env.GOOGLE_SEARCH_ENGINE_ID || 'default',
                q: validatedQuery,
                num: String(options?.numResults || 10),
            });

            if (options?.startIndex) {
                params.set('start', String(options.startIndex));
            }
            if (options?.safeSearch) {
                params.set('safe', options.safeSearch);
            }
            if (options?.language) {
                params.set('hl', options.language);
            }
            if (options?.country) {
                params.set('cr', options.country);
            }
            if (options?.searchType && options.searchType !== 'search') {
                params.set('searchType', options.searchType);
            }
            if (options?.fileType) {
                params.set('fileType', options.fileType);
            }
            if (options?.dateRestrict) {
                params.set('dateRestrict', `d${options.dateRestrict}`);
            }

            const url = `${this.config.baseURL}/customsearch/v1?${params.toString()}`;

            // Execute with retry
            const result = await retryGoogleAPI(
                async () => {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

                    try {
                        const response = await fetch(url, {
                            method: 'GET',
                            signal: controller.signal,
                            headers: {
                                'User-Agent': this.config.userAgent,
                            },
                        });

                        clearTimeout(timeoutId);

                        // Handle errors
                        if (!response.ok) {
                            const errorBody = await response.text();

                            if (response.status === 403) {
                                throw new GoogleAuthError(
                                    'API key invalid or unauthorized',
                                    { service: 'customsearch', statusCode: response.status }
                                );
                            }

                            if (response.status === 429) {
                                throw new GoogleQuotaError(
                                    'Rate limit exceeded',
                                    { service: 'customsearch', statusCode: response.status }
                                );
                            }

                            throw new GoogleAPIError(
                                `API request failed: ${response.status}`,
                                {
                                    service: 'customsearch',
                                    statusCode: response.status,
                                    context: { errorBody },
                                }
                            );
                        }

                        const data = await response.json();

                        return data;
                    } finally {
                        clearTimeout(timeoutId);
                    }
                },
                {
                    maxRetries: 3,
                    baseDelay: 1000,
                } as Partial<RetryConfig>,
                'google-search'
            );

            // Parse results
            const searchResult: SearchResult = {
                items: result.items || [],
                totalResults: parseInt(result.searchInformation?.totalResults || '0', 10),
                count: result.items?.length || 0,
                query: validatedQuery,
                hasMore: result.queries?.nextPage !== undefined,
                nextStartIndex: result.queries?.nextPage?.[0]?.startIndex,
            };

            // Log success
            const duration = Date.now() - startTime;
            this.logger.info('Search completed', {
                query: validatedQuery,
                resultCount: searchResult.count,
                duration,
            });

            // Record metrics
            this.metrics.record(SEO_METRIC_NAMES.GOOGLE_API_CALLS, 1, MetricType.COUNTER);
            this.metrics.record(SEO_METRIC_NAMES.GOOGLE_API_LATENCY, duration, MetricType.HISTOGRAM);

            return searchResult;
        });
    }

    /**
     * Get page speed data for a URL
     * 
     * @param url - URL to analyze
     * @returns Page speed result
     */
    async getPageSpeed(url: string): Promise<PageSpeedResult> {
        // Validate URL
        const validatedUrl = validateUrl(url);

        const startTime = Date.now();

        return this.rateLimiter.execute(async () => {
            this.logger.info('Getting page speed', { url: validatedUrl });

            // Build URL for PageSpeed Insights API
            const params = new URLSearchParams({
                key: this.config.apiKey,
                url: validatedUrl,
                strategy: 'desktop',
            });

            const apiURL = `${this.config.baseURL}/pagespeedonline/v5/runPagespeed?${params.toString()}`;

            const result = await retryGoogleAPI(
                async () => {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

                    try {
                        const response = await fetch(apiURL, {
                            method: 'GET',
                            signal: controller.signal,
                            headers: {
                                'User-Agent': this.config.userAgent,
                            },
                        });

                        clearTimeout(timeoutId);

                        if (!response.ok) {
                            if (response.status === 403) {
                                throw new GoogleAuthError(
                                    'API key invalid or unauthorized for PageSpeed',
                                    { service: 'pagespeedonline', statusCode: response.status }
                                );
                            }

                            if (response.status === 429) {
                                throw new GoogleQuotaError(
                                    'PageSpeed API rate limit exceeded',
                                    { service: 'pagespeedonline', statusCode: response.status }
                                );
                            }

                            throw new GoogleAPIError(
                                `PageSpeed API request failed: ${response.status}`,
                                { service: 'pagespeedonline', statusCode: response.status }
                            );
                        }

                        return await response.json();
                    } finally {
                        clearTimeout(timeoutId);
                    }
                },
                {
                    maxRetries: 2,
                    baseDelay: 2000,
                } as Partial<RetryConfig>,
                'google-pagespeed'
            );

            const pageSpeedResult: PageSpeedResult = {
                url: validatedUrl,
                loadingExperience: result.loadingExperience,
                lighthouseResult: result.lighthouseResult,
                requestId: result.requestId,
            };

            const duration = Date.now() - startTime;
            this.logger.info('Page speed analysis completed', {
                url: validatedUrl,
                duration,
            });

            // Record metrics
            this.metrics.record(SEO_METRIC_NAMES.GOOGLE_API_CALLS, 1, MetricType.COUNTER);
            this.metrics.record(SEO_METRIC_NAMES.GOOGLE_API_LATENCY, duration, MetricType.HISTOGRAM);

            return pageSpeedResult;
        });
    }

    /**
     * Submit URL for indexing (via Indexing API)
     * 
     * @param url - URL to submit
     * @returns Submission result
     */
    async submitURL(url: string): Promise<URLSubmissionResult> {
        // Validate URL
        const validatedUrl = validateUrl(url);

        const startTime = Date.now();

        return this.rateLimiter.execute(async () => {
            this.logger.info('Submitting URL for indexing', { url: validatedUrl });

            // Use Indexing API
            const apiURL = `https://indexing.googleapis.com/v3/urlNotifications:publish`;

            const body = {
                url: validatedUrl,
                type: 'URL_UPDATED',
            };

            const result = await retryGoogleAPI(
                async () => {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

                    try {
                        const response = await fetch(apiURL, {
                            method: 'POST',
                            signal: controller.signal,
                            headers: {
                                'Content-Type': 'application/json',
                                'User-Agent': this.config.userAgent,
                            },
                            body: JSON.stringify(body),
                        });

                        clearTimeout(timeoutId);

                        if (!response.ok) {
                            const errorBody = await response.text();

                            if (response.status === 403) {
                                throw new GoogleAuthError(
                                    'API key invalid or unauthorized for Indexing API',
                                    { service: 'indexing', statusCode: response.status }
                                );
                            }

                            if (response.status === 429) {
                                throw new GoogleQuotaError(
                                    'Indexing API rate limit exceeded',
                                    { service: 'indexing', statusCode: response.status }
                                );
                            }

                            throw new GoogleAPIError(
                                `Indexing API request failed: ${response.status}`,
                                {
                                    service: 'indexing',
                                    statusCode: response.status,
                                    context: { errorBody },
                                }
                            );
                        }

                        return await response.json();
                    } finally {
                        clearTimeout(timeoutId);
                    }
                },
                {
                    maxRetries: 3,
                    baseDelay: 2000,
                } as Partial<RetryConfig>,
                'google-indexing'
            );

            const submissionResult: URLSubmissionResult = {
                url: validatedUrl,
                success: true,
                message: result.urlNotification?.type || 'URL submitted successfully',
                submittedAt: new Date().toISOString(),
            };

            const duration = Date.now() - startTime;
            this.logger.info('URL submitted successfully', {
                url: validatedUrl,
                duration,
            });

            // Record metrics
            this.metrics.record(SEO_METRIC_NAMES.URLS_SUBMITTED, 1, MetricType.COUNTER);
            this.metrics.record(SEO_METRIC_NAMES.URL_SUBMISSION_TIME, duration, MetricType.TIMER);

            return submissionResult;
        });
    }

    /**
     * Check if URL is indexed
     * 
     * @param url - URL to check
     * @returns Index status
     */
    async checkIndexStatus(url: string): Promise<IndexStatusResult> {
        // Validate URL
        const validatedUrl = validateUrl(url);

        const startTime = Date.now();

        return this.rateLimiter.execute(async () => {
            this.logger.info('Checking index status', { url: validatedUrl });

            // Use Indexing API to get URL status
            const apiURL = `https://indexing.googleapis.com/v3/urlNotifications/metadata?url=${encodeURIComponent(validatedUrl)}`;

            const result = await retryGoogleAPI(
                async () => {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

                    try {
                        const response = await fetch(apiURL, {
                            method: 'GET',
                            signal: controller.signal,
                            headers: {
                                'User-Agent': this.config.userAgent,
                            },
                        });

                        clearTimeout(timeoutId);

                        if (response.status === 404) {
                            // URL not found in index
                            return { url: validatedUrl, indexed: false, status: 'NOT_INDEXED' };
                        }

                        if (!response.ok) {
                            if (response.status === 403) {
                                throw new GoogleAuthError(
                                    'API key invalid or unauthorized',
                                    { service: 'indexing', statusCode: response.status }
                                );
                            }

                            if (response.status === 429) {
                                throw new GoogleQuotaError(
                                    'Indexing API rate limit exceeded',
                                    { service: 'indexing', statusCode: response.status }
                                );
                            }

                            throw new GoogleAPIError(
                                `Indexing API request failed: ${response.status}`,
                                { service: 'indexing', statusCode: response.status }
                            );
                        }

                        return await response.json();
                    } finally {
                        clearTimeout(timeoutId);
                    }
                },
                {
                    maxRetries: 2,
                    baseDelay: 1000,
                } as Partial<RetryConfig>,
                'google-index-status'
            );

            const statusResult: IndexStatusResult = {
                url: validatedUrl,
                indexed: result.indexed ?? (result.urlNotification !== undefined),
                status: result.status || (result.indexed ? 'INDEXED' : 'NOT_INDEXED'),
                lastCrawled: result.latestUpdate?.notifyTime,
            };

            const duration = Date.now() - startTime;
            this.logger.info('Index status retrieved', {
                url: validatedUrl,
                indexed: statusResult.indexed,
                duration,
            });

            // Record metrics
            this.metrics.record(SEO_METRIC_NAMES.GOOGLE_API_CALLS, 1, MetricType.COUNTER);
            this.metrics.record(SEO_METRIC_NAMES.GOOGLE_API_LATENCY, duration, MetricType.HISTOGRAM);

            if (statusResult.indexed) {
                this.metrics.record(SEO_METRIC_NAMES.URLS_INDEXED, 1, MetricType.COUNTER);
            }

            return statusResult;
        });
    }

    /**
     * Get rate limiter statistics
     */
    getRateLimitStats(): ReturnType<RateLimiter['getStats']> {
        return this.rateLimiter.getStats();
    }

    /**
     * Get metrics collector
     */
    getMetrics(): MetricsCollector {
        return this.metrics;
    }

    /**
     * Check if API is initialized
     */
    isInitialized(): boolean {
        return this.initialized;
    }

    /**
     * Update configuration
     */
    updateConfig(config: Partial<GoogleAPIConfig>): void {
        this.config = { ...this.config, ...config };

        // Re-initialize if API key changed
        if (config.apiKey && config.apiKey !== this.config.apiKey) {
            this.initialized = false;
            if (this.config.validateOnInit) {
                this.initialize();
            }
        }
    }

    /**
     * Get current configuration (without API key)
     */
    getConfig(): Omit<GoogleAPIConfig, 'apiKey'> & { apiKey: string } {
        return {
            ...this.config,
            apiKey: this.config.apiKey ? `${this.config.apiKey.substring(0, 4)}...${this.config.apiKey.substring(this.config.apiKey.length - 4)}` : '',
        };
    }

    /**
     * Clear the rate limit queue
     */
    clearQueue(): void {
        this.rateLimiter.clearQueue();
    }
}

// ============================================================================
// Factory Functions
// ============================================================================

/**
 * Create a new Google Search API instance
 * 
 * @param config - Optional configuration
 * @returns Configured GoogleSearchAPI instance
 */
export function createGoogleSearchAPI(config?: Partial<GoogleAPIConfig>): GoogleSearchAPI {
    return new GoogleSearchAPI(config);
}

/**
 * Create a rate limiter instance
 * 
 * @param config - Rate limit configuration
 * @param logger - Optional logger
 * @returns Configured RateLimiter instance
 */
export function createRateLimiter(
    config?: Partial<RateLimitConfig>,
    logger?: Logger
): RateLimiter {
    return new RateLimiter(config, logger);
}

// ============================================================================
// Export Types
// ============================================================================

export type {
    // Re-export from errors
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    SEOValidationError as ValidationError,
    SEO_ERROR_CODES,
};

// Re-export retry
export { retryGoogleAPI } from './retry';

// Re-export logger
export { Logger, APILogger, LogLevel } from './logger';

// Re-export metrics
export { MetricsCollector, SEO_METRIC_NAMES, MetricType } from './metrics';

// Re-export validators
export { validateUrl, validateTopic, validateCompetitor } from './validators';

// Re-export config
export { getConfig } from './config';

// Re-export atomic state
export { AtomicStateManager, createStateManager } from './atomic-state';

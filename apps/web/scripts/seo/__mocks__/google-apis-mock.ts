/**
 * Google APIs Mock Implementation
 * 
 * Comprehensive mock implementations for Google APIs used in SEO scripts:
 * - Google Indexing API (urlNotifications.publish)
 * - Google Auth (JWT client, access token acquisition)
 * - Sitemap ping endpoints
 * - IndexNow API
 * 
 * These mocks simulate real API behavior including success, rate limit,
 * auth errors, and network failures without requiring real API keys.
 * 
 * @module seo/__mocks__/google-apis-mock
 */

// ============================================================================
// Types
// ============================================================================

/**
 * Mock configuration options
 */
export interface MockGoogleAPIConfig {
    /** Simulate successful submissions */
    simulateSuccess?: boolean;
    /** Simulate rate limiting */
    simulateRateLimit?: boolean;
    /** Simulate auth errors */
    simulateAuthError?: boolean;
    /** Simulate network errors */
    simulateNetworkError?: boolean;
    /** Simulate quota exceeded */
    simulateQuotaExceeded?: boolean;
    /** Custom response delay in ms */
    responseDelay?: number;
    /** Failure rate (0-1) when not using specific simulation modes */
    failureRate?: number;
    /** Maximum requests before rate limiting */
    maxRequestsBeforeRateLimit?: number;
    /** Whether to track request counts */
    trackRequests?: boolean;
}

/**
 * Request tracking information
 */
export interface RequestTrackInfo {
    url: string;
    type: 'URL_UPDATED' | 'URL_DELETED';
    timestamp: number;
    status: 'success' | 'error' | 'rate_limited' | 'auth_error';
    statusCode?: number;
    errorMessage?: string;
}

/**
 * Default mock configuration
 */
export const DEFAULT_MOCK_CONFIG: MockGoogleAPIConfig = {
    simulateSuccess: true,
    simulateRateLimit: false,
    simulateAuthError: false,
    simulateNetworkError: false,
    simulateQuotaExceeded: false,
    responseDelay: 50,
    failureRate: 0,
    maxRequestsBeforeRateLimit: Infinity,
    trackRequests: true,
};

// ============================================================================
// State
// ============================================================================

let mockConfig: MockGoogleAPIConfig = { ...DEFAULT_MOCK_CONFIG };
let requestCount = 0;
const requestHistory: RequestTrackInfo[] = [];

/**
 * Reset all mock state
 */
export function resetMockState(): void {
    mockConfig = { ...DEFAULT_MOCK_CONFIG };
    requestCount = 0;
    requestHistory.length = 0;
}

/**
 * Configure the mock behavior
 */
export function configureMock(config: Partial<MockGoogleAPIConfig>): void {
    mockConfig = { ...DEFAULT_MOCK_CONFIG, ...config };
}

/**
 * Get current mock configuration
 */
export function getMockConfig(): MockGoogleAPIConfig {
    return { ...mockConfig };
}

/**
 * Get request history
 */
export function getRequestHistory(): RequestTrackInfo[] {
    return [...requestHistory];
}

/**
 * Get total request count
 */
export function getRequestCount(): number {
    return requestCount;
}

/**
 * Clear request history
 */
export function clearRequestHistory(): void {
    requestHistory.length = 0;
    requestCount = 0;
}

// ============================================================================
// Mock Google Indexing API (urlNotifications.publish)
// ============================================================================

/**
 * Mock Google Indexing API URL notification response
 */
export interface IndexingAPIResponse {
    url: string;
    notifyTime: string;
}

/**
 * Mock Google Indexing API error response
 */
export interface IndexingAPIError {
    error: {
        code: number;
        message: string;
        status: string;
        details?: Array<{
            '@type': string;
            reason: string;
            domain: string;
        }>;
    };
}

/**
 * Submit URL to Google Indexing API (mock implementation)
 * 
 * @param url - The URL to submit
 * @param type - The notification type (URL_UPDATED or URL_DELETED)
 * @param accessToken - Mock access token (validated but not used)
 * @returns Promise resolving to the API response
 */
export async function mockIndexingPublish(
    url: string,
    type: 'URL_UPDATED' | 'URL_DELETED' = 'URL_UPDATED',
    accessToken?: string
): Promise<IndexingAPIResponse> {
    // Validate access token
    if (!accessToken) {
        const error: IndexingAPIError = {
            error: {
                code: 401,
                message: 'Request is missing required authentication credential',
                status: 'UNAUTHENTICATED',
            },
        };
        requestHistory.push({
            url,
            type,
            timestamp: Date.now(),
            status: 'auth_error',
            statusCode: 401,
            errorMessage: 'Missing access token',
        });
        throw createMockError(error, 401);
    }

    // Check for rate limiting
    requestCount++;

    if (mockConfig.simulateRateLimit || requestCount > (mockConfig.maxRequestsBeforeRateLimit ?? Infinity)) {
        const error: IndexingAPIError = {
            error: {
                code: 429,
                message: 'Rate limit exceeded for Google Indexing API',
                status: 'RESOURCE_EXHAUSTED',
            },
        };
        requestHistory.push({
            url,
            type,
            timestamp: Date.now(),
            status: 'rate_limited',
            statusCode: 429,
            errorMessage: 'Rate limit exceeded',
        });
        throw createMockError(error, 429);
    }

    // Check for auth error simulation
    if (mockConfig.simulateAuthError) {
        const error: IndexingAPIError = {
            error: {
                code: 403,
                message: 'The caller does not have permission',
                status: 'PERMISSION_DENIED',
            },
        };
        requestHistory.push({
            url,
            type,
            timestamp: Date.now(),
            status: 'auth_error',
            statusCode: 403,
            errorMessage: 'Permission denied',
        });
        throw createMockError(error, 403);
    }

    // Check for network error simulation
    if (mockConfig.simulateNetworkError) {
        requestHistory.push({
            url,
            type,
            timestamp: Date.now(),
            status: 'error',
            statusCode: 0,
            errorMessage: 'Network error',
        });
        throw new Error('Network error: socket hang up');
    }

    // Check for quota exceeded simulation
    if (mockConfig.simulateQuotaExceeded) {
        const error: IndexingAPIError = {
            error: {
                code: 429,
                message: 'Quota exceeded for this API',
                status: 'RESOURCE_EXHAUSTED',
                details: [
                    {
                        '@type': 'type.googleapis.com/google.rpc.RetryInfo',
                        reason: 'RATE_LIMIT_EXCEEDED',
                        domain: 'google.indexing.googleapis.com',
                    },
                ],
            },
        };
        requestHistory.push({
            url,
            type,
            timestamp: Date.now(),
            status: 'rate_limited',
            statusCode: 429,
            errorMessage: 'Quota exceeded',
        });
        throw createMockError(error, 429);
    }

    // Random failure simulation
    if (mockConfig.failureRate && Math.random() < mockConfig.failureRate) {
        const error: IndexingAPIError = {
            error: {
                code: 500,
                message: 'Internal server error',
                status: 'INTERNAL',
            },
        };
        requestHistory.push({
            url,
            type,
            timestamp: Date.now(),
            status: 'error',
            statusCode: 500,
            errorMessage: 'Internal server error',
        });
        throw createMockError(error, 500);
    }

    // Apply response delay
    if (mockConfig.responseDelay) {
        await new Promise(resolve => setTimeout(resolve, mockConfig.responseDelay));
    }

    // Success response
    const response: IndexingAPIResponse = {
        url,
        notifyTime: new Date().toISOString(),
    };

    requestHistory.push({
        url,
        type,
        timestamp: Date.now(),
        status: 'success',
        statusCode: 200,
    });

    return response;
}

/**
 * Create a mock error object that mimics Google API error structure
 */
function createMockError(apiError: IndexingAPIError, statusCode: number): Error & { response?: IndexingAPIError; statusCode?: number } {
    const error = new Error(apiError.error.message) as Error & { response?: IndexingAPIError; statusCode?: number };
    error.response = apiError;
    error.statusCode = statusCode;
    error.name = 'GoogleAPIError';
    return error;
}

// ============================================================================
// Mock Google Auth (JWT Client, Access Token)
// ============================================================================

/**
 * Mock service account credentials
 */
export interface MockServiceAccountCredentials {
    type: string;
    project_id: string;
    private_key_id: string;
    private_key: string;
    client_email: string;
    client_id: string;
    auth_uri: string;
    token_uri: string;
}

/**
 * Generate mock service account credentials
 */
export function generateMockCredentials(): MockServiceAccountCredentials {
    return {
        type: 'service_account',
        project_id: 'mock-project-123',
        private_key_id: 'mock-key-id-1234567890abcdef',
        private_key: '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\nMzEfYyjiWA4R4/M2bS1+fWIcPm15j9nJPKQaCj8hkjvvvPMWGHQKj4rF2nqPjvKU\nBPj3vqGqFwJBAN1p/OqbPy7XH2kQfYjLz9kqPvM6kqJvMJzH2jPJV1kqJvMJzH2\njPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kq\nJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH\n2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1\nkqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvM\nJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jP\nJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJ\nvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2\njPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1\nkqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvM\nJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jP\nJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJ\nvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH\n2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV\n1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJvMJzH2jPJV1kqJv\n-----END PRIVATE KEY-----',
        client_email: 'mock-service-account@mock-project.iam.gserviceaccount.com',
        client_id: '123456789012345678901',
        auth_uri: 'https://accounts.google.com/o/oauth2/auth',
        token_uri: 'https://oauth2.googleapis.com/token',
    };
}

/**
 * Mock JWT token response
 */
export interface MockTokenResponse {
    access_token: string;
    expires_in: number;
    token_type: string;
}

/**
 * Mock access token generation
 * 
 * @param credentials - Service account credentials (mocked)
 * @param scope - OAuth scope
 * @returns Promise resolving to token response
 */
export async function mockGetAccessToken(
    credentials?: MockServiceAccountCredentials,
    scope: string = 'https://www.googleapis.com/auth/indexing'
): Promise<MockTokenResponse> {
    // Simulate network delay
    if (mockConfig.responseDelay) {
        await new Promise(resolve => setTimeout(resolve, mockConfig.responseDelay));
    }

    // Check for auth error simulation
    if (mockConfig.simulateAuthError) {
        throw new Error('JWT generation failed: invalid_credentials');
    }

    // Check for network error simulation
    if (mockConfig.simulateNetworkError) {
        throw new Error('Network error: Connection refused');
    }

    // Generate mock token
    const token: MockTokenResponse = {
        access_token: `mock_token_${Date.now()}_${Math.random().toString(36).substring(7)}`,
        expires_in: 3600,
        token_type: 'Bearer',
    };

    return token;
}

/**
 * Create a mock Google Auth client
 */
export function createMockGoogleAuth(): {
    getAccessToken: () => Promise<string>;
    credentials: MockServiceAccountCredentials;
} {
    const credentials = generateMockCredentials();

    return {
        credentials,
        getAccessToken: () => mockGetAccessToken(credentials).then(t => t.access_token),
    };
}

// ============================================================================
// Mock Sitemap Ping Endpoints
// ============================================================================

/**
 * Mock sitemap ping response
 */
export interface SitemapPingResponse {
    success: boolean;
    message: string;
    timestamp: string;
}

/**
 * Mock sitemap URLs that Google accepts
 */
const MOCK_SITEMAP_ENDPOINTS = [
    'https://www.google.com/ping?sitemap=',
    'https://www.bing.com/indexnow',
];

/**
 * Submit sitemap to Google (mock implementation)
 * 
 * @param sitemapUrl - The full URL of the sitemap
 * @returns Promise resolving to ping response
 */
export async function mockPingSitemap(sitemapUrl: string): Promise<SitemapPingResponse> {
    // Simulate network delay
    if (mockConfig.responseDelay) {
        await new Promise(resolve => setTimeout(resolve, mockConfig.responseDelay));
    }

    // Validate sitemap URL
    if (!sitemapUrl || !sitemapUrl.startsWith('http')) {
        return {
            success: false,
            message: 'Invalid sitemap URL',
            timestamp: new Date().toISOString(),
        };
    }

    // Check for rate limiting
    if (mockConfig.simulateRateLimit) {
        throw new Error('Rate limit exceeded for sitemap ping');
    }

    // Check for network error
    if (mockConfig.simulateNetworkError) {
        throw new Error('Network error: timeout');
    }

    return {
        success: true,
        message: 'Sitemap successfully processed',
        timestamp: new Date().toISOString(),
    };
}

/**
 * Submit sitemap to Bing (mock implementation - IndexNow)
 * 
 * @param sitemapUrl - The full URL of the sitemap
 * @param apiKey - Bing API key (optional for mock)
 * @returns Promise resolving to IndexNow response
 */
export async function mockPingSitemapBing(
    sitemapUrl: string,
    apiKey?: string
): Promise<{ success: boolean; message: string }> {
    // Simulate network delay
    if (mockConfig.responseDelay) {
        await new Promise(resolve => setTimeout(resolve, mockConfig.responseDelay));
    }

    // Check for network error
    if (mockConfig.simulateNetworkError) {
        throw new Error('Network error: Connection reset');
    }

    return {
        success: true,
        message: 'Sitemap submitted to Bing IndexNow API',
    };
}

// ============================================================================
// Mock IndexNow API
// ============================================================================

/**
 * Mock IndexNow submission response
 */
export interface IndexNowResponse {
    statusCode: number;
    message: string;
    mantle?: string;
}

/**
 * Submit URL to IndexNow (mock implementation)
 * 
 * @param url - The URL to submit
 * @param apiKey - The API key for IndexNow
 * @param apiKeyLocation - Location of the API key
 * @returns Promise resolving to IndexNow response
 */
export async function mockIndexNowSubmit(
    url: string,
    apiKey: string = 'test-api-key',
    apiKeyLocation: string = 'file'
): Promise<IndexNowResponse> {
    // Simulate network delay
    if (mockConfig.responseDelay) {
        await new Promise(resolve => setTimeout(resolve, mockConfig.responseDelay));
    }

    // Validate URL
    if (!url || !url.startsWith('http')) {
        return {
            statusCode: 400,
            message: 'Invalid URL format',
        };
    }

    // Validate API key
    if (!apiKey || apiKey.length < 8) {
        return {
            statusCode: 403,
            message: 'Invalid API key',
        };
    }

    // Check for rate limiting
    if (mockConfig.simulateRateLimit) {
        return {
            statusCode: 429,
            message: 'Rate limit exceeded',
        };
    }

    // Check for network error
    if (mockConfig.simulateNetworkError) {
        throw new Error('Network error: ETIMEDOUT');
    }

    return {
        statusCode: 200,
        message: 'URL submitted successfully',
        mantle: '2023-01-01T00:00:00.000Z',
    };
}

/**
 * Submit batch of URLs to IndexNow (mock implementation)
 * 
 * @param urls - Array of URLs to submit
 * @param apiKey - The API key for IndexNow
 * @returns Promise resolving to batch response
 */
export async function mockIndexNowSubmitBatch(
    urls: string[],
    apiKey: string = 'test-api-key'
): Promise<{ submitted: number; failed: number; errors: string[] }> {
    // Simulate network delay
    const delay = mockConfig.responseDelay || 0;
    if (delay) {
        await new Promise(resolve => setTimeout(resolve, delay * urls.length));
    }

    let submitted = 0;
    let failed = 0;
    const errors: string[] = [];

    for (const url of urls) {
        try {
            const result = await mockIndexNowSubmit(url, apiKey);
            if (result.statusCode === 200) {
                submitted++;
            } else {
                failed++;
                errors.push(`${url}: ${result.message}`);
            }
        } catch (error) {
            failed++;
            errors.push(`${url}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    return { submitted, failed, errors };
}

// ============================================================================
// Mock HTTP Fetch
// ============================================================================

/**
 * Create a mock fetch function that simulates Google API responses
 * 
 * @returns Mocked fetch function
 */
export function createMockFetch(): typeof fetch {
    return async (
        url: string | URL | Request,
        options?: RequestInit
    ): Promise<Response> => {
        const urlString = url instanceof URL ? url.toString() : typeof url === 'string' ? url : url.url;

        // Parse options
        const method = options?.method || 'GET';
        const body = options?.body ? JSON.parse(options.body as string) : null;
        const headers = new Headers(options?.headers);

        // Determine which API endpoint is being called
        if (urlString.includes('indexing.googleapis.com') && urlString.includes(':publish')) {
            // Google Indexing API
            const urlToSubmit = body?.url;
            const type = body?.type || 'URL_UPDATED';

            try {
                const response = await mockIndexingPublish(urlToSubmit, type, headers.get('Authorization')?.replace('Bearer ', ''));

                return new Response(JSON.stringify(response), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' },
                });
            } catch (error: any) {
                return new Response(JSON.stringify(error.response || { error: { message: error.message } }), {
                    status: error.statusCode || 500,
                    headers: { 'Content-Type': 'application/json' },
                });
            }
        }

        if (urlString.includes('oauth2.googleapis.com') || urlString.includes('token')) {
            // OAuth token endpoint
            try {
                const tokenResponse = await mockGetAccessToken();
                return new Response(JSON.stringify(tokenResponse), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' },
                });
            } catch (error: any) {
                return new Response(JSON.stringify({ error: error.message }), {
                    status: 400,
                    headers: { 'Content-Type': 'application/json' },
                });
            }
        }

        if (urlString.includes('google.com/ping') || urlString.includes('bing.com/indexnow')) {
            // Sitemap ping endpoint
            const sitemapUrl = urlString.includes('sitemap=')
                ? decodeURIComponent(urlString.split('sitemap=')[1])
                : '';

            try {
                const response = await mockPingSitemap(sitemapUrl);
                return new Response(JSON.stringify(response), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' },
                });
            } catch (error: any) {
                return new Response(JSON.stringify({ error: error.message }), {
                    status: 500,
                    headers: { 'Content-Type': 'application/json' },
                });
            }
        }

        // Default: return 404 for unknown endpoints
        return new Response(JSON.stringify({ error: 'Unknown endpoint' }), {
            status: 404,
            headers: { 'Content-Type': 'application/json' },
        });
    };
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Simulate various error scenarios for testing
 */
export type ErrorScenario =
    | 'success'
    | 'rate_limit'
    | 'auth_error'
    | 'quota_exceeded'
    | 'network_error'
    | 'server_error'
    | 'random_failures';

/**
 * Configure mock to simulate a specific error scenario
 */
export function setErrorScenario(scenario: ErrorScenario): void {
    switch (scenario) {
        case 'success':
            configureMock({
                simulateSuccess: true,
                simulateRateLimit: false,
                simulateAuthError: false,
                simulateNetworkError: false,
                simulateQuotaExceeded: false,
                failureRate: 0,
            });
            break;
        case 'rate_limit':
            configureMock({
                simulateSuccess: false,
                simulateRateLimit: true,
                simulateAuthError: false,
                simulateNetworkError: false,
                simulateQuotaExceeded: false,
            });
            break;
        case 'auth_error':
            configureMock({
                simulateSuccess: false,
                simulateRateLimit: false,
                simulateAuthError: true,
                simulateNetworkError: false,
                simulateQuotaExceeded: false,
            });
            break;
        case 'quota_exceeded':
            configureMock({
                simulateSuccess: false,
                simulateRateLimit: false,
                simulateAuthError: false,
                simulateNetworkError: false,
                simulateQuotaExceeded: true,
            });
            break;
        case 'network_error':
            configureMock({
                simulateSuccess: false,
                simulateRateLimit: false,
                simulateAuthError: false,
                simulateNetworkError: true,
                simulateQuotaExceeded: false,
            });
            break;
        case 'server_error':
            configureMock({
                simulateSuccess: false,
                simulateRateLimit: false,
                simulateAuthError: false,
                simulateNetworkError: false,
                simulateQuotaExceeded: false,
                failureRate: 1,
            });
            break;
        case 'random_failures':
            configureMock({
                simulateSuccess: false,
                simulateRateLimit: false,
                simulateAuthError: false,
                simulateNetworkError: false,
                simulateQuotaExceeded: false,
                failureRate: 0.1,
            });
            break;
    }
}

// ============================================================================
// Export all mocks
// ============================================================================

export default {
    resetMockState,
    configureMock,
    getMockConfig,
    getRequestHistory,
    getRequestCount,
    clearRequestHistory,
    mockIndexingPublish,
    mockGetAccessToken,
    createMockGoogleAuth,
    generateMockCredentials,
    mockPingSitemap,
    mockPingSitemapBing,
    mockIndexNowSubmit,
    mockIndexNowSubmitBatch,
    createMockFetch,
    setErrorScenario,
};

/**
 * Magic Link Service - Centralized magic link handling
 * Ensures consistent behavior across Homepage, Login, and Onboarding
 * Enhanced with bot protection and rate limiting
 */

import { config } from '../config';
import { ValidationUtils } from '../lib/validation';
import { botProtection } from '../lib/botProtection';

export interface MagicLinkResponse {
  status: string;
  message?: string;
}

export interface MagicLinkError {
  status: number;
  message: string;
  retryAfter?: number;
}

class MagicLinkService {
  private rateLimitResets: Map<string, number> = new Map();
  private captchaRequired: boolean = false;
  private circuitBreakerState: Map<string, {
    failures: number;
    lastFailure: number;
    state: 'closed' | 'open' | 'half-open';
    successCount: number;  // Track successes in half-open state
    testRequests: number;  // Track test requests allowed in half-open
  }> = new Map();
  private readonly CIRCUIT_BREAKER_THRESHOLD = 5;
  private readonly CIRCUIT_BREAKER_TIMEOUT = 60000; // 1 minute
  private readonly CIRCUIT_BREAKER_HALF_OPEN_TIMEOUT = 30000; // 30 seconds
  private readonly CIRCUIT_BREAKER_HALF_OPEN_MAX_TESTS = 3; // Allow 3 test requests in half-open

  /**
   * Send a magic link to user's email with bot protection
   */
  async sendMagicLink(
    email: string,
    returnTo: string = '/app/onboarding',
    captchaToken?: string
  ): Promise<{ success: boolean; email: string; error?: string; retryAfter?: number; captchaRequired?: boolean }> {
    // RFC max email length is 320 chars (254 + local part variations). Allow full range.
    const normalizedEmail = ValidationUtils.sanitizeInput(email.trim().toLowerCase(), 320);

    // Enhanced email validation
    const emailValidation = ValidationUtils.validate.email(normalizedEmail);
    if (!emailValidation.isValid) {
      return {
        success: false,
        email: normalizedEmail,
        error: emailValidation.errors.join(', '),
      };
    }

    // FIRST: Check local cooldown to avoid unnecessary calls when we KNOW a recent 429 occurred
    const rateLimitReset = this.rateLimitResets.get(normalizedEmail);
    if (rateLimitReset) {
      if (rateLimitReset > Date.now()) {
        const secondsLeft = Math.max(1, Math.ceil((rateLimitReset - Date.now()) / 1000));
        return {
          success: false,
          email: normalizedEmail,
          error: `Too many requests. Please wait ${secondsLeft}s before trying again.`,
          retryAfter: secondsLeft,
        };
      }
      // Expired cooldown -> clean up
      this.rateLimitResets.delete(normalizedEmail);
    }

    // Enhanced rate limiting with IP and fingerprint checking
    const rateLimitCheck = await botProtection.checkRateLimit(normalizedEmail, {
      rateLimitPerIP: 5,
      rateLimitPerFingerprint: 3,
      windowMs: 15 * 60 * 1000, // 15 minutes
    });

    if (!rateLimitCheck.allowed) {
      const retryAfter = rateLimitCheck.resetIn || 300;
      this.rateLimitResets.set(normalizedEmail, Date.now() + retryAfter * 1000);
      return {
        success: false,
        email: normalizedEmail,
        error: rateLimitCheck.reason || `Too many requests. Please wait ${retryAfter} seconds before retrying.`,
        retryAfter: retryAfter,
      };
    }

    // Check if captcha is required
    const shouldRequireCaptcha = botProtection.shouldRequireCaptcha(normalizedEmail);
    if (shouldRequireCaptcha && !captchaToken) {
      return {
        success: false,
        email: normalizedEmail,
        error: 'Please complete the captcha verification to continue.',
        captchaRequired: true,
      };
    }

    // Note: Captcha verification happens on the backend.
    // If a token is provided, we just pass it along in the payload.

    try {
      // Prefer canonical app base URL
      const configuredOrigin = config.appBaseUrl?.trim();
      const browserOrigin = typeof window !== 'undefined' ? window.location.origin : '';

      // Enhanced URL validation
      if (configuredOrigin && !this.isValidURL(configuredOrigin)) {
        throw new Error('Invalid appBaseUrl configuration: malformed URL');
      }

      const origin = configuredOrigin || browserOrigin;

      if (!origin) {
        throw new Error('App base URL is not configured and origin is unavailable');
      }

      if (!configuredOrigin && browserOrigin) {
        if (import.meta.env.DEV) {
          console.warn('[MagicLink] Using browser origin as fallback - configure appBaseUrl for production');
        }
      }

      // Construct redirect URL to go through /login page first
      const sanitizedReturnTo = this.sanitizeReturnTo(returnTo);
      // NOTE: The backend handles the appending of ?token=... for magic links
      // We just tell it where to send the user *after* they click the link in email.
      // But typically we want them to come back to /login (or /verify) to process the token.
      // apps/api/auth.py appends token to `redirect_to`.
      // So checking `apps/api/auth.py`:
      // separator = "&" if "?" in redirect_to else "?"
      // return f"{redirect_to}{separator}token={token}"

      // So we should send the /login URL as the redirect_to.
      // However, the frontend currently constructs `redirectUrl` with `returnTo` param.
      // This seems fine. The backend will append `&token=...` to it.

      const redirectUrl = `${origin.replace(/\/$/, '')}/login?returnTo=${encodeURIComponent(sanitizedReturnTo)}`;

      // Validate redirect URL is properly formed
      if (!redirectUrl.startsWith('http')) {
        throw new Error('Invalid redirect URL: must be absolute URL with protocol');
      }

      if (import.meta.env.DEV) {
        const maskedEmail = normalizedEmail.replace(/(^.{2}).+(@.+)$/, '$1***$2');
        if (import.meta.env.DEV) {
          console.log('[MagicLink] Sending request to API:', maskedEmail, 'return_to:', sanitizedReturnTo);
        }
      }

      // Check circuit breaker before making request
      // States: 'closed' = healthy (default), 'open' = tripped/blocking, 'half-open' = testing recovery
      const circuitKey = `magiclink_${normalizedEmail}`;
      const circuitState = this.circuitBreakerState.get(circuitKey) || { failures: 0, lastFailure: 0, state: 'closed' };

      if (circuitState.state === 'open') {
        const timeUntilReset = circuitState.lastFailure + this.CIRCUIT_BREAKER_TIMEOUT - Date.now();
        if (timeUntilReset > 0) {
          return {
            success: false,
            email: normalizedEmail,
            error: `Service temporarily unavailable. Please try again in ${Math.ceil(timeUntilReset / 1000)} seconds.`,
            retryAfter: Math.ceil(timeUntilReset / 1000)
          };
        }
      } else if (circuitState.state === 'half-open') {
        // In half-open state, allow limited test requests
        if (circuitState.testRequests >= this.CIRCUIT_BREAKER_HALF_OPEN_MAX_TESTS) {
          return {
            success: false,
            email: normalizedEmail,
            error: `Service temporarily unavailable. Please try again in ${Math.ceil(this.CIRCUIT_BREAKER_HALF_OPEN_TIMEOUT / 1000)} seconds.`,
            retryAfter: Math.ceil(this.CIRCUIT_BREAKER_HALF_OPEN_TIMEOUT / 1000)
          };
        }
        // Allow this test request
        circuitState.testRequests += 1;
        this.circuitBreakerState.set(circuitKey, circuitState);
      }

      // Use the backend API to send the magic link with enhanced security
      const { apiPost } = await import('../lib/api');

      const payload: any = {
        email: normalizedEmail,
        return_to: sanitizedReturnTo,
        fingerprint: botProtection.generateFingerprint(),
        captcha_token: captchaToken,
      };

      // Include captcha token if provided
      if (captchaToken) {
        payload.captcha_token = captchaToken;
      }

      await apiPost('/auth/magic-link', payload);

      // Reset circuit breaker on success
      this.circuitBreakerState.set(circuitKey, {
        failures: 0,
        lastFailure: 0,
        state: 'closed',
        successCount: 0,
        testRequests: 0
      });

      if (import.meta.env.DEV) {
        console.log('[MagicLink] API request successful');
      }

      return {
        success: true,
        email: normalizedEmail,
      };
    } catch (error: any) {
      console.error('[MagicLink] Error:', error);

      // Update circuit breaker state on failure
      const circuitKey = `magiclink_${normalizedEmail}`;
      const circuitState = this.circuitBreakerState.get(circuitKey) || {
        failures: 0,
        lastFailure: 0,
        state: 'closed' as const,
        successCount: 0,
        testRequests: 0
      };
      const newFailures = circuitState.failures + 1;
      const now = Date.now();
      let newState: 'closed' | 'half-open' | 'open' = 'closed';

      if (newFailures >= this.CIRCUIT_BREAKER_THRESHOLD) {
        newState = 'open';
      } else if (newFailures >= Math.ceil(this.CIRCUIT_BREAKER_THRESHOLD / 2)) {
        newState = 'half-open';
      }

      if (circuitState.state === 'half-open') {
        if (newFailures >= this.CIRCUIT_BREAKER_THRESHOLD) {
          newState = 'open';
        }
        circuitState.testRequests = 0;
        circuitState.successCount = 0;
      }

      this.circuitBreakerState.set(circuitKey, {
        failures: newFailures,
        lastFailure: now,
        state: newState,
        successCount: newState === 'half-open' ? circuitState.successCount : 0,
        testRequests: newState === 'half-open' ? circuitState.testRequests : 0
      });

      // Handle 429 specifically
      if (error?.status === 429 || error?.message?.includes('Too many requests')) {
        const retryAfter = error.retryAfter || 60;
        this.rateLimitResets.set(normalizedEmail, Date.now() + retryAfter * 1000);
        return {
          success: false,
          email: normalizedEmail,
          error: `Too many requests. Please wait ${retryAfter} seconds.`,
          retryAfter
        };
      }

      // Extract clean error message — guard against [object Object]
      let message = 'Failed to send magic link. Please try again.';
      if (typeof error?.message === 'string' && error.message.length > 0 && !error.message.includes('[object Object]')) {
        message = error.message.replace(/\s*\(HTTP\s*\d+\)\s*$/, '');
      } else if (typeof error === 'string') {
        message = error;
      }

      return {
        success: false,
        email: normalizedEmail,
        error: message,
      };
    }
  }

  /**
   * Enhanced URL validation with security checks
   */
  private isValidURL(url: string): boolean {
    try {
      const parsed = new URL(url);
      return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch {
      return false;
    }
  }

  /**
   * Get rate limit countdown for an email
   */
  getRateLimitCountdown(email: string): number | null {
    const normalizedEmail = ValidationUtils.sanitizeInput(email.toLowerCase(), 320);
    const reset = this.rateLimitResets.get(normalizedEmail);
    if (!reset || reset <= Date.now()) {
      return null;
    }
    return Math.ceil((reset - Date.now()) / 1000);
  }

  /**
   * Enhanced return_to sanitization with security
   */
  private sanitizeReturnTo(url: string): string {
    if (!url || typeof url !== 'string') {
      return '/app/onboarding';
    }

    // Trim and cap length to avoid abuse
    const trimmed = ValidationUtils.sanitizeInput(url.trim(), 2048);

    // Reject dangerous schemes/hosts
    const lower = trimmed.toLowerCase();
    if (lower.startsWith('http:') || lower.startsWith('https:') || lower.startsWith('javascript:') || lower.startsWith('data:')) {
      return '/app/onboarding';
    }

    // Must be an absolute path (no host) and not protocol-relative
    if (!trimmed.startsWith('/') || trimmed.startsWith('//')) {
      return '/app/onboarding';
    }

    // Strip query/hash to avoid open redirects; we only trust path component
    const pathOnly = trimmed.split('?')[0].split('#')[0];

    // Check for path traversal attempts
    if (pathOnly.includes('../') || pathOnly.includes('..\\')) {
      return '/app/onboarding';
    }

    const allowedPaths = new Set([
      '/app/onboarding',
      '/app/dashboard',
      '/app/jobs',
      '/app/applications',
      '/app/holds',
      '/app/billing',
      '/app/settings',
      '/app/team',
      '/app/matches',
      '/app/tailor',
      '/app/ats-score',
      '/app/pipeline-view',
      '/app/application-export',
      '/app/follow-up-reminders',
      '/app/interview-practice',
      '/app/multi-resume',
      '/app/application-notes',
      '/app/communication-preferences',
      '/app/notification-history',
      '/app/dlq-dashboard',
      '/app/screenshot-capture',
      '/app/agent-improvements',
      '/app/admin/usage',
      '/app/admin/matches',
      '/app/admin/alerts',
      '/app/admin/sources',
    ]);

    if (allowedPaths.has(pathOnly)) {
      return pathOnly;
    }

    return '/app/onboarding';
  }

  /**
   * Get destination hint for UI
   */
  getDestinationHint(returnTo: string): string {
    const sanitized = this.sanitizeReturnTo(returnTo);
    switch (sanitized) {
      case '/app/onboarding':
        return "We'll drop you into onboarding as soon as you're verified.";
      case '/app/dashboard':
        return "You'll land on your dashboard after signing in.";
      case '/app/jobs':
        return "You'll go straight to job feed.";
      case '/app/team':
        return "You'll access your team workspace.";
      default:
        return `We'll take you to ${sanitized} once you're in.`;
    }
  }

  /**
   * Clear all rate limits (for testing/admin)
   */
  clearRateLimits(): void {
    this.rateLimitResets.clear();
  }
}

export const magicLinkService = new MagicLinkService();

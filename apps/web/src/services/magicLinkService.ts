/**
 * Magic Link Service - Centralized magic link handling
 * Ensures consistent behavior across Homepage, Login, and Onboarding
 */

import { config } from '../config';
import { ValidationUtils } from '../lib/validation';

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

  /**
   * Send a magic link to user's email
   */
  async sendMagicLink(
    email: string,
    returnTo: string = '/app/onboarding'
  ): Promise<{ success: boolean; email: string; error?: string; retryAfter?: number }> {
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

    // Adaptive rate limiting: up to 3 requests per 5 minutes per email
    const rateLimitCheck = ValidationUtils.security.rateLimit(`magiclink:${normalizedEmail}`, 3, 300000);
    if (!rateLimitCheck.allowed) {
      const retryAfter = rateLimitCheck.resetIn;
      this.rateLimitResets.set(normalizedEmail, Date.now() + retryAfter * 1000);
      return {
        success: false,
        email: normalizedEmail,
        error: `Too many magic link requests. Please wait ${retryAfter} seconds before retrying.`,
        retryAfter: retryAfter,
      };
    }

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
        console.warn('[MagicLink] Using browser origin as fallback - configure appBaseUrl for production');
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

      console.log('[MagicLink] Sending request to API:', normalizedEmail, 'return_to:', sanitizedReturnTo);

      // Use the backend API to send the magic link
      const { apiPost } = await import('../lib/api');

await apiPost('/auth/magic-link', {
        email: normalizedEmail,
        return_to: sanitizedReturnTo
      });

      console.log('[MagicLink] API request successful');

      // Clear rate limit on success
      this.rateLimitResets.delete(normalizedEmail);

      return {
        success: true,
        email: normalizedEmail,
      };
    } catch (error: any) {
      console.error('[MagicLink] Error:', error);

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

      // Extract clean error message
      let message = 'Network error';
      if (error?.message) {
        // Remove HTTP status suffix if present (e.g., " (HTTP 502)")
        message = error.message.replace(/\s*\(HTTP\s*\d+\)\s*$/, '');
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

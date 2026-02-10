/**
 * Magic Link Service - Centralized magic link handling
 * Ensures consistent behavior across Homepage, Login, and Onboarding
 */

import { config } from '../config';
import { supabase } from '../lib/supabase';
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
    const normalizedEmail = ValidationUtils.sanitizeInput(email.trim().toLowerCase(), 254);

    // Enhanced email validation
    const emailValidation = ValidationUtils.validate.email(normalizedEmail);
    if (!emailValidation.isValid) {
      return {
        success: false,
        email: normalizedEmail,
        error: emailValidation.errors.join(', '),
      };
    }

    // Validate Supabase Configuration
    if (!config.auth.supabaseUrl || !config.auth.supabaseAnonKey) {
      console.error('[MagicLink] Missing Supabase configuration. Check VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.');
      return {
        success: false,
        email: normalizedEmail,
        error: 'System configuration error: Missing authentication settings.',
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

    // Enhanced rate limiting with validation - strict to 1 request per 60 seconds to avoid Supabase 429 errors
    const rateLimitCheck = ValidationUtils.security.rateLimit(`magiclink:${normalizedEmail}`, 1, 60000); // 1 request per 60 seconds
    if (!rateLimitCheck.allowed) {
      const retryAfter = rateLimitCheck.resetIn;
      this.rateLimitResets.set(normalizedEmail, Date.now() + retryAfter * 1000);
      return {
        success: false,
        email: normalizedEmail,
        error: `Too many magic link requests. Please wait ${retryAfter} seconds.`,
        retryAfter: retryAfter,
      };
    }

    try {
      // Prefer canonical app base URL to avoid Supabase redirect whitelist errors
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
      // This ensures we have a stable entry point to handle hash fragment
      // before redirecting to protected route
      const sanitizedReturnTo = this.sanitizeReturnTo(returnTo);
      const redirectUrl = `${origin.replace(/\/$/, '')}/login?returnTo=${encodeURIComponent(sanitizedReturnTo)}`;

      /* console.group('[MagicLink] Request Details');
      console.log('Target Email:', normalizedEmail);
      console.log('Origin:', origin);
      console.log('Return To:', sanitizedReturnTo);
      console.log('Full Redirect URL:', redirectUrl);
      console.groupEnd(); */

      // Validate redirect URL is properly formed
      if (!redirectUrl.startsWith('http')) {
        throw new Error('Invalid redirect URL: must be absolute URL with protocol');
      }

      console.log('[MagicLink] Sending request to API:', normalizedEmail, 'return_to:', sanitizedReturnTo);

      // Use the backend API to send the magic link
      // This ensures we use the branded HTML template via Resend
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

      const message = error.message || 'Network error';
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
    const normalizedEmail = ValidationUtils.sanitizeInput(email.toLowerCase(), 254);
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

    const trimmed = ValidationUtils.sanitizeInput(url.trim(), 2048);

    // Must start with /
    if (!trimmed.startsWith('/')) {
      return '/app/onboarding';
    }

    // Prevent // (protocol-relative URLs)
    if (trimmed.startsWith('//')) {
      return '/app/onboarding';
    }

    // Prevent javascript: and data: protocols
    if (trimmed.toLowerCase().startsWith('javascript:') || trimmed.toLowerCase().startsWith('data:')) {
      return '/app/onboarding';
    }

    // Enhanced whitelist with security considerations
    const allowedPaths = [
      '/app/onboarding',
      '/app/dashboard',
      '/app/jobs',
      '/app/applications',
      '/app/holds',
      '/app/billing',
      '/app/settings',
      '/app/team',
    ];

    // Check for path traversal attempts
    if (trimmed.includes('../') || trimmed.includes('..\\')) {
      return '/app/onboarding';
    }

    if (allowedPaths.includes(trimmed)) {
      return trimmed;
    }

    // Default to onboarding
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
   * Validate magic link token
   */
  async validateToken(token: string, email: string): Promise<{ valid: boolean; error?: string }> {
    try {
      const { data, error } = await supabase.auth.verifyOtp({
        token,
        email,
        type: 'email'
      });

      if (error) {
        return {
          valid: false,
          error: error.message
        };
      }

      return {
        valid: !!data.user
      };
    } catch (error) {
      return {
        valid: false,
        error: error instanceof Error ? error.message : 'Token validation failed'
      };
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

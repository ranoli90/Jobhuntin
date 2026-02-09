/**
 * Magic Link Service - Centralized magic link handling
 * Ensures consistent behavior across Homepage, Login, and Onboarding
 */

import { config } from '../config';
import { supabase } from '../lib/supabase';

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
   * Send a magic link to the user's email
   */
  async sendMagicLink(
    email: string,
    returnTo: string = '/app/onboarding'
  ): Promise<{ success: boolean; email: string; error?: string; retryAfter?: number }> {
    const normalizedEmail = email.trim().toLowerCase();

    // Validate email
    if (!config.validation.emailRegex.test(normalizedEmail)) {
      return {
        success: false,
        email: normalizedEmail,
        error: 'Please enter a valid email address',
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

    // Check local cooldown to avoid unnecessary calls when we KNOW a recent 429 occurred
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

    try {
      // Prefer canonical app base URL to avoid Supabase redirect whitelist errors
      const configuredOrigin = config.appBaseUrl?.trim();
      const browserOrigin = typeof window !== 'undefined' ? window.location.origin : '';
      
      if (configuredOrigin && !URL.canParse(configuredOrigin)) {
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
      // This ensures we have a stable entry point to handle the hash fragment
      // before redirecting to the protected route
      const sanitizedReturnTo = this.sanitizeReturnTo(returnTo);
      const redirectUrl = `${origin.replace(/\/$/, '')}/login?returnTo=${encodeURIComponent(sanitizedReturnTo)}`;

      console.group('[MagicLink] Request Details');
      console.log('Target Email:', normalizedEmail);
      console.log('Origin:', origin);
      console.log('Return To:', sanitizedReturnTo);
      console.log('Full Redirect URL:', redirectUrl);
      console.groupEnd();
      
      // Validate the redirect URL is properly formed
      if (!redirectUrl.startsWith('http')) {
        throw new Error('Invalid redirect URL: must be absolute URL with protocol');
      }

      const { error } = await supabase.auth.signInWithOtp({
        email: normalizedEmail,
        options: {
          emailRedirectTo: redirectUrl,
        },
      });

      if (error) {
        console.group('[MagicLink] Supabase Error');
        console.error('Message:', error.message);
        console.error('Status:', error.status);
        console.error('Name:', error.name);
        console.groupEnd();
        
        // Handle rate limits specifically if Supabase returns them (usually 429 status in error)
        if (error.status === 429) {
          // Respect server suggested retry window if present, otherwise default to 60s
          const retryAfterMatch = /([0-9]{1,3})\s*second/i.exec(error.message || "");
          const retryAfter = retryAfterMatch ? Number(retryAfterMatch[1]) : 60;
          this.rateLimitResets.set(normalizedEmail, Date.now() + retryAfter * 1000);
          return {
            success: false,
            email: normalizedEmail,
            error: `Too many magic link requests. Please wait ${retryAfter} seconds.`,
            retryAfter,
          };
        }

        return {
          success: false,
          email: normalizedEmail,
          error: error.message,
        };
      }

      // Clear rate limit on success
      this.rateLimitResets.delete(normalizedEmail);

      return {
        success: true,
        email: normalizedEmail,
      };
    } catch (error) {
      console.error('[MagicLink] Unexpected Error:', error);
      const message = error instanceof Error ? error.message : 'Network error';
      return {
        success: false,
        email: normalizedEmail,
        error: message,
      };
    }
  }

  /**
   * Get rate limit countdown for an email
   */
  getRateLimitCountdown(email: string): number | null {
    const reset = this.rateLimitResets.get(email.toLowerCase());
    if (!reset || reset <= Date.now()) {
      return null;
    }
    return Math.ceil((reset - Date.now()) / 1000);
  }

  /**
   * Sanitize return_to URL to prevent open redirects
   */
  private sanitizeReturnTo(url: string): string {
    if (!url || typeof url !== 'string') {
      return '/app/onboarding';
    }

    const trimmed = url.trim();

    // Must start with /
    if (!trimmed.startsWith('/')) {
      return '/app/onboarding';
    }

    // Prevent // (protocol-relative URLs)
    if (trimmed.startsWith('//')) {
      return '/app/onboarding';
    }

    // Whitelist known paths
    const allowedPaths = [
      '/app/onboarding',
      '/app/dashboard',
      '/app/jobs',
      '/app/applications',
      '/app/holds',
      '/app/billing',
      '/app/settings',
    ];

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
        return "You'll go straight to the job feed.";
      default:
        return `We'll take you to ${sanitized} once you're in.`;
    }
  }
}

export const magicLinkService = new MagicLinkService();

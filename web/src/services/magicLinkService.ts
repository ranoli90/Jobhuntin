/**
 * Magic Link Service - Centralized magic link handling
 * Ensures consistent behavior across Homepage, Login, and Onboarding
 */

import { config } from '../config';

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
  ): Promise<{ success: boolean; email: string; error?: string }> {
    const normalizedEmail = email.trim().toLowerCase();

    // Validate email
    if (!config.validation.emailRegex.test(normalizedEmail)) {
      return {
        success: false,
        email: normalizedEmail,
        error: 'Please enter a valid email address',
      };
    }

    // Check rate limit
    const rateLimitReset = this.rateLimitResets.get(normalizedEmail);
    if (rateLimitReset && rateLimitReset > Date.now()) {
      const secondsLeft = Math.ceil((rateLimitReset - Date.now()) / 1000);
      return {
        success: false,
        email: normalizedEmail,
        error: `Too many requests. Please wait ${secondsLeft}s before trying again.`,
      };
    }

    try {
      const response = await fetch(`${config.api.baseUrl}/auth/magic-link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: normalizedEmail,
          return_to: this.sanitizeReturnTo(returnTo),
        }),
        signal: AbortSignal.timeout(config.api.timeout),
      });

      if (!response.ok) {
        if (response.status === 429) {
          // Rate limited - set cooldown
          this.rateLimitResets.set(normalizedEmail, Date.now() + 60_000);
          return {
            success: false,
            email: normalizedEmail,
            error: 'Too many magic link requests. Please wait 60 seconds.',
          };
        }

        let errorMessage = 'Failed to send magic link';
        try {
          const data = await response.json();
          errorMessage = data?.detail || data?.error || errorMessage;
        } catch {
          errorMessage = await response.text() || errorMessage;
        }

        return {
          success: false,
          email: normalizedEmail,
          error: errorMessage,
        };
      }

      // Clear rate limit on success
      this.rateLimitResets.delete(normalizedEmail);

      return {
        success: true,
        email: normalizedEmail,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Network error';
      return {
        success: false,
        email: normalizedEmail,
        error: message.includes('timeout')
          ? 'Request timed out. Please try again.'
          : message,
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

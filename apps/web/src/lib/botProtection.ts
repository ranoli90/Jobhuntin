import { telemetry } from './telemetry';

interface FingerprintData {
  userAgent: string;
  language: string;
  platform: string;
  screenResolution: string;
  timezone: string;
  canvas?: string;
  webgl?: string;
}

interface CaptchaConfig {
  enabled: boolean;
  provider: 'hcaptcha' | 'recaptcha' | 'turnstile';
  siteKey: string;
}

interface BotProtectionOptions {
  requireCaptcha?: boolean;
  rateLimitPerIP?: number;
  rateLimitPerFingerprint?: number;
  windowMs?: number;
}

/**
 * Bot protection utilities including IP fingerprinting, captcha integration, and enhanced rate limiting
 */
class BotProtection {
  private captchaConfig: CaptchaConfig | null = null;
  private readonly DEFAULT_OPTIONS: Required<BotProtectionOptions> = {
    requireCaptcha: false,
    rateLimitPerIP: 5,
    rateLimitPerFingerprint: 3,
    windowMs: 15 * 60 * 1000, // 15 minutes
  };

  constructor() {
    this.initCaptchaConfig();
  }

  private initCaptchaConfig(): void {
    // Initialize captcha configuration based on environment
    if (typeof window !== 'undefined') {
      // Check for captcha provider in environment or config
      const hcaptchaSiteKey = import.meta.env.VITE_HCAPTCHA_SITE_KEY;
      const recaptchaSiteKey = import.meta.env.VITE_RECAPTCHA_SITE_KEY;
      const turnstileSiteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY;

      if (hcaptchaSiteKey) {
        this.captchaConfig = {
          enabled: true,
          provider: 'hcaptcha',
          siteKey: hcaptchaSiteKey,
        };
      } else if (recaptchaSiteKey) {
        this.captchaConfig = {
          enabled: true,
          provider: 'recaptcha',
          siteKey: recaptchaSiteKey,
        };
      } else if (turnstileSiteKey) {
        this.captchaConfig = {
          enabled: true,
          provider: 'turnstile',
          siteKey: turnstileSiteKey,
        };
      }
    }
  }

  /**
   * Generate a browser fingerprint for bot detection
   */
  generateFingerprint(): string {
    if (typeof window === 'undefined') {
      return 'server-side';
    }

    const fingerprintData: FingerprintData = {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      screenResolution: `${screen.width}x${screen.height}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    };

    // Add canvas fingerprint if available
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (ctx) {
        canvas.width = 200;
        canvas.height = 50;
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Browser fingerprint', 2, 2);
        fingerprintData.canvas = canvas.toDataURL();
      }
    } catch (error) {
      // Canvas not available
    }

    // Add WebGL fingerprint if available
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (gl && gl instanceof WebGLRenderingContext) {
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
          fingerprintData.webgl = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) + 
                                   gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        }
      }
    } catch (error) {
      // WebGL not available
    }

    // Create hash from fingerprint data
    const fingerprintString = JSON.stringify(fingerprintData);
    return this.simpleHash(fingerprintString);
  }

  /**
   * Simple hash function for fingerprinting
   */
  private simpleHash(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
  }

  /**
   * Get client IP address (requires backend cooperation)
   */
  async getClientIP(): Promise<string> {
    try {
      // In production, this should come from your backend API
      // For now, we'll use a public IP service as fallback
      const response = await fetch('https://api.ipify.org?format=json');
      const data = await response.json();
      return data.ip || 'unknown';
    } catch (error) {
      console.warn('[BotProtection] Failed to get client IP:', error);
      return 'unknown';
    }
  }

  /**
   * Check if captcha should be required based on risk factors
   */
  shouldRequireCaptcha(email: string, options: BotProtectionOptions = {}): boolean {
    const opts = { ...this.DEFAULT_OPTIONS, ...options };

    // Always require if explicitly configured
    if (opts.requireCaptcha || this.captchaConfig?.enabled) {
      return true;
    }

    // Risk factors that trigger captcha
    const riskFactors = {
      suspiciousEmail: this.isSuspiciousEmail(email),
      automatedUserAgent: this.isAutomatedUserAgent(),
      incognitoMode: this.detectIncognitoMode(),
    };

    const riskScore = Object.values(riskFactors).filter(Boolean).length;
    
    telemetry.track('Bot Protection Risk Assessment', {
      email: email.replace(/(.{2}).+(@.+)/, '$1***$2'),
      riskScore,
      riskFactors,
    });

    // Require captcha for medium to high risk
    return riskScore >= 1;
  }

  /**
   * Detect suspicious email patterns
   */
  private isSuspiciousEmail(email: string): boolean {
    const suspiciousPatterns = [
      /^[a-z]+\d+@/,  // Letters followed immediately by numbers
      /\d{4,}@/,      // 4+ consecutive numbers
      /(test|demo|sample|fake|temp)/i,  // Common test words
      /(10minutemail|guerrillamail|mailinator)/i,  // Disposable email services
    ];

    return suspiciousPatterns.some(pattern => pattern.test(email));
  }

  /**
   * Detect automated user agents
   */
  private isAutomatedUserAgent(): boolean {
    if (typeof window === 'undefined') return false;

    const userAgent = navigator.userAgent.toLowerCase();
    const botPatterns = [
      /bot/,
      /crawler/,
      /spider/,
      /scraper/,
      /curl/,
      /wget/,
      /python/,
      /java/,
      /headless/,
      /phantom/,
      /selenium/,
    ];

    return botPatterns.some(pattern => pattern.test(userAgent));
  }

  /**
   * Attempt to detect incognito/private mode
   */
  private detectIncognitoMode(): boolean {
    if (typeof window === 'undefined') return false;

    try {
      // Chrome/Edge detection
      const fs = window.webkitRequestFileSystem || window.webkitResolveLocalFileSystemURL;
      if (fs) {
        fs(window.TEMPORARY, 100, () => {}, () => {
          return true; // Incognito detected
        });
      }

      // Firefox detection
      if ('serviceWorker' in navigator && !navigator.serviceWorker.controller) {
        return true;
      }

      // Safari detection
      try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        return false;
      } catch {
        return true; // Incognito detected
      }
    } catch {
      return false;
    }

    return false;
  }

  /**
   * Load captcha script
   */
  async loadCaptcha(): Promise<void> {
    if (!this.captchaConfig?.enabled) return;

    const { provider, siteKey } = this.captchaConfig;

    return new Promise((resolve, reject) => {
      // Check if already loaded
      if (window.grecaptcha || window.hcaptcha || window.turnstile) {
        resolve();
        return;
      }

      let scriptSrc = '';
      let globalVar = '';

      switch (provider) {
        case 'hcaptcha':
          scriptSrc = `https://js.hcaptcha.com/1/api.js?onload=hcaptchaOnLoad`;
          globalVar = 'hcaptchaOnLoad';
          break;
        case 'recaptcha':
          scriptSrc = `https://www.google.com/recaptcha/api.js?onload=recaptchaOnLoad&render=explicit`;
          globalVar = 'recaptchaOnLoad';
          break;
        case 'turnstile':
          scriptSrc = `https://challenges.cloudflare.com/turnstile/v0/api.js?onload=turnstileOnLoad`;
          globalVar = 'turnstileOnLoad';
          break;
      }

      const script = document.createElement('script');
      script.src = scriptSrc;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(`Failed to load ${provider} script`));

      // Set global callback
      (window as any)[globalVar] = () => resolve();

      document.head.appendChild(script);
    });
  }

  /**
   * Execute captcha challenge
   */
  async executeCaptcha(container: string | HTMLElement): Promise<string> {
    if (!this.captchaConfig?.enabled) {
      throw new Error('Captcha not configured');
    }

    await this.loadCaptcha();

    const { provider, siteKey } = this.captchaConfig;
    const element = typeof container === 'string' 
      ? document.getElementById(container) 
      : container;

    if (!element) {
      throw new Error('Captcha container not found');
    }

    return new Promise((resolve, reject) => {
      switch (provider) {
        case 'hcaptcha':
          if (!window.hcaptcha) {
            reject(new Error('hCaptcha not loaded'));
            return;
          }
          (window as any).hcaptcha.render(element, {
            sitekey: siteKey,
            callback: (token: string) => resolve(token),
            'error-callback': () => reject(new Error('hCaptcha failed')),
          });
          break;

        case 'recaptcha':
          if (!window.grecaptcha) {
            reject(new Error('reCAPTCHA not loaded'));
            return;
          }
          (window as any).grecaptcha.render(element, {
            sitekey: siteKey,
            callback: (token: string) => resolve(token),
            'error-callback': () => reject(new Error('reCAPTCHA failed')),
          });
          break;

        case 'turnstile':
          if (!window.turnstile) {
            reject(new Error('Turnstile not loaded'));
            return;
          }
          (window as any).turnstile.render(element, {
            sitekey: siteKey,
            callback: (token: string) => resolve(token),
            'error-callback': () => reject(new Error('Turnstile failed')),
          });
          break;
      }
    });
  }

  /**
   * Verify captcha token with backend
   */
  async verifyCaptcha(token: string): Promise<boolean> {
    try {
      const { apiPost } = await import('./api');
      const response = await apiPost('/auth/verify-captcha', { token });
      return response.success === true;
    } catch (error) {
      console.error('[BotProtection] Captcha verification failed:', error);
      return false;
    }
  }

  /**
   * Enhanced rate limiting that considers IP and fingerprint
   */
  async checkRateLimit(
    identifier: string,
    options: BotProtectionOptions = {}
  ): Promise<{ allowed: boolean; resetIn?: number; reason?: string }> {
    const opts = { ...this.DEFAULT_OPTIONS, ...options };

    try {
      const { apiPost } = await import('./api');
      
      // Get additional context
      const fingerprint = this.generateFingerprint();
      const clientIP = await this.getClientIP();

      const response = await apiPost('/auth/check-rate-limit', {
        identifier,
        fingerprint,
        ip: clientIP,
        rateLimitPerIP: opts.rateLimitPerIP,
        rateLimitPerFingerprint: opts.rateLimitPerFingerprint,
        windowMs: opts.windowMs,
      });

      telemetry.track('Rate Limit Check', {
        identifier: identifier.replace(/(.{2}).+(@.+)/, '$1***$2'),
        allowed: response.allowed,
        reason: response.reason,
      });

      return response;
    } catch (error) {
      console.error('[BotProtection] Rate limit check failed:', error);
      // Fail open - allow request if service is down
      return { allowed: true };
    }
  }
}

// Extend Window interface for captcha globals
declare global {
  interface Window {
    grecaptcha?: any;
    hcaptcha?: any;
    turnstile?: any;
  }
}

// Export singleton instance
export const botProtection = new BotProtection();

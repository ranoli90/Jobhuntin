/**
 * Centralized configuration for the frontend application.
 * All environment-dependent values should be defined here.
 */

export const config = {
  // API Configuration
  api: {
    baseUrl: (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, ""),
    timeout: 30000, // 30 seconds
  },

  // App base URL (used for auth redirects; override in env to avoid preview-domain issues)
  appBaseUrl: import.meta.env.VITE_APP_BASE_URL || "",

  // Authentication (handled by backend API)
  auth: {
    // Auth is handled via magic links through the backend API
    // No direct Supabase client needed
  },

  // Analytics
  analytics: {
    gaId: import.meta.env.VITE_GA_ID || "",
    hotjarId: import.meta.env.VITE_HOTJAR_ID || "",
    gtmId: import.meta.env.VITE_GTM_ID || "",
  },

  // Feature Flags
  features: {
    enableDebugMode: import.meta.env.DEV,
  },

  // URLs (SEO4: config.urls.og used for OG images; verify /api/og endpoint exists and responds quickly)
  urls: {
    homepage: import.meta.env.VITE_APP_BASE_URL || "https://jobhuntin.com",
    pricing: "/pricing",
    successStories: "/success-stories",
    chromeExtension: "/chrome-extension",
    recruiters: "/recruiters",
    guides: "/guides",
    privacy: "/privacy",
    terms: "/terms",
    og: import.meta.env.VITE_APP_BASE_URL || "https://jobhuntin.com",
  },

  // Validation
  validation: {
    emailRegex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    passwordMinLength: 10,
  },
} as const;

/**
 * Validate that all required environment variables are set.
 */
export function validateConfig(): string[] {
  const errors: string[] = [];

  if (!config.api.baseUrl) {
    errors.push("VITE_API_URL is not configured");
  }

  if (config.appBaseUrl && !/^https?:\/\//.test(config.appBaseUrl)) {
    errors.push("VITE_APP_BASE_URL must include protocol (e.g. https://app.example.com)");
  }

  if (import.meta.env.PROD && config.appBaseUrl && !config.appBaseUrl.startsWith('https://')) {
    errors.push("VITE_APP_BASE_URL must use HTTPS in production");
  }

  // Log errors in production for debugging
  if (errors.length > 0) {
    console.error("[Config] Validation errors:", errors);
  }

  return errors;
}

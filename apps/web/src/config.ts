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

  // Authentication
  auth: {
    supabaseUrl: import.meta.env.VITE_SUPABASE_URL || "",
    supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || "",
  },

  // Analytics
  analytics: {
    gaId: import.meta.env.VITE_GA_ID || "",
    hotjarId: import.meta.env.VITE_HOTJAR_ID || "",
  },

  // Feature Flags
  features: {
    enableDebugMode: import.meta.env.DEV,
  },

  // URLs
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

  if (!config.auth.supabaseUrl) {
    errors.push("VITE_SUPABASE_URL is not configured");
  }

  if (!config.auth.supabaseAnonKey) {
    errors.push("VITE_SUPABASE_ANON_KEY is not configured");
  }

  if (config.appBaseUrl && !/^https?:\/\//.test(config.appBaseUrl)) {
    errors.push("VITE_APP_BASE_URL must include protocol (e.g. https://app.example.com)");
  }

  if (import.meta.env.PROD && config.appBaseUrl && !config.appBaseUrl.startsWith('https://')) {
    errors.push("VITE_APP_BASE_URL must use HTTPS in production");
  }

  return errors;
}
